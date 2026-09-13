# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-10
#  Description:               The stimulus reaches aion_char, and both sides
#                             of a comparison get the same one
# ================================================================

"""What a Liberty file means depends on how it was measured.

``aion_char``'s default stimulus is an ideal linear ramp -- a zero-impedance
driver.  That is a fair idealisation for a cell whose inputs are transistor
gates, and it is not one for a transmission-gate cell: a pass gate's input is a
source/drain, so the driver stays in series with the channel for the whole
transition and the ramp flatters the cell by exactly the effect NLDM has no
axis for.  ``--driver-cell`` replaces it with a real cell.

Two things have to hold, and neither is visible in the ``.lib`` afterwards,
which is why they are pinned here rather than left to a run nobody re-reads:

* the flag has to *arrive* -- it crosses four layers (``pdk_cell.py`` ->
  ``aion-layout-flow`` -> this tool's Makefile -> ``aion_char``), and a
  pass-through that silently drops it produces a plausible library measured the
  wrong way;
* the driver's ``.subckt`` has to come with it.  A PEX netlist defines the
  extracted cell and nothing else, so without ``--driver-spice`` pointing at the
  PDK's own transistor views ``aion_char`` refuses with "no '.subckt
  sg13g2_buf_2' in the SPICE files given".

The command is graded as a string because that is the whole of the contract
this module has with ``aion_char``; nothing here runs a tool.
"""

from __future__ import annotations

import pytest

from aion_layout import characterize as ch


@pytest.fixture()
def spice(tmp_path):
    """A netlist with the one ``.subckt`` :func:`characterize` insists on."""
    path = tmp_path / "AION_mux4i_1.spice"
    path.write_text(
        ".subckt AION_mux4i_1 I0 I4 O0 VDD VSS\n"
        "XN0 O0 I0 VSS VSS sg13_lv_nmos w=740.00n l=130.00n\n"
        "XP0 O0 I0 VDD VDD sg13_lv_pmos w=1.12u l=130.00n\n"
        ".ends\n"
    )
    return path


@pytest.fixture()
def captured(monkeypatch, tmp_path):
    """Run :func:`characterize` without a container; keep the command."""
    seen: list = []

    def fake_run(command, timeout=None):
        seen.append(command)
        # characterize checks its outputs afterwards, so they have to exist.
        for corner in ch.DEFAULT_CORNERS[:1]:
            (tmp_path / "out" / f"AION_mux4i_1_{corner.tag}.lib").write_text(
                "library (x) { cell (AION_mux4i_1) { area : 1.0; } }\n"
            )
        return type("R", (), {"ok": True, "status": 0, "timed_out": False,
                              "tail": staticmethod(lambda n=0: "")})()

    monkeypatch.setattr(ch, "run_in_container", fake_run)
    (tmp_path / "out").mkdir()
    return seen


def _characterize(spice, tmp_path, **kwargs):
    return ch.characterize(
        spice,
        "AION_mux4i_1",
        tmp_path / "out",
        inputs=["I0", "I4"],
        outputs=["O0"],
        area_um2=29.0304,
        corners=ch.DEFAULT_CORNERS[:1],
        **kwargs,
    )


def test_no_driver_leaves_the_ideal_ramp(captured, spice, tmp_path):
    """The default is unchanged: no --driver-* anywhere in the command."""
    result = _characterize(spice, tmp_path)
    assert "--driver" not in captured[0]
    assert result.driver is None
    assert "ideal ramp" in result.describe()


def test_driver_reaches_aion_char(captured, spice, tmp_path):
    """All three flags arrive, spelled as aion_char's parser wants them."""
    driver = ch.Driver("sg13g2_buf_2", "A", "X")
    result = _characterize(spice, tmp_path, driver=driver)
    command = captured[0]

    assert "--driver-cell sg13g2_buf_2" in command
    assert "--driver-input A" in command
    assert "--driver-output X" in command
    # Recorded, because the .lib does not say which stimulus produced it.
    assert result.driver == driver
    assert "sg13g2_buf_2 (A -> X)" in result.describe()


def test_driver_brings_its_own_subckt(captured, spice, tmp_path):
    """--driver-spice names the PDK netlist, unquoted so the container expands it.

    A PEX netlist defines only the extracted cell.  Without this the run dies
    inside the container, after PEX has already been paid for.
    """
    _characterize(spice, tmp_path, driver=ch.Driver("sg13g2_buf_2", "A", "X"))
    command = captured[0]

    assert "--driver-spice" in command
    assert "$PDK_ROOT/$PDK/libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice" in command
    # The same contract --model-lib has: shell-expandable, and its own quotes.
    assert "--driver-spice \"$PDK_ROOT" in command


@pytest.mark.parametrize(
    "cell,in_pin,out_pin,named",
    [
        ("", "A", "X", "cell"),
        ("sg13g2_buf_2", "", "Y", "in_pin"),
        ("sg13g2_buf_2", "A", "", "out_pin"),
        ("sg13g2_buf_2", "A", "   ", "out_pin"),
    ],
)
def test_half_a_driver_is_refused_here(cell, in_pin, out_pin, named):
    """Refused on the host, not four hours into a container run.

    A SPICE ``.subckt`` does not say which of its pins is the input, so there
    is nothing to infer and no safe default to fall back on.
    """
    with pytest.raises(ch.CharacterizeError) as exc:
        ch.Driver(cell, in_pin, out_pin)
    assert named in str(exc.value)


def test_flow_gives_both_sides_the_same_stimulus():
    """The comparison is only meaningful if the candidate and the baseline agree.

    ``cmd_flow`` resolves the driver once and passes that one object to both
    ``characterize`` calls.  Grading it by reading the source is crude, but the
    alternative -- a real flow run -- needs Docker and a PDK, and the failure
    this guards against is someone adding a third call site that forgets.
    """
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "aion_layout" / "cli.py").read_text()
    flow = source[source.index("def cmd_flow"):]
    flow = flow[: flow.index("\ndef ")]

    assert flow.count("driver=driver") == 2, (
        "cmd_flow characterizes the candidate and the baseline; both must be "
        "given the same driver, or the delay comparison is measured with two "
        "different stimuli"
    )
    assert flow.count("_resolve_driver(") == 1, (
        "resolve the driver once; two resolutions can disagree"
    )


# ---------------------------------------------------------------------------
# Extraction mode, and the guard that made it necessary
# ---------------------------------------------------------------------------


def test_orphaned_port_is_refused(tmp_path):
    """A `.subckt` port nothing references is a floating net, not a netlist.

    This is Magic's ``extresist`` splitting a rail into renamed segments
    (``VSS`` -> ``VSS.t0``, ``VSS.n1``) and binding the port to none of them.
    LVS passes -- it extracts without resistance, where the net is whole -- so
    without this check the first symptom is a Liberty file measuring a circuit
    whose pull-downs are all floating: function ``O0 = 1``, no arcs, and a
    comparison that fails an hour later blaming the wrong thing.
    """
    netlist = tmp_path / "c_pex3.spice"
    netlist.write_text(
        ".subckt c I0 O0 VDD VSS\n"
        "XN0 O0 I0 VSS.t0 VSS.t0 sg13_lv_nmos w=740.00n l=130.00n\n"
        "XP0 O0 I0 VDD VDD sg13_lv_pmos w=1.12u l=130.00n\n"
        "R0 VSS.t0 VSS.n1 1.85\n"
        ".ends\n"
    )
    with pytest.raises(ch.CharacterizeError) as exc:
        ch._require_ports_connected(netlist, netlist.read_text(), "c")
    message = str(exc.value)
    assert "VSS" in message
    assert "--pex-mode 2" in message, "the error must name the way out"
    assert "extresist threshold" in message, "and the trap it must not take"


def test_a_bound_port_is_accepted(tmp_path):
    """The same netlist with the one binding Magic usually emits."""
    netlist = tmp_path / "c_pex3.spice"
    netlist.write_text(
        ".subckt c I0 O0 VDD VSS\n"
        "XN0 O0 I0 VSS.t0 VSS.t0 sg13_lv_nmos w=740.00n l=130.00n\n"
        "XP0 O0 I0 VDD VDD sg13_lv_pmos w=1.12u l=130.00n\n"
        "R0 VSS.t0 VSS 1.85\n"
        ".ends\n"
    )
    ch._require_ports_connected(netlist, netlist.read_text(), "c")


def test_segment_names_do_not_satisfy_the_port(tmp_path):
    """`VSS.t0` must not count as a reference to `VSS`.

    A substring match would accept exactly the netlists this guard exists to
    reject, and would do it silently.
    """
    netlist = tmp_path / "c_pex3.spice"
    netlist.write_text(
        ".subckt c VSS\nR0 VSS.t0 VSS.t1 1.0\n.ends\n"
    )
    with pytest.raises(ch.CharacterizeError):
        ch._require_ports_connected(netlist, netlist.read_text(), "c")


def test_flow_extracts_both_sides_the_same_way():
    """One --pex-mode for the candidate and the baseline.

    Same reason the driver is resolved once: two netlists extracted differently
    are not two measurements of the same thing, and the comparison in step 7
    subtracts one from the other.
    """
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "aion_layout" / "cli.py").read_text()
    flow = source[source.index("def cmd_flow"):]
    flow = flow[: flow.index("\ndef ")]
    assert flow.count("mode=args.pex_mode") == 2, (
        "cmd_flow extracts the candidate and the baseline; both must use the "
        "same PEX mode"
    )
