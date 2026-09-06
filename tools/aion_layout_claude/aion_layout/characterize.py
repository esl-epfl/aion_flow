# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Parasitic extraction and Liberty characterization
# ================================================================

"""Timing for the cell that was actually drawn, not for the netlist it came from.

The whole claim this tool makes is that one AION cell is *faster* than the PDK
cells it replaces.  A number that would support that claim has to come from the
layout, so this module characterizes the **PEX netlist** -- the transistors plus
the resistance and capacitance Magic extracted from the polygons -- and never
the schematic netlist the layout was drawn from.  Characterizing the schematic
would report the delay of a cell nobody can fabricate and would flatter every
layout equally, which is exactly the comparison the flow exists to avoid.

The same reasoning fixes the Liberty ``area``: it is the measured placement
footprint, taken from the LEF or passed in from :mod:`aion_layout.metrics`.
``area : 0;`` is not "unknown" to a resizer, it is a cell that costs nothing.

Everything here is mechanical.  ``sak-pex.sh`` and ``aion_char`` do the work,
this module only spells the commands, and then refuses to believe them: a run
that produced no netlist, an empty netlist, a netlist with no ``.subckt``, or
fewer ``.lib`` files than corners is an error.  A missing artifact is never a
result, and a tool's exit status is never discarded in favour of "the file is
there" -- the shell redirection that wrote it proves nothing.

Why the PEX netlist can be characterized at all: Magic renames the flattened
top cell to the name given with ``-n``, so the extracted ``.subckt`` keeps the
cell's own name and ``aion_char`` can instantiate it exactly as it would the
schematic.  Its port *order* is Magic's, not the source netlist's, which is why
pin directions are resolved by name throughout.
"""

from __future__ import annotations

import dataclasses as dc
import os
import re
import shlex
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

from .metrics import MetricsError, lef_macro_geometry
from .runner import REPO_ROOT, TOOL_DIR, DEFAULT_TIMEOUT, run_in_container
from .spice_parser import SpiceParseError, Subckt, parse_spice_file


class CharacterizeError(RuntimeError):
    """Raised when extraction or characterization did not positively succeed."""


@dc.dataclass(frozen=True)
class Corner:
    """One process/voltage/temperature point, spelled as ``aion_char`` wants it."""

    name: str
    section: str
    vdd: float
    temp: float

    @property
    def spec(self) -> str:
        """The ``--corner NAME:SECTION:VDD:TEMP`` argument."""
        return f"{self.name}:{self.section}:{self.vdd:g}:{self.temp:g}"

    @property
    def tag(self) -> str:
        """The file-name stem ``aion_char`` gives this corner, e.g. ``typ_1p20V_25C``.

        Mirrors ``aion_char.characterizer.Corner.tag``: the ``.lib`` files are
        found by name rather than by globbing, so that a stale file from an
        earlier run can never be counted as this run's output.
        """
        volt = f"{self.vdd:.2f}".replace(".", "p")
        temp = f"{self.temp:g}".replace("-", "m")
        return f"{self.name}_{volt}V_{temp}C"


#: The three corners the IHP standard-cell libraries are shipped at.
DEFAULT_CORNERS: Tuple[Corner, ...] = (
    Corner("typ", "mos_tt", 1.20, 25.0),
    Corner("slow", "mos_ss", 1.08, 125.0),
    Corner("fast", "mos_ff", 1.32, -40.0),
)

#: The PDK's own NLDM index, so a library from here reads next to IHP's in one STA run.
DEFAULT_SLEWS_NS: Tuple[float, ...] = (0.0186, 0.0966, 0.174, 0.3294, 0.6408, 1.263, 2.5074)
DEFAULT_LOADS_PF: Tuple[float, ...] = (0.001, 0.0234, 0.039, 0.0648, 0.108, 0.18, 0.3)

#: Device models, spelled for the container's shell to expand.
MODEL_LIB = '"$PDK_ROOT/$PDK/libs.tech/ngspice/models/cornerMOSlv.lib"'
#: The Liberty template, relative to the repository root.
LIB_TEMPLATE = "tools/aion_char/templates/sg13g2.lib.tmpl"
#: ``aion_char``'s package directory, relative to the repository root.
AION_CHAR_DIR = "tools/aion_char"

#: A full characterization is dozens of ngspice runs per corner; 1800 s is not enough.
CHAR_TIMEOUT = 14400

#: ``.subckt <name>`` at the start of a line, however the tool spelled the case.
_SUBCKT_RE = "^[.]subckt[ \t]+{name}([ \t]|$)"
#: A device instance line inside the extracted subcircuit.
_DEVICE_RE = re.compile(r"^[xm]\S*[ \t]", re.IGNORECASE | re.MULTILINE)


@dc.dataclass(frozen=True)
class CharResult:
    """What one characterization produced, with every path checked to exist."""

    cell: str
    lib_files: Tuple[Path, ...]
    report: Optional[Path]
    area_um2: float
    spice_used: Path
    corners: Tuple[Corner, ...]

    def describe(self) -> str:
        """One line, for a report or a verdict block."""
        return (
            f"{self.cell}: {len(self.lib_files)} corner(s) "
            f"[{', '.join(c.name for c in self.corners)}] from {self.spice_used.name}, "
            f"area {self.area_um2:.4f} um^2"
        )


def _rel_to_repo(path: os.PathLike[str] | str) -> str:
    """Spell ``path`` the way a command run from the repository root wants it."""
    return os.path.relpath(Path(path).resolve(), REPO_ROOT)


def _rel_to_tool(path: os.PathLike[str] | str) -> str:
    """Spell ``path`` the way a command run from this tool's directory wants it."""
    return os.path.relpath(Path(path).resolve(), TOOL_DIR)


def _readable(path: Path, what: str) -> str:
    """Return the text of a file that must exist and must not be empty."""
    if not path.is_file():
        raise CharacterizeError(f"{what} was not produced: {path}")
    text = path.read_text(errors="replace")
    if not text.strip():
        raise CharacterizeError(f"{what} is empty: {path}")
    return text


def _has_subckt(text: str, name: str) -> bool:
    """True when ``text`` defines ``.subckt <name>``."""
    return re.search(
        _SUBCKT_RE.format(name=re.escape(name)), text, re.IGNORECASE | re.MULTILINE
    ) is not None


def run_pex(
    gds: os.PathLike[str] | str,
    cell: str,
    work_dir: os.PathLike[str] | str,
    *,
    mode: int = 3,
    subckt_name: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Path:
    """Extract ``cell`` from ``gds`` and return the PEX netlist.

    ``mode`` is ``sak-pex.sh``'s: 1 C-decoupled, 2 C-coupled, 3 full RC.  Full
    RC is the default because the wire resistance inside a hand-drawn cell is
    exactly the thing a small layout can get wrong, and a C-only extraction
    cannot show it.

    The netlist is renamed to ``<cell>_pex<mode>.spice`` so that several modes
    can live in one directory and so that no later step can pick up a netlist
    without knowing which extraction produced it.
    """
    layout = Path(gds)
    work = Path(work_dir)
    subckt = subckt_name or cell

    if mode not in (1, 2, 3):
        raise CharacterizeError(f"PEX mode must be 1, 2 or 3, not {mode!r}")
    if not layout.is_file():
        raise CharacterizeError(f"no GDS at {layout}")
    if layout.stat().st_size == 0:
        raise CharacterizeError(f"GDS is empty: {layout}")
    # sak-pex.sh derives the cell to load from the *file name* and aborts when the
    # GDS has no top cell of that name.  Catching it here names the real cause.
    if layout.stem != cell:
        raise CharacterizeError(
            f"sak-pex.sh loads the cell named like the file, so {layout.name} can only "
            f"extract '{layout.stem}', not '{cell}'; rename the GDS to {cell}.gds"
        )

    work.mkdir(parents=True, exist_ok=True)
    command = " ".join(
        shlex.quote(a)
        for a in (
            "sak-pex.sh",
            "-d",
            "-m", str(mode),
            "-n", subckt,
            "-w", _rel_to_tool(work),
            _rel_to_tool(layout),
        )
    )
    result = run_in_container(command, timeout=timeout)
    if not result.ok:
        raise CharacterizeError(
            f"sak-pex.sh failed for {cell} (status {result.status}"
            f"{', timed out' if result.timed_out else ''}); its output, indented so no "
            "line of it can be read as a verdict:\n"
            + "\n".join("    " + line for line in result.tail().splitlines())
        )

    produced = work / f"{cell}.pex.spice"
    target = work / f"{cell}_pex{mode}.spice"
    if not produced.is_file():
        raise CharacterizeError(
            f"sak-pex.sh reported success but wrote no {produced.name}; its output:\n"
            + "\n".join("    " + line for line in result.tail().splitlines())
        )
    produced.replace(target)

    text = _readable(target, f"the PEX netlist of {cell}")
    if not _has_subckt(text, subckt):
        raise CharacterizeError(
            f"{target} carries no '.subckt {subckt}', so nothing can instantiate it; "
            "sak-pex.sh output:\n"
            + "\n".join("    " + line for line in result.tail().splitlines())
        )
    if not _DEVICE_RE.search(text):
        raise CharacterizeError(
            f"{target} defines '.subckt {subckt}' but holds no device instance; the "
            "extraction found no transistors"
        )

    # Magic leaves these in whatever directory it ran in; ref_makefile_1.mk removes
    # them for the same reason: they are not results, and a stale pair confuses the
    # next extraction of a cell of the same name.
    for directory in (TOOL_DIR, work):
        for stem in {cell, subckt}:
            for suffix in (".nodes", ".sim"):
                stray = directory / f"{stem}{suffix}"
                if stray.is_file():
                    stray.unlink()

    return target


def _subckt_of(spice: Path, cell: str) -> Subckt:
    """Return the ``.subckt`` named ``cell`` in ``spice``, or say why it cannot."""
    try:
        subckts = parse_spice_file(spice)
    except (SpiceParseError, OSError) as exc:
        raise CharacterizeError(f"cannot parse {spice}: {exc}") from None
    for sub in subckts:
        if sub.name == cell:
            return sub
    known = ", ".join(s.name for s in subckts) or "(none)"
    raise CharacterizeError(f"{spice} has no '.subckt {cell}'; it defines: {known}")


def _resolve_pins(
    spice: Path,
    cell: str,
    inputs: Optional[Sequence[str] | str],
    outputs: Optional[Sequence[str] | str],
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """Decide which pins are inputs and which are outputs.

    A SPICE ``.subckt`` does not say, and ``aion_char`` rightly refuses to guess.
    The guess is made here instead, from the transistor topology: the output is
    the port driven by both a PMOS and an NMOS drain.  A caller that knows
    better -- typically from the pre-layout netlist -- passes both lists, and
    they are then checked against the ports by name, never by position: a PEX
    netlist lists the same ports in Magic's order, not the source's.
    """
    ports = tuple(_subckt_of(spice, cell).pins)
    given = [x for x in (inputs, outputs) if x is not None]
    if len(given) == 1:
        raise CharacterizeError(
            "inputs and outputs must be given together or not at all: one alone "
            "leaves the remaining ports unclassified"
        )

    if inputs is not None and outputs is not None:
        ins = tuple(_as_names(inputs))
        outs = tuple(_as_names(outputs))
        if not ins:
            raise CharacterizeError(
                f"'{cell}': inputs= names no pin; aion_char would be handed an empty "
                "--inputs and would classify the remaining ports itself"
            )
    else:
        sub = _subckt_of(spice, cell)
        out = sub.output_net
        if out is None:
            raise CharacterizeError(
                f"cannot tell which port of '{cell}' is the output from the topology "
                f"of {spice.name} (ports: {', '.join(ports)}); pass inputs= and outputs="
            )
        outs = (out,)
        ins = tuple(sub.input_nets)
        if not ins:
            raise CharacterizeError(
                f"'{cell}' in {spice.name} has no input port besides the supplies; "
                "pass inputs= and outputs= if that is wrong"
            )

    upper = {p.upper() for p in ports}
    unknown = [p for p in ins + outs if p.upper() not in upper]
    if unknown:
        raise CharacterizeError(
            f"pin(s) {', '.join(unknown)} are not ports of '.subckt {cell} "
            f"{' '.join(ports)}'"
        )
    if not outs:
        raise CharacterizeError(f"'{cell}': no output pin given")
    return ins, outs


def _as_names(value: Sequence[str] | str) -> Tuple[str, ...]:
    """Accept ``"A,B"`` or ``["A", "B"]`` and return the names, blanks dropped."""
    items: Iterable[str] = value.split(",") if isinstance(value, str) else value
    return tuple(n.strip() for n in items if str(n).strip())


def _number_list(values: Sequence[float] | str) -> str:
    """Format a slew or load index the way ``--slews``/``--loads`` want it.

    The index has to be strictly increasing, not merely sorted: a repeated point
    makes an NLDM table two of whose columns are the same operating point, and
    every interpolation across that pair divides by zero.
    """
    items = values.replace(",", " ").split() if isinstance(values, str) else list(values)
    parsed: list[float] = []
    for item in items:
        try:
            parsed.append(float(item))
        except (TypeError, ValueError):
            raise CharacterizeError(
                f"--slews and --loads take numbers; {item!r} is not one"
            ) from None
    if len(parsed) < 2:
        raise CharacterizeError("--slews and --loads each need at least two points")
    if any(b <= a for a, b in zip(parsed, parsed[1:])):
        raise CharacterizeError(
            f"--slews and --loads must be strictly increasing, got {parsed}"
        )
    return ", ".join(f"{v:g}" for v in parsed)


def _resolve_area(
    cell: str,
    area_um2: Optional[float],
    area_lef: Optional[os.PathLike[str] | str],
) -> Tuple[float, list[str]]:
    """Return ``(area, extra aion_char arguments)``, refusing to leave it at 0.

    An explicit value wins over the LEF because a caller that measured the GDS
    itself (:func:`aion_layout.metrics.gds_boundary`) has the same number from
    the same boundary.  Both are read here as well as passed on, so the result
    carries the area rather than the caller having to re-derive it.
    """
    if area_um2 is not None:
        if area_um2 <= 0:
            raise CharacterizeError(
                f"area_um2={area_um2!r} is not a footprint; a Liberty 'area' of 0 makes "
                "every resizer and area report wrong"
            )
        return float(area_um2), ["--area", f"{area_um2:.6g}"]
    if area_lef is not None:
        lef = Path(area_lef)
        if not lef.is_file():
            raise CharacterizeError(f"no LEF at {lef} (area_lef=)")
        try:
            geometry = lef_macro_geometry(lef, cell)
        except MetricsError as exc:
            raise CharacterizeError(f"cannot take the area of {cell} from {lef}: {exc}") from None
        return geometry.area_um2, ["--area-from-lef", _rel_to_repo(lef)]
    raise CharacterizeError(
        "no area for the Liberty 'area' attribute: pass area_um2= (from "
        "metrics.gds_boundary) or area_lef=. Defaulting it to 0 would publish a cell "
        "that a resizer believes is free"
    )


def characterize(
    spice: os.PathLike[str] | str,
    cell: str,
    out_dir: os.PathLike[str] | str,
    *,
    inputs: Optional[Sequence[str] | str] = None,
    outputs: Optional[Sequence[str] | str] = None,
    area_um2: Optional[float] = None,
    area_lef: Optional[os.PathLike[str] | str] = None,
    corners: Sequence[Corner] = DEFAULT_CORNERS,
    jobs: int = 8,
    slews: Optional[Sequence[float] | str] = None,
    loads: Optional[Sequence[float] | str] = None,
    verify: bool = True,
    timeout: int = CHAR_TIMEOUT,
) -> CharResult:
    """Characterize ``cell`` in ``spice`` into one Liberty file per corner.

    ``spice`` is meant to be the netlist :func:`run_pex` returned, so the
    timing tables carry the layout's own parasitics; any transistor-level
    netlist that defines ``.subckt <cell>`` works, and the result records which
    one was used.

    ``verify=True`` leaves ``aion_char``'s functional check switched on.  Be
    clear about what that buys: the check needs an *oracle* -- a Liberty or
    Verilog view of what the cell should compute -- there is no way to hand one
    in through this function, and an AION cell has none before it is exported.
    So ``aion_char`` records ``skipped (no --lib and no --verilog: nothing to
    check the function against)`` in ``char_report.md`` and characterizes
    anyway; the run does not fail.  ``verify=False`` says the same thing out
    loud by passing ``--no-verify``.  Either way the cell's function is still
    *measured* from the ``.op`` sweep and written into the Liberty
    ``function``; what no caller of this function gets is an independent
    cross-check of it, and a caller that needs one must run ``aion_char``
    directly with ``--lib`` or ``--verilog``.
    """
    netlist = Path(spice)
    out = Path(out_dir)

    if not netlist.is_file():
        raise CharacterizeError(f"no SPICE netlist at {netlist}")
    _readable(netlist, f"the netlist for {cell}")
    corner_list = tuple(corners)
    if not corner_list:
        raise CharacterizeError("no corners given; there would be nothing to characterize")
    names = [c.name for c in corner_list]
    if len(set(names)) != len(names):
        raise CharacterizeError(
            f"corner names must be unique, got {names}: they name the .lib files"
        )
    if jobs < 1:
        raise CharacterizeError(f"jobs must be at least 1, not {jobs!r}")

    ins, outs = _resolve_pins(netlist, cell, inputs, outputs)
    area, area_args = _resolve_area(cell, area_um2, area_lef)
    slew_index = _number_list(DEFAULT_SLEWS_NS if slews is None else slews)
    load_index = _number_list(DEFAULT_LOADS_PF if loads is None else loads)

    out.mkdir(parents=True, exist_ok=True)
    # Removed before the run so a corner whose .lib is missing afterwards is a
    # missing file, never last week's file read back as this run's evidence.
    # ``char_report.md`` goes with them: :class:`CharResult` hands that path on as
    # this run's report, and aion_char writes it only after the last corner
    # succeeded, so a surviving one from an earlier run would be quoted as
    # evidence for measurements it never saw.  ``char_data.json`` is aion_char's
    # machine-readable twin of the report and is stale for exactly the same reason.
    for stale in (
        *(out / f"{cell}_{corner.tag}.lib" for corner in corner_list),
        out / "char_report.md",
        out / "char_data.json",
    ):
        if stale.is_file():
            stale.unlink()

    argv = [
        "python3", "-m", "aion_char", "lib", _rel_to_repo(netlist),
        "--cell", cell,
        "--inputs", ",".join(ins),
        "--outputs", ",".join(outs),
        "--template", LIB_TEMPLATE,
        "--slews", slew_index,
        "--loads", load_index,
        "--lib-name", cell,
        "--jobs", str(jobs),
        *area_args,
        "-o", _rel_to_repo(out),
    ]
    for corner in corner_list:
        argv += ["--corner", corner.spec]
    if not verify:
        argv.append("--no-verify")

    # --model-lib is left unquoted on purpose: $PDK_ROOT and $PDK are set inside the
    # container and nowhere else, so the container's shell has to expand them.
    command = (
        f"cd {shlex.quote(_rel_to_tool(REPO_ROOT))} && PYTHONPATH={AION_CHAR_DIR} "
        + " ".join(shlex.quote(a) for a in argv)
        + f" --model-lib {MODEL_LIB}"
    )
    result = run_in_container(command, timeout=timeout)
    if not result.ok:
        raise CharacterizeError(
            f"aion_char failed for {cell} (status {result.status}"
            f"{', timed out' if result.timed_out else ''}); its output, indented so no "
            "line of it can be read as a verdict:\n"
            + "\n".join("    " + line for line in result.tail(60).splitlines())
        )

    lib_files: list[Path] = []
    for corner in corner_list:
        path = out / f"{cell}_{corner.tag}.lib"
        text = _readable(path, f"the {corner.name} Liberty file for {cell}")
        if f"cell ({cell})" not in text:
            raise CharacterizeError(
                f"{path} defines no 'cell ({cell})', so it characterizes something else"
            )
        lib_files.append(path)

    report = out / "char_report.md"
    return CharResult(
        cell=cell,
        lib_files=tuple(lib_files),
        report=report if report.is_file() else None,
        area_um2=area,
        spice_used=netlist,
        corners=corner_list,
    )


__all__ = [
    "AION_CHAR_DIR",
    "CHAR_TIMEOUT",
    "DEFAULT_CORNERS",
    "DEFAULT_LOADS_PF",
    "DEFAULT_SLEWS_NS",
    "LIB_TEMPLATE",
    "MODEL_LIB",
    "CharResult",
    "CharacterizeError",
    "Corner",
    "characterize",
    "run_pex",
]
