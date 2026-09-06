# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Reusable layout building blocks
# ================================================================

"""Composable, cell-agnostic layout building blocks.

Each function returns a ``Cell`` containing shapes and ports that can be merged
into a parent cell.
"""

from __future__ import annotations

from typing import Optional, Sequence

from .cell import Cell, Port
from .primitives import Point, Rect
from .shapes import RectShape, TextShape
from .tech import Layer, Tech, sg13g2_tech


# Minimum Cont-to-Cont spacing, in nanometres.
#
# This rule is NOT present in ``tech.design_rules``: ``min_spacing_nm`` has no
# ``Cont`` entry and ``min_spacing_nm_pairs`` has no ``("Cont", "Cont")`` pair.
# The value below is the assumed SG13G2 minimum contact-to-contact spacing and
# is used only to derive the tap contact pitch in :func:`draw_tap`.  Move it
# into ``tech.py`` once the rule table grows a ``Cont`` spacing entry.
_ASSUMED_CONT_SPACING_NM = 180.0


def _tech(tech: Optional[Tech]) -> Tech:
    return tech if tech is not None else sg13g2_tech


def _cut_size(cut_name: str, tech: Tech) -> float:
    return tech.design_rules["via_size_nm"].get(cut_name, 0.0)


def _enclosure(conductor_name: str, cut_name: str, tech: Tech) -> float:
    return (
        tech.design_rules.get("min_enclosure_nm", {})
        .get(conductor_name, {})
        .get(cut_name, 0.0)
    )


def _pair_spacing(layer_a: str, layer_b: str, tech: Tech) -> float:
    pairs = tech.design_rules.get("min_spacing_nm_pairs", {})
    return pairs.get((layer_a, layer_b), pairs.get((layer_b, layer_a), 0.0))


def draw_diffusion(rect: Rect, doping: str, tech: Optional[Tech] = None) -> Cell:
    """Draw active diffusion plus the corresponding implant layer.

    In SG13G2, n+ active is the default doping, so no separate NSD drawing
    layer is emitted for n-type diffusion.  p-type diffusion still requires
    the PSD layer.
    """
    t = _tech(tech)
    doping = doping.lower()
    if doping not in ("n", "p"):
        raise ValueError("doping must be 'n' or 'p'")

    cell = Cell(f"diffusion_{doping}", t)
    cell.add_shape(RectShape(t["Activ"], rect))
    if doping == "p":
        cell.add_shape(RectShape(t["PSD"], rect))
    return cell


def draw_well(rect: Rect, well_type: str, tech: Optional[Tech] = None) -> Cell:
    """Draw an nwell or pwell rectangle."""
    t = _tech(tech)
    well_type = well_type.lower()
    if well_type not in ("n", "p"):
        raise ValueError("well_type must be 'n' or 'p'")

    layer = t["NWell"] if well_type == "n" else t["PWell"]
    cell = Cell(f"well_{well_type}", t)
    cell.add_shape(RectShape(layer, rect))
    return cell


def draw_poly_gate(rect: Rect, tech: Optional[Tech] = None) -> Cell:
    """Draw a polysilicon gate rectangle and expose a 'G' port."""
    t = _tech(tech)
    cell = Cell("poly_gate", t)
    cell.add_shape(RectShape(t["GatPoly"], rect))
    cell.add_port(Port("G", "G", t["GatPoly"], rect))
    return cell


def draw_metal_wire(layer: Layer, rect: Rect, tech: Optional[Tech] = None) -> Cell:
    """Draw a rectangular metal wire."""
    cell = Cell(f"wire_{layer.name}", _tech(tech))
    cell.add_shape(RectShape(layer, rect))
    return cell


def draw_pin(
    layer: Layer,
    rect: Rect,
    name: str,
    net: Optional[str] = None,
    tech: Optional[Tech] = None,
) -> Cell:
    """Draw a pin: metal rectangle plus label/pin text and a port."""
    t = _tech(tech)
    net = net if net is not None else name
    cell = Cell(f"pin_{name}", t)
    cell.add_shape(RectShape(layer, rect))
    center = rect.center
    if layer.label_datatype is not None:
        cell.add_shape(TextShape(layer, name, center, purpose="label"))
    if layer.pin_datatype is not None:
        cell.add_shape(TextShape(layer, name, center, purpose="pin"))
    cell.add_port(Port(name, net, layer, rect, direction="INOUT"))
    return cell


def draw_power_rail(
    y: float,
    width: float,
    net: str,
    tech: Optional[Tech] = None,
    cell_width: Optional[float] = None,
) -> Cell:
    """Draw a horizontal Metal1 power rail spanning ``cell_width``.

    If ``cell_width`` is omitted, the SG13G2 site width is used.
    """
    t = _tech(tech)
    if cell_width is None:
        cell_width = t.standard_cell["site_width_nm"]

    direction = {
        "VDD": "POWER",
        "VSS": "GROUND",
    }.get(net.upper(), "INOUT")

    rail_rect = Rect.from_lbrt(0, y - width / 2.0, cell_width, y + width / 2.0)
    cell = Cell(f"rail_{net}", t)
    cell.add_shape(RectShape(t["Metal1"], rail_rect))
    cell.add_port(Port(net, net, t["Metal1"], rail_rect, direction=direction))
    return cell


def draw_contact(
    stack: Sequence[str],
    rect: Rect,
    tech: Optional[Tech] = None,
) -> Cell:
    """Draw a contact/via stack: ``[top_layer, cut_layer, bottom_layer]``.

    The cut is centred in ``rect`` and the enclosing conductors are sized to
    satisfy the minimum enclosure rules from the technology.
    """
    t = _tech(tech)
    if len(stack) != 3:
        raise ValueError("stack must be [top_layer, cut_layer, bottom_layer]")
    top_name, cut_name, bottom_name = stack
    top_layer = t[top_name]
    cut_layer = t[cut_name]
    bottom_layer = t[bottom_name]

    cut_size = _cut_size(cut_name, t)
    cut_rect = Rect.from_center(rect.center, cut_size, cut_size)

    top_enc = _enclosure(top_name, cut_name, t)
    bottom_enc = _enclosure(bottom_name, cut_name, t)

    top_rect = cut_rect.resize(top_enc).union(rect)
    bottom_rect = cut_rect.resize(bottom_enc).union(rect)

    cell = Cell(f"contact_{cut_name}", t)
    cell.add_shape(RectShape(top_layer, top_rect))
    cell.add_shape(RectShape(cut_layer, cut_rect))
    cell.add_shape(RectShape(bottom_layer, bottom_rect))
    return cell


def draw_via_stack(
    from_layer: str,
    to_layer: str,
    rect: Rect,
    tech: Optional[Tech] = None,
) -> Cell:
    """Convenience wrapper for a single via between two metal layers.

    ``from_layer`` and ``to_layer`` must be adjacent metal layers, e.g.
    ``"Metal1"`` and ``"Metal2"`` (joined by ``"Via1"``).
    """
    t = _tech(tech)
    cut_map = {
        ("Metal1", "Metal2"): "Via1",
        ("Metal2", "Metal1"): "Via1",
        ("Metal1", "GatPoly"): "Cont",
        ("GatPoly", "Metal1"): "Cont",
        ("Metal1", "Activ"): "Cont",
        ("Activ", "Metal1"): "Cont",
    }
    key = (from_layer, to_layer)
    if key not in cut_map:
        raise ValueError(f"No predefined via between {from_layer} and {to_layer}")
    return draw_contact([from_layer, cut_map[key], to_layer], rect, t)


def draw_tap(
    rect: Rect,
    tap_type: str,
    net: str,
    tech: Optional[Tech] = None,
) -> Cell:
    """Draw a well/substrate tap: implant, a contact row and a Metal1 tie.

    ``tap_type`` is ``"n"`` for an n+ tap that ties an NWell to VDD, or ``"p"``
    for a p+ tap that ties the p-substrate to VSS.  Implants follow the same
    convention as :func:`draw_diffusion`: n-type emits ``Activ`` alone (n+ is the
    SG13G2 default doping), p-type emits ``Activ`` plus ``PSD``.

    ``rect`` is the tap active area.  A row of ``Cont`` cuts is placed along its
    longer axis, inset from its edges by the implant-to-cut enclosure, and
    covered by a Metal1 landing grown by the Metal1-to-cut enclosure.  A ``Port``
    and a Metal1 label, both named after ``net``, are added so extraction sees
    the tie.  Ports are keyed by name, so merging several taps of the same net
    into one cell keeps only the last port; they all carry the same net, so the
    extracted connectivity is unchanged.

    The caller places the tap: an ``"n"`` tap must sit inside an ``NWell``
    rectangle, a ``"p"`` tap outside every ``NWell``.  Tap rows are what satisfy
    the latch-up rules LU.a / LU.b, which bound how far any diffusion may be
    from a tap of the opposite type.
    """
    t = _tech(tech)
    tap_type = tap_type.lower()
    if tap_type not in ("n", "p"):
        raise ValueError(
            "tap_type must be 'n' (n+ tap in an NWell) or 'p' (p+ substrate tap)"
        )

    implant_name = "NSD" if tap_type == "n" else "PSD"
    cut_size = _cut_size("Cont", t)
    implant_enc = _enclosure(implant_name, "Cont", t)
    metal_enc = _enclosure("Metal1", "Cont", t)
    pitch = cut_size + _ASSUMED_CONT_SPACING_NM

    min_side = cut_size + 2.0 * implant_enc
    if rect.width < min_side or rect.height < min_side:
        raise ValueError(
            f"tap rect is {rect.width:g} x {rect.height:g} nm, too small for a "
            f"'{tap_type}' tap: at least {min_side:g} x {min_side:g} nm is "
            f"needed to hold one {cut_size:g} nm Cont with {implant_enc:g} nm "
            f"{implant_name}-to-Cont enclosure on every side"
        )

    cell = Cell(f"tap_{tap_type}_{net}", t)
    cell.merge_subcell(draw_diffusion(rect, tap_type, t))

    # Cut row along the longer axis of the tap, centred on the shorter one.
    usable = rect.resize(-implant_enc)
    horizontal = usable.width >= usable.height
    span = usable.width if horizontal else usable.height
    count = int((span - cut_size) / pitch + 1e-9) + 1
    run = count * cut_size + (count - 1) * _ASSUMED_CONT_SPACING_NM

    if horizontal:
        left = usable.left + (usable.width - run) / 2.0
        bottom = usable.bottom + (usable.height - cut_size) / 2.0
        dx, dy = pitch, 0.0
    else:
        left = usable.left + (usable.width - cut_size) / 2.0
        bottom = usable.bottom + (usable.height - run) / 2.0
        dx, dy = 0.0, pitch

    first_cut = Rect.from_lbrt(left, bottom, left + cut_size, bottom + cut_size)
    cuts = [first_cut.move(dx * i, dy * i) for i in range(count)]
    for cut in cuts:
        cell.add_shape(RectShape(t["Cont"], cut))

    landing = cuts[0].union(cuts[-1]).resize(metal_enc)
    direction = {
        "VDD": "POWER",
        "VSS": "GROUND",
    }.get(net.upper(), "INOUT")
    cell.add_shape(RectShape(t["Metal1"], landing))
    cell.add_shape(TextShape(t["Metal1"], net, landing.center, purpose="label"))
    cell.add_port(Port(net, net, t["Metal1"], landing, direction=direction))
    return cell


def draw_transistor(
    gate_rect: Rect,
    active_rect: Rect,
    fet_type: str,
    fingers: int = 1,
    tech: Optional[Tech] = None,
) -> Cell:
    """Draw a transistor: diffusion, gate, and source/drain contacts.

    Currently only ``fingers=1`` is supported.  The gate is assumed to cross the
    active area vertically (gate width < gate height).
    """
    t = _tech(tech)
    fet_type = fet_type.lower()
    if fet_type not in ("n", "p"):
        raise ValueError("fet_type must be 'n' or 'p'")
    if fingers != 1:
        raise NotImplementedError("multi-finger transistors are not yet implemented")
    if gate_rect.width >= gate_rect.height:
        raise ValueError("draw_transistor expects a vertical gate (width < height)")

    cell = Cell(f"transistor_{fet_type}", t)

    # Diffusion and gate.
    cell.merge_subcell(draw_diffusion(active_rect, fet_type, t))
    cell.merge_subcell(draw_poly_gate(gate_rect, t))

    # Source/drain contacts on the active area, one on each side of the gate.
    cut_size = _cut_size("Cont", t)
    poly_to_cont = _pair_spacing("GatPoly", "Cont", t)
    metal_enc = _enclosure("Metal1", "Cont", t)

    y_cut = active_rect.center.y - cut_size / 2.0

    def place_contact(desired_center_x: float, limit_x: float, side: int) -> Optional[Rect]:
        """Place a contact cut, shifting away from ``limit_x`` if needed.

        ``side`` is -1 for left of the gate and +1 for right.
        """
        left = desired_center_x - cut_size / 2.0
        right = desired_center_x + cut_size / 2.0
        if side == -1 and right > limit_x - poly_to_cont:
            shift = right - (limit_x - poly_to_cont)
            left -= shift
            right -= shift
        elif side == +1 and left < limit_x + poly_to_cont:
            shift = (limit_x + poly_to_cont) - left
            left += shift
            right += shift

        if left < active_rect.left or right > active_rect.right:
            return None
        return Rect.from_lbrt(left, y_cut, right, y_cut + cut_size)

    # Source contact (left of gate).
    src_cut = place_contact(
        (active_rect.left + gate_rect.left) / 2.0,
        gate_rect.left,
        -1,
    )
    # Drain contact (right of gate).
    drn_cut = place_contact(
        (gate_rect.right + active_rect.right) / 2.0,
        gate_rect.right,
        +1,
    )

    for port_name, cut_rect in (("S", src_cut), ("D", drn_cut)):
        if cut_rect is None:
            continue
        landing = cut_rect.resize(metal_enc)
        cell.add_port(Port(port_name, port_name, t["Metal1"], landing))
        cell.merge_subcell(
            draw_contact(["Metal1", "Cont", "Activ"], cut_rect, t)
        )

    return cell


__all__ = [
    "draw_diffusion",
    "draw_well",
    "draw_poly_gate",
    "draw_metal_wire",
    "draw_pin",
    "draw_power_rail",
    "draw_contact",
    "draw_via_stack",
    "draw_tap",
    "draw_transistor",
]
