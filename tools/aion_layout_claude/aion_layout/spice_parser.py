# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Minimal SPICE subckt parser for SG13G2 cells
# ================================================================

"""Parse IHP SG13G2-style standard-cell SPICE netlists into Python objects.

The parser is intentionally small: it only understands ``.subckt`` blocks and
MOSFET instances of the form used by the PDK standard cells:

    XN0 Y A VSS VSS sg13_lv_nmos w=740.00n l=130.00n ng=1 m=1

Non-MOSFET devices and parameters not relevant to layout are ignored.
"""

from __future__ import annotations

import dataclasses as dc
import re
from pathlib import Path
from typing import Dict, List, Optional, Set


class SpiceParseError(ValueError):
    """Raised when a SPICE file cannot be parsed."""


@dc.dataclass(frozen=True)
class Mosfet:
    """A single MOSFET instance inside a subckt."""

    name: str
    model: str
    drain: str
    gate: str
    source: str
    bulk: str
    width_nm: float
    length_nm: float
    fingers: int = 1
    multiplier: int = 1

    @property
    def is_nmos(self) -> bool:
        return "nmos" in self.model.lower()

    @property
    def is_pmos(self) -> bool:
        return "pmos" in self.model.lower()


@dc.dataclass(frozen=True)
class Subckt:
    """A parsed SPICE subcircuit."""

    name: str
    pins: List[str]
    devices: List[Mosfet]

    @property
    def nets(self) -> Set[str]:
        """Return the set of all node names used by devices."""
        result: Set[str] = set()
        for d in self.devices:
            result.update((d.drain, d.gate, d.source, d.bulk))
        return result

    @property
    def nmos_devices(self) -> List[Mosfet]:
        return [d for d in self.devices if d.is_nmos]

    @property
    def pmos_devices(self) -> List[Mosfet]:
        return [d for d in self.devices if d.is_pmos]

    def devices_on_net(self, net: str) -> List[Mosfet]:
        """Return all devices connected to ``net`` at drain/source/bulk/gate."""
        return [
            d
            for d in self.devices
            if net in (d.drain, d.gate, d.source, d.bulk)
        ]

    def net_is_input(self, net: str) -> bool:
        """Return True if ``net`` is an external pin that is not VDD/VSS/Y."""
        return net in self.pins and net not in {"VDD", "VSS"}

    @property
    def vdd_net(self) -> Optional[str]:
        for pin in self.pins:
            if pin.upper() == "VDD":
                return pin
        return None

    @property
    def vss_net(self) -> Optional[str]:
        for pin in self.pins:
            if pin.upper() == "VSS":
                return pin
        return None

    @property
    def input_nets(self) -> List[str]:
        """Return external input pins (everything except rails and output)."""
        rails = {self.vdd_net, self.vss_net}
        # Heuristic: the output is the only external pin connected to both a
        # PMOS drain and an NMOS drain.
        out = self.output_net
        return [p for p in self.pins if p not in rails and p != out]

    @property
    def output_net(self) -> Optional[str]:
        """Guess the output net.

        The output is the external pin that is connected to at least one PMOS
        drain and at least one NMOS drain.
        """
        candidates: Set[str] = set()
        for pin in self.pins:
            if pin in (self.vdd_net, self.vss_net):
                continue
            has_pmos_drain = any(d.drain == pin for d in self.pmos_devices)
            has_nmos_drain = any(d.drain == pin for d in self.nmos_devices)
            if has_pmos_drain and has_nmos_drain:
                candidates.add(pin)
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates.pop()
        # If multiple candidates exist, prefer the one named Y or OUT.
        for name in ("Y", "OUT", "Q"):
            if name in candidates:
                return name
        return sorted(candidates)[0]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_SUBCKT_RE = re.compile(r"^\.subckt\s+(\S+)\s+(.*)$", re.IGNORECASE)
_ENDS_RE = re.compile(r"^\.ends\b", re.IGNORECASE)
_COMMENT_RE = re.compile(r"^\*")
_EMPTY_RE = re.compile(r"^\s*$")

# Suffixes for SPICE metric values (base unit is metre).
_METRIC_FACTORS: Dict[str, float] = {
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "µ": 1e-6,
    "m": 1e-3,
    "k": 1e3,
    "meg": 1e6,
    "g": 1e9,
}
_METRIC_RE = re.compile(r"^([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([a-zA-Zµ]*)$")


def _parse_metric(value: str) -> float:
    """Convert a SPICE metric string (e.g. ``740.00n``) to nanometres."""
    value = value.strip()
    match = _METRIC_RE.match(value)
    if not match:
        raise SpiceParseError(f"Cannot parse metric value: {value!r}")
    number = float(match.group(1))
    suffix = match.group(2).lower()
    factor = _METRIC_FACTORS.get(suffix, 1.0)
    metres = number * factor
    return metres * 1e9


def _parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise SpiceParseError(f"Cannot parse integer: {value!r}") from exc


def _parse_instance(line: str) -> Optional[Mosfet]:
    """Parse one MOSFET instance line, or return None if it is not a MOSFET."""
    tokens = line.split()
    if not tokens:
        return None

    name = tokens[0]
    if not name.upper().startswith("X"):
        return None

    # Separate parameters (key=value) from positional tokens.
    positional: List[str] = []
    params: Dict[str, str] = {}
    for token in tokens[1:]:
        if "=" in token:
            key, _, val = token.partition("=")
            params[key.lower()] = val
        else:
            if params:
                # Positional token after parameters: ignore (should not happen
                # in SG13G2 netlists, but be tolerant).
                continue
            positional.append(token)

    if len(positional) < 5:
        raise SpiceParseError(
            f"MOSFET instance {name!r} has too few positional tokens: {line!r}"
        )

    # Last positional token is the model; the four before it are D/G/S/B.
    *nodes, model = positional
    if len(nodes) != 4:
        raise SpiceParseError(
            f"MOSFET instance {name!r} expected 4 nodes, got {len(nodes)}: {line!r}"
        )

    try:
        width_nm = _parse_metric(params.get("w", "0"))
        length_nm = _parse_metric(params.get("l", "0"))
    except SpiceParseError as exc:
        raise SpiceParseError(f"In instance {name!r}: {exc}") from exc

    fingers = _parse_int(params.get("ng", "1")) if "ng" in params else 1
    multiplier = _parse_int(params.get("m", "1")) if "m" in params else 1

    return Mosfet(
        name=name,
        model=model,
        drain=nodes[0],
        gate=nodes[1],
        source=nodes[2],
        bulk=nodes[3],
        width_nm=width_nm,
        length_nm=length_nm,
        fingers=fingers,
        multiplier=multiplier,
    )


def parse_spice(text: str) -> List[Subckt]:
    """Parse SPICE text and return all subcircuits found."""
    subckts: List[Subckt] = []
    current_name: Optional[str] = None
    current_pins: List[str] = []
    current_devices: List[Mosfet] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or _COMMENT_RE.match(line):
            continue

        subckt_match = _SUBCKT_RE.match(line)
        if subckt_match:
            if current_name is not None:
                raise SpiceParseError(
                    f"Nested subcircuits are not supported ({current_name})"
                )
            current_name = subckt_match.group(1)
            current_pins = subckt_match.group(2).split()
            current_devices = []
            continue

        if _ENDS_RE.match(line):
            if current_name is None:
                raise SpiceParseError(".ends without matching .subckt")
            subckts.append(
                Subckt(
                    name=current_name,
                    pins=current_pins,
                    devices=current_devices,
                )
            )
            current_name = None
            current_pins = []
            current_devices = []
            continue

        if current_name is not None:
            device = _parse_instance(line)
            if device is not None:
                current_devices.append(device)

    # Tolerate an unclosed trailing subcircuit.  Some upstream netlists are
    # extracted without a final .ends, but any complete subcircuit parsed
    # before it is still usable.
    if current_name is not None and not subckts:
        raise SpiceParseError(f"Unclosed subcircuit: {current_name}")

    return subckts


def parse_spice_file(path: Path | str) -> List[Subckt]:
    """Parse a SPICE file and return all subcircuits found."""
    return parse_spice(Path(path).read_text())


def parse_first_subckt(path: Path | str) -> Subckt:
    """Parse a SPICE file and return the first subcircuit.

    If the file contains an unclosed trailing subcircuit (common when a
    netlist has been truncated or extracted), the first complete subcircuit
    is still returned.
    """
    subckts = parse_spice_file(path)
    if not subckts:
        raise SpiceParseError(f"No subcircuit found in {path}")
    return subckts[0]


__all__ = [
    "SpiceParseError",
    "Mosfet",
    "Subckt",
    "parse_spice",
    "parse_spice_file",
    "parse_first_subckt",
]
