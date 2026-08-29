#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Davide Schiavone
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
"""
Split or merge SPICE netlists containing .subckt definitions.

merge  - read a single SPICE file and write one file per .subckt cell.
split  - read multiple SPICE files (or a directory) and merge them into one file.

Usage:
    python3 spice_split_merge.py merge <input.spice> -o <output_dir>
    python3 spice_split_merge.py split <file1.spice> <file2.spice> ... -o <output.spice>
    python3 spice_split_merge.py split <input_dir> -o <output.spice>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split or merge SPICE netlist files by .subckt cell.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    merge_parser = subparsers.add_parser(
        "merge",
        help="Split a SPICE file into one file per .subckt cell.",
    )
    merge_parser.add_argument(
        "input",
        type=Path,
        help="Input SPICE file to split.",
    )
    merge_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory for the split cell files.",
    )

    split_parser = subparsers.add_parser(
        "split",
        help="Merge multiple SPICE files (or a directory) into one file.",
    )
    split_parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Input SPICE files or a single directory containing .spice files.",
    )
    split_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output merged SPICE file.",
    )

    return parser.parse_args()


def read_spice(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def split_cells(content: str) -> dict[str, str]:
    """
    Split a SPICE netlist into a dictionary mapping cell name to its full
    .subckt block (including leading comments that belong to the block).
    """
    cells: dict[str, str] = {}
    lines = content.splitlines()

    current_name: str | None = None
    current_lines: list[str] = []
    header_buffer: list[str] = []

    # Matches: .subckt <name> <ports...>
    subckt_re = re.compile(r"^\.subckt\s+(\w+)", re.IGNORECASE)
    ends_re = re.compile(r"^\.ends\b", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()

        subckt_match = subckt_re.match(stripped)
        if subckt_match:
            # Save any leading comments/header lines as part of the cell block.
            current_name = subckt_match.group(1)
            current_lines = header_buffer + [line]
            header_buffer = []
            continue

        if current_name is not None:
            current_lines.append(line)
            if ends_re.match(stripped):
                cells[current_name] = "\n".join(current_lines) + "\n"
                current_name = None
                current_lines = []
        else:
            header_buffer.append(line)

    return cells


def cmd_merge(input_path: Path, output_dir: Path) -> int:
    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    content = read_spice(input_path)
    cells = split_cells(content)

    if not cells:
        print(f"Warning: no .subckt cells found in {input_path}", file=sys.stderr)
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, cell_content in cells.items():
        out_path = output_dir / f"{name}.spice"
        write_file(out_path, cell_content)
        print(f"  wrote {out_path}")

    print(f"Split {len(cells)} cell(s) into {output_dir}")
    return 0


def collect_spice_files(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in inputs:
        if path.is_dir():
            files.extend(sorted(path.glob("*.spice")))
        elif path.is_file():
            files.append(path)
        else:
            print(f"Warning: path not found, skipping: {path}", file=sys.stderr)
    return files


def cmd_split(inputs: list[Path], output_path: Path) -> int:
    files = collect_spice_files(inputs)

    if not files:
        print("Error: no input SPICE files found.", file=sys.stderr)
        return 1

    merged_lines: list[str] = []
    for file in files:
        content = read_spice(file)
        merged_lines.append(f"* Merged from: {file}\n")
        merged_lines.append(content.rstrip("\n"))
        merged_lines.append("\n")

    write_file(output_path, "".join(merged_lines))
    print(f"Merged {len(files)} file(s) into {output_path}")
    return 0


def main() -> int:
    args = parse_args()

    if args.command == "merge":
        return cmd_merge(args.input, args.output)
    if args.command == "split":
        return cmd_split(args.inputs, args.output)

    return 1


if __name__ == "__main__":
    sys.exit(main())
