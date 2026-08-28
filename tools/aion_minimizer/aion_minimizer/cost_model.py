"""Inverter insertion and cost metrics.

This module decides which primary inputs need a complemented version, builds
those inverters, and computes the total cost of the merged megagate for the
selected optimization mode.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from aion_minimizer.pn_network import TransistorNetwork
from aion_minimizer.spice_parser import Subcircuit, SubcircuitInstance


@dataclass
class Inverter:
    """A single CMOS inverter to be inserted."""

    input: str
    output: str


@dataclass
class CostReport:
    """Cost breakdown for a merged megagate."""

    mode: str
    megagate_transistors: int
    inverter_count: int
    inverter_transistors: int
    output_inverter_transistors: int
    total_transistors: int
    original_transistors: int
    savings: int
    better: bool
    max_stack_depth: int
    inverters: List[Inverter] = field(default_factory=list)
    warning: Optional[str] = None


def _required_inverters(
    network: TransistorNetwork, primary_inputs: List[str]
) -> List[Inverter]:
    """Return the inverters needed for complemented primary inputs."""
    needed: set = set()
    for branch in network.p_branches + network.n_branches:
        for switch in branch:
            gate = switch.gate_signal
            if gate.endswith("_bar"):
                base = gate[:-4]
                if base in primary_inputs:
                    needed.add(base)

    return [Inverter(input=base, output=f"{base}_bar") for base in sorted(needed)]


def _original_transistor_count(
    instances: List[SubcircuitInstance], gate_subckts: Dict[str, Subcircuit]
) -> int:
    return sum(len(gate_subckts[inst.subckt_name].mosfets) for inst in instances)


def _max_stack_depth(network: TransistorNetwork) -> int:
    """Maximum series stack depth (NMOS stacks or PMOS series groups)."""
    n_depth = max((len(b) for b in network.n_branches), default=0)
    p_depth = len(network.p_branches)
    return max(n_depth, p_depth)


def compute_cost(
    network: TransistorNetwork,
    mode: str,
    primary_inputs: List[str],
    original_instances: List[SubcircuitInstance],
    gate_subckts: Dict[str, Subcircuit],
    balance_max_stack: int = 3,
    output_inverted: bool = False,
    quiet: bool = False,
) -> CostReport:
    """Compute the cost of the merged megagate and insert required inverters."""
    if mode not in ("transistor", "area", "balance"):
        raise ValueError(f"Unknown cost mode: {mode!r}")

    inverters = _required_inverters(network, primary_inputs)
    megagate_transistors = network.transistor_count
    inverter_transistors = 2 * len(inverters)
    output_inverter_transistors = 2 if output_inverted else 0
    total_transistors = megagate_transistors + inverter_transistors + output_inverter_transistors
    original_transistors = _original_transistor_count(original_instances, gate_subckts)
    savings = original_transistors - total_transistors
    better = savings > 0
    max_depth = _max_stack_depth(network)

    # Mode-specific cost metric.
    if mode == "transistor":
        mode_cost = total_transistors
    elif mode == "area":
        # Normalized width: PMOS ~= 2× NMOS; inverter ~= 1 PMOS + 1 NMOS.
        mode_cost = (
            2 * network.pmos_count
            + 1 * network.nmos_count
            + 3 * len(inverters)
        )
    else:  # balance
        excess = max(0, max_depth - balance_max_stack)
        mode_cost = total_transistors + 2 * excess

    warning = None
    if not better:
        warning = (
            f"Warning: megagate ({total_transistors} transistors) is not cheaper "
            f"than original std-cell chain ({original_transistors} transistors)."
        )
        if not quiet:
            print(warning, file=sys.stderr)

    return CostReport(
        mode=mode,
        megagate_transistors=megagate_transistors,
        inverter_count=len(inverters),
        inverter_transistors=inverter_transistors,
        output_inverter_transistors=output_inverter_transistors,
        total_transistors=total_transistors,
        original_transistors=original_transistors,
        savings=savings,
        better=better,
        max_stack_depth=max_depth,
        inverters=inverters,
        warning=warning,
    )
