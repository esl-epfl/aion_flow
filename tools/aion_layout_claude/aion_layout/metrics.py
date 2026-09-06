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
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .tech import Tech, sg13g2_tech

#: SG13G2 ``CoreSite``: the placement grid a core cell has to land on.
SITE_WIDTH_UM = 0.48
#: SG13G2 row height.  One ``CoreSite`` row; every core cell is exactly this tall.
ROW_HEIGHT_UM = 3.78
#: Tolerance for a dimension that has to be a multiple of the site, in um.
#: The GDS database unit is 1 nm, so anything under half a nanometre is noise.
GRID_TOL_UM = 5e-4


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
    "ROW_HEIGHT_UM",
    "SITE_WIDTH_UM",
    "CellGeometry",
    "LayerStat",
    "MetricsError",
    "NetShort",
    "gds_boundary",
    "cross_net_overlaps",
    "layer_inventory",
    "lef_macro_geometry",
    "lef_macros",
    "pdk_lef_geometry",
    "routing_metals_used",
]
