"""Select a cover of pattern occurrences."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aion_opt.io.cell_lib import CellLib
    from aion_opt.pattern.subgraph import Pattern


@dataclass
class ScoredOccurrence:
    pattern_key: str
    instances: frozenset[str]
    saved_area: float
    representative: "Pattern"


def _occurrence_saved_area(
    pattern: "Pattern",
    cell_lib: "CellLib",
    area_factor: float,
) -> float:
    """Estimated saved area for one occurrence: old area - new area."""
    original_area = sum(
        cell_lib.area(cell_type) for cell_type in pattern.node_types.values()
    )
    new_area = area_factor * original_area
    return original_area - new_area


def select_cover(
    patterns: dict[str, list["Pattern"]],
    cell_lib: "CellLib",
    area_factor: float = 0.85,
    allow_overlapping: bool = False,
) -> list["Pattern"]:
    """Return a greedy cover of pattern occurrences maximizing total saved area.

    By default the cover is non-overlapping. Set ``allow_overlapping`` to True
    to keep every occurrence.
    """
    scored: list[ScoredOccurrence] = []
    for key, occurrences in patterns.items():
        for occ in occurrences:
            saved = _occurrence_saved_area(occ, cell_lib, area_factor)
            scored.append(
                ScoredOccurrence(
                    pattern_key=key,
                    instances=occ.instances,
                    saved_area=saved,
                    representative=occ,
                )
            )

    # Sort by descending saved area.
    scored.sort(key=lambda x: -x.saved_area)

    selected: list["Pattern"] = []
    used_instances: set[str] = set()

    for item in scored:
        if allow_overlapping:
            selected.append(item.representative)
            continue
        if item.instances.isdisjoint(used_instances):
            selected.append(item.representative)
            used_instances |= item.instances

    return selected
