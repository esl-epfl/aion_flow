"""Parse SPICE netlists into a structured representation.

The parser understands:

* ``.subckt`` / ``.ends`` blocks.
* Comment lines starting with ``*`` or ``;``.
* SPICE line continuations starting with ``+``.
* MOSFET devices, either as classic ``M`` lines or as the
  ``XN... / XP...`` subcircuit calls used in the IHP SG13G2 library
  (detected by the model name containing ``nmos`` / ``pmos``).
* Subcircuit instances (``X...`` lines).

All numeric parameters are kept as strings so that the caller can decide
how to interpret units.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union


@dataclass
class Mosfet:
    """A single MOSFET transistor."""

    name: str
    drain: str
    gate: str
    source: str
    bulk: str
    model: str
    params: Dict[str, str] = field(default_factory=dict)

    @property
    def is_nmos(self) -> bool:
        return "nmos" in self.model.lower()

    @property
    def is_pmos(self) -> bool:
        return "pmos" in self.model.lower()


@dataclass
class SubcircuitInstance:
    """An instance of another ``.subckt``."""

    name: str
    pins: List[str]
    subckt_name: str
    params: Dict[str, str] = field(default_factory=dict)


Device = Union[Mosfet, SubcircuitInstance]


@dataclass
class Subcircuit:
    """One ``.subckt`` block."""

    name: str
    pins: List[str]
    devices: List[Device] = field(default_factory=list)

    @property
    def is_gate_definition(self) -> bool:
        """True if the subckt contains transistor devices."""
        return any(isinstance(d, Mosfet) for d in self.devices)

    @property
    def mosfets(self) -> List[Mosfet]:
        return [d for d in self.devices if isinstance(d, Mosfet)]

    @property
    def instances(self) -> List[SubcircuitInstance]:
        return [d for d in self.devices if isinstance(d, SubcircuitInstance)]


def _split_params(tokens: List[str]) -> Dict[str, str]:
    """Parse ``key=value`` tokens into a dictionary."""
    params: Dict[str, str] = {}
    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            params[key.strip()] = value.strip()
    return params


def _strip_inline_comment(line: str) -> str:
    """Drop a trailing ``$`` or ``;`` comment.

    Both are in-line comment markers in the common SPICE dialects, and they
    only count when they follow whitespace so a node called ``a;b`` survives.
    """
    for marker in ("$", ";"):
        index = line.find(f" {marker}")
        if index >= 0:
            line = line[:index]
    return line.rstrip()


def _preprocess(text: str) -> List[str]:
    """Strip comments, join continuations, and return logical lines."""
    logical: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # SPICE comments start with '*' or ';'
        if line.startswith("*") or line.startswith(";"):
            continue
        line = _strip_inline_comment(line)
        if not line:
            continue
        if line.startswith("+"):
            if logical:
                logical[-1] = (logical[-1].rstrip() + " " + line[1:].strip()).strip()
        else:
            logical.append(line)
    return logical


def _looks_like_mosfet_model(name: str) -> bool:
    lowered = name.lower()
    return "nmos" in lowered or "pmos" in lowered


def _parse_mosfet_line(tokens: List[str]) -> Mosfet:
    """Parse a classic ``M`` device line."""
    # Mname drain gate source bulk model [params...]
    return Mosfet(
        name=tokens[0],
        drain=tokens[1],
        gate=tokens[2],
        source=tokens[3],
        bulk=tokens[4],
        model=tokens[5],
        params=_split_params(tokens[6:]),
    )


def _parse_x_device(tokens: List[str]) -> Union[Mosfet, SubcircuitInstance]:
    """Parse an ``X...`` line.

    If the called subcircuit/model name contains ``nmos`` or ``pmos`` the line
    is treated as a MOSFET (the SG13G2 style ``XN0 ... sg13_lv_nmos``).
    Otherwise it is a subcircuit instance.
    """
    name = tokens[0]

    # The model/subcircuit name is the last token that does not contain '='.
    # Everything after it are ``key=value`` parameters.
    plain = [i for i in range(1, len(tokens)) if "=" not in tokens[i]]
    if not plain:
        raise ValueError(
            f"X-device {name!r} names no subcircuit or model: {' '.join(tokens)}"
        )
    model_index = max(plain)
    model_or_subckt = tokens[model_index]
    pin_tokens = tokens[1:model_index]
    params = _split_params(tokens[model_index + 1 :])

    if _looks_like_mosfet_model(model_or_subckt):
        # XN... drain gate source bulk model [params...]
        if len(pin_tokens) < 4:
            raise ValueError(
                f"MOSFET-like X-device {name!r} has too few nodes: {tokens}"
            )
        return Mosfet(
            name=name,
            drain=pin_tokens[0],
            gate=pin_tokens[1],
            source=pin_tokens[2],
            bulk=pin_tokens[3],
            model=model_or_subckt,
            params=params,
        )

    return SubcircuitInstance(
        name=name,
        pins=list(pin_tokens),
        subckt_name=model_or_subckt,
        params=params,
    )


def parse_spice(text: str) -> Dict[str, Subcircuit]:
    """Return a mapping ``subckt_name -> Subcircuit`` for all ``.subckt`` blocks."""
    lines = _preprocess(text)
    subckts: Dict[str, Subcircuit] = {}
    current: Subcircuit | None = None

    for line in lines:
        tokens = line.split()
        if not tokens:
            continue
        directive = tokens[0].lower()

        if directive == ".subckt":
            if len(tokens) < 2:
                raise ValueError(f"Malformed .subckt line: {line!r}")
            if current is not None:
                raise ValueError(
                    f"Nested .subckt {tokens[1]!r} inside {current.name!r}: "
                    f"the enclosing block is missing its .ends"
                )
            # Trailing ``key=value`` tokens are subcircuit parameters, not pins.
            pins: List[str] = []
            for token in tokens[2:]:
                if "=" in token:
                    break
                pins.append(token)
            current = Subcircuit(name=tokens[1], pins=pins)

        elif directive == ".ends":
            if current is not None:
                if current.name in subckts:
                    raise ValueError(
                        f"Duplicate .subckt {current.name!r} in the same file"
                    )
                subckts[current.name] = current
                current = None

        elif directive.startswith("m") and current is not None:
            if len(tokens) < 6:
                raise ValueError(f"Malformed MOSFET line: {line!r}")
            current.devices.append(_parse_mosfet_line(tokens))

        elif directive.startswith("x") and current is not None:
            current.devices.append(_parse_x_device(tokens))

    if current is not None:
        raise ValueError(f"Unclosed .subckt block: {current.name!r}")

    return subckts


def parse_spice_file(path: Path | str) -> Dict[str, Subcircuit]:
    """Parse a SPICE file from disk."""
    return parse_spice(Path(path).read_text())
