# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The verdict: is the AION cell smaller and faster?
# ================================================================

"""The one question the tool exists to answer, with the arithmetic shown.

An AION cell is worth drawing only if it beats the alternative that costs
nothing: abutting the PDK standard cells that compute the same function.  This
module puts the two side by side and says so in one machine-readable line, and
in a report a human can check by hand.

Three decisions shape everything here.

**Area comes from the geometry, never from Liberty.**  The ``area`` attribute in
a generated ``.lib`` was written *from* the LEF footprint by the characterizer,
so reading it back would be checking our own homework.  The area metric is
:class:`aion_layout.metrics.CellGeometry`, measured from the prBoundary or the
LEF ``SIZE``.  The Liberty value is still read, and a disagreement between the
two becomes a note -- that disagreement means an export step published a size
that does not match the layout, which is worth knowing.

**Both sides are read at the same operating point.**  A delay is meaningless
without the slew and load it was measured at, and "18% faster" computed from two
different grid points is not a speedup, it is an error with a percent sign.  When
the two libraries share a characterization grid the shared middle grid point is
used.  When they do not, both are interpolated to the middle point of the
*smaller* grid -- the more coarsely characterized library, whose mid point is
the one more likely to fall inside the other's range -- and the report says so
in a note that cannot be missed.

The grid point is the small half of "the same operating point"; the **corner** is
the large half, and it is checked before anything else.  ``corner`` is only a
label a caller passed in, so the two libraries' own ``nom_voltage`` /
``nom_temperature`` / ``nom_process`` are compared instead, and a disagreement is
a :class:`CompareError`.  A fast-corner candidate against a slow-corner baseline
otherwise reports a forty-percent speedup that measures nothing but the corner
spread -- and it reports it as a ``WIN``.  Libraries that state no operating
conditions cannot be checked, and the report says that rather than reading
silence as agreement.

**Nothing is dropped quietly.**  ``worst_delay`` and ``mean_delay`` are each
taken over that cell's own complete arc set, so an arc one library publishes and
the other does not still counts against the library that has it; the asymmetry
becomes a note rather than a silent exclusion.  ``per_arc`` then shows the arcs
that do correspond, one line each, so a reader can see which path moved.

A comparison built on half the data is worse than no comparison, so a missing
library, an absent cell, an empty arc list, a zero baseline area and a geometry
whose height the parts disagree on are all errors, not caveats.
"""

from __future__ import annotations

import dataclasses as dc
import json
import math
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from .liberty import (
    LibCell,
    Library,
    LibertyError,
    arc_delays,
    default_operating_point,
    delay_grid,
    mean_arc_delay,
    read_liberty,
    worst_arc_delay,
)
from .metrics import GRID_TOL_UM, CellGeometry

#: A library, or a path to one that has not been read yet.
LibraryLike = Union[Library, Path, str]
#: One measured footprint, or the parts of an abutted row to add up.
GeometryLike = Union[CellGeometry, Sequence[CellGeometry]]

#: Relative tolerance on the Liberty ``area`` vs the measured footprint.
_AREA_CROSSCHECK_REL = 0.005
#: Absolute floor for the same check, in um^2, so tiny cells are not over-graded.
_AREA_CROSSCHECK_ABS = 1e-3


class CompareError(RuntimeError):
    """Raised when the two sides cannot be compared honestly."""


# --------------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class Metric:
    """One number measured on both sides, and which direction is good.

    ``improved`` is strict: a candidate that merely ties has not improved.  The
    flow is arguing that a hand-drawn cell earns its place, and a tie does not.
    """

    name: str
    unit: str
    candidate: float
    baseline: float
    lower_is_better: bool = True

    @property
    def delta(self) -> float:
        return self.candidate - self.baseline

    @property
    def pct(self) -> float:
        if self.baseline == 0:
            raise CompareError(
                f"{self.name}: the baseline is zero, so there is no percentage "
                "change to report"
            )
        return (self.candidate - self.baseline) / self.baseline * 100.0

    @property
    def improved(self) -> bool:
        if self.lower_is_better:
            return self.candidate < self.baseline
        return self.candidate > self.baseline

    def describe(self) -> str:
        """``'placement area: 10.8864 vs 19.9584 um2 (-45.5%)'``"""
        return (
            f"{self.name}: {_fmt(self.candidate, self.unit)} vs "
            f"{_fmt(self.baseline, self.unit)} {self.unit} ({self.pct:+.1f}%)"
        )

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "unit": self.unit,
            "candidate": self.candidate,
            "baseline": self.baseline,
            "delta": self.delta,
            "pct": self.pct,
            "lower_is_better": self.lower_is_better,
            "improved": self.improved,
        }


_FORMATS = {
    "um2": ".4f",
    "um": ".4f",
    "ps": ".2f",
    "ns": ".5f",
    "pF": ".5f",
    "pW": ".3f",
    "sites": ".3g",
}


def _fmt(value: float, unit: str) -> str:
    return format(value, _FORMATS.get(unit, ".6g"))


@dc.dataclass(frozen=True)
class Comparison:
    """Everything the verdict rests on, in one object.

    ``worst_delay`` and ``mean_delay`` are in **picoseconds** because that is
    the scale a standard cell lives at and the scale the verdict line prints.
    ``per_arc`` is in **nanoseconds**, the unit Liberty itself uses, so an entry
    can be checked against the ``.lib`` without a conversion in the reader's
    head.
    """

    cell: str
    baseline_cell: str
    area: Metric
    worst_delay: Metric
    mean_delay: Metric
    extra: Tuple[Metric, ...]
    per_arc: Tuple[Tuple[str, float, float], ...]
    notes: Tuple[str, ...]
    corner: str = "typ"
    slew_ns: float = 0.0
    load_pf: float = 0.0
    candidate_worst_arc: str = ""
    baseline_worst_arc: str = ""

    @property
    def smaller(self) -> bool:
        return self.area.improved

    @property
    def faster(self) -> bool:
        """True when the slowest path through the cell got shorter.

        The worst arc is what static timing analysis will pick up, so it is the
        one that decides this.  ``mean_delay`` is reported beside it, and a
        disagreement between the two is raised as a note.
        """
        return self.worst_delay.improved

    @property
    def wins(self) -> bool:
        return self.smaller and self.faster

    @property
    def metrics(self) -> Tuple[Metric, ...]:
        return (self.area, self.worst_delay, self.mean_delay) + self.extra


# --------------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------------


def abutted_geometry(
    parts: Sequence[CellGeometry], name: Optional[str] = None
) -> CellGeometry:
    """Add up the footprints of cells placed side by side in one row.

    This is the baseline the AION cell has to beat: the PDK cells it replaces,
    abutted.  Widths add; the height is the row height they must already share,
    and parts that do not share one were never going to abut, so that is an
    error rather than a note.  Every part's own row-legality problem is carried
    forward, because an illegal part makes the row illegal too.
    """
    if not parts:
        raise CompareError("an abutted footprint needs at least one cell")
    heights = [p.height_um for p in parts]
    if max(heights) - min(heights) > GRID_TOL_UM:
        detail = ", ".join(f"{p.cell} {p.height_um:.4f} um" for p in parts)
        raise CompareError(
            f"these cells cannot abut: their heights differ ({detail})"
        )
    problems: List[str] = []
    for part in parts:
        problems.extend(f"{part.cell}: {p}" for p in part.problems)
    sources = sorted({p.source for p in parts})
    return CellGeometry(
        cell=name or " + ".join(p.cell for p in parts),
        width_um=sum(p.width_um for p in parts),
        height_um=statistics.fmean(heights),
        source=f"abutted({'+'.join(sources)})",
        problems=tuple(problems),
    )


def _as_library(value: LibraryLike, role: str) -> Library:
    if isinstance(value, Library):
        return value
    try:
        return read_liberty(value)
    except LibertyError as exc:
        raise CompareError(f"{role} library: {exc}") from exc


def _as_geometry(value: GeometryLike, role: str) -> CellGeometry:
    if isinstance(value, CellGeometry):
        return value
    parts = list(value)
    if not parts:
        raise CompareError(f"{role} geometry is empty")
    if any(not isinstance(p, CellGeometry) for p in parts):
        raise CompareError(
            f"{role} geometry must be a CellGeometry or a sequence of them"
        )
    if len(parts) == 1:
        return parts[0]
    return abutted_geometry(parts)


def _lib_cell(library: Library, name: str, role: str) -> LibCell:
    try:
        cell = library.cell(name)
    except LibertyError as exc:
        raise CompareError(f"{role}: {exc}") from exc
    if not cell.arcs:
        raise CompareError(
            f"{role}: cell {name} in {library.path.name} publishes no timing "
            "arcs, so there is no delay to compare"
        )
    return cell


# --------------------------------------------------------------------------------
# The corner
# --------------------------------------------------------------------------------

#: ``Library`` attribute, printed unit, and how the report names it.
_PVT_FIELDS = (
    ("nom_voltage", " V", "voltage"),
    ("nom_temperature", " C", "temperature"),
    ("nom_process", "", "process"),
)


def _pvt_notes(candidate: Library, baseline: Library, corner: str) -> List[str]:
    """Prove the two libraries were characterized at the same PVT, or refuse.

    The slew/load grid is the small half of "same operating point"; the corner
    is the large half.  A fast-corner candidate against a slow-corner baseline
    produces a forty-percent speedup out of nothing at all, and the ``corner``
    argument is only a label -- nobody checked it against the files.  So it is
    checked here, and a disagreement is an error rather than a note: a delta
    between two different corners is not a slow result, it is not a result.

    A library that states no ``nom_*`` at all cannot be checked, and that is
    said plainly instead of being read as agreement.
    """
    disagree: List[str] = []
    silent: List[str] = []
    for field, unit, what in _PVT_FIELDS:
        mine = getattr(candidate, field)
        theirs = getattr(baseline, field)
        if mine is None or theirs is None:
            silent.append(what)
            continue
        if not math.isclose(mine, theirs, rel_tol=1e-9, abs_tol=1e-9):
            disagree.append(f"{what} {mine:g}{unit} vs {theirs:g}{unit}")
    if disagree:
        raise CompareError(
            f"the two libraries were not characterized at the same corner "
            f"({'; '.join(disagree)}): candidate {candidate.path.name} is "
            f"{candidate.pvt_label()} and baseline {baseline.path.name} is "
            f"{baseline.pvt_label()}. A delay difference between two corners is "
            f"not a speedup, whatever the corner argument ({corner!r}) says."
        )
    if silent:
        return [
            "CORNER UNCHECKED: "
            + ", ".join(silent)
            + " is not stated by both libraries, so the flow could not prove "
            f"they share a corner (candidate {candidate.pvt_label()}; baseline "
            f"{baseline.pvt_label()})"
        ]
    shared = ", ".join(
        f"{what} {getattr(candidate, field):g}{unit}".strip()
        for field, unit, what in _PVT_FIELDS
    )
    return [
        f"both libraries are characterized at the same corner ({shared}): "
        f"candidate {candidate.operating_conditions or candidate.name}, "
        f"baseline {baseline.operating_conditions or baseline.name}"
    ]


# --------------------------------------------------------------------------------
# The operating point
# --------------------------------------------------------------------------------


def _grid_size(
    grid: Tuple[Tuple[float, ...], Tuple[float, ...]],
) -> Tuple[int, float, float]:
    """A sortable size for a characterization grid.

    Point count first, then how far the two axes reach.  The reach matters as
    much as the count: SG13G2 characterizes ``nand2_1`` and ``nand2_2`` on grids
    of the same 7x7 shape but doubles the load axis for the stronger driver, and
    reading the weaker cell at the stronger one's mid load would clamp it
    against the end of its own table.  Picking the grid that reaches least far
    is what keeps the shared operating point inside both.
    """
    index_1, index_2 = grid
    return (
        len(index_1) * max(len(index_2), 1),
        index_1[-1] if index_1 else 0.0,
        index_2[-1] if index_2 else 0.0,
    )


def _grid_span(grid: Tuple[Tuple[float, ...], Tuple[float, ...]]) -> str:
    """``'7x7, slew 0.0186..2.5074 ns x load 0.001..0.3 pF'``"""
    index_1, index_2 = grid
    span = f"{len(index_1)}x{len(index_2)}, slew {index_1[0]:g}..{index_1[-1]:g} ns"
    if index_2:
        span += f" x load {index_2[0]:g}..{index_2[-1]:g} pF"
    return span


def _operating_point(
    candidate: LibCell, baseline: LibCell
) -> Tuple[float, float, List[str]]:
    """Pick one ``(slew, load)`` both cells are read at, and explain the choice."""
    try:
        grid_c = delay_grid(candidate)
        grid_b = delay_grid(baseline)
    except LibertyError as exc:
        raise CompareError(str(exc)) from exc

    notes: List[str] = []
    if grid_c == grid_b:
        slew, load = default_operating_point(candidate)
        notes.append(
            f"both libraries share a {len(grid_c[0])}x{len(grid_c[1])} "
            f"characterization grid; compared at its middle point, "
            f"slew {slew:g} ns / load {load:g} pF"
        )
        return slew, load, notes

    # Different grids.  Take the smaller one's mid point for both: it carries
    # less information, so interpolating the finer library onto it is the
    # better-conditioned direction, and its mid point is the one more likely to
    # sit inside the other library's range.
    if _grid_size(grid_b) <= _grid_size(grid_c):
        source, chosen = "baseline", baseline
    else:
        source, chosen = "candidate", candidate
    slew, load = default_operating_point(chosen)
    notes.append(
        "GRID MISMATCH: the two libraries were characterized on different "
        f"grids (candidate {_grid_span(grid_c)}; baseline {_grid_span(grid_b)}). "
        f"Both were read at the middle point of the smaller ({source}) grid, "
        f"slew {slew:g} ns / load {load:g} pF, so these delays are interpolated "
        "rather than tabulated. They are still the same operating point on both "
        "sides, which is what the comparison needs."
    )
    return slew, load, notes


def _clamping_note(cell: LibCell, role: str, slew: float, load: float) -> Optional[str]:
    """Say so when the operating point falls outside a cell's characterized grid."""
    outside = [
        arc.label(edge)
        for arc in cell.arcs
        for edge in ("rise", "fall")
        if arc.table(edge) is not None and not arc.table(edge).contains(slew, load)
    ]
    if not outside:
        return None
    shown = ", ".join(outside[:4]) + (" ..." if len(outside) > 4 else "")
    return (
        f"CLAMPED: slew {slew:g} ns / load {load:g} pF is outside the grid the "
        f"{role} cell {cell.name} was characterized on, for {len(outside)} "
        f"arc table(s) ({shown}). Those delays are edge values, not measurements "
        "at this point."
    )


# --------------------------------------------------------------------------------
# The comparison
# --------------------------------------------------------------------------------


def _area_crosscheck(cell: LibCell, geometry: CellGeometry, role: str) -> Optional[str]:
    if cell.area is None:
        return (
            f"the {role} library states no area for {cell.name}, so the Liberty "
            "view could not be cross-checked against the measured footprint"
        )
    measured = geometry.area_um2
    tolerance = max(_AREA_CROSSCHECK_ABS, _AREA_CROSSCHECK_REL * measured)
    if abs(cell.area - measured) <= tolerance:
        return None
    return (
        f"AREA MISMATCH ({role}): the Liberty file says {cell.name} is "
        f"{cell.area:.4f} um^2 but {geometry.cell} measures {measured:.4f} um^2 "
        f"from {geometry.source}. The comparison uses the measured value"
        + (
            "; the two are expected to differ when the baseline footprint is an "
            "abutment of several cells and the Liberty cell is one of them"
            if geometry.source.startswith("abutted")
            else ""
        )
        + "."
    )


def _geometry_notes(geometry: CellGeometry, role: str) -> List[str]:
    notes: List[str] = []
    if "bbox" in geometry.source:
        notes.append(
            f"the {role} footprint is a shape bounding box, not a placement "
            "boundary: it includes well and implant overhang an abutted "
            "neighbour would share, so it overstates the area"
        )
    for problem in geometry.problems:
        notes.append(f"{role} footprint is not row-legal: {problem}")
    return notes


def _arc_notes(
    candidate: LibCell,
    baseline: LibCell,
    cand_delays: Dict[str, float],
    base_delays: Dict[str, float],
) -> List[str]:
    notes: List[str] = []
    only_candidate = sorted(set(cand_delays) - set(base_delays))
    only_baseline = sorted(set(base_delays) - set(cand_delays))
    if only_candidate:
        notes.append(
            f"{len(only_candidate)} arc(s) exist only in the candidate and have "
            f"no baseline counterpart: {', '.join(only_candidate)}. They are "
            "counted in the candidate's worst and mean delay."
        )
    if only_baseline:
        notes.append(
            f"{len(only_baseline)} arc(s) exist only in the baseline and have no "
            f"candidate counterpart: {', '.join(only_baseline)}. They are "
            "counted in the baseline's worst and mean delay."
        )

    cand_sense = {arc.label(e): arc.sense for arc in candidate.arcs for e in ("rise", "fall")}
    base_sense = {arc.label(e): arc.sense for arc in baseline.arcs for e in ("rise", "fall")}
    for label in sorted(set(cand_delays) & set(base_delays)):
        if cand_sense.get(label) != base_sense.get(label):
            notes.append(
                f"arc {label} has timing_sense {cand_sense.get(label)!r} in the "
                f"candidate and {base_sense.get(label)!r} in the baseline; the "
                "two arcs may not be the same path"
            )
    if set(candidate.inputs) != set(baseline.inputs):
        notes.append(
            f"input pins differ: candidate {list(candidate.inputs)} vs "
            f"baseline {list(baseline.inputs)}"
        )
    if set(candidate.outputs) != set(baseline.outputs):
        notes.append(
            f"output pins differ: candidate {list(candidate.outputs)} vs "
            f"baseline {list(baseline.outputs)}"
        )
    return notes


def _add_extra(extra: List[Metric], notes: List[str], metric: Metric) -> None:
    """Keep a secondary metric only if it has a percentage change to report.

    ``Metric.pct`` refuses to divide by a zero baseline, which is right, but a
    single zero-valued extra would otherwise take the whole report down with it.
    A secondary metric is not worth that, so it becomes a note instead -- still
    stated, never invented, and the verdict is untouched because the verdict
    rests on area and the worst arc, both of which are checked for zero above.
    """
    if metric.baseline == 0:
        notes.append(
            f"{metric.name} was not compared: the baseline is zero "
            f"(candidate {_fmt(metric.candidate, metric.unit)} {metric.unit})"
        )
        return
    extra.append(metric)


def compare(
    *,
    cell: str,
    baseline_cell: str,
    candidate_lib: LibraryLike,
    baseline_lib: LibraryLike,
    candidate_geometry: GeometryLike,
    baseline_geometry: GeometryLike,
    corner: str = "typ",
) -> Comparison:
    """Compare one AION cell against the PDK cells it replaces.

    ``candidate_geometry`` and ``baseline_geometry`` may each be a single
    :class:`~aion_layout.metrics.CellGeometry` or the sequence of footprints
    that abut to form the baseline row; a sequence is summed with
    :func:`abutted_geometry`.
    """
    cand_lib = _as_library(candidate_lib, "candidate")
    base_lib = _as_library(baseline_lib, "baseline")
    cand_cell = _lib_cell(cand_lib, cell, "candidate")
    base_cell = _lib_cell(base_lib, baseline_cell, "baseline")
    cand_geom = _as_geometry(candidate_geometry, "candidate")
    base_geom = _as_geometry(baseline_geometry, "baseline")

    if base_geom.area_um2 <= 0:
        raise CompareError(
            f"the baseline footprint {base_geom.cell} measures "
            f"{base_geom.area_um2} um^2; there is nothing to compare against"
        )
    if cand_geom.area_um2 <= 0:
        raise CompareError(
            f"the candidate footprint {cand_geom.cell} measures "
            f"{cand_geom.area_um2} um^2, which is not a cell"
        )

    corner_notes = _pvt_notes(cand_lib, base_lib, corner)
    slew, load, notes = _operating_point(cand_cell, base_cell)
    notes[:0] = [
        f"corner {corner}: candidate {cand_lib.name} ({cand_lib.path.name}) "
        f"vs baseline {base_lib.name} ({base_lib.path.name})",
        *corner_notes,
    ]
    for role, subject in (("candidate", cand_cell), ("baseline", base_cell)):
        note = _clamping_note(subject, role, slew, load)
        if note:
            notes.append(note)

    try:
        cand_delays = arc_delays(cand_cell, slew=slew, load=load)
        base_delays = arc_delays(base_cell, slew=slew, load=load)
        cand_worst, cand_worst_arc = worst_arc_delay(cand_cell, slew=slew, load=load)
        base_worst, base_worst_arc = worst_arc_delay(base_cell, slew=slew, load=load)
        cand_mean = mean_arc_delay(cand_cell, slew=slew, load=load)
        base_mean = mean_arc_delay(base_cell, slew=slew, load=load)
    except LibertyError as exc:
        raise CompareError(str(exc)) from exc

    if base_worst <= 0 or base_mean <= 0:
        raise CompareError(
            f"the baseline cell {baseline_cell} publishes a worst arc delay of "
            f"{base_worst * 1000.0:g} ps and a mean of {base_mean * 1000.0:g} ps "
            "at this operating point; a zero baseline is not something a "
            "speedup can be computed against"
        )

    area = Metric("placement area", "um2", cand_geom.area_um2, base_geom.area_um2)
    worst = Metric("worst arc delay", "ps", cand_worst * 1000.0, base_worst * 1000.0)
    mean = Metric("mean arc delay", "ps", cand_mean * 1000.0, base_mean * 1000.0)

    extra: List[Metric] = []
    _add_extra(extra, notes, Metric("cell width", "um", cand_geom.width_um, base_geom.width_um))
    _add_extra(extra, notes, Metric("row sites", "sites", cand_geom.sites, base_geom.sites))
    if cand_cell.leakage is not None and base_cell.leakage is not None:
        _add_extra(
            extra, notes, Metric("leakage power", "pW", cand_cell.leakage, base_cell.leakage)
        )
    else:
        notes.append(
            "leakage was not compared: "
            + ", ".join(
                f"{role} states none"
                for role, subject in (("candidate", cand_cell), ("baseline", base_cell))
                if subject.leakage is None
            )
        )
    if cand_cell.input_caps and base_cell.input_caps:
        _add_extra(
            extra,
            notes,
            Metric(
                "worst input capacitance",
                "pF",
                max(cand_cell.input_caps.values()),
                max(base_cell.input_caps.values()),
            ),
        )
    else:
        notes.append(
            "input capacitance was not compared: "
            + ", ".join(
                f"{role} publishes none"
                for role, subject in (("candidate", cand_cell), ("baseline", base_cell))
                if not subject.input_caps
            )
        )

    notes.extend(_arc_notes(cand_cell, base_cell, cand_delays, base_delays))
    for role, subject, geometry in (
        ("candidate", cand_cell, cand_geom),
        ("baseline", base_cell, base_geom),
    ):
        note = _area_crosscheck(subject, geometry, role)
        if note:
            notes.append(note)
        notes.extend(_geometry_notes(geometry, role))

    if worst.improved != mean.improved:
        notes.append(
            "the worst arc and the mean arc disagree on direction: worst "
            f"{worst.pct:+.1f}%, mean {mean.pct:+.1f}%. The verdict follows the "
            "worst arc, which is what static timing analysis will see."
        )

    per_arc = tuple(
        (label, cand_delays[label], base_delays[label])
        for label in sorted(set(cand_delays) & set(base_delays))
    )
    if not per_arc:
        notes.append(
            "no arc label appears in both libraries, so there is no per-arc "
            "detail; the delay metrics still compare each cell's own arcs"
        )

    return Comparison(
        cell=cell,
        baseline_cell=baseline_cell,
        area=area,
        worst_delay=worst,
        mean_delay=mean,
        extra=tuple(extra),
        per_arc=per_arc,
        notes=tuple(notes),
        corner=corner,
        slew_ns=slew,
        load_pf=load,
        candidate_worst_arc=cand_worst_arc,
        baseline_worst_arc=base_worst_arc,
    )


# --------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------


def verdict_line(cmp: Comparison) -> str:
    """One line, column 0, machine-readable: the whole answer.

    ``WIN`` is padded to four characters so that the line's fields land in the
    same columns whether the verdict is ``WIN`` or ``LOSS``.
    """
    verdict = "WIN" if cmp.wins else "LOSS"
    return (
        f"COMPARE: {verdict:<4} "
        f"area {cmp.area.pct:+.1f}% "
        f"({cmp.area.candidate:.3f} vs {cmp.area.baseline:.3f} um2)  "
        f"worst delay {cmp.worst_delay.pct:+.1f}% "
        f"({cmp.worst_delay.candidate:.1f} vs {cmp.worst_delay.baseline:.1f} ps)"
    )


def _row(metric: Metric) -> str:
    mark = "yes" if metric.improved else "no"
    return (
        f"| {metric.name} | {_fmt(metric.candidate, metric.unit)} | "
        f"{_fmt(metric.baseline, metric.unit)} | {metric.unit} | "
        f"{metric.delta:+.4g} | {metric.pct:+.1f}% | {mark} |"
    )


def render_markdown(cmp: Comparison) -> str:
    """The report a human checks the verdict line against."""
    lines: List[str] = [
        f"# {cmp.cell} vs {cmp.baseline_cell}",
        "",
        "```",
        verdict_line(cmp),
        "```",
        "",
        f"Smaller: **{'yes' if cmp.smaller else 'no'}** &nbsp; "
        f"Faster: **{'yes' if cmp.faster else 'no'}** &nbsp; "
        f"Verdict: **{'WIN' if cmp.wins else 'LOSS'}**",
        "",
        f"Corner `{cmp.corner}`, read at slew {cmp.slew_ns:g} ns and load "
        f"{cmp.load_pf:g} pF.",
        "",
        "## Metrics",
        "",
        "| metric | candidate | baseline | unit | delta | change | better |",
        "| --- | ---: | ---: | :--- | ---: | ---: | :---: |",
    ]
    lines.extend(_row(m) for m in cmp.metrics)
    lines += [
        "",
        f"Worst arc: candidate `{cmp.candidate_worst_arc}`, "
        f"baseline `{cmp.baseline_worst_arc}`.",
        "",
        "## Per-arc delay",
        "",
    ]
    if cmp.per_arc:
        lines += [
            "| arc | candidate (ns) | baseline (ns) | change |",
            "| --- | ---: | ---: | ---: |",
        ]
        for label, cand, base in cmp.per_arc:
            change = (
                f"{(cand - base) / base * 100.0:+.1f}%" if base else "n/a"
            )
            lines.append(f"| `{label}` | {cand:.5f} | {base:.5f} | {change} |")
    else:
        lines.append("No arc label appears in both libraries.")
    lines += ["", "## Notes", ""]
    lines.extend(f"- {note}" for note in cmp.notes)
    return "\n".join(lines) + "\n"


def render_json(cmp: Comparison) -> str:
    """The same comparison, for whatever consumes the flow's output."""
    payload = {
        "cell": cmp.cell,
        "baseline_cell": cmp.baseline_cell,
        "corner": cmp.corner,
        "operating_point": {"slew_ns": cmp.slew_ns, "load_pf": cmp.load_pf},
        "verdict": "WIN" if cmp.wins else "LOSS",
        "smaller": cmp.smaller,
        "faster": cmp.faster,
        "area": cmp.area.as_dict(),
        "worst_delay": cmp.worst_delay.as_dict(),
        "mean_delay": cmp.mean_delay.as_dict(),
        "extra": [m.as_dict() for m in cmp.extra],
        "worst_arc": {
            "candidate": cmp.candidate_worst_arc,
            "baseline": cmp.baseline_worst_arc,
        },
        "per_arc": [
            {"arc": label, "candidate_ns": cand, "baseline_ns": base}
            for label, cand, base in cmp.per_arc
        ],
        "notes": list(cmp.notes),
        "verdict_line": verdict_line(cmp),
    }
    return json.dumps(payload, indent=2)


__all__ = [
    "CompareError",
    "Comparison",
    "GeometryLike",
    "LibraryLike",
    "Metric",
    "abutted_geometry",
    "compare",
    "render_json",
    "render_markdown",
    "verdict_line",
]
