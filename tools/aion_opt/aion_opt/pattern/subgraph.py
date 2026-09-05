"""Canonical pattern / subgraph representation."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from aion_opt.pattern.canonical import canonicalize_named

if TYPE_CHECKING:
    from aion_opt.graph.circuit import Circuit

#: ``(src_inst, src_pin, dst_inst, dst_pin, net_name)``
PinEdge = tuple[str, str, str, str, str]
#: ``(net_name, inst, pin)``
BoundaryEntry = tuple[str, str, str]


@dataclass(frozen=True)
class Pattern:
    """An abstract combinational pattern plus one concrete occurrence.

    The :attr:`canonical_key` ignores the concrete instance names, so two
    structurally identical occurrences map to the same pattern -- and therefore
    to the same generated cell.  The key also encodes the boundary pins, so any
    two occurrences sharing a key are guaranteed to have identical port maps.
    """

    instances: frozenset[str]
    node_types: dict[str, str]  # instance name -> collapsed cell type
    internal_edges: tuple[PinEdge, ...]
    boundary_inputs: tuple[BoundaryEntry, ...]
    boundary_outputs: tuple[BoundaryEntry, ...]
    canonical_key: str = field(compare=True)

    def __hash__(self) -> int:
        return hash(self.canonical_key)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pattern):
            return NotImplemented
        return self.canonical_key == other.canonical_key

    def size(self) -> int:
        return len(self.instances)

    def canonical_node_order(self) -> dict[str, int]:
        """Return the canonical relabelling of instances to indices ``0..n-1``.

        Consistent with :attr:`canonical_key`: occurrences that share a key
        also share this ordering (up to pattern automorphisms, which by
        definition produce an identical cell).
        """
        _, mapping = canonicalize_named(
            self.node_types,
            list(self.internal_edges),
            list(self.boundary_inputs),
            list(self.boundary_outputs),
        )
        return mapping


def _dedup(entries: Iterable[BoundaryEntry]) -> list[BoundaryEntry]:
    """Order-preserving de-duplication of boundary entries."""
    seen: set[BoundaryEntry] = set()
    result: list[BoundaryEntry] = []
    for entry in entries:
        if entry not in seen:
            seen.add(entry)
            result.append(entry)
    return result


def split_edges(
    inst_set: frozenset[str],
    pin_edges: Iterable[PinEdge],
) -> tuple[list[PinEdge], list[BoundaryEntry], list[BoundaryEntry]]:
    """Split incident pin edges into internal edges and boundary entries.

    ``pin_edges`` only needs to contain the edges incident to ``inst_set`` (see
    :meth:`~aion_opt.graph.builder.SignalFlowGraph.edges_for_instances`); edges
    that touch neither end are ignored anyway.
    """
    internal: list[PinEdge] = []
    boundary_in: list[BoundaryEntry] = []
    boundary_out: list[BoundaryEntry] = []

    for src, src_pin, dst, dst_pin, net_name in pin_edges:
        src_in = src in inst_set
        dst_in = dst in inst_set
        if src_in and dst_in:
            internal.append((src, src_pin, dst, dst_pin, net_name))
        elif src_in:
            boundary_out.append((net_name, src, src_pin))
        elif dst_in:
            boundary_in.append((net_name, dst, dst_pin))

    # A net may fan out to several pins inside the pattern but still
    # corresponds to a single boundary port per (net, instance, pin).
    return internal, _dedup(boundary_in), _dedup(boundary_out)


def build_pattern(
    circuit: "Circuit",
    instances: set[str] | frozenset[str],
    collapse: Callable[[str], str],
    pin_edges: Iterable[PinEdge],
) -> Pattern:
    """Build a :class:`Pattern` from a set of instance names in a circuit."""
    inst_set = frozenset(instances)
    node_types = {name: collapse(circuit.instances[name].cell_type) for name in inst_set}

    internal, boundary_in, boundary_out = split_edges(inst_set, pin_edges)
    key, _ = canonicalize_named(node_types, internal, boundary_in, boundary_out)

    return Pattern(
        instances=inst_set,
        node_types=node_types,
        internal_edges=tuple(internal),
        boundary_inputs=tuple(boundary_in),
        boundary_outputs=tuple(boundary_out),
        canonical_key=key,
    )
