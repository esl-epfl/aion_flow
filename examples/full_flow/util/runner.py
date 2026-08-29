"""Flow step runner."""

import subprocess
import sys

from .config import ROOT
from .step import Step
from .style import Style, banner, color


def run_step(step: Step, index: int, total: int) -> None:
    """Run a single Make target."""

    command = ["make", step.target, *step.variables]

    print()
    print(color(banner(f" STEP {index}/{total}: {step.name.upper()} "), Style.CYAN, Style.BOLD))
    print(color("  ▶ command:", Style.DIM), color(" ".join(command), Style.WHITE))
    print()

    result = subprocess.run(
        command,
        cwd=ROOT,
    )

    if result.returncode != 0:
        print()
        print(color(banner(" FAILED "), Style.BG_RED, Style.WHITE, Style.BOLD))
        print(color(f"  ✖ {step.name} failed with exit code {result.returncode}", Style.RED, Style.BOLD))
        print()

        sys.exit(result.returncode)

    print(color(f"  ✔ {step.name} completed", Style.GREEN))
