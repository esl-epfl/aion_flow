# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_dlygate4sd2_1
# ================================================================

"""Generated AION cell for sg13g2_dlygate4sd2_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2895.0, 590.0), Point(2895.0, 910.0), Point(2130.0, 910.0), Point(2130.0, 1330.0), Point(3705.0, 1330.0), Point(3705.0, 590.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2130.0, 2060.0), Point(2130.0, 3060.0), Point(2910.0, 3060.0), Point(2910.0, 3180.0), Point(3705.0, 3180.0), Point(3705.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(800.0, 2180.0), Point(800.0, 2555.0), Point(220.0, 2555.0), Point(220.0, 2975.0), Point(800.0, 2975.0), Point(800.0, 3180.0), Point(1840.0, 3180.0), Point(1840.0, 2180.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3840.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3840.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(190.0, 590.0, 1810.0, 1010.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(290.0, 2700.0, 450.0, 2860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(260.0, 660.0, 420.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(910.0, 660.0, 1070.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1610.0, 2700.0, 1770.0, 2860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2950.0, 2835.0, 3110.0, 2995.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2215.0, 2490.0, 2375.0, 2650.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3475.0, 2610.0, 3635.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3475.0, 2950.0, 3635.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2215.0, 2830.0, 2375.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(800.0, 2700.0, 960.0, 2860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1165.0, 1435.0, 1325.0, 1595.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1165.0, 1775.0, 1325.0, 1935.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1580.0, 660.0, 1740.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2215.0, 2150.0, 2375.0, 2310.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2200.0, 1015.0, 2360.0, 1175.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2190.0, 1605.0, 2350.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2950.0, 2495.0, 3110.0, 2655.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2965.0, 660.0, 3125.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3475.0, 2270.0, 3635.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(605.0, 1495.0, 765.0, 1655.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3475.0, 660.0, 3635.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3475.0, 1000.0, 3635.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3105.0, 1600.0, 3265.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2645.0, 730.0), Point(2645.0, 1520.0), Point(2120.0, 1520.0), Point(2120.0, 1850.0), Point(2575.0, 1850.0), Point(2575.0, 3240.0), Point(2825.0, 3240.0), Point(2825.0, 730.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(530.0, 410.0), Point(530.0, 2480.0), Point(560.0, 2480.0), Point(560.0, 3155.0), Point(690.0, 3155.0), Point(690.0, 1740.0), Point(840.0, 1740.0), Point(840.0, 1410.0), Point(660.0, 1410.0), Point(660.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1290.0, 410.0), Point(1290.0, 1350.0), Point(1050.0, 1350.0), Point(1050.0, 2020.0), Point(1250.0, 2020.0), Point(1250.0, 3360.0), Point(1500.0, 3360.0), Point(1500.0, 1350.0), Point(1470.0, 1350.0), Point(1470.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3235.0, 410.0), Point(3235.0, 1515.0), Point(3020.0, 1515.0), Point(3020.0, 1845.0), Point(3235.0, 1845.0), Point(3235.0, 3360.0), Point(3365.0, 3360.0), Point(3365.0, 410.0)]))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2155.0, 960.0), Point(2155.0, 1360.0), Point(2580.0, 1360.0), Point(2580.0, 1810.0), Point(3045.0, 1810.0), Point(3045.0, 2030.0), Point(2165.0, 2030.0), Point(2165.0, 3040.0), Point(2425.0, 3040.0), Point(2425.0, 2205.0), Point(3205.0, 2205.0), Point(3205.0, 1810.0), Point(3315.0, 1810.0), Point(3315.0, 1550.0), Point(2740.0, 1550.0), Point(2740.0, 1160.0), Point(2395.0, 1160.0), Point(2395.0, 960.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1520.0, 610.0), Point(1520.0, 870.0), Point(1580.0, 870.0), Point(1580.0, 2615.0), Point(1520.0, 2615.0), Point(1520.0, 2945.0), Point(1825.0, 2945.0), Point(1825.0, 1815.0), Point(2400.0, 1815.0), Point(2400.0, 1555.0), Point(1810.0, 1555.0), Point(1810.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(210.0, 610.0), Point(210.0, 1240.0), Point(1120.0, 1240.0), Point(1120.0, 2195.0), Point(240.0, 2195.0), Point(240.0, 2910.0), Point(500.0, 2910.0), Point(500.0, 2400.0), Point(1375.0, 2400.0), Point(1375.0, 1065.0), Point(480.0, 1065.0), Point(480.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3425.0, 610.0), Point(3425.0, 1115.0), Point(3065.0, 1115.0), Point(3065.0, 1370.0), Point(3495.0, 1370.0), Point(3495.0, 2220.0), Point(3430.0, 2220.0), Point(3430.0, 3160.0), Point(3685.0, 3160.0), Point(3685.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2900.0, 2455.0), Point(2900.0, 3560.0), Point(1010.0, 3560.0), Point(1010.0, 2650.0), Point(745.0, 2650.0), Point(745.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(3160.0, 3560.0), Point(3160.0, 2455.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(860.0, 220.0), Point(860.0, 870.0), Point(1120.0, 870.0), Point(1120.0, 220.0), Point(2915.0, 220.0), Point(2915.0, 870.0), Point(3175.0, 870.0), Point(3175.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(205.0, 1425.0, 835.0, 1945.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3065.0, 1115.0, 3685.0, 1370.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(205.0, 1425.0, 835.0, 1945.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(3360.0, 1260.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(2085.0, 3790.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(2200.0, 5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(520.0, 1680.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3910.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3910.0, 180.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(3360.0, 1260.0, 3360.0, 1260.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(2085.0, 3790.0, 2085.0, 3790.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(2200.0, 5.0, 2200.0, 5.0), direction='GROUND'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(520.0, 1680.0, 520.0, 1680.0), direction='INPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_dlygate4sd2_1', sg13g2_tech)
    c.write_gds("sg13g2_dlygate4sd2_1.gds")
