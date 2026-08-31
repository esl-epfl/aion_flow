# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_a21oi_2
# ================================================================

"""Generated AION cell for sg13g2_a21oi_2."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(235.0, 700.0, 3595.0, 1440.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(235.0, 2060.0, 3595.0, 3180.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(815.0, 1110.0, 975.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3365.0, 770.0, 3525.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3365.0, 2950.0, 3525.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2855.0, 770.0, 3015.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2855.0, 1110.0, 3015.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2855.0, 2130.0, 3015.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2855.0, 2555.0, 3015.0, 2715.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2345.0, 770.0, 2505.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2345.0, 2610.0, 2505.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2345.0, 2950.0, 2505.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3365.0, 1110.0, 3525.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2090.0, 1670.0, 2250.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1835.0, 770.0, 1995.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3355.0, 1670.0, 3515.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1835.0, 2950.0, 1995.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1495.0, 1670.0, 1655.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1325.0, 790.0, 1485.0, 950.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1325.0, 1130.0, 1485.0, 1290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1325.0, 2610.0, 1485.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1325.0, 2950.0, 1485.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1155.0, 1670.0, 1315.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(815.0, 770.0, 975.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(815.0, 2950.0, 975.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(560.0, 1670.0, 720.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(305.0, 770.0, 465.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(305.0, 1110.0, 465.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(305.0, 2610.0, 465.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3365.0, 2610.0, 3525.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(305.0, 2950.0, 465.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2105.0, 520.0), Point(2105.0, 1600.0), Point(2020.0, 1600.0), Point(2020.0, 1900.0), Point(2105.0, 1900.0), Point(2105.0, 3360.0), Point(2235.0, 3360.0), Point(2235.0, 1900.0), Point(2320.0, 1900.0), Point(2320.0, 1600.0), Point(2235.0, 1600.0), Point(2235.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(575.0, 520.0), Point(575.0, 1600.0), Point(490.0, 1600.0), Point(490.0, 1900.0), Point(575.0, 1900.0), Point(575.0, 3360.0), Point(705.0, 3360.0), Point(705.0, 1900.0), Point(790.0, 1900.0), Point(790.0, 1600.0), Point(705.0, 1600.0), Point(705.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2615.0, 520.0), Point(2615.0, 3360.0), Point(2745.0, 3360.0), Point(2745.0, 1900.0), Point(3125.0, 1900.0), Point(3125.0, 3360.0), Point(3255.0, 3360.0), Point(3255.0, 1900.0), Point(3585.0, 1900.0), Point(3585.0, 1600.0), Point(3255.0, 1600.0), Point(3255.0, 520.0), Point(3125.0, 520.0), Point(3125.0, 1600.0), Point(2745.0, 1600.0), Point(2745.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1085.0, 520.0), Point(1085.0, 3360.0), Point(1215.0, 3360.0), Point(1215.0, 1900.0), Point(1595.0, 1900.0), Point(1595.0, 3360.0), Point(1725.0, 3360.0), Point(1725.0, 520.0), Point(1595.0, 520.0), Point(1595.0, 1600.0), Point(1215.0, 1600.0), Point(1215.0, 520.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2760.0, 1160.0, 3045.0, 2765.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(255.0, 1600.0, 770.0, 2315.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3240.0, 1625.0, 3575.0, 2280.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1085.0, 1560.0, 1725.0, 1900.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(255.0, 220.0), Point(255.0, 1320.0), Point(515.0, 1320.0), Point(515.0, 220.0), Point(2295.0, 220.0), Point(2295.0, 980.0), Point(2555.0, 980.0), Point(2555.0, 220.0), Point(3315.0, 220.0), Point(3315.0, 1320.0), Point(3575.0, 1320.0), Point(3575.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(765.0, 2950.0), Point(765.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(2045.0, 3560.0), Point(2045.0, 2950.0), Point(1785.0, 2950.0), Point(1785.0, 3560.0), Point(1025.0, 3560.0), Point(1025.0, 2950.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3315.0, 2560.0), Point(3315.0, 2965.0), Point(2555.0, 2965.0), Point(2555.0, 2565.0), Point(255.0, 2565.0), Point(255.0, 3160.0), Point(515.0, 3160.0), Point(515.0, 2765.0), Point(1275.0, 2765.0), Point(1275.0, 3160.0), Point(1535.0, 3160.0), Point(1535.0, 2765.0), Point(2295.0, 2765.0), Point(2295.0, 3160.0), Point(3575.0, 3160.0), Point(3575.0, 2560.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2805.0, 720.0), Point(2805.0, 1160.0), Point(1535.0, 1160.0), Point(1535.0, 785.0), Point(1275.0, 785.0), Point(1275.0, 1320.0), Point(2760.0, 1320.0), Point(2760.0, 2765.0), Point(3045.0, 2765.0), Point(3045.0, 720.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(765.0, 445.0), Point(765.0, 1320.0), Point(1025.0, 1320.0), Point(1025.0, 605.0), Point(1785.0, 605.0), Point(1785.0, 980.0), Point(2045.0, 980.0), Point(2045.0, 445.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(255.0, 1600.0), Point(255.0, 2315.0), Point(2300.0, 2315.0), Point(2300.0, 1600.0), Point(2040.0, 1600.0), Point(2040.0, 2090.0), Point(770.0, 2090.0), Point(770.0, 1600.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(3240.0, 1625.0, 3575.0, 2280.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1085.0, 1560.0, 1725.0, 1900.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(2935.0, 1720.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A2', Point(575.0, 1950.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A1', Point(1405.0, 1735.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1725.0, -20.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B1', Point(3425.0, 1950.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1585.0, 3780.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3910.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3910.0, 3600.0)))

    # Ports
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(2935.0, 1720.0, 2935.0, 1720.0), direction='OUTPUT'))
    cell.add_port(Port('A2', 'A2', tech['Metal1'], Rect.from_lbrt(575.0, 1950.0, 575.0, 1950.0)))
    cell.add_port(Port('A1', 'A1', tech['Metal1'], Rect.from_lbrt(1405.0, 1735.0, 1405.0, 1735.0)))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1725.0, -20.0, 1725.0, -20.0), direction='GROUND'))
    cell.add_port(Port('B1', 'B1', tech['Metal1'], Rect.from_lbrt(3425.0, 1950.0, 3425.0, 1950.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1585.0, 3780.0, 1585.0, 3780.0), direction='POWER'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_a21oi_2', sg13g2_tech)
    c.write_gds("sg13g2_a21oi_2.gds")
