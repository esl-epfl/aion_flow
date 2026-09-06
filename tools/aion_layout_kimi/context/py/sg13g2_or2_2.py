# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_or2_2
# ================================================================

"""Generated AION cell for sg13g2_or2_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 2880.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 2880.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1250.0, 2180.0), Point(1250.0, 2460.0), Point(200.0, 2460.0), Point(200.0, 3300.0), Point(2685.0, 3300.0), Point(2685.0, 2180.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(200.0, 480.0), Point(200.0, 1030.0), Point(1255.0, 1030.0), Point(1255.0, 1220.0), Point(2685.0, 1220.0), Point(2685.0, 480.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2880.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2880.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1005.0, 1685.0, 1165.0, 1845.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2455.0, 2730.0, 2615.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(270.0, 3070.0, 430.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(270.0, 2730.0, 430.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2455.0, 550.0, 2615.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1840.0, 3070.0, 2000.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1835.0, 890.0, 1995.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1835.0, 550.0, 1995.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1840.0, 2730.0, 2000.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1840.0, 2390.0, 2000.0, 2550.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(635.0, 2160.0, 795.0, 2320.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1320.0, 2390.0, 1480.0, 2550.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1320.0, 2730.0, 1480.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1325.0, 550.0, 1485.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(270.0, 550.0, 430.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(780.0, 550.0, 940.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2455.0, 2390.0, 2615.0, 2550.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2455.0, 890.0, 2615.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1515.0, 1370.0, 1675.0, 1530.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2455.0, 3070.0, 2615.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1320.0, 3070.0, 1480.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1050.0, 220.0), Point(1050.0, 1615.0), Point(935.0, 1615.0), Point(935.0, 1915.0), Point(1050.0, 1915.0), Point(1050.0, 3525.0), Point(1180.0, 3525.0), Point(1180.0, 1915.0), Point(1235.0, 1915.0), Point(1235.0, 1615.0), Point(1180.0, 1615.0), Point(1180.0, 220.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(540.0, 220.0), Point(540.0, 3520.0), Point(670.0, 3520.0), Point(670.0, 2390.0), Point(870.0, 2390.0), Point(870.0, 2090.0), Point(670.0, 2090.0), Point(670.0, 220.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1595.0, 220.0), Point(1595.0, 1300.0), Point(1445.0, 1300.0), Point(1445.0, 1600.0), Point(1595.0, 1600.0), Point(1595.0, 3530.0), Point(1725.0, 3530.0), Point(1725.0, 1600.0), Point(2175.0, 1600.0), Point(2175.0, 3530.0), Point(2305.0, 3530.0), Point(2305.0, 220.0), Point(2175.0, 220.0), Point(2175.0, 1290.0), Point(1725.0, 1290.0), Point(1725.0, 220.0)]))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1785.0, 500.0), Point(1785.0, 1100.0), Point(1885.0, 1100.0), Point(1885.0, 2340.0), Point(1790.0, 2340.0), Point(1790.0, 3280.0), Point(2050.0, 3280.0), Point(2050.0, 500.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(220.0, 220.0), Point(220.0, 760.0), Point(480.0, 760.0), Point(480.0, 220.0), Point(1275.0, 220.0), Point(1275.0, 760.0), Point(1535.0, 760.0), Point(1535.0, 220.0), Point(2405.0, 220.0), Point(2405.0, 1100.0), Point(2665.0, 1100.0), Point(2665.0, 220.0), Point(2880.0, 220.0), Point(2880.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(840.0, 1335.0), Point(840.0, 1895.0), Point(1215.0, 1895.0), Point(1215.0, 1635.0), Point(1085.0, 1635.0), Point(1085.0, 1335.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(730.0, 500.0), Point(730.0, 945.0), Point(220.0, 945.0), Point(220.0, 3280.0), Point(480.0, 3280.0), Point(480.0, 2530.0), Point(405.0, 2530.0), Point(405.0, 1125.0), Point(1425.0, 1125.0), Point(1425.0, 1580.0), Point(1705.0, 1580.0), Point(1705.0, 1315.0), Point(1595.0, 1315.0), Point(1595.0, 945.0), Point(990.0, 945.0), Point(990.0, 500.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(585.0, 2130.0), Point(585.0, 2350.0), Point(840.0, 2350.0), Point(840.0, 2880.0), Point(1085.0, 2880.0), Point(1085.0, 2130.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1270.0, 2340.0), Point(1270.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2880.0, 4000.0), Point(2880.0, 3560.0), Point(2665.0, 3560.0), Point(2665.0, 2340.0), Point(2405.0, 2340.0), Point(2405.0, 3560.0), Point(1530.0, 3560.0), Point(1530.0, 2340.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(840.0, 2130.0, 1085.0, 2880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(840.0, 1335.0, 1085.0, 1895.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2880.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2880.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1790.0, 2340.0, 2050.0, 3280.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(960.0, 2520.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1430.0, -5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(960.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(1920.0, 2520.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1435.0, 3780.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3120.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2950.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2950.0, 3600.0)))

    # Ports
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(960.0, 2520.0, 960.0, 2520.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1430.0, -5.0, 1430.0, -5.0), direction='GROUND'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(960.0, 1680.0, 960.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(1920.0, 2520.0, 1920.0, 2520.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1435.0, 3780.0, 1435.0, 3780.0), direction='POWER'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_or2_2', sg13g2_tech)
    c.write_gds("sg13g2_or2_2.gds")
