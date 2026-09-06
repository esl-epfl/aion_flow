# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-scaffolded generator for AION_nand2_o21ai_0
# ================================================================

"""SCAFFOLD ONLY -- an unfinished starting point for AION_nand2_o21ai_0.

Written by aion_layout.scaffold from the target netlist.  It places a
poly gate under every input and nothing else that a cell needs.  It
will not pass DRC and it cannot pass LVS; do not mistake it for a cell.

Netlist: .subckt AION_nand2_o21ai_0 I0 I1 I2 I3 O0 VDD VSS
Devices: 5 nmos, 5 pmos
Inputs:  I0 I1 I2 I3   Output: O0
Internal nets (undrawn): Xg0_net1 Xg1_net1 Xg1_net14 w0

DELIBERATELY MISSING -- the model draws these:

1. Source/drain contacts. No Cont is drawn anywhere, so no transistor
   terminal reaches Metal1 and no device is wired to anything.
2. Routing. The Metal1 shapes are isolated stubs: one bar per input gate and
   one stub for the output. Internal nets have no geometry at all.
3. Substrate and well taps. Neither rail is tapped, which auto_scaffold
   records as eight LU.a/LU.b latch-up violations in a live DRC run.
4. Minimum area. At the default cell width the input/output stubs are below
   M1.d (0.09 um^2); auto_scaffold records four such violations.
5. Net labels. draw_power_rail() adds a Port and no TextShape, so VDD/VSS
   reach the GDS as a pin text (8/2) with no Metal1 label text (8/25), and
   no internal net is labelled at all.
6. Well/implant detail. One NWell rectangle covers the p-row; there is no
   PSD/NSD tap implant and no per-row implant sizing.
7. Device sizing. Both diffusion strips are one nominal height; the
   netlist's w= values are not honoured, so extracted widths will not match.
"""

from aion_layout.building_blocks import draw_diffusion, draw_pin, draw_power_rail
from aion_layout.cell import Cell, Port
from aion_layout.primitives import Rect
from aion_layout.shapes import RectShape
from aion_layout.tech import Tech

CELL_WIDTH = 3840.0
CELL_HEIGHT = 3780.0

# Active areas.  Adjust widths/heights during iteration.
NMOS_ACTIVE = Rect.from_lbrt(240.0, 590.0, 3600.0, 1330.0)
PMOS_ACTIVE = Rect.from_lbrt(240.0, 2060.0, 3600.0, 3180.0)

# (input_net, gate_center_x) left-to-right.
GATES = [
    ("I0", 912.0),
    ("I1", 1584.0),
    ("I2", 2256.0),
    ("I3", 2928.0),
]


def _input_bar_rect(x_center: float, y_center: float) -> tuple[float, float, float, float]:
    half_w = 145.0
    half_h = 140.0
    return (x_center - half_w, y_center - half_h, x_center + half_w, y_center + half_h)


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, CELL_WIDTH, CELL_HEIGHT))

    # Diffusion.
    cell.merge_subcell(draw_diffusion(NMOS_ACTIVE, "n", tech))
    cell.merge_subcell(draw_diffusion(PMOS_ACTIVE, "p", tech))

    # NWell encloses the PMOS active area.
    cell.add_shape(RectShape(tech["NWell"], Rect.from_lbrt(-240.0, 1750.0,
                                              CELL_WIDTH + 240.0, 4170.0)))

    # Power rails.
    cell.merge_subcell(draw_power_rail(0.0, 440.0, "VSS", tech, CELL_WIDTH))
    cell.merge_subcell(draw_power_rail(CELL_HEIGHT, 440.0, "VDD", tech, CELL_WIDTH))

    # Poly gates and input bars (stubs).
    for net, x in GATES:
        cell.add_shape(RectShape(tech["GatPoly"], Rect.from_lbrt(x - 65.0, 410.0,
                                                                x + 65.0, 3360.0)))
        cell.merge_subcell(draw_pin(tech["Metal1"], Rect.from_lbrt(*_input_bar_rect(x, 1920.0)), net, tech=tech))

    # Output pin (stub).  Replace with the real output Metal1 polygon.
    # It sits in its own Metal1 band, below the input bars, so it cannot
    # merge with the input bar of a gate placed at CELL_WIDTH/2.
    cell.merge_subcell(draw_pin(tech["Metal1"], Rect.from_lbrt(CELL_WIDTH/2 - 130.0, 1330.0,
                                                              CELL_WIDTH/2 + 130.0, 1600.0), "O0", tech=tech))

    return cell

if __name__ == "__main__":
    import sys

    from aion_layout.tech import sg13g2_tech

    out = sys.argv[1] if len(sys.argv) > 1 else 'AION_nand2_o21ai_0.gds'
    generate('AION_nand2_o21ai_0', sg13g2_tech).write_gds(out)
    print(f"wrote {out}")
