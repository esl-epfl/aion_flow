# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_a22oi_1
# ================================================================

"""Generated AION cell for sg13g2_a22oi_1."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2880.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2880.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(160.0, 480.0, 2720.0, 1220.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(165.0, 2180.0, 2720.0, 3300.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1590.0, 890.0, 1750.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 550.0, 2650.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1360.0, 2690.0, 1520.0, 2850.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 890.0, 2650.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 2350.0, 2650.0, 2510.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 2730.0, 2650.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 3070.0, 2650.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 1840.0, 2650.0, 2000.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1870.0, 2730.0, 2030.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1870.0, 3070.0, 2030.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1840.0, 1360.0, 2000.0, 1520.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1250.0, 890.0, 1410.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1360.0, 2350.0, 1520.0, 2510.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1840.0, 1840.0, 2000.0, 2000.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1020.0, 1860.0, 1180.0, 2020.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(850.0, 2730.0, 1010.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(850.0, 3070.0, 1010.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(240.0, 1880.0, 400.0, 2040.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(230.0, 550.0, 390.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(230.0, 890.0, 390.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(235.0, 2350.0, 395.0, 2510.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(235.0, 2730.0, 395.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(235.0, 3070.0, 395.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(505.0, 300.0), Point(505.0, 1630.0), Point(700.0, 1630.0), Point(700.0, 1750.0), Point(950.0, 1750.0), Point(950.0, 2090.0), Point(1120.0, 2090.0), Point(1120.0, 3480.0), Point(1250.0, 3480.0), Point(1250.0, 1610.0), Point(830.0, 1610.0), Point(830.0, 1490.0), Point(635.0, 1490.0), Point(635.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2250.0, 300.0), Point(2250.0, 3480.0), Point(2380.0, 3480.0), Point(2380.0, 2070.0), Point(2720.0, 2070.0), Point(2720.0, 1770.0), Point(2380.0, 1770.0), Point(2380.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1860.0, 300.0), Point(1860.0, 1290.0), Point(1770.0, 1290.0), Point(1770.0, 1590.0), Point(2070.0, 1590.0), Point(2070.0, 1290.0), Point(1990.0, 1290.0), Point(1990.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(170.0, 1810.0), Point(170.0, 2110.0), Point(505.0, 2110.0), Point(505.0, 3480.0), Point(635.0, 3480.0), Point(635.0, 1980.0), Point(475.0, 1980.0), Point(475.0, 1810.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1010.0, 300.0), Point(1010.0, 1430.0), Point(1430.0, 1430.0), Point(1430.0, 1900.0), Point(1630.0, 1900.0), Point(1630.0, 3480.0), Point(1760.0, 3480.0), Point(1760.0, 2070.0), Point(2070.0, 2070.0), Point(2070.0, 1770.0), Point(1560.0, 1770.0), Point(1560.0, 1290.0), Point(1140.0, 1290.0), Point(1140.0, 300.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1310.0, 2300.0, 1600.0, 2900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(820.0, 1785.0, 1115.0, 2255.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2270.0, 1330.0, 2720.0, 2070.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1780.0, 1770.0, 2080.0, 2440.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2880.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(170.0, 1560.0, 640.0, 2070.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2880.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1250.0, 840.0), Point(1250.0, 1100.0), Point(1420.0, 1100.0), Point(1420.0, 2300.0), Point(1310.0, 2300.0), Point(1310.0, 2900.0), Point(1600.0, 2900.0), Point(1600.0, 1100.0), Point(1750.0, 1100.0), Point(1750.0, 840.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(820.0, 1785.0), Point(820.0, 2255.0), Point(1115.0, 2255.0), Point(1115.0, 2070.0), Point(1240.0, 2070.0), Point(1240.0, 1785.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(800.0, 2680.0), Point(800.0, 3280.0), Point(2080.0, 3280.0), Point(2080.0, 2680.0), Point(1820.0, 2680.0), Point(1820.0, 3085.0), Point(1060.0, 3085.0), Point(1060.0, 2680.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(180.0, 220.0), Point(180.0, 1100.0), Point(440.0, 1100.0), Point(440.0, 220.0), Point(2440.0, 220.0), Point(2440.0, 1100.0), Point(2700.0, 1100.0), Point(2700.0, 220.0), Point(2880.0, 220.0), Point(2880.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(620.0, 480.0), Point(620.0, 1330.0), Point(420.0, 1330.0), Point(420.0, 1560.0), Point(170.0, 1560.0), Point(170.0, 2070.0), Point(640.0, 2070.0), Point(640.0, 1490.0), Point(780.0, 1490.0), Point(780.0, 640.0), Point(1930.0, 640.0), Point(1930.0, 1330.0), Point(1790.0, 1330.0), Point(1790.0, 1560.0), Point(2090.0, 1560.0), Point(2090.0, 480.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(180.0, 2300.0), Point(180.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2880.0, 4000.0), Point(2880.0, 3560.0), Point(2700.0, 3560.0), Point(2700.0, 2300.0), Point(2440.0, 2300.0), Point(2440.0, 3560.0), Point(450.0, 3560.0), Point(450.0, 2300.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2270.0, 1330.0, 2720.0, 2070.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1780.0, 1770.0, 2080.0, 2440.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(1440.0, 2520.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A2', Point(2570.0, 1925.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1390.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B1', Point(965.0, 2095.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A1', Point(315.0, 1920.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1320.0, -20.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B2', Point(1930.0, 1920.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3120.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2950.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2950.0, 180.0)))

    # Ports
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(1440.0, 2520.0, 1440.0, 2520.0), direction='OUTPUT'))
    cell.add_port(Port('A2', 'A2', tech['Metal1'], Rect.from_lbrt(2570.0, 1925.0, 2570.0, 1925.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1390.0, 3780.0, 1390.0, 3780.0), direction='POWER'))
    cell.add_port(Port('B1', 'B1', tech['Metal1'], Rect.from_lbrt(965.0, 2095.0, 965.0, 2095.0)))
    cell.add_port(Port('A1', 'A1', tech['Metal1'], Rect.from_lbrt(315.0, 1920.0, 315.0, 1920.0)))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1320.0, -20.0, 1320.0, -20.0), direction='GROUND'))
    cell.add_port(Port('B2', 'B2', tech['Metal1'], Rect.from_lbrt(1930.0, 1920.0, 1930.0, 1920.0)))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_a22oi_1', sg13g2_tech)
    c.write_gds("sg13g2_a22oi_1.gds")
