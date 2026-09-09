# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The abutted PDK-cell row the AION cell must beat
# ================================================================

"""The reference layout: the same logic, built by abutting PDK standard cells.

An AION cell only means something next to the thing it replaces, and the thing
it replaces is not a number in a datasheet -- it is a row of PDK standard cells
placed side by side and wired together, which somebody has to draw, DRC and LVS
before it can be quoted as a baseline.  This module draws it, and it draws it
with deterministic code so the comparison is a measurement rather than an
opinion: same PDK cells, same rules, same DRC and LVS runs, same area function.

Three decisions are worth recording, because each of them is a place where a
plausible shortcut would have produced a baseline that flatters or slanders the
AION cell:

**The row is flattened, not instantiated.**  Every shape of every placed cell is
copied into one top cell, translated by the placement offset.  Magic's extractor
and the DRC decks then see exactly the geometry a placer would produce after
abutment -- merged rails, merged wells, merged implants -- instead of a
hierarchy whose cell boundaries hide the interactions that abutment creates.

**The instances' own labels and pin shapes are dropped.**  Three PDK cells in a
row carry three texts saying ``Y`` on three different nets; copying them would
hand Netgen a layout in which one net name means three things.  The row gets one
new set of labels, taken from the *gate-level* netlist's ports, and internal
nets stay deliberately anonymous.

**A via that cannot be proven legal is an unrouted net, not a drawn guess.**
Every Via1 is checked against the metal it lands on before it is drawn -- V1.a
(exactly 190 nm), V1.c (>= 10 nm Metal1 enclosure everywhere) and V1.c1 (>= 50 nm
on at least one full axis, which is what the deck's ``one_side_allowed,
two_opposite_sides_allowed`` endcap check permits for a via sitting in a narrow
line).  A pin whose metal cannot host such a via puts its net in
``unrouted_nets`` with the reason in ``notes``; it never becomes a DRC violation
for somebody else to find later.

All coordinates in this module are nanometres, matching the rest of the
framework and the 1 nm database unit of the GDS files it reads.
"""

from __future__ import annotations

import dataclasses as dc
import re
from bisect import bisect_right
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import klayout.db as pya

from . import metrics
from .cell import Cell, Port
from .metrics import CellGeometry
from .primitives import Point, Rect
from .runner import TOOL_DIR
from .shapes import PolygonShape, RectShape, TextShape
from .tech import Layer, Tech, sg13g2_tech


class BaselineError(RuntimeError):
    """Raised when the abutted reference row cannot be built or proven."""


# --------------------------------------------------------------------------
# The numbers the row is drawn to.  Every one of them is a design rule from
# context/drc/docs/, not a preference, so they are named after the rule.
# --------------------------------------------------------------------------

#: Standard-cell row height; every SG13G2 core cell is exactly this tall.
ROW_HEIGHT_NM = 3780
#: ``CoreSite`` pitch: a row-legal cell width is a multiple of this.
SITE_WIDTH_NM = 480
#: Drawing grid the offgrid deck enforces on every polygon layer.
GRID_NM = 5

#: V1.a -- Via1 width is both the minimum *and* the maximum, so it is exact.
VIA1_SIZE_NM = 190
#: V1.b -- minimum Via1 space.
VIA1_SPACE_NM = 220
#: V1.c -- minimum Metal1 enclosure of Via1, required on all four sides.
VIA1_SIDE_ENCL_NM = 10
#: V1.c1 / M2.c1 -- endcap enclosure.  Demanded on at least one full axis.
VIA1_ENDCAP_ENCL_NM = 50

#: M2.a -- minimum Metal2 width, used for the horizontal trunks.
M2_WIDTH_NM = 200
#: M2.b -- minimum Metal2 space and notch.
M2_SPACE_NM = 210
#: M2.d -- minimum Metal2 area, in nm^2.  A 200 nm trunk needs 720 nm of length.
M2_MIN_AREA_NM2 = 144_000
#: Vertical Metal2 stubs are drawn wide enough to enclose a Via1 by the endcap
#: distance on *all* four sides, so no reading of M2.c/M2.c1 can be violated.
M2_STUB_WIDTH_NM = VIA1_SIZE_NM + 2 * VIA1_ENDCAP_ENCL_NM

#: Directions the top-level ports are given, by role.
_PORT_DIRECTIONS = {"power": "POWER", "ground": "GROUND",
                    "output": "OUTPUT", "input": "INPUT"}


# --------------------------------------------------------------------------
# Public result types
# --------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class Instance:
    """One PDK standard cell instantiated by the gate-level netlist.

    ``x_offset_nm`` is ``None`` until :func:`build_abutted_layout` places the
    instance.  It is deliberately not defaulted to ``0.0``: zero is a perfectly
    good offset for the leftmost cell, and a caller must never read "not yet
    placed" as "placed at the origin".
    """

    name: str
    cell: str
    conns: Mapping[str, str]
    x_offset_nm: Optional[float] = None

    def placed_at(self, x_offset_nm: float) -> "Instance":
        """Return a copy of this instance placed with its left edge at ``x``."""
        return dc.replace(self, x_offset_nm=float(x_offset_nm))


@dc.dataclass(frozen=True)
class BaselineResult:
    """Everything the abutted row is, measured from the file that was written."""

    cell: str
    gds: Path
    lvs_netlist: Path
    instances: Tuple[Instance, ...]
    geometry: CellGeometry
    routed_nets: Mapping[str, float]
    unrouted_nets: Tuple[str, ...]
    notes: Tuple[str, ...]

    @property
    def complete(self) -> bool:
        """True only when every signal net was routed and the row is legal.

        A baseline with an unrouted net is not a smaller baseline -- it is not a
        baseline at all, because the layout it describes does not implement the
        netlist.  Callers gate on this rather than on the file existing.
        """
        return not self.unrouted_nets and self.geometry.row_legal

    def describe(self) -> str:
        """One line for a report: what was built and whether it is usable."""
        state = "complete" if self.complete else "INCOMPLETE"
        return (
            f"{self.geometry.describe()} -- {len(self.instances)} abutted cells, "
            f"{len(self.routed_nets)} routed nets, {state}"
        )


# --------------------------------------------------------------------------
# SPICE: the gate-level netlist and the PDK cells it names
# --------------------------------------------------------------------------

_SUBCKT_RE = re.compile(r"^\.subckt\s+(\S+)\s*(.*)$", re.IGNORECASE)
_ENDS_RE = re.compile(r"^\.ends\b", re.IGNORECASE)


def _logical_lines(text: str) -> List[str]:
    """Return SPICE lines with comments stripped and continuations joined."""
    out: List[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith(("*", ";")):
            continue
        stripped = line.strip()
        if stripped.startswith("+"):
            if not out:
                raise BaselineError("continuation line before any statement")
            out[-1] = out[-1] + " " + stripped[1:].strip()
        else:
            out.append(stripped)
    return out


def _subckt_blocks(text: str) -> Dict[str, Tuple[List[str], List[str]]]:
    """Return ``{name: (ports, body lines)}`` for every ``.subckt`` in ``text``."""
    blocks: Dict[str, Tuple[List[str], List[str]]] = {}
    name: Optional[str] = None
    ports: List[str] = []
    body: List[str] = []
    for line in _logical_lines(text):
        match = _SUBCKT_RE.match(line)
        if match:
            if name is not None:
                raise BaselineError(f"nested .subckt inside {name!r}")
            name = match.group(1)
            ports = [p for p in match.group(2).split() if "=" not in p]
            body = []
            continue
        if _ENDS_RE.match(line):
            if name is None:
                raise BaselineError(".ends without a matching .subckt")
            blocks[name] = (ports, body)
            name = None
            continue
        if name is not None:
            body.append(line)
    if name is not None:
        raise BaselineError(f".subckt {name!r} is never closed by .ends")
    return blocks


def _context_dir(context_dir: Optional[Path | str]) -> Path:
    """Return the directory holding the PDK reference views."""
    path = Path(context_dir) if context_dir is not None else TOOL_DIR / "context"
    if not path.is_dir():
        raise BaselineError(f"no PDK context directory at {path}")
    return path


def _pdk_subckt(cell: str, context: Path) -> Tuple[List[str], str]:
    """Return ``(port order, verbatim .subckt block)`` for one PDK cell.

    A SPICE ``X`` line is positional: the only thing that says which position is
    which pin is the instantiated cell's own ``.subckt`` line, so it is read
    rather than guessed from the pin names.
    """
    path = context / "spice" / f"{cell}.spice"
    if not path.is_file():
        raise BaselineError(
            f"instance cell {cell!r} has no SPICE view at {path}; its pin order "
            "is unknown and a positional X line cannot be resolved without it"
        )
    text = path.read_text(errors="replace")
    blocks = _subckt_blocks(text)
    if cell not in blocks:
        raise BaselineError(
            f"{path} defines no .subckt {cell!r} (it defines: "
            + ", ".join(sorted(blocks)) + ")"
        )
    ports = blocks[cell][0]
    if not ports:
        raise BaselineError(f".subckt {cell!r} in {path} declares no pins")

    # Keep the definition verbatim: the LVS netlist has to carry the device
    # parameters the PDK wrote, not a re-rendering of them.
    lines = text.splitlines()
    start = end = None
    for i, line in enumerate(lines):
        match = _SUBCKT_RE.match(line.strip())
        if match and match.group(1) == cell:
            start = i
        elif start is not None and _ENDS_RE.match(line.strip()):
            end = i
            break
    if start is None or end is None:
        raise BaselineError(f"cannot delimit the .subckt {cell!r} block in {path}")
    return ports, "\n".join(lines[start:end + 1])


def parse_gate_netlist(
    path: Path | str,
    cell_name: Optional[str] = None,
    *,
    context_dir: Optional[Path | str] = None,
) -> Tuple[str, List[str], List[Instance]]:
    """Parse a gate-level netlist of PDK standard cells.

    Returns ``(subckt name, ports, instances)``.  Each :class:`Instance` carries
    the positional connections resolved against the instantiated cell's own
    ``.subckt`` pin order, read from ``context/spice/<cell>.spice``.  An
    instance whose cell has no SPICE view, or whose connection count disagrees
    with that view, is refused rather than resolved by position alone.
    """
    path = Path(path)
    if not path.is_file():
        raise BaselineError(f"no gate-level netlist at {path}")
    context = _context_dir(context_dir)

    blocks = _subckt_blocks(path.read_text(errors="replace"))
    if not blocks:
        raise BaselineError(f"{path} defines no .subckt")
    if cell_name is None:
        cell_name = next(iter(blocks))
    if cell_name not in blocks:
        raise BaselineError(
            f"{path} defines no .subckt {cell_name!r}; it defines: "
            + ", ".join(sorted(blocks))
        )
    ports, body = blocks[cell_name]
    if not ports:
        raise BaselineError(f".subckt {cell_name!r} in {path} declares no ports")

    instances: List[Instance] = []
    for line in body:
        tokens = [t for t in line.split() if "=" not in t]
        if not tokens or not tokens[0].upper().startswith("X"):
            raise BaselineError(
                f"{path}: {line!r} is not a subcircuit instance; a gate-level "
                "netlist for the abutted baseline may only instantiate PDK cells"
            )
        inst_name, *rest = tokens
        if len(rest) < 2:
            raise BaselineError(f"{path}: instance line {line!r} names no cell")
        cell = rest[-1]
        nets = rest[:-1]
        pin_order, _ = _pdk_subckt(cell, context)
        if len(nets) != len(pin_order):
            raise BaselineError(
                f"{path}: instance {inst_name} connects {len(nets)} nets to "
                f"{cell}, which declares {len(pin_order)} pins "
                f"({' '.join(pin_order)})"
            )
        instances.append(
            Instance(name=inst_name, cell=cell, conns=dict(zip(pin_order, nets)))
        )

    if not instances:
        raise BaselineError(f".subckt {cell_name!r} in {path} instantiates nothing")
    return cell_name, list(ports), instances


def write_lvs_netlist(
    gate_netlist: Path | str,
    out_path: Path | str,
    *,
    context_dir: Optional[Path | str] = None,
    cell_name: Optional[str] = None,
    top_name: Optional[str] = None,
) -> Path:
    """Write the netlist Netgen compares the abutted row against.

    It is the gate-level ``.subckt`` followed by the verbatim ``.subckt`` of
    every PDK cell it instantiates, so Netgen has a definition for every device
    it will meet.  The top subcircuit is renamed to ``top_name`` because
    ``sak-lvs.sh`` matches the schematic's top subcircuit to the GDS top cell by
    name, and the GDS top cell is named after the file it is written to.
    """
    gate_netlist = Path(gate_netlist)
    out_path = Path(out_path)
    context = _context_dir(context_dir)
    subckt, ports, instances = parse_gate_netlist(
        gate_netlist, cell_name, context_dir=context
    )
    top = top_name or f"{subckt}_abutted"

    lines = [
        "* Abutted PDK standard-cell reference for " + subckt,
        "* Generated by aion_layout.baseline from " + gate_netlist.name,
        "* Top subcircuit renamed to match the GDS top cell Netgen is given.",
        "",
        f".subckt {top} {' '.join(ports)}",
    ]
    for inst in instances:
        pin_order, _ = _pdk_subckt(inst.cell, context)
        nets = " ".join(inst.conns[pin] for pin in pin_order)
        lines.append(f"{inst.name} {nets} {inst.cell}")
    lines += [".ends", ""]

    emitted: List[str] = []
    for inst in instances:
        if inst.cell in emitted:
            continue
        emitted.append(inst.cell)
        _, block = _pdk_subckt(inst.cell, context)
        lines += ["* --- PDK cell " + inst.cell + " ---", block, ""]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    return out_path


# --------------------------------------------------------------------------
# GDS: reading one PDK cell
# --------------------------------------------------------------------------

#: Datatypes that carry pin shapes and label texts rather than mask geometry.
#: They are read for pin discovery and then deliberately left behind.
_PIN_DATATYPE = 2
_LABEL_DATATYPE = 25
_PRBOUNDARY_PAIR = (189, 4)
_METAL1_PAIR = (8, 0)


@dc.dataclass(frozen=True)
class _PdkCell:
    """One PDK standard cell, read out of its GDS and ready to be placed."""

    name: str
    width_nm: int
    boundary_source: str
    geometry: Mapping[Tuple[int, int], pya.Region]
    pins: Mapping[str, pya.Region]
    labels: Mapping[str, pya.Point]
    notes: Tuple[str, ...]


def _own_region(source: pya.Region) -> pya.Region:
    """Return a copy of ``source`` that owns its shapes.

    A ``pya.Region`` built from a ``RecursiveShapeIterator`` reads its polygons
    back out of the ``pya.Layout`` it came from, and ``merged()`` hands that
    lazy region straight back when there is nothing to merge -- a single shape
    on the layer.  The moment the Layout is collected, such a region silently
    reads as empty: not an exception, not a warning, just a mask layer that
    quietly stops existing.  Copying the polygons into a fresh Region cuts the
    tie to the Layout, so a caller may outlive the file it read.
    """
    out = pya.Region()
    out.insert(source)
    return out


def _region_of(cell: pya.Cell, layout: pya.Layout, pair: Tuple[int, int]) -> pya.Region:
    """Return the merged polygon region on one layer/datatype pair."""
    index = layout.find_layer(*pair)
    if index is None:
        return pya.Region()
    return _own_region(pya.Region(cell.begin_shapes_rec(index)).merged())


def _texts_of(cell: pya.Cell, layout: pya.Layout,
              pair: Tuple[int, int]) -> Dict[str, pya.Point]:
    """Return ``{text: position}`` for the texts on one layer/datatype pair."""
    index = layout.find_layer(*pair)
    out: Dict[str, pya.Point] = {}
    if index is None:
        return out
    iterator = cell.begin_shapes_rec(index)
    while not iterator.at_end():
        shape = iterator.shape()
        if shape.is_text():
            text = shape.text.transformed(iterator.trans())
            out.setdefault(text.string, pya.Point(text.x, text.y))
        iterator.next()
    return out


def _read_pdk_cell(cell: str, context: Path) -> _PdkCell:
    """Read one PDK standard cell: footprint, mask geometry and pin metal."""
    path = context / "gds" / f"{cell}.gds"
    if not path.is_file():
        raise BaselineError(f"no GDS view for {cell!r} at {path}")
    layout = pya.Layout()
    try:
        layout.read(str(path))
    except Exception as exc:  # pragma: no cover - corrupt input
        raise BaselineError(f"cannot read {path}: {exc}") from exc
    if abs(layout.dbu - 0.001) > 1e-9:
        raise BaselineError(
            f"{path} has a {layout.dbu} um database unit; this module places "
            "cells in nanometres and will not silently rescale one"
        )
    top = layout.cell(cell)
    if top is None:
        tops = layout.top_cells()
        if len(tops) != 1:
            raise BaselineError(
                f"{path} has no cell {cell!r} and {len(tops)} top cells"
            )
        top = tops[0]

    notes: List[str] = []

    # Mask geometry: everything except the pin/label datatypes and the
    # per-cell prBoundary, which the row replaces with one of its own.
    geometry: Dict[Tuple[int, int], pya.Region] = {}
    for index in layout.layer_indexes():
        info = layout.get_info(index)
        pair = (info.layer, info.datatype)
        if pair == _PRBOUNDARY_PAIR or info.datatype in (_PIN_DATATYPE, _LABEL_DATATYPE):
            continue
        region = _own_region(pya.Region(top.begin_shapes_rec(index)).merged())
        if not region.is_empty():
            geometry[pair] = region
    if _METAL1_PAIR not in geometry:
        raise BaselineError(f"{path} draws no Metal1; it cannot be a standard cell")
    metal1 = geometry[_METAL1_PAIR]

    # Footprint.  The prBoundary is the answer when it is drawn; without one the
    # power rail spans the placement width exactly, which is the only other
    # thing in the cell that does.
    boundary = _region_of(top, layout, _PRBOUNDARY_PAIR)
    if not boundary.is_empty():
        box = boundary.bbox()
        if box.left != 0 or box.bottom != 0:
            raise BaselineError(
                f"{cell}: prBoundary starts at ({box.left},{box.bottom}) nm, not "
                "the origin; abutment offsets assume a boundary at the origin"
            )
        width_nm = box.width()
        height_nm = box.height()
        boundary_source = "prBoundary"
    else:
        width_nm = None
        height_nm = ROW_HEIGHT_NM
        boundary_source = "power rail span"

    # Labels, and the Metal1 each one names.
    labels = _texts_of(top, layout, (8, _LABEL_DATATYPE))
    if not labels:
        labels = _texts_of(top, layout, (8, _PIN_DATATYPE))
        if labels:
            notes.append(f"{cell}: pin names read from 8/{_PIN_DATATYPE} texts; "
                         f"the cell draws no 8/{_LABEL_DATATYPE} labels")
    if not labels:
        raise BaselineError(f"{cell}: no Metal1 labels; its pins cannot be located")

    pin_shapes = _region_of(top, layout, (8, _PIN_DATATYPE))
    if not pin_shapes.is_empty() and not (pin_shapes - metal1).is_empty():
        notes.append(
            f"{cell}: some 8/{_PIN_DATATYPE} pin geometry is not covered by "
            "drawn Metal1; only the covered part is offered as via landing metal"
        )
    source = (pin_shapes & metal1) if not pin_shapes.is_empty() else metal1
    if source.is_empty():
        source = metal1

    pins: Dict[str, pya.Region] = {}
    for name, point in sorted(labels.items()):
        chosen = _polygon_at(source, point)
        if chosen is None:
            chosen = _polygon_at(metal1, point)
            if chosen is not None:
                notes.append(
                    f"{cell}: label {name!r} is not inside any pin shape; matched "
                    "to the drawn Metal1 polygon that contains it"
                )
        if chosen is None:
            chosen, distance = _nearest_polygon(source, point)
            if chosen is None:
                raise BaselineError(
                    f"{cell}: label {name!r} at ({point.x},{point.y}) nm matches "
                    "no Metal1 polygon at all"
                )
            notes.append(
                f"{cell}: label {name!r} lies outside every Metal1 polygon; "
                f"matched to the nearest one, {distance} nm away"
            )
        pins[name] = pya.Region(chosen) & metal1

    if width_nm is None:
        rail = pins.get("VDD") or pins.get("VSS")
        if rail is None or rail.is_empty():
            raise BaselineError(
                f"{cell}: no prBoundary and no VDD/VSS rail, so the placement "
                "width cannot be measured"
            )
        width_nm = rail.bbox().width()
        notes.append(
            f"{cell}: draws no prBoundary; placement width {width_nm} nm taken "
            "from the power rail span"
        )

    if width_nm % SITE_WIDTH_NM:
        raise BaselineError(
            f"{cell}: placement width {width_nm} nm is not a multiple of the "
            f"{SITE_WIDTH_NM} nm site pitch; abutting it would break the row"
        )
    if height_nm != ROW_HEIGHT_NM:
        raise BaselineError(
            f"{cell}: cell height {height_nm} nm is not the {ROW_HEIGHT_NM} nm "
            "row height; it cannot be abutted into this row"
        )

    return _PdkCell(
        name=cell,
        width_nm=int(width_nm),
        boundary_source=boundary_source,
        geometry=geometry,
        pins=pins,
        labels=labels,
        notes=tuple(notes),
    )


def _polygon_at(region: pya.Region, point: pya.Point) -> Optional[pya.Polygon]:
    """Return the polygon of ``region`` that contains ``point``, if any."""
    for poly in region.each():
        if poly.inside(point):
            return poly
    return None


def _nearest_polygon(region: pya.Region,
                     point: pya.Point) -> Tuple[Optional[pya.Polygon], int]:
    """Return the polygon whose bounding box is closest to ``point``."""
    best: Optional[pya.Polygon] = None
    best_distance = 0
    for poly in region.each():
        box = poly.bbox()
        dx = max(box.left - point.x, 0, point.x - box.right)
        dy = max(box.bottom - point.y, 0, point.y - box.top)
        distance = dx + dy
        if best is None or distance < best_distance:
            best, best_distance = poly, distance
    return best, best_distance


# --------------------------------------------------------------------------
# Rectangles inside a rectilinear region
# --------------------------------------------------------------------------


def _fits(region: pya.Region, box: pya.Box) -> bool:
    """True when ``box`` has positive area and lies wholly inside ``region``."""
    if box.width() <= 0 or box.height() <= 0:
        return False
    return (pya.Region(box) - region).is_empty()


def _region_coords(region: pya.Region) -> Tuple[List[int], List[int]]:
    """Return the sorted x and y coordinates of every vertex in ``region``."""
    xs, ys = set(), set()
    for poly in region.each():
        for point in poly.each_point_hull():
            xs.add(point.x)
            ys.add(point.y)
        for hole in range(poly.holes()):
            for point in poly.each_point_hole(hole):
                xs.add(point.x)
                ys.add(point.y)
    return sorted(xs), sorted(ys)


def _seed_cell(xs: List[int], ys: List[int], point: pya.Point) -> Optional[pya.Box]:
    """Return the grid cell of the vertex lattice that contains ``point``."""
    if len(xs) < 2 or len(ys) < 2:
        return None
    i = min(max(bisect_right(xs, point.x) - 1, 0), len(xs) - 2)
    j = min(max(bisect_right(ys, point.y) - 1, 0), len(ys) - 2)
    return pya.Box(xs[i], ys[j], xs[i + 1], ys[j + 1])


def _grow(region: pya.Region, box: pya.Box, xs: List[int], ys: List[int],
          x_first: bool) -> pya.Box:
    """Grow ``box`` inside ``region`` along the vertex lattice.

    A maximal axis-aligned rectangle inside a rectilinear region has its edges
    on region vertex coordinates, so stepping through those coordinates finds
    the same answer an exhaustive search would, in a few dozen boolean tests.
    """
    def expand(current: pya.Box, horizontal: bool) -> pya.Box:
        if horizontal:
            for x in [v for v in xs if v > current.right]:
                candidate = pya.Box(current.left, current.bottom, x, current.top)
                if not _fits(region, candidate):
                    break
                current = candidate
            for x in [v for v in reversed(xs) if v < current.left]:
                candidate = pya.Box(x, current.bottom, current.right, current.top)
                if not _fits(region, candidate):
                    break
                current = candidate
        else:
            for y in [v for v in ys if v > current.top]:
                candidate = pya.Box(current.left, current.bottom, current.right, y)
                if not _fits(region, candidate):
                    break
                current = candidate
            for y in [v for v in reversed(ys) if v < current.bottom]:
                candidate = pya.Box(current.left, y, current.right, current.top)
                if not _fits(region, candidate):
                    break
                current = candidate
        return current

    box = expand(box, x_first)
    return expand(box, not x_first)


def _rect_inside(region: pya.Region, point: pya.Point) -> Optional[pya.Box]:
    """Return a maximal rectangle of ``region`` containing ``point``."""
    if region.is_empty():
        return None
    xs, ys = _region_coords(region)
    seed = _seed_cell(xs, ys, point)
    if seed is None or not _fits(region, seed):
        centre = region.bbox().center()
        seed = _seed_cell(xs, ys, centre)
        if seed is None or not _fits(region, seed):
            return None
    candidates = [_grow(region, seed, xs, ys, True),
                  _grow(region, seed, xs, ys, False)]
    return max(candidates, key=lambda b: b.width() * b.height())


# --------------------------------------------------------------------------
# Via placement
# --------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class _ViaSite:
    """A proven-legal Via1 position on one instance pin."""

    net: str
    instance: str
    pin: str
    centre_x: int
    centre_y: int
    encl_x: int
    encl_y: int

    @property
    def box(self) -> pya.Box:
        half = VIA1_SIZE_NM // 2
        return pya.Box(self.centre_x - half, self.centre_y - half,
                       self.centre_x + half, self.centre_y + half)


def _via_site(region: pya.Region, target_y: int, net: str, instance: str,
              pin: str) -> Tuple[Optional[_ViaSite], str]:
    """Place one Via1 in ``region``, as close to ``target_y`` as it will go.

    Returns ``(site, reason)``; ``site`` is ``None`` when no position in the pin
    metal satisfies V1.c on all four sides and V1.c1 on a full axis, and
    ``reason`` then says which.

    All three legal enclosure shapes are offered at once and the *closest* legal
    position wins, rather than the most generously enclosed one.  Ranking by
    enclosure instead put vias in the wide stub of an L-shaped pin when the
    narrow arm reached the trunk directly, which is legal, ugly, and blocks the
    channel for every net that has to cross it.
    """
    half = VIA1_SIZE_NM // 2
    attempts = [
        (VIA1_ENDCAP_ENCL_NM, VIA1_ENDCAP_ENCL_NM),
        (VIA1_SIDE_ENCL_NM, VIA1_ENDCAP_ENCL_NM),
        (VIA1_ENDCAP_ENCL_NM, VIA1_SIDE_ENCL_NM),
    ]
    tried: List[str] = []
    best: Optional[Tuple[Tuple[int, int, int], int, int, int]] = None
    for rank, (encl_x, encl_y) in enumerate(attempts):
        core = region.sized(-(half + encl_x), -(half + encl_y), 2).merged()
        if core.is_empty():
            tried.append(f"{encl_x}/{encl_y} nm: no room")
            continue
        for poly in core.each():
            box = poly.bbox()
            cy = min(max(target_y, box.bottom), box.top)
            cx = box.center().x
            cx -= cx % GRID_NM
            cy -= cy % GRID_NM
            cx = min(max(cx, box.left), box.right)
            cy = min(max(cy, box.bottom), box.top)
            if not poly.inside(pya.Point(cx, cy)):
                continue
            via = pya.Box(cx - half, cy - half, cx + half, cy + half)
            if not _fits(region, via.enlarged(encl_x, encl_y)):
                continue
            # Distance is compared in whole track pitches: a via that saves
            # less than one pitch of stub has saved nothing worth trading a
            # DRC margin for, so the stronger enclosure wins that tie.
            distance = abs(cy - target_y)
            key = (distance // (M2_WIDTH_NM + M2_SPACE_NM), rank, distance)
            if best is None or key < best[0]:
                best = (key, cx, cy, rank)
    if best is None:
        box = region.bbox()
        return None, (
            f"{instance}/{pin} on net {net}: Metal1 {box.width()}x{box.height()} "
            f"nm cannot enclose a {VIA1_SIZE_NM} nm Via1 (" + ", ".join(tried) + ")"
        )
    _, cx, cy, rank = best
    encl_x, encl_y = attempts[rank]
    return _ViaSite(net=net, instance=instance, pin=pin, centre_x=cx,
                    centre_y=cy, encl_x=encl_x, encl_y=encl_y), ""


# --------------------------------------------------------------------------
# Metal2 routing
# --------------------------------------------------------------------------


def _merge_spans(spans: Sequence[Tuple[int, int]], gap: int) -> List[Tuple[int, int]]:
    """Merge x-intervals separated by less than ``gap``.

    Two stubs closer than M2.b would leave a notch in the merged Metal2 shape,
    which the deck reports exactly like a spacing error.  Closing the gap is
    both legal and what a router would do.
    """
    merged: List[Tuple[int, int]] = []
    for lo, hi in sorted(spans):
        if merged and lo - merged[-1][1] < gap:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def _net_metal2(sites: Sequence[_ViaSite], track_y: int,
                x_limits: Tuple[int, int]) -> Tuple[pya.Region, List[str]]:
    """Build the Metal2 of one net: a trunk on ``track_y`` plus a stub per via."""
    problems: List[str] = []
    half_trunk = M2_WIDTH_NM // 2
    half_stub = M2_STUB_WIDTH_NM // 2
    trunk_bottom = track_y - half_trunk
    trunk_top = track_y + half_trunk

    spans = _merge_spans(
        [(s.centre_x - half_stub, s.centre_x + half_stub) for s in sites],
        M2_SPACE_NM,
    )
    region = pya.Region()
    for lo, hi in spans:
        bottom = trunk_bottom
        top = trunk_top
        for site in sites:
            if lo <= site.centre_x <= hi:
                bottom = min(bottom, site.centre_y - VIA1_SIZE_NM // 2
                             - VIA1_ENDCAP_ENCL_NM)
                top = max(top, site.centre_y + VIA1_SIZE_NM // 2
                          + VIA1_ENDCAP_ENCL_NM)
        region.insert(pya.Box(lo, bottom, hi, top))

    left = min(lo for lo, _ in spans)
    right = max(hi for _, hi in spans)
    # M2.d: a minimum-width trunk has to be at least 720 nm long to carry the
    # minimum area, so a short net is stretched inside the row before it is
    # declared unroutable.
    shortfall = M2_MIN_AREA_NM2 - (right - left) * M2_WIDTH_NM
    if shortfall > 0:
        extra = -(-shortfall // (2 * M2_WIDTH_NM))
        extra += (-extra) % GRID_NM
        left = max(x_limits[0], left - extra)
        right = min(x_limits[1], right + extra)
    region.insert(pya.Box(left, trunk_bottom, right, trunk_top))
    region = region.merged()

    if region.area() < M2_MIN_AREA_NM2:
        problems.append(
            f"Metal2 area {region.area()} nm^2 is below the M2.d minimum "
            f"{M2_MIN_AREA_NM2} nm^2 even after stretching the trunk to the "
            "row edges"
        )
    if not region.notch_check(M2_SPACE_NM).is_empty():
        problems.append(f"Metal2 shape notches closer than M2.b ({M2_SPACE_NM} nm)")
    if not region.width_check(M2_WIDTH_NM).is_empty():
        problems.append(f"Metal2 shape narrower than M2.a ({M2_WIDTH_NM} nm)")
    return region, problems


def _tracks(band_bottom: int, band_top: int) -> List[int]:
    """Return the Metal2 track centre lines between the two power rails."""
    pitch = M2_WIDTH_NM + M2_SPACE_NM
    first = band_bottom + M2_WIDTH_NM // 2
    tracks: List[int] = []
    y = first
    while y + M2_WIDTH_NM // 2 <= band_top:
        tracks.append(y)
        y += pitch
    return tracks


def _tracks_by_cost(tracks: Sequence[int], pins: Sequence[Tuple[object, str, pya.Region]]
                    ) -> List[int]:
    """Order tracks by the total vertical stub length a net would spend on them.

    A net put on the first free track from the bottom drags a stub the height of
    the cell across every other net's channel; a net put on the track its own
    pins already reach spends almost no vertical wire and blocks almost nothing.
    Ties break on the track ordinal so the assignment stays reproducible.
    """
    def cost(track_y: int) -> Tuple[int, int]:
        total = 0
        for _, _, region in pins:
            box = region.bbox()
            total += max(box.bottom - track_y, 0, track_y - box.top)
        return total, track_y
    return sorted(tracks, key=cost)


@dc.dataclass(frozen=True)
class _RoutePlan:
    """One complete attempt at wiring every signal net of the row."""

    strategy: str
    routed: Mapping[str, float]
    unrouted: Tuple[str, ...]
    sites: Mapping[str, Tuple[_ViaSite, ...]]
    reasons: Mapping[str, Tuple[str, ...]]
    metal2: pya.Region
    via1: pya.Region

    @property
    def rank(self) -> Tuple[int, int]:
        """Sort key: fewest unrouted nets first, then least Metal2 spent."""
        return (len(self.unrouted), int(self.metal2.area()))


def _route_once(strategy: str, nets: Sequence[str], net_pins: Mapping[str, list],
                tracks: Sequence[int], total_width: int, bottom_up: bool,
                metal2_blocked: pya.Region,
                via1_blocked: pya.Region) -> _RoutePlan:
    """Assign every net a track, in the order given, first fit wins.

    ``metal2_blocked`` and ``via1_blocked`` are the Metal2 and Via1 the *placed
    cells* already contain.  Most SG13G2 core cells are Metal1-only, so these
    are usually empty; a sequential cell is not, and a router that only checked
    its own wires against each other would happily lay a trunk straight through
    a flip-flop's internal Metal2 and hand Netgen a short.
    """
    routed: Dict[str, float] = {}
    unrouted: List[str] = []
    sites_by_net: Dict[str, Tuple[_ViaSite, ...]] = {}
    reasons: Dict[str, Tuple[str, ...]] = {}
    metal2 = pya.Region()
    via1 = pya.Region()

    for net in nets:
        why: List[str] = []
        order = (list(tracks) if bottom_up
                 else _tracks_by_cost(tracks, net_pins[net]))
        for track_y in order:
            sites: List[_ViaSite] = []
            blocked = False
            for inst, pin, region in net_pins[net]:
                site, reason = _via_site(region, track_y, net, inst.name, pin)
                if site is None:
                    why.append(reason)
                    blocked = True
                    break
                sites.append(site)
            if blocked:
                break  # a pin with no legal via fails on every track
            shape, problems = _net_metal2(sites, track_y, (0, total_width))
            if problems:
                why.append(f"track y={track_y} nm: " + "; ".join(problems))
                continue
            clash = ""
            for other, what in ((metal2, "another net's Metal2"),
                                (metal2_blocked, "Metal2 already in a placed cell")):
                if other.is_empty():
                    continue
                if not (other & shape).is_empty():
                    clash = f"overlaps {what}"
                elif not other.separation_check(shape, M2_SPACE_NM).is_empty():
                    clash = (f"closer than M2.b ({M2_SPACE_NM} nm) to {what}")
                if clash:
                    break
            if clash:
                why.append(f"track y={track_y} nm: " + clash)
                continue
            new_vias = pya.Region()
            for site in sites:
                new_vias.insert(site.box)
            for other, what in ((via1, "another net's Via1"),
                                (via1_blocked, "Via1 already in a placed cell")):
                if other.is_empty():
                    continue
                if not (other & new_vias).is_empty():
                    clash = f"lands on {what}"
                elif not other.separation_check(new_vias, VIA1_SPACE_NM).is_empty():
                    clash = f"closer than V1.b ({VIA1_SPACE_NM} nm) to {what}"
                if clash:
                    break
            if clash:
                why.append(f"track y={track_y} nm: Via1 " + clash)
                continue
            metal2 = (metal2 + shape).merged()
            via1 += new_vias
            routed[net] = float(track_y)
            sites_by_net[net] = tuple(sites)
            break
        if net not in routed:
            unrouted.append(net)
            reasons[net] = tuple(why)

    return _RoutePlan(strategy=strategy, routed=routed, unrouted=tuple(unrouted),
                      sites=sites_by_net, reasons=reasons, metal2=metal2, via1=via1)


def _best_plan(nets: Sequence[str], net_pins: Mapping[str, list],
               tracks: Sequence[int], total_width: int,
               metal2_blocked: pya.Region,
               via1_blocked: pya.Region) -> _RoutePlan:
    """Try a fixed set of orderings and keep the best result.

    First fit on one ordering is a coin toss: the net that happens to go first
    takes the track its own pins like best and can leave a later net with no
    legal crossing, even though swapping the two would have wired both.  The
    orderings below are tried in a fixed sequence and the best outcome wins, so
    the router is stronger than first fit and still completely reproducible.
    """
    def left(net: str) -> int:
        return min(r.bbox().left for _, _, r in net_pins[net])

    def span(net: str) -> int:
        boxes = [r.bbox() for _, _, r in net_pins[net]]
        return max(b.right for b in boxes) - min(b.left for b in boxes)

    orderings = [
        ("left-edge order, nearest track", sorted(nets, key=lambda n: (left(n), n)),
         False),
        ("longest net first, nearest track",
         sorted(nets, key=lambda n: (-span(n), n)), False),
        ("shortest net first, nearest track",
         sorted(nets, key=lambda n: (span(n), n)), False),
        ("left-edge order, lowest track", sorted(nets, key=lambda n: (left(n), n)),
         True),
        ("longest net first, lowest track",
         sorted(nets, key=lambda n: (-span(n), n)), True),
    ]
    best: Optional[_RoutePlan] = None
    for name, order, bottom_up in orderings:
        plan = _route_once(name, order, net_pins, tracks, total_width, bottom_up,
                           metal2_blocked, via1_blocked)
        if best is None or plan.rank < best.rank:
            best = plan
        if not plan.unrouted:
            break
    if best is None:  # pragma: no cover - orderings is a non-empty constant
        raise BaselineError("no routing strategy was tried; nothing was wired")
    return best


# --------------------------------------------------------------------------
# Building the row
# --------------------------------------------------------------------------


def _layer_for(pair: Tuple[int, int], tech: Tech) -> Layer:
    """Return the tech layer for a GDS pair, or an ad-hoc one that names it."""
    for layer in tech.layers.values():
        if layer.gds_pair == pair:
            return layer
    return Layer(name=f"L{pair[0]}D{pair[1]}", gds_layer=pair[0],
                 gds_datatype=pair[1])


def _emit_region(cell: Cell, layer: Layer, region: pya.Region) -> None:
    """Add every polygon of ``region`` to ``cell`` on ``layer``."""
    for poly in region.merged().each():
        if poly.holes() > 0:
            poly = poly.resolved_holes()
        points = [Point(p.x, p.y) for p in poly.each_point_hull()]
        if len(points) == 4:
            xs = {p.x for p in points}
            ys = {p.y for p in points}
            if len(xs) == 2 and len(ys) == 2:
                cell.add_shape(RectShape(
                    layer, Rect.from_lbrt(min(xs), min(ys), max(xs), max(ys))))
                continue
        cell.add_shape(PolygonShape(layer, points))


def build_abutted_layout(
    gate_netlist: Path | str,
    out_gds: Path | str,
    *,
    cell_name: Optional[str] = None,
    subckt_name: Optional[str] = None,
    order: Optional[Sequence[str]] = None,
    context_dir: Optional[Path | str] = None,
    tech: Optional[Tech] = None,
    lvs_netlist: Optional[Path | str] = None,
) -> BaselineResult:
    """Place the netlist's PDK cells in one abutting row and wire them up.

    The cells are placed left to right in netlist order (or ``order``) with each
    left edge on the previous right edge, so the power rails, wells and implants
    merge exactly as they would under a placer.  Signal nets are routed on
    Metal2 trunks between the rails, dropping a Via1 on each instance pin.  The
    footprint in the result is measured from the GDS that was written, not from
    the placement arithmetic that produced it.
    """
    tech = tech or sg13g2_tech
    context = _context_dir(context_dir)
    gate_netlist = Path(gate_netlist)
    out_gds = Path(out_gds)
    top_name = cell_name or out_gds.stem

    subckt, ports, instances = parse_gate_netlist(
        gate_netlist, subckt_name, context_dir=context
    )
    if order is not None:
        wanted = list(order)
        if sorted(wanted) != sorted(i.name for i in instances):
            raise BaselineError(
                "order must be a permutation of the instance names "
                f"{[i.name for i in instances]}; got {wanted}"
            )
        by_name = {i.name: i for i in instances}
        instances = [by_name[name] for name in wanted]

    notes: List[str] = []
    pdk_cells: Dict[str, _PdkCell] = {}
    for inst in instances:
        if inst.cell not in pdk_cells:
            pdk_cells[inst.cell] = _read_pdk_cell(inst.cell, context)
            notes.extend(pdk_cells[inst.cell].notes)

    # ---------------------------------------------------------- placement --
    placed: List[Instance] = []
    x = 0
    for inst in instances:
        placed.append(inst.placed_at(x))
        x += pdk_cells[inst.cell].width_nm
    total_width = x
    notes.append(f"source: {gate_netlist.name} .subckt {subckt}")
    notes.append("row: " + " | ".join(
        f"{i.name}={i.cell}@{int(i.x_offset_nm)}nm"
        f"+{pdk_cells[i.cell].width_nm}nm[{pdk_cells[i.cell].boundary_source}]"
        for i in placed))

    # ------------------------------------------------------ flat geometry --
    geometry: Dict[Tuple[int, int], pya.Region] = {}
    for inst in placed:
        pdk = pdk_cells[inst.cell]
        dx = int(inst.x_offset_nm)
        for pair, region in pdk.geometry.items():
            geometry.setdefault(pair, pya.Region()).insert(region.moved(dx, 0))
    for pair in list(geometry):
        geometry[pair] = geometry[pair].merged()
    metal1_all = geometry[_METAL1_PAIR]

    # ------------------------------------------------------------ the nets --
    net_pins: Dict[str, List[Tuple[Instance, str, pya.Region]]] = {}
    for inst in placed:
        pdk = pdk_cells[inst.cell]
        dx = int(inst.x_offset_nm)
        for pin, net in inst.conns.items():
            if pin not in pdk.pins:
                raise BaselineError(
                    f"{inst.cell}: SPICE declares pin {pin!r} but the GDS has no "
                    f"label for it (it labels: {', '.join(sorted(pdk.pins))})"
                )
            net_pins.setdefault(net, []).append(
                (inst, pin, pdk.pins[pin].moved(dx, 0))
            )

    power_nets = {inst.conns["VDD"] for inst in placed if "VDD" in inst.conns}
    ground_nets = {inst.conns["VSS"] for inst in placed if "VSS" in inst.conns}
    if len(power_nets) != 1 or len(ground_nets) != 1:
        raise BaselineError(
            f"the instances disagree about the rails: VDD on {sorted(power_nets)}, "
            f"VSS on {sorted(ground_nets)}"
        )
    vdd_net = power_nets.pop()
    vss_net = ground_nets.pop()

    dangling = sorted(n for n, pins in net_pins.items() if len(pins) < 2
                      and n not in ports)
    if dangling:
        raise BaselineError(
            "internal nets with a single connection: " + ", ".join(dangling)
        )
    missing = [p for p in ports if p not in net_pins]
    if missing:
        raise BaselineError(
            "top-level ports that no instance connects to: " + ", ".join(missing)
        )

    # ------------------------------------------------------------- rails ---
    rails: Dict[str, pya.Box] = {}
    for net, pin in ((vdd_net, "VDD"), (vss_net, "VSS")):
        first = placed[0]
        label = pdk_cells[first.cell].labels.get(pin)
        if label is None:
            raise BaselineError(f"{first.cell}: no {pin} label to seed the rail")
        rail = _rect_inside(metal1_all, label)
        if rail is None:
            raise BaselineError(f"cannot find the {pin} rail rectangle in the row")
        if rail.left != 0 or rail.right != total_width:
            raise BaselineError(
                f"the {pin} rail spans x {rail.left}..{rail.right} nm, not the "
                f"whole 0..{total_width} nm row: the cells do not abut"
            )
        rails[net] = rail
    band_bottom = rails[vss_net].top
    band_top = rails[vdd_net].bottom
    tracks = _tracks(band_bottom, band_top)
    if not tracks:
        raise BaselineError(
            f"no Metal2 track fits between the rails (y {band_bottom}..{band_top} nm)"
        )

    # ------------------------------------------------------------ routing ---
    signal_nets = [n for n in net_pins
                   if n not in (vdd_net, vss_net) and len(net_pins[n]) > 1]
    metal2_blocked = geometry.get(tech["Metal2"].gds_pair, pya.Region())
    via1_blocked = geometry.get(tech["Via1"].gds_pair, pya.Region())
    if not metal2_blocked.is_empty():
        notes.append(
            f"routing obstacles: {metal2_blocked.count()} Metal2 and "
            f"{via1_blocked.count()} Via1 polygons already drawn by the placed "
            "cells; the router keeps M2.b and V1.b away from all of them"
        )
    plan = _best_plan(signal_nets, net_pins, tracks, total_width,
                      metal2_blocked, via1_blocked)
    routed = dict(plan.routed)
    unrouted = list(plan.unrouted)
    metal2 = plan.metal2
    via1 = plan.via1
    notes.append(f"routing: {plan.strategy} won "
                 f"({len(plan.routed)} of {len(signal_nets)} nets)")
    for net in sorted(plan.sites):
        for site in plan.sites[net]:
            notes.append(
                f"net {net}: Via1 at ({site.centre_x},{site.centre_y}) nm on "
                f"{site.instance}/{site.pin}, Metal1 enclosure proven to be at "
                f"least {site.encl_x} nm in x and {site.encl_y} nm in y"
            )
    for net in unrouted:
        notes.append(f"net {net} UNROUTED: " + "; ".join(plan.reasons.get(net, ())))

    single = [n for n in net_pins
              if n not in (vdd_net, vss_net) and len(net_pins[n]) == 1]
    for net in sorted(single):
        notes.append(
            f"net {net}: one connection only, labelled in place with no Metal2"
        )

    # --------------------------------------------------------- the output --
    out = Cell(top_name, tech)
    boundary = Rect.from_lbrt(0, 0, total_width, ROW_HEIGHT_NM)
    out.set_boundary(boundary)
    out.add_shape(RectShape(_layer_for(_PRBOUNDARY_PAIR, tech), boundary))
    for pair, region in sorted(geometry.items()):
        _emit_region(out, _layer_for(pair, tech), region)
    if not metal2.is_empty():
        _emit_region(out, tech["Metal2"], metal2)
    if not via1.is_empty():
        _emit_region(out, tech["Via1"], via1)

    metal1 = tech["Metal1"]
    metal1_pin = Layer(name=f"{metal1.name}.pin", gds_layer=metal1.gds_layer,
                       gds_datatype=metal1.pin_datatype)
    output_nets, direction_notes = _output_nets(placed, ports, context)
    notes.extend(direction_notes)

    for port_net in ports:
        if port_net == vdd_net:
            rect, role = rails[vdd_net], "power"
        elif port_net == vss_net:
            rect, role = rails[vss_net], "ground"
        else:
            role = "output" if port_net in output_nets else "input"
            inst, pin, region = min(net_pins[port_net],
                                    key=lambda t: (t[2].bbox().left, t[0].name))
            label = pdk_cells[inst.cell].labels[pin]
            seed = pya.Point(label.x + int(inst.x_offset_nm), label.y)
            rect = _rect_inside(region, seed)
            if rect is None:
                raise BaselineError(
                    f"port {port_net}: no rectangle inside the Metal1 of "
                    f"{inst.name}/{pin} to carry its label"
                )
        if not _fits(metal1_all, rect):
            raise BaselineError(
                f"port {port_net}: pin rectangle {rect} is not covered by drawn "
                "Metal1 (Pin.e)"
            )
        pin_rect = Rect.from_lbrt(rect.left, rect.bottom, rect.right, rect.top)
        centre = Point(rect.center().x, rect.center().y)
        out.add_shape(RectShape(metal1_pin, pin_rect))
        out.add_shape(TextShape(metal1, port_net, centre, purpose="label"))
        out.add_port(Port(name=port_net, net=port_net, layer=metal1,
                          rect=pin_rect, direction=_PORT_DIRECTIONS[role]))

    out.write_gds(out_gds)

    lvs_path = Path(lvs_netlist) if lvs_netlist is not None else \
        out_gds.with_suffix(".lvs.spice")
    write_lvs_netlist(gate_netlist, lvs_path, context_dir=context,
                      cell_name=subckt_name, top_name=top_name)

    # This row always draws its own prBoundary, so a measurement that had to
    # fall back to the shape bounding box would mean the file is not the file
    # this function wrote -- an error, not a smaller number.
    measured = metrics.gds_boundary(out_gds, top_name, tech,
                                    allow_bbox_fallback=False)
    notes.extend(f"footprint: {p}" for p in measured.problems)
    if unrouted:
        notes.append(
            "this row does not implement the netlist: "
            + ", ".join(unrouted) + " carry no wire"
        )

    return BaselineResult(
        cell=top_name,
        gds=out_gds,
        lvs_netlist=lvs_path,
        instances=tuple(placed),
        geometry=measured,
        routed_nets=dict(routed),
        unrouted_nets=tuple(unrouted),
        notes=tuple(notes),
    )


def _output_pins(cell: str, context: Path) -> Tuple[frozenset, Optional[str]]:
    """Return the output pins of a PDK cell, read from its transistors.

    An output is the pin a device pair drives -- one connected to both a PMOS
    and an NMOS drain -- which is a fact in the netlist rather than a convention
    about the letter ``Y``.  When the devices do not settle it, the second
    element of the pair explains why and the caller records that the port
    directions are a fallback.
    """
    path = context / "spice" / f"{cell}.spice"
    try:
        from .spice_parser import parse_spice_file
        subckts = [s for s in parse_spice_file(path) if s.name == cell]
    except Exception as exc:  # a device the small parser does not model
        return frozenset(), f"{cell}: devices unreadable ({exc})"
    if not subckts or not subckts[0].devices:
        return frozenset(), f"{cell}: no transistors to identify an output pin"
    subckt = subckts[0]
    rails = {subckt.vdd_net, subckt.vss_net}
    outputs = {
        pin for pin in subckt.pins
        if pin not in rails
        and any(d.drain == pin for d in subckt.pmos_devices)
        and any(d.drain == pin for d in subckt.nmos_devices)
    }
    if not outputs:
        return frozenset(), f"{cell}: no pin is driven by both a PMOS and an NMOS"
    return frozenset(outputs), None


def _output_nets(instances: Sequence[Instance], ports: Sequence[str],
                 context: Path) -> Tuple[set, List[str]]:
    """Return the top-level ports some instance drives, and any complaints."""
    driven: set = set()
    notes: List[str] = []
    seen: Dict[str, frozenset] = {}
    for inst in instances:
        if inst.cell not in seen:
            outputs, problem = _output_pins(inst.cell, context)
            seen[inst.cell] = outputs
            if problem:
                notes.append(
                    problem + "; ports it drives are declared INPUT by default"
                )
        driven |= {inst.conns[pin] for pin in seen[inst.cell] if pin in inst.conns}
    return {p for p in ports if p in driven}, notes


__all__ = [
    "BaselineError",
    "BaselineResult",
    "Instance",
    "M2_MIN_AREA_NM2",
    "M2_SPACE_NM",
    "M2_STUB_WIDTH_NM",
    "M2_WIDTH_NM",
    "ROW_HEIGHT_NM",
    "SITE_WIDTH_NM",
    "VIA1_SIZE_NM",
    "VIA1_SPACE_NM",
    "build_abutted_layout",
    "parse_gate_netlist",
    "write_lvs_netlist",
]
