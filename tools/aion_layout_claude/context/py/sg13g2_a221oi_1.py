# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_a221oi_1
# ================================================================

"""Generated AION cell for sg13g2_a221oi_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 3840.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 3840.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3840.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(2280.0, 2060.0, 3600.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(240.0, 700.0, 2070.0, 1440.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(2280.0, 700.0, 3600.0, 1440.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3840.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(240.0, 2060.0, 2070.0, 3180.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1775.0, 1670.0, 1935.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2350.0, 2950.0, 2510.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(310.0, 770.0, 470.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(310.0, 2610.0, 470.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1075.0, 1670.0, 1235.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(820.0, 770.0, 980.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(820.0, 2610.0, 980.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2350.0, 770.0, 2510.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(820.0, 2950.0, 980.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 1670.0, 530.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(310.0, 2270.0, 470.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(310.0, 1110.0, 470.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1840.0, 2950.0, 2000.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1840.0, 770.0, 2000.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3370.0, 770.0, 3530.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(310.0, 2950.0, 470.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2370.0, 1760.0, 2530.0, 1920.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1330.0, 2555.0, 1490.0, 2715.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3370.0, 2610.0, 3530.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3370.0, 2950.0, 3530.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3115.0, 1670.0, 3275.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2860.0, 2950.0, 3020.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2860.0, 2610.0, 3020.0, 2770.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1600.0, 520.0), Point(1600.0, 3360.0), Point(1730.0, 3360.0), Point(1730.0, 1900.0), Point(2050.0, 1900.0), Point(2050.0, 1600.0), Point(1730.0, 1600.0), Point(1730.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(580.0, 520.0), Point(580.0, 1600.0), Point(260.0, 1600.0), Point(260.0, 1900.0), Point(580.0, 1900.0), Point(580.0, 3360.0), Point(710.0, 3360.0), Point(710.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3130.0, 520.0), Point(3130.0, 1600.0), Point(3045.0, 1600.0), Point(3045.0, 1900.0), Point(3130.0, 1900.0), Point(3130.0, 3360.0), Point(3260.0, 3360.0), Point(3260.0, 1900.0), Point(3345.0, 1900.0), Point(3345.0, 1600.0), Point(3260.0, 1600.0), Point(3260.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1090.0, 520.0), Point(1090.0, 1600.0), Point(1005.0, 1600.0), Point(1005.0, 1900.0), Point(1090.0, 1900.0), Point(1090.0, 3360.0), Point(1220.0, 3360.0), Point(1220.0, 1900.0), Point(1305.0, 1900.0), Point(1305.0, 1600.0), Point(1220.0, 1600.0), Point(1220.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2620.0, 520.0), Point(2620.0, 1690.0), Point(2300.0, 1690.0), Point(2300.0, 1990.0), Point(2620.0, 1990.0), Point(2620.0, 3360.0), Point(2750.0, 3360.0), Point(2750.0, 520.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(250.0, 1555.0, 610.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(830.0, 1555.0, 1360.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2260.0, 1440.0, 2515.0, 1940.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1540.0, 1555.0, 2040.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2810.0, 1160.0, 3660.0, 1370.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2760.0, 1570.0, 3320.0, 1800.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3320.0, 2505.0), Point(3320.0, 3560.0), Point(2560.0, 3560.0), Point(2560.0, 2900.0), Point(2300.0, 2900.0), Point(2300.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(3580.0, 3560.0), Point(3580.0, 2505.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(770.0, 2560.0), Point(770.0, 3160.0), Point(2050.0, 3160.0), Point(2050.0, 2900.0), Point(1790.0, 2900.0), Point(1790.0, 2950.0), Point(1030.0, 2950.0), Point(1030.0, 2560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(260.0, 720.0), Point(260.0, 1370.0), Point(1540.0, 1370.0), Point(1540.0, 980.0), Point(2810.0, 980.0), Point(2810.0, 1370.0), Point(3500.0, 1370.0), Point(3500.0, 2165.0), Point(260.0, 2165.0), Point(260.0, 3160.0), Point(520.0, 3160.0), Point(520.0, 2325.0), Point(3660.0, 2325.0), Point(3660.0, 1160.0), Point(3070.0, 1160.0), Point(3070.0, 720.0), Point(1280.0, 720.0), Point(1280.0, 1160.0), Point(520.0, 1160.0), Point(520.0, 720.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2760.0, 1570.0), Point(2760.0, 1800.0), Point(3055.0, 1800.0), Point(3055.0, 1900.0), Point(3320.0, 1900.0), Point(3320.0, 1570.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1280.0, 2505.0), Point(1280.0, 2765.0), Point(1540.0, 2765.0), Point(1540.0, 2715.0), Point(2810.0, 2715.0), Point(2810.0, 3160.0), Point(3070.0, 3160.0), Point(3070.0, 2505.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2260.0, 1440.0), Point(2260.0, 1940.0), Point(2580.0, 1940.0), Point(2580.0, 1710.0), Point(2515.0, 1710.0), Point(2515.0, 1440.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(770.0, 220.0), Point(770.0, 980.0), Point(1030.0, 980.0), Point(1030.0, 220.0), Point(3320.0, 220.0), Point(3320.0, 980.0), Point(3580.0, 980.0), Point(3580.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1540.0, 1555.0, 2040.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(830.0, 1555.0, 1360.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(250.0, 1555.0, 610.0, 1900.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'C1', Point(445.0, 1735.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(3360.0, 1260.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B2', Point(1120.0, 1735.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B1', Point(1865.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A2', Point(3155.0, 1740.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1930.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A1', Point(2350.0, 1540.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1840.0, -20.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3910.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3910.0, 3600.0)))

    # Ports
    cell.add_port(Port('C1', 'C1', tech['Metal1'], Rect.from_lbrt(445.0, 1735.0, 445.0, 1735.0)))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(3360.0, 1260.0, 3360.0, 1260.0), direction='OUTPUT'))
    cell.add_port(Port('B2', 'B2', tech['Metal1'], Rect.from_lbrt(1120.0, 1735.0, 1120.0, 1735.0)))
    cell.add_port(Port('B1', 'B1', tech['Metal1'], Rect.from_lbrt(1865.0, 1680.0, 1865.0, 1680.0)))
    cell.add_port(Port('A2', 'A2', tech['Metal1'], Rect.from_lbrt(3155.0, 1740.0, 3155.0, 1740.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1930.0, 3780.0, 1930.0, 3780.0), direction='POWER'))
    cell.add_port(Port('A1', 'A1', tech['Metal1'], Rect.from_lbrt(2350.0, 1540.0, 2350.0, 1540.0)))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1840.0, -20.0, 1840.0, -20.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_a221oi_1', sg13g2_tech)
    c.write_gds("sg13g2_a221oi_1.gds")
