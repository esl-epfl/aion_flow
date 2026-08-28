"""Stack/fanout-aware transistor sizing heuristic.

Defaults follow the SG13G2 assumptions:

* ``Wn = 0.74u``
* ``Wp = 1.48u``
* ``L = 0.13u``

Each transistor width is scaled by its series stack depth and by the fanout
of the signal that controls it.  In ``area`` mode the final width is capped at
a configurable multiple of the base width.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Tuple

from aion_minimizer.cost_model import Inverter
from aion_minimizer.pn_network import Literal, Switch, TransistorNetwork


_WIDTH_RE = re.compile(r"^([0-9]*\.?[0-9]+)\s*([a-zA-Z]+)$")


def _parse_width(value: str) -> Tuple[float, str]:
    match = _WIDTH_RE.match(value.strip())
    if not match:
        raise ValueError(f"Invalid width value: {value!r}")
    return float(match.group(1)), match.group(2)


def _format_width(value: float, unit: str) -> str:
    return f"{value:.3f}{unit}"


def _scale_width(base: str, depth: int, fanout: int, cap: float | None) -> str:
    num, unit = _parse_width(base)
    factor = 1 + math.log2(fanout + 1)
    scaled = num * depth * factor
    if cap is not None:
        scaled = min(scaled, cap)
    return _format_width(scaled, unit)


@dataclass
class SizedTransistor:
    """A transistor with assigned geometry."""

    type: str
    gate: str
    w: str
    l: str
    ng: int = 1
    m: int = 1


@dataclass
class SizedInverter:
    """A sized CMOS inverter."""

    input: str
    output: str
    pmos: SizedTransistor
    nmos: SizedTransistor


@dataclass
class SizedNetwork:
    """A transistor network with sizing information attached."""

    output: str
    p_branches: List[List[SizedTransistor]] = field(default_factory=list)
    n_branches: List[List[SizedTransistor]] = field(default_factory=list)
    inverters: List[SizedInverter] = field(default_factory=list)

    @property
    def transistor_count(self) -> int:
        return (
            sum(len(b) for b in self.p_branches)
            + sum(len(b) for b in self.n_branches)
            + 2 * len(self.inverters)
        )


def size_network(
    network: TransistorNetwork,
    inverters: List[Inverter],
    mode: str = "transistor",
    wn: str = "0.74u",
    wp: str = "1.48u",
    l: str = "0.13u",
    area_max_width_mult: float = 4.0,
) -> SizedNetwork:
    """Assign widths to every switch and required inverter."""
    if mode not in ("transistor", "area", "balance"):
        raise ValueError(f"Unknown sizing mode: {mode!r}")

    wn_num, wn_unit = _parse_width(wn)
    wp_num, wp_unit = _parse_width(wp)
    cap_n = area_max_width_mult * wn_num if mode == "area" else None
    cap_p = area_max_width_mult * wp_num if mode == "area" else None

    # Fanout of every gate signal inside the megagate.
    fanout: Counter = Counter()
    for branch in network.p_branches + network.n_branches:
        for switch in branch:
            fanout[switch.gate_signal] += 1

    # Inverter inputs also load the primary input signal.
    for inv in inverters:
        fanout[inv.input] += 1

    p_depth = len(network.p_branches)

    sized_p: List[List[SizedTransistor]] = []
    for group in network.p_branches:
        sized_group: List[SizedTransistor] = []
        for switch in group:
            w = _scale_width(wp, p_depth, fanout[switch.gate_signal], cap_p)
            sized_group.append(
                SizedTransistor(
                    type="p", gate=switch.gate_signal, w=w, l=l
                )
            )
        sized_p.append(sized_group)

    sized_n: List[List[SizedTransistor]] = []
    for stack in network.n_branches:
        depth = len(stack)
        sized_stack: List[SizedTransistor] = []
        for switch in stack:
            w = _scale_width(wn, depth, fanout[switch.gate_signal], cap_n)
            sized_stack.append(
                SizedTransistor(
                    type="n", gate=switch.gate_signal, w=w, l=l
                )
            )
        sized_n.append(sized_stack)

    sized_inv: List[SizedInverter] = []
    for inv in inverters:
        inv_fanout = fanout.get(inv.output, 1)
        sized_inv.append(
            SizedInverter(
                input=inv.input,
                output=inv.output,
                pmos=SizedTransistor(
                    type="p",
                    gate=inv.input,
                    w=_scale_width(wp, 1, inv_fanout, cap_p),
                    l=l,
                ),
                nmos=SizedTransistor(
                    type="n",
                    gate=inv.input,
                    w=_scale_width(wn, 1, inv_fanout, cap_n),
                    l=l,
                ),
            )
        )

    return SizedNetwork(
        output=network.output,
        p_branches=sized_p,
        n_branches=sized_n,
        inverters=sized_inv,
    )
