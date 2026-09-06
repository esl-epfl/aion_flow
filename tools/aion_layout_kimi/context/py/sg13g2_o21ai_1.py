# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_o21ai_1
# ================================================================

"""Generated AION cell for sg13g2_o21ai_1."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(110.0, 2160.0, 2000.0, 3280.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(110.0, 550.0, 2000.0, 1290.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2400.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2400.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(710.0, 620.0, 870.0, 780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(180.0, 960.0, 340.0, 1120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1240.0, 3050.0, 1400.0, 3210.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1240.0, 960.0, 1400.0, 1120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1240.0, 620.0, 1400.0, 780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1770.0, 620.0, 1930.0, 780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(180.0, 3050.0, 340.0, 3210.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(180.0, 620.0, 340.0, 780.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1770.0, 960.0, 1930.0, 1120.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1770.0, 3050.0, 1930.0, 3210.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1240.0, 2370.0, 1400.0, 2530.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1425.0, 1800.0, 1585.0, 1960.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1240.0, 2710.0, 1400.0, 2870.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(180.0, 2370.0, 340.0, 2530.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(180.0, 2710.0, 340.0, 2870.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1770.0, 2710.0, 1930.0, 2870.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(850.0, 1800.0, 1010.0, 1960.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(290.0, 1800.0, 450.0, 1960.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(450.0, 370.0), Point(450.0, 1730.0), Point(220.0, 1730.0), Point(220.0, 2030.0), Point(450.0, 2030.0), Point(450.0, 3460.0), Point(600.0, 3460.0), Point(600.0, 370.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(980.0, 370.0), Point(980.0, 1730.0), Point(780.0, 1730.0), Point(780.0, 2030.0), Point(980.0, 2030.0), Point(980.0, 3460.0), Point(1130.0, 3460.0), Point(1130.0, 370.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1510.0, 1470.0), Point(1510.0, 1730.0), Point(1355.0, 1730.0), Point(1355.0, 2030.0), Point(1510.0, 2030.0), Point(1510.0, 3460.0), Point(1660.0, 3460.0), Point(1660.0, 1470.0)]))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(1510.0, 370.0, 1660.0, 1470.0)))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(660.0, 220.0), Point(660.0, 840.0), Point(920.0, 840.0), Point(920.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(130.0, 2320.0), Point(130.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(390.0, 3560.0), Point(390.0, 2320.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(130.0, 570.0), Point(130.0, 1245.0), Point(1450.0, 1245.0), Point(1450.0, 570.0), Point(1190.0, 570.0), Point(1190.0, 1060.0), Point(390.0, 1060.0), Point(390.0, 570.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1320.0, 1430.0), Point(1320.0, 2010.0), Point(1635.0, 2010.0), Point(1635.0, 1750.0), Point(1560.0, 1750.0), Point(1560.0, 1430.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1720.0, 570.0), Point(1720.0, 1220.0), Point(1870.0, 1220.0), Point(1870.0, 2270.0), Point(1190.0, 2270.0), Point(1190.0, 3260.0), Point(1450.0, 3260.0), Point(1450.0, 2480.0), Point(2090.0, 2480.0), Point(2090.0, 570.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1720.0, 2660.0, 1980.0, 3560.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(240.0, 1430.0, 600.0, 2010.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(800.0, 1430.0, 1080.0, 2010.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1720.0, 570.0, 2090.0, 1220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1320.0, 1430.0, 1560.0, 2010.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(800.0, 1430.0, 1080.0, 2010.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(240.0, 1430.0, 600.0, 2010.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1180.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1275.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(1920.0, 840.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B1', Point(1440.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A2', Point(835.0, 1860.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A1', Point(480.0, 1680.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2690.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2470.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))

    # Ports
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1180.0, 0.0, 1180.0, 0.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1275.0, 3780.0, 1275.0, 3780.0), direction='POWER'))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(1920.0, 840.0, 1920.0, 840.0), direction='OUTPUT'))
    cell.add_port(Port('B1', 'B1', tech['Metal1'], Rect.from_lbrt(1440.0, 1680.0, 1440.0, 1680.0)))
    cell.add_port(Port('A2', 'A2', tech['Metal1'], Rect.from_lbrt(835.0, 1860.0, 835.0, 1860.0)))
    cell.add_port(Port('A1', 'A1', tech['Metal1'], Rect.from_lbrt(480.0, 1680.0, 480.0, 1680.0)))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_o21ai_1', sg13g2_tech)
    c.write_gds("sg13g2_o21ai_1.gds")
