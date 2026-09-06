# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Inspect SPICE netlist topology
# ================================================================

"""Helpers that turn a parsed SPICE subckt into a human/AI-readable layout plan.

The functions here are intentionally simple: they produce *suggestions* that the
AI can use when writing a cell generator.  They do not perform full electrical
or topological analysis.
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from .spice_parser import Mosfet, Subckt


def pull_up_devices(subckt: Subckt) -> List[Mosfet]:
    """Return PMOS devices whose drain is connected to the output net."""
    out = subckt.output_net
    if out is None:
        return []
    return [d for d in subckt.pmos_devices if d.drain == out]


def pull_down_devices(subckt: Subckt) -> List[Mosfet]:
    """Return NMOS devices whose drain is connected to the output net."""
    out = subckt.output_net
    if out is None:
        return []
    return [d for d in subckt.nmos_devices if d.drain == out]


def devices_between(devices: List[Mosfet], net_a: str, net_b: str) -> List[Mosfet]:
    """Return devices whose source/drain terminals connect ``net_a`` and ``net_b``."""
    found: List[Mosfet] = []
    for d in devices:
        terminals = {d.drain, d.source}
        if net_a in terminals and net_b in terminals:
            found.append(d)
    return found


def series_chain(devices: List[Mosfet], head_net: str, rail_net: str) -> List[Mosfet]:
    """Order devices that form a simple series stack from ``head_net`` to ``rail_net``.

    The function walks from ``head_net`` through source/drain connections until
    ``rail_net`` is reached.  It only handles a single linear chain.
    """
    chain: List[Mosfet] = []
    current = head_net
    remaining = list(devices)

    while remaining and current != rail_net:
        for idx, d in enumerate(remaining):
            terminals = {d.drain, d.source}
            if current in terminals:
                chain.append(d)
                remaining.pop(idx)
                current = d.drain if d.source == current else d.source
                break
        else:
            # No further device found in the chain.
            break

    return chain


def is_series_pair(d1: Mosfet, d2: Mosfet) -> bool:
    """Return True if two devices share exactly one source/drain node (series)."""
    shared = {d1.drain, d1.source} & {d2.drain, d2.source}
    return len(shared) == 1


def is_parallel_pair(d1: Mosfet, d2: Mosfet) -> bool:
    """Return True if two devices share both drain and source nodes (parallel)."""
    return {d1.drain, d1.source} == {d2.drain, d2.source}


def series_parallel_groups(
    devices: List[Mosfet],
    head_net: str,
    rail_net: str,
) -> List[List[Mosfet]]:
    """Group devices into series chains or parallel pairs between two nets.

    For a simple complementary gate the result is either one chain (series) or
    one group containing all devices (parallel).
    """
    if not devices:
        return []

    # If every device connects head and rail directly, they are all in parallel.
    if all(
        {d.drain, d.source} == {head_net, rail_net} for d in devices
    ):
        return [list(devices)]

    # Otherwise try to walk a single series chain.
    chain = series_chain(devices, head_net, rail_net)
    if chain and len(chain) == len(devices):
        return [chain]

    # Fallback: each device is its own group.
    return [[d] for d in devices]


def suggest_gate_order(subckt: Subckt) -> List[str]:
    """Suggest a left-to-right ordering of poly gates.

    The heuristic prefers:
    1. Alphabetical order of input names.
    2. Inputs that drive a series stack are kept adjacent when possible.
    """
    inputs = list(subckt.input_nets)

    # Try to detect series NMOS inputs and keep them in stack order.
    nmos = subckt.nmos_devices
    out = subckt.output_net
    vss = subckt.vss_net
    if out is not None and vss is not None:
        chain = series_chain(nmos, out, vss)
        if chain and len(chain) == len(nmos):
            ordered = [d.gate for d in chain]
            # Append any missing inputs (e.g. PMOS-only branches) at the end.
            ordered += [inp for inp in inputs if inp not in ordered]
            return ordered

    return sorted(inputs)


def netlist_summary(subckt: Subckt) -> str:
    """Return a short human-readable summary of the subckt."""
    lines = [
        f"Subckt: {subckt.name}",
        f"Pins:   {' '.join(subckt.pins)}",
        f"Output: {subckt.output_net}",
        f"Inputs: {' '.join(subckt.input_nets)}",
        f"NMOS:   {len(subckt.nmos_devices)} devices",
        f"PMOS:   {len(subckt.pmos_devices)} devices",
        "",
        "Suggested gate order: " + " ".join(suggest_gate_order(subckt)),
    ]
    return "\n".join(lines)


__all__ = [
    "pull_up_devices",
    "pull_down_devices",
    "devices_between",
    "series_chain",
    "is_series_pair",
    "is_parallel_pair",
    "series_parallel_groups",
    "suggest_gate_order",
    "netlist_summary",
]
