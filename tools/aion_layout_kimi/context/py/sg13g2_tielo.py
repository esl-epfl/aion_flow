# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_tielo
# ================================================================

"""Generated AION cell for sg13g2_tielo."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(885.0, 2255.0), Point(885.0, 2470.0), Point(295.0, 2470.0), Point(295.0, 2770.0), Point(855.0, 2770.0), Point(855.0, 3040.0), Point(295.0, 3040.0), Point(295.0, 3630.0), Point(0.0, 3630.0), Point(0.0, 3930.0), Point(1920.0, 3930.0), Point(1920.0, 3630.0), Point(1015.0, 3630.0), Point(1015.0, 3300.0), Point(1585.0, 3300.0), Point(1585.0, 2255.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(0.0, -150.0), Point(0.0, 150.0), Point(295.0, 150.0), Point(295.0, 705.0), Point(835.0, 705.0), Point(835.0, 975.0), Point(295.0, 975.0), Point(295.0, 1360.0), Point(1585.0, 1360.0), Point(1585.0, 480.0), Point(1015.0, 480.0), Point(1015.0, 150.0), Point(1920.0, 150.0), Point(1920.0, -150.0)]))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(570.0, 355.0, 730.0, 515.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1370.0, 1510.0, 1530.0, 1670.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1355.0, 2665.0, 1515.0, 2825.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1355.0, 2325.0, 1515.0, 2485.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1355.0, 1030.0, 1515.0, 1190.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1355.0, 550.0, 1515.0, 710.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(540.0, 3220.0, 700.0, 3380.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(925.0, 1850.0, 1085.0, 2010.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(365.0, 2540.0, 525.0, 2700.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(365.0, 2160.0, 525.0, 2320.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(365.0, 1090.0, 525.0, 1250.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(1115.0, 290.0), Point(1115.0, 1570.0), Point(1300.0, 1570.0), Point(1300.0, 1705.0), Point(1305.0, 1705.0), Point(1305.0, 1710.0), Point(1310.0, 1710.0), Point(1310.0, 1715.0), Point(1315.0, 1715.0), Point(1315.0, 1720.0), Point(1320.0, 1720.0), Point(1320.0, 1725.0), Point(1325.0, 1725.0), Point(1325.0, 1730.0), Point(1330.0, 1730.0), Point(1330.0, 1735.0), Point(1335.0, 1735.0), Point(1335.0, 1740.0), Point(1600.0, 1740.0), Point(1600.0, 1440.0), Point(1245.0, 1440.0), Point(1245.0, 290.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(855.0, 1780.0), Point(855.0, 2080.0), Point(1115.0, 2080.0), Point(1115.0, 3490.0), Point(1245.0, 3490.0), Point(1245.0, 1935.0), Point(1155.0, 1935.0), Point(1155.0, 1815.0), Point(1150.0, 1815.0), Point(1150.0, 1810.0), Point(1145.0, 1810.0), Point(1145.0, 1805.0), Point(1140.0, 1805.0), Point(1140.0, 1800.0), Point(1135.0, 1800.0), Point(1135.0, 1795.0), Point(1130.0, 1795.0), Point(1130.0, 1790.0), Point(1125.0, 1790.0), Point(1125.0, 1785.0), Point(1120.0, 1785.0), Point(1120.0, 1780.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(635.0, 785.0), Point(635.0, 1440.0), Point(545.0, 1440.0), Point(545.0, 2090.0), Point(295.0, 2090.0), Point(295.0, 2390.0), Point(635.0, 2390.0), Point(635.0, 2960.0), Point(765.0, 2960.0), Point(765.0, 2260.0), Point(675.0, 2260.0), Point(675.0, 1570.0), Point(765.0, 1570.0), Point(765.0, 785.0)]))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1095.0, 485.0), Point(1095.0, 775.0), Point(1295.0, 775.0), Point(1295.0, 1230.0), Point(1585.0, 1230.0), Point(1585.0, 485.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(455.0, 3165.0), Point(455.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(1920.0, 4000.0), Point(1920.0, 3560.0), Point(780.0, 3560.0), Point(780.0, 3165.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(465.0, 220.0), Point(465.0, 605.0), Point(815.0, 605.0), Point(815.0, 220.0), Point(1920.0, 220.0), Point(1920.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(315.0, 1030.0), Point(315.0, 1290.0), Point(875.0, 1290.0), Point(875.0, 2060.0), Point(1115.0, 2060.0), Point(1115.0, 1030.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1305.0, 1460.0, 1580.0, 2875.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(315.0, 2110.0, 575.0, 2760.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1295.0, 485.0, 1585.0, 1230.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 1920.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 1920.0, 220.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'L_LO', Point(1435.0, 1020.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(985.0, 3785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(940.0, 0.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2160.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 1990.0, 180.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 1990.0, 3600.0)))

    # Ports
    cell.add_port(Port('L_LO', 'L_LO', tech['Metal1'], Rect.from_lbrt(1435.0, 1020.0, 1435.0, 1020.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(985.0, 3785.0, 985.0, 3785.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(940.0, 0.0, 940.0, 0.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_tielo', sg13g2_tech)
    c.write_gds("sg13g2_tielo.gds")
