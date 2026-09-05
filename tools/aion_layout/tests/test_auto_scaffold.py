# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               The scaffold must never hand the model a short
# ================================================================

"""The auto-scaffold is the model's starting point; it must not start broken.

The historical defect, still reproducible from
``tests/fixtures/iteration_0/AION_inv_nand2_nor2_1.py``: the scaffold emitted
the ``I1`` Metal1 input bar at ``(1295,1390)-(1585,1820)`` and the ``O0`` Metal1
output stub at ``(1310,1330)-(1570,2060)``.  They overlap, so ``I1`` and ``O0``
were one electrical node in the layout.  Extraction found 5 ports instead of 6 --
``I1`` was gone -- and the model spent every iteration chasing an LVS mismatch
its own starting geometry had created.

For an odd input count the middle gate sits at ``CELL_WIDTH/2``, i.e. directly
under the output stub, so the two kinds of Metal1 stub must never share a
horizontal band.
"""

from __future__ import annotations

import importlib.util
import itertools
import sys

import pytest

from aion_layout.auto_scaffold import generate_scaffold_source
from aion_layout.spice_parser import parse_first_subckt, parse_spice
from aion_layout.tech import sg13g2_tech


def _build_cell(source: str, tmp_path, name: str, cell_name: str = "SCAFFOLD"):
    """Write the generated source to a real module, import it, run generate()."""
    path = tmp_path / f"{name}.py"
    path.write_text(source)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, (
        f"{path} is not importable as a Python module; the build gate loads the "
        "generator exactly this way and would reject it"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        assert hasattr(module, "generate"), (
            f"the scaffold must define generate(cell_name, tech); "
            f"scripts/generate_cell.py and the build gate both refuse it otherwise"
        )
        return module.generate(cell_name, sg13g2_tech)
    finally:
        sys.modules.pop(name, None)


def _cross_net_overlaps(named):
    """Return every ((net_a, rect_a), (net_b, rect_b)) pair that overlaps."""
    return [
        (a, b)
        for a, b in itertools.combinations(named, 2)
        if a[0] != b[0] and a[1].overlaps(b[1])
    ]


def _cross_net_touches(named):
    """Return every different-net pair that shares an edge or corner."""
    out = []
    for (net_a, rect_a), (net_b, rect_b) in itertools.combinations(named, 2):
        if net_a == net_b:
            continue
        gap_x = max(rect_a.left - rect_b.right, rect_b.left - rect_a.right)
        gap_y = max(rect_a.bottom - rect_b.top, rect_b.bottom - rect_a.top)
        if max(gap_x, gap_y) <= 0:
            out.append(((net_a, rect_a), (net_b, rect_b)))
    return out


# ---------------------------------------------------------------------------
# The detector itself must not be vacuous
# ---------------------------------------------------------------------------

def test_detector_finds_the_historical_short(iter0_module, cell_name, metal1_net_rects, tmp_path):
    """Run the check against the artifact that has the bug: it must fire."""
    cell = _build_cell(
        iter0_module.read_text(), tmp_path, "historical_scaffold", cell_name
    )
    named, unnamed = metal1_net_rects(cell, sg13g2_tech)
    overlaps = _cross_net_overlaps(named)
    nets = {frozenset((a[0], b[0])) for a, b in overlaps}
    assert frozenset({"I1", "O0"}) in nets, (
        f"the captured iteration_0 generator shorts I1 to O0 through Metal1, but "
        f"the check found {nets}.  If this assertion fails the overlap test "
        "below proves nothing -- it would pass on a generator that is broken."
    )
    assert unnamed == [], (
        f"{len(unnamed)} Metal1 rectangle(s) match no Port, so a short involving "
        "them would go undetected"
    )


# ---------------------------------------------------------------------------
# Every input count
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n_inputs", [1, 2, 3, 4, 5, 6])
def test_scaffold_has_no_cross_net_metal1_overlap(
    n_inputs, synthetic_netlist, metal1_net_rects, tmp_path
):
    subckt = parse_spice(synthetic_netlist(n_inputs))[0]
    assert len(subckt.input_nets) == n_inputs, (
        f"the synthetic {n_inputs}-input netlist must expose {n_inputs} inputs, "
        f"got {subckt.input_nets}; otherwise this case does not test what it says"
    )
    cell = _build_cell(
        generate_scaffold_source(subckt), tmp_path, f"scaffold_{n_inputs}"
    )
    named, unnamed = metal1_net_rects(cell, sg13g2_tech)

    assert unnamed == [], (
        f"{n_inputs} inputs: {len(unnamed)} Metal1 rectangle(s) belong to no "
        f"Port ({unnamed}); an unattributed rectangle is one this check cannot "
        "see, so the absence of overlaps below would mean nothing"
    )
    overlaps = _cross_net_overlaps(named)
    assert overlaps == [], (
        f"{n_inputs} inputs: the scaffold shorts "
        f"{[(a[0], b[0]) for a, b in overlaps]} through Metal1 -- "
        f"{[(str(a[1]), str(b[1])) for a, b in overlaps]}.  A scaffold that "
        "starts with a short costs the model every iteration it spends chasing "
        "an LVS mismatch its own starting geometry created."
    )
    touches = _cross_net_touches(named)
    assert touches == [], (
        f"{n_inputs} inputs: Metal1 rectangles of different nets touch: "
        f"{[(a[0], b[0]) for a, b in touches]}.  Abutting metal is one node too, "
        "so an edge-exact 'non-overlap' is still a short."
    )


@pytest.mark.parametrize("n_inputs", [1, 2, 3, 4, 5, 6])
def test_scaffold_exposes_every_input_as_its_own_port(
    n_inputs, synthetic_netlist, tmp_path
):
    subckt = parse_spice(synthetic_netlist(n_inputs))[0]
    cell = _build_cell(
        generate_scaffold_source(subckt), tmp_path, f"ports_{n_inputs}"
    )
    nets = {p.net for p in cell.ports.values()}
    expected = set(subckt.input_nets) | {"O0", "VDD", "VSS"}
    assert nets == expected, (
        f"{n_inputs} inputs: expected ports for {sorted(expected)}, got "
        f"{sorted(nets)}.  Every input needs its own declared Port or extraction "
        "has no label to name the node from.  (Declaring the port is necessary "
        "but not sufficient: two ports whose Metal1 overlaps still extract as "
        "one node, which is what the overlap test above covers.)"
    )


# ---------------------------------------------------------------------------
# The netlist the historical run used
# ---------------------------------------------------------------------------

def test_fixture_netlist_scaffold_is_short_free(
    netlist_path, metal1_net_rects, tmp_path
):
    subckt = parse_first_subckt(netlist_path)
    assert subckt.input_nets == ["I0", "I1", "I2"], (
        f"the fixture netlist has three external inputs, got {subckt.input_nets}"
    )
    cell = _build_cell(generate_scaffold_source(subckt), tmp_path, "scaffold_fixture")
    named, unnamed = metal1_net_rects(cell, sg13g2_tech)
    assert unnamed == [], f"unattributed Metal1 rectangles: {unnamed}"

    overlaps = _cross_net_overlaps(named)
    assert overlaps == [], (
        f"the fixture netlist still scaffolds with a short: "
        f"{[(a[0], b[0]) for a, b in overlaps]}"
    )

    by_net = dict(named)
    i1, o0 = by_net["I1"], by_net["O0"]
    assert not i1.overlaps(o0), (
        f"the specific historical short is back: I1 at {i1} overlaps O0 at {o0}. "
        "With three inputs the middle gate sits at CELL_WIDTH/2, exactly under "
        "the output stub, which is why these two are the pair that merged."
    )
    assert i1.bottom > o0.top or o0.bottom > i1.top, (
        f"I1 {i1} and O0 {o0} must occupy separate horizontal Metal1 bands; "
        "sharing a band is what made them one node in the captured run"
    )
    gap = i1.bottom - o0.top
    assert gap >= 180.0, (
        f"the gap between the output stub band and the input bar band is {gap} "
        "nm, below the 180 nm Metal1 minimum spacing; a sub-spacing gap trades "
        "a short for a DRC violation instead of fixing it"
    )


def test_fixture_netlist_scaffold_still_misses_the_internal_gate_net(netlist_path):
    """Documented gap: the scaffold gates external inputs only.

    ``suggest_gate_order`` returns ``subckt.input_nets``, which is the three
    external pins.  The netlist has four gate nets -- the fourth is the internal
    node ``I1_bar`` -- so the scaffold is one device per type short.  The model
    is expected to add it; this test pins the fact so it stays visible rather
    than being rediscovered from an LVS log every run.
    """
    subckt = parse_first_subckt(netlist_path)
    gate_nets = {d.gate for d in subckt.devices}
    assert gate_nets == {"I0", "I1", "I2", "I1_bar"}, (
        f"the fixture netlist has four distinct gate nets, got {gate_nets}"
    )
    assert set(subckt.input_nets) == {"I0", "I1", "I2"}, (
        "input_nets is the external pins only"
    )
    assert "I1_bar" not in subckt.input_nets, (
        "if the scaffold ever starts gating internal nets this test should be "
        "rewritten to assert the stronger property, not deleted"
    )
    assert len(subckt.devices) == 8, (
        f"the netlist declares 4 nmos + 4 pmos, got {len(subckt.devices)} devices"
    )


def test_scaffold_source_compiles_for_every_input_count(synthetic_netlist):
    """A scaffold that does not compile blocks the build gate before iteration 0."""
    for n in range(1, 7):
        subckt = parse_spice(synthetic_netlist(n))[0]
        source = generate_scaffold_source(subckt)
        compile(source, f"<scaffold_{n}>", "exec")
        assert "def generate(" in source, (
            f"{n} inputs: the scaffold must define generate(); the pipeline "
            "calls it by name"
        )
