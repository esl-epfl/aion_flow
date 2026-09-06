# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The one deterministic entry point for the flow
# ================================================================

"""``python3 -m aion_layout <command>`` -- every mechanical step, one command each.

A language model draws the cell and nothing else.  Everything after that --
build, DRC, LVS, PEX, area, characterization, comparison, export -- is
deterministic code, and this module is the only door to it.  That matters twice
over: a human can re-run the whole chain with no model in the loop, and a model
can run one step without knowing how the step works.

Three rules the rest of the flow depends on, and the reasons they exist.

**The exit status is the interface.**  ``0`` is PASS or WIN, ``1`` is FAIL or
LOSS, ``2`` is ERROR -- the step could not run at all.  A caller that reads
nothing but the number still learns the right thing, and the three are kept
distinct because "the layout is dirty" and "DRC never ran" demand opposite
responses.  Python exits ``1`` on an uncaught exception, which would read as a
clean FAIL, so :func:`main` catches everything, reports it, and exits ``2``.

**Exactly one line starts at column 0.**  That line is the verdict:
``RESULT:`` from :func:`aion_layout.steps.render_verdict`, ``COMPARE:`` from
:func:`aion_layout.compare.verdict_line`, or ``STEP: <name> OK|FAIL`` for the
steps that have no verdict of their own.  Everything else -- including tool
output, report text and file names, all of which are written by code under
test -- is indented by :func:`say`, so no quantity of hostile or accidental
content can forge a second verdict for a ``grep '^RESULT:'`` to find.

**Nothing is swallowed.**  The named module exceptions are caught, printed
indented, and turned into ``RESULT: ERROR`` and exit ``2``; anything else is
caught too, but printed with its traceback, because an unexpected exception is
a bug in this tool and hiding it behind a tidy verdict would be a lie.  Absent
evidence is never a pass: a step whose artifact does not exist on disk fails.

Every module this CLI drives is imported **lazily, inside the handler that
needs it**.  ``python3 -m aion_layout --help`` therefore still works when one
of them is mid-edit or when KLayout is not installed, which is what makes this
module usable while the rest of the package is still being written.
"""

from __future__ import annotations

import argparse
import importlib
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Tuple

#: PASS, or WIN for :func:`cmd_compare`.
EXIT_PASS = 0
#: FAIL, or LOSS for :func:`cmd_compare`.  The step ran and the answer was no.
EXIT_FAIL = 1
#: ERROR: the step could not run, so there is no answer at all.
EXIT_ERROR = 2

#: Everything that is not the verdict is printed at least this far in.
INDENT = "  "

#: Names of the module exceptions the flow raises on purpose.  Matched by name
#: *and* by defining module so that a same-named exception from a third-party
#: library cannot be mistaken for a flow error and reported without its
#: traceback.  Listing names rather than classes keeps the check from importing
#: modules that may be mid-edit, which is the whole point of the lazy imports.
_FLOW_ERROR_NAMES = frozenset(
    {
        "BaselineError",
        "CharacterizeError",
        "CompareError",
        "EvidenceError",
        "ExportError",
        "LibertyError",
        "MetricsError",
        "ResizeError",
        "ScaffoldError",
        "StepError",
        "VerificationError",
    }
)


class CliError(RuntimeError):
    """A problem this module detects itself, before any tool is started.

    Its own class rather than a reused one, so that "the netlist you named does
    not exist" is never confused with "the netlist parser rejected the file".
    """


# ---------------------------------------------------------------------------
# Printing.  say() is the only way anything but the verdict reaches stdout.
# ---------------------------------------------------------------------------


def say(text: object = "", *, indent: str = INDENT) -> None:
    """Print ``text`` with every line indented, so none can read as a verdict.

    ``splitlines`` also splits on the vertical tab and form feed that ``print``
    would otherwise pass through untouched; re-joining with real newlines means
    a control character smuggled into a report cannot start a line at column 0.
    """
    for line in (str(text).splitlines() or [""]):
        print(f"{indent}{line}".rstrip())


def verdict(line: str) -> None:
    """Print the single column-0 summary line for this command.

    Whitespace is collapsed rather than merely stripped: the cell name in a
    verdict comes from the command line, and an embedded newline in it would
    otherwise produce two column-0 lines from one call.
    """
    print(" ".join(str(line).split()))


def _step_verdict(name: str, ok: bool) -> int:
    """Emit ``STEP: <name> OK|FAIL`` and return the matching exit status."""
    verdict(f"STEP: {name} {'OK' if ok else 'FAIL'}")
    return EXIT_PASS if ok else EXIT_FAIL


def _tail(text: str, lines: int = 40) -> str:
    """Return the last ``lines`` lines -- the part of tool output that says why."""
    kept = str(text).splitlines()[-lines:]
    return "\n".join(kept)


# ---------------------------------------------------------------------------
# Lazy loading and pre-flight checks
# ---------------------------------------------------------------------------


def _load(name: str) -> Any:
    """Import ``aion_layout.<name>`` now rather than at start-up.

    A module that does not import is an ERROR naming the module, not a
    traceback out of ``argparse``: while the package is being written in
    parallel, "characterize.py is not there yet" and "your netlist is bad" must
    not look alike.
    """
    try:
        return importlib.import_module(f".{name}", __package__ or "aion_layout")
    except Exception as exc:  # noqa: BLE001 - re-raised as CliError below
        raise CliError(
            f"aion_layout.{name} could not be imported "
            f"({type(exc).__name__}: {exc})"
        ) from exc


def _need_file(path: object, what: str) -> Path:
    """Return ``path`` as a Path, or raise naming what was missing.

    Called before any container or subprocess is started so that a typo costs a
    line of output instead of a half-hour DRC run against nothing.
    """
    p = Path(str(path))
    if not p.is_file():
        raise CliError(f"{what} not found: {p}")
    return p


def _make_dir(path: object) -> Path:
    """Create and return a directory the command is about to write into."""
    p = Path(str(path))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _make_parent(path: object) -> Path:
    """Create the parent of an output file and return the file path."""
    p = Path(str(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _csv(value: Optional[str]) -> Optional[List[str]]:
    """Split ``A,B,C`` into a list, or return None so a default applies."""
    if value is None:
        return None
    items = [part.strip() for part in value.split(",") if part.strip()]
    if not items:
        raise CliError(f"empty list given: {value!r}")
    return items


def _exists(path: object) -> bool:
    """True when a tool actually left the artifact it claimed to produce."""
    try:
        return Path(str(path)).exists()
    except (TypeError, ValueError, OSError):
        return False


# ---------------------------------------------------------------------------
# Report printers.  Each one prints indented; none decides an exit status.
# ---------------------------------------------------------------------------


def _print_step(result: Any) -> None:
    """Print one :class:`aion_layout.steps.StepResult`, artifacts included."""
    say(f"{result.name}: {'ok' if result.ok else 'FAILED'}")
    if getattr(result, "detail", ""):
        say(f"  {result.detail}")
    for key, path in sorted((getattr(result, "artifacts", None) or {}).items()):
        say(f"  {key}: {path}" + ("" if _exists(path) else "   [MISSING]"))
    if not result.ok and getattr(result, "output", ""):
        say("  output (last 40 lines):")
        say(_tail(result.output), indent=INDENT + "    ")


def _print_drc(report: Any) -> None:
    """Print one :class:`aion_layout.verification.DrcReport`.

    Degradation is printed even when the report is clean, because a clean
    report of unknown extent is the failure mode this whole flow is built to
    refuse: it looks exactly like a pass.
    """
    say(
        f"{report.tool} DRC: {'clean' if report.clean else 'NOT clean'} "
        f"-- {report.error_count} violations parsed"
        + (
            f", tool reported {report.reported_count}"
            if report.reported_count is not None
            else ""
        )
    )
    if not report.available:
        say(f"  unavailable: {report.unavailable_reason or 'no report found'}")
    if report.unparsed_files:
        say(f"  unparsed report files: {report.unparsed_files}")
    if report.completeness_note:
        say(f"  completeness ({report.completeness}): {report.completeness_note}")
    if report.missing_databases:
        say(f"  missing databases: {', '.join(report.missing_databases)}")
    if report.location_note:
        say(f"  location: {report.location_note}")
    for category in list(report.categories)[:20]:
        say(f"  category: {category}")
    for violation in list(report.violations)[:20]:
        say(f"  {violation.category} {violation.bbox_str} {violation.description}")
    if report.error_count > 20:
        say(f"  ... {report.error_count - 20} further violations not listed")


def _print_lvs(report: Any) -> None:
    """Print one :class:`aion_layout.verification.LvsReport`."""
    say(
        f"{report.tool} LVS: {'clean' if report.clean else 'NOT clean'} "
        f"-- verdict {report.verdict}"
    )
    if report.message:
        say(f"  {report.message}")
    if report.device_total:
        say(f"  devices: layout {report.device_total[0]} / netlist {report.device_total[1]}")
    if report.net_counts:
        say(f"  nets:    layout {report.net_counts[0]} / netlist {report.net_counts[1]}")
    for name, (layout_n, netlist_n) in sorted(report.device_counts.items()):
        say(f"  {name}: layout {layout_n} / netlist {netlist_n}")
    for pin_a, pin_b in report.unmatched_pins[:20]:
        say(f"  unmatched pin: {pin_a} <-> {pin_b}")
    for node in report.disconnected_nodes[:20]:
        say(f"  disconnected: {node}")
    if report.location_note:
        say(f"  location: {report.location_note}")


def _print_geometry(geometry: Any, label: str = "geometry") -> None:
    """Print one :class:`aion_layout.metrics.CellGeometry` and its problems."""
    say(f"{label}: {geometry.describe()}")
    for problem in geometry.problems:
        say(f"  not row-legal: {problem}")


def _degraded_drc(*reports: Any) -> List[str]:
    """Name every DRC report that is not evidence about the layout at all.

    A report that is missing, half-parsed, of unknown extent, or read from a
    directory no tool writes says nothing about whether the layout is clean.
    That is "DRC could not run", which is ERROR; only a report that ran and
    found violations is FAIL.  :func:`aion_layout.steps.verify` grades exactly
    this evidence the same way, and the two must never disagree about the same
    GDS: a caller told FAIL goes and edits a layout that may be perfectly fine.
    """
    named: List[str] = []
    for report in reports:
        if not (getattr(report, "degraded", False) or report.location_note):
            continue
        why = (
            report.unavailable_reason
            or report.completeness_note
            or report.location_note
            or f"completeness {report.completeness}"
        )
        named.append(f"{report.tool} DRC is not evidence: {why}")
    return named


def _error_verdict(reasons: Sequence[str]) -> int:
    """Print why the step could not run, then the one ERROR verdict line."""
    for reason in reasons:
        say(reason)
    verdict("RESULT: ERROR")
    return EXIT_ERROR


def _verdict_exit(result: object) -> int:
    """Map a ``Verdict.result`` string onto this CLI's exit statuses.

    Anything that is not exactly PASS or FAIL is ERROR: an unrecognised verdict
    is a verdict nobody has graded, and the fail-closed reading of that is "the
    step did not run", not "the step passed".
    """
    text = str(result).strip().upper()
    if text == "PASS":
        return EXIT_PASS
    if text == "FAIL":
        return EXIT_FAIL
    return EXIT_ERROR


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_resize(args: argparse.Namespace) -> int:
    """Widen the series stacks of a netlist into a new, separately named cell.

    The input netlist is never touched.  A series stack is the pull-up or
    pull-down network's speed limiter, and widening it is a real design change
    -- so it produces a *different cell*, with a report saying what was changed
    and why, rather than an edit that would silently invalidate every LVS run
    made against the original.
    """
    netlist = _need_file(args.netlist, "netlist")
    out = _make_parent(args.out)
    resize = _load("resize")

    extra: dict = {}
    if args.cell:
        extra["cell"] = args.cell
    if args.new_cell:
        extra["new_cell"] = args.new_cell
    if args.baseline:
        extra["baseline"] = _need_file(args.baseline, "baseline netlist")
    if args.max_sites is not None:
        extra["max_sites"] = args.max_sites
    if args.area_budget is not None:
        extra["area_budget_um2"] = args.area_budget
    if args.min_depth is not None:
        extra["min_depth"] = args.min_depth
    if args.multiplier:
        extra["multipliers"] = args.multiplier

    plan = resize.resize(netlist, out, report=args.report, **extra)

    say(f"source:   {netlist}")
    say(f"netlist:  {out}")
    if args.report:
        say(f"report:   {args.report}")
    say(f"budget:   {plan.budget_source}")
    for device in plan.devices:
        mark = "*" if device.changed else " "
        say(
            f"  {mark} {device.name:6s} {device.network:10s} depth {device.stack_depth}  "
            f"w {device.original_w_nm:.0f} -> {device.new_w_nm:.0f} nm  "
            f"ng {device.original_ng} -> {device.new_ng}"
        )
    for note in plan.notes:
        say(f"  note: {note}")
    # A plan that changes nothing is a real answer -- "no multiplier fits the
    # area budget" is information, not a failure -- so it still exits 0.
    print(resize.summary_line(plan))
    return EXIT_PASS


def cmd_scaffold(args: argparse.Namespace) -> int:
    """Write a cell-generator skeleton for the transistors in a SPICE netlist."""
    netlist = _need_file(args.netlist, "netlist")
    out_py = _make_parent(args.out)
    scaffold = _load("scaffold")
    # The optional arguments are passed only when the user asked for them, so
    # the ordinary call stays the plain one: refusing to overwrite an existing
    # generator is the default, and --force is the only way past it.
    extra: dict = {}
    if args.force:
        extra["force"] = True
    if args.width is not None:
        extra["cell_width"] = args.width
    path = scaffold.scaffold_module(netlist, out_py, cell_name=args.cell, **extra)
    say(f"netlist:  {netlist}")
    say(f"module:   {path}")
    return _step_verdict("scaffold", _exists(path))


def cmd_build(args: argparse.Namespace) -> int:
    """Execute a cell generator and write its GDS (and optionally a PNG)."""
    module = _need_file(args.module, "cell module")
    out_gds = _make_parent(args.out)
    steps = _load("steps")

    built = steps.build_gds(module, args.cell, out_gds)
    _print_step(built)
    ok = bool(built.ok) and _exists(out_gds)
    if built.ok and not _exists(out_gds):
        say(f"  build reported success but {out_gds} does not exist")

    # A PNG that was asked for and not produced fails the command: the caller
    # asked for two artifacts and got one.
    if ok and args.png:
        png = _make_parent(args.png)
        shot = steps.render_png(out_gds, png)
        _print_step(shot)
        ok = ok and bool(shot.ok) and _exists(png)

    return _step_verdict("build", ok)


def cmd_drc(args: argparse.Namespace) -> int:
    """Run Magic and KLayout DRC on a GDS and report both."""
    gds = _need_file(args.gds, "GDS")
    work_dir = Path(args.work_dir)
    cell = args.cell or gds.stem
    steps = _load("steps")

    magic, klayout = steps.drc(gds, work_dir, cell_name=args.cell)
    say(f"cell: {cell}")
    say(f"gds:  {gds}")
    say(f"work: {work_dir}")
    _print_drc(magic)
    _print_drc(klayout)

    # Printed after the reports so a failure to enumerate the rule tables does
    # not hide the reports themselves.  This is the other half of the KLayout
    # evidence: a rule table that died contributes no items to the merge, and
    # no items is exactly what a clean layout also looks like.  So a problem
    # here fails the command even when both reports came back clean -- the same
    # grading ``steps.verify`` applies.
    tables, problems = steps.klayout_table_logs(work_dir, cell)
    say(f"klayout rule tables that ran: {tables}")
    for problem in problems:
        say(f"  problem: {problem}")

    reasons = _degraded_drc(magic, klayout)
    reasons += [
        f"klayout rule tables did not all run ({tables} log(s)): {problem}"
        for problem in problems
    ]
    if reasons:
        return _error_verdict(reasons)
    return _step_verdict("drc", bool(magic.clean and klayout.clean))


def cmd_lvs(args: argparse.Namespace) -> int:
    """Run Magic extraction plus Netgen LVS against a SPICE netlist."""
    gds = _need_file(args.gds, "GDS")
    netlist = _need_file(args.netlist, "netlist")
    work_dir = Path(args.work_dir)
    steps = _load("steps")

    report = steps.lvs(gds, netlist, args.cell, work_dir)
    say(f"cell:    {args.cell}")
    say(f"gds:     {gds}")
    say(f"netlist: {netlist}")
    say(f"work:    {work_dir}")
    _print_lvs(report)

    # Netgen that never printed a final result, or a result read from a path
    # Netgen does not write, has not compared anything -- ERROR, not FAIL.
    reasons: List[str] = []
    if report.location_note:
        reasons.append(f"LVS report is not where netgen writes it: {report.location_note}")
    if report.verdict in ("no_final_result", "uncertain"):
        reasons.append(f"LVS produced no usable verdict ({report.verdict}): {report.message}")
    if reasons:
        return _error_verdict(reasons)
    return _step_verdict("lvs", bool(report.clean))


def cmd_verify(args: argparse.Namespace) -> int:
    """Build the cell, run DRC and LVS, and print the graded verdict."""
    module = _need_file(args.module, "cell module")
    netlist = _need_file(args.netlist, "netlist")
    work_dir = _make_dir(args.work_dir or Path("build") / args.cell)
    steps = _load("steps")

    graded = steps.verify(
        module, args.cell, netlist, work_dir, skip_build=args.skip_build
    )
    if args.report:
        path = steps.write_report(graded, _make_parent(args.report))
        say(f"report: {path}")

    # render_verdict ends in exactly one column-0 ``RESULT:`` line and indents
    # everything above it, so it is printed as it stands and printed last:
    # nothing may follow the verdict.
    print(steps.render_verdict(graded))
    return _verdict_exit(graded.result)


def cmd_pex(args: argparse.Namespace) -> int:
    """Extract a parasitic netlist from a GDS with Magic."""
    gds = _need_file(args.gds, "GDS")
    work_dir = _make_dir(args.work_dir)
    characterize = _load("characterize")

    pex = characterize.run_pex(gds, args.cell, work_dir, mode=args.mode)
    say(f"cell: {args.cell}")
    say(f"mode: {args.mode}")
    say(f"pex:  {pex}")
    if not _exists(pex):
        say("  the extractor returned a path that does not exist")
    return _step_verdict("pex", _exists(pex))


def cmd_evidence(args: argparse.Namespace) -> int:
    """Assemble the evidence packet a model needs to fix or write a cell."""
    netlist = _need_file(args.netlist, "netlist")
    gds = _need_file(args.gds, "GDS") if args.gds else None
    module = _need_file(args.module, "cell module") if args.module else None
    evidence = _load("evidence")

    packet = evidence.build_evidence(
        cell=args.cell,
        netlist=netlist,
        gds=gds,
        module=module,
        reference_cell=args.reference_cell,
    )
    text = packet.render(max_bytes=args.max_bytes)
    if args.out:
        out = _make_parent(args.out)
        out.write_text(text)
        say(f"evidence: {out} ({len(text.encode('utf-8'))} bytes)")
    else:
        # Indented on stdout, because evidence text is assembled from tool
        # output and could otherwise contain a line reading ``RESULT: PASS``.
        # ``-o`` writes the file verbatim; that is the copy to feed a model.
        say(text)
    return _step_verdict("evidence", bool(text.strip()))


def cmd_baseline(args: argparse.Namespace) -> int:
    """Build the same logic by abutting the PDK cells it replaces.

    Every stage the caller asked for runs even after one of them fails, and the
    verdict is their conjunction.  Unlike ``flow``, this command is what
    somebody runs while fixing the baseline, and they want the whole list of
    complaints from one run rather than the first one in execution order.
    """
    gate_netlist = _need_file(args.gate_netlist, "gate-level netlist")
    out_dir = _make_dir(args.out)
    baseline = _load("baseline")
    #: Reasons the baseline could not be judged at all, as opposed to judged
    #: and found wanting.  Any one of them makes the command ERROR, not FAIL.
    errors: List[str] = []

    name, ports, instances = baseline.parse_gate_netlist(
        gate_netlist, cell_name=args.cell
    )
    say(f"baseline cell: {name}")
    say(f"ports:         {', '.join(ports)}")
    for inst in instances:
        say(f"  {inst.name}: {inst.cell}")

    out_gds = out_dir / f"{name}.gds"
    result = baseline.build_abutted_layout(gate_netlist, out_gds, cell_name=args.cell)
    say(f"gds: {result.gds}")
    _print_geometry(result.geometry, "baseline geometry")
    for note in result.notes:
        say(f"  note: {note}")
    say(f"routed nets:   {', '.join(result.routed_nets) or '(none)'}")
    ok = _exists(result.gds) and not result.geometry.problems
    if result.unrouted_nets:
        # An unrouted net is not a warning: the baseline would lose the
        # comparison for a reason that is this tool's fault, not the layout's.
        say(f"  UNROUTED nets: {', '.join(result.unrouted_nets)}")
        ok = False

    lvs_netlist = result.lvs_netlist
    if not lvs_netlist or not _exists(lvs_netlist):
        lvs_netlist = baseline.write_lvs_netlist(
            gate_netlist, out_dir / f"{name}.lvs.spice"
        )
    say(f"lvs netlist: {lvs_netlist}")

    if args.verify:
        steps = _load("steps")
        magic, klayout = steps.drc(result.gds, out_dir / "drc", cell_name=name)
        _print_drc(magic)
        _print_drc(klayout)
        lvs = steps.lvs(result.gds, lvs_netlist, name, out_dir / "lvs")
        _print_lvs(lvs)
        # Collected rather than returned on: this command is the one somebody
        # runs while fixing the baseline, and they want every complaint from
        # one run.  The distinction is kept for the verdict at the end.
        errors += _degraded_drc(magic, klayout)
        if lvs.verdict in ("no_final_result", "uncertain"):
            errors.append(
                f"baseline LVS produced no usable verdict ({lvs.verdict}): "
                f"{lvs.message}"
            )
        ok = ok and bool(magic.clean and klayout.clean and lvs.clean)

    pex = None
    if args.pex or args.characterize:
        characterize = _load("characterize")
        pex = characterize.run_pex(result.gds, name, out_dir / "pex")
        say(f"pex: {pex}")
        ok = ok and _exists(pex)

    if args.characterize:
        characterize = _load("characterize")
        if pex is None or not _exists(pex):
            raise CliError("cannot characterize the baseline without a PEX netlist")
        char = characterize.characterize(
            pex,
            name,
            out_dir / "char",
            area_um2=result.geometry.area_um2,
        )
        ok = _print_char(char) and ok

    if errors:
        return _error_verdict(errors)
    return _step_verdict("baseline", ok)


def _print_char(result: Any) -> bool:
    """Print a :class:`aion_layout.characterize.CharResult`; True if usable.

    "Usable" means every Liberty file it named is on disk.  A characterizer
    that reports success and writes nothing must not feed a comparison.
    """
    say(f"characterized {result.cell} from {result.spice_used}")
    say(f"  area: {result.area_um2} um^2")
    say(f"  corners: {', '.join(c.name for c in result.corners)}")
    ok = bool(result.lib_files)
    if not ok:
        say("  no Liberty files were produced")
    for lib in result.lib_files:
        present = _exists(lib)
        say(f"  lib: {lib}" + ("" if present else "   [MISSING]"))
        ok = ok and present
    if result.report:
        say(f"  report: {result.report}")
    return ok


def _parse_corner(spec: str, corner_cls: Any) -> Any:
    """Parse a ``name:section:vdd:temp`` corner given on the command line."""
    parts = spec.split(":")
    if len(parts) != 4:
        raise CliError(
            f"corner {spec!r} is not NAME:SECTION:VDD:TEMP (e.g. typ:mos_tt:1.2:25)"
        )
    name, section, vdd, temp = (p.strip() for p in parts)
    try:
        return corner_cls(name=name, section=section, vdd=float(vdd), temp=float(temp))
    except ValueError as exc:
        raise CliError(f"corner {spec!r} has a non-numeric VDD or TEMP: {exc}") from exc


def cmd_characterize(args: argparse.Namespace) -> int:
    """Run SPICE over the corners and write Liberty for the cell."""
    spice = _need_file(args.spice, "SPICE netlist")
    out_dir = _make_dir(args.out)
    area_lef = _need_file(args.area_lef, "area LEF") if args.area_lef else None
    characterize = _load("characterize")

    # The Liberty ``area`` is the placement footprint, and characterize refuses
    # to invent one -- a cell published with area 0 is a cell the resizer thinks
    # is free.  --area-gds measures it here rather than making the caller shell
    # out to metrics, and refuses the bbox fallback for the reason in
    # :func:`_geometry_of`: a shape bbox is not a placement area.
    area_um2 = args.area
    if area_um2 is None and area_lef is None and args.area_gds:
        gds = _need_file(args.area_gds, "area GDS")
        geometry = _load("metrics").gds_boundary(
            gds, args.cell, allow_bbox_fallback=False
        )
        _print_geometry(geometry, "area")
        area_um2 = geometry.area_um2

    corners = (
        tuple(_parse_corner(spec, characterize.Corner) for spec in args.corner)
        if args.corner
        else characterize.DEFAULT_CORNERS
    )
    result = characterize.characterize(
        spice,
        args.cell,
        out_dir,
        inputs=_csv(args.inputs),
        outputs=_csv(args.outputs),
        area_um2=area_um2,
        area_lef=area_lef,
        corners=corners,
        jobs=args.jobs,
        verify=not args.no_verify,
    )
    return _step_verdict("characterize", _print_char(result))


def _geometry_of(
    metrics: Any, gds: Path, lef: Optional[Path], cell: str, label: str
) -> Any:
    """Measure the placement footprint of one side of the comparison.

    The bounding-box fallback is refused here.  A shape bbox and a prBoundary
    measure different things, and comparing one against the other would decide
    the whole "is it smaller" question on which artifact happened to carry a
    boundary -- so a missing boundary is an ERROR, not a smaller number.
    """
    if lef is not None:
        return metrics.lef_macro_geometry(lef, cell)
    geometry = metrics.gds_boundary(gds, cell, allow_bbox_fallback=False)
    say(f"{label} measured from {geometry.source}")
    return geometry


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare the AION cell against the abutted PDK baseline: area and delay."""
    candidate_gds = _need_file(args.candidate_gds, "candidate GDS")
    baseline_gds = _need_file(args.baseline_gds, "baseline GDS")
    candidate_lib = _need_file(args.candidate_lib, "candidate Liberty")
    baseline_lib = _need_file(args.baseline_lib, "baseline Liberty")
    candidate_lef = (
        _need_file(args.candidate_lef, "candidate LEF") if args.candidate_lef else None
    )
    baseline_lef = (
        _need_file(args.baseline_lef, "baseline LEF") if args.baseline_lef else None
    )
    metrics = _load("metrics")
    compare_mod = _load("compare")

    candidate_geometry = _geometry_of(
        metrics, candidate_gds, candidate_lef, args.cell, "candidate"
    )
    baseline_geometry = _geometry_of(
        metrics, baseline_gds, baseline_lef, args.baseline_cell, "baseline"
    )
    _print_geometry(candidate_geometry, "candidate")
    _print_geometry(baseline_geometry, "baseline")

    comparison = compare_mod.compare(
        cell=args.cell,
        baseline_cell=args.baseline_cell,
        candidate_lib=candidate_lib,
        baseline_lib=baseline_lib,
        candidate_geometry=candidate_geometry,
        baseline_geometry=baseline_geometry,
        corner=args.corner,
    )

    if args.markdown:
        path = _make_parent(args.markdown)
        path.write_text(compare_mod.render_markdown(comparison))
        say(f"markdown: {path}")
    if args.json:
        path = _make_parent(args.json)
        path.write_text(compare_mod.render_json(comparison))
        say(f"json:     {path}")

    # Indented: render_markdown has headings at column 0 by design.
    say(compare_mod.render_markdown(comparison))

    # The exit status is derived from the very line that is printed, so the
    # number and the text can never disagree about who won.
    line = " ".join(compare_mod.verdict_line(comparison).split())
    verdict(line)
    return EXIT_PASS if line.startswith("COMPARE: WIN") else EXIT_FAIL


def _directions_from_spice(spice: Path, cell: str) -> dict[str, str]:
    """Read each port's direction out of the transistor netlist.

    Magic writes no ``DIRECTION`` into a LEF, and a LEF pin without one is read
    as an INPUT -- so an exported cell's *output* pin arrives at the placer
    typed as an input, and the Verilog stub types every signal ``inout``.  The
    netlist already knows: a port that only ever appears on a gate terminal is
    an input, and the port the devices drive is the output.

    Returns an empty map rather than raising when the netlist cannot be read
    that way.  A missing direction is what the exporter already handles (it
    says so in a note); a wrong one would be worse than none.
    """
    try:
        parser = _load("spice_parser")
        subckts = parser.parse_spice_file(spice)
    except Exception:
        return {}
    subckt = next((s for s in subckts if s.name == cell), None)
    if subckt is None:
        return {}
    directions: dict[str, str] = {}
    try:
        for net in subckt.input_nets:
            directions[net] = "input"
        out = subckt.output_net
        if out:
            directions[out] = "output"
        # Supplies are inout however they are used; the exporter's USE
        # POWER/GROUND already covers the LEF side, and the Verilog stub needs
        # them spelled out.
        for supply in (subckt.vdd_net, subckt.vss_net):
            if supply:
                directions[supply] = "inout"
        return {pin: directions[pin] for pin in subckt.pins if pin in directions}
    except Exception:
        return {}


def cmd_export(args: argparse.Namespace) -> int:
    """Write the gds/lef/lib/v/spice/cdl views ``make pnr`` consumes."""
    gds = _need_file(args.gds, "GDS")
    spice = _need_file(args.spice, "SPICE netlist")
    libs = [_need_file(lib, "Liberty") for lib in args.lib]
    pex_spice = _need_file(args.pex_spice, "PEX netlist") if args.pex_spice else None
    out_dir = _make_dir(args.out)
    exporters = _load("exporters")

    views = exporters.export_all(
        cell=args.cell,
        gds=gds,
        spice_netlist=spice,
        lib_files=libs,
        out_dir=out_dir,
        pex_spice=pex_spice,
        directions=_directions_from_spice(spice, args.cell),
    )
    return _step_verdict("export", _print_views(views))


def _print_views(views: Any) -> bool:
    """Print an :class:`aion_layout.exporters.ExportedViews`; True if complete.

    Every view is checked on disk rather than trusted from the return value,
    and the LEF check decides the verdict: a LEF that breaks CLASS, SITE, the
    row height or the site pitch stops ``make pnr`` before placement, so a cell
    that exports one has not been exported successfully.
    """
    ok = True
    for name in ("gds", "lef", "lib", "verilog", "spice", "cdl"):
        value = getattr(views, name, None)
        paths = value if isinstance(value, (list, tuple)) else [value]
        for path in paths:
            if path is None:
                say(f"{name}: (not written)")
                ok = False
                continue
            present = _exists(path)
            say(f"{name}: {path}" + ("" if present else "   [MISSING]"))
            ok = ok and present
    check = views.lef_check
    say(f"lef check: {'ok' if check.ok else 'FAILED'}")
    say(f"  class {check.cell_class}, site {check.site}")
    # A check that failed before it could measure anything still has to print;
    # crashing here would replace a readable FAIL with an unexplained ERROR.
    if check.geometry is None:
        say("  lef geometry: not measured")
    else:
        _print_geometry(check.geometry, "  lef geometry")
    say(f"  pins: {', '.join(check.pins or ()) or '(none)'}")
    for problem in check.problems:
        say(f"  problem: {problem}")
    return ok and bool(check.ok)


def _flow_stop(kind: str) -> int:
    """End the chain early, keeping FAIL and ERROR apart.

    ``flow`` runs stages whose own verdicts are graded differently -- a dirty
    DRC is a FAIL, a DRC that never ran is an ERROR -- and collapsing the two
    into one status would tell a caller to fix a layout when the real problem
    is that the container is not running.
    """
    if kind == "error":
        verdict("RESULT: ERROR")
        return EXIT_ERROR
    return _step_verdict("flow", False)


def _flow_corners(mode: str, characterize: Any) -> Tuple[Any, ...]:
    """Return the corner set ``flow`` characterizes over."""
    if mode == "all":
        return tuple(characterize.DEFAULT_CORNERS)
    picked = tuple(c for c in characterize.DEFAULT_CORNERS if c.name == "typ")
    if not picked:
        raise CliError("characterize.DEFAULT_CORNERS has no corner named 'typ'")
    return picked


def cmd_flow(args: argparse.Namespace) -> int:
    """Run the whole mechanical chain in order and stop at the first failure.

    verify -> pex -> baseline (build, DRC, LVS, pex) -> characterize both ->
    compare -> export.  Every stage prints indented, so the chain still ends in
    exactly one column-0 line: the ``COMPARE:`` verdict when it completed,
    ``STEP: flow FAIL`` when a stage failed, ``RESULT: ERROR`` when one could
    not run.
    """
    netlist = _need_file(args.netlist, "netlist")
    module = _need_file(args.module, "cell module")
    gate_netlist = (
        None if args.skip_baseline else _need_file(args.baseline, "baseline netlist")
    )
    build_dir = _make_dir(args.out or Path("build") / args.cell)

    steps = _load("steps")
    metrics = _load("metrics")
    characterize = _load("characterize")
    corners = _flow_corners(args.corners, characterize)

    stages = 4 if args.skip_baseline else 7
    step = 0

    def stage(title: str) -> None:
        nonlocal step
        step += 1
        say("")
        say(f"[{step}/{stages}] {title}")

    # 1 -- build and grade the candidate.  Built explicitly so that the rest of
    # the chain knows the GDS path without having to guess where verify put it.
    stage("build + DRC + LVS (candidate)")
    candidate_gds = build_dir / f"{args.cell}.gds"
    built = steps.build_gds(module, args.cell, candidate_gds)
    _print_step(built)
    candidate_gds = Path(str((built.artifacts or {}).get("gds", candidate_gds)))
    if not built.ok or not _exists(candidate_gds):
        return _flow_stop("error")

    graded = steps.verify(
        module, args.cell, netlist, build_dir, skip_build=True
    )
    say(steps.render_verdict(graded))
    steps.write_report(graded, build_dir / f"{args.cell}.report.md")
    if not graded.passed:
        # The verdict already distinguishes "the layout is wrong" from "the
        # checker never ran"; the chain must not throw that distinction away.
        return _flow_stop(
            "fail" if _verdict_exit(graded.result) == EXIT_FAIL else "error"
        )

    candidate_geometry = metrics.gds_boundary(
        candidate_gds, args.cell, allow_bbox_fallback=False
    )
    _print_geometry(candidate_geometry, "candidate")

    # 2 -- parasitics for the candidate.
    stage("PEX (candidate)")
    candidate_pex = characterize.run_pex(candidate_gds, args.cell, build_dir / "pex")
    say(f"pex: {candidate_pex}")
    if not _exists(candidate_pex):
        return _flow_stop("error")

    baseline_cell = None
    baseline_gds = None
    baseline_geometry = None
    baseline_pex = None
    if not args.skip_baseline:
        # 3 -- the thing the candidate has to beat.
        stage("baseline: abut the PDK cells, then DRC + LVS + PEX")
        baseline = _load("baseline")
        base_dir = _make_dir(build_dir / "baseline")
        baseline_cell, _ports, _instances = baseline.parse_gate_netlist(gate_netlist)
        result = baseline.build_abutted_layout(
            gate_netlist, base_dir / f"{baseline_cell}.gds"
        )
        baseline_cell = result.cell
        baseline_gds = Path(str(result.gds))
        baseline_geometry = result.geometry
        _print_geometry(baseline_geometry, "baseline")
        if result.unrouted_nets:
            say(f"  UNROUTED nets: {', '.join(result.unrouted_nets)}")
            return _flow_stop("fail")

        base_lvs_netlist = result.lvs_netlist
        if not base_lvs_netlist or not _exists(base_lvs_netlist):
            base_lvs_netlist = baseline.write_lvs_netlist(
                gate_netlist, base_dir / f"{baseline_cell}.lvs.spice"
            )
        magic, klayout = steps.drc(baseline_gds, base_dir / "drc", cell_name=baseline_cell)
        _print_drc(magic)
        _print_drc(klayout)
        lvs = steps.lvs(baseline_gds, base_lvs_netlist, baseline_cell, base_dir / "lvs")
        _print_lvs(lvs)
        degraded = _degraded_drc(magic, klayout)
        if lvs.verdict in ("no_final_result", "uncertain"):
            degraded.append(
                f"baseline LVS produced no usable verdict ({lvs.verdict})"
            )
        if degraded:
            return _error_verdict(degraded)
        if not (magic.clean and klayout.clean and lvs.clean):
            return _flow_stop("fail")

        baseline_pex = characterize.run_pex(
            baseline_gds, baseline_cell, base_dir / "pex"
        )
        say(f"pex: {baseline_pex}")
        if not _exists(baseline_pex):
            return _flow_stop("error")

    # 4 -- characterize the candidate.
    stage("characterize (candidate)")
    candidate_char = characterize.characterize(
        candidate_pex,
        args.cell,
        build_dir / "char",
        area_um2=candidate_geometry.area_um2,
        corners=corners,
        jobs=args.jobs,
    )
    if not _print_char(candidate_char):
        return _flow_stop("error")

    baseline_char = None
    if not args.skip_baseline:
        # 5 -- and the baseline, over the same corners with the same tool.
        stage("characterize (baseline)")
        baseline_char = characterize.characterize(
            baseline_pex,
            baseline_cell,
            build_dir / "baseline" / "char",
            area_um2=baseline_geometry.area_um2,
            corners=corners,
            jobs=args.jobs,
        )
        if not _print_char(baseline_char):
            return _flow_stop("error")

    # 6 -- export the views before comparing, so the artifacts exist even if
    # the candidate loses; a losing cell is still a cell someone may want.
    stage("export views")
    exporters = _load("exporters")
    final_dir = _make_dir(build_dir / "final")
    views = exporters.export_all(
        cell=args.cell,
        gds=candidate_gds,
        spice_netlist=netlist,
        lib_files=list(candidate_char.lib_files),
        out_dir=final_dir,
        pex_spice=candidate_pex,
        directions=_directions_from_spice(netlist, args.cell),
    )
    if not _print_views(views):
        # A rejected LEF is a property of the cell, not of the toolchain: the
        # placer would refuse this cell, and that is a FAIL.
        return _flow_stop("fail")

    if args.skip_baseline:
        return _step_verdict("flow", True)

    # 7 -- the question the whole tool exists to answer.
    stage("compare against the abutted baseline")
    compare_mod = _load("compare")
    comparison = compare_mod.compare(
        cell=args.cell,
        baseline_cell=baseline_cell,
        candidate_lib=candidate_char.lib_files[0],
        baseline_lib=baseline_char.lib_files[0],
        candidate_geometry=candidate_geometry,
        baseline_geometry=baseline_geometry,
        corner="typ",
    )
    markdown = build_dir / f"{args.cell}.compare.md"
    markdown.write_text(compare_mod.render_markdown(comparison))
    (build_dir / f"{args.cell}.compare.json").write_text(
        compare_mod.render_json(comparison)
    )
    say(compare_mod.render_markdown(comparison))
    say(f"markdown: {markdown}")

    line = " ".join(compare_mod.verdict_line(comparison).split())
    verdict(line)
    return EXIT_PASS if line.startswith("COMPARE: WIN") else EXIT_FAIL


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the whole command line.  One subparser per command, no shortcuts."""
    parser = argparse.ArgumentParser(
        prog="python3 -m aion_layout",
        description=(
            "Deterministic entry point for the AION standard-cell flow. "
            "Exit status: 0 PASS/WIN, 1 FAIL/LOSS, 2 ERROR (the step could not "
            "run). Every command prints exactly one line starting at column 0; "
            "that line is the verdict."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # -- resize ------------------------------------------------------------
    p = subparsers.add_parser(
        "resize",
        help="widen series stacks into a new netlist, capped by an area budget",
        description=(
            "Widen the devices in a series stack and fold them into fingers, "
            "writing a NEW netlist beside the original. The input is never "
            "edited: resizing produces a differently named cell so that every "
            "LVS run stays honest about which netlist it verified."
        ),
    )
    p.add_argument("netlist", help="transistor-level SPICE netlist to resize")
    p.add_argument("-o", "--out", required=True, help="output SPICE netlist")
    p.add_argument("--cell", help="subcircuit to resize (default: the first)")
    p.add_argument("--new-cell", help="name for the resized cell (default: <cell>s)")
    p.add_argument(
        "--baseline",
        help="gate-level netlist whose abutted PDK row sets the area budget",
    )
    p.add_argument("--max-sites", type=int, help="area budget as a site count")
    p.add_argument("--area-budget", type=float, help="area budget in um^2")
    p.add_argument(
        "--min-depth",
        type=int,
        help="leave stacks this deep and shallower alone (default: 2)",
    )
    p.add_argument(
        "--multiplier",
        type=float,
        action="append",
        help="candidate width multiplier, largest tried first; repeat",
    )
    p.add_argument("--report", help="write the markdown resize report here")
    p.set_defaults(handler=cmd_resize)

    # -- scaffold ----------------------------------------------------------
    p = subparsers.add_parser(
        "scaffold",
        help="write a cell-generator skeleton from a transistor-level netlist",
        description="Write a cell-generator skeleton from a SPICE .subckt.",
    )
    p.add_argument("netlist", help="transistor-level SPICE netlist")
    p.add_argument("-o", "--out", required=True, help="output Python module")
    p.add_argument("--cell", help="subcircuit to scaffold (default: the first)")
    p.add_argument(
        "--width", type=float, help="cell width in NANOMETRES, a multiple of 480 (default: from the netlist)"
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing module, discarding whatever is in it",
    )
    p.set_defaults(handler=cmd_scaffold)

    # -- build -------------------------------------------------------------
    p = subparsers.add_parser(
        "build",
        help="run a cell generator and write its GDS",
        description="Execute a cell generator module and stream out its GDS.",
    )
    p.add_argument("module", help="cell generator module, e.g. cells/<cell>.py")
    p.add_argument("--cell", required=True, help="cell name the generator produces")
    p.add_argument("-o", "--out", required=True, help="output GDS path")
    p.add_argument("--png", help="also render the layout to this PNG")
    p.set_defaults(handler=cmd_build)

    # -- drc ---------------------------------------------------------------
    p = subparsers.add_parser(
        "drc",
        help="run Magic and KLayout DRC on a GDS",
        description="Run both DRC engines and report each; clean means both.",
    )
    p.add_argument("gds", help="GDS to check")
    p.add_argument("-w", "--work-dir", required=True, help="directory for the reports")
    p.add_argument("--cell", help="cell to check (default: the GDS file stem)")
    p.set_defaults(handler=cmd_drc)

    # -- lvs ---------------------------------------------------------------
    p = subparsers.add_parser(
        "lvs",
        help="run Magic extraction plus Netgen LVS",
        description="Compare the layout against the SPICE netlist it implements.",
    )
    p.add_argument("gds", help="GDS to extract")
    p.add_argument("netlist", help="SPICE netlist to compare against")
    p.add_argument("--cell", required=True, help="cell name in both views")
    p.add_argument("-w", "--work-dir", required=True, help="directory for the reports")
    p.set_defaults(handler=cmd_lvs)

    # -- verify ------------------------------------------------------------
    p = subparsers.add_parser(
        "verify",
        help="build, DRC, LVS and print the graded verdict",
        description=(
            "Build the cell then run both DRC engines and LVS, and print the "
            "graded verdict. Ends in one RESULT: PASS|FAIL|ERROR line."
        ),
    )
    p.add_argument("module", help="cell generator module")
    p.add_argument("--cell", required=True, help="cell name")
    p.add_argument("--netlist", required=True, help="transistor-level SPICE netlist")
    p.add_argument(
        "-w", "--work-dir", help="working directory (default: build/<cell>)"
    )
    p.add_argument(
        "--skip-build",
        action="store_true",
        help="grade the GDS already in the working directory",
    )
    p.add_argument("--report", help="also write the verdict report to this file")
    p.set_defaults(handler=cmd_verify)

    # -- pex ---------------------------------------------------------------
    p = subparsers.add_parser(
        "pex",
        help="extract a parasitic netlist from a GDS",
        description="Run Magic parasitic extraction and report the netlist path.",
    )
    p.add_argument("gds", help="GDS to extract")
    p.add_argument("--cell", required=True, help="cell name")
    p.add_argument("-w", "--work-dir", required=True, help="extraction directory")
    p.add_argument(
        "--mode", type=int, default=3, help="extraction mode (default: 3, R+C)"
    )
    p.set_defaults(handler=cmd_pex)

    # -- evidence ----------------------------------------------------------
    p = subparsers.add_parser(
        "evidence",
        help="assemble the evidence packet for a model",
        description=(
            "Collect netlist, geometry, reference cell and verdict into one "
            "packet. Use -o for the verbatim copy; stdout is indented."
        ),
    )
    p.add_argument("--cell", required=True, help="cell name")
    p.add_argument("--netlist", required=True, help="transistor-level SPICE netlist")
    p.add_argument("--gds", help="the layout, if one has been built")
    p.add_argument("--module", help="the cell generator, if one has been written")
    p.add_argument("--reference-cell", help="PDK cell to include as an example")
    p.add_argument("--max-bytes", type=int, help="truncate the packet to this size")
    p.add_argument("-o", "--out", help="write the packet here instead of stdout")
    p.set_defaults(handler=cmd_evidence)

    # -- baseline ----------------------------------------------------------
    p = subparsers.add_parser(
        "baseline",
        help="build the same logic by abutting PDK standard cells",
        description=(
            "Build the reference layout the AION cell has to beat, by abutting "
            "the PDK cells the gate-level netlist instantiates."
        ),
    )
    p.add_argument("gate_netlist", help="gate-level SPICE netlist of PDK cells")
    p.add_argument("-o", "--out", required=True, help="output directory")
    p.add_argument("--cell", help="subcircuit to build (default: the first)")
    p.add_argument("--verify", action="store_true", help="also run DRC and LVS on it")
    p.add_argument("--pex", action="store_true", help="also extract parasitics")
    p.add_argument(
        "--characterize", action="store_true", help="also characterize it (implies --pex)"
    )
    p.set_defaults(handler=cmd_baseline)

    # -- characterize ------------------------------------------------------
    p = subparsers.add_parser(
        "characterize",
        help="run SPICE over the corners and write Liberty",
        description="Characterize the cell with ngspice and emit Liberty files.",
    )
    p.add_argument("spice", help="SPICE netlist to characterize (PEX or schematic)")
    p.add_argument("--cell", required=True, help="cell name")
    p.add_argument("-o", "--out", required=True, help="output directory")
    p.add_argument("--area-lef", help="take the Liberty area from this LEF")
    p.add_argument("--area", type=float, help="Liberty area in um^2, if no LEF")
    p.add_argument(
        "--area-gds",
        help="measure the Liberty area from this GDS's prBoundary",
    )
    p.add_argument(
        "--corner",
        action="append",
        metavar="NAME:SECTION:VDD:TEMP",
        help="a corner, e.g. typ:mos_tt:1.2:25; repeatable "
             "(default: the built-in typ, slow and fast)",
    )
    p.add_argument("--jobs", type=int, default=8, help="parallel SPICE runs")
    p.add_argument(
        "--no-verify", action="store_true", help="skip the Liberty self-check"
    )
    p.add_argument("--inputs", help="comma-separated input pins, if not inferable")
    p.add_argument("--outputs", help="comma-separated output pins, if not inferable")
    p.set_defaults(handler=cmd_characterize)

    # -- compare -----------------------------------------------------------
    p = subparsers.add_parser(
        "compare",
        help="compare the AION cell against the abutted baseline",
        description=(
            "Compare area and delay against the baseline. Ends in one "
            "COMPARE: WIN|LOSS line; exit 0 on WIN, 1 on LOSS."
        ),
    )
    p.add_argument("--cell", required=True, help="the AION cell")
    p.add_argument("--baseline-cell", required=True, help="the abutted baseline cell")
    p.add_argument("--candidate-lib", required=True, help="candidate Liberty file")
    p.add_argument("--baseline-lib", required=True, help="baseline Liberty file")
    p.add_argument("--candidate-gds", required=True, help="candidate GDS, for the area")
    p.add_argument("--baseline-gds", required=True, help="baseline GDS, for the area")
    p.add_argument("--candidate-lef", help="take the candidate area from this LEF")
    p.add_argument("--baseline-lef", help="take the baseline area from this LEF")
    p.add_argument("--corner", default="typ", help="corner to compare at (default: typ)")
    p.add_argument("--json", help="write the comparison as JSON here")
    p.add_argument("--markdown", help="write the comparison as markdown here")
    p.set_defaults(handler=cmd_compare)

    # -- export ------------------------------------------------------------
    p = subparsers.add_parser(
        "export",
        help="write the gds/lef/lib/v/spice/cdl views",
        description="Write every view make pnr consumes, and check the LEF.",
    )
    p.add_argument("--cell", required=True, help="cell name")
    p.add_argument("--gds", required=True, help="the verified GDS")
    p.add_argument("--spice", required=True, help="the SPICE netlist")
    p.add_argument(
        "--lib", action="append", required=True, help="a Liberty file, repeatable"
    )
    p.add_argument("-o", "--out", required=True, help="output directory")
    p.add_argument("--pex-spice", help="PEX netlist, for the pin list")
    p.set_defaults(handler=cmd_export)

    # -- flow --------------------------------------------------------------
    p = subparsers.add_parser(
        "flow",
        help="run the whole mechanical chain and compare",
        description=(
            "verify -> pex -> baseline -> characterize both -> export -> "
            "compare. Stops at the first hard failure. Ends in one COMPARE: "
            "line, or STEP: flow FAIL, or RESULT: ERROR."
        ),
    )
    p.add_argument("netlist", help="transistor-level SPICE netlist")
    p.add_argument("--cell", required=True, help="cell name")
    p.add_argument("--module", required=True, help="cell generator module")
    p.add_argument(
        "--baseline", required=True, help="gate-level netlist of the PDK cells"
    )
    p.add_argument("-o", "--out", help="build directory (default: build/<cell>)")
    p.add_argument(
        "--corners",
        choices=("typ", "all"),
        default="typ",
        help="characterize at typ only, or every built-in corner",
    )
    p.add_argument("--jobs", type=int, default=8, help="parallel SPICE runs")
    p.add_argument(
        "--skip-baseline",
        action="store_true",
        help="build and characterize the cell only; no comparison",
    )
    p.set_defaults(handler=cmd_flow)

    return parser


def _report_flow_error(exc: BaseException) -> None:
    """Print a deliberate module exception: the message, and nothing else.

    Matched by class name *and* defining module.  A ``ValueError`` from deep
    inside KLayout is a bug and gets a traceback; a ``StepError`` is this flow
    saying no, and a traceback would bury the sentence that says why.
    """
    say(f"{type(exc).__name__}: {exc}")


def _is_flow_error(exc: BaseException) -> bool:
    """True for the named exceptions the flow modules raise on purpose."""
    if isinstance(exc, CliError):
        return True
    cls = type(exc)
    return (
        cls.__name__ in _FLOW_ERROR_NAMES
        and str(getattr(cls, "__module__", "")).startswith("aion_layout")
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse ``argv``, run one command, and return this CLI's exit status."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Optional[Callable[[argparse.Namespace], int]] = getattr(
        args, "handler", None
    )
    if handler is None:
        # Help goes to stderr: its ``usage:`` banner starts at column 0, and a
        # caller grepping stdout for the verdict must find the verdict and
        # nothing else -- including when it named no command at all.
        parser.print_help(sys.stderr)
        verdict("RESULT: ERROR")
        return EXIT_ERROR

    try:
        return int(handler(args))
    except BrokenPipeError:  # pragma: no cover - a closed pager, not a failure
        raise
    except Exception as exc:  # noqa: BLE001 - reported and re-raised as status 2
        if _is_flow_error(exc):
            _report_flow_error(exc)
        else:
            # Not a verdict this flow knows how to give: a bug here. Printed in
            # full, indented, so it is debuggable and still cannot forge a
            # verdict line, and graded ERROR rather than Python's own exit 1 --
            # which a caller would have read as a clean FAIL.
            say(f"unexpected {type(exc).__name__}: {exc}")
            say(
                "".join(
                    traceback.format_exception(type(exc), exc, exc.__traceback__)
                ),
                indent=INDENT + "  ",
            )
        verdict("RESULT: ERROR")
        return EXIT_ERROR


__all__ = [
    "EXIT_ERROR",
    "EXIT_FAIL",
    "EXIT_PASS",
    "CliError",
    "build_parser",
    "main",
    "say",
    "verdict",
]
