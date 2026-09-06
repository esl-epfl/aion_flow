# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_dlygate4sd3_1
# ================================================================

"""Generated AION cell for sg13g2_dlygate4sd3_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2190.0, 2060.0), Point(2190.0, 3060.0), Point(3100.0, 3060.0), Point(3100.0, 3180.0), Point(3950.0, 3180.0), Point(3950.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(3110.0, 590.0), Point(3110.0, 910.0), Point(2190.0, 910.0), Point(2190.0, 1330.0), Point(3920.0, 1330.0), Point(3920.0, 590.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(880.0, 2180.0), Point(880.0, 2555.0), Point(280.0, 2555.0), Point(280.0, 2975.0), Point(880.0, 2975.0), Point(880.0, 3180.0), Point(1970.0, 3180.0), Point(1970.0, 2180.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 4320.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(280.0, 590.0, 1970.0, 1010.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 4320.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2260.0, 2490.0, 2420.0, 2650.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3690.0, 660.0, 3850.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3690.0, 1090.0, 3850.0, 1250.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3720.0, 2270.0, 3880.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3720.0, 2610.0, 3880.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3325.0, 1595.0, 3485.0, 1755.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3180.0, 665.0, 3340.0, 825.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3170.0, 2610.0, 3330.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3170.0, 2950.0, 3330.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3720.0, 2950.0, 3880.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2735.0, 1600.0, 2895.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2395.0, 1600.0, 2555.0, 1760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2260.0, 1010.0, 2420.0, 1170.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2260.0, 2150.0, 2420.0, 2310.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1740.0, 715.0, 1900.0, 875.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1740.0, 2610.0, 1900.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1240.0, 1785.0, 1400.0, 1945.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 660.0, 1020.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(860.0, 2695.0, 1020.0, 2855.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(670.0, 1490.0, 830.0, 1650.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1240.0, 1430.0, 1400.0, 1590.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 715.0, 510.0, 875.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(350.0, 2695.0, 510.0, 2855.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, -80.0, 4160.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(4000.0, 3700.0, 4160.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2260.0, 2830.0, 2420.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1740.0, 2270.0, 1900.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1740.0, 2950.0, 1900.0, 3110.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(620.0, 410.0), Point(620.0, 1410.0), Point(590.0, 1410.0), Point(590.0, 1740.0), Point(620.0, 1740.0), Point(620.0, 3155.0), Point(750.0, 3155.0), Point(750.0, 1740.0), Point(920.0, 1740.0), Point(920.0, 1410.0), Point(750.0, 1410.0), Point(750.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3450.0, 410.0), Point(3450.0, 1515.0), Point(3245.0, 1515.0), Point(3245.0, 1845.0), Point(3440.0, 1845.0), Point(3440.0, 3360.0), Point(3570.0, 3360.0), Point(3570.0, 1845.0), Point(3610.0, 1845.0), Point(3610.0, 1515.0), Point(3580.0, 1515.0), Point(3580.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2530.0, 730.0), Point(2530.0, 1520.0), Point(2315.0, 1520.0), Point(2315.0, 1850.0), Point(2530.0, 1850.0), Point(2530.0, 3240.0), Point(3030.0, 3240.0), Point(3030.0, 1850.0), Point(3035.0, 1850.0), Point(3035.0, 1520.0), Point(3030.0, 1520.0), Point(3030.0, 730.0)]))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(1130.0, 410.0, 1630.0, 3360.0)))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3610.0, 595.0), Point(3610.0, 1340.0), Point(3805.0, 1340.0), Point(3805.0, 2075.0), Point(3655.0, 2075.0), Point(3655.0, 3170.0), Point(4020.0, 3170.0), Point(4020.0, 595.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(800.0, 220.0), Point(800.0, 835.0), Point(1070.0, 835.0), Point(1070.0, 220.0), Point(3130.0, 220.0), Point(3130.0, 850.0), Point(3390.0, 850.0), Point(3390.0, 220.0), Point(4320.0, 220.0), Point(4320.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3120.0, 2560.0), Point(3120.0, 3560.0), Point(1070.0, 3560.0), Point(1070.0, 2665.0), Point(810.0, 2665.0), Point(810.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(4320.0, 4000.0), Point(4320.0, 3560.0), Point(3380.0, 3560.0), Point(3380.0, 2560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2205.0, 945.0), Point(2205.0, 1235.0), Point(3150.0, 1235.0), Point(3150.0, 2045.0), Point(2210.0, 2045.0), Point(2210.0, 3040.0), Point(2470.0, 3040.0), Point(2470.0, 2215.0), Point(3340.0, 2215.0), Point(3340.0, 1845.0), Point(3535.0, 1845.0), Point(3535.0, 1515.0), Point(3340.0, 1515.0), Point(3340.0, 1045.0), Point(2470.0, 1045.0), Point(2470.0, 945.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1720.0, 665.0), Point(1720.0, 2220.0), Point(1690.0, 2220.0), Point(1690.0, 3160.0), Point(1955.0, 3160.0), Point(1955.0, 1810.0), Point(2925.0, 1810.0), Point(2925.0, 1550.0), Point(1955.0, 1550.0), Point(1955.0, 665.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(300.0, 690.0), Point(300.0, 1205.0), Point(1175.0, 1205.0), Point(1175.0, 2320.0), Point(300.0, 2320.0), Point(300.0, 2880.0), Point(560.0, 2880.0), Point(560.0, 2480.0), Point(1455.0, 2480.0), Point(1455.0, 1015.0), Point(560.0, 1015.0), Point(560.0, 690.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(285.0, 1410.0, 915.0, 2080.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(285.0, 1410.0, 915.0, 2080.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 4320.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 4320.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3655.0, 2075.0, 4020.0, 3170.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(620.0, 1755.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(2160.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(2160.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(3865.0, 2670.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4560.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 4390.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 4390.0, 3600.0)))

    # Ports
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(620.0, 1755.0, 620.0, 1755.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(2160.0, 3780.0, 2160.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(2160.0, 0.0, 2160.0, 0.0), direction='GROUND'))
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(3865.0, 2670.0, 3865.0, 2670.0)))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_dlygate4sd3_1', sg13g2_tech)
    c.write_gds("sg13g2_dlygate4sd3_1.gds")
