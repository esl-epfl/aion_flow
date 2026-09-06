"""End-to-end: decide, generate, rewrite and formally check a complement.

These shell out to the real CLI and to Yosys, because the point of the feature
is a contract between three files — the cell library, the transistor netlist
and the rewritten design — that only the whole pipeline exercises.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL_ROOT = REPO_ROOT / "tools" / "aion_opt"
MIN_ROOT = REPO_ROOT / "tools" / "aion_minimizer"
GATES = REPO_ROOT / "tech" / "spice" / "sg13g2_stdcell.spice"
CELL_LIB = REPO_ROOT / "tech" / "tech_dict" / "sg13g2_stdcell.json"
LIBERTY = REPO_ROOT / "tech" / "lib" / "sg13g2_stdcell_typ_1p20V_25C.lib"
MODELS = [
    REPO_ROOT / "tech" / "rtl" / "sg13g2_udp_eqy.v",
    REPO_ROOT / "tech" / "rtl" / "sg13g2_stdcell_eqy.v",
]

pytestmark = [
    pytest.mark.skipif(shutil.which("yosys") is None, reason="yosys not on PATH"),
    pytest.mark.skipif(not GATES.exists(), reason="PDK SPICE not present"),
    pytest.mark.skipif(not LIBERTY.exists(), reason="liberty not present"),
    pytest.mark.skipif(
        not all(m.exists() for m in MODELS), reason="PDK Verilog models not present"
    ),
]

# Purely combinational so the equivalence check needs no flop model.
RTL = """
module tiny (input [7:0] a, input [7:0] b, input [2:0] s,
             output [7:0] y, output [7:0] z);
  wire [7:0] m = s[0] ? a : b;
  wire [7:0] n = s[1] ? (a ^ b) : (a & b);
  assign y = s[2] ? m : n;
  assign z = (a + b) ^ {m[6:0], n[7]};
endmodule
"""


def _run(module: str, *argv: str, roots: list[Path]) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, "-m", module, *argv],
        cwd=REPO_ROOT,
        env={
            "PYTHONPATH": os.pathsep.join(str(r) for r in roots),
            "PATH": os.environ["PATH"],
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"{argv}\n{result.stdout}\n{result.stderr}"
    return result


def _yosys(script: str) -> bool:
    """True when Yosys proves the miter; False when the proof fails."""
    result = subprocess.run(
        ["yosys", "-q", "-p", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


@pytest.fixture(scope="module")
def flow(tmp_path_factory):
    """Run the whole complement flow once."""
    out = tmp_path_factory.mktemp("complement_flow")
    (out / "tiny.v").write_text(RTL)
    netlist = out / "tiny.nl.v"
    assert _yosys(
        f"read_verilog {out / 'tiny.v'}; synth -top tiny; "
        f"dfflibmap -liberty {LIBERTY}; abc -liberty {LIBERTY}; opt_clean; "
        f"write_verilog -noattr {netlist}"
    )

    common = [
        "--input", str(netlist), "--top", "tiny", "--cell-lib", str(CELL_LIB),
        "--max-size", "3", "--min-occurrences", "2", "--max-outputs", "1",
        "--work-dir", str(out / "work"), "--quiet",
    ]
    opt = [TOOL_ROOT]
    _run("aion_opt", "generate-cells", *common,
         "--output-cells", str(out / "cells.v"),
         "--output-report", str(out / "report.json"), roots=opt)
    _run("aion_opt", "cells-to-spice", "--cells", str(out / "cells.v"),
         "--gates", str(GATES), "--output-dir", str(out / "spice"), "--quiet", roots=opt)

    reports = out / "reports"
    reports.mkdir()
    for cell in sorted((out / "spice").glob("*.spice")):
        _run("aion_minimizer", "run", str(cell), "--gates", str(GATES), "--verify",
             "--report", str(reports / f"{cell.stem}.json"),
             "-o", str(out / "min" / f"{cell.stem}.spice"),
             "--max-inputs", "12", "--max-cluster-inputs", "12", roots=[MIN_ROOT])

    _run("aion_opt", "complement-plan", *common,
         "--cells", str(out / "cells.v"), "--interfaces", str(reports),
         "--output-plan", str(out / "plan.json"), roots=opt)
    _run("aion_opt", "generate-cells", *common,
         "--complement-plan", str(out / "plan.json"),
         "--output-cells", str(out / "cells_ext.v"),
         "--output-report", str(out / "report2.json"), roots=opt)
    _run("aion_opt", "rewrite", *common, "--cells", str(out / "cells_ext.v"),
         "--output-netlist", str(out / "tiny_opt.v"),
         "--output-report", str(out / "rw"), roots=opt)
    return out


def _equiv_script(out: Path, gate_netlist: Path) -> str:
    models = " ".join(str(m) for m in MODELS)
    return "; ".join([
        f"read_verilog {models}",
        f"read_verilog {out / 'tiny.nl.v'}",
        "prep -top tiny -flatten",
        "design -stash gold",
        f"read_verilog {models}",
        f"read_verilog {out / 'cells_ext.v'} {gate_netlist}",
        "prep -top tiny -flatten",
        "design -stash gate",
        "design -copy-from gold -as gold tiny",
        "design -copy-from gate -as gate tiny",
        "miter -equiv -flatten -make_assert gold gate miter",
        "hierarchy -top miter",
        "sat -verify -prove-asserts miter",
    ])


def test_some_input_is_externalized(flow):
    plan = json.loads((flow / "plan.json").read_text())
    assert plan["version"] == 1
    external = {m: e["external"] for m, e in plan["modules"].items() if e["external"]}
    assert external, "the fixture design should externalize at least one input"


def test_the_plan_is_backed_by_numbers(flow):
    plan = json.loads((flow / "plan.json").read_text())
    for entry in plan["modules"].values():
        for port, stat in entry["stats"].items():
            assert stat["occurrences"] > 0
            assert stat["internal_devices"] == 2 * stat["occurrences"]
            assert stat["external_devices"] == 2 * stat["new_inverters"]
            assert stat["recommended"] == (port in entry["external"])


def test_the_library_declares_the_extra_port_and_uses_it(flow):
    text = (flow / "cells_ext.v").read_text()
    assert "// AION complement_inputs:" in text
    plan = json.loads((flow / "plan.json").read_text())
    for module, entry in plan["modules"].items():
        for port in entry["external"]:
            assert f"input {port}_bar;" in text
            # The body must read the complement, not the plain port, so that a
            # mis-driven `_bar` cannot pass an equivalence check.
            assert f"assign {port}_int = ~{port}_bar;" in text


def test_every_instance_of_such_a_cell_drives_the_extra_port(flow):
    plan = json.loads((flow / "plan.json").read_text())
    netlist = (flow / "tiny_opt.v").read_text()
    for module, entry in plan["modules"].items():
        if not entry["external"]:
            continue
        instances = netlist.count(f"{module} ")
        for port in entry["external"]:
            assert netlist.count(f".{port}_bar(") == instances


def test_the_rewritten_netlist_is_equivalent(flow):
    assert _yosys(_equiv_script(flow, flow / "tiny_opt.v"))


def test_a_mis_driven_complement_is_caught(flow):
    """The check has to be sensitive, or the whole scheme proves nothing.

    Tying `<port>_bar` to the port itself is exactly the mistake the flow could
    make, so the equivalence check must reject it.
    """
    text = (flow / "tiny_opt.v").read_text()
    plan = json.loads((flow / "plan.json").read_text())
    port = next(p for e in plan["modules"].values() for p in e["external"])

    lines = text.splitlines()
    for index, line in enumerate(lines):
        if f".{port}_bar(" in line:
            source = next(
                l for l in lines[max(0, index - 8):index] if f".{port}(" in l
            )
            net = source.split("(", 1)[1].rsplit(")", 1)[0]
            lines[index] = f"    .{port}_bar({net}),"
            break
    else:  # pragma: no cover - the fixture always externalizes something
        pytest.fail(f"no .{port}_bar connection found")

    broken = flow / "tiny_broken.v"
    broken.write_text("\n".join(lines) + "\n")
    assert not _yosys(_equiv_script(flow, broken))
