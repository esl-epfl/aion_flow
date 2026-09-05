"""
Optimization Flow Runner
========================

Pattern extraction focused on producing a *small, high-value* cell library.

Where ``flow.py`` rewrites the netlist with every mined cell, this runner adds
a ranking step: the cells are sorted by how much area they buy back, only the
best ``ELITE_COUNT`` of them are kept, and the netlist is rewritten with that
reduced library.  That trade is the point of the flow -- each surviving cell
still has to be characterised and minimised by hand, so a library of 20 cells
that recovers most of the area is worth more than a library of 300 that
recovers all of it.

Both netlists are checked with LEC, which is where the flow stops.

This script is located in:
    examples/full_flow/flow_opt.py

Run it from the repository root:
    python examples/full_flow/flow_opt.py
    make flow-opt
"""

from __future__ import annotations

import json
from pathlib import Path

from util import PrintSectionName, Step, Style, banner, color, run_step

# =============================================================================
# Flow Variables
# =============================================================================
# General
TOP = "tt_um_aion"
INPUT_NETLIST = Path("examples/full_flow/tt_um_aion.nl.v")

BUILD_DIR = Path(f"build/{TOP}_opt/")
BUILD_DIR_STEPS = BUILD_DIR / "steps"
REPORT_DIR = BUILD_DIR / "report"

# -----------------------------------------------------------------------------
# Pattern mining
# -----------------------------------------------------------------------------
# MAX_SIZE        maximum number of standard cells per mined pattern
# MIN_OCCURRENCES how often a pattern must be mined to be considered
# MIN_SELECTED    how often it must survive the non-overlapping cover; below
#                 this the pattern is dropped and the cover is recomputed, so
#                 no cell is generated for a single use site. None = same as
#                 MIN_OCCURRENCES, 1 = keep single-use cells.
# MAX_OUTPUTS     cap on boundary outputs. 1 keeps the cells single-output,
#                 which is what the downstream logic minimizer expects.
# MAX_INPUTS      cap on boundary inputs (None = no limit)
# AREA_FACTOR     assumed AION cell area relative to the cells it replaces
# JOBS            mining worker processes (None = every available core)
MAX_SIZE = 8
MIN_OCCURRENCES = 4
MIN_SELECTED = None
AREA_FACTOR = 0.85
MAX_OUTPUTS = 1
MAX_INPUTS = None
JOBS = None

# -----------------------------------------------------------------------------
# Generated cell library
# -----------------------------------------------------------------------------
# CELL_PREFIX     prefix of every generated module and instance
# ELITE_COUNT     how many cells the elite library keeps (None = all)
# ELITE_METRIC    saved-area | occurrences | saved-area-per-cell
CELL_PREFIX = "AION_"
ELITE_COUNT = 20
ELITE_METRIC = "saved-area"

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
AION_CELLS = BUILD_DIR / "aion_cells.v"
ELITE_CELLS = BUILD_DIR / "aion_cells_elite.v"
FULL_NETLIST = BUILD_DIR / "aion_netlist.v"
ELITE_NETLIST = BUILD_DIR / "aion_netlist_elite.v"
PATTERN_REPORT = REPORT_DIR / "pattern_report.json"
FULL_REPORT = REPORT_DIR / "rewrite_report"
ELITE_REPORT = REPORT_DIR / "rewrite_report_elite"

# Mining result shared between the steps: `rewrite` reuses it instead of
# mining the design a second time.
SELECTION = BUILD_DIR_STEPS / "aion_opt" / "work" / "selection.json"


def optional(name: str, value) -> list[str]:
    """Forward a Make variable only when it is set.

    Leaving a variable out keeps the Makefile/CLI default in charge instead of
    passing an empty value down the chain.
    """
    return [] if value is None else [f"{name}={value}"]


MINE_VARS = [
    f"MAX_SIZE={MAX_SIZE}",
    f"MIN_OCCURRENCES={MIN_OCCURRENCES}",
    f"AREA_FACTOR={AREA_FACTOR}",
    f"CELL_PREFIX={CELL_PREFIX}",
    *optional("MIN_SELECTED", MIN_SELECTED),
    *optional("MAX_OUTPUTS", MAX_OUTPUTS),
    *optional("MAX_INPUTS", MAX_INPUTS),
    *optional("JOBS", JOBS),
]

ELITE_VARS = [
    f"ELITE_METRIC={ELITE_METRIC}",
    *optional("ELITE_COUNT", ELITE_COUNT),
]

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
            *MINE_VARS,
            *ELITE_VARS,
            f"CELLS={AION_CELLS}",
            f"ELITE_CELLS={ELITE_CELLS}",
            f"PATTERN_REPORT={PATTERN_REPORT}",
            f"SELECTION={SELECTION}",
            f"BUILD_DIR={BUILD_DIR_STEPS}",
        ],
    ),
    PrintSectionName("Full Cell Library"),
    Step(
        "Rewrite Netlist (all cells)",
        "aion-opt-rewrite",
        [
            f"INPUT={INPUT_NETLIST}",
            f"TOP={TOP}",
            *MINE_VARS,
            f"CELLS={AION_CELLS}",
            f"REWRITE_NETLIST={FULL_NETLIST}",
            f"REWRITE_REPORT={FULL_REPORT}",
            f"SELECTION={SELECTION}",
            f"BUILD_DIR={BUILD_DIR_STEPS}",
        ],
    ),
    Step(
        "Run LEC (all cells)",
        "aion-opt-lec",
        [
            f"REF={INPUT_NETLIST}",
            f"MOD={FULL_NETLIST} {AION_CELLS}",
            f"BUILD_DIR={BUILD_DIR_STEPS}",
        ],
    ),
    PrintSectionName("Elite Cell Library"),
    Step(
        "Rewrite Netlist (elite cells)",
        "aion-opt-rewrite",
        [
            f"INPUT={INPUT_NETLIST}",
            f"TOP={TOP}",
            *MINE_VARS,
            f"CELLS={ELITE_CELLS}",
            f"REWRITE_NETLIST={ELITE_NETLIST}",
            f"REWRITE_REPORT={ELITE_REPORT}",
            f"SELECTION={SELECTION}",
            f"BUILD_DIR={BUILD_DIR_STEPS}",
        ],
    ),
    Step(
        "Run LEC (elite cells)",
        "aion-opt-lec",
        [
            f"REF={INPUT_NETLIST}",
            f"MOD={ELITE_NETLIST} {ELITE_CELLS}",
            f"BUILD_DIR={BUILD_DIR_STEPS}",
        ],
    ),
]

# =============================================================================
# Runner
# =============================================================================


def summarize() -> None:
    """Print the full-vs-elite trade-off from the two rewrite reports."""
    rows = []
    for label, report in (("all cells", FULL_REPORT), ("elite cells", ELITE_REPORT)):
        path = report.with_suffix(".json")
        if not path.exists():
            continue
        summary = json.loads(path.read_text())["summary"]
        rows.append(
            (
                label,
                summary["patterns_applied"],
                summary["occurrences_applied"],
                summary["cell_reduction"],
                summary["estimated_area_savings"],
                summary["estimated_total_area_savings"]
                / summary["original_total_area"]
                * 100
                if summary["original_total_area"]
                else 0.0,
            )
        )

    if not rows:
        return

    print()
    print(color(banner(" RESULTS "), Style.BLUE, Style.BOLD))
    print()
    header = f"  {'library':<14}{'cells':>8}{'sites':>8}{'removed':>10}{'area saved':>14}{'of total':>11}"
    print(color(header, Style.BOLD))
    for label, cells, sites, removed, saved, pct in rows:
        print(
            f"  {label:<14}{cells:>8}{sites:>8}{removed:>10}{saved:>14.2f}{pct:>10.2f}%"
        )
    print()
    print(
        color(f"  cell libraries written to {AION_CELLS} and {ELITE_CELLS}", Style.DIM)
    )
    print(color(f"  reports written to {REPORT_DIR}", Style.DIM))


def main() -> None:
    total_steps = sum(1 for item in FLOW if isinstance(item, Step))

    print()
    print(color(banner(" OPTIMIZATION FLOW "), Style.BLUE, Style.BOLD))
    print(color(f"  → design {TOP} from {INPUT_NETLIST}", Style.DIM))
    print(
        color(
            f"  → patterns up to {MAX_SIZE} cell(s), "
            f"min {MIN_OCCURRENCES} occurrence(s), "
            f"elite library of {ELITE_COUNT or 'all'} cell(s)",
            Style.DIM,
        )
    )
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

    summarize()

    print()
    print(color(banner(" SUCCESS "), Style.GREEN, Style.BOLD))
    print(color("  ✔ all flow steps completed successfully", Style.GREEN))
    print()


if __name__ == "__main__":
    main()
