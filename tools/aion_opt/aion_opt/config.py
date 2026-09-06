"""Configuration dataclass and loading utilities.

Every knob the CLI exposes also exists here, so a run can be described
entirely by a YAML file::

    input_netlist: examples/full_flow/tt_um_aion.nl.v
    top_module: tt_um_aion
    max_pattern_size: 4
    min_occurrences: 4
    max_outputs: 1
    cell_prefix: AION_
    elite_count: 20
    jobs: 0            # 0 = every core

Command-line arguments always win over config values.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

from aion_opt.cellgen.generator import DEFAULT_CELL_PREFIX
from aion_opt.pattern.miner import MAX_SUPPORTED_PATTERN_SIZE

#: Config keys that hold filesystem paths.
_PATH_FIELDS = {"input_netlist", "cell_lib", "output_dir", "work_dir"}


@dataclass
class AionOptConfig:
    """Runtime configuration for aion_opt."""

    input_netlist: Path
    cell_lib: Path
    top_module: str | None = None

    # Mining
    max_pattern_size: int = 3
    min_occurrences: int = 2
    max_outputs: int | None = None
    max_inputs: int | None = None
    collapse_strengths: bool = True
    jobs: int | None = None

    # Cover
    area_factor: float = 0.85
    allow_overlapping: bool = False
    min_selected_occurrences: int | None = None

    # Cell generation
    cell_prefix: str = DEFAULT_CELL_PREFIX
    elite_count: int | None = None
    elite_metric: str = "saved-area"
    #: Plan written by ``complement-plan``: which cell inputs take their
    #: complement on a ``<port>_bar`` port instead of an internal inverter.
    complement_plan: Path | None = None

    # Outputs
    output_dir: Path = field(default_factory=lambda: Path("out"))
    work_dir: Path | None = None

    def __post_init__(self) -> None:
        if not (2 <= self.max_pattern_size <= MAX_SUPPORTED_PATTERN_SIZE):
            raise ValueError(
                f"max_pattern_size must be between 2 and {MAX_SUPPORTED_PATTERN_SIZE}"
            )
        if self.min_occurrences < 1:
            raise ValueError("min_occurrences must be at least 1")
        if not (0.0 < self.area_factor <= 1.0):
            raise ValueError("area_factor must be in (0, 1]")
        if self.max_outputs is not None and self.max_outputs < 1:
            raise ValueError("max_outputs must be at least 1")
        if self.max_inputs is not None and self.max_inputs < 1:
            raise ValueError("max_inputs must be at least 1")
        if self.min_selected_occurrences is None:
            self.min_selected_occurrences = self.min_occurrences

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AionOptConfig":
        """Build a configuration from a plain dictionary.

        Unknown keys are rejected so that a typo in a YAML file is reported
        instead of silently ignored.
        """
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(
                f"unknown configuration key(s): {', '.join(sorted(unknown))}"
            )
        mapped = {
            key: Path(value) if key in _PATH_FIELDS and value is not None else value
            for key, value in data.items()
        }
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
        """Serialize the configuration to a JSON/YAML-friendly dictionary."""
        return {
            key: str(value) if isinstance(value, Path) else value
            for key, value in asdict(self).items()
        }
