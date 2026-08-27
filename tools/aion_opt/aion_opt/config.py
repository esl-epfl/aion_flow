"""Configuration dataclass and loading utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AionOptConfig:
    """Runtime configuration for aion_opt."""

    input_netlist: Path
    cell_lib: Path
    top_module: str | None = None
    max_pattern_size: int = 3
    min_occurrences: int = 2
    collapse_strengths: bool = True
    allow_overlapping: bool = False
    area_factor: float = 0.85
    output_dir: Path = field(default_factory=lambda: Path("out"))

    def __post_init__(self) -> None:
        if not (2 <= self.max_pattern_size <= 6):
            raise ValueError("max_pattern_size must be between 2 and 6")
        if self.min_occurrences < 2:
            raise ValueError("min_occurrences must be at least 2")
        if not (0.0 < self.area_factor <= 1.0):
            raise ValueError("area_factor must be in (0, 1]")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AionOptConfig":
        """Build a configuration from a plain dictionary."""
        mapped: dict[str, Any] = {}
        for key, value in data.items():
            if key in ("input_netlist", "cell_lib", "output_dir"):
                value = Path(value)
            mapped[key] = value
        return cls(**mapped)

    @classmethod
    def from_yaml(cls, path: Path) -> "AionOptConfig":
        """Load configuration from a YAML file."""
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            raise ValueError(f"YAML file {path} does not contain a mapping")
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the configuration to a plain dictionary."""
        return {
            "input_netlist": str(self.input_netlist),
            "cell_lib": str(self.cell_lib),
            "top_module": self.top_module,
            "max_pattern_size": self.max_pattern_size,
            "min_occurrences": self.min_occurrences,
            "collapse_strengths": self.collapse_strengths,
            "allow_overlapping": self.allow_overlapping,
            "area_factor": self.area_factor,
            "output_dir": str(self.output_dir),
        }
