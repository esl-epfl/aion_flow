# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Publish the cell's views, and refuse a bad one
# ================================================================

"""The views a place-and-route flow consumes, and the gate that guards them.

Everything here exists because of one asymmetry: a view that is merely *absent*
costs an hour, and a view that is *wrong* costs a place-and-route run that dies
at detailed placement with an error naming a row, not a cell.  ``output_constr``
lists five properties -- ``CLASS CORE``, ``SITE CoreSite``, the row height, the
site pitch, and the two power pins -- that no earlier step of the flow can
catch, because DRC and LVS both pass happily on a cell that is 3.79 um tall.  So
:func:`check_lef` is a hard gate, it reports *every* violated property rather
than the first, and :func:`export_all` refuses to publish rather than emit a
directory that looks finished.

Two things Magic does that this module has to correct, and one it must not:

* Magic writes ``CLASS BLOCK ;`` for a cell it read from GDS, because nothing in
  the GDS says the cell is a core cell.  OpenROAD reads ``BLOCK`` as a macro and
  hard-blocks the area under it.
* Magic writes no ``SITE`` line at all, for the same reason.

Both are *declarations* about how the cell is meant to be used, and the flow
knows the answer: this is a single-row core cell.  Rewriting them is honest, and
every rewrite is recorded as a ``#`` comment at the top of the LEF so that a
human reading the file can see the tool did not write it unaided.

``SIZE`` is different.  It is a *measurement*, and two artifacts measure it
independently -- the LEF Magic wrote and the prBoundary in the GDS.  When they
disagree one of them is lying about the cell, and no repair to either is
defensible, so :func:`export_lef` raises and renames the LEF out of the way of
anything globbing ``*.lef``.
"""

from __future__ import annotations

import dataclasses as dc
import re
import shlex
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, NoReturn, Optional, Sequence, Tuple

from . import metrics
from .liberty import LibertyError, read_liberty
from .logic import LogicError, TruthTable, truth_table
from .metrics import GRID_TOL_UM, CellGeometry, MetricsError
from .runner import DEFAULT_TIMEOUT, rel_to_tool, run_in_container
from .spice_parser import SpiceParseError, Subckt, parse_spice_file


class ExportError(RuntimeError):
    """Raised when a view cannot be produced, or must not be published."""


#: Pin names the reference flow treats as supplies rather than signals.  They go
#: inside ``\`ifdef USE_POWER_PINS`` in the Verilog model, which is how a
#: gate-level netlist stays simulatable both with and without power nets.
DEFAULT_POWER_PINS: Tuple[str, ...] = ("VDD", "VSS", "VPWR", "VGND", "VNB", "VPB")

#: What ``output_constr.md`` requires of a core cell's LEF macro.
REQUIRED_CLASS = "CORE"
REQUIRED_SITE = "CoreSite"

#: A single-row core cell must be flippable, or the detailed placer can only put
#: it in the un-flipped half of the rows.  Every sg13g2 standard cell declares
#: exactly this; magic declares nothing, because a GDS says nothing about it.
REQUIRED_SYMMETRY = "X Y"

#: LEF spells port directions in upper case; the Verilog model spells them lower.
_LEF_DIRECTION = {"input": "INPUT", "output": "OUTPUT", "inout": "INOUT"}

#: Directions a Verilog port may be declared with.
_VERILOG_DIRECTIONS = ("input", "output", "inout")

#: The PDK's own cell models declare ``1ns / 10ps`` and the SDF the flow writes
#: is in ns.  A file with no timescale next to files that have one is a
#: simulator warning at best and a silently rescaled delay at worst.
_TIMESCALE = "`timescale 1ns / 10ps"

_CLASS_RE = re.compile(r"^[ \t]*CLASS[ \t]+([^;]*?)[ \t]*;", re.MULTILINE)
_SITE_RE = re.compile(r"^[ \t]*SITE[ \t]+(\S+)[ \t]*;", re.MULTILINE)
_PIN_RE = re.compile(r"^[ \t]*PIN[ \t]+(\S+)", re.MULTILINE)
_SIZE_LINE_RE = re.compile(r"^[ \t]*SIZE[ \t]+[^;]*;[ \t]*$", re.MULTILINE)
_MACRO_LINE_RE = re.compile(r"^[ \t]*MACRO[ \t]+\S+[ \t]*$", re.MULTILINE)
_SYMMETRY_RE = re.compile(r"^[ \t]*SYMMETRY[ \t]+[^;]*;", re.MULTILINE)
_PIN_OPEN_RE = re.compile(r"^([ \t]*)PIN[ \t]+(\S+)[ \t]*$")
_PIN_CLOSE_RE = re.compile(r"^[ \t]*END[ \t]+(\S+)[ \t]*$")
_DIRECTION_RE = re.compile(r"^[ \t]*DIRECTION[ \t]+\S+[ \t]*;")
_USE_RE = re.compile(r"^[ \t]*USE[ \t]+(\S+)[ \t]*;")

_SUBCKT_RE = re.compile(r"^[ \t]*\.subckt[ \t]+(\S+)[ \t]*(.*)$", re.IGNORECASE)
_ENDS_RE = re.compile(r"^([ \t]*)\.ends\b", re.IGNORECASE)
_DOT_SUBCKT_RE = re.compile(r"^([ \t]*)\.subckt\b", re.IGNORECASE)

#: How many lines of a tool's output an error message quotes.
_MAX_QUOTED_LINES = 40


def _indent_block(text: str, prefix: str = "  | ") -> str:
    """Indent captured tool output so none of its lines can pass for a verdict."""
    lines = str(text).splitlines()[-_MAX_QUOTED_LINES:]
    if not lines:
        lines = ["(no output)"]
    return "\n".join(prefix + line for line in lines)


def _readable(path: Path, what: str) -> Path:
    """Return ``path`` after proving it exists and carries bytes.

    An empty file is the shape a shell redirection leaves behind when the tool
    it redirected never ran, so "the file is there" is not evidence on its own.
    """
    if not path.is_file():
        raise ExportError(f"no {what} at {path}")
    if path.stat().st_size == 0:
        raise ExportError(f"{what} at {path} is empty")
    return path


def _copy_view(src: Path | str, dst: Path, what: str) -> Path:
    """Copy one view into the publish directory, verifying the copy landed."""
    source = _readable(Path(src), what)
    destination = Path(dst)
    if source.resolve() == destination.resolve():
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if not destination.is_file() or destination.stat().st_size != source.stat().st_size:
        raise ExportError(
            f"copying the {what} to {destination} did not reproduce it "
            f"({source.stat().st_size} bytes in, "
            f"{destination.stat().st_size if destination.is_file() else 'no file'} out)"
        )
    return destination


def _reject(lef: Path, reason: str) -> NoReturn:
    """Move a LEF out of the way of ``*.lef`` discovery, then raise.

    The file is kept -- it is the evidence for the reason -- but under a name no
    place-and-route flow will pick up, because a rejected LEF left in a publish
    directory is exactly the trap this module exists to close.
    """
    quarantined = lef.with_suffix(lef.suffix + ".rejected")
    if quarantined.exists():
        quarantined.unlink()
    lef.rename(quarantined)
    raise ExportError(f"{reason}\nthe rejected LEF is kept at {quarantined}")


# ---------------------------------------------------------------------------
# LEF
# ---------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class LefCheck:
    """The verdict ``make pnr`` would reach on this LEF, and why.

    ``problems`` is empty only when every requirement in ``output_constr.md``
    held.  It lists all of them rather than stopping at the first, because a
    cell that is both the wrong height and missing its site needs one edit to
    the generator, not two rounds of export.
    """

    ok: bool
    problems: Tuple[str, ...]
    geometry: CellGeometry
    pins: Tuple[str, ...]
    #: The ``CLASS`` found in the macro, or ``""`` when there is no CLASS line.
    cell_class: str
    #: The ``SITE`` found in the macro, or ``""`` when there is no SITE line.
    site: str

    def describe(self) -> str:
        """One line for a verdict block, plus one line per problem."""
        head = (
            f"LEF {self.geometry.cell}: "
            f"{'OK' if self.ok else str(len(self.problems)) + ' problem(s)'}; "
            f"CLASS {self.cell_class or '(none)'}, SITE {self.site or '(none)'}, "
            f"{self.geometry.width_um:.3f} x {self.geometry.height_um:.3f} um, "
            f"pins {' '.join(self.pins) or '(none)'}"
        )
        return "\n".join([head] + [f"  - {p}" for p in self.problems])


def _pin_directions(
    body: str, directions: Mapping[str, str]
) -> Tuple[str, Tuple[str, ...]]:
    """Give every PIN block a ``DIRECTION``, and say which ones were declared.

    Magic writes no ``DIRECTION`` at all, and a LEF pin without one is read by
    OpenROAD as an input -- so an output pin published this way is invisible to
    the resizer and to timing.  Two sources are honest enough to act on: the
    ``directions`` map the caller supplies, and the ``USE POWER``/``USE GROUND``
    line magic *does* write, which fixes a supply at ``INOUT``.  A signal pin
    with neither is left alone rather than guessed at.
    """
    notes: List[str] = []
    lines = body.splitlines()
    out: List[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        out.append(line)
        opening = _PIN_OPEN_RE.match(line)
        if opening is None:
            index += 1
            continue

        indent, name = opening.group(1), opening.group(2)
        end = index + 1
        while end < len(lines):
            closing = _PIN_CLOSE_RE.match(lines[end])
            if closing is not None and closing.group(1) == name:
                break
            end += 1
        block = lines[index + 1 : end]

        if any(_DIRECTION_RE.match(entry) for entry in block):
            declared = None
        elif name in directions:
            declared = _LEF_DIRECTION[directions[name]]
        else:
            uses = [
                match.group(1).upper()
                for match in (_USE_RE.match(entry) for entry in block)
                if match is not None
            ]
            declared = "INOUT" if {"POWER", "GROUND"} & set(uses) else None

        if declared is not None:
            out.append(f"{indent}  DIRECTION {declared} ;")
            notes.append(
                f"inserted 'DIRECTION {declared} ;' on PIN {name}: magic writes no "
                "pin direction, and a LEF pin without one is read as an input"
            )
        out.extend(block)
        # Resume on the block's own END line; the body lines were emitted above
        # and must not be walked a second time.
        index = end
    return "\n".join(out) + ("\n" if body.endswith("\n") else ""), tuple(notes)


def _normalise_macro(
    body: str,
    cell: str,
    directions: Optional[Mapping[str, str]] = None,
) -> Tuple[str, Tuple[str, ...]]:
    """Return the macro body with its declarations corrected, and what changed.

    Only *declarations* magic cannot read out of a GDS are touched -- the cell
    class, the site, the placement symmetry and the pin directions.  Everything
    else in the macro, ``SIZE`` above all, is a measurement and is left exactly
    as magic wrote it.
    """
    notes: List[str] = []

    class_match = _CLASS_RE.search(body)
    if class_match is None:
        macro_line = _MACRO_LINE_RE.search(body)
        if macro_line is None:
            raise ExportError(
                f"the MACRO {cell} block has no MACRO line to anchor a CLASS to"
            )
        body = (
            body[: macro_line.end()]
            + f"\n  CLASS {REQUIRED_CLASS} ;"
            + body[macro_line.end() :]
        )
        notes.append(
            f"inserted 'CLASS {REQUIRED_CLASS} ;': magic wrote no CLASS line, and "
            "output_constr.md requires one"
        )
    elif class_match.group(1).strip().upper() != REQUIRED_CLASS:
        found = class_match.group(1).strip()
        body = (
            body[: class_match.start()]
            + f"  CLASS {REQUIRED_CLASS} ;"
            + body[class_match.end() :]
        )
        notes.append(
            f"rewrote 'CLASS {found} ;' to 'CLASS {REQUIRED_CLASS} ;': magic reads "
            "no cell class out of a GDS and defaults to BLOCK, which OpenROAD "
            "treats as a hard macro"
        )

    if _SITE_RE.search(body) is None:
        size_line = _SIZE_LINE_RE.search(body)
        if size_line is None:
            raise ExportError(
                f"the MACRO {cell} block carries no SIZE line, so it describes no "
                "cell; magic's LEF output is unusable"
            )
        body = (
            body[: size_line.end()]
            + f"\n  SITE {REQUIRED_SITE} ;"
            + body[size_line.end() :]
        )
        notes.append(
            f"inserted 'SITE {REQUIRED_SITE} ;' after SIZE: magic emits no SITE, "
            "and without one the placer has no row to legalise the cell into"
        )

    if _SYMMETRY_RE.search(body) is None:
        # Verified against OpenROAD's detailed placer: with no SYMMETRY the
        # master reports symX=symY=0, and dpl moves an MX-oriented instance out
        # of its flipped row into an R0 one.  Every sg13g2 core cell declares
        # X Y, and a cell with its rails on the row boundaries is flippable by
        # construction.
        size_line = _SIZE_LINE_RE.search(body)
        if size_line is None:
            raise ExportError(
                f"the MACRO {cell} block carries no SIZE line, so it describes no "
                "cell; magic's LEF output is unusable"
            )
        body = (
            body[: size_line.end()]
            + f"\n  SYMMETRY {REQUIRED_SYMMETRY} ;"
            + body[size_line.end() :]
        )
        notes.append(
            f"inserted 'SYMMETRY {REQUIRED_SYMMETRY} ;' after SIZE: magic emits no "
            "SYMMETRY, and without it the detailed placer will not put the cell in "
            "a flipped row"
        )

    body, pin_notes = _pin_directions(body, dict(directions or {}))
    notes.extend(pin_notes)

    return body, tuple(notes)


def export_lef(
    gds: Path | str,
    cell: str,
    out_lef: Path | str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    directions: Optional[Mapping[str, str]] = None,
) -> Path:
    """Write the abstract LEF for ``cell`` with Magic, and prove it is honest.

    Follows the ``lef:`` recipe of ``ref_makefile_1.mk``.  ``-hide -pinonly``
    turns everything that is not a labelled pin into an obstruction, which is
    what a block-level router needs from a standard cell.

    ``directions`` is optional and additive: when a caller knows a pin is an
    output, saying so here is the only way the published LEF can say so, because
    magic writes no ``DIRECTION`` line and OpenROAD reads a pin without one as
    an input.  Supplies are typed from magic's own ``USE POWER``/``USE GROUND``.

    Raises :class:`ExportError` if Magic failed, if it wrote nothing, if the LEF
    does not define ``cell``, or if the LEF's ``SIZE`` cannot be confirmed
    against the GDS prBoundary -- the last because a placer believing a size the
    mask data does not have is a class of bug that only shows up as an overlap
    in the final layout.
    """
    for pin, direction in dict(directions or {}).items():
        if direction not in _LEF_DIRECTION:
            raise ExportError(
                f"unusable direction {direction!r} for PIN {pin} of {cell}; each "
                "must be one of " + ", ".join(_LEF_DIRECTION)
            )
    gds_path = _readable(Path(gds), "GDS")
    out = Path(out_lef)
    out.parent.mkdir(parents=True, exist_ok=True)
    # A LEF left by an earlier run must not be able to pass for this run's
    # output when magic writes nothing at all.
    if out.exists():
        out.unlink()

    script = (
        f"gds read {rel_to_tool(gds_path)}",
        f"load {cell}",
        f"lef write {rel_to_tool(out)} -hide -pinonly 2um",
    )
    command = (
        "printf '%s\\n' "
        + " ".join(shlex.quote(line) for line in script)
        + " | magic -dnull -noconsole"
        " -rcfile $PDK_ROOT/$PDK/libs.tech/magic/ihp-sg13g2.magicrc"
    )
    result = run_in_container(command, timeout=timeout)

    if not out.is_file() or out.stat().st_size == 0:
        # A zero-byte LEF is what magic leaves when it opens the file and then
        # dies -- verified: `load` of a cell the GDS does not contain exits 139
        # and leaves an empty file.  It carries no evidence, and leaving it in
        # place would hand a `*.lef` glob a file that parses as nothing, so it
        # is removed rather than quarantined.
        husk = ""
        if out.is_file():
            out.unlink()
            husk = f" (the empty file it left at {out} has been removed)"
        raise ExportError(
            f"magic wrote no LEF for {cell} "
            f"(status {result.status}{', timed out' if result.timed_out else ''})"
            f"{husk}; "
            "its output follows, indented so no line of it reads as a verdict:\n"
            + _indent_block(result.output)
        )
    if not result.ok:
        # A LEF exists, but the status says the run did not finish, so the file
        # may be a truncated prefix of one.  Only a status of 0 makes it evidence.
        _reject(
            out,
            f"magic exited {result.status}"
            f"{' (timed out)' if result.timed_out else ''} while writing the LEF "
            f"for {cell}; its output follows, indented so no line of it reads as "
            "a verdict:\n" + _indent_block(result.output),
        )

    macros = metrics.lef_macros(out)
    if cell not in macros:
        _reject(
            out,
            f"magic's LEF defines no MACRO {cell!r}; it defines: "
            + (", ".join(sorted(macros)) or "(nothing)"),
        )

    body, notes = _normalise_macro(macros[cell], cell, directions)
    if notes:
        text = out.read_text(errors="replace")
        text = text.replace(macros[cell], body, 1)
        header = "".join(f"# aion_layout: {note}\n" for note in notes)
        out.write_text(header + text)

    try:
        lef_geometry = metrics.lef_macro_geometry(out, cell)
        gds_geometry = metrics.gds_boundary(gds_path, cell)
    except MetricsError as exc:
        _reject(out, f"cannot compare the LEF SIZE with the GDS boundary: {exc}")

    if gds_geometry.source != "prBoundary":
        # metrics falls back to the shape bounding box when no prBoundary is
        # drawn, and says so.  Comparing the LEF SIZE against a bounding box
        # confirms nothing: the two can agree while the cell still has no
        # declared placement footprint, so this is "we could not tell", which
        # is not a pass.
        detail = "; ".join(gds_geometry.problems) or "none"
        _reject(
            out,
            f"the GDS declares no placement footprint for {cell}: "
            f"{metrics.__name__}.gds_boundary fell back to the {gds_geometry.source} "
            f"({detail}), so the LEF SIZE "
            f"{lef_geometry.width_um:.4f} x {lef_geometry.height_um:.4f} um cannot "
            "be confirmed against anything. Draw a prBoundary",
        )

    if (
        abs(lef_geometry.width_um - gds_geometry.width_um) > GRID_TOL_UM
        or abs(lef_geometry.height_um - gds_geometry.height_um) > GRID_TOL_UM
    ):
        detail = "; ".join(gds_geometry.problems) or "none"
        _reject(
            out,
            f"the LEF and the GDS disagree about the size of {cell}: LEF SIZE "
            f"{lef_geometry.width_um:.4f} x {lef_geometry.height_um:.4f} um, GDS "
            f"{gds_geometry.source} {gds_geometry.width_um:.4f} x "
            f"{gds_geometry.height_um:.4f} um (GDS boundary problems: {detail}). "
            "One of the two artifacts is lying about the cell; neither may be "
            "repaired to match the other",
        )

    return out


def check_lef(lef: Path | str, cell: Optional[str] = None) -> LefCheck:
    """Apply the gate ``make pnr`` applies, and report every failure it finds.

    The six requirements come from ``output_constr.md``.  The two dimensional
    ones are delegated to :func:`metrics.lef_macro_geometry` and the pin track
    rule to :func:`metrics.lef_pin_access`, so that the row height, the site
    pitch and the routing grid live in exactly one place in this package.
    """
    path = Path(lef)
    _readable(path, "LEF")
    try:
        geometry = metrics.lef_macro_geometry(path, cell)
    except MetricsError as exc:
        # A LEF whose macro cannot be measured is not a LefCheck with problems:
        # there is nothing to check, and returning a verdict would invent one.
        raise ExportError(f"cannot measure the macro in {path}: {exc}") from exc

    body = metrics.lef_macros(path)[geometry.cell]

    class_match = _CLASS_RE.search(body)
    cell_class = class_match.group(1).strip() if class_match else ""
    site_match = _SITE_RE.search(body)
    site = site_match.group(1).strip() if site_match else ""
    pins = tuple(dict.fromkeys(_PIN_RE.findall(body)))
    pin_names = {p.upper() for p in pins}

    problems: List[str] = []
    if not cell_class:
        problems.append(
            f"no CLASS line; output_constr.md requires 'CLASS {REQUIRED_CLASS} ;'"
        )
    elif cell_class.upper() != REQUIRED_CLASS:
        problems.append(
            f"CLASS is {cell_class!r}; output_constr.md requires "
            f"'CLASS {REQUIRED_CLASS} ;', because anything else makes OpenROAD "
            "treat the cell as a macro"
        )
    if not site:
        problems.append(
            f"no SITE line; output_constr.md requires 'SITE {REQUIRED_SITE} ;'"
        )
    elif site != REQUIRED_SITE:
        problems.append(
            f"SITE is {site!r}; output_constr.md requires 'SITE {REQUIRED_SITE} ;'"
        )
    problems.extend(geometry.problems)
    for rail in ("VDD", "VSS"):
        if rail not in pin_names:
            problems.append(
                f"no PIN {rail}; output_constr.md requires it so the PDN can "
                "strap the cell"
            )

    # A pin that covers no routing track survives placement and dies in
    # detailed routing, an hour later, taking the whole design with it --
    # DRT-0073 is a hard abort in pin access, not a DRC checker LENIENT=1 can
    # downgrade.  So it is graded here, with the rest of the abstract.
    problems.extend(metrics.lef_pin_access(path, geometry.cell).problems)

    return LefCheck(
        ok=not problems,
        problems=tuple(problems),
        geometry=geometry,
        pins=pins,
        cell_class=cell_class,
        site=site,
    )


# ---------------------------------------------------------------------------
# Pin lists
# ---------------------------------------------------------------------------


def _subckt_pin_lists(text: str) -> Dict[str, List[str]]:
    """Return ``{subckt name: pins}`` for every ``.subckt`` in ``text``.

    This does not go through :mod:`aion_layout.spice_parser`: that parser reads
    a ``.subckt`` header as one physical line, and a PEX netlist always wraps
    its pin list onto ``+`` continuations, so the pins after the first line
    would be silently lost.  Losing pins here would produce a Verilog model with
    a plausible but incomplete port list, which is the worst failure available.
    """
    table: Dict[str, List[str]] = {}
    pending: Optional[str] = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("*"):
            continue
        if line.startswith("+"):
            if pending is not None:
                table[pending].extend(line[1:].split())
            continue
        pending = None
        match = _SUBCKT_RE.match(line)
        if match is None:
            continue
        name = match.group(1)
        if name in table:
            # Keep the first definition; a redefinition is the caller's problem
            # to notice, and silently preferring the last would hide it.
            continue
        table[name] = match.group(2).split()
        pending = name
    return table


def _pins_of(text: str, candidates: Sequence[str], source: Path) -> List[str]:
    """Return the pin list of the first of ``candidates`` defined in ``text``."""
    table = _subckt_pin_lists(text)
    lowered = {name.lower(): pins for name, pins in table.items()}
    for candidate in candidates:
        pins = table.get(candidate)
        if pins is None:
            pins = lowered.get(candidate.lower())
        if pins is None:
            continue
        if not pins:
            raise ExportError(
                f"{source} defines .subckt {candidate} with no pins; a cell with "
                "no ports has no views worth publishing"
            )
        return list(pins)
    defined = ", ".join(sorted(table)) or "(nothing)"
    wanted = " or ".join(repr(c) for c in candidates)
    raise ExportError(f"{source} defines no .subckt named {wanted}; it defines: {defined}")


def pins_from_spice(spice_netlist: Path | str, cell: str) -> List[str]:
    """Return the pins of ``cell`` as its transistor-level netlist declares them."""
    path = _readable(Path(spice_netlist), "SPICE netlist")
    return _pins_of(path.read_text(errors="replace"), (cell,), path)


def pins_from_pex(pex_spice: Path | str, cell: str) -> List[str]:
    """Return the pins of ``cell`` as the PEX netlist declares them.

    The PEX flow renames the subcircuit to ``<cell>_pex`` (``ref_makefile_1.mk``
    does it with ``sed`` after extraction), so that name is tried first and the
    unrenamed one second.
    """
    path = _readable(Path(pex_spice), "PEX netlist")
    return _pins_of(path.read_text(errors="replace"), (f"{cell}_pex", cell), path)


# ---------------------------------------------------------------------------
# Verilog
# ---------------------------------------------------------------------------


def _subckt_of(spice_netlist: Path | str, cell: str) -> Subckt:
    """The parsed ``.subckt`` named ``cell``, or an error naming what is there."""
    path = _readable(Path(spice_netlist), "SPICE netlist")
    try:
        subckts = parse_spice_file(path)
    except SpiceParseError as exc:
        raise ExportError(f"{path} cannot be read as a netlist: {exc}") from exc
    for subckt in subckts:
        if subckt.name.lower() == cell.lower():
            return subckt
    defined = ", ".join(s.name for s in subckts) or "(nothing)"
    raise ExportError(f"{path} defines no .subckt named {cell!r}; it defines: {defined}")


def _checked_against_liberty(
    table: TruthTable, cell: str, lib_files: Sequence[Path | str]
) -> List[str]:
    """Hold the solved function against every Liberty ``function`` for ``cell``.

    The two are independent: this table was *derived* from the transistor
    netlist by :mod:`aion_layout.logic`, and the Liberty function was
    *measured* by ``aion_char`` with an ngspice ``.op`` per input vector.  They
    are the only two statements of the cell's behaviour the flow owns, so a
    disagreement means one of the published views is wrong and neither can be
    trusted to say which -- there is nothing useful to publish.

    Returns the lines that go into the model's header, so a reader can see what
    was checked rather than take "generated" on faith.
    """
    notes: List[str] = []
    for path in lib_files:
        lib = Path(path)
        try:
            library = read_liberty(lib)
            lib_cell = library.cell(cell)
        except LibertyError as exc:
            raise ExportError(
                f"the function of {cell} could not be checked against {lib.name}: {exc}"
            ) from exc
        for output in table.outputs:
            stated = lib_cell.functions.get(output)
            if stated is None:
                notes.append(f"{lib.name}: pin {output} states no function to check against")
                continue
            try:
                disagrees_at = table.disagrees_at(stated, output)
            except LogicError as exc:
                raise ExportError(
                    f"{lib.name} gives {cell} pin {output} the function {stated!r}, "
                    f"which cannot be read against this netlist: {exc}"
                ) from exc
            if disagrees_at is not None:
                vector = table.vector(disagrees_at)
                raise ExportError(
                    f"{cell} does not compute what its Liberty says it does. "
                    f"{lib.name} gives pin {output} the function {stated!r}, which "
                    f"aion_char measured in SPICE; the transistor netlist solves to "
                    f"{table.expression(output, style='liberty')!r}. They first differ "
                    "at "
                    + " ".join(f"{pin}={value}" for pin, value in vector.items())
                    + f", where the Liberty says {output}="
                    + f"{1 - table.column(output)[disagrees_at]} and the netlist says "
                    + f"{table.column(output)[disagrees_at]}. One of the two published "
                    "views is wrong, and a Verilog model written from either would be "
                    "a simulation that disagrees with static timing"
                )
            notes.append(f"{lib.name}: pin {output} function agrees")
    return notes


def _model_ports(
    pins: Iterable[str],
    table: TruthTable,
    cell: str,
    *,
    power: Sequence[str],
    directions: Optional[Mapping[str, str]],
) -> Tuple[List[str], List[str], List[str]]:
    """Split the pin list into supplies, outputs and inputs, and check it.

    The direction of a signal pin is not taken on trust from the caller: the
    netlist already settled it (a pin a device only gates is an input, a pin
    wired to a channel is driven), and a ``directions`` map that contradicts
    that is a LEF and a Verilog model that will disagree about the same cell.
    """
    names = [str(pin).strip() for pin in pins]
    if not names:
        raise ExportError(f"no pins given for {cell}; a model with no ports is not a view")
    if any(not name for name in names):
        raise ExportError(f"blank pin name in the pin list for {cell}: {names!r}")

    directions = dict(directions or {})
    bad = {p: d for p, d in directions.items() if d not in _VERILOG_DIRECTIONS}
    if bad:
        raise ExportError(
            f"unusable port directions for {cell}: {bad!r}; each must be one of "
            + ", ".join(_VERILOG_DIRECTIONS)
        )

    supplies = {p.upper() for p in power}
    power_pins = sorted({n for n in names if n.upper() in supplies})
    signal_pins = sorted({n for n in names if n.upper() not in supplies})

    solved = set(table.inputs) | set(table.outputs)
    if set(signal_pins) != solved:
        only_pins = ", ".join(sorted(set(signal_pins) - solved)) or "(none)"
        only_netlist = ", ".join(sorted(solved - set(signal_pins))) or "(none)"
        raise ExportError(
            f"the pin list for {cell} and its netlist name different signals: "
            f"only in the pin list: {only_pins}; only in the netlist: {only_netlist}. "
            "A model whose ports are not the cell's ports cannot be connected"
        )

    outputs = [pin for pin in signal_pins if pin in table.outputs]
    inputs = [pin for pin in signal_pins if pin in table.inputs]
    for pin in signal_pins:
        wanted = "output" if pin in outputs else "input"
        given = directions.get(pin)
        if given is not None and given != wanted:
            raise ExportError(
                f"{cell} pin {pin} was handed to the exporter as {given!r}, but the "
                f"netlist drives it as an {wanted}; the LEF and the Verilog model "
                "would disagree about which way the signal goes"
            )
    return power_pins, outputs, inputs


def verilog_model_text(
    cell: str,
    table: TruthTable,
    *,
    pins: Iterable[str],
    source: str = "",
    power: Sequence[str] = DEFAULT_POWER_PINS,
    directions: Optional[Mapping[str, str]] = None,
    notes: Sequence[str] = (),
) -> str:
    """Render the gate-level simulation model of ``cell``.

    A cell model is two statements, and a post-place-and-route run needs both:

    * **the function**, or the netlist that instantiates this cell drives ``z``
      out of it forever and the testbench reports ``x`` on a design that is
      fine;
    * **a ``specify`` path per timing arc**, because that is what an SDF's
      ``IOPATH`` records attach to.  A model with no ``specify`` block is
      annotated with nothing and simulates at zero delay -- silently, since the
      SDF reader has no path to complain about.

    The delays in the block are zero on purpose: they are placeholders the SDF
    overwrites, exactly as in the PDK's own ``sg13g2_stdcell.v``.  With no SDF
    the cell is zero-delay, which is what every gate-level model in this flow
    does without one.
    """
    power_pins, outputs, inputs = _model_ports(
        pins, table, cell, power=power, directions=directions
    )

    header = [
        f"// {cell} -- Verilog model for gate-level simulation.",
        "//",
        "// GENERATED by aion_layout.exporters"
        + (f" from {source}" if source else "")
        + " -- do not edit by hand.",
        "//",
        "// The function below is solved from the transistor netlist the layout was",
        "// drawn against (aion_layout.logic: a DC switch-level solve, one input",
        "// vector at a time), not transcribed from a schematic.",
    ]
    if notes:
        header.append("//")
        for note in notes:
            header.append(f"// {note}")
    header += [
        "//",
        "// The specify block carries one zero-delay path per timing arc, which is",
        "// what an SDF IOPATH record annotates. iverilog keeps specify blocks only",
        "// with -gspecify; Questa keeps them by default; Verilator ignores them and",
        "// simulates this model at zero delay, which is all it ever does with a gate",
        "// netlist. So this one file serves the timed and the untimed runs both.",
        "//",
        "// STA does not read this file, and the marker below is what tells OpenSTA's",
        "// Verilog reader to skip it. No timing is lost by that: the cell's arcs come",
        "// from its .lib, which LibreLane loads first (EXTRA_LIBS), so the instance",
        "// links as a liberty leaf cell and is timed like any PDK cell. Without the",
        "// marker OpenSTA aborts the whole run on the assign expression below --",
        "// its reader takes structural netlists only, not operators or specify.",
        "/// sta-blackbox",
        "",
    ]

    entries: List[Tuple[str, str]] = [("power", f"inout {pin}") for pin in power_pins]
    entries += [("signal", f"output {pin}") for pin in outputs]
    entries += [("signal", f"input {pin}") for pin in inputs]

    lines = [_TIMESCALE, "`celldefine", f"module {cell} ("]
    for index, (kind, decl) in enumerate(entries):
        if kind == "power" and (index == 0 or entries[index - 1][0] != "power"):
            lines.append("`ifdef USE_POWER_PINS")
        comma = "," if index < len(entries) - 1 else ""
        lines.append(f"    {decl}{comma}")
        if kind == "power" and (
            index == len(entries) - 1 or entries[index + 1][0] != "power"
        ):
            lines.append("`endif")
    lines.append(");")

    lines.append("")
    lines.append("  // Function")
    for pin in outputs:
        lines.append(f"  assign {pin} = {table.expression(pin)};")

    arcs = [(driver, pin) for pin in outputs for driver in table.support(pin)]
    lines.append("")
    if arcs:
        lines.append("  // Timing")
        lines.append("  specify")
        for driver, pin in arcs:
            lines.append(f"    ({driver} => {pin}) = (0.0, 0.0);")
        lines.append("  endspecify")
    else:
        lines.append("  // No timing: no output of this cell responds to any input.")
    lines.append("")
    lines.append("endmodule")
    lines.append("`endcelldefine")

    return "\n".join(header + lines) + "\n"


def export_verilog_model(
    spice_netlist: Path | str,
    cell: str,
    out_v: Path | str,
    *,
    pins: Optional[Iterable[str]] = None,
    power: Sequence[str] = DEFAULT_POWER_PINS,
    directions: Optional[Mapping[str, str]] = None,
    lib_files: Sequence[Path | str] = (),
) -> Path:
    """Write the gate-level simulation model of ``cell`` from its netlist.

    ``pins`` is the port list to declare -- ``export_all`` passes the PEX one,
    which is the layout's own -- and defaults to the netlist's.  Whichever it
    is, it has to name the same signals the netlist does.

    ``lib_files`` are cross-checked, not read: the function comes from the
    netlist either way, and a Liberty that disagrees stops the publish.
    """
    subckt = _subckt_of(spice_netlist, cell)
    try:
        table = truth_table(subckt)
    except LogicError as exc:
        raise ExportError(
            f"no Verilog model can be written for {cell}: {exc}. Publishing the empty "
            "module that used to stand in for one is worse than publishing nothing: it "
            "elaborates, links, and drives z out of every output for the whole "
            "simulation"
        ) from exc

    notes = _checked_against_liberty(table, cell, lib_files)
    text = verilog_model_text(
        cell,
        table,
        pins=list(pins) if pins is not None else subckt.pins,
        source=Path(spice_netlist).name,
        power=power,
        directions=directions,
        notes=notes,
    )
    out = Path(out_v)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out


# ---------------------------------------------------------------------------
# CDL
# ---------------------------------------------------------------------------


def export_cdl(spice_netlist: Path | str, cell: str, out_cdl: Path | str) -> Path:
    """Write a CDL netlist view of ``cell`` from its transistor-level SPICE.

    A CDL view is connectivity and nothing else, so every dot-directive except
    ``.subckt``/``.ends`` is dropped, along with anything inside a ``.control``
    block.  Continuation lines follow the fate of the card they continue -- an
    orphaned ``+`` line is a syntax error, not a harmless leftover.

    Every ``.subckt`` in the file survives, not only ``cell``'s: a netlist that
    instantiates a helper subcircuit needs its definition, and dropping one
    would turn an LVS mismatch into a mystery.  ``cell`` itself must be there.
    """
    source = _readable(Path(spice_netlist), "SPICE netlist")
    lines = source.read_text(errors="replace").splitlines()

    keep = [False] * len(lines)
    rewritten: Dict[int, str] = {}
    dropped: List[str] = []
    subckts: List[str] = []
    in_control = False
    head: Optional[int] = None

    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.startswith("+") and head is not None:
            keep[index] = keep[head]
            continue
        if not stripped or stripped.startswith("*"):
            keep[index] = not in_control
            continue
        head = index
        if not stripped.startswith("."):
            keep[index] = not in_control
            continue
        directive = stripped.split(None, 1)[0].lower()
        if directive == ".subckt":
            match = _SUBCKT_RE.match(stripped)
            if match is None:
                raise ExportError(f"{source}:{index + 1}: unreadable .subckt line: {raw!r}")
            subckts.append(match.group(1))
            keep[index] = True
            rewritten[index] = _DOT_SUBCKT_RE.sub(
                lambda m: m.group(1) + ".SUBCKT", raw, count=1
            )
        elif directive == ".ends":
            keep[index] = True
            rewritten[index] = _ENDS_RE.sub(lambda m: m.group(1) + ".ENDS", raw, count=1)
        elif directive == ".control":
            in_control = True
        elif directive == ".endc":
            in_control = False
        else:
            if directive not in dropped:
                dropped.append(directive)

    if not any(name.lower() == cell.lower() for name in subckts):
        raise ExportError(
            f"{source} defines no .subckt {cell!r}; it defines: "
            + (", ".join(subckts) or "(nothing)")
        )
    if in_control:
        raise ExportError(f"{source} opens a .control block that never ends")

    header = [
        f"* CDL netlist view of {cell}",
        f"* written by aion_layout.exporters from {source.name}",
    ]
    if dropped:
        header.append("* simulator-only directives dropped: " + " ".join(dropped))
    body = [rewritten.get(i, line) for i, line in enumerate(lines) if keep[i]]

    out = Path(out_cdl)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(header + body) + "\n")
    return out


# ---------------------------------------------------------------------------
# GDS and the whole set
# ---------------------------------------------------------------------------


def export_gds(gds: Path | str, out_gds: Path | str) -> Path:
    """Copy the streamout GDS into the publish directory, byte for byte."""
    return _copy_view(gds, Path(out_gds), "GDS")


def _publish_libs(libs: Sequence[Path], cell: str, out_dir: Path) -> Tuple[Path, ...]:
    """Copy the Liberty files in, keeping a corner set distinguishable.

    A single library is the cell's library and is published as ``<cell>.lib``.
    A set of them is one file per process corner, and renaming those to a single
    stem would either erase the corner or drop every corner but one, so they
    keep the names the characterizer gave them.  Discovery then groups them by
    the directory rather than the stem, which ``output_constr.md`` allows.
    """
    if len(libs) == 1:
        return (_copy_view(libs[0], out_dir / f"{cell}.lib", "Liberty library"),)
    published: List[Path] = []
    seen: Dict[str, Path] = {}
    for lib in libs:
        if lib.name in seen:
            raise ExportError(
                f"two Liberty files are both named {lib.name} ({seen[lib.name]} and "
                f"{lib}); one would overwrite the other in {out_dir}"
            )
        seen[lib.name] = lib
        published.append(_copy_view(lib, out_dir / lib.name, "Liberty library"))
    return tuple(published)


def _quarantine_stale_views(out_dir: Path, cell: str, libs: Sequence[Path]) -> List[Path]:
    """Rename any view a previous publish of ``cell`` left in ``out_dir``.

    Only the exact filenames :func:`export_all` itself writes are touched, so a
    directory holding other cells is untouched.  They are renamed rather than
    deleted because they are the previous run's evidence -- but they must stop
    being discoverable, since a stem carrying a GDS and a Liberty from an older
    layout and no LEF at all is a half-published cell, which is the state this
    module exists to prevent.
    """
    names = {f"{cell}.{ext}" for ext in ("gds", "v", "spice", "cdl", "lib")}
    names.update(lib.name for lib in libs)
    moved: List[Path] = []
    for name in sorted(names):
        stale = out_dir / name
        if not stale.is_file():
            continue
        quarantined = stale.with_suffix(stale.suffix + ".rejected")
        if quarantined.exists():
            quarantined.unlink()
        stale.rename(quarantined)
        moved.append(quarantined)
    return moved


@dc.dataclass(frozen=True)
class ExportedViews:
    """Every view published for one cell, and the verdict on its LEF."""

    cell: str
    gds: Path
    lef: Path
    lib: Tuple[Path, ...]
    verilog: Path
    spice: Path
    cdl: Path
    lef_check: LefCheck

    def describe(self) -> str:
        """One line per published view, for the end of a flow log."""
        views = [
            ("gds", self.gds),
            ("lef", self.lef),
            ("verilog", self.verilog),
            ("spice", self.spice),
            ("cdl", self.cdl),
        ] + [("lib", lib) for lib in self.lib]
        return "\n".join(f"{name:>8}: {path}" for name, path in views)


def export_all(
    *,
    cell: str,
    gds: Path | str,
    spice_netlist: Path | str,
    lib_files: Sequence[Path | str],
    out_dir: Path | str,
    pex_spice: Optional[Path | str] = None,
    directions: Optional[Mapping[str, str]] = None,
) -> ExportedViews:
    """Publish every view of ``cell`` into ``out_dir``, or publish none of them.

    The LEF is built and checked first, before anything else is copied, so that
    a cell the placer would reject leaves behind a quarantined ``.lef.rejected``
    and an error rather than a directory that looks finished.  Anything that
    fails after that -- a netlist with no truth table, a Liberty whose
    ``function`` disagrees with it -- takes the views already written with it,
    for the same reason.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    libs = [Path(p) for p in lib_files]
    if not libs:
        raise ExportError(
            f"no Liberty file given for {cell}; output_constr.md requires a .lib, "
            "because a cell with no timing model cannot be placed or optimised"
        )
    for lib in libs:
        _readable(lib, "Liberty library")
    _readable(Path(spice_netlist), "SPICE netlist")

    try:
        lef = export_lef(gds, cell, out / f"{cell}.lef", directions=directions)
    except ExportError as exc:
        stale = _quarantine_stale_views(out, cell, libs)
        raise ExportError(
            f"{exc}"
            + (
                "\nviews from an earlier publish of this cell were quarantined: "
                + ", ".join(str(path) for path in stale)
                if stale
                else ""
            )
        ) from exc

    lef_check = check_lef(lef, cell)
    if not lef_check.ok:
        stale = _quarantine_stale_views(out, cell, libs)
        _reject(
            lef,
            f"{cell} would be rejected at detailed placement; "
            f"{len(lef_check.problems)} requirement(s) from output_constr.md are "
            "not met:\n"
            + "\n".join(f"  - {p}" for p in lef_check.problems)
            + (
                "\nviews from an earlier publish of this cell were quarantined: "
                + ", ".join(str(path) for path in stale)
                if stale
                else ""
            ),
        )

    pins = (
        pins_from_pex(pex_spice, cell)
        if pex_spice is not None
        else pins_from_spice(spice_netlist, cell)
    )

    try:
        return ExportedViews(
            cell=cell,
            gds=export_gds(gds, out / f"{cell}.gds"),
            lef=lef,
            lib=_publish_libs(libs, cell, out),
            verilog=export_verilog_model(
                spice_netlist,
                cell,
                out / f"{cell}.v",
                pins=pins,
                directions=directions,
                lib_files=libs,
            ),
            spice=_copy_view(spice_netlist, out / f"{cell}.spice", "SPICE netlist"),
            cdl=export_cdl(spice_netlist, cell, out / f"{cell}.cdl"),
            lef_check=lef_check,
        )
    except ExportError as exc:
        # A view that failed halfway through leaves the others behind, and a
        # directory holding a GDS and a Liberty and no Verilog model is a cell
        # somebody will pick up and place.  Every view written by this call goes
        # out of the way of discovery, the LEF included.
        stale = _quarantine_stale_views(out, cell, libs)
        _reject(
            lef,
            f"{cell} was not published: {exc}"
            + (
                "\nthe views written before the failure were quarantined: "
                + ", ".join(str(path) for path in stale)
                if stale
                else ""
            ),
        )


__all__ = [
    "DEFAULT_POWER_PINS",
    "REQUIRED_CLASS",
    "REQUIRED_SITE",
    "REQUIRED_SYMMETRY",
    "ExportError",
    "ExportedViews",
    "LefCheck",
    "check_lef",
    "export_all",
    "export_cdl",
    "export_gds",
    "export_lef",
    "export_verilog_model",
    "pins_from_pex",
    "pins_from_spice",
]
