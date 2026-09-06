"""Geometry must be layout-legal for the SG13G2 cell row."""

from __future__ import annotations

import pytest

from aion_minimizer.cost_model import Inverter
from aion_minimizer.pn_network import Literal, Switch, TransistorNetwork
from aion_minimizer.sizing import (
    DEFAULT_WN,
    DEFAULT_WP,
    SizingRules,
    size_inverter,
    size_network,
)


def three_deep_network() -> TransistorNetwork:
    stack = [Switch("n", Literal(name)) for name in "ABC"]
    groups = [[Switch("p", Literal(name, True))] for name in "ABC"]
    return TransistorNetwork(output="Y", p_branches=groups, n_branches=[stack])


def test_base_drive_matches_the_x1_cells():
    """``nand4_1`` uses the same widths as ``inv_1``: no stack compensation."""
    sized = size_network(three_deep_network(), SizingRules())
    for device in [d for b in sized.n_branches for d in b]:
        assert (device.w, device.ng) == (DEFAULT_WN, 1)
    for device in [d for b in sized.p_branches for d in b]:
        assert (device.w, device.ng) == (DEFAULT_WP, 1)


@pytest.mark.parametrize("drive,wn,wp", [(1, "0.74u", "1.12u"), (4, "2.96u", "4.48u"), (16, "11.84u", "17.92u")])
def test_drive_strength_folds_exactly_like_the_pdk(drive, wn, wp):
    """``inv_1``/``inv_4``/``inv_16`` widths, with ``ng`` equal to the drive."""
    sized = size_network(three_deep_network(), SizingRules(drive=drive))
    n = sized.n_branches[0][0]
    p = sized.p_branches[0][0]
    assert (n.w, n.ng) == (wn, drive)
    assert (p.w, p.ng) == (wp, drive)


def test_stack_sizing_widens_by_depth_and_folds():
    """Opt-in compensation still folds, so the finger width never grows."""
    sized = size_network(three_deep_network(), SizingRules(stack_sizing=True))
    n = sized.n_branches[0][0]
    assert (n.w, n.ng) == ("2.22u", 3)
    p = sized.p_branches[0][0]
    assert (p.w, p.ng) == ("3.36u", 3)


def test_max_fingers_caps_runaway_widths():
    rules = SizingRules(drive=8, stack_sizing=True, max_fingers=4)
    sized = size_network(three_deep_network(), rules)
    assert all(d.ng <= 4 for b in sized.n_branches for d in b)


def test_inverters_are_sized_at_the_base_drive():
    inv = size_inverter(Inverter(input="A", output="A_bar"), SizingRules())
    assert (inv.nmos.w, inv.nmos.ng) == (DEFAULT_WN, 1)
    assert (inv.pmos.w, inv.pmos.ng) == (DEFAULT_WP, 1)


@pytest.mark.parametrize("bad", [{"drive": 0}, {"max_fingers": 0}, {"wn": "wide"}])
def test_invalid_rules_are_rejected_eagerly(bad):
    with pytest.raises(ValueError):
        SizingRules(**bad)
