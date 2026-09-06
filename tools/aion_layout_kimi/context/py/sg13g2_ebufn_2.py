# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_ebufn_2
# ================================================================

"""Generated AION cell for sg13g2_ebufn_2."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 4800.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 4800.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(310.0, 2060.0), Point(310.0, 3180.0), Point(1870.0, 3180.0), Point(1870.0, 3630.0), Point(0.0, 3630.0), Point(0.0, 3930.0), Point(4800.0, 3930.0), Point(4800.0, 3630.0), Point(2170.0, 3630.0), Point(2170.0, 3180.0), Point(2710.0, 3180.0), Point(2710.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2940.0, 2060.0), Point(2940.0, 3060.0), Point(3480.0, 3060.0), Point(3480.0, 3195.0), Point(3860.0, 3195.0), Point(3860.0, 3060.0), Point(4420.0, 3060.0), Point(4420.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(3030.0, 540.0, 4350.0, 1180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 4800.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(230.0, 540.0, 2570.0, 1280.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3010.0, 2130.0, 3170.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, -80.0, 4640.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(890.0, 2560.0, 1050.0, 2720.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(890.0, 2220.0, 1050.0, 2380.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1400.0, 2560.0, 1560.0, 2720.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2340.0, 950.0, 2500.0, 1110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2340.0, 610.0, 2500.0, 770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3570.0, 2950.0, 3730.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4120.0, 950.0, 4280.0, 1110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1400.0, 2220.0, 1560.0, 2380.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1400.0, 2900.0, 1560.0, 3060.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3805.0, 1600.0, 3965.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1320.0, 950.0, 1480.0, 1110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(810.0, 865.0, 970.0, 1025.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(380.0, 2900.0, 540.0, 3060.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(380.0, 2560.0, 540.0, 2720.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3100.0, 610.0, 3260.0, 770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4190.0, 2490.0, 4350.0, 2650.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4190.0, 2130.0, 4350.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4480.0, 3700.0, 4640.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3235.0, 1600.0, 3395.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2730.0, 1275.0, 2890.0, 1435.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1940.0, 3250.0, 2100.0, 3410.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1150.0, 1550.0, 1310.0, 1710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1320.0, 610.0, 1480.0, 770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4120.0, 610.0, 4280.0, 770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4190.0, 2830.0, 4350.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3610.0, 950.0, 3770.0, 1110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3610.0, 610.0, 3770.0, 770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3100.0, 950.0, 3260.0, 1110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2480.0, 2950.0, 2640.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1830.0, 610.0, 1990.0, 770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 950.0, 460.0, 1110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(300.0, 610.0, 460.0, 770.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3880.0, 360.0), Point(3880.0, 1530.0), Point(3735.0, 1530.0), Point(3735.0, 1830.0), Point(3930.0, 1830.0), Point(3930.0, 3240.0), Point(4060.0, 3240.0), Point(4060.0, 1530.0), Point(4010.0, 1530.0), Point(4010.0, 360.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3370.0, 360.0), Point(3370.0, 1530.0), Point(3165.0, 1530.0), Point(3165.0, 1745.0), Point(1670.0, 1745.0), Point(1670.0, 3360.0), Point(1800.0, 3360.0), Point(1800.0, 1895.0), Point(2240.0, 1895.0), Point(2240.0, 3360.0), Point(2370.0, 3360.0), Point(2370.0, 1895.0), Point(3280.0, 1895.0), Point(3280.0, 3240.0), Point(3410.0, 3240.0), Point(3410.0, 1830.0), Point(3500.0, 1830.0), Point(3500.0, 360.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1590.0, 360.0), Point(1590.0, 1505.0), Point(2960.0, 1505.0), Point(2960.0, 1205.0), Point(2660.0, 1205.0), Point(2660.0, 1355.0), Point(2230.0, 1355.0), Point(2230.0, 360.0), Point(2100.0, 360.0), Point(2100.0, 1355.0), Point(1720.0, 1355.0), Point(1720.0, 360.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(570.0, 360.0), Point(570.0, 1780.0), Point(650.0, 1780.0), Point(650.0, 3360.0), Point(780.0, 3360.0), Point(780.0, 1780.0), Point(1160.0, 1780.0), Point(1160.0, 3360.0), Point(1290.0, 3360.0), Point(1290.0, 1780.0), Point(1380.0, 1780.0), Point(1380.0, 1480.0), Point(1210.0, 1480.0), Point(1210.0, 360.0), Point(1080.0, 360.0), Point(1080.0, 1645.0), Point(700.0, 1645.0), Point(700.0, 360.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 4800.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 4800.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3155.0, 1370.0, 3495.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(840.0, 2170.0, 1100.0, 2765.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3695.0, 1370.0, 4015.0, 1850.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(740.0, 845.0), Point(740.0, 2380.0), Point(840.0, 2380.0), Point(840.0, 2765.0), Point(1100.0, 2765.0), Point(1100.0, 2170.0), Point(910.0, 2170.0), Point(910.0, 1080.0), Point(1025.0, 1080.0), Point(1025.0, 845.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(250.0, 440.0), Point(250.0, 1160.0), Point(510.0, 1160.0), Point(510.0, 635.0), Point(1270.0, 635.0), Point(1270.0, 1160.0), Point(2515.0, 1160.0), Point(2515.0, 540.0), Point(2300.0, 540.0), Point(2300.0, 1000.0), Point(1530.0, 1000.0), Point(1530.0, 440.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(1780.0, 220.0), Point(1780.0, 820.0), Point(2040.0, 820.0), Point(2040.0, 220.0), Point(3560.0, 220.0), Point(3560.0, 1130.0), Point(3820.0, 1130.0), Point(3820.0, 220.0), Point(4800.0, 220.0), Point(4800.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1350.0, 2170.0), Point(1350.0, 3075.0), Point(590.0, 3075.0), Point(590.0, 2510.0), Point(330.0, 2510.0), Point(330.0, 3235.0), Point(1610.0, 3235.0), Point(1610.0, 3050.0), Point(2430.0, 3050.0), Point(2430.0, 3160.0), Point(2690.0, 3160.0), Point(2690.0, 2890.0), Point(1610.0, 2890.0), Point(1610.0, 2170.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3520.0, 2915.0), Point(3520.0, 3560.0), Point(2150.0, 3560.0), Point(2150.0, 3230.0), Point(1890.0, 3230.0), Point(1890.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(4800.0, 4000.0), Point(4800.0, 3560.0), Point(3780.0, 3560.0), Point(3780.0, 2915.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3050.0, 560.0), Point(3050.0, 975.0), Point(2700.0, 975.0), Point(2700.0, 2340.0), Point(3220.0, 2340.0), Point(3220.0, 2080.0), Point(2915.0, 2080.0), Point(2915.0, 1160.0), Point(3300.0, 1160.0), Point(3300.0, 560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(4060.0, 595.0), Point(4060.0, 1130.0), Point(4245.0, 1130.0), Point(4245.0, 2080.0), Point(4140.0, 2080.0), Point(4140.0, 2545.0), Point(2520.0, 2545.0), Point(2520.0, 1600.0), Point(1355.0, 1600.0), Point(1355.0, 1500.0), Point(1100.0, 1500.0), Point(1100.0, 1760.0), Point(2360.0, 1760.0), Point(2360.0, 2710.0), Point(4140.0, 2710.0), Point(4140.0, 3040.0), Point(4435.0, 3040.0), Point(4435.0, 595.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3155.0, 1370.0, 3495.0, 1850.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3695.0, 1370.0, 4015.0, 1850.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(3870.0, 1585.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Z', Point(975.0, 2460.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(2485.0, -65.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(2245.0, 3775.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'TE_B', Point(3255.0, 1455.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 5040.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 4870.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-300.0, -180.0, 5100.0, 180.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(3870.0, 1585.0, 3870.0, 1585.0), direction='INPUT'))
    cell.add_port(Port('Z', 'Z', tech['Metal1'], Rect.from_lbrt(975.0, 2460.0, 975.0, 2460.0), direction='OUTPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(2485.0, -65.0, 2485.0, -65.0), direction='GROUND'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(2245.0, 3775.0, 2245.0, 3775.0), direction='POWER'))
    cell.add_port(Port('TE_B', 'TE_B', tech['Metal1'], Rect.from_lbrt(3255.0, 1455.0, 3255.0, 1455.0)))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_ebufn_2', sg13g2_tech)
    c.write_gds("sg13g2_ebufn_2.gds")
