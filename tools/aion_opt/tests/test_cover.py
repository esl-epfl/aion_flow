"""Cover selection: disjointness, reusability re-filter and determinism."""

from __future__ import annotations

from dataclasses import dataclass

from aion_opt.pattern.cover import select_cover


@dataclass
class _FakeCellLib:
    """Minimal stand-in: every cell has unit area."""

    areas: dict[str, float]

    def area(self, cell_type: str) -> float:
        return self.areas.get(cell_type, 1.0)


class _FakePattern:
    def __init__(self, types: dict[str, str]) -> None:
        self.node_types = types


class _FakeMining:
    """Just enough of MiningResult for the cover to run."""

    def __init__(self, occurrences: dict[str, list[tuple[str, ...]]], types) -> None:
        self.occurrences = occurrences
        self._types = types

    def representative(self, key: str) -> _FakePattern:
        return _FakePattern(self._types[key])


def _mining(occurrences, types=None):
    types = types or {
        key: {inst: "cell" for inst in occurrences[key][0]} for key in occurrences
    }
    return _FakeMining(occurrences, types)


LIB = _FakeCellLib({})


def test_cover_is_disjoint():
    mining = _mining({"k": [("a", "b"), ("b", "c"), ("d", "e")]})
    cover = select_cover(mining, LIB, area_factor=0.5, min_selected_occurrences=1)

    used: set[str] = set()
    for _, occ in cover.selected:
        assert used.isdisjoint(occ)
        used.update(occ)


def test_weak_patterns_are_dropped_and_the_cover_is_redone():
    """`rare` wins the first pass but is used once, so `common` takes over."""
    mining = _mining(
        {
            "rare": [("a", "b", "c")],
            "common": [("a", "b"), ("c", "d"), ("e", "f")],
        },
        types={
            "rare": {"a": "big", "b": "big", "c": "big"},
            "common": {"a": "small", "b": "small"},
        },
    )
    lib = _FakeCellLib({"big": 10.0, "small": 1.0})

    lax = select_cover(mining, lib, area_factor=0.5, min_selected_occurrences=1)
    assert lax.counts["rare"] == 1

    strict = select_cover(mining, lib, area_factor=0.5, min_selected_occurrences=2)
    assert "rare" not in strict.counts
    assert "rare" in strict.dropped_keys
    assert strict.counts["common"] == 3


def test_patterns_that_save_nothing_are_dropped():
    mining = _mining({"k": [("a", "b"), ("c", "d")]})
    cover = select_cover(mining, LIB, area_factor=1.0, min_selected_occurrences=1)
    assert not cover.selected
    assert cover.dropped_keys == {"k"}


def test_selection_is_deterministic():
    occurrences = {
        "k1": [("a", "b"), ("c", "d")],
        "k2": [("b", "c"), ("e", "f")],
    }
    first = select_cover(_mining(occurrences), LIB, min_selected_occurrences=1)
    second = select_cover(_mining(occurrences), LIB, min_selected_occurrences=1)
    assert first.selected == second.selected


def test_allow_overlapping_keeps_everything():
    mining = _mining({"k": [("a", "b"), ("b", "c")]})
    cover = select_cover(
        mining, LIB, allow_overlapping=True, min_selected_occurrences=1
    )
    assert len(cover.selected) == 2


def test_ranking_orders_by_total_saved_area():
    mining = _mining(
        {
            "small": [("a", "b"), ("c", "d")],
            "big": [("e", "f"), ("g", "h")],
        },
        types={
            "small": {"a": "small", "b": "small"},
            "big": {"e": "big", "f": "big"},
        },
    )
    lib = _FakeCellLib({"small": 1.0, "big": 10.0})
    cover = select_cover(mining, lib, area_factor=0.5, min_selected_occurrences=1)
    assert cover.keys[0] == "big"
    assert cover.total_saved_area("big") > cover.total_saved_area("small")
