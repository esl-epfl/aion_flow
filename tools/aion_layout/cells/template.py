# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Template for an AION standard-cell generator
# ================================================================

"""Minimal template showing the expected cell-generator contract.

Every cell generator must be a Python module that exposes:

    def generate(name: str, tech: aion_layout.tech.Tech) -> aion_layout.cell.Cell:
        ...

The ``name`` argument is the top-level cell name (e.g. ``sg13g2_nand2_1``);
``tech`` is the technology object loaded from ``aion_layout.tech``.

This template produces a valid, empty standard-cell site.  Copy it to
``cells/<your_cell>.py`` and replace the body with real geometry.
"""

from aion_layout.cell import Cell
from aion_layout.primitives import Rect
from aion_layout.tech import Tech

CELL_HEIGHT = 3780.0 # DO NOT CHANGE: SG13G2 standard-cell height in nm
CELL_WIDTH = 480.0 # SG13G2 standard-cell width in nm should be a mulSG13G2 standard-cell height in nmtiple of this value (pnr boundary, vdd/vss rails can be wider)


def generate(name: str, tech: Tech) -> Cell:
    """Generate an empty placeholder cell matching the SG13G2 site size."""
    cell = Cell(name, tech)

    # Standard-cell abutment box.  The SG13G2 site is 480 nm wide and
    # 3780 nm tall; a 1x site is used here as a starting point.
    site_width = tech.standard_cell["site_width_nm"]
    site_height = tech.standard_cell["cell_height_nm"]
    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, site_width, site_height))

    return cell
