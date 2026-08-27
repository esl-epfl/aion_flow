#!/usr/bin/env python3
"""Utility to run LEC/SEC with kepler-formal, capture logs, and print a clear PASS/FAIL summary."""

from __future__ import annotations

import argparse
import datetime
import os
import shutil
import subprocess
import sys
import unicodedata
from collections.abc import Sequence
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DOCKER_ROOT = Path("/foss/designs/aion_flow")
LOG_DIR_DEFAULT = SCRIPT_DIR / "logs"
LIB_DEFAULT = str(REPO_ROOT / "tech" / "lib" / "sg13g2_stdcell_typ_1p20V_25C.lib")

# Kepler-formal output markers.
PASS_MARKERS = [
    "No difference was found.",
    "No binary-defined difference was found.",
]
FAIL_MARKERS = [
    "Difference was found.",
    "binary-defined difference was found",
]

GREEN = "\033[1;32m"
RED = "\033[1;31m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"


def _display_width(text: str) -> int:
    return sum(
        2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1 for ch in text
    )


def _banner(text: str, color: str) -> str:
    text_width = _display_width(text)
    inner_width = max(text_width + 8, 44)
    padding = inner_width - text_width
    left = padding // 2
    right = padding - left
    centered = " " * left + text + " " * right

    top = "╔" + "═" * (inner_width + 4) + "╗"
    empty = "║" + " " * (inner_width + 4) + "║"
    middle = "║  " + centered + "  ║"
    bottom = "╚" + "═" * (inner_width + 4) + "╝"
    box = f"\n{top}\n{empty}\n{middle}\n{empty}\n{bottom}\n"
    return f"{color}{box}{RESET}"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run LEC/SEC verification using kepler-formal.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--log-dir",
        type=Path,
        default=LOG_DIR_DEFAULT,
        help="Directory where run outputs are collected.",
    )
    common.add_argument(
        "--lib",
        default=LIB_DEFAULT,
        help="Path to the Liberty file.",
    )
    common.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate the YAML config and print the command without executing it.",
    )

    lec_parser = subparsers.add_parser(
        "lec",
        parents=[common],
        help="Logical equivalence check between two netlists.",
    )
    lec_parser.add_argument(
        "--ref",
        nargs="+",
        required=True,
        help="Reference netlist file(s).",
    )
    lec_parser.add_argument(
        "--mod",
        nargs="+",
        required=True,
        help="Modified netlist file(s) to compare against the reference.",
    )

    sec_parser = subparsers.add_parser(
        "sec",
        parents=[common],
        help="Sequential equivalence check between RTL and netlist.",
    )
    sec_parser.add_argument(
        "--rtl",
        nargs="+",
        required=True,
        help="RTL source file(s).",
    )
    sec_parser.add_argument(
        "--netlist",
        nargs="+",
        required=True,
        help="Synthesized netlist file(s).",
    )
    sec_parser.add_argument(
        "--max-k",
        type=int,
        default=32,
        help="SEC max k bound.",
    )
    sec_parser.add_argument(
        "--engine",
        default="pdr",
        help="SEC engine.",
    )
    sec_parser.add_argument(
        "--encoding",
        default="dual_rail_steady",
        help="SEC encoding.",
    )
    sec_parser.add_argument(
        "--uncomputable-seq-as-boundary",
        type=bool,
        default=True,
        help="Treat uncomputable sequentials as boundary.",
    )
    sec_parser.add_argument(
        "--solver",
        default="kissat",
        help="SAT solver.",
    )
    sec_parser.add_argument(
        "--compact-mode",
        type=bool,
        default=True,
        help="Enable compact mode.",
    )
    sec_parser.add_argument(
        "--report-skipped-pos",
        type=bool,
        default=True,
        help="Report skipped primary outputs.",
    )

    return parser.parse_args(argv)


def _relative(path: str) -> str:
    """Return a path relative to the repository root.

    The Docker container always runs from /foss/designs/aion_flow (the repo
    root), so all paths inside the kepler-formal config must be repo-relative.
    """
    p = Path(path).resolve()
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        # Path is outside the repository; return it unchanged.
        return path


def _resolve_paths(paths: list[str]) -> list[str]:
    """Resolve a list of paths relative to the current working directory."""
    resolved: list[str] = []
    for p in paths:
        path = Path(p).resolve()
        resolved.append(str(path))
    return resolved


def build_lec_config(args: argparse.Namespace) -> dict:
    return {
        "verification": "lec",
        "input_paths": [
            [_relative(f) for f in _resolve_paths(args.ref)],
            [_relative(f) for f in _resolve_paths(args.mod)],
        ],
        "liberty_files": [_relative(_resolve_paths([args.lib])[0])],
    }


def build_sec_config(args: argparse.Namespace) -> dict:
    return {
        "format": "sv2v",
        "verification": "sec",
        "max_k": args.max_k,
        "sec_engine": args.engine,
        "sec_encoding": args.encoding,
        "sec_uncomputable_seq_as_boundary": args.uncomputable_seq_as_boundary,
        "input_paths": [
            [_relative(f) for f in _resolve_paths(args.rtl)],
            [_relative(f) for f in _resolve_paths(args.netlist)],
        ],
        "liberty_files": [_relative(_resolve_paths([args.lib])[0])],
        "solver": args.solver,
        "compact_mode": args.compact_mode,
        "report_skipped_pos": args.report_skipped_pos,
    }


def _snapshot_files(directory: Path) -> set:
    """Return a set of existing file paths (not dirs) inside directory."""
    return {p for p in directory.iterdir() if p.is_file()}


def _move_new_artifacts(
    before: set,
    after: set,
    artifacts_dir: Path,
    exclude: Sequence[Path],
) -> list[Path]:
    """Move files created during the run into artifacts_dir."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    exclude_set = {Path(p).resolve() for p in exclude}
    moved: list[Path] = []
    for path in sorted(after - before):
        resolved = path.resolve()
        if resolved in exclude_set:
            continue
        if resolved.is_file():
            dest = artifacts_dir / path.name
            shutil.move(str(path), str(dest))
            moved.append(dest)
    return moved


def _run_kepler(
    config_path: Path,
    log_file: Path,
    dry_run: bool = False,
) -> tuple[int, str]:
    # The container runs from the repo root, so pass a repo-relative config path.
    cmd = [
        "./docker_run.sh",
        "kepler-formal",
        "--config",
        _relative(str(config_path)),
    ]
    print(f"\n[run_lec_sec] Command: {' '.join(cmd)}")
    print(f"[run_lec_sec] Streaming output to: {log_file}\n")

    if dry_run:
        print("[run_lec_sec] Dry run - not executing.")
        return 0, ""

    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as fh:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=SCRIPT_DIR,
        )
        output_chunks: list[str] = []
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            fh.write(line)
            output_chunks.append(line)
        returncode = proc.wait()
    return returncode, "".join(output_chunks)


def _determine_result(output: str) -> tuple[str, str]:
    output_lower = output.lower()
    for marker in PASS_MARKERS:
        if marker.lower() in output_lower:
            return "PASS", "PASS"
    for marker in FAIL_MARKERS:
        if marker.lower() in output_lower:
            return "FAIL", "FAIL"
    if "error" in output_lower or "critical" in output_lower:
        return "ERROR", "FAIL"
    return "UNKNOWN", "FAIL"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    config = build_lec_config(args) if args.command == "lec" else build_sec_config(args)

    if args.dry_run:
        print(f"[run_lec_sec] Dry run config for {args.command}:")
        print(yaml.dump(config, default_flow_style=False, sort_keys=False))
        return 0

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.log_dir / f"{args.command}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    config_path = run_dir / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as fh:
        yaml.dump(config, fh, default_flow_style=False, sort_keys=False)
    print(f"[run_lec_sec] Generated config: {config_path}")

    kepler_log = run_dir / "kepler.log"
    artifacts_dir = run_dir / "artifacts"

    before = _snapshot_files(REPO_ROOT)
    returncode, output = _run_kepler(config_path, kepler_log, dry_run=args.dry_run)
    after = _snapshot_files(REPO_ROOT)

    # Read full output from the log (more reliable than the streamed string).
    full_output = kepler_log.read_text(encoding="utf-8")
    status, overall = _determine_result(full_output)

    moved = _move_new_artifacts(
        before,
        after,
        artifacts_dir,
        exclude=[
            config_path,
            kepler_log,
            SCRIPT_DIR / "run_lec_sec.py",
            SCRIPT_DIR / "docker_run.sh",
        ],
    )
    # Kepler-formal may drop miter logs in the repo root; collect those too.
    for miter_log in sorted(REPO_ROOT.glob("miter_log_*.txt")):
        dest = artifacts_dir / miter_log.name
        shutil.move(str(miter_log), str(dest))
        moved.append(dest)
    if moved:
        print(f"[run_lec_sec] Moved {len(moved)} artifact(s) to {artifacts_dir}")

    print(f"\n[run_lec_sec] Exit code: {returncode}")
    print(f"[run_lec_sec] Logs saved to: {run_dir}")

    if overall == "PASS":
        print(_banner(f"  {args.command.upper()} PASSED  ", GREEN))
    elif status == "ERROR":
        print(_banner(f"  {args.command.upper()} {status}  ", YELLOW))
    else:
        print(_banner(f"  {args.command.upper()} {status}  ", RED))

    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
