# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_nand3_1
# ================================================================

"""Generated AION cell for sg13g2_nand3_1."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(210.0, 610.0, 2090.0, 1350.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(260.0, 2130.0, 2090.0, 3250.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 2400.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 2400.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(330.0, 1020.0, 490.0, 1180.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1860.0, 3020.0, 2020.0, 3180.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1860.0, 2340.0, 2020.0, 2500.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1350.0, 2680.0, 1510.0, 2840.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1350.0, 3020.0, 1510.0, 3180.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1010.0, 1655.0, 1170.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(840.0, 2340.0, 1000.0, 2500.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(840.0, 2680.0, 1000.0, 2840.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1860.0, 1020.0, 2020.0, 1180.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(840.0, 3020.0, 1000.0, 3180.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(430.0, 1655.0, 590.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(330.0, 2340.0, 490.0, 2500.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(330.0, 2680.0, 490.0, 2840.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1805.0, 1655.0, 1965.0, 1815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1860.0, 680.0, 2020.0, 840.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(330.0, 3020.0, 490.0, 3180.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(330.0, 680.0, 490.0, 840.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1860.0, 2680.0, 2020.0, 2840.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1620.0, 430.0), Point(1620.0, 3430.0), Point(1750.0, 3430.0), Point(1750.0, 1900.0), Point(2035.0, 1900.0), Point(2035.0, 1585.0), Point(1750.0, 1585.0), Point(1750.0, 430.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1110.0, 430.0), Point(1110.0, 1585.0), Point(940.0, 1585.0), Point(940.0, 1900.0), Point(1110.0, 1900.0), Point(1110.0, 3430.0), Point(1240.0, 3430.0), Point(1240.0, 430.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(600.0, 430.0), Point(600.0, 1585.0), Point(360.0, 1585.0), Point(360.0, 1900.0), Point(600.0, 1900.0), Point(600.0, 3430.0), Point(730.0, 3430.0), Point(730.0, 430.0)]))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1810.0, 630.0), Point(1810.0, 975.0), Point(1400.0, 975.0), Point(1400.0, 2290.0), Point(790.0, 2290.0), Point(790.0, 3230.0), Point(1050.0, 3230.0), Point(1050.0, 2450.0), Point(1780.0, 2450.0), Point(1780.0, 3230.0), Point(2070.0, 3230.0), Point(2070.0, 2290.0), Point(1565.0, 2290.0), Point(1565.0, 1230.0), Point(2070.0, 1230.0), Point(2070.0, 630.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(280.0, 220.0), Point(280.0, 1230.0), Point(540.0, 1230.0), Point(540.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(280.0, 2290.0), Point(280.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(1560.0, 3560.0), Point(1560.0, 2630.0), Point(1300.0, 2630.0), Point(1300.0, 3560.0), Point(540.0, 3560.0), Point(540.0, 2290.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(300.0, 1505.0, 650.0, 1890.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(840.0, 1505.0, 1220.0, 1890.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1745.0, 1505.0, 2155.0, 1890.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(840.0, 1505.0, 1220.0, 1890.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(300.0, 1505.0, 650.0, 1890.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1745.0, 1505.0, 2155.0, 1890.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1780.0, 2290.0, 2070.0, 3230.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1225.0, 3785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'Y', Point(2020.0, 2740.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'B', Point(960.0, 1775.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'C', Point(520.0, 1770.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'A', Point(1920.0, 1680.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1200.0, 0.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2640.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2470.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))

    # Ports
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1225.0, 3785.0, 1225.0, 3785.0), direction='POWER'))
    cell.add_port(Port('Y', 'Y', tech['Metal1'], Rect.from_lbrt(2020.0, 2740.0, 2020.0, 2740.0), direction='OUTPUT'))
    cell.add_port(Port('B', 'B', tech['Metal1'], Rect.from_lbrt(960.0, 1775.0, 960.0, 1775.0), direction='INPUT'))
    cell.add_port(Port('C', 'C', tech['Metal1'], Rect.from_lbrt(520.0, 1770.0, 520.0, 1770.0), direction='INPUT'))
    cell.add_port(Port('A', 'A', tech['Metal1'], Rect.from_lbrt(1920.0, 1680.0, 1920.0, 1680.0), direction='INPUT'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1200.0, 0.0, 1200.0, 0.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_nand3_1', sg13g2_tech)
    c.write_gds("sg13g2_nand3_1.gds")
