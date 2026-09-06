# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nand3b_1
# ================================================================

"""Generated AION cell for sg13g2_nand3b_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 3360.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 3360.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1010.0, 610.0), Point(1010.0, 800.0), Point(470.0, 800.0), Point(470.0, 1350.0), Point(3070.0, 1350.0), Point(3070.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(580.0, 2060.0), Point(580.0, 2900.0), Point(1120.0, 2900.0), Point(1120.0, 3180.0), Point(2950.0, 3180.0), Point(2950.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3360.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3360.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2720.0, 2950.0, 2880.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2720.0, 2270.0, 2880.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2210.0, 2610.0, 2370.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2210.0, 2950.0, 2370.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1900.0, 1640.0, 2060.0, 1800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1700.0, 2270.0, 1860.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1700.0, 2610.0, 1860.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2825.0, 1020.0, 2985.0, 1180.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1700.0, 2950.0, 1860.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1410.0, 1640.0, 1570.0, 1800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1190.0, 2270.0, 1350.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1190.0, 2610.0, 1350.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2545.0, 1640.0, 2705.0, 1800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2825.0, 680.0, 2985.0, 840.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1190.0, 2950.0, 1350.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1135.0, 680.0, 1295.0, 840.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(825.0, 1640.0, 985.0, 1800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(650.0, 2330.0, 810.0, 2490.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2720.0, 2610.0, 2880.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(650.0, 2670.0, 810.0, 2830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(540.0, 995.0, 700.0, 1155.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2480.0, 430.0), Point(2480.0, 1570.0), Point(2470.0, 1570.0), Point(2470.0, 1870.0), Point(2480.0, 1870.0), Point(2480.0, 3360.0), Point(2610.0, 3360.0), Point(2610.0, 1870.0), Point(2775.0, 1870.0), Point(2775.0, 1570.0), Point(2610.0, 1570.0), Point(2610.0, 430.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(810.0, 620.0), Point(810.0, 1570.0), Point(755.0, 1570.0), Point(755.0, 1870.0), Point(920.0, 1870.0), Point(920.0, 3080.0), Point(1050.0, 3080.0), Point(1050.0, 1870.0), Point(1055.0, 1870.0), Point(1055.0, 1570.0), Point(940.0, 1570.0), Point(940.0, 620.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1460.0, 430.0), Point(1460.0, 1570.0), Point(1340.0, 1570.0), Point(1340.0, 1870.0), Point(1460.0, 1870.0), Point(1460.0, 3360.0), Point(1590.0, 3360.0), Point(1590.0, 1870.0), Point(1650.0, 1870.0), Point(1650.0, 1570.0), Point(1590.0, 1570.0), Point(1590.0, 430.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1970.0, 430.0), Point(1970.0, 1570.0), Point(1830.0, 1570.0), Point(1830.0, 1870.0), Point(1970.0, 1870.0), Point(1970.0, 3360.0), Point(2100.0, 3360.0), Point(2100.0, 1870.0), Point(2130.0, 1870.0), Point(2130.0, 1570.0), Point(2100.0, 1570.0), Point(2100.0, 430.0)]))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2775.0, 630.0), Point(2775.0, 1230.0), Point(2960.0, 1230.0), Point(2960.0, 2200.0), Point(1650.0, 2200.0), Point(1650.0, 3160.0), Point(1910.0, 3160.0), Point(1910.0, 2390.0), Point(2670.0, 2390.0), Point(2670.0, 3160.0), Point(3130.0, 3160.0), Point(3130.0, 630.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1140.0, 2220.0), Point(1140.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3360.0, 4000.0), Point(3360.0, 3560.0), Point(2420.0, 3560.0), Point(2420.0, 2575.0), Point(2160.0, 2575.0), Point(2160.0, 3560.0), Point(1400.0, 3560.0), Point(1400.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(1080.0, 220.0), Point(1080.0, 890.0), Point(1350.0, 890.0), Point(1350.0, 220.0), Point(3360.0, 220.0), Point(3360.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(440.0, 945.0), Point(440.0, 2880.0), Point(860.0, 2880.0), Point(860.0, 2280.0), Point(610.0, 2280.0), Point(610.0, 1230.0), Point(2430.0, 1230.0), Point(2430.0, 1850.0), Point(2755.0, 1850.0), Point(2755.0, 1590.0), Point(2590.0, 1590.0), Point(2590.0, 1070.0), Point(750.0, 1070.0), Point(750.0, 945.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1320.0, 1475.0, 1620.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1800.0, 1475.0, 2100.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(790.0, 1475.0, 1080.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1800.0, 1475.0, 2100.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1320.0, 1475.0, 1620.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(790.0, 1475.0, 1080.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2670.0, 2200.0, 3130.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3360.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3360.0, 220.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A_N', Point(960.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(2880.0, 2670.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1655.0, 3785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1215.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(2100.0, 1775.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(1510.0, 1770.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3600.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3430.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3430.0, 3600.0)))

    # Ports
    cell.add_port(Port('A_N', 'A_N', tech['Metal1'], Rect.from_lbrt(960.0, 1680.0, 960.0, 1680.0)))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(2880.0, 2670.0, 2880.0, 2670.0), direction='OUTPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1655.0, 3785.0, 1655.0, 3785.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1215.0, 0.0, 1215.0, 0.0), direction='GROUND'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(2100.0, 1775.0, 2100.0, 1775.0), direction='INPUT'))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(1510.0, 1770.0, 1510.0, 1770.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nand3b_1', sg13g2_tech)
    c.write_gds("sg13g2_nand3b_1.gds")
