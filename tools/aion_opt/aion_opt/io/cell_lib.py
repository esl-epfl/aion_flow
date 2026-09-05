"""Load and query the JSON technology dictionary.

The technology dictionary is a flat JSON mapping of standard-cell names to
``{"area": float, "pins": {name: direction}, "function": str}`` entries (see
``tech/tech_dict/sg13g2_stdcell.json``).  It may either be the mapping itself
or be wrapped in a top-level ``"cells"`` key.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


#: Substrings that mark a cell as sequential (flip-flop, latch, scan cell, ...).
SEQUENTIAL_KEYWORDS = {
    "dff",
    "dfrbp",
    "lat",
    "sdl",
    "sram",
    "scan",
    "dlh",
    "dll",
    "sdf",
    "lgcp",
}

#: Cells that carry no logic function and must never take part in a pattern.
NON_LOGIC_KEYWORDS = {
    "fill",
    "decap",
    "antenna",
    "sighold",
    "tap",
}

#: Trailing drive-strength suffix, e.g. ``sg13g2_buf_16`` -> ``sg13g2_buf``.
_STRENGTH_SUFFIX = re.compile(r"_\d+$")


@lru_cache(maxsize=None)
def collapse_cell_name(name: str) -> str:
    """Strip the trailing drive-strength suffix from a standard-cell name.

    ``sg13g2_xor2_1`` -> ``sg13g2_xor2``; ``sg13g2_buf_16`` -> ``sg13g2_buf``.
    Names without a numeric suffix (``sg13g2_tielo``) are returned unchanged.
    Note that only a *trailing* ``_<digits>`` group is removed, so the input
    count baked into a cell name (``sg13g2_and4``) is preserved.
    """
    return _STRENGTH_SUFFIX.sub("", name)


class CellLib:
    """Wrapper around a JSON technology dictionary.

    Parameters
    ----------
    path:
        Path to the JSON technology dictionary.
    collapse_strengths:
        When True (default) every drive-strength variant of a cell is folded
        onto a single generic key, and the smallest-area variant is kept as the
        representative used for area estimation and cell generation.
    """

    def __init__(self, path: Path, collapse_strengths: bool = True) -> None:
        self.path = Path(path)
        self.collapse_strengths = collapse_strengths
        self.raw: dict[str, dict[str, Any]] = {}
        self.cells: dict[str, dict[str, Any]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def _load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.raw = data.get("cells", data)
        for name, info in self.raw.items():
            key = self.collapse_name(name) if self.collapse_strengths else name
            if key not in self.cells:
                self.cells[key] = {"name": name, **info}
            elif info.get("area", float("inf")) < self.cells[key].get(
                "area", float("inf")
            ):
                # Keep the smallest-area variant as the representative.
                self.cells[key] = {"name": name, **info}

    # ------------------------------------------------------------------
    # Naming
    # ------------------------------------------------------------------
    def collapse_name(self, name: str) -> str:
        """Return the generic (strength-free) name for ``name``.

        When ``collapse_strengths`` is False the name is returned unchanged.
        """
        if not self.collapse_strengths:
            return name
        return collapse_cell_name(name)

    def concrete_name(self, cell_type: str) -> str:
        """Return the concrete PDK cell name used to instantiate ``cell_type``."""
        try:
            return str(self.info(cell_type).get("name", cell_type))
        except KeyError:
            return cell_type

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def __contains__(self, cell_type: str) -> bool:
        return cell_type in self.cells or self.collapse_name(cell_type) in self.cells

    def info(self, cell_type: str) -> dict[str, Any]:
        """Return the full dictionary entry for a cell type.

        Raises ``KeyError`` when the cell is unknown.
        """
        if cell_type in self.cells:
            return self.cells[cell_type]
        return self.cells[self.collapse_name(cell_type)]

    def area(self, cell_type: str) -> float:
        """Return the cell area, falling back to ``0.0`` if unknown."""
        try:
            return float(self.info(cell_type).get("area", 0.0))
        except KeyError:
            return 0.0

    def pins(self, cell_type: str) -> dict[str, str]:
        """Return ``pin name -> direction`` for a cell type."""
        try:
            return dict(self.info(cell_type).get("pins", {}))
        except KeyError:
            return {}

    def function(self, cell_type: str) -> str | None:
        """Return the Boolean function string if available."""
        try:
            return self.info(cell_type).get("function")
        except KeyError:
            return None

    def is_logic(self, cell_type: str) -> bool:
        """False for physical-only cells (fill, decap, antenna, tap, ...)."""
        base = self.collapse_name(cell_type).lower()
        return not any(kw in base for kw in NON_LOGIC_KEYWORDS)

    def is_combinational(self, cell_type: str) -> bool:
        """Heuristic: known, not sequential and not a physical-only filler."""
        if cell_type not in self:
            return False
        base = self.collapse_name(cell_type).lower()
        if any(kw in base for kw in SEQUENTIAL_KEYWORDS):
            return False
        return self.is_logic(cell_type)

    def is_sequential(self, cell_type: str) -> bool:
        """Heuristic sequential-cell detection."""
        if cell_type not in self:
            return False
        base = self.collapse_name(cell_type).lower()
        return any(kw in base for kw in SEQUENTIAL_KEYWORDS)

    def known_cell_types(self) -> set[str]:
        return set(self.cells.keys())

    def combinational_types(self) -> set[str]:
        return {ct for ct in self.cells if self.is_combinational(ct)}

    def sequential_types(self) -> set[str]:
        return {ct for ct in self.cells if self.is_sequential(ct)}
