"""End-to-end: mine, generate, rank and rewrite a small netlist.

These tests shell out to the real CLI (and therefore to Yosys) so they cover
the parts a unit test cannot: the Verilog front end, the cell-library file
format, the selection cache and the rewritten netlist.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL_ROOT = REPO_ROOT / "tools" / "aion_opt"
NETLIST = REPO_ROOT / "examples" / "aion_opt" / "test_single_pattern_netlist.v"
TOP = "test_single_pattern_netlist"
CELL_LIB = REPO_ROOT / "tech" / "tech_dict" / "sg13g2_stdcell.json"

pytestmark = [
    pytest.mark.skipif(shutil.which("yosys") is None, reason="yosys not on PATH"),
    pytest.mark.skipif(not NETLIST.exists(), reason="example netlist not present"),
]


def run_cli(*argv: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, "-m", "aion_opt", *argv],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": str(TOOL_ROOT), "PATH": __import__("os").environ["PATH"]},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"{argv}\n{result.stdout}\n{result.stderr}"
    return result


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    """Run generate-cells once for the whole module."""
    out = tmp_path_factory.mktemp("aion_opt_e2e")
    run_cli(
        "generate-cells",
        "--input", str(NETLIST),
        "--cell-lib", str(CELL_LIB),
        "--top", TOP,
        "--work-dir", str(out / "work"),
        "--max-size", "3",
        "--min-occurrences", "3",
        "--min-selected", "1",
        "--max-outputs", "1",
        "--output-cells", str(out / "cells.v"),
        "--output-elite-cells", str(out / "cells_elite.v"),
        "--elite-count", "1",
        "--output-report", str(out / "report.json"),
        "--quiet",
    )
    return out


def test_single_output_pattern_is_found_exactly_three_times(generated):
    """The fixture netlist holds 3 single-output and 2 multi-output copies."""
    report = json.loads((generated / "report.json").read_text())
    full = [
        p
        for p in report["patterns_found"]
        if p["size"] == 3
        and {"sg13g2_inv", "sg13g2_nand2", "sg13g2_nor2"}
        == set(p["node_types"].values())
    ]
    assert len(full) == 1
    assert full[0]["occurrences"] == 3


def test_cells_carry_canonical_keys_and_the_default_prefix(generated):
    text = (generated / "cells.v").read_text()
    keys = re.findall(r"// AION canonical_key: (.+)", text)
    modules = re.findall(r"^module\s+(\w+)", text, re.M)
    assert keys and len(keys) == len(modules)
    assert all(m.startswith("AION_") for m in modules)


def test_elite_library_is_a_subset_ranked_first(generated):
    full = re.findall(r"^module\s+(\w+)", (generated / "cells.v").read_text(), re.M)
    elite = re.findall(
        r"^module\s+(\w+)", (generated / "cells_elite.v").read_text(), re.M
    )
    assert len(elite) == 1
    assert set(elite) <= set(full)
    # Module ids follow the saved-area ranking, so the elite cell is _0.
    assert elite[0].endswith("_0")


def test_rewrite_reduces_the_cell_count_and_reuses_the_cache(generated):
    result = run_cli(
        "rewrite",
        "--input", str(NETLIST),
        "--cell-lib", str(CELL_LIB),
        "--top", TOP,
        "--work-dir", str(generated / "work"),
        "--max-size", "3",
        "--min-occurrences", "3",
        "--min-selected", "1",
        "--max-outputs", "1",
        "--cells", str(generated / "cells.v"),
        "--output-netlist", str(generated / "rewritten.v"),
        "--output-flat-netlist", str(generated / "flat.v"),
        "--output-report", str(generated / "rewrite_report"),
    )
    assert "Reusing selection cache" in result.stdout

    report = json.loads((generated / "rewrite_report.json").read_text())
    assert report["summary"]["cell_reduction"] > 0
    assert report["summary"]["estimated_area_savings"] > 0

    rewritten = (generated / "rewritten.v").read_text()
    assert "AION_" in rewritten
    # The flat netlist must contain no AION module instantiation at all.
    flat = (generated / "flat.v").read_text()
    assert not re.search(r"^\s*AION_\w+\s+\w+\s*\(", flat, re.M)


def test_rewriting_with_the_elite_library_only_uses_elite_cells(generated):
    run_cli(
        "rewrite",
        "--input", str(NETLIST),
        "--cell-lib", str(CELL_LIB),
        "--top", TOP,
        "--work-dir", str(generated / "work"),
        "--max-size", "3",
        "--min-occurrences", "3",
        "--min-selected", "1",
        "--max-outputs", "1",
        "--cells", str(generated / "cells_elite.v"),
        "--output-netlist", str(generated / "rewritten_elite.v"),
        "--output-report", str(generated / "rewrite_report_elite"),
    )
    elite_modules = set(
        re.findall(r"^module\s+(\w+)", (generated / "cells_elite.v").read_text(), re.M)
    )
    used = set(
        re.findall(
            r"^\s+(AION_\w+)\s+\w+\s*\(",
            (generated / "rewritten_elite.v").read_text(),
            re.M,
        )
    )
    assert used
    assert used <= elite_modules


def test_cell_prefix_is_not_hard_coded(tmp_path):
    run_cli(
        "generate-cells",
        "--input", str(NETLIST),
        "--cell-lib", str(CELL_LIB),
        "--top", TOP,
        "--work-dir", str(tmp_path / "work"),
        "--max-size", "3",
        "--min-occurrences", "3",
        "--min-selected", "1",
        "--max-outputs", "1",
        "--cell-prefix", "MYLIB_",
        "--output-cells", str(tmp_path / "cells.v"),
        "--output-report", str(tmp_path / "report.json"),
        "--quiet",
    )
    run_cli(
        "rewrite",
        "--input", str(NETLIST),
        "--cell-lib", str(CELL_LIB),
        "--top", TOP,
        "--work-dir", str(tmp_path / "work"),
        "--max-size", "3",
        "--min-occurrences", "3",
        "--min-selected", "1",
        "--max-outputs", "1",
        "--cell-prefix", "MYLIB_",
        "--cells", str(tmp_path / "cells.v"),
        "--output-netlist", str(tmp_path / "rewritten.v"),
        "--output-report", str(tmp_path / "rewrite_report"),
        "--quiet",
    )
    cells = (tmp_path / "cells.v").read_text()
    rewritten = (tmp_path / "rewritten.v").read_text()
    assert re.search(r"^module\s+MYLIB_", cells, re.M)
    assert "AION_" not in re.sub(r"// AION canonical_key.*", "", cells)
    assert "MYLIB_" in rewritten
    assert not re.search(r"\bAION_\w+\s+\w+\s*\(", rewritten)


def test_jobs_setting_does_not_change_the_result(tmp_path):
    reports = []
    for jobs in ("1", "4"):
        out = tmp_path / f"j{jobs}"
        run_cli(
            "generate-cells",
            "--input", str(NETLIST),
            "--cell-lib", str(CELL_LIB),
            "--top", TOP,
            "--work-dir", str(out / "work"),
            "--max-size", "3",
            "--min-occurrences", "2",
            "--jobs", jobs,
            "--output-cells", str(out / "cells.v"),
            "--output-report", str(out / "report.json"),
            "--quiet",
        )
        data = json.loads((out / "report.json").read_text())
        reports.append(
            sorted(
                (p["pattern_key"], p["occurrences"]) for p in data["patterns_found"]
            )
        )
    assert reports[0] == reports[1]
