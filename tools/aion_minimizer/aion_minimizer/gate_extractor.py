"""Extract truth tables from transistor-level gate definitions.

For a static complementary CMOS gate the module:

1. Identifies the output pin (the only pin connected to both an NMOS drain
   and a PMOS drain).
2. Identifies the input pins (remaining non-supply pins).
3. Enumerates all input combinations and performs an ideal switch-level
   simulation:

   * NMOS conducts when its gate is ``1``.
   * PMOS conducts when its gate is ``0``.
   * The output is ``1`` if connected only to VDD, ``0`` if connected only
     to VSS, and ``X`` (``None``) otherwise.
4. Returns the truth table and a SymPy Boolean expression.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sympy import SOPform, symbols

from aion_minimizer.spice_parser import Mosfet, Subcircuit


@dataclass
class GateFunction:
    """Boolean function extracted from a gate-definition subckt."""

    subckt_name: str
    inputs: List[str]
    output: str
    vdd: str
    vss: str
    truth_table: Dict[Tuple[int, ...], Optional[int]] = field(default_factory=dict)
    expr: Optional[object] = None

    def eval(self, **values: int) -> Optional[int]:
        """Evaluate the gate for a single input assignment."""
        key = tuple(values[name] for name in self.inputs)
        return self.truth_table[key]


def _identify_terminals(subckt: Subcircuit) -> Tuple[str, List[str], str, str]:
    """Return (output, inputs, vdd, vss) for a static CMOS gate subckt."""
    mosfets = subckt.mosfets
    if not mosfets:
        raise ValueError(f"Subckt {subckt.name!r} contains no MOSFETs")

    nmos_drains = {m.drain for m in mosfets if m.is_nmos}
    pmos_drains = {m.drain for m in mosfets if m.is_pmos}

    pin_set = set(subckt.pins)
    output_candidates = pin_set & nmos_drains & pmos_drains
    if len(output_candidates) != 1:
        raise ValueError(
            f"Cannot identify a unique output for {subckt.name!r}: "
            f"candidates={output_candidates}"
        )
    output = output_candidates.pop()

    # Prefer conventional names; fall back to a source/bulk heuristic.
    if "VDD" in pin_set and "VSS" in pin_set:
        vdd = "VDD"
        vss = "VSS"
    else:
        nmos_src_bulk = set()
        pmos_src_bulk = set()
        for m in mosfets:
            if m.is_nmos:
                nmos_src_bulk.update((m.source, m.bulk))
            else:
                pmos_src_bulk.update((m.source, m.bulk))

        non_io_pins = pin_set - {output}
        try:
            vdd = next(
                p
                for p in non_io_pins
                if p in pmos_src_bulk and p not in nmos_src_bulk
            )
        except StopIteration as exc:
            raise ValueError(f"Cannot identify VDD pin for {subckt.name!r}") from exc
        try:
            vss = next(
                p
                for p in non_io_pins
                if p in nmos_src_bulk and p not in pmos_src_bulk
            )
        except StopIteration as exc:
            raise ValueError(f"Cannot identify VSS pin for {subckt.name!r}") from exc

    # Inputs are the remaining pins in their original order.
    inputs = [p for p in subckt.pins if p not in (output, vdd, vss)]
    return output, inputs, vdd, vss


def _evaluate_gate(
    mosfets: List[Mosfet],
    output: str,
    vdd: str,
    vss: str,
    input_values: Dict[str, int],
) -> Optional[int]:
    """Return the output value for a single input vector using ideal switches.

    Internal nodes that gate transistors (e.g. in XOR or AND2 cells) are
    resolved iteratively, so the gate does not have to be a simple two-level
    network.
    """
    values: Dict[str, int] = {vdd: 1, vss: 0}
    values.update(input_values)

    # All nets that appear anywhere in the transistor list.
    all_nets: set = set()
    for m in mosfets:
        all_nets.update((m.drain, m.gate, m.source, m.bulk))
    all_nets.update((output, vdd, vss))

    def value_of_net(net: str) -> Optional[int]:
        # Build the connectivity graph for transistors that are currently on.
        graph: Dict[str, List[str]] = {}
        for m in mosfets:
            gate_val = values.get(m.gate)
            if gate_val is None:
                # Unknown gate -> transistor is off for now.
                continue
            on = (m.is_nmos and gate_val == 1) or (m.is_pmos and gate_val == 0)
            if on:
                a, b = m.drain, m.source
                graph.setdefault(a, []).append(b)
                graph.setdefault(b, []).append(a)

        # Search from the net of interest.
        visited: set = set()
        stack = [net]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            stack.extend(graph.get(node, ()))

        reaches_vdd = vdd in visited
        reaches_vss = vss in visited
        if reaches_vdd and not reaches_vss:
            return 1
        if reaches_vss and not reaches_vdd:
            return 0
        return None  # X / floating / contention

    # Iteratively resolve internal nodes until nothing more can be determined.
    changed = True
    while changed:
        changed = False
        for net in all_nets:
            if net in values:
                continue
            val = value_of_net(net)
            if val is not None:
                values[net] = val
                changed = True

    return value_of_net(output)


def extract_gate_functions(
    subckts: Dict[str, Subcircuit]
) -> Dict[str, GateFunction]:
    """Extract Boolean functions for all valid gate-definition subckts.

    Cells that do not look like single-output combinational gates (e.g.
    decoupling capacitors) are silently skipped.
    """
    functions: Dict[str, GateFunction] = {}
    for name, sub in subckts.items():
        if not sub.is_gate_definition:
            continue
        try:
            functions[name] = extract_gate_function(sub)
        except ValueError:
            # Not a recognizable combinational gate (no unique output, etc.).
            pass
    return functions


def extract_gate_function(subckt: Subcircuit) -> GateFunction:
    """Extract the Boolean function of a gate-definition subckt."""
    output, inputs, vdd, vss = _identify_terminals(subckt)
    mosfets = subckt.mosfets

    truth_table: Dict[Tuple[int, ...], Optional[int]] = {}
    minterms: List[Tuple[int, ...]] = []

    for combo in itertools.product((0, 1), repeat=len(inputs)):
        input_values = dict(zip(inputs, combo))
        value = _evaluate_gate(mosfets, output, vdd, vss, input_values)
        truth_table[combo] = value
        if value == 1:
            minterms.append(combo)
        elif value is None:
            raise ValueError(
                f"Subckt {subckt.name!r} produced X for input vector {combo}"
            )

    # Build a SymPy expression from the 1-minterms.
    input_symbols = symbols(" ".join(inputs))
    if not isinstance(input_symbols, (list, tuple)):
        input_symbols = (input_symbols,)

    if minterms:
        expr = SOPform(input_symbols, minterms)
    else:
        # All defined rows are 0 -> constant 0 function.
        expr = False

    return GateFunction(
        subckt_name=subckt.name,
        inputs=inputs,
        output=output,
        vdd=vdd,
        vss=vss,
        truth_table=truth_table,
        expr=expr,
    )
