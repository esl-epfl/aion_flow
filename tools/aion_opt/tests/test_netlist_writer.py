"""The structural Verilog writer: names that are not plain identifiers."""

from __future__ import annotations

import shutil
import subprocess

import pytest

from aion_opt.graph.circuit import Circuit, Instance, Net, TopPort
from aion_opt.io.netlist_writer import _instance_id, write_verilog


@pytest.mark.parametrize("name, expected", [
    ("_123_", "_123_"),
    ("u_icg", "u_icg"),
    # A cell instantiated in RTL keeps its flattened hierarchical name.
    ("u_top.core_clock_gate_i.u_icg", "\\u_top.core_clock_gate_i.u_icg "),
    ("$abc$42$auto_1", "\\$abc$42$auto_1 "),
    ("rf_reg[3]", "\\rf_reg[3] "),
])
def test_instance_id(name, expected):
    assert _instance_id(name) == expected


def test_hierarchical_instance_name_is_escaped(tmp_path):
    circuit = Circuit(
        name="top",
        ports=[TopPort("a", "input", [2]), TopPort("y", "output", [3])],
        instances={"u_sub.u_inv": Instance(
            name="u_sub.u_inv", cell_type="sg13g2_inv_1",
            connections={"A": [2], "Y": [3]})},
        nets={"a": Net("a", [2]), "y": Net("y", [3])},
    )
    out = tmp_path / "top.v"
    write_verilog(circuit, out)
    text = out.read_text()
    assert "sg13g2_inv_1 \\u_sub.u_inv  (" in text

    if shutil.which("yosys") is None:
        return
    stub = tmp_path / "cells.v"
    stub.write_text("(* blackbox *) module sg13g2_inv_1(input A, output Y); endmodule\n")
    result = subprocess.run(
        ["yosys", "-q", "-p", f"read_verilog {stub} {out}; hierarchy -top top; "
                              "select -assert-count 1 top/u_sub.u_inv"],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr + result.stdout
