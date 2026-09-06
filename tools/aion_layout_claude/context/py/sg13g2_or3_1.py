# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_or3_1
# ================================================================

"""Generated AION cell for sg13g2_or3_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(365.0, 2060.0), Point(365.0, 3060.0), Point(2140.0, 3060.0), Point(2140.0, 3180.0), Point(2980.0, 3180.0), Point(2980.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(365.0, 590.0), Point(365.0, 1140.0), Point(2265.0, 1140.0), Point(2265.0, 1330.0), Point(3045.0, 1330.0), Point(3045.0, 590.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3360.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3360.0, 150.0)))

    # Cont
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2240.0, 2490.0, 2400.0, 2650.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1900.0, 2490.0, 2060.0, 2650.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(580.0, 1655.0, 740.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1825.0, 1655.0, 1985.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1175.0, 1655.0, 1335.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2465.0, 1605.0, 2625.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(435.0, 660.0, 595.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(945.0, 660.0, 1105.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1795.0, 660.0, 1955.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1455.0, 660.0, 1615.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2305.0, 660.0, 2465.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2815.0, 1005.0, 2975.0, 1165.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2815.0, 665.0, 2975.0, 825.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(435.0, 2830.0, 595.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(435.0, 2490.0, 595.0, 2650.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2750.0, 2950.0, 2910.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2750.0, 2610.0, 2910.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2750.0, 2270.0, 2910.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2240.0, 2830.0, 2400.0, 2990.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1900.0, 2830.0, 2060.0, 2990.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(435.0, 2150.0, 595.0, 2310.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1215.0, 410.0), Point(1215.0, 1570.0), Point(1090.0, 1570.0), Point(1090.0, 1900.0), Point(1215.0, 1900.0), Point(1215.0, 3240.0), Point(1345.0, 3240.0), Point(1345.0, 1900.0), Point(1420.0, 1900.0), Point(1420.0, 1570.0), Point(1345.0, 1570.0), Point(1345.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(705.0, 410.0), Point(705.0, 1570.0), Point(495.0, 1570.0), Point(495.0, 1900.0), Point(705.0, 1900.0), Point(705.0, 3240.0), Point(835.0, 3240.0), Point(835.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2065.0, 410.0), Point(2065.0, 1570.0), Point(1660.0, 1570.0), Point(1660.0, 3240.0), Point(1790.0, 3240.0), Point(1790.0, 1900.0), Point(2195.0, 1900.0), Point(2195.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2575.0, 410.0), Point(2575.0, 1535.0), Point(2395.0, 1535.0), Point(2395.0, 1835.0), Point(2510.0, 1835.0), Point(2510.0, 3360.0), Point(2640.0, 3360.0), Point(2640.0, 1835.0), Point(2705.0, 1835.0), Point(2705.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(295.0, 1505.0, 835.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1090.0, 1505.0, 1560.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1740.0, 1505.0, 2070.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3360.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3360.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2700.0, 2220.0, 3050.0, 3160.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2760.0, 605.0), Point(2760.0, 1215.0), Point(2890.0, 1215.0), Point(2890.0, 2220.0), Point(2700.0, 2220.0), Point(2700.0, 3160.0), Point(3050.0, 3160.0), Point(3050.0, 605.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(385.0, 610.0), Point(385.0, 1325.0), Point(2345.0, 1325.0), Point(2345.0, 2090.0), Point(385.0, 2090.0), Point(385.0, 3040.0), Point(645.0, 3040.0), Point(645.0, 2295.0), Point(2515.0, 2295.0), Point(2515.0, 1850.0), Point(2710.0, 1850.0), Point(2710.0, 1520.0), Point(2515.0, 1520.0), Point(2515.0, 1115.0), Point(1965.0, 1115.0), Point(1965.0, 610.0), Point(1445.0, 610.0), Point(1445.0, 1110.0), Point(645.0, 1110.0), Point(645.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1850.0, 2475.0), Point(1850.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3360.0, 4000.0), Point(3360.0, 3560.0), Point(2450.0, 3560.0), Point(2450.0, 2475.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(895.0, 220.0), Point(895.0, 870.0), Point(1155.0, 870.0), Point(1155.0, 220.0), Point(2255.0, 220.0), Point(2255.0, 870.0), Point(2515.0, 870.0), Point(2515.0, 220.0), Point(3360.0, 220.0), Point(3360.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(295.0, 1505.0, 835.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1090.0, 1505.0, 1560.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1740.0, 1505.0, 2070.0, 1900.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1655.0, 3790.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1690.0, 5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(565.0, 1735.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(1335.0, 1695.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(1910.0, 1725.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(2865.0, 2770.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3600.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3430.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3430.0, 3600.0)))

    # Ports
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1655.0, 3790.0, 1655.0, 3790.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1690.0, 5.0, 1690.0, 5.0), direction='GROUND'))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(565.0, 1735.0, 565.0, 1735.0), direction='INPUT'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(1335.0, 1695.0, 1335.0, 1695.0), direction='INPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(1910.0, 1725.0, 1910.0, 1725.0), direction='INPUT'))
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(2865.0, 2770.0, 2865.0, 2770.0)))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_or3_1', sg13g2_tech)
    c.write_gds("sg13g2_or3_1.gds")
