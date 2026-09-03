#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Objective score for one layout iteration
# ================================================================

"""Score one iteration from its raw verification artifacts.

Why a score at all
------------------

The loop used to advance unconditionally: whatever the model wrote became the
next iteration's starting point, whether it was better or worse than what it
replaced.  That is an unfiltered random walk, and a regression is permanent
because nothing remembers the better version.  A scalar lets the harness keep
the best layout seen and branch from it instead.

What is scored
--------------

Only things already on disk, all of them read through the same parsers the
grader uses, so the score can never disagree with the verdict:

===========================  =========================================
component                    meaning
===========================  =========================================
``buildable``                the module imported and produced a GDS
``device_delta``             |layout - schematic| summed per device type
``net_delta``                |layout nets - schematic nets|
``disconnected``             nodes netgen could not attach
``unmatched_pins``           ports that failed to match
``lvs_verdict``              match_uniquely > ... > no_final_result
``drc_violations``           Magic + KLayout, by rule
``degraded``                 an artifact that could not be trusted
===========================  =========================================

**Lower is better, and 0 means DRC- and LVS-clean.**  The weights are ordered,
not tuned: connectivity outranks DRC because a layout that implements the wrong
circuit cannot be repaired by moving geometry, and a degraded artifact scores
worse than a known-bad one because "we could not tell" must never look like
progress.
"""

from __future__ import annotations

import argparse
import dataclasses as dc
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aion_layout import verification as _v  # noqa: E402

#: Ordered weights.  Connectivity first: geometry cannot fix a wrong circuit.
W_DEVICE = 1000.0
W_NET = 200.0
W_DISCONNECTED = 150.0
W_UNMATCHED_PIN = 120.0
W_LVS_VERDICT = 500.0
W_DRC = 10.0
W_DEGRADED = 5000.0
W_UNBUILDABLE = 100000.0

#: Distance of each verdict from "match_uniquely", in verdict steps.
LVS_VERDICT_COST: Dict[str, float] = {
    "match_uniquely": 0.0,
    "match_with_warnings": 1.0,
    "failed_pin_matching": 2.0,
    "do_not_match": 3.0,
    "uncertain": 4.0,
    "no_final_result": 4.0,
}


@dc.dataclass
class Score:
    """One iteration's objective score and the components behind it."""

    total: float
    buildable: bool
    device_delta: int
    net_delta: int
    disconnected: int
    unmatched_pins: int
    lvs_verdict: str
    drc_violations: int
    drc_by_rule: Dict[str, int]
    degraded: List[str]
    notes: List[str]

    @property
    def clean(self) -> bool:
        """True only when nothing is wrong and nothing is unverified."""
        return self.total == 0.0

    def as_dict(self) -> Dict[str, object]:
        return dc.asdict(self)

    def summary(self) -> str:
        bits = [
            f"score={self.total:.0f}",
            f"devices±{self.device_delta}",
            f"nets±{self.net_delta}",
            f"disc={self.disconnected}",
            f"pins={self.unmatched_pins}",
            f"lvs={self.lvs_verdict}",
            f"drc={self.drc_violations}",
        ]
        if self.degraded:
            bits.append("degraded=" + ",".join(self.degraded))
        if not self.buildable:
            bits.append("UNBUILDABLE")
        return "  ".join(bits)


# Discovery is delegated to aion_layout.verification, which owns the canonical
# path rules.  A second implementation here is exactly how a scorer ends up
# disagreeing with the grader about what it is scoring.


def score_iteration(iter_dir: Path, cell: str) -> Score:
    """Score the iteration whose artifacts live under ``iter_dir``."""
    degraded: List[str] = []
    notes: List[str] = []

    gds = iter_dir / f"{cell}.gds"
    buildable = gds.is_file() and gds.stat().st_size > 0
    if not buildable:
        notes.append(f"no GDS at {gds.name}: the module did not build")

    # ---- DRC ------------------------------------------------------------
    drc_by_rule: Dict[str, int] = {}
    drc_total = 0

    try:
        magic_rpt = _v._find_magic_drc_report(iter_dir, cell)
    except Exception:
        magic_rpt = None
    if magic_rpt is None:
        degraded.append("magic-missing")
    else:
        try:
            magic = _v.parse_magic_drc_report(magic_rpt)
            if not getattr(magic, "available", True):
                degraded.append("magic-unavailable")
            for v in magic.violations:
                key = _rule_code(v.category)
                drc_by_rule[key] = drc_by_rule.get(key, 0) + 1
            drc_total += magic.error_count
        except Exception as exc:
            degraded.append("magic-unreadable")
            notes.append(f"magic: {type(exc).__name__}: {exc}")

    try:
        kl = _v.parse_klayout_reports(iter_dir, cell)
    except Exception as exc:
        kl = None
        degraded.append("klayout-unreadable")
        notes.append(f"klayout: {type(exc).__name__}: {exc}")
    if kl is not None:
        try:
            if not getattr(kl, "available", True):
                degraded.append("klayout-unavailable")
            if getattr(kl, "completeness", "") == getattr(_v, "COMPLETENESS_DEGRADED", "DEGRADED"):
                degraded.append("klayout-incomplete")
            for v in kl.violations:
                key = _rule_code(v.category)
                drc_by_rule[key] = drc_by_rule.get(key, 0) + 1
            drc_total += kl.error_count
        except Exception as exc:
            degraded.append("klayout-unreadable")
            notes.append(f"klayout counts: {type(exc).__name__}: {exc}")

    # ---- LVS ------------------------------------------------------------
    device_delta = 0
    net_delta = 0
    disconnected = 0
    unmatched = 0
    verdict = "no_final_result"

    try:
        lvs_out = _v._find_netgen_lvs_report(iter_dir, cell)
    except Exception:
        lvs_out = None
    if lvs_out is None:
        degraded.append("lvs-missing")
    else:
        try:
            report = _v.parse_netgen_lvs_report(lvs_out)
            verdict = getattr(report, "verdict", "uncertain")
            for _dev, (a, b) in (report.device_counts or {}).items():
                device_delta += abs(a - b)
            nets = getattr(report, "net_counts", None)
            if nets:
                net_delta = abs(nets[0] - nets[1])
            disconnected = len(getattr(report, "disconnected_nodes", []) or [])
            unmatched = len(getattr(report, "unmatched_pins", []) or [])
        except Exception as exc:
            degraded.append("lvs-unreadable")
            notes.append(f"netgen: {type(exc).__name__}: {exc}")

    total = (
        W_DEVICE * device_delta
        + W_NET * net_delta
        + W_DISCONNECTED * disconnected
        + W_UNMATCHED_PIN * unmatched
        + W_LVS_VERDICT * LVS_VERDICT_COST.get(verdict, 4.0)
        + W_DRC * drc_total
        + W_DEGRADED * len(degraded)
        + (0.0 if buildable else W_UNBUILDABLE)
    )

    return Score(
        total=total,
        buildable=buildable,
        device_delta=device_delta,
        net_delta=net_delta,
        disconnected=disconnected,
        unmatched_pins=unmatched,
        lvs_verdict=verdict,
        drc_violations=drc_total,
        drc_by_rule=dict(sorted(drc_by_rule.items())),
        degraded=degraded,
        notes=notes,
    )


def _rule_code(category: str) -> str:
    """Return the bracketed rule code from a category string, or the string."""
    if "(" in category and ")" in category:
        inner = category[category.rfind("(") + 1 : category.rfind(")")]
        if inner:
            return inner
    return category.strip("'\"") or "unknown"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Score one layout iteration.")
    parser.add_argument("--iter-dir", required=True)
    parser.add_argument("--cell", required=True)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)

    score = score_iteration(Path(args.iter_dir), args.cell)
    if args.json:
        print(json.dumps(score.as_dict(), indent=2, sort_keys=True))
    else:
        print(score.summary())
        for note in score.notes:
            print(f"  note: {note}")
        if score.drc_by_rule:
            print("  drc by rule: " + ", ".join(f"{k}={v}" for k, v in score.drc_by_rule.items()))
    # 0 means clean; 1 means scored but not clean.  Never an error path.
    return 0 if score.clean else 1


if __name__ == "__main__":
    sys.exit(main())
