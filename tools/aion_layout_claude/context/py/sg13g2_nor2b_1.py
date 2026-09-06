# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nor2b_1
# ================================================================

"""Generated AION cell for sg13g2_nor2b_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 2400.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 2400.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(870.0, 590.0), Point(870.0, 780.0), Point(230.0, 780.0), Point(230.0, 1330.0), Point(2190.0, 1330.0), Point(2190.0, 590.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(230.0, 2060.0), Point(230.0, 2900.0), Point(870.0, 2900.0), Point(870.0, 3180.0), Point(2020.0, 3180.0), Point(2020.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2400.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2400.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1960.0, 660.0, 2120.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1960.0, 1100.0, 2120.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1790.0, 2255.0, 1950.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1790.0, 2605.0, 1950.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1790.0, 2950.0, 1950.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1785.0, 1550.0, 1945.0, 1710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1450.0, 660.0, 1610.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1450.0, 1100.0, 1610.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(950.0, 1550.0, 1110.0, 1710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(940.0, 660.0, 1100.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(940.0, 2605.0, 1100.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(940.0, 2950.0, 1100.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(340.0, 1550.0, 500.0, 1710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 1100.0, 460.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 2330.0, 460.0, 2490.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 2670.0, 460.0, 2830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(570.0, 600.0), Point(570.0, 1480.0), Point(270.0, 1480.0), Point(270.0, 1780.0), Point(570.0, 1780.0), Point(570.0, 3080.0), Point(700.0, 3080.0), Point(700.0, 600.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1210.0, 410.0), Point(1210.0, 1480.0), Point(880.0, 1480.0), Point(880.0, 1780.0), Point(1210.0, 1780.0), Point(1210.0, 3360.0), Point(1340.0, 3360.0), Point(1340.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1720.0, 410.0), Point(1720.0, 1480.0), Point(1550.0, 1480.0), Point(1550.0, 3360.0), Point(1680.0, 3360.0), Point(1680.0, 1780.0), Point(2030.0, 1780.0), Point(2030.0, 1480.0), Point(1850.0, 1480.0), Point(1850.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1730.0, 1500.0, 2060.0, 1870.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(270.0, 1500.0, 620.0, 1870.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1730.0, 2235.0, 2060.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1360.0, 605.0), Point(1360.0, 2435.0), Point(1730.0, 2435.0), Point(1730.0, 3160.0), Point(2060.0, 3160.0), Point(2060.0, 2235.0), Point(1530.0, 2235.0), Point(1530.0, 1310.0), Point(1625.0, 1310.0), Point(1625.0, 605.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(250.0, 1050.0), Point(250.0, 1310.0), Point(890.0, 1310.0), Point(890.0, 2080.0), Point(250.0, 2080.0), Point(250.0, 2880.0), Point(510.0, 2880.0), Point(510.0, 2260.0), Point(1150.0, 2260.0), Point(1150.0, 1050.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(890.0, 220.0), Point(890.0, 870.0), Point(1150.0, 870.0), Point(1150.0, 220.0), Point(1910.0, 220.0), Point(1910.0, 1310.0), Point(2170.0, 1310.0), Point(2170.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(890.0, 2555.0), Point(890.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(1150.0, 3560.0), Point(1150.0, 2555.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1730.0, 1500.0, 2060.0, 1870.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(270.0, 1500.0, 620.0, 1870.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(1920.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B_N', Point(480.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(985.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(1920.0, 2520.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(995.0, 5.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-270.0, 1750.0, 2640.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-100.0, 1760.0, 2470.0, 3600.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(1920.0, 1680.0, 1920.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('B_N', 'B_N', tech['Metal1'], Rect.from_lbrt(480.0, 1680.0, 480.0, 1680.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(985.0, 3780.0, 985.0, 3780.0), direction='POWER'))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(1920.0, 2520.0, 1920.0, 2520.0), direction='OUTPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(995.0, 5.0, 995.0, 5.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nor2b_1', sg13g2_tech)
    c.write_gds("sg13g2_nor2b_1.gds")
