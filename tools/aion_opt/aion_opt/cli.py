"""aion_opt command-line interface.

The tool is split into small commands that can be chained by the root
``Makefile`` or by the runners in ``examples/full_flow``:

``graph2verilog``
    Parse a netlist and write it back out -- a parser/emitter sanity check.
``generate-cells``
    Mine recurring patterns, emit one Verilog module per pattern, and rank them
    into a full and an *elite* cell library.
``select-elite``
    Re-cut an existing cell library to the best N cells without re-mining.
``rewrite``
    Substitute the cells of a library back into the netlist.
``run-all``
    Everything above plus the LEC/SEC verification gates.
``cells-to-spice``
    Convert generated cells into the gate-level SPICE that ``aion_minimizer``
    consumes.

Nothing is hard-coded: the cell-name prefix, the worker count, the pattern
size, the port limits and every output path are arguments (see ``--help``) and
are also settable through a YAML ``--config`` file.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import fields as dataclass_fields
from pathlib import Path
from collections.abc import Sequence
from typing import Any

from aion_opt.cellgen.generator import (
    COMPLEMENT_SUFFIX,
    DEFAULT_CELL_PREFIX,
    CellGenerator,
)
from aion_opt.config import AionOptConfig
from aion_opt.graph.builder import SignalFlowGraph, build_signal_flow_graph
from aion_opt.graph.circuit import Circuit
from aion_opt.io.cell_file import (
    CellModule,
    library_header,
    load_key_map,
    read_complement_ports,
    split_modules,
    write_library,
)
from aion_opt.io.complements import (
    ComplementPlan,
    analyse as analyse_complements,
    collect_interface_files,
    read_cell_interfaces,
)
from aion_opt.io.cell_lib import CellLib
from aion_opt.io.netlist_writer import write_verilog
from aion_opt.io.rewriter import rewrite_circuit
from aion_opt.io.selection import Selection, compute_fingerprint
from aion_opt.io.verilog_to_json import is_verilog, verilog_to_json
from aion_opt.io.yosys_json import load_yosys_json
from aion_opt.pattern.cover import CoverResult, pattern_area, select_cover
from aion_opt.pattern.miner import MiningResult, mine_patterns, resolve_jobs
from aion_opt.pattern.subgraph import Pattern, build_pattern
from aion_opt.report.reporter import (
    rank_patterns,
    select_elite_keys,
    write_pattern_report,
    write_rewrite_report,
)


TOOL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = TOOL_DIR.parent.parent

#: Default name of the selection cache written into ``--work-dir``.
SELECTION_FILENAME = "selection.json"


def _default_cell_lib() -> Path:
    """Return the default technology dictionary relative to the repo root."""
    return REPO_ROOT / "tech" / "tech_dict" / "sg13g2_stdcell.json"


# ---------------------------------------------------------------------------
# Argument plumbing
# ---------------------------------------------------------------------------
#: ``config field -> argparse dest``.  A config value is only applied when the
#: corresponding CLI argument was left at its default.
_CONFIG_TO_ARG = {
    "input_netlist": "input",
    "cell_lib": "cell_lib",
    "top_module": "top",
    "max_pattern_size": "max_size",
    "min_occurrences": "min_occurrences",
    "max_outputs": "max_outputs",
    "max_inputs": "max_inputs",
    "min_selected_occurrences": "min_selected",
    "collapse_strengths": "collapse_strengths",
    "allow_overlapping": "allow_overlapping",
    "area_factor": "area_factor",
    "cell_prefix": "cell_prefix",
    "elite_count": "elite_count",
    "elite_metric": "elite_metric",
    "complement_plan": "complement_plan",
    "jobs": "jobs",
    "output_dir": "output_dir",
    "work_dir": "work_dir",
}


def _load_config(args: argparse.Namespace) -> None:
    """Fill unset CLI arguments from a YAML config file.

    Explicit command-line values always win: an argument is only overwritten
    when it still holds its parser default, which ``main`` records in
    ``_defaults``.
    """
    config_path: Path | None = getattr(args, "config", None)
    if config_path is None or getattr(args, "_config_applied", False):
        return

    cfg = AionOptConfig.from_yaml(config_path)
    defaults: dict[str, Any] = getattr(args, "_defaults", {})
    known = {f.name for f in dataclass_fields(AionOptConfig)}

    for cfg_key, arg_key in _CONFIG_TO_ARG.items():
        if cfg_key not in known or not hasattr(args, arg_key):
            continue
        value = getattr(cfg, cfg_key)
        if value is None:
            continue
        current = getattr(args, arg_key)
        if arg_key in defaults and current != defaults[arg_key]:
            continue  # explicitly set on the command line
        setattr(args, arg_key, value)

    args._config_applied = True


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Arguments shared by every netlist-reading command."""
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Yosys JSON (.json) or Verilog (.v/.sv) netlist to read. Verilog "
        "inputs are converted to Yosys JSON first. Can also be set via --config.",
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
        help="Top module name (defaults to the module marked top in the JSON, "
        "or to auto-top when converting Verilog).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional YAML config file. Explicit CLI values override it.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Directory for intermediate files (Verilog-to-JSON conversion, "
        "selection cache).",
    )
    parser.add_argument(
        "--cell-prefix",
        type=str,
        default=DEFAULT_CELL_PREFIX,
        help="Prefix for generated module names, e.g. AION_ -> AION_nand2_nor2_0. "
        "Generated instance names use the same prefix.",
    )
    parser.add_argument(
        "--no-collapse-strengths",
        dest="collapse_strengths",
        action="store_false",
        default=True,
        help="Treat each drive-strength variant as its own cell type instead of "
        "folding sg13g2_buf_1/_4/_16 onto one generic type.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output.",
    )


def _add_mining_args(parser: argparse.ArgumentParser) -> None:
    """Arguments controlling pattern mining and cover selection."""
    parser.add_argument(
        "--max-size",
        type=int,
        default=3,
        help="Maximum number of standard cells per mined pattern.",
    )
    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=2,
        help="Minimum number of mined occurrences for a pattern to be kept.",
    )
    parser.add_argument(
        "--min-selected",
        type=int,
        default=None,
        help="Minimum number of occurrences a pattern must still have AFTER the "
        "non-overlapping cover, otherwise it is dropped and the cover is "
        "recomputed. Defaults to --min-occurrences; use 1 to disable.",
    )
    parser.add_argument(
        "--area-factor",
        type=float,
        default=0.85,
        help="Assumed area of an AION cell relative to the cells it replaces. "
        "Drives the area-savings estimate and the cover ranking.",
    )
    parser.add_argument(
        "--max-outputs",
        type=int,
        default=None,
        help="Only mine patterns with at most this many boundary outputs "
        "(default: no limit).",
    )
    parser.add_argument(
        "--max-inputs",
        type=int,
        default=None,
        help="Only mine patterns with at most this many boundary inputs "
        "(default: no limit).",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        help="Worker processes for pattern mining. Omitted or 0 uses every "
        "available core; a negative value leaves that many cores free.",
    )
    parser.add_argument(
        "--allow-overlapping",
        action="store_true",
        help="Keep every occurrence instead of enforcing a disjoint cover. "
        "Analysis only: an overlapping cover cannot be rewritten into a "
        "netlist, so `rewrite` and `run-all` reject it.",
    )


def _add_elite_args(parser: argparse.ArgumentParser) -> None:
    """Arguments controlling the elite (best-N) cell library."""
    parser.add_argument(
        "--elite-count",
        type=int,
        default=None,
        help="Keep only the N highest-ranked cells in the elite library. "
        "Omitted or 0 keeps every generated cell.",
    )
    parser.add_argument(
        "--elite-metric",
        choices=("saved-area", "occurrences", "saved-area-per-cell"),
        default="saved-area",
        help="Ranking used to pick the elite cells.",
    )


def _resolve_input_json(args: argparse.Namespace) -> Path:
    """Return a Yosys JSON path, converting Verilog inputs if necessary."""
    _load_config(args)
    if not is_verilog(args.input):
        return args.input

    _log(args, f"[aion_opt] Converting Verilog input to Yosys JSON: {args.input}")
    work_dir: Path | None = getattr(args, "work_dir", None)
    output_json: Path | None = None
    if work_dir is not None:
        work_dir.mkdir(parents=True, exist_ok=True)
        output_json = work_dir / f"{args.input.stem}.json"
    json_path = verilog_to_json(args.input, top_module=args.top, output_json=output_json)
    _log(args, f"[aion_opt] Intermediate JSON: {json_path}")
    return json_path


def _log(args: argparse.Namespace, message: str) -> None:
    if not getattr(args, "quiet", False):
        print(message, flush=True)


# ---------------------------------------------------------------------------
# Shared pipeline steps
# ---------------------------------------------------------------------------
def _load_design(args: argparse.Namespace) -> tuple[CellLib, Circuit, SignalFlowGraph]:
    """Read the netlist and build the signal-flow graph used for mining."""
    input_json = _resolve_input_json(args)
    cell_lib = CellLib(
        args.cell_lib, collapse_strengths=getattr(args, "collapse_strengths", True)
    )
    circuit = load_yosys_json(input_json, cell_lib=cell_lib, top_module=args.top)
    sfg = build_signal_flow_graph(circuit, cell_lib)
    _log(
        args,
        f"[aion_opt] Design {circuit.name}: {len(circuit.instances)} instance(s), "
        f"{len(circuit.nets)} net(s), {len(sfg.node_types)} combinational node(s)",
    )
    return cell_lib, circuit, sfg


def _mining_parameters(args: argparse.Namespace) -> dict[str, Any]:
    """The parameters that fully determine a mining + cover result."""
    return {
        "max_size": args.max_size,
        "min_occurrences": args.min_occurrences,
        "min_selected": _min_selected(args),
        "area_factor": args.area_factor,
        "max_outputs": args.max_outputs,
        "max_inputs": args.max_inputs,
        "cell_prefix": args.cell_prefix,
        "collapse_strengths": getattr(args, "collapse_strengths", True),
        "allow_overlapping": getattr(args, "allow_overlapping", False),
    }


def _min_selected(args: argparse.Namespace) -> int:
    value = getattr(args, "min_selected", None)
    return args.min_occurrences if value is None else value


def _mine_and_cover(
    args: argparse.Namespace,
    cell_lib: CellLib,
    circuit: Circuit,
    sfg: SignalFlowGraph,
) -> tuple[MiningResult, CoverResult]:
    """Run pattern mining followed by cover selection."""
    jobs = resolve_jobs(args.jobs)
    _log(
        args,
        f"[aion_opt] Mining patterns of up to {args.max_size} cell(s), "
        f"min {args.min_occurrences} occurrence(s), on {jobs} worker(s)",
    )
    mining = mine_patterns(
        circuit,
        sfg,
        cell_lib,
        max_size=args.max_size,
        min_occurrences=args.min_occurrences,
        max_outputs=args.max_outputs,
        max_inputs=args.max_inputs,
        jobs=args.jobs,
        progress=not getattr(args, "quiet", False),
    )
    _log(
        args,
        f"[aion_opt] Enumerated {mining.subgraphs_enumerated} subgraph(s) -> "
        f"{len(mining.occurrences)} pattern type(s) with "
        f"{mining.total_occurrences()} occurrence(s)",
    )

    cover = select_cover(
        mining,
        cell_lib,
        area_factor=args.area_factor,
        allow_overlapping=getattr(args, "allow_overlapping", False),
        min_selected_occurrences=_min_selected(args),
    )
    _log(
        args,
        f"[aion_opt] Cover: {len(cover.selected)} occurrence(s) of "
        f"{len(cover.counts)} pattern type(s) after {cover.iterations} iteration(s)",
    )
    return mining, cover


def _assign_module_names(
    cover: CoverResult,
    mining: MiningResult,
    generator: CellGenerator,
) -> dict[str, str]:
    """Name one module per selected pattern, best-ranked pattern first.

    Module ids follow the area-saving ranking, so ``<prefix>..._0`` is always
    the most valuable cell of the run.
    """
    return {
        key: generator.module_name(mining.representative(key), index)
        for index, key in enumerate(rank_patterns(cover))
    }


def _selection_path(args: argparse.Namespace) -> Path | None:
    """Where the selection cache lives for this invocation."""
    explicit = getattr(args, "selection", None)
    if explicit is not None:
        return explicit
    work_dir = getattr(args, "work_dir", None)
    if work_dir is None:
        return None
    return work_dir / SELECTION_FILENAME


def _materialise(
    circuit: Circuit,
    sfg: SignalFlowGraph,
    cell_lib: CellLib,
    instances: list[str] | tuple[str, ...],
) -> Pattern:
    """Rebuild the full :class:`Pattern` for one occurrence."""
    inst_set = set(instances)
    return build_pattern(
        circuit, inst_set, cell_lib.collapse_name, sfg.edges_for_instances(inst_set)
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_graph2verilog(args: argparse.Namespace) -> int:
    _, circuit, sfg = _load_design(args)
    write_verilog(circuit, args.output)
    _log(args, f"[graph2verilog] Wrote {args.output}")
    _log(
        args,
        f"[graph2verilog] Circuit: {len(circuit.instances)} instances, "
        f"{len(circuit.nets)} nets, {len(sfg.node_types)} combinational nodes",
    )
    return 0


def cmd_generate_cells(args: argparse.Namespace) -> int:
    cell_lib, circuit, sfg = _load_design(args)
    mining, cover = _mine_and_cover(args, cell_lib, circuit, sfg)

    generator = CellGenerator(prefix=args.cell_prefix)
    module_names = _assign_module_names(cover, mining, generator)

    plan = _load_complement_plan(args)
    modules = []
    for index, key in enumerate(rank_patterns(cover)):
        name = module_names[key]
        complements = plan.external_ports(name)
        modules.append(
            CellModule(
                name=name,
                text=_module_body(
                    generator,
                    mining.representative(key),
                    index,
                    cell_lib,
                    complement_inputs=complements,
                ),
                canonical_key=key,
                complement_inputs=tuple(complements),
            )
        )
    externalized = sum(len(m.complement_inputs) for m in modules)
    if externalized:
        _log(
            args,
            f"[generate-cells] {externalized} complemented input(s) taken on "
            f"ports across {sum(1 for m in modules if m.complement_inputs)} cell(s)",
        )

    elite_keys = select_elite_keys(cover, args.elite_count, args.elite_metric)
    elite_set = set(elite_keys)

    write_library(
        args.output_cells,
        modules,
        library_header(
            "AION Optimizer - extracted patterns",
            [
                f"design: {circuit.name}",
                f"cells: {len(modules)}",
                f"occurrences replaced: {len(cover.selected)}",
            ],
        ),
    )
    _log(
        args,
        f"[generate-cells] Wrote {len(modules)} cell module(s) to {args.output_cells}",
    )

    if args.output_elite_cells is not None:
        elite_modules = [m for m in modules if m.canonical_key in elite_set]
        write_library(
            args.output_elite_cells,
            elite_modules,
            library_header(
                "AION Optimizer - elite patterns",
                [
                    f"design: {circuit.name}",
                    f"ranked by: {args.elite_metric}",
                    f"cells: {len(elite_modules)} of {len(modules)}",
                    "estimated area saved: "
                    f"{sum(cover.total_saved_area(k) for k in elite_set):.4f}",
                ],
            ),
        )
        _log(
            args,
            f"[generate-cells] Wrote {len(elite_modules)} elite cell module(s) "
            f"to {args.output_elite_cells}",
        )

    write_pattern_report(
        args.output_report,
        mining,
        cover,
        module_names,
        cell_lib,
        area_factor=args.area_factor,
        elite_keys=elite_keys,
        parameters=_mining_parameters(args),
    )
    _log(args, f"[generate-cells] Wrote report to {args.output_report}")

    selection_path = _selection_path(args)
    if selection_path is not None:
        Selection(
            fingerprint=compute_fingerprint(
                args.input, args.cell_lib, args.top, _mining_parameters(args)
            ),
            parameters=_mining_parameters(args),
            module_names=module_names,
            occurrences=[(key, list(insts)) for key, insts in cover.selected],
            saved_area_per_occurrence={
                key: cover.saved_area_per_occurrence[key] for key in cover.counts
            },
        ).write(selection_path)
        _log(args, f"[generate-cells] Wrote selection cache to {selection_path}")

    return 0


def _module_body(
    generator: CellGenerator,
    pattern: Pattern,
    index: int,
    cell_lib: CellLib,
    complement_inputs: Sequence[str] = (),
) -> str:
    """Render a cell module without its markers.

    :class:`~aion_opt.io.cell_file.CellModule` adds them back when the library
    is written, so they must not be duplicated here.
    """
    rendered = generator.generate_cell(
        pattern, index, cell_lib, complement_inputs=complement_inputs
    )
    lines = rendered.splitlines(keepends=True)
    while lines and lines[0].lstrip().startswith("// AION "):
        lines.pop(0)
    return "".join(lines)


def cmd_select_elite(args: argparse.Namespace) -> int:
    """Re-cut an existing cell library down to its best cells."""
    with open(args.pattern_report, "r", encoding="utf-8") as fh:
        report = json.load(fh)

    entries = report.get("patterns_selected") or report.get("patterns") or []
    if not entries:
        print(
            f"[select-elite] Error: no selected patterns in {args.pattern_report}",
            file=sys.stderr,
        )
        return 1

    metric_key = {
        "saved-area": lambda e: -e.get("total_saved_area", 0.0),
        "occurrences": lambda e: -e.get("occurrences", 0),
        "saved-area-per-cell": lambda e: -(
            e.get("total_saved_area", 0.0) / max(1, e.get("occurrences", 1))
        ),
    }[args.elite_metric]
    ranked = sorted(entries, key=lambda e: (metric_key(e), e.get("pattern_key", "")))
    if args.elite_count:
        ranked = ranked[: args.elite_count]
    wanted = {e["pattern_key"] for e in ranked}

    modules = split_modules(args.cells.read_text(encoding="utf-8"))
    kept = [m for m in modules if m.canonical_key in wanted]
    if not kept:
        print(
            "[select-elite] Error: no module in "
            f"{args.cells} matches the report; was it generated from it?",
            file=sys.stderr,
        )
        return 1

    write_library(
        args.output_cells,
        kept,
        library_header(
            "AION Optimizer - elite patterns",
            [
                f"ranked by: {args.elite_metric}",
                f"cells: {len(kept)} of {len(modules)}",
            ],
        ),
    )
    _log(
        args,
        f"[select-elite] Wrote {len(kept)} of {len(modules)} cell module(s) "
        f"to {args.output_cells}",
    )
    return 0


def _cover_from_selection(
    selection: Selection,
    circuit: Circuit,
    sfg: SignalFlowGraph,
    cell_lib: CellLib,
    allowed_keys: set[str] | None,
) -> tuple[MiningResult, CoverResult]:
    """Rebuild mining/cover objects from a cached selection."""
    occurrences: dict[str, list[tuple[str, ...]]] = defaultdict(list)
    selected: list[tuple[str, tuple[str, ...]]] = []
    for key, insts in selection.occurrences:
        if allowed_keys is not None and key not in allowed_keys:
            continue
        occurrences[key].append(tuple(insts))
        selected.append((key, tuple(insts)))

    mining = MiningResult(occurrences=dict(occurrences))
    mining.bind(circuit, sfg, cell_lib.collapse_name)

    cover = CoverResult(
        selected=selected,
        counts=Counter(key for key, _ in selected),
        saved_area_per_occurrence=dict(selection.saved_area_per_occurrence),
    )
    # Fill in savings for keys the cache predates (older or hand-made files).
    for key in cover.counts:
        cover.saved_area_per_occurrence.setdefault(
            key,
            pattern_area(mining.representative(key).node_types, cell_lib)
            * (1.0 - float(selection.parameters.get("area_factor", 0.85))),
        )
    return mining, cover


def _load_complement_plan(args: argparse.Namespace) -> ComplementPlan:
    """Read ``--complement-plan`` if it was given."""
    path = getattr(args, "complement_plan", None)
    if path is None:
        return ComplementPlan.empty()
    if not path.exists():
        raise FileNotFoundError(f"complement plan not found: {path}")
    return ComplementPlan.read(path)


def _selected_for_cells(
    args: argparse.Namespace,
    cell_lib: CellLib,
    circuit: Circuit,
    sfg: SignalFlowGraph,
    allowed: set[str],
    tag: str,
) -> tuple[MiningResult, CoverResult]:
    """Mine, or reuse the selection cache, restricted to ``allowed`` keys."""
    selection_path = _selection_path(args)
    selection = (
        None
        if selection_path is None or getattr(args, "no_cache", False)
        else Selection.read(selection_path)
    )
    fingerprint = compute_fingerprint(
        args.input, args.cell_lib, args.top, _mining_parameters(args)
    )
    if selection is not None and selection.matches(fingerprint):
        _log(args, f"[{tag}] Reusing selection cache {selection_path}")
        return _cover_from_selection(selection, circuit, sfg, cell_lib, allowed)

    if selection is not None:
        _log(
            args,
            f"[{tag}] Selection cache {selection_path} does not match the "
            "current inputs/parameters; re-mining",
        )
    mining, cover = _mine_and_cover(args, cell_lib, circuit, sfg)
    mining.occurrences = {k: v for k, v in mining.occurrences.items() if k in allowed}
    cover.selected = [(k, occ) for k, occ in cover.selected if k in allowed]
    cover.counts = Counter(key for key, _ in cover.selected)
    return mining, cover


def cmd_complement_plan(args: argparse.Namespace) -> int:
    """Decide, per cell input, whether its inverter belongs outside the cell.

    `aion_minimizer` reports which inputs its transistor implementation needs
    complemented; this command costs both options against the netlist the cells
    will actually be instantiated in, and writes the verdict.
    """
    if not args.cells.exists():
        print(
            f"[complement-plan] Error: --cells file not found: {args.cells}",
            file=sys.stderr,
        )
        return 1

    cell_lib, circuit, sfg = _load_design(args)
    module_names = load_key_map(args.cells, cell_lib)
    if not module_names:
        print(
            f"[complement-plan] Error: no usable cell modules found in {args.cells}",
            file=sys.stderr,
        )
        return 1

    eligible: dict[str, list[str]] | None = None
    if args.interfaces:
        files = collect_interface_files(args.interfaces)
        eligible = read_cell_interfaces(files)
        _log(
            args,
            f"[complement-plan] Read {len(files)} minimizer report(s); "
            f"{sum(1 for v in eligible.values() if v)} cell(s) need a complement",
        )

    _mining, cover = _selected_for_cells(
        args, cell_lib, circuit, sfg, set(module_names), "complement-plan"
    )

    # Port *names* are shared across a pattern, but the boundary entries name
    # this occurrence's instances and nets, so the map is built per site.
    occurrences: list[tuple[str, dict[tuple[str, str, str], str]]] = []
    absorbed: set[str] = set()
    for key, insts in cover.selected:
        pattern = _materialise(circuit, sfg, cell_lib, insts)
        absorbed |= pattern.instances
        occurrences.append((key, CellGenerator.port_map_for_pattern(pattern)[0]))

    plan = analyse_complements(
        circuit,
        cell_lib,
        occurrences,
        module_names,
        absorbed=absorbed,
        eligible_ports=eligible,
    )
    plan.write(args.output_plan)

    chosen = sum(len(entry.get("external", [])) for entry in plan.modules.values())
    _log(
        args,
        f"[complement-plan] Wrote {args.output_plan}: {chosen} port(s) "
        f"externalized across {len(plan.modules)} cell(s)",
    )
    for module, entry in sorted(plan.modules.items()):
        for port, stat in sorted(entry.get("stats", {}).items()):
            verdict = "external" if port in entry.get("external", []) else "internal"
            _log(
                args,
                f"[complement-plan]   {module}.{port}: {verdict} "
                f"({stat['complement_available']}/{stat['occurrences']} sites already "
                f"have it, {stat['internal_devices']} vs {stat['external_devices']} devices)",
            )
    return 0


def cmd_rewrite(args: argparse.Namespace) -> int:
    if not args.cells.exists():
        print(f"[rewrite] Error: --cells file not found: {args.cells}", file=sys.stderr)
        return 1

    cell_lib, circuit, sfg = _load_design(args)

    # The cell library is an *input*: only patterns for which the user actually
    # supplied a module are substituted, and the file is never rewritten.
    module_names = load_key_map(args.cells, cell_lib)
    _log(
        args,
        f"[rewrite] Loaded {len(module_names)} AION cell module(s) from {args.cells}",
    )
    if not module_names:
        print(
            f"[rewrite] Error: no usable cell modules found in {args.cells}",
            file=sys.stderr,
        )
        return 1

    allowed = set(module_names)
    mining, cover = _selected_for_cells(
        args, cell_lib, circuit, sfg, allowed, "rewrite"
    )

    if not cover.selected:
        print(
            "[rewrite] Warning: no selected pattern matches the provided cells; "
            "nothing to rewrite.",
            file=sys.stderr,
        )

    selected_patterns = [
        _materialise(circuit, sfg, cell_lib, insts) for _, insts in cover.selected
    ]

    original_instances = len(circuit.instances)
    original_nets = len(circuit.nets)
    original_total_area = sum(
        cell_lib.area(inst.cell_type) for inst in circuit.instances.values()
    )

    # The library is the authority on a module's interface: if it declares
    # complemented inputs, this rewrite owes every instance a driver for them.
    complement_ports = read_complement_ports(args.cells)
    if complement_ports:
        _log(
            args,
            f"[rewrite] {len(complement_ports)} cell(s) take a complemented "
            f"input on a port",
        )

    rewritten = rewrite_circuit(
        circuit,
        selected_patterns,
        module_names,
        cell_prefix=args.cell_prefix,
        complement_ports=complement_ports,
        cell_lib=cell_lib,
    )
    inserted = len(rewritten.instances) - (
        original_instances - sum(len(p.instances) for p in selected_patterns)
        + len(selected_patterns)
    )
    if inserted:
        _log(
            args,
            f"[rewrite] Inserted {inserted} inverter(s) for complements the "
            f"netlist did not already carry",
        )
    write_verilog(rewritten, args.output_netlist)
    _log(
        args,
        f"[rewrite] Wrote optimized netlist to {args.output_netlist} "
        f"({len(rewritten.instances)} instances, {len(rewritten.nets)} nets)",
    )

    if args.output_flat_netlist is not None:
        flat = rewrite_circuit(
            circuit,
            selected_patterns,
            module_names,
            flatten=True,
            cell_prefix=args.cell_prefix,
        )
        write_verilog(flat, args.output_flat_netlist)
        _log(
            args,
            f"[rewrite] Wrote flat netlist to {args.output_flat_netlist} "
            f"({len(flat.instances)} instances, {len(flat.nets)} nets)",
        )

    write_rewrite_report(
        args.output_report,
        mining,
        cover,
        module_names,
        cell_lib,
        original_instances=original_instances,
        rewritten_instances=len(rewritten.instances),
        original_nets=original_nets,
        rewritten_nets=len(rewritten.nets),
        area_factor=args.area_factor,
        original_total_area=original_total_area,
        parameters=_mining_parameters(args),
    )
    _log(args, f"[rewrite] Wrote report to {args.output_report}.json / .md / .html")
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.work_dir is None:
        args.work_dir = args.output_dir / "work"

    cell_lib, circuit, sfg = _load_design(args)

    # LEC compares two gate-level Verilog netlists, so a JSON input needs an
    # equivalent Verilog reference first.
    ref_input = args.input
    if not is_verilog(ref_input):
        ref_input = args.output_dir / f"{circuit.name}_ref.v"
        write_verilog(circuit, ref_input)

    mining, cover = _mine_and_cover(args, cell_lib, circuit, sfg)

    generator = CellGenerator(prefix=args.cell_prefix)
    module_names = _assign_module_names(cover, mining, generator)
    ranked = rank_patterns(cover)
    plan = _load_complement_plan(args)
    modules = []
    for index, key in enumerate(ranked):
        name = module_names[key]
        complements = plan.external_ports(name)
        modules.append(
            CellModule(
                name=name,
                text=_module_body(
                    generator,
                    mining.representative(key),
                    index,
                    cell_lib,
                    complement_inputs=complements,
                ),
                canonical_key=key,
                complement_inputs=tuple(complements),
            )
        )

    cells_path = args.output_dir / "aion_cells.v"
    write_library(
        cells_path, modules, library_header("AION Optimizer - extracted patterns")
    )
    _log(args, f"[run-all] Wrote AION cells to {cells_path}")

    elite_keys = select_elite_keys(cover, args.elite_count, args.elite_metric)
    elite_path = args.output_dir / "aion_cells_elite.v"
    write_library(
        elite_path,
        [m for m in modules if m.canonical_key in set(elite_keys)],
        library_header("AION Optimizer - elite patterns"),
    )
    _log(args, f"[run-all] Wrote elite AION cells to {elite_path}")

    selected_patterns = [
        _materialise(circuit, sfg, cell_lib, insts) for _, insts in cover.selected
    ]
    original_instances = len(circuit.instances)
    original_nets = len(circuit.nets)
    original_total_area = sum(
        cell_lib.area(inst.cell_type) for inst in circuit.instances.values()
    )

    # `run-all` generates the library itself, so read the markers back from it.
    complement_ports = read_complement_ports(cells_path)
    if complement_ports:
        _log(
            args,
            f"[run-all] {len(complement_ports)} cell(s) take a complemented "
            f"input on a port",
        )

    rewritten = rewrite_circuit(
        circuit,
        selected_patterns,
        module_names,
        cell_prefix=args.cell_prefix,
        complement_ports=complement_ports,
        cell_lib=cell_lib,
    )
    inserted = len(rewritten.instances) - (
        original_instances - sum(len(p.instances) for p in selected_patterns)
        + len(selected_patterns)
    )
    if inserted:
        _log(
            args,
            f"[rewrite] Inserted {inserted} inverter(s) for complements the "
            f"netlist did not already carry",
        )
    netlist_path = args.output_dir / f"{circuit.name}_optimized.v"
    write_verilog(rewritten, netlist_path)
    _log(
        args,
        f"[run-all] Wrote optimized netlist to {netlist_path} "
        f"({len(rewritten.instances)} instances, {len(rewritten.nets)} nets)",
    )

    # Flat netlist (AION cells inlined) for tools that need pure PDK primitives.
    flat = rewrite_circuit(
        circuit,
        selected_patterns,
        module_names,
        flatten=True,
        cell_prefix=args.cell_prefix,
    )
    flat_netlist_path = args.output_dir / f"{circuit.name}_optimized_flat.v"
    write_verilog(flat, flat_netlist_path)
    _log(
        args,
        f"[run-all] Wrote flat netlist to {flat_netlist_path} "
        f"({len(flat.instances)} instances, {len(flat.nets)} nets)",
    )

    report_prefix = args.output_dir / "report"
    write_rewrite_report(
        report_prefix,
        mining,
        cover,
        module_names,
        cell_lib,
        original_instances=original_instances,
        rewritten_instances=len(rewritten.instances),
        original_nets=original_nets,
        rewritten_nets=len(rewritten.nets),
        area_factor=args.area_factor,
        original_total_area=original_total_area,
        elite_keys=elite_keys,
        parameters=_mining_parameters(args),
    )
    _log(args, f"[run-all] Wrote reports to {report_prefix}.json / .md / .html")

    # Verification gates.
    _log(args, "[run-all] Running LEC...")
    sys.stdout.flush()
    lec = subprocess.run(
        [
            "make",
            "aion-opt-lec",
            f"REF={ref_input}",
            f"MOD={netlist_path} {cells_path}",
            f"BUILD_DIR={args.output_dir}",
        ],
        cwd=REPO_ROOT,
    )
    if lec.returncode != 0:
        print("[run-all] LEC FAILED", file=sys.stderr)
        return 1

    # SEC needs RTL and cannot see through custom hierarchical cells, so it
    # runs against the flat netlist.
    rtl_existing = [str(p) for p in (Path(f) for f in args.rtl) if p.exists()]
    if rtl_existing:
        _log(args, "[run-all] Running SEC on flat netlist...")
        sys.stdout.flush()
        sec = subprocess.run(
            [
                "make",
                "aion-opt-sec",
                f"RTL={' '.join(rtl_existing)}",
                f"NETLIST={flat_netlist_path}",
                f"BUILD_DIR={args.output_dir}",
            ],
            cwd=REPO_ROOT,
        )
        if sec.returncode != 0:
            print("[run-all] SEC FAILED", file=sys.stderr)
            return 1
    else:
        _log(args, "[run-all] SEC skipped (no RTL files found)")

    _log(args, "[run-all] All verification gates passed")
    return 0


def cmd_cells_to_spice(args: argparse.Namespace) -> int:
    """Convert structural AION cell Verilog to gate-level SPICE netlists.

    Each generated cell module becomes one ``.subckt`` instantiating PDK gates,
    which is the input format ``aion_minimizer`` expects.
    """
    src = args.cells.read_text(encoding="utf-8")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Pin order for a SPICE subcircuit is positional, so it has to come from
    # the PDK SPICE library rather than from the Verilog.
    subckt_re = re.compile(r"^\s*\.subckt\s+(\w+)\s+(.*)$", re.MULTILINE)
    pin_order: dict[str, list[str]] = {}
    for cell, pins in subckt_re.findall(args.gates.read_text(encoding="utf-8")):
        pin_order.setdefault(cell, pins.split())

    prefix = re.escape(args.cell_prefix)
    module_re = re.compile(
        rf"module\s+({prefix}\w+)\s*\(([^)]*)\)\s*;(.*?)endmodule", re.S
    )
    inst_re = re.compile(r"(\w+)\s+(\w+)\s*\((.*?)\)\s*;", re.S)
    conn_re = re.compile(r"\.(\w+)\s*\(\s*(\w+)\s*\)")
    assign_re = re.compile(r"assign\s+(\w+)\s*=\s*~\s*(\w+)\s*;")

    found = 0
    for match in module_re.finditer(src):
        name = match.group(1)
        ports = [p.strip() for p in match.group(2).split(",") if p.strip()]
        body = match.group(3)

        # A cell that takes a complemented input reads it through
        # ``assign I1_int = ~I1_bar;``.  SPICE has no continuous assignment, and
        # the gate-level view the minimizer wants is the one *before* that
        # rewiring: ``~I1_bar`` is ``I1``, so route the wire straight back to
        # the plain port.  The ``I1_bar`` port stays in the pin list, which is
        # how the minimizer knows the complement is supplied from outside.
        alias: dict[str, str] = {}
        for wire, source in assign_re.findall(body):
            base = source[: -len(COMPLEMENT_SUFFIX)]
            if source.endswith(COMPLEMENT_SUFFIX) and base in ports:
                alias[wire] = base
            else:
                print(
                    f"[cells-to-spice] Warning: {name} assigns {wire} from "
                    f"{source}, which is not a complemented port; skipping cell",
                    file=sys.stderr,
                )
                alias = {}
                break

        lines = [f".subckt {name} {' '.join(ports)} {args.vdd} {args.vss}"]
        for inst in inst_re.finditer(body):
            cell, iname = inst.group(1), inst.group(2)
            pins = pin_order.get(cell)
            if not pins:
                print(
                    f"[cells-to-spice] Warning: no pin order for {cell} in "
                    f"{args.gates}; skipping instance {iname} of {name}",
                    file=sys.stderr,
                )
                continue
            conns = {
                pin: alias.get(net, net)
                for pin, net in conn_re.findall(inst.group(3))
            }
            mapped: list[str] = []
            for pin in pins:
                if pin in conns:
                    mapped.append(conns[pin])
                elif pin in (args.vdd, args.vss):
                    mapped.append(pin)
                else:
                    raise RuntimeError(
                        f"{name}: instance {iname} of {cell} missing pin {pin}"
                    )
            lines.append(f"X{iname} {' '.join(mapped)} {cell}")
        lines.append(".ends")

        out_path = args.output_dir / f"{name}.spice"
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _log(args, f"[cells-to-spice] Wrote {out_path}")
        found += 1

    _log(
        args,
        f"[cells-to-spice] Converted {found} cell module(s) to {args.output_dir}",
    )
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aion_opt",
        description="Graph-based netlist optimizer for Tiny Tapeout designs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- graph2verilog ------------------------------------------------------
    g2v = subparsers.add_parser(
        "graph2verilog", help="Read a netlist, build the graph, emit Verilog."
    )
    _add_common_args(g2v)
    g2v.add_argument(
        "--output", type=Path, required=True, help="Output Verilog netlist path."
    )
    g2v.set_defaults(func=cmd_graph2verilog)

    # -- generate-cells -----------------------------------------------------
    gen = subparsers.add_parser(
        "generate-cells", help="Mine patterns and generate AION cells."
    )
    _add_common_args(gen)
    _add_mining_args(gen)
    _add_elite_args(gen)
    gen.add_argument(
        "--output-cells",
        type=Path,
        required=True,
        help="Output path for the generated cell-library Verilog.",
    )
    gen.add_argument(
        "--output-elite-cells",
        type=Path,
        default=None,
        help="Optional output path for the elite (best --elite-count) cell library.",
    )
    gen.add_argument(
        "--output-report",
        type=Path,
        required=True,
        help="Output path for the pattern report (JSON).",
    )
    gen.add_argument(
        "--selection",
        type=Path,
        default=None,
        help=f"Path of the selection cache (default: <work-dir>/{SELECTION_FILENAME}). "
        "`rewrite` reuses it instead of mining a second time.",
    )
    gen.add_argument(
        "--complement-plan",
        type=Path,
        default=None,
        help="Plan written by `complement-plan`. Cells named in it take the "
        "complement of the listed inputs on a <port>_bar port instead of "
        "building an inverter internally.",
    )
    gen.set_defaults(func=cmd_generate_cells)

    # -- complement-plan ----------------------------------------------------
    comp = subparsers.add_parser(
        "complement-plan",
        help="Decide which complemented cell inputs are cheaper supplied from "
        "outside the cell.",
    )
    _add_common_args(comp)
    _add_mining_args(comp)
    comp.add_argument(
        "--cells",
        type=Path,
        required=True,
        help="AION cell library naming the modules to analyse.",
    )
    comp.add_argument(
        "--interfaces",
        type=Path,
        nargs="*",
        default=[],
        help="`aion_minimizer --report` JSON files, or directories of them. "
        "Restricts the analysis to inputs the transistor implementation "
        "actually needs complemented; without them every input is costed and "
        "nothing is externalized.",
    )
    comp.add_argument(
        "--output-plan",
        type=Path,
        required=True,
        help="Output path for the complement plan JSON.",
    )
    comp.add_argument(
        "--selection",
        type=Path,
        default=None,
        help=f"Selection cache written by generate-cells (default: "
        f"<work-dir>/{SELECTION_FILENAME}).",
    )
    comp.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore the selection cache and always re-mine.",
    )
    comp.set_defaults(func=cmd_complement_plan)

    # -- select-elite -------------------------------------------------------
    elite = subparsers.add_parser(
        "select-elite",
        help="Cut an existing cell library down to its best-ranked cells.",
    )
    elite.add_argument(
        "--cells", type=Path, required=True, help="Input AION cell library Verilog."
    )
    elite.add_argument(
        "--pattern-report",
        type=Path,
        required=True,
        help="Pattern report JSON produced by generate-cells.",
    )
    elite.add_argument(
        "--output-cells",
        type=Path,
        required=True,
        help="Output path for the elite cell library.",
    )
    _add_elite_args(elite)
    elite.add_argument("--quiet", action="store_true", help="Suppress progress output.")
    elite.set_defaults(func=cmd_select_elite)

    # -- rewrite ------------------------------------------------------------
    rew = subparsers.add_parser(
        "rewrite", help="Rewrite the netlist using a cell library."
    )
    _add_common_args(rew)
    _add_mining_args(rew)
    rew.add_argument(
        "--cells",
        type=Path,
        required=True,
        help="Input AION cell library Verilog. Only cells present in this file "
        "are substituted; the file itself is never modified.",
    )
    rew.add_argument(
        "--output-netlist",
        type=Path,
        required=True,
        help="Output path for the optimized hierarchical netlist.",
    )
    rew.add_argument(
        "--output-flat-netlist",
        type=Path,
        default=None,
        help="Optional output path for a flattened netlist of PDK cells only.",
    )
    rew.add_argument(
        "--output-report",
        type=Path,
        required=True,
        help="Report output prefix (.json / .md / .html are appended).",
    )
    rew.add_argument(
        "--selection",
        type=Path,
        default=None,
        help=f"Selection cache written by generate-cells (default: "
        f"<work-dir>/{SELECTION_FILENAME}). Reused when it matches the inputs "
        "and parameters, avoiding a second mining pass.",
    )
    rew.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore the selection cache and always re-mine.",
    )
    rew.set_defaults(func=cmd_rewrite)

    # -- run-all ------------------------------------------------------------
    allp = subparsers.add_parser("run-all", help="Run every step end-to-end.")
    _add_common_args(allp)
    _add_mining_args(allp)
    _add_elite_args(allp)
    allp.add_argument(
        "--output-dir", type=Path, default=Path("out"), help="Directory for all outputs."
    )
    allp.add_argument(
        "--rtl",
        type=Path,
        nargs="+",
        default=[],
        help="RTL Verilog file(s) used for SEC. SEC is skipped when none exist.",
    )
    allp.add_argument(
        "--complement-plan",
        type=Path,
        default=None,
        help="Plan written by `complement-plan`; see generate-cells.",
    )
    allp.set_defaults(func=cmd_run_all)

    # -- cells-to-spice -----------------------------------------------------
    c2s = subparsers.add_parser(
        "cells-to-spice",
        help="Convert generated AION cells to gate-level SPICE netlists.",
    )
    c2s.add_argument(
        "--cells", type=Path, required=True, help="Input AION cell library Verilog."
    )
    c2s.add_argument(
        "--gates",
        type=Path,
        required=True,
        help="PDK gate-level SPICE library, used for subcircuit pin order.",
    )
    c2s.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for the generated per-cell SPICE files.",
    )
    c2s.add_argument(
        "--cell-prefix",
        type=str,
        default=DEFAULT_CELL_PREFIX,
        help="Prefix identifying the modules to convert.",
    )
    c2s.add_argument("--vdd", type=str, default="VDD", help="Supply net name.")
    c2s.add_argument("--vss", type=str, default="VSS", help="Ground net name.")
    c2s.add_argument("--quiet", action="store_true", help="Suppress progress output.")
    c2s.set_defaults(func=cmd_cells_to_spice)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Record the invoked subcommand's defaults so that --config only fills in
    # arguments the user did not set explicitly.
    args._defaults = _subcommand_defaults(parser, args.command)

    _load_config(args)

    if args.command not in ("cells-to-spice", "select-elite") and args.input is None:
        parser.error("the following arguments are required: --input")

    # An overlapping cover claims the same instance more than once, which no
    # netlist can express. Fail loudly instead of emitting a broken netlist.
    if args.command in ("rewrite", "run-all") and getattr(
        args, "allow_overlapping", False
    ):
        parser.error(
            f"--allow-overlapping cannot be used with `{args.command}`: an "
            "overlapping cover cannot be rewritten into a netlist. Use it with "
            "`generate-cells` to study the pattern statistics instead."
        )

    return args.func(args)


def _subcommand_defaults(
    parser: argparse.ArgumentParser, command: str
) -> dict[str, Any]:
    """Return ``{dest: default}`` for every argument of ``command``."""
    for action in parser._subparsers._group_actions:  # type: ignore[union-attr]
        subparser = getattr(action, "choices", {}).get(command)
        if subparser is not None:
            return {a.dest: a.default for a in subparser._actions}
    return {}
