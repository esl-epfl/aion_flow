# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_sighold
# ================================================================

"""Generated AION cell for sg13g2_sighold."""

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
    cell.add_shape(PolygonShape(tech['Activ'], [Point(155.0, 2130.0), Point(155.0, 2580.0), Point(695.0, 2580.0), Point(695.0, 2850.0), Point(155.0, 2850.0), Point(155.0, 3630.0), Point(0.0, 3630.0), Point(0.0, 3930.0), Point(2400.0, 3930.0), Point(2400.0, 3630.0), Point(2045.0, 3630.0), Point(2045.0, 2720.0), Point(920.0, 2720.0), Point(920.0, 2430.0), Point(2045.0, 2430.0), Point(2045.0, 2130.0)]))
    cell.add_shape(PolygonShape(tech['Activ'], [Point(0.0, -150.0), Point(0.0, 150.0), Point(155.0, 150.0), Point(155.0, 665.0), Point(720.0, 665.0), Point(720.0, 935.0), Point(155.0, 935.0), Point(155.0, 1235.0), Point(2045.0, 1235.0), Point(2045.0, 935.0), Point(935.0, 935.0), Point(935.0, 665.0), Point(2045.0, 665.0), Point(2045.0, 150.0), Point(2400.0, 150.0), Point(2400.0, -150.0)]))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 305.0, 800.0, 465.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1815.0, 1005.0, 1975.0, 1165.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1815.0, 2200.0, 1975.0, 2360.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1075.0, 1375.0, 1235.0, 1535.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(595.0, 1815.0, 755.0, 1975.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(225.0, 2200.0, 385.0, 2360.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(225.0, 1005.0, 385.0, 1165.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 310.0, 1280.0, 470.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(985.0, 3225.0, 1145.0, 3385.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1330.0, 3225.0, 1490.0, 3385.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1695.0, 3225.0, 1855.0, 3385.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 305.0, 1760.0, 465.0)))
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
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3225.0, 800.0, 3385.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(495.0, 755.0), Point(495.0, 2760.0), Point(625.0, 2760.0), Point(625.0, 2045.0), Point(825.0, 2045.0), Point(825.0, 1745.0), Point(625.0, 1745.0), Point(625.0, 755.0)]))
    cell.add_shape(RectShape(tech['GatPoly'], Rect.from_lbrt(1005.0, 755.0, 1705.0, 2630.0)))

    # Metal1
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(570.0, 3170.0), Point(570.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(2400.0, 4000.0), Point(2400.0, 3560.0), Point(1925.0, 3560.0), Point(1925.0, 3170.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(555.0, 220.0), Point(555.0, 545.0), Point(1830.0, 545.0), Point(1830.0, 220.0), Point(2400.0, 220.0), Point(2400.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1805.0, 955.0), Point(1805.0, 1765.0), Point(585.0, 1765.0), Point(585.0, 2025.0), Point(1805.0, 2025.0), Point(1805.0, 2410.0), Point(2045.0, 2410.0), Point(2045.0, 955.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(175.0, 955.0), Point(175.0, 2410.0), Point(405.0, 2410.0), Point(405.0, 1585.0), Point(1245.0, 1585.0), Point(1245.0, 1325.0), Point(395.0, 1325.0), Point(395.0, 955.0)]))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(1805.0, 955.0, 2045.0, 2410.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 2400.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 2400.0, 220.0)))
    cell.add_shape(TextShape(tech['Metal1'], 'SH', Point(1915.0, 1740.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(1715.0, 3785.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1620.0, 0.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2640.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, 1760.0, 2470.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 2470.0, 180.0)))

    # Ports
    cell.add_port(Port('SH', 'SH', tech['Metal1'], Rect.from_lbrt(1915.0, 1740.0, 1915.0, 1740.0)))
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(1715.0, 3785.0, 1715.0, 3785.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1620.0, 0.0, 1620.0, 0.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_sighold', sg13g2_tech)
    c.write_gds("sg13g2_sighold.gds")
