"""Generate behavioral Verilog modules for mined patterns."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from aion_opt.io.cell_lib import CellLib
from aion_opt.io.netlist_writer import _sanitize
from aion_opt.pattern.subgraph import Pattern


SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = SCRIPT_DIR / "templates"


class CellGenerator:
    """Render AION cell modules from patterns."""

    def __init__(self, template_dir: Path | None = None) -> None:
        self.template_dir = template_dir or TEMPLATE_DIR
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @staticmethod
    def port_map_for_pattern(
        pattern: Pattern,
    ) -> tuple[dict[tuple[str, str, str], str], dict[tuple[str, str, str], str]]:
        """Return (input_entry -> port, output_entry -> port) for a pattern.

        Each map key is a boundary entry ``(net_name, instance, pin)`` so that
        the same net connected to two different cell pins produces two distinct
        ports.  This preserves the exact functionality of multi-input cells.
        """
        ordering = pattern.canonical_node_order()
        inputs = sorted(
            pattern.boundary_inputs,
            key=lambda x: (ordering[x[1]], x[2]),
        )
        outputs = sorted(
            pattern.boundary_outputs,
            key=lambda x: (ordering[x[1]], x[2]),
        )

        input_port_map = {entry: f"I{i}" for i, entry in enumerate(inputs)}
        output_port_map = {entry: f"O{i}" for i, entry in enumerate(outputs)}
        return input_port_map, output_port_map

    def generate_cell(
        self,
        pattern: Pattern,
        module_id: int,
        cell_lib: CellLib,
    ) -> str:
        """Render a single AION cell module for the given pattern."""
        ordering = pattern.canonical_node_order()

        # Generic instance names g0, g1, ...
        inst_name_map = {name: f"g{idx}" for name, idx in ordering.items()}

        input_port_map, output_port_map = self.port_map_for_pattern(pattern)

        ports: list[dict[str, str]] = []
        for name in input_port_map.values():
            ports.append({"name": name, "direction": "input"})
        for name in output_port_map.values():
            ports.append({"name": name, "direction": "output"})

        boundary_entries = set(input_port_map) | set(output_port_map)
        output_net_to_entry = {entry[0]: entry for entry in output_port_map}

        # Internal nets are those that connect instances inside the pattern
        # and are not boundary nets.  A net driven by an internal pin and also
        # leaving the pattern is an output port, not a local wire.
        internal_nets: set[str] = set()
        for _, _, _, _, net_name in pattern.internal_edges:
            if net_name not in output_net_to_entry:
                internal_nets.add(net_name)

        wire_map = {
            net: f"w{i}" for i, net in enumerate(sorted(internal_nets))
        }

        def net_for_pin(value: str | tuple[str, str, str]) -> str:
            if isinstance(value, tuple):
                if value in input_port_map:
                    return input_port_map[value]
                if value in output_port_map:
                    return output_port_map[value]
            # Internal edge that also leaves the pattern routes to the output port.
            if value in output_net_to_entry:
                return output_port_map[output_net_to_entry[value]]
            return wire_map.get(value, _sanitize(value))  # type: ignore[arg-type]

        # Build a pin-to-value mapping for all pins inside the pattern.
        # Boundary pins map to their boundary entry so that duplicate net names
        # on different pins still route to the correct AION port.
        pin_to_value: dict[tuple[str, str], str | tuple[str, str, str]] = {}
        for src, src_pin, dst, dst_pin, net_name in pattern.internal_edges:
            pin_to_value[(src, src_pin)] = net_name
            pin_to_value[(dst, dst_pin)] = net_name
        for entry in pattern.boundary_inputs:
            pin_to_value[(entry[1], entry[2])] = entry
        for entry in pattern.boundary_outputs:
            pin_to_value[(entry[1], entry[2])] = entry

        instances: list[dict[str, Any]] = []
        for name in sorted(pattern.instances, key=lambda n: ordering[n]):
            connections: list[dict[str, str]] = []
            for (iname, pin), value in sorted(pin_to_value.items()):
                if iname != name:
                    continue
                connections.append({"pin": pin, "net": net_for_pin(value)})

            collapsed_type = pattern.node_types[name]
            concrete_type = cell_lib.info(collapsed_type).get("name", collapsed_type)
            instances.append(
                {
                    "name": inst_name_map[name],
                    "cell_type": concrete_type,
                    "connections": connections,
                }
            )

        # Wires correspond to internal nets (not boundary ports).
        wires = sorted(wire_map.values())

        module_name = self.module_name(pattern, module_id)
        template = self.env.get_template("aion_cell_v.j2")
        rendered = template.render(
            module_name=module_name,
            ports=ports,
            wires=wires,
            instances=instances,
        )
        # Embed the canonical key so rewrite can map mined patterns back to
        # user-provided cell modules without regenerating them.
        return f"// AION canonical_key: {pattern.canonical_key}\n{rendered}"

    @staticmethod
    def module_name(pattern: Pattern, module_id: int) -> str:
        """Return a deterministic module name for a pattern."""
        type_names = sorted(set(pattern.node_types.values()))
        functionality = "_".join(type_names) if type_names else "EMPTY"
        functionality = functionality.replace("sg13g2_", "")
        return f"AION_{functionality}_{module_id}"
