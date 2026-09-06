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
    gds_boundary,
    layer_inventory,
    lef_macro_geometry,
    lef_macros,
    pdk_lef_geometry,
    routing_metals_used,
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
