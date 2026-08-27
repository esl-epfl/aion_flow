"""Build signal-flow graphs from a Circuit."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from aion_opt.graph.circuit import Circuit, Instance
    from aion_opt.io.cell_lib import CellLib


class SignalFlowGraph:
    """Directed graph of combinational instances linked by driven nets."""

    def __init__(
        self,
        circuit: "Circuit",
        combinational_types: set[str],
        collapse: Callable[[str], str] | None = None,
    ) -> None:
        self.circuit = circuit
        self.combo_types = combinational_types
        self.collapse = collapse or (lambda x: x)
        self.adj: dict[str, set[str]] = defaultdict(set)
        self.rev: dict[str, set[str]] = defaultdict(set)
        self.edge_net: dict[tuple[str, str], str] = {}
        # Pin-level signal-flow edges: (src_inst, src_pin, dst_inst, dst_pin, net_name)
        self.pin_edges: list[tuple[str, str, str, str, str]] = []
        self._build()

    def _build(self) -> None:
        for net in self.circuit.nets.values():
            inst_drivers = [
                inst for inst, pin in net.drivers if inst in self.circuit.instances
            ]
            inst_loads = [inst for inst, pin in net.loads if inst in self.circuit.instances]

            combo_drivers = [
                d
                for d in inst_drivers
                if self.collapse(self.circuit.instances[d].cell_type)
                in self.combo_types
            ]
            combo_loads = [
                l
                for l in inst_loads
                if self.collapse(self.circuit.instances[l].cell_type)
                in self.combo_types
            ]

            # Build signal-flow adjacency for combinational nodes only.
            if combo_drivers and combo_loads:
                for src in combo_drivers:
                    for dst in combo_loads:
                        self.adj[src].add(dst)
                        self.rev[dst].add(src)
                        self.edge_net[(src, dst)] = net.name

            # Record all pin edges that touch at least one combinational node.
            # These are used to detect pattern boundaries and include top-level
            # port drivers/loads even when they are not circuit instances.
            if not net.drivers or not net.loads:
                continue
            for src, sp in net.drivers:
                src_combo = (
                    src in self.circuit.instances
                    and self.collapse(self.circuit.instances[src].cell_type)
                    in self.combo_types
                )
                for dst, dp in net.loads:
                    dst_combo = (
                        dst in self.circuit.instances
                        and self.collapse(self.circuit.instances[dst].cell_type)
                        in self.combo_types
                    )
                    if src_combo or dst_combo:
                        self.pin_edges.append((src, sp, dst, dp, net.name))

    def nodes(self) -> set[str]:
        return {
            name
            for name, inst in self.circuit.instances.items()
            if self.collapse(inst.cell_type) in self.combo_types
        }

    def fanin(self, instance_name: str) -> set[str]:
        return set(self.rev.get(instance_name, set()))

    def fanout(self, instance_name: str) -> set[str]:
        return set(self.adj.get(instance_name, set()))

    def neighbors(self, instance_name: str) -> set[str]:
        """All combinational nodes connected to ``instance_name`` by an edge."""
        return self.fanin(instance_name) | self.fanout(instance_name)

    def neighbors_of_set(self, nodes: set[str]) -> set[str]:
        """All combinational nodes adjacent to any node in ``nodes``."""
        result: set[str] = set()
        for n in nodes:
            result |= self.neighbors(n)
        return result - nodes

    def topological_order(self) -> list[str]:
        """Return a topological ordering of combinational instances."""
        in_degree = {n: len(self.fanin(n)) for n in self.nodes()}
        queue = [n for n, d in in_degree.items() if d == 0]
        order: list[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for succ in sorted(self.fanout(node)):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)
        return order


def build_signal_flow_graph(
    circuit: "Circuit",
    cell_lib: "CellLib",
) -> SignalFlowGraph:
    """Build the directed signal-flow graph for pattern mining."""
    return SignalFlowGraph(
        circuit,
        cell_lib.combinational_types(),
        collapse=cell_lib.collapse_name,
    )
