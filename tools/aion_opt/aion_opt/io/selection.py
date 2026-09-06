"""Persist the mining + cover result so it can be reused between commands.

``generate-cells`` and ``rewrite`` need exactly the same mining result: the
first turns it into a cell library, the second substitutes it into the netlist.
Re-mining in ``rewrite`` doubles the runtime of the flow for no benefit, so
``generate-cells`` drops a *selection file* next to its other outputs and
``rewrite`` picks it up.

The file records a fingerprint of the inputs and of every mining parameter.
``rewrite`` only reuses a selection whose fingerprint matches what it was asked
to do; otherwise it silently falls back to mining, so a stale file can never
produce a wrong netlist.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Bumped whenever the on-disk layout or the canonical-key format changes.
SELECTION_FORMAT_VERSION = 2


def _file_fingerprint(path: Path) -> str:
    """Content hash of a file, or ``"missing"`` when it does not exist."""
    if not path.exists():
        return "missing"
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def compute_fingerprint(
    input_netlist: Path,
    cell_lib: Path,
    top_module: str | None,
    parameters: dict[str, Any],
) -> str:
    """Hash the inputs and parameters a mining run depends on."""
    payload = json.dumps(
        {
            "version": SELECTION_FORMAT_VERSION,
            "input": _file_fingerprint(Path(input_netlist)),
            "cell_lib": _file_fingerprint(Path(cell_lib)),
            "top": top_module,
            "parameters": parameters,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class Selection:
    """A cover, serialisable to JSON.

    ``occurrences`` are ordered pairs of ``(canonical key, instance names)``;
    ``module_names`` maps each key to the module ``generate-cells`` emitted for
    it.
    """

    fingerprint: str
    parameters: dict[str, Any] = field(default_factory=dict)
    module_names: dict[str, str] = field(default_factory=dict)
    occurrences: list[tuple[str, list[str]]] = field(default_factory=list)
    saved_area_per_occurrence: dict[str, float] = field(default_factory=dict)
    version: int = SELECTION_FORMAT_VERSION

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "version": self.version,
                    "fingerprint": self.fingerprint,
                    "parameters": self.parameters,
                    "module_names": self.module_names,
                    "saved_area_per_occurrence": self.saved_area_per_occurrence,
                    "occurrences": [
                        {"key": key, "instances": list(insts)}
                        for key, insts in self.occurrences
                    ],
                },
                fh,
                indent=2,
            )

    @classmethod
    def read(cls, path: Path) -> "Selection | None":
        """Load a selection file, returning ``None`` if it is absent or stale."""
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None
        if data.get("version") != SELECTION_FORMAT_VERSION:
            return None
        return cls(
            fingerprint=data.get("fingerprint", ""),
            parameters=data.get("parameters", {}),
            module_names=data.get("module_names", {}),
            saved_area_per_occurrence=data.get("saved_area_per_occurrence", {}),
            occurrences=[
                (entry["key"], list(entry["instances"]))
                for entry in data.get("occurrences", [])
            ],
            version=data["version"],
        )

    def matches(self, fingerprint: str) -> bool:
        return bool(self.fingerprint) and self.fingerprint == fingerprint
