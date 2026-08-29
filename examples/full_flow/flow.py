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
BUILD_DIR_STEPS = BUILD_DIR / "steps"
REPORT_DIR = BUILD_DIR / "report"

# Pattern Extraction
MAX_SIZE = 3
MIN_OCCURRENCES = 2
AREA_FACTOR = 0.85
MAX_OUTPUTS = 1

AION_CELLS = BUILD_DIR / "aion_cells.v"
OPTIMIZED_NETLIST = BUILD_DIR / "aion_netlist.v"

# Characterization
LIB_DIR = BUILD_DIR / "lib"

# Minimizer
RAW_SPICE_DIR = BUILD_DIR / "raw_spice"
MINIMIZED_SPICE_DIR = BUILD_DIR / "minimized_spice"
GATE_LIB_SPICE = Path("tech/spice/sg13g2_stdcell.spice")
MINIMIZER_MODE = "transistor"
MINIMIZER_WN = "0.74u"
MINIMIZER_WP = "1.48u"
MINIMIZER_L = "0.13u"
MINIMIZER_MAX_INPUTS = 6
MINIMIZER_VERIFY = True
MINIMIZER_VERIFY_SPICE = True

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
            f"BUILD_DIR={BUILD_DIR_STEPS}",
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
            f"BUILD_DIR={BUILD_DIR_STEPS}",
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
            f"BUILD_DIR={BUILD_DIR_STEPS}",
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
    PrintSectionName("Characterization"),
    Step(
        "Generate AION Cell Testbenches",
        "aion-char-generate",
        [
            f"BUILD_DIR={BUILD_DIR_STEPS}",
            f"NETLIST={AION_CELLS}",
        ],
    ),
    Step(
        "Run SystemVerilog Testbenches",
        "aion-char-sv",
        [
            f"BUILD_DIR={BUILD_DIR_STEPS}",
            f"NETLIST={AION_CELLS}",
        ],
    ),
    Step(
        "Run SPICE Testbenches",
        "aion-char-spice",
        [
            f"BUILD_DIR={BUILD_DIR_STEPS}",
            f"NETLIST={AION_CELLS}",
        ],
    ),
    PrintSectionName("Minimize Cells"),
    Step(
        "Split Reference SPICE Cells",
        "split-spice-cells",
        [
            f"INPUT={BUILD_DIR_STEPS / 'aion_char' / 'tb' / 'spice' / 'reference_cells.spice'}",
            f"OUTPUT={RAW_SPICE_DIR}",
        ],
    ),
    Step(
        "Minimize AION Cells",
        "run-aion-minimizer-batch",
        [
            f"INPUT_DIR={RAW_SPICE_DIR}",
            f"OUTPUT_DIR={MINIMIZED_SPICE_DIR}",
            f"NETLIST={AION_CELLS}",
            f"BUILD_DIR={BUILD_DIR_STEPS / 'minimizer'}",
            f"GATES={GATE_LIB_SPICE}",
            f"MODE={MINIMIZER_MODE}",
            f"WN={MINIMIZER_WN}",
            f"WP={MINIMIZER_WP}",
            f"L={MINIMIZER_L}",
            f"MAX_INPUTS={MINIMIZER_MAX_INPUTS}",
            *(["VERIFY=1"] if MINIMIZER_VERIFY else []),
            *(["VERIFY_SPICE=1"] if MINIMIZER_VERIFY_SPICE else []),
        ],
    ),
    # PrintSectionName("LIB File Generation"),
    # Step(
    #     "Characterize AION Cells",
    #     "aion-char-lib",
    #     [
    #         f"BUILD_DIR_CHAR={BUILD_DIR}",
    #         f"NETLIST={AION_CELLS}",
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
