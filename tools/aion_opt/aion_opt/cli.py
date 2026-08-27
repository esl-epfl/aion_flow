"""aion_opt CLI implementation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aion_opt.cellgen.generator import CellGenerator
from aion_opt.config import AionOptConfig
from aion_opt.graph.builder import build_signal_flow_graph
from aion_opt.io.cell_lib import CellLib
from aion_opt.io.netlist_writer import write_verilog
from aion_opt.io.rewriter import rewrite_circuit
from aion_opt.io.verilog_to_json import is_verilog, verilog_to_json
from aion_opt.io.yosys_json import load_yosys_json
from aion_opt.pattern.cover import select_cover
from aion_opt.pattern.miner import mine_patterns
from aion_opt.report.reporter import (
    write_pattern_report,
    write_rewrite_report,
)


TOOL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = TOOL_DIR.parent.parent


def _default_cell_lib() -> Path:
    """Return the default technology dictionary relative to the repo root."""
    return REPO_ROOT / "tech" / "tech_dict" / "sg13g2_stdcell.json"


def _load_config(args: argparse.Namespace) -> None:
    """Override CLI args with values from a YAML config file if provided."""
    config_path: Path | None = getattr(args, "config", None)
    if config_path is None:
        return

    from aion_opt.config import AionOptConfig

    cfg = AionOptConfig.from_yaml(config_path)
    overrides: dict[str, Any] = {
        "input": cfg.input_netlist,
        "cell_lib": cfg.cell_lib,
        "top": cfg.top_module,
        "max_size": cfg.max_pattern_size,
        "min_occurrences": cfg.min_occurrences,
        "area_factor": cfg.area_factor,
    }
    for key, value in overrides.items():
        if value is not None and hasattr(args, key):
            current = getattr(args, key, None)
            if current is None or (
                isinstance(current, (str, Path)) and not current
            ):
                setattr(args, key, value)


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Yosys JSON (.json) or Verilog (.v/.sv) netlist to read. "
             "Verilog inputs are converted to Yosys JSON first. "
             "Can also be set via --config.",
    )
    parser.add_argument(
        "--cell-lib",
        type=Path,
        default=_default_cell_lib(),
        help="Path to the JSON technology dictionary.",
    )
    parser.add_argument(
        "--top",
        type=str,
        default=None,
        help="Top module name (defaults to the module marked top in JSON "
             "or to auto-top when converting Verilog).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional YAML config file. CLI values override config values.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Directory for intermediate files (e.g. Verilog-to-JSON conversion).",
    )


def _resolve_input_json(args: argparse.Namespace) -> Path:
    """Return a Yosys JSON path, converting Verilog inputs if necessary."""
    _load_config(args)
    if is_verilog(args.input):
        print(f"[aion_opt] Converting Verilog input to Yosys JSON: {args.input}")
        work_dir: Path | None = getattr(args, "work_dir", None)
        output_json: Path | None = None
        if work_dir is not None:
            work_dir.mkdir(parents=True, exist_ok=True)
            output_json = work_dir / f"{args.input.stem}.json"
        json_path = verilog_to_json(
            args.input, top_module=args.top, output_json=output_json
        )
        print(f"[aion_opt] Intermediate JSON: {json_path}")
        return json_path
    return args.input


def cmd_graph2verilog(args: argparse.Namespace) -> int:
    input_json = _resolve_input_json(args)
    cell_lib = CellLib(args.cell_lib, collapse_strengths=True)
    circuit = load_yosys_json(input_json, cell_lib=cell_lib, top_module=args.top)
    write_verilog(circuit, args.output)
    print(f"[graph2verilog] Wrote {args.output}")

    # Build the signal-flow graph as a sanity check (not exported yet).
    sfg = build_signal_flow_graph(circuit, cell_lib)
    print(
        f"[graph2verilog] Circuit: {len(circuit.instances)} instances, "
        f"{len(circuit.nets)} nets, {len(sfg.nodes())} combinational nodes"
    )
    return 0


def cmd_generate_cells(args: argparse.Namespace) -> int:
    input_json = _resolve_input_json(args)
    cell_lib = CellLib(args.cell_lib, collapse_strengths=True)
    circuit = load_yosys_json(input_json, cell_lib=cell_lib, top_module=args.top)
    sfg = build_signal_flow_graph(circuit, cell_lib)

    print(
        f"[generate-cells] Mining patterns up to size {args.max_size} "
        f"with min {args.min_occurrences} occurrences"
    )
    patterns = mine_patterns(
        circuit,
        sfg,
        cell_lib,
        max_size=args.max_size,
        min_occurrences=args.min_occurrences,
    )
    total_occurrences = sum(len(v) for v in patterns.values())
    print(
        f"[generate-cells] Found {len(patterns)} pattern type(s) "
        f"with {total_occurrences} occurrence(s)"
    )

    selected = select_cover(
        patterns,
        cell_lib,
        area_factor=args.area_factor,
        allow_overlapping=False,
    )
    print(f"[generate-cells] Selected {len(selected)} non-overlapping occurrence(s)")

    # Generate one cell module per unique selected pattern key.
    generator = CellGenerator()
    seen_keys: set[str] = set()
    module_index: dict[str, int] = {}
    modules: list[str] = []

    for occ in selected:
        key = occ.canonical_key
        if key not in module_index:
            module_index[key] = len(module_index)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        modules.append(generator.generate_cell(occ, module_index[key], cell_lib))

    args.output_cells.parent.mkdir(parents=True, exist_ok=True)
    args.output_cells.write_text("\n".join(modules), encoding="utf-8")
    print(f"[generate-cells] Wrote {len(modules)} cell module(s) to {args.output_cells}")

    # Pattern report.
    write_pattern_report(
        args.output_report,
        patterns,
        selected,
        module_index,
        cell_lib,
        area_factor=args.area_factor,
    )
    print(f"[generate-cells] Wrote report to {args.output_report}")
    return 0


def cmd_rewrite(args: argparse.Namespace) -> int:
    input_json = _resolve_input_json(args)
    cell_lib = CellLib(args.cell_lib, collapse_strengths=True)
    circuit = load_yosys_json(input_json, cell_lib=cell_lib, top_module=args.top)
    sfg = build_signal_flow_graph(circuit, cell_lib)

    # Mine patterns using the same defaults as generate-cells.
    max_size = getattr(args, "max_size", 3)
    min_occurrences = getattr(args, "min_occurrences", 2)
    area_factor = getattr(args, "area_factor", 0.85)

    patterns = mine_patterns(
        circuit,
        sfg,
        cell_lib,
        max_size=max_size,
        min_occurrences=min_occurrences,
    )
    selected = select_cover(
        patterns,
        cell_lib,
        area_factor=area_factor,
        allow_overlapping=False,
    )

    # Re-generate cell modules and map pattern keys to module names.
    generator = CellGenerator()
    module_names: dict[str, str] = {}
    modules: list[str] = []
    for idx, occ in enumerate(
        sorted(selected, key=lambda o: o.canonical_key)
    ):
        key = occ.canonical_key
        if key in module_names:
            continue
        module_names[key] = generator.module_name(occ, len(module_names))
        modules.append(generator.generate_cell(occ, len(module_names) - 1, cell_lib))

    # Write the cell library if requested; otherwise assume existing --cells file.
    if modules:
        args.cells.parent.mkdir(parents=True, exist_ok=True)
        args.cells.write_text("\n".join(modules), encoding="utf-8")
        print(f"[rewrite] Wrote {len(modules)} AION cell module(s) to {args.cells}")

    original_instances = len(circuit.instances)
    original_nets = len(circuit.nets)
    original_total_area = sum(
        cell_lib.area(inst.cell_type) for inst in circuit.instances.values()
    )

    rewritten = rewrite_circuit(circuit, selected, module_names)
    write_verilog(rewritten, args.output_netlist)
    print(
        f"[rewrite] Wrote optimized netlist to {args.output_netlist} "
        f"({len(rewritten.instances)} instances, {len(rewritten.nets)} nets)"
    )

    write_rewrite_report(
        args.output_report,
        patterns,
        selected,
        module_names,
        cell_lib,
        original_instances=original_instances,
        rewritten_instances=len(rewritten.instances),
        original_nets=original_nets,
        rewritten_nets=len(rewritten.nets),
        area_factor=area_factor,
        original_total_area=original_total_area,
    )
    print(f"[rewrite] Wrote report to {args.output_report}.json / .md / .html")
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    args.work_dir = args.output_dir / "work"
    input_json = _resolve_input_json(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    cell_lib = CellLib(args.cell_lib, collapse_strengths=True)
    circuit = load_yosys_json(input_json, cell_lib=cell_lib, top_module=args.top)
    sfg = build_signal_flow_graph(circuit, cell_lib)

    # If the user gave a JSON input, write an equivalent reference Verilog
    # so that LEC can compare two gate-level Verilog netlists.
    ref_input = args.input
    if not is_verilog(ref_input):
        ref_path = args.output_dir / f"{circuit.name}_ref.v"
        write_verilog(circuit, ref_path)
        ref_input = ref_path

    max_size = args.max_size
    min_occurrences = args.min_occurrences
    area_factor = args.area_factor

    print(
        f"[run-all] Mining patterns up to size {max_size} "
        f"with min {min_occurrences} occurrences"
    )
    patterns = mine_patterns(
        circuit,
        sfg,
        cell_lib,
        max_size=max_size,
        min_occurrences=min_occurrences,
    )
    selected = select_cover(
        patterns,
        cell_lib,
        area_factor=area_factor,
        allow_overlapping=False,
    )
    print(
        f"[run-all] Selected {len(selected)} occurrence(s) "
        f"covering {len({o.canonical_key for o in selected})} pattern type(s)"
    )

    # Generate cells.
    generator = CellGenerator()
    module_names: dict[str, str] = {}
    modules: list[str] = []
    for occ in sorted(selected, key=lambda o: o.canonical_key):
        key = occ.canonical_key
        if key in module_names:
            continue
        module_names[key] = generator.module_name(occ, len(module_names))
        modules.append(generator.generate_cell(occ, len(module_names) - 1, cell_lib))

    cells_path = args.output_dir / "aion_cells.v"
    cells_path.write_text("\n".join(modules), encoding="utf-8")
    print(f"[run-all] Wrote AION cells to {cells_path}")

    # Rewrite netlist (hierarchical AION output).
    original_instances = len(circuit.instances)
    original_nets = len(circuit.nets)
    original_total_area = sum(
        cell_lib.area(inst.cell_type) for inst in circuit.instances.values()
    )
    rewritten = rewrite_circuit(circuit, selected, module_names, flatten=False)
    netlist_path = args.output_dir / f"{circuit.name}_optimized.v"
    write_verilog(rewritten, netlist_path)
    print(
        f"[run-all] Wrote optimized netlist to {netlist_path} "
        f"({len(rewritten.instances)} instances, {len(rewritten.nets)} nets)"
    )

    # Flat netlist (AION cells inlined) for SEC/physical tools that need a
    # pure PDK primitive netlist.
    flat = rewrite_circuit(circuit, selected, module_names, flatten=True)
    flat_netlist_path = args.output_dir / f"{circuit.name}_optimized_flat.v"
    write_verilog(flat, flat_netlist_path)
    print(
        f"[run-all] Wrote flat netlist to {flat_netlist_path} "
        f"({len(flat.instances)} instances, {len(flat.nets)} nets)"
    )

    # Reports.
    report_prefix = args.output_dir / "report"
    write_rewrite_report(
        report_prefix,
        patterns,
        selected,
        module_names,
        cell_lib,
        original_instances=original_instances,
        rewritten_instances=len(rewritten.instances),
        original_nets=original_nets,
        rewritten_nets=len(rewritten.nets),
        area_factor=area_factor,
        original_total_area=original_total_area,
    )
    print(f"[run-all] Wrote reports to {report_prefix}.json / .md / .html")

    # Verification gates.
    import subprocess

    print("[run-all] Running LEC...")
    sys.stdout.flush()

    lec_cmd = [
        "make",
        "aion-opt-lec",
        f"REF={ref_input}",
        f"MOD={netlist_path} {cells_path}",
        f"BUILD_DIR={args.output_dir}",
    ]
    lec_result = subprocess.run(lec_cmd, cwd=REPO_ROOT)
    if lec_result.returncode != 0:
        print("[run-all] LEC FAILED")
        return 1

    # SEC is optional and requires RTL files; only run if they exist.
    # Use the flat netlist (pure PDK primitives) because some formal tools
    # cannot reason through custom hierarchical AION cells.
    rtl_dirs = getattr(args, "rtl_dirs", [])
    rtl_files: list[Path] = []
    for rtl_dir in rtl_dirs:
        rtl_dir = Path(rtl_dir)
        rtl_files.extend(
            [
                rtl_dir / f"{circuit.name}.v",
                rtl_dir / "spm.v",
            ]
        )
    rtl_existing = [str(p) for p in rtl_files if p.exists()]
    if rtl_existing:
        print("[run-all] Running SEC on flat netlist...")
        sys.stdout.flush()
        sec_cmd = [
            "make",
            "aion-opt-sec",
            f"RTL={' '.join(rtl_existing)}",
            f"NETLIST={flat_netlist_path}",
            f"BUILD_DIR={args.output_dir}",
        ]
        sec_result = subprocess.run(sec_cmd, cwd=REPO_ROOT)
        if sec_result.returncode != 0:
            print("[run-all] SEC FAILED")
            return 1
    else:
        print("[run-all] SEC skipped (no RTL files found)")

    print("[run-all] All verification gates passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aion_opt",
        description="Graph-based netlist optimizer for Tiny Tapeout designs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    g2v = subparsers.add_parser(
        "graph2verilog",
        help="Read Yosys JSON, build graph, emit Verilog.",
    )
    _add_common_args(g2v)
    g2v.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output Verilog netlist path.",
    )
    g2v.set_defaults(func=cmd_graph2verilog)

    gen = subparsers.add_parser(
        "generate-cells",
        help="Mine patterns and generate AION cells.",
    )
    _add_common_args(gen)
    gen.add_argument(
        "--max-size",
        type=int,
        default=3,
        help="Maximum pattern size to mine.",
    )
    gen.add_argument(
        "--min-occurrences",
        type=int,
        default=2,
        help="Minimum number of occurrences for a pattern to be kept.",
    )
    gen.add_argument(
        "--area-factor",
        type=float,
        default=0.85,
        help="Area reduction factor for new cells.",
    )
    gen.add_argument(
        "--output-cells",
        type=Path,
        required=True,
        help="Output path for generated cell library Verilog.",
    )
    gen.add_argument(
        "--output-report",
        type=Path,
        required=True,
        help="Output path for pattern report (JSON).",
    )
    gen.set_defaults(func=cmd_generate_cells)

    rew = subparsers.add_parser(
        "rewrite",
        help="Rewrite netlist using generated AION cells.",
    )
    _add_common_args(rew)
    rew.add_argument(
        "--cells",
        type=Path,
        required=True,
        help="Generated AION cell library Verilog.",
    )
    rew.add_argument(
        "--output-netlist",
        type=Path,
        required=True,
        help="Output optimized netlist path.",
    )
    rew.add_argument(
        "--output-report",
        type=Path,
        required=True,
        help="Report output prefix (report.json / report.md).",
    )
    rew.add_argument(
        "--max-size",
        type=int,
        default=3,
        help="Maximum pattern size to mine.",
    )
    rew.add_argument(
        "--min-occurrences",
        type=int,
        default=2,
        help="Minimum number of occurrences for a pattern to be kept.",
    )
    rew.add_argument(
        "--area-factor",
        type=float,
        default=0.85,
        help="Area reduction factor for new cells.",
    )
    rew.set_defaults(func=cmd_rewrite)

    allp = subparsers.add_parser(
        "run-all",
        help="Run all steps end-to-end.",
    )
    _add_common_args(allp)
    allp.add_argument(
        "--output-dir",
        type=Path,
        default=Path("out"),
        help="Directory for all outputs.",
    )
    allp.add_argument(
        "--max-size",
        type=int,
        default=3,
        help="Maximum pattern size to mine.",
    )
    allp.add_argument(
        "--min-occurrences",
        type=int,
        default=2,
        help="Minimum number of occurrences for a pattern to be kept.",
    )
    allp.add_argument(
        "--area-factor",
        type=float,
        default=0.85,
        help="Area reduction factor for new cells.",
    )
    allp.add_argument(
        "--rtl-dirs",
        type=str,
        nargs="+",
        default=[],
        help="Directories to search for RTL files when running SEC.",
    )
    allp.set_defaults(func=cmd_run_all)

    args = parser.parse_args(argv)
    _load_config(args)
    if args.input is None:
        parser.error("the following arguments are required: --input")
    return args.func(args)
