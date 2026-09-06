# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_ebufn_4
# ================================================================

"""Generated AION cell for sg13g2_ebufn_4."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 7200.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 7200.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(2540.0, 570.0, 6940.0, 1310.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(2500.0, 2070.0, 6940.0, 3190.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(360.0, 2070.0, 1680.0, 3190.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(260.0, 570.0, 1595.0, 1310.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, -80.0, 6560.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6400.0, 3700.0, 6560.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6710.0, 640.0, 6870.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6710.0, 980.0, 6870.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6710.0, 2280.0, 6870.0, 2440.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6710.0, 2620.0, 6870.0, 2780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6710.0, 2960.0, 6870.0, 3120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6200.0, 980.0, 6360.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6200.0, 2280.0, 6360.0, 2440.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6200.0, 2620.0, 6360.0, 2780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5725.0, 1645.0, 5885.0, 1805.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5690.0, 2620.0, 5850.0, 2780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5690.0, 2960.0, 5850.0, 3120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5685.0, 640.0, 5845.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5385.0, 1645.0, 5545.0, 1805.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5170.0, 2280.0, 5330.0, 2440.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5170.0, 2620.0, 5330.0, 2780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5165.0, 980.0, 5325.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5045.0, 1645.0, 5205.0, 1805.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4650.0, 640.0, 4810.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4650.0, 980.0, 4810.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4650.0, 2280.0, 4810.0, 2440.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4650.0, 2620.0, 4810.0, 2780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4650.0, 2960.0, 4810.0, 3120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4140.0, 640.0, 4300.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4140.0, 2620.0, 4300.0, 2780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4140.0, 2960.0, 4300.0, 3120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3630.0, 640.0, 3790.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3630.0, 980.0, 3790.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3630.0, 2280.0, 3790.0, 2440.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3630.0, 2620.0, 3790.0, 2780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3630.0, 2960.0, 3790.0, 3120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3120.0, 640.0, 3280.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3120.0, 980.0, 3280.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3120.0, 2960.0, 3280.0, 3120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2610.0, 640.0, 2770.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2610.0, 980.0, 2770.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2610.0, 2960.0, 2770.0, 3120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2145.0, 585.0, 2305.0, 745.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2145.0, 925.0, 2305.0, 1085.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2145.0, 1265.0, 2305.0, 1425.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1450.0, 2180.0, 1610.0, 2340.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1365.0, 640.0, 1525.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1645.0, 1505.0, 1805.0, 1665.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, 3700.0, 7040.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(940.0, 2960.0, 1100.0, 3120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(855.0, 640.0, 1015.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(855.0, 980.0, 1015.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(705.0, 1585.0, 865.0, 1745.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4140.0, 980.0, 4300.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(6880.0, -80.0, 7040.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 2605.0, 590.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 2960.0, 590.0, 3120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(330.0, 640.0, 490.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(330.0, 980.0, 490.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2880.0, 390.0), Point(2880.0, 1385.0), Point(2375.0, 1385.0), Point(2375.0, 500.0), Point(2060.0, 500.0), Point(2060.0, 1535.0), Point(4540.0, 1535.0), Point(4540.0, 390.0), Point(4410.0, 390.0), Point(4410.0, 1385.0), Point(4030.0, 1385.0), Point(4030.0, 390.0), Point(3900.0, 390.0), Point(3900.0, 1385.0), Point(3520.0, 1385.0), Point(3520.0, 390.0), Point(3390.0, 390.0), Point(3390.0, 1385.0), Point(3010.0, 1385.0), Point(3010.0, 390.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1125.0, 390.0), Point(1125.0, 1700.0), Point(1210.0, 1700.0), Point(1210.0, 3370.0), Point(1340.0, 3370.0), Point(1340.0, 1925.0), Point(2880.0, 1925.0), Point(2880.0, 3370.0), Point(3010.0, 3370.0), Point(3010.0, 1925.0), Point(3390.0, 1925.0), Point(3390.0, 3370.0), Point(3520.0, 3370.0), Point(3520.0, 1925.0), Point(3900.0, 1925.0), Point(3900.0, 3370.0), Point(4030.0, 3370.0), Point(4030.0, 1925.0), Point(4410.0, 1925.0), Point(4410.0, 3370.0), Point(4540.0, 3370.0), Point(4540.0, 1775.0), Point(1875.0, 1775.0), Point(1875.0, 1420.0), Point(1255.0, 1420.0), Point(1255.0, 390.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4920.0, 390.0), Point(4920.0, 3370.0), Point(5050.0, 3370.0), Point(5050.0, 1875.0), Point(5440.0, 1875.0), Point(5440.0, 3370.0), Point(5570.0, 3370.0), Point(5570.0, 1875.0), Point(5960.0, 1875.0), Point(5960.0, 3370.0), Point(6090.0, 3370.0), Point(6090.0, 1875.0), Point(6470.0, 1875.0), Point(6470.0, 3370.0), Point(6600.0, 3370.0), Point(6600.0, 390.0), Point(6470.0, 390.0), Point(6470.0, 1575.0), Point(6090.0, 1575.0), Point(6090.0, 390.0), Point(5960.0, 390.0), Point(5960.0, 1575.0), Point(5570.0, 1575.0), Point(5570.0, 390.0), Point(5440.0, 390.0), Point(5440.0, 1575.0), Point(5050.0, 1575.0), Point(5050.0, 390.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(600.0, 390.0), Point(600.0, 1830.0), Point(700.0, 1830.0), Point(700.0, 3370.0), Point(830.0, 3370.0), Point(830.0, 1830.0), Point(935.0, 1830.0), Point(935.0, 1500.0), Point(730.0, 1500.0), Point(730.0, 390.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(5115.0, 1145.0, 6410.0, 1375.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1300.0, 1020.0, 1580.0, 1700.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 7200.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 7200.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(650.0, 1960.0, 1185.0, 2240.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(805.0, 220.0), Point(805.0, 1190.0), Point(1065.0, 1190.0), Point(1065.0, 220.0), Point(3070.0, 220.0), Point(3070.0, 1160.0), Point(3330.0, 1160.0), Point(3330.0, 220.0), Point(4090.0, 220.0), Point(4090.0, 1160.0), Point(4350.0, 1160.0), Point(4350.0, 220.0), Point(7200.0, 220.0), Point(7200.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4090.0, 2570.0), Point(4090.0, 3560.0), Point(3330.0, 3560.0), Point(3330.0, 2945.0), Point(3070.0, 2945.0), Point(3070.0, 3560.0), Point(1150.0, 3560.0), Point(1150.0, 2910.0), Point(890.0, 2910.0), Point(890.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(7200.0, 4000.0), Point(7200.0, 3560.0), Point(4350.0, 3560.0), Point(4350.0, 2570.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4600.0, 455.0), Point(4600.0, 1340.0), Point(3840.0, 1340.0), Point(3840.0, 590.0), Point(3580.0, 590.0), Point(3580.0, 1340.0), Point(2820.0, 1340.0), Point(2820.0, 590.0), Point(2560.0, 590.0), Point(2560.0, 1510.0), Point(4820.0, 1510.0), Point(4820.0, 625.0), Point(5635.0, 625.0), Point(5635.0, 850.0), Point(5895.0, 850.0), Point(5895.0, 625.0), Point(6660.0, 625.0), Point(6660.0, 1190.0), Point(6920.0, 1190.0), Point(6920.0, 455.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3580.0, 2115.0), Point(3580.0, 2600.0), Point(2560.0, 2600.0), Point(2560.0, 3170.0), Point(2820.0, 3170.0), Point(2820.0, 2765.0), Point(3580.0, 2765.0), Point(3580.0, 3170.0), Point(3840.0, 3170.0), Point(3840.0, 2275.0), Point(4615.0, 2275.0), Point(4615.0, 3330.0), Point(6920.0, 3330.0), Point(6920.0, 2230.0), Point(6660.0, 2230.0), Point(6660.0, 3170.0), Point(5900.0, 3170.0), Point(5900.0, 2570.0), Point(5640.0, 2570.0), Point(5640.0, 3170.0), Point(4845.0, 3170.0), Point(4845.0, 2115.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5115.0, 930.0), Point(5115.0, 1375.0), Point(6230.0, 1375.0), Point(6230.0, 2110.0), Point(5120.0, 2110.0), Point(5120.0, 2830.0), Point(5380.0, 2830.0), Point(5380.0, 2335.0), Point(6150.0, 2335.0), Point(6150.0, 2830.0), Point(6410.0, 2830.0), Point(6410.0, 930.0), Point(6145.0, 930.0), Point(6145.0, 1145.0), Point(5375.0, 1145.0), Point(5375.0, 930.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2095.0, 535.0), Point(2095.0, 590.0), Point(1315.0, 590.0), Point(1315.0, 840.0), Point(2095.0, 840.0), Point(2095.0, 1885.0), Point(1400.0, 1885.0), Point(1400.0, 2390.0), Point(1660.0, 2390.0), Point(1660.0, 2050.0), Point(2355.0, 2050.0), Point(2355.0, 535.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(650.0, 1535.0), Point(650.0, 2240.0), Point(1185.0, 2240.0), Point(1185.0, 1960.0), Point(915.0, 1960.0), Point(915.0, 1535.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1300.0, 1020.0), Point(1300.0, 1700.0), Point(1855.0, 1700.0), Point(1855.0, 1420.0), Point(1580.0, 1420.0), Point(1580.0, 1020.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(280.0, 590.0), Point(280.0, 3170.0), Point(640.0, 3170.0), Point(640.0, 2730.0), Point(2120.0, 2730.0), Point(2120.0, 2390.0), Point(3200.0, 2390.0), Point(3200.0, 1860.0), Point(5935.0, 1860.0), Point(5935.0, 1595.0), Point(4995.0, 1595.0), Point(4995.0, 1700.0), Point(3030.0, 1700.0), Point(3030.0, 2230.0), Point(1960.0, 2230.0), Point(1960.0, 2570.0), Point(640.0, 2570.0), Point(640.0, 2555.0), Point(445.0, 2555.0), Point(445.0, 1190.0), Point(540.0, 1190.0), Point(540.0, 590.0)]))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(920.0, 2080.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(3590.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(2540.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'TE_B', Point(1440.0, 1345.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Z', Point(5775.0, 1260.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 7440.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 7280.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 7280.0, 180.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(920.0, 2080.0, 920.0, 2080.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(3590.0, 3780.0, 3590.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(2540.0, 0.0, 2540.0, 0.0), direction='GROUND'))
    cell.add_port(Port('TE_B', 'TE_B', tech['Metal1'], Rect.from_lbrt(1440.0, 1345.0, 1440.0, 1345.0)))
    cell.add_port(Port('Z', 'Z', tech['Metal1'], Rect.from_lbrt(5775.0, 1260.0, 5775.0, 1260.0), direction='OUTPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_ebufn_4', sg13g2_tech)
    c.write_gds("sg13g2_ebufn_4.gds")
