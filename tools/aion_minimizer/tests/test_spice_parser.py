"""Parser behaviour, including the malformed inputs it has to reject."""

from __future__ import annotations

import pytest

from aion_minimizer.spice_parser import parse_spice


def test_parses_mosfets_and_instances():
    text = """
* a comment
.subckt cell Y A VDD VSS
XN0 Y A VSS VSS sg13_lv_nmos w=740.00n l=130.00n ng=1
XP0 Y A VDD VDD sg13_lv_pmos w=1.12u l=130.00n ng=1
.ends
.subckt top I0 O0 VDD VSS
Xg0 O0 I0 VDD VSS cell
.ends
"""
    subckts = parse_spice(text)
    assert set(subckts) == {"cell", "top"}
    assert subckts["cell"].is_gate_definition
    assert not subckts["top"].is_gate_definition
    assert subckts["cell"].mosfets[0].params["w"] == "740.00n"
    assert subckts["top"].instances[0].subckt_name == "cell"


def test_line_continuations_are_joined():
    text = """
.subckt cell Y A VDD VSS
XN0 Y A VSS VSS sg13_lv_nmos
+ w=740.00n l=130.00n
.ends
"""
    (mos,) = parse_spice(text)["cell"].mosfets
    assert mos.params == {"w": "740.00n", "l": "130.00n"}


def test_subckt_parameters_are_not_pins():
    """``.subckt`` may carry defaults; they would otherwise become terminals."""
    text = ".subckt cell Y A VDD VSS wn=740n\nXN0 Y A VSS VSS sg13_lv_nmos\n.ends\n"
    assert parse_spice(text)["cell"].pins == ["Y", "A", "VDD", "VSS"]


@pytest.mark.parametrize("marker", ["$", ";"])
def test_inline_comments_are_stripped(marker):
    text = f".subckt cell Y A VDD VSS {marker} the inverter\nXN0 Y A VSS VSS sg13_lv_nmos\n.ends\n"
    assert parse_spice(text)["cell"].pins == ["Y", "A", "VDD", "VSS"]


def test_unclosed_subckt_is_rejected():
    with pytest.raises(ValueError, match="Unclosed"):
        parse_spice(".subckt cell Y A VDD VSS\nXN0 Y A VSS VSS sg13_lv_nmos\n")


def test_nested_subckt_is_rejected():
    with pytest.raises(ValueError, match="Nested"):
        parse_spice(".subckt a Y\n.subckt b Y\n.ends\n.ends\n")


def test_duplicate_subckt_is_rejected():
    text = ".subckt a Y VDD VSS\n.ends\n.subckt a Y VDD VSS\n.ends\n"
    with pytest.raises(ValueError, match="Duplicate"):
        parse_spice(text)


def test_x_device_without_a_model_is_rejected():
    with pytest.raises(ValueError, match="names no subcircuit or model"):
        parse_spice(".subckt a Y VDD VSS\nX0 w=1u l=2u\n.ends\n")
