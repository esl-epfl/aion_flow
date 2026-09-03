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

# 480 x 3780 nm is one SG13G2 placement site by the PDK row height, i.e.
# tech.standard_cell["site_width_nm"] and ["cell_height_nm"] -- process facts,
# not a floorplan.

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

# Cell width is a caller decision (here: five placement sites); the row
# height is a PDK fact and comes from the technology.
site_w = sg13g2_tech.standard_cell["site_width_nm"]    # 480.0 nm, PDK site pitch
row_h = sg13g2_tech.standard_cell["cell_height_nm"]    # 3780.0 nm, PDK row height

cell = Cell("my_cell", sg13g2_tech)
cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 5 * site_w, row_h))

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
    draw_tap,
    draw_transistor,
)
```

### Names used by the examples below

The snippets in this section share one set of caller-side variables so they read
as a sequence. Only `site_w`, `row_h`, `rail_w`, `gate_ext`, `gate_w` and
`activ_spacing` are PDK facts, read back from `tech`; every band position is
this example's own decision and yours will be different. Derive your floorplan
from the cell you are building -- from its netlist, its site count and its rail
geometry -- never by copying coordinates out of a document.

```python
# PDK facts.
site_w = tech.standard_cell["site_width_nm"]              # 480.0 nm, PDK site pitch
row_h = tech.standard_cell["cell_height_nm"]              # 3780.0 nm, PDK row height
rail_w = tech.standard_cell["power_rail_width_nm"]        # 440.0 nm, PDK rail width
gate_ext = tech.standard_cell["gate_extension_nm"]        # 185.0 poly past active
gate_w = tech.design_rules["min_width_nm"]["GatPoly"]     # 130.0 nm, minimum poly
activ_spacing = tech.design_rules["min_spacing_nm"]["Activ"]  # 210.0

# This example's own choices.
sites_wide = 5          # cell width, in placement sites
x_margin = 380.0        # active kept this far inside the left/right cell edge
rail_clear = 600.0      # free strip between each rail and the nearest active
nmos_h, pmos_h = 800.0, 1000.0   # active band heights
well_margin = 400.0     # NWell grown this far around the PMOS active

cell_w = sites_wide * site_w
rail_half = rail_w / 2.0        # rails are centred on y = 0 and y = row_h
vss_rail = Rect.from_lbrt(0.0, -rail_half, cell_w, rail_half)
vdd_rail = Rect.from_lbrt(0.0, row_h - rail_half, cell_w, row_h + rail_half)

act_l, act_r = x_margin, cell_w - x_margin
nmos_active = Rect.from_lbrt(act_l, vss_rail.top + rail_clear,
                             act_r, vss_rail.top + rail_clear + nmos_h)
pmos_active = Rect.from_lbrt(act_l, vdd_rail.bottom - rail_clear - pmos_h,
                             act_r, vdd_rail.bottom - rail_clear)
```

### `draw_diffusion(rect, doping, tech=None)`

Draw active diffusion plus the corresponding implant layer. `doping` is `"n"` or `"p"`. For n-type diffusion no NSD layer is emitted (it is the SG13G2 default).

```python
subcell = draw_diffusion(nmos_active, "n", tech)
cell.merge_subcell(subcell)
cell.merge_subcell(draw_diffusion(pmos_active, "p", tech))
```

### `draw_well(rect, well_type, tech=None)`

Draw an `NWell` or `PWell` rectangle.

```python
# The well encloses the PMOS active with the caller's own margin and runs up to
# the top of the row.
nwell = Rect.from_lbrt(
    pmos_active.left - well_margin,
    pmos_active.bottom - well_margin,
    pmos_active.right + well_margin,
    vdd_rail.top,
)
cell.merge_subcell(draw_well(nwell, "n", tech))
```

### `draw_poly_gate(rect, tech=None)`

Draw a polysilicon gate rectangle and expose a `"G"` port.

```python
# Minimum-width poly, crossing both active bands and overhanging each by the
# PDK gate extension.  x is wherever this cell wants the gate.
gate_x = cell_w / 2.0
gate = Rect.from_lbrt(
    gate_x - gate_w / 2.0,
    nmos_active.bottom - gate_ext,
    gate_x + gate_w / 2.0,
    pmos_active.top + gate_ext,
)
subcell = draw_poly_gate(gate, tech)
cell.merge_subcell(subcell)
```

### `draw_metal_wire(layer, rect, tech=None)`

Draw a rectangular metal wire.

```python
# A minimum-width Metal1 link across the gap between the two active bands.
m1_w = tech.design_rules["min_width_nm"]["Metal1"]        # 160.0
link_y = (nmos_active.top + pmos_active.bottom) / 2.0
cell.merge_subcell(draw_metal_wire(
    tech["Metal1"],
    Rect.from_lbrt(act_l, link_y - m1_w / 2.0, act_r, link_y + m1_w / 2.0),
    tech,
))
```

### `draw_pin(layer, rect, name, net=None, tech=None)`

Draw a pin: metal rectangle + label/pin text + a port. `net` defaults to `name`.

```python
cell.merge_subcell(draw_pin(tech["Metal1"], input_bar, "A", tech=tech))
```

### `draw_power_rail(y, width, net, tech=None, cell_width=None)`

Draw a horizontal Metal1 power rail. `net` is `"VDD"` or `"VSS"`. `cell_width` defaults to the site width from the technology.

`y` is the centre line of the rail, so a rail drawn at `0.0` straddles the
bottom row boundary and one drawn at the row height straddles the top.

```python
cell.merge_subcell(draw_power_rail(0.0, rail_w, "VSS", tech, cell_width=cell_w))
cell.merge_subcell(draw_power_rail(row_h, rail_w, "VDD", tech, cell_width=cell_w))
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

### `draw_tap(rect, tap_type, net, tech=None)`

Draw a well/substrate tap: implant, a row of `Cont` cuts, a Metal1 landing, a label and a port. `tap_type` is `"n"` for an n+ tap that ties an `NWell` to VDD, or `"p"` for a p+ tap that ties the p-substrate to VSS. Implants follow the same convention as `draw_diffusion`: `"n"` emits `Activ` alone, `"p"` emits `Activ` plus `PSD`.

`rect` is the tap active area. The cuts are placed along its longer axis at a regular pitch, inset from its edges by the implant-to-cut enclosure (90 nm), and the Metal1 landing is the cut row grown by the Metal1-to-cut enclosure (70 nm). The `Port` and the Metal1 label are both named after `net`, so extraction sees the tie.

The helper derives everything from `rect` and never invents a position, so `rect` is the whole of the caller's decision. Build it from the values the module already holds — its own cell width and height, the rail geometry it drew, the active bands it placed — rather than from copied constants. The names below are the caller's own variables, not part of the API:

```python
# p+ substrate tap tying the bulk to VSS.  Spans the same x-range as the NMOS
# active band and fills the free strip between the VSS rail and that band.
p_tap = Rect.from_lbrt(
    nmos_active.left,
    vss_rail.top,                        # reach the rail: the landing must overlap it
    nmos_active.right,
    nmos_active.bottom - activ_spacing,  # stay clear of the transistor diffusion
)
cell.merge_subcell(draw_tap(p_tap, "p", "VSS", tech))

# n+ tap tying the NWell to VDD.  Mirror construction against the VDD rail; it
# must fall inside the NWell rectangle drawn around the PMOS.
n_tap = Rect.from_lbrt(
    pmos_active.left,
    pmos_active.top + activ_spacing,
    pmos_active.right,
    vdd_rail.bottom,
)
cell.merge_subcell(draw_tap(n_tap, "n", "VDD", tech))
```

For a `"p"` tap the helper emits `Activ` plus `PSD` over `rect`, a row of 160 nm `Cont` cuts inset from its edges, and a Metal1 landing grown around that cut row and carrying the `net` label and port; an `"n"` tap is the same without `PSD`. The tie to the supply comes from that landing overlapping the rail of the same net — `draw_tap` does not draw the rail, so a `rect` that stops short of it produces a tap that is electrically floating. Keep the tap active at least the `Activ` minimum spacing (210 nm) away from the transistor active areas.

Placement is the caller's job: an `"n"` tap must sit inside an `NWell` rectangle, a `"p"` tap outside every `NWell`. `rect` must be at least 340 x 340 nm (one cut plus its enclosure on both sides) or `ValueError` is raised, as it is for an unknown `tap_type`.

All dimensions come from `tech.design_rules` except the contact-to-contact spacing that sets the cut pitch, which the SG13G2 rule table does not carry; it is declared as the module-level constant `_ASSUMED_CONT_SPACING_NM` in `building_blocks.py`.

### `draw_transistor(gate_rect, active_rect, fet_type, fingers=1, tech=None)`

Draw a transistor: diffusion, gate, and source/drain contacts. Currently only `fingers=1` is supported. The gate must be vertical (`width < height`). Returns a cell with `"S"` and `"D"` ports.

```python
subcell = draw_transistor(
    gate_rect=gate,             # the vertical poly built above
    active_rect=nmos_active,
    fet_type="n",
    tech=tech,
)
cell.merge_subcell(subcell)
```

### Latch-up: `LU.a` and `LU.b`

The two SG13G2 latch-up rules bound the distance from a diffusion to a tap of the opposite type:

- `LU.a` -- *P-diff distance to N-tap must be < 20.0um*: every p-diffusion (the PMOS active inside the NWell) needs an n+ tap within 20 um.
- `LU.b` -- *N-diff distance to P-tap must be < 20.0um*: every n-diffusion (the NMOS active in the substrate) needs a p+ tap within 20 um.

A cell that draws no taps at all is infinitely far from a tap, so **every** diffusion region is reported: one `LU.a` item per uncovered p-diffusion region and one `LU.b` item per uncovered n-diffusion region. Poly gates cut an active area into separate regions and each region is counted on its own, so the item count follows the geometry the generator drew, not the transistor count.

The fix is not to move anything: it is to add tap rows with `draw_tap` -- an n+ tap inside the NWell tied to VDD, and a p+ tap in the substrate tied to VSS. Placing them in the strips next to the power rails, where they also serve as the bulk connection for LVS, clears both rules at once.

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

The floorplan below is worked out in the generator from two kinds of input: PDK
facts read from `tech`, and constants this generator declares for itself. Copying
the numbers it happens to produce into another cell is never right -- a cell with
a different transistor count, a different drive strength or different pin
positions needs a different frame, so compute yours the same way, from your own
netlist.

```python
from aion_layout.building_blocks import (
    draw_diffusion,
    draw_pin,
    draw_power_rail,
    draw_well,
)
from aion_layout.cell import Cell, Port
from aion_layout.primitives import Rect
from aion_layout.shapes import RectShape
from aion_layout.tech import Tech

# This generator's own floorplan choices -- not API constants.
SITES_WIDE = 5            # cell width, in placement sites
X_MARGIN_NM = 380.0       # active kept this far inside the left/right cell edge
RAIL_CLEAR_NM = 600.0     # free strip between each rail and the nearest active
NMOS_H_NM = 800.0         # NMOS active height
PMOS_H_NM = 1000.0        # PMOS active height
WELL_MARGIN_NM = 400.0    # NWell grown this far around the PMOS active


def generate(name: str, tech: Tech) -> Cell:
    # PDK facts.
    site_w = tech.standard_cell["site_width_nm"]            # 480.0 nm, site pitch
    row_h = tech.standard_cell["cell_height_nm"]            # 3780.0 nm, row height
    rail_w = tech.standard_cell["power_rail_width_nm"]      # 440.0 nm, rail width
    m1_w = tech.design_rules["min_width_nm"]["Metal1"]      # 160.0
    rail_half = rail_w / 2.0   # rails are centred on y = 0 and y = row_h

    cell_w = SITES_WIDE * site_w
    act_l, act_r = X_MARGIN_NM, cell_w - X_MARGIN_NM
    nmos = Rect.from_lbrt(act_l, rail_half + RAIL_CLEAR_NM,
                          act_r, rail_half + RAIL_CLEAR_NM + NMOS_H_NM)
    pmos_top = row_h - rail_half - RAIL_CLEAR_NM
    pmos = Rect.from_lbrt(act_l, pmos_top - PMOS_H_NM, act_r, pmos_top)

    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, cell_w, row_h))

    # Diffusion.
    cell.merge_subcell(draw_diffusion(nmos, "n", tech))
    cell.merge_subcell(draw_diffusion(pmos, "p", tech))

    # NWell around the PMOS active, run up to the top rail.
    cell.merge_subcell(draw_well(
        Rect.from_lbrt(pmos.left - WELL_MARGIN_NM, pmos.bottom - WELL_MARGIN_NM,
                       pmos.right + WELL_MARGIN_NM, row_h + rail_half),
        "n",
        tech,
    ))

    # Power rails on the row boundaries.
    cell.merge_subcell(draw_power_rail(0.0, rail_w, "VSS", tech, cell_w))
    cell.merge_subcell(draw_power_rail(row_h, rail_w, "VDD", tech, cell_w))

    # Input pin: a Metal1 bar in the gap between the two active bands.
    bar_y = (nmos.top + pmos.bottom) / 2.0
    cell.merge_subcell(draw_pin(
        tech["Metal1"],
        Rect.from_lbrt(act_l, bar_y - m1_w / 2.0, act_l + 2 * m1_w, bar_y + m1_w / 2.0),
        "A",
        tech=tech,
    ))

    # Geometry the helpers did not draw needs its port declared explicitly.
    out = Rect.from_lbrt(act_r - 2 * m1_w, bar_y - m1_w / 2.0,
                         act_r, bar_y + m1_w / 2.0)
    cell.add_shape(RectShape(tech["Metal1"], out))
    cell.add_port(Port("Y", "Y", tech["Metal1"], out, direction="OUTPUT"))

    return cell
```

This cell is a frame only: it has no transistors wired up, no taps and no
output logic. It is the shape of a generator, not a template to fill in.

Save the file and generate the GDS:

```bash
python3 scripts/generate_cell.py cells/my_cell.py runs/my_cell.gds
```
