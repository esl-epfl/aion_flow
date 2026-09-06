# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_a21oi_1
# ================================================================

"""Generated AION cell for sg13g2_a21oi_1."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 2400.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 2400.0, 3780.0))

    # Activ
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2400.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2400.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(305.0, 700.0, 2135.0, 1440.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(305.0, 2060.0, 2135.0, 3180.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1395.0, 2950.0, 1555.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(375.0, 2950.0, 535.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(375.0, 2610.0, 535.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 2610.0, 2065.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 2270.0, 2065.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 770.0, 2065.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(885.0, 2950.0, 1045.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 1670.0, 2065.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 1110.0, 2065.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1225.0, 1670.0, 1385.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 2950.0, 2065.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(885.0, 1110.0, 1045.0, 1270.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(885.0, 770.0, 1045.0, 930.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(885.0, 2610.0, 1045.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(375.0, 2270.0, 535.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(375.0, 1670.0, 535.0, 1830.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(375.0, 770.0, 535.0, 930.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1665.0, 520.0), Point(1665.0, 3360.0), Point(1795.0, 3360.0), Point(1795.0, 1900.0), Point(2135.0, 1900.0), Point(2135.0, 1600.0), Point(1795.0, 1600.0), Point(1795.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1155.0, 520.0), Point(1155.0, 3360.0), Point(1285.0, 3360.0), Point(1285.0, 1900.0), Point(1455.0, 1900.0), Point(1455.0, 1600.0), Point(1285.0, 1600.0), Point(1285.0, 520.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(645.0, 520.0), Point(645.0, 1600.0), Point(305.0, 1600.0), Point(305.0, 1900.0), Point(645.0, 1900.0), Point(645.0, 3360.0), Point(775.0, 3360.0), Point(775.0, 520.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1770.0, 1500.0, 2115.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(325.0, 1345.0, 600.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1320.0, 1345.0, 1580.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(325.0, 2080.0, 620.0, 3160.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1345.0, 2900.0), Point(1345.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(1605.0, 3560.0), Point(1605.0, 2900.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1855.0, 2080.0), Point(1855.0, 2555.0), Point(835.0, 2555.0), Point(835.0, 3160.0), Point(1095.0, 3160.0), Point(1095.0, 2715.0), Point(1855.0, 2715.0), Point(1855.0, 3160.0), Point(2115.0, 3160.0), Point(2115.0, 2080.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1320.0, 1345.0), Point(1320.0, 1620.0), Point(1175.0, 1620.0), Point(1175.0, 1880.0), Point(1580.0, 1880.0), Point(1580.0, 1345.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(325.0, 220.0), Point(325.0, 980.0), Point(585.0, 980.0), Point(585.0, 220.0), Point(1855.0, 220.0), Point(1855.0, 1320.0), Point(2115.0, 1320.0), Point(2115.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(835.0, 720.0), Point(835.0, 2080.0), Point(325.0, 2080.0), Point(325.0, 3160.0), Point(620.0, 3160.0), Point(620.0, 2290.0), Point(995.0, 2290.0), Point(995.0, 1320.0), Point(1095.0, 1320.0), Point(1095.0, 720.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(325.0, 1345.0, 600.0, 1880.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1770.0, 1500.0, 2115.0, 1880.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1180.0, 3800.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1205.0, 5.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A2', Point(1910.0, 1750.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A1', Point(1440.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B1', Point(480.0, 1682.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(470.0, 2620.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2640.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2470.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))

    # Ports
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1180.0, 3800.0, 1180.0, 3800.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1205.0, 5.0, 1205.0, 5.0), direction='GROUND'))
    cell.add_port(Port('A2', 'A2', tech['Metal1'], Rect.from_lbrt(1910.0, 1750.0, 1910.0, 1750.0)))
    cell.add_port(Port('A1', 'A1', tech['Metal1'], Rect.from_lbrt(1440.0, 1680.0, 1440.0, 1680.0)))
    cell.add_port(Port('B1', 'B1', tech['Metal1'], Rect.from_lbrt(480.0, 1682.0, 480.0, 1682.0)))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(470.0, 2620.0, 470.0, 2620.0), direction='OUTPUT'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_a21oi_1', sg13g2_tech)
    c.write_gds("sg13g2_a21oi_1.gds")
