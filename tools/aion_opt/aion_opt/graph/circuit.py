"""Lightweight internal circuit model.

A :class:`Circuit` is a bipartite graph of :class:`Instance` objects (standard
cells) and :class:`Net` objects (signals).  Bits are the Yosys signal
identifiers: integers for real signals, strings (``"0"``, ``"1"``, ``"x"``,
``"z"``) for constants.
"""

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

    # Lazily built ``bit -> Net`` index.  ``_bit_index_size`` records the number
    # of nets the index was built from so that additions/removals invalidate it
    # automatically.  Excluded from equality/repr to keep the model comparable.
    _bit_index: dict[int | str, Net] = field(
        default_factory=dict, repr=False, compare=False
    )
    _bit_index_size: int = field(default=-1, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Bit index
    # ------------------------------------------------------------------
    def rebuild_bit_index(self) -> None:
        """(Re)build the ``bit -> Net`` lookup table.

        The first net that carries a bit wins, matching the historical linear
        scan over ``self.nets`` in insertion order.
        """
        index: dict[int | str, Net] = {}
        for net in self.nets.values():
            for bit in net.bits:
                if bit not in index:
                    index[bit] = net
        self._bit_index = index
        self._bit_index_size = len(self.nets)

    def register_net(self, net: Net) -> None:
        """Add a net and keep the bit index consistent.

        Cheaper than adding to :attr:`nets` directly, which invalidates the
        whole index and forces a full rebuild on the next lookup.
        """
        self.nets[net.name] = net
        if self._bit_index_size >= 0:
            self._bit_index_size = len(self.nets)
            for bit in net.bits:
                self._bit_index.setdefault(bit, net)

    def invalidate_bit_index(self) -> None:
        """Force the next :meth:`net_for_bit` call to rebuild the index."""
        self._bit_index_size = -1
        self._bit_index = {}

    def net_for_bit(self, bit: int | str) -> Net | None:
        """Return the unique net that carries a given bit, if any.

        Backed by a lazily built index, so this is O(1) instead of a linear
        scan over every net.
        """
        if self._bit_index_size != len(self.nets):
            self.rebuild_bit_index()
        return self._bit_index.get(bit)

    # ------------------------------------------------------------------
    # Local connectivity helpers
    # ------------------------------------------------------------------
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
                            if driver_inst not in seen and driver_inst in self.instances:
                                seen.add(driver_inst)
                                result.append(self.instances[driver_inst])
        return result

    def fanout(self, instance_name: str) -> list[Instance]:
        """Return instances driven by outputs of the named instance."""
        inst = self.instances[instance_name]
        seen: set[str] = set()
        result: list[Instance] = []
        for bits in inst.connections.values():
            for bit in bits:
                if isinstance(bit, int):
                    net = self.net_for_bit(bit)
                    if net:
                        for load_inst, _ in net.loads:
                            if (
                                load_inst != instance_name
                                and load_inst not in seen
                                and load_inst in self.instances
                            ):
                                seen.add(load_inst)
                                result.append(self.instances[load_inst])
        return result

    def neighbors(self, instance_name: str) -> list[Instance]:
        """All instances connected to ``instance_name`` by a shared net."""
        seen = {instance_name}
        result: list[Instance] = []
        inst = self.instances[instance_name]
        for bits in inst.connections.values():
            for bit in bits:
                if isinstance(bit, int):
                    net = self.net_for_bit(bit)
                    if net:
                        for other, _ in net.drivers + net.loads:
                            if other not in seen and other in self.instances:
                                seen.add(other)
                                result.append(self.instances[other])
        return result

    def combinational_instances(
        self, is_combinational: Iterable[str]
    ) -> list[Instance]:
        """Return instances whose cell type is in the combinational set."""
        combo = set(is_combinational)
        return [i for i in self.instances.values() if i.cell_type in combo]
