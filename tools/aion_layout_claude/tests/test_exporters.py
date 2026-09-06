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
):
    """A LEF macro with one knob per requirement, so each can be broken alone."""
    lines = ["VERSION 5.7 ;", "BUSBITCHARS \"[]\" ;", "", f"MACRO {cell}"]
    if cell_class is not None:
        lines.append(f"  CLASS {cell_class} ;")
    lines.append("  ORIGIN 0 0 ;")
    lines.append(f"  FOREIGN {cell} 0 0 ;")
    lines.append(f"  SIZE {width} BY {height} ;")
    if site is not None:
        lines.append(f"  SITE {site} ;")
    for pin in pins:
        direction = "INOUT" if pin in ("VDD", "VSS") else "INPUT"
        use = "POWER" if pin == "VDD" else "GROUND" if pin == "VSS" else "SIGNAL"
        lines += [
            f"  PIN {pin}",
            f"    DIRECTION {direction} ;",
            f"    USE {use} ;",
            "    PORT",
            "      LAYER Metal1 ;",
            "        RECT 0.200 0.200 0.360 0.360 ;",
            "    END",
            f"  END {pin}",
        ]
    lines += [f"END {cell}", "", "END LIBRARY"]
    return "\n".join(lines) + "\n"


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
