"""The cell-library file format, including the complement marker."""

from __future__ import annotations

from aion_opt.io.cell_file import (
    CellModule,
    read_complement_ports,
    split_modules,
    write_library,
)

LIBRARY = """// header
// AION canonical_key: KEY0
module AION_a_0 ( I0, I1, O0);
endmodule

// AION canonical_key: KEY1
// AION complement_inputs: I1 I3
module AION_b_1 ( I0, I1, I2, I3, O0, I1_bar, I3_bar);
endmodule
"""


def test_both_markers_are_read():
    modules = {m.name: m for m in split_modules(LIBRARY)}
    assert modules["AION_a_0"].canonical_key == "KEY0"
    assert modules["AION_a_0"].complement_inputs == ()
    assert modules["AION_b_1"].canonical_key == "KEY1"
    assert modules["AION_b_1"].complement_inputs == ("I1", "I3")


def test_complement_ports_are_reported_per_module(tmp_path):
    path = tmp_path / "cells.v"
    path.write_text(LIBRARY)
    assert read_complement_ports(path) == {"AION_b_1": ["I1", "I3"]}


def test_a_marker_does_not_leak_to_the_next_module():
    text = LIBRARY + "\nmodule AION_c_2 ( I0, O0);\nendmodule\n"
    modules = {m.name: m for m in split_modules(text)}
    assert modules["AION_c_2"].complement_inputs == ()
    assert modules["AION_c_2"].canonical_key is None


def test_markers_survive_a_filtered_rewrite(tmp_path):
    """An elite library is a slice of the full one, markers included."""
    modules = split_modules(LIBRARY)
    out = tmp_path / "elite.v"
    write_library(out, [m for m in modules if m.name == "AION_b_1"])
    assert read_complement_ports(out) == {"AION_b_1": ["I1", "I3"]}
    assert split_modules(out.read_text())[0].canonical_key == "KEY1"


def test_render_emits_both_markers():
    rendered = CellModule(
        name="m", text="module m ();\nendmodule\n",
        canonical_key="K", complement_inputs=("I0",),
    ).render()
    assert rendered.startswith("// AION canonical_key: K\n// AION complement_inputs: I0\n")
