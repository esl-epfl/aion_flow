# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_and2_1
# ================================================================

"""Generated AION cell for sg13g2_and2_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1355.0, 700.0), Point(1355.0, 800.0), Point(225.0, 800.0), Point(225.0, 1440.0), Point(2055.0, 1440.0), Point(2055.0, 700.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1355.0, 2060.0), Point(1355.0, 2340.0), Point(225.0, 2340.0), Point(225.0, 3180.0), Point(2055.0, 3180.0), Point(2055.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2400.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2400.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(295.0, 2950.0, 455.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1825.0, 770.0, 1985.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1530.0, 1655.0, 1690.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(530.0, 480.0, 690.0, 640.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(190.0, 480.0, 350.0, 640.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(960.0, 1655.0, 1120.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1825.0, 2950.0, 1985.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1825.0, 2610.0, 1985.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1825.0, 2270.0, 1985.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(295.0, 1180.0, 455.0, 1340.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1315.0, 910.0, 1475.0, 1070.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1825.0, 1110.0, 1985.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(295.0, 2610.0, 455.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(805.0, 2950.0, 965.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(805.0, 2610.0, 965.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1315.0, 2950.0, 1475.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1315.0, 2610.0, 1475.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1585.0, 520.0), Point(1585.0, 1585.0), Point(1455.0, 1585.0), Point(1455.0, 1885.0), Point(1585.0, 1885.0), Point(1585.0, 3360.0), Point(1715.0, 3360.0), Point(1715.0, 1885.0), Point(1760.0, 1885.0), Point(1760.0, 1585.0), Point(1715.0, 1585.0), Point(1715.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(105.0, 410.0), Point(105.0, 730.0), Point(565.0, 730.0), Point(565.0, 3360.0), Point(695.0, 3360.0), Point(695.0, 730.0), Point(775.0, 730.0), Point(775.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1075.0, 620.0), Point(1075.0, 1585.0), Point(890.0, 1585.0), Point(890.0, 1885.0), Point(1075.0, 1885.0), Point(1075.0, 3360.0), Point(1205.0, 3360.0), Point(1205.0, 620.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1775.0, 2140.0, 2275.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(780.0, 1435.0, 1170.0, 1870.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(105.0, 405.0, 780.0, 960.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(245.0, 1140.0), Point(245.0, 2240.0), Point(755.0, 2240.0), Point(755.0, 3160.0), Point(1015.0, 3160.0), Point(1015.0, 2240.0), Point(1560.0, 2240.0), Point(1560.0, 1865.0), Point(1740.0, 1865.0), Point(1740.0, 1605.0), Point(1400.0, 1605.0), Point(1400.0, 2050.0), Point(505.0, 2050.0), Point(505.0, 1140.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1775.0, 720.0), Point(1775.0, 1320.0), Point(2040.0, 1320.0), Point(2040.0, 2140.0), Point(1775.0, 2140.0), Point(1775.0, 3160.0), Point(2275.0, 3160.0), Point(2275.0, 720.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(245.0, 2560.0), Point(245.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(1525.0, 3560.0), Point(1525.0, 2560.0), Point(1265.0, 2560.0), Point(1265.0, 3560.0), Point(505.0, 3560.0), Point(505.0, 2560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(1265.0, 220.0), Point(1265.0, 1155.0), Point(1525.0, 1155.0), Point(1525.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(780.0, 1435.0, 1170.0, 1870.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(105.0, 405.0, 780.0, 960.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(1995.0, 2680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1180.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1275.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(980.0, 1655.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(465.0, 745.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2640.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 550.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2470.0, 3600.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(1995.0, 2680.0, 1995.0, 2680.0)))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1180.0, 0.0, 1180.0, 0.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1275.0, 3780.0, 1275.0, 3780.0), direction='POWER'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(980.0, 1655.0, 980.0, 1655.0), direction='INPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(465.0, 745.0, 465.0, 745.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_and2_1', sg13g2_tech)
    c.write_gds("sg13g2_and2_1.gds")
