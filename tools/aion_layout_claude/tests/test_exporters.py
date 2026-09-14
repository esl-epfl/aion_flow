# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               A published view is a promise to the next tool
# ================================================================

"""The exported views are read by tools that will not argue back.

A LEF with ``CLASS BLOCK`` makes OpenROAD treat a standard cell as a hard macro
and refuse to place it in a row; a LEF with no ``SITE`` cannot be legalised at
all; a LEF with no ``PIN VSS`` leaves the power grid nothing to strap onto.
None of those is visible in the layout, and each is discovered at
place-and-route, an hour after the cell was called finished.

So ``check_lef`` is the gate, and the one behaviour it must have is to report
**every** failure at once: a check that stops at the first problem turns one
review into four rounds of the same review.  The other two exporters are pinned
on the mistakes their reference implementations actually make -- a trailing
comma in a Verilog port list (which does not compile) and a ``.include`` left in
a CDL netlist (which is not connectivity).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import CELL, optional_module

exporters = optional_module("aion_layout.exporters")

ExportError = exporters.ExportError


def lef_text(
    *,
    cell=CELL,
    cell_class="CORE",
    site="CoreSite",
    width=2.88,
    height=3.78,
    pins=("I0", "I1", "I2", "O0", "VDD", "VSS"),
    pin_rect=(0.150, 0.310, 0.440, 0.530),
    obs=(),
):
    """A LEF macro with one knob per requirement, so each can be broken alone.

    ``pin_rect`` is the Metal1 port of the first pin; each further pin is the
    same rectangle ``PIN_STEP`` um to the right, because pins are different nets
    and a via has to keep its spacing from all of them.  The default straddles
    y = 0.42 um, the first Metal1 track, and puts the sixth pin's right edge at
    x = 2.79 um: half the 0.18 um Metal1 spacing inside the 2.88 um cell, as
    close as the abutment rule allows.  ``obs`` is ``(layer, rect)`` pairs
    written to an OBS block, which is how a test takes a pin's via access away.
    """
    lines = ["VERSION 5.7 ;", "BUSBITCHARS \"[]\" ;", "", f"MACRO {cell}"]
    if cell_class is not None:
        lines.append(f"  CLASS {cell_class} ;")
    lines.append("  ORIGIN 0 0 ;")
    lines.append(f"  FOREIGN {cell} 0 0 ;")
    lines.append(f"  SIZE {width} BY {height} ;")
    if site is not None:
        lines.append(f"  SITE {site} ;")
    for index, pin in enumerate(pins):
        direction = "INOUT" if pin in ("VDD", "VSS") else "INPUT"
        use = "POWER" if pin == "VDD" else "GROUND" if pin == "VSS" else "SIGNAL"
        x1, y1, x2, y2 = pin_rect
        shift = index * PIN_STEP
        lines += [
            f"  PIN {pin}",
            f"    DIRECTION {direction} ;",
            f"    USE {use} ;",
            "    PORT",
            "      LAYER Metal1 ;",
            "        RECT {:.3f} {:.3f} {:.3f} {:.3f} ;".format(
                x1 + shift, y1, x2 + shift, y2
            ),
            "    END",
            f"  END {pin}",
        ]
    if obs:
        lines.append("  OBS")
        for layer, rect in obs:
            lines.append(f"      LAYER {layer} ;")
            lines.append("        RECT {:.3f} {:.3f} {:.3f} {:.3f} ;".format(*rect))
        lines.append("  END")
    lines += [f"END {cell}", "", "END LIBRARY"]
    return "\n".join(lines) + "\n"


#: How far right each pin's port sits from the previous one: 0.18 um of Metal1
#: between neighbouring 0.29 um ports, which is exactly the minimum spacing.
PIN_STEP = 0.47

#: Metal2 across the first pin of the default fixture and well past it, so that
#: no via reaching that pin keeps its pad 0.21 um clear, while the second pin
#: still has room for one.  It starts 0.355 um up, clear of the PDN's rail
#: via pad, so that the only thing wrong with it is where it sits over the pin.
STRAP_OVER_FIRST_PIN = (("Metal2", (0.150, 0.355, 0.450, 1.200)),)


def write_lef(tmp_path, **kwargs):
    path = tmp_path / "cell.lef"
    path.write_text(lef_text(**kwargs))
    return path


# ---------------------------------------------------------------------------
# check_lef
# ---------------------------------------------------------------------------


def test_a_correct_lef_passes(tmp_path):
    """Without this, every rejection below could be a check that rejects all."""
    check = exporters.check_lef(write_lef(tmp_path))

    assert check.ok, (
        "a CORE macro on CoreSite, 2.88 x 3.78 um, with VDD and VSS pins is "
        f"exactly what output_constr.md asks for: {check.problems}"
    )
    assert check.problems == ()
    assert check.cell_class == "CORE" and check.site == "CoreSite"
    assert {"VDD", "VSS"} <= set(check.pins), (
        f"the pins the macro declares must be reported: {check.pins}"
    )
    assert check.geometry.area_um2 == pytest.approx(10.8864), (
        "the check carries the footprint it measured, so a caller does not "
        f"have to parse the LEF twice: {check.geometry}"
    )


def test_class_block_is_rejected(tmp_path):
    """CLASS BLOCK makes OpenROAD treat the cell as a hard macro."""
    check = exporters.check_lef(write_lef(tmp_path, cell_class="BLOCK"))

    assert not check.ok
    assert any("CLASS" in p for p in check.problems), (
        f"the problem must name CLASS as the fault: {check.problems}"
    )
    assert any("CORE" in p for p in check.problems), (
        "the problem has to say what the value should be, not only that it is "
        f"wrong: {check.problems}"
    )


def test_a_missing_class_line_is_rejected(tmp_path):
    """No CLASS at all is not a default; it is a macro nothing can place."""
    check = exporters.check_lef(write_lef(tmp_path, cell_class=None))

    assert not check.ok and any("CLASS" in p for p in check.problems), (
        f"an absent CLASS is a failure, not a silent CORE: {check.problems}"
    )


def test_a_missing_site_is_rejected(tmp_path):
    """Without a SITE the legaliser has no grid to snap the cell to."""
    check = exporters.check_lef(write_lef(tmp_path, site=None))

    assert not check.ok and any("SITE" in p for p in check.problems), (
        f"an absent SITE must be reported: {check.problems}"
    )


def test_a_wrong_site_is_rejected(tmp_path):
    check = exporters.check_lef(write_lef(tmp_path, site="NotASite"))

    assert not check.ok and any("CoreSite" in p for p in check.problems), (
        f"the required site has to be named in the problem: {check.problems}"
    )


def test_a_wrong_row_height_is_rejected(tmp_path):
    """3.7 um is 80 nm short of the row: the cell cannot abut its neighbours."""
    check = exporters.check_lef(write_lef(tmp_path, height=3.7))

    assert not check.ok
    assert any("height" in p for p in check.problems), (
        f"the height must be named as the fault: {check.problems}"
    )


def test_an_off_site_width_is_rejected(tmp_path):
    """2.9 um is 6.04 sites: there is no legal column for the cell."""
    check = exporters.check_lef(write_lef(tmp_path, width=2.9))

    assert not check.ok
    assert any("width" in p for p in check.problems), (
        f"the width must be named as the fault: {check.problems}"
    )


def test_a_missing_power_pin_is_rejected(tmp_path):
    """With no PIN VSS the power grid has nothing to strap the cell onto."""
    check = exporters.check_lef(
        write_lef(tmp_path, pins=("I0", "I1", "I2", "O0", "VDD"))
    )

    assert not check.ok
    assert any("VSS" in p for p in check.problems), (
        f"the missing rail must be named: {check.problems}"
    )
    assert not any("VDD" in p for p in check.problems), (
        "VDD is present and must not be reported as missing; a check that "
        f"cannot tell them apart is not checking either: {check.problems}"
    )


def test_every_problem_is_reported_not_only_the_first(tmp_path):
    """Stopping at the first fault turns one review into four rounds of it."""
    check = exporters.check_lef(
        write_lef(
            tmp_path,
            cell_class="BLOCK",
            site=None,
            width=2.9,
            height=3.7,
            pins=("I0", "O0"),
        )
    )

    assert not check.ok
    joined = " | ".join(check.problems)
    for fault in ("CLASS", "SITE", "width", "height", "VDD", "VSS"):
        assert fault in joined, (
            f"this LEF breaks six requirements at once and {fault} is not "
            f"among the reported problems: {check.problems}"
        )
    assert len(check.problems) >= 6, (
        f"six independent faults must produce at least six problems, got "
        f"{len(check.problems)}: {check.problems}"
    )


def test_a_pin_no_via_can_reach_is_rejected(tmp_path):
    """The failure that survives placement and kills detailed routing.

    The router enters a Metal1 port through a via, and a via whose Metal2 pad
    cannot keep 0.21 um from another net's Metal2 cannot be placed.  With no
    position left, OpenROAD aborts the whole design with DRT-0073 an hour into
    step 7 -- so it is graded here.
    """
    check = exporters.check_lef(write_lef(tmp_path, obs=STRAP_OVER_FIRST_PIN))

    assert not check.ok, (
        f"no via reaches I0 past the strap across it; check_lef passed it: {check.problems}"
    )
    assert any("has no via access" in p for p in check.problems), check.problems
    assert any("DRT-0073" in p for p in check.problems), (
        "the rejection must name the error it prevents, or the reader has no "
        f"way to connect it to the failure they will otherwise see: {check.problems}"
    )


def test_a_pin_off_the_track_grid_is_not_rejected_for_that(tmp_path):
    """Covering no track is not a reason on its own.

    TritonRoute pin access reaches Metal1 ports that miss every y = n * 0.42 um
    line whenever the via has room to overlap them, so rejecting one would keep
    a routable cell out of place and route.
    """
    check = exporters.check_lef(write_lef(tmp_path, pin_rect=(0.200, 0.200, 0.360, 0.360)))

    assert check.ok, check.problems


def test_only_the_offending_pin_is_reported(tmp_path):
    """One problem per bad pin, so a redraw knows which port to move."""
    check = exporters.check_lef(
        write_lef(tmp_path, pins=("I0", "O0", "VDD", "VSS"), obs=STRAP_OVER_FIRST_PIN)
    )

    offenders = [p for p in check.problems if "has no via access" in p]
    assert len(offenders) == 1 and "PIN I0" in offenders[0], (
        f"only I0 is under the strap; O0 has room, VDD and VSS are exempt: {check.problems}"
    )


def test_a_power_pin_off_the_grid_is_not_a_problem(tmp_path):
    """VDD and VSS are strapped by the PDN, not routed to a track."""
    check = exporters.check_lef(
        write_lef(tmp_path, pins=("VDD", "VSS"), pin_rect=(0.2, 0.2, 0.36, 0.36))
    )

    assert check.ok, (
        f"only signal pins answer to the router's track grid: {check.problems}"
    )


# ---------------------------------------------------------------------------
# Via cuts: magic writes none, the router has to see them
# ---------------------------------------------------------------------------

_CUT_BODY = f"""\
MACRO {CELL}
  CLASS CORE ;
  SIZE 2.880 BY 3.780 ;
  PIN I0
    DIRECTION INPUT ;
    PORT
      LAYER Metal1 ;
        RECT 0.305 1.450 0.785 1.790 ;
      LAYER Metal2 ;
        RECT 0.570 0.400 0.770 1.745 ;
    END
  END I0
  PIN O0
    PORT
      LAYER Metal1 ;
        RECT 2.000 1.450 2.300 1.790 ;
    END
  END O0
  OBS
      LAYER Metal2 ;
        RECT 1.950 1.400 2.350 2.600 ;
  END
END {CELL}
END LIBRARY
"""

#: xnor2_1's I0 cut, under both of the pin's metals; and one under O0's Metal1
#: whose Metal2 is an obstruction.
_CUTS = {"Via1": [(0.575, 1.505, 0.765, 1.695), (2.055, 1.525, 2.245, 1.715)]}


def test_a_cut_under_both_of_a_pins_metals_goes_into_its_port():
    """AION_xnor2_1/I0: the cut TritonRoute could not see, and landed a Via1 beside."""
    body, notes = exporters._add_cut_layers(_CUT_BODY, CELL, _CUTS)

    i0 = re.search(r"PIN I0\n(.*?)END I0", body, re.S).group(1)
    assert "LAYER Via1 ;\n        RECT 0.575 1.505 0.765 1.695 ;\n    END" in i0, i0
    obs = re.search(r"  OBS\n(.*?)\n  END\n", body, re.S).group(1)
    assert "RECT 2.055 1.525 2.245 1.715" in obs, (
        f"O0's Metal2 is an obstruction, so its cut is too: {obs}"
    )
    assert "RECT 2.055" not in re.search(r"PIN O0\n(.*?)END O0", body, re.S).group(1)
    assert len(notes) == 1 and "2 Via1" in notes[0] and "1 in pin PORTs and 1 in OBS" in notes[0], notes


def test_a_macro_with_no_obs_gets_one_for_its_cuts():
    no_obs = re.sub(r"  OBS\n.*?\n  END\n", "", _CUT_BODY, flags=re.S)
    body, _ = exporters._add_cut_layers(no_obs, CELL, {"Via1": [_CUTS["Via1"][1]]})

    assert re.search(
        rf"  OBS\n      LAYER Via1 ;\n        RECT 2.055 1.525 2.245 1.715 ;\n  END\nEND {CELL}\n",
        body,
    ), body


def test_a_cell_with_no_cuts_is_left_exactly_as_magic_wrote_it():
    assert exporters._add_cut_layers(_CUT_BODY, CELL, {}) == (_CUT_BODY, ())


# ---------------------------------------------------------------------------
# Rail band: pin metal the router must not land on beside the PDN's via pads
# ---------------------------------------------------------------------------

#: AION_xnor2_4's I0 as published: a Metal2 U whose bar sits at the lowest y the
#: rail rule allows, with Metal1 pads on the risers and a Via1 up to each.  O0
#: reaches the top band, I1 stays clear of both; VSS carries Metal2 of its own
#: and the OBS a bar of another net, neither of which is a pin to land on.
_BAND_BODY = f"""\
MACRO {CELL}
  CLASS CORE ;
  SIZE 2.880 BY 3.780 ;
  PIN I0
    DIRECTION INPUT ;
    PORT
      LAYER Metal1 ;
        RECT 0.305 1.450 0.785 1.790 ;
      LAYER Metal2 ;
        RECT 0.570 0.555 0.770 1.745 ;
        RECT 2.115 0.555 2.315 1.745 ;
        RECT 0.570 0.355 2.315 0.555 ;
    END
  END I0
  PIN O0
    PORT
      LAYER Metal2 ;
        RECT 1.000 2.900 1.200 3.420 ;
    END
  END O0
  PIN I1
    PORT
      LAYER Metal2 ;
        RECT 1.300 1.000 1.500 2.000 ;
    END
  END I1
  PIN VSS
    USE GROUND ;
    PORT
      LAYER Metal1 ;
        RECT 0.000 -0.220 2.880 0.220 ;
      LAYER Metal2 ;
        RECT 2.500 0.400 2.700 0.600 ;
    END
  END VSS
  OBS
      LAYER Metal2 ;
        RECT 0.200 0.400 0.400 1.000 ;
  END
END {CELL}
END LIBRARY
"""


def _block(body, name):
    return re.search(rf"PIN {name}\n(.*?)END {name}", body, re.S).group(1)


def test_pin_metal2_in_the_rail_band_is_published_as_an_obstruction():
    """The split that took detailed routing from 23 stuck violations to 0.

    Under every power strap the PDN's rail via pads sit where the router landed
    on bars like I0's, at y = 0.42 um.  Only the part within 0.565 um of a rail
    line moves, the rest of the pin stays a pin, and the note says so.
    """
    body, notes = exporters._rail_band_to_obs(_BAND_BODY, CELL)

    i0 = _block(body, "I0")
    assert re.findall(r"RECT [\d. ]+", i0.split("LAYER Metal2 ;")[1]) == [
        "RECT 0.570 0.565 0.770 1.745 ",
        "RECT 2.115 0.565 2.315 1.745 ",
    ], f"the risers stay pin from y = 0.565 up, the bar leaves: {i0}"
    assert "RECT 0.305 1.450 0.785 1.790" in i0, "Metal1 is not in the band's rule"
    assert "RECT 1.000 2.900 1.200 3.215" in _block(body, "O0"), "the top band splits too"
    assert _block(body, "I1") == _block(_BAND_BODY, "I1"), "a pin clear of both bands is untouched"
    assert _block(body, "VSS") == _block(_BAND_BODY, "VSS"), "a supply is not a pin to land on"

    obs = re.search(r"  OBS\n(.*?)\n  END\n", body, re.S).group(1)
    for rect in ("0.200 0.400 0.400 1.000",               # the OBS it already had
                 "0.570 0.555 0.770 0.565", "2.115 0.555 2.315 0.565",
                 "0.570 0.355 2.315 0.555", "1.000 3.215 1.200 3.420"):
        assert f"RECT {rect} ;" in obs, f"{rect} missing from OBS: {obs}"
    assert len(notes) == 1 and "published 4 rect(s)" in notes[0] and "PIN I0, O0" in notes[0], notes


def test_a_layer_the_band_empties_is_dropped():
    """A LAYER line with no geometry under it is not something to hand a LEF reader."""
    bar_only = _BAND_BODY.replace(
        "        RECT 0.570 0.555 0.770 1.745 ;\n        RECT 2.115 0.555 2.315 1.745 ;\n", "")
    body, _ = exporters._rail_band_to_obs(bar_only, CELL)

    assert "LAYER Metal2" not in _block(body, "I0"), _block(body, "I0")
    assert "LAYER Metal1 ;\n        RECT 0.305 1.450 0.785 1.790 ;\n    END" in _block(body, "I0")


def test_a_cut_under_the_moved_metal_follows_it_into_obs():
    """Cuts are assigned after the split: a pin's port no longer covers one in the band."""
    body, _ = exporters._rail_band_to_obs(_BAND_BODY, CELL)
    cuts = {"Via1": [(0.575, 1.505, 0.765, 1.695), (1.000, 0.360, 1.190, 0.550)]}
    with_metal1 = body.replace(
        "        RECT 0.305 1.450 0.785 1.790 ;",
        "        RECT 0.305 1.450 0.785 1.790 ;\n        RECT 0.950 0.300 1.240 0.610 ;")
    body, _ = exporters._add_cut_layers(with_metal1, CELL, cuts)

    assert "RECT 0.575 1.505 0.765 1.695" in _block(body, "I0"), "the riser's cut is still the pin's"
    obs = re.search(r"  OBS\n(.*?)\n  END\n", body, re.S).group(1)
    assert "RECT 1.000 0.360 1.190 0.550" in obs, obs


def test_a_cell_clear_of_the_band_is_left_exactly_as_magic_wrote_it():
    clear = re.sub(r"  PIN I0\n.*?END I0\n  PIN O0\n.*?END O0\n", "", _BAND_BODY, flags=re.S)
    assert exporters._rail_band_to_obs(clear, CELL) == (clear, ())


def test_a_macro_with_no_obs_gets_one_for_the_band():
    no_obs = re.sub(r"  OBS\n.*?\n  END\n", "", _BAND_BODY, flags=re.S)
    body, _ = exporters._rail_band_to_obs(no_obs, CELL)

    assert re.search(
        rf"  OBS\n      LAYER Metal2 ;\n(        RECT [\d. ]+;\n){{4}}  END\nEND {CELL}\n", body
    ), body


# ---------------------------------------------------------------------------
# Liberty: one file, or one per corner, never both
# ---------------------------------------------------------------------------

_CORNER_TAGS = ("typ_1p20V_25C", "slow_1p08V_125C", "fast_1p32V_m40C")


def _libs(directory, names):
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        (directory / name).write_text(f"library ({name}) {{ }}\n")
    return [directory / name for name in names]


def test_the_corner_tags_are_the_ones_make_pnr_reads():
    """collect_cells.LIB_CORNERS in aion_chip spells the same three suffixes."""
    from aion_layout.characterize import DEFAULT_CORNERS
    assert tuple(corner.tag for corner in DEFAULT_CORNERS) == _CORNER_TAGS


def test_a_publish_per_corner_removes_the_single_liberty_an_earlier_one_left(tmp_path):
    """Beside a corner set, <cell>.lib is a second timing model `make pnr` refuses."""
    out = tmp_path / "final"
    _libs(out, [f"{CELL}.lib"])
    corner_libs = _libs(tmp_path / "char", [f"{CELL}_{tag}.lib" for tag in _CORNER_TAGS])

    exporters._publish_libs(corner_libs, CELL, out)

    assert sorted(p.name for p in out.glob("*.lib")) == sorted(
        f"{CELL}_{tag}.lib" for tag in _CORNER_TAGS)


def test_a_single_corner_publish_removes_the_corner_set_an_earlier_one_left(tmp_path):
    out = tmp_path / "final"
    _libs(out, [f"{CELL}_{tag}.lib" for tag in _CORNER_TAGS] + ["AION_other_slow_1p08V_125C.lib"])
    typ = _libs(tmp_path / "char", [f"{CELL}_typ_1p20V_25C.lib"])

    exporters._publish_libs(typ, CELL, out)

    assert sorted(p.name for p in out.glob("*.lib")) == sorted([
        "AION_other_slow_1p08V_125C.lib", f"{CELL}.lib"]), "another cell's files are not touched"


def test_make_export_publishes_the_directions_the_flow_does(tmp_path, monkeypatch):
    """A two-output cell's second output is an OUTPUT, not the netlist guess's INPUT.

    `make export` guessed directions from the transistors, and the guess knows
    one output: re-exported on its own, AION_xor2_5 came out with O1 declared an
    input in the LEF and missing from the Verilog model, while `flow` -- which
    reads the generator's port sidecar -- had published it as an output.
    """
    import argparse
    import json

    from aion_layout import cli

    gds = tmp_path / f"{CELL}.gds"
    gds.write_bytes(b"not read")
    (tmp_path / f"{CELL}.gds.ports.json").write_text(json.dumps([
        {"name": name, "layer": "Metal1", "direction": direction, "rect": [0, 0, 1, 1]}
        for name, direction in (("I0", "INPUT"), ("O0", "OUTPUT"), ("O1", "OUTPUT"),
                                ("VDD", "POWER"), ("VSS", "GROUND"))]))
    spice = tmp_path / f"{CELL}.spice"
    spice.write_text(f".subckt {CELL} I0 O0 O1 VDD VSS\n.ends\n")
    lib = tmp_path / f"{CELL}.lib"
    lib.write_text("library (x) { }\n")

    seen = {}

    def fake_export_all(**kwargs):
        seen.update(kwargs)
        raise SystemExit(0)

    monkeypatch.setattr(exporters, "export_all", fake_export_all)
    args = argparse.Namespace(cell=CELL, gds=str(gds), spice=str(spice), lib=[str(lib)],
                              pex_spice=None, out=str(tmp_path / "final"))
    with pytest.raises(SystemExit):
        cli.cmd_export(args)

    assert seen["directions"]["O1"] == "output", seen["directions"]
    assert seen["directions"]["O0"] == "output" and seen["directions"]["I0"] == "input"


def test_gds_cuts_reads_every_via_layer(gds_factory):
    """Via1 at 19/0 and Via2 at 29/0, per sg13g2.map; a duplicate is one cut."""
    gds = gds_factory(extra_layers={
        (19, 0): (0.575, 1.505, 0.765, 1.695),
        (29, 0): (1.000, 1.000, 1.190, 1.190),
    })
    cuts = exporters.gds_cuts(gds, "SYNTH")
    assert cuts == {
        "Via1": [(0.575, 1.505, 0.765, 1.695)],
        "Via2": [(1.0, 1.0, 1.19, 1.19)],
    }, cuts


def test_an_unmeasurable_lef_raises_rather_than_verdicts(tmp_path):
    """A macro with no SIZE has nothing to check; a verdict would invent one."""
    path = tmp_path / "nosize.lef"
    path.write_text(f"MACRO {CELL}\n  CLASS CORE ;\n  SITE CoreSite ;\nEND {CELL}\n")

    with pytest.raises(ExportError) as excinfo:
        exporters.check_lef(path)
    assert "measure" in str(excinfo.value), (
        f"the refusal must say the macro could not be measured: {excinfo.value}"
    )


def test_a_missing_lef_raises(tmp_path):
    """An absent LEF is a failed export, never a cell with no problems."""
    with pytest.raises(ExportError):
        exporters.check_lef(tmp_path / "never-written.lef")


def test_describe_states_the_verdict(tmp_path):
    line = exporters.check_lef(write_lef(tmp_path, cell_class="BLOCK")).describe()
    assert "CLASS" in line or "problem" in line.lower(), (
        f"a one-line summary of a failed check has to say it failed: {line!r}"
    )


# ---------------------------------------------------------------------------
# The Verilog model
#
# This view used to be a port list and an empty module.  That is not a smaller
# model, it is a *wrong* one: a netlist that instantiates it elaborates, links,
# runs, and drives z out of the cell for the whole simulation, which reaches
# the testbench as x on a design that is fine.  So the tests here are about the
# two things the file has to carry -- the function, and a specify path per arc
# for an SDF to annotate -- and about refusing to write it at all when either
# cannot be established.
# ---------------------------------------------------------------------------

PINS = ["I0", "I1", "I2", "O0", "VDD", "VSS"]

logic = optional_module("aion_layout.logic")


def model(netlist_path, tmp_path, *, name="cell.v", **kwargs):
    """The published model of the worked cell, as text."""
    return exporters.export_verilog_model(
        netlist_path, CELL, tmp_path / name, **kwargs
    ).read_text()


def liberty_stating(tmp_path, function, *, name="tiny.lib", cell=CELL):
    """A minimal Liberty whose only interesting claim is one function."""
    path = tmp_path / name
    path.write_text(
        "library (tiny) {\n"
        '  time_unit : "1ns";\n'
        "  capacitive_load_unit (1, pf);\n"
        f"  cell ({cell}) {{\n"
        "    pin (I0) { direction : input; }\n"
        "    pin (I1) { direction : input; }\n"
        "    pin (I2) { direction : input; }\n"
        "    pin (O0) {\n"
        "      direction : output;\n"
        f'      function : "{function}";\n'
        "    }\n"
        "  }\n"
        "}\n"
    )
    return path


def test_the_model_is_a_module_with_every_pin(netlist_path, tmp_path):
    """A model missing a port silently changes the netlist it stands in for."""
    text = model(netlist_path, tmp_path, pins=PINS)

    assert f"module {CELL} (" in text, f"the module header names the cell:\n{text}"
    assert text.rstrip().endswith("`endcelldefine"), (
        f"the module has to be closed, inside `celldefine as the PDK's own models "
        f"are:\n{text[-80:]}"
    )
    assert "endmodule" in text
    for pin in PINS:
        assert pin in text, f"port {pin} is missing from the model:\n{text}"


def test_the_module_body_is_not_empty(netlist_path, tmp_path):
    """The whole point: an empty module is a cell that drives z forever."""
    text = model(netlist_path, tmp_path, pins=PINS)
    body = text[text.index(");") : text.index("endmodule")]

    assert "assign O0 =" in body, (
        f"the model has to say what the cell computes:\n{body}"
    )
    assert body.strip(), "the module body is empty"


def test_the_model_is_marked_sta_blackbox(netlist_path, tmp_path):
    """Without the marker, OpenSTA aborts PnR instead of skipping the file.

    LibreLane hands every EXTRA_VERILOG_MODELS file to OpenSTA's Verilog
    reader, which takes structural netlists only -- it stops on the `assign`
    expression this exporter emits and takes the whole run down with it.  The
    marker makes it skip the file; the cell is still fully timed, because its
    arcs come from the Liberty read just before (EXTRA_LIBS).
    """
    text = model(netlist_path, tmp_path, pins=PINS)

    assert "/// sta-blackbox" in text, (
        f"the model must carry the '/// sta-blackbox' marker or STA fails the "
        f"run on the assign expression below it:\n{text}"
    )
    assert text.index("/// sta-blackbox") < text.index("module "), (
        f"the marker belongs in the header, above the module:\n{text}"
    )


def test_the_body_computes_what_the_netlist_computes(netlist_path, tmp_path):
    """Read the emitted expression back and grade it against the transistors."""
    text = model(netlist_path, tmp_path, pins=PINS)
    line = next(l for l in text.splitlines() if l.strip().startswith("assign O0"))
    expression = line.split("=", 1)[1].strip().rstrip(";")

    table = logic.truth_table(
        optional_module("aion_layout.spice_parser").parse_first_subckt(netlist_path)
    )
    assert table.disagrees_at(expression, "O0") is None, (
        f"the model computes {expression!r}, the netlist computes "
        f"{table.expression('O0')!r}"
    )


def test_a_specify_path_is_written_for_every_arc(netlist_path, tmp_path):
    """No specify path means no SDF IOPATH lands, and no delay, silently."""
    text = model(netlist_path, tmp_path, pins=PINS)

    assert "specify" in text and "endspecify" in text, (
        f"an SDF has nothing to attach to without a specify block:\n{text}"
    )
    for pin in ("I0", "I1", "I2"):
        assert f"({pin} => O0) = (0.0, 0.0);" in text, (
            f"the {pin}->O0 arc has no path for the SDF to annotate:\n{text}"
        )


def test_the_delays_in_the_specify_block_are_zero(netlist_path, tmp_path):
    """They are placeholders the SDF overwrites; a guess here would survive it."""
    text = model(netlist_path, tmp_path, pins=PINS)
    paths = [l.strip() for l in text.splitlines() if "=>" in l]

    assert paths, f"no module paths at all:\n{text}"
    assert all(p.endswith("= (0.0, 0.0);") for p in paths), (
        f"a non-zero delay in the model is a delay no SDF corner asked for: {paths}"
    )


def test_the_model_declares_a_timescale(netlist_path, tmp_path):
    """Next to files that declare one, a file that does not is a rescaled delay."""
    text = model(netlist_path, tmp_path, pins=PINS)
    assert "`timescale 1ns / 10ps" in text, (
        f"the PDK's own models declare 1ns / 10ps and the SDF is in ns:\n{text}"
    )


def test_supplies_sit_inside_ifdef_use_power_pins(netlist_path, tmp_path):
    """A power port outside the guard breaks every non-power simulation."""
    text = model(netlist_path, tmp_path, pins=PINS)
    lines = text.splitlines()

    assert "`ifdef USE_POWER_PINS" in lines, (
        f"the guard must be present when the cell has supplies:\n{text}"
    )
    open_at = lines.index("`ifdef USE_POWER_PINS")
    close_at = lines.index("`endif")
    guarded = "\n".join(lines[open_at + 1 : close_at])

    assert "VDD" in guarded and "VSS" in guarded, (
        f"both supplies belong inside the guard:\n{text}"
    )
    for signal in ("I0", "I1", "I2", "O0"):
        assert signal not in guarded, (
            f"{signal} is a signal port and must stay outside USE_POWER_PINS, "
            f"or it disappears from a simulation that does not define it:\n{text}"
        )


def test_the_port_list_never_ends_in_a_comma(netlist_path, tmp_path):
    """A trailing comma is a module that does not compile."""
    table = logic.truth_table(
        optional_module("aion_layout.spice_parser").parse_first_subckt(netlist_path)
    )
    for pins in (PINS, ["I0", "I1", "I2", "O0"]):
        text = exporters.verilog_model_text(CELL, table, pins=pins)
        declarations = [
            line.strip()
            for line in text.splitlines()
            if line.startswith("    ") and line.strip().split()[0] in
            ("input", "output", "inout")
        ]
        assert declarations, f"no port declarations were emitted for {pins}:\n{text}"
        assert not declarations[-1].endswith(","), (
            f"the last port declaration ends in a comma for pins {pins}, which "
            f"is the exact defect the reference makefile emits:\n{text}"
        )
        assert all(d.endswith(",") for d in declarations[:-1]), (
            f"every port but the last must be comma-separated:\n{text}"
        )


def test_the_directions_come_from_the_netlist(netlist_path, tmp_path):
    """A model with every port `inout` hides a direction error until synthesis."""
    text = model(netlist_path, tmp_path, pins=PINS)

    assert "output O0" in text, f"the driven pin is an output:\n{text}"
    for pin in ("I0", "I1", "I2"):
        assert f"input {pin}" in text, f"{pin} only gates devices:\n{text}"
    assert "inout VDD" in text, (
        f"a supply is always inout; a model cannot drive it:\n{text}"
    )


def test_a_direction_contradicting_the_netlist_is_refused(netlist_path, tmp_path):
    """The LEF and the model would then disagree about which way O0 goes."""
    with pytest.raises(ExportError) as excinfo:
        model(netlist_path, tmp_path, pins=PINS, directions={"O0": "input"})
    assert "O0" in str(excinfo.value), (
        f"the refusal must name the port it could not use: {excinfo.value}"
    )


def test_an_unusable_direction_is_refused(netlist_path, tmp_path):
    with pytest.raises(ExportError) as excinfo:
        model(netlist_path, tmp_path, pins=PINS, directions={"I0": "in"})
    assert "I0" in str(excinfo.value), (
        f"the refusal must name the port it could not use: {excinfo.value}"
    )


def test_a_pin_list_that_is_not_the_netlists_is_refused(netlist_path, tmp_path):
    """A model whose ports are not the cell's ports cannot be connected."""
    with pytest.raises(ExportError) as excinfo:
        model(netlist_path, tmp_path, pins=PINS + ["I3"])
    assert "I3" in str(excinfo.value), excinfo.value


def test_a_model_with_no_pins_is_refused(netlist_path, tmp_path):
    """A module with no ports is not a view of anything."""
    with pytest.raises(ExportError):
        model(netlist_path, tmp_path, pins=[])


def test_a_liberty_that_agrees_is_recorded_in_the_model(netlist_path, tmp_path):
    """What was checked is written down, so it is not taken on faith."""
    lib = liberty_stating(tmp_path, "I1*!I0*!I2")
    text = model(netlist_path, tmp_path, pins=PINS, lib_files=[lib])
    assert "function agrees" in text, (
        f"the header has to record the cross-check that ran:\n{text}"
    )


def test_a_liberty_that_disagrees_stops_the_publish(netlist_path, tmp_path):
    """Two views of the same cell, and no way to tell which one is right.

    The Liberty function is what static timing and the resizer believe; the
    netlist is what the layout was drawn and LVS'd against.  A Verilog model
    written from either one would be a simulation that disagrees with STA.
    """
    lib = liberty_stating(tmp_path, "I1*I0*!I2")  # I0 the wrong way round
    with pytest.raises(ExportError) as excinfo:
        model(netlist_path, tmp_path, pins=PINS, lib_files=[lib])
    message = str(excinfo.value)

    assert "O0" in message and "I1*I0*!I2" in message, (
        f"the refusal must quote the function it disagreed with: {message}"
    )
    assert "I0=" in message and "I1=" in message, (
        f"and name the vector where the two first differ: {message}"
    )
    assert not (tmp_path / "cell.v").exists(), (
        "a model must not be left behind by a publish that was refused"
    )


def test_a_liberty_naming_another_cells_pins_is_refused(netlist_path, tmp_path):
    """The loudest evidence there is that the two files are not the same cell."""
    lib = liberty_stating(tmp_path, "A*!B")
    with pytest.raises(ExportError) as excinfo:
        model(netlist_path, tmp_path, pins=PINS, lib_files=[lib])
    assert "A" in str(excinfo.value), excinfo.value


def test_a_liberty_that_cannot_be_read_stops_the_publish(netlist_path, tmp_path):
    """A cross-check that silently does not run is not a cross-check."""
    broken = tmp_path / "broken.lib"
    broken.write_text("library (tiny) {\n  cell (nothing) {\n")
    with pytest.raises(ExportError):
        model(netlist_path, tmp_path, pins=PINS, lib_files=[broken])


def test_a_cell_with_no_truth_table_is_refused(tmp_path):
    """A latch has no ``assign``, and inventing one is worse than refusing."""
    netlist = tmp_path / "latch.spice"
    netlist.write_text(
        """.subckt LATCH D GATE Q VDD VSS
XP0 qb Q VDD VDD sg13_lv_pmos w=1u l=0.13u
XN0 qb Q VSS VSS sg13_lv_nmos w=740n l=0.13u
XP1 Q qb VDD VDD sg13_lv_pmos w=1u l=0.13u
XN1 Q qb VSS VSS sg13_lv_nmos w=740n l=0.13u
XP2 Q GATE D VDD sg13_lv_pmos w=1u l=0.13u
XN2 Q GATE D VSS sg13_lv_nmos w=740n l=0.13u
.ends
"""
    )
    with pytest.raises(ExportError) as excinfo:
        exporters.export_verilog_model(netlist, "LATCH", tmp_path / "latch.v")
    assert "drives z" in str(excinfo.value), (
        f"the refusal has to say what publishing anyway would cost: {excinfo.value}"
    )
    assert not (tmp_path / "latch.v").exists()


def test_a_netlist_without_the_cell_is_refused(netlist_path, tmp_path):
    with pytest.raises(ExportError) as excinfo:
        exporters.export_verilog_model(netlist_path, "not_a_cell", tmp_path / "x.v")
    assert CELL in str(excinfo.value), (
        f"the refusal names what the netlist does define: {excinfo.value}"
    )


def test_a_publish_that_fails_late_leaves_nothing_discoverable(
    monkeypatch, tmp_path, netlist_path, known_gds
):
    """The Verilog model is written last, and it can still refuse.

    ``export_lef`` is the one step that needs the container, so it is replaced
    here by a LEF that passes every check -- the rest of ``export_all`` is the
    code under test.  What it must not do is leave a directory holding a GDS, a
    Liberty and a LEF and no Verilog model: discovery groups by stem, so that
    directory is a cell somebody places.
    """
    out = tmp_path / "final"
    out.mkdir()

    def fake_lef(gds, cell, path, **kwargs):
        Path(path).write_text(lef_text())
        return Path(path)

    monkeypatch.setattr(exporters, "export_lef", fake_lef)

    with pytest.raises(ExportError) as excinfo:
        exporters.export_all(
            cell=CELL,
            gds=known_gds,
            spice_netlist=netlist_path,
            lib_files=[liberty_stating(tmp_path, "I1*I0*!I2")],  # the wrong function
            out_dir=out,
        )
    assert "was not published" in str(excinfo.value), excinfo.value

    left = sorted(p.name for p in out.iterdir())
    assert not any(name.endswith((".gds", ".lef", ".lib", ".v")) for name in left), (
        f"a half-published cell was left behind: {left}"
    )
    assert any(name.endswith(".rejected") for name in left), (
        f"the evidence has to be kept, under a name discovery ignores: {left}"
    )


def test_a_clean_publish_clears_an_earlier_refusal(
    monkeypatch, tmp_path, netlist_path, known_gds
):
    """A ``.rejected`` file is a claim about the *last* publish of a cell.

    ``make pnr`` refuses to publish a cell whose export directory holds any --
    that is the whole point of the quarantine.  So one left behind by an
    earlier iteration bars the cell from the flow however many clean exports
    follow it, and the only way out is deleting the file by hand.  That is what
    happened to AION_nand2_o21ai_0: a refused LEF at 11:38 kept a cell that
    exported cleanly at 12:02 out of implementation/cells.
    """
    out = tmp_path / "final"
    out.mkdir()

    def fake_lef(gds, cell, path, **kwargs):
        Path(path).write_text(lef_text())
        return Path(path)

    monkeypatch.setattr(exporters, "export_lef", fake_lef)

    # what the earlier, failing iteration left behind
    (out / f"{CELL}.lef.rejected").write_text("the LEF that was refused\n")
    (out / f"{CELL}.gds.rejected").write_bytes(b"stale")

    views = exporters.export_all(
        cell=CELL,
        gds=known_gds,
        spice_netlist=netlist_path,
        lib_files=[liberty_stating(tmp_path, "!I0*I1*!I2")],  # what the netlist computes
        out_dir=out,
    )

    assert views.lef_check.ok, views.lef_check.problems
    left = sorted(p.name for p in out.iterdir())
    assert not any(name.endswith(".rejected") for name in left), (
        f"a publish that succeeded left an older refusal behind: {left}"
    )
    assert f"{CELL}.lef" in left and f"{CELL}.gds" in left, (
        f"and it still has to publish the views: {left}"
    )


# ---------------------------------------------------------------------------
# CDL
# ---------------------------------------------------------------------------

SPICE_WITH_NOISE = f"""\
* a netlist with the simulator-only cruft a CDL view must not carry
.include "/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib"
.lib "/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib" mos_tt
.param vdd=1.2
.subckt {CELL} I0 I1 I2 O0 VDD VSS
XP0 I1_bar I1 VDD VDD sg13_lv_pmos w=1.12u l=0.13u ng=1 m=1
XN0 I1_bar I1 VSS VSS sg13_lv_nmos w=740n l=0.13u ng=1 m=1
.ends
.control
run
write out.raw
.endc
.end
"""


def test_cdl_keeps_the_devices(tmp_path):
    """A CDL view is connectivity; losing a device loses the connectivity."""
    source = tmp_path / "in.spice"
    source.write_text(SPICE_WITH_NOISE)

    text = exporters.export_cdl(source, CELL, tmp_path / "out.cdl").read_text()

    assert "XP0" in text and "XN0" in text, (
        f"both devices must survive into the CDL view:\n{text}"
    )
    assert CELL in text, f"the subcircuit itself must survive:\n{text}"
    assert ".ENDS" in text.upper(), f"the subcircuit must be closed:\n{text}"


def test_cdl_drops_include_and_the_other_simulator_directives(tmp_path):
    """`.include` points at a model library; a CDL view has no simulator."""
    source = tmp_path / "in.spice"
    source.write_text(SPICE_WITH_NOISE)

    text = exporters.export_cdl(source, CELL, tmp_path / "out.cdl").read_text()
    # Compare the first TOKEN of each card, not a substring: '.end' is a prefix
    # of '.ends', and a substring test here would reject a correct CDL view.
    cards = [
        line.strip().split()[0].lower()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("*")
    ]

    for directive in (".include", ".lib", ".param", ".control", ".endc", ".end"):
        assert directive not in cards, (
            f"{directive} is simulator-only and must not reach the CDL view:\n{text}"
        )
    assert cards == [".subckt", "xp0", "xn0", ".ends"], (
        "a CDL view is the subcircuit and its devices and nothing else: "
        f"{cards}"
    )


def test_cdl_refuses_a_netlist_that_does_not_define_the_cell(tmp_path):
    """Publishing a view of a cell the netlist lacks publishes a different cell."""
    source = tmp_path / "in.spice"
    source.write_text(".subckt SOMETHING_ELSE A Y\n.ends\n")

    with pytest.raises(ExportError) as excinfo:
        exporters.export_cdl(source, CELL, tmp_path / "out.cdl")

    assert CELL in str(excinfo.value) and "SOMETHING_ELSE" in str(excinfo.value), (
        "the refusal must name both what was asked for and what the file "
        f"actually defines: {excinfo.value}"
    )


def test_cdl_refuses_an_unterminated_control_block(tmp_path):
    """An unclosed .control means everything after it is of unknown status."""
    source = tmp_path / "in.spice"
    source.write_text(f".subckt {CELL} A Y\n.ends\n.control\nrun\n")

    with pytest.raises(ExportError) as excinfo:
        exporters.export_cdl(source, CELL, tmp_path / "out.cdl")
    assert "control" in str(excinfo.value), (
        f"the refusal must name the unterminated block: {excinfo.value}"
    )


def test_cdl_and_gds_copies_refuse_a_missing_source(tmp_path):
    """A view that cannot be produced must not be reported as produced."""
    with pytest.raises(ExportError):
        exporters.export_cdl(tmp_path / "nope.spice", CELL, tmp_path / "out.cdl")
    with pytest.raises(ExportError):
        exporters.export_gds(tmp_path / "nope.gds", tmp_path / "out.gds")


def test_pins_from_spice_reads_the_declared_pins(netlist_path):
    """The stub's port list comes from the netlist, never from a guess."""
    assert exporters.pins_from_spice(netlist_path, CELL) == [
        "I0", "I1", "I2", "O0", "VDD", "VSS",
    ], "the pin list and its order are the cell's interface"


def test_pins_from_spice_refuses_a_netlist_that_lacks_the_cell(tmp_path, netlist_path):
    """A pin list is an interface; taking it from whatever subckt is there is fatal.

    ``pins_from_spice`` feeds the Verilog stub and the LEF pin check.  If it
    answered with the ports of some other subcircuit the netlist happens to
    define, both views would be internally consistent and describe a cell that
    does not exist.
    """
    with pytest.raises(ExportError) as excinfo:
        exporters.pins_from_spice(netlist_path, "AION_not_this_cell")

    message = str(excinfo.value)
    assert "AION_not_this_cell" in message, (
        f"the refusal must name the cell that was asked for: {message}"
    )
    assert "AION_inv_nand2_nor2" in message, (
        "and what the file actually defines, so the caller can see it pointed "
        f"at the wrong netlist rather than the wrong cell: {message}"
    )


def test_pins_from_pex_refuses_a_netlist_that_lacks_the_cell(tmp_path):
    """The same rule for the extracted netlist, which is where PEX lands."""
    pex = tmp_path / "pex.spice"
    pex.write_text(".subckt SOMETHING_ELSE A B\n.ends\n")

    with pytest.raises(ExportError) as excinfo:
        exporters.pins_from_pex(pex, CELL)

    assert CELL in str(excinfo.value) and "SOMETHING_ELSE" in str(excinfo.value), (
        "the refusal must name both the cell asked for and the one the file "
        f"holds; a PEX run for another cell is a silently wrong pin list: "
        f"{excinfo.value}"
    )


def test_pins_from_pex_follows_continuation_lines(tmp_path):
    """PEX wraps its pin list; a parser that reads one line loses pins."""
    pex = tmp_path / "pex.spice"
    pex.write_text(
        f".subckt {CELL}_pex I0 I1\n"
        "+ I2 O0\n"
        "+ VDD VSS\n"
        "C1 I0 VSS 1f\n"
        ".ends\n"
    )

    assert exporters.pins_from_pex(pex, CELL) == [
        "I0", "I1", "I2", "O0", "VDD", "VSS",
    ], (
        "every pin on a '+' continuation must be read; a stub built from the "
        "first line alone has a plausible and incomplete port list"
    )
