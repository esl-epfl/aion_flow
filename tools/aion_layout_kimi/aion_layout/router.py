# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Manual routing helpers
# ================================================================

"""Generic, topology-agnostic manual routing helpers.

These helpers build small sub-cells containing wires and via stacks that can be
merged into a parent ``Cell``.
"""

from __future__ import annotations

from typing import Sequence

from .building_blocks import draw_via_stack as _draw_via_stack
from .cell import Cell, Port
from .primitives import Point, Rect
from .shapes import RectShape
from .tech import Layer, Tech, sg13g2_tech


def _tech(tech: Tech | None) -> Tech:
    return tech if tech is not None else sg13g2_tech


def _default_width(layer: Layer) -> float:
    if layer.min_width is not None:
        return layer.min_width
    raise ValueError(f"Layer {layer.name} has no defined minimum width")


def draw_wire(
    layer: Layer,
    path: Sequence[Point],
    width: float | None = None,
    tech: Tech | None = None,
) -> Cell:
    """Draw a Manhattan wire along ``path`` on ``layer``.

    ``path`` is a sequence of points connected by axis-aligned segments.  The
    wire width defaults to the layer's minimum width.
    """
    t = _tech(tech)
    if len(path) < 2:
        raise ValueError("path must contain at least two points")
    width = _default_width(layer) if width is None else width
    half = width / 2.0

    cell = Cell("wire", t)
    for p1, p2 in zip(path, path[1:]):
        dx = abs(p1.x - p2.x)
        dy = abs(p1.y - p2.y)
        if dx < 1e-9 and dy > 1e-9:
            # Vertical segment.
            x = p1.x
            y0, y1 = sorted((p1.y, p2.y))
            rect = Rect.from_lbrt(x - half, y0, x + half, y1)
        elif dy < 1e-9 and dx > 1e-9:
            # Horizontal segment.
            y = p1.y
            x0, x1 = sorted((p1.x, p2.x))
            rect = Rect.from_lbrt(x0, y - half, x1, y + half)
        else:
            raise ValueError(
                "draw_wire only supports axis-aligned segments "
                f"({p1.as_tuple()} -> {p2.as_tuple()})"
            )
        cell.add_shape(RectShape(layer, rect))

    return cell


def connect_ports(
    port_a: Port,
    port_b: Port,
    layer: Layer,
    width: float | None = None,
    tech: Tech | None = None,
) -> Cell:
    """Create an L-shaped wire connecting the centres of two ports.

    The route goes horizontally first, then vertically.  Both ports must be on
    ``layer``; multi-layer connections are left to explicit via-stack calls.
    """
    if port_a.layer != layer or port_b.layer != layer:
        raise ValueError("connect_ports currently requires both ports to be on the target layer")

    a = port_a.rect.center
    b = port_b.rect.center
    corner = Point(b.x, a.y)
    return draw_wire(layer, [a, corner, b], width=width, tech=tech)


# Re-export the generic via-stack helper from building_blocks so callers only
# need to import from the router module.
draw_via_stack = _draw_via_stack


__all__ = ["draw_wire", "connect_ports", "draw_via_stack"]
