# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_buf_4
# ================================================================

"""Generated AION cell for sg13g2_buf_4."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(215.0, 2060.0), Point(215.0, 3180.0), Point(2525.0, 3180.0), Point(2525.0, 2900.0), Point(3575.0, 2900.0), Point(3575.0, 2060.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3840.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3840.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(215.0, 590.0, 3575.0, 1330.0)))

    # Cont
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(285.0, 1000.0, 445.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2905.0, 1655.0, 3065.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2070.0, 1590.0, 2230.0, 1750.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1730.0, 1590.0, 1890.0, 1750.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(795.0, 1000.0, 955.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(795.0, 660.0, 955.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2835.0, 2200.0, 2995.0, 2360.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3345.0, 1000.0, 3505.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3345.0, 660.0, 3505.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(795.0, 2950.0, 955.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(795.0, 2540.0, 955.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(795.0, 2130.0, 955.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1815.0, 1000.0, 1975.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1815.0, 660.0, 1975.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(285.0, 660.0, 445.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1305.0, 660.0, 1465.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2765.0, 660.0, 2925.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(285.0, 2950.0, 445.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(285.0, 2540.0, 445.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(285.0, 2130.0, 445.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1305.0, 2950.0, 1465.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1305.0, 2540.0, 1465.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1815.0, 2950.0, 1975.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1815.0, 2540.0, 1975.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1815.0, 2130.0, 1975.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2425.0, 660.0, 2585.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2325.0, 2540.0, 2485.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2325.0, 2130.0, 2485.0, 2290.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3345.0, 2670.0, 3505.0, 2830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2835.0, 2540.0, 2995.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3105.0, 410.0), Point(3105.0, 1570.0), Point(2820.0, 1570.0), Point(2820.0, 1750.0), Point(2595.0, 1750.0), Point(2595.0, 3080.0), Point(2725.0, 3080.0), Point(2725.0, 1900.0), Point(3105.0, 1900.0), Point(3105.0, 3080.0), Point(3235.0, 3080.0), Point(3235.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(555.0, 410.0), Point(555.0, 3360.0), Point(685.0, 3360.0), Point(685.0, 1670.0), Point(1065.0, 1670.0), Point(1065.0, 3360.0), Point(1195.0, 3360.0), Point(1195.0, 1670.0), Point(1575.0, 1670.0), Point(1575.0, 3360.0), Point(1705.0, 3360.0), Point(1705.0, 1820.0), Point(2085.0, 1820.0), Point(2085.0, 3360.0), Point(2215.0, 3360.0), Point(2215.0, 1820.0), Point(2300.0, 1820.0), Point(2300.0, 1520.0), Point(2215.0, 1520.0), Point(2215.0, 410.0), Point(2085.0, 410.0), Point(2085.0, 1520.0), Point(1705.0, 1520.0), Point(1705.0, 410.0), Point(1575.0, 410.0), Point(1575.0, 1520.0), Point(1195.0, 1520.0), Point(1195.0, 410.0), Point(1065.0, 410.0), Point(1065.0, 1520.0), Point(685.0, 1520.0), Point(685.0, 410.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2700.0, 1475.0, 3150.0, 1885.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(320.0, 1525.0, 1005.0, 1840.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(745.0, 605.0), Point(745.0, 1525.0), Point(320.0, 1525.0), Point(320.0, 1840.0), Point(745.0, 1840.0), Point(745.0, 3130.0), Point(1005.0, 3130.0), Point(1005.0, 2165.0), Point(1765.0, 2165.0), Point(1765.0, 3130.0), Point(2025.0, 3130.0), Point(2025.0, 1995.0), Point(1005.0, 1995.0), Point(1005.0, 1225.0), Point(2025.0, 1225.0), Point(2025.0, 645.0), Point(1765.0, 645.0), Point(1765.0, 1065.0), Point(1005.0, 1065.0), Point(1005.0, 605.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3245.0, 640.0), Point(3245.0, 1050.0), Point(2265.0, 1050.0), Point(2265.0, 1540.0), Point(1680.0, 1540.0), Point(1680.0, 1800.0), Point(2430.0, 1800.0), Point(2430.0, 1210.0), Point(3400.0, 1210.0), Point(3400.0, 2150.0), Point(2785.0, 2150.0), Point(2785.0, 2770.0), Point(3045.0, 2770.0), Point(3045.0, 2420.0), Point(3590.0, 2420.0), Point(3590.0, 640.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2275.0, 2080.0), Point(2275.0, 3560.0), Point(1515.0, 3560.0), Point(1515.0, 2490.0), Point(1255.0, 2490.0), Point(1255.0, 3560.0), Point(495.0, 3560.0), Point(495.0, 2115.0), Point(235.0, 2115.0), Point(235.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(3555.0, 3560.0), Point(3555.0, 2640.0), Point(3295.0, 2640.0), Point(3295.0, 3560.0), Point(2535.0, 3560.0), Point(2535.0, 2080.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(235.0, 220.0), Point(235.0, 1210.0), Point(495.0, 1210.0), Point(495.0, 220.0), Point(1255.0, 220.0), Point(1255.0, 870.0), Point(1515.0, 870.0), Point(1515.0, 220.0), Point(2545.0, 220.0), Point(2545.0, 610.0), Point(2375.0, 610.0), Point(2375.0, 870.0), Point(2975.0, 870.0), Point(2975.0, 610.0), Point(2805.0, 610.0), Point(2805.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2700.0, 1475.0, 3150.0, 1885.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'X', Point(480.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1440.0, 0.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(2970.0, 1800.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(2330.0, 3780.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3910.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3910.0, 180.0)))

    # Ports
    cell.add_port(Port('X', 'X', tech['Metal1'], Rect.from_lbrt(480.0, 1680.0, 480.0, 1680.0)))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1440.0, 0.0, 1440.0, 0.0), direction='GROUND'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(2970.0, 1800.0, 2970.0, 1800.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(2330.0, 3780.0, 2330.0, 3780.0), direction='POWER'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_buf_4', sg13g2_tech)
    c.write_gds("sg13g2_buf_4.gds")
