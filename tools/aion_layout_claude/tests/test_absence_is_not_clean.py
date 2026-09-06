# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Silence is never a pass
# ================================================================

"""The governing rule, applied to every artifact the flow reads.

Absent, empty, truncated, unparseable or merely not-positively-confirmed
evidence is NOT good evidence.  A missing report is an error, never a pass.

The failure this guards against does not look like a bug while it is happening.
A parser finds no violation rows and reports the absence of findings as a
finding of absence; a merge counts items across the files that happen to be
present and cannot notice the rule table that is not; a report planted under
another name answers for the one the tool never wrote.  In each case the flow
prints PASS and the layout is wrong.

Every case below is built in ``tmp_path`` from the committed real artifacts, so
the file starts by proving the real ones grade the way they should -- a suite
that only knows how to fail can pass while detecting nothing at all.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from aion_layout.verification import (
    COMPLETENESS_DEGRADED,
    COMPLETENESS_UNVERIFIED,
    COMPLETENESS_VERIFIED,
    KLAYOUT_RECEIPT_NAME,
    VerificationError,
    canonical_report_dirs,
    locate_magic_drc_report,
    locate_netgen_lvs_report,
    parse_klayout_reports,
    parse_magic_drc_report,
    parse_netgen_lvs_report,
)
from conftest import CELL

MAGIC_RPT = f"{CELL}.magic.drc.rpt"
LVS_OUT = f"{CELL}.lvs.out"

#: A Magic section header, so the truncated cases below are recognisably a
#: *report* rather than obvious rubbish.  The point of the table is that a file
#: which looks like a real report but never states a count is still not clean.
_MAGIC_HEADER = (
    f"{CELL}\n"
    "----------------------------------------\n"
    "P-diff distance to N-tap must be < 20.0um (LU.a)\n"
    "----------------------------------------\n"
)


def magic_dir(tree: Path) -> Path:
    return tree / "drc" / f"{CELL}.magic.drc"


def klayout_dir(tree: Path) -> Path:
    return tree / "drc" / f"{CELL}.klayout.drc"


def lvs_dir(tree: Path) -> Path:
    return tree / "lvs" / f"{CELL}.magic.lvs"


# ---------------------------------------------------------------------------
# Positive controls: the real artifacts grade the way the tools meant them to
# ---------------------------------------------------------------------------


def test_the_real_clean_run_is_clean(clean_tree):
    """Without this, every assertion below could pass by refusing everything."""
    magic = parse_magic_drc_report(magic_dir(clean_tree) / MAGIC_RPT)
    klayout = parse_klayout_reports(clean_tree / "drc", CELL)
    lvs = parse_netgen_lvs_report(lvs_dir(clean_tree) / LVS_OUT)

    assert magic.clean and magic.reported_count == 0, (
        "the captured Magic report says '[INFO] COUNT: 0'; refusing it would "
        f"make the flow unable to ever pass: {magic}"
    )
    assert klayout.clean and klayout.completeness == COMPLETENESS_VERIFIED, (
        "the captured KLayout run has zero items and a receipt that matches "
        f"the databases on disk, which is the only shape of a clean DRC: {klayout}"
    )
    assert lvs.clean and lvs.verdict == "match_uniquely", (
        f"the captured Netgen report says 'Circuits match uniquely': {lvs}"
    )
    assert not magic.degraded and not klayout.degraded, (
        "a fully evidenced report is not degraded"
    )


def test_the_real_dirty_run_is_found_dirty(dirty_tree):
    """Violations that ARE there must be reported, with their coordinates."""
    magic = parse_magic_drc_report(magic_dir(dirty_tree) / MAGIC_RPT)
    klayout = parse_klayout_reports(dirty_tree / "drc", CELL)
    lvs = parse_netgen_lvs_report(lvs_dir(dirty_tree) / LVS_OUT)

    assert magic.reported_count == 8 and magic.error_count == 8, (
        "Magic's own trailer says 8; parsing fewer rows than the tool counted "
        f"is the exact defect this harness exists to kill: {magic}"
    )
    assert not magic.clean, "a report with 8 violations is not clean"
    assert {"LU.a", "LU.b"} <= {
        c.split("(")[-1].rstrip(")") for c in magic.categories
    }, (
        "the latch-up rules that fired have to be named, or the report cannot "
        f"be acted on: {magic.categories}"
    )
    assert all(v.bbox_um != (0, 0, 0, 0) for v in magic.violations), (
        "every violation carries the bounding box Magic printed; a row parsed "
        "without coordinates cannot be found in the layout"
    )

    assert klayout.error_count == 1 and not klayout.clean, (
        f"the captured KLayout database holds one LU.b item: {klayout}"
    )
    assert klayout.completeness == COMPLETENESS_VERIFIED, (
        "this run IS complete -- the receipt matches -- and must be refused "
        "for the violation it found, not for a missing file; conflating the "
        f"two hides real violations behind plumbing errors: {klayout}"
    )
    assert not lvs.clean and lvs.verdict == "failed_pin_matching", (
        f"the captured Netgen report failed pin matching: {lvs}"
    )
    assert lvs.unmatched_pins, (
        "the pins that failed to match are the whole content of the finding "
        "and must survive parsing"
    )


# ---------------------------------------------------------------------------
# Magic: a report with no '[INFO] COUNT:' trailer never said anything
# ---------------------------------------------------------------------------

TRAILERLESS = [
    pytest.param(b"", id="zero_bytes"),
    pytest.param(b"   \n\n\t\n", id="whitespace_only"),
    pytest.param(_MAGIC_HEADER.encode(), id="header_only"),
    pytest.param(
        (_MAGIC_HEADER + " 0.240um 2.060um 0.775um\n").encode(),
        id="truncated_mid_row",
    ),
    pytest.param(
        (_MAGIC_HEADER + " 0.240um 2.060um 0.775um 3.180um\n").encode(),
        id="rows_but_no_count",
    ),
    pytest.param(b"\x00\x01\x02\xff\xfe binary garbage \x00", id="binary_garbage"),
    pytest.param(
        b'{"drc": {"violations": 0, "status": "clean"}}\n', id="unknown_format"
    ),
]


@pytest.mark.parametrize("payload", TRAILERLESS)
def test_magic_report_without_a_count_trailer_is_not_clean(tmp_path, payload):
    """Nothing in such a file says Magic ran to completion, so nothing passed."""
    path = tmp_path / MAGIC_RPT
    path.write_bytes(payload)

    report = parse_magic_drc_report(path)

    assert not report.clean, (
        "a Magic report with no '[INFO] COUNT:' trailer is empty, truncated or "
        "in an unknown format; reading it as a clean layout is reading silence "
        f"as a pass ({len(payload)} bytes)"
    )
    assert not report.available, (
        "the report carries no evidence the tool finished, so it must be "
        "marked unavailable rather than merely violation-free"
    )
    assert report.reported_count is None, (
        "there is no count to report; a 0 here would be the parser inventing "
        "the verdict the tool never gave"
    )
    assert report.unavailable_reason, (
        "an unavailable report must say why, or the flow reports a missing "
        "artifact with no way to tell a crash from an empty directory"
    )
    assert report.degraded, "an unavailable report is by definition degraded"


def test_magic_report_that_counts_more_than_it_shows_refuses_to_grade(tmp_path):
    """A trailer of 8 over zero parseable rows means the parser went blind."""
    path = tmp_path / MAGIC_RPT
    path.write_text(f"{CELL}\n[INFO] COUNT: 8\n")

    with pytest.raises(VerificationError) as excinfo:
        parse_magic_drc_report(path)

    assert "8" in str(excinfo.value), (
        "the refusal must quote the count Magic gave, so the mismatch between "
        f"what the tool said and what was parsed is visible: {excinfo.value}"
    )


def test_a_missing_magic_report_raises(tmp_path):
    """An absent report is an error; there is nothing to be clean about."""
    with pytest.raises(VerificationError):
        parse_magic_drc_report(tmp_path / "not-there.rpt")

    (tmp_path / "drc" / f"{CELL}.magic.drc").mkdir(parents=True)
    with pytest.raises(VerificationError) as excinfo:
        locate_magic_drc_report(tmp_path, CELL)

    assert MAGIC_RPT in str(excinfo.value), (
        "the error has to name the file it expected, so a reader can tell a "
        f"tool that never ran from one that wrote elsewhere: {excinfo.value}"
    )


def test_magic_report_under_a_name_magic_does_not_write_is_never_clean(work_tree):
    """A planted 'COUNT: 0' is not Magic saying the layout is clean."""
    tree = work_tree("clean")
    (magic_dir(tree) / MAGIC_RPT).rename(magic_dir(tree) / "planted.magic.drc.rpt")

    path, note = locate_magic_drc_report(tree / "drc", CELL)
    report = parse_magic_drc_report(path, location_note=note)

    assert note, (
        "a report read under a name the tool does not write must come back "
        "with a note; accepting it silently is how a planted file wins"
    )
    assert report.reported_count == 0, (
        "the contents are still reported -- the note is about provenance, not "
        "about discarding evidence"
    )
    assert not report.clean, (
        "a file nobody can attribute to Magic cannot be graded clean, whatever "
        f"its trailer says: {report.location_note}"
    )
    assert report.completeness == COMPLETENESS_DEGRADED, (
        f"an unattributable report is degraded evidence: {report.completeness}"
    )


def test_two_unnamed_magic_reports_refuse_to_pick_one(work_tree):
    """Choosing the first of a sorted list is how a planted file outranks the real one."""
    tree = work_tree("clean")
    real = magic_dir(tree) / MAGIC_RPT
    shutil.copy(real, magic_dir(tree) / "a.magic.drc.rpt")
    real.rename(magic_dir(tree) / "b.magic.drc.rpt")

    with pytest.raises(VerificationError) as excinfo:
        locate_magic_drc_report(tree / "drc", CELL)

    assert "refusing to guess" in str(excinfo.value), (
        "with two candidates and no canonical name the only safe answer is to "
        f"refuse: {excinfo.value}"
    )


def test_two_canonical_directories_refuse_to_pick_one(work_tree):
    """Exactly one directory is the run's; guessing costs a false PASS."""
    tree = work_tree("clean")
    shutil.copytree(magic_dir(tree), tree / "drc" / "drc" / f"{CELL}.magic.drc")

    with pytest.raises(VerificationError) as excinfo:
        locate_magic_drc_report(tree / "drc", CELL)

    assert "canonical directories" in str(excinfo.value), (
        f"the ambiguity must be named as such: {excinfo.value}"
    )


def test_a_cell_name_with_a_separator_is_refused(tmp_path):
    """A name with a path in it would point discovery anywhere at all."""
    with pytest.raises(VerificationError) as excinfo:
        canonical_report_dirs(tmp_path, "../../etc", "magic.drc")

    assert "single path component" in str(excinfo.value), (
        f"the refusal must say why the name is rejected: {excinfo.value}"
    )


# ---------------------------------------------------------------------------
# KLayout: counting the files that are present cannot notice the one that is not
# ---------------------------------------------------------------------------


def test_klayout_directory_with_no_receipt_is_not_clean(work_tree):
    """Zero items across an unknown set of files is not zero violations."""
    tree = work_tree("clean")
    (klayout_dir(tree) / KLAYOUT_RECEIPT_NAME).unlink()

    report = parse_klayout_reports(tree / "drc", CELL)

    assert report.error_count == 0, (
        "the databases still hold no items; the objection is to their extent, "
        "not their contents"
    )
    assert report.completeness == COMPLETENESS_UNVERIFIED, (
        "with no receipt nothing records the database set the run wrote, so "
        f"completeness is unverified, not verified: {report.completeness}"
    )
    assert not report.clean, (
        "a zero-item result over a database set nobody vouched for is exactly "
        "how deleting a rule table used to turn a violation into a pass"
    )
    assert report.degraded and report.completeness_note, (
        "the report must say, in words, that the missing receipt is why it "
        f"cannot pass: {report.completeness_note!r}"
    )


def test_receipt_naming_a_database_that_is_not_there_is_not_clean(work_tree):
    """A rule table the run wrote and the merge never read is a rule unchecked."""
    tree = work_tree("clean")
    receipt_path = klayout_dir(tree) / KLAYOUT_RECEIPT_NAME
    receipt = json.loads(receipt_path.read_text())
    receipt["databases"].append(f"{CELL}_{CELL}_latchup.lyrdb")
    receipt_path.write_text(json.dumps(receipt, indent=2))

    report = parse_klayout_reports(tree / "drc", CELL)

    assert report.completeness == COMPLETENESS_DEGRADED, (
        "a receipt that does not match the disk describes a run that broke or "
        f"a directory that was edited: {report.completeness}"
    )
    assert "latchup" in " ".join(report.missing_databases), (
        "the missing database has to be named, or nobody can tell which rule "
        f"went unchecked: {report.missing_databases}"
    )
    assert not report.clean, (
        "the latch-up table is exactly the one the real failing run tripped; a "
        "merge that cannot see it must not report a clean layout"
    )


def test_a_database_the_receipt_does_not_name_is_not_clean(work_tree):
    """A file that appeared from nowhere makes the whole set unattributable."""
    tree = work_tree("clean")
    source = next(klayout_dir(tree).glob("*.lyrdb"))
    shutil.copy(source, klayout_dir(tree) / f"{CELL}_{CELL}_planted.lyrdb")

    report = parse_klayout_reports(tree / "drc", CELL)

    assert report.completeness == COMPLETENESS_DEGRADED, (
        f"an unexpected database degrades the run's extent: {report.completeness}"
    )
    assert not report.clean, (
        "a merge over files the run did not write is not the run's result"
    )


@pytest.mark.parametrize(
    "exit_status, why",
    [
        (2, "a runner that exited 2 neither ran clean nor found violations"),
        ("0", "a non-integer status is not a status"),
        (None, "a receipt with no status records nothing about the run"),
        (True, "a boolean is not an exit status, however int-like it looks"),
    ],
)
def test_receipt_whose_run_did_not_finish_is_not_clean(work_tree, exit_status, why):
    """The receipt has to say the runner finished, not merely that it started."""
    tree = work_tree("clean")
    receipt_path = klayout_dir(tree) / KLAYOUT_RECEIPT_NAME
    receipt = json.loads(receipt_path.read_text())
    receipt["exit_status"] = exit_status
    receipt_path.write_text(json.dumps(receipt, indent=2))

    report = parse_klayout_reports(tree / "drc", CELL)

    assert report.completeness == COMPLETENESS_DEGRADED, why
    assert not report.clean, f"{why}; a zero-item merge over it is not a pass"


@pytest.mark.parametrize(
    "payload, why",
    [
        ("not json at all", "a receipt that cannot be parsed vouches for nothing"),
        ("[]", "a JSON array is not the receipt object the runner writes"),
        ('{"exit_status": 0}', "a receipt with no 'databases' list names no files"),
        (
            '{"exit_status": 0, "databases": "one.lyrdb"}',
            "a string is not a list of file names",
        ),
    ],
)
def test_unusable_receipt_is_degraded_not_absent(work_tree, payload, why):
    """A receipt that exists and cannot be used is a break, not a missing file."""
    tree = work_tree("clean")
    (klayout_dir(tree) / KLAYOUT_RECEIPT_NAME).write_text(payload)

    report = parse_klayout_reports(tree / "drc", CELL)

    assert report.completeness == COMPLETENESS_DEGRADED, (
        f"{why}, and a broken receipt is worse news than none: "
        f"{report.completeness}"
    )
    assert not report.clean, why


def test_an_unreadable_database_is_a_rule_table_nobody_checked(work_tree):
    """A .lyrdb that will not parse is an unchecked rule, not an empty one."""
    tree = work_tree("clean")
    next(klayout_dir(tree).glob("*.lyrdb")).write_text("<report-database><oops>")

    report = parse_klayout_reports(tree / "drc", CELL)

    assert report.unparsed_files == 1, (
        "the file that could not be read has to be counted; skipping it "
        f"silently turns a whole rule table into 0 violations: {report}"
    )
    assert not report.clean, (
        "a merge that could not read one of its databases has not checked the "
        "rules in it"
    )
    assert report.degraded


def test_a_klayout_directory_with_no_databases_is_unavailable(work_tree):
    """A KLayout run that produced nothing is a degradation, not a pass."""
    tree = work_tree("clean")
    for path in klayout_dir(tree).glob("*.lyrdb"):
        path.unlink()

    report = parse_klayout_reports(tree / "drc", CELL)

    assert not report.available, (
        "no databases at all means KLayout did not run; that is not the same "
        f"as running and finding nothing: {report}"
    )
    assert not report.clean and report.unavailable_reason, (
        "the report must say no databases were found, in the canonical place "
        f"it looked: {report.unavailable_reason!r}"
    )


def test_databases_read_from_a_non_canonical_directory_are_never_clean(
    tmp_path, clean_tree
):
    """Files in a directory no tool writes are not a set anyone vouched for."""
    planted = tmp_path / "planted"
    planted.mkdir()
    for path in (clean_tree / "drc" / f"{CELL}.klayout.drc").iterdir():
        shutil.copy(path, planted / path.name)

    report = parse_klayout_reports(planted, CELL)

    assert report.location_note, (
        "reading from a non-canonical directory must be recorded, even though "
        "it was the caller's own choice to point there"
    )
    assert report.completeness == COMPLETENESS_DEGRADED, (
        "a receipt sitting beside planted files does not make them the run's "
        f"output: {report.completeness}"
    )
    assert not report.clean, (
        "the same zero items, in a directory no tool writes, is not a pass"
    )


# ---------------------------------------------------------------------------
# Netgen: no 'Final result:' line means Netgen never gave a verdict
# ---------------------------------------------------------------------------

NO_VERDICT = [
    pytest.param("", id="zero_bytes"),
    pytest.param("\n\n   \n", id="whitespace_only"),
    pytest.param(
        "Circuit 1 cell sg13_lv_nmos and Circuit 2 cell sg13_lv_nmos are black boxes.\n",
        id="header_only",
    ),
    pytest.param(
        "Subcircuit summary:\n"
        f"Circuit 1: {CELL}   |Circuit 2: {CELL}\n"
        "Number of devices: 8                       |Number of devices: 8\n",
        id="truncated_before_the_verdict",
    ),
    pytest.param("Netlists match uniquely.\n", id="match_line_without_final_result"),
]


@pytest.mark.parametrize("payload", NO_VERDICT)
def test_netgen_report_without_a_final_result_is_not_clean(tmp_path, payload):
    """Netgen states its verdict on one line; without it there is no verdict."""
    path = tmp_path / LVS_OUT
    path.write_text(payload)

    report = parse_netgen_lvs_report(path)

    assert report.verdict == "no_final_result", (
        "a report with no 'Final result:' line has to be classified as having "
        f"none, not as uncertain or as a match: {report.verdict}"
    )
    assert not report.clean, (
        "LVS is only clean when Netgen itself said the circuits match "
        "uniquely; a per-subcircuit 'Netlists match uniquely.' partway through "
        "the file is not the top-level verdict"
    )
    assert report.message, "a refusal must carry a reason a human can read"


@pytest.mark.parametrize(
    "final, expected",
    [
        ("Circuits match uniquely.", "match_uniquely"),
        ("Circuits do not match.", "do_not_match"),
        ("Top level cell failed pin matching.", "failed_pin_matching"),
        ("Circuits match uniquely with property errors.", "match_with_warnings"),
    ],
)
def test_netgen_verdicts_are_classified_not_pattern_matched(
    tmp_path, final, expected
):
    """Only one of the four sentences Netgen writes is a pass."""
    path = tmp_path / LVS_OUT
    path.write_text(f"Final result: {final}\n")

    report = parse_netgen_lvs_report(path)

    assert report.verdict == expected, (
        f"{final!r} classifies as {expected!r}, got {report.verdict!r}"
    )
    assert report.clean == (expected == "match_uniquely"), (
        "'match uniquely' is the only clean LVS verdict; 'match uniquely with "
        "property errors' is a warning a human has to read"
    )


def test_only_the_last_final_result_is_the_verdict(tmp_path):
    """Netgen prints one per compared cell; the top level is the last."""
    path = tmp_path / LVS_OUT
    path.write_text(
        "Final result: Circuits match uniquely.\n"
        "Final result: Circuits do not match.\n"
    )

    report = parse_netgen_lvs_report(path)

    assert report.verdict == "do_not_match", (
        "grading on the first verdict lets a matching sub-cell answer for a "
        f"top level that did not match: {report.verdict}"
    )
    assert not report.clean


def test_a_missing_netgen_report_raises(tmp_path):
    """An absent LVS report is an error, not an unmatched-but-tolerable run."""
    with pytest.raises(VerificationError):
        parse_netgen_lvs_report(tmp_path / "not-there.lvs.out")

    (tmp_path / "lvs" / f"{CELL}.magic.lvs").mkdir(parents=True)
    with pytest.raises(VerificationError) as excinfo:
        locate_netgen_lvs_report(tmp_path, CELL)
    assert LVS_OUT in str(excinfo.value), (
        f"the error must name the file it expected: {excinfo.value}"
    )


def test_netgen_report_under_a_name_netgen_does_not_write_is_never_clean(work_tree):
    """A 'match uniquely' nobody can attribute to Netgen is not a pass."""
    tree = work_tree("clean")
    (lvs_dir(tree) / LVS_OUT).rename(lvs_dir(tree) / "planted.lvs.out")

    path, note = locate_netgen_lvs_report(tree / "lvs", CELL)
    report = parse_netgen_lvs_report(path, location_note=note)

    assert note, "a non-canonical file name must be recorded"
    assert report.verdict == "match_uniquely", (
        "the contents are still read; the objection is to provenance"
    )
    assert not report.clean, (
        "clean requires both the verdict and a file the tool itself named: "
        f"{report.location_note}"
    )


def test_lvs_out_is_preferred_over_the_log_fallback(work_tree):
    """Two files, one canonical name: the canonical one wins with no note."""
    tree = work_tree("clean")
    shutil.copy(lvs_dir(tree) / LVS_OUT, lvs_dir(tree) / f"{CELL}.lvs.log")

    path, note = locate_netgen_lvs_report(tree / "lvs", CELL)

    assert path.name == LVS_OUT, (
        f"*.lvs.out is what sak-lvs.sh writes and must win: {path.name}"
    )
    assert note == "", (
        f"the canonical file needs no caveat: {note!r}"
    )
