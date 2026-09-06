"""Turn sized P/N networks into concrete MOSFET devices.

Everything the tool can emit — a merged complex gate, an inverter, a tie cell,
an inlined standard cell — ends up as a list of :class:`Mosfet`.  Rendering
into that one representation is what lets a multi-stage cell mix resynthesized
stages with untouched PDK cells inside a single ``.subckt``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import List, Set

from aion_minimizer.sizing import SizedInverter, SizedNetwork, SizedTransistor
from aion_minimizer.spice_parser import Mosfet

NMOS_MODEL = "sg13_lv_nmos"
PMOS_MODEL = "sg13_lv_pmos"


@dataclass
class DeviceNamer:
    """Hand out unique device names and unique internal node names."""

    reserved: Set[str] = field(default_factory=set)
    _n: int = 0
    _p: int = 0
    _node: int = 0

    def device(self, kind: str) -> str:
        if kind == "n":
            name = f"XN{self._n}"
            self._n += 1
        else:
            name = f"XP{self._p}"
            self._p += 1
        return name

    def node(self, hint: str) -> str:
        while True:
            name = f"{hint}_{self._node}"
            self._node += 1
            if name not in self.reserved:
                self.reserved.add(name)
                return name


def _mosfet(
    namer: DeviceNamer,
    t: SizedTransistor,
    drain: str,
    gate: str,
    source: str,
    bulk: str,
) -> Mosfet:
    return Mosfet(
        name=namer.device(t.type),
        drain=drain,
        gate=gate,
        source=source,
        bulk=bulk,
        model=PMOS_MODEL if t.type == "p" else NMOS_MODEL,
        params={"w": t.w, "l": t.l, "ng": str(t.ng), "m": str(t.m)},
    )


def render_inverter(
    inv: SizedInverter, namer: DeviceNamer, vdd: str = "VDD", vss: str = "VSS"
) -> List[Mosfet]:
    """Render one CMOS inverter driving ``inv.output`` from ``inv.input``."""
    pmos = replace(inv.pmos, gate=inv.input)
    nmos = replace(inv.nmos, gate=inv.input)
    return [
        _mosfet(namer, pmos, inv.output, inv.input, vdd, vdd),
        _mosfet(namer, nmos, inv.output, inv.input, vss, vss),
    ]


def render_network(
    sized: SizedNetwork,
    output_net: str,
    namer: DeviceNamer,
    output_inverted: bool = False,
    vdd: str = "VDD",
    vss: str = "VSS",
) -> List[Mosfet]:
    """Render one complementary stage driving ``output_net``.

    Input inverters are *not* rendered here: several stages usually want the
    same complemented signal, so the caller collects them and emits one
    inverter per net.
    """
    if sized.constant is not None:
        # Tying both gates to the same rail leaves exactly one device on.
        rail = vss if sized.constant == 1 else vdd
        pmos = SizedTransistor(type="p", gate=rail, w="1.480u", l="0.130u")
        nmos = SizedTransistor(type="n", gate=rail, w="0.740u", l="0.130u")
        return [
            _mosfet(namer, pmos, output_net, rail, vdd, vdd),
            _mosfet(namer, nmos, output_net, rail, vss, vss),
        ]

    devices: List[Mosfet] = []
    stage_out = namer.node("mega") if output_inverted else output_net

    # PMOS pull-up: parallel groups placed in series from VDD to the stage
    # output.  The output side is the drain so the node reads as an output.
    left = vdd
    last = len(sized.p_branches) - 1
    for index, group in enumerate(sized.p_branches):
        right = stage_out if index == last else namer.node("net_p")
        for transistor in group:
            devices.append(_mosfet(namer, transistor, right, transistor.gate, left, vdd))
        left = right

    # NMOS pull-down: series stacks placed in parallel from the output to VSS.
    for stack in sized.n_branches:
        top = stage_out
        for level, transistor in enumerate(stack):
            bottom = vss if level == len(stack) - 1 else namer.node("net_n")
            devices.append(_mosfet(namer, transistor, top, transistor.gate, bottom, vss))
            top = bottom

    if output_inverted:
        if sized.output_inverter is None:
            raise ValueError(
                "output_inverted was requested but the network carries no sized "
                "output inverter"
            )
        devices.extend(
            render_inverter(
                replace(sized.output_inverter, input=stage_out, output=output_net),
                namer,
                vdd,
                vss,
            )
        )
    return devices
