"""Load and query the JSON technology dictionary."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SEQUENTIAL_KEYWORDS = {
    "dff",
    "dfrbp",
    "lat",
    "sdl",
    "sram",
    "scan",
}


class CellLib:
    """Wrapper around the sg13g2_stdcell.json tech dictionary."""

    def __init__(self, path: Path, collapse_strengths: bool = True) -> None:
        self.path = path
        self.collapse_strengths = collapse_strengths
        self.raw: dict[str, dict[str, Any]] = {}
        self.cells: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.raw = data.get("cells", data)
        for name, info in self.raw.items():
            key = self.collapse_name(name) if self.collapse_strengths else name
            # Keep the first (usually weakest / smallest) variant for the generic key.
            if key not in self.cells:
                self.cells[key] = {"name": name, **info}
            else:
                # Preserve the smallest area variant as the representative.
                if info.get("area", float("inf")) < self.cells[key].get(
                    "area", float("inf")
                ):
                    self.cells[key] = {"name": name, **info}

    @staticmethod
    def collapse_name(name: str) -> str:
        """Strip strength suffixes like `_1`, `_2` from standard-cell names."""
        # e.g. sg13g2_xor2_1 -> sg13g2_xor2
        if name.endswith("_1") or name.endswith("_2"):
            return name.rsplit("_", 1)[0]
        return name

    def __contains__(self, cell_type: str) -> bool:
        if cell_type in self.cells:
            return True
        return self.collapse_name(cell_type) in self.cells

    def info(self, cell_type: str) -> dict[str, Any]:
        """Return the full dictionary entry for a cell type."""
        if cell_type in self.cells:
            return self.cells[cell_type]
        # Try without strength suffix.
        collapsed = self.collapse_name(cell_type)
        return self.cells[collapsed]

    def area(self, cell_type: str) -> float:
        """Return the cell area, falling back to 0.0 if unknown."""
        try:
            return float(self.info(cell_type).get("area", 0.0))
        except KeyError:
            return 0.0

    def pins(self, cell_type: str) -> dict[str, str]:
        """Return pin name -> direction for a cell type."""
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

    def is_combinational(self, cell_type: str) -> bool:
        """Heuristic: a cell is combinational iff it is known and not sequential."""
        if cell_type not in self:
            return False
        base = cell_type.lower()
        return not any(kw in base for kw in SEQUENTIAL_KEYWORDS)

    def is_sequential(self, cell_type: str) -> bool:
        """Heuristic sequential-cell detection."""
        return cell_type in self and not self.is_combinational(cell_type)

    def known_cell_types(self) -> set[str]:
        return set(self.cells.keys())

    def combinational_types(self) -> set[str]:
        return {ct for ct in self.cells if self.is_combinational(ct)}

    def sequential_types(self) -> set[str]:
        return {ct for ct in self.cells if self.is_sequential(ct)}
