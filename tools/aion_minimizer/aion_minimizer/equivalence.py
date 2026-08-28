"""Exhaustive truth-table equivalence checker.

The checker evaluates both the original gate-level netlist and the generated
transistor-level netlist on every input combination using the same ideal
switch-level model and reports the first mismatching vector.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from aion_minimizer.gate_extractor import _evaluate_gate
from aion_minimizer.netlist_evaluator import FlattenedNetlist
from aion_minimizer.spice_parser import Mosfet, Subcircuit, parse_spice


@dataclass
class EquivalenceResult:
    """Result of an equivalence check."""

    passed: bool
    mismatch_vector: Optional[Tuple[int, ...]] = None
    expected: Optional[int] = None
    got: Optional[int] = None


def _identify_terminals(subckt: Subcircuit) -> Tuple[str, List[str], str, str]:
    """Identify output, inputs, VDD and VSS in a generated subckt."""
    from aion_minimizer.gate_extractor import _identify_terminals as _gate_id

    return _gate_id(subckt)


def check_equivalence(
    flat: FlattenedNetlist,
    generated_spice: str,
    max_inputs: int = 6,
) -> EquivalenceResult:
    """Check that ``generated_spice`` implements ``flat.truth_table``."""
    if len(flat.primary_inputs) > max_inputs:
        raise ValueError(
            f"Too many inputs for exhaustive check: {len(flat.primary_inputs)} > {max_inputs}"
        )

    parsed = parse_spice(generated_spice)
    if len(parsed) != 1:
        raise ValueError(
            f"Generated SPICE must contain exactly one .subckt, found {len(parsed)}"
        )
    subckt = next(iter(parsed.values()))

    output, inputs, vdd, vss = _identify_terminals(subckt)
    if set(inputs) != set(flat.primary_inputs):
        raise ValueError(
            f"Generated SPICE inputs {inputs} do not match expected {flat.primary_inputs}"
        )
    if output != flat.primary_output:
        raise ValueError(
            f"Generated SPICE output {output!r} does not match expected {flat.primary_output!r}"
        )

    mosfets = subckt.mosfets
    if not mosfets:
        raise ValueError("Generated SPICE contains no MOSFETs")

    # Use the same switch-level evaluator as gate_extractor.
    for combo in itertools.product((0, 1), repeat=len(flat.primary_inputs)):
        input_values = dict(zip(flat.primary_inputs, combo))
        got = _evaluate_gate(mosfets, output, vdd, vss, input_values)
        expected = flat.truth_table[combo]
        if got != expected:
            return EquivalenceResult(
                passed=False,
                mismatch_vector=combo,
                expected=expected,
                got=got,
            )

    return EquivalenceResult(passed=True)
