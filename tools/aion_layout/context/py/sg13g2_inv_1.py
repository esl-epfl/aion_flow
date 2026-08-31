# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_inv_1
# ================================================================

"""Generated AION cell for sg13g2_inv_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 1440.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 1440.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 1440.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 1440.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(310.0, 590.0, 1120.0, 1330.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(310.0, 2075.0, 1120.0, 3195.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(395.0, 1605.0, 555.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(890.0, 1000.0, 1050.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(890.0, 660.0, 1050.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(890.0, 2965.0, 1050.0, 3125.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(890.0, 2625.0, 1050.0, 2785.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(890.0, 2285.0, 1050.0, 2445.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(380.0, 1000.0, 540.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(380.0, 660.0, 540.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(380.0, 2965.0, 540.0, 3125.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(380.0, 2625.0, 540.0, 2785.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(380.0, 2285.0, 540.0, 2445.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(650.0, 410.0), Point(650.0, 1520.0), Point(310.0, 1520.0), Point(310.0, 1850.0), Point(650.0, 1850.0), Point(650.0, 3375.0), Point(780.0, 3375.0), Point(780.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(310.0, 1520.0, 625.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(855.0, 610.0, 1085.0, 3175.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 1440.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 1440.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(330.0, 2235.0), Point(330.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(1440.0, 4000.0), Point(1440.0, 3560.0), Point(590.0, 3560.0), Point(590.0, 2235.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(330.0, 220.0), Point(330.0, 1210.0), Point(590.0, 1210.0), Point(590.0, 220.0), Point(1440.0, 220.0), Point(1440.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(310.0, 1520.0, 625.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(855.0, 610.0, 1085.0, 3175.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(980.0, 1690.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(480.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(720.0, -20.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(705.0, 3780.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 1680.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 1510.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 1510.0, 3600.0)))

    # Ports
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(980.0, 1690.0, 980.0, 1690.0), direction='OUTPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(480.0, 1680.0, 480.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(720.0, -20.0, 720.0, -20.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(705.0, 3780.0, 705.0, 3780.0), direction='POWER'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_inv_1', sg13g2_tech)
    c.write_gds("sg13g2_inv_1.gds")
