# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Convert a GDS cell into AION Python code
# ================================================================

"""Read a GDSII layout and emit a runnable AION cell generator.

The reader is intentionally low-level: every GDS shape becomes a
``RectShape``, ``PolygonShape`` or ``TextShape``.  Text labels on a layer's
pin/label datatype are also turned into ``Port`` objects.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import klayout.db as pya

from .cell import Cell, Port
from .primitives import Point, Rect
from .shapes import PolygonShape, RectShape, TextShape
from .tech import Layer, Tech


class UnsupportedLayerError(RuntimeError):
    """Raised when a GDS layer/datatype pair is not defined in the technology."""


class UnsupportedShapeError(RuntimeError):
    """Raised when the reader encounters a shape type it cannot convert."""


class GdsReader:
    """Read a GDS file into an AION ``Cell``."""

    def __init__(self, tech: Tech):
        self.tech = tech
        self._layer_map: Dict[Tuple[int, int], Tuple[Layer, str]] = {}
        for layer in tech.layer_list:
            self._layer_map[layer.gds_pair] = (layer, "geometry")
            if layer.pin_pair is not None:
                self._layer_map[layer.pin_pair] = (layer, "pin")
            if layer.label_pair is not None:
                self._layer_map[layer.label_pair] = (layer, "label")

    def _resolve_layer(self, layer: int, datatype: int) -> Tuple[Layer, str]:
        key = (layer, datatype)
        if key not in self._layer_map:
            raise UnsupportedLayerError(
                f"GDS layer/datatype ({layer}, {datatype}) is not defined in {self.tech.name}"
            )
        return self._layer_map[key]

    def read(self, gds_path: Path, top_cell_name: Optional[str] = None) -> Cell:
        """Read ``gds_path`` and return a flat ``Cell``."""
        gds_path = Path(gds_path)
        layout = pya.Layout()
        layout.read(str(gds_path))

        if top_cell_name:
            klayout_cell = layout.cell(top_cell_name)
            if klayout_cell is None:
                raise ValueError(f"Top cell '{top_cell_name}' not found in {gds_path}")
        else:
            top_cells = layout.top_cells()
            if not top_cells:
                raise ValueError(f"No top-level cells found in {gds_path}")
            klayout_cell = top_cells[0]

        # Work on a copy so the original hierarchy can be flattened safely.
        flat_layout = pya.Layout()
        flat_layout.dbu = layout.dbu
        flat_cell = flat_layout.create_cell(klayout_cell.name)
        flat_cell.copy_tree(klayout_cell)
        flat_cell.flatten(True)

        cell = Cell(flat_cell.name, self.tech)
        boundary: Optional[Rect] = None
        all_bboxes: List[Rect] = []
        ports: List[Port] = []

        for layer_index in flat_layout.layer_indices():
            info = flat_layout.get_info(layer_index)
            layer, purpose = self._resolve_layer(info.layer, info.datatype)
            shapes_iter = flat_cell.shapes(layer_index)

            for shape in shapes_iter.each():
                if shape.is_box():
                    box = shape.box
                    rect = Rect.from_lbrt(
                        float(box.left),
                        float(box.bottom),
                        float(box.right),
                        float(box.top),
                    )
                    if layer.name == "prBoundary":
                        boundary = rect
                    else:
                        cell.add_shape(RectShape(layer, rect))
                        all_bboxes.append(rect)

                elif shape.is_polygon() or shape.is_simple_polygon():
                    polygon = shape.polygon
                    points = [
                        Point(float(p.x), float(p.y))
                        for p in polygon.each_point_hull()
                    ]
                    poly_shape = PolygonShape(layer, points)
                    cell.add_shape(poly_shape)
                    all_bboxes.append(poly_shape.bbox())

                elif shape.is_text():
                    pos = Point(float(shape.text_trans.disp.x), float(shape.text_trans.disp.y))
                    text = shape.text_string
                    text_shape = TextShape(layer, text, pos, purpose=purpose)  # type: ignore[arg-type]
                    cell.add_shape(text_shape)

                    if purpose in ("pin", "label"):
                        direction = _guess_port_direction(text)
                        ports.append(
                            Port(
                                name=text,
                                net=text,
                                layer=layer,
                                rect=Rect.from_lbrt(pos.x, pos.y, pos.x, pos.y),
                                direction=direction,
                            )
                        )
                else:
                    raise UnsupportedShapeError(
                        f"Unsupported GDS shape type at layer ({info.layer}, {info.datatype})"
                    )

        if boundary is not None:
            cell.set_boundary(boundary)
        elif all_bboxes:
            bbox = all_bboxes[0]
            for b in all_bboxes[1:]:
                bbox = bbox.union(b)
            cell.set_boundary(bbox)

        for port in ports:
            cell.add_port(port)

        return cell


def _guess_port_direction(name: str) -> Optional[str]:
    """Infer a LEF-style direction from a port/label name."""
    upper = name.upper()
    if upper in ("VDD", "VCC", "VPWR"):
        return "POWER"
    if upper in ("VSS", "GND", "VGND"):
        return "GROUND"
    if re.match(r"^(A|B|C|D|E|IN|EN|CLK|RST|SET)(\[\d+\])?$", upper):
        return "INPUT"
    if re.match(r"^(Y|OUT|Q|Z)(\[\d+\])?$", upper):
        return "OUTPUT"
    return None


def _fmt(value: float) -> str:
    """Format a coordinate as a clean float literal."""
    if value == int(value):
        return f"{int(value)}.0"
    return f"{value:g}"


def emit_python(cell: Cell, module_name: Optional[str] = None, tech_name: str = "sg13g2_tech") -> str:
    """Return a Python module string that recreates ``cell``."""
    name = module_name or cell.name or "cell"
    boundary = cell._boundary or cell.bbox
    width = boundary.right - boundary.left
    height = boundary.top - boundary.bottom

    lines: List[str] = [
        "# ================================================================",
        "#  SPDX-FileCopyrightText:    2026 Filippo Quadri",
        "#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1",
        "#  Created:                   2026-08-25",
        f"#  Description:               Auto-generated from GDS: {name}",
        "# ================================================================",
        "",
        f'"""Generated AION cell for {name}."""',
        "",
        "from aion_layout.cell import Cell, Port",
        "from aion_layout.primitives import Point, Rect",
        "from aion_layout.shapes import PolygonShape, RectShape, TextShape",
        "from aion_layout.tech import Tech",
        "",
        f"CELL_WIDTH = {_fmt(width)}",
        f"CELL_HEIGHT = {_fmt(height)}",
        "",
        "",
        "def generate(name: str, tech: Tech) -> Cell:",
        '    """Generate the cell."""',
        "    cell = Cell(name, tech)",
        f"    cell.set_boundary(Rect.from_lbrt({_fmt(boundary.left)}, {_fmt(boundary.bottom)}, "
        f"{_fmt(boundary.right)}, {_fmt(boundary.top)}))",
        "",
    ]

    # Group shapes by layer for readability.
    shapes_by_layer: Dict[Layer, List] = {}
    for layer, shapes in cell.shapes.items():
        shapes_by_layer.setdefault(layer, []).extend(shapes)

    for layer in sorted(shapes_by_layer, key=lambda l: l.name):
        lines.append(f"    # {layer.name}")
        for shape in shapes_by_layer[layer]:
            if isinstance(shape, RectShape):
                r = shape.rect
                lines.append(
                    f"    cell.add_shape(RectShape(tech[{layer.name!r}], "
                    f"Rect.from_lbrt({_fmt(r.left)}, {_fmt(r.bottom)}, {_fmt(r.right)}, {_fmt(r.top)})))"
                )
            elif isinstance(shape, PolygonShape):
                pts = ", ".join(
                    f"Point({_fmt(p.x)}, {_fmt(p.y)})" for p in shape.points
                )
                lines.append(
                    f"    cell.add_shape(PolygonShape(tech[{layer.name!r}], [{pts}]))"
                )
            elif isinstance(shape, TextShape):
                lines.append(
                    f"    cell.add_shape(TextShape(tech[{layer.name!r}], {shape.text!r}, "
                    f"Point({_fmt(shape.position.x)}, {_fmt(shape.position.y)}), purpose={shape.purpose!r}))"
                )
        lines.append("")

    if cell.ports:
        lines.append("    # Ports")
        for port in cell.ports.values():
            r = port.rect
            direction_arg = f", direction={port.direction!r}" if port.direction else ""
            lines.append(
                f"    cell.add_port(Port({port.name!r}, {port.net!r}, tech[{port.layer.name!r}], "
                f"Rect.from_lbrt({_fmt(r.left)}, {_fmt(r.bottom)}, {_fmt(r.right)}, {_fmt(r.top)})"
                f"{direction_arg}))"
            )
        lines.append("")

    lines.extend([
        "    return cell",
        "",
        "",
        'if __name__ == "__main__":',
        "    from aion_layout.tech import sg13g2_tech",
        f"    c = generate({name!r}, sg13g2_tech)",
        f'    c.write_gds("{name}.gds")',
        "",
    ])

    return "\n".join(lines)


__all__ = ["GdsReader", "emit_python", "UnsupportedLayerError", "UnsupportedShapeError"]
