# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Geometry is measured, never assumed
# ================================================================

"""Every size the flow reports has to come out of an artifact.

The trap this file guards is the one that makes a cell look finished: a
measurement that quietly falls back to something *else* that is also a pair of
numbers.  The shape bounding box of a standard cell is not its placement
footprint -- wells and implants overhang the boundary on purpose so abutted
neighbours share them -- so a bbox reported as an area is both too large and
attributed to geometry the neighbour also pays for.  ``gds_boundary`` may fall
back to it, but never silently, and never as though it were the same number.

Ground truth for the whole file is ``build/AION_inv_nand2_nor2_1.gds``: the
built, DRC- and LVS-clean worked example, 2.88 x 3.78 um from its own
prBoundary, drawn on Metal1 only.
"""

from __future__ import annotations

import pytest

from aion_layout.metrics import (
    GRID_TOL_UM,
    ROW_HEIGHT_UM,
    SITE_WIDTH_UM,
    CellGeometry,
    MetricsError,
    _grade_footprint,
    drawn_shapes,
    gds_boundary,
    layer_inventory,
    lef_macro_geometry,
    lef_macros,
    lef_pin_access,
    pdk_lef_geometry,
    routing_metals_used,
    tap_contact_problems,
)
from conftest import CELL, KNOWN_AREA_UM2, KNOWN_HEIGHT_UM, KNOWN_WIDTH_UM

# ---------------------------------------------------------------------------
# The known-good cell
# ---------------------------------------------------------------------------


def test_known_cell_is_measured_from_its_prboundary(known_gds):
    """The verified cell measures 2.88 x 3.78 um, and says where that came from."""
    geometry = gds_boundary(known_gds, CELL)

    assert geometry.source == "prBoundary", (
        "the placement footprint must be read from the prBoundary the cell "
        f"draws; this one was taken from {geometry.source!r}, which measures "
        "something else"
    )
    assert geometry.width_um == pytest.approx(KNOWN_WIDTH_UM, abs=GRID_TOL_UM), (
        f"{CELL} is {KNOWN_WIDTH_UM} um wide in the GDS the tools verified; "
        f"the measurement says {geometry.width_um}"
    )
    assert geometry.height_um == pytest.approx(KNOWN_HEIGHT_UM, abs=GRID_TOL_UM), (
        f"a core cell is exactly one {ROW_HEIGHT_UM} um row tall; the "
        f"measurement says {geometry.height_um}"
    )
    assert geometry.area_um2 == pytest.approx(KNOWN_AREA_UM2, abs=1e-4), (
        "area is width x height of the placement footprint, which is the "
        f"number the Liberty `area` attribute takes: expected {KNOWN_AREA_UM2}"
    )
    assert geometry.cell == CELL, (
        "the geometry must name the cell it measured, or a report cannot say "
        f"what it is about; it named {geometry.cell!r}"
    )


def test_known_cell_is_row_legal(known_gds):
    """A cell that cannot sit in a row is not a standard cell, whatever its DRC."""
    geometry = gds_boundary(known_gds, CELL)

    assert geometry.problems == (), (
        "the verified cell must be row-legal -- one row tall and a whole "
        f"number of {SITE_WIDTH_UM} um sites wide -- but it was graded: "
        f"{geometry.problems}"
    )
    assert geometry.row_legal, "row_legal must agree with an empty problems tuple"
    assert geometry.sites == pytest.approx(6.0), (
        f"{KNOWN_WIDTH_UM} um is exactly 6 CoreSite pitches; the width is only "
        f"legal on the placement grid at a whole number of sites, got "
        f"{geometry.sites}"
    )


def test_describe_states_the_source(known_gds):
    """A one-line summary that omits the source invites a bbox to be quoted as area."""
    line = gds_boundary(known_gds, CELL).describe()

    assert "prBoundary" in line, (
        "describe() has to name the artifact the numbers came from; a reader "
        f"cannot tell a footprint from a bounding box otherwise: {line!r}"
    )
    assert CELL in line, f"describe() must name the cell: {line!r}"


def test_layer_inventory_finds_metal1_and_no_metal2(known_gds):
    """The verified cell routes on Metal1 alone; Metal2 in it would be a blockage."""
    inventory = layer_inventory(known_gds, CELL)

    assert "Metal1" in inventory, (
        "the cell draws Metal1 pins and rails, so an inventory without Metal1 "
        f"means the layer map is wrong, not that the cell is empty: "
        f"{sorted(inventory)}"
    )
    assert inventory["Metal1"].gds_pair == (8, 0), (
        "Metal1 drawing is GDS 8/0 in SG13G2; an inventory keyed to the wrong "
        f"pair is measuring another layer: {inventory['Metal1'].gds_pair}"
    )
    assert inventory["Metal1"].polygons > 0 and inventory["Metal1"].area_um2 > 0, (
        "a layer only appears in the inventory when it carries geometry, so a "
        "zero count or area here is a merge that lost the shapes"
    )
    assert "Metal2" not in inventory, (
        "this cell is Metal1-only; Metal2 inside a standard cell is a routing "
        "blockage the block router has to work around, and must never appear "
        f"unnoticed: {sorted(inventory)}"
    )


def test_routing_metals_used_reports_metal1_only(known_gds):
    """The metals a cell spends are a floorplan fact, reported not discovered."""
    assert routing_metals_used(known_gds, CELL) == ["Metal1"], (
        "the verified cell is Metal1-only; any other answer means the flow "
        "would under- or over-state the routing resources the cell consumes"
    )


# ---------------------------------------------------------------------------
# A GDS with no prBoundary
# ---------------------------------------------------------------------------


def test_missing_prboundary_falls_back_but_says_so(gds_factory):
    """A bbox may be reported, but never as though it were the footprint."""
    path = gds_factory("NOBOUND", boundary_um=None, metal_um=(0.0, 0.0, 2.88, 3.78))

    geometry = gds_boundary(path, "NOBOUND")

    assert geometry.source == "bbox", (
        "with no prBoundary drawn the numbers are a shape bounding box and the "
        f"source must say so; it said {geometry.source!r}"
    )
    assert geometry.problems, (
        "a bbox fallback must carry a problem: the numbers are not the "
        "placement footprint, and a caller that exports a LEF from them "
        "publishes a cell whose size disagrees with its own boundary"
    )
    assert not geometry.row_legal, (
        "a footprint of unknown provenance is not row-legal evidence, even "
        "when its numbers happen to be the right ones"
    )
    assert any("prBoundary" in p for p in geometry.problems), (
        "the problem has to name the missing prBoundary so a reader can fix "
        f"the cause rather than the symptom: {geometry.problems}"
    )


def test_missing_prboundary_raises_when_the_fallback_is_refused(gds_factory):
    """A caller that needs the real footprint must be able to demand it."""
    path = gds_factory("NOBOUND", boundary_um=None, metal_um=(0.0, 0.0, 2.88, 3.78))

    with pytest.raises(MetricsError) as excinfo:
        gds_boundary(path, "NOBOUND", allow_bbox_fallback=False)

    assert "prBoundary" in str(excinfo.value), (
        "the refusal must name what is missing; 'measurement failed' does not "
        f"tell anyone what to draw: {excinfo.value}"
    )


def test_several_top_cells_refuse_to_guess(gds_factory):
    """Guessing which cell to measure is how the wrong cell gets reported."""
    path = gds_factory("MULTI", cells=3)

    with pytest.raises(MetricsError) as excinfo:
        gds_boundary(path)

    assert "top cells" in str(excinfo.value), (
        "with more than one top cell the measurement is ambiguous and must "
        f"say so rather than picking one: {excinfo.value}"
    )


def test_a_cell_the_gds_does_not_contain_is_an_error(known_gds):
    """Measuring the cell that is there, under the name that was asked for.

    The name reaching these functions comes from a Makefile variable or a CLI
    flag, so a typo is the ordinary case.  Falling back to whatever top cell the
    file happens to hold would report a real, correct measurement of the wrong
    cell -- which is worse than no measurement, because it is believable.
    """
    for measure in (gds_boundary, layer_inventory, routing_metals_used):
        with pytest.raises(MetricsError) as excinfo:
            measure(known_gds, "sg13g2_not_in_this_file")

        assert "sg13g2_not_in_this_file" in str(excinfo.value), (
            f"{measure.__name__} must name the cell it was asked for and could "
            f"not find, never silently measure another: {excinfo.value}"
        )


def test_absent_and_empty_gds_are_errors(tmp_path):
    """A missing or zero-byte GDS is an error, never a cell of size zero."""
    with pytest.raises(MetricsError):
        gds_boundary(tmp_path / "nope.gds")

    empty = tmp_path / "empty.gds"
    empty.write_bytes(b"")
    with pytest.raises(MetricsError) as excinfo:
        gds_boundary(empty)
    assert "empty" in str(excinfo.value), (
        "a zero-byte GDS -- what an OOM-killed writer leaves -- must be "
        f"reported as empty, not measured: {excinfo.value}"
    )


# ---------------------------------------------------------------------------
# _grade_footprint: the three ways a footprint is not row-legal
# ---------------------------------------------------------------------------


def test_grade_footprint_accepts_the_known_good_size():
    """The grader must not reject the size the flow has already verified."""
    assert _grade_footprint(KNOWN_WIDTH_UM, KNOWN_HEIGHT_UM) == (), (
        f"{KNOWN_WIDTH_UM} x {KNOWN_HEIGHT_UM} um is six sites of one row and "
        "is the size of the cell Magic, KLayout and Netgen all passed"
    )


def test_grade_footprint_rejects_a_wrong_row_height():
    """3.7 um is not 3.78 um: a cell that tall cannot abut a row."""
    problems = _grade_footprint(KNOWN_WIDTH_UM, 3.7)

    assert problems, (
        "a 3.7 um cell is 80 nm short of the SG13G2 row and would leave a gap "
        "no filler can close; it must be graded illegal"
    )
    assert any("height" in p for p in problems), (
        f"the problem must name the height as the fault: {problems}"
    )
    assert not CellGeometry(
        cell="X", width_um=KNOWN_WIDTH_UM, height_um=3.7, source="bbox",
        problems=problems,
    ).row_legal, "row_legal must be False whenever problems is non-empty"


def test_grade_footprint_rejects_an_off_site_width():
    """2.9 um is 6.04 sites: off-grid, so the placer cannot legalise it."""
    problems = _grade_footprint(2.9, ROW_HEIGHT_UM)

    assert problems, (
        f"2.9 um is not a multiple of the {SITE_WIDTH_UM} um site pitch, so a "
        "cell that wide has no legal column to sit in"
    )
    assert any("width" in p for p in problems), (
        f"the problem must name the width as the fault: {problems}"
    )
    assert any("site" in p for p in problems), (
        f"the problem must say what the width is measured against: {problems}"
    )


def test_grade_footprint_rejects_a_degenerate_footprint():
    """A zero-area cell is a failed measurement, not a very small cell."""
    problems = _grade_footprint(0.0, ROW_HEIGHT_UM)
    assert any("degenerate" in p for p in problems), (
        f"a zero width has to be called out as degenerate: {problems}"
    )


def test_grade_footprint_reports_every_fault_at_once():
    """One fix per run is one iteration per fix; the grader lists them all."""
    problems = _grade_footprint(2.9, 3.7)
    assert len(problems) >= 2, (
        "a cell that is both the wrong height and off the site grid has two "
        f"faults, and reporting only the first hides the second: {problems}"
    )


# ---------------------------------------------------------------------------
# LEF: what the placer will believe
# ---------------------------------------------------------------------------

_ONE_MACRO_LEF = f"""\
VERSION 5.7 ;
MACRO {CELL}
  CLASS CORE ;
  ORIGIN 0 0 ;
  FOREIGN {CELL} 0 0 ;
  SIZE {KNOWN_WIDTH_UM} BY {KNOWN_HEIGHT_UM} ;
  SITE CoreSite ;
END {CELL}
"""

_TWO_MACRO_LEF = _ONE_MACRO_LEF + """\
MACRO sg13g2_inv_1
  CLASS CORE ;
  SIZE 1.44 BY 3.78 ;
  SITE CoreSite ;
END sg13g2_inv_1
"""


def _pin_lef(*pins, obs=()):
    """A macro carrying exactly the PIN blocks given, as (name, use, body).

    ``obs`` is the body of an OBS block, in the same form as a port body.
    """
    lines = [f"MACRO {CELL}", "  CLASS CORE ;",
             f"  SIZE {KNOWN_WIDTH_UM} BY {KNOWN_HEIGHT_UM} ;", "  SITE CoreSite ;"]
    for name, use, geometry in pins:
        lines.append(f"  PIN {name}")
        if use is not None:
            lines.append(f"    USE {use} ;")
        lines.append("    PORT")
        lines.extend(f"      {line}" for line in geometry)
        lines.append("    END")
        lines.append(f"  END {name}")
    if obs:
        lines.append("  OBS")
        lines.extend(f"      {line}" for line in obs)
        lines.append("  END")
    lines.append(f"END {CELL}")
    return "\n".join(lines) + "\n"


def _write(tmp_path, text):
    lef = tmp_path / "pins.lef"
    lef.write_text(text)
    return lef


def test_the_tracks_a_pin_covers_are_reported_not_required(tmp_path):
    """Metal1 routes along y = n * 0.42 um, and a port no longer has to cross a line.

    TritonRoute pin access reaches a Metal1 port 10 nm or 40 nm off the track
    grid whenever the via has room: it sits on the nearest track or half track
    with its enclosure overlapping the port.  This check used to reject every
    such port.  The lines a port covers are still reported -- a port that
    crosses one is the easy case for the router, not the only one.
    """
    on = ("LAYER Metal1 ;", "RECT 0.975 1.450 1.255 1.790 ;")   # y 1.45..1.79 > 1.68
    off = ("LAYER Metal1 ;", "RECT 2.150 1.090 2.550 1.250 ;")  # between 0.84 and 1.26

    good = lef_pin_access(_write(tmp_path, _pin_lef(("I0", "SIGNAL", on))))
    assert good.ok, good.problems
    assert good.reachable["I0"] == ("Metal1 y",)

    free = lef_pin_access(_write(tmp_path, _pin_lef(("O0", "SIGNAL", off))))
    assert free.ok, (
        "nothing of another net stops a via from overlapping this port, so the "
        f"router reaches it off the grid: {free.problems}"
    )
    assert free.reachable["O0"] == (), "and it is still reported as covering no line"


def test_a_metal2_pin_reports_vertical_tracks(tmp_path):
    """Metal2 is DIRECTION VERTICAL, so the axis of the lines flips to x = n * 0.48 um."""
    on = ("LAYER Metal2 ;", "RECT 2.150 1.090 2.550 1.390 ;")   # x 2.15..2.55 > 2.40
    off = ("LAYER Metal2 ;", "RECT 2.500 1.090 2.850 1.390 ;")  # between 2.40 and 2.88

    good = lef_pin_access(_write(tmp_path, _pin_lef(("O0", "SIGNAL", on))))
    assert good.ok and good.reachable["O0"] == ("Metal2 x",), good
    free = lef_pin_access(_write(tmp_path, _pin_lef(("O0", "SIGNAL", off))))
    assert free.ok and free.reachable["O0"] == (), free


def test_a_pin_passes_on_any_one_of_its_layers(tmp_path):
    """A port drawn on two metals only has to be reachable on one of them."""
    both = ("LAYER Metal1 ;", "RECT 2.150 1.090 2.550 1.250 ;",   # off grid
            "LAYER Metal2 ;", "RECT 2.150 1.090 2.550 1.390 ;")   # on grid in x
    access = lef_pin_access(_write(tmp_path, _pin_lef(("O0", "SIGNAL", both))))

    assert access.ok, f"either rect is a way in: {access.problems}"
    assert access.reachable["O0"] == ("Metal2 x",)


def test_a_thin_port_is_reached_by_a_via_that_overhangs_it(tmp_path):
    """0.21 um across is not a floor: the via's enclosure may run off the port.

    TritonRoute reaches a 0.18 um Metal1 port when no other net's Metal1 is
    within 0.18 um of where the overhanging enclosure goes.  It cannot reach the
    same port with another net's Metal1 0.18 um above and below it, because then
    every enclosure that overlaps the port crowds one of them -- and the reason
    has to say it is Metal1 that closes the door, not Metal2.
    """
    thin = ("LAYER Metal1 ;", "RECT 2.150 1.090 2.550 1.270 ;")   # 0.40 x 0.18
    free = lef_pin_access(_write(tmp_path, _pin_lef(("O0", "SIGNAL", thin))))
    assert free.ok, free.problems

    boxed = (
        "LAYER Metal1 ;",
        "RECT 2.000 1.450 2.700 1.540 ;",   # 0.18 um above the port
        "RECT 2.000 0.820 2.700 0.910 ;",   # 0.18 um below it
    )
    bad = lef_pin_access(_write(tmp_path, _pin_lef(("O0", "SIGNAL", thin), obs=boxed)))
    assert not bad.ok
    assert "has no via access" in bad.problems[0]
    assert "Metal1 enclosure cannot overlap the port" in bad.problems[0], bad.problems


def test_a_landing_pad_may_hang_off_the_end_of_the_port(tmp_path):
    """sg13g2_nand4_1/A: the PDK's own port is narrower than the via pad.

    Its widest port RECT is 0.275 um against a 0.29 um pad, and it routes,
    because the overhang lands on nothing of another net.
    """
    narrow = ("LAYER Metal1 ;", "RECT 1.965 1.590 2.240 1.850 ;")  # 0.275 x 0.26
    access = lef_pin_access(_write(tmp_path, _pin_lef(("A", "SIGNAL", narrow))))
    assert access.ok, access.problems


def test_an_obstruction_over_the_port_leaves_the_via_nowhere_to_go(tmp_path):
    """A port whose own strap was written out as an obstruction is unroutable.

    This is AION_nand2_o21ai_0/O0 as first drawn.  The cell routes its output up
    to Metal2, but the strap went to OBS -- sitting across the pin, wider than
    any overhang can escape.  Moving that same rect into the port is the fix.
    """
    port = ("LAYER Metal1 ;", "RECT 1.790 0.960 2.050 1.270 ;")
    strap = ("LAYER Metal2 ;", "RECT 1.835 0.950 2.035 2.650 ;")

    bad = lef_pin_access(_write(tmp_path, _pin_lef(("O0", "SIGNAL", port), obs=strap)))
    assert not bad.ok, "the Metal2 obstruction is within 0.21 um of every pad"
    assert "has no via access" in bad.problems[0]
    assert "Metal2 pad" in bad.problems[0], bad.problems
    assert "DRT-0073" in bad.problems[0]

    good = lef_pin_access(_write(tmp_path, _pin_lef(("O0", "SIGNAL", port + strap))))
    assert good.ok, f"labelled as part of the port, the strap is access: {good.problems}"


def test_a_via_slides_off_the_port_to_clear_another_nets_strap(tmp_path):
    """AION_mux2_0/I0: refused by this check, and routed by TritonRoute anyway.

    Another net's Metal2 strap runs 5 nm right of the Metal1 port, so no via
    centred over the port keeps its pad 0.21 um clear -- which is all this check
    used to try, and why the cell never reached implementation/cells/.  Detailed
    routing connected all 126 instances with 0 DRC errors: a Via1_YY 60 nm left
    of the port, its cut overlapping the port by 35 nm, its pad 0.265 um from
    the strap.  Wall off the free Metal1 it hangs onto and pin access finds no
    access point, so neither may this.
    """
    port = ("LAYER Metal1 ;", "RECT 2.220 1.450 2.520 1.790 ;")
    strap = ("LAYER Metal2 ;", "RECT 2.525 0.620 2.725 2.710 ;")
    reached = lef_pin_access(_write(tmp_path, _pin_lef(("I0", "SIGNAL", port), obs=strap)))
    assert reached.ok, reached.problems

    wall = ("LAYER Metal1 ;", "RECT 1.900 1.450 2.000 1.790 ;")
    blocked = lef_pin_access(
        _write(tmp_path, _pin_lef(("I0", "SIGNAL", port), obs=strap + wall))
    )
    assert not blocked.ok
    assert "has no via access" in blocked.problems[0], blocked.problems


def test_metal2_on_both_sides_has_to_leave_the_pad_its_spacing(tmp_path):
    """A second strap closes the escape: the pad needs 0.21 um from each.

    Calibrated against pin access on AION_mux2_0/I0 with a strap added on the
    left: reached with it ending at x = 1.80, no access point at 1.95.
    """
    port = ("LAYER Metal1 ;", "RECT 2.220 1.450 2.520 1.790 ;")
    right = ("LAYER Metal2 ;", "RECT 2.525 0.620 2.725 2.710 ;")
    far = ("RECT 1.600 0.620 1.800 2.710 ;",)
    near = ("RECT 1.750 0.620 1.950 2.710 ;",)

    reached = lef_pin_access(_write(tmp_path, _pin_lef(("I0", "SIGNAL", port), obs=right + far)))
    assert reached.ok, reached.problems

    blocked = lef_pin_access(_write(tmp_path, _pin_lef(("I0", "SIGNAL", port), obs=right + near)))
    assert not blocked.ok
    assert "Metal2 pad" in blocked.problems[0], blocked.problems


def test_another_pins_metal_is_another_net(tmp_path):
    """A neighbouring pin blocks a via exactly as an obstruction does."""
    port = ("LAYER Metal1 ;", "RECT 2.220 1.450 2.520 1.790 ;")
    over = ("LAYER Metal2 ;", "RECT 2.170 0.620 2.570 2.710 ;")   # crosses x = 2.40

    access = lef_pin_access(
        _write(tmp_path, _pin_lef(("I0", "SIGNAL", port), ("I1", "SIGNAL", over)))
    )
    assert len(access.problems) == 1 and "PIN I0" in access.problems[0], access.problems

    own = lef_pin_access(_write(tmp_path, _pin_lef(("I0", "SIGNAL", port + over))))
    assert own.ok, f"the same Metal2 in I0's own port is a landing: {own.problems}"


#: AION_mux2i_1 as published to implementation/pdk_extension/, GatPoly dropped.
_MUX2I_1 = """\
MACRO AION_mux2i_1
  CLASS CORE ;
  SIZE 3.360 BY 3.780 ;
  SITE CoreSite ;
  PIN I2
    PORT
      LAYER Metal1 ;
        RECT 1.040 1.970 2.930 2.130 ;
        RECT 1.040 1.450 1.320 1.970 ;
        RECT 2.650 1.450 2.930 1.970 ;
    END
  END I2
  PIN I0
    PORT
      LAYER Metal1 ;
        RECT 2.915 2.310 3.270 2.910 ;
        RECT 3.110 1.250 3.270 2.310 ;
        RECT 1.875 1.090 3.270 1.250 ;
        RECT 1.875 0.590 2.175 1.090 ;
    END
  END I0
  PIN I1
    PORT
      LAYER Metal1 ;
        RECT 1.875 2.910 2.175 3.230 ;
        RECT 1.895 2.310 2.155 2.910 ;
        RECT 2.880 0.590 3.210 0.910 ;
      LAYER Metal2 ;
        RECT 1.875 2.985 3.145 3.185 ;
        RECT 2.945 0.660 3.145 2.985 ;
    END
  END I1
  PIN O0
    PORT
      LAYER Metal1 ;
        RECT 0.180 2.310 0.545 2.910 ;
        RECT 0.180 0.910 0.340 2.310 ;
        RECT 0.180 0.590 0.545 0.910 ;
    END
  END O0
  PIN VDD
    USE POWER ;
    PORT
      LAYER Metal1 ;
        RECT 0.000 3.560 3.360 4.000 ;
        RECT 0.795 2.310 1.055 3.560 ;
    END
  END VDD
  PIN VSS
    USE GROUND ;
    PORT
      LAYER Metal1 ;
        RECT 0.795 0.220 1.055 0.880 ;
        RECT 0.000 -0.220 3.360 0.220 ;
    END
  END VSS
  OBS
      LAYER Metal1 ;
        RECT 1.285 2.310 1.585 2.910 ;
        RECT 2.385 2.310 2.685 2.910 ;
        RECT 0.520 1.450 0.820 1.790 ;
        RECT 1.900 1.450 2.420 1.790 ;
        RECT 1.285 0.590 1.585 0.910 ;
        RECT 2.385 0.590 2.685 0.910 ;
      LAYER Metal2 ;
        RECT 0.570 0.450 0.770 1.770 ;
        RECT 1.335 1.720 1.535 2.750 ;
        RECT 1.335 1.520 2.200 1.720 ;
        RECT 1.335 0.660 1.535 1.520 ;
        RECT 2.435 0.450 2.635 2.595 ;
        RECT 0.570 0.250 2.635 0.450 ;
  END
END AION_mux2i_1
"""


def test_the_select_pin_that_aborted_detailed_routing_is_still_rejected(tmp_path):
    """AION_mux2i_1/I2: 'DRT-0073 No access point', in a PnR run and in pin access.

    Both pads and the strap joining them are hemmed in by other nets' Metal2
    risers and Metal1 fingers.  Relaxing the rule for the pins the router does
    reach must not relax it for this one -- and must not flag the four that
    route.
    """
    lef = tmp_path / "mux2i.lef"
    lef.write_text(_MUX2I_1)
    access = lef_pin_access(lef, "AION_mux2i_1")

    assert [problem.split()[1] for problem in access.problems] == ["I2"], access.problems


# ---------------------------------------------------------------------------
# Rail tap contacts: the grid abutted rows share
# ---------------------------------------------------------------------------

ON_GRID = [(160.0, -80.0, 320.0, 80.0), (640.0, -80.0, 800.0, 80.0)]


def test_rail_taps_on_the_pdk_grid_pass():
    """160 + 480k is what all 2497 rail contacts of the PDK library use."""
    assert tap_contact_problems(ON_GRID) == ()
    top = [(x1, 3700.0, x2, 3860.0) for x1, _, x2, _ in ON_GRID]
    assert tap_contact_problems(top) == (), "the top rail is graded the same way"


def test_rail_taps_off_the_grid_are_caught():
    """The 150 + 430k grid the AION cells used, and what it cost.

    Each contact is legal where it sits; what is not legal is what happens when
    the row above puts its own contact at 160..320 and the two overlap by 70 nm.
    """
    off = [(70.0, -80.0, 230.0, 80.0), (500.0, -80.0, 660.0, 80.0)]
    problems = tap_contact_problems(off)

    assert len(problems) == 1, "one problem for the cell, not one per contact"
    assert "2 power-rail tap contact(s)" in problems[0], problems[0]
    assert "70..230" in problems[0], f"it has to name where they are: {problems[0]}"
    assert "160 + 480k" in problems[0], f"and the grid to move to: {problems[0]}"


def test_a_contact_that_is_not_in_a_rail_is_not_a_tap():
    """Transistor contacts sit on no shared grid and must not be graded."""
    inside = [(70.0, 670.0, 230.0, 830.0), (1355.0, 2360.0, 1515.0, 2520.0)]
    assert tap_contact_problems(inside) == (), (
        "only geometry reaching into a rail is shared with the abutting row"
    )


def test_a_tap_of_the_wrong_size_is_caught():
    """On-grid on its left edge is not enough if the cut is not 160 nm."""
    wide = [(160.0, -80.0, 400.0, 80.0)]
    assert tap_contact_problems(wide), (
        "a 240 nm cut at x = 160 still overhangs the neighbour's 160..320"
    )


def test_drawn_shapes_reads_the_layers_the_abutment_rules_need(known_gds):
    """The rules are only as good as what is read out of the GDS for them."""
    drawn = drawn_shapes(known_gds, cell_name=CELL)

    assert "Metal1" in drawn and drawn["Metal1"], f"no Metal1 read: {list(drawn)}"
    assert "Cont" in drawn and drawn["Cont"], f"no Cont read: {list(drawn)}"
    assert all(len(r) == 4 for r in drawn["Cont"]), "rectangles, in nm"
    assert any(r[1] < 220 and r[3] > -220 for r in drawn["Cont"]), (
        "the worked example does have rail taps, so the tap rule has input"
    )


def test_power_pins_are_not_graded(tmp_path):
    """The PDN straps VDD and VSS; the signal router never lands on them."""
    off = ("LAYER Metal1 ;", "RECT 0.200 0.200 0.360 0.360 ;")
    by_use = lef_pin_access(
        _write(tmp_path, _pin_lef(("VDD", "POWER", off), ("VSS", "GROUND", off)))
    )
    assert by_use.ok and by_use.reachable == {}, by_use.problems

    # magic writes no USE line, so the names have to carry it on their own.
    by_name = lef_pin_access(
        _write(tmp_path, _pin_lef(("VDD", None, off), ("VSS", None, off)))
    )
    assert by_name.ok, f"VDD/VSS must be exempt without a USE line too: {by_name.problems}"


def test_a_pin_with_no_routing_layer_geometry_is_unreachable(tmp_path):
    """A port drawn only on a masterslice is not something a wire can reach."""
    only_poly = ("LAYER GatPoly ;", "RECT 0.200 0.200 0.360 0.360 ;")
    access = lef_pin_access(_write(tmp_path, _pin_lef(("I0", "SIGNAL", only_poly))))

    assert not access.ok
    assert any("no geometry on a routing layer" in p for p in access.problems), (
        f"the reason must distinguish 'off the grid' from 'not on metal': {access.problems}"
    )


def test_a_polygon_port_is_reported_rather_than_assumed_good(tmp_path):
    """Unmeasured is not passed -- the same rule the prBoundary check follows.

    A POLYGON's bounding box can straddle a track while the polygon itself
    does not, so passing it on the bbox would be inventing a verdict.
    """
    poly = ("LAYER Metal1 ;", "POLYGON 0.2 0.2 0.4 0.2 0.4 0.5 0.2 0.5 ;")
    access = lef_pin_access(_write(tmp_path, _pin_lef(("O0", "SIGNAL", poly))))

    assert not access.ok
    assert any("POLYGON" in p for p in access.problems), access.problems


def test_lef_pin_access_names_the_macro_when_there_are_several(tmp_path):
    """Same contract as lef_macro_geometry: never guess which cell was meant."""
    lef = tmp_path / "two.lef"
    lef.write_text(_TWO_MACRO_LEF)

    with pytest.raises(MetricsError) as excinfo:
        lef_pin_access(lef)
    assert CELL in str(excinfo.value) and "sg13g2_inv_1" in str(excinfo.value)

    assert lef_pin_access(lef, CELL).cell == CELL


def test_lef_macro_geometry_reads_the_size_line(tmp_path):
    """The LEF SIZE is what a placer allocates; it is read, not recomputed."""
    lef = tmp_path / "one.lef"
    lef.write_text(_ONE_MACRO_LEF)

    geometry = lef_macro_geometry(lef)

    assert geometry.source == "lef", (
        f"a LEF measurement must be attributed to the LEF: {geometry.source!r}"
    )
    assert (geometry.width_um, geometry.height_um) == (
        KNOWN_WIDTH_UM,
        KNOWN_HEIGHT_UM,
    ), (
        "the geometry must be the SIZE line verbatim; anything else means the "
        "flow and the placer disagree about how big the cell is"
    )
    assert geometry.problems == (), "the known-good SIZE is row-legal"


def test_lef_with_two_macros_refuses_to_guess(tmp_path):
    """Picking one of two macros is how the wrong cell's area gets published."""
    lef = tmp_path / "two.lef"
    lef.write_text(_TWO_MACRO_LEF)

    assert set(lef_macros(lef)) == {CELL, "sg13g2_inv_1"}, (
        "both macros must be found before the ambiguity can be refused"
    )

    with pytest.raises(MetricsError) as excinfo:
        lef_macro_geometry(lef)

    message = str(excinfo.value)
    assert "2 macros" in message, (
        f"the refusal must say how many candidates there were: {message}"
    )
    assert CELL in message and "sg13g2_inv_1" in message, (
        "the refusal must name the candidates, so the caller can pick one "
        f"instead of being told only that it failed: {message}"
    )

    named = lef_macro_geometry(lef, CELL)
    assert named.cell == CELL, (
        "naming the macro resolves the ambiguity; refusing then too would make "
        "a multi-macro LEF unusable"
    )


def test_lef_without_a_size_line_is_an_error(tmp_path):
    """A macro with no SIZE has no footprint; it must not default to zero."""
    lef = tmp_path / "nosize.lef"
    lef.write_text(f"MACRO {CELL}\n  CLASS CORE ;\n  SITE CoreSite ;\nEND {CELL}\n")

    with pytest.raises(MetricsError) as excinfo:
        lef_macro_geometry(lef)
    assert "SIZE" in str(excinfo.value), (
        f"the error must name the missing SIZE line: {excinfo.value}"
    )


def test_lef_with_no_macro_at_all_is_an_error(tmp_path):
    """An empty LEF is a failed export, not a library of zero cells."""
    lef = tmp_path / "empty.lef"
    lef.write_text("VERSION 5.7 ;\nEND LIBRARY\n")
    with pytest.raises(MetricsError):
        lef_macro_geometry(lef)


def test_pdk_lef_geometry_measures_several_named_macros(tmp_path):
    """The baseline's area comes from the PDK LEF, macro by named macro."""
    lef = tmp_path / "two.lef"
    lef.write_text(_TWO_MACRO_LEF)

    found = pdk_lef_geometry([CELL, "sg13g2_inv_1"], lef)

    assert set(found) == {CELL, "sg13g2_inv_1"}
    assert found["sg13g2_inv_1"].width_um == pytest.approx(1.44), (
        "each macro must get its own SIZE, not the first one in the file"
    )

    with pytest.raises(MetricsError) as excinfo:
        pdk_lef_geometry(["sg13g2_not_a_cell"], lef)
    assert "sg13g2_not_a_cell" in str(excinfo.value), (
        "asking for a macro the LEF does not define must name it, never come "
        f"back as a cell of size zero: {excinfo.value}"
    )
