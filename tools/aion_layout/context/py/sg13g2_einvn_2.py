# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_einvn_2
# ================================================================

"""Generated AION cell for sg13g2_einvn_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 4320.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 4320.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 4320.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 4320.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1610.0, 570.0, 3960.0, 1310.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(580.0, 2540.0, 1390.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1610.0, 2060.0, 3950.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(580.0, 570.0, 1395.0, 990.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(650.0, 2610.0, 810.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1160.0, 2610.0, 1320.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(800.0, 2085.0, 960.0, 2245.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2190.0, 2610.0, 2350.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(650.0, 2950.0, 810.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2190.0, 640.0, 2350.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(650.0, 700.0, 810.0, 860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3220.0, 1030.0, 3380.0, 1190.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1680.0, 640.0, 1840.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1680.0, 980.0, 1840.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3720.0, 2270.0, 3880.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1680.0, 2270.0, 1840.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2700.0, 2270.0, 2860.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2700.0, 2610.0, 2860.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2700.0, 2950.0, 2860.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1160.0, 2950.0, 1320.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3730.0, 640.0, 3890.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2700.0, 640.0, 2860.0, 800.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2700.0, 980.0, 2860.0, 1140.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1165.0, 700.0, 1325.0, 860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1410.0, 1605.0, 1570.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(800.0, 1745.0, 960.0, 1905.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(800.0, 1405.0, 960.0, 1565.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3210.0, 2610.0, 3370.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3210.0, 2270.0, 3370.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3720.0, 2950.0, 3880.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3720.0, 2610.0, 3880.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2190.0, 2950.0, 2350.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1680.0, 2950.0, 1840.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1680.0, 2610.0, 1840.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3775.0, 1505.0, 3935.0, 1665.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1950.0, 390.0), Point(1950.0, 1520.0), Point(1325.0, 1520.0), Point(1325.0, 1850.0), Point(1655.0, 1850.0), Point(1655.0, 1670.0), Point(2590.0, 1670.0), Point(2590.0, 390.0), Point(2460.0, 390.0), Point(2460.0, 1520.0), Point(2080.0, 1520.0), Point(2080.0, 390.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2970.0, 390.0), Point(2970.0, 3360.0), Point(3100.0, 3360.0), Point(3100.0, 1670.0), Point(3480.0, 1670.0), Point(3480.0, 3360.0), Point(3610.0, 3360.0), Point(3610.0, 1735.0), Point(4025.0, 1735.0), Point(4025.0, 1435.0), Point(3620.0, 1435.0), Point(3620.0, 390.0), Point(3490.0, 390.0), Point(3490.0, 1520.0), Point(3100.0, 1520.0), Point(3100.0, 390.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(920.0, 390.0), Point(920.0, 1320.0), Point(715.0, 1320.0), Point(715.0, 2330.0), Point(920.0, 2330.0), Point(920.0, 3400.0), Point(2590.0, 3400.0), Point(2590.0, 1855.0), Point(2460.0, 1855.0), Point(2460.0, 3250.0), Point(2080.0, 3250.0), Point(2080.0, 1860.0), Point(1950.0, 1860.0), Point(1950.0, 3250.0), Point(1050.0, 3250.0), Point(1050.0, 390.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 4320.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 4320.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3700.0, 1010.0, 4030.0, 1750.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(280.0, 1320.0, 995.0, 2330.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3160.0, 1005.0, 3490.0, 2825.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(600.0, 2560.0), Point(600.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(4320.0, 4000.0), Point(4320.0, 3560.0), Point(2400.0, 3560.0), Point(2400.0, 2560.0), Point(2140.0, 2560.0), Point(2140.0, 3560.0), Point(860.0, 3560.0), Point(860.0, 2560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(600.0, 220.0), Point(600.0, 910.0), Point(865.0, 910.0), Point(865.0, 220.0), Point(2140.0, 220.0), Point(2140.0, 850.0), Point(2400.0, 850.0), Point(2400.0, 220.0), Point(4320.0, 220.0), Point(4320.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1115.0, 650.0), Point(1115.0, 910.0), Point(1215.0, 910.0), Point(1215.0, 2560.0), Point(1085.0, 2560.0), Point(1085.0, 3160.0), Point(1385.0, 3160.0), Point(1385.0, 1850.0), Point(1655.0, 1850.0), Point(1655.0, 1520.0), Point(1380.0, 1520.0), Point(1380.0, 650.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1655.0, 575.0), Point(1655.0, 1195.0), Point(2910.0, 1195.0), Point(2910.0, 825.0), Point(3950.0, 825.0), Point(3950.0, 590.0), Point(2650.0, 590.0), Point(2650.0, 1030.0), Point(1900.0, 1030.0), Point(1900.0, 575.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1630.0, 2215.0), Point(1630.0, 3160.0), Point(1890.0, 3160.0), Point(1890.0, 2380.0), Point(2650.0, 2380.0), Point(2650.0, 3335.0), Point(3930.0, 3335.0), Point(3930.0, 2220.0), Point(3670.0, 2220.0), Point(3670.0, 3175.0), Point(2910.0, 3175.0), Point(2910.0, 2215.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3700.0, 1010.0, 4030.0, 1750.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(280.0, 1320.0, 995.0, 2330.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3160.0, 1005.0, 3490.0, 2825.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(705.0, 3795.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'TE_B', Point(650.0, 1885.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(2010.0, -5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(3860.0, 1385.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Z', Point(3345.0, 2070.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4560.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 4390.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 4390.0, 180.0)))

    # Ports
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(705.0, 3795.0, 705.0, 3795.0), direction='POWER'))
    cell.add_port(Port('TE_B', 'TE_B', tech['Metal1'], Rect.from_lbrt(650.0, 1885.0, 650.0, 1885.0)))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(2010.0, -5.0, 2010.0, -5.0), direction='GROUND'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(3860.0, 1385.0, 3860.0, 1385.0), direction='INPUT'))
    cell.add_port(Port('Z', 'Z', tech['Metal1'], Rect.from_lbrt(3345.0, 2070.0, 3345.0, 2070.0), direction='OUTPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_einvn_2', sg13g2_tech)
    c.write_gds("sg13g2_einvn_2.gds")
