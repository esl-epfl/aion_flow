"""Select which mined pattern occurrences to actually replace.

Mining reports *all* occurrences, and they overlap heavily -- a single NAND
gate can be part of dozens of candidate patterns.  Covering picks a subset to
substitute.

Two rules drive the selection:

* **Disjointness.**  A standard cell can only be absorbed into one AION cell,
  so the greedy pass takes occurrences in decreasing order of saved area and
  skips any that touch an already-claimed instance.
* **Reusability.**  A pattern that survives the greedy pass only once forces a
  brand-new cell to be characterised and minimised for a single instantiation.
  ``min_selected_occurrences`` drops those patterns and re-runs the cover so
  their instances become available to patterns that *are* reused; this repeats
  until the selection is stable.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aion_opt.io.cell_lib import CellLib
    from aion_opt.pattern.miner import MiningResult


#: One chosen occurrence: its pattern key and the instances it absorbs.
Occurrence = tuple[str, tuple[str, ...]]

#: Maximum greedy/re-filter rounds before giving up on a stable fixpoint.
MAX_COVER_ITERATIONS = 20


@dataclass
class CoverResult:
    """The selected occurrences plus the bookkeeping behind them."""

    selected: list[Occurrence] = field(default_factory=list)
    counts: Counter[str] = field(default_factory=Counter)
    saved_area_per_occurrence: dict[str, float] = field(default_factory=dict)
    dropped_keys: set[str] = field(default_factory=set)
    iterations: int = 0

    @property
    def keys(self) -> list[str]:
        """Selected pattern keys, ordered by decreasing total saved area."""
        return sorted(
            self.counts,
            key=lambda k: (-self.total_saved_area(k), k),
        )

    def total_saved_area(self, key: str) -> float:
        """Estimated area saved across every selected occurrence of ``key``."""
        return self.saved_area_per_occurrence.get(key, 0.0) * self.counts[key]

    def total_saved_area_all(self) -> float:
        return sum(self.total_saved_area(k) for k in self.counts)


def pattern_area(node_types: dict[str, str], cell_lib: "CellLib") -> float:
    """Sum of the standard-cell areas making up a pattern."""
    return sum(cell_lib.area(ct) for ct in node_types.values())


def _saved_area_per_key(
    mining: "MiningResult",
    cell_lib: "CellLib",
    area_factor: float,
) -> dict[str, float]:
    """Estimated area saved by replacing one occurrence of each pattern.

    The generated AION cell is assumed to cost ``area_factor`` times the sum of
    the standard cells it replaces, so the saving is the remaining fraction.
    """
    saved: dict[str, float] = {}
    for key in mining.occurrences:
        original = pattern_area(mining.representative(key).node_types, cell_lib)
        saved[key] = original * (1.0 - area_factor)
    return saved


def select_cover(
    mining: "MiningResult",
    cell_lib: "CellLib",
    area_factor: float = 0.85,
    allow_overlapping: bool = False,
    min_selected_occurrences: int = 2,
) -> CoverResult:
    """Return a greedy, non-overlapping cover maximising total saved area.

    Parameters
    ----------
    mining:
        Result of :func:`~aion_opt.pattern.miner.mine_patterns`.
    area_factor:
        Assumed area of an AION cell relative to the cells it replaces.
    allow_overlapping:
        Keep every occurrence instead of enforcing disjointness.  Only useful
        for analysis -- the netlist cannot be rewritten from an overlapping
        cover.
    min_selected_occurrences:
        Drop patterns that survive the cover fewer times than this and re-run
        the cover.  ``1`` disables the re-filter.
    """
    saved_per_occ = _saved_area_per_key(mining, cell_lib, area_factor)

    # A pattern that saves nothing is never worth a dedicated cell.
    candidates = {k for k, s in saved_per_occ.items() if s > 0.0}
    dropped: set[str] = set(mining.occurrences) - candidates

    result = CoverResult(saved_area_per_occurrence=saved_per_occ)

    for iteration in range(1, MAX_COVER_ITERATIONS + 1):
        if not candidates:
            result.iterations = iteration
            result.dropped_keys = dropped
            return result

        # Highest saving first; ties broken deterministically so runs are
        # reproducible regardless of dict ordering.
        scored = sorted(
            (
                (-saved_per_occ[key], key, occ)
                for key in candidates
                for occ in mining.occurrences[key]
            ),
        )

        selected: list[Occurrence] = []
        used: set[str] = set()
        for _, key, occ in scored:
            if allow_overlapping:
                selected.append((key, occ))
                continue
            if used.isdisjoint(occ):
                selected.append((key, occ))
                used.update(occ)

        counts = Counter(key for key, _ in selected)
        weak = {k for k in candidates if counts[k] < min_selected_occurrences}

        if not weak:
            result.selected = selected
            result.counts = counts
            result.dropped_keys = dropped
            result.iterations = iteration
            return result

        if weak == candidates:
            # Everything looks weak, which usually means one high-scoring
            # pattern is claiming instances that several reusable patterns
            # need.  Dropping the whole set would throw the cover away, so
            # blame the greediest pattern and try again.
            weak = {max(weak, key=lambda k: (saved_per_occ[k], k))}

        dropped |= weak
        candidates -= weak

    # Fixpoint not reached within the iteration budget: keep the last cover.
    result.selected = selected
    result.counts = counts
    result.dropped_keys = dropped
    result.iterations = MAX_COVER_ITERATIONS
    return result
