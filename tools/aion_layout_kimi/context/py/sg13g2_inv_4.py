# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_inv_4
# ================================================================

"""Generated AION cell for sg13g2_inv_4."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2880.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2880.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(245.0, 590.0, 2585.0, 1330.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(245.0, 2060.0, 2585.0, 3180.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1755.0, 1655.0, 1915.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1415.0, 1655.0, 1575.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1075.0, 1655.0, 1235.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(735.0, 1655.0, 895.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(825.0, 1000.0, 985.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(825.0, 660.0, 985.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1845.0, 1000.0, 2005.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1845.0, 660.0, 2005.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1845.0, 2945.0, 2005.0, 3105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1845.0, 2605.0, 2005.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1845.0, 2255.0, 2005.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(315.0, 1000.0, 475.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(315.0, 660.0, 475.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1335.0, 660.0, 1495.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2355.0, 660.0, 2515.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(315.0, 2945.0, 475.0, 3105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(315.0, 2605.0, 475.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(315.0, 2255.0, 475.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(825.0, 2945.0, 985.0, 3105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(825.0, 2605.0, 985.0, 2765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(825.0, 2255.0, 985.0, 2415.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2355.0, 2945.0, 2515.0, 3105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2355.0, 2595.0, 2515.0, 2755.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1335.0, 2945.0, 1495.0, 3105.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1335.0, 2595.0, 1495.0, 2755.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(585.0, 410.0), Point(585.0, 3360.0), Point(715.0, 3360.0), Point(715.0, 1900.0), Point(1095.0, 1900.0), Point(1095.0, 3360.0), Point(1225.0, 3360.0), Point(1225.0, 1900.0), Point(1605.0, 1900.0), Point(1605.0, 3360.0), Point(1735.0, 3360.0), Point(1735.0, 1900.0), Point(2115.0, 1900.0), Point(2115.0, 3360.0), Point(2245.0, 3360.0), Point(2245.0, 410.0), Point(2115.0, 410.0), Point(2115.0, 1570.0), Point(1735.0, 1570.0), Point(1735.0, 410.0), Point(1605.0, 410.0), Point(1605.0, 1570.0), Point(1225.0, 1570.0), Point(1225.0, 410.0), Point(1095.0, 410.0), Point(1095.0, 1570.0), Point(715.0, 1570.0), Point(715.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(480.0, 1520.0, 2000.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2880.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2880.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2245.0, 1050.0, 2540.0, 2340.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(775.0, 610.0), Point(775.0, 1210.0), Point(2245.0, 1210.0), Point(2245.0, 2170.0), Point(775.0, 2170.0), Point(775.0, 3155.0), Point(1035.0, 3155.0), Point(1035.0, 2340.0), Point(1795.0, 2340.0), Point(1795.0, 3155.0), Point(2055.0, 3155.0), Point(2055.0, 2340.0), Point(2540.0, 2340.0), Point(2540.0, 1050.0), Point(2055.0, 1050.0), Point(2055.0, 610.0), Point(1795.0, 610.0), Point(1795.0, 1050.0), Point(1035.0, 1050.0), Point(1035.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(265.0, 2205.0), Point(265.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2880.0, 4000.0), Point(2880.0, 3560.0), Point(2565.0, 3560.0), Point(2565.0, 2545.0), Point(2305.0, 2545.0), Point(2305.0, 3560.0), Point(1545.0, 3560.0), Point(1545.0, 2545.0), Point(1285.0, 2545.0), Point(1285.0, 3560.0), Point(525.0, 3560.0), Point(525.0, 2205.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(265.0, 220.0), Point(265.0, 1210.0), Point(525.0, 1210.0), Point(525.0, 220.0), Point(1280.0, 220.0), Point(1280.0, 870.0), Point(1550.0, 870.0), Point(1550.0, 220.0), Point(2305.0, 220.0), Point(2305.0, 870.0), Point(2565.0, 870.0), Point(2565.0, 220.0), Point(2880.0, 220.0), Point(2880.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(480.0, 1520.0, 2000.0, 1900.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(960.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1925.0, 3800.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(2400.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1405.0, 5.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3120.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2950.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2950.0, 180.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(960.0, 1680.0, 960.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1925.0, 3800.0, 1925.0, 3800.0), direction='POWER'))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(2400.0, 1680.0, 2400.0, 1680.0), direction='OUTPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1405.0, 5.0, 1405.0, 5.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_inv_4', sg13g2_tech)
    c.write_gds("sg13g2_inv_4.gds")
