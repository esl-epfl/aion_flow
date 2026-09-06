# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Widen the series stacks, under an area cap
# ================================================================

"""Widen the devices in a deep series stack, as far as the area budget allows.

The worked example is why this module exists.  ``aion_minimizer`` folds three
PDK gates into one cell that is **45.5% smaller** and **28.6% slower**: every
falling arc gets faster, every rising arc gets 25-38% worse.  Characterising the
same netlist with no parasitics at all moves the numbers by 1.3-11.8 ps, about
1.6% -- so the layout is not the problem.  The problem is topological.  Folding
an inverter, a NAND2 and a NOR2 into one gate produces a **3-high series PMOS
stack**, the abutted row it replaces never has more than 2 devices in series,
and the minimizer left every device at the library's uniform ``w=1.12u``.  A
3-high stack of minimum-width PMOS is three times the on-resistance charging the
same load.

Widening only the stacked devices fixes it.  Measured on the ideal netlist, typ
corner, same 7x7 grid, at the middle grid point (slew 0.3294 ns, load 0.0648 pF):

======================  ===========  ==========================  ==========
series PMOS ``w``       worst delay  vs the abutted baseline      worst fall
======================  ===========  ==========================  ==========
1.12u (as minimized)      740.8 ps   +26.6%  (loses)              309.5 ps
2.24u                     466.4 ps   -20.3%  (wins)               318.9 ps
3.36u                     382.6 ps   -34.6%  (wins)               348.7 ps
======================  ===========  ==========================  ==========

3.36u is the fastest and it is the wrong answer: at three fingers per device it
costs enough poly columns to make the cell *wider than the abutted row*, so it
would buy speed by giving away the area win that was the point.  2.24u needs two
fingers, lands at nine sites, and wins on both axes at once.  **Choosing between
them is an area-constrained optimisation, and that is the whole job of this
module** -- not "make the stack wider", but "make the stack as wide as the cell
can afford and no wider".

Four decisions are worth recording, because each is a place where the obvious
shortcut produces a cell that is wrong rather than merely suboptimal.

**A 2-high stack is left alone.**  The PDK does not widen its own: ``nand2_1``,
``nor2_1``, ``nor3_1`` and ``nor4_1`` are all ``w=1.12u`` PMOS and ``w=740n``
NMOS however deep the stack, and only the ``_2`` drive-strength variants go
wider.  A blanket "widen every series device" rule would disagree with the
library this cell has to sit in a row beside, for no measured gain.  So the
default ``min_depth=2`` touches depth 3 and deeper, and every device that was
left alone carries a ``reason`` saying which rule spared it.

**Fingers stay at the library's own finger width.**  ``w`` in an SG13G2 netlist
is the TOTAL width across ``ng`` fingers -- ``sg13g2_nand2_2`` writes
``w=2.24u ... ng=2``, which is two 1.12u fingers, not one 2.24u device.  A
multiplier is therefore only usable if it lands on a whole number of fingers of
the width the library already draws; 2.5 does not, and is rounded to the 3
fingers it is nearest rather than silently becoming something the PDK's own
diffusion and contact rules were never dimensioned for.

**The input netlist is never edited.**  It is the flow's source of truth: LVS is
run against it, and a resize that rewrote it in place would leave every later
verification comparing the layout to a netlist that had quietly moved.  Resizing
is legitimate precisely because it is an explicit, recorded, re-runnable step
that produces a *differently named cell* in a *new file* -- so
:func:`write_resized_netlist` refuses, by resolved path, to write over its own
input.

**"Nothing fits" is an answer, not a failure.**  When every candidate overshoots
the budget the plan comes back with ``multiplier=1.0``, ``unchanged=True`` and a
note saying by how much each one overshot.  Falling back to 1.0 silently would
report the slow cell as though it had been considered and approved; saying so
tells the caller the real finding, which is that this cell cannot be made faster
without giving up the area win.
"""

from __future__ import annotations

import dataclasses as dc
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .metrics import ROW_HEIGHT_UM, SITE_WIDTH_UM
from .spice_parser import Mosfet, Subckt, parse_first_subckt, parse_spice_file


class ResizeError(RuntimeError):
    """Raised when a resize cannot be planned or written."""


# ---------------------------------------------------------------------------
# The geometry model
#
# Cell width is estimated rather than drawn, because the multiplier has to be
# chosen *before* anything is laid out.  The model is deliberately the crudest
# one that is still exact for a row-legal single-row cell: every poly finger
# takes one contacted column, the two rows share those columns, and diffusion
# overhangs the outermost gate at each end.
# ---------------------------------------------------------------------------

#: One contacted poly column, in nm: 110 (contact to gate) + 160 (contact) +
#: 110 (contact to gate) + 130 (gate length) = 510.  This is the pitch at which
#: fingers can be placed when every source/drain between them is contacted,
#: which is what a standard cell does.
CONTACTED_POLY_PITCH_NM = 510.0

#: Diffusion overhang beyond the outermost gate, in nm, at each end of the row.
#: Charged once per side, hence the ``2 *`` in :func:`estimate_width_nm`.
DIFF_OVERHANG_NM = 190.0

#: The placement site, in nm.  A cell width that is not a whole number of these
#: cannot be placed, so the estimate is always rounded UP to one.
SITE_WIDTH_NM = SITE_WIDTH_UM * 1000.0

#: Candidate multipliers, largest first.  The largest that fits the budget wins.
DEFAULT_MULTIPLIERS: Tuple[float, ...] = (3.0, 2.5, 2.0, 1.5)

#: Widest single finger the library draws (the PMOS of every ``_1`` cell).
#: A device wider than this is folded into more fingers rather than drawn tall.
DEFAULT_MAX_FINGER_W_NM = 1120.0

#: Ceiling on the path walk in :func:`stack_depths`.  A standard cell has a
#: handful of devices and a few dozen paths; anything that blows past this is
#: not a standard cell, and guessing at its depths would be worse than refusing.
MAX_WALK_STEPS = 200_000

#: Widths are compared in nm; anything under this is float noise, not a size.
WIDTH_TOL_NM = 1e-6

#: Instance parameters that describe the *original* diffusion geometry and are
#: wrong the moment ``w`` changes.  Dropped from a resized device line rather
#: than carried forward; see :func:`write_resized_netlist`.
GEOMETRY_PARAMS = ("ad", "as", "pd", "ps", "nrd", "nrs", "sa", "sb", "sd")


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class DeviceSizing:
    """What happened to one device, and why -- including "nothing"."""

    name: str
    model: str
    #: ``'pull-up'``, ``'pull-down'``, or ``'unknown'`` for a model that is
    #: neither NMOS nor PMOS and therefore sits in neither network.
    network: str
    #: Devices in series on the longest rail-to-output path through this one.
    #: ``0`` means it is on no such path at all.
    stack_depth: int
    original_w_nm: float
    original_ng: int
    new_w_nm: float
    new_ng: int
    #: ``new_w / original_w``.  Exactly ``1.0`` when the device was untouched.
    multiplier: float
    #: ``new_w / new_ng`` -- the width of one finger, which must stay a width
    #: the library already draws.
    finger_w_nm: float
    #: Why this device was, or was not, resized.  Present on every device: a
    #: report that only explains the changes cannot be checked for the ones it
    #: should have made and did not.
    reason: str

    @property
    def changed(self) -> bool:
        """True when this device's width or finger count actually moved."""
        return (
            abs(self.new_w_nm - self.original_w_nm) > WIDTH_TOL_NM
            or self.new_ng != self.original_ng
        )

    @property
    def fingers(self) -> int:
        """Poly columns this device occupies: fingers times the SPICE ``m``."""
        return self.new_ng


@dc.dataclass(frozen=True)
class CandidateFit:
    """One multiplier, costed against the budget.

    Kept per candidate rather than folded into a single verdict because the
    interesting part of the answer is the runner-up: "3.0 was rejected by
    1.81 um2" is what tells a reader the cell is two sites short of being able
    to afford the fastest option, and a plan that reported only its winner
    could not say that.
    """

    multiplier: float
    #: The multiplier actually realisable in whole library fingers, which is
    #: what was costed.  2.5 is not drawable and is costed as 3.0.
    realised: float
    gate_columns: int
    sites: int
    area_um2: float
    fits: bool
    reason: str


@dc.dataclass(frozen=True)
class ResizePlan:
    """The chosen sizing, everything rejected on the way to it, and the sums."""

    cell: str
    new_cell: str
    source: Path
    devices: Tuple[DeviceSizing, ...]
    #: The stack multiplier actually chosen.  ``1.0`` when nothing was resized.
    multiplier: float
    #: Every multiplier evaluated, largest first.
    considered: Tuple[float, ...]
    #: The costing of each of those, in the same order.  Additive to the
    #: specified surface, and the only structured record of *why* a candidate
    #: lost; :func:`render_report` reads it rather than re-deriving it.
    candidates: Tuple[CandidateFit, ...]
    gate_columns: int
    estimated_sites: int
    estimated_area_um2: float
    #: The cap, when one was given.  ``None`` means no cap was given at all,
    #: which is a different statement from "the cap was large".
    area_budget_um2: Optional[float]
    #: How the cap was derived, in words a report can print unedited.
    budget_source: str
    notes: Tuple[str, ...]

    @property
    def changed_devices(self) -> Tuple[DeviceSizing, ...]:
        return tuple(d for d in self.devices if d.changed)

    @property
    def unchanged(self) -> bool:
        """True when no device moved -- whatever the reason."""
        return not self.changed_devices


# ---------------------------------------------------------------------------
# Topology: how deep is each device's stack
# ---------------------------------------------------------------------------


def _rails(subckt: Subckt) -> Tuple[str, str]:
    """Return ``(vdd, vss)``, refusing to guess when either is missing."""
    vdd, vss = subckt.vdd_net, subckt.vss_net
    if vdd is None or vss is None:
        raise ResizeError(
            f".subckt {subckt.name} declares pins {' '.join(subckt.pins)}; a "
            "series-stack depth is measured from a supply rail to an output, "
            "and this netlist names no VDD and/or no VSS pin to measure from"
        )
    return vdd, vss


def _terminals(device: Mosfet) -> Set[str]:
    """The two conducting terminals.  The bulk carries no signal current."""
    return {device.drain, device.source}


def stage_outputs(subckt: Subckt) -> Set[str]:
    """Return the nets a pull-up and a pull-down network meet at.

    A net that is a source/drain terminal of both a PMOS and an NMOS is where
    one CMOS stage ends, and it is where a stack depth stops being counted.
    That boundary is what keeps the inverter in front of a stack from being
    absorbed into it: ``I1_bar`` in the worked example is the inverter's output
    *and* the gate of the stack's top device, so the walk from VDD ends there
    and ``XP0`` keeps its own depth of 1 instead of inheriting the stack's 3.

    External non-rail pins that carry current are included too, so that a cell
    whose output pin happens to have no complementary device on it still has a
    place for the walk to stop.
    """
    rails = {subckt.vdd_net, subckt.vss_net}
    pmos_nets: Set[str] = set()
    nmos_nets: Set[str] = set()
    all_nets: Set[str] = set()
    for device in subckt.devices:
        terminals = _terminals(device)
        all_nets |= terminals
        if device.is_pmos:
            pmos_nets |= terminals
        elif device.is_nmos:
            nmos_nets |= terminals
    outputs = (pmos_nets & nmos_nets) | (all_nets & set(subckt.pins))
    return {net for net in outputs if net not in rails}


def _graph(devices: Sequence[Mosfet]) -> Dict[str, List[Tuple[str, Mosfet]]]:
    """Adjacency over nets, one undirected edge per conducting device."""
    graph: Dict[str, List[Tuple[str, Mosfet]]] = {}
    for device in devices:
        if device.drain == device.source:
            # A device with both terminals on one net conducts nothing in
            # series; counting it would inflate every depth through that net.
            continue
        graph.setdefault(device.drain, []).append((device.source, device))
        graph.setdefault(device.source, []).append((device.drain, device))
    return graph


def _network_depths(
    devices: Sequence[Mosfet],
    rail: str,
    outputs: Set[str],
) -> Dict[str, int]:
    """Longest rail-to-output series depth through each device in one network.

    Every node-simple path from ``rail`` is enumerated and stopped at the first
    stage output it reaches; each device on such a path is credited with that
    path's length, and keeps the largest credit it ever gets.  A device that is
    on no rail-to-output path at all comes back ``0`` rather than ``1``: it is
    not in series with anything because it is not in the conducting network,
    and reporting it as a 1-high stack would be a number where the honest
    answer is "this device does not switch the output".

    Exhaustive enumeration is affordable here because a standard cell has a
    handful of devices; :data:`MAX_WALK_STEPS` turns anything that is not one
    into a refusal rather than a hang.
    """
    depths: Dict[str, int] = {d.name: 0 for d in devices}
    graph = _graph(devices)
    if rail not in graph:
        return depths

    steps = 0
    chain: List[Mosfet] = []
    visited: Set[str] = {rail}

    def walk(node: str) -> None:
        nonlocal steps
        for neighbour, device in graph.get(node, ()):
            if neighbour in visited:
                continue
            steps += 1
            if steps > MAX_WALK_STEPS:
                raise ResizeError(
                    f"the conduction network at rail {rail!r} has more than "
                    f"{MAX_WALK_STEPS} distinct paths; this does not look like "
                    "a standard cell, and a stack depth guessed from a partial "
                    "walk would be worse than no answer at all"
                )
            chain.append(device)
            if neighbour in outputs:
                depth = len(chain)
                for member in chain:
                    if depth > depths[member.name]:
                        depths[member.name] = depth
            else:
                visited.add(neighbour)
                walk(neighbour)
                visited.discard(neighbour)
            chain.pop()

    walk(rail)
    return depths


def stack_depths(subckt: Subckt) -> Dict[str, int]:
    """Return each device's series depth: devices in series on its worst path.

    PMOS are walked from VDD and NMOS from VSS, each in its own network, so a
    cell built out of several stages reports each stage's own depth rather than
    the sum of all of them.  For the worked example this is exactly::

        {XP0: 1, XN0: 1, XP1: 3, XP2: 3, XP3: 3, XN1: 1, XN2: 1, XN3: 1}
    """
    vdd, vss = _rails(subckt)
    outputs = stage_outputs(subckt)
    if not outputs:
        raise ResizeError(
            f".subckt {subckt.name} has no net where a pull-up and a pull-down "
            "network meet and no external pin carrying current; there is no "
            "output for a stack depth to be measured to"
        )
    depths = _network_depths(subckt.pmos_devices, vdd, outputs)
    depths.update(_network_depths(subckt.nmos_devices, vss, outputs))
    for device in subckt.devices:
        depths.setdefault(device.name, 0)
    return depths


def _network_of(device: Mosfet) -> str:
    if device.is_pmos:
        return "pull-up"
    if device.is_nmos:
        return "pull-down"
    return "unknown"


# ---------------------------------------------------------------------------
# Sizing one candidate multiplier
# ---------------------------------------------------------------------------


def _round_half_up(value: float) -> int:
    """Round to nearest, ties away from zero.

    Python's built-in ``round`` is banker's rounding, which sends 2.5 to 2 and
    would make a 2.5x candidate a silent duplicate of the 2.0x one -- a
    multiplier that never over-delivers is not a distinct option, and a report
    listing both would be reporting the same cell twice.
    """
    return int(math.floor(value + 0.5))


def _size_device(
    device: Mosfet,
    depth: int,
    min_depth: int,
    multiplier: float,
    max_finger_w_nm: float,
) -> DeviceSizing:
    """Size one device for one candidate multiplier.

    Raises :class:`ResizeError` when the multiplier cannot be realised in whole
    fingers of a legal width on this device; the caller turns that into a
    rejected candidate rather than letting it escape.
    """
    network = _network_of(device)
    original_w = float(device.width_nm)
    original_ng = max(1, int(device.fingers))
    untouched = DeviceSizing(
        name=device.name,
        model=device.model,
        network=network,
        stack_depth=depth,
        original_w_nm=original_w,
        original_ng=original_ng,
        new_w_nm=original_w,
        new_ng=original_ng,
        multiplier=1.0,
        finger_w_nm=original_w / original_ng,
        reason="",
    )

    if network == "unknown":
        return dc.replace(
            untouched,
            reason=(
                f"model {device.model!r} is neither NMOS nor PMOS, so it sits "
                "in no pull-up or pull-down network and has no stack to widen"
            ),
        )
    if depth == 0:
        return dc.replace(
            untouched,
            reason=(
                "on no path from its supply rail to a stage output, so it is "
                "not in series with anything that switches the output"
            ),
        )
    if depth <= min_depth:
        return dc.replace(
            untouched,
            reason=(
                f"depth {depth} <= min_depth {min_depth}: the PDK leaves stacks "
                "this shallow at the library width (nand2_1, nor2_1, nor3_1 and "
                "nor4_1 are all w=1.12u PMOS), so widening it would disagree "
                "with the library this cell is placed beside"
            ),
        )

    if original_w <= 0:
        raise ResizeError(
            f"device {device.name} declares w={original_w}; a device with no "
            "width cannot be scaled by a multiplier"
        )

    finger_w = original_w / original_ng
    # `w` is the TOTAL width across `ng` fingers, so the multiplier acts on the
    # finger COUNT: k fingers of the library's own width, never a fraction of
    # one.  See sg13g2_nand2_2: w=2.24u ng=2 is two 1.12u fingers.
    k = _round_half_up(multiplier * original_ng)
    if k < 1:
        raise ResizeError(
            f"multiplier {multiplier} on {device.name} rounds to {k} fingers"
        )
    new_w = k * finger_w
    new_ng = max(k, math.ceil(new_w / max_finger_w_nm - 1e-9))
    new_finger_w = new_w / new_ng
    if abs(new_finger_w * new_ng - new_w) > WIDTH_TOL_NM:
        raise ResizeError(
            f"{device.name}: w={new_w:.4f}n does not divide into {new_ng} "
            "whole fingers"
        )
    if new_finger_w > max_finger_w_nm + WIDTH_TOL_NM:
        raise ResizeError(
            f"{device.name}: {new_ng} fingers of {new_finger_w:.1f}n exceed the "
            f"{max_finger_w_nm:.1f}n maximum finger width"
        )

    if k == original_ng:
        return dc.replace(
            untouched,
            reason=(
                f"depth {depth} > min_depth {min_depth}, but x{multiplier:g} "
                f"rounds to the {original_ng} finger(s) it already has"
            ),
        )
    return DeviceSizing(
        name=device.name,
        model=device.model,
        network=network,
        stack_depth=depth,
        original_w_nm=original_w,
        original_ng=original_ng,
        new_w_nm=new_w,
        new_ng=new_ng,
        multiplier=new_w / original_w,
        finger_w_nm=new_finger_w,
        reason=(
            f"depth {depth} > min_depth {min_depth}: series stack device "
            f"widened x{new_w / original_w:g} into {new_ng} finger(s) of "
            f"{_fmt_um(new_finger_w)}"
        ),
    )


def _gate_columns(
    subckt: Subckt,
    sizings: Sequence[DeviceSizing],
    multipliers: Optional[Dict[str, int]] = None,
) -> int:
    """Poly columns the two rows need: the finger sum of the wider row.

    The pull-up row and the pull-down row sit above and below each other and
    share their poly, so the cell is as wide as whichever row needs more
    fingers -- not as wide as their sum.
    """
    m_of = multipliers or {d.name: max(1, int(d.multiplier)) for d in subckt.devices}
    per_row: Dict[str, int] = {"pull-up": 0, "pull-down": 0, "unknown": 0}
    for sizing in sizings:
        per_row[sizing.network] = per_row.get(sizing.network, 0) + sizing.new_ng * m_of.get(
            sizing.name, 1
        )
    return max(per_row["pull-up"], per_row["pull-down"] + per_row["unknown"])


def estimate_width_nm(gate_columns: int) -> float:
    """Cell width for a row of ``gate_columns`` contacted poly columns, in nm."""
    return gate_columns * CONTACTED_POLY_PITCH_NM + 2 * DIFF_OVERHANG_NM


def estimate_sites(gate_columns: int) -> int:
    """Cell width in whole 0.48 um placement sites, always rounded up."""
    return int(math.ceil(estimate_width_nm(gate_columns) / SITE_WIDTH_NM - 1e-9))


def estimate_area_um2(sites: int) -> float:
    """Placement area of a ``sites``-wide single-row cell, in um^2."""
    return sites * SITE_WIDTH_UM * ROW_HEIGHT_UM


# ---------------------------------------------------------------------------
# The budget
# ---------------------------------------------------------------------------

#: Where the PDK LEF lives, inside the container only.  Tried after the GDS
#: because the committed ``context/gds`` prBoundaries need no container at all.
PDK_LEF_RELPATH = "libs.ref/sg13g2_stdcell/lef/sg13g2_stdcell.lef"


def _pdk_lef_path() -> Optional[Path]:
    """The container's standard-cell LEF, if this host happens to have it."""
    import os

    root, pdk = os.environ.get("PDK_ROOT"), os.environ.get("PDK")
    if not root or not pdk:
        return None
    path = Path(root) / pdk / PDK_LEF_RELPATH
    return path if path.is_file() else None


def baseline_area_um2(
    gate_netlist: Path | str,
    *,
    cell: Optional[str] = None,
    context_dir: Optional[Path | str] = None,
) -> Tuple[float, str]:
    """Return ``(area_um2, description)`` for the abutted PDK row.

    The widths come from each PDK cell's own prBoundary in ``context/gds``,
    which is committed and needs no container.  Only if a cell has no GDS here
    is the PDK LEF consulted, and only when this host actually has one -- a
    number quoted from a LEF that is not present is not a number.
    """
    from . import baseline as baseline_mod
    from . import metrics

    tool_dir = Path(__file__).resolve().parent.parent
    gds_dir = Path(context_dir) if context_dir else tool_dir / "context" / "gds"

    name, _ports, instances = baseline_mod.parse_gate_netlist(gate_netlist, cell)
    if not instances:
        raise ResizeError(f"{gate_netlist} instantiates no PDK cells")

    widths: List[Tuple[str, float, str]] = []
    missing: List[str] = []
    for instance in instances:
        gds = gds_dir / f"{instance.cell}.gds"
        if gds.is_file():
            geometry = metrics.gds_boundary(gds, instance.cell)
            widths.append((instance.cell, geometry.width_um, geometry.source))
        else:
            missing.append(instance.cell)

    if missing:
        lef = _pdk_lef_path()
        if lef is None:
            raise ResizeError(
                "no prBoundary available for "
                + ", ".join(sorted(set(missing)))
                + f" (looked in {gds_dir}), and no PDK LEF at $PDK_ROOT/$PDK/"
                + PDK_LEF_RELPATH
                + " to fall back on; the abutted area cannot be measured"
            )
        measured = metrics.pdk_lef_geometry(sorted(set(missing)), lef)
        for instance in instances:
            if instance.cell in measured:
                widths.append(
                    (instance.cell, measured[instance.cell].width_um, "lef")
                )

    total_um = sum(width for _cell, width, _source in widths)
    area = total_um * ROW_HEIGHT_UM
    sources = sorted({source for _c, _w, source in widths})
    detail = " + ".join(f"{c} {w:.3f}" for c, w, _s in widths)
    description = (
        f"the abutted PDK row of {name}: {detail} = {total_um:.3f} um wide "
        f"({total_um / SITE_WIDTH_UM:.0f} sites) x {ROW_HEIGHT_UM} um "
        f"= {area:.4f} um^2, measured from {'/'.join(sources)}"
    )
    return area, description


@dc.dataclass(frozen=True)
class _Budget:
    """The area cap, and whether the cell must beat it or merely meet it."""

    area_um2: Optional[float]
    #: True when the cap is a rival to beat (the abutted row) rather than an
    #: allowance the caller granted; a tie with the thing you are replacing is
    #: not a win, but a tie with your own ``--max-sites 9`` is what you asked
    #: for.
    strict: bool
    source: str

    def admits(self, area_um2: float) -> bool:
        if self.area_um2 is None:
            return True
        if self.strict:
            return area_um2 < self.area_um2 - 1e-9
        return area_um2 <= self.area_um2 + 1e-9

    def overshoot(self, area_um2: float) -> float:
        return 0.0 if self.area_um2 is None else area_um2 - self.area_um2


def _resolve_budget(
    max_sites: Optional[int],
    area_budget_um2: Optional[float],
    baseline: Optional[Path | str],
    notes: List[str],
) -> _Budget:
    """Pick the cap, most explicitly stated first, and say which one won."""
    given = [
        name
        for name, value in (
            ("--area-budget", area_budget_um2),
            ("--max-sites", max_sites),
            ("--baseline", baseline),
        )
        if value is not None
    ]
    if len(given) > 1:
        notes.append(
            "more than one area cap was given ("
            + ", ".join(given)
            + f"); the most explicitly stated one, {given[0]}, was used"
        )

    if area_budget_um2 is not None:
        if area_budget_um2 <= 0:
            raise ResizeError(f"area_budget_um2 must be positive, got {area_budget_um2}")
        return _Budget(
            area_um2=float(area_budget_um2),
            strict=False,
            source=f"{area_budget_um2:.4f} um^2, given directly as the cap",
        )
    if max_sites is not None:
        if max_sites <= 0:
            raise ResizeError(f"max_sites must be positive, got {max_sites}")
        area = estimate_area_um2(int(max_sites))
        return _Budget(
            area_um2=area,
            strict=False,
            source=(
                f"{max_sites} sites given as the cap: {max_sites} x "
                f"{SITE_WIDTH_UM} x {ROW_HEIGHT_UM} = {area:.4f} um^2"
            ),
        )
    if baseline is not None:
        area, description = baseline_area_um2(baseline)
        return _Budget(area_um2=area, strict=True, source=description)
    return _Budget(
        area_um2=None,
        strict=False,
        source=(
            "no area cap was given, so every candidate fits and the largest "
            "multiplier was taken; pass --baseline, --max-sites or "
            "--area-budget to make this an area-constrained choice"
        ),
    )


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


def _normalise_multipliers(multipliers: Optional[Iterable[float]]) -> Tuple[float, ...]:
    """Sort the candidates largest first, refusing ones that shrink the cell."""
    values = tuple(DEFAULT_MULTIPLIERS if multipliers is None else multipliers)
    if not values:
        raise ResizeError("no candidate multipliers were given")
    out: List[float] = []
    for value in values:
        number = float(value)
        if number < 1.0:
            raise ResizeError(
                f"multiplier {number} would make the stack narrower than the "
                "library width; resize widens a stack, it does not shrink one"
            )
        if number not in out:
            out.append(number)
    return tuple(sorted(out, reverse=True))


def _subckt_of(netlist: Path, cell: Optional[str]) -> Subckt:
    """Return the named subckt, or the only one, refusing to pick for you."""
    subckts = parse_spice_file(netlist)
    if not subckts:
        raise ResizeError(f"no .subckt found in {netlist}")
    if cell is None:
        return subckts[0]
    for subckt in subckts:
        if subckt.name == cell:
            return subckt
    raise ResizeError(
        f"{netlist} defines no .subckt {cell!r}; it defines: "
        + ", ".join(s.name for s in subckts)
    )


def plan_resize(
    netlist: Path | str,
    *,
    cell: Optional[str] = None,
    min_depth: int = 2,
    multipliers: Optional[Iterable[float]] = None,
    max_sites: Optional[int] = None,
    area_budget_um2: Optional[float] = None,
    baseline: Optional[Path | str] = None,
    max_finger_w_nm: float = DEFAULT_MAX_FINGER_W_NM,
    new_cell: Optional[str] = None,
) -> ResizePlan:
    """Choose the largest stack multiplier the area budget can afford.

    Nothing is written; the plan is a value the caller can print, assert on, or
    hand to :func:`write_resized_netlist`.
    """
    source = Path(netlist)
    if not source.is_file():
        raise ResizeError(f"no netlist at {source}")
    if min_depth < 1:
        raise ResizeError(f"min_depth must be at least 1, got {min_depth}")
    if max_finger_w_nm <= 0:
        raise ResizeError(f"max_finger_w_nm must be positive, got {max_finger_w_nm}")

    subckt = _subckt_of(source, cell)
    if not subckt.devices:
        raise ResizeError(f".subckt {subckt.name} in {source} contains no devices")

    notes: List[str] = []
    depths = stack_depths(subckt)
    budget = _resolve_budget(max_sites, area_budget_um2, baseline, notes)
    candidates = _normalise_multipliers(multipliers)
    m_of = {d.name: max(1, int(d.multiplier)) for d in subckt.devices}

    # x1.0: the cell as it stands.  Costed first, because it is both the
    # fallback and the number every candidate's overshoot is read against.
    unchanged_sizings = tuple(
        _size_device(d, depths[d.name], min_depth, 1.0, max_finger_w_nm)
        for d in subckt.devices
    )
    base_columns = _gate_columns(subckt, unchanged_sizings, m_of)
    base_sites = estimate_sites(base_columns)
    base_area = estimate_area_um2(base_sites)

    deep = [d for d in subckt.devices if depths[d.name] > min_depth]
    if not deep:
        deepest = max(depths.values()) if depths else 0
        notes.append(
            f"no device sits in a stack deeper than {min_depth} (the deepest is "
            f"{deepest}), so there is nothing this rule would widen; the cell "
            "is left at the library width"
        )
        return ResizePlan(
            cell=subckt.name,
            new_cell=new_cell or f"{subckt.name}s",
            source=source,
            devices=unchanged_sizings,
            multiplier=1.0,
            considered=candidates,
            candidates=(),
            gate_columns=base_columns,
            estimated_sites=base_sites,
            estimated_area_um2=base_area,
            area_budget_um2=budget.area_um2,
            budget_source=budget.source,
            notes=tuple(notes),
        )

    fits: List[CandidateFit] = []
    chosen: Optional[Tuple[CandidateFit, Tuple[DeviceSizing, ...]]] = None
    for multiplier in candidates:
        try:
            sizings = tuple(
                _size_device(d, depths[d.name], min_depth, multiplier, max_finger_w_nm)
                for d in subckt.devices
            )
        except ResizeError as exc:
            fits.append(
                CandidateFit(
                    multiplier=multiplier,
                    realised=float("nan"),
                    gate_columns=0,
                    sites=0,
                    area_um2=float("nan"),
                    fits=False,
                    reason=f"not drawable in whole library fingers: {exc}",
                )
            )
            continue

        columns = _gate_columns(subckt, sizings, m_of)
        sites = estimate_sites(columns)
        area = estimate_area_um2(sites)
        changed = [s for s in sizings if s.changed]
        realised = max((s.multiplier for s in changed), default=1.0)
        admitted = budget.admits(area)
        if not changed:
            reason = (
                f"x{multiplier:g} rounds to the finger count every device "
                "already has, so it is not a distinct cell"
            )
            admitted = False
        elif admitted:
            reason = (
                f"fits: {columns} columns -> {sites} sites -> {area:.4f} um^2"
                + (
                    ""
                    if budget.area_um2 is None
                    else f", {budget.area_um2 - area:.4f} um^2 under the budget"
                )
            )
        else:
            over = budget.overshoot(area)
            reason = (
                f"rejected: {columns} columns -> {sites} sites -> {area:.4f} "
                f"um^2, {over:+.4f} um^2 against the "
                f"{budget.area_um2:.4f} um^2 budget"
                if budget.area_um2 is not None
                else "rejected"
            )
        fit = CandidateFit(
            multiplier=multiplier,
            realised=realised,
            gate_columns=columns,
            sites=sites,
            area_um2=area,
            fits=admitted,
            reason=reason,
        )
        fits.append(fit)
        if admitted and chosen is None:
            chosen = (fit, sizings)

    if chosen is None:
        rejected = "; ".join(
            f"x{f.multiplier:g} -> {f.sites} sites {f.area_um2:.4f} um^2 "
            f"({budget.overshoot(f.area_um2):+.4f} um^2)"
            for f in fits
            if f.sites
        )
        notes.append(
            "every candidate multiplier was rejected"
            + (
                f" against the {budget.area_um2:.4f} um^2 budget"
                if budget.area_um2 is not None
                else ""
            )
            + (f": {rejected}" if rejected else "")
        )
        notes.append(
            "the cell is left at the library width: it cannot be made faster "
            "without giving up the area win that is the reason it exists"
        )
        return ResizePlan(
            cell=subckt.name,
            new_cell=new_cell or f"{subckt.name}s",
            source=source,
            devices=unchanged_sizings,
            multiplier=1.0,
            considered=candidates,
            candidates=tuple(fits),
            gate_columns=base_columns,
            estimated_sites=base_sites,
            estimated_area_um2=base_area,
            area_budget_um2=budget.area_um2,
            budget_source=budget.source,
            notes=tuple(notes),
        )

    fit, sizings = chosen
    changed = [s for s in sizings if s.changed]
    notes.append(
        f"widened {len(changed)} device(s) in a stack deeper than {min_depth}: "
        + ", ".join(s.name for s in changed)
    )
    notes.append(
        f"the cell grows from {base_sites} sites ({base_area:.4f} um^2) to "
        f"{fit.sites} sites ({fit.area_um2:.4f} um^2)"
        + (
            ""
            if budget.area_um2 is None
            else f", still {budget.area_um2 - fit.area_um2:.4f} um^2 inside the budget"
        )
    )
    if any(s.changed and _has_geometry_params(s) for s in sizings):
        pass  # reported by write_resized_netlist, which sees the raw text
    return ResizePlan(
        cell=subckt.name,
        new_cell=new_cell or f"{subckt.name}s",
        source=source,
        devices=sizings,
        multiplier=fit.realised,
        considered=candidates,
        candidates=tuple(fits),
        gate_columns=fit.gate_columns,
        estimated_sites=fit.sites,
        estimated_area_um2=fit.area_um2,
        area_budget_um2=budget.area_um2,
        budget_source=budget.source,
        notes=tuple(notes),
    )


def _has_geometry_params(_sizing: DeviceSizing) -> bool:
    """Placeholder: the raw parameters live in the text, not in the plan."""
    return False


# ---------------------------------------------------------------------------
# Emitting the resized netlist
# ---------------------------------------------------------------------------

_SUBCKT_RE = re.compile(r"^(\s*)(\.subckt)(\s+)(\S+)(\s*)(.*)$", re.IGNORECASE)
_ENDS_RE = re.compile(r"^\s*\.ends\b", re.IGNORECASE)


def _fmt_um(nm: float) -> str:
    """Format a width in nm the way the PDK writes it: micrometres, e.g. 2.24u."""
    text = f"{nm / 1000.0:.6f}".rstrip("0").rstrip(".")
    return f"{text or '0'}u"


def _rewrite_device_line(line: str, sizing: DeviceSizing) -> Tuple[str, List[str]]:
    """Return ``(line, dropped)`` with ``w``/``ng`` updated in place.

    Everything else on the line keeps its original spelling, with one exception
    that is deliberate: ``ad``/``as``/``pd``/``ps`` and friends describe the
    diffusion geometry of the *original* width and are simply wrong at the new
    one.  Carrying them forward would hand the simulator a precise, confident,
    incorrect number; dropping them lets the model compute from ``w`` and lets
    PEX supply the real ones.  They are returned so the caller can say so.
    """
    dropped: List[str] = []
    tokens = line.split()
    indent = line[: len(line) - len(line.lstrip())]
    out: List[str] = []
    saw_ng = False
    for index, token in enumerate(tokens):
        if index == 0 or "=" not in token:
            out.append(token)
            continue
        key, _, _value = token.partition("=")
        low = key.lower()
        if low == "w":
            out.append(f"{key}={_fmt_um(sizing.new_w_nm)}")
        elif low == "ng":
            saw_ng = True
            out.append(f"{key}={sizing.new_ng}")
        elif low in GEOMETRY_PARAMS:
            dropped.append(token)
        else:
            out.append(token)
    if not saw_ng and sizing.new_ng != 1:
        # No ng= to update: insert one after l=, where the PDK writes it.
        position = len(out)
        for index, token in enumerate(out):
            if token.lower().startswith("l="):
                position = index + 1
                break
        out.insert(position, f"ng={sizing.new_ng}")
    return indent + " ".join(out), dropped


def _header(plan: ResizePlan, dropped: Dict[str, List[str]]) -> List[str]:
    """The comment block that stops this file being mistaken for a hand edit."""
    lines = [
        "*" * 72,
        "* GENERATED by `python3 -m aion_layout resize` -- do not edit by hand.",
        "*",
        f"* source:     {plan.source}",
        f"* cell:       {plan.cell}  ->  {plan.new_cell}",
    ]
    if plan.unchanged:
        lines += [
            "*",
            "* NO DEVICE WAS RESIZED.  This is a renamed copy of the source "
            "netlist,",
            "* emitted so the flow has a named file; it is electrically the "
            "same cell.",
        ]
    else:
        lines.append(
            f"* multiplier: x{plan.multiplier:g} on every device in a series "
            f"stack deeper than {_min_depth_of(plan)}"
        )
        lines.append(
            f"* area:       {plan.gate_columns} poly columns -> "
            f"{plan.estimated_sites} sites -> {plan.estimated_area_um2:.4f} um^2"
        )
        if plan.area_budget_um2 is not None:
            lines.append(f"* budget:     {plan.area_budget_um2:.4f} um^2")
        lines.append(f"* budget src: {plan.budget_source}")
        lines.append("*")
        lines.append("* changed devices:")
        for sizing in plan.changed_devices:
            lines.append(
                f"*   {sizing.name:<6} depth {sizing.stack_depth} {sizing.network:<9} "
                f"w {_fmt_um(sizing.original_w_nm)} -> {_fmt_um(sizing.new_w_nm)}   "
                f"ng {sizing.original_ng} -> {sizing.new_ng}   "
                f"({sizing.new_ng} x {_fmt_um(sizing.finger_w_nm)})"
            )
    if dropped:
        lines.append("*")
        lines.append(
            "* the following per-device geometry parameters described the "
            "ORIGINAL width"
        )
        lines.append(
            "* and would be wrong at the new one, so they were dropped rather "
            "than carried:"
        )
        for name in sorted(dropped):
            lines.append(f"*   {name}: {' '.join(dropped[name])}")
    lines.append("*" * 72)
    return lines


def _min_depth_of(plan: ResizePlan) -> int:
    """Recover the depth threshold from the sizings, for the header text."""
    resized = [d.stack_depth for d in plan.changed_devices]
    spared = [d.stack_depth for d in plan.devices if not d.changed and d.stack_depth]
    if not resized:
        return 0
    below = [d for d in spared if d < min(resized)]
    return max(below) if below else min(resized) - 1


def write_resized_netlist(plan: ResizePlan, out_path: Path | str) -> Path:
    """Write the resized netlist beside the original, never over it.

    The input netlist is what LVS grades the layout against.  A resize that
    edited it in place would leave every later check comparing the layout to a
    netlist that had silently moved underneath it, so the resolved paths are
    compared and an attempt to write over the source is refused outright.
    """
    out = Path(out_path)
    try:
        same = out.resolve() == plan.source.resolve()
    except OSError as exc:  # pragma: no cover - unreadable path
        raise ResizeError(f"cannot resolve {out}: {exc}") from exc
    if same:
        raise ResizeError(
            f"refusing to write the resized netlist over its own input "
            f"({plan.source}); the input netlist is what LVS grades the layout "
            "against, and a resize that edited it in place would make every "
            "later verification meaningless -- write to a different file"
        )
    if out.is_dir():
        raise ResizeError(f"{out} is a directory, not a netlist file")

    text = plan.source.read_text(errors="replace")
    by_name = {d.name: d for d in plan.devices}

    body: List[str] = []
    dropped: Dict[str, List[str]] = {}
    inside = False
    found = False
    for raw in text.splitlines():
        if not inside:
            match = _SUBCKT_RE.match(raw)
            if match and match.group(4) == plan.cell:
                inside = True
                found = True
                body.append(
                    f"{match.group(1)}{match.group(2)}{match.group(3)}"
                    f"{plan.new_cell}{match.group(5)}{match.group(6)}".rstrip()
                )
            continue
        if raw.lstrip().startswith("+"):
            raise ResizeError(
                f"{plan.source}: line continuation {raw.strip()!r} inside "
                f".subckt {plan.cell}; this writer rewrites one device per line "
                "and will not silently reflow a continued one"
            )
        if _ENDS_RE.match(raw):
            body.append(raw.rstrip())
            inside = False
            continue
        name = raw.split()[0] if raw.split() else ""
        sizing = by_name.get(name)
        if sizing is not None and sizing.changed:
            line, gone = _rewrite_device_line(raw, sizing)
            body.append(line)
            if gone:
                dropped[name] = gone
        else:
            body.append(raw.rstrip())

    if not found:
        raise ResizeError(
            f"{plan.source} has no `.subckt {plan.cell}` line to rewrite"
        )
    if inside:
        raise ResizeError(f"{plan.source}: .subckt {plan.cell} has no .ends")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(_header(plan, dropped) + body) + "\n")
    return out


# ---------------------------------------------------------------------------
# The report -- a deliverable, not a debug print
# ---------------------------------------------------------------------------


def summary_line(plan: ResizePlan) -> str:
    """One machine-readable line, at column 0, saying what was chosen.

    Whitespace inside every name is collapsed: the cell name reaches here from
    a command line, and a newline smuggled into it would turn one verdict line
    into two.
    """
    cell = " ".join(str(plan.cell).split())
    new_cell = " ".join(str(plan.new_cell).split())
    if plan.unchanged:
        if plan.area_budget_um2 is None:
            why = "no device sits in a stack deep enough to widen"
        elif plan.candidates:
            why = (
                f"no multiplier fits the {plan.area_budget_um2:.3f} um2 budget"
            )
        else:
            why = (
                f"no device sits in a stack deep enough to widen "
                f"(budget {plan.area_budget_um2:.3f} um2)"
            )
        return f"RESIZE: {cell} unchanged  {why}"
    budget = (
        ""
        if plan.area_budget_um2 is None
        else f" (budget {plan.area_budget_um2:.3f})"
    )
    return (
        f"RESIZE: {cell} -> {new_cell}  x{plan.multiplier:g} on "
        f"{len(plan.changed_devices)} device(s), {plan.gate_columns} columns, "
        f"{plan.estimated_sites} sites, {plan.estimated_area_um2:.3f} um2{budget}"
    )


def _table(rows: Sequence[Sequence[str]], head: Sequence[str]) -> List[str]:
    """A markdown table, padded so the source is readable as plain text too."""
    widths = [len(h) for h in head]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    def line(cells: Sequence[str]) -> str:
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"
    out = [line(head), "|" + "|".join("-" * (w + 2) for w in widths) + "|"]
    out += [line(row) for row in rows]
    return out


def render_report(plan: ResizePlan) -> str:
    """Render the resize decision as markdown.

    This is the deliverable the user asked for: a cell that came back a
    different size has to *say* so, with the arithmetic that chose the size, or
    the next reader has no way to tell a considered decision from a typo.
    """
    lines: List[str] = [
        f"# Resize: {plan.cell}",
        "",
        f"- source netlist: `{plan.source}`",
        f"- resized cell:   `{plan.new_cell}`",
    ]
    if plan.unchanged:
        lines.append("- **outcome: unchanged** -- no device was resized")
    else:
        lines.append(
            f"- **outcome: x{plan.multiplier:g} on "
            f"{len(plan.changed_devices)} device(s)**"
        )
    lines += [
        f"- estimated size: {plan.gate_columns} poly columns, "
        f"{plan.estimated_sites} sites, {plan.estimated_area_um2:.4f} um^2",
        (
            "- area budget:    none given"
            if plan.area_budget_um2 is None
            else f"- area budget:    {plan.area_budget_um2:.4f} um^2"
        ),
        f"- budget source:  {plan.budget_source}",
        "",
        "## Why",
        "",
        "A device in a deep series stack drives the output through every "
        "device above it, so the stack's on-resistance -- and the transition "
        "it is the limiter of -- scales with its depth.  Widening only those "
        "devices buys the speed back; widening everything would spend area on "
        "devices that were never the limit.  Devices at depth "
        f"{_min_depth_of(plan) or plan_min_depth_default()} or less are left "
        "at the library width because the PDK leaves its own that way.",
        "",
        "## Devices",
        "",
    ]
    rows = [
        [
            d.name,
            d.network,
            str(d.stack_depth),
            f"{_fmt_um(d.original_w_nm)} -> {_fmt_um(d.new_w_nm)}",
            f"{d.original_ng} -> {d.new_ng}",
            f"x{d.multiplier:g}",
            d.reason,
        ]
        for d in plan.devices
    ]
    lines += _table(
        rows, ["device", "network", "depth", "w", "ng", "mult", "reason"]
    )

    lines += ["", "## Multipliers considered", ""]
    if plan.candidates:
        lines += _table(
            [
                [
                    f"x{f.multiplier:g}",
                    ("-" if f.sites == 0 else str(f.gate_columns)),
                    ("-" if f.sites == 0 else str(f.sites)),
                    ("-" if f.sites == 0 else f"{f.area_um2:.4f}"),
                    "CHOSEN" if (f.fits and f.multiplier == _chosen_of(plan)) else
                    ("fits" if f.fits else "rejected"),
                    f.reason,
                ]
                for f in plan.candidates
            ],
            ["mult", "columns", "sites", "um^2", "verdict", "detail"],
        )
    else:
        lines.append(
            "None were costed: no device sits in a stack deep enough for this "
            "rule to widen, so the multiplier never came into it."
        )

    lines += [
        "",
        "## Area arithmetic",
        "",
        f"- contacted poly pitch: {CONTACTED_POLY_PITCH_NM:.0f} nm "
        "(110 contact-to-gate + 160 contact + 110 contact-to-gate + 130 gate)",
        f"- diffusion overhang:   {DIFF_OVERHANG_NM:.0f} nm at each end",
        f"- columns:              {plan.gate_columns} "
        "(the finger sum of the wider of the two rows; the rows share poly)",
        f"- width:                {plan.gate_columns} x "
        f"{CONTACTED_POLY_PITCH_NM:.0f} + 2 x {DIFF_OVERHANG_NM:.0f} = "
        f"{estimate_width_nm(plan.gate_columns):.0f} nm",
        f"- sites:                ceil({estimate_width_nm(plan.gate_columns):.0f} "
        f"/ {SITE_WIDTH_NM:.0f}) = {plan.estimated_sites}",
        f"- area:                 {plan.estimated_sites} x {SITE_WIDTH_UM} x "
        f"{ROW_HEIGHT_UM} = {plan.estimated_area_um2:.4f} um^2",
    ]
    if plan.area_budget_um2 is not None:
        margin = plan.area_budget_um2 - plan.estimated_area_um2
        lines.append(
            f"- against the budget:   {plan.estimated_area_um2:.4f} vs "
            f"{plan.area_budget_um2:.4f} um^2 -> {margin:+.4f} um^2"
        )

    lines += ["", "## Notes", ""]
    lines += [f"- {note}" for note in plan.notes] or ["- (none)"]
    lines += ["", "```", summary_line(plan), "```", ""]
    return "\n".join(lines)


def plan_min_depth_default() -> int:
    """The default depth threshold, for report text that has no plan to read."""
    return 2


def _chosen_of(plan: ResizePlan) -> float:
    """The candidate multiplier that won, as it was requested (not realised)."""
    for fit in plan.candidates:
        if fit.fits:
            return fit.multiplier
    return float("nan")


def write_report(plan: ResizePlan, path: Path | str) -> Path:
    """Write :func:`render_report` to ``path`` and return it."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(plan))
    return out


def resize(
    netlist: Path | str,
    out_path: Path | str,
    *,
    report: Optional[Path | str] = None,
    **plan_kwargs,
) -> ResizePlan:
    """Plan, write the resized netlist, optionally write the report."""
    plan = plan_resize(netlist, **plan_kwargs)
    write_resized_netlist(plan, out_path)
    if report is not None:
        write_report(plan, report)
    return plan


__all__ = [
    "CONTACTED_POLY_PITCH_NM",
    "DEFAULT_MAX_FINGER_W_NM",
    "DEFAULT_MULTIPLIERS",
    "DIFF_OVERHANG_NM",
    "SITE_WIDTH_NM",
    "CandidateFit",
    "DeviceSizing",
    "ResizeError",
    "ResizePlan",
    "baseline_area_um2",
    "estimate_area_um2",
    "estimate_sites",
    "estimate_width_nm",
    "plan_resize",
    "render_report",
    "resize",
    "stack_depths",
    "stage_outputs",
    "summary_line",
    "write_report",
    "write_resized_netlist",
]
