# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_decap_8
# ================================================================

"""Generated AION cell for sg13g2_decap_8."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(165.0, 2185.0, 3225.0, 3185.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 3360.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(155.0, 650.0, 3215.0, 1070.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 3360.0, 150.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, 3700.0, 3200.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(3040.0, -80.0, 3200.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2995.0, 2955.0, 3155.0, 3115.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(235.0, 2955.0, 395.0, 3115.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1905.0, 1555.0, 2065.0, 1715.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2995.0, 2615.0, 3155.0, 2775.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2630.0, 1560.0, 2790.0, 1720.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1605.0, 780.0, 1765.0, 940.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1615.0, 2955.0, 1775.0, 3115.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1300.0, 1555.0, 1460.0, 1715.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2985.0, 780.0, 3145.0, 940.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(590.0, 1560.0, 750.0, 1720.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(225.0, 780.0, 385.0, 940.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1615.0, 2615.0, 1775.0, 2775.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(235.0, 2615.0, 395.0, 2775.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2995.0, 2275.0, 3155.0, 2435.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(235.0, 2275.0, 395.0, 2435.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1615.0, 2275.0, 1775.0, 2435.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, 3700.0, 2240.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2080.0, -80.0, 2240.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, 3700.0, 2720.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(2560.0, -80.0, 2720.0, 80.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(495.0, 470.0), Point(495.0, 1250.0), Point(1220.0, 1250.0), Point(1220.0, 1805.0), Point(2155.0, 1805.0), Point(2155.0, 1250.0), Point(2875.0, 1250.0), Point(2875.0, 470.0), Point(1875.0, 470.0), Point(1875.0, 1415.0), Point(1495.0, 1415.0), Point(1495.0, 470.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(2555.0, 1480.0), Point(2555.0, 2005.0), Point(1885.0, 2005.0), Point(1885.0, 3365.0), Point(2885.0, 3365.0), Point(2885.0, 1480.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(505.0, 1480.0), Point(505.0, 3365.0), Point(1505.0, 3365.0), Point(1505.0, 2005.0), Point(835.0, 2005.0), Point(835.0, 1480.0)]))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(175.0, 220.0), Point(175.0, 990.0), Point(520.0, 990.0), Point(520.0, 1810.0), Point(810.0, 1810.0), Point(810.0, 220.0), Point(1530.0, 220.0), Point(1530.0, 1030.0), Point(1835.0, 1030.0), Point(1835.0, 220.0), Point(2585.0, 220.0), Point(2585.0, 1810.0), Point(2835.0, 1810.0), Point(2835.0, 990.0), Point(3195.0, 990.0), Point(3195.0, 220.0), Point(3360.0, 220.0), Point(3360.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1220.0, 1475.0), Point(1220.0, 3560.0), Point(445.0, 3560.0), Point(445.0, 2205.0), Point(185.0, 2205.0), Point(185.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(3360.0, 4000.0), Point(3360.0, 3560.0), Point(3205.0, 3560.0), Point(3205.0, 2210.0), Point(2945.0, 2210.0), Point(2945.0, 3560.0), Point(2155.0, 3560.0), Point(2155.0, 1475.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 3360.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 3360.0, 220.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1680.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1680.0, 0.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 3600.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 3430.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 3430.0, 3600.0)))

    # Ports
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1680.0, 3780.0, 1680.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1680.0, 0.0, 1680.0, 0.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_decap_8', sg13g2_tech)
    c.write_gds("sg13g2_decap_8.gds")
