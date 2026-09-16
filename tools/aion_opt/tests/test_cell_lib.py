"""Technology-dictionary handling, notably drive-strength collapsing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aion_opt.io.cell_lib import CellLib, collapse_cell_name

REPO_ROOT = Path(__file__).resolve().parents[3]
TECH_DICT = REPO_ROOT / "tech" / "tech_dict" / "sg13g2_stdcell.json"


@pytest.mark.parametrize(
    "name,expected",
    [
        ("sg13g2_inv_1", "sg13g2_inv"),
        ("sg13g2_inv_16", "sg13g2_inv"),   # regression: only _1/_2 were stripped
        ("sg13g2_buf_4", "sg13g2_buf"),
        ("sg13g2_buf_8", "sg13g2_buf"),
        ("sg13g2_and4_1", "sg13g2_and4"),  # the input count must survive
        ("sg13g2_a221oi_1", "sg13g2_a221oi"),
        ("sg13g2_tielo", "sg13g2_tielo"),
        ("sg13g2_sighold", "sg13g2_sighold"),
    ],
)
def test_collapse_strips_only_the_drive_strength(name, expected):
    assert collapse_cell_name(name) == expected


@pytest.mark.skipif(not TECH_DICT.exists(), reason="technology dictionary not present")
def test_every_strength_variant_folds_onto_one_key():
    lib = CellLib(TECH_DICT)
    raw = json.loads(TECH_DICT.read_text())
    raw = raw.get("cells", raw)

    for name in raw:
        assert name in lib, f"{name} is not resolvable through the collapsed keys"

    # All five inverter strengths must share a single generic entry.
    inverters = {n for n in raw if n.startswith("sg13g2_inv_")}
    assert len(inverters) > 1
    assert {lib.collapse_name(n) for n in inverters} == {"sg13g2_inv"}


@pytest.mark.skipif(not TECH_DICT.exists(), reason="technology dictionary not present")
def test_representative_is_the_smallest_variant():
    lib = CellLib(TECH_DICT)
    raw = json.loads(TECH_DICT.read_text())
    raw = raw.get("cells", raw)
    variants = {n: raw[n]["area"] for n in raw if n.startswith("sg13g2_inv_")}
    assert lib.area("sg13g2_inv") == min(variants.values())
    assert lib.concrete_name("sg13g2_inv") in variants


def _leaf_design(tmp_path):
    """nand2 -> AION_mux2i_1 -> nand2, with the hand-designed cell marked a leaf."""
    tech = tmp_path / "tech.json"
    tech.write_text(json.dumps({"cells": {
        "sg13g2_nand2_1": {"area": 7.26, "pins": {"A": "input", "B": "input", "Y": "output"},
                           "function": "!(A*B)"},
        "AION_mux2i_1": {"area": 12.70, "pins": {"I0": "input", "I1": "input", "I2": "input",
                                                 "O0": "output"},
                         "function": "!I2*!I0+I2*!I1", "mineable": False},
    }}))

    def cell(kind, **pins):
        return {"type": kind, "connections": pins}

    netlist = tmp_path / "top.json"
    netlist.write_text(json.dumps({"modules": {"top": {
        "attributes": {"top": 1},
        "ports": {"a": {"direction": "input", "bits": [2]},
                  "b": {"direction": "input", "bits": [3]},
                  "y": {"direction": "output", "bits": [6]}},
        "cells": {
            "g0": cell("sg13g2_nand2_1", A=[2], B=[3], Y=[4]),
            "m0": cell("AION_mux2i_1", I0=[4], I1=[2], I2=[3], O0=[5]),
            "g1": cell("sg13g2_nand2_1", A=[5], B=[4], Y=[6]),
        },
        "netnames": {},
    }}}))
    return CellLib(tech), netlist


def test_a_cell_marked_not_mineable_stays_a_leaf(tmp_path):
    """The PDK-extension mux: known, combinational, and never inside a pattern.

    Mined into a pattern, AION_mux2i_1 would be rebuilt by the minimizer from
    its function as static CMOS -- losing the transmission gates it exists for
    -- and step 6 would have no PDK layout to build the pattern's baseline from.
    Kept out of the graph, it stays in the netlist and its pins are pattern
    boundaries, exactly as a flip-flop's are.
    """
    from aion_opt.graph.builder import build_signal_flow_graph
    from aion_opt.io.yosys_json import load_yosys_json

    lib, netlist = _leaf_design(tmp_path)
    assert "AION_mux2i_1" in lib and lib.is_combinational("AION_mux2i_1")
    assert not lib.is_mineable("AION_mux2i_1")
    assert lib.is_mineable("sg13g2_nand2_1")
    assert "AION_mux2i" not in lib.mineable_types()
    assert "AION_mux2i" in lib.combinational_types(), "the classification itself is unchanged"

    circuit = load_yosys_json(netlist, cell_lib=lib)
    sfg = build_signal_flow_graph(circuit, lib)

    assert "m0" in circuit.instances, "the leaf is kept in the design"
    assert sfg.nodes() == {"g0", "g1"}
    assert sfg.fanout("g0") == {"g1"}, "g0 -> g1 directly is still one edge"
    through_leaf = [edge for edge in sfg.pin_edges if "m0" in (edge[0], edge[2])]
    assert {(src, dst) for src, _, dst, _, _ in through_leaf} == {("g0", "m0"), ("m0", "g1")}, (
        "the leaf's connections are kept as pattern boundaries")


@pytest.mark.skipif(not TECH_DICT.exists(), reason="technology dictionary not present")
def test_sequential_and_physical_cells_are_excluded_from_mining():
    lib = CellLib(TECH_DICT)
    combinational = lib.combinational_types()

    for name in ("sg13g2_dfrbp", "sg13g2_sdfrbp", "sg13g2_dlhq", "sg13g2_slgcp"):
        assert name not in combinational, f"{name} must not be mined"
    for name in ("sg13g2_fill", "sg13g2_decap", "sg13g2_antennanp", "sg13g2_sighold"):
        assert name not in combinational, f"{name} carries no logic"
    for name in ("sg13g2_nand2", "sg13g2_xor2", "sg13g2_mux2", "sg13g2_a21oi"):
        assert name in combinational
