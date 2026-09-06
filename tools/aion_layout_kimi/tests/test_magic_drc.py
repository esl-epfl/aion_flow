# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Golden tests for Magic DRC report parsing
# ================================================================

"""Magic ``*.magic.drc.rpt`` parsing must never report a dirty layout as clean.

The historical defect: ``parse_magic_drc_report`` did ``float(p)`` over the four
whitespace-separated tokens of a coordinate row, while Magic writes them with a
unit suffix (``0.240um``).  Every row raised ``ValueError`` and was skipped, so
the parser returned ``clean=True`` with zero violations for a report that lists
eight and ends with ``[INFO] COUNT: 8``.  DRC could not fail the gate.
"""

from __future__ import annotations

from collections import Counter

import pytest

from aion_layout.verification import VerificationError, parse_magic_drc_report


def test_fixture_report_is_not_clean(magic_rpt):
    report = parse_magic_drc_report(magic_rpt)
    assert report.clean is False, (
        "the captured Magic report lists 8 latch-up violations; reporting it "
        "clean is the float('0.240um') ValueError bug that let DRC never fail "
        "the acceptance gate"
    )
    assert report.tool == "magic", "the report must identify the tool that produced it"


def test_fixture_report_has_eight_violations(magic_rpt):
    report = parse_magic_drc_report(magic_rpt)
    assert report.error_count == 8, (
        f"expected the 8 violations the fixture lists, parsed {report.error_count}; "
        "a short count means coordinate rows are being silently dropped again"
    )


def test_fixture_report_category_histogram(magic_rpt):
    report = parse_magic_drc_report(magic_rpt)
    # ``category`` is the whole section title; the rule code lives in the
    # parenthesised tail, which is what ``description`` carries.
    by_code = Counter(v.description for v in report.violations)
    assert dict(by_code) == {"LU.a": 4, "LU.b": 4}, (
        f"expected the measured {{LU.a: 4, LU.b: 4}} latch-up histogram, got "
        f"{dict(by_code)}; losing the rule code hides the fact that every "
        "violation is a missing well/substrate tap"
    )
    titles = sorted(report.categories)
    assert titles == [
        "N-diff distance to P-tap must be < 20.0um (LU.b)",
        "P-diff distance to N-tap must be < 20.0um (LU.a)",
    ], (
        f"section titles must survive parsing verbatim, got {titles}; the title "
        "is the only place the report says what the rule actually requires"
    )


def test_fixture_report_reported_count_matches_trailer(magic_rpt):
    report = parse_magic_drc_report(magic_rpt)
    assert report.reported_count == 8, (
        f"Magic's own '[INFO] COUNT: 8' trailer must be captured, got "
        f"{report.reported_count}; without it a caller cannot tell a parser that "
        "went blind from a genuinely clean layout"
    )
    assert report.reported_count == report.error_count, (
        "the tool's count and the parsed count agree on this fixture; a "
        "divergence means the parser is dropping rows"
    )


def test_fixture_first_bbox_is_in_microns(magic_rpt):
    report = parse_magic_drc_report(magic_rpt)
    x1, y1, x2, y2 = report.violations[0].bbox_um
    assert (x1, y1, x2, y2) == pytest.approx((0.240, 2.060, 0.775, 3.180)), (
        f"first violation bbox must be the fixture's ' 0.240um 2.060um 0.775um "
        f"3.180um' in microns, got {(x1, y1, x2, y2)}; a wrong scale (nm read as "
        "um) would send the model looking at the wrong part of the cell"
    )


def test_nanometre_suffix_is_scaled_to_microns(tmp_path):
    report_path = tmp_path / "nm.magic.drc.rpt"
    report_path.write_text(
        "CELL\n"
        "----------------------------------------\n"
        "Some rule (XX.a)\n"
        "----------------------------------------\n"
        " 240nm 2060nm 775nm 3180nm\n"
        "----------------------------------------\n"
        "[INFO] COUNT: 1\n"
    )
    report = parse_magic_drc_report(report_path)
    assert report.violations[0].bbox_um == pytest.approx((0.240, 2.060, 0.775, 3.180)), (
        "a 'nm' suffix must be converted to microns, not truncated to a bare "
        "float; mixing units in one bbox field makes every coordinate the model "
        "is shown untrustworthy"
    )


def test_count_trailer_without_parsable_rows_raises(tmp_path):
    """A report claiming violations from which none parse must refuse to pass."""
    report_path = tmp_path / "blind.magic.drc.rpt"
    report_path.write_text(
        "CELL\n"
        "----------------------------------------\n"
        "P-diff distance to N-tap must be < 20.0um (LU.a)\n"
        "----------------------------------------\n"
        " left bottom right top\n"
        " x1 y1 x2 y2\n"
        "----------------------------------------\n"
        "[INFO] COUNT: 8\n"
    )
    with pytest.raises(VerificationError) as excinfo:
        parse_magic_drc_report(report_path)
    message = str(excinfo.value)
    assert "8" in message and "clean" in message.lower(), (
        f"the error must name the count it could not account for, got {message!r}; "
        "this is the exact shape of the original bug -- COUNT: 8 with zero rows "
        "parsed -- and it must be a hard error, never a clean report"
    )


def test_clean_report_with_zero_count_is_clean(tmp_path):
    """The guard above must not turn a genuinely clean run into an error."""
    report_path = tmp_path / "clean.magic.drc.rpt"
    report_path.write_text("CELL\n[INFO] COUNT: 0\n")
    report = parse_magic_drc_report(report_path)
    assert report.clean is True and report.error_count == 0, (
        "'COUNT: 0' with no violation rows is the only legitimate clean Magic "
        "report; rejecting it would make a passing layout unreportable"
    )


def test_missing_report_raises_rather_than_passing(tmp_path):
    with pytest.raises(VerificationError):
        parse_magic_drc_report(tmp_path / "does-not-exist.rpt")
    # Absence must never be a pass: a missing Magic report is how a run with no
    # DRC at all could otherwise be graded clean.
