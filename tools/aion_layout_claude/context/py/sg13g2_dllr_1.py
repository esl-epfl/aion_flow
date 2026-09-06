# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_dllr_1
# ================================================================

"""Generated AION cell for sg13g2_dllr_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 9120.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 9120.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(915.0, 590.0), Point(915.0, 780.0), Point(370.0, 780.0), Point(370.0, 1330.0), Point(1760.0, 1330.0), Point(1760.0, 590.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(5490.0, 1930.0), Point(5490.0, 2760.0), Point(4080.0, 2760.0), Point(4080.0, 2180.0), Point(2490.0, 2180.0), Point(2490.0, 1955.0), Point(2190.0, 1955.0), Point(2190.0, 3020.0), Point(2770.0, 3020.0), Point(2770.0, 3630.0), Point(0.0, 3630.0), Point(0.0, 3930.0), Point(9120.0, 3930.0), Point(9120.0, 3630.0), Point(3120.0, 3630.0), Point(3120.0, 3180.0), Point(5685.0, 3180.0), Point(5685.0, 3050.0), Point(7245.0, 3050.0), Point(7245.0, 1930.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(8050.0, 2060.0), Point(8050.0, 2140.0), Point(7510.0, 2140.0), Point(7510.0, 2980.0), Point(8050.0, 2980.0), Point(8050.0, 3180.0), Point(8900.0, 3180.0), Point(8900.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2740.0, 570.0), Point(2740.0, 590.0), Point(2095.0, 590.0), Point(2095.0, 1330.0), Point(2835.0, 1330.0), Point(2835.0, 1230.0), Point(5270.0, 1230.0), Point(5270.0, 810.0), Point(4265.0, 810.0), Point(4265.0, 590.0), Point(3065.0, 590.0), Point(3065.0, 570.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(8065.0, 535.0), Point(8065.0, 725.0), Point(7525.0, 725.0), Point(7525.0, 1275.0), Point(8875.0, 1275.0), Point(8875.0, 535.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(5480.0, 535.0, 7170.0, 1275.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 9120.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(375.0, 2340.0, 1930.0, 3180.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(445.0, 2950.0, 605.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(440.0, 955.0, 600.0, 1115.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1000.0, 660.0, 1160.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2835.0, 655.0, 2995.0, 815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3925.0, 665.0, 4085.0, 825.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3850.0, 2710.0, 4010.0, 2870.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5550.0, 605.0, 5710.0, 765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5550.0, 970.0, 5710.0, 1130.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, 3700.0, 6560.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6245.0, 1525.0, 6405.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, 3700.0, 7040.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6850.0, 1525.0, 7010.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7015.0, 2415.0, 7175.0, 2575.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7015.0, 2820.0, 7175.0, 2980.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7595.0, 795.0, 7755.0, 955.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7580.0, 2405.0, 7740.0, 2565.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8160.0, 2130.0, 8320.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8160.0, 2540.0, 8320.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8645.0, 605.0, 8805.0, 765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8645.0, 1045.0, 8805.0, 1205.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8800.0, -80.0, 8960.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1530.0, 1065.0, 1690.0, 1225.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2260.0, 2025.0, 2420.0, 2185.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4245.0, 1425.0, 4405.0, 1585.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, -80.0, 6560.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5040.0, 940.0, 5200.0, 1100.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8135.0, 1045.0, 8295.0, 1205.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7015.0, 2025.0, 7175.0, 2185.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, 3700.0, 7520.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8310.0, 1605.0, 8470.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1375.0, 1565.0, 1535.0, 1725.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, -80.0, 7040.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7840.0, -80.0, 8000.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(805.0, 1565.0, 965.0, 1725.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(805.0, 1905.0, 965.0, 2065.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(445.0, 2410.0, 605.0, 2570.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8670.0, 2540.0, 8830.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7840.0, 3700.0, 8000.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6430.0, 605.0, 6590.0, 765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3110.0, 1775.0, 3270.0, 1935.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4330.0, 2355.0, 4490.0, 2515.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2165.0, 1015.0, 2325.0, 1175.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1530.0, 660.0, 1690.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8670.0, 2950.0, 8830.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5995.0, 2820.0, 6155.0, 2980.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6430.0, 945.0, 6590.0, 1105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2875.0, 3125.0, 3035.0, 3285.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5210.0, 1525.0, 5370.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5070.0, 2830.0, 5230.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2165.0, 660.0, 2325.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1375.0, 1905.0, 1535.0, 2065.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8800.0, 3700.0, 8960.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8670.0, 2130.0, 8830.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8320.0, -80.0, 8480.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8320.0, 3700.0, 8480.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8160.0, 2950.0, 8320.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(8135.0, 605.0, 8295.0, 765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7580.0, 2750.0, 7740.0, 2910.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(7360.0, -80.0, 7520.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6940.0, 605.0, 7100.0, 765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6940.0, 950.0, 7100.0, 1110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5485.0, 2830.0, 5645.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4900.0, 2265.0, 5060.0, 2425.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3650.0, 1425.0, 3810.0, 1585.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2555.0, 1525.0, 2715.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1700.0, 2470.0, 1860.0, 2630.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1000.0, 1065.0, 1160.0, 1225.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(955.0, 2950.0, 1115.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5995.0, 2025.0, 6155.0, 2185.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6505.0, 2450.0, 6665.0, 2610.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6505.0, 2790.0, 6665.0, 2950.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5995.0, 2425.0, 6155.0, 2585.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1290.0, 410.0), Point(1290.0, 2150.0), Point(1460.0, 2150.0), Point(1460.0, 3360.0), Point(1590.0, 3360.0), Point(1590.0, 2150.0), Point(1640.0, 2150.0), Point(1640.0, 1480.0), Point(1420.0, 1480.0), Point(1420.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(8405.0, 355.0), Point(8405.0, 1520.0), Point(8225.0, 1520.0), Point(8225.0, 1850.0), Point(8430.0, 1850.0), Point(8430.0, 3360.0), Point(8560.0, 3360.0), Point(8560.0, 1520.0), Point(8535.0, 1520.0), Point(8535.0, 355.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(6700.0, 355.0), Point(6700.0, 1800.0), Point(6775.0, 1800.0), Point(6775.0, 3230.0), Point(6905.0, 3230.0), Point(6905.0, 1800.0), Point(7605.0, 1800.0), Point(7605.0, 1980.0), Point(7850.0, 1980.0), Point(7850.0, 3160.0), Point(7980.0, 3160.0), Point(7980.0, 1980.0), Point(7995.0, 1980.0), Point(7995.0, 545.0), Point(7865.0, 545.0), Point(7865.0, 1440.0), Point(6830.0, 1440.0), Point(6830.0, 355.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(6190.0, 355.0), Point(6190.0, 1440.0), Point(6160.0, 1440.0), Point(6160.0, 1770.0), Point(6265.0, 1770.0), Point(6265.0, 3230.0), Point(6395.0, 3230.0), Point(6395.0, 1770.0), Point(6490.0, 1770.0), Point(6490.0, 1440.0), Point(6320.0, 1440.0), Point(6320.0, 355.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(5820.0, 355.0), Point(5820.0, 1440.0), Point(5125.0, 1440.0), Point(5125.0, 1770.0), Point(5755.0, 1770.0), Point(5755.0, 3230.0), Point(5885.0, 3230.0), Point(5885.0, 1770.0), Point(5950.0, 1770.0), Point(5950.0, 355.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4730.0, 630.0), Point(4730.0, 2060.0), Point(4815.0, 2060.0), Point(4815.0, 2685.0), Point(4830.0, 2685.0), Point(4830.0, 3360.0), Point(4960.0, 3360.0), Point(4960.0, 2510.0), Point(5145.0, 2510.0), Point(5145.0, 2180.0), Point(4965.0, 2180.0), Point(4965.0, 1910.0), Point(4860.0, 1910.0), Point(4860.0, 630.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4150.0, 2270.0), Point(4150.0, 3360.0), Point(4280.0, 3360.0), Point(4280.0, 2600.0), Point(4575.0, 2600.0), Point(4575.0, 2270.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4360.0, 630.0), Point(4360.0, 1340.0), Point(4160.0, 1340.0), Point(4160.0, 1910.0), Point(3610.0, 1910.0), Point(3610.0, 3360.0), Point(3740.0, 3360.0), Point(3740.0, 2060.0), Point(4310.0, 2060.0), Point(4310.0, 1670.0), Point(4490.0, 1670.0), Point(4490.0, 630.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3565.0, 410.0), Point(3565.0, 1670.0), Point(3895.0, 1670.0), Point(3895.0, 1340.0), Point(3695.0, 1340.0), Point(3695.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3195.0, 410.0), Point(3195.0, 1690.0), Point(3025.0, 1690.0), Point(3025.0, 2020.0), Point(3190.0, 2020.0), Point(3190.0, 3360.0), Point(3320.0, 3360.0), Point(3320.0, 2025.0), Point(3355.0, 2025.0), Point(3355.0, 1690.0), Point(3325.0, 1690.0), Point(3325.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2435.0, 410.0), Point(2435.0, 1770.0), Point(2570.0, 1770.0), Point(2570.0, 3200.0), Point(2700.0, 3200.0), Point(2700.0, 1770.0), Point(2800.0, 1770.0), Point(2800.0, 1440.0), Point(2565.0, 1440.0), Point(2565.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(715.0, 600.0), Point(715.0, 3360.0), Point(845.0, 3360.0), Point(845.0, 2150.0), Point(1050.0, 2150.0), Point(1050.0, 1480.0), Point(845.0, 1480.0), Point(845.0, 600.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(720.0, 1480.0, 1100.0, 2120.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6110.0, 1410.0, 6450.0, 1810.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6975.0, 1965.0, 7310.0, 3035.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 9120.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 9120.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(8550.0, 2070.0, 8960.0, 3135.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1290.0, 1490.0, 1610.0, 2120.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(7545.0, 725.0), Point(7545.0, 980.0), Point(7615.0, 980.0), Point(7615.0, 2355.0), Point(7530.0, 2355.0), Point(7530.0, 2960.0), Point(7825.0, 2960.0), Point(7825.0, 1850.0), Point(8520.0, 1850.0), Point(8520.0, 1520.0), Point(7835.0, 1520.0), Point(7835.0, 725.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5495.0, 555.0), Point(5495.0, 1270.0), Point(5605.0, 1270.0), Point(5605.0, 2200.0), Point(4815.0, 2200.0), Point(4815.0, 2510.0), Point(5900.0, 2510.0), Point(5900.0, 3070.0), Point(6230.0, 3070.0), Point(6230.0, 2245.0), Point(6795.0, 2245.0), Point(6795.0, 1770.0), Point(7060.0, 1770.0), Point(7060.0, 1480.0), Point(6635.0, 1480.0), Point(6635.0, 1990.0), Point(5780.0, 1990.0), Point(5780.0, 555.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(8595.0, 540.0), Point(8595.0, 1220.0), Point(8715.0, 1220.0), Point(8715.0, 2070.0), Point(8550.0, 2070.0), Point(8550.0, 3135.0), Point(8960.0, 3135.0), Point(8960.0, 540.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3835.0, 595.0), Point(3835.0, 830.0), Point(4670.0, 830.0), Point(4670.0, 1855.0), Point(3915.0, 1855.0), Point(3915.0, 2625.0), Point(3785.0, 2625.0), Point(3785.0, 2955.0), Point(4075.0, 2955.0), Point(4075.0, 2020.0), Point(5010.0, 2020.0), Point(5010.0, 1770.0), Point(5405.0, 1770.0), Point(5405.0, 1440.0), Point(4830.0, 1440.0), Point(4830.0, 595.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2130.0, 605.0), Point(2130.0, 2250.0), Point(2485.0, 2250.0), Point(2485.0, 1955.0), Point(2300.0, 1955.0), Point(2300.0, 1225.0), Point(2380.0, 1225.0), Point(2380.0, 1170.0), Point(4160.0, 1170.0), Point(4160.0, 1670.0), Point(4490.0, 1670.0), Point(4490.0, 1010.0), Point(2390.0, 1010.0), Point(2390.0, 605.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(950.0, 220.0), Point(950.0, 1235.0), Point(1210.0, 1235.0), Point(1210.0, 220.0), Point(2785.0, 220.0), Point(2785.0, 820.0), Point(3045.0, 820.0), Point(3045.0, 220.0), Point(5010.0, 220.0), Point(5010.0, 1165.0), Point(5240.0, 1165.0), Point(5240.0, 220.0), Point(6380.0, 220.0), Point(6380.0, 1160.0), Point(6640.0, 1160.0), Point(6640.0, 220.0), Point(8085.0, 220.0), Point(8085.0, 1220.0), Point(8345.0, 1220.0), Point(8345.0, 220.0), Point(9120.0, 220.0), Point(9120.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(8150.0, 2060.0), Point(8150.0, 3560.0), Point(6715.0, 3560.0), Point(6715.0, 2425.0), Point(6455.0, 2425.0), Point(6455.0, 3560.0), Point(5695.0, 3560.0), Point(5695.0, 2815.0), Point(5020.0, 2815.0), Point(5020.0, 3560.0), Point(3085.0, 3560.0), Point(3085.0, 3120.0), Point(2825.0, 3120.0), Point(2825.0, 3560.0), Point(1165.0, 3560.0), Point(1165.0, 2895.0), Point(905.0, 2895.0), Point(905.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(9120.0, 4000.0), Point(9120.0, 3560.0), Point(8330.0, 3560.0), Point(8330.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1510.0, 595.0), Point(1510.0, 1290.0), Point(1790.0, 1290.0), Point(1790.0, 2410.0), Point(1690.0, 2410.0), Point(1690.0, 2695.0), Point(1960.0, 2695.0), Point(1960.0, 2590.0), Point(2840.0, 2590.0), Point(2840.0, 1510.0), Point(3565.0, 1510.0), Point(3565.0, 2200.0), Point(3405.0, 2200.0), Point(3405.0, 3340.0), Point(4550.0, 3340.0), Point(4550.0, 2270.0), Point(4275.0, 2270.0), Point(4275.0, 3155.0), Point(3575.0, 3155.0), Point(3575.0, 2365.0), Point(3735.0, 2365.0), Point(3735.0, 1670.0), Point(3895.0, 1670.0), Point(3895.0, 1350.0), Point(2520.0, 1350.0), Point(2520.0, 1465.0), Point(2505.0, 1465.0), Point(2505.0, 1770.0), Point(2670.0, 1770.0), Point(2670.0, 2430.0), Point(1950.0, 2430.0), Point(1950.0, 595.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(380.0, 875.0), Point(380.0, 3120.0), Point(655.0, 3120.0), Point(655.0, 2515.0), Point(1350.0, 2515.0), Point(1350.0, 3120.0), Point(2300.0, 3120.0), Point(2300.0, 2940.0), Point(3195.0, 2940.0), Point(3195.0, 2020.0), Point(3355.0, 2020.0), Point(3355.0, 1690.0), Point(3025.0, 1690.0), Point(3025.0, 2780.0), Point(2130.0, 2780.0), Point(2130.0, 2950.0), Point(1510.0, 2950.0), Point(1510.0, 2355.0), Point(540.0, 2355.0), Point(540.0, 1185.0), Point(660.0, 1185.0), Point(660.0, 875.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(6890.0, 535.0), Point(6890.0, 1250.0), Point(7245.0, 1250.0), Point(7245.0, 1965.0), Point(6975.0, 1965.0), Point(6975.0, 3035.0), Point(7310.0, 3035.0), Point(7310.0, 2200.0), Point(7435.0, 2200.0), Point(7435.0, 1135.0), Point(7365.0, 1135.0), Point(7365.0, 535.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(6110.0, 1410.0, 6450.0, 1810.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1290.0, 1490.0, 1610.0, 2120.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(720.0, 1480.0, 1100.0, 2120.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'GATE_N', Point(1450.0, 1630.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Q_N', Point(8770.0, 2610.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'D', Point(910.0, 1930.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'RESET_B', Point(6315.0, 1600.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Q', Point(7135.0, 2605.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(4350.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(4335.0, 25.0), purpose='label'))

    # NWell
    cell.add_shape(PolygonShape(tech['NWell'], [Point(5025.0, 1620.0), Point(5025.0, 1645.0), Point(1880.0, 1645.0), Point(1880.0, 1750.0), Point(-240.0, 1750.0), Point(-240.0, 4170.0), Point(9360.0, 4170.0), Point(9360.0, 1750.0), Point(7510.0, 1750.0), Point(7510.0, 1620.0)]))

    # PSD
    cell.add_shape(PolygonShape(tech['PSD'], [Point(5220.0, 1630.0), Point(5220.0, 2460.0), Point(4345.0, 2460.0), Point(4345.0, 1880.0), Point(2710.0, 1880.0), Point(2710.0, 1655.0), Point(1955.0, 1655.0), Point(1955.0, 1760.0), Point(-70.0, 1760.0), Point(-70.0, 3600.0), Point(9190.0, 3600.0), Point(9190.0, 1760.0), Point(7550.0, 1760.0), Point(7550.0, 1630.0)]))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 9190.0, 180.0)))

    # Ports
    cell.add_port(Port('GATE_N', 'GATE_N', tech['Metal1'], Rect.from_lbrt(1450.0, 1630.0, 1450.0, 1630.0)))
    cell.add_port(Port('Q_N', 'Q_N', tech['Metal1'], Rect.from_lbrt(8770.0, 2610.0, 8770.0, 2610.0)))
    cell.add_port(Port('D', 'D', tech['Metal1'], Rect.from_lbrt(910.0, 1930.0, 910.0, 1930.0), direction='INPUT'))
    cell.add_port(Port('RESET_B', 'RESET_B', tech['Metal1'], Rect.from_lbrt(6315.0, 1600.0, 6315.0, 1600.0)))
    cell.add_port(Port('Q', 'Q', tech['Metal1'], Rect.from_lbrt(7135.0, 2605.0, 7135.0, 2605.0), direction='OUTPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(4350.0, 3780.0, 4350.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(4335.0, 25.0, 4335.0, 25.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_dllr_1', sg13g2_tech)
    c.write_gds("sg13g2_dllr_1.gds")
