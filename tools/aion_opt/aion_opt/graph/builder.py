"""Build signal-flow graphs from a :class:`~aion_opt.graph.circuit.Circuit`.

The signal-flow graph (SFG) is the object the pattern miner works on.  It
contains only *combinational* instances as nodes, but it also records every
pin-level edge that touches a combinational instance -- including edges that
cross the combinational boundary (top-level ports, flip-flops).  Those crossing
edges are what turns a set of instances into a cell with input/output ports.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from aion_opt.graph.circuit import Circuit
    from aion_opt.io.cell_lib import CellLib


#: A pin-level edge: ``(src_inst, src_pin, dst_inst, dst_pin, net_name)``.
#: ``src_inst`` is ``""`` for a top-level input port and ``dst_inst`` is ``""``
#: for a top-level output port.
PinEdge = tuple[str, str, str, str, str]


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

        #: instance name -> collapsed cell type, for combinational nodes only.
        self.node_types: dict[str, str] = {}
        self.adj: dict[str, set[str]] = defaultdict(set)
        self.rev: dict[str, set[str]] = defaultdict(set)
        self.edge_net: dict[tuple[str, str], str] = {}
        #: All pin-level edges touching at least one combinational instance.
        self.pin_edges: list[PinEdge] = []
        #: instance name -> indices into :attr:`pin_edges` touching it.
        self.pin_edges_by_inst: dict[str, list[int]] = defaultdict(list)
        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        instances = self.circuit.instances
        collapse = self.collapse
        combo = self.combo_types

        self.node_types = {
            name: collapse(inst.cell_type)
            for name, inst in instances.items()
            if collapse(inst.cell_type) in combo
        }
        is_node = self.node_types.__contains__

        for net in self.circuit.nets.values():
            if not net.drivers or not net.loads:
                continue

            combo_drivers = [d for d, _ in net.drivers if is_node(d)]
            combo_loads = [l for l, _ in net.loads if is_node(l)]

            # Instance-level adjacency for combinational nodes only.
            for src in combo_drivers:
                for dst in combo_loads:
                    if src == dst:
                        continue
                    self.adj[src].add(dst)
                    self.rev[dst].add(src)
                    self.edge_net[(src, dst)] = net.name

            # Pin-level edges: keep every edge with a combinational endpoint so
            # that pattern boundaries (ports, flops) can be reconstructed.
            for src, sp in net.drivers:
                src_combo = is_node(src)
                for dst, dp in net.loads:
                    dst_combo = is_node(dst)
                    if not (src_combo or dst_combo):
                        continue
                    idx = len(self.pin_edges)
                    self.pin_edges.append((src, sp, dst, dp, net.name))
                    if src_combo:
                        self.pin_edges_by_inst[src].append(idx)
                    if dst_combo:
                        self.pin_edges_by_inst[dst].append(idx)

    # ------------------------------------------------------------------
    def nodes(self) -> set[str]:
        """Return the set of combinational instance names."""
        return set(self.node_types)

    def fanin(self, instance_name: str) -> set[str]:
        return set(self.rev.get(instance_name, ()))

    def fanout(self, instance_name: str) -> set[str]:
        return set(self.adj.get(instance_name, ()))

    def neighbors(self, instance_name: str) -> set[str]:
        """All combinational nodes connected to ``instance_name`` by an edge."""
        return self.fanin(instance_name) | self.fanout(instance_name)

    def neighbors_of_set(self, nodes: set[str]) -> set[str]:
        """All combinational nodes adjacent to any node in ``nodes``."""
        result: set[str] = set()
        for n in nodes:
            result |= self.neighbors(n)
        return result - nodes

    def edges_for_instances(self, instances: set[str]) -> list[PinEdge]:
        """Return the pin edges incident to any instance in ``instances``.

        Much cheaper than scanning :attr:`pin_edges`, which is what makes
        pattern construction independent of the design size.
        """
        seen: set[int] = set()
        for name in instances:
            seen.update(self.pin_edges_by_inst.get(name, ()))
        return [self.pin_edges[i] for i in sorted(seen)]

    def topological_order(self) -> list[str]:
        """Return a topological ordering of combinational instances."""
        from collections import deque

        in_degree = {n: len(self.fanin(n)) for n in self.nodes()}
        queue = deque(sorted(n for n, d in in_degree.items() if d == 0))
        order: list[str] = []
        while queue:
            node = queue.popleft()
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
    """Build the directed signal-flow graph used for pattern mining."""
    return SignalFlowGraph(
        circuit,
        cell_lib.combinational_types(),
        collapse=cell_lib.collapse_name,
    )
