#!/usr/bin/env python3
"""
Render a GDS layout to a raster image.

The script reads a GDS file with klayout.db, draws every layer/datatype with a
distinct colour, and writes a PNG/JPEG/etc. image using Pillow.  It runs
headless and does not require a Qt display.
"""

import argparse
import sys

from klayout import db
from PIL import Image, ImageDraw

# Default layer colours (layer, datatype) -> (R, G, B, A).
# Fall back to a deterministic colour for unknown layers.
DEFAULT_LAYER_COLOURS: dict[tuple[int, int], tuple[int, int, int, int]] = {
    (1, 0): (255, 50, 50, 60),  # Activ (slightly transparent)
    (5, 0): (50, 255, 50, 60),  # Poly (slightly transparent)
    (6, 0): (200, 200, 200, 60),  # Contact (slightly transparent)
    (8, 0): (50, 100, 255, 60),  # Metal1 (slightly transparent)
    (8, 2): (255, 200, 50, 60),  # Metal1 pin (slightly transparent)
    (14, 0): (255, 150, 200, 15),  # pSD (very transparent)
    (31, 0): (150, 50, 255, 15),  # NWell (very transparent)
    (46, 0): (100, 255, 255, 15),  # PWell (very transparent)
    (189, 4): (180, 180, 180, 15),  # Abutment (very transparent)
}

BACKGROUND_COLOUR: tuple[int, int, int, int] = (0, 0, 0, 255)


def deterministic_colour(layer: int, datatype: int) -> tuple[int, int, int, int]:
    """Return a deterministic ARGB colour for a (layer, datatype) pair."""
    hue = ((layer * 47 + datatype * 13) % 360) / 360.0
    saturation = 0.6 + ((layer + datatype) % 5) * 0.08
    value = 0.75 + ((layer * 7 + datatype) % 4) * 0.05
    return (*hsv_to_rgb(hue, saturation, value), 255)


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    """Convert HSV in [0,1] to RGB in [0,255]."""

    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i %= 6
    rgb = {
        0: (v, t, p),
        1: (q, v, p),
        2: (p, v, t),
        3: (p, q, v),
        4: (t, p, v),
        5: (v, p, q),
    }[i]
    return tuple(int(c * 255) for c in rgb)


def _points_from_polygon(poly: db.Polygon) -> list[tuple[int, int]]:
    """Return a list of (x, y) tuples from a klayout Polygon hull."""
    points: list[tuple[int, int]] = []
    hull_iter = iter(poly.each_point_hull())
    for item in hull_iter:
        if isinstance(item, db.Point):
            points.append((item.x, item.y))
        else:
            # Some klayout versions expose hull points as flat x/y coordinates.
            points.append((int(item), int(next(hull_iter))))
    return points


def collect_polygons(
    layout: db.Layout,
    cell: db.Cell,
    layer_idx: int,
    trans: db.ICplxTrans = db.ICplxTrans(),
) -> list[list[tuple[int, int]]]:
    """Recursively collect flattened polygon points for a layer."""
    polygons: list[list[tuple[int, int]]] = []
    for shape in cell.shapes(layer_idx).each():
        if shape.is_polygon():
            poly = shape.polygon.transformed(trans)
            polygons.append(_points_from_polygon(poly))
        elif shape.is_box():
            box = shape.box.transformed(trans)
            polygons.append(
                [
                    (box.left, box.bottom),
                    (box.right, box.bottom),
                    (box.right, box.top),
                    (box.left, box.top),
                ]
            )
        elif shape.is_path():
            # Render paths as their bounding box for simplicity.
            bbox = shape.path.bbox().transformed(trans)
            polygons.append(
                [
                    (bbox.left, bbox.bottom),
                    (bbox.right, bbox.bottom),
                    (bbox.right, bbox.top),
                    (bbox.left, bbox.top),
                ]
            )

    # Recurse into instances.
    for instance in cell.each_inst():
        child = instance.cell
        child_trans = trans * instance.trans
        polygons.extend(collect_polygons(layout, child, layer_idx, child_trans))

    return polygons


def render_gds(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
    margin: int,
    colours: dict[tuple[int, int], tuple[int, int, int, int]],
    background: tuple[int, int, int, int],
    include_layers: list[tuple[int, int]] | None = None,
    exclude_layers: list[tuple[int, int]] | None = None,
    no_insts: bool = False,
) -> None:
    """Render a GDS file to an image."""
    layout = db.Layout()
    layout.read(input_path)

    top_cell = layout.top_cell()
    if top_cell is None:
        raise RuntimeError("No top cell found in the GDS file.")

    # Determine the bounding box of the layout.
    bbox = top_cell.bbox()
    if bbox.empty():
        raise RuntimeError("Top cell has no bounding box.")

    # Compute a uniform scaling factor that fits the layout in the image.
    layout_width = bbox.width()
    layout_height = bbox.height()
    available_width = width - 2 * margin
    available_height = height - 2 * margin
    scale_x = available_width / layout_width if layout_width > 0 else 1.0
    scale_y = available_height / layout_height if layout_height > 0 else 1.0
    scale = min(scale_x, scale_y)

    offset_x = margin + (available_width - layout_width * scale) / 2.0
    offset_y = margin + (available_height - layout_height * scale) / 2.0

    def to_img(x: int, y: int) -> tuple[float, float]:
        """Map layout coordinates to image coordinates (Y-flipped)."""
        return (
            offset_x + (x - bbox.left) * scale,
            offset_y + (bbox.top - y) * scale,
        )

    # Bottom-to-top draw order.  Large well/implant/outline layers are placed
    # underneath the device/routing layers so that transparent areas tint the
    # image instead of revealing the PNG checkerboard background.
    _DRAW_ORDER: dict[tuple[int, int], int] = {
        (189, 4): 0,  # Abutment / outline
        (31, 0): 1,   # NWell
        (46, 0): 2,   # PWell
        (14, 0): 3,   # pSD
        (1, 0): 4,    # Activ
        (5, 0): 5,    # Poly
        (6, 0): 6,    # Contact
        (8, 0): 7,    # Metal1
        (8, 2): 8,    # Metal1 pin
        (8, 25): 9,   # Metal1 label
    }

    def _draw_order(key: tuple[int, int]) -> int:
        return _DRAW_ORDER.get(key, 100 + key[0])

    layer_infos = []
    for idx in layout.layer_indices():
        info = layout.get_info(idx)
        layer_infos.append((info.layer, info.datatype, idx))
    layer_infos.sort(key=lambda t: (_draw_order((t[0], t[1])), t[0], t[1]))

    # Render layers with proper alpha compositing.  Each layer is drawn onto a
    # transparent scratch image and then alpha-composited onto the background.
    # This prevents transparent polygons from punching holes in the image.
    img = Image.new("RGBA", (width, height), background)

    for layer, datatype, idx in layer_infos:
        key = (layer, datatype)
        if include_layers is not None and key not in include_layers:
            continue
        if exclude_layers is not None and key in exclude_layers:
            continue

        if no_insts:
            # Only draw shapes placed directly in the top cell.
            shapes = []
            for shape in top_cell.shapes(idx).each():
                if shape.is_polygon():
                    shapes.append(_points_from_polygon(shape.polygon))
                elif shape.is_box():
                    box = shape.box
                    shapes.append(
                        [
                            (box.left, box.bottom),
                            (box.right, box.bottom),
                            (box.right, box.top),
                            (box.left, box.top),
                        ]
                    )
        else:
            shapes = collect_polygons(layout, top_cell, idx)

        if not shapes:
            continue

        colour = colours.get(key, deterministic_colour(layer, datatype))
        layer_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer_img)
        for poly in shapes:
            layer_draw.polygon([to_img(x, y) for x, y in poly], fill=colour)
        img = Image.alpha_composite(img, layer_img)

    img.save(output_path)


def parse_layer_list(value: str) -> list[tuple[int, int]]:
    """Parse a comma-separated list of layer/datatype pairs, e.g. '1/0,5/0'."""
    result: list[tuple[int, int]] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split("/")
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(
                f"Invalid layer/datatype pair: {item!r} (expected L/D)"
            )
        result.append((int(parts[0]), int(parts[1])))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a GDS layout to a raster image.",
    )
    parser.add_argument("input", help="Input GDS file")
    parser.add_argument("output", help="Output image file (PNG/JPEG/etc.)")
    parser.add_argument(
        "--width", type=int, default=1600, help="Image width in pixels (default: 1600)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1200,
        help="Image height in pixels (default: 1200)",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=20,
        help="Margin around the layout in pixels (default: 20)",
    )
    parser.add_argument(
        "--include-layers",
        type=parse_layer_list,
        metavar="L/D,L/D",
        help="Only render the given layer/datatype pairs (comma separated, e.g. 1/0,5/0)",
    )
    parser.add_argument(
        "--exclude-layers",
        type=parse_layer_list,
        metavar="L/D,L/D",
        help="Exclude the given layer/datatype pairs (comma separated, e.g. 200/1,200/2)",
    )
    parser.add_argument(
        "--no-insts",
        action="store_true",
        help="Do not recurse into cell instances; only draw shapes in the top cell",
    )

    args = parser.parse_args()

    try:
        render_gds(
            input_path=args.input,
            output_path=args.output,
            width=args.width,
            height=args.height,
            margin=args.margin,
            colours=DEFAULT_LAYER_COLOURS,
            background=BACKGROUND_COLOUR,
            include_layers=args.include_layers,
            exclude_layers=args.exclude_layers,
            no_insts=args.no_insts,
        )
        print(f"Saved image to {args.output}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
