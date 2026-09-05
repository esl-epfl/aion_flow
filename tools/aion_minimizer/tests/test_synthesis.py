"""End-to-end properties that must hold for every input netlist."""

from __future__ import annotations

import pytest

from aion_minimizer.equivalence import check_equivalence
from aion_minimizer.sizing import SizingRules
from netlists import CORPUS

CASES = sorted(CORPUS)


@pytest.mark.parametrize("name", CASES)
def test_result_is_logically_equivalent(name, synth):
    text, _ = CORPUS[name]
    result = synth(text)
    check = check_equivalence(result.flat, result.spice, max_inputs=8)
    assert check.passed, check.describe()


@pytest.mark.parametrize("name", CASES)
def test_result_is_never_worse_than_the_original(name, synth):
    """The guardrail: a cluster keeps its PDK cell rather than losing to it.

    Before the decomposer existed, a 4-input XOR tree came out at 72 devices
    against 30 in the original cells, and the tool emitted it anyway.
    """
    text, original = CORPUS[name]
    result = synth(text)
    assert result.original_transistors == original
    assert result.transistors <= original, (
        f"{name}: {result.transistors} devices against {original} original"
    )


@pytest.mark.parametrize("name", CASES)
def test_stack_depth_stays_within_budget(name, synth):
    result = synth(text=CORPUS[name][0], max_stack_depth=4)
    assert result.max_stack_depth <= 4


@pytest.mark.parametrize("name", CASES)
def test_ports_are_preserved_verbatim(name, synth):
    """SPICE binds terminals positionally, so the pin order must not move."""
    text, _ = CORPUS[name]
    result = synth(text)
    header = result.spice.splitlines()[0].split()
    assert header[0] == ".subckt"
    assert header[2:] == result.flat.ports


@pytest.mark.parametrize("name", CASES)
def test_output_is_deterministic(name, synth):
    text, _ = CORPUS[name]
    assert synth(text).spice == synth(text).spice


def test_xor_tree_keeps_its_cells(synth):
    result = synth(CORPUS["xor4"][0])
    assert result.merged_stages == 0
    assert result.kept_cells == 3


def test_and3_becomes_nand3_plus_inverter(synth):
    """Costing the two polarities correctly is worth four devices here.

    The pull-up is driven by the complement of each POS literal, so a *plain*
    literal is what needs an inverter.  Getting that backwards made the tool
    build three input inverters plus an inverted-input NAND3.
    """
    result = synth(CORPUS["and3"][0])
    assert result.transistors == 8
    assert len(result.inverters) == 0


def test_or3_becomes_nor3_plus_inverter(synth):
    result = synth(CORPUS["or3"][0])
    assert result.transistors == 8
    assert len(result.inverters) == 0


def test_reconvergent_merge_is_found(synth):
    """A net with two consumers can still be merged when both are absorbed."""
    result = synth(CORPUS["reconvergent_blob"][0])
    assert result.transistors == 20
    assert result.merged_stages == 1


def test_constant_output_collapses_and_prunes_its_fanin(synth):
    """Folding to a constant makes everything upstream dead."""
    result = synth(CORPUS["reconvergent_constant"][0])
    assert result.transistors == 2
    assert len(result.stages) == 1


def test_single_stage_mode_still_flattens_everything(synth):
    """``--single-stage`` reproduces the unconditional merge, blow-up included."""
    merged = synth(CORPUS["xor3"][0], single_stage=True)
    assert len(merged.stages) == 1
    assert merged.transistors > merged.original_transistors


def test_no_inline_forces_resynthesis(synth):
    result = synth(CORPUS["xor2"][0], allow_inline=False)
    assert result.merged_stages == 1
    assert result.kept_cells == 0


def test_drive_strength_folds_like_the_pdk(synth):
    """``inv_4`` is ``2.96u``/``4.48u`` at ``ng=4``; a drive-4 cell must match."""
    result = synth(CORPUS["and3"][0], rules=SizingRules(drive=4))
    for device in result.devices:
        assert device.params["ng"] == "4"
        assert device.params["w"] in ("2.96u", "4.48u")


def test_multi_output_cells_are_supported(synth):
    result = synth(CORPUS["multi_output"][0])
    assert result.flat.primary_outputs == ["O0", "O1", "O2"]
    check = check_equivalence(result.flat, result.spice, max_inputs=8)
    assert check.passed, check.describe()
