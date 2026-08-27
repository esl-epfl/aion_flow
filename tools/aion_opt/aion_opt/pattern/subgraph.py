"""Canonical pattern / subgraph representation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from itertools import permutations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aion_opt.graph.circuit import Circuit


@dataclass(frozen=True)
class Pattern:
    """An abstract combinational pattern plus one concrete occurrence.

    The canonical key ignores the concrete instance names so that two
    structurally identical occurrences map to the same pattern.
    """

    instances: frozenset[str]
    node_types: dict[str, str]  # instance name -> collapsed cell type
    internal_edges: tuple[
        tuple[str, str, str, str, str], ...
    ]  # (src, src_pin, dst, dst_pin, net_name)
    boundary_inputs: tuple[
        tuple[str, str, str], ...
    ]  # (net_name, dst_inst, dst_pin)
    boundary_outputs: tuple[
        tuple[str, str, str], ...
    ]  # (net_name, src_inst, src_pin)
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
        """Return the canonical relabeling of instances to indices 0..n-1."""
        instances = sorted(self.node_types.keys())
        n = len(instances)
        if n == 0:
            return {}

        best: str | None = None
        best_mapping: dict[str, int] | None = None
        for perm in permutations(range(n)):
            mapping = {instances[i]: perm[i] for i in range(n)}
            parts: list[str] = []
            for inst in instances:
                parts.append(f"N{mapping[inst]}:{self.node_types[inst]}")
            for src, src_pin, dst, dst_pin, _ in self.internal_edges:
                parts.append(
                    f"E{mapping[src]}:{src_pin}:{mapping[dst]}:{dst_pin}"
                )
            parts.sort()
            candidate = "|".join(parts)
            if best is None or candidate < best:
                best = candidate
                best_mapping = mapping
        assert best_mapping is not None
        return best_mapping


@dataclass
class PatternOccurrence:
    """A concrete occurrence of a pattern in a circuit."""

    pattern_key: str
    instances: frozenset[str]
    boundary_inputs: list[tuple[str, str, str]]  # (net_name, dst_inst, dst_pin)
    boundary_outputs: list[tuple[str, str, str]]  # (net_name, src_inst, src_pin)


def _canonical_key(
    node_types: dict[str, str],
    internal_edges: list[tuple[str, str, str, str, str]],
) -> str:
    """Return a deterministic canonical string for the abstract pattern."""
    instances = sorted(node_types.keys())
    n = len(instances)
    if n == 0:
        return ""

    best: str | None = None
    for perm in permutations(range(n)):
        mapping = {instances[i]: perm[i] for i in range(n)}
        parts: list[str] = []
        for inst in instances:
            parts.append(f"N{mapping[inst]}:{node_types[inst]}")
        for src, src_pin, dst, dst_pin, net_name in internal_edges:
            parts.append(
                f"E{mapping[src]}:{src_pin}:{mapping[dst]}:{dst_pin}"
            )
        parts.sort()
        candidate = "|".join(parts)
        if best is None or candidate < best:
            best = candidate
    assert best is not None
    return best


def build_pattern(
    circuit: "Circuit",
    instances: set[str],
    collapse: Callable[[str], str],
    pin_edges: list[tuple[str, str, str, str, str]],
) -> Pattern:
    """Build a Pattern from a set of instance names in a circuit."""
    inst_set = frozenset(instances)
    node_types = {name: collapse(circuit.instances[name].cell_type) for name in inst_set}

    internal_edges: list[tuple[str, str, str, str, str]] = []
    boundary_inputs: list[tuple[str, str, str]] = []
    boundary_outputs: list[tuple[str, str, str]] = []

    for src, src_pin, dst, dst_pin, net_name in pin_edges:
        src_in = src in inst_set
        dst_in = dst in inst_set
        if src_in and dst_in:
            internal_edges.append((src, src_pin, dst, dst_pin, net_name))
        elif src_in and not dst_in:
            boundary_outputs.append((net_name, src, src_pin))
        elif not src_in and dst_in:
            boundary_inputs.append((net_name, dst, dst_pin))

    # Deduplicate boundary entries: a net may fan out to multiple pins inside
    # the pattern, but it corresponds to a single boundary port.
    seen_bi: set[tuple[str, str, str]] = set()
    dedup_bi: list[tuple[str, str, str]] = []
    for x in boundary_inputs:
        if x not in seen_bi:
            seen_bi.add(x)
            dedup_bi.append(x)
    seen_bo: set[tuple[str, str, str]] = set()
    dedup_bo: list[tuple[str, str, str]] = []
    for x in boundary_outputs:
        if x not in seen_bo:
            seen_bo.add(x)
            dedup_bo.append(x)

    key = _canonical_key(node_types, internal_edges)

    return Pattern(
        instances=inst_set,
        node_types=node_types,
        internal_edges=tuple(internal_edges),
        boundary_inputs=tuple(dedup_bi),
        boundary_outputs=tuple(dedup_bo),
        canonical_key=key,
    )

