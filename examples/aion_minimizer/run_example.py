#!/usr/bin/env python3
"""Standalone example: minimize a gate-level SPICE netlist.

This mirrors the old pytest smoke test but runs as a plain script.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = REPO_ROOT / "examples" / "aion_minimizer"
BUILD_DIR = REPO_ROOT / "build" / "aion_minimizer"


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    top = EXAMPLE_DIR / "AION_inv_nand2_nor2.spice"
    gates = EXAMPLE_DIR / "sg13g2_stdcell.spice"
    output = BUILD_DIR / "AION_inv_nand2_nor2_minimized.spice"

    run(
        [
            sys.executable,
            "-m",
            "aion_minimizer",
            "run",
            str(top),
            "--gates",
            str(gates),
            "-o",
            str(output),
            "--mode",
            "transistor",
            "--verify",
        ]
    )

    print(f"\nOutput written to: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
