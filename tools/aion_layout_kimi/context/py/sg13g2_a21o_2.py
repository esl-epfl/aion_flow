# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_a21o_2
# ================================================================

"""Generated AION cell for sg13g2_a21o_2."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3840.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3840.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1790.0, 700.0, 3670.0, 1440.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(1785.0, 2180.0, 3670.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(255.0, 2110.0, 1575.0, 3230.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(255.0, 700.0, 1575.0, 1440.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3440.0, 2250.0, 3600.0, 2410.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3440.0, 1110.0, 3600.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3270.0, 1770.0, 3430.0, 1930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3440.0, 2600.0, 3600.0, 2760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3440.0, 2950.0, 3600.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2930.0, 2600.0, 3090.0, 2760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2930.0, 2950.0, 3090.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2775.0, 1755.0, 2935.0, 1915.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2545.0, 770.0, 2705.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2545.0, 1110.0, 2705.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3440.0, 770.0, 3600.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2235.0, 1720.0, 2395.0, 1880.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1980.0, 770.0, 2140.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1860.0, 2250.0, 2020.0, 2410.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1860.0, 2600.0, 2020.0, 2760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1860.0, 2950.0, 2020.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1345.0, 2320.0, 1505.0, 2480.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1345.0, 2660.0, 1505.0, 2820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1345.0, 3000.0, 1505.0, 3160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1345.0, 770.0, 1505.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1345.0, 1110.0, 1505.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1285.0, 1720.0, 1445.0, 1880.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(835.0, 2320.0, 995.0, 2480.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2380.0, 2950.0, 2540.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2380.0, 2600.0, 2540.0, 2760.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2380.0, 2250.0, 2540.0, 2410.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(835.0, 2660.0, 995.0, 2820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(835.0, 3000.0, 995.0, 3160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(835.0, 770.0, 995.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(835.0, 1110.0, 995.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(325.0, 2320.0, 485.0, 2480.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(325.0, 2660.0, 485.0, 2820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(325.0, 3000.0, 485.0, 3160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(325.0, 770.0, 485.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(325.0, 1110.0, 485.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3200.0, 520.0), Point(3200.0, 3360.0), Point(3330.0, 3360.0), Point(3330.0, 2000.0), Point(3500.0, 2000.0), Point(3500.0, 1700.0), Point(3330.0, 1700.0), Point(3330.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2815.0, 520.0), Point(2815.0, 1650.0), Point(2690.0, 1650.0), Point(2690.0, 3360.0), Point(2820.0, 3360.0), Point(2820.0, 2000.0), Point(3020.0, 2000.0), Point(3020.0, 1670.0), Point(2945.0, 1670.0), Point(2945.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2305.0, 520.0), Point(2305.0, 1650.0), Point(2135.0, 1650.0), Point(2135.0, 3360.0), Point(2265.0, 3360.0), Point(2265.0, 1950.0), Point(2480.0, 1950.0), Point(2480.0, 1650.0), Point(2435.0, 1650.0), Point(2435.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(595.0, 520.0), Point(595.0, 3410.0), Point(725.0, 3410.0), Point(725.0, 1950.0), Point(1105.0, 1950.0), Point(1105.0, 3410.0), Point(1235.0, 3410.0), Point(1235.0, 1950.0), Point(1515.0, 1950.0), Point(1515.0, 1650.0), Point(1235.0, 1650.0), Point(1235.0, 520.0), Point(1105.0, 520.0), Point(1105.0, 1650.0), Point(725.0, 1650.0), Point(725.0, 520.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2725.0, 1560.0, 3020.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3200.0, 1560.0, 3545.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2230.0, 1560.0, 2480.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(785.0, 2270.0, 1080.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(275.0, 220.0), Point(275.0, 1320.0), Point(535.0, 1320.0), Point(535.0, 220.0), Point(1295.0, 220.0), Point(1295.0, 1320.0), Point(1555.0, 1320.0), Point(1555.0, 220.0), Point(1935.0, 220.0), Point(1935.0, 990.0), Point(2195.0, 990.0), Point(2195.0, 220.0), Point(3390.0, 220.0), Point(3390.0, 1320.0), Point(3650.0, 1320.0), Point(3650.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(275.0, 2270.0), Point(275.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(1555.0, 3560.0), Point(1555.0, 2270.0), Point(1295.0, 2270.0), Point(1295.0, 3560.0), Point(535.0, 3560.0), Point(535.0, 2270.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2330.0, 2200.0), Point(2330.0, 3160.0), Point(2590.0, 3160.0), Point(2590.0, 2360.0), Point(3390.0, 2360.0), Point(3390.0, 3160.0), Point(3650.0, 3160.0), Point(3650.0, 2200.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2495.0, 720.0), Point(2495.0, 1220.0), Point(1810.0, 1220.0), Point(1810.0, 1670.0), Point(1235.0, 1670.0), Point(1235.0, 1930.0), Point(1810.0, 1930.0), Point(1810.0, 3160.0), Point(2070.0, 3160.0), Point(2070.0, 2170.0), Point(2050.0, 2170.0), Point(2050.0, 1380.0), Point(2755.0, 1380.0), Point(2755.0, 720.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(785.0, 720.0), Point(785.0, 3160.0), Point(1080.0, 3160.0), Point(1080.0, 2270.0), Point(1045.0, 2270.0), Point(1045.0, 720.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3200.0, 1560.0, 3545.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2880.0, 2550.0, 3140.0, 3560.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2725.0, 1560.0, 3020.0, 2000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2230.0, 1560.0, 2535.0, 2000.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'B1', Point(2400.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(930.0, 2495.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1665.0, 3785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1645.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A1', Point(2880.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A2', Point(3360.0, 1680.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3960.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3910.0, 180.0)))

    # Ports
    cell.add_port(Port('B1', 'B1', tech['Metal1'], Rect.from_lbrt(2400.0, 1680.0, 2400.0, 1680.0)))
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(930.0, 2495.0, 930.0, 2495.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1665.0, 3785.0, 1665.0, 3785.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1645.0, 0.0, 1645.0, 0.0), direction='GROUND'))
    cell.add_port(Port('A1', 'A1', tech['Metal1'], Rect.from_lbrt(2880.0, 1680.0, 2880.0, 1680.0)))
    cell.add_port(Port('A2', 'A2', tech['Metal1'], Rect.from_lbrt(3360.0, 1680.0, 3360.0, 1680.0)))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_a21o_2', sg13g2_tech)
    c.write_gds("sg13g2_a21o_2.gds")
