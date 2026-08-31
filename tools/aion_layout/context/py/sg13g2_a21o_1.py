# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_a21o_1
# ================================================================

"""Generated AION cell for sg13g2_a21o_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(925.0, 700.0), Point(925.0, 1290.0), Point(1035.0, 1290.0), Point(1035.0, 1440.0), Point(3195.0, 1440.0), Point(3195.0, 800.0), Point(1760.0, 800.0), Point(1760.0, 700.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(280.0, 2060.0, 1090.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1310.0, 2180.0, 3195.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3360.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3360.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 2950.0, 510.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 2555.0, 510.0, 2715.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 2165.0, 510.0, 2325.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(680.0, 1625.0, 840.0, 1785.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 2950.0, 1020.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 2555.0, 1020.0, 2715.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 2165.0, 1020.0, 2325.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(995.0, 935.0, 1155.0, 1095.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1385.0, 2950.0, 1545.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1385.0, 2605.0, 1545.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1385.0, 2255.0, 1545.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1505.0, 780.0, 1665.0, 940.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1760.0, 1755.0, 1920.0, 1915.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 2950.0, 2065.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 2605.0, 2065.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 2255.0, 2065.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2070.0, 880.0, 2230.0, 1040.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2300.0, 1755.0, 2460.0, 1915.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2455.0, 2950.0, 2615.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2455.0, 2605.0, 2615.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2900.0, 455.0, 3060.0, 615.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2965.0, 2950.0, 3125.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2965.0, 2605.0, 3125.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2965.0, 2255.0, 3125.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2965.0, 1195.0, 3125.0, 1355.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1265.0, 520.0), Point(1265.0, 1615.0), Point(925.0, 1615.0), Point(925.0, 1540.0), Point(575.0, 1540.0), Point(575.0, 1870.0), Point(620.0, 1870.0), Point(620.0, 3360.0), Point(750.0, 3360.0), Point(750.0, 1870.0), Point(925.0, 1870.0), Point(925.0, 1765.0), Point(1395.0, 1765.0), Point(1395.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1830.0, 620.0), Point(1830.0, 1670.0), Point(1660.0, 1670.0), Point(1660.0, 3360.0), Point(1790.0, 3360.0), Point(1790.0, 2105.0), Point(2005.0, 2105.0), Point(2005.0, 1670.0), Point(1960.0, 1670.0), Point(1960.0, 620.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2340.0, 620.0), Point(2340.0, 1670.0), Point(2215.0, 1670.0), Point(2215.0, 3360.0), Point(2345.0, 3360.0), Point(2345.0, 2000.0), Point(2545.0, 2000.0), Point(2545.0, 1670.0), Point(2470.0, 1670.0), Point(2470.0, 620.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2725.0, 370.0), Point(2725.0, 3360.0), Point(2855.0, 3360.0), Point(2855.0, 700.0), Point(3145.0, 700.0), Point(3145.0, 370.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2250.0, 1525.0, 2545.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2760.0, 405.0, 3110.0, 965.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1755.0, 1525.0, 2050.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(285.0, 2095.0, 560.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3360.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3360.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(205.0, 885.0), Point(205.0, 3160.0), Point(560.0, 3160.0), Point(560.0, 2095.0), Point(445.0, 2095.0), Point(445.0, 1145.0), Point(1225.0, 1145.0), Point(1225.0, 885.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2020.0, 825.0), Point(2020.0, 1145.0), Point(1415.0, 1145.0), Point(1415.0, 1540.0), Point(625.0, 1540.0), Point(625.0, 1870.0), Point(1335.0, 1870.0), Point(1335.0, 3125.0), Point(1595.0, 3125.0), Point(1595.0, 2170.0), Point(1575.0, 2170.0), Point(1575.0, 1305.0), Point(2235.0, 1305.0), Point(2235.0, 825.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1855.0, 2210.0), Point(1855.0, 3125.0), Point(2115.0, 3125.0), Point(2115.0, 2405.0), Point(2915.0, 2405.0), Point(2915.0, 3125.0), Point(3175.0, 3125.0), Point(3175.0, 2210.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(810.0, 2140.0), Point(810.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3360.0, 4000.0), Point(3360.0, 3560.0), Point(2665.0, 3560.0), Point(2665.0, 2585.0), Point(2405.0, 2585.0), Point(2405.0, 3560.0), Point(1070.0, 3560.0), Point(1070.0, 2140.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(1455.0, 220.0), Point(1455.0, 965.0), Point(1715.0, 965.0), Point(1715.0, 220.0), Point(2415.0, 220.0), Point(2415.0, 1310.0), Point(2920.0, 1310.0), Point(2920.0, 1410.0), Point(3165.0, 1410.0), Point(3165.0, 1145.0), Point(2575.0, 1145.0), Point(2575.0, 220.0), Point(3360.0, 220.0), Point(3360.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1755.0, 1525.0, 2050.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2250.0, 1525.0, 2545.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2760.0, 405.0, 3110.0, 965.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'B1', Point(1920.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(430.0, 2615.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1665.0, 3785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1645.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A1', Point(2390.0, 1795.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A2', Point(3015.0, 680.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3600.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3430.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3430.0, 180.0)))

    # Ports
    cell.add_port(Port('B1', 'B1', tech['Metal1'], Rect.from_lbrt(1920.0, 1680.0, 1920.0, 1680.0)))
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(430.0, 2615.0, 430.0, 2615.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1665.0, 3785.0, 1665.0, 3785.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1645.0, 0.0, 1645.0, 0.0), direction='GROUND'))
    cell.add_port(Port('A1', 'A1', tech['Metal1'], Rect.from_lbrt(2390.0, 1795.0, 2390.0, 1795.0)))
    cell.add_port(Port('A2', 'A2', tech['Metal1'], Rect.from_lbrt(3015.0, 680.0, 3015.0, 680.0)))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_a21o_1', sg13g2_tech)
    c.write_gds("sg13g2_a21o_1.gds")
