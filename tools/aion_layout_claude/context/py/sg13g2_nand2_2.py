# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nand2_2
# ================================================================

"""Generated AION cell for sg13g2_nand2_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 2880.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 2880.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(285.0, 575.0, 2670.0, 1295.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2880.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(300.0, 2060.0, 2680.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2880.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1930.0, 1760.0, 2090.0, 1920.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1930.0, 1050.0, 2090.0, 1210.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(900.0, 1640.0, 1060.0, 1800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2440.0, 650.0, 2600.0, 810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(375.0, 990.0, 535.0, 1150.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(380.0, 650.0, 540.0, 810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2440.0, 2550.0, 2600.0, 2710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2440.0, 2210.0, 2600.0, 2370.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2440.0, 2950.0, 2600.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1930.0, 2550.0, 2090.0, 2710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1930.0, 2950.0, 2090.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1410.0, 1005.0, 1570.0, 1165.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(900.0, 2950.0, 1060.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(900.0, 2550.0, 1060.0, 2710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1410.0, 660.0, 1570.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(900.0, 645.0, 1060.0, 805.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 2950.0, 530.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 2540.0, 530.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 2130.0, 530.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1410.0, 2950.0, 1570.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2440.0, 990.0, 2600.0, 1150.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(660.0, 395.0), Point(660.0, 3360.0), Point(790.0, 3360.0), Point(790.0, 1875.0), Point(1170.0, 1875.0), Point(1170.0, 3360.0), Point(1300.0, 3360.0), Point(1300.0, 395.0), Point(1170.0, 395.0), Point(1170.0, 1565.0), Point(790.0, 1565.0), Point(790.0, 395.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1690.0, 395.0), Point(1690.0, 3360.0), Point(1820.0, 3360.0), Point(1820.0, 1990.0), Point(2200.0, 1990.0), Point(2200.0, 3360.0), Point(2330.0, 3360.0), Point(2330.0, 395.0), Point(2200.0, 395.0), Point(2200.0, 1690.0), Point(1820.0, 1690.0), Point(1820.0, 395.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1790.0, 1730.0, 2050.0, 2320.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2880.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2880.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1320.0, 1390.0, 1560.0, 2360.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(820.0, 1435.0, 1100.0, 1900.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(320.0, 2080.0), Point(320.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2880.0, 4000.0), Point(2880.0, 3560.0), Point(2650.0, 3560.0), Point(2650.0, 2160.0), Point(2390.0, 2160.0), Point(2390.0, 3560.0), Point(1620.0, 3560.0), Point(1620.0, 2900.0), Point(1360.0, 2900.0), Point(1360.0, 3560.0), Point(580.0, 3560.0), Point(580.0, 2080.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1790.0, 1730.0), Point(1790.0, 2320.0), Point(2050.0, 2320.0), Point(2050.0, 1980.0), Point(2170.0, 1980.0), Point(2170.0, 1730.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1880.0, 1000.0), Point(1880.0, 1390.0), Point(1320.0, 1390.0), Point(1320.0, 2500.0), Point(850.0, 2500.0), Point(850.0, 3160.0), Point(1110.0, 3160.0), Point(1110.0, 2720.0), Point(1880.0, 2720.0), Point(1880.0, 3160.0), Point(2140.0, 3160.0), Point(2140.0, 2500.0), Point(1560.0, 2500.0), Point(1560.0, 1550.0), Point(2140.0, 1550.0), Point(2140.0, 1000.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(325.0, 500.0), Point(325.0, 1200.0), Point(1620.0, 1200.0), Point(1620.0, 760.0), Point(2370.0, 760.0), Point(2370.0, 1200.0), Point(2650.0, 1200.0), Point(2650.0, 530.0), Point(1350.0, 530.0), Point(1350.0, 1035.0), Point(585.0, 1035.0), Point(585.0, 500.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(850.0, 220.0), Point(850.0, 855.0), Point(1110.0, 855.0), Point(1110.0, 220.0), Point(2880.0, 220.0), Point(2880.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(820.0, 1435.0, 1100.0, 1900.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(1440.0, 2100.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1370.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(1920.0, 2100.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1445.0, -20.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(980.0, 1655.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3120.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2950.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2950.0, 180.0)))

    # Ports
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(1440.0, 2100.0, 1440.0, 2100.0), direction='OUTPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1370.0, 3780.0, 1370.0, 3780.0), direction='POWER'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(1920.0, 2100.0, 1920.0, 2100.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1445.0, -20.0, 1445.0, -20.0), direction='GROUND'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(980.0, 1655.0, 980.0, 1655.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nand2_2', sg13g2_tech)
    c.write_gds("sg13g2_nand2_2.gds")
