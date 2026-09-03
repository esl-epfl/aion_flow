#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Host-written iteration ledger
# ================================================================

"""Append-only record of what each iteration scored, written by the host.

Why the host writes it
----------------------

Continuity was supposed to come from ``memory.md``, which the model was asked to
append to.  It is 0 bytes after every run so far, for a structural reason: the
write was mandated as the *last* action inside a hard wall-clock timeout, so it
is the first thing lost when the model runs out of budget -- which is exactly
the run whose lessons matter most.

The ledger does not depend on the model finishing.  The host writes one record
per iteration from artifacts that already exist, immediately after grading and
before the model is invoked at all.  ``memory.md`` stays as the model's own
scratchpad; this is the part that has to survive.

Format
------

JSON Lines, one object per iteration, in ``<build>/layout/ledger.jsonl``.  A
rendered digest of the last few records goes into the prompt so the model can
see whether it is climbing or wandering: same score three iterations running
means the edits are not moving the objective.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

LEDGER_NAME = "ledger.jsonl"

#: Records rendered into the prompt.  Enough to show a trend, few enough that
#: the digest cannot crowd out the verification evidence.
DEFAULT_TAIL = 4


def ledger_path(build_dir: Path) -> Path:
    return Path(build_dir) / "layout" / LEDGER_NAME


def append(build_dir: Path, record: Dict[str, Any]) -> Path:
    """Append one record.  Never raises: losing the run beats losing a note."""
    path = ledger_path(build_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        pass
    return path


def read(build_dir: Path) -> List[Dict[str, Any]]:
    """Return every parsable record, oldest first.  Bad lines are skipped."""
    path = ledger_path(build_dir)
    if not path.is_file():
        return []
    out: List[Dict[str, Any]] = []
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _delta(cur: Optional[float], prev: Optional[float]) -> str:
    """Return a signed change, or '' when there is nothing to compare."""
    if cur is None or prev is None:
        return ""
    diff = cur - prev
    if diff == 0:
        return "  (no change)"
    return f"  ({diff:+.0f})"


def render(build_dir: Path, tail: int = DEFAULT_TAIL) -> str:
    """Return the ledger digest inlined into the prompt."""
    records = read(build_dir)
    if not records:
        return "(no iterations scored yet — this is the first pass.)"

    shown = records[-tail:]
    lines = [
        "iter  score      devices  nets  disc  pins  drc  lvs verdict          outcome",
        "----  ---------  -------  ----  ----  ----  ---  -------------------  -------",
    ]
    prev_score: Optional[float] = None
    if len(records) > len(shown):
        prev_score = records[-len(shown) - 1].get("score")

    for rec in shown:
        score = rec.get("score")
        lines.append(
            "{:<4}  {:<9}  {:<7}  {:<4}  {:<4}  {:<4}  {:<3}  {:<19}  {}".format(
                rec.get("iteration", "?"),
                f"{score:.0f}" if isinstance(score, (int, float)) else "?",
                rec.get("device_delta", "?"),
                rec.get("net_delta", "?"),
                rec.get("disconnected", "?"),
                rec.get("unmatched_pins", "?"),
                rec.get("drc_violations", "?"),
                str(rec.get("lvs_verdict", "?"))[:19],
                rec.get("outcome", ""),
            )
            + _delta(score if isinstance(score, (int, float)) else None, prev_score)
        )
        prev_score = score if isinstance(score, (int, float)) else prev_score

    best = min(
        (r for r in records if isinstance(r.get("score"), (int, float))),
        key=lambda r: r["score"],
        default=None,
    )
    if best is not None:
        lines.append("")
        lines.append(
            f"best so far: iteration {best.get('iteration')} at score "
            f"{best['score']:.0f} ({best.get('lvs_verdict', '?')}, "
            f"{best.get('drc_violations', '?')} DRC)"
        )

    # The point of showing a trend is so a flat one is visible as a flat one.
    scores = [r.get("score") for r in shown if isinstance(r.get("score"), (int, float))]
    if len(scores) >= 3 and len(set(scores)) == 1:
        lines.append(
            "WARNING: the score has not moved in the last "
            f"{len(scores)} iterations. Whatever is being changed is not what is "
            "wrong — re-read block [1] and block [2] before editing again."
        )
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Read or append the iteration ledger.")
    parser.add_argument("--build-dir", required=True)
    sub = parser.add_subparsers(dest="cmd", required=True)

    render_p = sub.add_parser("render", help="Print the prompt digest.")
    render_p.add_argument("--tail", type=int, default=DEFAULT_TAIL)

    append_p = sub.add_parser("append", help="Append one scored iteration.")
    append_p.add_argument("--iteration", type=int, required=True)
    append_p.add_argument("--cell", required=True)
    append_p.add_argument("--iter-dir", required=True)
    append_p.add_argument("--outcome", default="")
    append_p.add_argument("--stage", default="")

    args = parser.parse_args(argv)
    build_dir = Path(args.build_dir)

    if args.cmd == "render":
        print(render(build_dir, args.tail))
        return 0

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from score_iteration import score_iteration  # noqa: E402

    score = score_iteration(Path(args.iter_dir), args.cell)
    record: Dict[str, Any] = {"iteration": args.iteration, "outcome": args.outcome}
    if args.stage:
        record["stage"] = args.stage
    record.update(
        {
            "score": score.total,
            "buildable": score.buildable,
            "device_delta": score.device_delta,
            "net_delta": score.net_delta,
            "disconnected": score.disconnected,
            "unmatched_pins": score.unmatched_pins,
            "lvs_verdict": score.lvs_verdict,
            "drc_violations": score.drc_violations,
            "drc_by_rule": score.drc_by_rule,
            "degraded": score.degraded,
        }
    )
    append(build_dir, record)
    print(score.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
