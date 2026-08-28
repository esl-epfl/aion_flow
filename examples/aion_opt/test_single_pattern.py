#!/usr/bin/env python3
"""Validate single-output pattern extraction on a fake netlist.

The fake netlist (test_single_pattern_netlist.v) contains:
  - 3 single-output instances of the pattern inv -> nand2 -> nor2
  - 2 multi-output variants where an internal node (inv or nand2 output)
    and the nor2 output both leave the pattern

Running aion_opt generate-cells with --max-outputs 1 and --min-occurrences 3
must extract exactly the 3 single-output occurrences of the full 3-cell
pattern and no multi-output occurrence.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NETLIST = REPO_ROOT / "examples" / "aion_opt" / "test_single_pattern_netlist.v"
CELL_LIB = REPO_ROOT / "tech" / "tech_dict" / "sg13g2_stdcell.json"
AION_OPT = [sys.executable, "-m", "aion_opt"]

EXPECTED_SINGLE_OUTPUT = 3


def run_generate_cells(output_report: Path) -> None:
    cmd = [
        *AION_OPT,
        "generate-cells",
        "--input",
        str(NETLIST),
        "--cell-lib",
        str(CELL_LIB),
        "--top",
        "test_single_pattern_netlist",
        "--max-size",
        "3",
        "--min-occurrences",
        "3",
        "--max-outputs",
        "1",
        "--area-factor",
        "0.85",
        "--output-cells",
        str(output_report.with_suffix(".v")),
        "--output-report",
        str(output_report),
    ]
    env = {"PYTHONPATH": str(REPO_ROOT / "tools" / "aion_opt")}
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"aion_opt generate-cells failed with code {result.returncode}")


def count_full_pattern_occurrences(report_path: Path) -> int:
    """Return occurrences of the 3-cell inv-nand2-nor2 pattern."""
    data = json.loads(report_path.read_text())
    target_key = None
    for pattern in data["patterns_found"]:
        key = pattern["pattern_key"]
        if (
            "sg13g2_inv" in key
            and "sg13g2_nand2" in key
            and "sg13g2_nor2" in key
            and "xor2" not in key
            and pattern["size"] == 3
        ):
            if target_key is not None:
                raise RuntimeError("Found more than one 3-cell inv-nand2-nor2 pattern key")
            target_key = key
    if target_key is None:
        raise RuntimeError("3-cell inv-nand2-nor2 pattern not found in report")
    return next(
        p["occurrences"]
        for p in data["patterns_found"]
        if p["pattern_key"] == target_key
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aion_opt_test_") as tmp:
        report_path = Path(tmp) / "pattern_report.json"
        run_generate_cells(report_path)
        found = count_full_pattern_occurrences(report_path)

    print(f"Found {found} occurrence(s) of the full 3-cell inv-nand2-nor2 pattern")
    if found != EXPECTED_SINGLE_OUTPUT:
        print(
            f"FAIL: expected {EXPECTED_SINGLE_OUTPUT} single-output occurrences, "
            f"found {found}",
            file=sys.stderr,
        )
        return 1

    print("PASS: exactly the 3 single-output occurrences were extracted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
