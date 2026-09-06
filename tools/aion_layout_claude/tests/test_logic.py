# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-06
#  Description:               The function is solved, so it can be graded
# ================================================================

"""What the netlist computes, graded against cells whose answer is published.

A truth table derived from transistors is only worth having if it is right, and
"right" here has an external referee: ``context/spice`` holds the PDK's own
schematic netlist for every SG13G2 standard cell, and the PDK's Liberty states
the ``function`` of each one.  So every assertion about a PDK cell below is the
IHP library's own sentence about that cell, quoted, and the solver has to
reproduce it from the transistors alone -- through an inverter, a NAND, a NOR,
an AOI, a pass-gate MUX and an XOR, which is every topology this flow's cells
are built out of.

The cells the solver must *refuse* are graded the same way.  A latch has no
truth table, a tri-state buffer has none either, and both of those netlists are
committed here too.  Getting an answer out of them would mean the solver had
invented one.
"""

from __future__ import annotations

import pytest

from conftest import optional_module

logic = optional_module("aion_layout.logic")
spice_parser = optional_module("aion_layout.spice_parser")

LogicError = logic.LogicError


def pdk_subckt(tool_dir, name: str):
    """The PDK's own schematic netlist for one standard cell."""
    path = tool_dir / "context" / "spice" / f"{name}.spice"
    assert path.is_file(), f"the committed PDK netlist for {name} is missing: {path}"
    for subckt in spice_parser.parse_spice_file(path):
        if subckt.name == name:
            return subckt
    raise AssertionError(f"{path} defines no .subckt {name}")


# ---------------------------------------------------------------------------
# Against the PDK's own published functions
# ---------------------------------------------------------------------------

#: cell -> (output pin, the `function` attribute of
#: sg13g2_stdcell_typ_1p20V_25C.lib, quoted verbatim).
PDK_FUNCTIONS = {
    "sg13g2_inv_1": ("Y", "!(A)"),
    "sg13g2_buf_1": ("X", "A"),
    "sg13g2_nand2_1": ("Y", "!(A*B)"),
    "sg13g2_nor2_1": ("Y", "!(A+B)"),
    "sg13g2_nand2b_1": ("Y", "!(!A_N*B)"),
    "sg13g2_and3_1": ("X", "(A*B*C)"),
    "sg13g2_a21oi_1": ("Y", "!((A1*A2)+B1)"),
    "sg13g2_o21ai_1": ("Y", "!((A1+A2)*B1)"),
    "sg13g2_a221oi_1": ("Y", "!((A1*A2)+(B1*B2)+C1)"),
    "sg13g2_xor2_1": ("X", "(A^B)"),
    "sg13g2_xnor2_1": ("Y", "!(A^B)"),
    # The two that no series/parallel reduction of the pull-down network can
    # reach: the MUXes pass their data through transmission gates.
    "sg13g2_mux2_1": ("X", "(!S*A0)+(S*A1)"),
    "sg13g2_mux4_1": (
        "X",
        "(A0*(!S0*!S1))+(A1*(S0*!S1))+(A2*(!S0*S1))+(A3*(S0*S1))",
    ),
}


@pytest.mark.parametrize("cell", sorted(PDK_FUNCTIONS))
def test_the_solver_reproduces_the_pdk_function(tool_dir, cell):
    """Every one of these is IHP's own sentence about the cell, from its .lib."""
    output, published = PDK_FUNCTIONS[cell]
    table = logic.truth_table(pdk_subckt(tool_dir, cell))

    assert output in table.outputs, (
        f"{cell} drives {table.outputs}, and the PDK gives the function of {output}"
    )
    disagrees_at = table.disagrees_at(published, output)
    assert disagrees_at is None, (
        f"{cell}: the PDK says {output} = {published!r}, the transistors solve to "
        f"{table.expression(output, style='liberty')!r}; they first differ at "
        + " ".join(f"{p}={v}" for p, v in table.vector(disagrees_at).items())
    )


def test_the_worked_cell_is_the_function_its_liberty_states(netlist_path):
    """The AION cell is three merged gates, and the merge must not change it."""
    subckt = spice_parser.parse_first_subckt(netlist_path)
    table = logic.truth_table(subckt)

    assert table.inputs == ("I0", "I1", "I2") and table.outputs == ("O0",), (
        f"the worked cell has three inputs and one output, not {table.inputs} / "
        f"{table.outputs}"
    )
    # aion_char measured this with ngspice and wrote it into every .lib the
    # flow published for this cell.
    assert table.disagrees_at("I1*!I0*!I2", "O0") is None, (
        f"the netlist solves to {table.expression('O0', style='liberty')!r}, and the "
        "characterizer measured I1*!I0*!I2"
    )
    assert table.column("O0") == (0, 0, 1, 0, 0, 0, 0, 0), (
        f"only I0=0 I1=1 I2=0 may drive O0 high: {table.column('O0')}"
    )


def test_an_internal_node_is_solved_before_the_stage_that_reads_it(netlist_path):
    """A merged cell has a gate whose input is another gate's drain.

    The pull-up of the second stage is gated by ``I1_bar``, which no input
    vector gives a value to directly.  A solver that only looked at the output
    pin would find it undriven and stop.
    """
    subckt = spice_parser.parse_first_subckt(netlist_path)
    assert "I1_bar" in {d.gate for d in subckt.devices}, (
        "this test is anchored to the worked netlist's internal inverter node"
    )
    assert logic.truth_table(subckt).column("O0") == (0, 0, 1, 0, 0, 0, 0, 0)


# ---------------------------------------------------------------------------
# The cells that have no truth table
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cell, because",
    [
        ("sg13g2_dlhq_1", "feedback"),
        ("sg13g2_dfrbpq_1", "feedback"),
        ("sg13g2_einvn_2", "high impedance"),
    ],
)
def test_a_cell_with_no_truth_table_is_refused(tool_dir, cell, because):
    """A latch, a flop and a tri-state inverter: no vector settles them all.

    An ``x`` returned here would become an ``assign`` in a Verilog model that a
    place-and-route flow then simulates as if it were the cell.
    """
    with pytest.raises(LogicError) as excinfo:
        logic.truth_table(pdk_subckt(tool_dir, cell))
    assert "settle at no level" in str(excinfo.value), (
        f"the refusal has to say what went wrong ({because}): {excinfo.value}"
    )


def test_a_fill_cell_is_refused_for_having_no_output(tool_dir):
    with pytest.raises(LogicError) as excinfo:
        logic.truth_table(pdk_subckt(tool_dir, "sg13g2_fill_1"))
    assert "no output" in str(excinfo.value), excinfo.value


def test_a_device_that_is_neither_nmos_nor_pmos_is_refused():
    """Dropping a device silently would change the function and say nothing."""
    text = """
.subckt weird Y A VDD VSS
XP0 Y A VDD VDD sg13_lv_pmos w=1u l=0.13u
XN0 Y A VSS VSS sg13_lv_nmos w=740n l=0.13u
XR0 Y A VSS VSS some_resistor w=740n l=0.13u
.ends
"""
    subckt = spice_parser.parse_spice(text)[0]
    with pytest.raises(LogicError) as excinfo:
        logic.truth_table(subckt)
    assert "XR0" in str(excinfo.value) and "some_resistor" in str(excinfo.value), (
        f"the refusal must name the device it could not switch: {excinfo.value}"
    )


def test_a_node_tied_to_both_rails_is_refused():
    """A fight settles at a ratio, and a ratio is not a logic level."""
    text = """
.subckt fight Y A VDD VSS
XP0 Y A VDD VDD sg13_lv_pmos w=1u l=0.13u
XN0 Y A VSS VSS sg13_lv_nmos w=740n l=0.13u
XP1 Y VSS VDD VDD sg13_lv_pmos w=1u l=0.13u
XN1 Y VDD VSS VSS sg13_lv_nmos w=740n l=0.13u
.ends
"""
    subckt = spice_parser.parse_spice(text)[0]
    with pytest.raises(LogicError) as excinfo:
        logic.truth_table(subckt)
    assert "both" in str(excinfo.value), excinfo.value


def test_a_netlist_with_no_supplies_is_refused():
    text = """
.subckt floating Y A B
XP0 Y A B B sg13_lv_pmos w=1u l=0.13u
.ends
"""
    subckt = spice_parser.parse_spice(text)[0]
    with pytest.raises(LogicError) as excinfo:
        logic.truth_table(subckt)
    assert "VDD" in str(excinfo.value) and "VSS" in str(excinfo.value), excinfo.value


# ---------------------------------------------------------------------------
# Arcs and unateness
# ---------------------------------------------------------------------------


def test_the_support_is_the_arc_list(netlist_path):
    """An input the output ignores has no arc, and must get no specify path."""
    table = logic.truth_table(spice_parser.parse_first_subckt(netlist_path))
    assert table.support("O0") == ("I0", "I1", "I2")


def test_the_senses_match_the_characterized_liberty(netlist_path):
    """aion_char wrote these three timing_sense values into the published .lib."""
    table = logic.truth_table(spice_parser.parse_first_subckt(netlist_path))
    assert [table.sense("O0", pin) for pin in ("I0", "I1", "I2")] == [
        "negative_unate",
        "positive_unate",
        "negative_unate",
    ]


def test_an_input_nothing_depends_on_is_not_in_the_support():
    """A device gated by a pin it cannot influence the output through."""
    text = """
.subckt half_used Y A B VDD VSS
XP0 Y A VDD VDD sg13_lv_pmos w=1u l=0.13u
XN0 Y A VSS VSS sg13_lv_nmos w=740n l=0.13u
XP1 dead B VDD VDD sg13_lv_pmos w=1u l=0.13u
XN1 dead B VSS VSS sg13_lv_nmos w=740n l=0.13u
.ends
"""
    table = logic.truth_table(spice_parser.parse_spice(text)[0])
    assert table.support("Y") == ("A",), (
        f"B cannot reach Y, so it is not an arc: {table.support('Y')}"
    )
    assert "B" not in table.expression("Y")


def test_a_non_unate_arc_is_named_as_one(tool_dir):
    table = logic.truth_table(pdk_subckt(tool_dir, "sg13g2_xor2_1"))
    assert table.sense("X", "A") == "non_unate"


# ---------------------------------------------------------------------------
# Minimisation and rendering
# ---------------------------------------------------------------------------


def test_the_expression_is_checked_against_the_table_it_came_from(tool_dir):
    """Every emitted expression is re-evaluated; this is that check, from outside."""
    for cell, (output, _) in PDK_FUNCTIONS.items():
        table = logic.truth_table(pdk_subckt(tool_dir, cell))
        rendered = table.expression(output)
        assert table.disagrees_at(rendered, output) is None, (
            f"{cell}: the expression this module emitted, {rendered!r}, does not "
            "compute its own truth table"
        )


@pytest.mark.parametrize(
    "cell, output, spelling",
    [
        ("sg13g2_nor2_1", "Y", "~(A | B)"),
        ("sg13g2_nand2_1", "Y", "~(A & B)"),
        ("sg13g2_a21oi_1", "Y", "~((A1 & A2) | B1)"),
    ],
)
def test_an_inverting_cell_spells_as_the_complement_it_is(tool_dir, cell, output, spelling):
    """``~(A | B)``, not the equally short ``~A & ~B`` nobody reads as a NOR.

    Both are two literals, so the tie is broken on negation signs -- which is
    what makes the emitted expression line up with the PDK's own Liberty for
    the same cell.
    """
    table = logic.truth_table(pdk_subckt(tool_dir, cell))
    assert table.expression(output) == spelling, table.expression(output)


def test_an_and_keeps_the_plain_form(tool_dir):
    table = logic.truth_table(pdk_subckt(tool_dir, "sg13g2_and3_1"))
    assert table.expression("X") == "A & B & C", table.expression("X")


def test_a_constant_output_renders_as_a_constant():
    values = (0, 0, 0, 0)
    assert logic.render(*logic.minimal_cover(values, ("A", "B"))) == "1'b0"
    assert logic.render(*logic.minimal_cover((1, 1, 1, 1), ("A", "B"))) == "1'b1"


def test_the_two_styles_spell_the_same_function(netlist_path):
    table = logic.truth_table(spice_parser.parse_first_subckt(netlist_path))
    for style in ("verilog", "liberty"):
        assert table.disagrees_at(table.expression("O0", style=style), "O0") is None


def test_an_unknown_style_is_refused(netlist_path):
    table = logic.truth_table(spice_parser.parse_first_subckt(netlist_path))
    with pytest.raises(LogicError):
        table.expression("O0", style="vhdl")


# ---------------------------------------------------------------------------
# Reading the other tool's expression
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("A*B", [0, 0, 0, 1]),
        ("A B", [0, 0, 0, 1]),  # juxtaposition is AND in Liberty
        ("A&B", [0, 0, 0, 1]),
        ("A+B", [0, 1, 1, 1]),
        ("A|B", [0, 1, 1, 1]),
        ("A^B", [0, 1, 1, 0]),
        ("!A*B", [0, 1, 0, 0]),
        ("A'*B", [0, 1, 0, 0]),  # the postfix negation Liberty also allows
        ("~A & B", [0, 1, 0, 0]),  # and the Verilog spelling of the same
        ("!(A+B)", [1, 0, 0, 0]),
        ("A*B+!A*!B", [1, 0, 0, 1]),
        ("A+B*A", [0, 0, 1, 1]),  # AND binds tighter than OR
        ("!A", [1, 1, 0, 0]),
        ("1", [1, 1, 1, 1]),
        ("0", [0, 0, 0, 0]),
    ],
)
def test_parse_boolean_reads_liberty_and_verilog_alike(expression, expected):
    function = logic.parse_boolean(expression, known=("A", "B"))
    got = [function({"A": a, "B": b}) for a in (0, 1) for b in (0, 1)]
    assert got == expected, f"{expression!r} evaluated to {got}, expected {expected}"


def test_an_expression_naming_a_pin_the_cell_does_not_have_is_refused():
    """The loudest evidence there is that two files describe different cells."""
    with pytest.raises(LogicError) as excinfo:
        logic.parse_boolean("A*C", known=("A", "B"))
    assert "C" in str(excinfo.value), excinfo.value


@pytest.mark.parametrize("expression", ["A*", "(A+B", "A B)", "", "*A"])
def test_an_unreadable_expression_is_refused(expression):
    with pytest.raises(LogicError):
        logic.parse_boolean(expression, known=("A", "B"))
