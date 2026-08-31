# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nand2b_1
# ================================================================

"""Generated AION cell for sg13g2_nand2b_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(135.0, 2060.0), Point(135.0, 2900.0), Point(675.0, 2900.0), Point(675.0, 3180.0), Point(1995.0, 3180.0), Point(1995.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(675.0, 590.0), Point(675.0, 780.0), Point(135.0, 780.0), Point(135.0, 1330.0), Point(2105.0, 1330.0), Point(2105.0, 590.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2400.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2400.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(745.0, 710.0, 905.0, 870.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(745.0, 2950.0, 905.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1595.0, 1600.0, 1755.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(975.0, 1600.0, 1135.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(375.0, 1600.0, 535.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1875.0, 1100.0, 2035.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1875.0, 660.0, 2035.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(205.0, 2670.0, 365.0, 2830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(205.0, 2330.0, 365.0, 2490.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(745.0, 2590.0, 905.0, 2750.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1765.0, 2950.0, 1925.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(205.0, 970.0, 365.0, 1130.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1255.0, 2950.0, 1415.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1255.0, 2590.0, 1415.0, 2750.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1525.0, 410.0), Point(1525.0, 3360.0), Point(1655.0, 3360.0), Point(1655.0, 1830.0), Point(1935.0, 1830.0), Point(1935.0, 1520.0), Point(1655.0, 1520.0), Point(1655.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1015.0, 410.0), Point(1015.0, 1520.0), Point(905.0, 1520.0), Point(905.0, 1830.0), Point(1015.0, 1830.0), Point(1015.0, 3360.0), Point(1145.0, 3360.0), Point(1145.0, 1830.0), Point(1205.0, 1830.0), Point(1205.0, 1520.0), Point(1145.0, 1520.0), Point(1145.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(475.0, 600.0), Point(475.0, 1520.0), Point(305.0, 1520.0), Point(305.0, 1850.0), Point(475.0, 1850.0), Point(475.0, 3080.0), Point(605.0, 3080.0), Point(605.0, 600.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(840.0, 1530.0, 1205.0, 1835.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1745.0, 610.0, 2160.0, 1315.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(295.0, 1530.0, 600.0, 1835.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(155.0, 920.0), Point(155.0, 1350.0), Point(1385.0, 1350.0), Point(1385.0, 2170.0), Point(155.0, 2170.0), Point(155.0, 2880.0), Point(415.0, 2880.0), Point(415.0, 2355.0), Point(1545.0, 2355.0), Point(1545.0, 1830.0), Point(1805.0, 1830.0), Point(1805.0, 1520.0), Point(1545.0, 1520.0), Point(1545.0, 1190.0), Point(415.0, 1190.0), Point(415.0, 920.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1745.0, 610.0), Point(1745.0, 1315.0), Point(2000.0, 1315.0), Point(2000.0, 2540.0), Point(1205.0, 2540.0), Point(1205.0, 3160.0), Point(1465.0, 3160.0), Point(1465.0, 2700.0), Point(2160.0, 2700.0), Point(2160.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(690.0, 220.0), Point(690.0, 940.0), Point(960.0, 940.0), Point(960.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(695.0, 2540.0), Point(695.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(1975.0, 3560.0), Point(1975.0, 2900.0), Point(1715.0, 2900.0), Point(1715.0, 3560.0), Point(955.0, 3560.0), Point(955.0, 2540.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(840.0, 1530.0, 1205.0, 1835.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(195.0, 1530.0, 600.0, 1835.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(685.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A_N', Point(480.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(1920.0, 840.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(1065.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1235.0, 3780.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2640.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2470.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))

    # Ports
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(685.0, 0.0, 685.0, 0.0), direction='GROUND'))
    cell.add_port(Port('A_N', 'A_N', tech['Metal1'], Rect.from_lbrt(480.0, 1680.0, 480.0, 1680.0)))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(1920.0, 840.0, 1920.0, 840.0), direction='OUTPUT'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(1065.0, 1680.0, 1065.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1235.0, 3780.0, 1235.0, 3780.0), direction='POWER'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nand2b_1', sg13g2_tech)
    c.write_gds("sg13g2_nand2b_1.gds")
