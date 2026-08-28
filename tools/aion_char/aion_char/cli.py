"""aion_char CLI dispatcher."""

from __future__ import annotations

import argparse
import sys

from aion_char.characterizer import main as lib_main
from aion_char.tb_generator import main as generate_main


def main(argv: list[str] | None = None) -> int:
    """Dispatch to the aion_char subcommands."""
    parser = argparse.ArgumentParser(
        prog="aion_char",
        description="Testbench generation and Liberty characterization for AION cells.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__import__('aion_char').__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "generate",
        help="Generate exhaustive SV/SPICE testbenches for a std-cell netlist.",
    )
    subparsers.add_parser(
        "lib",
        help="Characterize a SPICE cell and write Liberty .lib files.",
    )

    args, remaining = parser.parse_known_args(argv)

    if args.command == "generate":
        return generate_main(remaining)
    if args.command == "lib":
        return lib_main(remaining)
    return 0
