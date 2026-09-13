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
    "lef_macro_geometry",
    "lef_macros",
    "lef_pin_access",
    "pdk_lef_geometry",
    "routing_metals_used",
    "drawn_shapes",
    "tap_contact_problems",
]
