# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Liberty is read, including its units
# ================================================================

"""The Liberty parser, graded against a fixture whose numbers check by hand.

A characterisation result is only a claim about speed if its **units** are read.
A library that states ``time_unit : "1ps"`` and is parsed as nanoseconds makes
the cell look a thousand times faster than it is, and the comparison report
built on it is confident and wrong.  So units are asserted first, and asserted
against two libraries that differ only in their unit headers.

The tables in ``tests/fixtures/liberty/`` are 2x2 arithmetic squares on a known
index grid, so every lookup below has an answer a reader can compute: a corner
returns a value printed in the file, and the centre returns the mean of the four
corners.  A parser that transposes the axes, drops a row, or interpolates on the
wrong index fails at least one of them.
"""

from __future__ import annotations

import pytest

from conftest import CELL, GATE_CELL, optional_module

liberty = optional_module("aion_layout.liberty")

CANDIDATE = "candidate.lib"
BASELINE = "baseline.lib"

#: The index grid both fixtures share: input slew in ns, output load in pF.
SLEW_LO, SLEW_HI = 0.0100, 0.1000
LOAD_LO, LOAD_HI = 0.0010, 0.0100
SLEW_MID = (SLEW_LO + SLEW_HI) / 2
LOAD_MID = (LOAD_LO + LOAD_HI) / 2


def get_cell(library, name):
    """Return one cell, failing with the library's own list if it is absent."""
    found = library.cell(name)
    assert found is not None, (
        f"the library does not contain the cell {name!r}; a comparison report "
        "built on it would have nothing to grade"
    )
    return found


def arc_for(cell, related_pin):
    matches = [a for a in cell.arcs if a.related_pin == related_pin]
    assert len(matches) == 1, (
        f"{cell.name} must have exactly one arc from {related_pin!r}; got "
        f"{len(matches)}, which means arcs were merged or duplicated"
    )
    return matches[0]


@pytest.fixture(scope="module")
def candidate(fixtures_dir):
    return liberty.read_liberty(fixtures_dir / "liberty" / CANDIDATE)


@pytest.fixture(scope="module")
def baseline(fixtures_dir):
    return liberty.read_liberty(fixtures_dir / "liberty" / BASELINE)


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


def test_units_are_read_from_the_header(candidate, fixtures_dir):
    """A delay is only a number until the header says what it counts in."""
    assert candidate.time_unit_ns == pytest.approx(1.0), (
        'the fixture states time_unit : "1ns", so one table unit is one '
        f"nanosecond; got {candidate.time_unit_ns}"
    )
    assert candidate.cap_unit_pf == pytest.approx(1.0), (
        "the fixture states capacitive_load_unit (1, pf); got "
        f"{candidate.cap_unit_pf}"
    )
    assert candidate.name == "aion_candidate_typ", (
        f"the library name identifies the corner it was run at: {candidate.name}"
    )
    assert candidate.path == fixtures_dir / "liberty" / CANDIDATE, (
        "a Library must remember the file it came from, or a report cannot say "
        "which corner it quoted"
    )


def test_other_units_are_not_silently_treated_as_nanoseconds(tmp_path, fixtures_dir):
    """The unit is parsed, not assumed: ps and fF must convert, not pass through."""
    text = (fixtures_dir / "liberty" / CANDIDATE).read_text()
    text = text.replace('time_unit : "1ns"', 'time_unit : "1ps"')
    text = text.replace("capacitive_load_unit (1, pf)", "capacitive_load_unit (1, ff)")
    path = tmp_path / "picoseconds.lib"
    path.write_text(text)

    library = liberty.read_liberty(path)

    assert library.time_unit_ns == pytest.approx(1e-3), (
        "one picosecond is 0.001 ns; a library read as nanoseconds regardless "
        f"of its header reports a cell 1000x faster than it is: "
        f"{library.time_unit_ns}"
    )
    assert library.cap_unit_pf == pytest.approx(1e-3), (
        f"one femtofarad is 0.001 pF: {library.cap_unit_pf}"
    )


# ---------------------------------------------------------------------------
# The cell
# ---------------------------------------------------------------------------


def test_the_cell_carries_its_area_and_leakage(candidate):
    """Liberty `area` is the placement footprint the comparison report grades."""
    cell = get_cell(candidate, CELL)

    assert cell.area == pytest.approx(10.8864), (
        "the fixture states area : 10.8864, which is the 2.88 x 3.78 um "
        f"placement footprint of the verified cell: {cell.area}"
    )
    assert cell.leakage == pytest.approx(1500.0), (
        "cell_leakage_power is 1.5 under leakage_power_unit \"1nW\", and this "
        "reader canonicalises power to pW, so the number handed out is 1500; "
        f"anything else means the unit was ignored: {cell.leakage}"
    )


def test_pin_directions_split_inputs_from_outputs(candidate):
    """A pin on the wrong side of the interface makes every arc meaningless."""
    cell = get_cell(candidate, CELL)

    assert sorted(cell.inputs) == ["I0", "I1", "I2"], (
        f"the fixture declares three input pins: {cell.inputs}"
    )
    assert list(cell.outputs) == ["O0"], (
        f"the fixture declares one output pin: {cell.outputs}"
    )
    assert cell.input_caps["I1"] == pytest.approx(0.0015), (
        "input capacitance is what the driving cell pays for; it must be read "
        f"per pin: {cell.input_caps}"
    )


def test_every_arc_is_found(candidate, baseline):
    """A dropped arc is a path the timing report never looks at."""
    assert len(get_cell(candidate, CELL).arcs) == 3, (
        "the candidate fixture declares three timing() groups on O0"
    )
    assert len(get_cell(baseline, GATE_CELL).arcs) == 2, (
        "the baseline fixture deliberately declares only two, so the "
        "comparison has an asymmetry to report"
    )


def test_an_arc_states_its_pins_and_sense(candidate):
    """Which pin, to which pin, in which direction: all three or none."""
    arc = arc_for(get_cell(candidate, CELL), "I0")

    assert arc.output_pin == "O0", (
        f"the arc must name the pin it drives: {arc.output_pin}"
    )
    assert "negative" in str(arc.sense), (
        f"the fixture states timing_sense : negative_unate for I0: {arc.sense}"
    )
    assert arc.when in (None, ""), (
        f"this arc is unconditional, so `when` must be empty rather than a "
        f"string a report would print as a condition: {arc.when!r}"
    )


# ---------------------------------------------------------------------------
# The tables
# ---------------------------------------------------------------------------


def test_a_table_keeps_its_index_grid(candidate):
    """Interpolating on the wrong axis is silent; the axes are asserted first."""
    table = arc_for(get_cell(candidate, CELL), "I0").cell_rise

    assert [pytest.approx(v) for v in table.index_1] == [SLEW_LO, SLEW_HI], (
        f"index_1 is the input slew axis: {table.index_1}"
    )
    assert [pytest.approx(v) for v in table.index_2] == [LOAD_LO, LOAD_HI], (
        f"index_2 is the output load axis: {table.index_2}"
    )
    assert len(table.values) == 2 and all(len(row) == 2 for row in table.values), (
        "the fixture's tables are 2x2, one row per index_1 value; any other "
        f"shape means the values string was split wrong: {table.values}"
    )
    assert table.values[0][0] == pytest.approx(0.0200), (
        "values are laid out row-major over index_1; a transposed table puts "
        f"0.0600 here instead: {table.values}"
    )


def test_lookup_at_a_grid_point_returns_the_printed_value(candidate):
    """At a corner the answer is in the file; anything else is interpolation error."""
    table = arc_for(get_cell(candidate, CELL), "I0").cell_rise

    assert table.at(SLEW_LO, LOAD_LO) == pytest.approx(0.0200), (
        "the low-slew, low-load corner is printed as 0.0200 and must come back "
        f"exactly: {table.at(SLEW_LO, LOAD_LO)}"
    )
    assert table.at(SLEW_HI, LOAD_HI) == pytest.approx(0.0800), (
        f"the high corner is printed as 0.0800: {table.at(SLEW_HI, LOAD_HI)}"
    )
    assert table.at(SLEW_LO, LOAD_HI) == pytest.approx(0.0400), (
        "slow-load-only corner is 0.0400; getting 0.0600 here means the two "
        f"axes are swapped: {table.at(SLEW_LO, LOAD_HI)}"
    )
    assert table.at(SLEW_HI, LOAD_LO) == pytest.approx(0.0600)


def test_lookup_between_two_points_interpolates(candidate):
    """Real loads land between the characterised ones; the table must span them."""
    table = arc_for(get_cell(candidate, CELL), "I0").cell_rise

    centre = table.at(SLEW_MID, LOAD_MID)
    assert centre == pytest.approx((0.0200 + 0.0400 + 0.0600 + 0.0800) / 4), (
        "the fixture's corners are an arithmetic square, so the centre of a "
        f"bilinear interpolation is their mean, 0.05: {centre}"
    )

    edge = table.at(SLEW_MID, LOAD_LO)
    assert edge == pytest.approx((0.0200 + 0.0600) / 2), (
        "halfway along index_1 at a fixed index_2 is the mean of that column: "
        f"{edge}"
    )
    assert min(0.0200, 0.0800) <= centre <= max(0.0200, 0.0800), (
        "an interpolated value can never leave the range of the table it came "
        "from; one that does is an extrapolation bug"
    )


def test_mid_is_a_value_the_table_could_produce(candidate):
    """`mid` is the representative operating point a summary quotes."""
    table = arc_for(get_cell(candidate, CELL), "I0").cell_rise
    flat = [v for row in table.values for v in row]

    assert min(flat) <= table.mid <= max(flat), (
        f"mid must lie inside the characterised range {min(flat)}..{max(flat)}, "
        f"got {table.mid}"
    )


def test_all_four_tables_of_an_arc_are_read(candidate):
    """Transitions drive the next stage's slew; dropping them breaks the chain."""
    arc = arc_for(get_cell(candidate, CELL), "I0")

    for name, corner in (
        ("cell_rise", 0.0200),
        ("cell_fall", 0.0100),
        ("rise_transition", 0.0150),
        ("fall_transition", 0.0120),
    ):
        table = getattr(arc, name)
        assert table is not None, (
            f"the fixture declares {name} for this arc; a None here means a "
            "whole table was skipped"
        )
        assert table.at(SLEW_LO, LOAD_LO) == pytest.approx(corner), (
            f"{name} low corner is {corner} in the fixture: "
            f"{table.at(SLEW_LO, LOAD_LO)}"
        )


# ---------------------------------------------------------------------------
# Delays over a whole cell
# ---------------------------------------------------------------------------


def test_arc_delays_cover_every_arc(candidate):
    """A per-arc table with a missing key hides the path that was slowest."""
    cell = get_cell(candidate, CELL)

    delays = liberty.arc_delays(cell, slew=SLEW_HI, load=LOAD_HI)

    assert len(delays) == 2 * len(cell.arcs), (
        "both edges of every arc are a path the timing report has to look at, "
        f"so a cell with {len(cell.arcs)} arcs publishes "
        f"{2 * len(cell.arcs)} delays; got {len(delays)}: {sorted(delays)}"
    )
    assert set(delays) == {
        f"{pin}->O0 {edge}" for pin in cell.inputs for edge in ("rise", "fall")
    }, (
        "each delay is labelled by the pins and the edge it belongs to, or a "
        f"report cannot say which path was slowest: {sorted(delays)}"
    )
    assert all(isinstance(v, float) for v in delays.values()), (
        f"a delay is a number, not a table or a string: {delays}"
    )


def test_worst_is_the_maximum_and_names_its_arc(candidate):
    """"Worst" has to be the slowest arc and say which one, or it cannot be fixed."""
    cell = get_cell(candidate, CELL)

    delays = liberty.arc_delays(cell, slew=SLEW_HI, load=LOAD_HI)
    worst, arc_name = liberty.worst_arc_delay(cell, slew=SLEW_HI, load=LOAD_HI)

    assert worst == pytest.approx(max(delays.values())), (
        f"the worst-case delay is the maximum over the arcs: {worst} vs "
        f"{max(delays.values())} in {delays}"
    )
    assert "I1" in arc_name, (
        "I1 carries the slowest tables in the fixture, so it is the arc that "
        f"has to be named: {arc_name!r}"
    )


def test_mean_is_the_mean_of_the_arcs(candidate):
    """A mean over a subset of arcs flatters whichever arcs were dropped."""
    cell = get_cell(candidate, CELL)

    delays = liberty.arc_delays(cell, slew=SLEW_HI, load=LOAD_HI)
    mean = liberty.mean_arc_delay(cell, slew=SLEW_HI, load=LOAD_HI)

    assert mean == pytest.approx(sum(delays.values()) / len(delays)), (
        f"the mean must be taken over all {len(delays)} arcs: {mean} vs "
        f"{sum(delays.values()) / len(delays)}"
    )
    worst, _ = liberty.worst_arc_delay(cell, slew=SLEW_HI, load=LOAD_HI)
    assert mean <= worst + 1e-12, "the mean can never exceed the worst case"


def test_the_baseline_is_slower_than_the_candidate(candidate, baseline):
    """The fixtures encode the outcome the flow exists to demonstrate."""
    fast, _ = liberty.worst_arc_delay(
        get_cell(candidate, CELL), slew=SLEW_HI, load=LOAD_HI
    )
    slow, _ = liberty.worst_arc_delay(
        get_cell(baseline, GATE_CELL), slew=SLEW_HI, load=LOAD_HI
    )

    assert slow > fast, (
        "every baseline table in the fixture is 0.02 slower than the "
        f"candidate's; a parser that reports otherwise has crossed the two "
        f"files: candidate {fast}, baseline {slow}"
    )


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


def test_a_truncated_library_raises(fixtures_dir):
    """A file that stops mid-table is a killed run, not a library of one arc."""
    with pytest.raises(liberty.LibertyError):
        liberty.read_liberty(fixtures_dir / "liberty" / "truncated.lib")


def test_a_missing_library_raises(tmp_path):
    """An absent .lib is an error; there is no timing to report."""
    with pytest.raises((liberty.LibertyError, OSError)):
        liberty.read_liberty(tmp_path / "never-written.lib")


def test_an_empty_library_raises(tmp_path):
    """Zero bytes is what an OOM-killed characterisation leaves behind."""
    path = tmp_path / "empty.lib"
    path.write_text("")
    with pytest.raises(liberty.LibertyError):
        liberty.read_liberty(path)
