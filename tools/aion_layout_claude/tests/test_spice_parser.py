# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The netlist is the specification
# ================================================================

"""The netlist is what LVS grades the layout against, so misreading it is fatal.

Two mistakes matter more than the rest.  A **unit** mistake -- ``740n`` read as
740 um, or ``0.13u`` as 0.13 nm -- draws a transistor a thousand times the wrong
size and every downstream rule check then argues about the wrong shape.  A
**port** mistake -- an internal node treated as a pin -- produces a cell with a
terminal the schematic does not have, which is the single most expensive way to
fail LVS: the layout looks finished and is wrong at its interface.

Ground truth is ``AION_inv_nand2_nor2_1_minimized.spice``, the worked example
this whole tool exists to lay out: 8 transistors, 4 n and 4 p, six ports, three
internal nets.
"""

from __future__ import annotations

import pytest

from aion_layout.spice_parser import (
    SpiceParseError,
    parse_first_subckt,
    parse_spice,
    parse_spice_file,
)
from conftest import CELL

PORTS = ["I0", "I1", "I2", "O0", "VDD", "VSS"]
INTERNAL = {"I1_bar", "net_p_0", "net_p_1"}


@pytest.fixture(scope="module")
def subckt(request):
    path = request.config.rootpath / f"{CELL}_minimized.spice"
    assert path.is_file(), f"the worked netlist is missing: {path}"
    return parse_first_subckt(path)


def test_the_worked_netlist_has_eight_transistors(subckt):
    """Eight devices is what Netgen counted on both sides of the captured LVS."""
    assert subckt.name == CELL, (
        f"the subcircuit name is the cell name LVS compares under: {subckt.name}"
    )
    assert len(subckt.devices) == 8, (
        "the AION cell is 8 transistors; parsing fewer means a device would be "
        f"missing from the layout and LVS would fail on a count: "
        f"{[d.name for d in subckt.devices]}"
    )


def test_the_split_is_four_nmos_and_four_pmos(subckt):
    """The n/p split decides the two diffusion rows; getting it wrong is a redraw."""
    assert len(subckt.nmos_devices) == 4, (
        f"4 NMOS sit in the lower row: {[d.name for d in subckt.nmos_devices]}"
    )
    assert len(subckt.pmos_devices) == 4, (
        f"4 PMOS sit in the upper row: {[d.name for d in subckt.pmos_devices]}"
    )
    assert not (
        set(subckt.nmos_devices) & set(subckt.pmos_devices)
    ), "no device may be counted in both rows"


def test_ports_are_exactly_the_six_the_subckt_declares(subckt):
    """A pin the schematic does not have is the most expensive LVS failure."""
    assert subckt.pins == PORTS, (
        "the port list is the cell's interface and its order is the order LVS "
        f"and the LEF use: expected {PORTS}, got {subckt.pins}"
    )


def test_internal_nets_are_not_ports(subckt):
    """I1_bar and the two series nodes are internal; exposing them breaks LVS."""
    assert INTERNAL <= subckt.nets, (
        "the three internal nets must be seen on the devices at all, or the "
        f"series stack has been misread: {sorted(subckt.nets)}"
    )
    leaked = INTERNAL & set(subckt.pins)
    assert not leaked, (
        f"{sorted(leaked)} are internal nodes of the minimized cell; a layout "
        "that gives them a pin has a terminal the schematic does not, and "
        "Netgen fails it at pin matching"
    )


def test_rails_and_output_are_recognised(subckt):
    """The rails place the power rows and the output names the driven pin."""
    assert subckt.vdd_net == "VDD" and subckt.vss_net == "VSS", (
        "the rails must be found by name; without them the power rails cannot "
        f"be drawn: {subckt.vdd_net}/{subckt.vss_net}"
    )
    assert subckt.output_net == "O0", (
        "O0 is the only external pin driven by both a PMOS and an NMOS drain, "
        f"which is what makes it the output: {subckt.output_net}"
    )
    assert subckt.input_nets == ["I0", "I1", "I2"], (
        f"the inputs are everything that is neither a rail nor the output: "
        f"{subckt.input_nets}"
    )


def test_widths_and_lengths_are_nanometres(subckt):
    """`740n` is 740 nm and `1.12u` is 1120 nm; the framework draws in nm."""
    by_name = {d.name: d for d in subckt.devices}

    assert by_name["XN0"].width_nm == pytest.approx(740.0), (
        "w=740n is 740 nanometres; any other number means the metric suffix "
        f"was dropped or applied twice: {by_name['XN0'].width_nm}"
    )
    assert by_name["XP0"].width_nm == pytest.approx(1120.0), (
        f"w=1.12u is 1120 nanometres: {by_name['XP0'].width_nm}"
    )
    for device in subckt.devices:
        assert device.length_nm == pytest.approx(130.0), (
            f"every device in this cell is l=0.13u, i.e. 130 nm; {device.name} "
            f"came back as {device.length_nm}"
        )
        assert device.fingers == 1 and device.multiplier == 1, (
            f"ng and m are both 1 throughout this netlist; {device.name} says "
            f"ng={device.fingers} m={device.multiplier}"
        )


def test_the_series_pmos_stack_is_read_in_order(subckt):
    """The p-stack is what makes this cell one cell instead of three."""
    by_name = {d.name: d for d in subckt.devices}

    assert (by_name["XP1"].drain, by_name["XP1"].source) == ("net_p_0", "VDD")
    assert (by_name["XP2"].drain, by_name["XP2"].source) == ("net_p_1", "net_p_0"), (
        "XP2 sits between XP1 and XP3 in the series chain; reading its "
        "source/drain the wrong way round breaks the stack the layout abuts"
    )
    assert (by_name["XP3"].drain, by_name["XP3"].source) == ("O0", "net_p_1")


def test_bulk_terminals_are_kept(subckt):
    """The bulk decides which well a device sits in; dropping it drops the well."""
    for device in subckt.devices:
        expected = "VDD" if device.is_pmos else "VSS"
        assert device.bulk == expected, (
            f"{device.name} is a {'PMOS' if device.is_pmos else 'NMOS'} and "
            f"must be bulk-tied to {expected}, not {device.bulk!r}"
        )


def test_devices_on_net_finds_every_terminal(subckt):
    """Routing asks which devices touch a net; a partial answer is a missed wire."""
    on_output = {d.name for d in subckt.devices_on_net("O0")}

    assert on_output == {"XP3", "XN1", "XN2", "XN3"}, (
        "four devices drive O0 in this cell; a router told about fewer leaves "
        f"a terminal unconnected: {sorted(on_output)}"
    )


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


def test_a_file_with_no_subckt_is_an_error(tmp_path):
    """An empty netlist is a failed input, not a cell with no transistors."""
    path = tmp_path / "empty.spice"
    path.write_text("* just a comment\n")

    assert parse_spice_file(path) == [], (
        "a file with no .subckt yields no subcircuits"
    )
    with pytest.raises(SpiceParseError) as excinfo:
        parse_first_subckt(path)
    assert "No subcircuit" in str(excinfo.value), (
        f"the error must say what was missing: {excinfo.value}"
    )


def test_an_unclosed_subckt_is_an_error():
    """A truncated netlist must raise, not return the half of it that parsed."""
    with pytest.raises(SpiceParseError) as excinfo:
        parse_spice(
            f".subckt {CELL} I0 O0 VDD VSS\n"
            "XN0 O0 I0 VSS VSS sg13_lv_nmos w=740n l=0.13u\n"
        )
    assert "Unclosed" in str(excinfo.value), (
        f"the error must name the truncation: {excinfo.value}"
    )


def test_a_device_with_the_wrong_node_count_is_an_error():
    """A MOSFET has four terminals; five is a different device, not a MOSFET."""
    with pytest.raises(SpiceParseError) as excinfo:
        parse_spice(
            ".subckt X A Y VDD VSS\n"
            "XN0 Y A B VSS VSS sg13_lv_nmos w=740n l=0.13u\n"
            ".ends\n"
        )
    assert "4 nodes" in str(excinfo.value), (
        "the refusal has to say how many terminals were expected, so the "
        f"caller can see it handed over a subcircuit instance: {excinfo.value}"
    )


def test_an_unparseable_width_is_an_error():
    """A width that is not a number must raise rather than default to zero."""
    with pytest.raises(SpiceParseError) as excinfo:
        parse_spice(
            ".subckt X A Y VDD VSS\n"
            "XN0 Y A VSS VSS sg13_lv_nmos w=wide l=0.13u\n"
            ".ends\n"
        )
    assert "XN0" in str(excinfo.value), (
        f"the error must name the instance that could not be read: {excinfo.value}"
    )
