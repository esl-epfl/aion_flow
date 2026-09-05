"""Pulling the inverter for a complemented input out of the cell."""

from __future__ import annotations

import pytest

from aion_minimizer.equivalence import check_equivalence
from netlists import CORPUS

# I1 reaches a NAND2 through an inverter, so the merged cell wants ~I1.
NEEDS_COMPLEMENT = CORPUS["inv_nand2_nor2"][0]


def verify(result):
    return check_equivalence(
        result.flat,
        result.spice,
        max_inputs=8,
        ports=result.ports,
        complement_ports=result.complement_ports,
    )


def test_internal_is_the_default(synth):
    result = synth(NEEDS_COMPLEMENT)
    assert result.internal_complements == ["I1"]
    assert result.external_complements == []
    assert result.ports == result.flat.ports
    assert verify(result).passed


def test_external_drops_the_inverter_and_adds_a_port(synth):
    """Two devices leave the cell; the caller owes it the complement."""
    internal = synth(NEEDS_COMPLEMENT)
    external = synth(NEEDS_COMPLEMENT, inverted_inputs="external")

    assert external.external_complements == ["I1"]
    assert external.transistors == internal.transistors - 2
    assert external.complement_ports == {"I1_bar": "I1"}
    assert verify(external).passed


def test_supplies_stay_last_in_the_port_list(synth):
    """SG13G2 cells end with VDD VSS; the extra port goes before them."""
    result = synth(NEEDS_COMPLEMENT, inverted_inputs="external")
    assert result.ports == ["I0", "I1", "I2", "O0", "I1_bar", "VDD", "VSS"]
    assert result.spice.splitlines()[0].split()[2:] == result.ports


def test_auto_externalizes_only_the_named_pins(synth):
    result = synth(
        NEEDS_COMPLEMENT, inverted_inputs="auto", external_inputs=["I1"]
    )
    assert result.external_complements == ["I1"]
    assert verify(result).passed


def test_auto_without_a_list_keeps_everything_inside(synth):
    result = synth(NEEDS_COMPLEMENT, inverted_inputs="auto")
    assert result.external_complements == []
    assert result.internal_complements == ["I1"]


def test_naming_a_pin_that_needs_no_complement_is_a_no_op(synth):
    """The decision is made per pattern upstream, not per synthesized variant."""
    result = synth(
        NEEDS_COMPLEMENT, inverted_inputs="auto", external_inputs=["I0", "I1"]
    )
    assert result.external_complements == ["I1"]


def test_naming_an_unknown_pin_is_an_error(synth):
    with pytest.raises(ValueError, match="not primary inputs"):
        synth(NEEDS_COMPLEMENT, inverted_inputs="auto", external_inputs=["nope"])


def test_unknown_mode_is_an_error(synth):
    with pytest.raises(ValueError, match="Unknown inverted-input mode"):
        synth(NEEDS_COMPLEMENT, inverted_inputs="sideways")


def test_a_cell_with_no_complemented_inputs_is_unchanged(synth):
    """`external` must not alter cells that never needed an inverter."""
    plain = synth(CORPUS["aoi_tree"][0])
    forced = synth(CORPUS["aoi_tree"][0], inverted_inputs="external")
    assert plain.spice == forced.spice
    assert forced.ports == plain.flat.ports


def test_internal_net_complements_are_never_externalized(synth):
    """A complemented internal net has no port to hang off."""
    result = synth(CORPUS["reconvergent_blob"][0], inverted_inputs="external")
    assert set(result.net_complements) & set(result.flat.primary_inputs) == set()
    for net in result.net_complements:
        assert net + "_bar" not in result.ports
    assert verify(result).passed


def test_report_describes_the_interface(synth):
    report = synth(NEEDS_COMPLEMENT, inverted_inputs="external").externalization_report()
    assert report["cell"] == "T"
    assert report["complement_ports"] == {"I1_bar": "I1"}
    assert report["complemented_inputs"]["external"] == ["I1"]
    assert report["devices_saved_per_externalized_input"] == 2
