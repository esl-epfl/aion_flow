# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Tests for the Stage 5 curriculum
# ================================================================

"""The gate ladder, its exit tests and the objective it generates.

Three things are pinned here, and each of them is a way the curriculum could
quietly stop working while still producing output:

* **The ladder is derived, not written down.**  A cell with no PMOS, one input,
  no internal nets or rails named something other than ``VDD``/``VSS`` must get
  a valid ladder.  The harness is for "any standard cell", and a ladder that
  only fits the one cell in ``tests/fixtures`` is a ladder that has to be
  rewritten for the second cell anybody generates.
* **The exit tests fail closed.**  ``device_delta == 0`` is true of an
  iteration whose LVS never ran.  A rung that passes on absent evidence walks
  the model up the ladder while the layout gets no better, which is the
  absence-is-success bug this whole codebase exists to prevent.
* **``current_gate`` is monotonic and stateless.**  It re-derives the rung from
  the artifacts every pass, so a regression resumes at the rung that broke
  rather than at the rung the run had reached.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aion_layout.spice_parser import parse_spice  # noqa: E402


def _load(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"aion_curr_test_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


curriculum = _load("curriculum")
scorer = _load("score_iteration")


def _score(**overrides):
    """A score with everything unmeasured, then the named fields set.

    Built from ``unmeasured_score()`` on purpose: a test that starts from an
    all-zero Score is testing a state the harness never produces, and would
    happily pass while every fail-closed guard was broken.
    """
    score = scorer.unmeasured_score()
    for key, value in overrides.items():
        assert hasattr(score, key), f"Score has no field {key!r}"
        setattr(score, key, value)
    return score


def _measured(**overrides):
    """A score where every tool ran and found nothing wrong, then overridden."""
    return _score(
        **{
            "buildable": True,
            "degraded": [],
            "lvs_verdict": "match_uniquely",
            "device_delta": 0,
            "net_delta": 0,
            "disconnected": 0,
            "unmatched_pins": 0,
            "drc_violations": 0,
            "drc_by_rule": {},
            "gate_crossings": 4,
            "gate_crossings_required": 4,
            **overrides,
        }
    )


# ---------------------------------------------------------------------------
# The ladder is derived from the netlist
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n_inputs", [1, 2, 3, 4, 5, 6])
def test_ladder_is_derived_for_every_input_count(synthetic_netlist, n_inputs):
    """1-6 inputs, the same range test_auto_scaffold.py drives the scaffold at."""
    subckt = parse_spice(synthetic_netlist(n_inputs))[0]
    ladder = curriculum.gates(subckt)

    keys = [g.key for g in ladder]
    assert keys[0] == "build", f"the ladder must start at build, got {keys}"
    assert keys[-1] == "drc", f"the ladder must end at drc, got {keys}"
    assert len(keys) == len(set(keys)), f"a rung appears twice: {keys}"
    for gate in ladder:
        assert gate.objective.strip(), f"rung {gate.key} has an empty objective"
        assert gate.exit_text.strip(), f"rung {gate.key} states no exit criterion"


def test_a_cell_with_no_pmos_still_gets_a_valid_ladder():
    """An NMOS-only cell has no n-well, but it still has a substrate to tie."""
    subckt = parse_spice(
        ".subckt PULLDOWN A Y VDD VSS\n"
        "    XN0 Y A VSS VSS sg13_lv_nmos w=1u l=0.13u\n"
        ".ends\n"
    )[0]
    keys = [g.key for g in curriculum.gates(subckt)]
    assert "gates" in keys and "drc" in keys
    assert "taps" in keys, (
        "an NMOS-only cell still needs its substrate tied, so the taps rung must "
        f"survive; ladder was {keys}"
    )
    n_tie, p_tie = curriculum.tie_nets(subckt)
    assert n_tie is None and p_tie == "VSS", (
        f"with no PMOS there is no well to tie, got n={n_tie!r} p={p_tie!r}"
    )


def test_a_cell_with_no_devices_has_no_device_rungs():
    """A rung that could never fail is not a rung; it is a place to get stuck."""
    subckt = parse_spice(".subckt FILLER VDD VSS\n.ends\n")[0]
    keys = [g.key for g in curriculum.gates(subckt)]
    assert "gates" not in keys and "devices" not in keys and "nets" not in keys, (
        f"a cell with no transistors was given transistor rungs: {keys}"
    )
    assert keys == ["build", "pins", "drc"], keys
    assert "shorts" not in keys, (
        "the shorts rung is about merged device nets; with no devices there is "
        f"nothing it could measure: {keys}"
    )


def test_rails_are_derived_from_topology_not_from_the_names_vdd_and_vss():
    """The hard requirement: nothing may be specific to one cell's naming.

    ``Subckt.vdd_net`` matches the literal pin name ``VDD``.  Deriving the taps
    rung from it drops that rung for every cell whose rails are called anything
    else -- while the latch-up rules still fire, leaving the drc rung holding an
    objective nothing has told the model how to meet.
    """
    subckt = parse_spice(
        ".subckt ALT A Y VPWR VGND\n"
        "    XP0 Y A VPWR VPWR sg13_lv_pmos w=1u l=0.13u\n"
        "    XN0 Y A VGND VGND sg13_lv_nmos w=1u l=0.13u\n"
        ".ends\n"
    )[0]
    assert subckt.vdd_net is None and subckt.vss_net is None, (
        "the premise of this test is that the name-based helpers find nothing here"
    )
    assert curriculum.tie_nets(subckt) == ("VPWR", "VGND")

    keys = [g.key for g in curriculum.gates(subckt)]
    assert "taps" in keys, f"the taps rung vanished for non-VDD/VSS rails: {keys}"

    taps = curriculum.gate_by_key(subckt, "taps")
    assert "VPWR" in taps.objective and "VGND" in taps.objective, (
        f"the taps objective does not name this cell's own rails:\n{taps.objective}"
    )


# ---------------------------------------------------------------------------
# current_gate walks from the bottom
# ---------------------------------------------------------------------------

def test_current_gate_returns_the_first_failing_rung(synthetic_netlist):
    subckt = parse_spice(synthetic_netlist(2))[0]
    assert curriculum.current_gate(subckt, _score()).key == "build", (
        "an unmeasured iteration must sit at the bottom of the ladder"
    )
    assert curriculum.current_gate(subckt, _measured(gate_crossings=1)).key == "gates"
    assert curriculum.current_gate(subckt, _measured(device_delta=2)).key == "devices"
    assert (
        curriculum.current_gate(subckt, _measured(drc_by_rule={"LU.a": 4})).key == "taps"
    )
    assert curriculum.current_gate(subckt, _measured(disconnected=3)).key == "shorts"
    assert curriculum.current_gate(subckt, _measured(unmatched_pins=2)).key == "pins"
    assert (
        curriculum.current_gate(subckt, _measured(lvs_verdict="do_not_match")).key
        == "nets"
    )
    assert curriculum.current_gate(subckt, _measured(drc_violations=7)).key == "drc"


def test_a_regression_sends_the_run_back_down_the_ladder(synthetic_netlist):
    """Monotonic without state: the rung is re-derived from the artifacts.

    A run that has reached `nets` and then breaks the device count must go back
    to `devices`, not carry on asking for connectivity work on a layout that no
    longer has the right transistors in it.
    """
    subckt = parse_spice(synthetic_netlist(3))[0]
    assert curriculum.current_gate(subckt, _measured(drc_violations=2)).key == "drc"
    regressed = _measured(drc_violations=2, device_delta=1)
    assert curriculum.current_gate(subckt, regressed).key == "devices"


def test_all_rungs_cleared_returns_the_last_one(synthetic_netlist):
    subckt = parse_spice(synthetic_netlist(2))[0]
    clean = _measured()
    assert all(passed for _g, passed in curriculum.ladder_status(subckt, clean))
    assert curriculum.current_gate(subckt, clean).key == "drc"


# ---------------------------------------------------------------------------
# Fail closed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "key,overrides",
    [
        ("devices", {"degraded": ["lvs-missing"], "lvs_verdict": "match_uniquely"}),
        ("pins", {"degraded": ["lvs-unreadable"], "lvs_verdict": "match_uniquely"}),
        ("shorts", {"degraded": ["lvs-partial"], "lvs_verdict": "match_uniquely"}),
        ("nets", {"degraded": ["lvs-missing"], "lvs_verdict": "match_uniquely"}),
        ("taps", {"degraded": ["magic-missing"]}),
        ("drc", {"degraded": ["klayout-incomplete"]}),
    ],
)
def test_a_rung_does_not_pass_on_evidence_that_was_never_read(
    synthetic_netlist, key, overrides
):
    """Every number these rungs read defaults to the value that means "fine".

    ``device_delta``, ``disconnected``, ``unmatched_pins`` and
    ``drc_violations`` are all 0 for an iteration whose tools never ran.  Each
    rung therefore has to check that the tool ran at all, and this is the test
    that says so -- the fields below are set to their *passing* values on
    purpose, so only the degradation can fail the rung.
    """
    subckt = parse_spice(synthetic_netlist(2))[0]
    gate = curriculum.gate_by_key(subckt, key)
    assert gate is not None
    assert not gate.passed(_measured(**overrides)), (
        f"rung {key!r} passed on {overrides['degraded']}: every number it reads "
        "is at its clean value because nothing measured it, and treating that as "
        "progress is exactly the bug this harness exists to prevent"
    )


def test_the_gates_rung_does_not_pass_without_a_crossing_measurement(synthetic_netlist):
    subckt = parse_spice(synthetic_netlist(2))[0]
    gate = curriculum.gate_by_key(subckt, "gates")
    assert not gate.passed(_measured(gate_crossings=None))
    assert not gate.passed(_measured(gate_crossings_required=None))
    assert gate.passed(_measured(gate_crossings=4, gate_crossings_required=4))


def test_a_raising_exit_test_is_not_a_pass(synthetic_netlist):
    """`Gate.passed` swallows exceptions -- into a failure, never into a pass."""
    subckt = parse_spice(synthetic_netlist(2))[0]
    broken = curriculum.Gate(
        key="broken",
        title="t",
        objective="o",
        exit_test=lambda s: 1 / 0,
        exit_text="never",
    )
    assert not broken.passed(_measured())


# ---------------------------------------------------------------------------
# The objective block
# ---------------------------------------------------------------------------

def test_the_objective_states_the_rung_the_measurement_and_the_criterion(
    synthetic_netlist,
):
    subckt = parse_spice(synthetic_netlist(3))[0]
    score = _measured(gate_crossings=2, gate_crossings_required=6)
    gate = curriculum.current_gate(subckt, score)
    body = curriculum.objective_block(gate, subckt, score)

    assert f"THIS TURN : {gate.key}" in body
    assert "PASSES WHEN:" in body
    assert "2" in body and "6" in body, (
        f"the measured crossing count and its target are not both in:\n{body}"
    )
    assert "still to do:" in body, "the model is not told what is deferred"


def test_the_objective_never_reports_the_whole_score(synthetic_netlist):
    """Only this rung's own numbers, or the objective is wide again.

    Listing every component invites the model to work on the ones it can see,
    which is the whole-cell objective reintroduced inside a narrow one.
    """
    subckt = parse_spice(synthetic_netlist(2))[0]
    score = _measured(gate_crossings=1, gate_crossings_required=4, drc_violations=97)
    gate = curriculum.current_gate(subckt, score)
    assert gate.key == "gates"
    body = curriculum.objective_block(gate, subckt, score)
    assert "97" not in body, (
        f"the DRC count leaked into the crossing rung's objective:\n{body}"
    )


def test_every_rung_declares_the_blocks_it_needs(synthetic_netlist):
    subckt = parse_spice(synthetic_netlist(2))[0]
    for gate in curriculum.gates(subckt):
        blocks = gate.all_blocks
        assert curriculum.BLOCK_OBJECTIVE in blocks
        assert curriculum.BLOCK_NETLIST in blocks, (
            f"rung {gate.key} does not carry the specification"
        )
        assert curriculum.BLOCK_VERDICT in blocks, (
            f"rung {gate.key} does not carry the verdict; orchestrate.sh's "
            "packet_is_gradable() would read its packet as degraded"
        )
        assert curriculum.BLOCK_BUILD_ERROR in blocks, (
            f"rung {gate.key} would withhold a build traceback"
        )


def test_the_ladder_is_stable_across_calls(synthetic_netlist):
    """Two calls must agree, or the rung the ledger records is not the rung run."""
    subckt = parse_spice(synthetic_netlist(4))[0]
    first = [g.key for g in curriculum.gates(subckt)]
    second = [g.key for g in curriculum.gates(subckt)]
    assert first == second


# ---------------------------------------------------------------------------
# The CLI orchestrate.sh actually calls
# ---------------------------------------------------------------------------

def test_cli_prints_one_rung_key(tmp_path):
    from conftest import FIXTURES, run

    proc = run(
        [
            sys.executable, str(ROOT / "scripts" / "curriculum.py"),
            "--netlist", str(FIXTURES / "AION_inv_nand2_nor2_1_minimized.spice"),
            "--cell", "AION_inv_nand2_nor2_1",
            "--iter-dir", str(FIXTURES / "iteration_0"),
            "--print", "key",
        ]
    )
    assert proc.returncode == 0, proc.stderr
    key = proc.stdout.strip()
    assert key in {"build", "gates", "devices", "taps", "pins", "nets", "drc"}, (
        f"orchestrate.sh reads this straight into a ledger field, got {key!r}"
    )
    assert "\n" not in proc.stdout.strip(), "the key must be one bare line"


def test_cli_rejects_a_rung_this_cell_does_not_have(tmp_path):
    from conftest import FIXTURES, run

    proc = run(
        [
            sys.executable, str(ROOT / "scripts" / "curriculum.py"),
            "--netlist", str(FIXTURES / "AION_inv_nand2_nor2_1_minimized.spice"),
            "--gate", "not-a-rung", "--print", "key",
        ]
    )
    assert proc.returncode == 2, (
        f"an unknown rung must be an error, not a silent fallback; got "
        f"{proc.returncode} / {proc.stdout!r}"
    )
    assert "not-a-rung" in proc.stderr and "ladder is" in proc.stderr


# ---------------------------------------------------------------------------
# The objective is bounded by construction, because nothing else bounds it
# ---------------------------------------------------------------------------

def _wide_netlist(n_pairs: int, name: str = "BIG") -> str:
    inputs = " ".join(f"I{i}" for i in range(n_pairs))
    rows = "\n".join(
        f"    XP{i} O0 I{i} VDD VDD sg13_lv_pmos w=1.0u l=0.13u ng=1 m=1\n"
        f"    XN{i} O0 I{i} VSS VSS sg13_lv_nmos w=1.0u l=0.13u ng=1 m=1"
        for i in range(n_pairs)
    )
    return f".subckt {name} {inputs} O0 VDD VSS\n{rows}\n.ends\n"


@pytest.mark.parametrize("n_pairs", [1, 30, 200])
def test_no_objective_grows_with_the_cell(n_pairs):
    """Block [0] is exempt from every byte cap, so it must bound itself.

    It is exempt on purpose -- ``BLOCK_CAPS[0]`` is ``None`` and ``TRIM_ORDER``
    omits it -- because an instruction that arrives truncated is worse than no
    instruction: the model would be told to do something and not told what
    clears it.

    That exemption is only safe if nothing in the objective scales with the
    netlist.  It did: the ``devices`` rung enumerated every transistor, so a
    120-device cell produced a 7.8 KB objective and a 900-device one would have
    spent the turn's entire budget restating a table block [1] already carries.
    """
    subckt = parse_spice(_wide_netlist(n_pairs))[0]
    for gate in curriculum.gates(subckt):
        size = len(gate.objective.encode("utf-8"))
        assert size < 3_000, (
            f"the {gate.key!r} objective is {size} bytes for a "
            f"{len(subckt.devices)}-device cell.  Block [0] is uncapped, so an "
            "objective that scales with the netlist crowds out the very evidence "
            "the rung is graded on."
        )


def test_the_device_rung_still_shows_real_devices_and_says_it_truncated():
    """Anti-vacuity: bounding it must not empty it, and must not hide the cut."""
    subckt = parse_spice(_wide_netlist(50))[0]
    objective = curriculum.gate_by_key(subckt, "devices").objective
    assert "XP0" in objective, "the listing shows no device at all"
    assert objective.count("sg13_lv_") >= 4 or objective.count("nmos") >= 4, (
        f"the listing is too short to show the shape of the netlist:\n{objective}"
    )
    assert "more" in objective and "block [1]" in objective, (
        "the objective silently dropped devices instead of saying how many it "
        f"dropped and where the full table is:\n{objective}"
    )
