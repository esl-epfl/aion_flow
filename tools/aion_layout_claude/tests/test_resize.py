# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Resizing is explicit, capped, and never in place
# ================================================================

"""Widening a series stack is a design change, so it must behave like one.

Three things make this step safe, and each is pinned below.

**It never edits its input.**  The netlist is what LVS grades the layout
against.  A resize that rewrote it in place would leave every earlier
verification claiming to have checked a circuit that no longer exists, and
nothing would say so.

**It is capped by area.**  The reason an AION cell exists is that it is smaller
than the PDK cells it replaces, so a multiplier that spends the area win is not
an improvement -- it is a different, worse cell.  The planner takes the largest
multiplier that still fits the budget, and when none fits it says so instead of
quietly resizing by 1.0 and reporting success.

**It only touches deep stacks.**  The PDK does not widen 2-high stacks either
(``nand2_1``, ``nor2_1``, ``nor3_1``, ``nor4_1`` all use w=1.12u pmos), so a
cell that did would be the odd one out in the library it has to live beside.

Ground truth for the whole file is the worked example.  Its pull-up is three
devices deep and its pull-down is flat, so ``stack_depths`` must read
``{XP1, XP2, XP3} = 3`` and everything else 1; and against the real abutted row
(19.9584 um^2) the planner must choose x2 -- 7 poly columns, 9 sites,
16.3296 um^2 -- rejecting x3 and x2.5 for area.  Those numbers are the ones the
whole resize step turns on, and a change to any of them is a change of design.
"""

from __future__ import annotations

import pytest

from aion_layout.resize import (
    ResizeError,
    estimate_area_um2,
    estimate_sites,
    plan_resize,
    render_report,
    resize,
    stack_depths,
    summary_line,
    write_resized_netlist,
)
from aion_layout.spice_parser import parse_first_subckt

from conftest import CELL

#: The example's pull-up is a 3-high series stack; its pull-down is flat.
EXPECTED_DEPTHS = {
    "XP0": 1, "XN0": 1,
    "XP1": 3, "XP2": 3, "XP3": 3,
    "XN1": 1, "XN2": 1, "XN3": 1,
}

#: What the planner must choose against the real abutted row.
EXPECTED_MULTIPLIER = 2.0
EXPECTED_COLUMNS = 7
EXPECTED_SITES = 9
EXPECTED_AREA_UM2 = 16.3296
BASELINE_AREA_UM2 = 19.9584

#: A flat cell: two parallel pull-downs, two parallel pull-ups. Nothing to widen.
FLAT_NETLIST = """\
.subckt flat_cell A B Y VDD VSS
XP0 Y A VDD VDD sg13_lv_pmos w=1.12u l=0.13u ng=1 m=1
XP1 Y B VDD VDD sg13_lv_pmos w=1.12u l=0.13u ng=1 m=1
XN0 Y A VSS VSS sg13_lv_nmos w=740n l=0.13u ng=1 m=1
XN1 Y B VSS VSS sg13_lv_nmos w=740n l=0.13u ng=1 m=1
.ends
"""

#: The mirror image of the worked example: the deep stack is on the nmos side.
NAND3_NETLIST = """\
.subckt deep_pulldown A B C Y VDD VSS
XP0 Y A VDD VDD sg13_lv_pmos w=1.12u l=0.13u ng=1 m=1
XP1 Y B VDD VDD sg13_lv_pmos w=1.12u l=0.13u ng=1 m=1
XP2 Y C VDD VDD sg13_lv_pmos w=1.12u l=0.13u ng=1 m=1
XN0 Y A n1 VSS sg13_lv_nmos w=740n l=0.13u ng=1 m=1
XN1 n1 B n2 VSS sg13_lv_nmos w=740n l=0.13u ng=1 m=1
XN2 n2 C VSS VSS sg13_lv_nmos w=740n l=0.13u ng=1 m=1
.ends
"""


@pytest.fixture()
def flat(tmp_path):
    path = tmp_path / "flat_cell.spice"
    path.write_text(FLAT_NETLIST)
    return path


@pytest.fixture()
def deep_pulldown(tmp_path):
    path = tmp_path / "deep_pulldown.spice"
    path.write_text(NAND3_NETLIST)
    return path


# ---------------------------------------------------------------- depths ----


def test_stack_depths_of_the_worked_example(netlist_path):
    """The 3-high pull-up is the whole reason this step exists; pin it."""
    assert stack_depths(parse_first_subckt(netlist_path)) == EXPECTED_DEPTHS, (
        "the pull-up of the worked example is three devices deep and its "
        "pull-down is flat; if this reads differently the planner is widening "
        "the wrong devices"
    )


def test_a_flat_cell_has_no_stack(flat):
    """A parallel network is depth 1 everywhere, whichever rail it hangs off."""
    assert set(stack_depths(parse_first_subckt(flat)).values()) == {1}


def test_depth_is_found_in_the_pull_down_network_too(deep_pulldown):
    """The walk must not be pmos-only: a nand3's nmos stack is the limiter."""
    depths = stack_depths(parse_first_subckt(deep_pulldown))
    assert {depths["XN0"], depths["XN1"], depths["XN2"]} == {3}, depths
    assert {depths["XP0"], depths["XP1"], depths["XP2"]} == {1}, depths


# ------------------------------------------------------------ the choice ----


def test_the_worked_example_chooses_x2_against_the_real_baseline(
    netlist_path, gate_netlist_path
):
    """The one number the whole step turns on, with its arithmetic."""
    plan = plan_resize(netlist_path, baseline=gate_netlist_path)
    assert plan.multiplier == EXPECTED_MULTIPLIER
    assert plan.gate_columns == EXPECTED_COLUMNS
    assert plan.estimated_sites == EXPECTED_SITES
    assert plan.estimated_area_um2 == pytest.approx(EXPECTED_AREA_UM2)
    assert plan.area_budget_um2 == pytest.approx(BASELINE_AREA_UM2)
    assert plan.estimated_area_um2 < plan.area_budget_um2, (
        "a resized cell that is not strictly smaller than the abutted row has "
        "spent the only advantage it had"
    )


def test_only_the_deep_stack_is_widened(netlist_path, gate_netlist_path):
    """Depth 1 devices keep the library width, and say why."""
    plan = plan_resize(netlist_path, baseline=gate_netlist_path)
    changed = {d.name for d in plan.changed_devices}
    assert changed == {"XP1", "XP2", "XP3"}
    for device in plan.devices:
        if device.name in changed:
            assert device.new_w_nm == pytest.approx(2240.0)
            assert device.new_ng == 2
            assert device.finger_w_nm == pytest.approx(1120.0), (
                "fingers must stay at the library's own finger width, or the "
                "cell no longer matches the devices the PDK characterised"
            )
        else:
            assert not device.changed
            assert device.new_w_nm == device.original_w_nm
            assert device.reason, "an untouched device must still say why"


def test_a_two_high_stack_is_left_alone_by_default(deep_pulldown, tmp_path):
    """min_depth=2 means depth 2 is not deep enough -- the PDK agrees."""
    two_high = tmp_path / "two_high.spice"
    two_high.write_text(
        NAND3_NETLIST.replace("XN1 n1 B n2 VSS", "XN1 n1 B VSS VSS").replace(
            "XN2 n2 C VSS VSS sg13_lv_nmos w=740n l=0.13u ng=1 m=1\n", ""
        )
    )
    plan = plan_resize(two_high, area_budget_um2=1000.0)
    assert plan.unchanged, [d.reason for d in plan.devices]


def test_no_multiplier_fitting_the_budget_is_reported_not_hidden(netlist_path):
    """A cap nothing fits must never read as a successful resize."""
    plan = plan_resize(netlist_path, area_budget_um2=1.0)
    assert plan.unchanged
    assert plan.multiplier == 1.0
    assert plan.changed_devices == ()
    assert any("reject" in note.lower() for note in plan.notes), plan.notes
    assert "unchanged" in summary_line(plan)


def test_area_estimate_is_the_documented_arithmetic():
    """7 columns -> 9 sites -> 16.3296 um^2, from the contacted pitch."""
    assert estimate_sites(EXPECTED_COLUMNS) == EXPECTED_SITES
    assert estimate_area_um2(EXPECTED_SITES) == pytest.approx(EXPECTED_AREA_UM2)


# ------------------------------------------------------------- the output ---


def test_the_resized_netlist_reparses_to_the_same_circuit(
    netlist_path, gate_netlist_path, tmp_path
):
    """Same pins, same devices, same connectivity -- only w and ng move."""
    original = parse_first_subckt(netlist_path)
    plan = plan_resize(netlist_path, baseline=gate_netlist_path)
    out = write_resized_netlist(plan, tmp_path / "resized.spice")
    resized = parse_first_subckt(out)

    assert resized.name == plan.new_cell != original.name
    assert resized.pins == original.pins
    assert len(resized.devices) == len(original.devices)
    by_name = {d.name: d for d in resized.devices}
    for device in original.devices:
        new = by_name[device.name]
        assert (new.drain, new.gate, new.source, new.bulk) == (
            device.drain, device.gate, device.source, device.bulk
        ), f"{device.name} changed connectivity, which resizing must never do"
        assert new.length_nm == device.length_nm
    for name in ("XP1", "XP2", "XP3"):
        assert by_name[name].width_nm == pytest.approx(2240.0)
        assert by_name[name].fingers == 2


def test_it_refuses_to_write_over_its_own_input(netlist_path, gate_netlist_path):
    """The input netlist is the flow's source of truth; it is never edited."""
    plan = plan_resize(netlist_path, baseline=gate_netlist_path)
    before = netlist_path.read_bytes()
    with pytest.raises(ResizeError) as excinfo:
        write_resized_netlist(plan, netlist_path)
    assert "input" in str(excinfo.value).lower()
    assert netlist_path.read_bytes() == before, "the input netlist was modified"


def test_the_summary_line_is_exactly_one_line_at_column_zero(
    netlist_path, gate_netlist_path
):
    """One machine-readable line, like every other verdict in the flow."""
    line = summary_line(plan_resize(netlist_path, baseline=gate_netlist_path))
    assert "\n" not in line
    assert line.startswith("RESIZE: ")
    assert line == line.lstrip()


def test_the_report_states_what_changed_and_why(netlist_path, gate_netlist_path):
    """The user asked to be told a new size was chosen; that is this text."""
    report = render_report(plan_resize(netlist_path, baseline=gate_netlist_path))
    for needle in ("XP1", "XP2", "XP3", "2.24", str(EXPECTED_SITES)):
        assert needle in report, f"the report never mentions {needle!r}"
    assert "19.9" in report, "the report must show the budget it was capped by"


def test_resize_writes_both_the_netlist_and_the_report(
    netlist_path, gate_netlist_path, tmp_path
):
    out = tmp_path / "out.spice"
    report = tmp_path / "out.md"
    plan = resize(netlist_path, out, report=report, baseline=gate_netlist_path)
    assert out.is_file() and out.stat().st_size > 0
    assert report.is_file() and report.stat().st_size > 0
    assert plan.multiplier == EXPECTED_MULTIPLIER


# ----------------------------------------------------------- fail closed ----


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cell": "no_such_cell"},
        {"multipliers": [0.0]},
        {"multipliers": [-2.0]},
    ],
)
def test_unusable_arguments_raise_rather_than_guess(netlist_path, kwargs):
    with pytest.raises(ResizeError):
        plan_resize(netlist_path, area_budget_um2=1000.0, **kwargs)


def test_a_missing_netlist_raises(tmp_path):
    with pytest.raises((ResizeError, FileNotFoundError, OSError)):
        plan_resize(tmp_path / "nope.spice", area_budget_um2=1000.0)


def test_an_empty_netlist_raises(tmp_path):
    empty = tmp_path / "empty.spice"
    empty.write_text("")
    with pytest.raises(ResizeError):
        plan_resize(empty, area_budget_um2=1000.0)
