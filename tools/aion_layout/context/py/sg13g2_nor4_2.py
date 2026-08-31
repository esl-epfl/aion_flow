# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nor4_2
# ================================================================

"""Generated AION cell for sg13g2_nor4_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 5760.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 5760.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(225.0, 2060.0, 1550.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1760.0, 2060.0, 4100.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(4310.0, 2060.0, 5630.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(225.0, 700.0, 5630.0, 1440.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 5760.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 5760.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3530.0, 1670.0, 3690.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 2950.0, 460.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 2610.0, 460.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 2270.0, 460.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 1110.0, 460.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 770.0, 460.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5400.0, 770.0, 5560.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5400.0, 1110.0, 5560.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3190.0, 1670.0, 3350.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(810.0, 2950.0, 970.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(810.0, 2610.0, 970.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(810.0, 2270.0, 970.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(810.0, 1110.0, 970.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(810.0, 770.0, 970.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 1670.0, 800.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1320.0, 2950.0, 1480.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1320.0, 2610.0, 1480.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1320.0, 770.0, 1480.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1830.0, 2950.0, 1990.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1830.0, 2610.0, 1990.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1830.0, 770.0, 1990.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2510.0, 1670.0, 2670.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2340.0, 2610.0, 2500.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2340.0, 2270.0, 2500.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2340.0, 1110.0, 2500.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2340.0, 770.0, 2500.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2850.0, 2950.0, 3010.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2850.0, 2610.0, 3010.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2850.0, 2270.0, 3010.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2850.0, 770.0, 3010.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3360.0, 2610.0, 3520.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3360.0, 2270.0, 3520.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3360.0, 1110.0, 3520.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3360.0, 770.0, 3520.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3870.0, 2950.0, 4030.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3870.0, 2610.0, 4030.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3870.0, 770.0, 4030.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4380.0, 2950.0, 4540.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4380.0, 2610.0, 4540.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4380.0, 2270.0, 4540.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4380.0, 770.0, 4540.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4430.0, 1670.0, 4590.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4890.0, 2610.0, 5050.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4890.0, 2270.0, 5050.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4890.0, 1110.0, 5050.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(980.0, 1670.0, 1140.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4890.0, 770.0, 5050.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5400.0, 2950.0, 5560.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5400.0, 2610.0, 5560.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2170.0, 1670.0, 2330.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5400.0, 2270.0, 5560.0, 2430.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(570.0, 520.0), Point(570.0, 3360.0), Point(700.0, 3360.0), Point(700.0, 1900.0), Point(1080.0, 1900.0), Point(1080.0, 3360.0), Point(1210.0, 3360.0), Point(1210.0, 520.0), Point(1080.0, 520.0), Point(1080.0, 1600.0), Point(700.0, 1600.0), Point(700.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2100.0, 520.0), Point(2100.0, 3360.0), Point(2230.0, 3360.0), Point(2230.0, 1900.0), Point(2610.0, 1900.0), Point(2610.0, 3360.0), Point(2740.0, 3360.0), Point(2740.0, 520.0), Point(2610.0, 520.0), Point(2610.0, 1600.0), Point(2230.0, 1600.0), Point(2230.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3120.0, 520.0), Point(3120.0, 3360.0), Point(3250.0, 3360.0), Point(3250.0, 1900.0), Point(3630.0, 1900.0), Point(3630.0, 3360.0), Point(3760.0, 3360.0), Point(3760.0, 520.0), Point(3630.0, 520.0), Point(3630.0, 1600.0), Point(3250.0, 1600.0), Point(3250.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4650.0, 520.0), Point(4650.0, 1600.0), Point(4360.0, 1600.0), Point(4360.0, 1900.0), Point(4650.0, 1900.0), Point(4650.0, 3360.0), Point(4780.0, 3360.0), Point(4780.0, 1900.0), Point(5160.0, 1900.0), Point(5160.0, 3360.0), Point(5290.0, 3360.0), Point(5290.0, 520.0), Point(5160.0, 520.0), Point(5160.0, 1600.0), Point(4780.0, 1600.0), Point(4780.0, 520.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 5760.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(4025.0, 1560.0, 4640.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2120.0, 1560.0, 2720.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3140.0, 1560.0, 3740.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5100.0, 1520.0, 5485.0, 1840.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 5760.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(590.0, 1560.0, 1190.0, 1880.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(760.0, 720.0), Point(760.0, 1350.0), Point(4840.0, 1350.0), Point(4840.0, 2820.0), Point(5100.0, 2820.0), Point(5100.0, 720.0), Point(4840.0, 720.0), Point(4840.0, 1160.0), Point(3570.0, 1160.0), Point(3570.0, 720.0), Point(3310.0, 720.0), Point(3310.0, 1160.0), Point(2550.0, 1160.0), Point(2550.0, 720.0), Point(2290.0, 720.0), Point(2290.0, 1160.0), Point(1020.0, 1160.0), Point(1020.0, 720.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(760.0, 2180.0), Point(760.0, 3160.0), Point(1020.0, 3160.0), Point(1020.0, 2380.0), Point(2290.0, 2380.0), Point(2290.0, 2820.0), Point(2550.0, 2820.0), Point(2550.0, 2180.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2800.0, 2220.0), Point(2800.0, 3000.0), Point(2040.0, 3000.0), Point(2040.0, 2560.0), Point(1780.0, 2560.0), Point(1780.0, 3180.0), Point(4080.0, 3180.0), Point(4080.0, 2560.0), Point(3820.0, 2560.0), Point(3820.0, 3000.0), Point(3060.0, 3000.0), Point(3060.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(250.0, 220.0), Point(250.0, 1320.0), Point(510.0, 1320.0), Point(510.0, 220.0), Point(1270.0, 220.0), Point(1270.0, 980.0), Point(2040.0, 980.0), Point(2040.0, 220.0), Point(2800.0, 220.0), Point(2800.0, 980.0), Point(3060.0, 980.0), Point(3060.0, 220.0), Point(3820.0, 220.0), Point(3820.0, 980.0), Point(4590.0, 980.0), Point(4590.0, 220.0), Point(5350.0, 220.0), Point(5350.0, 1320.0), Point(5610.0, 1320.0), Point(5610.0, 220.0), Point(5760.0, 220.0), Point(5760.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(250.0, 2220.0), Point(250.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(5760.0, 4000.0), Point(5760.0, 3560.0), Point(1530.0, 3560.0), Point(1530.0, 2560.0), Point(1270.0, 2560.0), Point(1270.0, 3560.0), Point(510.0, 3560.0), Point(510.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5350.0, 2080.0), Point(5350.0, 3000.0), Point(4590.0, 3000.0), Point(4590.0, 2180.0), Point(3310.0, 2180.0), Point(3310.0, 2820.0), Point(3570.0, 2820.0), Point(3570.0, 2380.0), Point(4330.0, 2380.0), Point(4330.0, 3160.0), Point(5610.0, 3160.0), Point(5610.0, 2080.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5100.0, 1520.0, 5485.0, 1840.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3140.0, 1560.0, 3740.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2120.0, 1560.0, 2720.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(590.0, 1560.0, 1190.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(4025.0, 1560.0, 4640.0, 1880.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(5280.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1180.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(4320.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(2040.0, 3775.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(2400.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(960.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1275.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(2085.0, 5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(3360.0, 1680.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 6000.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 5830.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 5830.0, 180.0)))

    # Ports
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(5280.0, 1680.0, 5280.0, 1680.0), direction='OUTPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(2085.0, 5.0, 2085.0, 5.0), direction='GROUND'))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(4320.0, 1680.0, 4320.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1275.0, 3780.0, 1275.0, 3780.0), direction='POWER'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(2400.0, 1680.0, 2400.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(960.0, 1680.0, 960.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(3360.0, 1680.0, 3360.0, 1680.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nor4_2', sg13g2_tech)
    c.write_gds("sg13g2_nor4_2.gds")
