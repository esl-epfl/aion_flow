# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Cell container and GDS writer
# ================================================================

"""Generic standard-cell container with GDSII output."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import klayout.db as pya

from .primitives import Point, Rect, Transformation, translate
from .shapes import PolygonShape, RectShape, Shape, TextShape
from .tech import Layer, Tech, sg13g2_tech


@dataclass(frozen=True)
class Port:
    """A named terminal on a specific layer and rectangle."""

    name: str
    net: str
    layer: Layer
    rect: Rect
    direction: Optional[str] = None

    def __post_init__(self) -> None:
        if self.direction is not None and self.direction not in {
            "INPUT",
            "OUTPUT",
            "INOUT",
            "POWER",
            "GROUND",
        }:
            raise ValueError(f"Invalid port direction: {self.direction}")


class Cell:
    """A collection of shapes, ports and an optional boundary rectangle."""

    def __init__(self, name: str, tech: Optional[Tech] = None):
        self.name = name
        self.tech = tech if tech is not None else sg13g2_tech
        self._shapes: dict[Layer, list[Shape]] = {}
        self.ports: dict[str, Port] = {}
        self._boundary: Optional[Rect] = None

    def add_shape(self, shape: Shape) -> "Cell":
        """Add a shape to the cell."""
        self._shapes.setdefault(shape.layer, []).append(shape)
        return self

    def add_port(self, port: Port) -> "Cell":
        """Add a port to the cell."""
        self.ports[port.name] = port
        return self

    def set_boundary(self, rect: Rect) -> "Cell":
        """Set the explicit abutment / prBoundary rectangle."""
        self._boundary = rect
        return self

    @property
    def shapes(self) -> dict[Layer, list[Shape]]:
        """Return a shallow copy of the layer-grouped shapes dictionary."""
        return {layer: list(shapes) for layer, shapes in self._shapes.items()}

    @property
    def bbox(self) -> Rect:
        """Return the bounding box of all shapes and the explicit boundary."""
        bboxes: list[Rect] = []
        for shapes in self._shapes.values():
            bboxes.extend(s.bbox() for s in shapes)
        if self._boundary is not None:
            bboxes.append(self._boundary)
        if not bboxes:
            return Rect(Point(0, 0), Point(0, 0))
        result = bboxes[0]
        for r in bboxes[1:]:
            result = result.union(r)
        return result

    def merge_subcell(
        self,
        subcell: "Cell",
        offset: Point | tuple[float, float] = Point(0, 0),
    ) -> "Cell":
        """Merge all shapes and ports from ``subcell`` into this cell.

        Existing ports with colliding names are overwritten.
        """
        if isinstance(offset, (tuple, list)):
            transformation = translate(offset[0], offset[1])
        else:
            transformation = translate(offset.x, offset.y)

        for shapes in subcell._shapes.values():
            for shape in shapes:
                self.add_shape(shape.transformed(transformation))

        for port in subcell.ports.values():
            transformed_port = Port(
                name=port.name,
                net=port.net,
                layer=port.layer,
                rect=transformation.apply(port.rect),
                direction=port.direction,
            )
            self.add_port(transformed_port)

        return self

    def _insert_shapes(self, layout: pya.Layout, top: pya.Cell) -> None:
        """Insert all cell shapes into a KLayout cell."""
        for layer, shapes in self._shapes.items():
            layer_index = layout.layer(layer.gds_layer, layer.gds_datatype)
            for shape in shapes:
                if isinstance(shape, RectShape):
                    box = pya.Box(
                        int(round(shape.rect.left)),
                        int(round(shape.rect.bottom)),
                        int(round(shape.rect.right)),
                        int(round(shape.rect.top)),
                    )
                    top.shapes(layer_index).insert(box)
                elif isinstance(shape, PolygonShape):
                    pts = [
                        pya.Point(int(round(p.x)), int(round(p.y)))
                        for p in shape.points
                    ]
                    top.shapes(layer_index).insert(pya.SimplePolygon(pts))
                elif isinstance(shape, TextShape):
                    if shape.purpose == "label" and layer.label_datatype is not None:
                        dt = layer.label_datatype
                    elif shape.purpose == "pin" and layer.pin_datatype is not None:
                        dt = layer.pin_datatype
                    else:
                        continue
                    text_layer_index = layout.layer(layer.gds_layer, dt)
                    text = pya.Text(
                        shape.text,
                        int(round(shape.position.x)),
                        int(round(shape.position.y)),
                    )
                    top.shapes(text_layer_index).insert(text)
                else:
                    raise TypeError(f"Unsupported shape type: {type(shape)}")

    def _insert_ports(self, layout: pya.Layout, top: pya.Cell) -> None:
        """Insert pin labels for every port using the layer's pin datatype.

        Only writes a pin text if the same text is not already present on the
        pin layer at the same location (some generators already add explicit
        pin TextShapes).
        """
        if not self.ports:
            return

        # Collect existing pin texts so we don't duplicate them.
        existing: set[tuple[int, int, str]] = set()
        for layer, shapes in self._shapes.items():
            if layer.pin_datatype is None:
                continue
            for shape in shapes:
                if isinstance(shape, TextShape) and shape.purpose == "pin":
                    existing.add(
                        (layer.gds_layer, layer.pin_datatype, shape.text)
                    )

        for port in self.ports.values():
            if port.layer.pin_datatype is None:
                continue
            if (port.layer.gds_layer, port.layer.pin_datatype, port.name) in existing:
                continue
            layer_index = layout.layer(port.layer.gds_layer, port.layer.pin_datatype)
            center = port.rect.center
            text = pya.Text(
                port.name,
                int(round(center.x)),
                int(round(center.y)),
            )
            top.shapes(layer_index).insert(text)

    def write_gds(self, path: str | Path) -> None:
        """Write the cell to a GDSII file using the KLayout Python API."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        layout = pya.Layout()
        layout.dbu = self.tech.db_unit * 1e6  # metres -> micrometres
        top = layout.create_cell(self.name)
        self._insert_shapes(layout, top)
        self._insert_ports(layout, top)
        layout.write(str(path))

    def __repr__(self) -> str:
        return f"Cell({self.name!r}, shapes={sum(len(s) for s in self._shapes.values())}, ports={len(self.ports)})"


__all__ = ["Port", "Cell"]
