# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-13
#  Description:               TritonRoute's word on pin access, graded
# ================================================================

"""The design pin access is run on, and what its log is allowed to mean.

No OpenROAD runs here.  The logs below are the verdict-bearing lines of real
runs on the published cells: ``AION_mux2i_1``, whose ``I2`` aborted detailed
routing with ``DRT-0073`` in step 7, and ``AION_xnor2_1`` with its via cuts in
the LEF, which TritonRoute enters on Metal2 at ``I0`` instead of dropping the
``Via1`` that collided with the cell's own in step 7.
"""

from __future__ import annotations

import re

from aion_layout.pin_access import (
    NEIGHBOUR,
    grade_log,
    placement_def,
    signal_pins,
)
from conftest import CELL

_LEF = f"""\
VERSION 5.7 ;
MACRO {CELL}
  CLASS CORE ;
  SIZE 2.880 BY 3.780 ;
  SITE CoreSite ;
  PIN I0
    PORT
      LAYER Metal1 ;
        RECT 0.200 1.450 0.500 1.790 ;
    END
  END I0
  PIN O0
    DIRECTION OUTPUT ;
    PORT
      LAYER Metal1 ;
        RECT 2.000 1.450 2.300 1.790 ;
    END
  END O0
  PIN VDD
    USE POWER ;
    PORT
      LAYER Metal1 ;
        RECT 0.000 3.560 2.880 4.000 ;
    END
  END VDD
  PIN VSS
    PORT
      LAYER Metal1 ;
        RECT 0.000 -0.220 2.880 0.220 ;
    END
  END VSS
END {CELL}
END LIBRARY
"""

_INSTANCES = {"cell_N_1": "N", "cell_N_2": "N", "cell_FS_1": "FS", "cell_FS_2": "FS"}

_UNREACHABLE = """\
[INFO DRT-0150] Reading design.
[ERROR DRT-0073] No access point for cell_N_1/I2 (AION_mux2i_1).
[ERROR DRT-0073] No access point for cell_FS_1/I2 (AION_mux2i_1).
PIN_ACCESS_AP cell_N_1 I2 0
PIN_ACCESS_AP cell_N_1 I0 0
PIN_ACCESS_DONE 1
"""

_REACHED = """\
[INFO DRT-0078]   Complete 22 pins.
PIN_ACCESS_AP cell_N_1 I0 1 720,420,Metal2
PIN_ACCESS_AP cell_N_1 I1 1 2725,1620,Metal1
PIN_ACCESS_AP cell_N_2 I0 1 720,420,Metal2
PIN_ACCESS_AP cell_N_2 I1 1 2725,1620,Metal1
PIN_ACCESS_AP cell_FS_1 I0 1 720,2520,Metal2
PIN_ACCESS_AP cell_FS_1 I1 1 2725,2160,Metal1
PIN_ACCESS_AP cell_FS_2 I0 1 720,2520,Metal2
PIN_ACCESS_AP cell_FS_2 I1 1 2725,2160,Metal1
PIN_ACCESS_DONE 0
"""


def _lef(tmp_path):
    path = tmp_path / f"{CELL}.lef"
    path.write_text(_LEF)
    return path


def test_the_design_places_the_cell_the_way_step_7_does(tmp_path):
    """N and FS rows, abutted, on the site grid, every signal pin on a net."""
    design, instances = placement_def(_lef(tmp_path), CELL)

    assert sorted(instances.values()) == ["FS", "FS", "N", "N"], instances
    placed = re.findall(r"^- (\S+) (\S+) \+ FIXED \( (\d+) (\d+) \) (\S+) ;$", design, re.M)
    rows = {}
    for name, master, x, y, orient in placed:
        assert int(x) % 480 == 0 and int(y) % 3780 == 0, f"{name} is off the grid"
        rows.setdefault((y, orient), []).append((int(x), master))
    assert set(rows) == {("3780", "N"), ("7560", "FS")}, rows
    for cells in rows.values():
        cells.sort()
        assert [m for _, m in cells] == [NEIGHBOUR, CELL, CELL, NEIGHBOUR], cells
        widths = {NEIGHBOUR: 1440, CELL: 2880}
        for (x, m), (nx, _) in zip(cells, cells[1:]):
            assert x + widths[m] == nx, f"not abutted: {cells}"

    for inst in instances:
        for pin in ("I0", "O0"):
            assert f"( {inst} {pin} )" in design, f"pin access skips a pin with no net: {inst}/{pin}"
        assert f"( {inst} VDD )" not in design and f"( {inst} VSS )" not in design


def test_supplies_are_not_signal_pins_with_or_without_a_use_line(tmp_path):
    """magic writes USE on some supplies and not others; neither is routed to."""
    assert signal_pins(_lef(tmp_path), CELL) == ["I0", "O0"]


def test_a_pin_with_no_access_point_is_named_with_its_rows():
    report = grade_log(_UNREACHABLE, "AION_mux2i_1", _INSTANCES, ["I2", "I0"])

    assert report.result == "FAIL", report
    assert len(report.problems) == 1 and report.problems[0].startswith("PIN I2:"), report.problems
    assert "N and FS" in report.problems[0], report.problems[0]
    assert "DRT-0073" in report.problems[0], "name the error it prevents"


def test_every_pin_reached_is_a_pass_with_where_it_was_reached():
    report = grade_log(_REACHED, "AION_xnor2_1", _INSTANCES, ["I0", "I1"])

    assert report.result == "PASS", report.problems
    assert report.access_points["I0"] == ((0.72, 0.42, "Metal2"),), report.access_points


def test_a_run_that_did_not_finish_is_an_error_not_a_pass():
    """No DONE marker: the script died before it could say anything."""
    truncated = _REACHED.replace("PIN_ACCESS_DONE 0\n", "")
    assert grade_log(truncated, "AION_xnor2_1", _INSTANCES, ["I0", "I1"]).result == "ERROR"


def test_an_error_pin_access_does_not_explain_is_an_error():
    odd = "[ERROR ODB-0250] something unrelated\n" + _REACHED
    report = grade_log(odd, "AION_xnor2_1", _INSTANCES, ["I0", "I1"])
    assert report.result == "ERROR" and "ODB-0250" in report.problems[0], report


def test_a_failed_run_that_names_no_pin_is_an_error():
    assert grade_log("PIN_ACCESS_DONE 1\n", CELL, _INSTANCES, ["I0"]).result == "ERROR"


def test_a_pin_the_run_never_reported_is_not_graded_reached():
    """Absent evidence is not a pass: I1 missing from the log is unknown."""
    report = grade_log(_REACHED, "AION_xnor2_1", _INSTANCES, ["I0", "I1", "I2"])
    assert report.result == "ERROR" and "I2" in report.problems[0], report


def test_a_pin_with_no_preferred_access_point_fails_even_without_drt_0073():
    empty = _REACHED.replace("cell_FS_2 I1 1 2725,2160,Metal1", "cell_FS_2 I1 0 ")
    report = grade_log(empty, "AION_xnor2_1", _INSTANCES, ["I0", "I1"])
    assert report.result == "FAIL" and report.problems[0].startswith("PIN I1:"), report
