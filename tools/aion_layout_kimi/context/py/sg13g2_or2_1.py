# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_or2_1
# ================================================================

"""Generated AION cell for sg13g2_or2_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1290.0, 2180.0), Point(1290.0, 2460.0), Point(240.0, 2460.0), Point(240.0, 3300.0), Point(2120.0, 3300.0), Point(2120.0, 2180.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(240.0, 480.0), Point(240.0, 1030.0), Point(1290.0, 1030.0), Point(1290.0, 1220.0), Point(2105.0, 1220.0), Point(2105.0, 480.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2400.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2400.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1045.0, 1685.0, 1205.0, 1845.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(310.0, 3070.0, 470.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(310.0, 2730.0, 470.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1880.0, 3070.0, 2040.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1875.0, 890.0, 2035.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1875.0, 550.0, 2035.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1880.0, 2730.0, 2040.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1880.0, 2390.0, 2040.0, 2550.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(675.0, 2160.0, 835.0, 2320.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1360.0, 2390.0, 1520.0, 2550.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1350.0, 2730.0, 1510.0, 2890.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1350.0, 3070.0, 1510.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1365.0, 550.0, 1525.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1350.0, 3070.0, 1510.0, 3230.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(310.0, 550.0, 470.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(820.0, 550.0, 980.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1560.0, 1370.0, 1720.0, 1530.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1350.0, 3070.0, 1510.0, 3230.0)))
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
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1090.0, 220.0), Point(1090.0, 1615.0), Point(975.0, 1615.0), Point(975.0, 1915.0), Point(1090.0, 1915.0), Point(1090.0, 2395.0), Point(1220.0, 2395.0), Point(1220.0, 1915.0), Point(1275.0, 1915.0), Point(1275.0, 1615.0), Point(1220.0, 1615.0), Point(1220.0, 220.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1635.0, 220.0), Point(1635.0, 1290.0), Point(1485.0, 1290.0), Point(1485.0, 1600.0), Point(1635.0, 1600.0), Point(1635.0, 3530.0), Point(1765.0, 3530.0), Point(1765.0, 1600.0), Point(1800.0, 1600.0), Point(1800.0, 1290.0), Point(1765.0, 1290.0), Point(1765.0, 220.0)]))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(580.0, 2360.0, 710.0, 3520.0)))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(610.0, 2090.0, 910.0, 2390.0)))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(1090.0, 2360.0, 1220.0, 3525.0)))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(580.0, 220.0, 710.0, 2495.0)))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(840.0, 1495.0), Point(840.0, 1895.0), Point(1255.0, 1895.0), Point(1255.0, 1635.0), Point(1080.0, 1635.0), Point(1080.0, 1495.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1825.0, 500.0), Point(1825.0, 1100.0), Point(1955.0, 1100.0), Point(1955.0, 2340.0), Point(1800.0, 2340.0), Point(1800.0, 3280.0), Point(2150.0, 3280.0), Point(2150.0, 500.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(770.0, 500.0), Point(770.0, 940.0), Point(260.0, 940.0), Point(260.0, 3280.0), Point(520.0, 3280.0), Point(520.0, 2680.0), Point(445.0, 2680.0), Point(445.0, 1120.0), Point(1445.0, 1120.0), Point(1445.0, 1580.0), Point(1770.0, 1580.0), Point(1770.0, 1315.0), Point(1635.0, 1315.0), Point(1635.0, 940.0), Point(1030.0, 940.0), Point(1030.0, 500.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(625.0, 2130.0), Point(625.0, 2370.0), Point(840.0, 2370.0), Point(840.0, 2650.0), Point(1080.0, 2650.0), Point(1080.0, 2130.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(260.0, 220.0), Point(260.0, 760.0), Point(520.0, 760.0), Point(520.0, 220.0), Point(1315.0, 220.0), Point(1315.0, 760.0), Point(1575.0, 760.0), Point(1575.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1300.0, 2340.0), Point(1300.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(1560.0, 3560.0), Point(1560.0, 2340.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(840.0, 1495.0, 1080.0, 1895.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(840.0, 2130.0, 1080.0, 2650.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1800.0, 2340.0, 2150.0, 3280.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(960.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1300.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(915.0, 2395.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(2010.0, 2775.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1220.0, 3780.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2640.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2470.0, 3600.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(960.0, 1680.0, 960.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1300.0, 0.0, 1300.0, 0.0), direction='GROUND'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(915.0, 2395.0, 915.0, 2395.0), direction='INPUT'))
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(2010.0, 2775.0, 2010.0, 2775.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1220.0, 3780.0, 1220.0, 3780.0), direction='POWER'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_or2_1', sg13g2_tech)
    c.write_gds("sg13g2_or2_1.gds")
