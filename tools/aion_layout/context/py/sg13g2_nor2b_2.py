# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nor2b_2
# ================================================================

"""Generated AION cell for sg13g2_nor2b_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 3360.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 3360.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(790.0, 720.0), Point(790.0, 800.0), Point(250.0, 800.0), Point(250.0, 1440.0), Point(3130.0, 1440.0), Point(3130.0, 720.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(250.0, 2060.0), Point(250.0, 3060.0), Point(790.0, 3060.0), Point(790.0, 3180.0), Point(3130.0, 3180.0), Point(3130.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3360.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3360.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(320.0, 2830.0, 480.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(320.0, 2490.0, 480.0, 2650.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(320.0, 2150.0, 480.0, 2310.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(320.0, 1210.0, 480.0, 1370.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(420.0, 470.0, 580.0, 630.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1370.0, 790.0, 1530.0, 950.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1370.0, 2610.0, 1530.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1370.0, 2950.0, 1530.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2900.0, 2610.0, 3060.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2900.0, 2270.0, 3060.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2390.0, 2950.0, 2550.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2390.0, 2610.0, 2550.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1880.0, 790.0, 2040.0, 950.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1880.0, 2130.0, 2040.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1880.0, 2470.0, 2040.0, 2630.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2250.0, 1705.0, 2410.0, 1865.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2390.0, 2270.0, 2550.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2390.0, 1130.0, 2550.0, 1290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2390.0, 790.0, 2550.0, 950.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(970.0, 1705.0, 1130.0, 1865.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 790.0, 1020.0, 950.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2900.0, 2950.0, 3060.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1370.0, 1130.0, 1530.0, 1290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2900.0, 1130.0, 3060.0, 1290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 1130.0, 1020.0, 1290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 2270.0, 1020.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 2610.0, 1020.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2900.0, 790.0, 3060.0, 950.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 2950.0, 1020.0, 3110.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1130.0, 220.0), Point(1130.0, 1635.0), Point(900.0, 1635.0), Point(900.0, 1935.0), Point(1130.0, 1935.0), Point(1130.0, 3360.0), Point(1260.0, 3360.0), Point(1260.0, 355.0), Point(2660.0, 355.0), Point(2660.0, 3360.0), Point(2790.0, 3360.0), Point(2790.0, 220.0), Point(2660.0, 220.0), Point(2660.0, 225.0), Point(1260.0, 225.0), Point(1260.0, 220.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(350.0, 400.0), Point(350.0, 700.0), Point(590.0, 700.0), Point(590.0, 3240.0), Point(720.0, 3240.0), Point(720.0, 400.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1640.0, 540.0), Point(1640.0, 3360.0), Point(1770.0, 3360.0), Point(1770.0, 1935.0), Point(2150.0, 1935.0), Point(2150.0, 3360.0), Point(2280.0, 3360.0), Point(2280.0, 1935.0), Point(2480.0, 1935.0), Point(2480.0, 1595.0), Point(2280.0, 1595.0), Point(2280.0, 540.0), Point(2150.0, 540.0), Point(2150.0, 1635.0), Point(1770.0, 1635.0), Point(1770.0, 540.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2200.0, 1540.0, 3000.0, 1915.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(340.0, 400.0, 630.0, 980.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3360.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1320.0, 720.0, 1580.0, 1420.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3360.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(810.0, 220.0), Point(810.0, 1340.0), Point(1070.0, 1340.0), Point(1070.0, 220.0), Point(1830.0, 220.0), Point(1830.0, 980.0), Point(2090.0, 980.0), Point(2090.0, 220.0), Point(2850.0, 220.0), Point(2850.0, 1340.0), Point(3110.0, 1340.0), Point(3110.0, 220.0), Point(3360.0, 220.0), Point(3360.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(810.0, 2220.0), Point(810.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3360.0, 4000.0), Point(3360.0, 3560.0), Point(3110.0, 3560.0), Point(3110.0, 2220.0), Point(2850.0, 2220.0), Point(2850.0, 3560.0), Point(1070.0, 3560.0), Point(1070.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(270.0, 1160.0), Point(270.0, 3040.0), Point(530.0, 3040.0), Point(530.0, 1915.0), Point(1180.0, 1915.0), Point(1180.0, 1655.0), Point(530.0, 1655.0), Point(530.0, 1160.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1320.0, 720.0), Point(1320.0, 1420.0), Point(1360.0, 1420.0), Point(1360.0, 2285.0), Point(1830.0, 2285.0), Point(1830.0, 2680.0), Point(2090.0, 2680.0), Point(2090.0, 2080.0), Point(1580.0, 2080.0), Point(1580.0, 1360.0), Point(2600.0, 1360.0), Point(2600.0, 720.0), Point(2340.0, 720.0), Point(2340.0, 1160.0), Point(1580.0, 1160.0), Point(1580.0, 720.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2340.0, 2220.0), Point(2340.0, 2920.0), Point(1580.0, 2920.0), Point(1580.0, 2560.0), Point(1320.0, 2560.0), Point(1320.0, 3160.0), Point(2600.0, 3160.0), Point(2600.0, 2220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(340.0, 400.0, 630.0, 980.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2200.0, 1540.0, 3000.0, 1915.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(2610.0, 1685.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B_N', Point(480.0, 840.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(985.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(1440.0, 840.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(995.0, 5.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-270.0, 1750.0, 3600.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3430.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-100.0, 1760.0, 3430.0, 3600.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(2610.0, 1685.0, 2610.0, 1685.0), direction='INPUT'))
    cell.add_port(Port('B_N', 'B_N', tech['Metal1'], Rect.from_lbrt(480.0, 840.0, 480.0, 840.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(985.0, 3780.0, 985.0, 3780.0), direction='POWER'))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(1440.0, 840.0, 1440.0, 840.0), direction='OUTPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(995.0, 5.0, 995.0, 5.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nor2b_2', sg13g2_tech)
    c.write_gds("sg13g2_nor2b_2.gds")
