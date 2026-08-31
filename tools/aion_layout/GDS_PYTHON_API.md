# AION Python GDS API Reference

This document describes the Python classes and helper functions used to build SG13G2 standard-cell layouts with the `aion_layout` framework. It is intended as a quick reference for AI agents and human users who want to write or modify cell generators without reading the source code.

All coordinates are in **nanometres** unless otherwise noted.

---

## Table of contents

1. [Core workflow](#core-workflow)
2. [Geometry primitives](#geometry-primitives)
   - [`Point`](#point)
   - [`Rect`](#rect)
   - [`Transformation`](#transformation)
3. [Technology data](#technology-data)
   - [`Layer`](#layer)
   - [`Tech`](#tech)
   - [`sg13g2_tech`](#sg13g2_tech)
4. [Shapes](#shapes)
   - [`RectShape`](#rectshape)
   - [`PolygonShape`](#polygonshape)
   - [`TextShape`](#textshape)
5. [Cell container](#cell-container)
   - [`Port`](#port)
   - [`Cell`](#cell)
6. [Building blocks](#building-blocks)
7. [Routing helpers](#routing-helpers)
8. [Complete example](#complete-example)

---

## Core workflow

A typical cell generator follows these steps:

1. Import the framework.
2. Create a `Cell(name, tech)`.
3. Add shapes with `cell.add_shape(...)` or merge sub-cells with `cell.merge_subcell(...)`.
4. Declare ports with `cell.add_port(Port(...))`.
5. Call `cell.write_gds("path/to/cell.gds")`.

The cell generator must expose a function with this signature:

```python
def generate(name: str, tech: aion_layout.tech.Tech) -> aion_layout.cell.Cell:
    ...
```

---

## Geometry primitives

### `Point`

Immutable 2-D point.

```python
from aion_layout.primitives import Point

p = Point(100.0, 200.0)
p2 = p.move(dx=50.0, dy=0.0)          # translated copy
p3 = p.translated_by((50.0, 0.0))     # same, accepts tuple/list
p4 = p.scale(2.0, 2.0)
t = p.as_tuple()                      # (100.0, 200.0)
```

Arithmetic is supported:

```python
p + Point(10, 20)
p - (10, 20)
-p
```

### `Rect`

Immutable axis-aligned rectangle defined by two `Point`s.

```python
from aion_layout.primitives import Rect, Point

# From left/bottom/right/top
r = Rect.from_lbrt(0.0, 0.0, 480.0, 3780.0)

# From centre and size
r = Rect.from_center(Point(240.0, 1890.0), 480.0, 3780.0)

# From size with bottom-left at origin
r = Rect.from_size(480.0, 3780.0)

# Properties
r.left, r.bottom, r.right, r.top
r.width, r.height, r.center, r.area
r.top_left, r.bottom_right

# Methods returning new rectangles
r2 = r.move(dx=10.0)
r3 = r.translated_by((10.0, 0.0))
r4 = r.resize(50.0)                   # grow/shrink uniformly
r5 = r.scale_from_center(2.0, 1.0)
r6 = r.union(other_rect)
r7 = r.intersection(other_rect)

# Predicates
r.contains(Point(10.0, 10.0))
r.contains(other_rect)
r.overlaps(other_rect)
r.is_empty()
```

### `Transformation`

Rigid transformation: optional mirroring about the origin followed by translation.

```python
from aion_layout.primitives import Transformation, translate, mirror_x, mirror_y

t = translate(100.0, 200.0)
t2 = t.then_translate(50.0, 0.0)
t3 = translate(10, 0) * mirror_x()    # compose: other first, then self

p2 = t.apply(Point(1.0, 2.0))
r2 = t.apply(rect)
```

### `repeat`

Create multiple translated copies of a `Rect` or `Point`.

```python
from aion_layout.primitives import repeat, Point, Rect

copies = repeat(Rect.from_size(100, 100), Point(120, 0), count=4)
```

---

## Technology data

### `Layer`

A physical layer with GDSII layer/datatype numbers and optional design rules.

```python
from aion_layout.tech import Layer

layer = Layer(
    name="Metal1",
    gds_layer=8,
    gds_datatype=0,
    min_width=160.0,
    min_spacing=180.0,
    pin_datatype=2,
    label_datatype=25,
)

layer.gds_pair      # (8, 0)
layer.pin_pair      # (8, 2)
layer.label_pair    # (8, 25)
```

### `Tech`

Container for layers, design rules, routing grid, and standard-cell defaults.

```python
from aion_layout.tech import sg13g2_tech

metal1 = sg13g2_tech["Metal1"]
metal1 = sg13g2_tech.get("Metal1")

for layer in sg13g2_tech.layer_list:
    print(layer.name)

# Useful fields
sg13g2_tech.db_unit                         # 1e-9 (metres per nm)
sg13g2_tech.design_rules["min_width_nm"]
sg13g2_tech.design_rules["min_enclosure_nm"]
sg13g2_tech.standard_cell["site_width_nm"]  # 480.0
sg13g2_tech.standard_cell["cell_height_nm"] # 3780.0
```

### `sg13g2_tech`

Global SG13G2 technology object. Layers available by name include:

- `Activ`
- `NSD`, `PSD`
- `NWell`, `PWell`
- `GatPoly`
- `Cont`, `Via1`
- `Metal1`, `Metal2`
- `prBoundary`

---

## Shapes

All shapes are immutable and belong to a `Layer`.

### `RectShape`

Axis-aligned rectangle on a layer.

```python
from aion_layout.shapes import RectShape
from aion_layout.primitives import Rect

shape = RectShape(sg13g2_tech["Metal1"], Rect.from_lbrt(0, 0, 480, 100))
```

### `PolygonShape`

Simple polygon on a layer.

```python
from aion_layout.shapes import PolygonShape
from aion_layout.primitives import Point

shape = PolygonShape(
    sg13g2_tech["Metal1"],
    [Point(0, 0), Point(100, 0), Point(100, 100), Point(0, 100)],
)
```

### `TextShape`

Text label or pin marker on a layer.

```python
from aion_layout.shapes import TextShape
from aion_layout.primitives import Point

label = TextShape(sg13g2_tech["Metal1"], "A", Point(240.0, 1605.0), purpose="label")
pin   = TextShape(sg13g2_tech["Metal1"], "A", Point(240.0, 1605.0), purpose="pin")
```

`purpose` must be `"label"` or `"pin"`. The GDS datatype used is the layer's `label_datatype` or `pin_datatype` respectively.

---

## Cell container

### `Port`

A named terminal on a layer and rectangle.

```python
from aion_layout.cell import Port
from aion_layout.primitives import Rect

port = Port(
    name="A",
    net="A",
    layer=sg13g2_tech["Metal1"],
    rect=Rect.from_lbrt(0, 0, 100, 100),
    direction="INPUT",   # optional: INPUT, OUTPUT, INOUT, POWER, GROUND
)
```

### `Cell`

Container for shapes, ports, and an optional boundary rectangle.

```python
from aion_layout.cell import Cell
from aion_layout.tech import sg13g2_tech
from aion_layout.primitives import Rect

cell = Cell("my_cell", sg13g2_tech)
cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 1920.0, 3780.0))

# Add shapes
cell.add_shape(RectShape(...))

# Add ports
cell.add_port(Port(...))

# Merge another cell (shapes + ports) with an offset
cell.merge_subcell(other_cell, offset=Point(100.0, 0.0))

# Read-only access
cell.shapes      # dict[Layer, list[Shape]]
cell.ports       # dict[str, Port]
cell.bbox        # Rect bounding box of all shapes + boundary

# Write GDS
cell.write_gds("runs/my_cell.gds")
```

---

## Building blocks

Import from `aion_layout.building_blocks`:

```python
from aion_layout.building_blocks import (
    draw_diffusion,
    draw_well,
    draw_poly_gate,
    draw_metal_wire,
    draw_pin,
    draw_power_rail,
    draw_contact,
    draw_via_stack,
    draw_transistor,
)
```

### `draw_diffusion(rect, doping, tech=None)`

Draw active diffusion plus the corresponding implant layer. `doping` is `"n"` or `"p"`. For n-type diffusion no NSD layer is emitted (it is the SG13G2 default).

```python
subcell = draw_diffusion(Rect.from_lbrt(300, 590, 1620, 1330), "n", tech)
cell.merge_subcell(subcell)
```

### `draw_well(rect, well_type, tech=None)`

Draw an `NWell` or `PWell` rectangle.

```python
cell.merge_subcell(draw_well(Rect.from_lbrt(-240, 1750, 2160, 4170), "n", tech))
```

### `draw_poly_gate(rect, tech=None)`

Draw a polysilicon gate rectangle and expose a `"G"` port.

```python
subcell = draw_poly_gate(Rect.from_lbrt(640, 410, 770, 3360), tech)
cell.merge_subcell(subcell)
```

### `draw_metal_wire(layer, rect, tech=None)`

Draw a rectangular metal wire.

```python
cell.merge_subcell(draw_metal_wire(tech["Metal1"], Rect.from_lbrt(0, -220, 1920, 220), tech))
```

### `draw_pin(layer, rect, name, net=None, tech=None)`

Draw a pin: metal rectangle + label/pin text + a port. `net` defaults to `name`.

```python
cell.merge_subcell(draw_pin(tech["Metal1"], input_bar, "A", tech=tech))
```

### `draw_power_rail(y, width, net, tech=None, cell_width=None)`

Draw a horizontal Metal1 power rail. `net` is `"VDD"` or `"VSS"`. `cell_width` defaults to the site width from the technology.

```python
cell.merge_subcell(draw_power_rail(0.0, 440.0, "VSS", tech, cell_width=1920.0))
cell.merge_subcell(draw_power_rail(3780.0, 440.0, "VDD", tech, cell_width=1920.0))
```

### `draw_contact(stack, rect, tech=None)`

Draw a contact/via stack. `stack` is `[top_layer, cut_layer, bottom_layer]`. The cut is centred in `rect` and the conductors are sized by enclosure rules.

```python
cell.merge_subcell(draw_contact(["Metal1", "Cont", "Activ"], cut_rect, tech))
```

### `draw_via_stack(from_layer, to_layer, rect, tech=None)`

Convenience wrapper for a single via between adjacent layers. Supported pairs:

- `Metal1` ↔ `Metal2` (`Via1`)
- `Metal1` ↔ `GatPoly` (`Cont`)
- `Metal1` ↔ `Activ` (`Cont`)

```python
cell.merge_subcell(draw_via_stack("Metal1", "Metal2", via_rect, tech))
```

### `draw_transistor(gate_rect, active_rect, fet_type, fingers=1, tech=None)`

Draw a transistor: diffusion, gate, and source/drain contacts. Currently only `fingers=1` is supported. The gate must be vertical (`width < height`). Returns a cell with `"S"` and `"D"` ports.

```python
subcell = draw_transistor(
    gate_rect=Rect.from_lbrt(640, 410, 770, 3360),
    active_rect=Rect.from_lbrt(300, 590, 1620, 1330),
    fet_type="n",
    tech=tech,
)
cell.merge_subcell(subcell)
```

---

## Routing helpers

Import from `aion_layout.router`:

```python
from aion_layout.router import draw_wire, connect_ports, draw_via_stack
```

### `draw_wire(layer, path, width=None, tech=None)`

Draw a Manhattan wire along a sequence of `Point`s. Width defaults to the layer's minimum width.

```python
wire = draw_wire(
    tech["Metal1"],
    [Point(0, 0), Point(100, 0), Point(100, 200)],
    width=160.0,
    tech=tech,
)
cell.merge_subcell(wire)
```

### `connect_ports(port_a, port_b, layer, width=None, tech=None)`

Create an L-shaped wire connecting the centres of two ports on the same layer.

```python
wire = connect_ports(port_a, port_b, tech["Metal1"], tech=tech)
cell.merge_subcell(wire)
```

### `draw_via_stack(from_layer, to_layer, rect, tech=None)`

Same helper as in `building_blocks`, re-exported for convenience.

---

## Complete example

```python
from aion_layout.building_blocks import draw_diffusion, draw_pin, draw_power_rail
from aion_layout.cell import Cell, Port
from aion_layout.primitives import Rect
from aion_layout.shapes import RectShape
from aion_layout.tech import Tech

CELL_WIDTH = 1920.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, CELL_WIDTH, CELL_HEIGHT))

    # Diffusion
    cell.merge_subcell(draw_diffusion(Rect.from_lbrt(300, 590, 1620, 1330), "n", tech))
    cell.merge_subcell(draw_diffusion(Rect.from_lbrt(300, 2060, 1620, 3180), "p", tech))

    # NWell around PMOS
    cell.add_shape(RectShape(tech["NWell"], Rect.from_lbrt(-240, 1750, 2160, 4170)))

    # Power rails
    cell.merge_subcell(draw_power_rail(0.0, 440.0, "VSS", tech, CELL_WIDTH))
    cell.merge_subcell(draw_power_rail(CELL_HEIGHT, 440.0, "VDD", tech, CELL_WIDTH))

    # Input pin
    cell.merge_subcell(
        draw_pin(tech["Metal1"], Rect.from_lbrt(330, 1470, 620, 1900), "A", tech=tech)
    )
    cell.ports["A"] = Port(
        "A", "A", tech["GatPoly"], Rect.from_lbrt(330, 1470, 620, 1900), direction="INPUT"
    )

    return cell
```

Save the file and generate the GDS:

```bash
python3 scripts/generate_cell.py cells/my_cell.py runs/my_cell.gds
```
