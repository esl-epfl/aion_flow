# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nand2b_2
# ================================================================

"""Generated AION cell for sg13g2_nand2b_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 3840.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 3840.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3840.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3840.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1130.0, 2060.0, 3510.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1130.0, 575.0, 3500.0, 1295.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(110.0, 745.0, 920.0, 1295.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(110.0, 2060.0, 920.0, 2900.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2240.0, 2610.0, 2400.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 2610.0, 3430.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 2950.0, 3430.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 650.0, 3430.0, 810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2760.0, 1050.0, 2920.0, 1210.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2760.0, 2270.0, 2920.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2760.0, 2610.0, 2920.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2760.0, 2950.0, 2920.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2380.0, 1635.0, 2540.0, 1795.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2240.0, 660.0, 2400.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2240.0, 1005.0, 2400.0, 1165.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2240.0, 2950.0, 2400.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1730.0, 645.0, 1890.0, 805.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1730.0, 2270.0, 1890.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1730.0, 2610.0, 1890.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1730.0, 2950.0, 1890.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1260.0, 1635.0, 1420.0, 1795.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1210.0, 650.0, 1370.0, 810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1205.0, 990.0, 1365.0, 1150.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1200.0, 2270.0, 1360.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1200.0, 2610.0, 1360.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1200.0, 2950.0, 1360.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(690.0, 1065.0, 850.0, 1225.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(690.0, 2330.0, 850.0, 2490.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(690.0, 2670.0, 850.0, 2830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(400.0, 1600.0, 560.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(180.0, 1065.0, 340.0, 1225.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(180.0, 2330.0, 340.0, 2490.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(180.0, 2670.0, 340.0, 2830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 2270.0, 3430.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 990.0, 3430.0, 1150.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1490.0, 395.0), Point(1490.0, 1565.0), Point(1190.0, 1565.0), Point(1190.0, 1865.0), Point(1490.0, 1865.0), Point(1490.0, 3360.0), Point(1620.0, 3360.0), Point(1620.0, 1795.0), Point(2000.0, 1795.0), Point(2000.0, 3360.0), Point(2130.0, 3360.0), Point(2130.0, 395.0), Point(2000.0, 395.0), Point(2000.0, 1565.0), Point(1620.0, 1565.0), Point(1620.0, 395.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(450.0, 565.0), Point(450.0, 1530.0), Point(330.0, 1530.0), Point(330.0, 1830.0), Point(450.0, 1830.0), Point(450.0, 3080.0), Point(580.0, 3080.0), Point(580.0, 1830.0), Point(630.0, 1830.0), Point(630.0, 1530.0), Point(580.0, 1530.0), Point(580.0, 565.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2520.0, 395.0), Point(2520.0, 1565.0), Point(2310.0, 1565.0), Point(2310.0, 1865.0), Point(2520.0, 1865.0), Point(2520.0, 3360.0), Point(2650.0, 3360.0), Point(2650.0, 1795.0), Point(3030.0, 1795.0), Point(3030.0, 3360.0), Point(3160.0, 3360.0), Point(3160.0, 395.0), Point(3030.0, 395.0), Point(3030.0, 1565.0), Point(2650.0, 1565.0), Point(2650.0, 395.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2160.0, 1535.0, 2590.0, 1845.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2710.0, 2200.0, 3000.0, 3180.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(155.0, 1475.0, 610.0, 1865.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2180.0, 530.0), Point(2180.0, 1035.0), Point(1415.0, 1035.0), Point(1415.0, 600.0), Point(1155.0, 600.0), Point(1155.0, 1200.0), Point(2450.0, 1200.0), Point(2450.0, 760.0), Point(3200.0, 760.0), Point(3200.0, 1200.0), Point(3480.0, 1200.0), Point(3480.0, 530.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2710.0, 1000.0), Point(2710.0, 1390.0), Point(2770.0, 1390.0), Point(2770.0, 2200.0), Point(1680.0, 2200.0), Point(1680.0, 3160.0), Point(1940.0, 3160.0), Point(1940.0, 2360.0), Point(2710.0, 2360.0), Point(2710.0, 3180.0), Point(3000.0, 3180.0), Point(3000.0, 1000.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(130.0, 220.0), Point(130.0, 1275.0), Point(390.0, 1275.0), Point(390.0, 220.0), Point(1680.0, 220.0), Point(1680.0, 855.0), Point(1940.0, 855.0), Point(1940.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(640.0, 1015.0), Point(640.0, 1275.0), Point(805.0, 1275.0), Point(805.0, 2210.0), Point(640.0, 2210.0), Point(640.0, 2880.0), Point(900.0, 2880.0), Point(900.0, 2340.0), Point(965.0, 2340.0), Point(965.0, 1845.0), Point(1470.0, 1845.0), Point(1470.0, 1585.0), Point(965.0, 1585.0), Point(965.0, 1015.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1150.0, 2125.0), Point(1150.0, 3560.0), Point(390.0, 3560.0), Point(390.0, 2280.0), Point(130.0, 2280.0), Point(130.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(3480.0, 3560.0), Point(3480.0, 2220.0), Point(3220.0, 2220.0), Point(3220.0, 3560.0), Point(2450.0, 3560.0), Point(2450.0, 2560.0), Point(2190.0, 2560.0), Point(2190.0, 3560.0), Point(1410.0, 3560.0), Point(1410.0, 2125.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2160.0, 1535.0, 2590.0, 1845.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(155.0, 1475.0, 610.0, 1865.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A_N', Point(410.0, 1690.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(2860.0, 2500.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(970.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(510.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(2230.0, 1765.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3910.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3910.0, 3600.0)))

    # Ports
    cell.add_port(Port('A_N', 'A_N', tech['Metal1'], Rect.from_lbrt(410.0, 1690.0, 410.0, 1690.0)))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(2860.0, 2500.0, 2860.0, 2500.0), direction='OUTPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(970.0, 3780.0, 970.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(510.0, 0.0, 510.0, 0.0), direction='GROUND'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(2230.0, 1765.0, 2230.0, 1765.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nand2b_2', sg13g2_tech)
    c.write_gds("sg13g2_nand2b_2.gds")
