# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_or4_1
# ================================================================

"""Generated AION cell for sg13g2_or4_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2725.0, 2060.0), Point(2725.0, 2180.0), Point(360.0, 2180.0), Point(360.0, 3180.0), Point(3435.0, 3180.0), Point(3435.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2635.0, 590.0), Point(2635.0, 780.0), Point(1855.0, 780.0), Point(1855.0, 750.0), Point(1410.0, 750.0), Point(1410.0, 780.0), Point(360.0, 780.0), Point(360.0, 1330.0), Point(3435.0, 1330.0), Point(3435.0, 590.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3840.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3840.0, 150.0)))

    # Cont
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1825.0, 1725.0, 1985.0, 1885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(600.0, 1725.0, 760.0, 1885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2915.0, 1605.0, 3075.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2370.0, 1725.0, 2530.0, 1885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1230.0, 1725.0, 1390.0, 1885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2165.0, 905.0, 2325.0, 1065.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 2945.0, 590.0, 3105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 2605.0, 590.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3205.0, 2935.0, 3365.0, 3095.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3205.0, 2540.0, 3365.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3205.0, 2145.0, 3365.0, 2305.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(940.0, 905.0, 1100.0, 1065.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3205.0, 1085.0, 3365.0, 1245.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3205.0, 670.0, 3365.0, 830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 850.0, 590.0, 1010.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1505.0, 825.0, 1665.0, 985.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2685.0, 840.0, 2845.0, 1000.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2695.0, 2930.0, 2855.0, 3090.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2695.0, 2590.0, 2855.0, 2750.0)))
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
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1210.0, 600.0), Point(1210.0, 1655.0), Point(1145.0, 1655.0), Point(1145.0, 1955.0), Point(1210.0, 1955.0), Point(1210.0, 3360.0), Point(1340.0, 3360.0), Point(1340.0, 1955.0), Point(1475.0, 1955.0), Point(1475.0, 1655.0), Point(1340.0, 1655.0), Point(1340.0, 600.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2965.0, 410.0), Point(2965.0, 1520.0), Point(2830.0, 1520.0), Point(2830.0, 1850.0), Point(2965.0, 1850.0), Point(2965.0, 3360.0), Point(3095.0, 3360.0), Point(3095.0, 1850.0), Point(3160.0, 1850.0), Point(3160.0, 1520.0), Point(3095.0, 1520.0), Point(3095.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1925.0, 600.0), Point(1925.0, 1655.0), Point(1715.0, 1655.0), Point(1715.0, 1955.0), Point(1925.0, 1955.0), Point(1925.0, 3360.0), Point(2055.0, 3360.0), Point(2055.0, 600.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2435.0, 600.0), Point(2435.0, 1655.0), Point(2285.0, 1655.0), Point(2285.0, 1955.0), Point(2435.0, 1955.0), Point(2435.0, 3360.0), Point(2565.0, 3360.0), Point(2565.0, 1955.0), Point(2620.0, 1955.0), Point(2620.0, 1655.0), Point(2565.0, 1655.0), Point(2565.0, 600.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(700.0, 600.0), Point(700.0, 1655.0), Point(530.0, 1655.0), Point(530.0, 1955.0), Point(700.0, 1955.0), Point(700.0, 3360.0), Point(830.0, 3360.0), Point(830.0, 600.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3155.0, 2095.0, 3500.0, 3145.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2270.0, 1545.0, 2605.0, 1935.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(320.0, 1545.0, 875.0, 1935.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1145.0, 1545.0, 1560.0, 1935.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1750.0, 1545.0, 2045.0, 1935.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(890.0, 855.0), Point(890.0, 1365.0), Point(2785.0, 1365.0), Point(2785.0, 2190.0), Point(2200.0, 2190.0), Point(2200.0, 2555.0), Point(380.0, 2555.0), Point(380.0, 3160.0), Point(640.0, 3160.0), Point(640.0, 2750.0), Point(2360.0, 2750.0), Point(2360.0, 2380.0), Point(2955.0, 2380.0), Point(2955.0, 1850.0), Point(3160.0, 1850.0), Point(3160.0, 1520.0), Point(2995.0, 1520.0), Point(2995.0, 1195.0), Point(2375.0, 1195.0), Point(2375.0, 855.0), Point(2115.0, 855.0), Point(2115.0, 1195.0), Point(1150.0, 1195.0), Point(1150.0, 855.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3180.0, 620.0), Point(3180.0, 1295.0), Point(3340.0, 1295.0), Point(3340.0, 2095.0), Point(3155.0, 2095.0), Point(3155.0, 3145.0), Point(3500.0, 3145.0), Point(3500.0, 620.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(380.0, 220.0), Point(380.0, 1060.0), Point(640.0, 1060.0), Point(640.0, 220.0), Point(1455.0, 220.0), Point(1455.0, 1000.0), Point(1715.0, 1000.0), Point(1715.0, 220.0), Point(2635.0, 220.0), Point(2635.0, 1010.0), Point(2895.0, 1010.0), Point(2895.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2645.0, 2585.0), Point(2645.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(2905.0, 3560.0), Point(2905.0, 2585.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1750.0, 1545.0, 2045.0, 1935.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2270.0, 1545.0, 2605.0, 1935.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1145.0, 1545.0, 1560.0, 1935.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(320.0, 1545.0, 875.0, 1935.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(3315.0, 2525.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(1295.0, 1765.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(550.0, 1760.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1780.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1575.0, -5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(2445.0, 1755.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(1885.0, 1755.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(0.0, -180.0, 3840.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3910.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3910.0, 180.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(3315.0, 2525.0, 3315.0, 2525.0)))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(1295.0, 1765.0, 1295.0, 1765.0), direction='INPUT'))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(550.0, 1760.0, 550.0, 1760.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1780.0, 3780.0, 1780.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1575.0, -5.0, 1575.0, -5.0), direction='GROUND'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(2445.0, 1755.0, 2445.0, 1755.0), direction='INPUT'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(1885.0, 1755.0, 1885.0, 1755.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_or4_1', sg13g2_tech)
    c.write_gds("sg13g2_or4_1.gds")
