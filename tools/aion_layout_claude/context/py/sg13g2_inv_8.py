# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_inv_8
# ================================================================

"""Generated AION cell for sg13g2_inv_8."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 4800.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 4800.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 4800.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 4800.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(185.0, 2060.0, 4575.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(185.0, 590.0, 4575.0, 1330.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3315.0, 1000.0, 3475.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2250.0, 1655.0, 2410.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1910.0, 1655.0, 2070.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4345.0, 660.0, 4505.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1570.0, 1655.0, 1730.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1230.0, 1655.0, 1390.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(890.0, 1655.0, 1050.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(255.0, 2950.0, 415.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(255.0, 2610.0, 415.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(255.0, 2270.0, 415.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4345.0, 2950.0, 4505.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4345.0, 2610.0, 4505.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4345.0, 2270.0, 4505.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(765.0, 1000.0, 925.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(765.0, 660.0, 925.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1785.0, 1000.0, 1945.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1785.0, 660.0, 1945.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2805.0, 1000.0, 2965.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2805.0, 660.0, 2965.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3825.0, 1000.0, 3985.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3825.0, 660.0, 3985.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(765.0, 2950.0, 925.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(765.0, 2610.0, 925.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(765.0, 2270.0, 925.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1785.0, 2950.0, 1945.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1785.0, 2610.0, 1945.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1785.0, 2270.0, 1945.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2805.0, 2950.0, 2965.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2805.0, 2610.0, 2965.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2805.0, 2270.0, 2965.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3825.0, 2950.0, 3985.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3825.0, 2610.0, 3985.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3825.0, 2270.0, 3985.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(255.0, 1000.0, 415.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(255.0, 660.0, 415.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1275.0, 660.0, 1435.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2295.0, 660.0, 2455.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3315.0, 660.0, 3475.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4345.0, 1000.0, 4505.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1275.0, 2950.0, 1435.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1275.0, 2610.0, 1435.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3315.0, 2950.0, 3475.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3315.0, 2610.0, 3475.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3315.0, 2270.0, 3475.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2295.0, 2950.0, 2455.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2295.0, 2610.0, 2455.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(525.0, 410.0), Point(525.0, 3360.0), Point(655.0, 3360.0), Point(655.0, 1900.0), Point(1035.0, 1900.0), Point(1035.0, 3360.0), Point(1165.0, 3360.0), Point(1165.0, 1900.0), Point(1545.0, 1900.0), Point(1545.0, 3360.0), Point(1675.0, 3360.0), Point(1675.0, 1900.0), Point(2055.0, 1900.0), Point(2055.0, 3360.0), Point(2185.0, 3360.0), Point(2185.0, 1900.0), Point(2565.0, 1900.0), Point(2565.0, 3360.0), Point(2695.0, 3360.0), Point(2695.0, 1900.0), Point(3075.0, 1900.0), Point(3075.0, 3360.0), Point(3205.0, 3360.0), Point(3205.0, 1900.0), Point(3585.0, 1900.0), Point(3585.0, 3360.0), Point(3715.0, 3360.0), Point(3715.0, 1900.0), Point(4105.0, 1900.0), Point(4105.0, 3360.0), Point(4235.0, 3360.0), Point(4235.0, 410.0), Point(4105.0, 410.0), Point(4105.0, 1570.0), Point(3715.0, 1570.0), Point(3715.0, 410.0), Point(3585.0, 410.0), Point(3585.0, 1570.0), Point(3205.0, 1570.0), Point(3205.0, 410.0), Point(3075.0, 410.0), Point(3075.0, 1570.0), Point(2695.0, 1570.0), Point(2695.0, 410.0), Point(2565.0, 410.0), Point(2565.0, 1570.0), Point(2185.0, 1570.0), Point(2185.0, 410.0), Point(2055.0, 410.0), Point(2055.0, 1570.0), Point(1675.0, 1570.0), Point(1675.0, 410.0), Point(1545.0, 410.0), Point(1545.0, 1570.0), Point(1165.0, 1570.0), Point(1165.0, 410.0), Point(1035.0, 410.0), Point(1035.0, 1570.0), Point(655.0, 1570.0), Point(655.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2740.0, 1530.0, 4035.0, 1840.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(805.0, 1570.0, 2495.0, 1865.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 4800.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 4800.0, 4000.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(205.0, 220.0), Point(205.0, 1210.0), Point(465.0, 1210.0), Point(465.0, 220.0), Point(1225.0, 220.0), Point(1225.0, 870.0), Point(1485.0, 870.0), Point(1485.0, 220.0), Point(2245.0, 220.0), Point(2245.0, 890.0), Point(2505.0, 890.0), Point(2505.0, 220.0), Point(3265.0, 220.0), Point(3265.0, 1210.0), Point(3525.0, 1210.0), Point(3525.0, 220.0), Point(4295.0, 220.0), Point(4295.0, 1210.0), Point(4555.0, 1210.0), Point(4555.0, 220.0), Point(4800.0, 220.0), Point(4800.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(205.0, 2220.0), Point(205.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(4800.0, 4000.0), Point(4800.0, 3560.0), Point(4555.0, 3560.0), Point(4555.0, 2220.0), Point(4295.0, 2220.0), Point(4295.0, 3560.0), Point(3525.0, 3560.0), Point(3525.0, 2220.0), Point(3265.0, 2220.0), Point(3265.0, 3560.0), Point(2505.0, 3560.0), Point(2505.0, 2560.0), Point(2245.0, 2560.0), Point(2245.0, 3560.0), Point(1485.0, 3560.0), Point(1485.0, 2560.0), Point(1225.0, 2560.0), Point(1225.0, 3560.0), Point(465.0, 3560.0), Point(465.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1735.0, 610.0), Point(1735.0, 1050.0), Point(980.0, 1050.0), Point(980.0, 620.0), Point(715.0, 620.0), Point(715.0, 1230.0), Point(2740.0, 1230.0), Point(2740.0, 2220.0), Point(715.0, 2220.0), Point(715.0, 3160.0), Point(975.0, 3160.0), Point(975.0, 2380.0), Point(1735.0, 2380.0), Point(1735.0, 3160.0), Point(1995.0, 3160.0), Point(1995.0, 2380.0), Point(2755.0, 2380.0), Point(2755.0, 3160.0), Point(3015.0, 3160.0), Point(3015.0, 1840.0), Point(3775.0, 1840.0), Point(3775.0, 3160.0), Point(4035.0, 3160.0), Point(4035.0, 610.0), Point(3775.0, 610.0), Point(3775.0, 1530.0), Point(3015.0, 1530.0), Point(3015.0, 610.0), Point(2755.0, 610.0), Point(2755.0, 1070.0), Point(2000.0, 1070.0), Point(2000.0, 610.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(805.0, 1535.0, 2495.0, 1865.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(3650.0, 1640.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(1925.0, 1685.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(2310.0, -20.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(2710.0, 3780.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 5040.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 4870.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 4870.0, 180.0)))

    # Ports
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(3650.0, 1640.0, 3650.0, 1640.0), direction='OUTPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(1925.0, 1685.0, 1925.0, 1685.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(2310.0, -20.0, 2310.0, -20.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(2710.0, 3780.0, 2710.0, 3780.0), direction='POWER'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_inv_8', sg13g2_tech)
    c.write_gds("sg13g2_inv_8.gds")
