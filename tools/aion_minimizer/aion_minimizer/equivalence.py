"""Exhaustive truth-table equivalence checker.

The generated transistor netlist is simulated with the same ideal switch-level
model used to read the PDK cells, and compared against the truth tables the
flattener produced from the original gate netlist.

The interface comes from the flattened netlist rather than being re-derived
from the generated SPICE.  Re-deriving it would let a cell whose ports drifted
still pass, which is exactly the failure the check exists to catch.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from aion_minimizer.gate_extractor import _evaluate_gate
from aion_minimizer.netlist_evaluator import FlattenedNetlist
from aion_minimizer.spice_parser import parse_spice


@dataclass
class EquivalenceResult:
    """Result of an equivalence check."""

    passed: bool
    output: Optional[str] = None
    mismatch_vector: Optional[Tuple[int, ...]] = None
    expected: Optional[int] = None
    got: Optional[int] = None

    def describe(self) -> str:
        if self.passed:
            return "PASS"
        return (
            f"FAIL on {self.output} at vector {self.mismatch_vector} "
            f"(expected {self.expected}, got {self.got})"
        )


def check_equivalence(
    flat: FlattenedNetlist,
    generated_spice: str,
    max_inputs: int = 6,
    vdd: str = "VDD",
    vss: str = "VSS",
    ports: Optional[List[str]] = None,
    complement_ports: Optional[Dict[str, str]] = None,
) -> EquivalenceResult:
    """Check that ``generated_spice`` implements every output of ``flat``.

    ``complement_ports`` maps an externalized ``<pin>_bar`` port to the pin it
    complements.  Those ports are driven with the inverse of their source, which
    is exactly the obligation the caller takes on by leaving the inverter out of
    the cell — so the check fails if the cell needs anything more than that.
    """
    if len(flat.primary_inputs) > max_inputs:
        raise ValueError(
            f"Too many inputs for exhaustive check: "
            f"{len(flat.primary_inputs)} > {max_inputs}"
        )

    parsed = parse_spice(generated_spice)
    if len(parsed) != 1:
        raise ValueError(
            f"Generated SPICE must contain exactly one .subckt, found {len(parsed)}"
        )
    subckt = next(iter(parsed.values()))

    expected_ports = list(ports if ports is not None else flat.ports)
    if subckt.pins != expected_ports:
        raise ValueError(
            f"Generated SPICE ports {subckt.pins} do not match the original "
            f"{expected_ports}"
        )

    mosfets = subckt.mosfets
    if not mosfets:
        raise ValueError("Generated SPICE contains no MOSFETs")

    for combo in itertools.product((0, 1), repeat=len(flat.primary_inputs)):
        input_values: Dict[str, int] = dict(zip(flat.primary_inputs, combo))
        for port, source in (complement_ports or {}).items():
            input_values[port] = 1 - input_values[source]
        for output in flat.primary_outputs:
            got = _evaluate_gate(mosfets, output, vdd, vss, input_values)
            expected = flat.truth_tables[output][combo]
            if got != expected:
                return EquivalenceResult(
                    passed=False,
                    output=output,
                    mismatch_vector=combo,
                    expected=expected,
                    got=got,
                )

    return EquivalenceResult(passed=True)
