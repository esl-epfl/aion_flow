"""Flatten and evaluate a gate-level netlist.

Given a top-level subckt that instantiates known gates, the evaluator:

1. Builds a DAG of gate instances.
2. Rejects sequential feedback / combinational loops, multiple outputs, and
   unknown gate cells.
3. Propagates values for every primary-input vector using the truth tables
   extracted from the gate library.
4. Returns the complete top-level truth table and a SymPy expression.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import networkx as nx
from sympy import SOPform, symbols

from aion_minimizer.gate_extractor import GateFunction
from aion_minimizer.spice_parser import Subcircuit, SubcircuitInstance


@dataclass
class FlattenedNetlist:
    """Result of flattening a gate-level netlist."""

    top_name: str
    primary_inputs: List[str]
    primary_output: str
    instance_order: List[str]
    truth_table: Dict[Tuple[int, ...], int] = field(default_factory=dict)
    expr: Optional[object] = None

    def eval(self, **values: int) -> int:
        """Evaluate the flattened function for a single input assignment."""
        key = tuple(values[name] for name in self.primary_inputs)
        return self.truth_table[key]


def _is_supply(name: str) -> bool:
    return name.upper() in ("VDD", "VSS")


def _instance_io(
    instance: SubcircuitInstance,
    gate_fn: GateFunction,
    gate_subckt: Subcircuit,
) -> Tuple[str, List[str]]:
    """Return (output_net, input_nets) for a gate instance.

    The instance pin order matches the gate-definition subckt pin order, so we
    map by terminal name.
    """
    output_net: Optional[str] = None
    input_nets: List[str] = []
    for terminal, net in zip(gate_subckt.pins, instance.pins):
        if terminal == gate_fn.output:
            output_net = net
        elif terminal in gate_fn.inputs:
            input_nets.append(net)
    if output_net is None:
        raise ValueError(
            f"Instance {instance.name!r} of {instance.subckt_name!r} "
            f"does not connect the gate output pin {gate_fn.output!r}"
        )
    return output_net, input_nets


def flatten_top(
    top: Subcircuit,
    gate_functions: Dict[str, GateFunction],
    gate_subckts: Dict[str, Subcircuit],
) -> FlattenedNetlist:
    """Flatten a top-level gate netlist into a Boolean function."""
    if top.is_gate_definition:
        raise ValueError(f"Subckt {top.name!r} looks like a gate definition, not a top-level netlist")

    instances = top.instances
    if not instances:
        raise ValueError(f"Top-level subckt {top.name!r} contains no gate instances")

    # Validate that every instance references a known gate.
    unknown = [i.subckt_name for i in instances if i.subckt_name not in gate_functions]
    if unknown:
        raise ValueError(
            f"Unknown gate cell(s) in {top.name!r}: {set(unknown)}. "
            f"Supported gates: {sorted(gate_functions)}"
        )

    # Determine each instance's output net and ordered input nets.
    instance_outputs: Dict[str, str] = {}
    instance_inputs: Dict[str, List[str]] = {}
    driven_by: Dict[str, List[str]] = {}

    for inst in instances:
        gate_fn = gate_functions[inst.subckt_name]
        gate_subckt = gate_subckts[inst.subckt_name]
        out_net, in_nets = _instance_io(inst, gate_fn, gate_subckt)
        instance_outputs[inst.name] = out_net
        instance_inputs[inst.name] = in_nets
        driven_by.setdefault(out_net, []).append(inst.name)

    # Build the instance dependency graph and detect loops before rejecting
    # multiple drivers, because a feedback loop often creates multiple drivers.
    graph = nx.DiGraph()
    for inst in instances:
        graph.add_node(inst.name)
    for inst in instances:
        for in_net in instance_inputs[inst.name]:
            for driver in driven_by.get(in_net, []):
                if driver != inst.name:
                    graph.add_edge(driver, inst.name)

    try:
        instance_order = list(nx.topological_sort(graph))
    except nx.NetworkXUnfeasible as exc:
        raise ValueError(
            f"Top-level netlist {top.name!r} contains a combinational loop"
        ) from exc

    # Now reject multiple drivers on any net.
    for net, drivers in driven_by.items():
        if len(drivers) > 1:
            raise ValueError(
                f"Net {net!r} is driven by multiple instances: {drivers!r}"
            )

    # Identify the primary output and primary inputs.
    supply_pins = [p for p in top.pins if _is_supply(p)]
    non_supply_pins = [p for p in top.pins if not _is_supply(p)]
    output_candidates = [p for p in non_supply_pins if p in driven_by]
    if len(output_candidates) != 1:
        raise ValueError(
            f"Top-level subckt {top.name!r} must have exactly one primary output; "
            f"found candidates {output_candidates}"
        )
    primary_output = output_candidates[0]
    primary_inputs = [p for p in top.pins if p not in supply_pins and p != primary_output]

    # Evaluate the netlist for every primary-input vector.
    truth_table: Dict[Tuple[int, ...], int] = {}
    minterms: List[Tuple[int, ...]] = []
    base_values = {pin: 1 if pin.upper() == "VDD" else 0 for pin in supply_pins}

    for combo in itertools.product((0, 1), repeat=len(primary_inputs)):
        net_values = dict(zip(primary_inputs, combo))
        net_values.update(base_values)

        for inst_name in instance_order:
            inst = next(i for i in instances if i.name == inst_name)
            gate_fn = gate_functions[inst.subckt_name]
            in_values = [net_values[n] for n in instance_inputs[inst_name]]
            out_value = gate_fn.eval(**dict(zip(gate_fn.inputs, in_values)))
            if out_value is None:
                raise ValueError(
                    f"Instance {inst_name!r} produced X for inputs {in_values}"
                )
            net_values[instance_outputs[inst_name]] = out_value

        top_value = net_values[primary_output]
        truth_table[combo] = top_value
        if top_value == 1:
            minterms.append(combo)

    # Build a SymPy expression from the 1-minterms.
    input_symbols = symbols(" ".join(primary_inputs))
    if not isinstance(input_symbols, (list, tuple)):
        input_symbols = (input_symbols,)
    expr = SOPform(input_symbols, minterms) if minterms else False

    return FlattenedNetlist(
        top_name=top.name,
        primary_inputs=primary_inputs,
        primary_output=primary_output,
        instance_order=instance_order,
        truth_table=truth_table,
        expr=expr,
    )
