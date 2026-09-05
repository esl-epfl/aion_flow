# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Golden tests for KLayout .lyrdb merging
# ================================================================

"""KLayout at ``sak-drc.sh -l macro`` writes one database *per rule table*.

The historical defect: the report step looked for a single ``*_full.lyrdb``,
which that level never writes.  It raised ``FileNotFoundError`` after printing
only the ``Cell:`` header, and the loop was handed a report with no verdict in
it at all.  The 31 per-table databases have to be merged instead.
"""

from __future__ import annotations

import pytest

from aion_layout.verification import (
    VerificationError,
    parse_klayout_lyrdb,
    parse_klayout_reports,
)


def test_no_full_lyrdb_exists_in_the_fixture(klayout_dir):
    """The premise of the whole merge: the file the old code wanted is absent."""
    full = list(klayout_dir.rglob("*_full.lyrdb"))
    assert full == [], (
        f"the fixture must keep reproducing the real macro-level output, but "
        f"found {full}; if a combined database appears the regression this "
        "suite guards can no longer be reproduced"
    )
    assert len(list(klayout_dir.rglob("*.lyrdb"))) == 31, (
        "the captured run wrote exactly 31 per-rule-table databases; the merge "
        "must be exercised against all of them"
    )


def test_merged_report_has_exactly_one_violation(klayout_dir, cell_name):
    report = parse_klayout_reports(klayout_dir, cell_name)
    assert report.available is True, (
        "31 databases are present, so the report is available; reporting it "
        "missing is the *_full.lyrdb lookup failing again"
    )
    assert report.error_count == 1, (
        f"expected the single measured KLayout item, got {report.error_count}; "
        "0 means only one (empty) database was read instead of all 31"
    )
    assert report.clean is False, (
        "one item is not clean; a clean verdict here would let the loop stop on "
        "a layout with an unfixed latch-up violation"
    )


def test_merged_violation_is_the_latchup_rule(klayout_dir, cell_name):
    report = parse_klayout_reports(klayout_dir, cell_name)
    violation = report.violations[0]
    assert violation.category == "LU.b", (
        f"the only KLayout item is the LU.b latch-up rule, got "
        f"{violation.category!r}; the category is what tells the model it needs "
        "a substrate tap rather than a spacing change"
    )
    assert report.categories == ["LU.b"], (
        f"only categories that carry an item are interesting, got "
        f"{report.categories}; listing all 31 declared rule categories would "
        "bury the one real finding"
    )
    assert violation.bbox_um == pytest.approx((0.240, 0.590, 2.640, 1.330)), (
        f"the item bbox must come out of the <values> polygon, got "
        f"{violation.bbox_um}; an all-zero bbox means the polygon fallback broke"
    )
    assert "LU.b" in violation.description, (
        "the rule-table description must be carried over from <category>; "
        "without it the model sees a bare code and no rule text"
    )


def test_thirty_of_thirty_one_databases_are_empty(klayout_dir, cell_name):
    """Merging must tolerate the 30 empty databases without counting them."""
    per_file = {
        path.name: len(parse_klayout_lyrdb(path).violations)
        for path in sorted(klayout_dir.rglob("*.lyrdb"))
    }
    non_empty = {name: n for name, n in per_file.items() if n}
    assert list(non_empty.values()) == [1], (
        f"exactly one database carries an item, got {non_empty}; more would mean "
        "the fixture changed, fewer that the XML item scan stopped working"
    )
    assert "latchup" in next(iter(non_empty)), (
        f"the non-empty database is the latch-up rule table, got "
        f"{next(iter(non_empty))!r}"
    )
    report = parse_klayout_reports(klayout_dir, cell_name)
    assert report.unparsed_files == 0, (
        f"{report.unparsed_files} database(s) failed to parse; an unparsed file "
        "silently removes a whole rule table from the verdict"
    )


def test_empty_directory_is_unavailable_not_an_exception(tmp_path):
    report = parse_klayout_reports(tmp_path, "AnyCell")
    assert report.available is False, (
        "a directory with no *.lyrdb must report available=False; raising here "
        "is what aborted the report step after the Cell: header and produced a "
        "verdict-free report.txt"
    )
    assert report.clean is False, (
        "a KLayout run that produced nothing is not a pass -- absence is never "
        "evidence of a clean layout"
    )
    assert report.violations == [] and report.error_count == 0, (
        "an unavailable report carries no violations; it must be distinguished "
        "by `available`, not by an empty list that reads like success"
    )


def test_unreadable_database_is_counted_not_fatal(tmp_path, klayout_dir):
    """One corrupt file must not delete the findings of the other 30."""
    work = tmp_path / "drc"
    work.mkdir()
    good = next(p for p in klayout_dir.rglob("*latchup.lyrdb"))
    (work / good.name).write_bytes(good.read_bytes())
    (work / "AION_broken.lyrdb").write_text("<report><this is not xml")

    report = parse_klayout_reports(work)
    assert report.unparsed_files == 1, (
        f"the corrupt database must be counted, got {report.unparsed_files}; "
        "silently skipping it hides that a rule table was never checked"
    )
    assert report.error_count == 1, (
        "the readable database's item must survive its neighbour being corrupt"
    )
    assert report.clean is False, (
        "a partially read DRC result can never be clean: the unread table might "
        "have held the violation that matters"
    )


def test_missing_single_database_raises(tmp_path):
    with pytest.raises(VerificationError):
        parse_klayout_lyrdb(tmp_path / "nope.lyrdb")
