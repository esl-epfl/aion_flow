"""aion_opt CLI implementation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from aion_opt.cellgen.generator import CellGenerator
from aion_opt.config import AionOptConfig
from aion_opt.graph.circuit import Circuit
from aion_opt.graph.builder import build_signal_flow_graph
from aion_opt.io.cell_lib import CellLib
from aion_opt.io.netlist_writer import write_verilog
from aion_opt.io.rewriter import rewrite_circuit
from aion_opt.io.verilog_to_json import (
    is_verilog,
    verilog_to_json,
    verilog_to_json_all_modules,
)
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


def _canonical_key_for_circuit(circuit: Circuit, cell_lib: CellLib) -> str:
    """Compute a pattern canonical key from a structural module circuit."""
    from aion_opt.pattern.subgraph import _canonical_key

    node_types = {
        name: cell_lib.collapse_name(inst.cell_type)
        for name, inst in circuit.instances.items()
    }
    internal_edges: list[tuple[str, str, str, str, str]] = []
    seen: set[tuple[str, str, str, str, str]] = set()

    for net_name, net in circuit.nets.items():
        # Keep instance-to-instance connections even when the net is also a
        # module port (boundary outputs may still fan out inside the cell).
        for src_inst, src_pin in net.drivers:
            if src_inst == "":
                continue
            for dst_inst, dst_pin in net.loads:
                if dst_inst == "":
                    continue
                edge = (src_inst, src_pin, dst_inst, dst_pin, net_name)
                if edge not in seen:
                    seen.add(edge)
                    internal_edges.append(edge)

    return _canonical_key(node_types, internal_edges)


def _load_cells_mapping(cells_path: Path, cell_lib: CellLib) -> dict[str, str]:
    """Return a mapping from pattern canonical key to AION module name.

    First try embedded ``// AION canonical_key: ...`` comments. If none are
    found, fall back to deriving the canonical key from each module's
    structure via Yosys.
    """
    text = cells_path.read_text(encoding="utf-8")
    module_names: dict[str, str] = {}

    # Comment-based matching (fast, works for cells from generate-cells).
    pending_key: str | None = None
    for line in text.splitlines():
        key_match = re.match(r"^\s*//\s*AION\s+canonical_key:\s*(.+?)\s*$", line)
        if key_match:
            pending_key = key_match.group(1)
            continue
        if pending_key is not None:
            module_match = re.match(r"^\s*module\s+(\w+)", line)
            if module_match:
                module_names[pending_key] = module_match.group(1)
                pending_key = None
            elif line.strip() and not line.strip().startswith("//"):
                # Reset if we hit a non-comment line before the module header.
                pending_key = None

    if module_names:
        return module_names

    # Structural fallback for cell libraries without embedded metadata.
    if not is_verilog(cells_path):
        raise ValueError(f"--cells must be a Verilog file: {cells_path}")

    json_path = verilog_to_json_all_modules(cells_path)
    try:
        with open(json_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for mod_name in data.get("modules", {}):
            circuit = load_yosys_json(
                json_path, cell_lib=cell_lib, top_module=mod_name
            )
            key = _canonical_key_for_circuit(circuit, cell_lib)
            if key:
                module_names[key] = mod_name
    finally:
        json_path.unlink(missing_ok=True)

    return module_names


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
    args.output_cells.write_text("// AION Optimizer - Extracted Patterns\n// Automatically generated by AION Optimizer\n\n" + "\n".join(modules), encoding="utf-8")
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
    if not args.cells.exists():
        print(
            f"[rewrite] Error: --cells file not found: {args.cells}",
            file=sys.stderr,
        )
        return 1

    input_json = _resolve_input_json(args)
    cell_lib = CellLib(args.cell_lib, collapse_strengths=True)
    circuit = load_yosys_json(input_json, cell_lib=cell_lib, top_module=args.top)
    sfg = build_signal_flow_graph(circuit, cell_lib)

    # Build a mapping from pattern canonical key to the module names supplied
    # by the user. rewrite will only use these cells and will never overwrite
    # the --cells file.
    module_names = _load_cells_mapping(args.cells, cell_lib)
    print(
        f"[rewrite] Loaded {len(module_names)} AION cell module(s) from {args.cells}"
    )

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

    # Keep only the occurrences for which the user actually provided a cell.
    selected = [occ for occ in selected if occ.canonical_key in module_names]
    if not selected:
        print(
            "[rewrite] Warning: no selected patterns match the provided cells; "
            "nothing to rewrite.",
            file=sys.stderr,
        )

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
    rtl_files = [Path(f) for f in getattr(args, "rtl", [])]
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
        help="Input AION cell library Verilog. Only cells present in this file are used for rewriting.",
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
        "--rtl",
        type=Path,
        nargs="+",
        default=[],
        help="RTL Verilog file(s) to use when running SEC.",
    )
    allp.set_defaults(func=cmd_run_all)

    args = parser.parse_args(argv)
    _load_config(args)
    if args.input is None:
        parser.error("the following arguments are required: --input")
    return args.func(args)
