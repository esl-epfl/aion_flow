# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_einvn_4
# ================================================================

"""Generated AION cell for sg13g2_einvn_4."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(335.0, 2060.0, 1155.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1510.0, 2060.0, 5890.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(335.0, 590.0, 1155.0, 1330.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1710.0, 590.0, 6090.0, 1330.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, -80.0, 6080.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5920.0, 3700.0, 6080.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5860.0, 660.0, 6020.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5660.0, 2270.0, 5820.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5660.0, 2610.0, 5820.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5660.0, 2950.0, 5820.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, -80.0, 5600.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5440.0, 3700.0, 5600.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5380.0, 1715.0, 5540.0, 1875.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5350.0, 940.0, 5510.0, 1100.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5150.0, 2270.0, 5310.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5150.0, 2610.0, 5310.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5040.0, 1715.0, 5200.0, 1875.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, -80.0, 5120.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4960.0, 3700.0, 5120.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4840.0, 660.0, 5000.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4700.0, 1715.0, 4860.0, 1875.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4640.0, 2610.0, 4800.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4640.0, 2950.0, 4800.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4330.0, 1080.0, 4490.0, 1240.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4130.0, 2270.0, 4290.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4130.0, 2610.0, 4290.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3820.0, 660.0, 3980.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3820.0, 1000.0, 3980.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3620.0, 2270.0, 3780.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3620.0, 2610.0, 3780.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3620.0, 2950.0, 3780.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3310.0, 660.0, 3470.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3310.0, 1000.0, 3470.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3110.0, 2270.0, 3270.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3110.0, 2610.0, 3270.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3110.0, 2950.0, 3270.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2800.0, 660.0, 2960.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2800.0, 1000.0, 2960.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2600.0, 2270.0, 2760.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2600.0, 2610.0, 2760.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2600.0, 2950.0, 2760.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2290.0, 660.0, 2450.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2290.0, 1000.0, 2450.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2090.0, 2270.0, 2250.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2090.0, 2610.0, 2250.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2090.0, 2950.0, 2250.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1780.0, 660.0, 1940.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(5860.0, 1000.0, 6020.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1780.0, 1000.0, 1940.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1580.0, 2270.0, 1740.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1580.0, 2610.0, 1740.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1580.0, 2950.0, 1740.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1355.0, 660.0, 1515.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1355.0, 1000.0, 1515.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(925.0, 660.0, 1085.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(925.0, 1000.0, 1085.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(925.0, 2270.0, 1085.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(925.0, 2610.0, 1085.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(925.0, 2950.0, 1085.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(515.0, 1715.0, 675.0, 1875.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(415.0, 660.0, 575.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(415.0, 1000.0, 575.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(415.0, 2270.0, 575.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(415.0, 2610.0, 575.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(415.0, 2950.0, 575.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(4090.0, 410.0), Point(4090.0, 1795.0), Point(3890.0, 1795.0), Point(3890.0, 3360.0), Point(4020.0, 3360.0), Point(4020.0, 1945.0), Point(4400.0, 1945.0), Point(4400.0, 3360.0), Point(4530.0, 3360.0), Point(4530.0, 1945.0), Point(4910.0, 1945.0), Point(4910.0, 3360.0), Point(5040.0, 3360.0), Point(5040.0, 1945.0), Point(5420.0, 1945.0), Point(5420.0, 3360.0), Point(5550.0, 3360.0), Point(5550.0, 1945.0), Point(5750.0, 1945.0), Point(5750.0, 410.0), Point(5620.0, 410.0), Point(5620.0, 1645.0), Point(5240.0, 1645.0), Point(5240.0, 410.0), Point(5110.0, 410.0), Point(5110.0, 1645.0), Point(4730.0, 1645.0), Point(4730.0, 410.0), Point(4600.0, 410.0), Point(4600.0, 1645.0), Point(4220.0, 1645.0), Point(4220.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2050.0, 410.0), Point(2050.0, 1405.0), Point(1600.0, 1405.0), Point(1600.0, 590.0), Point(1270.0, 590.0), Point(1270.0, 1555.0), Point(3710.0, 1555.0), Point(3710.0, 410.0), Point(3580.0, 410.0), Point(3580.0, 1405.0), Point(3200.0, 1405.0), Point(3200.0, 410.0), Point(3070.0, 410.0), Point(3070.0, 1405.0), Point(2690.0, 1405.0), Point(2690.0, 410.0), Point(2560.0, 410.0), Point(2560.0, 1405.0), Point(2180.0, 1405.0), Point(2180.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(685.0, 410.0), Point(685.0, 1645.0), Point(445.0, 1645.0), Point(445.0, 1945.0), Point(685.0, 1945.0), Point(685.0, 3360.0), Point(815.0, 3360.0), Point(815.0, 1945.0), Point(1850.0, 1945.0), Point(1850.0, 3360.0), Point(1980.0, 3360.0), Point(1980.0, 1945.0), Point(2360.0, 1945.0), Point(2360.0, 3360.0), Point(2490.0, 3360.0), Point(2490.0, 1945.0), Point(2870.0, 1945.0), Point(2870.0, 3360.0), Point(3000.0, 3360.0), Point(3000.0, 1945.0), Point(3380.0, 1945.0), Point(3380.0, 3360.0), Point(3510.0, 3360.0), Point(3510.0, 1795.0), Point(815.0, 1795.0), Point(815.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 6240.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(4650.0, 1540.0, 5590.0, 1925.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 6240.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(4200.0, 1025.0, 4435.0, 2170.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(340.0, 1460.0, 725.0, 2000.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(365.0, 220.0), Point(365.0, 1210.0), Point(625.0, 1210.0), Point(625.0, 220.0), Point(2240.0, 220.0), Point(2240.0, 1210.0), Point(2500.0, 1210.0), Point(2500.0, 220.0), Point(3260.0, 220.0), Point(3260.0, 1210.0), Point(3520.0, 1210.0), Point(3520.0, 220.0), Point(6240.0, 220.0), Point(6240.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(365.0, 2220.0), Point(365.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(6240.0, 4000.0), Point(6240.0, 3560.0), Point(3320.0, 3560.0), Point(3320.0, 2220.0), Point(3060.0, 2220.0), Point(3060.0, 3560.0), Point(2300.0, 3560.0), Point(2300.0, 2220.0), Point(2040.0, 2220.0), Point(2040.0, 3560.0), Point(625.0, 3560.0), Point(625.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4770.0, 475.0), Point(4770.0, 605.0), Point(3770.0, 605.0), Point(3770.0, 1405.0), Point(3010.0, 1405.0), Point(3010.0, 610.0), Point(2750.0, 610.0), Point(2750.0, 1405.0), Point(1965.0, 1405.0), Point(1965.0, 610.0), Point(1770.0, 610.0), Point(1770.0, 1575.0), Point(4000.0, 1575.0), Point(4000.0, 840.0), Point(5060.0, 840.0), Point(5060.0, 645.0), Point(5810.0, 645.0), Point(5810.0, 1210.0), Point(6070.0, 1210.0), Point(6070.0, 475.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1530.0, 1795.0), Point(1530.0, 3160.0), Point(1790.0, 3160.0), Point(1790.0, 2010.0), Point(2550.0, 2010.0), Point(2550.0, 3160.0), Point(2810.0, 3160.0), Point(2810.0, 2010.0), Point(3570.0, 2010.0), Point(3570.0, 3335.0), Point(5870.0, 3335.0), Point(5870.0, 2220.0), Point(5610.0, 2220.0), Point(5610.0, 3140.0), Point(4850.0, 3140.0), Point(4850.0, 2540.0), Point(4590.0, 2540.0), Point(4590.0, 3140.0), Point(3830.0, 3140.0), Point(3830.0, 1795.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(875.0, 610.0), Point(875.0, 1210.0), Point(910.0, 1210.0), Point(910.0, 2220.0), Point(875.0, 2220.0), Point(875.0, 3160.0), Point(1135.0, 3160.0), Point(1135.0, 1210.0), Point(1570.0, 1210.0), Point(1570.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(5300.0, 890.0), Point(5300.0, 1115.0), Point(4540.0, 1115.0), Point(4540.0, 1025.0), Point(4200.0, 1025.0), Point(4200.0, 2015.0), Point(4080.0, 2015.0), Point(4080.0, 2820.0), Point(4340.0, 2820.0), Point(4340.0, 2330.0), Point(5100.0, 2330.0), Point(5100.0, 2820.0), Point(5360.0, 2820.0), Point(5360.0, 2130.0), Point(4435.0, 2130.0), Point(4435.0, 1305.0), Point(5560.0, 1305.0), Point(5560.0, 890.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(4650.0, 1540.0, 5590.0, 1925.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(340.0, 1460.0, 725.0, 2000.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(5175.0, 1655.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(3120.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(3100.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'TE_B', Point(515.0, 1685.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Z', Point(4320.0, 1610.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 6480.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 6310.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 6310.0, 180.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(5175.0, 1655.0, 5175.0, 1655.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(3120.0, 0.0, 3120.0, 0.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(3100.0, 3780.0, 3100.0, 3780.0), direction='POWER'))
    cell.add_port(Port('TE_B', 'TE_B', tech['Metal1'], Rect.from_lbrt(515.0, 1685.0, 515.0, 1685.0)))
    cell.add_port(Port('Z', 'Z', tech['Metal1'], Rect.from_lbrt(4320.0, 1610.0, 4320.0, 1610.0), direction='OUTPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_einvn_4', sg13g2_tech)
    c.write_gds("sg13g2_einvn_4.gds")
