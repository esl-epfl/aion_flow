# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_buf_1
# ================================================================

"""Generated AION cell for sg13g2_buf_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(740.0, 570.0), Point(740.0, 760.0), Point(200.0, 760.0), Point(200.0, 1310.0), Point(1610.0, 1310.0), Point(1610.0, 570.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(840.0, 2060.0), Point(840.0, 2340.0), Point(200.0, 2340.0), Point(200.0, 3180.0), Point(1595.0, 3180.0), Point(1595.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 1920.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 1920.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(270.0, 2610.0, 430.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(270.0, 2950.0, 430.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(990.0, 1585.0, 1150.0, 1745.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1380.0, 650.0, 1540.0, 810.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1380.0, 1065.0, 1540.0, 1225.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1365.0, 2950.0, 1525.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1365.0, 2270.0, 1525.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(820.0, 2950.0, 980.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(435.0, 2000.0, 595.0, 2160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(820.0, 850.0, 980.0, 1010.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1365.0, 2610.0, 1525.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(270.0, 1075.0, 430.0, 1235.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1090.0, 390.0), Point(1090.0, 1500.0), Point(920.0, 1500.0), Point(920.0, 1830.0), Point(1090.0, 1830.0), Point(1090.0, 3360.0), Point(1220.0, 3360.0), Point(1220.0, 390.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(540.0, 580.0), Point(540.0, 1930.0), Point(365.0, 1930.0), Point(365.0, 2230.0), Point(540.0, 2230.0), Point(540.0, 3360.0), Point(670.0, 3360.0), Point(670.0, 580.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(285.0, 1930.0, 680.0, 2260.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1315.0, 2070.0, 1580.0, 2945.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 1920.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 1920.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1315.0, 2070.0, 1580.0, 2945.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(215.0, 1000.0), Point(215.0, 1465.0), Point(900.0, 1465.0), Point(900.0, 2440.0), Point(240.0, 2440.0), Point(240.0, 3180.0), Point(510.0, 3180.0), Point(510.0, 2620.0), Point(1070.0, 2620.0), Point(1070.0, 1830.0), Point(1225.0, 1830.0), Point(1225.0, 1500.0), Point(1070.0, 1500.0), Point(1070.0, 1290.0), Point(515.0, 1290.0), Point(515.0, 1000.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1310.0, 550.0), Point(1310.0, 1290.0), Point(1410.0, 1290.0), Point(1410.0, 2020.0), Point(1300.0, 2020.0), Point(1300.0, 3180.0), Point(1600.0, 3180.0), Point(1600.0, 550.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(765.0, 220.0), Point(765.0, 1070.0), Point(1015.0, 1070.0), Point(1015.0, 220.0), Point(1920.0, 220.0), Point(1920.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(770.0, 2890.0), Point(770.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(1920.0, 4000.0), Point(1920.0, 3560.0), Point(1030.0, 3560.0), Point(1030.0, 2890.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(285.0, 1930.0, 680.0, 2260.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(1450.0, 2510.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(530.0, 2100.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(980.0, -10.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1070.0, 3830.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2160.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-65.0, -180.0, 1990.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-65.0, 1760.0, 1990.0, 3600.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(1450.0, 2510.0, 1450.0, 2510.0)))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(530.0, 2100.0, 530.0, 2100.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(980.0, -10.0, 980.0, -10.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1070.0, 3830.0, 1070.0, 3830.0), direction='POWER'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_buf_1', sg13g2_tech)
    c.write_gds("sg13g2_buf_1.gds")
