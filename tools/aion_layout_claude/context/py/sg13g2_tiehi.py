# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_tiehi
# ================================================================

"""Generated AION cell for sg13g2_tiehi."""

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import PolygonShape, RectShape, TextShape
from aion_layout.tech import Tech

CELL_WIDTH = 1920.0
CELL_HEIGHT = 3780.0


def generate(name: str, tech: Tech) -> Cell:
    """Generate the cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, 1920.0, 3780.0))

    # Activ
    cell.add_shape(PolygonShape(tech['Activ'], [Point(115.0, 2145.0), Point(115.0, 2805.0), Point(705.0, 2805.0), Point(705.0, 3075.0), Point(115.0, 3075.0), Point(115.0, 3630.0), Point(0.0, 3630.0), Point(0.0, 3930.0), Point(1920.0, 3930.0), Point(1920.0, 3630.0), Point(1020.0, 3630.0), Point(1020.0, 3300.0), Point(1580.0, 3300.0), Point(1580.0, 2145.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(0.0, -150.0), Point(0.0, 150.0), Point(740.0, 150.0), Point(740.0, 975.0), Point(115.0, 975.0), Point(115.0, 1275.0), Point(1580.0, 1275.0), Point(1580.0, 480.0), Point(1010.0, 480.0), Point(1010.0, 150.0), Point(1920.0, 150.0), Point(1920.0, -150.0)]))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1400.0, 1745.0, 1560.0, 1905.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1350.0, 2215.0, 1510.0, 2375.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1350.0, 1035.0, 1510.0, 1195.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1350.0, 2655.0, 1510.0, 2815.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(915.0, 1415.0, 1075.0, 1575.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(185.0, 3145.0, 345.0, 3305.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(185.0, 1425.0, 345.0, 1585.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(185.0, 1045.0, 345.0, 1205.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(810.0, 550.0, 970.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(185.0, 2240.0, 345.0, 2400.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1330.0, 1675.0), Point(1330.0, 1830.0), Point(1110.0, 1830.0), Point(1110.0, 3490.0), Point(1240.0, 3490.0), Point(1240.0, 1975.0), Point(1630.0, 1975.0), Point(1630.0, 1675.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(485.0, 785.0), Point(485.0, 1355.0), Point(115.0, 1355.0), Point(115.0, 1655.0), Point(485.0, 1655.0), Point(485.0, 2995.0), Point(615.0, 2995.0), Point(615.0, 785.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1105.0, 300.0), Point(1105.0, 1345.0), Point(845.0, 1345.0), Point(845.0, 1645.0), Point(1145.0, 1645.0), Point(1145.0, 1490.0), Point(1235.0, 1490.0), Point(1235.0, 300.0)]))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(870.0, 1355.0), Point(870.0, 1815.0), Point(195.0, 1815.0), Point(195.0, 2190.0), Point(135.0, 2190.0), Point(135.0, 2450.0), Point(395.0, 2450.0), Point(395.0, 2030.0), Point(1120.0, 2030.0), Point(1120.0, 1355.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(760.0, 220.0), Point(760.0, 760.0), Point(1020.0, 760.0), Point(1020.0, 220.0), Point(1920.0, 220.0), Point(1920.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(135.0, 3095.0), Point(135.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(1920.0, 4000.0), Point(1920.0, 3560.0), Point(395.0, 3560.0), Point(395.0, 3095.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1300.0, 2165.0, 1585.0, 2910.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1300.0, 985.0, 1575.0, 1955.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(135.0, 995.0, 395.0, 1635.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1300.0, 2165.0, 1585.0, 2910.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 1920.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 1920.0, 220.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'L_HI', Point(1443.0, 2520.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(985.0, 3785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(940.0, 0.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2160.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 1990.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 1990.0, 180.0)))

    # Ports
    cell.add_port(Port('L_HI', 'L_HI', tech['Metal1'], Rect.from_lbrt(1443.0, 2520.0, 1443.0, 2520.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(985.0, 3785.0, 985.0, 3785.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(940.0, 0.0, 940.0, 0.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_tiehi', sg13g2_tech)
    c.write_gds("sg13g2_tiehi.gds")
