"""Lightweight internal circuit model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class TopPort:
    """A top-level port declaration."""

    name: str
    direction: str  # "input", "output", or "inout"
    bits: list[int | str]

    @property
    def width(self) -> int:
        return len(self.bits)


@dataclass
class Instance:
    """A standard-cell or black-box instance."""

    name: str
    cell_type: str
    parameters: dict[str, str] = field(default_factory=dict)
    connections: dict[str, list[int | str]] = field(default_factory=dict)
    attributes: dict[str, str] = field(default_factory=dict)

    def output_pins(self, pin_dirs: dict[str, str] | None = None) -> list[str]:
        """Return pins that drive output signals."""
        if pin_dirs is None:
            return [pin for pin, bits in self.connections.items() if bits]
        return [
            pin
            for pin, bits in self.connections.items()
            if bits and pin_dirs.get(pin) == "output"
        ]

    def input_pins(self, pin_dirs: dict[str, str] | None = None) -> list[str]:
        """Return pins that receive input signals."""
        if pin_dirs is None:
            return [pin for pin, bits in self.connections.items() if bits]
        return [
            pin
            for pin, bits in self.connections.items()
            if bits and pin_dirs.get(pin) == "input"
        ]


@dataclass
class Net:
    """A net connecting one or more instance pins and/or a top port."""

    name: str
    bits: list[int | str]
    drivers: list[tuple[str, str]] = field(default_factory=list)
    loads: list[tuple[str, str]] = field(default_factory=list)
    top_port: tuple[str, str] | None = None  # (port_name, direction)

    def is_constant(self) -> bool:
        """True if every bit of the net is a constant value."""
        return all(isinstance(b, str) for b in self.bits)


@dataclass
class Circuit:
    """An entire (top) module as a bipartite graph of instances and nets."""

    name: str
    ports: list[TopPort] = field(default_factory=list)
    instances: dict[str, Instance] = field(default_factory=dict)
    nets: dict[str, Net] = field(default_factory=dict)
    attributes: dict[str, str] = field(default_factory=dict)

    def net_for_bit(self, bit: int | str) -> Net | None:
        """Return the unique net that carries a given bit, if any."""
        for net in self.nets.values():
            if bit in net.bits:
                return net
        return None

    def fanin(self, instance_name: str) -> list[Instance]:
        """Return instances that drive inputs of the named instance."""
        inst = self.instances[instance_name]
        seen: set[str] = set()
        result: list[Instance] = []
        for bits in inst.connections.values():
            for bit in bits:
                if isinstance(bit, int):
                    net = self.net_for_bit(bit)
                    if net:
                        for driver_inst, _ in net.drivers:
                            if driver_inst not in seen:
                                seen.add(driver_inst)
                                result.append(self.instances[driver_inst])
        return result

    def fanout(self, instance_name: str) -> list[Instance]:
        """Return instances driven by outputs of the named instance."""
        inst = self.instances[instance_name]
        seen: set[str] = set()
        result: list[Instance] = []
        for pin, bits in inst.connections.items():
            for bit in bits:
                if isinstance(bit, int):
                    net = self.net_for_bit(bit)
                    if net:
                        for load_inst, _ in net.loads:
                            if load_inst != instance_name and load_inst not in seen:
                                seen.add(load_inst)
                                result.append(self.instances[load_inst])
        return result

    def neighbors(self, instance_name: str) -> list[Instance]:
        """All combinational instances connected by a shared net."""
        seen = {instance_name}
        result: list[Instance] = []
        inst = self.instances[instance_name]
        for bits in inst.connections.values():
            for bit in bits:
                if isinstance(bit, int):
                    net = self.net_for_bit(bit)
                    if net:
                        for other, _ in net.drivers + net.loads:
                            if other not in seen:
                                seen.add(other)
                                result.append(self.instances[other])
        return result

    def combinational_instances(
        self, is_combinational: Iterable[str]
    ) -> list[Instance]:
        """Return instances whose cell type is in the combinational set."""
        combo = set(is_combinational)
        return [i for i in self.instances.values() if i.cell_type in combo]
