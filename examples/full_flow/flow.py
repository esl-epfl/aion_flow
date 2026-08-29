"""
Full Flow Runner
================

Run the flow using the root Makefile.

This script is located in:
    examples/full_flow/flow.py

Run it from the repository root:
    python examples/full_flow/flow.py
"""

from __future__ import annotations

from pathlib import Path

from util import PrintSectionName, Step, Style, banner, color, run_step

# =============================================================================
# Flow Variables
# =============================================================================
# General
# TOP = "pm32"
# INPUT_NETLIST = Path("examples/aion_opt/pm32.nl.v")

TOP = "netlist"
INPUT_NETLIST = Path("examples/full_flow/netlist.v")

BUILD_DIR = Path("build/full_flow")
REPORT_DIR = BUILD_DIR / "report"

# Pattern Extraction
MAX_SIZE = 3
MIN_OCCURRENCES = 2
AREA_FACTOR = 0.85
MAX_OUTPUTS = 1

AION_CELLS = BUILD_DIR / "aion_cells.v"
OPTIMIZED_NETLIST = BUILD_DIR / "aion_netlist.v"

# =============================================================================
# Flow definition
# =============================================================================

FLOW = [
    PrintSectionName("Pattern Extraction"),
    Step(
        "Extract AION Cells",
        "aion-opt-generate-cells",
        [
            f"INPUT={INPUT_NETLIST}",
            f"TOP={TOP}",
            f"MIN_OCCURRENCES={MIN_OCCURRENCES}",
            f"AREA_FACTOR={AREA_FACTOR}",
            f"MAX_OUTPUTS={MAX_OUTPUTS}",
            f"CELLS={AION_CELLS}",
            f"BUILD_DIR={BUILD_DIR}",
            f"PATTERN_REPORT={REPORT_DIR / 'pattern_report.json'}",
        ],
    ),
    Step(
        "Rewrite Netlist",
        "aion-opt-rewrite",
        [
            f"INPUT={INPUT_NETLIST}",
            f"TOP={TOP}",
            f"CELLS={AION_CELLS}",
            f"BUILD_DIR={BUILD_DIR}",
            f"REWRITE_NETLIST={OPTIMIZED_NETLIST}",
            f"REWRITE_REPORT={REPORT_DIR / 'extraction_report'}",
            f"MAX_OUTPUTS={MAX_OUTPUTS}",
        ],
    ),
    Step(
        "Run LEC",
        "aion-opt-lec",
        [
            f"REF={INPUT_NETLIST}",
            f"MOD={OPTIMIZED_NETLIST} {AION_CELLS}",
            f"BUILD_DIR={BUILD_DIR}",
        ],
    ),
    # Step(
    #     "Run SEC",
    #     "aion-opt-sec",
    #     [
    #         f"RTL={}",
    #         f"NETLIST={}",
    #     ],
    # ),
]


# =============================================================================
# Runner
# =============================================================================


def main() -> None:
    total_steps = sum(1 for item in FLOW if isinstance(item, Step))

    print()
    print(color(banner(" FULL FLOW "), Style.BLUE, Style.BOLD))
    print(color(f"  → running {total_steps} step(s)", Style.DIM))
    print()

    step_index = 0
    for item in FLOW:
        if isinstance(item, PrintSectionName):
            print()
            print(color(banner(f" {item.name.upper()} "), Style.MAGENTA, Style.BOLD))
            print()
            continue

        step_index += 1
        run_step(item, step_index, total_steps)

    print()
    print(color(banner(" SUCCESS "), Style.GREEN, Style.BOLD))
    print(color("  ✔ all flow steps completed successfully", Style.GREEN))
    print()


if __name__ == "__main__":
    main()
