# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_dlhrq_1
# ================================================================

"""Generated AION cell for sg13g2_dlhrq_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(6085.0, 2060.0), Point(6085.0, 2180.0), Point(5045.0, 2180.0), Point(5045.0, 2760.0), Point(3825.0, 2760.0), Point(3825.0, 2180.0), Point(2055.0, 2180.0), Point(2055.0, 3020.0), Point(2600.0, 3020.0), Point(2600.0, 3180.0), Point(6835.0, 3180.0), Point(6835.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2615.0, 480.0), Point(2615.0, 515.0), Point(2045.0, 515.0), Point(2045.0, 1495.0), Point(2345.0, 1495.0), Point(2345.0, 1255.0), Point(2815.0, 1255.0), Point(2815.0, 1155.0), Point(3870.0, 1155.0), Point(3870.0, 935.0), Point(4770.0, 935.0), Point(4770.0, 515.0), Point(2855.0, 515.0), Point(2855.0, 480.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(975.0, 590.0), Point(975.0, 780.0), Point(225.0, 780.0), Point(225.0, 1330.0), Point(1795.0, 1330.0), Point(1795.0, 590.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1420.0, 2155.0), Point(1420.0, 2340.0), Point(340.0, 2340.0), Point(340.0, 3180.0), Point(1795.0, 3180.0), Point(1795.0, 2155.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 7200.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 7200.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(5005.0, 590.0, 6695.0, 1330.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, -80.0, 7040.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, 3700.0, 7040.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6590.0, 2140.0, 6750.0, 2300.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6590.0, 2540.0, 6750.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6590.0, 2940.0, 6750.0, 3100.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6465.0, 815.0, 6625.0, 975.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, -80.0, 6560.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, 3700.0, 6560.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6310.0, 1525.0, 6470.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6045.0, 2255.0, 6205.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6045.0, 2605.0, 6205.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6045.0, 2950.0, 6205.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5955.0, 815.0, 6115.0, 975.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5770.0, 1655.0, 5930.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5535.0, 2255.0, 5695.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5535.0, 2605.0, 5695.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5535.0, 2950.0, 5695.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5075.0, 665.0, 5235.0, 825.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5075.0, 1095.0, 5235.0, 1255.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5000.0, 1775.0, 5160.0, 1935.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4925.0, 2950.0, 5085.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4640.0, 2355.0, 4800.0, 2515.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4540.0, 705.0, 4700.0, 865.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4100.0, 1530.0, 4260.0, 1690.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4050.0, 2355.0, 4210.0, 2515.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3595.0, 2710.0, 3755.0, 2870.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3585.0, 900.0, 3745.0, 1060.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3385.0, 1425.0, 3545.0, 1585.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2860.0, 1775.0, 3020.0, 1935.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2670.0, 2950.0, 2830.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2655.0, 580.0, 2815.0, 740.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2125.0, 2250.0, 2285.0, 2410.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2115.0, 1265.0, 2275.0, 1425.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1835.0, 1755.0, 1995.0, 1915.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1565.0, 660.0, 1725.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1565.0, 1095.0, 1725.0, 1255.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1525.0, 2225.0, 1685.0, 2385.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1265.0, 1755.0, 1425.0, 1915.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1045.0, 660.0, 1205.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(920.0, 2950.0, 1080.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(425.0, 1605.0, 585.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(410.0, 2435.0, 570.0, 2595.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(410.0, 2930.0, 570.0, 3090.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(295.0, 975.0, 455.0, 1135.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(6225.0, 410.0), Point(6225.0, 1770.0), Point(6315.0, 1770.0), Point(6315.0, 3360.0), Point(6445.0, 3360.0), Point(6445.0, 1770.0), Point(6555.0, 1770.0), Point(6555.0, 1440.0), Point(6355.0, 1440.0), Point(6355.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(5715.0, 410.0), Point(5715.0, 1570.0), Point(5685.0, 1570.0), Point(5685.0, 1900.0), Point(5805.0, 1900.0), Point(5805.0, 3360.0), Point(5935.0, 3360.0), Point(5935.0, 1900.0), Point(6015.0, 1900.0), Point(6015.0, 1570.0), Point(5845.0, 1570.0), Point(5845.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(5345.0, 410.0), Point(5345.0, 1690.0), Point(4915.0, 1690.0), Point(4915.0, 2020.0), Point(5295.0, 2020.0), Point(5295.0, 3360.0), Point(5425.0, 3360.0), Point(5425.0, 2020.0), Point(5475.0, 2020.0), Point(5475.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4300.0, 335.0), Point(4300.0, 1235.0), Point(4555.0, 1235.0), Point(4555.0, 2450.0), Point(4550.0, 2450.0), Point(4550.0, 3360.0), Point(4680.0, 3360.0), Point(4680.0, 2600.0), Point(4885.0, 2600.0), Point(4885.0, 2270.0), Point(4705.0, 2270.0), Point(4705.0, 1085.0), Point(4430.0, 1085.0), Point(4430.0, 335.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3945.0, 335.0), Point(3945.0, 1910.0), Point(3345.0, 1910.0), Point(3345.0, 3360.0), Point(3475.0, 3360.0), Point(3475.0, 2060.0), Point(4095.0, 2060.0), Point(4095.0, 1775.0), Point(4345.0, 1775.0), Point(4345.0, 1445.0), Point(4075.0, 1445.0), Point(4075.0, 335.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3895.0, 2270.0), Point(3895.0, 3360.0), Point(4025.0, 3360.0), Point(4025.0, 2600.0), Point(4295.0, 2600.0), Point(4295.0, 2270.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3315.0, 335.0), Point(3315.0, 1670.0), Point(3645.0, 1670.0), Point(3645.0, 1340.0), Point(3445.0, 1340.0), Point(3445.0, 335.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2925.0, 335.0), Point(2925.0, 1690.0), Point(2775.0, 1690.0), Point(2775.0, 2020.0), Point(2940.0, 2020.0), Point(2940.0, 3360.0), Point(3070.0, 3360.0), Point(3070.0, 2020.0), Point(3105.0, 2020.0), Point(3105.0, 1690.0), Point(3055.0, 1690.0), Point(3055.0, 335.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2415.0, 335.0), Point(2415.0, 1670.0), Point(1750.0, 1670.0), Point(1750.0, 2000.0), Point(2080.0, 2000.0), Point(2080.0, 1820.0), Point(2395.0, 1820.0), Point(2395.0, 3200.0), Point(2525.0, 3200.0), Point(2525.0, 1820.0), Point(2545.0, 1820.0), Point(2545.0, 335.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1325.0, 410.0), Point(1325.0, 1670.0), Point(1165.0, 1670.0), Point(1165.0, 2000.0), Point(1190.0, 2000.0), Point(1190.0, 3360.0), Point(1320.0, 3360.0), Point(1320.0, 2000.0), Point(1510.0, 2000.0), Point(1510.0, 1670.0), Point(1455.0, 1670.0), Point(1455.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(775.0, 600.0), Point(775.0, 1520.0), Point(355.0, 1520.0), Point(355.0, 1850.0), Point(680.0, 1850.0), Point(680.0, 3360.0), Point(810.0, 3360.0), Point(810.0, 1670.0), Point(905.0, 1670.0), Point(905.0, 600.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(300.0, 1520.0, 600.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5695.0, 1570.0, 6015.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1185.0, 1505.0, 1525.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 7200.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6525.0, 2075.0, 6885.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 7200.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(995.0, 220.0), Point(995.0, 870.0), Point(1260.0, 870.0), Point(1260.0, 220.0), Point(2590.0, 220.0), Point(2590.0, 745.0), Point(2880.0, 745.0), Point(2880.0, 220.0), Point(4490.0, 220.0), Point(4490.0, 895.0), Point(4750.0, 895.0), Point(4750.0, 220.0), Point(5905.0, 220.0), Point(5905.0, 985.0), Point(6165.0, 985.0), Point(6165.0, 220.0), Point(7200.0, 220.0), Point(7200.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(6025.0, 2205.0), Point(6025.0, 3560.0), Point(5135.0, 3560.0), Point(5135.0, 2935.0), Point(4875.0, 2935.0), Point(4875.0, 3560.0), Point(2880.0, 3560.0), Point(2880.0, 2935.0), Point(2620.0, 2935.0), Point(2620.0, 3560.0), Point(1130.0, 3560.0), Point(1130.0, 2935.0), Point(870.0, 2935.0), Point(870.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(7200.0, 4000.0), Point(7200.0, 3560.0), Point(6230.0, 3560.0), Point(6230.0, 2205.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(6395.0, 770.0), Point(6395.0, 1020.0), Point(6725.0, 1020.0), Point(6725.0, 2075.0), Point(6525.0, 2075.0), Point(6525.0, 3160.0), Point(6885.0, 3160.0), Point(6885.0, 770.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5025.0, 640.0), Point(5025.0, 1360.0), Point(5355.0, 1360.0), Point(5355.0, 2300.0), Point(4555.0, 2300.0), Point(4555.0, 2585.0), Point(5495.0, 2585.0), Point(5495.0, 3160.0), Point(5735.0, 3160.0), Point(5735.0, 2205.0), Point(5515.0, 2205.0), Point(5515.0, 1360.0), Point(6225.0, 1360.0), Point(6225.0, 1770.0), Point(6545.0, 1770.0), Point(6545.0, 1200.0), Point(5285.0, 1200.0), Point(5285.0, 640.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3535.0, 850.0), Point(3535.0, 1085.0), Point(3745.0, 1085.0), Point(3745.0, 1945.0), Point(3625.0, 1945.0), Point(3625.0, 2660.0), Point(3545.0, 2660.0), Point(3545.0, 2920.0), Point(3785.0, 2920.0), Point(3785.0, 2115.0), Point(5175.0, 2115.0), Point(5175.0, 1690.0), Point(4915.0, 1690.0), Point(4915.0, 1955.0), Point(3905.0, 1955.0), Point(3905.0, 850.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3100.0, 475.0), Point(3100.0, 925.0), Point(1775.0, 925.0), Point(1775.0, 605.0), Point(1485.0, 605.0), Point(1485.0, 1315.0), Point(1705.0, 1315.0), Point(1705.0, 2180.0), Point(1465.0, 2180.0), Point(1465.0, 2415.0), Point(1875.0, 2415.0), Point(1875.0, 2000.0), Point(2080.0, 2000.0), Point(2080.0, 1680.0), Point(1865.0, 1680.0), Point(1865.0, 1085.0), Point(3270.0, 1085.0), Point(3270.0, 645.0), Point(4085.0, 645.0), Point(4085.0, 1775.0), Point(4345.0, 1775.0), Point(4345.0, 1445.0), Point(4255.0, 1445.0), Point(4255.0, 475.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2045.0, 1265.0), Point(2045.0, 1445.0), Point(2260.0, 1445.0), Point(2260.0, 2200.0), Point(2055.0, 2200.0), Point(2055.0, 2415.0), Point(2420.0, 2415.0), Point(2420.0, 1445.0), Point(3285.0, 1445.0), Point(3285.0, 2195.0), Point(3155.0, 2195.0), Point(3155.0, 3340.0), Point(4295.0, 3340.0), Point(4295.0, 2295.0), Point(3965.0, 2295.0), Point(3965.0, 3180.0), Point(3325.0, 3180.0), Point(3325.0, 2370.0), Point(3445.0, 2370.0), Point(3445.0, 1670.0), Point(3565.0, 1670.0), Point(3565.0, 1265.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(240.0, 920.0), Point(240.0, 1340.0), Point(780.0, 1340.0), Point(780.0, 2370.0), Point(365.0, 2370.0), Point(365.0, 3140.0), Point(610.0, 3140.0), Point(610.0, 2755.0), Point(2945.0, 2755.0), Point(2945.0, 2020.0), Point(3105.0, 2020.0), Point(3105.0, 1690.0), Point(2775.0, 1690.0), Point(2775.0, 2595.0), Point(965.0, 2595.0), Point(965.0, 1120.0), Point(515.0, 1120.0), Point(515.0, 920.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5695.0, 1570.0, 6015.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1185.0, 1505.0, 1525.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(300.0, 1520.0, 600.0, 2000.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Q', Point(6720.0, 2620.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(445.0, 1765.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'RESET_B', Point(5855.0, 1785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'GATE', Point(1360.0, 1765.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(3605.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(3535.0, 20.0), purpose='label'))

    # NWell
    cell.add_shape(PolygonShape(tech['NWell'], [Point(-240.0, 1750.0), Point(-240.0, 4170.0), Point(7440.0, 4170.0), Point(7440.0, 1750.0), Point(5830.0, 1750.0), Point(5830.0, 1870.0), Point(2030.0, 1870.0), Point(2030.0, 1845.0), Point(1120.0, 1845.0), Point(1120.0, 1750.0)]))

    # PSD
    cell.add_shape(PolygonShape(tech['PSD'], [Point(-70.0, 1760.0), Point(-70.0, 3600.0), Point(7270.0, 3600.0), Point(7270.0, 1760.0), Point(5890.0, 1760.0), Point(5890.0, 1880.0), Point(2020.0, 1880.0), Point(2020.0, 1855.0), Point(1110.0, 1855.0), Point(1110.0, 1760.0)]))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 7270.0, 180.0)))

    # Ports
    cell.add_port(Port('Q', 'Q', tech['Metal1'], Rect.from_lbrt(6720.0, 2620.0, 6720.0, 2620.0), direction='OUTPUT'))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(445.0, 1765.0, 445.0, 1765.0), direction='INPUT'))
    cell.add_port(Port('RESET_B', 'RESET_B', tech['Metal1'], Rect.from_lbrt(5855.0, 1785.0, 5855.0, 1785.0)))
    cell.add_port(Port('GATE', 'GATE', tech['Metal1'], Rect.from_lbrt(1360.0, 1765.0, 1360.0, 1765.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(3605.0, 3780.0, 3605.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(3535.0, 20.0, 3535.0, 20.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_dlhrq_1', sg13g2_tech)
    c.write_gds("sg13g2_dlhrq_1.gds")
