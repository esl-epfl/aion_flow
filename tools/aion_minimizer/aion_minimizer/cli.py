#!/usr/bin/env python3
"""aion_minimizer CLI implementation.

Example:
    python -m aion_minimizer run top.spice --gates lib.spice -o mega.spice --mode transistor --verify
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

from aion_minimizer.equivalence import check_equivalence
from aion_minimizer.gate_extractor import extract_gate_functions
from aion_minimizer.spice_parser import Subcircuit, parse_spice_file
from aion_minimizer.decompose import DEFAULT_MAX_CLUSTER_INPUTS, INLINE, MEGAGATE
from aion_minimizer.sizing import DEFAULT_L, DEFAULT_WN, DEFAULT_WP, SizingRules
from aion_minimizer.synthesis import (
    DEFAULT_MAX_STACK_DEPTH,
    INVERTED_INPUT_MODES,
    SynthesisResult,
    synthesize,
)


def _split_list(value: str | None) -> List[str]:
    """Parse a comma- or space-separated pin list."""
    if not value:
        return []
    return [item for item in re.split(r"[,\s]+", value.strip()) if item]


def _merge_libraries(paths: List[str]) -> Dict[str, Subcircuit]:
    merged: Dict[str, Subcircuit] = {}
    for path in paths:
        for name, sub in parse_spice_file(path).items():
            merged[name] = sub
    return merged


def _select_top(subckts: Dict[str, Subcircuit], name: str | None = None) -> Subcircuit:
    if name is not None:
        if name not in subckts:
            raise ValueError(
                f"No .subckt named {name!r}; the file defines {sorted(subckts)}"
            )
        return subckts[name]
    netlists = [s for s in subckts.values() if not s.is_gate_definition]
    if len(netlists) == 1:
        return netlists[0]
    if len(subckts) == 1:
        return next(iter(subckts.values()))
    raise ValueError(
        f"Could not identify a unique top-level netlist among {sorted(subckts)}; "
        f"name one with --top"
    )


def run(args: argparse.Namespace) -> None:
    gate_subckts = _merge_libraries(args.gates)
    skipped: Dict[str, str] = {}
    gate_functions = extract_gate_functions(gate_subckts, skipped)

    top_subckts = parse_spice_file(args.top)
    top = _select_top(top_subckts, args.top_name)

    result = synthesize(
        top,
        gate_functions,
        gate_subckts,
        skipped=skipped,
        mode=args.mode,
        rules=SizingRules(
            wn=args.wn,
            wp=args.wp,
            l=args.l,
            drive=args.drive,
            stack_sizing=args.stack_sizing,
            max_fingers=args.max_fingers,
        ),
        max_stack_depth=args.max_stack_depth,
        max_cluster_inputs=args.max_cluster_inputs,
        allow_inline=not args.no_inline,
        single_stage=args.single_stage,
        inverted_inputs=args.inverted_inputs,
        external_inputs=_split_list(args.external_inputs),
    )
    if len(result.flat.primary_inputs) > args.max_inputs:
        raise ValueError(
            f"Too many primary inputs ({len(result.flat.primary_inputs)}); "
            f"maximum is {args.max_inputs}"
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.spice)

    print(f"Wrote {args.output}")
    _report(result)

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(result.externalization_report(), indent=2) + "\n"
        )
        print(f"Wrote {args.report}")

    if args.verify:
        check = check_equivalence(
            result.flat,
            result.spice,
            max_inputs=args.max_inputs,
            ports=result.ports,
            complement_ports=result.complement_ports,
        )
        print(f"Equivalence: {check.describe()}")
        if not check.passed:
            sys.exit(1)


def _report(result: SynthesisResult) -> None:
    """Print the outcome and, per stage, what the decomposer decided."""
    print(
        f"{result.transistors} transistors vs {result.original_transistors} original "
        f"({result.savings:+d}), {result.merged_stages} merged stage(s), "
        f"{result.kept_cells} cell(s) kept, {len(result.inverters)} inverter(s), "
        f"max stack {result.max_stack_depth}"
    )
    for stage in result.stages:
        what = "merged" if stage.kind == MEGAGATE else "kept"
        print(f"  {stage.output_net}: {what} {'+'.join(stage.instances)}")
    if result.external_complements:
        print(
            "  complemented inputs on ports: "
            + ", ".join(sorted(result.complement_ports))
            + " (the instantiating netlist must drive them)"
        )
    if result.internal_complements:
        print(
            "  complemented inputs built inside: "
            + ", ".join(result.internal_complements)
        )


def _add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("top", help="Top-level gate-level SPICE netlist")
    parser.add_argument(
        "--top-name",
        default=None,
        help="Name of the .subckt to minimize, when the file defines several",
    )
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
    parser.add_argument(
        "--wn", default=DEFAULT_WN, help="NMOS width of a single finger"
    )
    parser.add_argument(
        "--wp", default=DEFAULT_WP, help="PMOS width of a single finger"
    )
    parser.add_argument("--l", default=DEFAULT_L, help="Transistor length")
    parser.add_argument(
        "--drive",
        type=int,
        default=1,
        help="Drive strength; N multiplies every device width and finger count",
    )
    parser.add_argument(
        "--stack-sizing",
        action="store_true",
        help=(
            "Widen a device by the depth of its series stack. Off by default "
            "because the SG13G2 x1 cells do not do it either"
        ),
    )
    parser.add_argument(
        "--max-fingers",
        type=int,
        default=16,
        help="Upper bound on fingers per device",
    )
    parser.add_argument(
        "--max-inputs",
        type=int,
        default=6,
        help="Maximum number of primary inputs for exhaustive verification",
    )
    parser.add_argument(
        "--max-stack-depth",
        type=int,
        default=DEFAULT_MAX_STACK_DEPTH,
        help="Maximum series transistors between a rail and the output",
    )
    parser.add_argument(
        "--max-cluster-inputs",
        type=int,
        default=DEFAULT_MAX_CLUSTER_INPUTS,
        help="Maximum boundary inputs of a single merged stage",
    )
    parser.add_argument(
        "--no-inline",
        action="store_true",
        help=(
            "Never keep a standard cell as-is; every stage must be resynthesized "
            "even when that costs more transistors"
        ),
    )
    parser.add_argument(
        "--single-stage",
        action="store_true",
        help=(
            "Flatten the whole netlist into one complementary gate regardless of "
            "cost (the pre-decomposition behaviour)"
        ),
    )
    parser.add_argument(
        "--inverted-inputs",
        choices=INVERTED_INPUT_MODES,
        default="internal",
        help=(
            "Where the inverter for a complemented primary input lives: "
            "'internal' builds it in the cell, 'external' turns every one into a "
            "<pin>_bar port, 'auto' externalizes only the pins named by "
            "--external-inputs"
        ),
    )
    parser.add_argument(
        "--external-inputs",
        default=None,
        help=(
            "Comma-separated pins whose complement arrives on a port "
            "(used by --inverted-inputs auto)"
        ),
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Write a JSON summary of the cell interface and its complemented inputs",
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
