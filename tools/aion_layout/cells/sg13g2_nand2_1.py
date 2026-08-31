# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               AI-iterated NAND2 standard-cell generator
# ================================================================

"""AI-iterated NAND2 layout matching the IHP SG13G2 reference cell.

Transistor sizes (from ``nand2.spice``):
  - PMOS: W=1120 nm, L=130 nm (two in parallel between Y and VDD)
  - NMOS: W=740 nm, L=130 nm (two in series between Y and VSS)

Cell dimensions match the reference ``sg13g2_nand2_1.gds``:
  - width: 1920 nm (4 SG13G2 site columns)
  - height: 3780 nm
"""

from aion_layout.building_blocks import draw_diffusion, draw_pin
from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import RectShape
from aion_layout.tech import Tech


# Cell outline.
CELL_WIDTH = 1920.0
CELL_HEIGHT = 3780.0

# Active areas.
NMOS_ACTIVE = Rect.from_lbrt(300.0, 590.0, 1620.0, 1330.0)   # W=740
PMOS_ACTIVE = Rect.from_lbrt(300.0, 2060.0, 1620.0, 3180.0)  # W=1120
VSS_TAP = Rect.from_lbrt(0.0, -150.0, CELL_WIDTH, 150.0)
VDD_TAP = Rect.from_lbrt(0.0, 3630.0, CELL_WIDTH, 3930.0)

# Poly gates: vertical 130 nm channel strip plus a separate contact head.
# Gate B is on the left, gate A on the right.
POLY_B_STRIP = Rect.from_lbrt(640.0, 410.0, 770.0, 3360.0)
POLY_B_HEAD = Rect.from_lbrt(330.0, 1455.0, 640.0, 1755.0)
POLY_A_STRIP = Rect.from_lbrt(1150.0, 410.0, 1280.0, 3360.0)
POLY_A_HEAD = Rect.from_lbrt(1280.0, 1455.0, 1560.0, 1755.0)

# Metal1 connectivity rectangles (same net rectangles merge in the GDS viewer/DRC).
VSS_RAIL = Rect.from_lbrt(0.0, -220.0, CELL_WIDTH, 220.0)
VSS_TAB = Rect.from_lbrt(320.0, 220.0, 580.0, 1275.0)
VDD_RAIL = Rect.from_lbrt(0.0, 3560.0, CELL_WIDTH, 4000.0)
VDD_LEFT_TAB = Rect.from_lbrt(320.0, 2080.0, 580.0, 3560.0)
VDD_RIGHT_TAB = Rect.from_lbrt(1340.0, 2080.0, 1600.0, 3560.0)
Y_STRAP = Rect.from_lbrt(830.0, 1060.0, 1090.0, 3160.0)
Y_NMOS_TAB = Rect.from_lbrt(1090.0, 620.0, 1600.0, 1245.0)

# Input A/B Metal1 bars.
INPUT_A_BAR = Rect.from_lbrt(1270.0, 1470.0, 1600.0, 1900.0)
INPUT_B_BAR = Rect.from_lbrt(330.0, 1470.0, 620.0, 1900.0)


def _place_cont_cut(cell: Cell, center_x: float, center_y: float, tech: Tech) -> None:
    """Place a 160x160 Cont cut."""
    cell.add_shape(
        RectShape(
            tech["Cont"],
            Rect.from_center(Point(center_x, center_y), 160.0, 160.0),
        )
    )


def _add_active_contacts(cell: Cell, tech: Tech) -> None:
    """Place source/drain/tap contact cuts on the active areas."""
    # Power-rail taps.
    for x in (240.0, 720.0, 1200.0, 1680.0):
        _place_cont_cut(cell, x, 0.0, tech)
        _place_cont_cut(cell, x, CELL_HEIGHT, tech)

    # NMOS contacts (B-side / VSS on the left, A-side / Y on the right).
    for y in (750.0, 1145.0):
        _place_cont_cut(cell, 450.0, y, tech)
        _place_cont_cut(cell, 1470.0, y, tech)

    # PMOS contacts (VDD on the sides, Y in the middle).
    for y in (2210.0, 2620.0, 3030.0):
        for x in (450.0, 960.0, 1470.0):
            _place_cont_cut(cell, x, y, tech)


def _add_poly_contacts(cell: Cell, tech: Tech) -> None:
    """Connect the gate poly heads to the A/B input Metal1 bars."""
    _place_cont_cut(cell, 480.0, 1605.0, tech)
    _place_cont_cut(cell, 1410.0, 1605.0, tech)


def generate(name: str, tech: Tech) -> Cell:
    """Generate the NAND2 cell."""
    cell = Cell("sg13g2_nand2_1", tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, CELL_WIDTH, CELL_HEIGHT))

    # Active + implants.
    cell.merge_subcell(draw_diffusion(NMOS_ACTIVE, "n", tech))
    cell.merge_subcell(draw_diffusion(PMOS_ACTIVE, "p", tech))
    cell.merge_subcell(draw_diffusion(VSS_TAP, "p", tech))
    cell.merge_subcell(draw_diffusion(VDD_TAP, "n", tech))

    # NWell encloses the PMOS area and the VDD tap.
    cell.add_shape(RectShape(tech["NWell"], Rect.from_lbrt(-240.0, 1750.0, 2160.0, 4170.0)))

    # PSD covers the PMOS active and the p+ substrate tap.
    cell.add_shape(RectShape(tech["PSD"], Rect.from_lbrt(-70.0, 1760.0, 1990.0, 3600.0)))
    cell.add_shape(RectShape(tech["PSD"], Rect.from_lbrt(-70.0, -180.0, 1990.0, 180.0)))

    # Poly gates.
    cell.add_shape(RectShape(tech["GatPoly"], POLY_B_STRIP))
    cell.add_shape(RectShape(tech["GatPoly"], POLY_B_HEAD))
    cell.add_shape(RectShape(tech["GatPoly"], POLY_A_STRIP))
    cell.add_shape(RectShape(tech["GatPoly"], POLY_A_HEAD))

    # Contacts.
    _add_active_contacts(cell, tech)
    _add_poly_contacts(cell, tech)

    # Metal1 connectivity.
    cell.add_shape(RectShape(tech["Metal1"], VSS_RAIL))
    cell.add_shape(RectShape(tech["Metal1"], VSS_TAB))
    cell.add_shape(RectShape(tech["Metal1"], VDD_RAIL))
    cell.add_shape(RectShape(tech["Metal1"], VDD_LEFT_TAB))
    cell.add_shape(RectShape(tech["Metal1"], VDD_RIGHT_TAB))
    cell.add_shape(RectShape(tech["Metal1"], Y_STRAP))
    cell.add_shape(RectShape(tech["Metal1"], Y_NMOS_TAB))

    # Pins and ports.
    cell.merge_subcell(draw_pin(tech["Metal1"], INPUT_A_BAR, "A", tech=tech))
    cell.merge_subcell(draw_pin(tech["Metal1"], INPUT_B_BAR, "B", tech=tech))
    cell.merge_subcell(draw_pin(tech["Metal1"], Y_STRAP, "Y", tech=tech))
    cell.merge_subcell(draw_pin(tech["Metal1"], VDD_RAIL, "VDD", tech=tech))
    cell.merge_subcell(draw_pin(tech["Metal1"], VSS_RAIL, "VSS", tech=tech))

    cell.ports["A"] = Port("A", "A", tech["GatPoly"], INPUT_A_BAR, direction="INPUT")
    cell.ports["B"] = Port("B", "B", tech["GatPoly"], INPUT_B_BAR, direction="INPUT")
    cell.ports["Y"] = Port("Y", "Y", tech["Metal1"], Y_STRAP, direction="OUTPUT")
    cell.ports["VDD"] = Port("VDD", "VDD", tech["Metal1"], VDD_RAIL, direction="POWER")
    cell.ports["VSS"] = Port("VSS", "VSS", tech["Metal1"], VSS_RAIL, direction="GROUND")

    return cell
