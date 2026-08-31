# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_mux2_2
# ================================================================

"""Generated AION cell for sg13g2_mux2_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 5280.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 5280.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(295.0, 2060.0), Point(295.0, 2900.0), Point(915.0, 2900.0), Point(915.0, 3060.0), Point(3590.0, 3060.0), Point(3590.0, 3180.0), Point(5155.0, 3180.0), Point(5155.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(835.0, 590.0), Point(835.0, 780.0), Point(295.0, 780.0), Point(295.0, 1330.0), Point(5155.0, 1330.0), Point(5155.0, 590.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 5280.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 5280.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4925.0, 660.0, 5085.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4925.0, 2820.0, 5085.0, 2980.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4925.0, 2470.0, 5085.0, 2630.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4925.0, 2130.0, 5085.0, 2290.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3650.0, 2820.0, 3810.0, 2980.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3650.0, 660.0, 3810.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4010.0, 1600.0, 4170.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4330.0, 2950.0, 4490.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4330.0, 2535.0, 4490.0, 2695.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4330.0, 2130.0, 4490.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4330.0, 1000.0, 4490.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4330.0, 660.0, 4490.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3470.0, 1620.0, 3630.0, 1780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2765.0, 1520.0, 2925.0, 1680.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2350.0, 2395.0, 2510.0, 2555.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2350.0, 2735.0, 2510.0, 2895.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2225.0, 1520.0, 2385.0, 1680.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2060.0, 660.0, 2220.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3650.0, 2470.0, 3810.0, 2630.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1680.0, 1520.0, 1840.0, 1680.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(905.0, 660.0, 1065.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1025.0, 2830.0, 1185.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(905.0, 1000.0, 1065.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3650.0, 2130.0, 3810.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(815.0, 1650.0, 975.0, 1810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(365.0, 970.0, 525.0, 1130.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(365.0, 2330.0, 525.0, 2490.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(365.0, 2670.0, 525.0, 2830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4925.0, 1000.0, 5085.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1295.0, 410.0), Point(1295.0, 1570.0), Point(765.0, 1570.0), Point(765.0, 600.0), Point(635.0, 600.0), Point(635.0, 3080.0), Point(765.0, 3080.0), Point(765.0, 1900.0), Point(1295.0, 1900.0), Point(1295.0, 3240.0), Point(1425.0, 3240.0), Point(1425.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3920.0, 410.0), Point(3920.0, 3360.0), Point(4050.0, 3360.0), Point(4050.0, 1850.0), Point(4250.0, 1850.0), Point(4250.0, 1520.0), Point(4050.0, 1520.0), Point(4050.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3390.0, 410.0), Point(3390.0, 3240.0), Point(3520.0, 3240.0), Point(3520.0, 1870.0), Point(3720.0, 1870.0), Point(3720.0, 1540.0), Point(3520.0, 1540.0), Point(3520.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2665.0, 1440.0), Point(2665.0, 3240.0), Point(2795.0, 3240.0), Point(2795.0, 1770.0), Point(2995.0, 1770.0), Point(2995.0, 1440.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2350.0, 410.0), Point(2350.0, 1440.0), Point(2090.0, 1440.0), Point(2090.0, 3240.0), Point(2220.0, 3240.0), Point(2220.0, 1770.0), Point(2480.0, 1770.0), Point(2480.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1780.0, 410.0), Point(1780.0, 1450.0), Point(1610.0, 1450.0), Point(1610.0, 1750.0), Point(1910.0, 1750.0), Point(1910.0, 410.0)]))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(4600.0, 410.0, 4730.0, 3360.0)))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(4050.0, 1520.0, 4730.0, 1850.0)))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(855.0, 220.0), Point(855.0, 1210.0), Point(1090.0, 1210.0), Point(1090.0, 220.0), Point(3600.0, 220.0), Point(3600.0, 870.0), Point(3860.0, 870.0), Point(3860.0, 220.0), Point(4875.0, 220.0), Point(4875.0, 1210.0), Point(5135.0, 1210.0), Point(5135.0, 220.0), Point(5280.0, 220.0), Point(5280.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3630.0, 2080.0), Point(3630.0, 3560.0), Point(1235.0, 3560.0), Point(1235.0, 2780.0), Point(975.0, 2780.0), Point(975.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(5280.0, 4000.0), Point(5280.0, 3560.0), Point(5105.0, 3560.0), Point(5105.0, 2080.0), Point(4905.0, 2080.0), Point(4905.0, 3560.0), Point(3830.0, 3560.0), Point(3830.0, 2080.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4315.0, 610.0), Point(4315.0, 1210.0), Point(4515.0, 1210.0), Point(4515.0, 2040.0), Point(4135.0, 2040.0), Point(4135.0, 3200.0), Point(4685.0, 3200.0), Point(4685.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(310.0, 920.0), Point(310.0, 2880.0), Point(575.0, 2880.0), Point(575.0, 2600.0), Point(1480.0, 2600.0), Point(1480.0, 3295.0), Point(3450.0, 3295.0), Point(3450.0, 1870.0), Point(3720.0, 1870.0), Point(3720.0, 1540.0), Point(3290.0, 1540.0), Point(3290.0, 3125.0), Point(1640.0, 3125.0), Point(1640.0, 2440.0), Point(575.0, 2440.0), Point(575.0, 2280.0), Point(470.0, 2280.0), Point(470.0, 1180.0), Point(575.0, 1180.0), Point(575.0, 920.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1710.0, 1030.0), Point(1710.0, 1470.0), Point(1630.0, 1470.0), Point(1630.0, 1730.0), Point(1890.0, 1730.0), Point(1890.0, 1200.0), Point(2715.0, 1200.0), Point(2715.0, 1785.0), Point(3015.0, 1785.0), Point(3015.0, 1030.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1290.0, 610.0), Point(1290.0, 2260.0), Point(1825.0, 2260.0), Point(1825.0, 2505.0), Point(2300.0, 2505.0), Point(2300.0, 2945.0), Point(2560.0, 2945.0), Point(2560.0, 2345.0), Point(1985.0, 2345.0), Point(1985.0, 2100.0), Point(1450.0, 2100.0), Point(1450.0, 830.0), Point(3195.0, 830.0), Point(3195.0, 1260.0), Point(3945.0, 1260.0), Point(3945.0, 1850.0), Point(4245.0, 1850.0), Point(4245.0, 1520.0), Point(4135.0, 1520.0), Point(4135.0, 1100.0), Point(3365.0, 1100.0), Point(3365.0, 610.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2175.0, 1400.0, 2535.0, 1875.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(650.0, 1500.0, 1110.0, 1905.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(650.0, 1500.0, 1110.0, 1905.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2715.0, 1030.0, 3015.0, 1785.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(4135.0, 2040.0, 4685.0, 3200.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2175.0, 1400.0, 2535.0, 1875.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 5280.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 5280.0, 220.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A1', Point(2850.0, 1425.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(4405.0, 2600.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'S', Point(850.0, 1705.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1635.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(2710.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A0', Point(2400.0, 1680.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 5520.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 5350.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 5350.0, 3600.0)))

    # Ports
    cell.add_port(Port('A1', 'A1', tech['Metal1'], Rect.from_lbrt(2850.0, 1425.0, 2850.0, 1425.0)))
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(4405.0, 2600.0, 4405.0, 2600.0)))
    cell.add_port(Port('S', 'S', tech['Metal1'], Rect.from_lbrt(850.0, 1705.0, 850.0, 1705.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1635.0, 3780.0, 1635.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(2710.0, 0.0, 2710.0, 0.0), direction='GROUND'))
    cell.add_port(Port('A0', 'A0', tech['Metal1'], Rect.from_lbrt(2400.0, 1680.0, 2400.0, 1680.0)))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_mux2_2', sg13g2_tech)
    c.write_gds("sg13g2_mux2_2.gds")
