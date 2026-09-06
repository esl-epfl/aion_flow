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
from aion_layout.layout_metrics import count_gate_crossings  # noqa: E402
from aion_layout.spice_parser import SpiceParseError, parse_spice_file  # noqa: E402

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

    # ---- curriculum signals -------------------------------------------
    # Measured, recorded and shown to the model, but deliberately NOT part of
    # ``total``.  The crossing count is how the curriculum's second rung knows
    # whether every transistor is drawn; the *objective* already charges for a
    # missing device through ``device_delta``, and charging twice would make one
    # defect outrank connectivity purely because it is counted in two places.

    #: Distinct GatPoly-over-Activ regions in the written GDS, or ``None`` when
    #: the GDS could not be read.  ``None`` is "we could not tell", never 0.
    gate_crossings: Optional[int] = None
    #: ``len(subckt.devices)`` for the target netlist, when one was given.
    gate_crossings_required: Optional[int] = None
    #: Why the crossing count is ``None``; empty when it was measured.
    gate_crossings_reason: str = ""

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
        if self.gate_crossings_required is not None:
            got = self.gate_crossings
            bits.append(
                f"gates={got if got is not None else '?'}/{self.gate_crossings_required}"
            )
        if self.degraded:
            bits.append("degraded=" + ",".join(self.degraded))
        if not self.buildable:
            bits.append("UNBUILDABLE")
        return "  ".join(bits)


# Discovery is delegated to aion_layout.verification, which owns the canonical
# path rules.  A second implementation here is exactly how a scorer ends up
# disagreeing with the grader about what it is scoring.


def _crossing_target(netlist: Optional[Path], cell: str) -> Optional[int]:
    """Return how many transistors the netlist requires, or ``None``.

    ``None`` means "no target was given or the file could not be parsed", which
    the curriculum reads as *unmeasured*.  It must never fall back to 0: a
    target of 0 is satisfied by a layout with no transistors at all.
    """
    if netlist is None:
        return None
    try:
        subckts = parse_spice_file(netlist)
    except (SpiceParseError, OSError):
        return None
    if not subckts:
        return None
    subckt = next((s for s in subckts if s.name == cell), subckts[0])
    return len(subckt.devices)


def score_iteration(
    iter_dir: Path, cell: str, netlist: Optional[Path] = None
) -> Score:
    """Score the iteration whose artifacts live under ``iter_dir``.

    ``netlist`` is optional and only feeds the curriculum's crossing target; the
    graded components are unchanged without it, so every existing caller keeps
    the score it had.
    """
    degraded: List[str] = []
    notes: List[str] = []

    gds = iter_dir / f"{cell}.gds"
    buildable = gds.is_file() and gds.stat().st_size > 0
    if not buildable:
        notes.append(f"no GDS at {gds.name}: the module did not build")

    # ---- gate crossings -------------------------------------------------
    # Read from the GDS, not from the generator: the scorer runs in-process
    # inside scripts/ledger.py, and executing model-written code there would put
    # one os._exit(0) between the harness and its own history.
    crossing = count_gate_crossings(gds, cell_name=cell)
    crossings_required = _crossing_target(netlist, cell)

    # ---- DRC ------------------------------------------------------------
    drc_by_rule: Dict[str, int] = {}
    drc_total = 0

    magic_note = ""
    try:
        # locate_*, not _find_*: the wrapper drops the location note, and the
        # note is what says the report was not at the path sak-drc.sh writes.
        # parse_magic_drc_report takes it and turns it into a DEGRADED
        # completeness -- so discarding it graded a report of unknown
        # provenance as fully measured.
        magic_rpt, magic_note = _v.locate_magic_drc_report(iter_dir, cell)
    except Exception:
        magic_rpt = None
    if magic_rpt is None:
        degraded.append("magic-missing")
    else:
        try:
            magic = _v.parse_magic_drc_report(magic_rpt, location_note=magic_note)
            # DrcReport.degraded, not a re-derivation of it.  This used to check
            # only `available`, so two of that property's three clauses were
            # silently dropped: a report of UNKNOWN EXTENT (no receipt) and one
            # with unparsed_files > 0 (a database present but corrupt, whose
            # violations vanish from the merge) both scored as fully measured.
            # A second opinion about what "degraded" means is exactly how a
            # scorer ends up disagreeing with the grader it must not disagree
            # with.
            if getattr(magic, "degraded", not getattr(magic, "available", True)):
                degraded.append(_drc_tag("magic", magic))
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
            if getattr(kl, "degraded", not getattr(kl, "available", True)):
                degraded.append(_drc_tag("klayout", kl))
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

    lvs_note = ""
    try:
        # locate_*, not _find_*: the wrapper drops the location note, and the
        # note is the only thing that says the report came from the *.lvs.log
        # fallback rather than the *.lvs.out sak-lvs.sh writes.  The log carries
        # the "Final result:" line and the prose totals but NOT the per-type
        # device table, the disconnected-node lines or the pin-matching table --
        # so every one of those parsed as 0, read as "nothing wrong", and the
        # devices and pins rungs cleared on a report that says *** MISMATCH ***.
        lvs_out, lvs_note = _v.locate_netgen_lvs_report(iter_dir, cell)
    except Exception:
        lvs_out = None
    if lvs_out is None:
        degraded.append("lvs-missing")
    else:
        try:
            report = _v.parse_netgen_lvs_report(lvs_out, location_note=lvs_note)
        except TypeError:
            report = _v.parse_netgen_lvs_report(lvs_out)
        except Exception as exc:
            report = None
            degraded.append("lvs-unreadable")
            notes.append(f"netgen: {type(exc).__name__}: {exc}")
        if report is not None:
            try:
                verdict = getattr(report, "verdict", "uncertain")
                counts = report.device_counts or {}
                for _dev, (a, b) in counts.items():
                    device_delta += abs(a - b)
                nets = getattr(report, "net_counts", None)
                if nets:
                    net_delta = abs(nets[0] - nets[1])
                disconnected = len(getattr(report, "disconnected_nodes", []) or [])
                unmatched = len(getattr(report, "unmatched_pins", []) or [])

                # A report read from somewhere other than the canonical path is
                # of unknown provenance; one with no per-type device table has
                # not measured the device count, whatever its totals say.
                if lvs_note:
                    degraded.append("lvs-fallback")
                    notes.append(f"netgen report came from a fallback path: {lvs_note}")
                totals = getattr(report, "device_total", None)
                if not counts and _is_pair(totals) and totals[0] != totals[1]:
                    degraded.append("lvs-partial")
                    notes.append(
                        "netgen reported a device-count mismatch "
                        f"({totals[0]} vs {totals[1]}) but no per-type table, so "
                        "device_delta could not be measured and is not 0"
                    )
                elif not counts and not _is_pair(totals):
                    degraded.append("lvs-partial")
                    notes.append("netgen reported no device counts at all")
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
        gate_crossings=crossing.count,
        gate_crossings_required=crossings_required,
        gate_crossings_reason=crossing.reason,
    )


def unmeasured_score() -> Score:
    """A score that has measured nothing, so nothing has passed.

    Used when there is no iteration to read yet.  An all-zero ``Score`` would
    read as "no device delta, no violations, no disconnected node" -- i.e. as a
    clean layout -- which is the absence-is-success bug this codebase exists to
    prevent.  Every field here is set to the value that means *unknown*.
    """
    return Score(
        total=W_UNBUILDABLE,
        buildable=False,
        device_delta=0,
        net_delta=0,
        disconnected=0,
        unmatched_pins=0,
        lvs_verdict="no_final_result",
        drc_violations=0,
        drc_by_rule={},
        degraded=["magic-missing", "lvs-missing"],
        notes=["nothing has been measured yet"],
        gate_crossings=None,
        gate_crossings_required=None,
        gate_crossings_reason="no iteration has been scored yet",
    )


def _is_pair(value: object) -> bool:
    """True for a two-element sequence of ints, the shape a count pair has."""
    return (
        isinstance(value, (tuple, list))
        and len(value) == 2
        and all(isinstance(v, int) for v in value)
    )


def _drc_tag(engine: str, report: object) -> str:
    """Name *why* a DRC report is degraded, not merely that it is.

    The tag reaches the model in the score summary and reaches the curriculum
    through ``drc_measured()``; "klayout-incomplete" and "klayout-unverified"
    call for different responses from whoever reads the run.
    """
    if not getattr(report, "available", True):
        return f"{engine}-unavailable"
    if getattr(report, "unparsed_files", 0):
        return f"{engine}-unparsed"
    completeness = getattr(report, "completeness", "")
    if completeness == getattr(_v, "COMPLETENESS_DEGRADED", "degraded"):
        return f"{engine}-incomplete"
    if completeness == getattr(_v, "COMPLETENESS_UNVERIFIED", "unverified"):
        return f"{engine}-unverified"
    return f"{engine}-degraded"


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
    parser.add_argument(
        "--netlist",
        default=None,
        help="Target netlist; supplies the curriculum's device-count target.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)

    score = score_iteration(
        Path(args.iter_dir), args.cell, Path(args.netlist) if args.netlist else None
    )
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
