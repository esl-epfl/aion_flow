# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_xor2_1
# ================================================================

"""Generated AION cell for sg13g2_xor2_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 3840.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 3840.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1880.0, 650.0), Point(1880.0, 840.0), Point(235.0, 840.0), Point(235.0, 1390.0), Point(3730.0, 1390.0), Point(3730.0, 650.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1900.0, 2060.0, 3730.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3840.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(395.0, 2180.0, 1600.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3840.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(485.0, 2270.0, 645.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(485.0, 2610.0, 645.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1370.0, 2950.0, 1530.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1155.0, 910.0, 1315.0, 1070.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1950.0, 720.0, 2110.0, 880.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1950.0, 1060.0, 2110.0, 1220.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2480.0, 2950.0, 2640.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2990.0, 2610.0, 3150.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3500.0, 2270.0, 3660.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2885.0, 1060.0, 3045.0, 1220.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2990.0, 2950.0, 3150.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2680.0, 1620.0, 2840.0, 1780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1370.0, 2270.0, 1530.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1370.0, 2610.0, 1530.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3420.0, 725.0, 3580.0, 885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3160.0, 1620.0, 3320.0, 1780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1970.0, 2950.0, 2130.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(645.0, 910.0, 805.0, 1070.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(610.0, 1620.0, 770.0, 1780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(485.0, 2950.0, 645.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(305.0, 910.0, 465.0, 1070.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3500.0, 2610.0, 3660.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3500.0, 2950.0, 3660.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1970.0, 2610.0, 2130.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2885.0, 720.0, 3045.0, 880.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1580.0, 1620.0, 1740.0, 1780.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1680.0, 660.0), Point(1680.0, 1550.0), Point(1510.0, 1550.0), Point(1510.0, 1910.0), Point(1130.0, 1910.0), Point(1130.0, 3365.0), Point(1260.0, 3365.0), Point(1260.0, 2060.0), Point(1670.0, 2060.0), Point(1670.0, 1850.0), Point(1810.0, 1850.0), Point(1810.0, 660.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2610.0, 470.0), Point(2610.0, 1850.0), Point(2750.0, 1850.0), Point(2750.0, 3365.0), Point(2880.0, 3365.0), Point(2880.0, 1850.0), Point(2910.0, 1850.0), Point(2910.0, 1550.0), Point(2740.0, 1550.0), Point(2740.0, 470.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3180.0, 470.0), Point(3180.0, 1550.0), Point(3090.0, 1550.0), Point(3090.0, 1850.0), Point(3260.0, 1850.0), Point(3260.0, 3365.0), Point(3390.0, 3365.0), Point(3390.0, 1550.0), Point(3310.0, 1550.0), Point(3310.0, 470.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(915.0, 320.0), Point(915.0, 1550.0), Point(540.0, 1550.0), Point(540.0, 1850.0), Point(755.0, 1850.0), Point(755.0, 3365.0), Point(885.0, 3365.0), Point(885.0, 1720.0), Point(1045.0, 1720.0), Point(1045.0, 470.0), Point(2240.0, 470.0), Point(2240.0, 3365.0), Point(2370.0, 3365.0), Point(2370.0, 320.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3450.0, 2155.0, 3710.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1530.0, 1550.0, 2890.0, 1830.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(200.0, 1550.0, 820.0, 1830.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1920.0, 2520.0), Point(1920.0, 3160.0), Point(2180.0, 3160.0), Point(2180.0, 2680.0), Point(2940.0, 2680.0), Point(2940.0, 3160.0), Point(3200.0, 3160.0), Point(3200.0, 2520.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(435.0, 2220.0), Point(435.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(2690.0, 3560.0), Point(2690.0, 2900.0), Point(2430.0, 2900.0), Point(2430.0, 3560.0), Point(695.0, 3560.0), Point(695.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(285.0, 220.0), Point(285.0, 1120.0), Point(820.0, 1120.0), Point(820.0, 220.0), Point(1900.0, 220.0), Point(1900.0, 1270.0), Point(2160.0, 1270.0), Point(2160.0, 220.0), Point(3370.0, 220.0), Point(3370.0, 935.0), Point(3630.0, 935.0), Point(3630.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2835.0, 670.0), Point(2835.0, 1315.0), Point(3530.0, 1315.0), Point(3530.0, 2155.0), Point(3450.0, 2155.0), Point(3450.0, 3160.0), Point(3710.0, 3160.0), Point(3710.0, 1115.0), Point(3100.0, 1115.0), Point(3100.0, 670.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1030.0, 860.0), Point(1030.0, 2340.0), Point(1320.0, 2340.0), Point(1320.0, 3160.0), Point(1580.0, 3160.0), Point(1580.0, 2340.0), Point(3270.0, 2340.0), Point(3270.0, 1830.0), Point(3350.0, 1830.0), Point(3350.0, 1570.0), Point(3110.0, 1570.0), Point(3110.0, 2170.0), Point(1200.0, 2170.0), Point(1200.0, 1120.0), Point(1365.0, 1120.0), Point(1365.0, 860.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(200.0, 1550.0, 820.0, 1830.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1530.0, 1550.0, 2890.0, 1830.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(3505.0, 2635.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(2300.0, 3775.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(2255.0, 1725.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(520.0, 1630.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(2090.0, 20.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3910.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3910.0, 3600.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(3505.0, 2635.0, 3505.0, 2635.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(2300.0, 3775.0, 2300.0, 3775.0), direction='POWER'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(2255.0, 1725.0, 2255.0, 1725.0), direction='INPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(520.0, 1630.0, 520.0, 1630.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(2090.0, 20.0, 2090.0, 20.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_xor2_1', sg13g2_tech)
    c.write_gds("sg13g2_xor2_1.gds")
