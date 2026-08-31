# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nand2_1
# ================================================================

"""Generated AION cell for sg13g2_nand2_1."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(300.0, 590.0, 1620.0, 1330.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(300.0, 2060.0, 1620.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 1920.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 1920.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 1065.0, 530.0, 1225.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1390.0, 1065.0, 1550.0, 1225.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1330.0, 1525.0, 1490.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(400.0, 1525.0, 560.0, 1685.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(880.0, 2950.0, 1040.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(880.0, 2540.0, 1040.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(880.0, 2130.0, 1040.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1390.0, 670.0, 1550.0, 830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 670.0, 530.0, 830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 2950.0, 530.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 2540.0, 530.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 2130.0, 530.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1390.0, 2950.0, 1550.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1390.0, 2540.0, 1550.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1390.0, 2130.0, 1550.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(640.0, 410.0), Point(640.0, 1455.0), Point(330.0, 1455.0), Point(330.0, 1755.0), Point(640.0, 1755.0), Point(640.0, 3360.0), Point(770.0, 3360.0), Point(770.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1150.0, 410.0), Point(1150.0, 3360.0), Point(1280.0, 3360.0), Point(1280.0, 1755.0), Point(1560.0, 1755.0), Point(1560.0, 1455.0), Point(1280.0, 1455.0), Point(1280.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1270.0, 1470.0, 1600.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 1920.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 1920.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(830.0, 1365.0, 1090.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(330.0, 1470.0, 620.0, 1900.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(320.0, 2080.0), Point(320.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(1920.0, 4000.0), Point(1920.0, 3560.0), Point(1600.0, 3560.0), Point(1600.0, 2080.0), Point(1340.0, 2080.0), Point(1340.0, 3560.0), Point(580.0, 3560.0), Point(580.0, 2080.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(320.0, 220.0), Point(320.0, 1275.0), Point(580.0, 1275.0), Point(580.0, 220.0), Point(1920.0, 220.0), Point(1920.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1340.0, 620.0), Point(1340.0, 1060.0), Point(830.0, 1060.0), Point(830.0, 3160.0), Point(1090.0, 3160.0), Point(1090.0, 1245.0), Point(1600.0, 1245.0), Point(1600.0, 620.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1270.0, 1470.0, 1600.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(330.0, 1470.0, 620.0, 1900.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(970.0, 2210.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(970.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(1435.0, 1630.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(990.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(450.0, 1620.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2160.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 1990.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 1990.0, 180.0)))

    # Ports
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(970.0, 2210.0, 970.0, 2210.0), direction='OUTPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(970.0, 3780.0, 970.0, 3780.0), direction='POWER'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(1435.0, 1630.0, 1435.0, 1630.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(990.0, 0.0, 990.0, 0.0), direction='GROUND'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(450.0, 1620.0, 450.0, 1620.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nand2_1', sg13g2_tech)
    c.write_gds("sg13g2_nand2_1.gds")
