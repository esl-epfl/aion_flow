# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               One verdict line, and an exit status that agrees
# ================================================================

"""What the outside world reads: one column-0 line, and one exit status.

Everything upstream of this file can be right and the flow still be unusable if
the summary lies.  Two ways it can.

**Two verdict lines.**  Report text is written by the tools and, through them,
by the layout being checked: a cell named ``x\\nRESULT: PASS`` would print a
second column-0 line that a harness grepping for ``^RESULT:`` would take as the
answer.  So exactly one line starts at column 0, it is last, and everything else
is indented.

**A verdict that outvotes the evidence.**  A cell can be DRC-clean, LVS-clean
and still unplaceable -- the wrong row height, an off-grid width -- and a
KLayout run can report zero violations because a rule table died rather than
because the layout is clean.  Neither may come out PASS.

No tool runs here.  ``steps.drc``/``steps.lvs`` are replaced by functions that
return the reports parsed from the committed real artifacts, which is exactly
what those functions do on a machine that has the container.
"""

from __future__ import annotations

import dataclasses as dc
import re
import shutil

import pytest

from aion_layout.metrics import CellGeometry
from aion_layout.verification import (
    parse_klayout_reports,
    parse_magic_drc_report,
    parse_netgen_lvs_report,
)
from conftest import CELL, optional_module

steps = optional_module("aion_layout.steps")
cli = optional_module("aion_layout.cli")

RESULT_RE = re.compile(r"^RESULT: ", re.MULTILINE)

ROW_LEGAL = CellGeometry(
    cell=CELL, width_um=2.88, height_um=3.78, source="prBoundary"
)

#: Ports a router can land on: Metal1 is horizontal, so each spans a
#: y = n * 420 nm track, and each is over 210 nm across so a via has somewhere
#: to sit.  ``(name, layer, x1, y1, x2, y2)`` in nm.
ON_TRACK_PORTS = [
    ("I0", "Metal1", 200.0, 310.0, 490.0, 530.0),      # crosses y = 420
    ("O0", "Metal1", 2150.0, 1570.0, 2550.0, 1790.0),  # crosses y = 1680
]

#: Geometry a cell can be abutted with: rail tap contacts on the shared grid
#: (x = 160 + 480k, one per site) and nothing drawn over a port's via landing.
#:
#: Supplied rather than read from ``known_gds`` because the worked example is
#: itself off that grid -- every cells/*.py places taps at 150 + 430k -- so
#: reading it would make the positive control below assert a defect.
ABUTTABLE = {
    "Cont": [
        (160.0, -80.0, 320.0, 80.0),
        (640.0, 3700.0, 800.0, 3860.0),
    ],
}


def reports(tree):
    """The three parsed reports of a committed artifact tree."""
    magic = parse_magic_drc_report(
        tree / "drc" / f"{CELL}.magic.drc" / f"{CELL}.magic.drc.rpt"
    )
    klayout = parse_klayout_reports(tree / "drc", CELL)
    lvs = parse_netgen_lvs_report(
        tree / "lvs" / f"{CELL}.magic.lvs" / f"{CELL}.lvs.out"
    )
    return magic, klayout, lvs


@pytest.fixture
def graded(monkeypatch, tmp_path, known_gds, netlist_path, clean_tree):
    """Return ``run(**overrides) -> Verdict`` with no tool ever started.

    Every containerised step is replaced by one that hands back the reports
    parsed from the real captured run.  Overriding one of them is how each test
    below asks "what does the grader do when this single thing is wrong".
    """
    work = tmp_path / "work"
    work.mkdir()
    shutil.copy(known_gds, work / f"{CELL}.gds")

    def run(*, magic=None, klayout=None, lvs=None, geometry=ROW_LEGAL, tables=(1, ()),
            ports=ON_TRACK_PORTS, drawn=ABUTTABLE):
        base_magic, base_klayout, base_lvs = reports(clean_tree)
        monkeypatch.setattr(
            steps, "drc",
            lambda *a, **k: (magic or base_magic, klayout or base_klayout),
        )
        monkeypatch.setattr(steps, "lvs", lambda *a, **k: lvs or base_lvs)
        monkeypatch.setattr(steps, "gds_boundary", lambda *a, **k: geometry)
        monkeypatch.setattr(steps, "klayout_table_logs", lambda *a, **k: tables)
        monkeypatch.setattr(steps, "declared_ports", lambda *a, **k: ports)
        monkeypatch.setattr(steps, "drawn_shapes", lambda *a, **k: drawn)
        return steps.verify(
            "unused-because-skip-build",
            CELL,
            netlist_path,
            work,
            skip_build=True,
        )

    return run


# ---------------------------------------------------------------------------
# The grading chain
# ---------------------------------------------------------------------------


def test_all_evidence_clean_and_row_legal_is_a_pass(graded):
    """The positive control: the grader must be able to pass something."""
    verdict = graded()

    assert verdict.result == "PASS", (
        "clean Magic, clean KLayout with a matching receipt, a Netgen match "
        f"and a row-legal footprint is a pass: {verdict.reasons}"
    )
    assert verdict.passed and verdict.reasons == ()


def test_a_non_row_legal_cell_is_not_a_pass(graded):
    """DRC-clean and LVS-clean is not enough: the cell still has to be placeable."""
    verdict = graded(
        geometry=dc.replace(
            ROW_LEGAL, height_um=3.7, problems=("height 3.7000 um is not the row height",)
        )
    )

    assert verdict.result != "PASS", (
        "a cell 80 nm short of the row height cannot abut its neighbours; "
        "passing it means discovering that at place-and-route instead"
    )
    assert verdict.result == "FAIL", (
        "the tools ran and the answer is that the layout is wrong, which is "
        f"FAIL, not ERROR: {verdict.result}"
    )
    assert any("row-legal" in r for r in verdict.reasons), (
        f"the reason must name the row legality as the fault: {verdict.reasons}"
    )


def test_an_off_site_width_is_not_a_pass(graded):
    verdict = graded(
        geometry=dc.replace(
            ROW_LEGAL, width_um=2.9, problems=("width 2.9000 um is off the site grid",)
        )
    )

    assert not verdict.passed, (
        "an off-grid width has no legal column; the placer will refuse it"
    )


def test_a_degraded_klayout_completeness_is_not_a_pass(graded, work_tree):
    """Zero items over a database set nobody vouched for is not zero violations."""
    tree = work_tree("clean")
    (tree / "drc" / f"{CELL}.klayout.drc" / "klayout.receipt.json").unlink()
    _, klayout, _ = reports(tree)
    assert klayout.error_count == 0, "the fixture still holds no violations"

    verdict = graded(klayout=klayout)

    assert verdict.result == "ERROR", (
        "nothing is known about the extent of the KLayout run, so nothing was "
        f"verified; that is ERROR, not FAIL and certainly not PASS: {verdict}"
    )
    assert any("completeness" in r for r in verdict.reasons), (
        f"the reason must name completeness as the fault: {verdict.reasons}"
    )


def test_an_unavailable_magic_report_is_an_error_not_a_pass(graded, tmp_path):
    """A trailerless report says nothing; a grader that passes it grades nothing."""
    path = tmp_path / f"{CELL}.magic.drc.rpt"
    path.write_text("")
    empty = parse_magic_drc_report(path)

    verdict = graded(magic=empty)

    assert verdict.result == "ERROR", (
        f"a Magic report with no COUNT trailer is missing evidence: {verdict}"
    )
    assert any("Magic" in r for r in verdict.reasons)


def test_a_port_off_the_routing_grid_is_not_a_pass(graded):
    """The failure this grader was extended to catch.

    Metal1 routes along y = n * 420 nm.  A port between two tracks is
    DRC-clean, LVS-clean and row-legal, and then aborts detailed routing for
    the whole design with DRT-0073 -- twelve minutes into step 7, long after
    this cell looked finished.
    """
    verdict = graded(
        ports=[("O0", "Metal1", 2150.0, 1090.0, 2550.0, 1250.0)]  # 10 nm under 1260
    )

    assert verdict.result == "FAIL", (
        "the tools ran and the answer is that the layout is wrong, which is "
        f"FAIL, not ERROR: {verdict.result} {verdict.reasons}"
    )
    assert any("DRT-0073" in reason for reason in verdict.reasons), (
        "the reason must name the error it prevents, so a model reading the "
        f"verdict knows what it is being asked to fix: {verdict.reasons}"
    )
    assert any("1260" in reason for reason in verdict.reasons), (
        f"and where the nearest track is, or it cannot act on it: {verdict.reasons}"
    )


def test_a_port_too_thin_for_a_via_fails_in_the_loop(graded):
    """The thin-port half of pin access has to fail here, not only at export.

    AION_a21oi_nor2_1/O0 as first drawn: on the grid, 180 nm across, and a hard
    DRT-0073 in step 7.
    """
    verdict = graded(ports=[("O0", "Metal1", 2150.0, 1090.0, 2550.0, 1270.0)])

    assert verdict.result == "FAIL", "180 nm across cannot take a via"
    assert any("no via can land on it" in r for r in verdict.reasons), verdict.reasons


def test_metal_drawn_over_a_port_fails_in_the_loop(graded):
    """A strap over the port is an OBS in the LEF, so it has to fail here too.

    AION_nand2_o21ai_0/O0: a Metal1 port on the grid and wide enough, with the
    cell's own Metal2 output strap running straight over the only place a via
    could land.  ``lef write -pinonly`` labels one rectangle and puts the rest
    in OBS, so this passes every other check and dies in detailed routing.  The
    verdict has to name it while the model that drew it can still move it --
    which is the whole point of grading ports here rather than at export.
    """
    port = [("O0", "Metal1", 1790.0, 960.0, 2050.0, 1270.0)]
    over = {"Metal2": [(1835.0, 950.0, 2035.0, 2650.0)]}
    clear = {"Metal2": [(2400.0, 950.0, 2600.0, 2650.0)]}

    blocked = graded(ports=port, drawn=over)
    assert blocked.result == "FAIL", "the strap covers every via landing"
    assert any("could land on" in r for r in blocked.reasons), blocked.reasons
    assert any("declare O0 on Metal2" in r for r in blocked.reasons), (
        f"the verdict has to say what to do about it: {blocked.reasons}"
    )

    moved = graded(ports=port, drawn=clear)
    assert moved.result == "PASS", (
        f"the same port is fine once the strap is off it: {moved.reasons}"
    )


def test_off_grid_rail_taps_fail_in_the_loop(graded):
    """The other thing a cell does to its neighbours that it survives alone.

    Rows abut mirrored, so a cell's VSS rail is the same silicon as the VSS
    rail of the row below and their tap contacts land in one band.  The first
    two AION cells placed theirs at 150 + 430k while all 84 PDK cells use
    160 + 480k, so every abutment put contacts partially on top of each other:
    10322 Magic and 2872 KLayout violations in a design whose cells were each
    individually DRC-clean.
    """
    off = {"Cont": [(70.0, -80.0, 230.0, 80.0), (500.0, -80.0, 660.0, 80.0)]}

    verdict = graded(drawn=off)
    assert verdict.result == "FAIL", "off-grid taps collide with every neighbour"
    assert any("abutment grid" in r for r in verdict.reasons), verdict.reasons
    assert any("160 + 480k" in r for r in verdict.reasons), (
        f"the verdict has to name the grid to move to: {verdict.reasons}"
    )


def test_power_ports_are_not_graded_against_the_track_grid(graded):
    """VDD and VSS are strapped by the PDN; the signal router never lands."""
    verdict = graded(
        ports=ON_TRACK_PORTS + [
            ("VDD", "Metal1", 0.0, 3560.0, 2880.0, 4000.0),
            ("VSS", "Metal1", 0.0, -220.0, 2880.0, 220.0),
        ]
    )

    assert verdict.result == "PASS", (
        f"the rails answer to the PDN, not to the track grid: {verdict.reasons}"
    )


def test_ports_that_could_not_be_read_are_not_a_pass(graded):
    """Unknown is not clean -- the rule the whole grader is built on."""
    verdict = graded(ports=None)

    assert verdict.result == "ERROR", (
        "a build that recorded no ports leaves the track rule unchecked; "
        f"reporting PASS would be inventing the answer: {verdict.result}"
    )
    assert any("routing track grid" in reason for reason in verdict.reasons), (
        verdict.reasons
    )


def test_real_violations_are_a_fail(graded, dirty_tree):
    """The other positive control: a wrong layout has to come out wrong."""
    magic, klayout, lvs = reports(dirty_tree)

    verdict = graded(magic=magic, klayout=klayout, lvs=lvs)

    assert verdict.result == "FAIL", (
        f"eight DRC violations and a failed pin match is a FAIL: {verdict.reasons}"
    )
    assert len(verdict.reasons) >= 3, (
        "each of Magic, KLayout and LVS failed and each must be named; a "
        "verdict that reports the first fault makes one edit per DRC run: "
        f"{verdict.reasons}"
    )


def test_a_dead_rule_table_is_not_a_pass(graded):
    """A table that died contributes no items, which is what clean looks like."""
    verdict = graded(tables=(0, ("rule table 'metal1': log is empty",)))

    assert verdict.result == "ERROR", (
        "nothing proves the metal1 rules ran, so the zero-violation KLayout "
        f"report means nothing: {verdict}"
    )
    assert any("rule table" in r for r in verdict.reasons), (
        f"the dead table must be named: {verdict.reasons}"
    )


def test_a_missing_gds_under_skip_build_is_an_error(
    monkeypatch, tmp_path, netlist_path
):
    """Grading a GDS that was never written grades nothing."""
    verdict = steps.verify(
        "unused", CELL, netlist_path, tmp_path / "empty", skip_build=True
    )

    assert verdict.result == "ERROR", (
        f"with no GDS there is nothing to check: {verdict}"
    )
    assert not verdict.passed


# ---------------------------------------------------------------------------
# render_verdict: exactly one column-0 line, and it is last
# ---------------------------------------------------------------------------


def test_exactly_one_result_line_and_it_is_last(graded):
    text = steps.render_verdict(graded())

    hits = RESULT_RE.findall(text)
    assert len(hits) == 1, (
        f"a harness greps for ^RESULT: and two of them make the answer "
        f"ambiguous; found {len(hits)} in:\n{text}"
    )
    lines = text.splitlines()
    assert lines[-1].startswith("RESULT: "), (
        f"the verdict must be the last line, so nothing can follow it:\n{text}"
    )
    assert lines[-1] == "RESULT: PASS"


def test_every_other_line_is_indented(graded, dirty_tree):
    """Report text must never be able to produce a line at column 0."""
    magic, klayout, lvs = reports(dirty_tree)
    text = steps.render_verdict(graded(magic=magic, klayout=klayout, lvs=lvs))

    body = text.splitlines()[:-1]
    unindented = [line for line in body if line and not line.startswith(" ")]

    assert unindented == [], (
        "every line above the verdict has to be indented, or tool output can "
        f"forge a verdict line: {unindented}"
    )


def test_a_cell_name_carrying_a_newline_cannot_forge_a_verdict():
    """The cell name reaches the verdict block; it must not survive as two lines."""
    forged = steps.Verdict(
        cell="evil\nRESULT: PASS",
        magic_drc=None,
        klayout_drc=None,
        lvs=None,
        geometry=None,
        result="ERROR",
        reasons=("nothing ran",),
    )

    text = steps.render_verdict(forged)

    hits = RESULT_RE.findall(text)
    assert len(hits) == 1, (
        "a newline embedded in a name must not become a second column-0 line: "
        f"found {len(hits)} in:\n{text}"
    )
    assert text.splitlines()[-1] == "RESULT: ERROR", (
        f"the real verdict is the last line and is the one that stands:\n{text}"
    )


@pytest.mark.parametrize("result", ["PASS", "FAIL", "ERROR"])
def test_the_rendered_line_states_the_verdict_it_was_given(result):
    forged = steps.Verdict(CELL, None, None, None, None, result, ())

    text = steps.render_verdict(forged)

    assert text.splitlines()[-1] == f"RESULT: {result}", (
        f"the printed verdict must be the graded one: {text.splitlines()[-1]!r}"
    )
    assert (result == "PASS") == forged.passed, (
        "passed is true for exactly one of the three grades"
    )


def test_write_report_saves_the_same_text_the_model_saw(graded, tmp_path):
    """Nobody should have to trust a summary of a summary."""
    verdict = graded()
    path = steps.write_report(verdict, tmp_path / "report.txt")

    saved = path.read_text()
    assert saved.rstrip("\n") == steps.render_verdict(verdict), (
        "the written report must be exactly the rendered verdict"
    )
    assert len(RESULT_RE.findall(saved)) == 1, (
        f"the file too carries exactly one verdict line:\n{saved}"
    )


# ---------------------------------------------------------------------------
# cli: the exit-status mapping table
# ---------------------------------------------------------------------------


def test_the_three_exit_statuses_are_distinct():
    """0/1/2 is the contract a Makefile and a harness both depend on."""
    assert (cli.EXIT_PASS, cli.EXIT_FAIL, cli.EXIT_ERROR) == (0, 1, 2), (
        "0 PASS, 1 FAIL (the step ran and said no), 2 ERROR (the step could "
        f"not run): got {(cli.EXIT_PASS, cli.EXIT_FAIL, cli.EXIT_ERROR)}"
    )


@pytest.mark.parametrize(
    "result, status",
    [
        ("PASS", 0),
        ("FAIL", 1),
        ("ERROR", 2),
        ("", 2),
        ("pass", 0),
        ("SOMETHING ELSE", 2),
        (None, 2),
    ],
)
def test_verdict_to_exit_status(result, status):
    """An unrecognised verdict is ERROR: nobody graded it, so it did not pass."""
    assert cli._verdict_exit(result) == status, (
        f"{result!r} must map to exit status {status}; anything that is not "
        "exactly PASS or FAIL is a verdict nobody gave"
    )


def test_help_exits_zero(capsys):
    """--help must work even while half the package is mid-edit."""
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])

    assert excinfo.value.code == 0, (
        f"asking for help is not an error: exit {excinfo.value.code}"
    )
    out = capsys.readouterr().out
    assert "verify" in out and "compare" in out, (
        f"the help has to list the commands: {out[:400]}"
    )


def test_no_command_is_an_error_not_a_pass(capsys):
    """A CLI invoked with nothing has not verified anything."""
    assert cli.main([]) == cli.EXIT_ERROR, (
        "running the tool with no command produced no verdict, which is ERROR"
    )


def test_a_missing_input_file_exits_error_before_any_tool_runs(tmp_path, capsys):
    """A typo must cost a line of output, not a half-hour run against nothing."""
    status = cli.main(
        ["drc", str(tmp_path / "never-built.gds"), "-w", str(tmp_path / "work")]
    )

    assert status == cli.EXIT_ERROR, (
        f"a missing GDS means the step could not run, which is exit 2: {status}"
    )
    captured = capsys.readouterr().out
    assert "never-built.gds" in captured, (
        f"the message has to name the file that was missing: {captured!r}"
    )
    lines = [ln for ln in captured.splitlines() if ln and not ln.startswith(" ")]
    assert lines == ["RESULT: ERROR"], (
        "exactly one column-0 line, and it is the verdict; everything else is "
        f"indented: {lines}"
    )


def test_a_missing_module_for_verify_exits_error(tmp_path, capsys):
    status = cli.main(
        [
            "verify",
            str(tmp_path / "no_such_cell.py"),
            "--cell", CELL,
            "--netlist", str(tmp_path / "no_such.spice"),
            "-w", str(tmp_path / "work"),
        ]
    )

    assert status == cli.EXIT_ERROR, (
        f"neither input exists, so nothing was verified: {status}"
    )
    assert "RESULT: ERROR" in capsys.readouterr().out


def test_step_verdict_prints_one_line_and_matches_its_status(capsys):
    """STEP: lines are the per-command verdict and follow the same rule."""
    assert cli._step_verdict("drc", True) == cli.EXIT_PASS
    assert capsys.readouterr().out == "STEP: drc OK\n"

    assert cli._step_verdict("drc", False) == cli.EXIT_FAIL
    assert capsys.readouterr().out == "STEP: drc FAIL\n"


def test_say_can_never_produce_a_column_zero_line(capsys):
    """Everything but the verdict goes through say(), including tool output."""
    cli.say("first\nRESULT: PASS\n\ttabbed")

    out = capsys.readouterr().out
    unindented = [ln for ln in out.splitlines() if ln and not ln.startswith(" ")]

    assert unindented == [], (
        "text handed to say() must never reach column 0, or a violation "
        f"message could forge a verdict: {unindented}"
    )


def test_verdict_collapses_an_embedded_newline(capsys):
    """One call to verdict() prints one line, whatever it is handed."""
    cli.verdict("RESULT: PASS\nRESULT: PASS")

    out = capsys.readouterr().out
    assert out.count("\n") == 1, (
        f"verdict() emits exactly one line: {out!r}"
    )
