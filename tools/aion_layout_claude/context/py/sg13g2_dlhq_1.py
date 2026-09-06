# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_dlhq_1
# ================================================================

"""Generated AION cell for sg13g2_dlhq_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(0.0, -150.0), Point(0.0, 150.0), Point(5260.0, 150.0), Point(5260.0, 545.0), Point(4720.0, 545.0), Point(4720.0, 1285.0), Point(6100.0, 1285.0), Point(6100.0, 545.0), Point(5560.0, 545.0), Point(5560.0, 150.0), Point(6860.0, 150.0), Point(6860.0, 630.0), Point(6320.0, 630.0), Point(6320.0, 1370.0), Point(7700.0, 1370.0), Point(7700.0, 630.0), Point(7160.0, 630.0), Point(7160.0, 150.0), Point(8160.0, 150.0), Point(8160.0, -150.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(4480.0, 1905.0), Point(4480.0, 3025.0), Point(5020.0, 3025.0), Point(5020.0, 3630.0), Point(2135.0, 3630.0), Point(2135.0, 3105.0), Point(2045.0, 3105.0), Point(2045.0, 2600.0), Point(2585.0, 2600.0), Point(2585.0, 2180.0), Point(1285.0, 2180.0), Point(1285.0, 3180.0), Point(1825.0, 3180.0), Point(1825.0, 3630.0), Point(0.0, 3630.0), Point(0.0, 3930.0), Point(8160.0, 3930.0), Point(8160.0, 3630.0), Point(5320.0, 3630.0), Point(5320.0, 2745.0), Point(5860.0, 2745.0), Point(5860.0, 1905.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(6435.0, 2060.0), Point(6435.0, 2900.0), Point(6975.0, 2900.0), Point(6975.0, 3180.0), Point(7755.0, 3180.0), Point(7755.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2805.0, 2180.0), Point(2805.0, 2875.0), Point(2685.0, 2875.0), Point(2685.0, 3275.0), Point(3075.0, 3275.0), Point(3075.0, 3180.0), Point(3885.0, 3180.0), Point(3885.0, 3295.0), Point(4185.0, 3295.0), Point(4185.0, 2760.0), Point(3615.0, 2760.0), Point(3615.0, 2180.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1395.0, 645.0), Point(1395.0, 1130.0), Point(1465.0, 1130.0), Point(1465.0, 1385.0), Point(4035.0, 1385.0), Point(4035.0, 645.0), Point(3335.0, 645.0), Point(3335.0, 965.0), Point(2115.0, 965.0), Point(2115.0, 645.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(315.0, 660.0, 1125.0, 1210.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(255.0, 2340.0, 1065.0, 3180.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7840.0, -80.0, 8000.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7840.0, 3700.0, 8000.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7525.0, 2145.0, 7685.0, 2305.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7525.0, 2540.0, 7685.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7525.0, 2940.0, 7685.0, 3100.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7470.0, 705.0, 7630.0, 865.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7470.0, 1125.0, 7630.0, 1285.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, -80.0, 7520.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, 3700.0, 7520.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7200.0, 1625.0, 7360.0, 1785.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7015.0, 2255.0, 7175.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7015.0, 2675.0, 7175.0, 2835.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6930.0, 350.0, 7090.0, 510.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, -80.0, 7040.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, 3700.0, 7040.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6660.0, 1655.0, 6820.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6505.0, 2255.0, 6665.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6505.0, 2660.0, 6665.0, 2820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, -80.0, 6560.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, 3700.0, 6560.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6390.0, 1140.0, 6550.0, 1300.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6120.0, 1655.0, 6280.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5870.0, 1055.0, 6030.0, 1215.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5630.0, 1975.0, 5790.0, 2135.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5630.0, 2325.0, 5790.0, 2485.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5330.0, 270.0, 5490.0, 430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5090.0, 3145.0, 5250.0, 3305.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4790.0, 615.0, 4950.0, 775.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4790.0, 1055.0, 4950.0, 1215.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4550.0, 1990.0, 4710.0, 2150.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4340.0, 1080.0, 4500.0, 1240.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3955.0, 3065.0, 4115.0, 3225.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3805.0, 815.0, 3965.0, 975.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3800.0, 1580.0, 3960.0, 1740.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3385.0, 2275.0, 3545.0, 2435.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3295.0, 1155.0, 3455.0, 1315.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3130.0, 1740.0, 3290.0, 1900.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2830.0, 3035.0, 2990.0, 3195.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2450.0, 560.0, 2610.0, 720.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2355.0, 2310.0, 2515.0, 2470.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1975.0, 1095.0, 2135.0, 1255.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1900.0, 3195.0, 2060.0, 3355.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1465.0, 805.0, 1625.0, 965.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1355.0, 2270.0, 1515.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1355.0, 2610.0, 1515.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1355.0, 2950.0, 1515.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1110.0, 1405.0, 1270.0, 1565.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1110.0, 1745.0, 1270.0, 1905.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(895.0, 855.0, 1055.0, 1015.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(835.0, 2420.0, 995.0, 2580.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(835.0, 2945.0, 995.0, 3105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(540.0, 1485.0, 700.0, 1645.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(540.0, 1825.0, 700.0, 1985.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(385.0, 855.0, 545.0, 1015.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(325.0, 2420.0, 485.0, 2580.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(325.0, 2945.0, 485.0, 3105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(7230.0, 450.0), Point(7230.0, 1540.0), Point(7115.0, 1540.0), Point(7115.0, 1870.0), Point(7285.0, 1870.0), Point(7285.0, 3360.0), Point(7415.0, 3360.0), Point(7415.0, 1870.0), Point(7445.0, 1870.0), Point(7445.0, 1540.0), Point(7360.0, 1540.0), Point(7360.0, 450.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(6660.0, 450.0), Point(6660.0, 1570.0), Point(6575.0, 1570.0), Point(6575.0, 1900.0), Point(6775.0, 1900.0), Point(6775.0, 3080.0), Point(6905.0, 3080.0), Point(6905.0, 1570.0), Point(6790.0, 1570.0), Point(6790.0, 450.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(5630.0, 365.0), Point(5630.0, 1570.0), Point(5390.0, 1570.0), Point(5390.0, 2925.0), Point(5520.0, 2925.0), Point(5520.0, 1720.0), Point(6035.0, 1720.0), Point(6035.0, 1900.0), Point(6365.0, 1900.0), Point(6365.0, 1570.0), Point(5760.0, 1570.0), Point(5760.0, 365.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(5060.0, 365.0), Point(5060.0, 1445.0), Point(4585.0, 1445.0), Point(4585.0, 995.0), Point(4255.0, 995.0), Point(4255.0, 1595.0), Point(4820.0, 1595.0), Point(4820.0, 3205.0), Point(4950.0, 3205.0), Point(4950.0, 1595.0), Point(5190.0, 1595.0), Point(5190.0, 365.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3565.0, 465.0), Point(3565.0, 1610.0), Point(3695.0, 1610.0), Point(3695.0, 1850.0), Point(3685.0, 1850.0), Point(3685.0, 3360.0), Point(3815.0, 3360.0), Point(3815.0, 2000.0), Point(4045.0, 2000.0), Point(4045.0, 1460.0), Point(3695.0, 1460.0), Point(3695.0, 465.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3000.0, 785.0), Point(3000.0, 1985.0), Point(3145.0, 1985.0), Point(3145.0, 3360.0), Point(3275.0, 3360.0), Point(3275.0, 1985.0), Point(3375.0, 1985.0), Point(3375.0, 1655.0), Point(3130.0, 1655.0), Point(3130.0, 785.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2365.0, 475.0), Point(2365.0, 805.0), Point(2630.0, 805.0), Point(2630.0, 1850.0), Point(2115.0, 1850.0), Point(2115.0, 2780.0), Point(2245.0, 2780.0), Point(2245.0, 2000.0), Point(2760.0, 2000.0), Point(2760.0, 475.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1735.0, 465.0), Point(1735.0, 1460.0), Point(1355.0, 1460.0), Point(1355.0, 1320.0), Point(1025.0, 1320.0), Point(1025.0, 1990.0), Point(1355.0, 1990.0), Point(1355.0, 1610.0), Point(1625.0, 1610.0), Point(1625.0, 3360.0), Point(1755.0, 3360.0), Point(1755.0, 1610.0), Point(1865.0, 1610.0), Point(1865.0, 465.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(655.0, 480.0), Point(655.0, 1400.0), Point(455.0, 1400.0), Point(455.0, 2070.0), Point(595.0, 2070.0), Point(595.0, 3360.0), Point(725.0, 3360.0), Point(725.0, 2070.0), Point(785.0, 2070.0), Point(785.0, 480.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6575.0, 1570.0, 6905.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(7450.0, 2075.0, 7785.0, 3155.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 8160.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 8160.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(315.0, 1400.0, 785.0, 2070.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(335.0, 220.0), Point(335.0, 1030.0), Point(595.0, 1030.0), Point(595.0, 220.0), Point(1925.0, 220.0), Point(1925.0, 1270.0), Point(2185.0, 1270.0), Point(2185.0, 220.0), Point(5270.0, 220.0), Point(5270.0, 445.0), Point(5550.0, 445.0), Point(5550.0, 220.0), Point(6880.0, 220.0), Point(6880.0, 515.0), Point(7140.0, 515.0), Point(7140.0, 220.0), Point(8160.0, 220.0), Point(8160.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(6965.0, 2230.0), Point(6965.0, 3560.0), Point(5305.0, 3560.0), Point(5305.0, 3115.0), Point(5030.0, 3115.0), Point(5030.0, 3560.0), Point(2110.0, 3560.0), Point(2110.0, 3190.0), Point(1850.0, 3190.0), Point(1850.0, 3560.0), Point(535.0, 3560.0), Point(535.0, 2400.0), Point(275.0, 2400.0), Point(275.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(8160.0, 4000.0), Point(8160.0, 3560.0), Point(7225.0, 3560.0), Point(7225.0, 2230.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(7435.0, 630.0), Point(7435.0, 1355.0), Point(7625.0, 1355.0), Point(7625.0, 2075.0), Point(7450.0, 2075.0), Point(7450.0, 3155.0), Point(7785.0, 3155.0), Point(7785.0, 630.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2390.0, 475.0), Point(2390.0, 780.0), Point(2665.0, 780.0), Point(2665.0, 635.0), Point(4770.0, 635.0), Point(4770.0, 1930.0), Point(4500.0, 1930.0), Point(4500.0, 2195.0), Point(5005.0, 2195.0), Point(5005.0, 785.0), Point(6290.0, 785.0), Point(6290.0, 880.0), Point(7085.0, 880.0), Point(7085.0, 1870.0), Point(7445.0, 1870.0), Point(7445.0, 1540.0), Point(7255.0, 1540.0), Point(7255.0, 700.0), Point(6500.0, 700.0), Point(6500.0, 625.0), Point(5005.0, 625.0), Point(5005.0, 475.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(6235.0, 1115.0), Point(6235.0, 1570.0), Point(6035.0, 1570.0), Point(6035.0, 2725.0), Point(3950.0, 2725.0), Point(3950.0, 1930.0), Point(3545.0, 1930.0), Point(3545.0, 1655.0), Point(3045.0, 1655.0), Point(3045.0, 1975.0), Point(3390.0, 1975.0), Point(3390.0, 2095.0), Point(3780.0, 2095.0), Point(3780.0, 2885.0), Point(6715.0, 2885.0), Point(6715.0, 2205.0), Point(6395.0, 2205.0), Point(6395.0, 1390.0), Point(6600.0, 1390.0), Point(6600.0, 1115.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5565.0, 1005.0), Point(5565.0, 2385.0), Point(4290.0, 2385.0), Point(4290.0, 1515.0), Point(3735.0, 1515.0), Point(3735.0, 1750.0), Point(4130.0, 1750.0), Point(4130.0, 2545.0), Point(5815.0, 2545.0), Point(5815.0, 1265.0), Point(6055.0, 1265.0), Point(6055.0, 1005.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4255.0, 995.0), Point(4255.0, 1155.0), Point(3225.0, 1155.0), Point(3225.0, 1315.0), Point(2705.0, 1315.0), Point(2705.0, 2315.0), Point(3050.0, 2315.0), Point(3050.0, 2435.0), Point(3600.0, 2435.0), Point(3600.0, 2275.0), Point(3205.0, 2275.0), Point(3205.0, 2155.0), Point(2865.0, 2155.0), Point(2865.0, 1475.0), Point(3545.0, 1475.0), Point(3545.0, 1325.0), Point(4585.0, 1325.0), Point(4585.0, 995.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2270.0, 2225.0), Point(2270.0, 2660.0), Point(2710.0, 2660.0), Point(2710.0, 2785.0), Point(3330.0, 2785.0), Point(3330.0, 3235.0), Point(4175.0, 3235.0), Point(4175.0, 3065.0), Point(3500.0, 3065.0), Point(3500.0, 2615.0), Point(2865.0, 2615.0), Point(2865.0, 2495.0), Point(2520.0, 2495.0), Point(2520.0, 2225.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1415.0, 725.0), Point(1415.0, 1035.0), Point(1535.0, 1035.0), Point(1535.0, 1745.0), Point(2525.0, 1745.0), Point(2525.0, 1130.0), Point(3020.0, 1130.0), Point(3020.0, 975.0), Point(4020.0, 975.0), Point(4020.0, 815.0), Point(2850.0, 815.0), Point(2850.0, 965.0), Point(2365.0, 965.0), Point(2365.0, 1575.0), Point(1695.0, 1575.0), Point(1695.0, 725.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1335.0, 2215.0), Point(1335.0, 3165.0), Point(1570.0, 3165.0), Point(1570.0, 3000.0), Point(2355.0, 3000.0), Point(2355.0, 3205.0), Point(3040.0, 3205.0), Point(3040.0, 3025.0), Point(2525.0, 3025.0), Point(2525.0, 2840.0), Point(1570.0, 2840.0), Point(1570.0, 2215.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(825.0, 790.0), Point(825.0, 1095.0), Point(965.0, 1095.0), Point(965.0, 2405.0), Point(785.0, 2405.0), Point(785.0, 3135.0), Point(1135.0, 3135.0), Point(1135.0, 1990.0), Point(1355.0, 1990.0), Point(1355.0, 1320.0), Point(1125.0, 1320.0), Point(1125.0, 790.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6575.0, 1570.0, 6905.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(315.0, 1400.0, 785.0, 2070.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'GATE', Point(6740.0, 1785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Q', Point(7610.0, 2650.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(4080.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(4185.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(550.0, 1735.0), purpose='label'))

    # NWell
    cell.add_shape(PolygonShape(tech['NWell'], [Point(4270.0, 1595.0), Point(4270.0, 1675.0), Point(4195.0, 1675.0), Point(4195.0, 1750.0), Point(-250.0, 1750.0), Point(-250.0, 4170.0), Point(8460.0, 4170.0), Point(8460.0, 1750.0), Point(6140.0, 1750.0), Point(6140.0, 1630.0), Point(6105.0, 1630.0), Point(6105.0, 1595.0)]))

    # PSD
    cell.add_shape(PolygonShape(tech['PSD'], [Point(4275.0, 1600.0), Point(4275.0, 1680.0), Point(4200.0, 1680.0), Point(4200.0, 1760.0), Point(-70.0, 1760.0), Point(-70.0, 3600.0), Point(8230.0, 3600.0), Point(8230.0, 1760.0), Point(6135.0, 1760.0), Point(6135.0, 1635.0), Point(6100.0, 1635.0), Point(6100.0, 1600.0)]))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 8230.0, 180.0)))

    # Ports
    cell.add_port(Port('GATE', 'GATE', tech['Metal1'], Rect.from_lbrt(6740.0, 1785.0, 6740.0, 1785.0)))
    cell.add_port(Port('Q', 'Q', tech['Metal1'], Rect.from_lbrt(7610.0, 2650.0, 7610.0, 2650.0), direction='OUTPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(4080.0, 3780.0, 4080.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(4185.0, 0.0, 4185.0, 0.0), direction='GROUND'))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(550.0, 1735.0, 550.0, 1735.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_dlhq_1', sg13g2_tech)
    c.write_gds("sg13g2_dlhq_1.gds")
