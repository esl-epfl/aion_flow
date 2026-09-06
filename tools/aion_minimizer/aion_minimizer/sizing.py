"""Assign transistor geometry to a P/N network.

The model follows what SG13G2 actually does rather than a textbook rule.  In
that PDK a device is described by a *total* width ``w`` split into ``ng``
fingers, and the finger width never changes: ``inv_1`` is ``740n``/``1.12u``
with ``ng=1``, ``inv_4`` is ``2.96u``/``4.48u`` with ``ng=4``, ``inv_16`` is
``11.84u``/``17.92u`` with ``ng=16`` — always ``740n`` and ``1.12u`` per
finger, because a wider finger does not fit the cell row.

Two consequences for this tool:

* Drive strength is expressed by *folding*, never by a bare width.  Emitting
  ``w=11.477u ng=1``, as the previous heuristic did, describes a device six
  times taller than the row it has to be laid out in.
* ``nand4_1`` and ``nor4_1`` use exactly the same widths as ``inv_1``, so the
  PDK does not compensate series stacks at x1 either.  Stack compensation is
  therefore opt-in (``stack_sizing``) rather than the default.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from aion_minimizer.cost_model import Inverter
from aion_minimizer.pn_network import TransistorNetwork

MODES = ("transistor", "area", "balance")

#: Widths of one finger in the SG13G2 x1 cells.
DEFAULT_WN = "0.74u"
DEFAULT_WP = "1.12u"
DEFAULT_L = "0.13u"

_WIDTH_RE = re.compile(r"^([0-9]*\.?[0-9]+)\s*([a-zA-Z]*)$")


def _parse_width(value: str) -> Tuple[float, str]:
    match = _WIDTH_RE.match(value.strip())
    if not match:
        raise ValueError(f"Invalid width value: {value!r}")
    return float(match.group(1)), match.group(2)


def _format_width(value: float, unit: str) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return f"{text}{unit}"


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
    #: Output-restoring inverter, present when the inverted polarity was built.
    #: Its ``input``/``output`` are placeholders; the renderer wires the nodes.
    output_inverter: Optional[SizedInverter] = None
    #: ``0``/``1`` when the function is constant, ``None`` otherwise.
    constant: Optional[int] = None

    @property
    def transistor_count(self) -> int:
        return (
            sum(len(b) for b in self.p_branches)
            + sum(len(b) for b in self.n_branches)
            + 2 * len(self.inverters)
            + (2 if self.output_inverter is not None else 0)
        )


@dataclass
class SizingRules:
    """Everything that decides one device's geometry."""

    wn: str = DEFAULT_WN
    wp: str = DEFAULT_WP
    l: str = DEFAULT_L
    #: Drive strength; ``2`` doubles every device and its finger count.
    drive: int = 1
    #: Widen a device by the depth of the series stack it sits in.
    stack_sizing: bool = False
    #: Upper bound on fingers per device, so a deep stack cannot run away.
    max_fingers: int = 16

    def __post_init__(self) -> None:
        if self.drive < 1:
            raise ValueError(f"drive must be at least 1, got {self.drive}")
        if self.max_fingers < 1:
            raise ValueError(f"max_fingers must be at least 1, got {self.max_fingers}")
        # Validate eagerly so a bad --wn surfaces before any device is built.
        _parse_width(self.wn)
        _parse_width(self.wp)

    def device(self, kind: str, gate: str, stack_depth: int = 1) -> SizedTransistor:
        """Return the geometry of one device controlled by ``gate``."""
        base = self.wp if kind == "p" else self.wn
        fingers = self.drive * (stack_depth if self.stack_sizing else 1)
        fingers = min(max(fingers, 1), self.max_fingers)
        if fingers == 1:
            width = base  # keep the caller's own spelling, e.g. "1.12u"
        else:
            num, unit = _parse_width(base)
            width = _format_width(num * fingers, unit)
        return SizedTransistor(type=kind, gate=gate, w=width, l=self.l, ng=fingers)


def size_network(network: TransistorNetwork, rules: SizingRules) -> SizedNetwork:
    """Assign geometry to every switch of ``network``."""
    if network.constant is not None:
        return SizedNetwork(output=network.output, constant=network.constant)

    # A pull-up made of parallel groups in series conducts through as many
    # devices as there are groups.
    p_depth = len(network.p_branches)
    sized_p = [
        [rules.device("p", switch.gate_signal, p_depth) for switch in group]
        for group in network.p_branches
    ]
    sized_n = [
        [rules.device("n", switch.gate_signal, len(stack)) for switch in stack]
        for stack in network.n_branches
    ]
    return SizedNetwork(output=network.output, p_branches=sized_p, n_branches=sized_n)


def size_inverter(inv: Inverter, rules: SizingRules) -> SizedInverter:
    """Size one CMOS inverter at the base drive."""
    return SizedInverter(
        input=inv.input,
        output=inv.output,
        pmos=rules.device("p", inv.input),
        nmos=rules.device("n", inv.input),
    )


def restoring_inverter(rules: SizingRules) -> SizedInverter:
    """Size the output inverter of an inverted-polarity stage.

    Node names are filled in by the renderer, which owns the internal node.
    """
    return SizedInverter(
        input="",
        output="",
        pmos=rules.device("p", ""),
        nmos=rules.device("n", ""),
    )
