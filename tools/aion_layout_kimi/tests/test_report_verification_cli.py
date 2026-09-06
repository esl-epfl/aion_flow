# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               End-to-end tests for scripts/report_verification.py
# ================================================================

"""``report_verification.py`` must never exit without printing a verdict.

The historical defect, reproduced by ``tests/fixtures/iteration_0/report.txt``:
the program looked for a ``*_full.lyrdb`` that ``sak-drc.sh -l macro`` never
writes, raised ``FileNotFoundError`` after printing only the ``Cell:`` header,
and left a 918-byte report with no ``DRC:``, no ``LVS:`` and no ``RESULT:`` line
in it.  ``pipeline.sh`` then grepped that file for ``^(DRC|LVS|RESULT):`` and
injected the result -- three characters -- into the prompt.  Silence read as
success and the loop was blind.
"""

from __future__ import annotations

import re
import sys

from conftest import run

RESULT_RE = re.compile(r"^RESULT:\s*(PASS|FAIL|ERROR)\s*$", re.MULTILINE)


def _report_cli(cell, runs_dir, netlist, gds="/nonexistent.gds"):
    return run(
        [
            sys.executable,
            "scripts/report_verification.py",
            "--cell", cell,
            "--gds", str(gds),
            "--netlist", str(netlist),
            "--runs-dir", str(runs_dir),
            "--parse-only",
        ]
    )


# ---------------------------------------------------------------------------
# The artifact that proves the regression
# ---------------------------------------------------------------------------

def test_captured_report_txt_has_no_verdict(broken_report_txt):
    """The fixture is the broken output; assert it really is verdict-free."""
    text = broken_report_txt.read_text(errors="replace")
    assert RESULT_RE.search(text) is None, (
        "tests/fixtures/iteration_0/report.txt is the captured 918-byte artifact "
        "with no verdict; if it grew a RESULT: line the fixture was regenerated "
        "and no longer reproduces the regression this file guards"
    )
    assert not re.search(r"^DRC:", text, re.MULTILINE), (
        "the captured report has no DRC: line either -- it stops after the "
        "Cell:/GDS:/Netlist: header"
    )
    assert "Cell:" in text, (
        "the captured report does contain the header; the bug is what is "
        "missing after it, not that nothing was written"
    )
    assert len(text.encode("utf-8")) < 1200, (
        f"the captured artifact is 918 bytes, got {len(text.encode('utf-8'))}"
    )


# ---------------------------------------------------------------------------
# The fixed code path, on the same artifacts
# ---------------------------------------------------------------------------

def test_fixtures_produce_a_fail_verdict(cell_name, iter0_dir, netlist_path):
    proc = _report_cli(cell_name, iter0_dir, netlist_path)
    match = RESULT_RE.search(proc.stdout)
    assert match is not None, (
        f"no ^RESULT: line in:\n{proc.stdout}\n---stderr---\n{proc.stderr}\n"
        "This is the exact regression that produced the verdict-free "
        "report.txt: the program must always end with a verdict"
    )
    assert match.group(1) == "FAIL", (
        f"the captured iteration has 8 Magic violations, 1 KLayout item and a "
        f"failed LVS, so the verdict is FAIL, got {match.group(1)}"
    )
    assert proc.returncode == 1, (
        f"exit status must be 1 for FAIL (0 PASS / 1 FAIL / 2 ERROR), got "
        f"{proc.returncode}; the shell gate keys off this status"
    )
    assert proc.stdout.rstrip().splitlines()[-1].startswith("RESULT:"), (
        "RESULT: must be the last line so the harness can parse the outcome "
        "even when everything before it went wrong"
    )


def test_fixtures_report_the_magic_violations(cell_name, iter0_dir, netlist_path):
    out = _report_cli(cell_name, iter0_dir, netlist_path).stdout
    assert re.search(r"^DRC:\s+FAIL", out, re.MULTILINE), (
        f"the DRC: header line must be greppable and say FAIL, got:\n{out}"
    )
    assert "magic=8" in out, (
        f"the DRC header must carry Magic's 8 violations, got:\n{out}; a zero "
        "here is the float('0.240um') parser going blind again"
    )
    assert "klayout=1" in out, (
        f"the DRC header must carry KLayout's single merged item, got:\n{out}; "
        "a 'NO REPORT' here means the 31 per-rule-table databases were not merged"
    )
    assert "COUNT: 8" in out, (
        "Magic's own trailer count must be echoed so a parser that went blind "
        "is visible as a disagreement rather than as a clean layout"
    )
    assert out.count("LU.a") >= 1 and out.count("LU.b") >= 1, (
        f"both latch-up rule codes must reach the reader, got:\n{out}; they are "
        "the whole diagnosis (missing well/substrate taps)"
    )
    assert "31 rule databases" in out, (
        f"the report must say how many databases were scanned, got:\n{out}; "
        "otherwise 'klayout=0' cannot be told apart from 'klayout never ran'"
    )


def test_fixtures_report_the_device_mismatch(cell_name, iter0_dir, netlist_path):
    out = _report_cli(cell_name, iter0_dir, netlist_path).stdout
    assert re.search(r"^LVS:\s+FAIL", out, re.MULTILINE), (
        f"the LVS: header line must be greppable and say FAIL, got:\n{out}"
    )
    assert "verdict=failed_pin_matching" in out, (
        f"the classified verdict must be printed, got:\n{out}"
    )
    assert "layout=3 schematic=4" in out, (
        f"the per-type 3-vs-4 device mismatch must be printed, got:\n{out}; it "
        "is what tells the model a device is missing rather than miswired"
    )
    assert "layout=6 schematic=8" in out, (
        f"the device totals must be printed, got:\n{out}"
    )
    assert "MISMATCH" in out, (
        "a mismatched count must be labelled, not left for the reader to compare"
    )
    assert "disconnected nodes" in out, (
        f"the disconnected nodes must be listed, got:\n{out}"
    )


# ---------------------------------------------------------------------------
# The failure paths
# ---------------------------------------------------------------------------

def test_empty_runs_dir_still_prints_a_verdict_block(cell_name, netlist_path, tmp_path):
    """An empty runs-dir must give RESULT: ERROR, never a bare header."""
    proc = _report_cli(cell_name, tmp_path, netlist_path)
    match = RESULT_RE.search(proc.stdout)
    assert match is not None, (
        f"an empty runs-dir printed no verdict:\n{proc.stdout}\n"
        "This is precisely how the 918-byte report.txt was produced -- the "
        "program raised after the header and the loop saw nothing"
    )
    assert match.group(1) == "ERROR", (
        f"'could not verify' must be ERROR, never PASS or FAIL, got "
        f"{match.group(1)}; conflating it with a result is what let an "
        "unverified layout be graded"
    )
    assert proc.returncode == 2, (
        f"exit status must be 2 for ERROR, got {proc.returncode}; the shell "
        "distinguishes 'verified and failed' (1) from 'could not verify' (2)"
    )
    assert re.search(r"^DRC:\s+ERROR", proc.stdout, re.MULTILINE), (
        f"the DRC: line must still be printed on the error path, got:\n"
        f"{proc.stdout}; pipeline.sh greps for it"
    )
    assert re.search(r"^LVS:\s+ERROR", proc.stdout, re.MULTILINE), (
        f"the LVS: line must still be printed on the error path, got:\n{proc.stdout}"
    )
    assert "Traceback:" in proc.stdout, (
        f"the traceback must be in stdout, not only stderr, got:\n{proc.stdout}; "
        "stdout is the only stream the report file captures"
    )
    assert "magic.drc.rpt" in proc.stdout, (
        "the error must name what was looked for, so the reader can tell a "
        "missing run from a renamed artifact"
    )


def test_error_output_is_more_than_the_header(cell_name, netlist_path, tmp_path):
    """Byte-for-byte guard against regressing to the captured 918-byte report."""
    proc = _report_cli(cell_name, tmp_path, netlist_path)
    after_header = proc.stdout.split("Runs dir:", 1)[-1]
    assert len(after_header.strip().splitlines()) > 5, (
        f"the error path emitted only:\n{proc.stdout}\nA run that stops after "
        "the Cell:/GDS:/Netlist:/Runs dir: header is the exact artifact in "
        "tests/fixtures/iteration_0/report.txt"
    )


def test_drc_present_but_lvs_missing_is_an_error(cell_name, iter0_dir, netlist_path, tmp_path):
    """A half-run must not be graded: the missing half carries the verdict."""
    runs = tmp_path / "runs"
    (runs / "drc").mkdir(parents=True)
    src = iter0_dir / "drc"
    for path in src.rglob("*.rpt"):
        target = runs / "drc" / path.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())

    proc = _report_cli(cell_name, runs, netlist_path)
    match = RESULT_RE.search(proc.stdout)
    assert match is not None and match.group(1) == "ERROR", (
        f"a run with DRC but no Netgen report must be ERROR, got "
        f"{match.group(1) if match else None}:\n{proc.stdout}; reporting only "
        "the half that ran is how a layout nothing checked could pass"
    )
    assert proc.returncode == 2, f"expected exit 2, got {proc.returncode}"


def test_bad_command_line_still_prints_a_verdict():
    proc = run([sys.executable, "scripts/report_verification.py", "--cell"])
    match = RESULT_RE.search(proc.stdout)
    assert match is not None and match.group(1) == "ERROR", (
        f"even argparse rejecting the command line must end in RESULT: ERROR, "
        f"got:\n{proc.stdout}\n{proc.stderr}\nEvery exit path has to leave a "
        "verdict, or the harness cannot tell what happened"
    )
    assert proc.returncode == 2, f"expected exit 2, got {proc.returncode}"


def test_help_exits_zero_without_a_false_verdict():
    proc = run([sys.executable, "scripts/report_verification.py", "--help"])
    assert proc.returncode == 0, "--help must exit 0"
    assert RESULT_RE.search(proc.stdout) is None, (
        "--help must not print a RESULT: line; a verdict emitted by a help "
        "screen would be scraped by the harness as a real grade"
    )
