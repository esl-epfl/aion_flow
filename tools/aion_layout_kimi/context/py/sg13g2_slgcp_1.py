# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_slgcp_1
# ================================================================

"""Generated AION cell for sg13g2_slgcp_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 8160.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 8160.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(0.0, -150.0), Point(0.0, 150.0), Point(1260.0, 150.0), Point(1260.0, 780.0), Point(210.0, 780.0), Point(210.0, 1330.0), Point(2100.0, 1330.0), Point(2100.0, 590.0), Point(1560.0, 590.0), Point(1560.0, 150.0), Point(8160.0, 150.0), Point(8160.0, -150.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(7005.0, 2060.0), Point(7005.0, 2235.0), Point(5325.0, 2235.0), Point(5325.0, 3075.0), Point(5865.0, 3075.0), Point(5865.0, 3630.0), Point(6165.0, 3630.0), Point(6165.0, 3075.0), Point(7005.0, 3075.0), Point(7005.0, 3180.0), Point(7725.0, 3180.0), Point(7725.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(5130.0, 590.0), Point(5130.0, 1330.0), Point(6765.0, 1330.0), Point(6765.0, 690.0), Point(5910.0, 690.0), Point(5910.0, 590.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(4345.0, 1980.0), Point(4345.0, 2680.0), Point(3680.0, 2680.0), Point(3680.0, 2115.0), Point(2860.0, 2115.0), Point(2860.0, 2955.0), Point(3450.0, 2955.0), Point(3450.0, 3100.0), Point(5070.0, 3100.0), Point(5070.0, 1980.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2320.0, 590.0), Point(2320.0, 1140.0), Point(3210.0, 1140.0), Point(3210.0, 1040.0), Point(4210.0, 1040.0), Point(4210.0, 1330.0), Point(4910.0, 1330.0), Point(4910.0, 590.0), Point(4210.0, 590.0), Point(4210.0, 620.0), Point(3210.0, 620.0), Point(3210.0, 590.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1800.0, 2060.0), Point(1800.0, 3180.0), Point(2100.0, 3180.0), Point(2100.0, 2900.0), Point(2640.0, 2900.0), Point(2640.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 8160.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(7030.0, 590.0, 7860.0, 1330.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(210.0, 2340.0, 1530.0, 3180.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7840.0, -80.0, 8000.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7840.0, 3700.0, 8000.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7630.0, 670.0, 7790.0, 830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7630.0, 1090.0, 7790.0, 1250.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7495.0, 2145.0, 7655.0, 2305.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7495.0, 2540.0, 7655.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7495.0, 2945.0, 7655.0, 3105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, -80.0, 7520.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, 3700.0, 7520.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7255.0, 1605.0, 7415.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7100.0, 670.0, 7260.0, 830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7100.0, 1010.0, 7260.0, 1170.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6985.0, 2360.0, 7145.0, 2520.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6985.0, 2845.0, 7145.0, 3005.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, -80.0, 7040.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, 3700.0, 7040.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6535.0, 760.0, 6695.0, 920.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6535.0, 1100.0, 6695.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6475.0, 2310.0, 6635.0, 2470.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6475.0, 2840.0, 6635.0, 3000.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, -80.0, 6560.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, 3700.0, 6560.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6380.0, 1525.0, 6540.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5710.0, 760.0, 5870.0, 920.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5710.0, 1100.0, 5870.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5670.0, 1660.0, 5830.0, 1820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5395.0, 2305.0, 5555.0, 2465.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5200.0, 660.0, 5360.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5200.0, 1100.0, 5360.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4840.0, 2050.0, 5000.0, 2210.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4840.0, 2460.0, 5000.0, 2620.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4840.0, 2870.0, 5000.0, 3030.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4680.0, 960.0, 4840.0, 1120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4330.0, 1525.0, 4490.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4330.0, 2810.0, 4490.0, 2970.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3990.0, 700.0, 4150.0, 860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3940.0, 2085.0, 4100.0, 2245.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3440.0, 2190.0, 3600.0, 2350.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3440.0, 2725.0, 3600.0, 2885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3130.0, 810.0, 3290.0, 970.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2950.0, 1690.0, 3110.0, 1850.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2930.0, 2190.0, 3090.0, 2350.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2930.0, 2725.0, 3090.0, 2885.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2425.0, 1335.0, 2585.0, 1495.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2410.0, 2140.0, 2570.0, 2300.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2390.0, 705.0, 2550.0, 865.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1870.0, 1100.0, 2030.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1870.0, 2950.0, 2030.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1330.0, 410.0, 1490.0, 570.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1300.0, 2610.0, 1460.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1300.0, 2950.0, 1460.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1145.0, 1935.0, 1305.0, 2095.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(790.0, 970.0, 950.0, 1130.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(405.0, 1935.0, 565.0, 2095.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(280.0, 2610.0, 440.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(280.0, 2950.0, 440.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(280.0, 970.0, 440.0, 1130.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(550.0, 600.0), Point(550.0, 1865.0), Point(335.0, 1865.0), Point(335.0, 2180.0), Point(550.0, 2180.0), Point(550.0, 3360.0), Point(680.0, 3360.0), Point(680.0, 600.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(7390.0, 410.0), Point(7390.0, 1405.0), Point(7170.0, 1405.0), Point(7170.0, 1945.0), Point(7255.0, 1945.0), Point(7255.0, 3360.0), Point(7385.0, 3360.0), Point(7385.0, 1945.0), Point(7520.0, 1945.0), Point(7520.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(6295.0, 510.0), Point(6295.0, 1770.0), Point(6745.0, 1770.0), Point(6745.0, 3255.0), Point(6875.0, 3255.0), Point(6875.0, 1440.0), Point(6425.0, 1440.0), Point(6425.0, 510.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(5470.0, 410.0), Point(5470.0, 1890.0), Point(5665.0, 1890.0), Point(5665.0, 3255.0), Point(5795.0, 3255.0), Point(5795.0, 2160.0), Point(6235.0, 2160.0), Point(6235.0, 3255.0), Point(6365.0, 3255.0), Point(6365.0, 2010.0), Point(6110.0, 2010.0), Point(6110.0, 510.0), Point(5980.0, 510.0), Point(5980.0, 1590.0), Point(5600.0, 1590.0), Point(5600.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4440.0, 410.0), Point(4440.0, 1440.0), Point(4245.0, 1440.0), Point(4245.0, 1770.0), Point(4595.0, 1770.0), Point(4595.0, 1905.0), Point(4600.0, 1905.0), Point(4600.0, 3280.0), Point(4730.0, 3280.0), Point(4730.0, 1905.0), Point(4775.0, 1905.0), Point(4775.0, 1440.0), Point(4570.0, 1440.0), Point(4570.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3750.0, 440.0), Point(3750.0, 2320.0), Point(4090.0, 2320.0), Point(4090.0, 3280.0), Point(4220.0, 3280.0), Point(4220.0, 2605.0), Point(4270.0, 2605.0), Point(4270.0, 2010.0), Point(3880.0, 2010.0), Point(3880.0, 440.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1630.0, 410.0), Point(1630.0, 1580.0), Point(2170.0, 1580.0), Point(2170.0, 3445.0), Point(3880.0, 3445.0), Point(3880.0, 2500.0), Point(3750.0, 2500.0), Point(3750.0, 3315.0), Point(2300.0, 3315.0), Point(2300.0, 1580.0), Point(2670.0, 1580.0), Point(2670.0, 1365.0), Point(2870.0, 1365.0), Point(2870.0, 410.0), Point(2740.0, 410.0), Point(2740.0, 1215.0), Point(2340.0, 1215.0), Point(2340.0, 1430.0), Point(1760.0, 1430.0), Point(1760.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3440.0, 440.0), Point(3440.0, 1620.0), Point(2880.0, 1620.0), Point(2880.0, 1920.0), Point(3200.0, 1920.0), Point(3200.0, 3135.0), Point(3330.0, 3135.0), Point(3330.0, 1920.0), Point(3570.0, 1920.0), Point(3570.0, 440.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1060.0, 600.0), Point(1060.0, 3360.0), Point(1190.0, 3360.0), Point(1190.0, 2180.0), Point(1390.0, 2180.0), Point(1390.0, 1865.0), Point(1190.0, 1865.0), Point(1190.0, 600.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(355.0, 1510.0, 615.0, 2145.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(820.0, 1960.0, 1525.0, 2240.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5585.0, 1560.0, 5890.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 8160.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 8160.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(7445.0, 2060.0, 7840.0, 3180.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(230.0, 220.0), Point(230.0, 1165.0), Point(490.0, 1165.0), Point(490.0, 220.0), Point(1280.0, 220.0), Point(1280.0, 575.0), Point(1540.0, 575.0), Point(1540.0, 220.0), Point(3990.0, 220.0), Point(3990.0, 910.0), Point(4150.0, 910.0), Point(4150.0, 220.0), Point(5660.0, 220.0), Point(5660.0, 1275.0), Point(5920.0, 1275.0), Point(5920.0, 220.0), Point(7090.0, 220.0), Point(7090.0, 1220.0), Point(7275.0, 1220.0), Point(7275.0, 220.0), Point(8160.0, 220.0), Point(8160.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(6935.0, 2335.0), Point(6935.0, 3560.0), Point(4540.0, 3560.0), Point(4540.0, 2785.0), Point(4280.0, 2785.0), Point(4280.0, 3560.0), Point(2080.0, 3560.0), Point(2080.0, 2940.0), Point(1820.0, 2940.0), Point(1820.0, 3560.0), Point(490.0, 3560.0), Point(490.0, 2540.0), Point(230.0, 2540.0), Point(230.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(8160.0, 4000.0), Point(8160.0, 3560.0), Point(7195.0, 3560.0), Point(7195.0, 2335.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4670.0, 910.0), Point(4670.0, 1170.0), Point(4760.0, 1170.0), Point(4760.0, 2045.0), Point(3890.0, 2045.0), Point(3890.0, 2305.0), Point(4790.0, 2305.0), Point(4790.0, 3065.0), Point(5050.0, 3065.0), Point(5050.0, 3025.0), Point(6165.0, 3025.0), Point(6165.0, 2655.0), Point(6255.0, 2655.0), Point(6255.0, 1760.0), Point(6560.0, 1760.0), Point(6560.0, 1460.0), Point(6085.0, 1460.0), Point(6085.0, 2450.0), Point(6005.0, 2450.0), Point(6005.0, 2865.0), Point(5050.0, 2865.0), Point(5050.0, 2000.0), Point(4935.0, 2000.0), Point(4935.0, 910.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(7580.0, 620.0), Point(7580.0, 1300.0), Point(7680.0, 1300.0), Point(7680.0, 2060.0), Point(7445.0, 2060.0), Point(7445.0, 3180.0), Point(7840.0, 3180.0), Point(7840.0, 620.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(6485.0, 710.0), Point(6485.0, 1270.0), Point(6740.0, 1270.0), Point(6740.0, 1940.0), Point(6455.0, 1940.0), Point(6455.0, 3075.0), Point(6650.0, 3075.0), Point(6650.0, 2110.0), Point(6900.0, 2110.0), Point(6900.0, 1850.0), Point(7500.0, 1850.0), Point(7500.0, 1520.0), Point(6910.0, 1520.0), Point(6910.0, 710.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2740.0, 450.0), Point(2740.0, 1250.0), Point(2400.0, 1250.0), Point(2400.0, 1545.0), Point(2645.0, 1545.0), Point(2645.0, 1420.0), Point(2900.0, 1420.0), Point(2900.0, 610.0), Point(3650.0, 610.0), Point(3650.0, 1265.0), Point(4490.0, 1265.0), Point(4490.0, 645.0), Point(5150.0, 645.0), Point(5150.0, 1310.0), Point(5245.0, 1310.0), Point(5245.0, 2515.0), Point(5560.0, 2515.0), Point(5560.0, 2255.0), Point(5405.0, 2255.0), Point(5405.0, 1310.0), Point(5435.0, 1310.0), Point(5435.0, 475.0), Point(4330.0, 475.0), Point(4330.0, 1105.0), Point(3810.0, 1105.0), Point(3810.0, 450.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3080.0, 790.0), Point(3080.0, 990.0), Point(3195.0, 990.0), Point(3195.0, 1470.0), Point(3305.0, 1470.0), Point(3305.0, 1935.0), Point(3390.0, 1935.0), Point(3390.0, 2935.0), Point(3650.0, 2935.0), Point(3650.0, 1720.0), Point(4575.0, 1720.0), Point(4575.0, 1500.0), Point(3470.0, 1500.0), Point(3470.0, 1315.0), Point(3370.0, 1315.0), Point(3370.0, 790.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2340.0, 655.0), Point(2340.0, 755.0), Point(740.0, 755.0), Point(740.0, 1180.0), Point(970.0, 1180.0), Point(970.0, 1680.0), Point(1710.0, 1680.0), Point(1710.0, 2560.0), Point(1250.0, 2560.0), Point(1250.0, 3140.0), Point(1510.0, 3140.0), Point(1510.0, 2760.0), Point(2880.0, 2760.0), Point(2880.0, 2935.0), Point(3140.0, 2935.0), Point(3140.0, 2175.0), Point(2880.0, 2175.0), Point(2880.0, 2595.0), Point(1870.0, 2595.0), Point(1870.0, 1520.0), Point(1140.0, 1520.0), Point(1140.0, 920.0), Point(2560.0, 920.0), Point(2560.0, 655.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1820.0, 1100.0), Point(1820.0, 1340.0), Point(2050.0, 1340.0), Point(2050.0, 1935.0), Point(2335.0, 1935.0), Point(2335.0, 2370.0), Point(2635.0, 2370.0), Point(2635.0, 1935.0), Point(3125.0, 1935.0), Point(3125.0, 1640.0), Point(2835.0, 1640.0), Point(2835.0, 1765.0), Point(2220.0, 1765.0), Point(2220.0, 1100.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1095.0, 1885.0), Point(1095.0, 1960.0), Point(820.0, 1960.0), Point(820.0, 2240.0), Point(1525.0, 2240.0), Point(1525.0, 1960.0), Point(1355.0, 1960.0), Point(1355.0, 1885.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5585.0, 1560.0, 5890.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(355.0, 1510.0, 615.0, 2145.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'GCLK', Point(7620.0, 2615.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'SCE', Point(580.0, 1845.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'GATE', Point(1290.0, 2115.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'CLK', Point(5735.0, 1785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(4085.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(4080.0, 3780.0), purpose='label'))

    # NWell
    cell.add_shape(PolygonShape(tech['NWell'], [Point(4135.0, 1670.0), Point(4135.0, 1750.0), Point(-300.0, 1750.0), Point(-300.0, 4170.0), Point(8460.0, 4170.0), Point(8460.0, 1750.0), Point(5565.0, 1750.0), Point(5565.0, 1670.0)]))

    # PSD
    cell.add_shape(PolygonShape(tech['PSD'], [Point(4145.0, 1680.0), Point(4145.0, 1760.0), Point(-160.0, 1760.0), Point(-160.0, 3600.0), Point(8320.0, 3600.0), Point(8320.0, 1760.0), Point(5555.0, 1760.0), Point(5555.0, 1680.0)]))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-300.0, -180.0, 8460.0, 180.0)))

    # Ports
    cell.add_port(Port('GCLK', 'GCLK', tech['Metal1'], Rect.from_lbrt(7620.0, 2615.0, 7620.0, 2615.0)))
    cell.add_port(Port('SCE', 'SCE', tech['Metal1'], Rect.from_lbrt(580.0, 1845.0, 580.0, 1845.0)))
    cell.add_port(Port('GATE', 'GATE', tech['Metal1'], Rect.from_lbrt(1290.0, 2115.0, 1290.0, 2115.0)))
    cell.add_port(Port('CLK', 'CLK', tech['Metal1'], Rect.from_lbrt(5735.0, 1785.0, 5735.0, 1785.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(4085.0, 0.0, 4085.0, 0.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(4080.0, 3780.0, 4080.0, 3780.0), direction='POWER'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_slgcp_1', sg13g2_tech)
    c.write_gds("sg13g2_slgcp_1.gds")
