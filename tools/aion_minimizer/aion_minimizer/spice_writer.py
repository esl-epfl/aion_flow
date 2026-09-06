"""Emit transistor-level SPICE netlists.

Every generator in the tool produces a list of :class:`Mosfet`, so the writer
only has to lay out one ``.subckt`` around them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from aion_minimizer.spice_parser import Mosfet

#: Parameters are emitted in this order when present, then the rest sorted.
_PARAM_ORDER = ("w", "l", "ng", "m", "ad", "as", "pd", "ps")


def format_device(mos: Mosfet) -> str:
    """Render one MOSFET line."""
    params = dict(mos.params)
    ordered = [f"{key}={params.pop(key)}" for key in _PARAM_ORDER if key in params]
    ordered += [f"{key}={value}" for key, value in sorted(params.items())]
    return (
        f"{mos.name} {mos.drain} {mos.gate} {mos.source} {mos.bulk} {mos.model} "
        + " ".join(ordered)
    ).rstrip()


def write_subckt(
    subckt_name: str, ports: Sequence[str], devices: Sequence[Mosfet]
) -> str:
    """Return a ``.subckt`` block holding ``devices``.

    ``ports`` is emitted verbatim: SPICE binds subcircuit terminals by
    position, so the generated cell has to keep the pin order of the netlist it
    replaces or every instantiation of it is miswired.
    """
    lines = [f".subckt {subckt_name} {' '.join(ports)}"]
    lines.extend(f"    {format_device(mos)}" for mos in devices)
    lines.append(".ends")
    return "\n".join(lines) + "\n"


def write_subckt_to_file(path: str, *args, **kwargs) -> None:
    """Write :func:`write_subckt` output to ``path``."""
    Path(path).write_text(write_subckt(*args, **kwargs))
