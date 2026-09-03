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

# Metal1 stub bands.  Both the input bars and the output stub sit in the gap
# between the NMOS and PMOS active areas.  For an odd input count the middle
# gate falls exactly on CELL_WIDTH/2, i.e. under the output stub, so the two
# kinds of stub must not share a horizontal band: if they did, that input and
# the output would merge into a single Metal1 node and extraction would lose
# the input.  The gap is therefore split into two bands kept apart by the
# Metal1 minimum spacing.
#
# KNOWN TRADE-OFF, deliberate.  Splitting the 730 nm gap into two bands leaves
# each stub about 275 nm tall, and at the stub widths the default cell width
# allows that is below the M1.d minimum-area rule (0.09 um^2): a live run
# reports four "Metal1 minimum area" violations, one per stub, on top of the
# eight LU.a/LU.b violations the tap-less scaffold has by design.
#
# That is the better failure.  The overlap it replaces merged an input and the
# output into one Metal1 node, so extraction silently lost a port and LVS could
# not be reconstructed from the result.  A minimum-area violation is reported
# with its rule name and coordinates, reaches the model in the evidence packet,
# and is fixed by enlarging one rectangle.
#
# Satisfying both rules here needs a wider cell or a different stub placement,
# i.e. a floorplan decision.  The scaffold does not make floorplan decisions --
# it is a deliberately incomplete starting point, and the model draws the cell.
_METAL1_MIN_SPACING_NM = 180.0
_OUTPUT_STUB_TOP_NM = 1600.0
_INPUT_BAR_BOTTOM_NM = _OUTPUT_STUB_TOP_NM + _METAL1_MIN_SPACING_NM
_INPUT_BAR_CENTER_Y_NM = (_INPUT_BAR_BOTTOM_NM + _PMOS_BOTTOM_NM) / 2.0
_INPUT_BAR_HALF_HEIGHT_NM = (_PMOS_BOTTOM_NM - _INPUT_BAR_BOTTOM_NM) / 2.0
_INPUT_BAR_HALF_WIDTH_NM = 145.0


def _input_bar_rect(
    x_center: float,
    y_center: float,
    half_w: float = _INPUT_BAR_HALF_WIDTH_NM,
) -> Tuple[float, float, float, float]:
    """Return (left, bottom, right, top) for a Metal1 input bar stub."""
    half_h = _INPUT_BAR_HALF_HEIGHT_NM
    return (x_center - half_w, y_center - half_h, x_center + half_w, y_center + half_h)


def _input_bar_half_width(gates: List[Tuple[str, float]]) -> float:
    """Return a bar half-width that keeps neighbouring input bars apart.

    Bars are clipped to half the gate pitch minus the Metal1 minimum spacing, so
    two inputs can never merge into one node.  With the default cell width the
    pitch is always wide enough and the nominal half-width is returned
    unchanged; only an explicitly requested, very narrow ``cell_width`` shrinks
    the bars.  In that over-constrained case the bars are still kept strictly
    disjoint and DRC reports the width/spacing violation: a visible width error
    is recoverable, a silently merged net is not.
    """
    if len(gates) < 2:
        return _INPUT_BAR_HALF_WIDTH_NM
    pitch = min(b[1] - a[1] for a, b in zip(gates, gates[1:]))
    spacing = min(_METAL1_MIN_SPACING_NM, pitch / 2.0)
    return min(_INPUT_BAR_HALF_WIDTH_NM, (pitch - spacing) / 2.0)


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
    bar_half_w = _input_bar_half_width(gates)

    gate_entries = "\n".join(
        f'    ("{net}", {x:.1f}),' for net, x in gates
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
        f'    half_w = {bar_half_w:.1f}',
        f'    half_h = {_INPUT_BAR_HALF_HEIGHT_NM:.1f}',
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
        f'        cell.merge_subcell(draw_pin(tech["Metal1"], Rect.from_lbrt(*_input_bar_rect(x, {_INPUT_BAR_CENTER_Y_NM:.1f})), net, tech=tech))',
        '',
        '    # Output pin (stub).  Replace with the real output Metal1 polygon.',
        '    # It sits in its own Metal1 band, below the input bars, so it cannot',
        '    # merge with the input bar of a gate placed at CELL_WIDTH/2.',
        f'    cell.merge_subcell(draw_pin(tech["Metal1"], Rect.from_lbrt(CELL_WIDTH/2 - 130.0, {_NMOS_TOP_NM:.1f},',
        f'                                                              CELL_WIDTH/2 + 130.0, {_OUTPUT_STUB_TOP_NM:.1f}), "{output}", tech=tech))',
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
