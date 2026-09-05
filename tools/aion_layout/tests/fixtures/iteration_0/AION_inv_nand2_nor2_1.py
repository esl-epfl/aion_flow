# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-scaffolded generator for AION_inv_nand2_nor2_1
# ================================================================

"""Auto-scaffolded cell generator for AION_inv_nand2_nor2_1."""

from aion_layout.building_blocks import draw_diffusion, draw_pin, draw_power_rail
from aion_layout.cell import Cell, Port
from aion_layout.primitives import Rect
from aion_layout.shapes import RectShape
from aion_layout.tech import Tech

CELL_WIDTH = 2880.0
CELL_HEIGHT = 3780.0

# Active areas.  Adjust widths/heights during iteration.
NMOS_ACTIVE = Rect.from_lbrt(240.0, 590.0, 2640.0, 1330.0)
PMOS_ACTIVE = Rect.from_lbrt(240.0, 2060.0, 2640.0, 3180.0)

# (input_net, gate_center_x) left-to-right.
GATES = [
    ("I0", 840.0),
    ("I1", 1440.0),
    ("I2", 2040.0),
]


def _input_bar_rect(x_center: float, y_center: float) -> tuple[float, float, float, float]:
    half_w = 145.0
    half_h = 215.0
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
        cell.merge_subcell(draw_pin(tech["Metal1"], Rect.from_lbrt(*_input_bar_rect(x, 1605.0)), net, tech=tech))

    # Output pin (stub).  Replace with the real output Metal1 polygon.
    cell.merge_subcell(draw_pin(tech["Metal1"], Rect.from_lbrt(CELL_WIDTH/2 - 130.0, 1330.0,
                                                              CELL_WIDTH/2 + 130.0, 2060.0), "O0", tech=tech))

    return cell
