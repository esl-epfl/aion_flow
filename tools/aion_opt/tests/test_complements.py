"""Deciding where the inverter for a complemented cell input belongs."""

from __future__ import annotations

import json

import pytest

from aion_opt.graph.circuit import Circuit, Instance, Net
from aion_opt.io.cell_lib import CellLib
from aion_opt.io.complements import (
    ComplementPlan,
    analyse,
    default_inverter,
    find_complement_bit,
    inverter_pins,
    is_inverter,
    read_cell_interfaces,
)

TECH = {
    "sg13g2_inv_1": {"area": 5.4, "pins": {"Y": "output", "A": "input"}, "function": "!(A)"},
    "sg13g2_inv_4": {"area": 10.9, "pins": {"A": "input", "Y": "output"}, "function": "!(A)"},
    "sg13g2_buf_1": {"area": 7.3, "pins": {"A": "input", "X": "output"}, "function": "A"},
    "sg13g2_einvn_2": {
        "area": 9.1,
        "pins": {"Z": "output", "A": "input", "TE_B": "input"},
        "function": "!(A)",
    },
    "sg13g2_nand2_1": {
        "area": 7.3,
        "pins": {"Y": "output", "A": "input", "B": "input"},
        "function": "!(A*B)",
    },
}


@pytest.fixture
def lib(tmp_path):
    path = tmp_path / "tech.json"
    path.write_text(json.dumps({"cells": TECH}))
    return CellLib(path)


def test_inverters_are_recognised_from_the_function(lib):
    assert is_inverter(lib, "sg13g2_inv_1")
    assert is_inverter(lib, "sg13g2_inv_4")
    assert not is_inverter(lib, "sg13g2_buf_1")
    assert not is_inverter(lib, "sg13g2_nand2_1")


def test_a_tristate_inverter_is_not_an_inverter(lib):
    """`einvn` also reports `!(A)`; its enable pin is what rules it out."""
    assert not is_inverter(lib, "sg13g2_einvn_2")


def test_inverter_pins_are_found_whatever_the_dict_order(lib):
    assert inverter_pins(lib, "sg13g2_inv_1") == ("A", "Y")
    assert inverter_pins(lib, "sg13g2_inv_4") == ("A", "Y")


def test_the_cheapest_inverter_is_chosen(lib):
    assert default_inverter(lib) == "sg13g2_inv_1"


def test_no_inverter_in_the_technology_is_an_error(tmp_path):
    path = tmp_path / "t.json"
    path.write_text(json.dumps({"cells": {"x": TECH["sg13g2_nand2_1"]}}))
    with pytest.raises(ValueError, match="no single-input inverter"):
        default_inverter(CellLib(path))


def _circuit(instances, nets):
    circuit = Circuit(name="t")
    for inst in instances:
        circuit.instances[inst.name] = inst
    for net in nets:
        circuit.nets[net.name] = net
    return circuit


def test_complement_found_when_an_inverter_reads_the_net(lib):
    circuit = _circuit(
        [
            Instance(name="i0", cell_type="sg13g2_inv_1", connections={"A": [5], "Y": [6]}),
            Instance(name="u0", cell_type="sg13g2_nand2_1", connections={"A": [5], "B": [7], "Y": [8]}),
        ],
        [Net(name="n5", bits=[5], loads=[("i0", "A"), ("u0", "A")]), Net(name="n6", bits=[6], drivers=[("i0", "Y")])],
    )
    assert find_complement_bit(circuit, lib, 5) == 6


def test_complement_found_when_the_net_is_an_inverter_output(lib):
    circuit = _circuit(
        [Instance(name="i0", cell_type="sg13g2_inv_1", connections={"A": [5], "Y": [6]})],
        [Net(name="n6", bits=[6], drivers=[("i0", "Y")])],
    )
    assert find_complement_bit(circuit, lib, 6) == 5


def test_no_complement_when_nothing_inverts_the_net(lib):
    circuit = _circuit(
        [Instance(name="u0", cell_type="sg13g2_nand2_1", connections={"A": [5], "B": [7], "Y": [8]})],
        [Net(name="n5", bits=[5], loads=[("u0", "A")])],
    )
    assert find_complement_bit(circuit, lib, 5) is None


def test_a_multi_bit_net_does_not_leak_between_its_bits(lib):
    """The bug this guards: a `Net` aggregates every bit of a bus.

    `s[2:0]` is one `Net` whose `loads` mixes the consumers of `s[0]` with
    those of `s[1]`, so searching the net rather than the bit once returned
    `~s[1]` as the complement of `s[0]` — a silently wrong netlist.
    """
    bus = Net(name="s", bits=[10, 11, 12], loads=[("i1", "A")])
    circuit = _circuit(
        [Instance(name="i1", cell_type="sg13g2_inv_1", connections={"A": [11], "Y": [20]})],
        [bus, Net(name="n20", bits=[20], drivers=[("i1", "Y")])],
    )
    assert find_complement_bit(circuit, lib, 11) == 20
    assert find_complement_bit(circuit, lib, 10) is None
    assert find_complement_bit(circuit, lib, 12) is None


def test_an_absorbed_inverter_is_not_reused(lib):
    """Its output net will not survive the rewrite that absorbs it."""
    circuit = _circuit(
        [Instance(name="i0", cell_type="sg13g2_inv_1", connections={"A": [5], "Y": [6]})],
        [Net(name="n5", bits=[5], loads=[("i0", "A")])],
    )
    assert find_complement_bit(circuit, lib, 5) == 6
    assert find_complement_bit(circuit, lib, 5, excluded=["i0"]) is None


def test_constant_bits_have_no_complement(lib):
    assert find_complement_bit(_circuit([], []), lib, "0") is None


def _analysis_circuit(lib, sites, with_inverter):
    """`sites` sites of one cell, `with_inverter` of them already inverted."""
    instances = []
    nets = []
    for index in range(sites):
        bit = 100 + index
        loads = [(f"u{index}", "A")]
        instances.append(
            Instance(name=f"u{index}", cell_type="sg13g2_nand2_1",
                     connections={"A": [bit], "B": [0], "Y": [200 + index]})
        )
        if index < with_inverter:
            instances.append(
                Instance(name=f"i{index}", cell_type="sg13g2_inv_1",
                         connections={"A": [bit], "Y": [300 + index]})
            )
            loads.append((f"i{index}", "A"))
        nets.append(Net(name=f"n{bit}", bits=[bit], loads=loads))
    return _circuit(instances, nets), [
        ("k", {(f"n{100 + i}", f"u{i}", "A"): "I0"}) for i in range(sites)
    ]


def test_externalizing_wins_when_the_complements_already_exist(lib):
    circuit, occurrences = _analysis_circuit(lib, sites=6, with_inverter=6)
    plan = analyse(circuit, lib, occurrences, {"k": "CELL"})
    stat = plan.modules["CELL"]["stats"]["I0"]
    assert (stat["occurrences"], stat["complement_available"]) == (6, 6)
    assert (stat["internal_devices"], stat["external_devices"]) == (12, 0)
    assert plan.external_ports("CELL") == ["I0"]


def test_externalizing_loses_when_every_site_needs_a_new_inverter(lib):
    circuit, occurrences = _analysis_circuit(lib, sites=4, with_inverter=0)
    plan = analyse(circuit, lib, occurrences, {"k": "CELL"})
    stat = plan.modules["CELL"]["stats"]["I0"]
    # Four distinct nets, so four new inverters: eight devices either way.
    assert (stat["internal_devices"], stat["external_devices"]) == (8, 8)
    assert plan.external_ports("CELL") == []


def test_sites_sharing_a_net_share_one_inverter(lib):
    """Two sites on the same signal only ever need one inverter."""
    circuit = _circuit(
        [
            Instance(name="u0", cell_type="sg13g2_nand2_1", connections={"A": [5], "B": [0], "Y": [1]}),
            Instance(name="u1", cell_type="sg13g2_nand2_1", connections={"A": [5], "B": [0], "Y": [2]}),
        ],
        [Net(name="n5", bits=[5], loads=[("u0", "A"), ("u1", "A")])],
    )
    occurrences = [("k", {("n5", "u0", "A"): "I0"}), ("k", {("n5", "u1", "A"): "I0"})]
    stat = analyse(circuit, lib, occurrences, {"k": "CELL"}).modules["CELL"]["stats"]["I0"]
    assert (stat["occurrences"], stat["new_inverters"]) == (2, 1)
    assert (stat["internal_devices"], stat["external_devices"]) == (4, 2)


def test_only_ports_the_minimizer_asked_about_are_costed(lib):
    circuit, occurrences = _analysis_circuit(lib, sites=6, with_inverter=6)
    plan = analyse(circuit, lib, occurrences, {"k": "CELL"}, eligible_ports={"CELL": []})
    assert plan.modules == {}


def test_plan_round_trips(tmp_path, lib):
    circuit, occurrences = _analysis_circuit(lib, sites=6, with_inverter=6)
    plan = analyse(circuit, lib, occurrences, {"k": "CELL"})
    path = tmp_path / "plan.json"
    plan.write(path)
    assert ComplementPlan.read(path).modules == plan.modules
    assert ComplementPlan.read(path).complement_ports("CELL") == {"I0_bar": "I0"}


def test_a_plan_from_another_version_is_rejected(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps({"version": 99, "modules": {}}))
    with pytest.raises(ValueError, match="version"):
        ComplementPlan.read(path)


def test_reading_minimizer_reports(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({
        "cell": "AION_x_0",
        "complemented_inputs": {"internal": ["I1"], "external": [], "nets": ["w0"]},
    }))
    assert read_cell_interfaces([tmp_path / "a.json"]) == {"AION_x_0": ["I1"]}
