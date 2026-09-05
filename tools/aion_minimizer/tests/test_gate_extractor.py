"""Reading Boolean functions out of the PDK transistor netlists."""

from __future__ import annotations

import itertools

import pytest

from aion_minimizer.gate_extractor import extract_gate_functions

EXPECTED = {
    "sg13g2_inv_1": lambda a: not a,
    "sg13g2_nand2_1": lambda a, b: not (a and b),
    "sg13g2_nor2_1": lambda a, b: not (a or b),
    "sg13g2_and2_1": lambda a, b: a and b,
    "sg13g2_or2_1": lambda a, b: a or b,
    "sg13g2_xor2_1": lambda a, b: a ^ b,
    "sg13g2_xnor2_1": lambda a, b: not (a ^ b),
    "sg13g2_mux2_1": None,  # checked separately: pin order is not obvious
}


@pytest.mark.parametrize("cell", [c for c, fn in EXPECTED.items() if fn])
def test_pdk_cells_extract_to_the_expected_function(cell, gate_functions):
    fn = gate_functions[cell]
    expected = EXPECTED[cell]
    for combo in itertools.product((0, 1), repeat=len(fn.inputs)):
        assert fn.truth_table[combo] == int(expected(*combo)), (cell, combo)


def test_the_xor_cell_is_a_two_stage_static_gate(gate_functions, gate_subckts):
    """Ten devices, not the twelve a single complementary stage would need."""
    assert len(gate_subckts["sg13g2_xor2_1"].mosfets) == 10
    assert set(gate_functions["sg13g2_xor2_1"].inputs) == {"A", "B"}


def test_sequential_and_physical_cells_are_skipped_with_a_reason(gate_subckts):
    skipped = {}
    functions = extract_gate_functions(gate_subckts, skipped)
    assert "sg13g2_dfrbp_1" not in functions
    assert "sg13g2_dfrbp_1" in skipped and skipped["sg13g2_dfrbp_1"]
    assert "sg13g2_fill_1" in skipped


def test_combinational_cells_are_all_recognised(gate_functions):
    for cell in ("sg13g2_a21o_1", "sg13g2_a21oi_1", "sg13g2_nand4_1", "sg13g2_o21ai_1"):
        assert cell in gate_functions
