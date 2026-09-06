# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_dllrq_1
# ================================================================

"""Generated AION cell for sg13g2_dllrq_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 7680.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 7680.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(0.0, -150.0), Point(0.0, 150.0), Point(940.0, 150.0), Point(940.0, 850.0), Point(400.0, 850.0), Point(400.0, 1400.0), Point(1780.0, 1400.0), Point(1780.0, 660.0), Point(1240.0, 660.0), Point(1240.0, 150.0), Point(2675.0, 150.0), Point(2675.0, 520.0), Point(2130.0, 520.0), Point(2130.0, 1260.0), Point(2850.0, 1260.0), Point(2850.0, 1120.0), Point(4345.0, 1120.0), Point(4345.0, 900.0), Point(5290.0, 900.0), Point(5290.0, 480.0), Point(3480.0, 480.0), Point(3480.0, 150.0), Point(7680.0, 150.0), Point(7680.0, -150.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(5450.0, 2060.0), Point(5450.0, 2650.0), Point(3870.0, 2650.0), Point(3870.0, 2070.0), Point(2040.0, 2070.0), Point(2040.0, 2910.0), Point(2695.0, 2910.0), Point(2695.0, 3630.0), Point(0.0, 3630.0), Point(0.0, 3930.0), Point(7680.0, 3930.0), Point(7680.0, 3630.0), Point(2995.0, 3630.0), Point(2995.0, 3070.0), Point(5215.0, 3070.0), Point(5215.0, 3060.0), Point(6425.0, 3060.0), Point(6425.0, 3180.0), Point(7395.0, 3180.0), Point(7395.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(460.0, 2080.0, 1780.0, 2920.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(5525.0, 480.0, 7340.0, 1220.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(530.0, 2675.0, 690.0, 2835.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(470.0, 1045.0, 630.0, 1205.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2920.0, 1455.0, 3080.0, 1615.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2765.0, 3040.0, 2925.0, 3200.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3615.0, 2295.0, 3775.0, 2455.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5060.0, 550.0, 5220.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5025.0, 2750.0, 5185.0, 2910.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5595.0, 550.0, 5755.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, 3700.0, 6560.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6290.0, 1415.0, 6450.0, 1575.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6835.0, 1515.0, 6995.0, 1675.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6525.0, 550.0, 6685.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7140.0, 2145.0, 7300.0, 2305.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7140.0, 2540.0, 7300.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1550.0, 2170.0, 1710.0, 2330.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, 3700.0, 7040.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5350.0, 1495.0, 5510.0, 1655.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, -80.0, 6560.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1390.0, 1645.0, 1550.0, 1805.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4870.0, 2225.0, 5030.0, 2385.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2200.0, 1030.0, 2360.0, 1190.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, 3700.0, 7520.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, -80.0, 7520.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1010.0, 320.0, 1170.0, 480.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(820.0, 1645.0, 980.0, 1805.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2225.0, 2175.0, 2385.0, 2335.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(530.0, 2170.0, 690.0, 2330.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6495.0, 2950.0, 6655.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7110.0, 990.0, 7270.0, 1150.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1550.0, 2675.0, 1710.0, 2835.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, -80.0, 7040.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3250.0, 320.0, 3410.0, 480.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4185.0, 610.0, 4345.0, 770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1550.0, 1125.0, 1710.0, 1285.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4390.0, 1385.0, 4550.0, 1545.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3460.0, 1640.0, 3620.0, 1800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2745.0, 320.0, 2905.0, 480.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1960.0, 1535.0, 2120.0, 1695.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1040.0, 2170.0, 1200.0, 2330.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1040.0, 2675.0, 1200.0, 2835.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7140.0, 2935.0, 7300.0, 3095.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7110.0, 550.0, 7270.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6525.0, 930.0, 6685.0, 1090.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6495.0, 2610.0, 6655.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5955.0, 2480.0, 6115.0, 2640.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5955.0, 2830.0, 6115.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5595.0, 990.0, 5755.0, 1150.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5445.0, 2750.0, 5605.0, 2910.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4300.0, 2225.0, 4460.0, 2385.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(740.0, 670.0), Point(740.0, 1560.0), Point(720.0, 1560.0), Point(720.0, 1890.0), Point(800.0, 1890.0), Point(800.0, 3100.0), Point(930.0, 3100.0), Point(930.0, 1890.0), Point(1065.0, 1890.0), Point(1065.0, 1560.0), Point(870.0, 1560.0), Point(870.0, 670.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1310.0, 480.0), Point(1310.0, 1560.0), Point(1305.0, 1560.0), Point(1305.0, 1890.0), Point(1310.0, 1890.0), Point(1310.0, 3100.0), Point(1440.0, 3100.0), Point(1440.0, 1890.0), Point(1635.0, 1890.0), Point(1635.0, 1560.0), Point(1440.0, 1560.0), Point(1440.0, 480.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2470.0, 340.0), Point(2470.0, 1450.0), Point(1875.0, 1450.0), Point(1875.0, 1780.0), Point(2495.0, 1780.0), Point(2495.0, 3090.0), Point(2625.0, 3090.0), Point(2625.0, 1700.0), Point(2600.0, 1700.0), Point(2600.0, 340.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3375.0, 1555.0), Point(3375.0, 3250.0), Point(3505.0, 3250.0), Point(3505.0, 1885.0), Point(3705.0, 1885.0), Point(3705.0, 1555.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3555.0, 300.0), Point(3555.0, 1195.0), Point(3015.0, 1195.0), Point(3015.0, 1370.0), Point(2835.0, 1370.0), Point(2835.0, 1700.0), Point(3065.0, 1700.0), Point(3065.0, 3250.0), Point(3195.0, 3250.0), Point(3195.0, 1345.0), Point(3685.0, 1345.0), Point(3685.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3945.0, 300.0), Point(3945.0, 1990.0), Point(4100.0, 1990.0), Point(4100.0, 3250.0), Point(4230.0, 3250.0), Point(4230.0, 2470.0), Point(4545.0, 2470.0), Point(4545.0, 2140.0), Point(4250.0, 2140.0), Point(4250.0, 1840.0), Point(4075.0, 1840.0), Point(4075.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4455.0, 300.0), Point(4455.0, 1300.0), Point(4305.0, 1300.0), Point(4305.0, 1630.0), Point(4635.0, 1630.0), Point(4635.0, 1300.0), Point(4585.0, 1300.0), Point(4585.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4820.0, 300.0), Point(4820.0, 1600.0), Point(4875.0, 1600.0), Point(4875.0, 2140.0), Point(4785.0, 2140.0), Point(4785.0, 3250.0), Point(4915.0, 3250.0), Point(4915.0, 2470.0), Point(5115.0, 2470.0), Point(5115.0, 2140.0), Point(5025.0, 2140.0), Point(5025.0, 1450.0), Point(4950.0, 1450.0), Point(4950.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(5865.0, 300.0), Point(5865.0, 1295.0), Point(5265.0, 1295.0), Point(5265.0, 1835.0), Point(5715.0, 1835.0), Point(5715.0, 3240.0), Point(5845.0, 3240.0), Point(5845.0, 1685.0), Point(5595.0, 1685.0), Point(5595.0, 1445.0), Point(5995.0, 1445.0), Point(5995.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(6235.0, 300.0), Point(6235.0, 1330.0), Point(6205.0, 1330.0), Point(6205.0, 1660.0), Point(6225.0, 1660.0), Point(6225.0, 3240.0), Point(6355.0, 3240.0), Point(6355.0, 1660.0), Point(6535.0, 1660.0), Point(6535.0, 1330.0), Point(6365.0, 1330.0), Point(6365.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(6825.0, 300.0), Point(6825.0, 1430.0), Point(6765.0, 1430.0), Point(6765.0, 3360.0), Point(6895.0, 3360.0), Point(6895.0, 1875.0), Point(7085.0, 1875.0), Point(7085.0, 1430.0), Point(6955.0, 1430.0), Point(6955.0, 300.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 7680.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 7680.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(7085.0, 2085.0, 7415.0, 3155.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6130.0, 1290.0, 6535.0, 1915.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(750.0, 1560.0, 1115.0, 1960.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1305.0, 1560.0, 1620.0, 1960.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(395.0, 670.0), Point(395.0, 2855.0), Point(750.0, 2855.0), Point(750.0, 2140.0), Point(565.0, 2140.0), Point(565.0, 1360.0), Point(745.0, 1360.0), Point(745.0, 835.0), Point(2835.0, 835.0), Point(2835.0, 1700.0), Point(3165.0, 1700.0), Point(3165.0, 670.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1495.0, 1070.0), Point(1495.0, 1335.0), Point(1805.0, 1335.0), Point(1805.0, 2140.0), Point(1490.0, 2140.0), Point(1490.0, 2855.0), Point(1975.0, 2855.0), Point(1975.0, 2840.0), Point(4545.0, 2840.0), Point(4545.0, 2140.0), Point(4215.0, 2140.0), Point(4215.0, 2680.0), Point(1965.0, 2680.0), Point(1965.0, 1780.0), Point(2205.0, 1780.0), Point(2205.0, 1460.0), Point(1965.0, 1460.0), Point(1965.0, 1070.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(7065.0, 500.0), Point(7065.0, 1200.0), Point(7255.0, 1200.0), Point(7255.0, 2085.0), Point(7085.0, 2085.0), Point(7085.0, 3155.0), Point(7415.0, 3155.0), Point(7415.0, 500.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4135.0, 560.0), Point(4135.0, 1075.0), Point(5185.0, 1075.0), Point(5185.0, 1800.0), Point(3875.0, 1800.0), Point(3875.0, 2290.0), Point(3555.0, 2290.0), Point(3555.0, 2460.0), Point(4035.0, 2460.0), Point(4035.0, 1960.0), Point(5370.0, 1960.0), Point(5370.0, 1740.0), Point(5595.0, 1740.0), Point(5595.0, 1410.0), Point(5355.0, 1410.0), Point(5355.0, 915.0), Point(4395.0, 915.0), Point(4395.0, 560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2145.0, 1015.0), Point(2145.0, 1280.0), Point(2385.0, 1280.0), Point(2385.0, 2125.0), Point(2165.0, 2125.0), Point(2165.0, 2385.0), Point(2545.0, 2385.0), Point(2545.0, 2110.0), Point(3690.0, 2110.0), Point(3690.0, 1615.0), Point(4635.0, 1615.0), Point(4635.0, 1300.0), Point(3375.0, 1300.0), Point(3375.0, 1950.0), Point(2545.0, 1950.0), Point(2545.0, 1015.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(990.0, 2155.0), Point(990.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(7680.0, 4000.0), Point(7680.0, 3560.0), Point(6705.0, 3560.0), Point(6705.0, 2560.0), Point(6450.0, 2560.0), Point(6450.0, 3560.0), Point(5655.0, 3560.0), Point(5655.0, 2700.0), Point(4975.0, 2700.0), Point(4975.0, 3560.0), Point(2975.0, 3560.0), Point(2975.0, 3025.0), Point(2715.0, 3025.0), Point(2715.0, 3560.0), Point(1250.0, 3560.0), Point(1250.0, 2155.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5550.0, 495.0), Point(5550.0, 1200.0), Point(5780.0, 1200.0), Point(5780.0, 2140.0), Point(4785.0, 2140.0), Point(4785.0, 2470.0), Point(5905.0, 2470.0), Point(5905.0, 3030.0), Point(6165.0, 3030.0), Point(6165.0, 2375.0), Point(6885.0, 2375.0), Point(6885.0, 1760.0), Point(7075.0, 1760.0), Point(7075.0, 1430.0), Point(6715.0, 1430.0), Point(6715.0, 2215.0), Point(5950.0, 2215.0), Point(5950.0, 495.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(960.0, 220.0), Point(960.0, 490.0), Point(1220.0, 490.0), Point(1220.0, 220.0), Point(2695.0, 220.0), Point(2695.0, 490.0), Point(3460.0, 490.0), Point(3460.0, 220.0), Point(5010.0, 220.0), Point(5010.0, 725.0), Point(5270.0, 725.0), Point(5270.0, 220.0), Point(6475.0, 220.0), Point(6475.0, 1105.0), Point(6735.0, 1105.0), Point(6735.0, 220.0), Point(7680.0, 220.0), Point(7680.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6130.0, 1290.0, 6535.0, 1915.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1305.0, 1560.0, 1620.0, 1960.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(750.0, 1560.0, 1115.0, 1960.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'GATE_N', Point(1460.0, 1760.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(3675.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(3910.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Q', Point(7255.0, 2635.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'RESET_B', Point(6370.0, 1475.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(930.0, 1760.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 7920.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 7750.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 7750.0, 180.0)))

    # Ports
    cell.add_port(Port('GATE_N', 'GATE_N', tech['Metal1'], Rect.from_lbrt(1460.0, 1760.0, 1460.0, 1760.0)))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(3675.0, 0.0, 3675.0, 0.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(3910.0, 3780.0, 3910.0, 3780.0), direction='POWER'))
    cell.add_port(Port('Q', 'Q', tech['Metal1'], Rect.from_lbrt(7255.0, 2635.0, 7255.0, 2635.0), direction='OUTPUT'))
    cell.add_port(Port('RESET_B', 'RESET_B', tech['Metal1'], Rect.from_lbrt(6370.0, 1475.0, 6370.0, 1475.0)))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(930.0, 1760.0, 930.0, 1760.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_dllrq_1', sg13g2_tech)
    c.write_gds("sg13g2_dllrq_1.gds")
