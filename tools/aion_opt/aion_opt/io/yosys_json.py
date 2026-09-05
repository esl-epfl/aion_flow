"""Parse a Yosys JSON netlist into the internal Circuit model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aion_opt.graph.circuit import Circuit, Instance, Net, TopPort
from aion_opt.io.cell_lib import CellLib


CONST_NAMES = {
    "0": "1'b0",
    "1": "1'b1",
    "x": "1'bx",
    "z": "1'bz",
}


def _bit_name(bit: int | str) -> str:
    """Return a human-readable Verilog name for a bit value."""
    if isinstance(bit, str):
        return CONST_NAMES.get(bit, f"1'b{bit}")
    return f"_bit_{bit}_"


def load_yosys_json(
    path: Path,
    cell_lib: CellLib | None = None,
    top_module: str | None = None,
) -> Circuit:
    """Load a Yosys JSON file and return the top-module Circuit."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    modules = data.get("modules", {})
    if top_module is None:
        # Pick the module flagged as top, or the only module, or raise.
        top_module = _resolve_top_module(modules)

    if top_module not in modules:
        raise ValueError(f"Module {top_module!r} not found in {path}")

    mod = modules[top_module]
    circuit = Circuit(
        name=top_module,
        attributes=mod.get("attributes", {}),
    )

    # 1. Ports.
    for port_name, port_info in mod.get("ports", {}).items():
        bits = port_info.get("bits", [])
        circuit.ports.append(
            TopPort(
                name=port_name,
                direction=port_info.get("direction", "input"),
                bits=_normalize_bits(bits),
            )
        )

    # 2. Netnames.
    for net_name, net_info in mod.get("netnames", {}).items():
        bits = _normalize_bits(net_info.get("bits", []))
        circuit.nets[net_name] = Net(name=net_name, bits=bits)

    # 3. Cells -> Instances.
    for cell_name, cell_info in mod.get("cells", {}).items():
        cell_type = cell_info.get("type", "")
        if cell_lib is not None and cell_type not in cell_lib:
            # Skip blackboxes / macros not present in the tech dictionary.
            continue

        port_directions = {
            k: str(v) for k, v in cell_info.get("port_directions", {}).items()
        }
        # If the JSON did not include port directions (e.g. read_verilog output),
        # fall back to the cell library pin definitions.
        if not port_directions and cell_lib is not None:
            port_directions = cell_lib.pins(cell_type)
        inst = Instance(
            name=cell_name,
            cell_type=cell_type,
            parameters={
                k: str(v) for k, v in cell_info.get("parameters", {}).items()
            },
            connections={
                k: _normalize_bits(v)
                for k, v in cell_info.get("connections", {}).items()
            },
            attributes={
                "port_directions": port_directions,
                **{k: str(v) for k, v in cell_info.get("attributes", {}).items()},
            },
        )
        circuit.instances[cell_name] = inst

    # 4. Cross-link nets with instance pins.
    _link_nets(circuit, cell_lib)

    return circuit


def _normalize_bits(bits: list[Any]) -> list[int | str]:
    """Normalize Yosys bit values: integers for signals, strings for constants."""
    result: list[int | str] = []
    for b in bits:
        if isinstance(b, int):
            result.append(b)
        elif isinstance(b, str):
            result.append(b)
        else:
            result.append(str(b))
    return result


def _resolve_top_module(modules: dict[str, Any]) -> str:
    """Find the module marked as top, or the sole module."""
    for name, info in modules.items():
        attrs = info.get("attributes", {})
        if attrs.get("top") in ("1", 1, "00000000000000000000000000000001"):
            return name
    if len(modules) == 1:
        return next(iter(modules))
    raise ValueError(
        "No top module specified and multiple modules found: "
        f"{list(modules.keys())}"
    )


def _link_nets(circuit: Circuit, cell_lib: CellLib | None = None) -> None:
    """Populate Net.drivers, Net.loads, and Net.top_port from circuit data."""
    port_direction: dict[str, str] = {}
    for port in circuit.ports:
        for bit in port.bits:
            if isinstance(bit, int):
                port_direction[bit] = port.direction
        # Also mark the net itself as a top-port net.
        if port.name in circuit.nets:
            circuit.nets[port.name].top_port = (port.name, port.direction)

    for inst in circuit.instances.values():
        pin_dirs = dict(inst.attributes.get("port_directions", {}))
        # If the JSON did not include port directions (e.g. read_verilog output),
        # fall back to the cell library pin definitions.
        if not pin_dirs and cell_lib is not None:
            pin_dirs = cell_lib.pins(inst.cell_type)
        for pin, bits in inst.connections.items():
            direction = pin_dirs.get(pin)
            for bit in bits:
                if isinstance(bit, int):
                    net = circuit.net_for_bit(bit)
                    if net is None:
                        # Floating / anonymous net: create one.
                        net_name = f"_auto_{bit}_"
                        net = Net(name=net_name, bits=[bit])
                        circuit.register_net(net)
                    if direction == "output":
                        net.drivers.append((inst.name, pin))
                    else:
                        net.loads.append((inst.name, pin))

    # Resolve top-port directions for bits.
    # A top-level input port drives the circuit (driver), while a top-level
    # output port is driven by the circuit (load).
    for port in circuit.ports:
        for bit in port.bits:
            if isinstance(bit, int):
                net = circuit.net_for_bit(bit)
                if net is not None:
                    if port.direction == "input":
                        net.drivers.append(("", port.name))
                    else:
                        net.loads.append(("", port.name))
                    if net.top_port is None:
                        net.top_port = (port.name, port.direction)
