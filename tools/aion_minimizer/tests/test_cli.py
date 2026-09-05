"""The command-line entry point, driven the way the Makefile drives it."""

from __future__ import annotations

import pytest

from aion_minimizer.cli import main
from netlists import CORPUS


@pytest.fixture
def netlist(tmp_path):
    def write(name: str) -> str:
        path = tmp_path / f"{name}.spice"
        path.write_text(CORPUS[name][0])
        return str(path)

    return write


def test_run_writes_a_netlist_and_verifies(netlist, gate_library_path, tmp_path, capsys):
    out = tmp_path / "out" / "cell.spice"
    assert main(
        [
            "run",
            netlist("and3"),
            "--gates",
            str(gate_library_path),
            "--verify",
            "-o",
            str(out),
        ]
    ) == 0
    assert out.exists()
    assert "Equivalence: PASS" in capsys.readouterr().out


def test_unknown_cell_reports_why_it_was_skipped(
    tmp_path, gate_library_path, capsys
):
    top = tmp_path / "t.spice"
    top.write_text(
        ".subckt T I0 I1 O0 VDD VSS\n"
        "Xg0 O0 I0 I1 CLK VDD VSS sg13g2_dfrbp_1\n"
        ".ends\n"
    )
    with pytest.raises(SystemExit) as exc:
        main(["run", str(top), "--gates", str(gate_library_path), "-o", str(tmp_path / "o")])
    assert exc.value.code == 1
    assert "Cannot identify a unique output" in capsys.readouterr().err


def test_top_name_selects_among_several_subckts(
    tmp_path, gate_library_path, capsys
):
    top = tmp_path / "t.spice"
    top.write_text(CORPUS["and3"][0] .replace(".subckt T ", ".subckt A ")
                   + CORPUS["or3"][0].replace(".subckt T ", ".subckt B "))
    out = tmp_path / "o.spice"
    args = ["run", str(top), "--gates", str(gate_library_path), "-o", str(out)]

    with pytest.raises(SystemExit):
        main(args)
    assert "name one with --top" in capsys.readouterr().err

    assert main(args + ["--top-name", "B", "--verify"]) == 0
    assert out.read_text().startswith(".subckt B ")


def test_too_many_inputs_is_refused(tmp_path, gate_library_path, capsys):
    top = tmp_path / "t.spice"
    top.write_text(CORPUS["nand_chain"][0])
    with pytest.raises(SystemExit):
        main(
            [
                "run",
                str(top),
                "--gates",
                str(gate_library_path),
                "--max-inputs",
                "3",
                "-o",
                str(tmp_path / "o"),
            ]
        )
    assert "Too many primary inputs" in capsys.readouterr().err
