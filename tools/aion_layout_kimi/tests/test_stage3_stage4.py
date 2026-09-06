# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Tests for the ranker, the scorer and the ledger
# ================================================================

"""Coverage for the Stage 3 and Stage 4 host-side tools.

These three scripts decide what the model is shown (the reference cell) and how
the harness will judge what it writes back (the score, the ledger).  Every test
below names the defect it guards against, because two of them are guarding
mistakes that were actually made while writing these files.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
NETLIST = FIXTURES / "AION_inv_nand2_nor2_1_minimized.spice"
ITER0 = FIXTURES / "iteration_0"
CELL = "AION_inv_nand2_nor2_1"


def _load(name: str):
    """Import a scripts/*.py module by location, as evidence.py does."""
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"aion_test_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: @dataclass resolves its own module out of
    # sys.modules while the class body runs, and a module that is not there
    # yet dies with a bare AttributeError on None.  This bit us for real.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


picker = _load("pick_reference_cells")
scorer = _load("score_iteration")
ledger = _load("ledger")


# ---------------------------------------------------------------------------
# Stage 3 -- the reference-cell ranker
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not (ROOT / "context" / "spice").is_dir(), reason="no context/ corpus")
def test_ranker_selects_a_structurally_identical_cell():
    """The winner must match the target's fingerprint exactly.

    Guards the whole premise of block [11]: an example that does not share the
    target's shape teaches the wrong layout.
    """
    winner, target, ranked = picker.pick(NETLIST, ROOT / "context")
    assert winner is not None, "no reference cell selected at all"
    assert winner.distance == 0.0, (
        f"selected {winner.name} at distance {winner.distance}; an exact "
        f"structural match exists in the corpus and should have won"
    )
    assert winner.features == target, (
        f"{winner.name} fingerprint {winner.features.as_row()} != "
        f"target {target.as_row()}"
    )
    assert len(ranked) > 50, f"only {len(ranked)} candidates parsed; corpus is 83"


@pytest.mark.skipif(not (ROOT / "context" / "spice").is_dir(), reason="no context/ corpus")
def test_ranker_never_proposes_the_target_as_its_own_example():
    """Showing the cell its own solved layout would be handing over the answer."""
    _winner, _t, ranked = picker.pick(NETLIST, ROOT / "context")
    assert all(c.name != CELL for c in ranked), (
        "the target cell appeared in its own candidate list"
    )


@pytest.mark.skipif(not (ROOT / "context" / "spice").is_dir(), reason="no context/ corpus")
def test_reference_block_says_it_is_not_the_answer():
    """The block must state plainly that it is a different cell.

    A worked example that reads as a solution invites copying, and copying it
    fails LVS -- the block has to say so where the model cannot miss it.
    """
    body = picker.render_block(NETLIST, ROOT / "context")
    assert "NOT THE ANSWER" in body, "block [11] does not disclaim itself"
    assert "block [1]" in body, "block [11] does not point back at the real topology"


def test_chain_depth_is_linear_not_exponential():
    """A wide parallel network must not blow up the fingerprint.

    The first implementation enumerated every simple path.  On a 900-device
    synthetic netlist it never returned, hanging the whole test suite.
    """
    from aion_layout.spice_parser import parse_spice

    devices = "\n".join(
        f"    XN{i} O0 I{i} VSS VSS sg13_lv_nmos w=1u l=0.13u" for i in range(200)
    )
    text = f".subckt WIDE {' '.join(f'I{i}' for i in range(200))} O0 VDD VSS\n{devices}\n.ends\n"
    sub = parse_spice(text)[0]
    feats = picker.features_of(sub)  # must return promptly
    assert feats.n_nmos == 200
    assert feats.pdn_depth == 1, (
        f"200 devices all sourced on VSS are in parallel, so depth is 1, "
        f"got {feats.pdn_depth}"
    )


def test_parallel_and_series_depths_are_distinguished():
    """The feature has to separate a stack from a parallel bank to be useful."""
    from aion_layout.spice_parser import parse_spice

    series = parse_spice(
        ".subckt S A B C O0 VDD VSS\n"
        "    XN0 O0 A n1 VSS sg13_lv_nmos w=1u l=0.13u\n"
        "    XN1 n1 B n2 VSS sg13_lv_nmos w=1u l=0.13u\n"
        "    XN2 n2 C VSS VSS sg13_lv_nmos w=1u l=0.13u\n"
        ".ends\n"
    )[0]
    parallel = parse_spice(
        ".subckt P A B C O0 VDD VSS\n"
        "    XN0 O0 A VSS VSS sg13_lv_nmos w=1u l=0.13u\n"
        "    XN1 O0 B VSS VSS sg13_lv_nmos w=1u l=0.13u\n"
        "    XN2 O0 C VSS VSS sg13_lv_nmos w=1u l=0.13u\n"
        ".ends\n"
    )[0]
    assert picker.features_of(series).pdn_depth == 3
    assert picker.features_of(parallel).pdn_depth == 1


# ---------------------------------------------------------------------------
# Stage 4 -- the scorer
# ---------------------------------------------------------------------------

def test_scorer_reproduces_the_fixture_ground_truth():
    """The score must be computed from the same numbers the grader reports."""
    score = scorer.score_iteration(ITER0, CELL)
    assert score.device_delta == 2, "nmos 3|4 plus pmos 3|4 is a delta of 2"
    assert score.net_delta == 4, "nets 13 vs 9"
    assert score.disconnected == 5, "I0 I2 O0 VSS VDD"
    assert score.lvs_verdict == "failed_pin_matching"
    assert score.drc_violations == 9, "8 Magic + 1 KLayout"
    assert score.drc_by_rule.get("LU.a") == 4
    assert score.drc_by_rule.get("LU.b") == 5, "4 from Magic + 1 from KLayout"


def test_scorer_is_not_clean_on_the_known_bad_fixture():
    """The whole point: a broken layout must never score clean."""
    assert not scorer.score_iteration(ITER0, CELL).clean


def test_missing_artifacts_score_worse_than_known_bad(tmp_path):
    """'We could not tell' must never look like progress.

    Absence reading as success is the defect this entire harness exists to
    kill; it must not come back through the objective function.
    """
    empty = tmp_path / "iteration_9"
    (empty / "drc").mkdir(parents=True)
    (empty / "lvs").mkdir(parents=True)
    blind = scorer.score_iteration(empty, CELL)
    known_bad = scorer.score_iteration(ITER0, CELL)
    assert blind.degraded, "an empty iteration was not marked degraded"
    assert not blind.clean
    assert blind.total > known_bad.total, (
        f"an unmeasured layout scored {blind.total}, better than a measured "
        f"broken one at {known_bad.total} -- the loop would prefer blindness"
    )


def test_scorer_cli_exit_codes(tmp_path):
    """0 means clean, 1 means scored-and-not-clean; neither is an error path."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "score_iteration.py"),
         "--iter-dir", str(ITER0), "--cell", CELL, "--json"],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert proc.returncode == 1, "a dirty layout must exit 1"
    payload = json.loads(proc.stdout)
    assert payload["lvs_verdict"] == "failed_pin_matching"
    assert payload["drc_violations"] == 9


# ---------------------------------------------------------------------------
# Stage 4 -- the ledger
# ---------------------------------------------------------------------------

def test_ledger_round_trips_and_orders_oldest_first(tmp_path):
    ledger.append(tmp_path, {"iteration": 0, "score": 10.0})
    ledger.append(tmp_path, {"iteration": 1, "score": 5.0})
    records = ledger.read(tmp_path)
    assert [r["iteration"] for r in records] == [0, 1]


def test_ledger_survives_a_corrupt_line(tmp_path):
    """A torn write must cost one record, not the whole history."""
    ledger.append(tmp_path, {"iteration": 0, "score": 10.0})
    path = ledger.ledger_path(tmp_path)
    with path.open("a") as handle:
        handle.write("{not json\n")
    ledger.append(tmp_path, {"iteration": 1, "score": 5.0})
    assert [r["iteration"] for r in ledger.read(tmp_path)] == [0, 1]


def test_ledger_reports_the_best_iteration_not_the_last(tmp_path):
    """Best-tracking is what makes a regression recoverable."""
    ledger.append(tmp_path, {"iteration": 0, "score": 900.0, "lvs_verdict": "x"})
    ledger.append(tmp_path, {"iteration": 1, "score": 100.0, "lvs_verdict": "x"})
    ledger.append(tmp_path, {"iteration": 2, "score": 800.0, "lvs_verdict": "x"})
    out = ledger.render(tmp_path)
    assert "best so far: iteration 1" in out, out


def test_ledger_warns_when_the_score_stops_moving(tmp_path):
    """A flat score means the edits are not touching what is wrong."""
    for i in range(3):
        ledger.append(tmp_path, {"iteration": i, "score": 500.0, "lvs_verdict": "x"})
    assert "has not moved" in ledger.render(tmp_path)


def test_ledger_does_not_warn_when_the_score_is_improving(tmp_path):
    """The warning must mean something; firing on progress makes it noise."""
    for i, s in enumerate((900.0, 500.0, 100.0)):
        ledger.append(tmp_path, {"iteration": i, "score": s, "lvs_verdict": "x"})
    assert "has not moved" not in ledger.render(tmp_path)


def test_ledger_render_is_safe_before_anything_is_scored(tmp_path):
    assert "first pass" in ledger.render(tmp_path)


def test_ledger_does_not_double_count_a_re_graded_iteration(tmp_path):
    """Restarting the loop re-grades the current iteration; that is one row.

    ``orchestrate.sh`` re-reads the artifacts on every invocation rather than
    trusting the step flags, so a build directory that is run three times scores
    iteration N three times.  Appending an identical row each time makes three
    restarts read as three iterations that made no progress -- and the digest's
    "the score has not moved" warning then fires on a run that has not had a
    chance to move it yet.
    """
    row = {"iteration": 0, "score": 6270.0, "stage": "gates",
           "lvs_verdict": "failed_pin_matching", "drc_violations": 13}
    for _ in range(3):
        ledger.append(tmp_path, dict(row))
    assert len(ledger.read(tmp_path)) == 1, (
        "the same iteration, re-graded to the same score, was recorded more "
        "than once"
    )

    # A real change to the same iteration is still a new row: the point is to
    # drop duplicates, not to stop recording an iteration that actually moved.
    ledger.append(tmp_path, dict(row, score=5230.0, stage="taps"))
    assert len(ledger.read(tmp_path)) == 2

    # And a later iteration is always its own row, even at an identical score.
    ledger.append(tmp_path, dict(row, iteration=1))
    assert [r["iteration"] for r in ledger.read(tmp_path)] == [0, 0, 1]


# ---------------------------------------------------------------------------
# Fail-closed: the scorer must not report a number it did not measure
# ---------------------------------------------------------------------------

def test_a_klayout_run_of_unknown_extent_is_degraded():
    """`DrcReport.degraded` has three clauses; the scorer used to check one.

    It tested `available` and `completeness == DEGRADED`, and silently dropped
    the other two: COMPLETENESS_UNVERIFIED (no receipt, so the extent of the run
    is unknown) and `unparsed_files > 0` (a database present but corrupt, whose
    violations vanish from the merge without a word).

    The committed fixture is in exactly the first state, and it scored
    `degraded: []` -- so `curriculum.drc_measured()` returned True and the taps
    and drc rungs were free to pass on a DRC run nobody could vouch for.
    """
    score = scorer.score_iteration(ITER0, CELL)
    assert score.degraded, (
        "the fixture's KLayout run carries no receipt, so its extent is "
        "unknown; the scorer reported it as fully measured"
    )
    assert any("unverified" in tag for tag in score.degraded), (
        f"the degradation is not named as an unverified run: {score.degraded}"
    )


def test_a_netgen_log_fallback_does_not_read_as_a_measured_device_count(tmp_path):
    """The *.lvs.log fallback has no device table, and 0 is not "no mismatch".

    `sak-lvs.sh` writes `<cell>.lvs.out`; `<cell>.lvs.log` is a documented
    fallback that `pipeline.sh` accepts as sufficient LVS evidence.  The log
    carries the `Final result:` line and the prose totals but NOT the per-type
    device table, the `disconnected node:` lines or the pin-matching table.

    Every one of those parsed as 0 and read as "nothing wrong", so an iteration
    whose `.lvs.out` was lost scored device_delta=0, disconnected=0,
    unmatched_pins=0 -- clearing the `devices` and `pins` rungs off a report
    whose own text says `*** MISMATCH ***`, and scoring BETTER than the same
    iteration measured properly.
    """
    import shutil

    tree = tmp_path / "iteration_0"
    shutil.copytree(ITER0, tree)
    removed = list(tree.glob("lvs/*/*.lvs.out"))
    assert removed, "the fixture has no .lvs.out to remove; this test is vacuous"
    for path in removed:
        path.unlink()
    assert list(tree.glob("lvs/*/*.lvs.log")), (
        "the fixture has no .lvs.log fallback, so the state under test is "
        "unreachable and this test proves nothing"
    )

    full = scorer.score_iteration(ITER0, CELL)
    log_only = scorer.score_iteration(tree, CELL)

    assert log_only.device_delta == 0 and log_only.disconnected == 0, (
        "the premise of this test is that the log cannot supply these numbers"
    )
    assert "lvs-partial" in log_only.degraded, (
        f"the log fallback was not flagged as partly measured: "
        f"{log_only.degraded}.  Its zeros then read as a clean LVS."
    )
    assert not curriculum_lvs_measured(log_only), (
        "curriculum.lvs_measured() still says this iteration's LVS was measured, "
        "so the devices and pins rungs would clear on it"
    )
    assert log_only.total > full.total, (
        f"the less-measured iteration scored {log_only.total}, better than the "
        f"fully measured one at {full.total} -- accept_or_reject would crown it "
        "as .best_iteration and the next model call would branch from it"
    )


def curriculum_lvs_measured(score):
    """`curriculum.lvs_measured`, imported here so the guard is tested as used."""
    return _load("curriculum").lvs_measured(score)
