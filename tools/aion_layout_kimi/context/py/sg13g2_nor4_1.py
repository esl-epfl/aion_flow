# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nor4_1
# ================================================================

"""Generated AION cell for sg13g2_nor4_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 2880.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 2880.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(280.0, 590.0), Point(280.0, 1330.0), Point(2565.0, 1330.0), Point(2565.0, 1075.0), Point(2620.0, 1075.0), Point(2620.0, 590.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(280.0, 2060.0, 2670.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2880.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2880.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 1000.0, 510.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1020.0, 1525.0, 1180.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(420.0, 1525.0, 580.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1510.0, 1525.0, 1670.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2085.0, 1525.0, 2245.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2440.0, 2950.0, 2600.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2440.0, 2610.0, 2600.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2440.0, 2270.0, 2600.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 2950.0, 510.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 2610.0, 510.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 2270.0, 510.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 1000.0, 1020.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 660.0, 1020.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1880.0, 1000.0, 2040.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1880.0, 660.0, 2040.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 660.0, 510.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1370.0, 660.0, 1530.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2390.0, 660.0, 2550.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(620.0, 410.0), Point(620.0, 1455.0), Point(350.0, 1455.0), Point(350.0, 1755.0), Point(620.0, 1755.0), Point(620.0, 3360.0), Point(750.0, 3360.0), Point(750.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1130.0, 410.0), Point(1130.0, 1455.0), Point(950.0, 1455.0), Point(950.0, 1755.0), Point(1130.0, 1755.0), Point(1130.0, 3360.0), Point(1260.0, 3360.0), Point(1260.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1640.0, 410.0), Point(1640.0, 1455.0), Point(1440.0, 1455.0), Point(1440.0, 1755.0), Point(1640.0, 1755.0), Point(1640.0, 3360.0), Point(1770.0, 3360.0), Point(1770.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2150.0, 410.0), Point(2150.0, 1455.0), Point(2015.0, 1455.0), Point(2015.0, 1755.0), Point(2150.0, 1755.0), Point(2150.0, 3360.0), Point(2280.0, 3360.0), Point(2280.0, 1755.0), Point(2315.0, 1755.0), Point(2315.0, 1455.0), Point(2280.0, 1455.0), Point(2280.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2880.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2880.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(330.0, 1455.0, 630.0, 1905.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(835.0, 1455.0, 1080.0, 1905.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1300.0, 1905.0, 1580.0, 2335.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1800.0, 2335.0, 2060.0, 2740.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2280.0, 2220.0, 2700.0, 3160.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1900.0, 1455.0), Point(1900.0, 2335.0), Point(1800.0, 2335.0), Point(1800.0, 2740.0), Point(2060.0, 2740.0), Point(2060.0, 1905.0), Point(2320.0, 1905.0), Point(2320.0, 1455.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1410.0, 1455.0), Point(1410.0, 1905.0), Point(1300.0, 1905.0), Point(1300.0, 2335.0), Point(1580.0, 2335.0), Point(1580.0, 1735.0), Point(1720.0, 1735.0), Point(1720.0, 1455.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(810.0, 610.0), Point(810.0, 1210.0), Point(2505.0, 1210.0), Point(2505.0, 2220.0), Point(2280.0, 2220.0), Point(2280.0, 3160.0), Point(2700.0, 3160.0), Point(2700.0, 1050.0), Point(2090.0, 1050.0), Point(2090.0, 610.0), Point(1830.0, 610.0), Point(1830.0, 1050.0), Point(1070.0, 1050.0), Point(1070.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(835.0, 1455.0), Point(835.0, 1905.0), Point(1080.0, 1905.0), Point(1080.0, 1735.0), Point(1230.0, 1735.0), Point(1230.0, 1455.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2880.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(300.0, 2220.0, 560.0, 3560.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(330.0, 1455.0, 630.0, 1905.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(300.0, 220.0, 560.0, 1210.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1320.0, 220.0, 1580.0, 870.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2880.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2340.0, 220.0, 2600.0, 870.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1110.0, 5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1170.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(960.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(1440.0, 2100.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(2400.0, 2520.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(480.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(1920.0, 2520.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3120.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2950.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2950.0, 3600.0)))

    # Ports
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1110.0, 5.0, 1110.0, 5.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1170.0, 3780.0, 1170.0, 3780.0), direction='POWER'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(960.0, 1680.0, 960.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(1440.0, 2100.0, 1440.0, 2100.0), direction='INPUT'))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(2400.0, 2520.0, 2400.0, 2520.0), direction='OUTPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(480.0, 1680.0, 480.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(1920.0, 2520.0, 1920.0, 2520.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nor4_1', sg13g2_tech)
    c.write_gds("sg13g2_nor4_1.gds")
