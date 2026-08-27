"""Enumerate and count recurring combinational patterns."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from aion_opt.pattern.subgraph import Pattern, build_pattern

if TYPE_CHECKING:
    from aion_opt.graph.builder import SignalFlowGraph
    from aion_opt.graph.circuit import Circuit
    from aion_opt.io.cell_lib import CellLib


def mine_patterns(
    circuit: "Circuit",
    sfg: "SignalFlowGraph",
    cell_lib: "CellLib",
    max_size: int = 3,
    min_occurrences: int = 2,
) -> dict[str, list[Pattern]]:
    """Mine connected combinational patterns up to ``max_size`` nodes.

    Returns a mapping from canonical pattern key to all its occurrences.
    Only patterns with at least ``min_occurrences`` occurrences are kept.
    """
    if max_size < 2:
        raise ValueError("max_size must be at least 2")

    collapse = cell_lib.collapse_name
    nodes = sorted(sfg.nodes())

    patterns: dict[str, list[Pattern]] = defaultdict(list)

    for root in nodes:
        # Each connected subset is enumerated once from its minimum node.
        # Stack items: (current_set, candidate_nodes)
        stack: list[tuple[frozenset[str], set[str]]] = [
            (frozenset([root]), sfg.neighbors(root) - {root})
        ]

        while stack:
            current, candidates = stack.pop()

            if len(current) >= 2:
                pattern = build_pattern(
                    circuit, set(current), collapse, sfg.pin_edges
                )
                patterns[pattern.canonical_key].append(pattern)

            if len(current) >= max_size:
                continue

            for cand in sorted(candidates):
                # Enforce root is the minimum element to avoid duplicates.
                if cand <= root:
                    continue
                new_set = current | {cand}
                new_candidates = (
                    candidates | sfg.neighbors(cand)
                ) - new_set
                stack.append((new_set, new_candidates))

    # Filter by minimum occurrence count.
    return {
        key: occurrences
        for key, occurrences in patterns.items()
        if len(occurrences) >= min_occurrences
    }
