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

import math
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


# ======================================================================
#  Via1 and Metal2
# ======================================================================
#
# Three traps make the Metal1/Via1/Metal2 stack worth its own primitives.
#
# 1. Via1 is 190 nm square *exactly*.  V1.a is a minimum and a maximum rule at
#    the same value, so a Via1 is never "at least" a size -- it is one size,
#    and a cut sized from a min-width table alone is as illegal when it is too
#    big as when it is too small.
#
# 2. Enclosure comes in two tiers, and designing to either one alone is wrong.
#    V1.c wants 10 nm of Metal1 on every side of a Via1 and M2.c wants 5 nm of
#    Metal2; the endcap rules V1.c1 and M2.c1 want 50 nm but are waived on one
#    side, or on two *opposite* sides.  Sizing a landing from the all-sides
#    number gives an endcap violation; sizing it from the endcap number on all
#    four sides forbids minimum-width Metal2 routing for no reason, because a
#    200 nm Metal2 wire has only 5 nm of enclosure across the via -- and that
#    is legal precisely because those two sides are opposite each other, as
#    long as the wire runs 50 nm past the via at both ends.  The PDK's own
#    sg13g2_sdfbbp_1 does exactly this: its three Via1 cuts have Metal1
#    enclosures of (105, 10, 140, 75), (190, 220, 215, 80) and
#    (110, 70, 25, 220) nm -- under 50 nm on one side twice, never on two
#    adjacent sides.
#
# 3. Metal2 has a 0.144 um2 minimum area (M2.d), 60% more than Metal1's
#    0.09 um2 (M1.d).  A minimum-width 200 nm Metal2 rectangle is illegal
#    until it is 720 nm long.  That, not the enclosure rules, is what actually
#    sizes Metal2 in a standard cell: a via landing needs 290 nm of Metal2 and
#    the area rule then demands another 430 nm of it.
#
# The endcap values live in ``tech.design_rules["min_enclosure_nm"]`` because
# they are what a landing has to be *drawn* to; the all-sides values live here
# because only this code knows to apply them to the narrow pair of sides.

#: Manufacturing grid.  Rule 3.1 ``*_Offgrid``: "All features are on a drawing
#: grid of 5 nm".  Every edge this module emits is checked against it, because
#: an off-grid edge is a DRC error on a layer that otherwise looks perfect.
_DRAWING_GRID_NM = 5.0

#: V1.c / M2.c -- the enclosure a Via1 needs on *every* side.  Smaller than the
#: endcap rule in ``tech``; see the note above for why both are needed.
_VIA1_SIDE_ENCLOSURE_NM = {"Metal1": 10.0, "Metal2": 5.0}

#: V1.b1 -- Via1 spacing inside an array of more than 3 rows *and* more than
#: 3 columns, required in one direction only.
_VIA1_ARRAY_SPACING_NM = 290.0
_VIA1_ARRAY_ROWS_TRIGGER = 3

#: Rule names, per layer, for the four checks a Via1 landing has to pass.  They
#: go into the exception messages: a number without its rule name is a number
#: nobody can check against the deck.
_VIA1_RULES = {
    "Metal1": {
        "side": "V1.c",
        "endcap": "V1.c1",
        "width": "M1.a",
        "area": "M1.d",
    },
    "Metal2": {
        "side": "M2.c",
        "endcap": "M2.c1",
        "width": "M2.a",
        "area": "M2.d",
    },
}


def _on_grid(value: float) -> bool:
    """Return True if ``value`` sits on the manufacturing grid."""
    quotient = value / _DRAWING_GRID_NM
    return abs(quotient - round(quotient)) <= 1e-6


def _check_on_grid(rect: Rect, what: str) -> None:
    """Raise unless every edge of ``rect`` is on the manufacturing grid."""
    off = [
        f"{name}={value:g}"
        for name, value in (
            ("left", rect.left),
            ("bottom", rect.bottom),
            ("right", rect.right),
            ("top", rect.top),
        )
        if not _on_grid(value)
    ]
    if off:
        raise ValueError(
            f"{what} is off-grid ({', '.join(off)}): rule 3.1 *_Offgrid puts "
            f"every drawn edge on a {_DRAWING_GRID_NM:g} nm grid"
        )


def _ceil_to(value: float, step: float) -> float:
    """Round ``value`` up to a multiple of ``step``, tolerating float noise."""
    quotient = value / step
    rounded = round(quotient)
    if abs(quotient - rounded) <= 1e-9:
        return rounded * step
    return math.ceil(quotient) * step


def _required_enclosure(conductor_name: str, cut_name: str, tech: Tech) -> float:
    """Return an enclosure rule, refusing to invent one that is missing.

    :func:`_enclosure` returns 0.0 for an unknown pair, which is a perfectly
    plausible-looking measurement and would silently draw a landing flush with
    its cut.  Sizing geometry must fail instead.
    """
    value = (
        tech.design_rules.get("min_enclosure_nm", {})
        .get(conductor_name, {})
        .get(cut_name)
    )
    if value is None:
        raise ValueError(
            f"tech {tech.name!r} has no {conductor_name} enclosure of "
            f"{cut_name}; design_rules['min_enclosure_nm'] must carry it "
            f"before a landing can be sized"
        )
    return float(value)


def _min_area(layer_name: str, tech: Tech) -> float:
    """Return a minimum-area rule in nm^2, refusing to invent a missing one."""
    areas = tech.design_rules.get("min_area_nm2", {})
    if layer_name not in areas:
        raise ValueError(
            f"tech {tech.name!r} has no minimum area for {layer_name}; "
            f"design_rules['min_area_nm2'] must carry it"
        )
    return float(areas[layer_name])


def _pin_layer(layer: Layer) -> Layer:
    """Return the pin-datatype twin of ``layer``."""
    if layer.pin_datatype is None:
        raise ValueError(f"layer {layer.name} has no pin datatype")
    return Layer(
        name=f"{layer.name}.pin",
        gds_layer=layer.gds_layer,
        gds_datatype=layer.pin_datatype,
    )


def _check_via1_landing(
    rect: Rect,
    via_rect: Rect,
    layer_name: str,
    tech: Tech,
) -> None:
    """Raise unless ``rect`` is a legal landing for the Via1 at ``via_rect``.

    Checks all four rules that decide a landing locally: the all-sides
    enclosure, the endcap enclosure (satisfied by *either* opposite pair), the
    layer minimum width and the layer minimum area.

    The area check is why a landing merged into a wire must be handed to
    :func:`draw_via1` as the whole wire rectangle rather than as a patch around
    the cut: a 200 x 290 nm patch of a legal Metal2 wire is not itself a legal
    Metal2 shape, and this function cannot see the wire it will merge with.
    """
    rules = _VIA1_RULES[layer_name]
    layer = tech[layer_name]
    side = _VIA1_SIDE_ENCLOSURE_NM[layer_name]
    endcap = _required_enclosure(layer_name, "Via1", tech)
    min_width = layer.min_width or 0.0
    min_area = _min_area(layer_name, tech)

    enclosure = {
        "left": via_rect.left - rect.left,
        "right": rect.right - via_rect.right,
        "bottom": via_rect.bottom - rect.bottom,
        "top": rect.top - via_rect.top,
    }
    short = {k: v for k, v in enclosure.items() if v < side - 1e-9}
    if short:
        detail = ", ".join(f"{k}={v:g}" for k, v in sorted(short.items()))
        raise ValueError(
            f"{rules['side']}: {layer_name} must enclose Via1 by at least "
            f"{side:g} nm on every side, but {detail} nm"
        )

    horizontal = min(enclosure["left"], enclosure["right"]) >= endcap - 1e-9
    vertical = min(enclosure["bottom"], enclosure["top"]) >= endcap - 1e-9
    if not (horizontal or vertical):
        detail = ", ".join(f"{k}={v:g}" for k, v in sorted(enclosure.items()))
        raise ValueError(
            f"{rules['endcap']}: {layer_name} must enclose Via1 by "
            f"{endcap:g} nm on two opposite sides (the endcap pair), but "
            f"neither pair does: {detail} nm"
        )

    if rect.width < min_width - 1e-9 or rect.height < min_width - 1e-9:
        raise ValueError(
            f"{rules['width']}: {layer_name} landing is {rect.width:g} x "
            f"{rect.height:g} nm; minimum width is {min_width:g} nm"
        )

    if rect.area < min_area - 1e-6:
        raise ValueError(
            f"{rules['area']}: {layer_name} landing is {rect.width:g} x "
            f"{rect.height:g} nm = {rect.area / 1e6:.4f} um2; minimum area is "
            f"{min_area / 1e6:g} um2.  Pass the whole wire rectangle if this "
            f"landing merges into one"
        )

    _check_on_grid(rect, f"{layer_name} Via1 landing")


def m2_min_length_for_area(width_nm: float, tech: Optional[Tech] = None) -> float:
    """Shortest legal Metal2 rectangle of this width under the minimum-area rule.

    M2.d (0.144 um2) is the rule that sizes Metal2 in a standard cell, and it
    bites at exactly the widths routing wants to use: a minimum-width 200 nm
    wire is illegal until it is 720 nm long, which is longer than most cells
    are tall in Metal2 terms.  Returns a length on the manufacturing grid, so
    the answer is always drawable as-is.
    """
    t = _tech(tech)
    layer = t["Metal2"]
    min_width = layer.min_width or 0.0
    if width_nm < min_width - 1e-9:
        raise ValueError(
            f"M2.a: Metal2 width {width_nm:g} nm is below the {min_width:g} nm "
            f"minimum; no length makes it legal"
        )
    if not _on_grid(width_nm):
        raise ValueError(
            f"Metal2 width {width_nm:g} nm is off the {_DRAWING_GRID_NM:g} nm "
            f"grid (rule 3.1 Metal2_Offgrid)"
        )
    min_area = _min_area("Metal2", t)
    return _ceil_to(max(min_area / width_nm, min_width), _DRAWING_GRID_NM)


def via1_landing_rect(
    center: Point,
    layer_name: str,
    tech: Optional[Tech] = None,
) -> Rect:
    """The smallest legal Metal1 or Metal2 landing around a Via1 at this centre.

    Wire-shaped, not square, and deliberately so.  Across the via only the
    all-sides rule applies (V1.c / M2.c), because those two sides are opposite
    each other and the endcap rule is waived on an opposite pair; along the via
    the endcap rule (V1.c1 / M2.c1) applies, and then the minimum-area rule
    (M1.d / M2.d) usually demands more length still.  The result is a vertical
    stub: 210 x 430 nm on Metal1, 200 x 720 nm on Metal2.

    A square landing grown to 50 nm on all four sides looks safer and is in
    fact larger *and* illegal on Metal1 -- 290 x 290 nm is 0.0841 um2, under
    the 0.09 um2 M1.d floor.  For a horizontal landing, pass your own
    rectangle to :func:`draw_via1`; it is checked, not trusted.
    """
    t = _tech(tech)
    if layer_name not in _VIA1_SIDE_ENCLOSURE_NM:
        raise ValueError(
            f"via1_landing_rect: {layer_name!r} does not touch Via1; expected "
            f"'Metal1' or 'Metal2'"
        )
    if not (_on_grid(center.x) and _on_grid(center.y)):
        raise ValueError(
            f"Via1 centre ({center.x:g}, {center.y:g}) is off the "
            f"{_DRAWING_GRID_NM:g} nm grid (rule 3.1 Via1_Offgrid)"
        )

    layer = t[layer_name]
    via = _cut_size("Via1", t)
    side = _VIA1_SIDE_ENCLOSURE_NM[layer_name]
    endcap = _required_enclosure(layer_name, "Via1", t)
    min_width = layer.min_width or 0.0
    min_area = _min_area(layer_name, t)

    # The rectangle is centred on the cut, so half of each dimension has to
    # land on the grid too: round up to twice the grid, not to the grid.
    step = 2.0 * _DRAWING_GRID_NM
    width = _ceil_to(max(via + 2.0 * side, min_width), step)
    height = _ceil_to(max(via + 2.0 * endcap, min_width, min_area / width), step)
    return Rect.from_center(center, width, height)


def draw_via1(
    center: Point,
    tech: Optional[Tech] = None,
    *,
    metal1_rect: Optional[Rect] = None,
    metal2_rect: Optional[Rect] = None,
) -> Cell:
    """One Via1 with its Metal1 and Metal2 landings, sized from the rules.

    ``metal1_rect`` / ``metal2_rect`` override the landings from
    :func:`via1_landing_rect`.  Hand over the *whole* metal shape the via lands
    on -- typically the entire wire -- not a patch around the cut: the minimum
    area rules are checked here and a patch of a legal wire is not itself a
    legal shape.  Every landing, generated or supplied, is checked against
    V1.c/V1.c1/M1.a/M1.d and M2.c/M2.c1/M2.a/M2.d before anything is drawn.
    """
    t = _tech(tech)
    if not (_on_grid(center.x) and _on_grid(center.y)):
        raise ValueError(
            f"Via1 centre ({center.x:g}, {center.y:g}) is off the "
            f"{_DRAWING_GRID_NM:g} nm grid (rule 3.1 Via1_Offgrid)"
        )

    via = _cut_size("Via1", t)
    if via <= 0.0:
        raise ValueError(
            f"tech {t.name!r} has no Via1 size in design_rules['via_size_nm']"
        )
    via_rect = Rect.from_center(center, via, via)
    _check_on_grid(via_rect, "Via1 cut")

    m1 = metal1_rect if metal1_rect is not None else via1_landing_rect(center, "Metal1", t)
    m2 = metal2_rect if metal2_rect is not None else via1_landing_rect(center, "Metal2", t)
    _check_via1_landing(m1, via_rect, "Metal1", t)
    _check_via1_landing(m2, via_rect, "Metal2", t)

    cell = Cell("via1", t)
    cell.add_shape(RectShape(t["Metal1"], m1))
    cell.add_shape(RectShape(t["Via1"], via_rect))
    cell.add_shape(RectShape(t["Metal2"], m2))
    return cell


def draw_via1_array(
    rect: Rect,
    tech: Optional[Tech] = None,
    *,
    rows: Optional[int] = None,
    cols: Optional[int] = None,
) -> Cell:
    """Fill ``rect`` with as many Via1 cuts as fit, under one Metal1/Metal2 pad.

    ``rect`` is the landing, shared by both metals, and is checked as a Metal1
    *and* a Metal2 shape -- Metal2 is the binding one, so the pad is never
    smaller than 200 nm wide or 0.144 um2.

    The cuts keep 50 nm of metal above and below the array and at least the
    all-sides enclosure to left and right.  That asymmetry is the endcap rule
    read correctly: it makes the vertical pair the endcap pair for *every* cut
    in the array, including the ones in the outermost columns, whose horizontal
    enclosure is only the side value.  Growing the horizontal margin to 50 nm
    as well would be legal but would cost a column for nothing.

    ``rows`` / ``cols`` default to as many as fit; asking for more than fits is
    an error, not a silent trim.
    """
    t = _tech(tech)
    _check_on_grid(rect, "Via1 array landing")

    via = _cut_size("Via1", t)
    spacing = t.design_rules.get("min_spacing_nm", {}).get("Via1")
    if spacing is None:
        raise ValueError(
            f"tech {t.name!r} has no Via1 spacing in "
            f"design_rules['min_spacing_nm'] (rule V1.b)"
        )

    # The pad has to stand on its own on both metals.
    for layer_name in ("Metal1", "Metal2"):
        rules = _VIA1_RULES[layer_name]
        layer = t[layer_name]
        min_width = layer.min_width or 0.0
        if rect.width < min_width - 1e-9 or rect.height < min_width - 1e-9:
            raise ValueError(
                f"{rules['width']}: Via1 array landing is {rect.width:g} x "
                f"{rect.height:g} nm; {layer_name} minimum width is "
                f"{min_width:g} nm"
            )
        min_area = _min_area(layer_name, t)
        if rect.area < min_area - 1e-6:
            raise ValueError(
                f"{rules['area']}: Via1 array landing is "
                f"{rect.area / 1e6:.4f} um2; {layer_name} minimum area is "
                f"{min_area / 1e6:g} um2"
            )

    h_margin = max(_VIA1_SIDE_ENCLOSURE_NM.values())
    v_margin = max(
        _required_enclosure(name, "Via1", t) for name in ("Metal1", "Metal2")
    )

    def fit(span: float, margin: float, pitch_space: float) -> int:
        usable = span - 2.0 * margin
        if usable < via - 1e-9:
            return 0
        return int((usable + pitch_space) / (via + pitch_space) + 1e-9)

    cols_max = fit(rect.width, h_margin, spacing)
    rows_max = fit(rect.height, v_margin, spacing)
    if cols_max < 1 or rows_max < 1:
        raise ValueError(
            f"V1.c1/M2.c1: a {rect.width:g} x {rect.height:g} nm landing holds "
            f"no Via1: a cut is {via:g} nm square and needs {h_margin:g} nm of "
            f"metal left and right and {v_margin:g} nm above and below"
        )

    # ``int(2.7)`` is 2, and a request for 2.7 columns answered with two cuts
    # is a number where a refusal belongs: the caller asked for something this
    # function cannot draw and would never learn it.
    for label, value in (("rows", rows), ("cols", cols)):
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"draw_via1_array: {label} must be a whole number of Via1 "
                f"cuts, not {value!r}"
            )
    n_cols = cols_max if cols is None else int(cols)
    n_rows = rows_max if rows is None else int(rows)
    if n_cols < 1 or n_rows < 1:
        raise ValueError("draw_via1_array: rows and cols must be at least 1")

    # V1.b1: an array with more than 3 rows *and* more than 3 columns needs
    # 290 nm of spacing in one direction.  Widen the columns, and re-check the
    # fit, because the wider pitch may not fit at all.
    x_spacing = spacing
    if n_rows > _VIA1_ARRAY_ROWS_TRIGGER and n_cols > _VIA1_ARRAY_ROWS_TRIGGER:
        x_spacing = _VIA1_ARRAY_SPACING_NM
        cols_max = fit(rect.width, h_margin, x_spacing)
        if cols is None:
            n_cols = max(cols_max, 1)

    if n_cols > cols_max or n_rows > rows_max:
        raise ValueError(
            f"V1.b/V1.b1: {n_rows} x {n_cols} Via1 cuts do not fit in a "
            f"{rect.width:g} x {rect.height:g} nm landing; at {via:g} nm per "
            f"cut with {x_spacing:g} nm column and {spacing:g} nm row spacing "
            f"and {h_margin:g}/{v_margin:g} nm margins, at most "
            f"{rows_max} x {cols_max} fit"
        )

    span_x = n_cols * via + (n_cols - 1) * x_spacing
    span_y = n_rows * via + (n_rows - 1) * spacing
    # Centre the array, then snap down to the grid; the margins are re-checked
    # below so the snap can never eat into an enclosure.
    x0 = _ceil_to(rect.center.x - span_x / 2.0, _DRAWING_GRID_NM)
    y0 = _ceil_to(rect.center.y - span_y / 2.0, _DRAWING_GRID_NM)

    left_margin = x0 - rect.left
    right_margin = rect.right - (x0 + span_x)
    bottom_margin = y0 - rect.bottom
    top_margin = rect.top - (y0 + span_y)
    if min(left_margin, right_margin) < h_margin - 1e-9:
        raise ValueError(
            f"V1.c/M2.c: {n_cols} Via1 columns leave "
            f"{min(left_margin, right_margin):g} nm of metal at the side of a "
            f"{rect.width:g} nm wide landing; {h_margin:g} nm is required"
        )
    if min(bottom_margin, top_margin) < v_margin - 1e-9:
        raise ValueError(
            f"V1.c1/M2.c1: {n_rows} Via1 rows leave "
            f"{min(bottom_margin, top_margin):g} nm of metal above or below a "
            f"{rect.height:g} nm tall landing; {v_margin:g} nm is required so "
            f"the vertical pair can serve as the endcap pair"
        )

    cell = Cell("via1_array", t)
    cell.add_shape(RectShape(t["Metal1"], rect))
    cell.add_shape(RectShape(t["Metal2"], rect))
    for row in range(n_rows):
        for col in range(n_cols):
            left = x0 + col * (via + x_spacing)
            bottom = y0 + row * (via + spacing)
            cut = Rect.from_lbrt(left, bottom, left + via, bottom + via)
            _check_on_grid(cut, "Via1 cut")
            cell.add_shape(RectShape(t["Via1"], cut))
    return cell


def draw_m2_wire(rect: Rect, tech: Optional[Tech] = None) -> Cell:
    """Draw a Metal2 rectangle, refusing one the area or width rules forbid.

    Unlike :func:`draw_metal_wire` this checks, because Metal2's rules are the
    ones a Metal1-trained eye gets wrong: M2.d wants 0.144 um2 out of a shape
    whose minimum width is only 200 nm.
    """
    t = _tech(tech)
    layer = t["Metal2"]
    _check_on_grid(rect, "Metal2 wire")

    min_width = layer.min_width or 0.0
    if rect.width < min_width - 1e-9 or rect.height < min_width - 1e-9:
        raise ValueError(
            f"M2.a: Metal2 rectangle is {rect.width:g} x {rect.height:g} nm; "
            f"minimum width is {min_width:g} nm"
        )
    min_area = _min_area("Metal2", t)
    if rect.area < min_area - 1e-6:
        needed = m2_min_length_for_area(min(rect.width, rect.height), t)
        raise ValueError(
            f"M2.d: Metal2 rectangle is {rect.width:g} x {rect.height:g} nm = "
            f"{rect.area / 1e6:.4f} um2; minimum area is {min_area / 1e6:g} "
            f"um2, so at {min(rect.width, rect.height):g} nm wide it must be "
            f"at least {needed:g} nm long"
        )

    cell = Cell("m2_wire", t)
    cell.add_shape(RectShape(layer, rect))
    return cell


def draw_m2_pin(
    name: str,
    rect: Rect,
    tech: Optional[Tech] = None,
    *,
    direction: str = "INPUT",
) -> Cell:
    """Draw a Metal2 pin: drawing rectangle, pin rectangle, label and port.

    The pin rectangle is the drawing rectangle: Pin.f_M2 wants Metal2 to
    enclose Metal2:pin by at least 0, and an identical rectangle is the
    smallest thing that satisfies it while still marking the whole shape as
    connectable.
    """
    t = _tech(tech)
    # An empty or blank name draws a label with no text and registers a port
    # keyed on "": LEF, LVS and the Verilog stub then all carry a pin nobody
    # can name, and nothing downstream fails loudly enough to say why.
    if not isinstance(name, str) or not name.strip():
        raise ValueError(
            f"draw_m2_pin: pin name must be a non-empty string, not {name!r}"
        )
    layer = t["Metal2"]
    cell = draw_m2_wire(rect, t)
    cell.name = f"m2_pin_{name}"
    cell.add_shape(RectShape(_pin_layer(layer), rect))
    cell.add_shape(TextShape(layer, name, rect.center, purpose="label"))
    cell.add_port(Port(name, name, layer, rect, direction=direction))
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
    "draw_via1",
    "draw_via1_array",
    "draw_m2_wire",
    "draw_m2_pin",
    "m2_min_length_for_area",
    "via1_landing_rect",
]
