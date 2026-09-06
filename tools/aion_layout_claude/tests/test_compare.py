# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The winning claim has to survive arithmetic
# ================================================================

"""The comparison is the tool's whole claim, so it is the easiest thing to fake.

Three ways a comparison lies without anyone editing a number.  It can compare
the two sides at **different operating points**, which turns an error into a
percentage.  It can **drop an arc** one library publishes and the other does
not, which flatters whichever side had the extra slow path.  And it can call a
**tie** a win.  Each is pinned below, together with the sign convention -- a
smaller candidate is a NEGATIVE percentage -- because a sign flip in a summary
line is a result read backwards by everyone downstream.

The fixtures are built so the answer is known in advance: the candidate is
10.8864 um2 against an abutted row of 19.9584, and every baseline delay table
is 0.02 ns slower than its candidate counterpart.  The candidate wins on both,
and the file asserts that it is *reported* as winning on both.
"""

from __future__ import annotations

import dataclasses as dc
import json

import pytest

from aion_layout.metrics import CellGeometry
from conftest import CELL, GATE_CELL, optional_module

compare_mod = optional_module("aion_layout.compare")
liberty = optional_module("aion_layout.liberty")

CompareError = compare_mod.CompareError
Comparison = compare_mod.Comparison
Metric = compare_mod.Metric

#: The verified AION cell: 6 sites of one row.
CANDIDATE_GEOMETRY = CellGeometry(
    cell=CELL, width_um=2.88, height_um=3.78, source="prBoundary"
)
#: Three abutted PDK cells: 11 sites of the same row.
BASELINE_GEOMETRY = CellGeometry(
    cell=GATE_CELL, width_um=5.28, height_um=3.78, source="lef"
)


@pytest.fixture(scope="module")
def comparison(fixtures_dir):
    return compare_mod.compare(
        cell=CELL,
        baseline_cell=GATE_CELL,
        candidate_lib=fixtures_dir / "liberty" / "candidate.lib",
        baseline_lib=fixtures_dir / "liberty" / "baseline.lib",
        candidate_geometry=CANDIDATE_GEOMETRY,
        baseline_geometry=BASELINE_GEOMETRY,
    )


def metric(candidate, baseline, *, lower_is_better=True):
    return Metric(
        name="test metric",
        unit="um2",
        candidate=candidate,
        baseline=baseline,
        lower_is_better=lower_is_better,
    )


# ---------------------------------------------------------------------------
# Metric: sign convention and strictness
# ---------------------------------------------------------------------------


def test_a_smaller_candidate_is_a_negative_percentage():
    """The sign says the direction; getting it backwards inverts every report."""
    m = metric(10.8864, 19.9584)

    assert m.delta < 0, f"a smaller candidate has a negative delta: {m.delta}"
    assert m.pct == pytest.approx((10.8864 - 19.9584) / 19.9584 * 100.0), (
        "pct is the change FROM the baseline TO the candidate, as a percentage "
        f"of the baseline: {m.pct}"
    )
    assert m.pct == pytest.approx(-45.45, abs=0.01), (
        f"10.8864 um2 against 19.9584 is 45.45% smaller: {m.pct}"
    )
    assert m.improved, "smaller is better for an area metric"


def test_a_larger_candidate_is_a_positive_percentage():
    m = metric(19.9584, 10.8864)

    assert m.pct > 0, (
        f"a candidate larger than the baseline reports a positive change: {m.pct}"
    )
    assert not m.improved, "a bigger cell has not improved on area"


def test_a_tie_is_not_an_improvement():
    """The tool argues a hand-drawn cell earns its place; a tie does not."""
    m = metric(10.0, 10.0)

    assert m.pct == pytest.approx(0.0)
    assert not m.improved, (
        "improvement is strict: an equal candidate has bought nothing for the "
        "effort of drawing it, and reporting it as a win makes the whole "
        "comparison meaningless"
    )


def test_higher_is_better_metrics_invert_only_improved():
    """Some metrics (drive, margin) are better larger; the sign stays absolute."""
    m = metric(12.0, 10.0, lower_is_better=False)

    assert m.improved, "for a higher-is-better metric, larger is an improvement"
    assert m.pct > 0, (
        "pct always describes the change, not the goodness; folding the "
        "direction into the sign makes two metrics uncomparable"
    )


def test_a_zero_baseline_has_no_percentage():
    """Dividing by a baseline of zero must refuse, not produce inf or 0."""
    with pytest.raises(CompareError) as excinfo:
        metric(10.0, 0.0).pct

    assert "zero" in str(excinfo.value), (
        f"the refusal must name the zero baseline as the cause: {excinfo.value}"
    )


# ---------------------------------------------------------------------------
# Comparison.wins: both, or it is not a win
# ---------------------------------------------------------------------------


def build_comparison(*, area, worst, mean=None, notes=()):
    """A Comparison assembled by hand, to test the verdict logic alone."""
    return Comparison(
        cell=CELL,
        baseline_cell=GATE_CELL,
        area=Metric("placement area", "um2", *area),
        worst_delay=Metric("worst arc delay", "ps", *worst),
        mean_delay=Metric("mean arc delay", "ps", *(mean or worst)),
        extra=(),
        per_arc=(),
        notes=tuple(notes),
    )


@pytest.mark.parametrize(
    "area, worst, expect_win, why",
    [
        ((10.0, 20.0), (90.0, 110.0), True, "smaller and faster is the only win"),
        ((10.0, 20.0), (110.0, 90.0), False, "smaller but slower is not a win"),
        ((20.0, 10.0), (90.0, 110.0), False, "faster but larger is not a win"),
        ((20.0, 10.0), (110.0, 90.0), False, "larger and slower is a loss"),
        ((10.0, 10.0), (90.0, 110.0), False, "an area tie is not smaller"),
        ((10.0, 20.0), (90.0, 90.0), False, "a delay tie is not faster"),
    ],
)
def test_wins_requires_both(area, worst, expect_win, why):
    """A cell that trades area for delay has not replaced anything."""
    cmp = build_comparison(area=area, worst=worst)

    assert cmp.wins is expect_win, why
    assert cmp.smaller == (area[0] < area[1]), "smaller follows the area metric"
    assert cmp.faster == (worst[0] < worst[1]), (
        "faster follows the WORST arc, which is what static timing analysis "
        "will pick up"
    )


def test_the_verdict_follows_the_worst_arc_not_the_mean():
    """A mean improvement over a worse critical path is not a faster cell."""
    cmp = build_comparison(area=(10.0, 20.0), worst=(110.0, 90.0), mean=(80.0, 100.0))

    assert not cmp.faster, (
        "the mean got better while the critical path got worse; timing "
        "closure follows the critical path, so this is not faster"
    )
    assert not cmp.wins


# ---------------------------------------------------------------------------
# verdict_line: one line, column 0
# ---------------------------------------------------------------------------


def test_verdict_line_is_exactly_one_line_at_column_zero(comparison):
    """A harness greps for this line; a second one makes the result ambiguous."""
    line = compare_mod.verdict_line(comparison)

    assert "\n" not in line.strip("\n"), (
        f"the verdict is one line and must contain no newline: {line!r}"
    )
    assert line.startswith("COMPARE: "), (
        f"the line has to start at column 0 with its marker: {line!r}"
    )
    assert line.split()[1] in ("WIN", "LOSS"), (
        f"the second field is the verdict itself: {line!r}"
    )


@pytest.mark.parametrize(
    "area, worst, expected",
    [((10.0, 20.0), (90.0, 110.0), "WIN"), ((20.0, 10.0), (110.0, 90.0), "LOSS")],
)
def test_verdict_line_states_the_verdict_it_computed(area, worst, expected):
    line = compare_mod.verdict_line(build_comparison(area=area, worst=worst))

    assert line.split()[1] == expected, (
        f"the printed verdict must match Comparison.wins: {line!r}"
    )


def test_verdict_line_appears_once_in_the_rendered_report(comparison):
    """The report embeds the line; two of them and a grep picks the wrong one."""
    markdown = compare_mod.render_markdown(comparison)

    hits = [ln for ln in markdown.splitlines() if ln.startswith("COMPARE: ")]

    assert len(hits) == 1, (
        f"exactly one column-0 COMPARE: line may appear in the report, found "
        f"{len(hits)}: {hits}"
    )


# ---------------------------------------------------------------------------
# The real comparison over the fixture pair
# ---------------------------------------------------------------------------


def test_the_candidate_is_reported_smaller_and_faster(comparison):
    """The fixtures encode a win; a comparison that cannot see it is broken."""
    assert comparison.area.candidate == pytest.approx(10.8864), (
        "area comes from the measured geometry, never from the Liberty "
        f"attribute the characterizer wrote from it: {comparison.area.candidate}"
    )
    assert comparison.area.baseline == pytest.approx(19.9584)
    assert comparison.smaller, "10.8864 um2 is smaller than 19.9584"
    assert comparison.faster, (
        "every baseline table is 0.02 ns slower than the candidate's, so the "
        f"worst arc must improve: {comparison.worst_delay}"
    )
    assert comparison.wins


def test_both_sides_are_read_at_the_same_operating_point(comparison):
    """"18% faster" from two different grid points is an error with a % sign."""
    assert comparison.slew_ns > 0 and comparison.load_pf > 0, (
        "the comparison must record the slew and load it read both libraries "
        f"at: {comparison.slew_ns} ns, {comparison.load_pf} pF"
    )
    assert comparison.worst_delay.candidate == pytest.approx(90.0), (
        "at the shared mid grid point (0.1 ns, 0.01 pF) the candidate's "
        f"slowest arc is I1->O0 rise at 0.09 ns = 90 ps: "
        f"{comparison.worst_delay.candidate}"
    )
    assert comparison.worst_delay.baseline == pytest.approx(110.0), (
        f"the baseline's slowest arc is 0.11 ns = 110 ps: "
        f"{comparison.worst_delay.baseline}"
    )
    assert "I1" in comparison.candidate_worst_arc, (
        "the report has to name the arc that decided the verdict: "
        f"{comparison.candidate_worst_arc!r}"
    )


def test_an_arc_only_one_library_has_lands_in_notes(comparison):
    """Silently dropping it flatters whichever side published the extra path."""
    labels = [label for label, _, _ in comparison.per_arc]

    assert all("I2" not in label for label in labels), (
        "the baseline publishes no I2 arc, so there is no per-arc row to show "
        f"for it: {labels}"
    )
    joined = "\n".join(comparison.notes)
    assert "I2->O0" in joined, (
        "the arc the two libraries do not share must be named in the notes; "
        f"an unreported asymmetry is a comparison over different cells: {joined}"
    )
    assert "only in the candidate" in joined, (
        f"the note must say which side has it: {joined}"
    )


def test_the_unmatched_arc_still_counts_against_its_own_cell(comparison, fixtures_dir):
    """The candidate's extra arcs are in the candidate's own mean, not excluded."""
    candidate = liberty.read_liberty(fixtures_dir / "liberty" / "candidate.lib")
    cell = candidate.cell(CELL)
    own_mean = liberty.mean_arc_delay(
        cell, slew=comparison.slew_ns, load=comparison.load_pf
    )

    assert comparison.mean_delay.candidate == pytest.approx(own_mean * 1000.0), (
        "the candidate's mean is taken over ALL six of its delays including "
        "the I2 arc the baseline lacks; restricting it to the shared arcs "
        f"would hide a slow path: {comparison.mean_delay.candidate} ps vs "
        f"{own_mean * 1000.0} ps"
    )
    shared_only = [
        d for label, d in
        liberty.arc_delays(
            cell, slew=comparison.slew_ns, load=comparison.load_pf
        ).items()
        if "I2" not in label
    ]
    assert comparison.mean_delay.candidate != pytest.approx(
        sum(shared_only) / len(shared_only) * 1000.0
    ), "the mean must NOT be the mean over the shared arcs alone"


def test_per_arc_shows_only_the_arcs_that_correspond(comparison):
    """A row pairing two arcs that are not the same path is worse than no row."""
    labels = {label for label, _, _ in comparison.per_arc}

    assert labels == {
        "I0->O0 rise", "I0->O0 fall", "I1->O0 rise", "I1->O0 fall",
    }, f"the two libraries share exactly these four arcs: {sorted(labels)}"
    for label, candidate_ns, baseline_ns in comparison.per_arc:
        assert baseline_ns == pytest.approx(candidate_ns + 0.02), (
            f"every baseline table in the fixture is 0.02 ns slower than its "
            f"candidate counterpart; {label} is "
            f"{baseline_ns - candidate_ns:+.4f}"
        )


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


def test_a_zero_baseline_area_is_refused(fixtures_dir):
    """There is nothing to compare against; a percentage would be infinite."""
    with pytest.raises(CompareError) as excinfo:
        compare_mod.compare(
            cell=CELL,
            baseline_cell=GATE_CELL,
            candidate_lib=fixtures_dir / "liberty" / "candidate.lib",
            baseline_lib=fixtures_dir / "liberty" / "baseline.lib",
            candidate_geometry=CANDIDATE_GEOMETRY,
            baseline_geometry=dc.replace(BASELINE_GEOMETRY, width_um=0.0),
        )

    assert "baseline" in str(excinfo.value).lower(), (
        f"the refusal must say which side measured zero: {excinfo.value}"
    )


def test_a_missing_cell_is_refused(fixtures_dir):
    """Comparing against a cell the library does not define compares nothing."""
    with pytest.raises(CompareError) as excinfo:
        compare_mod.compare(
            cell="not_a_cell",
            baseline_cell=GATE_CELL,
            candidate_lib=fixtures_dir / "liberty" / "candidate.lib",
            baseline_lib=fixtures_dir / "liberty" / "baseline.lib",
            candidate_geometry=CANDIDATE_GEOMETRY,
            baseline_geometry=BASELINE_GEOMETRY,
        )

    assert "not_a_cell" in str(excinfo.value), (
        f"the refusal must name the cell it could not find: {excinfo.value}"
    )


def test_a_missing_library_is_refused(tmp_path, fixtures_dir):
    """An absent .lib is an error, never a comparison against nothing."""
    with pytest.raises((CompareError, OSError)):
        compare_mod.compare(
            cell=CELL,
            baseline_cell=GATE_CELL,
            candidate_lib=fixtures_dir / "liberty" / "candidate.lib",
            baseline_lib=tmp_path / "never-characterized.lib",
            candidate_geometry=CANDIDATE_GEOMETRY,
            baseline_geometry=BASELINE_GEOMETRY,
        )


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def test_the_json_report_carries_the_numbers_and_the_notes(comparison):
    """A machine-readable report that drops the caveats is a prettier lie."""
    payload = json.loads(compare_mod.render_json(comparison))

    assert payload["cell"] == CELL and payload["baseline_cell"] == GATE_CELL
    assert payload["verdict"] == "WIN", (
        "the JSON verdict must agree with Comparison.wins: "
        f"{payload.get('verdict')!r}"
    )
    assert payload["smaller"] is True and payload["faster"] is True, (
        "the two halves of the verdict are reported separately so a reader can "
        f"see which one carried it: {payload.get('smaller')}, {payload.get('faster')}"
    )
    assert payload["notes"], (
        "the notes are where every asymmetry and caveat lives; a report "
        "without them cannot be audited"
    )


def test_the_markdown_report_names_both_cells_and_every_note(comparison):
    """A human has to be able to check the claim without rerunning the flow."""
    markdown = compare_mod.render_markdown(comparison)

    assert CELL in markdown and GATE_CELL in markdown
    for note in comparison.notes:
        assert note.splitlines()[0] in markdown, (
            f"every note must reach the rendered report; this one did not: {note!r}"
        )
