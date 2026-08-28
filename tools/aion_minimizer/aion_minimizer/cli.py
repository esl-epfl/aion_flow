#!/usr/bin/env python3
"""aion_minimizer CLI implementation.

Example:
    python -m aion_minimizer run top.spice --gates lib.spice -o mega.spice --mode transistor --verify
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

from aion_minimizer.cost_model import compute_cost
from aion_minimizer.equivalence import check_equivalence
from aion_minimizer.gate_extractor import extract_gate_functions
from aion_minimizer.minimizer import minimize_function
from aion_minimizer.netlist_evaluator import flatten_top
from aion_minimizer.pn_network import generate_networks
from aion_minimizer.sizing import size_network
from aion_minimizer.spice_parser import Subcircuit, parse_spice, parse_spice_file
from aion_minimizer.spice_writer import write_spice_to_file


def _merge_libraries(paths: List[str]) -> Dict[str, Subcircuit]:
    merged: Dict[str, Subcircuit] = {}
    for path in paths:
        for name, sub in parse_spice_file(path).items():
            merged[name] = sub
    return merged


def _select_top(subckts: Dict[str, Subcircuit]) -> Subcircuit:
    netlists = [s for s in subckts.values() if not s.is_gate_definition]
    if len(netlists) == 1:
        return netlists[0]
    if len(subckts) == 1:
        return next(iter(subckts.values()))
    raise ValueError(
        f"Could not identify a unique top-level netlist among {list(subckts)}"
    )


def run(args: argparse.Namespace) -> None:
    gate_subckts = _merge_libraries(args.gates)
    gate_functions = extract_gate_functions(gate_subckts)

    top_subckts = parse_spice_file(args.top)
    top = _select_top(top_subckts)

    flat = flatten_top(top, gate_functions, gate_subckts)
    if len(flat.primary_inputs) > args.max_inputs:
        raise ValueError(
            f"Too many primary inputs ({len(flat.primary_inputs)}); "
            f"maximum is {args.max_inputs}"
        )

    min_forms = minimize_function(flat, mode=args.mode)
    network = generate_networks(min_forms, flat.primary_output)
    cost = compute_cost(
        network,
        mode=args.mode,
        primary_inputs=flat.primary_inputs,
        original_instances=top.instances,
        gate_subckts=gate_subckts,
        output_inverted=min_forms.output_inverted,
    )
    sized = size_network(
        network,
        cost.inverters,
        mode=args.mode,
        wn=args.wn,
        wp=args.wp,
        l=args.l,
    )

    write_spice_to_file(
        args.output,
        top.name,
        flat.primary_inputs,
        flat.primary_output,
        sized,
        output_inverted=min_forms.output_inverted,
    )

    print(f"Wrote {args.output}")
    print(
        f"Megagate: {cost.megagate_transistors} transistors, "
        f"{cost.inverter_count} input inverters, "
        f"{cost.total_transistors} total vs {cost.original_transistors} original "
        f"({cost.savings:+d})"
    )

    if args.verify:
        spice_text = Path(args.output).read_text()
        result = check_equivalence(flat, spice_text, max_inputs=args.max_inputs)
        if result.passed:
            print("Equivalence: PASS")
        else:
            print(
                f"Equivalence: FAIL at vector {result.mismatch_vector} "
                f"(expected {result.expected}, got {result.got})"
            )
            sys.exit(1)


def _add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("top", help="Top-level gate-level SPICE netlist")
    parser.add_argument(
        "--gates",
        action="append",
        required=True,
        help="Gate-definition library (repeatable)",
    )
    parser.add_argument(
        "-o", "--output", default="mega.spice", help="Output SPICE file"
    )
    parser.add_argument(
        "--mode",
        choices=["transistor", "area", "balance"],
        default="transistor",
        help="Optimization mode",
    )
    parser.add_argument("--wn", default="0.74u", help="NMOS base width")
    parser.add_argument("--wp", default="1.48u", help="PMOS base width")
    parser.add_argument("--l", default="0.13u", help="Transistor length")
    parser.add_argument(
        "--max-inputs",
        type=int,
        default=6,
        help="Maximum number of primary inputs for exhaustive verification",
    )
    parser.add_argument(
        "--verify", action="store_true", help="Run equivalence check after generation"
    )


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aion-minimizer",
        description="Merge a small gate-level SPICE netlist into a transistor-level megagate.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__import__('aion_minimizer').__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Minimize a gate-level SPICE netlist into a transistor-level megagate.",
    )
    _add_run_args(run_parser)

    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            run(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
