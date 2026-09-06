# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nor2_1
# ================================================================

"""Generated AION cell for sg13g2_nor2_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 1920.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 1920.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(360.0, 2060.0, 1530.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(380.0, 590.0, 1700.0, 1330.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 1920.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 1920.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1295.0, 1605.0, 1455.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(435.0, 1605.0, 595.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(960.0, 1000.0, 1120.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(960.0, 660.0, 1120.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1300.0, 2950.0, 1460.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1300.0, 2610.0, 1460.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1300.0, 2270.0, 1460.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(450.0, 1000.0, 610.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(450.0, 660.0, 610.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1470.0, 1000.0, 1630.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1470.0, 660.0, 1630.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(450.0, 2950.0, 610.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(450.0, 2610.0, 610.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(450.0, 2270.0, 610.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1230.0, 410.0), Point(1230.0, 1520.0), Point(1060.0, 1520.0), Point(1060.0, 3360.0), Point(1190.0, 3360.0), Point(1190.0, 1850.0), Point(1540.0, 1850.0), Point(1540.0, 1520.0), Point(1360.0, 1520.0), Point(1360.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(720.0, 410.0), Point(720.0, 1520.0), Point(350.0, 1520.0), Point(350.0, 1850.0), Point(720.0, 1850.0), Point(720.0, 3360.0), Point(850.0, 3360.0), Point(850.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1245.0, 1520.0, 1580.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(350.0, 1520.0, 680.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 1920.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1250.0, 2235.0, 1570.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 1920.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(870.0, 605.0), Point(870.0, 2435.0), Point(1250.0, 2435.0), Point(1250.0, 3160.0), Point(1570.0, 3160.0), Point(1570.0, 2235.0), Point(1040.0, 2235.0), Point(1040.0, 1210.0), Point(1170.0, 1210.0), Point(1170.0, 605.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(400.0, 2220.0), Point(400.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(1920.0, 4000.0), Point(1920.0, 3560.0), Point(660.0, 3560.0), Point(660.0, 2220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(400.0, 220.0), Point(400.0, 1210.0), Point(660.0, 1210.0), Point(660.0, 220.0), Point(1420.0, 220.0), Point(1420.0, 1210.0), Point(1680.0, 1210.0), Point(1680.0, 220.0), Point(1920.0, 220.0), Point(1920.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(350.0, 1520.0, 680.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1245.0, 1520.0, 1580.0, 1850.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(520.0, 1765.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(985.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(1440.0, 2520.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(995.0, 5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(1380.0, 1760.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2160.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 1990.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 1990.0, 180.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(520.0, 1765.0, 520.0, 1765.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(985.0, 3780.0, 985.0, 3780.0), direction='POWER'))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(1440.0, 2520.0, 1440.0, 2520.0), direction='OUTPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(995.0, 5.0, 995.0, 5.0), direction='GROUND'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(1380.0, 1760.0, 1380.0, 1760.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nor2_1', sg13g2_tech)
    c.write_gds("sg13g2_nor2_1.gds")
