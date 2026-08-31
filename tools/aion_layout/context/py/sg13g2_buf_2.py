# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_buf_2
# ================================================================

"""Generated AION cell for sg13g2_buf_2."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(130.0, 2060.0), Point(130.0, 3180.0), Point(1735.0, 3180.0), Point(1735.0, 3135.0), Point(2275.0, 3135.0), Point(2275.0, 2135.0), Point(1735.0, 2135.0), Point(1735.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(445.0, 590.0), Point(445.0, 1330.0), Point(2275.0, 1330.0), Point(2275.0, 690.0), Point(1735.0, 690.0), Point(1735.0, 590.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2400.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2400.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2045.0, 2545.0, 2205.0, 2705.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2045.0, 2885.0, 2205.0, 3045.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(200.0, 2610.0, 360.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(275.0, 1605.0, 435.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1910.0, 1655.0, 2070.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1025.0, 1100.0, 1185.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1025.0, 660.0, 1185.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2045.0, 2205.0, 2205.0, 2365.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(200.0, 2950.0, 360.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2045.0, 1100.0, 2205.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2045.0, 760.0, 2205.0, 920.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1025.0, 2130.0, 1185.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(515.0, 1100.0, 675.0, 1260.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(515.0, 660.0, 675.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1535.0, 755.0, 1695.0, 915.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1535.0, 2905.0, 1695.0, 3065.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1805.0, 510.0), Point(1805.0, 3315.0), Point(1935.0, 3315.0), Point(1935.0, 1885.0), Point(2140.0, 1885.0), Point(2140.0, 1585.0), Point(1935.0, 1585.0), Point(1935.0, 510.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(785.0, 410.0), Point(785.0, 1520.0), Point(205.0, 1520.0), Point(205.0, 1850.0), Point(785.0, 1850.0), Point(785.0, 3360.0), Point(915.0, 3360.0), Point(915.0, 1850.0), Point(1295.0, 1850.0), Point(1295.0, 3360.0), Point(1425.0, 3360.0), Point(1425.0, 410.0), Point(1295.0, 410.0), Point(1295.0, 1520.0), Point(915.0, 1520.0), Point(915.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(670.0, 1520.0, 1235.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1755.0, 1490.0, 2140.0, 1870.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1995.0, 720.0), Point(1995.0, 1145.0), Point(1415.0, 1145.0), Point(1415.0, 2550.0), Point(765.0, 2550.0), Point(765.0, 2215.0), Point(485.0, 2215.0), Point(485.0, 1555.0), Point(225.0, 1555.0), Point(225.0, 2375.0), Point(605.0, 2375.0), Point(605.0, 2710.0), Point(1970.0, 2710.0), Point(1970.0, 3100.0), Point(2260.0, 3100.0), Point(2260.0, 2180.0), Point(1970.0, 2180.0), Point(1970.0, 2550.0), Point(1575.0, 2550.0), Point(1575.0, 1310.0), Point(2255.0, 1310.0), Point(2255.0, 720.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(150.0, 2560.0), Point(150.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(1745.0, 3560.0), Point(1745.0, 2895.0), Point(1485.0, 2895.0), Point(1485.0, 3560.0), Point(410.0, 3560.0), Point(410.0, 2560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(975.0, 610.0), Point(975.0, 1520.0), Point(670.0, 1520.0), Point(670.0, 1850.0), Point(975.0, 1850.0), Point(975.0, 2340.0), Point(1235.0, 2340.0), Point(1235.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(465.0, 220.0), Point(465.0, 1310.0), Point(725.0, 1310.0), Point(725.0, 220.0), Point(1485.0, 220.0), Point(1485.0, 965.0), Point(1745.0, 965.0), Point(1745.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1755.0, 1490.0, 2140.0, 1870.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1175.0, -5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(965.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(960.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(1920.0, 1680.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2640.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2560.0, 3600.0)))

    # Ports
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1175.0, -5.0, 1175.0, -5.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(965.0, 3780.0, 965.0, 3780.0), direction='POWER'))
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(960.0, 1680.0, 960.0, 1680.0)))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(1920.0, 1680.0, 1920.0, 1680.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_buf_2', sg13g2_tech)
    c.write_gds("sg13g2_buf_2.gds")
