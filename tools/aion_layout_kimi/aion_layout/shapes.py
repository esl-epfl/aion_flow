# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Layer-aware shapes
# ================================================================

"""Layer-aware geometric shapes that can be attached to a ``Cell``."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from .primitives import Point, Rect, Transformation
from .tech import Layer


class Shape(ABC):
    """Base class for all geometry that belongs to a layout layer."""

    layer: Layer

    @abstractmethod
    def bbox(self) -> Rect:
        """Return the axis-aligned bounding box of the shape."""

    @abstractmethod
    def transformed(self, transformation: Transformation) -> Shape:
        """Return a copy of the shape transformed by ``transformation``."""


@dataclass(frozen=True)
class RectShape(Shape):
    """An axis-aligned rectangle on a layer."""

    layer: Layer
    rect: Rect

    def bbox(self) -> Rect:
        return self.rect

    def transformed(self, transformation: Transformation) -> RectShape:
        return RectShape(self.layer, transformation.apply(self.rect))


@dataclass(frozen=True)
class PolygonShape(Shape):
    """A simple polygon on a layer."""

    layer: Layer
    points: tuple[Point, ...]

    def __init__(self, layer: Layer, points: Sequence[Point]):
        if len(points) < 3:
            raise ValueError("A polygon requires at least three points")
        object.__setattr__(self, "layer", layer)
        object.__setattr__(self, "points", tuple(points))

    def bbox(self) -> Rect:
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return Rect.from_lbrt(min(xs), min(ys), max(xs), max(ys))

    def transformed(self, transformation: Transformation) -> PolygonShape:
        return PolygonShape(self.layer, [transformation.apply(p) for p in self.points])


@dataclass(frozen=True)
class TextShape(Shape):
    """A text label on a layer, rendered on the layer's label or pin datatype."""

    layer: Layer
    text: str
    position: Point
    purpose: str = "label"  # "label" or "pin"

    def __post_init__(self) -> None:
        if self.purpose not in ("label", "pin"):
            raise ValueError("purpose must be 'label' or 'pin'")

    def bbox(self) -> Rect:
        # Text has no geometric extent for DRC purposes.
        return Rect(self.position, self.position)

    def transformed(self, transformation: Transformation) -> TextShape:
        return TextShape(self.layer, self.text, transformation.apply(self.position), self.purpose)


__all__ = ["Shape", "RectShape", "PolygonShape", "TextShape"]
