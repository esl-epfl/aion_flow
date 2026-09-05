"""Enumerate and count recurring combinational patterns.

The miner answers one question: *which connected groups of up to ``max_size``
combinational cells appear again and again in this netlist?*

Three properties matter and each one is implemented deliberately here.

**Exactness.**  Subgraphs are enumerated with ESU (Wernicke's
*enumerate-subgraphs* algorithm).  ESU visits every connected subgraph exactly
once; a naive "grow the frontier" search visits ``{a,b,c}`` once per insertion
order and therefore over-counts occurrences by up to ``(k-1)!``, which silently
inflates the ``min_occurrences`` filter.

**Speed.**  Two things dominate the cost of the inner loop and both are
indexed away:

* boundary detection only looks at the pin edges incident to the candidate
  cells (via :attr:`~aion_opt.graph.builder.SignalFlowGraph.pin_edges_by_inst`)
  instead of scanning every edge in the design, and
* canonicalisation is memoised colour refinement rather than ``n!`` brute
  force (see :mod:`aion_opt.pattern.canonical`).

Everything inside the hot loop works on dense integer node ids, not on Python
strings.

**Parallelism.**  ESU partitions naturally by root node, so roots are split
into interleaved chunks and mined in worker processes.  Workers inherit the
read-only graph through ``fork`` -- nothing large is pickled -- and return
compact ``{canonical key: [node-id tuples]}`` maps that the parent merges.  The
result is independent of the number of workers.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Iterable, Sequence

from aion_opt.pattern.canonical import canonicalize
from aion_opt.pattern.subgraph import Pattern, build_pattern

if TYPE_CHECKING:
    from aion_opt.graph.builder import SignalFlowGraph
    from aion_opt.graph.circuit import Circuit
    from aion_opt.io.cell_lib import CellLib


#: Hard ceiling on the pattern size.  Canonicalisation brute-forces the
#: relabellings inside each colour class, so a fully symmetric pattern of this
#: size is still tractable while anything larger is not.
MAX_SUPPORTED_PATTERN_SIZE = 8


# ---------------------------------------------------------------------------
# Compact, fork-shareable view of the signal-flow graph
# ---------------------------------------------------------------------------
@dataclass
class MiningGraph:
    """Integer-indexed projection of a :class:`SignalFlowGraph`.

    Node ids are assigned by sorted instance name, which makes every result
    deterministic and independent of dictionary iteration order.
    """

    names: list[str]
    types: list[str]
    adj: list[tuple[int, ...]]
    edge_src: list[int]  # node id, or -1 when outside the combinational graph
    edge_dst: list[int]
    edge_src_pin: list[str]
    edge_dst_pin: list[str]
    edge_net: list[str]
    node_edges: list[tuple[int, ...]]

    @property
    def order(self) -> int:
        return len(self.names)

    @classmethod
    def from_sfg(cls, sfg: "SignalFlowGraph") -> "MiningGraph":
        names = sorted(sfg.node_types)
        node_id = {name: i for i, name in enumerate(names)}
        types = [sfg.node_types[name] for name in names]

        adj: list[tuple[int, ...]] = []
        for name in names:
            neighbours = {
                node_id[n] for n in sfg.neighbors(name) if n in node_id
            }
            neighbours.discard(node_id[name])
            adj.append(tuple(sorted(neighbours)))

        edge_src: list[int] = []
        edge_dst: list[int] = []
        edge_src_pin: list[str] = []
        edge_dst_pin: list[str] = []
        edge_net: list[str] = []
        node_edges: list[list[int]] = [[] for _ in names]

        for src, src_pin, dst, dst_pin, net in sfg.pin_edges:
            s = node_id.get(src, -1)
            d = node_id.get(dst, -1)
            if s < 0 and d < 0:
                continue
            idx = len(edge_src)
            edge_src.append(s)
            edge_dst.append(d)
            edge_src_pin.append(src_pin)
            edge_dst_pin.append(dst_pin)
            edge_net.append(net)
            if s >= 0:
                node_edges[s].append(idx)
            if d >= 0:
                node_edges[d].append(idx)

        return cls(
            names=names,
            types=types,
            adj=adj,
            edge_src=edge_src,
            edge_dst=edge_dst,
            edge_src_pin=edge_src_pin,
            edge_dst_pin=edge_dst_pin,
            edge_net=edge_net,
            node_edges=[tuple(e) for e in node_edges],
        )


@dataclass
class MiningResult:
    """Outcome of a mining run.

    ``occurrences`` maps a canonical key to every occurrence of that pattern,
    each occurrence being a sorted tuple of instance names.  Full
    :class:`Pattern` objects are materialised lazily (see
    :meth:`representative`) because a design can easily produce millions of
    occurrences and only a few thousand distinct patterns.
    """

    occurrences: dict[str, list[tuple[str, ...]]] = field(default_factory=dict)
    subgraphs_enumerated: int = 0
    patterns_before_filters: int = 0
    _representatives: dict[str, Pattern] = field(default_factory=dict, repr=False)
    _circuit: "Circuit | None" = field(default=None, repr=False)
    _sfg: "SignalFlowGraph | None" = field(default=None, repr=False)
    _collapse: Callable[[str], str] | None = field(default=None, repr=False)

    def bind(
        self,
        circuit: "Circuit",
        sfg: "SignalFlowGraph",
        collapse: Callable[[str], str],
    ) -> None:
        """Attach the circuit needed to rebuild :class:`Pattern` objects."""
        self._circuit = circuit
        self._sfg = sfg
        self._collapse = collapse

    def total_occurrences(self) -> int:
        return sum(len(v) for v in self.occurrences.values())

    def pattern_for(self, instances: Sequence[str]) -> Pattern:
        """Materialise the full :class:`Pattern` for one occurrence."""
        assert self._circuit is not None and self._sfg is not None
        assert self._collapse is not None
        inst_set = frozenset(instances)
        return build_pattern(
            self._circuit,
            inst_set,
            self._collapse,
            self._sfg.edges_for_instances(set(inst_set)),
        )

    def representative(self, key: str) -> Pattern:
        """Return (and cache) a representative :class:`Pattern` for ``key``."""
        cached = self._representatives.get(key)
        if cached is None:
            cached = self.pattern_for(self.occurrences[key][0])
            self._representatives[key] = cached
        return cached

    def patterns(self) -> dict[str, list[Pattern]]:
        """Materialise every occurrence as a :class:`Pattern`.

        Convenience for tests and small designs; prefer
        :meth:`representative` plus :attr:`occurrences` on real netlists.
        """
        return {
            key: [self.pattern_for(occ) for occ in occs]
            for key, occs in self.occurrences.items()
        }


# ---------------------------------------------------------------------------
# ESU enumeration
# ---------------------------------------------------------------------------
def _mine_roots(
    graph: MiningGraph,
    roots: Iterable[int],
    max_size: int,
    max_outputs: int | None,
    max_inputs: int | None,
) -> tuple[dict[str, list[tuple[int, ...]]], int]:
    """Mine every connected subgraph whose lowest-id node is one of ``roots``.

    Returns ``({canonical key: [node-id tuples]}, subgraphs_enumerated)``.
    """
    adj = graph.adj
    node_edges = graph.node_edges
    edge_src = graph.edge_src
    edge_dst = graph.edge_dst
    edge_src_pin = graph.edge_src_pin
    edge_dst_pin = graph.edge_dst_pin
    types = graph.types

    found: dict[str, list[tuple[int, ...]]] = defaultdict(list)
    enumerated = 0

    def record(sub: list[int]) -> None:
        """Classify one connected subgraph and file it under its pattern key."""
        nonlocal enumerated
        enumerated += 1

        nodes = sorted(sub)
        node_set = set(nodes)
        local = {node: i for i, node in enumerate(nodes)}

        edge_ids: set[int] = set()
        for node in nodes:
            edge_ids.update(node_edges[node])

        internal: set[tuple[int, str, int, str]] = set()
        boundary_in: set[tuple[int, str]] = set()
        boundary_out: set[tuple[int, str]] = set()
        for eid in edge_ids:
            src = edge_src[eid]
            dst = edge_dst[eid]
            src_in = src in node_set
            dst_in = dst in node_set
            if src_in and dst_in:
                internal.add(
                    (local[src], edge_src_pin[eid], local[dst], edge_dst_pin[eid])
                )
            elif src_in:
                boundary_out.add((local[src], edge_src_pin[eid]))
            elif dst_in:
                boundary_in.add((local[dst], edge_dst_pin[eid]))

        if max_outputs is not None and len(boundary_out) > max_outputs:
            return
        if max_inputs is not None and len(boundary_in) > max_inputs:
            return

        key, _ = canonicalize(
            tuple(types[node] for node in nodes),
            tuple(sorted(internal)),
            tuple(sorted(boundary_in)),
            tuple(sorted(boundary_out)),
        )
        found[key].append(tuple(nodes))

    def extend(sub: list[int], ext: list[int], closed: set[int], root: int) -> None:
        if len(sub) >= 2:
            record(sub)
        if len(sub) >= max_size:
            return
        # ESU: each extension candidate is consumed before recursing, which is
        # what guarantees every connected subgraph is visited exactly once.
        remaining = list(ext)
        while remaining:
            w = remaining.pop()
            exclusive = [u for u in adj[w] if u > root and u not in closed]
            sub.append(w)
            extend(
                sub,
                remaining + exclusive,
                closed | set(adj[w]) | {w},
                root,
            )
            sub.pop()

    for root in roots:
        neighbours = adj[root]
        extend(
            [root],
            [u for u in neighbours if u > root],
            set(neighbours) | {root},
            root,
        )

    return dict(found), enumerated


# ---------------------------------------------------------------------------
# Parallel driver
# ---------------------------------------------------------------------------
#: Set in the parent before the worker pool forks; inherited read-only.
_WORKER_GRAPH: MiningGraph | None = None
_WORKER_ARGS: tuple[int, int | None, int | None] = (3, None, None)


def _worker(roots: tuple[int, ...]) -> tuple[dict[str, list[tuple[int, ...]]], int]:
    assert _WORKER_GRAPH is not None
    max_size, max_outputs, max_inputs = _WORKER_ARGS
    return _mine_roots(_WORKER_GRAPH, roots, max_size, max_outputs, max_inputs)


def resolve_jobs(jobs: int | None) -> int:
    """Return the worker count to use.

    ``None`` or ``0`` means "every available core"; a negative value means
    "every core but ``-jobs``".  The result is always at least 1.
    """
    available = os.cpu_count() or 1
    if jobs is None or jobs == 0:
        return available
    if jobs < 0:
        return max(1, available + jobs)
    return max(1, jobs)


def mine_patterns(
    circuit: "Circuit",
    sfg: "SignalFlowGraph",
    cell_lib: "CellLib",
    max_size: int = 3,
    min_occurrences: int = 2,
    max_outputs: int | None = None,
    max_inputs: int | None = None,
    jobs: int | None = None,
    progress: bool = True,
) -> MiningResult:
    """Mine connected combinational patterns of 2..``max_size`` cells.

    Parameters
    ----------
    max_size:
        Largest number of standard cells a pattern may contain.
    min_occurrences:
        Patterns seen fewer times than this are dropped.
    max_outputs, max_inputs:
        Optional caps on the number of boundary ports of a pattern.  Growing a
        pattern can absorb a boundary output as easily as create one, so these
        cannot prune the enumeration itself; they are checked before
        canonicalisation and before anything is stored, which is where the cost
        actually is.
    jobs:
        Worker processes; see :func:`resolve_jobs`.  ``1`` runs in-process.
    progress:
        Print a one-line progress indicator to stderr.
    """
    if max_size < 2:
        raise ValueError("max_size must be at least 2")
    if max_size > MAX_SUPPORTED_PATTERN_SIZE:
        raise ValueError(
            f"max_size must be at most {MAX_SUPPORTED_PATTERN_SIZE}"
        )
    if min_occurrences < 1:
        raise ValueError("min_occurrences must be at least 1")
    if max_outputs is not None and max_outputs < 1:
        raise ValueError("max_outputs must be at least 1")
    if max_inputs is not None and max_inputs < 1:
        raise ValueError("max_inputs must be at least 1")

    graph = MiningGraph.from_sfg(sfg)
    n_jobs = resolve_jobs(jobs)
    # The progress line rewrites itself with \r, which is only readable on a
    # terminal; in a log it would be one huge line.
    progress = progress and sys.stderr.isatty()

    merged: dict[str, list[tuple[int, ...]]] = defaultdict(list)
    enumerated = 0

    if n_jobs <= 1 or graph.order < 2 * n_jobs:
        partial, count = _mine_roots(
            graph, range(graph.order), max_size, max_outputs, max_inputs
        )
        for key, occs in partial.items():
            merged[key].extend(occs)
        enumerated += count
    else:
        # Interleaved chunks: ESU work per root is very uneven, and striding
        # spreads the expensive high-degree roots across all workers.
        n_chunks = min(graph.order, n_jobs * 8)
        chunks = [
            tuple(range(start, graph.order, n_chunks)) for start in range(n_chunks)
        ]
        chunks = [c for c in chunks if c]

        global _WORKER_GRAPH, _WORKER_ARGS
        _WORKER_GRAPH = graph
        _WORKER_ARGS = (max_size, max_outputs, max_inputs)
        try:
            ctx = mp.get_context("fork")
            with ctx.Pool(processes=n_jobs) as pool:
                for done, (partial, count) in enumerate(
                    pool.imap_unordered(_worker, chunks), start=1
                ):
                    for key, occs in partial.items():
                        merged[key].extend(occs)
                    enumerated += count
                    if progress:
                        print(
                            f"\r[mine] {done}/{len(chunks)} chunks, "
                            f"{enumerated} subgraph(s), {len(merged)} pattern(s)",
                            end="",
                            file=sys.stderr,
                            flush=True,
                        )
        finally:
            _WORKER_GRAPH = None
        if progress:
            print("", file=sys.stderr)

    patterns_before_filters = len(merged)

    names = graph.names
    occurrences = {
        key: sorted(tuple(names[i] for i in occ) for occ in occs)
        for key, occs in merged.items()
        if len(occs) >= min_occurrences
    }

    result = MiningResult(
        occurrences=occurrences,
        subgraphs_enumerated=enumerated,
        patterns_before_filters=patterns_before_filters,
    )
    result.bind(circuit, sfg, cell_lib.collapse_name)
    return result
