# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Geometry measured from the artifacts themselves
# ================================================================

"""Area and geometry, read out of the GDS and the LEF the tools consumed.

Every number the flow reports about size comes from here, and every one of them
is measured from an artifact rather than computed from the generator that wrote
it.  A generator says what it meant to draw; the GDS is what Magic, KLayout and
Netgen actually read, and the LEF is what the placer will read.  When those two
disagree the disagreement is the finding, so both are measured and compared
rather than one being trusted.

The area that goes into the Liberty ``area`` attribute is the **placement**
area -- the prBoundary, or equivalently the LEF ``SIZE`` -- not the bounding box
of the drawn shapes.  A standard cell's wells and implants deliberately overhang
the boundary so that abutted neighbours share them; grading a cell on its shape
bbox would charge it for geometry its neighbour also pays for, and would make a
cell look larger the better it abuts.
"""

from __future__ import annotations

import bisect
import dataclasses as dc
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .tech import Tech, sg13g2_tech

#: SG13G2 ``CoreSite``: the placement grid a core cell has to land on.
SITE_WIDTH_UM = 0.48
#: SG13G2 row height.  One ``CoreSite`` row; every core cell is exactly this tall.
ROW_HEIGHT_UM = 3.78
#: Tolerance for a dimension that has to be a multiple of the site, in um.
#: The GDS database unit is 1 nm, so anything under half a nanometre is noise.
GRID_TOL_UM = 5e-4

#: SG13G2 routing tracks, from
#: ``libs.tech/librelane/sg13g2_stdcell/tracks.info``: ``<layer> X 0.0 0.48``
#: and ``<layer> Y 0.0 0.42`` on every Metal.  ``(offset, pitch)`` in um.
TRACK_UM = {"x": (0.0, 0.48), "y": (0.0, 0.42)}

#: Routing layer -> the axis of the track lines a pin drawn on it can cover,
#: taken from ``DIRECTION`` in ``sg13g2_tech.lef``.  A wire runs *along* its
#: layer's preferred direction, so it can stop at any coordinate on that axis
#: but is pinned to a track on the other one: a HORIZONTAL layer routes along
#: y = n * 0.42, a VERTICAL layer along x = n * 0.48.  A pin on such a line is
#: the easy case for the router; one off it is reached by a via that overlaps
#: it from the nearest line, when there is room (see :func:`lef_pin_access`).
ROUTING_AXIS = {
    "Metal1": "y",      # DIRECTION HORIZONTAL
    "Metal2": "x",      # DIRECTION VERTICAL
    "Metal3": "y",      # DIRECTION HORIZONTAL
    "Metal4": "x",      # DIRECTION VERTICAL
    "Metal5": "y",      # DIRECTION HORIZONTAL
}

#: Pins the router never touches, so pin access is not graded on them.
#: Matched by ``USE`` first; the names are the fallback for a LEF that omits
#: it, which is what magic writes.
POWER_PIN_NAMES = frozenset({"VDD", "VSS"})

#: The two metal shapes of every ``DEFAULT`` ``ViaN`` (N = 1..4) in
#: ``sg13g2_tech.lef``, as ``((enclosure on the metal below w, h), (pad on the
#: metal above w, h))`` in um: ``ViaN_XX``, ``_XY``, ``_YX`` and ``_YY``.  The
#: ``_s`` variants and ``Via1_s`` only have bigger pads, so they reach no port
#: these four cannot.
VIA_SHAPES_UM = (
    ((0.29, 0.21), (0.29, 0.20)),
    ((0.29, 0.21), (0.20, 0.29)),
    ((0.21, 0.29), (0.29, 0.20)),
    ((0.21, 0.29), (0.20, 0.29)),
)

#: The smallest entry of each routing metal's ``SPACINGTABLE``.  The smallest,
#: because that keeps :func:`lef_pin_access` a *necessary* condition: a pin it
#: rejects is one the router cannot reach, never one it merely might not.
METAL_SPACING_UM = {
    "Metal1": 0.18,
    "Metal2": 0.21,
    "Metal3": 0.21,
    "Metal4": 0.21,
    "Metal5": 0.21,
}

#: ``MANUFACTURINGGRID``.  Every via half-size above is a multiple of it, so a
#: via centre off this grid would put the via's own edges off it.
MANUFACTURING_GRID_UM = 0.005

#: The layer a via off a port lands on, so that the macro's own obstructions
#: there can be checked for sitting on top of it.  Metal5 is absent on purpose:
#: TopVia1 is a different animal and no cell pin is drawn that high.
LAYER_ABOVE = {
    "Metal1": "Metal2",
    "Metal2": "Metal3",
    "Metal3": "Metal4",
    "Metal4": "Metal5",
}

#: The power-rail tap contact grid, in nm.  Rows abut mirrored, so the VDD rail
#: of one row *is* the VDD rail of the row above it: the tap ``Cont`` cuts of
#: both cells land in the same band and have to be the same rectangles.  All
#: 2497 rail contacts of all 84 PDK ``sg13g2_stdcell`` cells sit at
#: ``160 + 480k .. 320 + 480k`` -- one per ``CoreSite``, centred in it -- with
#: no exception, so anything else partially overlaps a neighbour's and is a
#: ``Cnt.b`` / ``CntB.a1`` violation in the placed design.
TAP_CONT_PITCH_NM = 480.0
TAP_CONT_OFFSET_NM = 160.0
TAP_CONT_SIZE_NM = 160.0

#: Half-height of a VDD/VSS rail, in nm: it spans -220 .. 220 about the row
#: line.  Geometry reaching into that band is shared with the abutting row.
RAIL_HALF_NM = 220.0

#: Half the height, in um, of the pad each metal gets in the via stack the PDN
#: drops onto both rails wherever a ``TopMetal1`` strap crosses a row -- which
#: can be anywhere along a cell.  The pads are centred on the row line.
#: Measured from step 7's placed GDS (``VIA_via1_2_2200_440_1_5_410_410`` up to
#: ``VIA_via5_6_2200_440_1_2_840_840``): 1.84 x 0.29 um on Metal2 and Metal4,
#: 1.93 x 0.20 um on Metal3, 1.46 x 0.62 um on Metal5.  They follow from the
#: 0.44 um rail and the via enclosure rules, not from the cell, so a cell has
#: to leave them room: see :func:`lef_abutment_problems`.
PDN_RAIL_PAD_HALF_UM = {
    "Metal2": 0.145,
    "Metal3": 0.100,
    "Metal4": 0.145,
    "Metal5": 0.310,
}

#: ``WIDTH`` of each routing metal in ``sg13g2_tech.lef``: the narrowest wire the
#: router draws, so the narrowest gap between other nets' metal it can pass.
METAL_WIDTH_UM = {
    "Metal1": 0.16,
    "Metal2": 0.20,
    "Metal3": 0.20,
    "Metal4": 0.20,
    "Metal5": 0.20,
}

#: The fewest ``Metal3`` tracks a signal pin has to be able to put a ``Via2`` on.
#: One stalled detailed routing in step 7 and two routed clean: see
#: :func:`lef_pin_escape_problems`.
PIN_ESCAPE_TRACKS_MIN = 2


class MetricsError(RuntimeError):
    """Raised when a measurement cannot be taken from the artifact given."""


@dc.dataclass(frozen=True)
class CellGeometry:
    """The placement footprint of one cell, and whether it is row-legal.

    ``source`` names the artifact the numbers came from -- ``"prBoundary"``,
    ``"lef"`` or ``"bbox"`` -- because a fallback to the shape bounding box
    measures something different from the other two and must never be reported
    as though it were the placement area.
    """

    cell: str
    width_um: float
    height_um: float
    source: str
    #: Empty when the footprint is row-legal; otherwise every reason it is not.
    problems: Tuple[str, ...] = ()

    @property
    def area_um2(self) -> float:
        """Placement area, in um^2 -- the value the Liberty ``area`` takes."""
        return self.width_um * self.height_um

    @property
    def sites(self) -> float:
        """Width in ``CoreSite`` pitches.  Whole numbers are row-legal."""
        return self.width_um / SITE_WIDTH_UM

    @property
    def row_legal(self) -> bool:
        """True when the cell can be placed in a standard-cell row."""
        return not self.problems

    def describe(self) -> str:
        """One line, for a report or a verdict block."""
        return (
            f"{self.cell}: {self.width_um:.3f} x {self.height_um:.3f} um "
            f"= {self.area_um2:.4f} um^2 ({self.sites:.3g} sites, from {self.source})"
        )


def _grade_footprint(width_um: float, height_um: float) -> Tuple[str, ...]:
    """Return every reason this footprint cannot sit in a standard-cell row.

    The three checks are the ones ``output_constr.md`` says ``make pnr`` refuses
    on, and they are checked here rather than only at export because a cell that
    fails them is not merely unexportable -- it is the wrong size, and that is a
    floorplan fact worth knowing during iteration.
    """
    problems: List[str] = []
    if abs(height_um - ROW_HEIGHT_UM) > GRID_TOL_UM:
        problems.append(
            f"height {height_um:.4f} um is not the {ROW_HEIGHT_UM} um row height"
        )
    sites = width_um / SITE_WIDTH_UM
    if abs(sites - round(sites)) > GRID_TOL_UM / SITE_WIDTH_UM:
        problems.append(
            f"width {width_um:.4f} um is not a multiple of the "
            f"{SITE_WIDTH_UM} um site pitch ({sites:.4f} sites)"
        )
    if width_um <= 0 or height_um <= 0:
        problems.append(f"degenerate footprint {width_um} x {height_um} um")
    return tuple(problems)


def _top_cell(layout, cell_name: Optional[str], what: str):
    """Return the cell to measure, refusing to guess between several tops."""
    if cell_name:
        cell = layout.cell(cell_name)
        if cell is None:
            raise MetricsError(f"{what} has no cell named {cell_name!r}")
        return cell
    tops = layout.top_cells()
    if len(tops) != 1:
        names = ", ".join(sorted(c.name for c in tops)) or "(none)"
        raise MetricsError(
            f"{what} has {len(tops)} top cells ({names}); name the one to measure"
        )
    return tops[0]


def gds_boundary(
    gds_path: Path | str,
    cell_name: Optional[str] = None,
    tech: Optional[Tech] = None,
    *,
    allow_bbox_fallback: bool = True,
) -> CellGeometry:
    """Measure the placement footprint of a cell in ``gds_path``.

    The prBoundary layer is the answer when it is drawn.  Without one the shape
    bounding box is returned instead, tagged ``source="bbox"`` and carrying a
    problem line: the numbers are not wrong, but they are not the placement
    footprint either, and a caller that exports a LEF from them would publish a
    cell whose size disagrees with its own boundary.
    """
    tech = tech or sg13g2_tech
    path = Path(gds_path)
    if not path.is_file():
        raise MetricsError(f"no GDS at {path}")
    if path.stat().st_size == 0:
        raise MetricsError(f"{path} is empty")

    try:
        import klayout.db as pya
    except Exception as exc:  # pragma: no cover - klayout is a hard dependency
        raise MetricsError(f"klayout.db unavailable: {exc}") from exc

    layout = pya.Layout()
    try:
        layout.read(str(path))
    except Exception as exc:
        raise MetricsError(f"cannot read {path.name}: {exc}") from exc

    top = _top_cell(layout, cell_name, path.name)
    dbu = layout.dbu

    boundary = tech.get("prBoundary")
    if boundary is not None:
        index = layout.find_layer(*boundary.gds_pair)
        if index is not None:
            region = pya.Region(top.begin_shapes_rec(index)).merged()
            if not region.is_empty():
                box = region.bbox()
                width = box.width() * dbu
                height = box.height() * dbu
                return CellGeometry(
                    cell=top.name,
                    width_um=width,
                    height_um=height,
                    source="prBoundary",
                    problems=_grade_footprint(width, height),
                )

    if not allow_bbox_fallback:
        raise MetricsError(
            f"{path.name} draws no prBoundary; the placement footprint is "
            "undefined and the shape bounding box is not a substitute"
        )
    box = top.bbox()
    if box.empty():
        # An empty cell's bbox is KLayout's inverted "world" box, whose width()
        # underflows to about 4.29e6 um.  Reporting that as a footprint is how a
        # generator that drew nothing at all comes back as an enormous cell
        # instead of as a mistake.
        raise MetricsError(
            f"{path.name} cell {top.name!r} contains no geometry at all: there "
            "is no footprint to measure"
        )
    width = box.width() * dbu
    height = box.height() * dbu
    return CellGeometry(
        cell=top.name,
        width_um=width,
        height_um=height,
        source="bbox",
        problems=(
            "no prBoundary drawn: this is the bounding box of every shape, "
            "including well and implant overhang a neighbour would share, and "
            "is not the placement footprint",
        )
        + _grade_footprint(width, height),
    )


#: ``SIZE <w> BY <h> ;`` inside a LEF ``MACRO`` block.
_LEF_SIZE_RE = re.compile(
    r"^\s*SIZE\s+([0-9.eE+-]+)\s+BY\s+([0-9.eE+-]+)\s*;", re.MULTILINE
)
_LEF_MACRO_RE = re.compile(r"^\s*MACRO\s+(\S+)", re.MULTILINE)


def lef_macros(lef_path: Path | str) -> Dict[str, str]:
    """Return ``{macro name: macro body}`` for every MACRO in ``lef_path``."""
    text = Path(lef_path).read_text(errors="replace")
    macros: Dict[str, str] = {}
    starts = [(m.start(), m.group(1)) for m in _LEF_MACRO_RE.finditer(text)]
    for i, (start, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        macros[name] = text[start:end]
    return macros


def lef_macro_geometry(
    lef_path: Path | str,
    macro: Optional[str] = None,
) -> CellGeometry:
    """Measure the footprint the LEF publishes for ``macro``.

    This is what a placer will believe, so it is the number the comparison
    report quotes and the number the Liberty ``area`` is taken from.
    """
    path = Path(lef_path)
    if not path.is_file():
        raise MetricsError(f"no LEF at {path}")
    macros = lef_macros(path)
    if not macros:
        raise MetricsError(f"{path.name} defines no MACRO")
    if macro is None:
        if len(macros) != 1:
            names = ", ".join(sorted(macros))
            raise MetricsError(
                f"{path.name} defines {len(macros)} macros ({names}); "
                "name the one to measure"
            )
        macro = next(iter(macros))
    if macro not in macros:
        raise MetricsError(
            f"{path.name} defines no MACRO {macro!r}; it has: "
            + ", ".join(sorted(macros))
        )
    match = _LEF_SIZE_RE.search(macros[macro])
    if match is None:
        raise MetricsError(f"MACRO {macro} in {path.name} carries no SIZE line")
    width, height = float(match.group(1)), float(match.group(2))
    return CellGeometry(
        cell=macro,
        width_um=width,
        height_um=height,
        source="lef",
        problems=_grade_footprint(width, height),
    )


#: ``PIN <name> ... END <name>`` inside a LEF ``MACRO`` body.
_LEF_PIN_RE = re.compile(
    r"^[ \t]*PIN[ \t]+(\S+)[ \t]*$(.*?)^[ \t]*END[ \t]+\1[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
_LEF_LAYER_RE = re.compile(r"^\s*LAYER\s+(\S+)\s*;", re.MULTILINE)
_LEF_RECT_RE = re.compile(
    r"^\s*RECT\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+"
    r"([0-9.eE+-]+)\s+([0-9.eE+-]+)\s*;",
    re.MULTILINE,
)
_LEF_USE_RE = re.compile(r"^\s*USE\s+(\S+)\s*;", re.MULTILINE)
_LEF_POLYGON_RE = re.compile(r"^\s*POLYGON\b", re.MULTILINE)
#: The ``OBS`` block of a macro.  It runs to the first bare ``END``; ``END
#: <macro>`` carries a token after it and cannot close it by accident.
_LEF_OBS_RE = re.compile(
    r"^[ \t]*OBS[ \t]*$(.*?)^[ \t]*END[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


def _covers_track(lo_um: float, hi_um: float, axis: str) -> bool:
    """True when ``[lo, hi]`` contains a routing track line on ``axis``."""
    offset, pitch = TRACK_UM[axis]
    # First track at or above lo, then ask whether it is still inside.
    n = math.ceil((lo_um - offset) / pitch - GRID_TOL_UM / pitch)
    return offset + n * pitch <= hi_um + GRID_TOL_UM


def _layer_rects(block: str) -> List[Tuple[str, float, float, float, float]]:
    """Every RECT of a ``PORT`` or ``OBS`` block, as ``(layer, x1, y1, x2, y2)``."""
    rects: List[Tuple[str, float, float, float, float]] = []
    layer: Optional[str] = None
    for line in block.splitlines():
        layer_match = _LEF_LAYER_RE.match(line)
        if layer_match is not None:
            layer = layer_match.group(1)
            continue
        rect_match = _LEF_RECT_RE.match(line)
        if rect_match is None or layer is None:
            continue
        x1, y1, x2, y2 = (float(v) for v in rect_match.groups())
        rects.append((layer, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
    return rects


def _grid_points(lo: float, hi: float) -> range:
    """Indices of the manufacturing-grid points strictly inside ``(lo, hi)``."""
    grid = MANUFACTURING_GRID_UM
    return range(math.floor(lo / grid + 1e-6) + 1, math.ceil(hi / grid - 1e-6))


def _free_grid_point(lo: float, hi: float, spans) -> Optional[float]:
    """The lowest grid point in ``(lo, hi)`` outside every open span, or None.

    A point exactly on the end of a span is outside it: that is a via at
    exactly the minimum spacing, which is legal.
    """
    grid = MANUFACTURING_GRID_UM
    points = _grid_points(lo, hi)
    k = points.start
    while k < points.stop:
        at = k * grid
        covering = [end for start, end in spans if start + 1e-6 < at < end - 1e-6]
        if not covering:
            return at
        k = max(k + 1, math.ceil(max(covering) / grid - 1e-6))
    return None


def _via_fits(port, others, *, below: bool = True, above: bool = True) -> bool:
    """Whether some ViaN can connect to ``port`` with its metal clear of ``others``.

    ``port`` is ``(layer, x1, y1, x2, y2)`` in um, and ``others`` holds every
    shape of every *other* net in the macro in the same form -- its OBS and the
    other pins.  The via's enclosure has to overlap the port, and nothing more:
    it may hang off the port onto free metal.  That is how TritonRoute reaches a
    port whose own landing is crowded -- on ``AION_mux2_0/I0`` it put a
    ``Via1_YY`` whose cut overlaps the port by 35 nm, with the rest of the
    enclosure beside it and the Metal2 pad 0.265 um clear of the cell's strap.
    What neither shape may do is come within its layer's spacing of another
    net, measured the way spacing is: corner to corner, not as a square.

    The search runs over the manufacturing grid, where a via has to sit.  It
    accepts every position that is legal, including ones TritonRoute never
    tries (it only tries tracks, half tracks, the pin centre and positions that
    align the enclosure with the pin), so a pin it passes can still fail pin
    access when the only room is a few nanometres wide.  A pin it rejects,
    TritonRoute cannot reach.

    ``below=False`` or ``above=False`` ignores the other nets on that metal,
    which is how a caller finds out which of the two closes the door.
    """
    layer, x1, y1, x2, y2 = port
    upper = LAYER_ABOVE.get(layer)
    if upper is None:                     # topmost routing layer, nothing above
        return True
    for (below_w, below_h), (above_w, above_h) in VIA_SHAPES_UM:
        # Via centres at which the enclosure overlaps the port.
        box = (x1 - below_w / 2, y1 - below_h / 2, x2 + below_w / 2, y2 + below_h / 2)
        # Each shape of another net, grown by the via shape that has to clear
        # it, so that the question is how close the via *centre* may come.
        grown = []
        for other, ox1, oy1, ox2, oy2 in others:
            if other == layer and below:
                half_w, half_h, space = below_w / 2, below_h / 2, METAL_SPACING_UM[layer]
            elif other == upper and above:
                half_w, half_h, space = above_w / 2, above_h / 2, METAL_SPACING_UM[upper]
            else:
                continue
            grown.append((ox1 - half_w, oy1 - half_h, ox2 + half_w, oy2 + half_h, space))
        for kx in _grid_points(box[0], box[2]):
            cx = kx * MANUFACTURING_GRID_UM
            spans = []
            for gx1, gy1, gx2, gy2, space in grown:
                dx = max(gx1 - cx, cx - gx2, 0.0)
                if dx < space - 1e-6:
                    reach = math.sqrt(space * space - dx * dx)
                    spans.append((gy1 - reach, gy2 + reach))
            if _free_grid_point(box[1], box[3], spans) is not None:
                return True
    return False


def _no_via_access(name: str, ports, others) -> str:
    """Why no via reaches any port of pin ``name``, and what would make room."""
    layer = min((port[0] for port in ports), key=list(ROUTING_AXIS).index)
    upper = LAYER_ABOVE[layer]
    lowest = [port for port in ports if port[0] == layer]
    space, upper_space = METAL_SPACING_UM[layer], METAL_SPACING_UM[upper]
    if not any(_via_fits(port, others, below=False) for port in lowest):
        why = (
            f"every place for the via's {upper} pad is within {upper_space} um "
            f"of another net's {upper} -- OBS or another pin; metal written to "
            "OBS counts as another net even when it is this pin's own"
        )
        fix = (
            f"move that {upper} {upper_space} um clear of where a via can sit, or "
            f"declare the port on {upper} where the metal already is"
        )
    elif not any(_via_fits(port, others, above=False) for port in lowest):
        why = (
            f"the via's {layer} enclosure cannot overlap the port without coming "
            f"within {space} um of another net's {layer}"
        )
        fix = f"leave {layer} free beside the port for the enclosure to hang onto"
    else:
        why = (
            f"the positions whose {upper} pad clears the other nets put the "
            f"{layer} enclosure within {space} um of another net's {layer}, and "
            "the other way around"
        )
        fix = f"make room on one side of the port, on {layer} and {upper} both"
    return (
        f"PIN {name} has no via access: no ViaN can overlap the port with its "
        f"{layer} enclosure and keep both of its metal shapes clear of every other "
        f"net -- {why}. Detailed routing aborts with 'DRT-0073 No access point'; "
        f"{fix}"
    )


def tap_contact_problems(
    contacts: Iterable[Tuple[float, float, float, float]],
    cell_height_nm: float = ROW_HEIGHT_UM * 1000.0,
) -> Tuple[str, ...]:
    """Grade the power-rail tap contacts against the grid the PDK abuts on.

    Rows are placed mirrored and abutted, so a cell's VSS rail is the same
    piece of silicon as the VSS rail of the row below it, and the tap ``Cont``
    cuts of both cells land in one band.  Two cells using different grids put
    contacts *partially* on top of each other -- neither coincident nor spaced
    -- which is what Magic calls "this layer can't abut or partially overlap
    between subcells" and KLayout files as ``Cnt.b`` / ``CntB.a1``.

    None of that is visible in a cell on its own, which is why it is checked
    here from the geometry rather than left to a DRC deck: the cell-level run
    has no neighbour to collide with and passes clean.

    ``contacts`` are the drawn ``Cont`` rectangles in nm, from
    :func:`drawn_shapes`.
    """
    tol = GRID_TOL_UM * 1000.0
    off_grid = []
    for x1, y1, x2, y2 in contacts:
        in_rail = any(
            y1 < line + RAIL_HALF_NM and y2 > line - RAIL_HALF_NM
            for line in (0.0, cell_height_nm)
        )
        if not in_rail:
            continue
        phase = (x1 - TAP_CONT_OFFSET_NM) % TAP_CONT_PITCH_NM
        on_grid = min(phase, TAP_CONT_PITCH_NM - phase) < tol
        right_size = abs((x2 - x1) - TAP_CONT_SIZE_NM) < tol
        if not (on_grid and right_size):
            off_grid.append((x1, x2))

    if not off_grid:
        return ()

    shown = ", ".join(f"{x1:.0f}..{x2:.0f}" for x1, x2 in sorted(off_grid)[:4])
    more = f" and {len(off_grid) - 4} more" if len(off_grid) > 4 else ""
    return (
        f"{len(off_grid)} power-rail tap contact(s) are off the abutment grid "
        f"(x = {shown}{more} nm). Rows share their rails, so a tap Cont has to "
        f"be one of the neighbour's exactly: x = {TAP_CONT_OFFSET_NM:.0f} + "
        f"{TAP_CONT_PITCH_NM:.0f}k, {TAP_CONT_SIZE_NM:.0f} nm wide, one per "
        "site, which every PDK cell uses. Off it they partially overlap and "
        "the placed design fails Cnt.b / CntB.a1 -- invisible in this cell "
        "alone, which is why it is graded here",
    )


@dc.dataclass(frozen=True)
class PinAccess:
    """Whether every signal pin of a cell is reachable by the router."""

    cell: str
    #: ``{pin name: the track lines it covers}``, one entry per signal pin.
    #: Information, not a requirement: a via hanging off the port reaches a pin
    #: that covers none.
    reachable: Dict[str, Tuple[str, ...]]
    #: Empty when every signal pin can be reached; otherwise one per pin.
    problems: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.problems


def lef_pin_access(
    lef_path: Path | str,
    macro: Optional[str] = None,
) -> PinAccess:
    """Check that a via can reach every signal pin of ``macro``.

    This is the cheap, static half of what TritonRoute's pin access does, and it
    is kept a *necessary* condition: a pin it rejects is one detailed routing
    cannot enter, while a pin it passes can still fail pin access once the
    router's own choice of via positions is applied (see :func:`_via_fits`).

    Only one thing is required of a pin -- that some ViaN overlaps one of its
    routing-layer port rectangles with both metal shapes clear of every other
    net.  Covering a track and being 0.21 um across are *not* required, and this
    check used to require both.  TritonRoute pin access
    (OpenROAD 26Q3) reaches a Metal1 port 10 nm or 40 nm off the track grid, a
    0.18 um port and ``AION_mux2_0``'s I0/I1/I3, whenever the via has room to
    hang off the port; it finds no access point for ``AION_mux2i_1/I2``, a port
    boxed in by other nets' Metal1 and Metal2, or a port with an obstruction
    strap over it, and this check rejects exactly those.  The track lines a pin
    covers are still reported in :attr:`PinAccess.reachable`.

    Validated against ``libs.ref/sg13g2_stdcell/lef/sg13g2_stdcell.lef``: every
    signal pin of the PDK library passes.
    """
    path = Path(lef_path)
    macros = lef_macros(path)
    if not macros:
        raise MetricsError(f"{path.name} defines no MACRO")
    if macro is None:
        if len(macros) != 1:
            names = ", ".join(sorted(macros))
            raise MetricsError(
                f"{path.name} defines {len(macros)} macros ({names}); "
                "name the one to check"
            )
        macro = next(iter(macros))
    if macro not in macros:
        raise MetricsError(
            f"{path.name} defines no MACRO {macro!r}; it has: "
            + ", ".join(sorted(macros))
        )

    reachable: Dict[str, Tuple[str, ...]] = {}
    problems: List[str] = []

    obs_block = _LEF_OBS_RE.search(macros[macro])
    obs = _layer_rects(obs_block.group(1)) if obs_block else []
    pin_blocks = _LEF_PIN_RE.findall(macros[macro])
    # Every pin's shapes, so each pin is graded against the others: to the
    # router a neighbouring pin is another net exactly as an obstruction is.
    pin_rects = {pin: _layer_rects(pin_body) for pin, pin_body in pin_blocks}

    for name, body in pin_blocks:
        use = _LEF_USE_RE.search(body)
        if use is not None and use.group(1).upper() in ("POWER", "GROUND"):
            continue
        if use is None and name.upper() in POWER_PIN_NAMES:
            continue

        if _LEF_POLYGON_RE.search(body):
            # A POLYGON's bounding box covering a track does not mean the
            # polygon does, so this is "we could not tell", which is not a
            # pass.  Nothing in this flow emits one today.
            problems.append(
                f"PIN {name} is drawn with POLYGON geometry, which this check "
                "cannot measure; redraw the port as RECTs"
            )
            continue

        ports = [rect for rect in pin_rects[name] if rect[0] in ROUTING_AXIS]
        reachable[name] = tuple(dict.fromkeys(
            f"{layer} {ROUTING_AXIS[layer]}"
            for layer, x1, y1, x2, y2 in ports
            if _covers_track(
                *((y1, y2) if ROUTING_AXIS[layer] == "y" else (x1, x2)),
                ROUTING_AXIS[layer],
            )
        ))
        if not ports:
            problems.append(
                f"PIN {name} has no geometry on a routing layer "
                f"({', '.join(sorted(ROUTING_AXIS))}), so the router cannot "
                "reach it at all"
            )
            continue

        others = obs + [
            rect for pin, rects in pin_rects.items() if pin != name for rect in rects
        ]
        if not any(_via_fits(port, others) for port in ports):
            problems.append(_no_via_access(name, ports, others))

    return PinAccess(cell=macro, reachable=reachable, problems=tuple(problems))


def _shown_rects(offenders, clearance) -> str:
    """Up to three offending ``(owner, x1, y1, x2, y2)`` shapes, as LEF lines.

    Nearest first, by ``clearance(x1, y1, x2, y2)``: a strap running into the
    band is listed after the bar that sits in it, which is the one to move.
    """
    offenders = sorted(offenders, key=lambda shape: clearance(*shape[1:]))
    shown = ", ".join(
        f"{owner} RECT {x1:.3f} {y1:.3f} {x2:.3f} {y2:.3f}"
        for owner, x1, y1, x2, y2 in offenders[:3]
    )
    more = f" and {len(offenders) - 3} more" if len(offenders) > 3 else ""
    return shown + more


def lef_abutment_problems(
    lef_path: Path | str,
    macro: Optional[str] = None,
) -> Tuple[str, ...]:
    """Grade the metal a placed cell shares with its neighbours and the PDN.

    Two rules, both invisible in a cell on its own -- DRC-clean, LVS-clean, pin
    access clean -- and both measured in step 7 on cells that were:

    * **Metal2..Metal5 stay clear of the rail lines.**  The PDN drops a via
      stack onto both rails wherever a strap crosses a row, and its pads reach
      :data:`PDN_RAIL_PAD_HALF_UM` either side of the line.  A cell's metal must
      keep that plus the layer's spacing from y = 0 and from the top edge.
      Seven AION cells drew Metal2 at y = 0.11 um: 130 nets shorted to VGND
      and 111 ``M2.b`` / 4 ``M2.a`` errors.
    * **Every routing metal keeps half its spacing from the left and right
      edges**, because the neighbour abutted there is held to only the other
      half.  ``AION_xnor2_xor2_7`` drew Metal1 10 nm from its right edge: 50
      ``M1.b`` errors against the PDK cells beside it.  The VDD/VSS rails are
      exempt -- they are meant to join the neighbour's.

    Graded on every net, pins and OBS alike.  All 84 PDK ``sg13g2_stdcell``
    cells pass both.  ``collect_cells.check_abutment`` in aion_chip applies the
    same rules at publish and before PnR; the two must stay in step.
    """
    path = Path(lef_path)
    macros = lef_macros(path)
    if not macros:
        raise MetricsError(f"{path.name} defines no MACRO")
    if macro is None:
        if len(macros) != 1:
            names = ", ".join(sorted(macros))
            raise MetricsError(
                f"{path.name} defines {len(macros)} macros ({names}); "
                "name the one to check"
            )
        macro = next(iter(macros))
    if macro not in macros:
        raise MetricsError(
            f"{path.name} defines no MACRO {macro!r}; it has: "
            + ", ".join(sorted(macros))
        )
    body = macros[macro]
    size = _LEF_SIZE_RE.search(body)
    if size is None:
        raise MetricsError(f"MACRO {macro} in {path.name} carries no SIZE line")
    width, height = float(size.group(1)), float(size.group(2))

    shapes: List[Tuple[str, bool, Tuple[str, float, float, float, float]]] = []
    for name, pin_body in _LEF_PIN_RE.findall(body):
        use = _LEF_USE_RE.search(pin_body)
        power = (
            use.group(1).upper() in ("POWER", "GROUND")
            if use is not None
            else name.upper() in POWER_PIN_NAMES
        )
        shapes.extend((f"PIN {name}", power, rect) for rect in _layer_rects(pin_body))
    obs_block = _LEF_OBS_RE.search(body)
    if obs_block is not None:
        shapes.extend(("OBS", False, rect) for rect in _layer_rects(obs_block.group(1)))

    rail_half = RAIL_HALF_NM / 1000.0
    problems: List[str] = []
    for layer in ROUTING_AXIS:
        rects = [(owner, power, rect) for owner, power, rect in shapes if rect[0] == layer]

        keep = PDN_RAIL_PAD_HALF_UM.get(layer)
        if keep is not None:
            keep += METAL_SPACING_UM[layer]
            near = [
                (owner, x1, y1, x2, y2)
                for owner, _, (_, x1, y1, x2, y2) in rects
                if y1 < keep - GRID_TOL_UM or y2 > height - keep + GRID_TOL_UM
            ]
            if near:
                problems.append(
                    f"{layer} within {keep:.3f} um of a rail line: "
                    f"{_shown_rects(near, lambda x1, y1, x2, y2: min(y1, height - y2))}. Keep {layer} inside y = {keep:.3f} .. "
                    f"{height - keep:.3f}. In PnR the power grid drops a via stack "
                    f"onto both rails, anywhere along the cell, with a {layer} pad "
                    f"reaching {PDN_RAIL_PAD_HALF_UM[layer]:.3f} um from the rail "
                    f"line: nearer than {METAL_SPACING_UM[layer]} um to it is a "
                    "spacing error, touching it shorts the net to VDD or VSS -- "
                    "invisible in this cell alone"
                )

        half = METAL_SPACING_UM[layer] / 2.0
        edge = [
            (owner, x1, y1, x2, y2)
            for owner, power, (_, x1, y1, x2, y2) in rects
            if not (
                power
                and any(
                    y1 >= line - rail_half - GRID_TOL_UM
                    and y2 <= line + rail_half + GRID_TOL_UM
                    for line in (0.0, height)
                )
            )
            and (x1 < half - GRID_TOL_UM or x2 > width - half + GRID_TOL_UM)
        ]
        if edge:
            problems.append(
                f"{layer} within {half:.3f} um of the left or right cell edge: "
                f"{_shown_rects(edge, lambda x1, y1, x2, y2: min(x1, width - x2))}. "
                f"Keep {layer} inside x = {half:.3f} .. "
                f"{width - half:.3f} -- half the {METAL_SPACING_UM[layer]} um "
                "spacing, because the cell abutted on that side is held to only "
                "the other half; nearer, the placed design has a spacing error "
                "at every such abutment, invisible in this cell alone. The "
                "VDD/VSS rails are exempt"
            )
    return tuple(problems)


#: A macro shape in nm, as ``(owner, layer, x1, y1, x2, y2)``; ``owner`` is
#: ``"PIN <name>"`` or ``"OBS"``, the way a problem names it.
_Shape = Tuple[str, str, int, int, int, int]
#: ``(x1, y1, x2, y2)`` in nm.
_Box = Tuple[float, float, float, float]


def _nm(um: float) -> int:
    return round(um * 1000.0)


def _grown(shapes: Iterable[_Shape], layer: str, half_x: float, half_y: float) -> List[_Box]:
    """The ``layer`` shapes grown by ``half_x`` and ``half_y`` nm, read as open boxes.

    Grown by the layer's spacing plus half of the wire or via that has to clear
    them, other nets' shapes become the region that wire's or via's *centre*
    may not enter.  The boundary itself is exactly minimum spacing, and free.
    """
    return [
        (x1 - half_x, y1 - half_y, x2 + half_x, y2 + half_y)
        for _, shape_layer, x1, y1, x2, y2 in shapes
        if shape_layer == layer
    ]


def _free_spans(lo: float, hi: float, blocked: Iterable[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """``[lo, hi]`` minus the open ``blocked`` spans: the pieces of positive length."""
    free: List[Tuple[float, float]] = []
    at = lo
    for start, end in sorted(blocked):
        if min(start, hi) > at:
            free.append((at, min(start, hi)))
        at = max(at, end)
        if at >= hi:
            break
    if at < hi:
        free.append((at, hi))
    return free


class _FreeSpace:
    """Where the centre of a wire may sit inside a cell, and which of it connects.

    The cell is cut into horizontal bands at every edge of every box.  In a band
    the free centres are a few x spans: the cell width minus the ``blocked``
    boxes covering the band, plus the pin's ``own`` metal, which its wire may
    always run along.  Spans of adjacent bands that overlap by a positive length
    are one connected piece.  A gap exactly one wire wide between two other
    nets' shapes is a span of length zero and connects nothing: a route that
    has to hold minimum spacing on both sides at once is not a way out to count
    on.
    """

    def __init__(self, width: int, height: int, blocked: List[_Box], own: Iterable[_Box] = ()):
        own = list(own)
        cuts = {0, height}
        for box in blocked + own:
            cuts.update(y for y in (box[1], box[3]) if 0 < y < height)
        self.ys = sorted(cuts)
        self.bands: List[List[Tuple[float, float]]] = []
        for lo, hi in zip(self.ys, self.ys[1:]):
            spans = _free_spans(0, width, [
                (x1, x2) for x1, y1, x2, y2 in blocked if y1 <= lo and y2 >= hi
            ])
            spans += [
                (max(x1, 0), min(x2, width)) for x1, y1, x2, y2 in own if y1 <= lo and y2 >= hi
            ]
            merged: List[Tuple[float, float]] = []
            for start, end in sorted(spans):
                if end <= start:
                    continue
                if merged and start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            self.bands.append(merged)

        first = [0]
        for spans in self.bands:
            first.append(first[-1] + len(spans))
        parent = list(range(first[-1]))

        def root(index: int) -> int:
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        for band in range(len(self.bands) - 1):
            for i, (a1, a2) in enumerate(self.bands[band]):
                for j, (b1, b2) in enumerate(self.bands[band + 1]):
                    if a1 < b2 and b1 < a2:
                        parent[root(first[band] + i)] = root(first[band + 1] + j)
        self.pieces = [
            [root(first[band] + i) for i in range(len(spans))]
            for band, spans in enumerate(self.bands)
        ]

    def piece(self, x: float, y: float) -> Optional[int]:
        """The connected piece the free centre ``(x, y)`` is in, or None."""
        band = bisect.bisect_right(self.ys, y) - 1
        for b in (band, band - 1):
            if 0 <= b < len(self.bands) and self.ys[b] <= y <= self.ys[b + 1]:
                for (x1, x2), piece in zip(self.bands[b], self.pieces[b]):
                    if x1 <= x <= x2:
                        return piece
        return None

    def centres(self) -> Iterable[Tuple[float, float]]:
        """One point inside every free span of every band."""
        for band, spans in enumerate(self.bands):
            y = (self.ys[band] + self.ys[band + 1]) / 2
            for x1, x2 in spans:
                yield (x1 + x2) / 2, y

    def extent(self, pieces: Iterable[int]) -> Optional[_Box]:
        """The bounding box of ``pieces``, or None when there are none."""
        wanted = set(pieces)
        boxes = [
            (x1, self.ys[band], x2, self.ys[band + 1])
            for band, spans in enumerate(self.bands)
            for (x1, x2), piece in zip(spans, self.pieces[band])
            if piece in wanted
        ]
        if not boxes:
            return None
        return (min(b[0] for b in boxes), min(b[1] for b in boxes),
                max(b[2] for b in boxes), max(b[3] for b in boxes))


def _via_blocked(others: List[_Shape], lower: str, upper: str, shape) -> List[_Box]:
    """Where a via of ``shape`` may not be centred, for its metal below and above."""
    (below_w, below_h), (above_w, above_h) = shape
    below, above = _nm(METAL_SPACING_UM[lower]), _nm(METAL_SPACING_UM[upper])
    return (
        _grown(others, lower, below + _nm(below_w / 2), below + _nm(below_h / 2))
        + _grown(others, upper, above + _nm(above_w / 2), above + _nm(above_h / 2))
    )


def _pin_escape(
    width: int, height: int, own: List[_Shape], others: List[_Shape]
) -> Tuple[Tuple[int, ...], Optional[_Box]]:
    """The ``Metal3`` tracks a pin can put a ``Via2`` on, and the Metal2 it reaches.

    A wire of the pin's net runs on Metal1 and Metal2 wherever its centre keeps
    spacing plus half the wire's width from every other net, and along the pin's
    own metal; it changes layer through a ``Via1`` wherever both of the via's
    metal shapes clear the other nets.  Every Metal2 piece reached that way is
    searched for a ``Via2`` centred on a Metal3 track ``y = 0.42k`` with both
    of its metal shapes clear.  Returns those tracks in nm, and the bounding
    box of the Metal2 centres the pin reaches.
    """
    wire = {}
    for layer in ("Metal1", "Metal2"):
        half = _nm(METAL_SPACING_UM[layer]) + _nm(METAL_WIDTH_UM[layer] / 2)
        wire[layer] = _FreeSpace(
            width, height, _grown(others, layer, half, half),
            [(x1, y1, x2, y2) for _, shape_layer, x1, y1, x2, y2 in own if shape_layer == layer],
        )

    reached = set()
    for _, layer, x1, y1, x2, y2 in own:
        if layer in wire:
            piece = wire[layer].piece((x1 + x2) / 2, (y1 + y2) / 2)
            if piece is not None:
                reached.add((layer, piece))

    links: Dict[Tuple[str, int], set] = {}
    for shape in VIA_SHAPES_UM:
        vias = _FreeSpace(width, height, _via_blocked(others, "Metal1", "Metal2", shape))
        for x, y in vias.centres():
            below, above = wire["Metal1"].piece(x, y), wire["Metal2"].piece(x, y)
            if below is not None and above is not None:
                links.setdefault(("Metal1", below), set()).add(("Metal2", above))
                links.setdefault(("Metal2", above), set()).add(("Metal1", below))
    todo = list(reached)
    while todo:
        for node in links.get(todo.pop(), ()):
            if node not in reached:
                reached.add(node)
                todo.append(node)

    offset, pitch = (_nm(v) for v in TRACK_UM["y"])
    lines = [offset + k * pitch for k in range(height // pitch + 1)
             if 0 < offset + k * pitch < height]
    tracks = set()
    for shape in VIA_SHAPES_UM:
        blocked = _via_blocked(others, "Metal2", "Metal3", shape)
        for y in lines:
            if y in tracks:
                continue
            spans = _free_spans(0, width, [(x1, x2) for x1, y1, x2, y2 in blocked if y1 < y < y2])
            if any(("Metal2", wire["Metal2"].piece((x1 + x2) / 2, y)) in reached
                   for x1, x2 in spans):
                tracks.add(y)

    metal2 = wire["Metal2"].extent(piece for layer, piece in reached if layer == "Metal2")
    return tuple(sorted(tracks)), metal2


def _pin_escape_problem(
    name: str, tracks: Tuple[int, ...], metal2: Optional[_Box], others: List[_Shape],
    height: int,
) -> str:
    """Why pin ``name`` has too few ways up, naming the metal that closes the rest.

    For each track within half a pitch of the Metal2 the pin reaches, the other
    net's shape that keeps a Via2 off the longest stretch of it is named: the
    bar across the box, not the riser that clips one end of it.
    """
    count = len(tracks)
    on = f" (y = {', '.join(f'{y / 1000:.3f}' for y in tracks)} um)" if tracks else ""
    text = (
        f"PIN {name} can put a Via2 on {count} Metal3 track{'' if count == 1 else 's'}"
        f"{on}; detailed routing needs at least {PIN_ESCAPE_TRACKS_MIN}"
    )
    closed = []
    if metal2 is None:
        text += (
            ": no Via1 from the Metal1 its wire can reach lands on Metal2 clear of "
            "other nets"
        )
    else:
        offset, pitch = (_nm(v) for v in TRACK_UM["y"])
        narrow = {
            "Metal2": min(min(below) for below, _ in VIA_SHAPES_UM),
            "Metal3": min(min(above) for _, above in VIA_SHAPES_UM),
        }
        x1, y1, x2, y2 = metal2
        for k in range(math.ceil((y1 - pitch / 2 - offset) / pitch),
                       math.floor((y2 + pitch / 2 - offset) / pitch) + 1):
            y = offset + k * pitch
            if not 0 < y < height or y in tracks:
                continue
            # Grown for the narrower side of a Via2 on both axes, so a shape
            # named here keeps every one of the four shapes off that stretch.
            longest = None
            for owner, layer, ox1, oy1, ox2, oy2 in others:
                if layer not in narrow:
                    continue
                reach = _nm(METAL_SPACING_UM[layer]) + _nm(narrow[layer] / 2)
                covered = min(ox2 + reach, x2) - max(ox1 - reach, x1)
                if oy1 - reach < y < oy2 + reach and covered > 0:
                    if longest is None or covered > longest[0]:
                        longest = (covered, owner, layer, ox1, oy1, ox2, oy2)
            if longest is not None:
                _, owner, layer, ox1, oy1, ox2, oy2 = longest
                closed.append(
                    f"y = {y / 1000:.3f} by {layer} of {owner} (RECT {ox1 / 1000:.3f} "
                    f"{oy1 / 1000:.3f} {ox2 / 1000:.3f} {oy2 / 1000:.3f})"
                )
        text += (
            f": its wire can reach Metal2 only with its centre in x = {x1 / 1000:.3f} "
            f".. {x2 / 1000:.3f}, y = {y1 / 1000:.3f} .. {y2 / 1000:.3f} um"
        )
        if closed:
            text += f", and a Via2 is kept off track {'; '.join(closed)}"
    fix = (
        "Move the metal named above so that a Via2 (Metal2 enclosure 0.29 x 0.21 um, "
        "0.21 um clear of other nets' Metal2) fits on a second track"
        if closed else
        "Clear Metal1 and Metal2 around the pin so that a Via2 (Metal2 enclosure "
        "0.29 x 0.21 um, 0.21 um clear of other nets' Metal2) fits on two tracks"
    )
    return (
        f"{text}. Walled in like that, every route out of the pin goes up through "
        "those few Via2 sites, and the router has nothing to trade when a "
        "neighbour's wire needs one: step 7 stalled at ~400 Metal2 shorts, at every "
        "die size, on AION_xor2_5, AION_xor2_8 and AION_xnor2_xor2_9, whose inner "
        "pins each had one such track, and routed clean when the same pins had two. "
        f"{fix}, y = 0.42k um, or run the pin's own Metal2 out of the enclosure. "
        "DRC, LVS and pin access do not see this"
    )


def lef_pin_escape_problems(
    lef_path: Path | str,
    macro: Optional[str] = None,
) -> Tuple[str, ...]:
    """Grade how many ways up out of the cell each signal pin has.

    :func:`lef_pin_access` asks whether a via reaches a pin at all.  This asks
    whether the router can get the pin's wire *out*: from the pin, along free
    Metal1 and Metal2 and through ``Via1`` wherever they clear the other nets,
    to a ``Via2`` on a Metal3 track.  A pin has to reach at least
    :data:`PIN_ESCAPE_TRACKS_MIN` distinct tracks that way.

    Calibrated on one step-7 placement, 2026-09-14.  After Metal2 was lifted
    out of the rail via band, ``AION_xor2_5`` (I0, I2), ``AION_xor2_8`` (I0) and
    ``AION_xnor2_xor2_9`` (I1) each had an inner pin boxed in by a neighbour
    pin's U-shaped Metal2 below and an obstruction bar above, with a Via2 fitting
    on one track only (y = 1.26 um).  Detailed routing plateaued at ~415
    violations, Metal2 shorts through the neighbour's bar, for 60+ iterations at
    every die size; those three masters held 433 of the 498 markers at
    iteration 10.  Swapping the same instances back to the abstracts with the
    bar at y = 0.11 um -- the same boxes, with a second track at y = 0.84 um --
    routed to 0 violations by iteration 8.  This rule gives exactly those four
    pins one track, the old abstracts two, every other pin of the ten mined
    cells four or more, and all 283 signal pins of the PDK library eight.  It
    does not depend on the exact margin: requiring up to 30 nm more room than
    minimum spacing changes none of those counts.  It also gives
    ``AION_mux2i_1`` and ``AION_mux2i_2`` one track on I0; both are already
    refused for I2, which TritonRoute cannot reach, and have never been routed.

    Metal1 is followed as a route in its own right because TritonRoute takes
    planar Metal1 access out of a crowded spot and goes up elsewhere: counting
    only a Via1 over the pin's own Metal1 leaves 33 PDK pins and
    ``AION_mux2_0``'s I0, I1 and I3 short of two tracks, and every one of them
    routes clean.  A gap exactly one wire wide is not followed (see
    :class:`_FreeSpace`).  Only the cell is seen, not its neighbours, and pins
    drawn on Metal3 or above are not graded.
    ``collect_cells.check_pin_escape`` in aion_chip applies the same rule at
    publish and before PnR; the two must stay in step.
    """
    path = Path(lef_path)
    macros = lef_macros(path)
    if not macros:
        raise MetricsError(f"{path.name} defines no MACRO")
    if macro is None:
        if len(macros) != 1:
            names = ", ".join(sorted(macros))
            raise MetricsError(
                f"{path.name} defines {len(macros)} macros ({names}); "
                "name the one to check"
            )
        macro = next(iter(macros))
    if macro not in macros:
        raise MetricsError(
            f"{path.name} defines no MACRO {macro!r}; it has: "
            + ", ".join(sorted(macros))
        )
    body = macros[macro]
    size = _LEF_SIZE_RE.search(body)
    if size is None:
        raise MetricsError(f"MACRO {macro} in {path.name} carries no SIZE line")
    width, height = _nm(float(size.group(1))), _nm(float(size.group(2)))

    def shapes(owner: str, block: str) -> List[_Shape]:
        return [(owner, layer, *(_nm(v) for v in rect))
                for layer, *rect in _layer_rects(block)]

    obs_block = _LEF_OBS_RE.search(body)
    obs = shapes("OBS", obs_block.group(1)) if obs_block else []
    pin_blocks = _LEF_PIN_RE.findall(body)
    pins = {name: shapes(f"PIN {name}", pin_body) for name, pin_body in pin_blocks}

    problems: List[str] = []
    for name, pin_body in pin_blocks:
        use = _LEF_USE_RE.search(pin_body)
        if use is not None and use.group(1).upper() in ("POWER", "GROUND"):
            continue
        if use is None and name.upper() in POWER_PIN_NAMES:
            continue
        layers = {shape[1] for shape in pins[name]}
        # No routing geometry is lef_pin_access's to report; a pin already on
        # Metal3 or above is past the Via2 counted here.
        if (not layers & {"Metal1", "Metal2"}
                or layers & {"Metal3", "Metal4", "Metal5"}):
            continue
        others = obs + [shape for other, rects in pins.items() if other != name for shape in rects]
        tracks, metal2 = _pin_escape(width, height, pins[name], others)
        if len(tracks) < PIN_ESCAPE_TRACKS_MIN:
            problems.append(_pin_escape_problem(name, tracks, metal2, others, height))
    return tuple(problems)


def pdk_lef_geometry(
    macros: List[str],
    lef_path: Path | str,
) -> Dict[str, CellGeometry]:
    """Measure several macros out of one LEF, e.g. the PDK standard-cell LEF."""
    path = Path(lef_path)
    bodies = lef_macros(path)
    out: Dict[str, CellGeometry] = {}
    for name in macros:
        if name not in bodies:
            raise MetricsError(f"{path.name} defines no MACRO {name!r}")
        match = _LEF_SIZE_RE.search(bodies[name])
        if match is None:
            raise MetricsError(f"MACRO {name} in {path.name} carries no SIZE line")
        width, height = float(match.group(1)), float(match.group(2))
        out[name] = CellGeometry(
            cell=name,
            width_um=width,
            height_um=height,
            source="lef",
            problems=_grade_footprint(width, height),
        )
    return out


@dc.dataclass(frozen=True)
class LayerStat:
    """What one layer contributes to a layout."""

    layer: str
    gds_pair: Tuple[int, int]
    polygons: int
    area_um2: float
    bbox_um: Optional[Tuple[float, float, float, float]]


def layer_inventory(
    gds_path: Path | str,
    cell_name: Optional[str] = None,
    tech: Optional[Tech] = None,
) -> Dict[str, LayerStat]:
    """Return per-layer shape counts, areas and bounding boxes.

    Only layers that carry geometry appear.  This is the inventory the evidence
    packet prints: it is what names a Metal2 strip nobody meant to draw, and
    what shows at a glance whether the cell uses the metals it claims to.
    """
    tech = tech or sg13g2_tech
    path = Path(gds_path)
    if not path.is_file():
        raise MetricsError(f"no GDS at {path}")
    try:
        import klayout.db as pya
    except Exception as exc:  # pragma: no cover
        raise MetricsError(f"klayout.db unavailable: {exc}") from exc

    layout = pya.Layout()
    layout.read(str(path))
    top = _top_cell(layout, cell_name, path.name)
    dbu = layout.dbu

    stats: Dict[str, LayerStat] = {}
    for name, layer in tech.layers.items():
        index = layout.find_layer(*layer.gds_pair)
        if index is None:
            continue
        region = pya.Region(top.begin_shapes_rec(index)).merged()
        if region.is_empty():
            continue
        box = region.bbox()
        stats[name] = LayerStat(
            layer=name,
            gds_pair=layer.gds_pair,
            polygons=region.count(),
            area_um2=region.area() * dbu * dbu,
            bbox_um=(
                box.left * dbu,
                box.bottom * dbu,
                box.right * dbu,
                box.top * dbu,
            ),
        )
    return stats


#: Layers read out of the GDS to grade a cell for what abutting it will do:
#: ``Cont`` carries the power-rail taps, which the row above and below share.
#: The routing metals come along for callers that want the drawn metal; pin
#: access is graded on the LEF, where PORT and OBS say which net is which.
ABUTMENT_LAYERS = tuple(ROUTING_AXIS) + ("Cont",)


def drawn_shapes(
    gds_path: Path | str,
    layers: Iterable[str] = ABUTMENT_LAYERS,
    cell_name: Optional[str] = None,
    tech: Optional[Tech] = None,
) -> Dict[str, Tuple[Tuple[float, float, float, float], ...]]:
    """Rectangles the cell draws on each named layer, merged, in nanometres.

    Merged across nets: this is what is drawn, not who it belongs to, so it
    cannot say whether a Metal2 strap beside a port is that port's own net.

    Merged and decomposed rather than taken as bounding boxes, so an L-shaped
    piece of metal blocks the corner it occupies and not the corner it does
    not.  Geometry in this PDK is rectilinear, so the decomposition is exact.
    """
    tech = tech or sg13g2_tech
    path = Path(gds_path)
    if not path.is_file():
        raise MetricsError(f"no GDS at {path}")
    try:
        import klayout.db as pya
    except Exception as exc:  # pragma: no cover - klayout is a hard dependency
        raise MetricsError(f"klayout.db unavailable: {exc}") from exc

    layout = pya.Layout()
    layout.read(str(path))
    top = _top_cell(layout, cell_name, path.name)
    to_nm = layout.dbu * 1000.0

    drawn: Dict[str, Tuple[Tuple[float, float, float, float], ...]] = {}
    for name in layers:
        layer = tech.layers.get(name)
        if layer is None:
            continue
        index = layout.find_layer(*layer.gds_pair)
        if index is None:
            continue
        region = pya.Region(top.begin_shapes_rec(index)).merged()
        if region.is_empty():
            continue
        drawn[name] = tuple(
            (box.left * to_nm, box.bottom * to_nm, box.right * to_nm, box.top * to_nm)
            for box in (part.bbox() for part in region.decompose_trapezoids())
        )
    return drawn


def routing_metals_used(
    gds_path: Path | str,
    cell_name: Optional[str] = None,
    tech: Optional[Tech] = None,
) -> List[str]:
    """Return the routing metals the layout actually draws, lowest first.

    Metal above Metal1 inside a standard cell is a routing blockage the block
    router has to work around, so the flow reports which metals a cell spends
    rather than leaving it to be discovered at place-and-route.
    """
    inventory = layer_inventory(gds_path, cell_name, tech)
    order = ["Metal1", "Metal2", "Metal3", "Metal4", "Metal5"]
    return [name for name in order if name in inventory]


@dc.dataclass(frozen=True)
class NetShort:
    """Two or more differently-named nets sharing one connected piece of metal."""

    layer: str
    nets: Tuple[str, ...]
    bbox_um: Tuple[float, float, float, float]

    def __str__(self) -> str:
        x1, y1, x2, y2 = self.bbox_um
        return (
            f"{self.layer}: {' + '.join(self.nets)} share metal at "
            f"({x1:.3f},{y1:.3f})-({x2:.3f},{y2:.3f})"
        )


def cross_net_overlaps(
    gds_path: Path | str,
    cell_name: Optional[str] = None,
    tech: Optional[Tech] = None,
    layers: Optional[List[str]] = None,
) -> List[NetShort]:
    """Return every connected piece of metal carrying more than one net name.

    This is the cheap half of what LVS does, and it is the half worth having
    immediately: a short is a *connected component* of one routing layer that
    holds two differently-named labels, and that is answerable from the GDS in
    about a second without starting a container.

    It is deliberately per-layer and label-driven.  It does not follow Via1 from
    Metal1 to Metal2, and it cannot see a short between two nets of which only
    one is labelled -- both are LVS's job, and LVS is what grades the cell.  What
    it does catch is the mistake that costs the most time when it is found late:
    two labelled nets drawn onto the same strip of metal.  An empty result is
    therefore "no *labelled* short on a single layer", never "the cell is clean".
    """
    tech = tech or sg13g2_tech
    path = Path(gds_path)
    if not path.is_file():
        raise MetricsError(f"no GDS at {path}")
    try:
        import klayout.db as pya
    except Exception as exc:  # pragma: no cover
        raise MetricsError(f"klayout.db unavailable: {exc}") from exc

    layout = pya.Layout()
    layout.read(str(path))
    top = _top_cell(layout, cell_name, path.name)
    dbu = layout.dbu

    names = layers or ["Metal1", "Metal2", "Metal3", "GatPoly", "Activ"]
    shorts: List[NetShort] = []
    for name in names:
        layer = tech.get(name)
        if layer is None:
            continue
        metal_index = layout.find_layer(*layer.gds_pair)
        if metal_index is None:
            continue
        region = pya.Region(top.begin_shapes_rec(metal_index)).merged()
        if region.is_empty():
            continue

        # Labels may sit on the layer's own label datatype, on its pin datatype
        # or on the drawing layer itself; all three spellings occur across the
        # PDK cells and the generators here, so collect from every one of them.
        labels: List[Tuple[str, "pya.Point"]] = []
        seen_pairs = set()
        for pair in (layer.label_pair, layer.pin_pair, layer.gds_pair):
            if pair is None or pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            index = layout.find_layer(*pair)
            if index is None:
                continue
            iterator = top.begin_shapes_rec(index)
            while not iterator.at_end():
                shape = iterator.shape()
                if shape.is_text():
                    text = shape.text.transformed(iterator.trans())
                    labels.append((shape.text_string, pya.Point(text.x, text.y)))
                iterator.next()
        if len(labels) < 2:
            continue

        for polygon in region.each_merged():
            carried = sorted(
                {net for net, point in labels if polygon.inside(point)}
            )
            if len(carried) > 1:
                box = polygon.bbox()
                shorts.append(
                    NetShort(
                        layer=name,
                        nets=tuple(carried),
                        bbox_um=(
                            box.left * dbu,
                            box.bottom * dbu,
                            box.right * dbu,
                            box.top * dbu,
                        ),
                    )
                )
    return shorts


__all__ = [
    "GRID_TOL_UM",
    "POWER_PIN_NAMES",
    "ROUTING_AXIS",
    "ROW_HEIGHT_UM",
    "SITE_WIDTH_UM",
    "TRACK_UM",
    "CellGeometry",
    "LayerStat",
    "MetricsError",
    "NetShort",
    "PinAccess",
    "gds_boundary",
    "cross_net_overlaps",
    "layer_inventory",
    "lef_abutment_problems",
    "lef_macro_geometry",
    "lef_macros",
    "lef_pin_access",
    "lef_pin_escape_problems",
    "pdk_lef_geometry",
    "routing_metals_used",
    "drawn_shapes",
    "tap_contact_problems",
]
