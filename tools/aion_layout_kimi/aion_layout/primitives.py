# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Generic geometry primitives
# ================================================================

"""Generic, PDK-agnostic geometry primitives used by the layout framework.

All coordinates are treated as abstract numbers; callers are expected to use
nanometres consistently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class Point:
    """An immutable 2-D point."""

    x: float
    y: float

    def __post_init__(self) -> None:
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            raise TypeError("Point coordinates must be numeric")

    def __add__(self, other: Point | Sequence[float]) -> Point:
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        if isinstance(other, (tuple, list)) and len(other) == 2:
            return Point(self.x + other[0], self.y + other[1])
        return NotImplemented

    def __sub__(self, other: Point | Sequence[float]) -> Point:
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        if isinstance(other, (tuple, list)) and len(other) == 2:
            return Point(self.x - other[0], self.y - other[1])
        return NotImplemented

    def __neg__(self) -> Point:
        return Point(-self.x, -self.y)

    def move(self, dx: float = 0, dy: float = 0) -> Point:
        """Return a new point translated by ``(dx, dy)``."""
        return Point(self.x + dx, self.y + dy)

    def translated_by(self, vector: Point | Sequence[float]) -> Point:
        """Return a new point translated by ``vector``."""
        if isinstance(vector, Point):
            return self.move(vector.x, vector.y)
        return self.move(vector[0], vector[1])

    def scale(self, sx: float, sy: float) -> Point:
        """Return a new point scaled about the origin."""
        return Point(self.x * sx, self.y * sy)

    def as_tuple(self) -> tuple[float, float]:
        """Return the point as an ``(x, y)`` tuple."""
        return (self.x, self.y)


@dataclass(frozen=True)
class Rect:
    """An immutable axis-aligned rectangle defined by two corner points."""

    bottom_left: Point
    top_right: Point

    def __post_init__(self) -> None:
        if self.bottom_left.x > self.top_right.x or self.bottom_left.y > self.top_right.y:
            raise ValueError(
                f"Invalid rectangle: bottom_left={self.bottom_left.as_tuple()} "
                f"must not be above/right of top_right={self.top_right.as_tuple()}"
            )

    @classmethod
    def from_lbrt(
        cls,
        left: float,
        bottom: float,
        right: float,
        top: float,
    ) -> Rect:
        """Create a rectangle from left/bottom/right/top coordinates."""
        return cls(Point(left, bottom), Point(right, top))

    @classmethod
    def from_center(cls, center: Point, width: float, height: float) -> Rect:
        """Create a rectangle from a center point and dimensions."""
        half_w = width / 2.0
        half_h = height / 2.0
        return cls(
            Point(center.x - half_w, center.y - half_h),
            Point(center.x + half_w, center.y + half_h),
        )

    @classmethod
    def from_size(
        cls,
        width: float,
        height: float,
        origin: Point = Point(0, 0),
    ) -> Rect:
        """Create a rectangle with its bottom-left corner at ``origin``."""
        return cls(origin, Point(origin.x + width, origin.y + height))

    @property
    def left(self) -> float:
        return self.bottom_left.x

    @property
    def bottom(self) -> float:
        return self.bottom_left.y

    @property
    def right(self) -> float:
        return self.top_right.x

    @property
    def top(self) -> float:
        return self.top_right.y

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom

    @property
    def center(self) -> Point:
        return Point((self.left + self.right) / 2.0, (self.bottom + self.top) / 2.0)

    @property
    def top_left(self) -> Point:
        return Point(self.left, self.top)

    @property
    def bottom_right(self) -> Point:
        return Point(self.right, self.bottom)

    @property
    def area(self) -> float:
        return self.width * self.height

    def is_empty(self) -> bool:
        """Return ``True`` if the rectangle has zero width or height."""
        return self.width <= 0 or self.height <= 0

    def move(self, dx: float = 0, dy: float = 0) -> Rect:
        """Return a new rectangle translated by ``(dx, dy)``."""
        return Rect(self.bottom_left.move(dx, dy), self.top_right.move(dx, dy))

    def translated_by(self, vector: Point | Sequence[float]) -> Rect:
        """Return a new rectangle translated by ``vector``."""
        if isinstance(vector, Point):
            return self.move(vector.x, vector.y)
        return self.move(vector[0], vector[1])

    def resize(self, margin: float) -> Rect:
        """Return a new rectangle expanded (or shrunk) uniformly by ``margin``.

        A positive margin grows the rectangle; a negative margin shrinks it.
        """
        if margin < 0:
            limit = min(self.width, self.height) / 2.0
            if abs(margin) > limit:
                raise ValueError(
                    f"margin magnitude {abs(margin)} exceeds half the smaller side {limit}"
                )
        return Rect.from_lbrt(
            self.left - margin,
            self.bottom - margin,
            self.right + margin,
            self.top + margin,
        )

    def scale_from_center(self, sx: float, sy: float) -> Rect:
        """Return a new rectangle scaled about its center."""
        center = self.center
        half_w = (self.width * sx) / 2.0
        half_h = (self.height * sy) / 2.0
        return Rect(
            Point(center.x - half_w, center.y - half_h),
            Point(center.x + half_w, center.y + half_h),
        )

    def contains(self, other: Point | Rect) -> bool:
        """Return ``True`` if this rectangle fully contains ``other``."""
        if isinstance(other, Point):
            return (
                self.left <= other.x <= self.right
                and self.bottom <= other.y <= self.top
            )
        if isinstance(other, Rect):
            return (
                self.left <= other.left
                and self.right >= other.right
                and self.bottom <= other.bottom
                and self.top >= other.top
            )
        return NotImplemented

    def overlaps(self, other: Rect) -> bool:
        """Return ``True`` if this rectangle overlaps ``other``."""
        return (
            self.left < other.right
            and self.right > other.left
            and self.bottom < other.top
            and self.top > other.bottom
        )

    def union(self, other: Rect) -> Rect:
        """Return the smallest rectangle containing both rectangles."""
        return Rect(
            Point(min(self.left, other.left), min(self.bottom, other.bottom)),
            Point(max(self.right, other.right), max(self.top, other.top)),
        )

    def intersection(self, other: Rect) -> Rect:
        """Return the intersection of two rectangles.

        The result may be an empty rectangle (zero width/height) if they do not
        overlap.
        """
        left = max(self.left, other.left)
        bottom = max(self.bottom, other.bottom)
        right = min(self.right, other.right)
        top = min(self.top, other.top)
        if right < left or top < bottom:
            # Empty intersection: return a zero-area rectangle at the lower bounds.
            p = Point(left, bottom)
            return Rect(p, p)
        return Rect(Point(left, bottom), Point(right, top))


@dataclass(frozen=True)
class Transformation:
    """A rigid transformation: optional mirroring about the origin followed by translation."""

    offset: Point = Point(0, 0)
    mirror_x: bool = False
    mirror_y: bool = False

    def apply(self, obj: Point | Rect) -> Point | Rect:
        """Apply the transformation to a ``Point`` or ``Rect``."""
        if isinstance(obj, Point):
            x = -obj.x if self.mirror_y else obj.x
            y = -obj.y if self.mirror_x else obj.y
            return Point(x, y) + self.offset
        if isinstance(obj, Rect):
            corners = [
                self.apply(obj.bottom_left),
                self.apply(obj.top_right),
                self.apply(obj.bottom_right),
                self.apply(obj.top_left),
            ]
            xs = [p.x for p in corners]
            ys = [p.y for p in corners]
            return Rect(Point(min(xs), min(ys)), Point(max(xs), max(ys)))
        raise TypeError(f"Cannot apply transformation to {type(obj)}")

    def then_translate(self, dx: float, dy: float) -> Transformation:
        """Return a new transformation with an additional translation applied after this one."""
        return Transformation(offset=self.offset.move(dx, dy), mirror_x=self.mirror_x, mirror_y=self.mirror_y)

    def __mul__(self, other: Transformation) -> Transformation:
        """Compose two transformations: ``self * other`` applies ``other`` first."""
        # Apply other's mirrors, then its offset, then self's mirrors and offset.
        def compose_mirror(a: bool, b: bool) -> bool:
            return a ^ b

        return Transformation(
            offset=self.apply(other.offset),
            mirror_x=compose_mirror(self.mirror_x, other.mirror_x),
            mirror_y=compose_mirror(self.mirror_y, other.mirror_y),
        )


def translate(dx: float, dy: float) -> Transformation:
    """Return a pure translation transformation."""
    return Transformation(offset=Point(dx, dy))


def mirror_x() -> Transformation:
    """Return a transformation that mirrors points across the x-axis (flips y)."""
    return Transformation(mirror_x=True)


def mirror_y() -> Transformation:
    """Return a transformation that mirrors points across the y-axis (flips x)."""
    return Transformation(mirror_y=True)


def repeat(
    shape: Rect | Point,
    step: Point | Sequence[float],
    count: int,
) -> list[Rect | Point]:
    """Return ``count`` copies of ``shape`` stepped by ``step``.

    The first copy is the original shape at index 0.
    """
    if count < 0:
        raise ValueError("count must be non-negative")
    if isinstance(step, (tuple, list)):
        step_p = Point(step[0], step[1])
    else:
        step_p = step
    return [shape.translated_by(step_p.scale(i, i)) for i in range(count)]


__all__ = [
    "Point",
    "Rect",
    "Transformation",
    "translate",
    "mirror_x",
    "mirror_y",
    "repeat",
]
