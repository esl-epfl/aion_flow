"""Canonical labelling of small labelled multi-digraphs.

Two pattern occurrences must map to the same *canonical key* if and only if
they are structurally interchangeable, i.e. one can be turned into the other by
renaming instances.  The key is what ties a mined occurrence in the netlist to
a generated ``<PREFIX>_...`` cell module, so it has to be

* **complete** - equal keys imply isomorphic patterns (the key literally spells
  out every node, every internal edge and every boundary pin), and
* **invariant** - isomorphic patterns always produce the same key regardless of
  the instance names they happen to carry in the netlist.

Naive canonicalisation tries all ``n!`` relabellings.  That is the single
hottest operation in the miner, so this module instead

1. runs colour refinement (1-dimensional Weisfeiler-Leman) to split the nodes
   into isomorphism-invariant classes, and
2. brute-forces only the relabellings *inside* each class.

For virtually every real pattern refinement produces singleton classes and a
single relabelling is tried.  Results are memoised, so repeated occurrences of
the same pattern cost one dictionary lookup.

Boundary pins are part of the key.  This matters: two occurrences with the same
internal structure but a different number of boundary inputs (because a pin is
tied to a constant, or left dangling in one of them) need *different* cells,
and folding them together would silently corrupt the rewritten netlist.
"""

from __future__ import annotations

from functools import lru_cache
from itertools import permutations, product

#: ``(src_index, src_pin, dst_index, dst_pin)`` - net names are deliberately
#: excluded, they are occurrence-specific.
LocalEdge = tuple[int, str, int, str]
#: ``(node_index, pin)`` for a pin crossing the pattern boundary.
LocalPin = tuple[int, str]


def _refine_colors(
    n: int,
    types: tuple[str, ...],
    edges: tuple[LocalEdge, ...],
    in_pins: tuple[LocalPin, ...],
    out_pins: tuple[LocalPin, ...],
) -> list[int]:
    """Return isomorphism-invariant colours for the ``n`` nodes.

    Nodes that end up with different colours can never be mapped onto each
    other by an isomorphism, which is what lets the caller skip most
    relabellings.
    """
    boundary_in: list[list[str]] = [[] for _ in range(n)]
    boundary_out: list[list[str]] = [[] for _ in range(n)]
    for idx, pin in in_pins:
        boundary_in[idx].append(pin)
    for idx, pin in out_pins:
        boundary_out[idx].append(pin)

    out_edges: list[list[tuple[str, str, int]]] = [[] for _ in range(n)]
    in_edges: list[list[tuple[str, str, int]]] = [[] for _ in range(n)]
    for src, sp, dst, dp in edges:
        out_edges[src].append((sp, dp, dst))
        in_edges[dst].append((sp, dp, src))

    signatures = [
        f"{types[i]}|<{','.join(sorted(boundary_in[i]))}|>{','.join(sorted(boundary_out[i]))}"
        for i in range(n)
    ]
    colors = _compact(signatures)

    previous = -1
    while len(set(colors)) != previous:
        previous = len(set(colors))
        if previous == n:
            break  # already discrete
        signatures = []
        for i in range(n):
            outs = sorted(f"o{sp}>{dp}>{colors[j]}" for sp, dp, j in out_edges[i])
            ins = sorted(f"i{sp}>{dp}>{colors[j]}" for sp, dp, j in in_edges[i])
            signatures.append(f"{colors[i]}|{','.join(outs)}|{','.join(ins)}")
        colors = _compact(signatures)
    return colors


def _compact(signatures: list[str]) -> list[int]:
    """Map signature strings onto dense integers, ordered lexicographically."""
    order = {sig: idx for idx, sig in enumerate(sorted(set(signatures)))}
    return [order[sig] for sig in signatures]


def _render(
    mapping: tuple[int, ...],
    types: tuple[str, ...],
    edges: tuple[LocalEdge, ...],
    in_pins: tuple[LocalPin, ...],
    out_pins: tuple[LocalPin, ...],
) -> str:
    """Render the key for one concrete relabelling ``local index -> key index``."""
    parts = [f"N{mapping[i]}:{t}" for i, t in enumerate(types)]
    parts += [f"E{mapping[s]}:{sp}:{mapping[d]}:{dp}" for s, sp, d, dp in edges]
    parts += [f"I{mapping[i]}:{pin}" for i, pin in in_pins]
    parts += [f"O{mapping[i]}:{pin}" for i, pin in out_pins]
    parts.sort()
    return "|".join(parts)


@lru_cache(maxsize=1 << 18)
def canonicalize(
    types: tuple[str, ...],
    edges: tuple[LocalEdge, ...],
    in_pins: tuple[LocalPin, ...],
    out_pins: tuple[LocalPin, ...],
) -> tuple[str, tuple[int, ...]]:
    """Return ``(canonical_key, mapping)`` for a labelled pattern.

    ``mapping[i]`` is the canonical index assigned to local node ``i``.  All
    four arguments must be hashable tuples so the result can be memoised;
    ``edges``, ``in_pins`` and ``out_pins`` are expected to be sorted by the
    caller so that equivalent inputs share a cache entry.
    """
    n = len(types)
    if n == 0:
        return "", ()

    colors = _refine_colors(n, types, edges, in_pins, out_pins)

    # Group node indices by colour; colours are invariant, so the block order
    # is invariant too.  Only permutations *within* a block can change the key.
    blocks: dict[int, list[int]] = {}
    for idx, color in enumerate(colors):
        blocks.setdefault(color, []).append(idx)

    best_key: str | None = None
    best_mapping: tuple[int, ...] | None = None

    ordered_blocks = [blocks[c] for c in sorted(blocks)]
    for choice in product(*(permutations(block) for block in ordered_blocks)):
        mapping = [0] * n
        next_index = 0
        for permuted_block in choice:
            for node in permuted_block:
                mapping[node] = next_index
                next_index += 1
        candidate = _render(tuple(mapping), types, edges, in_pins, out_pins)
        if best_key is None or candidate < best_key:
            best_key = candidate
            best_mapping = tuple(mapping)

    assert best_key is not None and best_mapping is not None
    return best_key, best_mapping


def canonicalize_named(
    node_types: dict[str, str],
    internal_edges: list[tuple[str, str, str, str, str]],
    boundary_inputs: list[tuple[str, str, str]],
    boundary_outputs: list[tuple[str, str, str]],
) -> tuple[str, dict[str, int]]:
    """Canonicalise a pattern expressed with instance *names*.

    Returns ``(canonical_key, {instance_name: canonical_index})``.  Names are
    first replaced by their rank in sorted order so that the memoised
    :func:`canonicalize` sees a compact, name-independent problem.
    """
    names = sorted(node_types)
    local = {name: i for i, name in enumerate(names)}

    types = tuple(node_types[name] for name in names)
    edges = tuple(
        sorted(
            (local[src], src_pin, local[dst], dst_pin)
            for src, src_pin, dst, dst_pin, _ in internal_edges
        )
    )
    in_pins = tuple(sorted((local[inst], pin) for _, inst, pin in boundary_inputs))
    out_pins = tuple(sorted((local[inst], pin) for _, inst, pin in boundary_outputs))

    key, mapping = canonicalize(types, edges, in_pins, out_pins)
    return key, {name: mapping[local[name]] for name in names}
