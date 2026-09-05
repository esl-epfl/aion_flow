"""Small shared types for the synthesis pipeline.

Costing itself lives where the decisions are made: per-stage device counts in
:mod:`aion_minimizer.decompose`, polarity accounting in
:mod:`aion_minimizer.minimizer`.  Keeping a second cost model here would just be
a second thing to keep in sync.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Inverter:
    """A CMOS inverter that produces one complemented signal."""

    input: str
    output: str
