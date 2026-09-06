# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Golden tests for the well/substrate tap block
# ================================================================

"""``draw_tap`` is the only thing that can clear LU.a / LU.b.

Every DRC violation in the captured run is a latch-up rule: a diffusion too far
from a well or substrate tap.  Before this block existed the words *tap*, *tie*
and *latch-up* appeared nowhere in the layout API or its documentation, so the
one fix the report demanded was not expressible -- the model could read
``P-diff distance to N-tap must be < 20.0um`` and had no call to make.
"""

from __future__ import annotations

import pytest

from aion_layout import building_blocks
from aion_layout.building_blocks import draw_tap
from aion_layout.primitives import Rect
from aion_layout.shapes import RectShape, TextShape
from aion_layout.tech import sg13g2_tech as TECH

RULES = TECH.design_rules
CONT_SIZE = RULES["via_size_nm"]["Cont"]
METAL1_CONT_ENC = RULES["min_enclosure_nm"]["Metal1"]["Cont"]
NSD_CONT_ENC = RULES["min_enclosure_nm"]["NSD"]["Cont"]
PSD_CONT_ENC = RULES["min_enclosure_nm"]["PSD"]["Cont"]

TAP_RECT = Rect.from_lbrt(0.0, 0.0, 1200.0, 500.0)


def _rects(cell, layer_name):
    layer = TECH[layer_name]
    return [s.rect for s in cell.shapes.get(layer, []) if isinstance(s, RectShape)]


def _texts(cell, layer_name):
    layer = TECH[layer_name]
    return [s for s in cell.shapes.get(layer, []) if isinstance(s, TextShape)]


def _margin(outer: Rect, inner: Rect) -> float:
    """Smallest edge-to-edge distance from ``inner`` out to ``outer``."""
    return min(
        inner.left - outer.left,
        inner.bottom - outer.bottom,
        outer.right - inner.right,
        outer.top - inner.top,
    )


# ---------------------------------------------------------------------------
# The fix has to be reachable at all
# ---------------------------------------------------------------------------

def test_draw_tap_is_part_of_the_public_api():
    assert "draw_tap" in building_blocks.__all__, (
        "draw_tap must be exported; a block that is not in __all__ is not in the "
        "generated API reference either, and the model cannot call what the "
        "documentation never names -- that is why LU.a/LU.b went unfixed for "
        "every iteration of the captured run"
    )


# ---------------------------------------------------------------------------
# Shapes, both tap types
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tap_type,net", [("n", "VDD"), ("p", "VSS")])
def test_tap_emits_activ_cont_and_metal1(tap_type, net):
    cell = draw_tap(TAP_RECT, tap_type, net)
    activ = _rects(cell, "Activ")
    cont = _rects(cell, "Cont")
    metal1 = _rects(cell, "Metal1")

    assert activ == [TAP_RECT], (
        f"'{tap_type}' tap: Activ must be exactly the requested tap area, got "
        f"{activ}; the caller places the tap and the block must not move it"
    )
    assert len(cont) >= 1, (
        f"'{tap_type}' tap: no Cont cut was drawn; without a contact the implant "
        "is not tied to anything and the latch-up rule is still violated"
    )
    assert len(metal1) == 1, (
        f"'{tap_type}' tap: expected one Metal1 landing, got {metal1}; the tie "
        "to the power rail is what makes the tap a tap"
    )


@pytest.mark.parametrize("tap_type,net", [("n", "VDD"), ("p", "VSS")])
def test_tap_declares_a_port_on_the_requested_net(tap_type, net):
    cell = draw_tap(TAP_RECT, tap_type, net)
    ports = list(cell.ports.values())
    assert len(ports) == 1, (
        f"'{tap_type}' tap: expected exactly one Port, got {ports}"
    )
    port = ports[0]
    assert port.net == net and port.name == net, (
        f"'{tap_type}' tap: the port must carry the requested net {net!r}, got "
        f"name={port.name!r} net={port.net!r}; extraction identifies the tie by "
        "this net and a mislabelled tap reads as a floating node"
    )
    assert port.layer == TECH["Metal1"], (
        f"the port must be on Metal1 so it can abut the power rail, got "
        f"{port.layer.name}"
    )
    assert port.rect == _rects(cell, "Metal1")[0], (
        "the port rectangle must be the Metal1 landing that was actually drawn, "
        "not a phantom rectangle with no geometry behind it"
    )
    expected_direction = {"VDD": "POWER", "VSS": "GROUND"}[net]
    assert port.direction == expected_direction, (
        f"a tap tied to {net} must be a {expected_direction} port, got "
        f"{port.direction}"
    )

    labels = _texts(cell, "Metal1")
    assert [t.text for t in labels if t.purpose == "label"] == [net], (
        f"'{tap_type}' tap: a Metal1 label named {net!r} must be emitted, got "
        f"{[(t.text, t.purpose) for t in labels]}; Magic's extraction names the "
        "node from the label, and an unlabelled tie extracts as an anonymous net"
    )


def test_non_rail_net_is_an_inout_port():
    cell = draw_tap(TAP_RECT, "p", "VBB")
    port = next(iter(cell.ports.values()))
    assert port.direction == "INOUT", (
        f"a tap on a net that is not VDD/VSS must be INOUT, got {port.direction}; "
        "hard-coding POWER/GROUND would misdeclare a body-bias tie"
    )


# ---------------------------------------------------------------------------
# Implants
# ---------------------------------------------------------------------------

def test_p_tap_emits_psd():
    cell = draw_tap(TAP_RECT, "p", "VSS")
    psd = _rects(cell, "PSD")
    assert psd == [TAP_RECT], (
        f"a p+ substrate tap must carry the PSD implant over the whole tap area, "
        f"got {psd}; without PSD the shape is an n+ region and ties nothing"
    )


def test_n_tap_emits_no_psd_and_no_nsd_drawing_layer():
    cell = draw_tap(TAP_RECT, "n", "VDD")
    layer_names = {layer.name for layer in cell.shapes}
    assert "PSD" not in layer_names, (
        f"an n+ tap must not carry PSD, got layers {sorted(layer_names)}; PSD "
        "over an n+ tap inverts the doping and the tie stops working"
    )
    assert "NSD" not in layer_names, (
        f"n+ is the SG13G2 default doping, so no NSD drawing layer is emitted -- "
        f"this matches draw_diffusion.  Got layers {sorted(layer_names)}"
    )
    assert layer_names == {"Activ", "Cont", "Metal1"}, (
        f"an n tap is Activ + Cont + Metal1 and nothing else, got "
        f"{sorted(layer_names)}"
    )


# ---------------------------------------------------------------------------
# Enclosures, straight out of tech.design_rules
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "tap_type,net,implant_layer,implant_enc",
    [
        ("n", "VDD", "Activ", NSD_CONT_ENC),
        ("p", "VSS", "PSD", PSD_CONT_ENC),
    ],
)
def test_cut_enclosures_match_the_design_rules(tap_type, net, implant_layer, implant_enc):
    cell = draw_tap(TAP_RECT, tap_type, net)
    cuts = _rects(cell, "Cont")
    landing = _rects(cell, "Metal1")[0]
    implant = _rects(cell, implant_layer)[0]

    for cut in cuts:
        assert cut.width == CONT_SIZE and cut.height == CONT_SIZE, (
            f"'{tap_type}' tap: a Cont cut is {cut.width}x{cut.height} nm but the "
            f"technology fixes it at {CONT_SIZE} nm; an off-size cut is a DRC "
            "violation of its own"
        )
        assert _margin(landing, cut) >= METAL1_CONT_ENC, (
            f"'{tap_type}' tap: Metal1 encloses the cut by {_margin(landing, cut)} "
            f"nm, below the {METAL1_CONT_ENC} nm required by "
            f"design_rules['min_enclosure_nm']['Metal1']['Cont']; a tap that "
            "trades LU.a for a Cont enclosure error has not helped anyone"
        )
        assert _margin(implant, cut) >= implant_enc, (
            f"'{tap_type}' tap: {implant_layer} encloses the cut by "
            f"{_margin(implant, cut)} nm, below the required {implant_enc} nm"
        )

    if len(cuts) > 1:
        ordered = sorted(cuts, key=lambda r: (r.left, r.bottom))
        for a, b in zip(ordered, ordered[1:]):
            gap = max(b.left - a.right, b.bottom - a.top)
            assert gap >= building_blocks._ASSUMED_CONT_SPACING_NM, (
                f"'{tap_type}' tap: adjacent cuts are {gap} nm apart, below the "
                f"{building_blocks._ASSUMED_CONT_SPACING_NM} nm assumed "
                "contact-to-contact minimum; a tap row that shorts its own cuts "
                "together is a width violation, not a tie"
            )


def test_cut_row_follows_the_longer_axis():
    wide = draw_tap(Rect.from_lbrt(0, 0, 2000, 500), "p", "VSS")
    tall = draw_tap(Rect.from_lbrt(0, 0, 500, 2000), "p", "VSS")
    wide_cuts = sorted(_rects(wide, "Cont"), key=lambda r: r.left)
    tall_cuts = sorted(_rects(tall, "Cont"), key=lambda r: r.bottom)
    assert len(wide_cuts) > 1 and len(tall_cuts) > 1, (
        "a tap long enough for several cuts must get several cuts; one contact "
        "on a long tap is a current-density problem and wastes the implant"
    )
    assert {c.bottom for c in wide_cuts} == {wide_cuts[0].bottom}, (
        f"a wide tap must lay its cuts out along x, got {wide_cuts}"
    )
    assert {c.left for c in tall_cuts} == {tall_cuts[0].left}, (
        f"a tall tap must lay its cuts out along y, got {tall_cuts}"
    )


# ---------------------------------------------------------------------------
# Rejection paths
# ---------------------------------------------------------------------------

def test_too_small_rect_raises_value_error():
    min_side = CONT_SIZE + 2.0 * PSD_CONT_ENC
    too_small = Rect.from_lbrt(0.0, 0.0, min_side - 1.0, min_side - 1.0)
    with pytest.raises(ValueError) as excinfo:
        draw_tap(too_small, "p", "VSS")
    message = str(excinfo.value)
    assert str(int(min_side)) in message or f"{min_side:g}" in message, (
        f"the error must state the minimum size the caller needs, got {message!r}; "
        "silently emitting a tap with no room for its enclosure would produce a "
        "DRC violation instead of a diagnosable error"
    )
    assert "Cont" in message and "enclosure" in message, (
        f"the error must explain which rule the rect cannot satisfy, got {message!r}"
    )


def test_exactly_minimum_rect_is_accepted():
    """The rejection above must not also reject the smallest legal tap."""
    min_side = CONT_SIZE + 2.0 * PSD_CONT_ENC
    cell = draw_tap(Rect.from_lbrt(0.0, 0.0, min_side, min_side), "p", "VSS")
    assert len(_rects(cell, "Cont")) == 1, (
        "the smallest legal tap holds exactly one contact; rejecting it would "
        "make a tap unplaceable in a tight standard cell"
    )


def test_unknown_tap_type_raises_value_error():
    with pytest.raises(ValueError) as excinfo:
        draw_tap(TAP_RECT, "x", "VSS")
    message = str(excinfo.value)
    assert "'n'" in message and "'p'" in message, (
        f"the error must name the two accepted tap types, got {message!r}; the "
        "caller is a model reading the exception text"
    )
