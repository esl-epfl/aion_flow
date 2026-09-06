#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Davide Schiavone
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
"""
Run the aion_minimizer on every SPICE cell in a directory.

Only single-output cells are minimized; multi-output cells are skipped with a
warning. The minimized netlists are written to the output directory.

Usage:
    python3 run_aion_minimizer_batch.py <input_dir> <output_dir> \
        --gates <gate_lib.spice> [--mode transistor] [--verify] ...
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch-run aion_minimizer on SPICE cells.",
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing SPICE files to minimize.",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where minimized SPICE files will be written.",
    )
    parser.add_argument(
        "--gates",
        action="append",
        required=True,
        help="Gate-definition library SPICE file(s) (repeatable).",
    )
    parser.add_argument(
        "--mode",
        choices=["transistor", "area", "balance"],
        default="transistor",
        help="Optimization mode for the minimizer.",
    )
    parser.add_argument(
        "--wn",
        default="0.74u",
        help="NMOS base width (one finger; matches the SG13G2 x1 cells).",
    )
    parser.add_argument(
        "--wp",
        default="1.12u",
        help="PMOS base width (one finger; matches the SG13G2 x1 cells).",
    )
    parser.add_argument(
        "--l",
        dest="length",
        default="0.13u",
        help="Transistor length.",
    )
    parser.add_argument(
        "--max-inputs",
        type=int,
        default=12,
        help="Maximum number of primary inputs for exhaustive verification.",
    )
    parser.add_argument(
        "--skip-multi-output",
        action="store_true",
        help="Skip cells with more than one output. aion_minimizer handles them, "
        "so this is only needed for downstream steps that cannot.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run equivalence check after generation.",
    )
    parser.add_argument(
        "--python",
        default="python3",
        help="Python executable to use for invoking aion_minimizer.",
    )
    parser.add_argument(
        "--module",
        default="aion_minimizer",
        help="Python module name for the minimizer CLI.",
    )
    parser.add_argument(
        "--verify-spice",
        action="store_true",
        help="Run aion-char-verify-spice on each minimized cell.",
    )
    parser.add_argument(
        "--make",
        default="make",
        help="Make executable for verify-spice invocations.",
    )
    parser.add_argument(
        "--docker-runner",
        default=None,
        help="Path to a Docker runner script; if set, verify-spice runs through it.",
    )
    parser.add_argument(
        "--netlist",
        default=None,
        help="AION cells Verilog netlist used for verify-spice.",
    )
    parser.add_argument(
        "--build-dir",
        default=None,
        help="Build directory passed to verify-spice (BUILD_DIR_CHAR).",
    )
    return parser.parse_args()


def count_outputs(spice_path: Path) -> int:
    """Count the .subckt pins that look like outputs (non-VDD/VSS).

    A name heuristic, and only used by ``--skip-multi-output``; the minimizer
    itself works out the real directions from the netlist.
    """
    outputs = 0
    with open(spice_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip().lower()
            if stripped.startswith(".subckt"):
                tokens = stripped.split()
                pins = [p for p in tokens[2:] if p not in ("vdd", "vss")]
                # Heuristic: output pins are typically after inputs. We count
                # pins that look like outputs (O* or Y* or X*).
                outputs = sum(
                    1
                    for p in pins
                    if p.startswith("o") or p.startswith("y") or p.startswith("x")
                )
                break
    return outputs


def strip_reference_prefix(name: str) -> str:
    """Remove the 'reference_' prefix used by aion_char generated netlists."""
    return name.removeprefix("reference_")


def rewrite_subckt_name(spice_path: Path, new_name: str) -> str:
    """Read a SPICE file and replace the top-level .subckt name."""
    content = spice_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped.startswith(".subckt"):
            tokens = line.split()
            tokens[1] = new_name
            lines[i] = " ".join(tokens)
            break
    return "\n".join(lines) + "\n"


def run_minimizer(
    python: str,
    module: str,
    input_path: Path,
    output_path: Path,
    gates: list[str],
    mode: str,
    wn: str,
    wp: str,
    length: str,
    max_inputs: int,
    verify: bool,
) -> int:
    """Invoke aion_minimizer run on a single SPICE file."""
    cmd = [
        python,
        "-m",
        module,
        "run",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        mode,
        "--wn",
        wn,
        "--wp",
        wp,
        "--l",
        length,
        "--max-inputs",
        str(max_inputs),
    ]
    for gate in gates:
        cmd.extend(["--gates", gate])
    if verify:
        cmd.append("--verify")

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
    else:
        print(result.stdout, end="")
    return result.returncode


def run_verify_spice(
    make: str,
    cell: str,
    spice: Path,
    docker_runner: str | None,
    netlist: Path | None,
    build_dir: Path | None,
) -> int:
    """Invoke make aion-minimizer-verify-spice for a minimized cell."""
    make_cmd = f"{make} aion-minimizer-verify-spice CELL={cell} SPICE={spice}"
    if netlist:
        make_cmd += f" NETLIST={netlist}"
    if build_dir:
        make_cmd += f" BUILD_DIR={build_dir}"
    if docker_runner:
        cmd = [docker_runner, make_cmd]
    else:
        cmd = make_cmd.split()
    print(f"[VERIFY] {cell}")
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
    else:
        print(result.stdout, end="")
    return result.returncode


def main() -> int:
    args = parse_args()

    if not args.input_dir.is_dir():
        print(f"Error: input directory not found: {args.input_dir}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    spice_files = sorted(args.input_dir.glob("*.spice"))
    if not spice_files:
        print(f"Warning: no .spice files found in {args.input_dir}", file=sys.stderr)
        return 0

    skipped: list[str] = []
    failed: list[str] = []
    passed: list[str] = []
    verify_failed: list[str] = []

    for spice_file in spice_files:
        outputs = count_outputs(spice_file)
        if args.skip_multi_output and outputs != 1:
            skipped.append(spice_file.name)
            print(
                f"[SKIP] {spice_file.name}: {outputs} outputs (only single-output cells are minimized)"
            )
            continue

        cell_name = strip_reference_prefix(spice_file.stem)
        output_path = args.output_dir / f"{cell_name}_minimized.spice"
        print(f"[RUN] {spice_file.name} -> {output_path.name}")
        rc = run_minimizer(
            python=args.python,
            module=args.module,
            input_path=spice_file,
            output_path=output_path,
            gates=args.gates,
            mode=args.mode,
            wn=args.wn,
            wp=args.wp,
            length=args.length,
            max_inputs=args.max_inputs,
            verify=args.verify,
        )
        if rc != 0:
            failed.append(spice_file.name)
            continue

        passed.append(spice_file.name)

        # aion_minimizer keeps the input subckt name (reference_*); rewrite it
        # to the clean AION cell name so downstream tools see a consistent name.
        output_path.write_text(
            rewrite_subckt_name(output_path, cell_name),
            encoding="utf-8",
        )

        if args.verify_spice:
            vrc = run_verify_spice(
                args.make,
                cell_name,
                output_path,
                args.docker_runner,
                args.netlist,
                args.build_dir,
            )
            if vrc != 0:
                verify_failed.append(cell_name)

    print()
    print(
        f"Batch minimization complete: {len(passed)} passed, {len(failed)} failed, "
        f"{len(skipped)} skipped, {len(verify_failed)} verify-spice failed"
    )
    if skipped:
        print(f"  skipped: {', '.join(skipped)}")
    if failed:
        print(f"  failed: {', '.join(failed)}")
    if verify_failed:
        print(f"  verify-spice failed: {', '.join(verify_failed)}")

    return 1 if (failed or verify_failed) else 0


if __name__ == "__main__":
    sys.exit(main())
