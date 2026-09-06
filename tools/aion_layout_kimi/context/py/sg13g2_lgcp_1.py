# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_lgcp_1
# ================================================================

"""Generated AION cell for sg13g2_lgcp_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 7200.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 7200.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(330.0, 2090.0), Point(330.0, 3210.0), Point(1240.0, 3210.0), Point(1240.0, 3170.0), Point(3100.0, 3170.0), Point(3100.0, 3630.0), Point(0.0, 3630.0), Point(0.0, 3930.0), Point(7200.0, 3930.0), Point(7200.0, 3630.0), Point(3400.0, 3630.0), Point(3400.0, 3040.0), Point(3940.0, 3040.0), Point(3940.0, 2200.0), Point(3210.0, 2200.0), Point(3210.0, 2750.0), Point(2215.0, 2750.0), Point(2215.0, 2170.0), Point(1085.0, 2170.0), Point(1085.0, 2090.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(5965.0, 2060.0), Point(5965.0, 2175.0), Point(4190.0, 2175.0), Point(4190.0, 3015.0), Point(5965.0, 3015.0), Point(5965.0, 3180.0), Point(6780.0, 3180.0), Point(6780.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(4160.0, 790.0), Point(4160.0, 1530.0), Point(4940.0, 1530.0), Point(4940.0, 1430.0), Point(5835.0, 1430.0), Point(5835.0, 790.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(875.0, 520.0), Point(875.0, 580.0), Point(330.0, 580.0), Point(330.0, 1320.0), Point(1060.0, 1320.0), Point(1060.0, 1250.0), Point(3235.0, 1250.0), Point(3235.0, 1575.0), Point(3935.0, 1575.0), Point(3935.0, 835.0), Point(3265.0, 835.0), Point(3265.0, 830.0), Point(2215.0, 830.0), Point(2215.0, 610.0), Point(1175.0, 610.0), Point(1175.0, 520.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 7200.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(6070.0, 580.0, 6880.0, 1320.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, -80.0, 7040.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, 3700.0, 7040.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6650.0, 660.0, 6810.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6650.0, 1085.0, 6810.0, 1245.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6550.0, 2250.0, 6710.0, 2410.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6550.0, 2600.0, 6710.0, 2760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6550.0, 2950.0, 6710.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, -80.0, 6560.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, 3700.0, 6560.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6140.0, 655.0, 6300.0, 815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6140.0, 1085.0, 6300.0, 1245.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6040.0, 2250.0, 6200.0, 2410.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6040.0, 2600.0, 6200.0, 2760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6040.0, 2950.0, 6200.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6030.0, 1595.0, 6190.0, 1755.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5605.0, 860.0, 5765.0, 1020.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5605.0, 1200.0, 5765.0, 1360.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5280.0, 2445.0, 5440.0, 2605.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5280.0, 2785.0, 5440.0, 2945.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4905.0, 1770.0, 5065.0, 1930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4770.0, 2785.0, 4930.0, 2945.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4740.0, 860.0, 4900.0, 1020.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4740.0, 1210.0, 4900.0, 1370.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4260.0, 2445.0, 4420.0, 2605.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4260.0, 2785.0, 4420.0, 2945.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4230.0, 1300.0, 4390.0, 1460.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3710.0, 2270.0, 3870.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3705.0, 905.0, 3865.0, 1065.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3705.0, 1295.0, 3865.0, 1455.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3430.0, 1795.0, 3590.0, 1955.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3175.0, 905.0, 3335.0, 1065.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3170.0, 3125.0, 3330.0, 3285.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2950.0, 475.0, 3110.0, 635.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2530.0, 1805.0, 2690.0, 1965.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2460.0, 2345.0, 2620.0, 2505.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2150.0, 2845.0, 2310.0, 3005.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2140.0, 945.0, 2300.0, 1105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1990.0, 1445.0, 2150.0, 1605.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1330.0, 1765.0, 1490.0, 1925.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(945.0, 590.0, 1105.0, 750.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(940.0, 2940.0, 1100.0, 3100.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(760.0, 1595.0, 920.0, 1755.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(400.0, 650.0, 560.0, 810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(400.0, 1090.0, 560.0, 1250.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(400.0, 2260.0, 560.0, 2420.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(400.0, 2600.0, 560.0, 2760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(400.0, 2940.0, 560.0, 3100.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(6410.0, 400.0), Point(6410.0, 1510.0), Point(5945.0, 1510.0), Point(5945.0, 1840.0), Point(6310.0, 1840.0), Point(6310.0, 3360.0), Point(6440.0, 3360.0), Point(6440.0, 1840.0), Point(6475.0, 1840.0), Point(6475.0, 1660.0), Point(6540.0, 1660.0), Point(6540.0, 400.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2865.0, 295.0), Point(2865.0, 1475.0), Point(2985.0, 1475.0), Point(2985.0, 2290.0), Point(2900.0, 2290.0), Point(2900.0, 3350.0), Point(3030.0, 3350.0), Point(3030.0, 2440.0), Point(3135.0, 2440.0), Point(3135.0, 1325.0), Point(2995.0, 1325.0), Point(2995.0, 720.0), Point(3195.0, 720.0), Point(3195.0, 425.0), Point(5365.0, 425.0), Point(5365.0, 1700.0), Point(5550.0, 1700.0), Point(5550.0, 3195.0), Point(5680.0, 3195.0), Point(5680.0, 1550.0), Point(5495.0, 1550.0), Point(5495.0, 295.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4500.0, 610.0), Point(4500.0, 2090.0), Point(4530.0, 2090.0), Point(4530.0, 3195.0), Point(4660.0, 3195.0), Point(4660.0, 2090.0), Point(5040.0, 2090.0), Point(5040.0, 3195.0), Point(5170.0, 3195.0), Point(5170.0, 1940.0), Point(5140.0, 1940.0), Point(5140.0, 610.0), Point(5010.0, 610.0), Point(5010.0, 1685.0), Point(4630.0, 1685.0), Point(4630.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3465.0, 655.0), Point(3465.0, 1710.0), Point(3345.0, 1710.0), Point(3345.0, 2040.0), Point(3470.0, 2040.0), Point(3470.0, 3220.0), Point(3600.0, 3220.0), Point(3600.0, 2040.0), Point(3675.0, 2040.0), Point(3675.0, 1710.0), Point(3595.0, 1710.0), Point(3595.0, 655.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2475.0, 650.0), Point(2475.0, 1720.0), Point(2445.0, 1720.0), Point(2445.0, 1900.0), Point(1785.0, 1900.0), Point(1785.0, 2095.0), Point(1800.0, 2095.0), Point(1800.0, 3350.0), Point(1930.0, 3350.0), Point(1930.0, 2095.0), Point(1965.0, 2095.0), Point(1965.0, 2050.0), Point(2775.0, 2050.0), Point(2775.0, 1720.0), Point(2605.0, 1720.0), Point(2605.0, 650.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2375.0, 2260.0), Point(2375.0, 2590.0), Point(2495.0, 2590.0), Point(2495.0, 2675.0), Point(2510.0, 2675.0), Point(2510.0, 3350.0), Point(2640.0, 3350.0), Point(2640.0, 2675.0), Point(2675.0, 2675.0), Point(2675.0, 2590.0), Point(2705.0, 2590.0), Point(2705.0, 2260.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1815.0, 430.0), Point(1815.0, 1690.0), Point(2235.0, 1690.0), Point(2235.0, 1360.0), Point(1945.0, 1360.0), Point(1945.0, 430.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1445.0, 430.0), Point(1445.0, 1680.0), Point(1245.0, 1680.0), Point(1245.0, 2010.0), Point(1365.0, 2010.0), Point(1365.0, 2095.0), Point(1380.0, 2095.0), Point(1380.0, 3350.0), Point(1510.0, 3350.0), Point(1510.0, 2095.0), Point(1545.0, 2095.0), Point(1545.0, 2010.0), Point(1575.0, 2010.0), Point(1575.0, 430.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(670.0, 400.0), Point(670.0, 3390.0), Point(800.0, 3390.0), Point(800.0, 1840.0), Point(1005.0, 1840.0), Point(1005.0, 1510.0), Point(800.0, 1510.0), Point(800.0, 400.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1245.0, 1680.0, 1635.0, 2210.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 7200.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(4680.0, 1685.0, 4955.0, 2420.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6495.0, 1760.0, 6845.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 7200.0, 4000.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(900.0, 220.0), Point(900.0, 800.0), Point(1115.0, 800.0), Point(1115.0, 220.0), Point(3365.0, 220.0), Point(3365.0, 895.0), Point(2990.0, 895.0), Point(2990.0, 1125.0), Point(3525.0, 1125.0), Point(3525.0, 220.0), Point(4690.0, 220.0), Point(4690.0, 1445.0), Point(4950.0, 1445.0), Point(4950.0, 220.0), Point(6090.0, 220.0), Point(6090.0, 1260.0), Point(6350.0, 1260.0), Point(6350.0, 220.0), Point(7200.0, 220.0), Point(7200.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5990.0, 2200.0), Point(5990.0, 3560.0), Point(4980.0, 3560.0), Point(4980.0, 2730.0), Point(4720.0, 2730.0), Point(4720.0, 3560.0), Point(3380.0, 3560.0), Point(3380.0, 3095.0), Point(3115.0, 3095.0), Point(3115.0, 3560.0), Point(1150.0, 3560.0), Point(1150.0, 2890.0), Point(890.0, 2890.0), Point(890.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(7200.0, 4000.0), Point(7200.0, 3560.0), Point(6250.0, 3560.0), Point(6250.0, 2200.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(6590.0, 560.0), Point(6590.0, 1760.0), Point(6495.0, 1760.0), Point(6495.0, 3160.0), Point(6845.0, 3160.0), Point(6845.0, 560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5525.0, 815.0), Point(5525.0, 1410.0), Point(5585.0, 1410.0), Point(5585.0, 2195.0), Point(5230.0, 2195.0), Point(5230.0, 2995.0), Point(5490.0, 2995.0), Point(5490.0, 2355.0), Point(5765.0, 2355.0), Point(5765.0, 1840.0), Point(6275.0, 1840.0), Point(6275.0, 1510.0), Point(5855.0, 1510.0), Point(5855.0, 815.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4680.0, 1685.0), Point(4680.0, 2420.0), Point(4955.0, 2420.0), Point(4955.0, 2015.0), Point(5125.0, 2015.0), Point(5125.0, 1685.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4205.0, 1230.0), Point(4205.0, 2695.0), Point(3290.0, 2695.0), Point(3290.0, 2040.0), Point(3655.0, 2040.0), Point(3655.0, 1725.0), Point(3115.0, 1725.0), Point(3115.0, 2305.0), Point(2235.0, 2305.0), Point(2235.0, 1360.0), Point(1975.0, 1360.0), Point(1975.0, 2565.0), Point(3115.0, 2565.0), Point(3115.0, 2905.0), Point(4205.0, 2905.0), Point(4205.0, 2995.0), Point(4470.0, 2995.0), Point(4470.0, 2155.0), Point(4445.0, 2155.0), Point(4445.0, 1230.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3705.0, 845.0), Point(3705.0, 1370.0), Point(2445.0, 1370.0), Point(2445.0, 2050.0), Point(2775.0, 2050.0), Point(2775.0, 1540.0), Point(3845.0, 1540.0), Point(3845.0, 2260.0), Point(3650.0, 2260.0), Point(3650.0, 2450.0), Point(4015.0, 2450.0), Point(4015.0, 845.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1295.0, 465.0), Point(1295.0, 980.0), Point(595.0, 980.0), Point(595.0, 600.0), Point(350.0, 600.0), Point(350.0, 1050.0), Point(330.0, 1050.0), Point(330.0, 2480.0), Point(350.0, 2480.0), Point(350.0, 3150.0), Point(610.0, 3150.0), Point(610.0, 2125.0), Point(495.0, 2125.0), Point(495.0, 1300.0), Point(595.0, 1300.0), Point(595.0, 1160.0), Point(1455.0, 1160.0), Point(1455.0, 635.0), Point(2865.0, 635.0), Point(2865.0, 710.0), Point(3185.0, 710.0), Point(3185.0, 465.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1635.0, 890.0), Point(1635.0, 1340.0), Point(855.0, 1340.0), Point(855.0, 1510.0), Point(675.0, 1510.0), Point(675.0, 1840.0), Point(855.0, 1840.0), Point(855.0, 2580.0), Point(1625.0, 2580.0), Point(1625.0, 3055.0), Point(2350.0, 3055.0), Point(2350.0, 2795.0), Point(1785.0, 2795.0), Point(1785.0, 2420.0), Point(1025.0, 2420.0), Point(1025.0, 1500.0), Point(1795.0, 1500.0), Point(1795.0, 1140.0), Point(2395.0, 1140.0), Point(2395.0, 890.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1245.0, 1680.0, 1635.0, 2210.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'GCLK', Point(6650.0, 2655.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(3340.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'CLK', Point(4800.0, 2100.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(3680.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'GATE', Point(1440.0, 1940.0), purpose='label'))

    # NWell
    cell.add_shape(PolygonShape(tech['NWell'], [Point(-240.0, 1750.0), Point(-240.0, 4170.0), Point(7440.0, 4170.0), Point(7440.0, 1750.0), Point(5710.0, 1750.0), Point(5710.0, 1865.0), Point(4045.0, 1865.0), Point(4045.0, 1890.0), Point(2670.0, 1890.0), Point(2670.0, 1750.0)]))

    # PSD
    cell.add_shape(PolygonShape(tech['PSD'], [Point(-70.0, 1760.0), Point(-70.0, 3600.0), Point(7270.0, 3600.0), Point(7270.0, 1760.0), Point(5785.0, 1760.0), Point(5785.0, 1865.0), Point(4055.0, 1865.0), Point(4055.0, 1900.0), Point(2655.0, 1900.0), Point(2655.0, 1760.0)]))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 7270.0, 180.0)))

    # Ports
    cell.add_port(Port('GCLK', 'GCLK', tech['Metal1'], Rect.from_lbrt(6650.0, 2655.0, 6650.0, 2655.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(3340.0, 3780.0, 3340.0, 3780.0), direction='POWER'))
    cell.add_port(Port('CLK', 'CLK', tech['Metal1'], Rect.from_lbrt(4800.0, 2100.0, 4800.0, 2100.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(3680.0, 0.0, 3680.0, 0.0), direction='GROUND'))
    cell.add_port(Port('GATE', 'GATE', tech['Metal1'], Rect.from_lbrt(1440.0, 1940.0, 1440.0, 1940.0)))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_lgcp_1', sg13g2_tech)
    c.write_gds("sg13g2_lgcp_1.gds")
