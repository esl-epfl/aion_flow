# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Auto-generated from GDS: sg13g2_decap_4
# ================================================================

"""Generated AION cell for sg13g2_decap_4."""

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
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, 3630.0, 1920.0, 3930.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(120.0, 2180.0, 1800.0, 3180.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(0.0, -150.0, 1920.0, 150.0)))
    cell.add_shape(RectShape(tech['Activ'], Rect.from_lbrt(120.0, 645.0, 1800.0, 1065.0)))

    # Cont
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1570.0, 2270.0, 1730.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(190.0, 2270.0, 350.0, 2430.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, 3700.0, 1760.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1600.0, -80.0, 1760.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, 3700.0, 1280.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1120.0, -80.0, 1280.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, 3700.0, 800.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(640.0, -80.0, 800.0, 80.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1570.0, 2950.0, 1730.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(610.0, 1560.0, 770.0, 1720.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(190.0, 2950.0, 350.0, 3110.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(190.0, 2610.0, 350.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1570.0, 2610.0, 1730.0, 2770.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1150.0, 1555.0, 1310.0, 1715.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(190.0, 720.0, 350.0, 880.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(1570.0, 720.0, 1730.0, 880.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, 3700.0, 320.0, 3860.0)))
    cell.add_shape(RectShape(tech['Cont'], Rect.from_lbrt(160.0, -80.0, 320.0, 80.0)))

    # GatPoly
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(460.0, 1475.0), Point(460.0, 3360.0), Point(1460.0, 3360.0), Point(1460.0, 2000.0), Point(855.0, 2000.0), Point(855.0, 1475.0)]))
    cell.add_shape(PolygonShape(tech['GatPoly'], [Point(460.0, 465.0), Point(460.0, 1245.0), Point(1065.0, 1245.0), Point(1065.0, 1800.0), Point(1460.0, 1800.0), Point(1460.0, 465.0)]))

    # Metal1
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, 3560.0, 1920.0, 4000.0)))
    cell.add_shape(RectShape(tech['Metal1'], Rect.from_lbrt(0.0, -220.0, 1920.0, 220.0)))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(0.0, -220.0), Point(0.0, 220.0), Point(130.0, 220.0), Point(130.0, 935.0), Point(530.0, 935.0), Point(530.0, 1805.0), Point(855.0, 1805.0), Point(855.0, 220.0), Point(1510.0, 220.0), Point(1510.0, 935.0), Point(1790.0, 935.0), Point(1790.0, 220.0), Point(1920.0, 220.0), Point(1920.0, -220.0)]))
    cell.add_shape(PolygonShape(tech['Metal1'], [Point(1065.0, 1470.0), Point(1065.0, 3560.0), Point(400.0, 3560.0), Point(400.0, 2220.0), Point(130.0, 2220.0), Point(130.0, 3560.0), Point(0.0, 3560.0), Point(0.0, 4000.0), Point(1920.0, 4000.0), Point(1920.0, 3560.0), Point(1790.0, 3560.0), Point(1790.0, 2220.0), Point(1405.0, 2220.0), Point(1405.0, 1470.0)]))
    cell.add_shape(TextShape(tech['Metal1'], 'VDD', Point(950.0, 3780.0), purpose='label'))
    cell.add_shape(TextShape(tech['Metal1'], 'VSS', Point(1080.0, 0.0), purpose='label'))

    # NWell
    cell.add_shape(RectShape(tech['NWell'], Rect.from_lbrt(-240.0, 1750.0, 2160.0, 4170.0)))

    # PSD
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-160.0, 1760.0, 1990.0, 3600.0)))
    cell.add_shape(RectShape(tech['PSD'], Rect.from_lbrt(-70.0, -180.0, 1990.0, 180.0)))

    # Ports
    cell.add_port(Port('VDD', 'VDD', tech['Metal1'], Rect.from_lbrt(950.0, 3780.0, 950.0, 3780.0), direction='POWER'))
    cell.add_port(Port('VSS', 'VSS', tech['Metal1'], Rect.from_lbrt(1080.0, 0.0, 1080.0, 0.0), direction='GROUND'))

    return cell


if __name__ == "__main__":
    from aion_layout.tech import sg13g2_tech
    c = generate('sg13g2_decap_4', sg13g2_tech)
    c.write_gds("sg13g2_decap_4.gds")
