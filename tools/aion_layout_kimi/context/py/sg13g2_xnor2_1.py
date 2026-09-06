# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_xnor2_1
# ================================================================

"""Generated AION cell for sg13g2_xnor2_1."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(1705.0, 2060.0), Point(1705.0, 2145.0), Point(290.0, 2145.0), Point(290.0, 2985.0), Point(1705.0, 2985.0), Point(1705.0, 3180.0), Point(3460.0, 3180.0), Point(3460.0, 2060.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(2245.0, 410.0), Point(2245.0, 590.0), Point(1705.0, 590.0), Point(1705.0, 1330.0), Point(3595.0, 1330.0), Point(3595.0, 590.0), Point(2545.0, 590.0), Point(2545.0, 410.0)]))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3840.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(290.0, 800.0, 1490.0, 1440.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3840.0, 150.0)))

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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, 3700.0, 3680.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3520.0, -80.0, 3680.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3365.0, 660.0, 3525.0, 820.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3055.0, 1605.0, 3215.0, 1765.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2855.0, 815.0, 3015.0, 975.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2720.0, 2270.0, 2880.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2720.0, 2610.0, 2880.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2720.0, 2950.0, 2880.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2425.0, 1655.0, 2585.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3230.0, 2610.0, 3390.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2315.0, 480.0, 2475.0, 640.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1895.0, 1655.0, 2055.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1775.0, 815.0, 1935.0, 975.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1775.0, 2610.0, 1935.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1775.0, 2950.0, 1935.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1325.0, 1655.0, 1485.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1260.0, 870.0, 1420.0, 1030.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1070.0, 2415.0, 1230.0, 2575.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3365.0, 1000.0, 3525.0, 1160.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1070.0, 2755.0, 1230.0, 2915.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 2415.0, 530.0, 2575.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(370.0, 2755.0, 530.0, 2915.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3230.0, 2950.0, 3390.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(375.0, 870.0, 535.0, 1030.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(375.0, 1210.0, 535.0, 1370.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(645.0, 310.0), Point(645.0, 2070.0), Point(830.0, 2070.0), Point(830.0, 3165.0), Point(960.0, 3165.0), Point(960.0, 1910.0), Point(775.0, 1910.0), Point(775.0, 440.0), Point(2045.0, 440.0), Point(2045.0, 1585.0), Point(1810.0, 1585.0), Point(1810.0, 1885.0), Point(2045.0, 1885.0), Point(2045.0, 3360.0), Point(2175.0, 3360.0), Point(2175.0, 310.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2615.0, 410.0), Point(2615.0, 1585.0), Point(2355.0, 1585.0), Point(2355.0, 1885.0), Point(2430.0, 1885.0), Point(2430.0, 3360.0), Point(2560.0, 3360.0), Point(2560.0, 1885.0), Point(2655.0, 1885.0), Point(2655.0, 1760.0), Point(2745.0, 1760.0), Point(2745.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(3125.0, 410.0), Point(3125.0, 1520.0), Point(2970.0, 1520.0), Point(2970.0, 1850.0), Point(2990.0, 1850.0), Point(2990.0, 3360.0), Point(3120.0, 3360.0), Point(3120.0, 1850.0), Point(3300.0, 1850.0), Point(3300.0, 1520.0), Point(3255.0, 1520.0), Point(3255.0, 410.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1020.0, 620.0), Point(1020.0, 1715.0), Point(1240.0, 1715.0), Point(1240.0, 1885.0), Point(1340.0, 1885.0), Point(1340.0, 3165.0), Point(1470.0, 3165.0), Point(1470.0, 1885.0), Point(1570.0, 1885.0), Point(1570.0, 1585.0), Point(1150.0, 1585.0), Point(1150.0, 620.0)]))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(320.0, 2365.0), Point(320.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3840.0, 4000.0), Point(3840.0, 3560.0), Point(3440.0, 3560.0), Point(3440.0, 2560.0), Point(3180.0, 2560.0), Point(3180.0, 3560.0), Point(1985.0, 3560.0), Point(1985.0, 2560.0), Point(1725.0, 2560.0), Point(1725.0, 3560.0), Point(580.0, 3560.0), Point(580.0, 2365.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(320.0, 220.0), Point(320.0, 1420.0), Point(585.0, 1420.0), Point(585.0, 220.0), Point(2265.0, 220.0), Point(2265.0, 650.0), Point(2525.0, 650.0), Point(2525.0, 220.0), Point(3840.0, 220.0), Point(3840.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(800.0, 835.0), Point(800.0, 2565.0), Point(1020.0, 2565.0), Point(1020.0, 2965.0), Point(1280.0, 2965.0), Point(1280.0, 2365.0), Point(960.0, 2365.0), Point(960.0, 995.0), Point(1210.0, 995.0), Point(1210.0, 1340.0), Point(2930.0, 1340.0), Point(2930.0, 1815.0), Point(3230.0, 1815.0), Point(3230.0, 1555.0), Point(3100.0, 1555.0), Point(3100.0, 1180.0), Point(1470.0, 1180.0), Point(1470.0, 835.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(2770.0, 790.0), Point(2770.0, 830.0), Point(2025.0, 830.0), Point(2025.0, 800.0), Point(1725.0, 800.0), Point(1725.0, 1000.0), Point(3065.0, 1000.0), Point(3065.0, 790.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(3315.0, 610.0), Point(3315.0, 1210.0), Point(3410.0, 1210.0), Point(3410.0, 2080.0), Point(2670.0, 2080.0), Point(2670.0, 3160.0), Point(3000.0, 3160.0), Point(3000.0, 2240.0), Point(3570.0, 2240.0), Point(3570.0, 610.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1240.0, 1525.0), Point(1240.0, 1900.0), Point(1420.0, 1900.0), Point(1420.0, 2240.0), Point(2480.0, 2240.0), Point(2480.0, 1865.0), Point(2635.0, 1865.0), Point(2635.0, 1605.0), Point(2320.0, 1605.0), Point(2320.0, 2080.0), Point(1580.0, 2080.0), Point(1580.0, 1525.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1760.0, 1525.0, 2075.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1240.0, 1525.0, 1580.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3840.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(2670.0, 2080.0, 3000.0, 3160.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1760.0, 1525.0, 2075.0, 1900.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3840.0, 4000.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(2820.0, 2575.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(1420.0, 1775.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1860.0, 3795.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(1920.0, 1750.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1880.0, 15.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 4080.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-80.0, -180.0, 3910.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-80.0, 1760.0, 3910.0, 3600.0)))

    # Ports
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(2820.0, 2575.0, 2820.0, 2575.0), direction='OUTPUT'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(1420.0, 1775.0, 1420.0, 1775.0), direction='INPUT'))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1860.0, 3795.0, 1860.0, 3795.0), direction='POWER'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(1920.0, 1750.0, 1920.0, 1750.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1880.0, 15.0, 1880.0, 15.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_xnor2_1', sg13g2_tech)
    c.write_gds("sg13g2_xnor2_1.gds")
