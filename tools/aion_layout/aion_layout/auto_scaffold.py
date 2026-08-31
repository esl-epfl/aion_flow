# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Generate a starter cell from a SPICE netlist
# ================================================================

"""Generate a runnable-but-incomplete ``cells/<name>.py`` file from a netlist.

The scaffold produces a cell with the correct boundary, power rails, active
areas, poly gates for every input, and pin declarations.  The AI is expected to
complete the source/drain routing and contacts in the iteration phase.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from .netlist_view import suggest_gate_order
from .spice_parser import Subckt, parse_first_subckt


# SG13G2 defaults used for the starter geometry.  These may be tweaked by the
# AI during iteration.
_GATE_WIDTH_NM = 130.0
_POWER_RAIL_WIDTH_NM = 440.0
_NMOS_BOTTOM_NM = 590.0
_NMOS_TOP_NM = 1330.0
_PMOS_BOTTOM_NM = 2060.0
_PMOS_TOP_NM = 3180.0
_POLY_BOTTOM_NM = 410.0
_POLY_TOP_NM = 3360.0
_WELL_OVERhang_NM = 240.0


def _input_bar_rect(x_center: float, y_center: float) -> Tuple[float, float, float, float]:
    """Return (left, bottom, right, top) for a Metal1 input bar stub."""
    half_w = 145.0
    half_h = 215.0
    return (x_center - half_w, y_center - half_h, x_center + half_w, y_center + half_h)


def _gate_positions(inputs: List[str], active_left: float, active_right: float) -> List[Tuple[str, float]]:
    """Distribute poly gates evenly across the active area."""
    n = len(inputs)
    if n == 0:
        return []
    pitch = (active_right - active_left) / (n + 1)
    return [(inp, active_left + pitch * (i + 1)) for i, inp in enumerate(inputs)]


def generate_scaffold_source(
    subckt: Subckt,
    cell_width: float | None = None,
) -> str:
    """Return Python source for a starter cell generator."""
    tech = None  # source code references the ``tech`` argument.
    inputs = suggest_gate_order(subckt)
    output = subckt.output_net or "Y"
    vdd = subckt.vdd_net or "VDD"
    vss = subckt.vss_net or "VSS"

    site_width = 480.0
    cell_height = 3780.0
    if cell_width is None:
        # Give two sites per input; the AI can shrink later.
        cell_width = max(1, len(inputs)) * site_width * 2.0

    active_left = site_width / 2.0
    active_right = cell_width - site_width / 2.0
    gates = _gate_positions(inputs, active_left, active_right)

    gate_entries = "\n".join(
        f'    ("{net}", {x:.1f}),' for net, x in gates
    )

    pin_entries = "\n".join(
        f'    draw_pin(tech["Metal1"], Rect.from_lbrt(*_input_bar_rect({x:.1f}, 1605.0)), "{net}", tech=tech),'
        for net, x in gates
    )

    lines = [
        '# ================================================================',
        '#  SPDX-FileCopyrightText:    2026 Filippo Quadri',
        '#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1',
        '#  Created:                   2026-08-25',
        f'#  Description:               Auto-scaffolded generator for {subckt.name}',
        '# ================================================================',
        '',
        f'"""Auto-scaffolded cell generator for {subckt.name}."""',
        '',
        'from aion_layout.building_blocks import draw_diffusion, draw_pin, draw_power_rail',
        'from aion_layout.cell import Cell, Port',
        'from aion_layout.primitives import Rect',
        'from aion_layout.shapes import RectShape',
        'from aion_layout.tech import Tech',
        '',
        f'CELL_WIDTH = {cell_width:.1f}',
        f'CELL_HEIGHT = {cell_height:.1f}',
        '',
        '# Active areas.  Adjust widths/heights during iteration.',
        f'NMOS_ACTIVE = Rect.from_lbrt({active_left:.1f}, {_NMOS_BOTTOM_NM:.1f}, {active_right:.1f}, {_NMOS_TOP_NM:.1f})',
        f'PMOS_ACTIVE = Rect.from_lbrt({active_left:.1f}, {_PMOS_BOTTOM_NM:.1f}, {active_right:.1f}, {_PMOS_TOP_NM:.1f})',
        '',
        '# (input_net, gate_center_x) left-to-right.',
        'GATES = [',
        gate_entries,
        ']',
        '',
        '',
        'def _input_bar_rect(x_center: float, y_center: float) -> tuple[float, float, float, float]:',
        '    half_w = 145.0',
        '    half_h = 215.0',
        '    return (x_center - half_w, y_center - half_h, x_center + half_w, y_center + half_h)',
        '',
        '',
        'def generate(name: str, tech: Tech) -> Cell:',
        '    """Generate the cell."""',
        '    cell = Cell(name, tech)',
        f'    cell.set_boundary(Rect.from_lbrt(0.0, 0.0, CELL_WIDTH, CELL_HEIGHT))',
        '',
        '    # Diffusion.',
        '    cell.merge_subcell(draw_diffusion(NMOS_ACTIVE, "n", tech))',
        '    cell.merge_subcell(draw_diffusion(PMOS_ACTIVE, "p", tech))',
        '',
        '    # NWell encloses the PMOS active area.',
        f'    cell.add_shape(RectShape(tech["NWell"], Rect.from_lbrt(-{_WELL_OVERhang_NM:.1f}, {_PMOS_BOTTOM_NM - 310:.1f},',
        f'                                              CELL_WIDTH + {_WELL_OVERhang_NM:.1f}, {_PMOS_TOP_NM + 990:.1f})))',
        '',
        '    # Power rails.',
        f'    cell.merge_subcell(draw_power_rail(0.0, {_POWER_RAIL_WIDTH_NM:.1f}, "{vss}", tech, CELL_WIDTH))',
        f'    cell.merge_subcell(draw_power_rail(CELL_HEIGHT, {_POWER_RAIL_WIDTH_NM:.1f}, "{vdd}", tech, CELL_WIDTH))',
        '',
        '    # Poly gates and input bars (stubs).',
        '    for net, x in GATES:',
        f'        cell.add_shape(RectShape(tech["GatPoly"], Rect.from_lbrt(x - {_GATE_WIDTH_NM/2:.1f}, {_POLY_BOTTOM_NM:.1f},',
        f'                                                                x + {_GATE_WIDTH_NM/2:.1f}, {_POLY_TOP_NM:.1f})))',
        '        cell.merge_subcell(draw_pin(tech["Metal1"], Rect.from_lbrt(*_input_bar_rect(x, 1605.0)), net, tech=tech))',
        '',
        '    # Output pin (stub).  Replace with the real output Metal1 polygon.',
        f'    cell.merge_subcell(draw_pin(tech["Metal1"], Rect.from_lbrt(CELL_WIDTH/2 - 130.0, {_NMOS_TOP_NM:.1f},',
        f'                                                              CELL_WIDTH/2 + 130.0, {_PMOS_BOTTOM_NM:.1f}), "{output}", tech=tech))',
        '',
        '    return cell',
        '',
    ]
    return "\n".join(lines)


def write_scaffold(
    netlist_path: Path | str,
    output_path: Path | str,
    cell_width: float | None = None,
    force: bool = False,
) -> Path:
    """Parse a netlist and write a starter cell generator to ``output_path``."""
    subckt = parse_first_subckt(netlist_path)
    source = generate_scaffold_source(subckt, cell_width=cell_width)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not force:
        raise FileExistsError(
            f"Output file already exists: {output_path}. Use force=True to overwrite."
        )
    output_path.write_text(source)
    return output_path
