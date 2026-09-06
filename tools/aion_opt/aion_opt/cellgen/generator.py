"""Generate structural Verilog modules for mined patterns."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from aion_opt.io.cell_lib import CellLib
from aion_opt.io.netlist_writer import _sanitize
from aion_opt.pattern.subgraph import Pattern


SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = SCRIPT_DIR / "templates"

#: Prefix put in front of every generated module name.  Overridable everywhere
#: via ``--cell-prefix`` / ``CELL_PREFIX``; nothing in the tool assumes "AION_".
DEFAULT_CELL_PREFIX = "AION_"

#: Prefix of the generated *port* names.  ``I0..In`` are inputs, ``O0..On``
#: outputs; :func:`aion_opt.io.rewriter._pin_directions_for_instance` relies on
#: this convention to re-derive port directions for AION instances.
INPUT_PORT_PREFIX = "I"
OUTPUT_PORT_PREFIX = "O"

#: Suffix of the port carrying a complemented input.  ``aion_minimizer`` uses
#: the same spelling, and the port name is the whole interface between the two
#: tools.
COMPLEMENT_SUFFIX = "_bar"


class CellGenerator:
    """Render AION cell modules from patterns.

    Parameters
    ----------
    template_dir:
        Directory holding ``aion_cell_v.j2``.
    prefix:
        Module-name prefix, e.g. ``"AION_"`` or ``"MYLIB_"``.
    """

    def __init__(
        self,
        template_dir: Path | None = None,
        prefix: str = DEFAULT_CELL_PREFIX,
    ) -> None:
        self.template_dir = template_dir or TEMPLATE_DIR
        self.prefix = prefix
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # ------------------------------------------------------------------
    # Ports
    # ------------------------------------------------------------------
    @staticmethod
    def port_map_for_pattern(
        pattern: Pattern,
    ) -> tuple[dict[tuple[str, str, str], str], dict[tuple[str, str, str], str]]:
        """Return ``(input_entry -> port, output_entry -> port)`` for a pattern.

        Each map key is a boundary entry ``(net_name, instance, pin)``, so the
        same net connected to two different cell pins produces two distinct
        ports.  This preserves the exact functionality of multi-input cells.

        Ports are ordered by the pattern's canonical node order, which is part
        of the canonical key -- so every occurrence of a pattern produces the
        same port map and can share one generated module.
        """
        ordering = pattern.canonical_node_order()
        inputs = sorted(
            pattern.boundary_inputs,
            key=lambda x: (ordering[x[1]], x[2], x[0]),
        )
        outputs = sorted(
            pattern.boundary_outputs,
            key=lambda x: (ordering[x[1]], x[2], x[0]),
        )

        input_port_map = {
            entry: f"{INPUT_PORT_PREFIX}{i}" for i, entry in enumerate(inputs)
        }
        output_port_map = {
            entry: f"{OUTPUT_PORT_PREFIX}{i}" for i, entry in enumerate(outputs)
        }
        return input_port_map, output_port_map

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def generate_cell(
        self,
        pattern: Pattern,
        module_id: int,
        cell_lib: CellLib,
        complement_inputs: Sequence[str] = (),
    ) -> str:
        """Render a single AION cell module for the given pattern.

        ``complement_inputs`` names input ports (``I0``, ``I1``, ...) whose
        transistor implementation takes the complement from outside.  Each gains
        a ``<port>_bar`` port, and the module body reads ``~<port>_bar`` in
        place of the port itself.

        Reading the complement rather than the port is deliberate: the module is
        the reference an equivalence check compares against, so wiring
        ``I1_bar`` to anything other than ``~I1`` has to make that check fail.
        The plain port stays in the interface because the generated transistor
        cell still uses it.
        """
        ordering = pattern.canonical_node_order()

        # Generic instance names g0, g1, ... in canonical order.
        inst_name_map = {name: f"g{idx}" for name, idx in ordering.items()}

        input_port_map, output_port_map = self.port_map_for_pattern(pattern)

        port_names = set(input_port_map.values())
        unknown = [p for p in complement_inputs if p not in port_names]
        if unknown:
            raise ValueError(
                f"complement_inputs names non-input port(s) {sorted(unknown)}; "
                f"this pattern has {sorted(port_names)}"
            )
        complements = [p for p in input_port_map.values() if p in set(complement_inputs)]

        ports: list[dict[str, str]] = []
        for name in input_port_map.values():
            ports.append({"name": name, "direction": "input"})
        for name in output_port_map.values():
            ports.append({"name": name, "direction": "output"})
        for name in complements:
            ports.append({"name": name + COMPLEMENT_SUFFIX, "direction": "input"})

        # Inside the module a complemented input is read through a local wire,
        # so every consumer of that port goes through ``~<port>_bar``.
        complement_wire = {name: f"{name}_int" for name in complements}
        assigns = [
            {"lhs": wire, "rhs": f"~{name}{COMPLEMENT_SUFFIX}"}
            for name, wire in complement_wire.items()
        ]

        output_net_to_entry = {entry[0]: entry for entry in output_port_map}

        # Internal nets connect instances inside the pattern.  A net driven by
        # an internal pin that also leaves the pattern is an output port, not a
        # local wire.
        internal_nets = {
            net_name
            for *_, net_name in pattern.internal_edges
            if net_name not in output_net_to_entry
        }
        wire_map = {net: f"w{i}" for i, net in enumerate(sorted(internal_nets))}

        def net_for_pin(value: str | tuple[str, str, str]) -> str:
            if isinstance(value, tuple):
                if value in input_port_map:
                    port = input_port_map[value]
                    return complement_wire.get(port, port)
                if value in output_port_map:
                    return output_port_map[value]
            if value in output_net_to_entry:
                return output_port_map[output_net_to_entry[value]]
            return wire_map.get(value, _sanitize(value))  # type: ignore[arg-type]

        # Pin-to-value mapping for every pin inside the pattern.  Boundary pins
        # map to their boundary *entry* so that duplicate net names on
        # different pins still route to the correct AION port.
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
            connections = [
                {"pin": pin, "net": net_for_pin(value)}
                for (iname, pin), value in sorted(pin_to_value.items())
                if iname == name
            ]
            instances.append(
                {
                    "name": inst_name_map[name],
                    "cell_type": cell_lib.concrete_name(pattern.node_types[name]),
                    "connections": connections,
                }
            )

        rendered = self.env.get_template("aion_cell_v.j2").render(
            module_name=self.module_name(pattern, module_id),
            ports=ports,
            wires=sorted(wire_map.values()) + sorted(complement_wire.values()),
            assigns=assigns,
            instances=instances,
        )
        # Embed the canonical key so `rewrite` can map mined patterns back to
        # user-provided cell modules without regenerating them, and the
        # complemented ports so it knows what else it has to drive.
        markers = f"// AION canonical_key: {pattern.canonical_key}\n"
        if complements:
            markers += f"// AION complement_inputs: {' '.join(complements)}\n"
        return f"{markers}{rendered}"

    # ------------------------------------------------------------------
    # Naming
    # ------------------------------------------------------------------
    def module_name(self, pattern: Pattern, module_id: int) -> str:
        """Return a deterministic module name for a pattern.

        ``<prefix><sorted cell functions>_<id>``, e.g. ``AION_nand2_nor2_0``.
        The library-specific cell-name prefix (``sg13g2_``) is stripped to keep
        the identifier readable.
        """
        type_names = sorted(set(pattern.node_types.values()))
        functionality = "_".join(type_names) if type_names else "EMPTY"
        functionality = _strip_library_prefix(functionality)
        return f"{self.prefix}{functionality}_{module_id}"


def _strip_library_prefix(name: str) -> str:
    """Drop the ``<tech>_`` prefix shared by every PDK cell name.

    ``sg13g2_nand2_sg13g2_nor2`` -> ``nand2_nor2``.  The prefix is derived from
    the cell names themselves, so no technology is hard-coded.
    """
    parts = name.split("_")
    if not parts:
        return name
    library = parts[0]
    return "_".join(p for p in name.split("_") if p != library) or name
