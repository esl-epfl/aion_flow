# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-13
#  Description:               TritonRoute's own pin access, on the abstract
# ================================================================

"""Ask TritonRoute whether it can reach every pin, before the cell is placed.

:func:`metrics.lef_pin_access` is the static half of pin access: a pin it
rejects cannot be reached, but a pin it passes can still miss, because
TritonRoute only tries certain via positions -- tracks, half tracks, the pin
centre and positions that align the enclosure with the pin.  The only way to
know what TritonRoute does is to run it, and OpenROAD's ``pin_access`` is
exactly the pin access stage ``detailed_route`` starts with: the stage that
aborts a whole design with ``DRT-0073 No access point``.

It needs a placed design, so :func:`placement_def` builds the smallest one that
looks like step 7 to the router: the cell twice, abutted to itself, between two
PDK cells, in an ``N`` row and in an ``FS`` row -- the two orientations step 7
placed every AION instance in -- on the tracks of ``tracks.info`` and with the
routing layers step 7 routes on.  Every pin is tied to a net, because pin access
skips a pin nothing connects to.

The verdict follows the rest of the package: ``FAIL`` names every pin with no
access point, ``ERROR`` means OpenROAD did not finish or said something this
module does not recognise, and nothing unmeasured is ever a ``PASS``.
"""

from __future__ import annotations

import dataclasses as dc
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .metrics import (
    POWER_PIN_NAMES,
    ROW_HEIGHT_UM,
    SITE_WIDTH_UM,
    TRACK_UM,
    MetricsError,
    _LEF_PIN_RE,
    _LEF_USE_RE,
    lef_macro_geometry,
    lef_macros,
)
from .runner import rel_to_tool, run_in_container

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_ERROR = "ERROR"

#: The PDK cell placed on either side, and its signal pins.  ``SIZE 1.44 BY
#: 3.78`` in ``sg13g2_stdcell.lef``.
NEIGHBOUR = "sg13g2_inv_1"
NEIGHBOUR_WIDTH_NM = 1440
NEIGHBOUR_PINS = ("A", "Y")

#: The routing layers step 7 routes signals on: ``RT_MIN_LAYER`` and
#: ``RT_MAX_LAYER`` in its resolved LibreLane configuration.
ROUTING_LAYERS = ("Metal2", "TopMetal1")

#: ``libs.tech/librelane/sg13g2_stdcell/tracks.info``, as ``(offset, pitch)`` in
#: nm per axis.  Metal1..Metal5 are :data:`metrics.TRACK_UM`.
TRACKS_NM: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]] = {
    **{
        layer: (
            (round(TRACK_UM["x"][0] * 1000), round(TRACK_UM["x"][1] * 1000)),
            (round(TRACK_UM["y"][0] * 1000), round(TRACK_UM["y"][1] * 1000)),
        )
        for layer in ("Metal1", "Metal2", "Metal3", "Metal4", "Metal5")
    },
    "TopMetal1": ((1640, 3280), (1640, 3280)),
    "TopMetal2": ((2000, 4000), (2000, 4000)),
}

#: Rows, bottom up, each with the orientation step 7 gives it.
ROW_ORIENTATIONS = ("N", "FS")

#: OpenROAD's ``pin_access`` on a handful of instances takes seconds; this is
#: for a container that is wedged, not for a slow run.
DEFAULT_TIMEOUT = 300

_SCRIPT = """\
set lef_dir $::env(PDK_ROOT)/$::env(PDK)/libs.ref/sg13g2_stdcell/lef
read_lef $lef_dir/sg13g2_tech.lef
read_lef $lef_dir/sg13g2_stdcell.lef
read_lef {lef}
read_def {def_}
set_routing_layers -signal {bottom}-{top} -clock {bottom}-{top}
set status [catch {{pin_access}} message]
foreach inst [[ord::get_db_block] getInsts] {{
  if {{[[$inst getMaster] getName] ne "{cell}"}} continue
  foreach iterm [$inst getITerms] {{
    set mterm [$iterm getMTerm]
    if {{[$mterm getSigType] in {{POWER GROUND}}}} continue
    set points {{}}
    foreach ap [$iterm getPrefAccessPoints] {{ lappend points [join [concat [$ap getPoint] [[$ap getLayer] getName]] ,] }}
    puts "PIN_ACCESS_AP [$inst getName] [$mterm getName] [llength $points] [join $points {{ }}]"
  }}
}}
puts "PIN_ACCESS_DONE $status"
"""

_DONE_RE = re.compile(r"^PIN_ACCESS_DONE (\d+)\s*$", re.MULTILINE)
_AP_RE = re.compile(r"^PIN_ACCESS_AP (\S+) (\S+) (\d+) ?(.*)$", re.MULTILINE)
_NO_ACCESS_RE = re.compile(r"\[ERROR DRT-0073\] No access point for (\S+)/(\S+) \(")
_ERROR_RE = re.compile(r"^\[ERROR (\S+)\].*$|^Error: .*$", re.MULTILINE)


class PinAccessError(RuntimeError):
    """Raised when the design pin access needs cannot be built from the LEF."""


@dc.dataclass(frozen=True)
class PinAccessReport:
    """TritonRoute's verdict on one cell's pins.

    ``access_points`` is where it would enter each pin of the cell placed ``N``:
    ``(x, y, layer)``, in um from the cell origin, one per pin when it found one.
    """

    cell: str
    result: str
    problems: Tuple[str, ...] = ()
    access_points: Dict[str, Tuple[Tuple[float, float, str], ...]] = dc.field(default_factory=dict)
    log: Optional[Path] = None

    @property
    def ok(self) -> bool:
        return self.result == RESULT_PASS


def signal_pins(lef: Path | str, cell: str) -> List[str]:
    """The pins of ``cell`` the router has to reach, in LEF order."""
    pins = []
    for name, body in _LEF_PIN_RE.findall(lef_macros(lef)[cell]):
        use = _LEF_USE_RE.search(body)
        if use is not None and use.group(1).upper() in ("POWER", "GROUND"):
            continue
        if use is None and name.upper() in POWER_PIN_NAMES:
            continue
        pins.append(name)
    return pins


def placement_def(lef: Path | str, cell: str) -> Tuple[str, Dict[str, str]]:
    """A DEF placing ``cell`` the way step 7 does, and ``{instance: orientation}``.

    Each row reads ``NEIGHBOUR | cell | cell | NEIGHBOUR``, abutted, with the row
    and the cells on the site and track grid exactly as in the chip: origins on
    multiples of 0.48 um and of the 3.78 um row height, tracks at offset 0.
    """
    try:
        geometry = lef_macro_geometry(lef, cell)
    except MetricsError as exc:
        raise PinAccessError(f"cannot place {cell}: {exc}") from exc
    width = round(geometry.width_um * 1000)
    height = round(ROW_HEIGHT_UM * 1000)
    site = round(SITE_WIDTH_UM * 1000)
    pins = signal_pins(lef, cell)

    margin = 4 * site
    components: List[Tuple[str, str, int, int, str]] = []
    nets: Dict[str, List[Tuple[str, str]]] = {}
    instances: Dict[str, str] = {}
    for row, orient in enumerate(ROW_ORIENTATIONS):
        x, y = margin, (row + 1) * height
        for slot, (master, span) in enumerate(
            [(NEIGHBOUR, NEIGHBOUR_WIDTH_NM), (cell, width), (cell, width),
             (NEIGHBOUR, NEIGHBOUR_WIDTH_NM)]
        ):
            name = f"{'cell' if master == cell else 'pdk'}_{orient}_{slot}"
            components.append((name, master, x, y, orient))
            for pin in pins if master == cell else NEIGHBOUR_PINS:
                nets[f"{name}_{pin}"] = [(name, pin)]
            if master == cell:
                instances[name] = orient
            x += span
    die_w = x + margin
    die_h = (len(ROW_ORIENTATIONS) + 2) * height

    lines = [
        "VERSION 5.8 ;",
        'DIVIDERCHAR "/" ;',
        'BUSBITCHARS "[]" ;',
        "DESIGN pin_access ;",
        "UNITS DISTANCE MICRONS 1000 ;",
        f"DIEAREA ( 0 0 ) ( {die_w} {die_h} ) ;",
    ]
    for row, orient in enumerate(ROW_ORIENTATIONS):
        lines.append(
            f"ROW ROW_{row} CoreSite 0 {(row + 1) * height} {orient} "
            f"DO {die_w // site} BY 1 STEP {site} 0 ;"
        )
    for layer, ((x_off, x_pitch), (y_off, y_pitch)) in TRACKS_NM.items():
        lines.append(f"TRACKS X {x_off} DO {(die_w - x_off) // x_pitch + 1} "
                     f"STEP {x_pitch} LAYER {layer} ;")
        lines.append(f"TRACKS Y {y_off} DO {(die_h - y_off) // y_pitch + 1} "
                     f"STEP {y_pitch} LAYER {layer} ;")
    lines.append(f"COMPONENTS {len(components)} ;")
    lines.extend(f"- {name} {master} + FIXED ( {x} {y} ) {orient} ;"
                 for name, master, x, y, orient in components)
    lines.append("END COMPONENTS")
    lines.append(f"NETS {len(nets)} ;")
    lines.extend(f"- {net} " + " ".join(f"( {inst} {pin} )" for inst, pin in terms) + " ;"
                 for net, terms in nets.items())
    lines += ["END NETS", "END DESIGN"]
    return "\n".join(lines) + "\n", instances


def grade_log(
    text: str, cell: str, instances: Dict[str, str], pins: Sequence[str]
) -> PinAccessReport:
    """Grade what OpenROAD printed for the design :func:`placement_def` wrote.

    ``DRT-0073`` is logged once per pin with no access point before the command
    gives up, so every such pin is named, with the rows it failed in.
    """
    done = _DONE_RE.search(text)
    if done is None:
        return PinAccessReport(cell, RESULT_ERROR, (
            "OpenROAD did not finish the pin access script; its output ends:\n"
            + "\n".join(text.strip().splitlines()[-15:]),
        ))

    unreached: Dict[str, List[str]] = {}
    for inst, pin in _NO_ACCESS_RE.findall(text):
        if inst in instances:
            unreached.setdefault(pin, []).append(instances[inst])
    others = sorted({m.group(0).strip() for m in _ERROR_RE.finditer(text)
                     if "DRT-0073" not in m.group(0)})
    if others:
        return PinAccessReport(cell, RESULT_ERROR, (
            "OpenROAD reported errors pin access does not explain: " + "; ".join(others[:5]),
        ))

    if done.group(1) != "0":
        if not unreached:
            return PinAccessReport(cell, RESULT_ERROR, (
                "pin_access failed without naming a pin (no DRT-0073)",
            ))
        return PinAccessReport(cell, RESULT_FAIL, tuple(
            _no_access_point(pin, rows) for pin, rows in unreached.items()
        ))

    seen: Dict[Tuple[str, str], List[Tuple[float, float, str]]] = {}
    for inst, pin, count, points in _AP_RE.findall(text):
        if inst not in instances:
            continue
        seen[inst, pin] = [
            (int(x) / 1000.0, int(y) / 1000.0, layer)
            for x, y, layer in (point.split(",") for point in points.split())
        ][: int(count)]
    missing = [f"{inst}/{pin}" for inst in instances for pin in pins if (inst, pin) not in seen]
    if missing:
        return PinAccessReport(cell, RESULT_ERROR, (
            "pin_access ran but reported nothing for " + ", ".join(missing[:6]),
        ))
    empty: Dict[str, List[str]] = {}
    for (inst, pin), points in seen.items():
        if not points:
            empty.setdefault(pin, []).append(instances[inst])
    if empty:
        return PinAccessReport(cell, RESULT_FAIL, tuple(
            _no_access_point(pin, rows) for pin, rows in empty.items()
        ))

    first = next(inst for inst, orient in instances.items() if orient == ROW_ORIENTATIONS[0])
    return PinAccessReport(cell, RESULT_PASS, access_points={
        pin: tuple(seen[first, pin]) for pin in pins
    })


def _no_access_point(pin: str, rows: Sequence[str]) -> str:
    placed = " and ".join(sorted(set(rows), key=ROW_ORIENTATIONS.index))
    return (
        f"PIN {pin}: TritonRoute finds no access point with the cell placed "
        f"{placed} between PDK cells (OpenROAD pin_access, 'DRT-0073 No access "
        "point'), so step 7 aborts in detailed routing. It only tries vias on "
        "tracks, half tracks, the pin centre and positions aligning the "
        "enclosure with the pin, so a port the static via check passes can still "
        "miss here: give the via more room on the port's layer and the one above, "
        "or widen the port across a track"
    )


def run_pin_access(
    lef: Path | str,
    cell: str,
    work_dir: Path | str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
) -> PinAccessReport:
    """Run OpenROAD ``pin_access`` on ``cell`` placed as in step 7, and grade it.

    ``work_dir`` is wiped and rewritten: it holds the DEF, the script and the
    log of this run only, so nothing an earlier run left can be read as this
    run's evidence.
    """
    lef_path = Path(lef)
    work = Path(work_dir)
    try:
        pins = signal_pins(lef_path, cell)
        design, instances = placement_def(lef_path, cell)
    except (OSError, KeyError, PinAccessError) as exc:
        return PinAccessReport(cell, RESULT_ERROR, (f"cannot build the design: {exc}",))

    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    def_path = work / f"{cell}.pin_access.def"
    def_path.write_text(design)
    script = work / "pin_access.tcl"
    script.write_text(_SCRIPT.format(
        lef=rel_to_tool(lef_path), def_=rel_to_tool(def_path), cell=cell,
        bottom=ROUTING_LAYERS[0], top=ROUTING_LAYERS[1],
    ))

    result = run_in_container(
        f"openroad -no_init -no_splash -exit {rel_to_tool(script)}", timeout=timeout
    )
    log = work / "pin_access.log"
    log.write_text(result.output)
    if result.status == 125 or result.timed_out:
        return PinAccessReport(cell, RESULT_ERROR, (
            "OpenROAD could not run: " + result.output.strip().splitlines()[-1],
        ), log=log)
    report = grade_log(result.output, cell, instances, pins)
    return dc.replace(report, log=log)


__all__ = [
    "NEIGHBOUR",
    "RESULT_ERROR",
    "RESULT_FAIL",
    "RESULT_PASS",
    "ROUTING_LAYERS",
    "PinAccessError",
    "PinAccessReport",
    "grade_log",
    "placement_def",
    "run_pin_access",
    "signal_pins",
]
