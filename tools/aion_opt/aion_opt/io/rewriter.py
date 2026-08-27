"""Rewrite a circuit by replacing pattern occurrences with AION cells."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from aion_opt.cellgen.generator import CellGenerator
from aion_opt.graph.circuit import Circuit, Instance, Net
from aion_opt.io.netlist_writer import _collect_net_names, _collect_port_slices

if TYPE_CHECKING:
    from aion_opt.pattern.subgraph import Pattern


def rewrite_circuit(
    circuit: Circuit,
    selected: list["Pattern"],
    module_names: dict[str, str],
    flatten: bool = False,
) -> Circuit:
    """Return a new circuit with selected pattern occurrences replaced.

    ``module_names`` maps each pattern canonical key to the AION module name
    that was generated for it. If ``flatten`` is True, the AION cells are
    inlined as original PDK instances instead of being kept as hierarchical
    instances.
    """
    if flatten:
        return _rewrite_circuit_flat(circuit, selected)
    return _rewrite_circuit_hierarchical(circuit, selected, module_names)


def _rewrite_circuit_hierarchical(
    circuit: Circuit,
    selected: list["Pattern"],
    module_names: dict[str, str],
) -> Circuit:
    """Replace occurrences with hierarchical AION instances."""
    new_circuit = deepcopy(circuit)

    instances_to_remove: set[str] = set()
    new_instances: list[Instance] = []

    for idx, occ in enumerate(selected):
        key = occ.canonical_key
        module_name = module_names[key]
        input_port_map, output_port_map = CellGenerator.port_map_for_pattern(occ)

        # Build port -> net connection for the AION instance.
        # Use the exact bit from the original instance pin connection so that
        # multi-bit ports are connected to the correct scalar slice.
        connections: dict[str, list[int | str]] = {}
        for entry, port_name in input_port_map.items():
            _, dst_inst, dst_pin = entry
            bit = circuit.instances[dst_inst].connections[dst_pin][0]
            connections[port_name] = [bit]
        for entry, port_name in output_port_map.items():
            _, src_inst, src_pin = entry
            bit = circuit.instances[src_inst].connections[src_pin][0]
            connections[port_name] = [bit]

        aion_inst = Instance(
            name=f"_AION_{idx}_",
            cell_type=module_name,
            connections=connections,
        )
        new_instances.append(aion_inst)
        instances_to_remove |= occ.instances

    for name in instances_to_remove:
        del new_circuit.instances[name]

    for inst in new_instances:
        new_circuit.instances[inst.name] = inst

    _rebuild_net_links(new_circuit)
    _remove_disconnected_nets(new_circuit)
    return new_circuit


def _rewrite_circuit_flat(
    circuit: Circuit,
    selected: list["Pattern"],
) -> Circuit:
    """Replace occurrences by inlining the original PDK cells.

    This produces a flat netlist containing only the original standard cells,
    which is useful for tools that cannot reason about custom hierarchical
    modules during sequential equivalence checking.
    """
    new_circuit = deepcopy(circuit)

    # Determine mapping from net name to bit for boundary net lookup.
    net_to_bit: dict[str, int | str] = {}
    for net_name, net in circuit.nets.items():
        if len(net.bits) == 1:
            net_to_bit[net_name] = net.bits[0]

    instances_to_remove: set[str] = set()
    new_instances: list[Instance] = []
    next_local_bit = -1

    for idx, occ in enumerate(selected):
        ordering = occ.canonical_node_order()
        inst_name_map = {name: f"_AION_{idx}_g{n}" for name, n in ordering.items()}

        input_port_map, output_port_map = CellGenerator.port_map_for_pattern(occ)

        # Map each boundary entry to the original scalar bit.
        entry_to_bit: dict[tuple[str, str, str], int | str] = {}
        for entry in occ.boundary_inputs:
            _, dst_inst, dst_pin = entry
            entry_to_bit[entry] = circuit.instances[dst_inst].connections[dst_pin][0]
        for entry in occ.boundary_outputs:
            _, src_inst, src_pin = entry
            entry_to_bit[entry] = circuit.instances[src_inst].connections[src_pin][0]

        boundary_nets = {entry[0] for entry in entry_to_bit}

        # Internal nets (not boundary) get a local wire with a unique bit id.
        internal_nets: set[str] = set()
        for _, _, _, _, net_name in occ.internal_edges:
            if net_name not in boundary_nets:
                internal_nets.add(net_name)
        wire_map: dict[str, int] = {}
        for net in sorted(internal_nets):
            wire_map[net] = next_local_bit
            next_local_bit -= 1

        def net_for_pin(net_name: str) -> int | str:
            if net_name in wire_map:
                return wire_map[net_name]
            return net_to_bit.get(net_name, net_name)

        # Build pin-to-net mapping.  Boundary pins use their specific entry so
        # duplicate net names on different pins resolve to the correct scalar.
        pin_to_net: dict[tuple[str, str], int | str] = {}
        for src, src_pin, dst, dst_pin, net_name in occ.internal_edges:
            val = net_for_pin(net_name)
            pin_to_net[(src, src_pin)] = val
            pin_to_net[(dst, dst_pin)] = val
        for entry in occ.boundary_inputs:
            pin_to_net[(entry[1], entry[2])] = entry_to_bit[entry]
        for entry in occ.boundary_outputs:
            pin_to_net[(entry[1], entry[2])] = entry_to_bit[entry]

        for name in sorted(occ.instances, key=lambda n: ordering[n]):
            orig = circuit.instances[name]
            connections: dict[str, list[int | str]] = {}
            for (iname, pin), val in sorted(pin_to_net.items()):
                if iname != name:
                    continue
                connections[pin] = [val]

            new_instances.append(
                Instance(
                    name=inst_name_map[name],
                    cell_type=orig.cell_type,
                    connections=connections,
                    attributes=orig.attributes,
                )
            )

        # Add local wires to the circuit nets.
        for net_name, bit in sorted(wire_map.items(), key=lambda x: x[1], reverse=True):
            new_circuit.nets[net_name] = Net(name=net_name, bits=[bit])

        instances_to_remove |= occ.instances

    for name in instances_to_remove:
        del new_circuit.instances[name]

    for inst in new_instances:
        new_circuit.instances[inst.name] = inst

    _rebuild_net_links(new_circuit)
    _remove_disconnected_nets(new_circuit)
    return new_circuit


def _rebuild_net_links(circuit: Circuit) -> None:
    """Recompute Net.drivers and Net.loads from circuit instances."""
    for net in circuit.nets.values():
        net.drivers = []
        net.loads = []

    # Re-derive pin directions from instance attributes or, for AION cells,
    # from the port direction encoded in the port name (I* = input, O* = output).
    for inst in circuit.instances.values():
        pin_dirs = _pin_directions_for_instance(inst)
        for pin, bits in inst.connections.items():
            direction = pin_dirs.get(pin)
            for bit in bits:
                if isinstance(bit, int):
                    net = circuit.net_for_bit(bit)
                    if net is None:
                        net_name = f"_auto_{bit}_"
                        net = circuit.nets.get(net_name)
                        if net is None:
                            from aion_opt.graph.circuit import Net

                            net = Net(name=net_name, bits=[bit])
                            circuit.nets[net_name] = net
                    if direction == "output":
                        net.drivers.append((inst.name, pin))
                    else:
                        net.loads.append((inst.name, pin))


def _pin_directions_for_instance(inst: Instance) -> dict[str, str]:
    """Return pin directions for an instance."""
    pin_dirs = inst.attributes.get("port_directions")
    if pin_dirs:
        return dict(pin_dirs)
    # AION cells: I* are inputs, O* are outputs.
    return {
        pin: ("output" if pin.startswith("O") else "input")
        for pin in inst.connections
    }


def _remove_disconnected_nets(circuit: Circuit) -> None:
    """Delete nets that are no longer connected to any instance."""
    to_remove: list[str] = []
    for net_name, net in circuit.nets.items():
        # Keep nets tied to top-level ports.
        if net.top_port is not None:
            continue
        # Keep auto-generated placeholder nets.
        if net_name.startswith("_auto_"):
            continue
        # Keep nets that still have at least one non-removed instance connection.
        connected = any(
            inst in circuit.instances for inst, _ in net.drivers + net.loads
        )
        if not connected:
            to_remove.append(net_name)
    for net_name in to_remove:
        del circuit.nets[net_name]
