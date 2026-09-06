"""Rewrite a circuit by replacing pattern occurrences with AION cells."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from aion_opt.cellgen.generator import (
    COMPLEMENT_SUFFIX,
    CellGenerator,
    DEFAULT_CELL_PREFIX,
    OUTPUT_PORT_PREFIX,
)
from aion_opt.graph.circuit import Circuit, Instance, Net
from aion_opt.io.cell_lib import CellLib
from aion_opt.io.complements import default_inverter, find_complement_bit, inverter_pins

if TYPE_CHECKING:
    from aion_opt.pattern.subgraph import Pattern


def _instance_prefix(cell_prefix: str) -> str:
    """Instance-name prefix derived from the module-name prefix.

    ``AION_`` -> ``_AION_``; the leading underscore keeps generated instance
    names from colliding with anything a synthesiser emits.
    """
    return f"_{cell_prefix.rstrip('_')}_"


def rewrite_circuit(
    circuit: Circuit,
    selected: list["Pattern"],
    module_names: dict[str, str],
    flatten: bool = False,
    cell_prefix: str = DEFAULT_CELL_PREFIX,
    complement_ports: dict[str, list[str]] | None = None,
    cell_lib: CellLib | None = None,
) -> Circuit:
    """Return a new circuit with the selected pattern occurrences replaced.

    Parameters
    ----------
    circuit:
        The netlist to rewrite; left untouched.
    selected:
        Non-overlapping occurrences to substitute.
    module_names:
        ``canonical key -> AION module name``, from the cell library.
    flatten:
        Inline the original PDK instances instead of instantiating the
        hierarchical AION cells.  Useful for tools that cannot reason through
        custom modules (e.g. some sequential equivalence checkers).
    cell_prefix:
        Module-name prefix of the AION cells; also determines the generated
        instance names.
    complement_ports:
        ``module name -> input ports whose complement the cell expects on a
        ``<port>_bar`` port``.  Each is wired to a complement the netlist
        already carries, or to an inverter inserted here.
    cell_lib:
        Technology dictionary; required only when ``complement_ports`` is given,
        to recognise existing inverters and to pick one to instantiate.

    The flat rewrite inlines the original PDK cells, so it never instantiates an
    AION module and needs no complements.
    """
    if flatten:
        return _rewrite_circuit_flat(circuit, selected, cell_prefix)
    return _rewrite_circuit_hierarchical(
        circuit, selected, module_names, cell_prefix, complement_ports, cell_lib
    )


def _rewrite_circuit_hierarchical(
    circuit: Circuit,
    selected: list["Pattern"],
    module_names: dict[str, str],
    cell_prefix: str,
    complement_ports: dict[str, list[str]] | None = None,
    cell_lib: CellLib | None = None,
) -> Circuit:
    """Replace occurrences with hierarchical AION instances."""
    new_circuit = deepcopy(circuit)
    new_circuit.invalidate_bit_index()
    prefix = _instance_prefix(cell_prefix)

    complement_ports = complement_ports or {}
    if complement_ports and cell_lib is None:
        raise ValueError("complement_ports requires cell_lib")

    # Which instances disappear has to be known before any complement is
    # resolved: an inverter that is itself absorbed into an AION cell stops
    # driving its output net, so its complement cannot be reused.
    instances_to_remove: set[str] = set()
    for occ in selected:
        instances_to_remove |= occ.instances

    complements = _ComplementBuilder(
        circuit, cell_lib, prefix, instances_to_remove
    )
    new_instances: list[Instance] = []

    for idx, occ in enumerate(selected):
        module_name = module_names[occ.canonical_key]
        input_port_map, output_port_map = CellGenerator.port_map_for_pattern(occ)

        # Connect each AION port to the exact bit the original pin used, so
        # multi-bit ports still resolve to the correct scalar slice.
        connections: dict[str, list[int | str]] = {}
        for (_, inst, pin), port_name in input_port_map.items():
            connections[port_name] = [circuit.instances[inst].connections[pin][0]]
        for (_, inst, pin), port_name in output_port_map.items():
            connections[port_name] = [circuit.instances[inst].connections[pin][0]]

        for port in complement_ports.get(module_name, ()):
            if port not in connections:
                raise ValueError(
                    f"Module {module_name!r} expects a complement of {port!r}, "
                    f"but that port is not on the pattern"
                )
            connections[port + COMPLEMENT_SUFFIX] = [
                complements.bit_for(connections[port][0])
            ]

        new_instances.append(
            Instance(
                name=f"{prefix}{idx}_",
                cell_type=module_name,
                connections=connections,
            )
        )

    for name in instances_to_remove:
        del new_circuit.instances[name]

    for inst in [*complements.instances, *new_instances]:
        new_circuit.instances[inst.name] = inst
    for net in complements.nets:
        new_circuit.register_net(net)

    _rebuild_net_links(new_circuit)
    _remove_disconnected_nets(new_circuit)
    return new_circuit


class _ComplementBuilder:
    """Supply the complement of a bit, reusing the netlist's own where possible.

    Reuse is the point of the whole exercise: post-synthesis netlists carry a
    lot of already-inverted signals, and every one that can be reused makes the
    cell two devices cheaper for free.
    """

    def __init__(
        self,
        circuit: Circuit,
        cell_lib: CellLib | None,
        prefix: str,
        absorbed: set[str],
    ) -> None:
        self.circuit = circuit
        self.cell_lib = cell_lib
        self.prefix = prefix
        self.absorbed = absorbed
        self.instances: list[Instance] = []
        self.nets: list[Net] = []
        self._cache: dict[int | str, int | str] = {}
        # Fresh signals get negative bit ids so they cannot clash with the ones
        # Yosys assigned, matching what the flat rewrite does.
        self._next_bit = -1
        self._inverter: str | None = None

    def bit_for(self, bit: int | str) -> int | str:
        if bit in self._cache:
            return self._cache[bit]
        assert self.cell_lib is not None
        existing = find_complement_bit(
            self.circuit, self.cell_lib, bit, self.absorbed
        )
        result = existing if existing is not None else self._insert_inverter(bit)
        self._cache[bit] = result
        return result

    def _insert_inverter(self, bit: int | str) -> int:
        assert self.cell_lib is not None
        if self._inverter is None:
            self._inverter = default_inverter(self.cell_lib)
        input_pin, output_pin = inverter_pins(self.cell_lib, self._inverter)

        output_bit = self._next_bit
        self._next_bit -= 1
        name = f"{self.prefix}inv{len(self.instances)}_"
        self.instances.append(
            Instance(
                name=name,
                cell_type=self._inverter,
                connections={input_pin: [bit], output_pin: [output_bit]},
                # Without this the pin names would be classified by the AION
                # ``I``/``O`` convention, and the inverter output would be
                # registered as a load rather than a driver.
                attributes={"port_directions": self.cell_lib.pins(self._inverter)},
            )
        )
        self.nets.append(Net(name=f"{name}{COMPLEMENT_SUFFIX}", bits=[output_bit]))
        return output_bit


def _rewrite_circuit_flat(
    circuit: Circuit,
    selected: list["Pattern"],
    cell_prefix: str,
) -> Circuit:
    """Replace occurrences by inlining the original PDK cells.

    Produces a flat netlist containing only original standard cells, renamed so
    that it mirrors the hierarchical result one-to-one.
    """
    new_circuit = deepcopy(circuit)
    new_circuit.invalidate_bit_index()
    prefix = _instance_prefix(cell_prefix)

    net_to_bit: dict[str, int | str] = {
        name: net.bits[0] for name, net in circuit.nets.items() if len(net.bits) == 1
    }

    instances_to_remove: set[str] = set()
    new_instances: list[Instance] = []
    next_local_bit = -1

    for idx, occ in enumerate(selected):
        ordering = occ.canonical_node_order()
        inst_name_map = {name: f"{prefix}{idx}_g{n}" for name, n in ordering.items()}

        # Map each boundary entry to the original scalar bit.
        entry_to_bit: dict[tuple[str, str, str], int | str] = {
            entry: circuit.instances[entry[1]].connections[entry[2]][0]
            for entry in (*occ.boundary_inputs, *occ.boundary_outputs)
        }
        boundary_nets = {entry[0] for entry in entry_to_bit}

        # Internal nets get a fresh negative bit id so they cannot clash with
        # Yosys-assigned ids elsewhere in the design.
        internal_nets = sorted(
            {net for *_, net in occ.internal_edges if net not in boundary_nets}
        )
        wire_map: dict[str, int] = {}
        for net in internal_nets:
            wire_map[net] = next_local_bit
            next_local_bit -= 1

        pin_to_net: dict[tuple[str, str], int | str] = {}
        for src, src_pin, dst, dst_pin, net_name in occ.internal_edges:
            value = wire_map.get(net_name, net_to_bit.get(net_name, net_name))
            pin_to_net[(src, src_pin)] = value
            pin_to_net[(dst, dst_pin)] = value
        for entry, bit in entry_to_bit.items():
            pin_to_net[(entry[1], entry[2])] = bit

        for name in sorted(occ.instances, key=lambda n: ordering[n]):
            orig = circuit.instances[name]
            new_instances.append(
                Instance(
                    name=inst_name_map[name],
                    cell_type=orig.cell_type,
                    connections={
                        pin: [value]
                        for (iname, pin), value in sorted(pin_to_net.items())
                        if iname == name
                    },
                    attributes=orig.attributes,
                )
            )

        for net_name, bit in wire_map.items():
            new_circuit.register_net(Net(name=net_name, bits=[bit]))

        instances_to_remove |= occ.instances

    for name in instances_to_remove:
        del new_circuit.instances[name]

    for inst in new_instances:
        new_circuit.instances[inst.name] = inst

    _rebuild_net_links(new_circuit)
    _remove_disconnected_nets(new_circuit)
    return new_circuit


def _rebuild_net_links(circuit: Circuit) -> None:
    """Recompute ``Net.drivers`` and ``Net.loads`` from the instances."""
    circuit.invalidate_bit_index()
    for net in circuit.nets.values():
        net.drivers = []
        net.loads = []

    for inst in circuit.instances.values():
        pin_dirs = _pin_directions_for_instance(inst)
        for pin, bits in inst.connections.items():
            direction = pin_dirs.get(pin)
            for bit in bits:
                if not isinstance(bit, int):
                    continue
                net = circuit.net_for_bit(bit)
                if net is None:
                    net_name = f"_auto_{bit}_"
                    net = circuit.nets.get(net_name)
                    if net is None:
                        net = Net(name=net_name, bits=[bit])
                        circuit.register_net(net)
                if direction == "output":
                    net.drivers.append((inst.name, pin))
                else:
                    net.loads.append((inst.name, pin))


def _pin_directions_for_instance(inst: Instance) -> dict[str, str]:
    """Return pin directions for an instance.

    Standard cells carry their directions in ``attributes["port_directions"]``.
    Generated AION cells do not exist in the technology dictionary, so their
    directions are recovered from the port-naming convention (``O*`` outputs,
    everything else inputs) established by
    :class:`~aion_opt.cellgen.generator.CellGenerator`.
    """
    pin_dirs = inst.attributes.get("port_directions")
    if pin_dirs:
        return dict(pin_dirs)
    return {
        pin: ("output" if pin.startswith(OUTPUT_PORT_PREFIX) else "input")
        for pin in inst.connections
    }


def _remove_disconnected_nets(circuit: Circuit) -> None:
    """Delete nets that are no longer connected to any instance."""
    to_remove = [
        net_name
        for net_name, net in circuit.nets.items()
        # Keep top-level port nets and auto-generated placeholders.
        if net.top_port is None
        and not net_name.startswith("_auto_")
        and not any(inst in circuit.instances for inst, _ in net.drivers + net.loads)
    ]
    for net_name in to_remove:
        del circuit.nets[net_name]
    if to_remove:
        circuit.invalidate_bit_index()
