# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Geometry measurements taken from a written GDS
# ================================================================

"""Measurements read out of the GDS the verification tools actually consumed.

Why not measure the generator instead
-------------------------------------

``scripts/evidence.py`` already describes the ``Cell`` object the model's module
returns, and it has to *run that module* to do it -- in a subprocess, under a
wall-clock limit, with stdout and stderr captured separately, because the code
being measured is the code being graded.

The curriculum needs the same numbers as a *gate exit criterion*, and an exit
criterion may not depend on running model-written code: the scorer is called
in-process by ``scripts/ledger.py`` immediately after grading, and one
``os._exit(0)`` in a generator would take the whole ledger down with it.

The GDS is the artifact Magic, KLayout and Netgen all read.  Measuring it needs
no model code, cannot hang, and cannot disagree with what the tools saw --
which is the property the curriculum is built on.

What is measured
----------------

``count_gate_crossings`` returns the number of distinct GatPoly-over-Activ
regions.  That is the number of transistors the geometry implements: a poly
stripe crossing both the NMOS and the PMOS active band is two devices, and the
merge makes it count as two because the bands are disjoint.  It is compared
against ``len(subckt.devices)`` to answer "is every transistor drawn?".
"""

from __future__ import annotations

import dataclasses as dc
from pathlib import Path
from typing import Optional

from .tech import Tech, sg13g2_tech

#: The two layers whose intersection is a transistor gate.
GATE_LAYER = "GatPoly"
CHANNEL_LAYER = "Activ"


@dc.dataclass(frozen=True)
class CrossingCount:
    """The result of one crossing measurement, including why it failed."""

    #: Number of distinct gate regions, or ``None`` when it could not be read.
    count: Optional[int]
    #: Empty when the measurement succeeded; otherwise why it did not.
    reason: str = ""

    def __bool__(self) -> bool:  # pragma: no cover - convenience only
        return self.count is not None


def count_gate_crossings(
    gds_path: Path | str,
    tech: Optional[Tech] = None,
    cell_name: Optional[str] = None,
) -> CrossingCount:
    """Count distinct GatPoly-over-Activ regions in ``gds_path``.

    Never raises.  A missing file, an unreadable one, a layout with no top cell
    or a missing KLayout binding all come back as ``count=None`` with a stated
    reason, because "we could not tell" must never be reported as a number the
    curriculum would then treat as a measurement.
    """
    tech = tech or sg13g2_tech
    path = Path(gds_path)

    if not path.is_file():
        return CrossingCount(None, f"no GDS at {path.name}")
    if path.stat().st_size == 0:
        return CrossingCount(None, f"{path.name} is empty")

    try:
        import klayout.db as pya
    except Exception as exc:  # pragma: no cover - klayout is a hard dependency
        return CrossingCount(None, f"klayout.db unavailable: {type(exc).__name__}: {exc}")

    try:
        gate = tech.get(GATE_LAYER)
        channel = tech.get(CHANNEL_LAYER)
    except Exception as exc:
        return CrossingCount(None, f"technology has no {GATE_LAYER}/{CHANNEL_LAYER}: {exc}")

    try:
        layout = pya.Layout()
        layout.read(str(path))
    except Exception as exc:
        return CrossingCount(None, f"cannot read {path.name}: {type(exc).__name__}: {exc}")

    top = None
    if cell_name:
        top = layout.cell(cell_name)
        if top is None:
            return CrossingCount(None, f"{path.name} has no cell named {cell_name}")
    else:
        try:
            top = layout.top_cell()
        except Exception as exc:
            return CrossingCount(None, f"{path.name} has no single top cell: {exc}")
    if top is None:
        return CrossingCount(None, f"{path.name} has no top cell")

    try:
        gate_region = pya.Region(top.begin_shapes_rec(layout.layer(*gate.gds_pair)))
        channel_region = pya.Region(top.begin_shapes_rec(layout.layer(*channel.gds_pair)))
        crossings = (gate_region & channel_region).merged()
        return CrossingCount(crossings.count())
    except Exception as exc:
        return CrossingCount(None, f"geometry error: {type(exc).__name__}: {exc}")


__all__ = ["CHANNEL_LAYER", "GATE_LAYER", "CrossingCount", "count_gate_crossings"]
