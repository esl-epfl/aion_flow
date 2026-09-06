# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_buf_8
# ================================================================

"""Generated AION cell for sg13g2_buf_8."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 6240.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 6240.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 6240.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 6240.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(135.0, 590.0, 6050.0, 1330.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(140.0, 2060.0, 6055.0, 3180.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3030.0, 1605.0, 3190.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 2950.0, 3430.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 2610.0, 3430.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 2270.0, 3430.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4290.0, 2950.0, 4450.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4290.0, 2610.0, 4450.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4290.0, 2270.0, 4450.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3780.0, 2950.0, 3940.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3780.0, 2610.0, 3940.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4800.0, 2950.0, 4960.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4800.0, 2610.0, 4960.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5310.0, 2950.0, 5470.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5310.0, 2610.0, 5470.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5310.0, 2270.0, 5470.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5820.0, 2950.0, 5980.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5820.0, 2610.0, 5980.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5820.0, 2270.0, 5980.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(210.0, 2610.0, 370.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(210.0, 2270.0, 370.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1230.0, 2950.0, 1390.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1230.0, 2610.0, 1390.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1230.0, 2270.0, 1390.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(720.0, 2950.0, 880.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(720.0, 2610.0, 880.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1740.0, 2950.0, 1900.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1740.0, 2610.0, 1900.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2250.0, 2950.0, 2410.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2250.0, 2610.0, 2410.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2250.0, 2270.0, 2410.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2760.0, 2950.0, 2920.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2760.0, 2610.0, 2920.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(210.0, 2950.0, 370.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1230.0, 1000.0, 1390.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1230.0, 660.0, 1390.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2250.0, 1000.0, 2410.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2250.0, 660.0, 2410.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(720.0, 660.0, 880.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1740.0, 660.0, 1900.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2760.0, 660.0, 2920.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1300.0, 1655.0, 1460.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(960.0, 1655.0, 1120.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(620.0, 1655.0, 780.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2690.0, 1605.0, 2850.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2350.0, 1605.0, 2510.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2010.0, 1605.0, 2170.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(210.0, 1000.0, 370.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(210.0, 660.0, 370.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3710.0, 1605.0, 3870.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3370.0, 1605.0, 3530.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3780.0, 660.0, 3940.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4800.0, 660.0, 4960.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5820.0, 1000.0, 5980.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5820.0, 660.0, 5980.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5310.0, 660.0, 5470.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4730.0, 1605.0, 4890.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4390.0, 1605.0, 4550.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4050.0, 1605.0, 4210.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 1000.0, 3430.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 660.0, 3430.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4290.0, 1000.0, 4450.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4290.0, 660.0, 4450.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5310.0, 1000.0, 5470.0, 1160.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2010.0, 410.0), Point(2010.0, 1490.0), Point(1925.0, 1490.0), Point(1925.0, 1850.0), Point(2010.0, 1850.0), Point(2010.0, 3360.0), Point(2140.0, 3360.0), Point(2140.0, 1850.0), Point(2520.0, 1850.0), Point(2520.0, 3360.0), Point(2650.0, 3360.0), Point(2650.0, 1850.0), Point(3030.0, 1850.0), Point(3030.0, 3360.0), Point(3160.0, 3360.0), Point(3160.0, 1850.0), Point(3540.0, 1850.0), Point(3540.0, 3360.0), Point(3670.0, 3360.0), Point(3670.0, 1850.0), Point(4050.0, 1850.0), Point(4050.0, 3360.0), Point(4180.0, 3360.0), Point(4180.0, 1850.0), Point(4560.0, 1850.0), Point(4560.0, 3360.0), Point(4690.0, 3360.0), Point(4690.0, 1850.0), Point(5070.0, 1850.0), Point(5070.0, 3360.0), Point(5200.0, 3360.0), Point(5200.0, 1850.0), Point(5580.0, 1850.0), Point(5580.0, 3360.0), Point(5710.0, 3360.0), Point(5710.0, 410.0), Point(5580.0, 410.0), Point(5580.0, 1520.0), Point(5200.0, 1520.0), Point(5200.0, 410.0), Point(5070.0, 410.0), Point(5070.0, 1520.0), Point(4690.0, 1520.0), Point(4690.0, 410.0), Point(4560.0, 410.0), Point(4560.0, 1520.0), Point(4180.0, 1520.0), Point(4180.0, 410.0), Point(4050.0, 410.0), Point(4050.0, 1520.0), Point(3670.0, 1520.0), Point(3670.0, 410.0), Point(3540.0, 410.0), Point(3540.0, 1520.0), Point(3160.0, 1520.0), Point(3160.0, 410.0), Point(3030.0, 410.0), Point(3030.0, 1520.0), Point(2650.0, 1520.0), Point(2650.0, 410.0), Point(2520.0, 410.0), Point(2520.0, 1520.0), Point(2140.0, 1520.0), Point(2140.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(480.0, 410.0), Point(480.0, 3360.0), Point(610.0, 3360.0), Point(610.0, 1900.0), Point(990.0, 1900.0), Point(990.0, 3360.0), Point(1120.0, 3360.0), Point(1120.0, 1900.0), Point(1500.0, 1900.0), Point(1500.0, 3360.0), Point(1630.0, 3360.0), Point(1630.0, 410.0), Point(1500.0, 410.0), Point(1500.0, 1570.0), Point(1120.0, 1570.0), Point(1120.0, 410.0), Point(990.0, 410.0), Point(990.0, 1570.0), Point(610.0, 1570.0), Point(610.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 6240.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5520.0, 1550.0, 5950.0, 1815.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(570.0, 1500.0, 1510.0, 1865.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 6240.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(160.0, 610.0), Point(160.0, 1210.0), Point(1770.0, 1210.0), Point(1770.0, 2220.0), Point(160.0, 2220.0), Point(160.0, 3160.0), Point(420.0, 3160.0), Point(420.0, 2380.0), Point(1180.0, 2380.0), Point(1180.0, 3160.0), Point(1440.0, 3160.0), Point(1440.0, 2380.0), Point(1940.0, 2380.0), Point(1940.0, 1815.0), Point(4975.0, 1815.0), Point(4975.0, 1555.0), Point(1940.0, 1555.0), Point(1940.0, 1050.0), Point(1440.0, 1050.0), Point(1440.0, 610.0), Point(1180.0, 610.0), Point(1180.0, 1050.0), Point(420.0, 1050.0), Point(420.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2200.0, 610.0), Point(2200.0, 1210.0), Point(5260.0, 1210.0), Point(5260.0, 2220.0), Point(2200.0, 2220.0), Point(2200.0, 3160.0), Point(2460.0, 3160.0), Point(2460.0, 2380.0), Point(3220.0, 2380.0), Point(3220.0, 3160.0), Point(3480.0, 3160.0), Point(3480.0, 2380.0), Point(4240.0, 2380.0), Point(4240.0, 3160.0), Point(4500.0, 3160.0), Point(4500.0, 2380.0), Point(5260.0, 2380.0), Point(5260.0, 3160.0), Point(5520.0, 3160.0), Point(5520.0, 1815.0), Point(5950.0, 1815.0), Point(5950.0, 1550.0), Point(5520.0, 1550.0), Point(5520.0, 610.0), Point(5260.0, 610.0), Point(5260.0, 1050.0), Point(4500.0, 1050.0), Point(4500.0, 610.0), Point(4240.0, 610.0), Point(4240.0, 1050.0), Point(3480.0, 1050.0), Point(3480.0, 610.0), Point(3220.0, 610.0), Point(3220.0, 1050.0), Point(2460.0, 1050.0), Point(2460.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5770.0, 2220.0), Point(5770.0, 3560.0), Point(5010.0, 3560.0), Point(5010.0, 2560.0), Point(4750.0, 2560.0), Point(4750.0, 3560.0), Point(3990.0, 3560.0), Point(3990.0, 2560.0), Point(3730.0, 2560.0), Point(3730.0, 3560.0), Point(2970.0, 3560.0), Point(2970.0, 2560.0), Point(2710.0, 2560.0), Point(2710.0, 3560.0), Point(1950.0, 3560.0), Point(1950.0, 2560.0), Point(1690.0, 2560.0), Point(1690.0, 3560.0), Point(930.0, 3560.0), Point(930.0, 2560.0), Point(670.0, 2560.0), Point(670.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(6240.0, 4000.0), Point(6240.0, 3560.0), Point(6030.0, 3560.0), Point(6030.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(670.0, 220.0), Point(670.0, 870.0), Point(930.0, 870.0), Point(930.0, 220.0), Point(1690.0, 220.0), Point(1690.0, 870.0), Point(1950.0, 870.0), Point(1950.0, 220.0), Point(2710.0, 220.0), Point(2710.0, 870.0), Point(2970.0, 870.0), Point(2970.0, 220.0), Point(3730.0, 220.0), Point(3730.0, 870.0), Point(3990.0, 870.0), Point(3990.0, 220.0), Point(4750.0, 220.0), Point(4750.0, 870.0), Point(5010.0, 870.0), Point(5010.0, 220.0), Point(5770.0, 220.0), Point(5770.0, 1210.0), Point(6030.0, 1210.0), Point(6030.0, 220.0), Point(6240.0, 220.0), Point(6240.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(570.0, 1500.0, 1510.0, 1865.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(5760.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(3330.0, 3775.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(960.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(3095.0, 5.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 6480.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-240.0, -180.0, 6480.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-160.0, 1760.0, 6400.0, 3600.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(5760.0, 1680.0, 5760.0, 1680.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(3330.0, 3775.0, 3330.0, 3775.0), direction='POWER'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(960.0, 1680.0, 960.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(3095.0, 5.0, 3095.0, 5.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_buf_8', sg13g2_tech)
    c.write_gds("sg13g2_buf_8.gds")
