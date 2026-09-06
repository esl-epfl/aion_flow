# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Regressions for "silence read as success"
# ================================================================

"""An artifact that says nothing must never be graded clean.

This is the one defect the whole harness exists to kill.  The original loop
printed ``Magic : PASS`` over eight real violations because the parser dropped
every coordinate row and then read its own empty result as a clean layout.  Four
adversarial verifiers found the same shape alive in five more places, and each
one is pinned here:

* **F1** a Magic report with no ``[INFO] COUNT:`` trailer -- 0 bytes, header
  only, truncated mid-row, a row with a fifth token, binary garbage, a format
  this parser has never seen -- used to come back ``clean=True``.
* **F13** the same inputs through ``scripts/evidence.py``'s block ``[2]``, which
  is the headline a model reads first.
* **F12** an unreadable ``.lyrdb`` is a whole rule table nobody checked, and used
  to be summarised as ``PASS - 0 items``.
* **F20** ``scripts/generate_cell_doc.py`` printed ``Overall: PASS`` four lines
  under "*No verification reports found*".
* **F22** a zero-byte ``.rpt`` -- what an OOM-killed container leaves -- used to
  satisfy the DRC step as proof the tools had run.

The governing rule every assertion below enforces: only positive evidence of
cleanliness counts as clean.  Absent, empty, truncated, unparsable and merely
not-confirmed are all *not clean*.
"""

from __future__ import annotations

import os
import re

import pytest

from aion_layout.verification import parse_klayout_reports, parse_magic_drc_report
from conftest import CELL, run

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

#: A Magic section header, so the truncated cases are recognisably a *report*
#: rather than an obviously bogus file.  The point of the table is that a file
#: which looks like a real report but never states a count is still not clean.
_MAGIC_HEADER = (
    f"{CELL}\n"
    "----------------------------------------\n"
    "P-diff distance to N-tap must be < 20.0um (LU.a)\n"
    "----------------------------------------\n"
)


def block_body(packet: str, index: int) -> str:
    """Return the body of evidence packet block ``index``.

    Split on the fences by line rather than by ``str.split``: the closing fence
    shares the opening fence's prefix, so a naive split silently truncates the
    block and a test written on it would assert against half the evidence.
    """
    open_fence = f"===== [{index}] "
    close_fence = f"===== [{index}] END "
    body: list[str] = []
    inside = False
    for line in packet.split("\n"):
        if line.startswith(close_fence):
            inside = False
            continue
        if line.startswith(open_fence):
            inside = True
            continue
        if inside:
            body.append(line)
    assert body, f"block [{index}] is absent from the packet:\n{packet[:2000]}"
    return "\n".join(body)


def headline(packet: str, tool: str) -> str:
    """Return block [2]'s one-line verdict for ``tool`` (MAGIC/KLAYOUT/NETGEN)."""
    for line in block_body(packet, 2).split("\n"):
        if line.startswith(f"{tool} DRC") or line.startswith(f"{tool} LVS"):
            return line
    raise AssertionError(
        f"block [2] states no headline for {tool}; the three tool lines are the "
        f"only thing a skimming model is guaranteed to read:\n{block_body(packet, 2)}"
    )


def result_line(packet: str) -> str:
    """Return the single ``^RESULT:`` line the packet is graded on."""
    lines = [ln for ln in packet.split("\n") if ln.startswith("RESULT:")]
    assert len(lines) == 1, (
        f"the packet carries {len(lines)} lines starting at column 0 with "
        f"'RESULT:', expected exactly one: {lines}"
    )
    return lines[0]


# ---------------------------------------------------------------------------
# F1 -- a Magic report with no COUNT trailer is not clean, and not available
# ---------------------------------------------------------------------------

#: Every shape of Magic report that carries no ``[INFO] COUNT:`` trailer.  Each
#: one was returned as ``clean=True`` before D1: the parser found no violation
#: rows and reported the absence of findings as a finding of absence.
TRAILERLESS_MAGIC_REPORTS = [
    pytest.param(b"", id="zero_bytes"),
    pytest.param(b"   \n\n\t\n", id="whitespace_only"),
    pytest.param(_MAGIC_HEADER.encode(), id="header_only"),
    pytest.param(
        (_MAGIC_HEADER + " 0.240um 2.060um 0.775um\n").encode(),
        id="truncated_mid_row",
    ),
    pytest.param(
        (_MAGIC_HEADER + " 0.240um 2.060um 0.775um 3.180um extra\n").encode(),
        id="five_token_row",
    ),
    pytest.param(b"\x00\x01\x02\x7f\xff\xfe\x00 \x8a\x9b garbage \x00", id="binary_garbage"),
    pytest.param(
        b'{"schema": "magic-drc/2", "violations": []}\n', id="future_json_format"
    ),
    pytest.param(
        b"<html><body>504 Gateway Timeout</body></html>\n", id="not_a_report_at_all"
    ),
]


@pytest.mark.parametrize("body", TRAILERLESS_MAGIC_REPORTS)
def test_magic_report_without_a_count_trailer_is_never_clean(tmp_path, body):
    path = tmp_path / f"{CELL}.magic.drc.rpt"
    path.write_bytes(body)

    report = parse_magic_drc_report(path)

    assert report.clean is False, (
        f"a {len(body)}-byte Magic report with no '[INFO] COUNT:' trailer came "
        "back clean=True.  Magic never said it finished, so nothing in this file "
        "is evidence of a clean layout -- this is the exact defect that let a "
        "killed DRC run be graded PASS."
    )
    assert report.available is False, (
        "a report with no COUNT trailer must be marked unavailable, not merely "
        "'clean=False': callers grade an available report on its violation count, "
        "and a count of 0 from a file the tool never finished reads as a pass"
    )
    assert report.degraded is True, (
        "degraded is what every caller checks to decide the run cannot be graded; "
        "leaving it False makes the unavailability invisible downstream"
    )
    assert report.reported_count is None, (
        f"reported_count must stay None when there is no trailer, got "
        f"{report.reported_count}; inventing a count is inventing evidence"
    )
    reason = report.unavailable_reason or ""
    assert "COUNT" in reason, (
        f"the unavailable reason must name the missing trailer, got {reason!r}; a "
        "reason nobody can act on is how a degradation gets ignored"
    )


def test_a_real_count_zero_trailer_is_still_clean(tmp_path):
    """Anti-vacuity control: the table above must not be rejecting everything.

    ``[INFO] COUNT: 0`` is Magic's own positive statement that it ran to the end
    and found nothing.  If this case ever fails with the table, the parser has
    stopped distinguishing "clean" from "unreadable" and no passing layout could
    ever be reported.
    """
    path = tmp_path / f"{CELL}.magic.drc.rpt"
    path.write_text(f"{CELL}\n[INFO] COUNT: 0\n")

    report = parse_magic_drc_report(path)

    assert report.clean is True and report.available is True, (
        "a report carrying Magic's own 'COUNT: 0' is the one legitimately clean "
        "Magic report; rejecting it would make a fixed layout unreportable and "
        "the loop unable to ever terminate"
    )


# ---------------------------------------------------------------------------
# F13 -- the same reports through the evidence packet's block [2] headline
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("body", TRAILERLESS_MAGIC_REPORTS)
def test_packet_headline_never_reads_pass_over_a_trailerless_report(
    evidence, netlist_path, iteration_tree, cell_name, body
):
    """Block [2] is the three lines a model reads first; they must fail closed."""
    iter_dir = iteration_tree()
    rpt = iter_dir / "drc" / f"{cell_name}.magic.drc" / f"{cell_name}.magic.drc.rpt"
    rpt.write_bytes(body)

    packet = evidence.build_evidence(netlist_path, iter_dir, cell_name, None)
    line = headline(packet, "MAGIC")

    assert evidence.STATUS_PASS not in line, (
        f"block [2] headlines a report with no COUNT trailer as {line!r}.  This "
        "line is what the model acts on; the word PASS on it over a report Magic "
        "never finished writing is the original blindness, moved one file over."
    )
    assert line.startswith(f"MAGIC DRC   : {evidence.STATUS_UNAVAILABLE}"), (
        f"expected the headline to open with '{evidence.STATUS_UNAVAILABLE}', got "
        f"{line!r}; the status token is what report_verification.py, the doc "
        "generator and this packet agree on, and a fourth spelling means they "
        "can disagree about the same tree again"
    )
    assert "COUNT" in line, (
        f"the headline must say *why* nothing was read, got {line!r}; without the "
        "reason the model cannot tell a missing run from a dirty layout"
    )
    assert result_line(packet) != "RESULT: PASS", (
        "the packet verdict is PASS while Magic never reported.  Absence of "
        "evidence has never been evidence of absence."
    )


# ---------------------------------------------------------------------------
# F12 -- an unparsable .lyrdb is a rule table nobody checked
# ---------------------------------------------------------------------------

def _blind_the_klayout_run(iter_dir, cell_name):
    """Make every KLayout database item-free, then corrupt exactly one.

    This is the ``PASS - 0 items`` exploit in its purest form: after this the
    only thing standing between the run and a clean verdict is the one rule
    table that could not be read.  Returns the corrupted path.
    """
    klayout_dir = iter_dir / "drc" / f"{cell_name}.klayout.drc"
    databases = sorted(klayout_dir.glob("*.lyrdb"))
    assert len(databases) > 2, f"expected the 31 fixture databases, got {len(databases)}"

    empty = next(p for p in databases if "activ.lyrdb" in p.name).read_bytes()
    for path in databases:
        path.write_bytes(empty)

    corrupted = next(p for p in databases if "latchup" in p.name)
    corrupted.write_text("<report-database><this file was truncated mid-write")
    return corrupted


def test_unparsable_database_makes_the_library_report_unclean(iteration_tree, cell_name):
    iter_dir = iteration_tree()
    _blind_the_klayout_run(iter_dir, cell_name)

    report = parse_klayout_reports(iter_dir, cell_name)

    assert report.unparsed_files == 1, (
        f"the corrupt rule database must be counted, got {report.unparsed_files}; "
        "skipping it silently is how a whole rule table goes unchecked without "
        "anyone being told"
    )
    assert report.error_count == 0, (
        "this fixture is deliberately item-free apart from the unreadable file, "
        "so the test isolates 'unreadable' from 'dirty'"
    )
    assert report.clean is False, (
        "zero items across 30 readable databases plus one that could not be read "
        "is NOT a clean DRC result: the unread table is exactly where the "
        "violation would have been"
    )


def test_unparsable_database_never_headlines_as_pass_zero_items(
    evidence, netlist_path, iteration_tree, cell_name
):
    iter_dir = iteration_tree()
    _blind_the_klayout_run(iter_dir, cell_name)

    packet = evidence.build_evidence(netlist_path, iter_dir, cell_name, None)
    line = headline(packet, "KLAYOUT")

    assert "PASS - 0 items" not in line, (
        f"block [2] reads {line!r} while one rule database could not be parsed.  "
        "'0 items' from a run that never read a table is the same lie as "
        "'0 violations' from a report Magic never finished."
    )
    assert evidence.STATUS_PASS not in line, (
        f"the KLayout headline must not carry the word PASS, got {line!r}"
    )
    assert any(token in line for token in evidence.STATUS_UNVERIFIED), (
        f"expected one of {evidence.STATUS_UNVERIFIED} on the headline, got "
        f"{line!r}; a partially read DRC run is not a graded DRC run"
    )
    assert result_line(packet) != "RESULT: PASS", (
        "the packet verdict must not be PASS while a rule table went unchecked"
    )


def test_unparsable_database_never_passes_the_cli_grader(
    iteration_tree, cell_name, netlist_path
):
    """The same tree through the program pipeline.sh greps for ``^RESULT:``."""
    iter_dir = iteration_tree()
    _blind_the_klayout_run(iter_dir, cell_name)

    proc = run(
        [
            "python3", "scripts/report_verification.py",
            "--cell", cell_name,
            "--gds", str(iter_dir / f"{cell_name}.gds"),
            "--netlist", str(netlist_path),
            "--runs-dir", str(iter_dir),
            "--parse-only",
        ]
    )

    assert proc.returncode != 0, (
        f"report_verification.py exited 0 (PASS) over an unreadable rule "
        f"database:\n{proc.stdout}"
    )
    klayout_lines = [ln for ln in proc.stdout.split("\n") if "KLayout" in ln]
    assert klayout_lines, f"no KLayout line in the summary:\n{proc.stdout}"
    assert not any(" PASS" in ln for ln in klayout_lines), (
        f"a KLayout line reads PASS with one database unread: {klayout_lines}"
    )
    assert "RESULT: FAIL" in proc.stdout, (
        f"expected RESULT: FAIL, got:\n{proc.stdout}"
    )


# ---------------------------------------------------------------------------
# F20 -- the generated cell documentation
# ---------------------------------------------------------------------------

def _overall(markdown: str) -> str:
    match = re.search(r"^\*\*Overall:\*\* (\S+)", markdown, re.M)
    assert match, f"the document states no Overall verdict:\n{markdown[-2000:]}"
    return match.group(1)


def test_cell_doc_over_the_dirty_fixtures_is_not_a_pass(
    tmp_path, iter0_dir, iter0_module, netlist_path, cell_name
):
    out = tmp_path / "cell.md"
    proc = run(
        [
            "python3", "scripts/generate_cell_doc.py",
            "--cell-module", str(iter0_module),
            "--cell-name", cell_name,
            "--netlist", str(netlist_path),
            "-o", str(out),
            "--runs-dir", str(iter0_dir),
        ]
    )
    assert proc.returncode == 0, (
        f"the doc generator failed on the captured artifacts:\n"
        f"{proc.stdout}\n{proc.stderr}"
    )

    markdown = out.read_text()
    assert _overall(markdown) == "FAIL", (
        f"the document grades the captured iteration_0 as "
        f"{_overall(markdown)!r}.  That tree carries 8 Magic violations, 1 "
        "KLayout item and a failed_pin_matching LVS; publishing it as PASS is "
        "how an unverified cell reaches a library."
    )
    assert "**Overall:** PASS" not in markdown, (
        "the string that a human greps for must not appear anywhere in a "
        "document written over a dirty layout"
    )


def test_cell_doc_with_no_reports_at_all_is_an_error_not_a_pass(
    tmp_path, iter0_module, netlist_path, cell_name
):
    """"No verification reports found" four lines above "Overall: PASS"."""
    empty_runs = tmp_path / "runs"
    empty_runs.mkdir()
    out = tmp_path / "cell.md"

    proc = run(
        [
            "python3", "scripts/generate_cell_doc.py",
            "--cell-module", str(iter0_module),
            "--cell-name", cell_name,
            "--netlist", str(netlist_path),
            "-o", str(out),
            "--runs-dir", str(empty_runs),
        ]
    )
    assert proc.returncode == 0, f"the doc generator failed:\n{proc.stderr}"

    markdown = out.read_text()
    assert _overall(markdown) == "ERROR", (
        f"a cell nothing has ever checked is documented as "
        f"{_overall(markdown)!r}; it must be ERROR -- not PASS, and not the "
        "FAIL that would imply something measured a defect"
    )
    for label in ("Magic DRC", "KLayout DRC", "LVS"):
        assert f"**{label}:**" in markdown or f"**{label} (" in markdown, (
            f"the {label} bullet is missing entirely; an artifact that is absent "
            f"must be *stated* as absent, because omitting the line is what left "
            "the verification block empty and the document reading PASS"
        )
    assert "NOT AVAILABLE" in markdown, (
        "no artifact is marked NOT AVAILABLE although none of them exists"
    )


# ---------------------------------------------------------------------------
# F22 -- a zero-byte report is not proof that DRC ran
# ---------------------------------------------------------------------------

def _write_stub_runner(tmp_path, body: str):
    """Write a stand-in for scripts/docker_run.sh.  No container is ever started."""
    stub = tmp_path / "stub_runner.sh"
    stub.write_text("#!/bin/bash\n" + body)
    stub.chmod(0o755)
    return stub


def _drive(repo_root, snippet: str, env: dict | None = None):
    """Source pipeline.sh and run ``snippet`` against it, errexit disabled.

    pipeline.sh sets ``-e`` at source time; without ``set +e`` a step that
    returns non-zero kills the driver before it can report the status, which is
    the very thing under test.
    """
    return run(
        [
            "bash", "-c",
            f'set -uo pipefail\nsource "{repo_root}/pipeline.sh"\nset +e\n{snippet}',
        ],
        env=env or dict(os.environ),
    )


def test_zero_byte_report_does_not_satisfy_the_drc_artifact_gate(
    repo_root, tmp_path, cell_name
):
    """The gate step_drc_at grades on, tested directly."""
    drc = tmp_path / "drc"
    (drc / f"{cell_name}.magic.drc").mkdir(parents=True)
    (drc / f"{cell_name}.klayout.drc").mkdir(parents=True)
    (drc / f"{cell_name}.magic.drc" / f"{cell_name}.magic.drc.rpt").write_bytes(b"")
    (drc / f"{cell_name}.klayout.drc" / f"{cell_name}_x.lyrdb").write_text("<report/>\n")

    proc = _drive(
        repo_root,
        f'pipeline_drc_artifacts_ok "{drc}" "{cell_name}"\n'
        'echo "rc=$?"\n'
        'echo "reason=${PIPELINE_ARTIFACT_REASON}"\n',
    )
    assert "rc=0" not in proc.stdout, (
        f"a zero-byte *.magic.drc.rpt satisfied the DRC artifact gate:\n"
        f"{proc.stdout}{proc.stderr}\nAn OOM-killed container leaves exactly "
        "this file, and accepting it records a DRC run that never happened."
    )
    assert "reason=" in proc.stdout and proc.stdout.split("reason=", 1)[1].strip(), (
        f"the gate rejected the report but said nothing about why:\n{proc.stdout}"
    )


def test_step_drc_rejects_a_run_that_wrote_only_a_zero_byte_report(
    repo_root, tmp_path, cell_name
):
    """End to end through step_drc_at, with the container runner stubbed out."""
    iter_dir = tmp_path / "iter"
    iter_dir.mkdir()
    (iter_dir / f"{cell_name}.gds").write_text("GDS")
    drc = iter_dir / "drc"

    stub = _write_stub_runner(
        tmp_path,
        # Exactly what a container killed between opening the file and writing
        # the report leaves behind: the directories and an empty .rpt.
        'mkdir -p "${STUB_DRC}/${STUB_CELL}.magic.drc" '
        '"${STUB_DRC}/${STUB_CELL}.klayout.drc"\n'
        ': > "${STUB_DRC}/${STUB_CELL}.magic.drc/${STUB_CELL}.magic.drc.rpt"\n'
        'printf \'<report/>\\n\' > '
        '"${STUB_DRC}/${STUB_CELL}.klayout.drc/${STUB_CELL}_x.lyrdb"\n'
        "exit 0\n",
    )

    proc = _drive(
        repo_root,
        f'step_drc_at "{iter_dir / (cell_name + ".gds")}" "{drc}"\necho "rc=$?"\n',
        {
            **os.environ,
            "PIPELINE_RUN_SCRIPT": str(stub),
            "STUB_DRC": str(drc),
            "STUB_CELL": cell_name,
        },
    )

    assert "rc=0" not in proc.stdout, (
        f"step_drc_at reported success over a zero-byte Magic report:\n"
        f"{proc.stdout}{proc.stderr}\nThe step's own contract is that a report "
        "is evidence only when it is non-empty and carries Magic's COUNT trailer."
    )
    assert "no usable DRC evidence" in proc.stderr or "no non-empty" in proc.stderr, (
        f"the failure must name the missing evidence, got:\n{proc.stderr}"
    )
