"""Expand standard-cell instances into their PDK transistors, unchanged.

Any cluster the decomposer cannot beat is emitted this way, which is what makes
the tool's output never worse than its input: the PDK's own devices and its own
characterised widths come through untouched.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Sequence

from aion_minimizer.render import DeviceNamer
from aion_minimizer.spice_parser import Mosfet, Subcircuit, SubcircuitInstance


def inline_instances(
    instances: Sequence[SubcircuitInstance],
    gate_subckts: Dict[str, Subcircuit],
    namer: DeviceNamer,
) -> List[Mosfet]:
    """Return the transistors of ``instances`` with every cell expanded.

    Nets internal to a cell are renamed ``<instance>_<net>`` so that two
    instances of the same cell cannot collide.  Pins are mapped positionally,
    which is how SPICE binds subcircuit terminals.
    """
    devices: List[Mosfet] = []
    for inst in instances:
        gate = gate_subckts.get(inst.subckt_name)
        if gate is None:
            raise ValueError(f"Unknown gate cell {inst.subckt_name!r}")
        if len(gate.pins) != len(inst.pins):
            raise ValueError(
                f"Instance {inst.name!r} connects {len(inst.pins)} nodes but "
                f"{inst.subckt_name!r} declares {len(gate.pins)} pins"
            )
        net_map = dict(zip(gate.pins, inst.pins))

        def resolve(net: str, _map=net_map, _inst=inst.name) -> str:
            return _map.get(net) or f"{_inst}_{net}"

        for mos in gate.mosfets:
            devices.append(
                replace(
                    mos,
                    name=namer.device("n" if mos.is_nmos else "p"),
                    drain=resolve(mos.drain),
                    gate=resolve(mos.gate),
                    source=resolve(mos.source),
                    bulk=resolve(mos.bulk),
                )
            )
    return devices
