# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_and3_2
# ================================================================

"""Generated AION cell for sg13g2_and3_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 3360.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 3360.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2020.0, 2170.0), Point(2020.0, 2355.0), Point(380.0, 2355.0), Point(380.0, 3195.0), Point(1940.0, 3195.0), Point(1940.0, 3290.0), Point(3230.0, 3290.0), Point(3230.0, 2170.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1940.0, 700.0), Point(1940.0, 800.0), Point(380.0, 800.0), Point(380.0, 1440.0), Point(3230.0, 1440.0), Point(3230.0, 700.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3360.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3360.0, 3930.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3000.0, 2965.0, 3160.0, 3125.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3000.0, 815.0, 3160.0, 975.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1980.0, 2965.0, 2140.0, 3125.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(960.0, 2965.0, 1120.0, 3125.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(775.0, 500.0, 935.0, 660.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(435.0, 500.0, 595.0, 660.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1810.0, 1735.0, 1970.0, 1895.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2320.0, 1820.0, 2480.0, 1980.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1175.0, 1735.0, 1335.0, 1895.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(450.0, 2965.0, 610.0, 3125.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(450.0, 2625.0, 610.0, 2785.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 2965.0, 2650.0, 3125.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 2625.0, 2650.0, 2785.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(450.0, 1105.0, 610.0, 1265.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 1155.0, 2650.0, 1315.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2490.0, 815.0, 2650.0, 975.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1980.0, 890.0, 2140.0, 1050.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1470.0, 2965.0, 1630.0, 3125.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1470.0, 2625.0, 1630.0, 2785.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1980.0, 2625.0, 2140.0, 2785.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(960.0, 2625.0, 1120.0, 2785.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2760.0, 515.0), Point(2760.0, 1750.0), Point(2380.0, 1750.0), Point(2380.0, 520.0), Point(2250.0, 520.0), Point(2250.0, 3505.0), Point(2380.0, 3505.0), Point(2380.0, 2050.0), Point(2760.0, 2050.0), Point(2760.0, 3500.0), Point(2890.0, 3500.0), Point(2890.0, 515.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(350.0, 430.0), Point(350.0, 730.0), Point(720.0, 730.0), Point(720.0, 3375.0), Point(850.0, 3375.0), Point(850.0, 730.0), Point(1020.0, 730.0), Point(1020.0, 430.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1230.0, 540.0), Point(1230.0, 1650.0), Point(1090.0, 1650.0), Point(1090.0, 1980.0), Point(1230.0, 1980.0), Point(1230.0, 3375.0), Point(1360.0, 3375.0), Point(1360.0, 1980.0), Point(1420.0, 1980.0), Point(1420.0, 1650.0), Point(1360.0, 1650.0), Point(1360.0, 540.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1740.0, 545.0), Point(1740.0, 3375.0), Point(1870.0, 3375.0), Point(1870.0, 1980.0), Point(2040.0, 1980.0), Point(2040.0, 1650.0), Point(1870.0, 1650.0), Point(1870.0, 545.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2740.0, 1290.0, 3020.0, 2510.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1760.0, 1400.0, 2060.0, 1950.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1125.0, 1400.0, 1560.0, 1950.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1225.0, 475.0, 1590.0, 1090.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3360.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3360.0, 4000.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(400.0, 1090.0), Point(400.0, 3175.0), Point(660.0, 3175.0), Point(660.0, 2320.0), Point(1415.0, 2320.0), Point(1415.0, 3175.0), Point(1675.0, 3175.0), Point(1675.0, 2320.0), Point(2430.0, 2320.0), Point(2430.0, 2030.0), Point(2530.0, 2030.0), Point(2530.0, 1770.0), Point(2270.0, 1770.0), Point(2270.0, 2160.0), Point(660.0, 2160.0), Point(660.0, 1090.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(1930.0, 220.0), Point(1930.0, 1140.0), Point(2190.0, 1140.0), Point(2190.0, 220.0), Point(2950.0, 220.0), Point(2950.0, 1090.0), Point(3210.0, 1090.0), Point(3210.0, 220.0), Point(3360.0, 220.0), Point(3360.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(910.0, 2575.0), Point(910.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3360.0, 4000.0), Point(3360.0, 3560.0), Point(3210.0, 3560.0), Point(3210.0, 2915.0), Point(2950.0, 2915.0), Point(2950.0, 3560.0), Point(2190.0, 3560.0), Point(2190.0, 2575.0), Point(1930.0, 2575.0), Point(1930.0, 3560.0), Point(1170.0, 3560.0), Point(1170.0, 2575.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2440.0, 770.0), Point(2440.0, 1550.0), Point(2740.0, 1550.0), Point(2740.0, 2510.0), Point(2435.0, 2510.0), Point(2435.0, 3175.0), Point(2705.0, 3175.0), Point(2705.0, 2690.0), Point(3020.0, 2690.0), Point(3020.0, 1290.0), Point(2700.0, 1290.0), Point(2700.0, 770.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(350.0, 475.0), Point(350.0, 790.0), Point(1225.0, 790.0), Point(1225.0, 1090.0), Point(1590.0, 1090.0), Point(1590.0, 475.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1760.0, 1400.0, 2060.0, 1950.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1125.0, 1400.0, 1560.0, 1950.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(2880.0, 2100.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(1315.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1680.0, 3770.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1600.0, -65.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(1900.0, 1770.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(1405.0, 790.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3600.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3430.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3430.0, 3600.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(2880.0, 2100.0, 2880.0, 2100.0)))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(1315.0, 1680.0, 1315.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1680.0, 3770.0, 1680.0, 3770.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1600.0, -65.0, 1600.0, -65.0), direction='GROUND'))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(1900.0, 1770.0, 1900.0, 1770.0), direction='INPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(1405.0, 790.0, 1405.0, 790.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_and3_2', sg13g2_tech)
    c.write_gds("sg13g2_and3_2.gds")
