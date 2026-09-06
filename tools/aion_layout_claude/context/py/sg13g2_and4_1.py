# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_and4_1
# ================================================================

"""Generated AION cell for sg13g2_and4_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(405.0, 590.0), Point(405.0, 1230.0), Point(2605.0, 1230.0), Point(2605.0, 1330.0), Point(3485.0, 1330.0), Point(3485.0, 590.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2645.0, 2060.0), Point(2645.0, 2340.0), Point(405.0, 2340.0), Point(405.0, 3180.0), Point(3485.0, 3180.0), Point(3485.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3840.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3840.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3255.0, 660.0, 3415.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3255.0, 1000.0, 3415.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3255.0, 2270.0, 3415.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3255.0, 2610.0, 3415.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3255.0, 2950.0, 3415.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2955.0, 1650.0, 3115.0, 1810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2605.0, 660.0, 2765.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2605.0, 1000.0, 2765.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2590.0, 2610.0, 2750.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2590.0, 2950.0, 2750.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2415.0, 1650.0, 2575.0, 1810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2035.0, 2610.0, 2195.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2035.0, 2950.0, 2195.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1835.0, 1650.0, 1995.0, 1810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1495.0, 2610.0, 1655.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1495.0, 2950.0, 1655.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1335.0, 1650.0, 1495.0, 1810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(985.0, 2610.0, 1145.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(985.0, 2950.0, 1145.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(775.0, 1650.0, 935.0, 1810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(475.0, 660.0, 635.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(475.0, 1000.0, 635.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(475.0, 2610.0, 635.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(475.0, 2950.0, 635.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2875.0, 410.0), Point(2875.0, 3360.0), Point(3005.0, 3360.0), Point(3005.0, 1900.0), Point(3210.0, 1900.0), Point(3210.0, 1570.0), Point(3005.0, 1570.0), Point(3005.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(745.0, 410.0), Point(745.0, 1580.0), Point(705.0, 1580.0), Point(705.0, 1880.0), Point(745.0, 1880.0), Point(745.0, 3360.0), Point(875.0, 3360.0), Point(875.0, 1880.0), Point(1005.0, 1880.0), Point(1005.0, 1580.0), Point(875.0, 1580.0), Point(875.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1255.0, 410.0), Point(1255.0, 3360.0), Point(1385.0, 3360.0), Point(1385.0, 1880.0), Point(1585.0, 1880.0), Point(1585.0, 1580.0), Point(1385.0, 1580.0), Point(1385.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1765.0, 410.0), Point(1765.0, 3360.0), Point(1895.0, 3360.0), Point(1895.0, 1880.0), Point(2065.0, 1880.0), Point(2065.0, 1580.0), Point(1895.0, 1580.0), Point(1895.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2335.0, 410.0), Point(2335.0, 3360.0), Point(2465.0, 3360.0), Point(2465.0, 1880.0), Point(2645.0, 1880.0), Point(2645.0, 1580.0), Point(2465.0, 1580.0), Point(2465.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1800.0, 1455.0, 2045.0, 1985.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2315.0, 1450.0, 2665.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1285.0, 1455.0, 1560.0, 1985.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(725.0, 1455.0, 1080.0, 1985.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3205.0, 2070.0, 3685.0, 3180.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(2550.0, 220.0), Point(2550.0, 1210.0), Point(2815.0, 1210.0), Point(2815.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(425.0, 2560.0), Point(425.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(2800.0, 3560.0), Point(2800.0, 2560.0), Point(2540.0, 2560.0), Point(2540.0, 3560.0), Point(1705.0, 3560.0), Point(1705.0, 2560.0), Point(1445.0, 2560.0), Point(1445.0, 3560.0), Point(685.0, 3560.0), Point(685.0, 2560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3205.0, 610.0), Point(3205.0, 1210.0), Point(3525.0, 1210.0), Point(3525.0, 2070.0), Point(3205.0, 2070.0), Point(3205.0, 3180.0), Point(3685.0, 3180.0), Point(3685.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(355.0, 610.0), Point(355.0, 2380.0), Point(935.0, 2380.0), Point(935.0, 3125.0), Point(1195.0, 3125.0), Point(1195.0, 2380.0), Point(1985.0, 2380.0), Point(1985.0, 3120.0), Point(2245.0, 3120.0), Point(2245.0, 2380.0), Point(3010.0, 2380.0), Point(3010.0, 1870.0), Point(3205.0, 1870.0), Point(3205.0, 1540.0), Point(2850.0, 1540.0), Point(2850.0, 2220.0), Point(525.0, 2220.0), Point(525.0, 1210.0), Point(685.0, 1210.0), Point(685.0, 610.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2315.0, 1450.0, 2665.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1800.0, 1455.0, 2045.0, 1985.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1285.0, 1455.0, 1560.0, 1985.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(725.0, 1455.0, 1080.0, 1985.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(3450.0, 2640.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(1430.0, 1840.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(875.0, 1665.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1885.0, 3770.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1795.0, 10.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(1965.0, 1840.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(2490.0, 1785.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3910.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3910.0, 3600.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(3450.0, 2640.0, 3450.0, 2640.0)))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(1430.0, 1840.0, 1430.0, 1840.0), direction='INPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(875.0, 1665.0, 875.0, 1665.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1885.0, 3770.0, 1885.0, 3770.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1795.0, 10.0, 1795.0, 10.0), direction='GROUND'))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(1965.0, 1840.0, 1965.0, 1840.0), direction='INPUT'))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(2490.0, 1785.0, 2490.0, 1785.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_and4_1', sg13g2_tech)
    c.write_gds("sg13g2_and4_1.gds")
