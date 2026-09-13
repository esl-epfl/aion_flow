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

#: Geometry a cell can be abutted with: rail tap contacts on the shared grid
#: (x = 160 + 480k, one per site).
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
            drawn=ABUTTABLE, abstract=((), ())):
        base_magic, base_klayout, base_lvs = reports(clean_tree)
        monkeypatch.setattr(
            steps, "drc",
            lambda *a, **k: (magic or base_magic, klayout or base_klayout),
        )
        monkeypatch.setattr(steps, "lvs", lambda *a, **k: lvs or base_lvs)
        monkeypatch.setattr(steps, "gds_boundary", lambda *a, **k: geometry)
        monkeypatch.setattr(steps, "klayout_table_logs", lambda *a, **k: tables)
        monkeypatch.setattr(steps, "drawn_shapes", lambda *a, **k: drawn)
        # (errors, failures), as abstract_problems returns them; writing the
        # LEF is a magic run in the container.
        monkeypatch.setattr(
            steps, "abstract_problems",
            lambda *a, **k: (list(abstract[0]), list(abstract[1])),
        )
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


def test_a_pin_the_abstract_leaves_unreachable_fails_in_the_loop(graded):
    """Pin access fails here, in the loop, on the LEF that publishing grades.

    It used to be graded here by a different rule than the one publishing
    applied to the LEF, and the two disagreed: AION_mux2_0 passed verify, was
    refused at publish, and never reached implementation/cells/ with nothing in
    the drawing loop to say why.
    """
    unreachable = (
        "abstract (LEF): PIN I0 has no via access: no ViaN can overlap the port "
        "with its Metal1 enclosure and keep both of its metal shapes clear of "
        "every other net"
    )
    verdict = graded(abstract=((), (unreachable,)))

    assert verdict.result == "FAIL", (
        "magic wrote the LEF and the LEF is wrong: that is FAIL, not ERROR: "
        f"{verdict.result} {verdict.reasons}"
    )
    assert unreachable in verdict.reasons, verdict.reasons


def test_an_abstract_that_could_not_be_written_is_not_a_pass(graded):
    """No LEF is no evidence about pin access, which is ERROR like any other."""
    verdict = graded(
        abstract=(("the abstract (LEF) of X could not be written: magic exited 125",), ())
    )

    assert verdict.result == "ERROR", f"{verdict.result} {verdict.reasons}"
    assert any("could not be written" in r for r in verdict.reasons), verdict.reasons


_ABSTRACT_LEF = f"""\
VERSION 5.7 ;
MACRO {CELL}
  CLASS CORE ;
  SIZE 2.88 BY 3.78 ;
  SITE CoreSite ;
  PIN I0
    PORT
      LAYER Metal1 ;
        RECT 2.220 1.450 2.520 1.790 ;
    END
  END I0
  PIN VDD
    USE POWER ;
    PORT
      LAYER Metal1 ;
        RECT 0.000 3.560 2.880 4.000 ;
    END
  END VDD
  PIN VSS
    USE GROUND ;
    PORT
      LAYER Metal1 ;
        RECT 0.000 -0.220 2.880 0.220 ;
    END
  END VSS
  OBS
      LAYER Metal1 ;
        RECT 1.900 1.450 2.000 1.790 ;
      LAYER Metal2 ;
        RECT 2.525 0.620 2.725 2.710 ;
  END
END {CELL}
END LIBRARY
"""


def test_abstract_problems_grades_the_lef_magic_wrote(monkeypatch, tmp_path):
    """The abstract is graded by the same check_lef that publishing runs."""
    gds = tmp_path / f"{CELL}.gds"
    gds.write_bytes(b"not read: export_lef is replaced")

    def written(gds_path, cell, out, **kwargs):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_ABSTRACT_LEF)
        return out

    monkeypatch.setattr(steps, "export_lef", written)
    errors, failures = steps.abstract_problems(gds, CELL, tmp_path)

    assert errors == []
    assert len(failures) == 1 and "PIN I0" in failures[0], failures
    assert failures[0].startswith("abstract (LEF): "), (
        f"the reason has to say which artifact it is about: {failures}"
    )


def test_abstract_problems_tells_a_refused_lef_from_a_missing_one(monkeypatch, tmp_path):
    """A LEF export_lef refused is a FAIL; a LEF magic never wrote is an ERROR."""
    gds = tmp_path / f"{CELL}.gds"
    gds.write_bytes(b"not read: export_lef is replaced")
    rejected = tmp_path / steps.ABSTRACT_DIR / f"{CELL}.lef.rejected"

    def refused(gds_path, cell, out, **kwargs):
        out.parent.mkdir(parents=True, exist_ok=True)
        rejected.write_text("the LEF that was refused\n")
        raise steps.ExportError("the LEF and the GDS disagree about the size")

    monkeypatch.setattr(steps, "export_lef", refused)
    errors, failures = steps.abstract_problems(gds, CELL, tmp_path)
    assert errors == [] and len(failures) == 1, (errors, failures)
    assert "was refused" in failures[0]

    def no_magic(gds_path, cell, out, **kwargs):
        raise steps.ExportError("magic wrote no LEF (status 125)")

    # The quarantine left by the refusal above must not turn a container that
    # is down into a statement about the cell.
    monkeypatch.setattr(steps, "export_lef", no_magic)
    errors, failures = steps.abstract_problems(gds, CELL, tmp_path)
    assert failures == [] and len(errors) == 1, (errors, failures)
    assert "could not be written" in errors[0]


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
