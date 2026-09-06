# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nor3_1
# ================================================================

"""Generated AION cell for sg13g2_nor3_1."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2400.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(355.0, 600.0, 2245.0, 1370.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(355.0, 2060.0, 2245.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2400.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1845.0, 1620.0, 2005.0, 1780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2015.0, 2270.0, 2175.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2015.0, 2610.0, 2175.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2015.0, 2950.0, 2175.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2015.0, 670.0, 2175.0, 830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2015.0, 1010.0, 2175.0, 1170.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1505.0, 670.0, 1665.0, 830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1335.0, 1620.0, 1495.0, 1780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(995.0, 670.0, 1155.0, 830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(995.0, 1010.0, 1155.0, 1170.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(425.0, 670.0, 585.0, 830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(425.0, 1010.0, 585.0, 1170.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(425.0, 1620.0, 585.0, 1780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(425.0, 2270.0, 585.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(425.0, 2610.0, 585.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(425.0, 2950.0, 585.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1775.0, 300.0), Point(1775.0, 3360.0), Point(1905.0, 3360.0), Point(1905.0, 1850.0), Point(2075.0, 1850.0), Point(2075.0, 1550.0), Point(1905.0, 1550.0), Point(1905.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(695.0, 300.0), Point(695.0, 1550.0), Point(355.0, 1550.0), Point(355.0, 1850.0), Point(695.0, 1850.0), Point(695.0, 3360.0), Point(825.0, 3360.0), Point(825.0, 300.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1265.0, 300.0), Point(1265.0, 3360.0), Point(1395.0, 3360.0), Point(1395.0, 1850.0), Point(1565.0, 1850.0), Point(1565.0, 1550.0), Point(1395.0, 1550.0), Point(1395.0, 300.0)]))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(375.0, 220.0), Point(375.0, 1220.0), Point(635.0, 1220.0), Point(635.0, 220.0), Point(1455.0, 220.0), Point(1455.0, 880.0), Point(1715.0, 880.0), Point(1715.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(375.0, 2205.0), Point(375.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(635.0, 3560.0), Point(635.0, 2205.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(945.0, 620.0), Point(945.0, 2665.0), Point(1965.0, 2665.0), Point(1965.0, 3130.0), Point(2225.0, 3130.0), Point(2225.0, 2220.0), Point(1965.0, 2220.0), Point(1965.0, 2380.0), Point(1120.0, 2380.0), Point(1120.0, 1220.0), Point(2225.0, 1220.0), Point(2225.0, 620.0), Point(1965.0, 620.0), Point(1965.0, 1060.0), Point(1205.0, 1060.0), Point(1205.0, 620.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1780.0, 1515.0, 2060.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1300.0, 1515.0, 1580.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(340.0, 1515.0, 620.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1300.0, 1515.0, 1580.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1780.0, 1515.0, 2060.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(960.0, 2380.0, 2225.0, 2665.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(340.0, 1515.0, 620.0, 1850.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(480.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(1440.0, 2515.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(1440.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(1940.0, 1740.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1240.0, 3785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1215.0, 0.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2640.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2470.0, 3600.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(480.0, 1680.0, 480.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(1440.0, 2515.0, 1440.0, 2515.0), direction='OUTPUT'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(1440.0, 1680.0, 1440.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(1940.0, 1740.0, 1940.0, 1740.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1240.0, 3785.0, 1240.0, 3785.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1215.0, 0.0, 1215.0, 0.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nor3_1', sg13g2_tech)
    c.write_gds("sg13g2_nor3_1.gds")
