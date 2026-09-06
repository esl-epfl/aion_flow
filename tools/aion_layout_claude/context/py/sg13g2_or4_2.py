# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_or4_2
# ================================================================

"""Generated AION cell for sg13g2_or4_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 4320.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 4320.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2725.0, 2060.0), Point(2725.0, 2180.0), Point(360.0, 2180.0), Point(360.0, 3180.0), Point(4000.0, 3180.0), Point(4000.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2635.0, 590.0), Point(2635.0, 780.0), Point(1855.0, 780.0), Point(1855.0, 750.0), Point(1410.0, 750.0), Point(1410.0, 780.0), Point(360.0, 780.0), Point(360.0, 1330.0), Point(3970.0, 1330.0), Point(3970.0, 590.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 4320.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 4320.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3740.0, 660.0, 3900.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3740.0, 1000.0, 3900.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3185.0, 1000.0, 3345.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3185.0, 660.0, 3345.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3205.0, 2610.0, 3365.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3205.0, 2950.0, 3365.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3770.0, 2610.0, 3930.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3770.0, 2270.0, 3930.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3770.0, 2950.0, 3930.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1800.0, 1725.0, 1960.0, 1885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(630.0, 1725.0, 790.0, 1885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2915.0, 1605.0, 3075.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2370.0, 1655.0, 2530.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1230.0, 1725.0, 1390.0, 1885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2165.0, 850.0, 2325.0, 1010.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 2950.0, 590.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 2610.0, 590.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 2270.0, 590.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3205.0, 2270.0, 3365.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(940.0, 850.0, 1100.0, 1010.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 850.0, 590.0, 1010.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1505.0, 820.0, 1665.0, 980.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2675.0, 840.0, 2835.0, 1000.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2695.0, 2950.0, 2855.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2695.0, 2610.0, 2855.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1210.0, 600.0), Point(1210.0, 1640.0), Point(1145.0, 1640.0), Point(1145.0, 1970.0), Point(1210.0, 1970.0), Point(1210.0, 3360.0), Point(1340.0, 3360.0), Point(1340.0, 1970.0), Point(1475.0, 1970.0), Point(1475.0, 1640.0), Point(1340.0, 1640.0), Point(1340.0, 600.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2945.0, 410.0), Point(2945.0, 1520.0), Point(2830.0, 1520.0), Point(2830.0, 1850.0), Point(2965.0, 1850.0), Point(2965.0, 3360.0), Point(3095.0, 3360.0), Point(3095.0, 1850.0), Point(3160.0, 1850.0), Point(3160.0, 1520.0), Point(3075.0, 1520.0), Point(3075.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1925.0, 600.0), Point(1925.0, 1640.0), Point(1715.0, 1640.0), Point(1715.0, 1970.0), Point(1925.0, 1970.0), Point(1925.0, 3360.0), Point(2055.0, 3360.0), Point(2055.0, 600.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2435.0, 600.0), Point(2435.0, 1570.0), Point(2285.0, 1570.0), Point(2285.0, 1900.0), Point(2435.0, 1900.0), Point(2435.0, 3360.0), Point(2565.0, 3360.0), Point(2565.0, 1900.0), Point(2620.0, 1900.0), Point(2620.0, 1570.0), Point(2565.0, 1570.0), Point(2565.0, 600.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(700.0, 600.0), Point(700.0, 1640.0), Point(545.0, 1640.0), Point(545.0, 1970.0), Point(700.0, 1970.0), Point(700.0, 3360.0), Point(830.0, 3360.0), Point(830.0, 1970.0), Point(875.0, 1970.0), Point(875.0, 1640.0), Point(830.0, 1640.0), Point(830.0, 600.0)]))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(3500.0, 1840.0, 3630.0, 1880.0)))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(3160.0, 1520.0, 3630.0, 1850.0)))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(3500.0, 410.0, 3630.0, 1520.0)))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(3500.0, 1880.0, 3630.0, 3360.0)))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 4320.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3155.0, 2220.0, 3500.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2270.0, 1545.0, 2605.0, 1975.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(265.0, 1545.0, 875.0, 1935.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 4320.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1180.0, 1545.0, 1570.0, 1970.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1750.0, 1545.0, 2045.0, 1970.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(890.0, 800.0), Point(890.0, 1365.0), Point(2785.0, 1365.0), Point(2785.0, 2190.0), Point(380.0, 2190.0), Point(380.0, 3160.0), Point(640.0, 3160.0), Point(640.0, 2380.0), Point(2955.0, 2380.0), Point(2955.0, 1850.0), Point(3160.0, 1850.0), Point(3160.0, 1520.0), Point(2995.0, 1520.0), Point(2995.0, 1195.0), Point(2375.0, 1195.0), Point(2375.0, 800.0), Point(2115.0, 800.0), Point(2115.0, 1195.0), Point(1150.0, 1195.0), Point(1150.0, 800.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3180.0, 610.0), Point(3180.0, 1210.0), Point(3340.0, 1210.0), Point(3340.0, 2220.0), Point(3155.0, 2220.0), Point(3155.0, 3160.0), Point(3500.0, 3160.0), Point(3500.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3720.0, 2220.0), Point(3720.0, 3560.0), Point(2905.0, 3560.0), Point(2905.0, 2585.0), Point(2645.0, 2585.0), Point(2645.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(4320.0, 4000.0), Point(4320.0, 3560.0), Point(3980.0, 3560.0), Point(3980.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(380.0, 220.0), Point(380.0, 1060.0), Point(640.0, 1060.0), Point(640.0, 220.0), Point(1455.0, 220.0), Point(1455.0, 1015.0), Point(1715.0, 1015.0), Point(1715.0, 220.0), Point(2625.0, 220.0), Point(2625.0, 1010.0), Point(2885.0, 1010.0), Point(2885.0, 220.0), Point(3690.0, 220.0), Point(3690.0, 1210.0), Point(3950.0, 1210.0), Point(3950.0, 220.0), Point(4320.0, 220.0), Point(4320.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2270.0, 1545.0, 2605.0, 1975.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1180.0, 1545.0, 1570.0, 1970.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1750.0, 1545.0, 2045.0, 1970.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(265.0, 1545.0, 875.0, 1935.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(3360.0, 2520.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(1295.0, 1765.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(550.0, 1760.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1780.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1575.0, -5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(2445.0, 1755.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(1885.0, 1755.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4560.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 4390.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 4390.0, 3600.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(3360.0, 2520.0, 3360.0, 2520.0)))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(1295.0, 1765.0, 1295.0, 1765.0), direction='INPUT'))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(550.0, 1760.0, 550.0, 1760.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1780.0, 3780.0, 1780.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1575.0, -5.0, 1575.0, -5.0), direction='GROUND'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(2445.0, 1755.0, 2445.0, 1755.0), direction='INPUT'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(1885.0, 1755.0, 1885.0, 1755.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_or4_2', sg13g2_tech)
    c.write_gds("sg13g2_or4_2.gds")
