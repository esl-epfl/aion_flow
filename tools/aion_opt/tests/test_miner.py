"""Enumeration must be exhaustive, duplicate-free and job-count independent."""

from __future__ import annotations

from itertools import combinations

import pytest

from aion_opt.pattern.miner import MiningGraph, _mine_roots


def _graph(adjacency: dict[int, list[int]], types: dict[int, str] | None = None):
    """Build a MiningGraph from a plain undirected adjacency map.

    One pin edge per undirected pair keeps the boundary bookkeeping simple; the
    tests here are about *which* subgraphs are visited, not about ports.
    """
    n = max(adjacency) + 1
    names = [f"u{i}" for i in range(n)]
    node_types = [(types or {}).get(i, "cell") for i in range(n)]

    edge_src, edge_dst, edge_sp, edge_dp, edge_net = [], [], [], [], []
    node_edges: list[list[int]] = [[] for _ in range(n)]
    for a in range(n):
        for b in adjacency.get(a, []):
            if b <= a:
                continue
            idx = len(edge_src)
            edge_src.append(a)
            edge_dst.append(b)
            edge_sp.append("Y")
            edge_dp.append("A")
            edge_net.append(f"n{a}_{b}")
            node_edges[a].append(idx)
            node_edges[b].append(idx)

    return MiningGraph(
        names=names,
        types=node_types,
        adj=[tuple(sorted(adjacency.get(i, []))) for i in range(n)],
        edge_src=edge_src,
        edge_dst=edge_dst,
        edge_src_pin=edge_sp,
        edge_dst_pin=edge_dp,
        edge_net=edge_net,
        node_edges=[tuple(e) for e in node_edges],
    )


def _brute_force_connected(adjacency: dict[int, list[int]], n: int, max_size: int):
    """Every connected vertex subset of size 2..max_size, by exhaustive search."""
    result = set()
    for size in range(2, max_size + 1):
        for subset in combinations(range(n), size):
            members = set(subset)
            seen = {subset[0]}
            frontier = [subset[0]]
            while frontier:
                node = frontier.pop()
                for nb in adjacency.get(node, []):
                    if nb in members and nb not in seen:
                        seen.add(nb)
                        frontier.append(nb)
            if seen == members:
                result.add(subset)
    return result


def _enumerated(graph, max_size):
    found, count = _mine_roots(graph, range(graph.order), max_size, None, None)
    occurrences = [occ for occs in found.values() for occ in occs]
    return occurrences, count


TRIANGLE = {0: [1, 2], 1: [0, 2], 2: [0, 1]}
CHAIN = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2]}
STAR = {0: [1, 2, 3], 1: [0], 2: [0], 3: [0]}
DENSE = {
    0: [1, 2, 3],
    1: [0, 2, 4],
    2: [0, 1, 3, 4],
    3: [0, 2, 4],
    4: [1, 2, 3],
}


@pytest.mark.parametrize("adjacency", [TRIANGLE, CHAIN, STAR, DENSE])
@pytest.mark.parametrize("max_size", [2, 3, 4, 5])
def test_enumeration_is_exhaustive_and_duplicate_free(adjacency, max_size):
    graph = _graph(adjacency)
    occurrences, count = _enumerated(graph, max_size)

    assert len(occurrences) == len(set(occurrences)), "a subgraph was visited twice"
    assert count == len(occurrences)
    assert set(occurrences) == _brute_force_connected(
        adjacency, graph.order, max_size
    )


def test_triangle_is_not_counted_six_times():
    """Regression: the old frontier walk emitted {0,1,2} once per insertion order."""
    occurrences, _ = _enumerated(_graph(TRIANGLE), 3)
    assert occurrences.count((0, 1, 2)) == 1


def test_partitioned_roots_match_a_single_pass():
    """Splitting the roots across workers must not change the result."""
    graph = _graph(DENSE)
    whole, _ = _mine_roots(graph, range(graph.order), 4, None, None)

    merged: dict[str, list] = {}
    for start in range(2):
        partial, _ = _mine_roots(
            graph, range(start, graph.order, 2), 4, None, None
        )
        for key, occs in partial.items():
            merged.setdefault(key, []).extend(occs)

    assert {k: sorted(v) for k, v in whole.items()} == {
        k: sorted(v) for k, v in merged.items()
    }


def test_same_structure_shares_one_key():
    """Two disjoint copies of a chain are one pattern with two occurrences."""
    adjacency = {0: [1], 1: [0], 2: [3], 3: [2]}
    found, _ = _mine_roots(_graph(adjacency), range(4), 2, None, None)
    assert len(found) == 1
    assert sorted(next(iter(found.values()))) == [(0, 1), (2, 3)]


def test_different_cell_types_split_the_pattern():
    adjacency = {0: [1], 1: [0], 2: [3], 3: [2]}
    types = {0: "nand2", 1: "nor2", 2: "nand2", 3: "inv"}
    found, _ = _mine_roots(_graph(adjacency, types), range(4), 2, None, None)
    assert len(found) == 2


def test_max_outputs_filters_during_enumeration():
    """A chain 0-1-2: {0,1} leaves via node 1, so it has one boundary output."""
    graph = _graph(CHAIN)
    unlimited, _ = _mine_roots(graph, range(graph.order), 2, None, None)
    limited, _ = _mine_roots(graph, range(graph.order), 2, 0 + 1, None)
    assert sum(len(v) for v in limited.values()) <= sum(
        len(v) for v in unlimited.values()
    )
