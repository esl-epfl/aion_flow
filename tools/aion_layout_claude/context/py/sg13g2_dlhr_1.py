# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_dlhr_1
# ================================================================

"""Generated AION cell for sg13g2_dlhr_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 8640.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 8640.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(0.0, -150.0), Point(0.0, 150.0), Point(2625.0, 150.0), Point(2625.0, 620.0), Point(2050.0, 620.0), Point(2050.0, 1360.0), Point(2800.0, 1360.0), Point(2800.0, 1170.0), Point(4835.0, 1170.0), Point(4835.0, 750.0), Point(3750.0, 750.0), Point(3750.0, 530.0), Point(2925.0, 530.0), Point(2925.0, 150.0), Point(8640.0, 150.0), Point(8640.0, -150.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(5110.0, 2060.0), Point(5110.0, 2760.0), Point(3800.0, 2760.0), Point(3800.0, 2180.0), Point(2095.0, 2180.0), Point(2095.0, 3020.0), Point(2635.0, 3020.0), Point(2635.0, 3630.0), Point(1250.0, 3630.0), Point(1250.0, 2960.0), Point(1850.0, 2960.0), Point(1850.0, 2120.0), Point(375.0, 2120.0), Point(375.0, 2960.0), Point(950.0, 2960.0), Point(950.0, 3630.0), Point(0.0, 3630.0), Point(0.0, 3930.0), Point(8640.0, 3930.0), Point(8640.0, 3630.0), Point(2920.0, 3630.0), Point(2920.0, 3180.0), Point(6850.0, 3180.0), Point(6850.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(7650.0, 2060.0), Point(7650.0, 2340.0), Point(7070.0, 2340.0), Point(7070.0, 3180.0), Point(8390.0, 3180.0), Point(8390.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(7530.0, 450.0), Point(7530.0, 480.0), Point(6990.0, 480.0), Point(6990.0, 1030.0), Point(7530.0, 1030.0), Point(7530.0, 1220.0), Point(8340.0, 1220.0), Point(8340.0, 480.0), Point(7800.0, 480.0), Point(7800.0, 450.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(925.0, 650.0), Point(925.0, 840.0), Point(365.0, 840.0), Point(365.0, 1390.0), Point(1735.0, 1390.0), Point(1735.0, 650.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(5070.0, 500.0, 6730.0, 1240.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8320.0, -80.0, 8480.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8320.0, 3700.0, 8480.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8160.0, 2140.0, 8320.0, 2300.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8160.0, 2540.0, 8320.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8160.0, 2880.0, 8320.0, 3040.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8110.0, 550.0, 8270.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8110.0, 890.0, 8270.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7840.0, -80.0, 8000.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7840.0, 3700.0, 8000.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7805.0, 1535.0, 7965.0, 1695.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7650.0, 2490.0, 7810.0, 2650.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7650.0, 2940.0, 7810.0, 3100.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7600.0, 540.0, 7760.0, 700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7600.0, 890.0, 7760.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, -80.0, 7520.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, 3700.0, 7520.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7140.0, 2500.0, 7300.0, 2660.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7140.0, 2855.0, 7300.0, 3015.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7060.0, 550.0, 7220.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, -80.0, 7040.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, 3700.0, 7040.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6620.0, 2515.0, 6780.0, 2675.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6620.0, 2950.0, 6780.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6500.0, 590.0, 6660.0, 750.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6500.0, 990.0, 6660.0, 1150.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, -80.0, 6560.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, 3700.0, 6560.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6375.0, 1565.0, 6535.0, 1725.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6110.0, 2610.0, 6270.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6110.0, 2950.0, 6270.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5990.0, 570.0, 6150.0, 730.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5990.0, 910.0, 6150.0, 1070.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5835.0, 1435.0, 5995.0, 1595.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5600.0, 2200.0, 5760.0, 2360.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5600.0, 2540.0, 5760.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5600.0, 2880.0, 5760.0, 3040.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5140.0, 595.0, 5300.0, 755.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5140.0, 970.0, 5300.0, 1130.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5090.0, 2950.0, 5250.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4910.0, 1565.0, 5070.0, 1725.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4750.0, 2950.0, 4910.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4605.0, 880.0, 4765.0, 1040.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4595.0, 2205.0, 4755.0, 2365.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4055.0, 2265.0, 4215.0, 2425.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3945.0, 450.0, 4105.0, 610.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3675.0, 890.0, 3835.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3570.0, 2650.0, 3730.0, 2810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3435.0, 1365.0, 3595.0, 1525.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2875.0, 1685.0, 3035.0, 1845.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2705.0, 2970.0, 2865.0, 3130.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2695.0, 375.0, 2855.0, 535.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2165.0, 2250.0, 2325.0, 2410.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2155.0, 1125.0, 2315.0, 1285.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1915.0, 1635.0, 2075.0, 1795.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1590.0, 2190.0, 1750.0, 2350.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1505.0, 720.0, 1665.0, 880.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1505.0, 1060.0, 1665.0, 1220.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1345.0, 1665.0, 1505.0, 1825.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1020.0, 2970.0, 1180.0, 3130.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(995.0, 720.0, 1155.0, 880.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(995.0, 1060.0, 1155.0, 1220.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(820.0, 1665.0, 980.0, 1825.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(445.0, 2385.0, 605.0, 2545.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(445.0, 2730.0, 605.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(435.0, 1035.0, 595.0, 1195.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(7870.0, 290.0), Point(7870.0, 1450.0), Point(7720.0, 1450.0), Point(7720.0, 1780.0), Point(7920.0, 1780.0), Point(7920.0, 3360.0), Point(8050.0, 3360.0), Point(8050.0, 1450.0), Point(8000.0, 1450.0), Point(8000.0, 290.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(7330.0, 290.0), Point(7330.0, 1480.0), Point(6390.0, 1480.0), Point(6390.0, 320.0), Point(6260.0, 320.0), Point(6260.0, 1810.0), Point(6380.0, 1810.0), Point(6380.0, 3360.0), Point(6510.0, 3360.0), Point(6510.0, 1810.0), Point(6620.0, 1810.0), Point(6620.0, 1630.0), Point(7330.0, 1630.0), Point(7330.0, 2170.0), Point(7410.0, 2170.0), Point(7410.0, 3360.0), Point(7540.0, 3360.0), Point(7540.0, 2020.0), Point(7460.0, 2020.0), Point(7460.0, 290.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(5750.0, 320.0), Point(5750.0, 1680.0), Point(5870.0, 1680.0), Point(5870.0, 3360.0), Point(6000.0, 3360.0), Point(6000.0, 1680.0), Point(6080.0, 1680.0), Point(6080.0, 1350.0), Point(5880.0, 1350.0), Point(5880.0, 320.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(5410.0, 320.0), Point(5410.0, 1480.0), Point(4840.0, 1480.0), Point(4840.0, 1810.0), Point(5360.0, 1810.0), Point(5360.0, 3360.0), Point(5490.0, 3360.0), Point(5490.0, 1810.0), Point(5540.0, 1810.0), Point(5540.0, 320.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4365.0, 570.0), Point(4365.0, 1395.0), Point(4510.0, 1395.0), Point(4510.0, 3360.0), Point(4640.0, 3360.0), Point(4640.0, 2450.0), Point(4840.0, 2450.0), Point(4840.0, 2120.0), Point(4660.0, 2120.0), Point(4660.0, 1245.0), Point(4495.0, 1245.0), Point(4495.0, 570.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3885.0, 2180.0), Point(3885.0, 2510.0), Point(3900.0, 2510.0), Point(3900.0, 3360.0), Point(4030.0, 3360.0), Point(4030.0, 2510.0), Point(4300.0, 2510.0), Point(4300.0, 2180.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3860.0, 380.0), Point(3860.0, 680.0), Point(4010.0, 680.0), Point(4010.0, 1820.0), Point(3330.0, 1820.0), Point(3330.0, 3360.0), Point(3460.0, 3360.0), Point(3460.0, 1970.0), Point(4140.0, 1970.0), Point(4140.0, 680.0), Point(4175.0, 680.0), Point(4175.0, 380.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3350.0, 350.0), Point(3350.0, 1610.0), Point(3680.0, 1610.0), Point(3680.0, 1280.0), Point(3480.0, 1280.0), Point(3480.0, 350.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2995.0, 350.0), Point(2995.0, 1245.0), Point(2970.0, 1245.0), Point(2970.0, 1600.0), Point(2790.0, 1600.0), Point(2790.0, 1930.0), Point(2990.0, 1930.0), Point(2990.0, 3360.0), Point(3120.0, 3360.0), Point(3120.0, 1395.0), Point(3125.0, 1395.0), Point(3125.0, 350.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2425.0, 440.0), Point(2425.0, 1550.0), Point(1830.0, 1550.0), Point(1830.0, 1880.0), Point(2160.0, 1880.0), Point(2160.0, 1700.0), Point(2400.0, 1700.0), Point(2400.0, 2015.0), Point(2435.0, 2015.0), Point(2435.0, 3200.0), Point(2565.0, 3200.0), Point(2565.0, 1550.0), Point(2555.0, 1550.0), Point(2555.0, 440.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1265.0, 470.0), Point(1265.0, 1580.0), Point(1260.0, 1580.0), Point(1260.0, 1910.0), Point(1335.0, 1910.0), Point(1335.0, 3140.0), Point(1465.0, 3140.0), Point(1465.0, 1910.0), Point(1590.0, 1910.0), Point(1590.0, 1580.0), Point(1395.0, 1580.0), Point(1395.0, 470.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(705.0, 660.0), Point(705.0, 2045.0), Point(715.0, 2045.0), Point(715.0, 3140.0), Point(845.0, 3140.0), Point(845.0, 1910.0), Point(1050.0, 1910.0), Point(1050.0, 1580.0), Point(835.0, 1580.0), Point(835.0, 660.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5630.0, 1325.0, 6050.0, 1875.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1290.0, 1450.0, 1590.0, 1910.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 8640.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6530.0, 2395.0, 6945.0, 3175.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(8000.0, 1970.0, 8390.0, 3090.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(765.0, 1450.0, 1110.0, 1910.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 8640.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(910.0, 220.0), Point(910.0, 1250.0), Point(1240.0, 1250.0), Point(1240.0, 220.0), Point(2645.0, 220.0), Point(2645.0, 540.0), Point(2905.0, 540.0), Point(2905.0, 220.0), Point(4545.0, 220.0), Point(4545.0, 1115.0), Point(4830.0, 1115.0), Point(4830.0, 220.0), Point(5905.0, 220.0), Point(5905.0, 1140.0), Point(6235.0, 1140.0), Point(6235.0, 220.0), Point(7550.0, 220.0), Point(7550.0, 1120.0), Point(7810.0, 1120.0), Point(7810.0, 220.0), Point(8640.0, 220.0), Point(8640.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(7635.0, 2310.0), Point(7635.0, 3560.0), Point(6285.0, 3560.0), Point(6285.0, 2460.0), Point(6095.0, 2460.0), Point(6095.0, 3560.0), Point(5300.0, 3560.0), Point(5300.0, 2835.0), Point(4700.0, 2835.0), Point(4700.0, 3560.0), Point(2930.0, 3560.0), Point(2930.0, 2935.0), Point(2650.0, 2935.0), Point(2650.0, 3560.0), Point(1230.0, 3560.0), Point(1230.0, 2935.0), Point(970.0, 2935.0), Point(970.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(8640.0, 4000.0), Point(8640.0, 3560.0), Point(7820.0, 3560.0), Point(7820.0, 2310.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(8020.0, 470.0), Point(8020.0, 1085.0), Point(8215.0, 1085.0), Point(8215.0, 1970.0), Point(8000.0, 1970.0), Point(8000.0, 3090.0), Point(8390.0, 3090.0), Point(8390.0, 470.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(7000.0, 490.0), Point(7000.0, 775.0), Point(7125.0, 775.0), Point(7125.0, 3090.0), Point(7315.0, 3090.0), Point(7315.0, 1760.0), Point(8000.0, 1760.0), Point(8000.0, 1475.0), Point(7305.0, 1475.0), Point(7305.0, 490.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(6435.0, 510.0), Point(6435.0, 1240.0), Point(6785.0, 1240.0), Point(6785.0, 2395.0), Point(6530.0, 2395.0), Point(6530.0, 3175.0), Point(6945.0, 3175.0), Point(6945.0, 1010.0), Point(6720.0, 1010.0), Point(6720.0, 510.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5085.0, 510.0), Point(5085.0, 1230.0), Point(5290.0, 1230.0), Point(5290.0, 2120.0), Point(4510.0, 2120.0), Point(4510.0, 2450.0), Point(5575.0, 2450.0), Point(5575.0, 3090.0), Point(5780.0, 3090.0), Point(5780.0, 2215.0), Point(6605.0, 2215.0), Point(6605.0, 1480.0), Point(6290.0, 1480.0), Point(6290.0, 2055.0), Point(5450.0, 2055.0), Point(5450.0, 510.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3590.0, 840.0), Point(3590.0, 1090.0), Point(3865.0, 1090.0), Point(3865.0, 1770.0), Point(3640.0, 1770.0), Point(3640.0, 2535.0), Point(3495.0, 2535.0), Point(3495.0, 2855.0), Point(3800.0, 2855.0), Point(3800.0, 1935.0), Point(5110.0, 1935.0), Point(5110.0, 1480.0), Point(4840.0, 1480.0), Point(4840.0, 1760.0), Point(4035.0, 1760.0), Point(4035.0, 840.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2110.0, 1075.0), Point(2110.0, 1350.0), Point(2330.0, 1350.0), Point(2330.0, 2125.0), Point(2110.0, 2125.0), Point(2110.0, 2415.0), Point(2500.0, 2415.0), Point(2500.0, 1435.0), Point(3300.0, 1435.0), Point(3300.0, 2105.0), Point(3140.0, 2105.0), Point(3140.0, 3205.0), Point(4300.0, 3205.0), Point(4300.0, 2180.0), Point(3990.0, 2180.0), Point(3990.0, 3035.0), Point(3310.0, 3035.0), Point(3310.0, 2270.0), Point(3460.0, 2270.0), Point(3460.0, 1590.0), Point(3680.0, 1590.0), Point(3680.0, 1270.0), Point(2500.0, 1270.0), Point(2500.0, 1075.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3105.0, 440.0), Point(3105.0, 720.0), Point(1930.0, 720.0), Point(1930.0, 660.0), Point(1455.0, 660.0), Point(1455.0, 1250.0), Point(1770.0, 1250.0), Point(1770.0, 2165.0), Point(1520.0, 2165.0), Point(1520.0, 2355.0), Point(1930.0, 2355.0), Point(1930.0, 1880.0), Point(2145.0, 1880.0), Point(2145.0, 1550.0), Point(1930.0, 1550.0), Point(1930.0, 890.0), Point(3275.0, 890.0), Point(3275.0, 630.0), Point(4190.0, 630.0), Point(4190.0, 440.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(380.0, 960.0), Point(380.0, 2945.0), Point(665.0, 2945.0), Point(665.0, 2755.0), Point(2960.0, 2755.0), Point(2960.0, 1920.0), Point(3120.0, 1920.0), Point(3120.0, 1620.0), Point(2790.0, 1620.0), Point(2790.0, 2595.0), Point(665.0, 2595.0), Point(665.0, 2300.0), Point(540.0, 2300.0), Point(540.0, 1270.0), Point(665.0, 1270.0), Point(665.0, 960.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5630.0, 1325.0, 6050.0, 1875.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1290.0, 1450.0, 1590.0, 1910.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(765.0, 1450.0, 1110.0, 1910.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Q_N', Point(8215.0, 2550.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'RESET_B', Point(5855.0, 1610.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'GATE', Point(1440.0, 1690.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(4510.0, 3775.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Q', Point(6760.0, 2790.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(4715.0, 10.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(940.0, 1675.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 8880.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-80.0, 1760.0, 8710.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-80.0, -180.0, 8710.0, 180.0)))

    # Ports
    cell.add_port(Port('Q_N', 'Q_N', tech['Metal1'], Rect.from_lbrt(8215.0, 2550.0, 8215.0, 2550.0)))
    cell.add_port(Port('RESET_B', 'RESET_B', tech['Metal1'], Rect.from_lbrt(5855.0, 1610.0, 5855.0, 1610.0)))
    cell.add_port(Port('GATE', 'GATE', tech['Metal1'], Rect.from_lbrt(1440.0, 1690.0, 1440.0, 1690.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(4510.0, 3775.0, 4510.0, 3775.0), direction='POWER'))
    cell.add_port(Port('Q', 'Q', tech['Metal1'], Rect.from_lbrt(6760.0, 2790.0, 6760.0, 2790.0), direction='OUTPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(4715.0, 10.0, 4715.0, 10.0), direction='GROUND'))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(940.0, 1675.0, 940.0, 1675.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_dlhr_1', sg13g2_tech)
    c.write_gds("sg13g2_dlhr_1.gds")
