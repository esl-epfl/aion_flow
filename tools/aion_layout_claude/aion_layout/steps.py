# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The deterministic build/verify chain
# ================================================================

"""Build, render, DRC, LVS, measure -- and one verdict, in plain code.

This is the half of the flow no model touches.  A model writes a cell
generator; everything downstream of that file is mechanical, and shaped by
three decisions worth stating once here rather than re-deriving at each call
site.

**The generator runs in a subprocess.**  It is the one artifact a language
model authored, so it may ``sys.exit``, print a novel, or loop.  In-process,
all three would take the flow down with it; through
:func:`runner.run_python_isolated` all three are results, and the traceback
comes back as text -- which matters, because that text is the next thing the
model reads.

**A relative path means "relative to the tool directory".**  The containerised
runners already spell paths that way, so the Python half agrees with them
instead of depending on the caller's working directory.  Absolute paths are
left alone.

**Nothing that could not be measured is graded good.**  A verdict is ``PASS``
only on positive evidence from every check; a step that could not run at all is
``ERROR``, which is a different thing from ``FAIL`` and is never rounded down to
it.  :func:`klayout_table_logs` exists for exactly that reason: the KLayout DRC
receipt proves the rule *databases* on disk are the ones the run wrote, but a
rule table that died mid-run leaves a log with an error in it and contributes no
items -- which, counted, reads as clean.  Counting the logs and checking each
one finished closes that gap.
"""

from __future__ import annotations

import dataclasses as dc
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from . import verification as _v
from .metrics import (
    POWER_PIN_NAMES,
    ROW_HEIGHT_UM,
    CellGeometry,
    MetricsError,
    drawn_shapes,
    gds_boundary,
    port_access_problems,
    tap_contact_problems,
)
from .runner import (
    TOOL_DIR,
    rel_to_tool,
    run_host,
    run_in_container,
    run_python_isolated,
)
from .verification import (
    COMPLETENESS_DEGRADED,
    COMPLETENESS_UNVERIFIED,
    DrcReport,
    DrcViolation,
    KLAYOUT_DRC_DIR_SUFFIX,
    LvsReport,
    VerificationError,
    canonical_report_dirs,
)


class StepError(RuntimeError):
    """Raised when a step cannot run at all -- no input, no tool, no report."""


@dc.dataclass(frozen=True)
class StepResult:
    """The outcome of one mechanical step, and the artifacts it left behind.

    ``output`` carries the tool's own text on failure.  For :func:`build_gds`
    that is the generator's traceback, and it is returned rather than logged
    because it is what the model is handed to fix next.
    """

    name: str
    ok: bool
    detail: str
    artifacts: dict = dc.field(default_factory=dict)
    output: str = ""


@dc.dataclass(frozen=True)
class Verdict:
    """Everything the flow learned about one cell, and its single grade.

    ``result`` distinguishes three outcomes that a boolean would flatten into
    two.  ``FAIL`` means a tool ran and said the layout is wrong; ``ERROR``
    means a tool did not run, or its report could not be read, and so nothing is
    known -- which is emphatically not a pass.  ``reasons`` names every failing
    condition, not the first: a model fixing one violation at a time from a
    one-line verdict makes one edit per DRC run.
    """

    cell: str
    magic_drc: Optional[DrcReport]
    klayout_drc: Optional[DrcReport]
    lvs: Optional[LvsReport]
    geometry: Optional[CellGeometry]
    result: str
    reasons: Tuple[str, ...]

    @property
    def passed(self) -> bool:
        """True only for the one grade that means every check produced evidence."""
        return self.result == "PASS"


RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Paths and text hygiene


def _tool_path(path: os.PathLike[str] | str) -> Path:
    """Resolve ``path`` the way the containerised runners already spell paths.

    Relative means "below the tool directory", so a flow driven from any
    working directory reads and writes the same files the container does.
    """
    candidate = Path(path)
    return candidate if candidate.is_absolute() else (TOOL_DIR / candidate)


_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def _flatten(value: object, limit: int = 300) -> str:
    """Collapse tool text to one printable, bounded line.

    Report text is written by the tools and, through them, by the layout: it
    must never be able to introduce a line of its own into a verdict block.
    """
    text = _CONTROL_RE.sub(" ", str(value)).strip()
    text = re.sub(r"\s{2,}", " ", text)
    return text if len(text) <= limit else text[: limit - 3] + "..."


# ---------------------------------------------------------------------------
# build


#: Executed by :func:`runner.run_python_isolated`.  It loads the generator by
#: file path rather than by module name so that a cell can live anywhere the
#: caller likes, and it deliberately does not catch anything: an uncaught
#: traceback on stderr is the most useful thing a failed build can produce.
_BUILD_SCRIPT = """\
import importlib.util, sys
from pathlib import Path

module_path, cell_name, out_gds = {module!r}, {cell!r}, {out!r}

spec = importlib.util.spec_from_file_location("aion_cell_under_build", module_path)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load a Python module from " + module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

generate = getattr(module, "generate", None)
if generate is None:
    raise SystemExit(module_path + " defines no generate(cell_name, tech)")

from aion_layout.tech import sg13g2_tech

cell = generate(cell_name, sg13g2_tech)
if cell is None:
    raise SystemExit("generate() returned None instead of a Cell")
Path(out_gds).parent.mkdir(parents=True, exist_ok=True)
cell.write_gds(out_gds)

# The ports go out beside the GDS so that verify can grade them against the
# routing track grid.  They do not survive the GDS round trip as rectangles --
# write_gds keeps only a label at each port's centre -- and the caller runs in
# a different process, so the sidecar is how the geometry gets back.
import json
json.dump(
    [
        {{
            "name": port.name,
            "layer": port.layer.name,
            "direction": port.direction,
            "rect": [
                port.rect.bottom_left.x, port.rect.bottom_left.y,
                port.rect.top_right.x, port.rect.top_right.y,
            ],
        }}
        for port in cell.ports.values()
    ],
    open(out_gds + ".ports.json", "w"),
)
"""


#: Written next to the GDS by :data:`_BUILD_SCRIPT`.
PORTS_SUFFIX = ".ports.json"


def declared_ports(gds: Path) -> Optional[List[Tuple[str, str, float, float, float, float]]]:
    """Read the ports :func:`build_gds` recorded, or None when there are none.

    None means "this build wrote no sidecar" -- an older build directory, or a
    ``skip_build`` run against a GDS built before this existed.  That is not
    the same as a cell with no ports, and must not be graded as one.
    """
    sidecar = Path(str(gds) + PORTS_SUFFIX)
    try:
        raw = json.loads(sidecar.read_text())
    except (OSError, ValueError):
        return None
    ports = []
    for entry in raw:
        try:
            x1, y1, x2, y2 = (float(v) for v in entry["rect"])
            ports.append((str(entry["name"]), str(entry["layer"]), x1, y1, x2, y2))
        except (KeyError, TypeError, ValueError):
            return None
    return ports


def declared_directions(gds: Path) -> Optional[Dict[str, str]]:
    """Return ``{port: direction}`` as the generator recorded it, or None.

    The directions are the cell's own statement of what it drives and what it
    is driven by, and they are the only statement there is: a ``.subckt`` line
    does not carry them, and inferring them from the transistors works only for
    a cell whose every input is a gate terminal.  A transmission gate breaks
    that -- its pass inputs sit on a channel terminal exactly as the output
    does -- so a caller that has this sidecar must prefer it to a guess.
    """
    sidecar = Path(str(gds) + PORTS_SUFFIX)
    try:
        raw = json.loads(sidecar.read_text())
    except (OSError, ValueError):
        return None
    directions: Dict[str, str] = {}
    for entry in raw:
        try:
            directions[str(entry["name"])] = str(entry["direction"])
        except (KeyError, TypeError):
            return None
    return directions or None


def _gds_top_cells(gds: Path) -> List[str]:
    """Return the names of the top cells in ``gds``."""
    try:
        import klayout.db as pya
    except Exception as exc:  # pragma: no cover - klayout is a hard dependency
        raise StepError(f"klayout.db unavailable: {exc}") from exc
    layout = pya.Layout()
    try:
        layout.read(str(gds))
    except Exception as exc:
        raise StepError(f"cannot read {gds.name}: {exc}") from exc
    return [cell.name for cell in layout.top_cells()]


def build_gds(
    module_path: os.PathLike[str] | str,
    cell_name: str,
    out_gds: os.PathLike[str] | str,
    *,
    timeout: int = 300,
) -> StepResult:
    """Run a cell generator in a subprocess and write ``out_gds``.

    Three things have to be true before the build counts as done, and a
    generator can satisfy the first while failing the others: the subprocess
    exited 0, a non-empty file appeared, and the single top cell in it is named
    ``cell_name``.  The name matters downstream -- ``run_drc`` names its report
    directories after the GDS stem and ``run_lvs`` is told the cell by name --
    so a mismatch caught here becomes one clear sentence instead of an LVS run
    that cannot find its cell.
    """
    module = _tool_path(module_path)
    gds = _tool_path(out_gds)
    name = "build"

    if not module.is_file():
        return StepResult(name, False, f"no generator module at {module}")

    # A stale GDS from a previous build must not survive a failed one and be
    # mistaken for this build's output.
    if gds.exists():
        try:
            gds.unlink()
        except OSError as exc:
            return StepResult(name, False, f"cannot remove stale {gds}: {exc}")

    script = _BUILD_SCRIPT.format(module=str(module), cell=cell_name, out=str(gds))
    run = run_python_isolated(script, timeout=timeout)

    if not run.ok:
        why = "timed out" if run.timed_out else f"exited {run.status}"
        return StepResult(
            name,
            False,
            f"{module.name}: generate({cell_name!r}) {why}",
            output=run.output,
        )
    if not gds.is_file():
        return StepResult(
            name,
            False,
            f"{module.name}: generate({cell_name!r}) succeeded but wrote no {gds}",
            output=run.output,
        )
    if gds.stat().st_size == 0:
        return StepResult(
            name,
            False,
            f"{module.name}: generate({cell_name!r}) wrote an empty {gds}",
            output=run.output,
        )

    try:
        tops = _gds_top_cells(gds)
    except StepError as exc:
        return StepResult(name, False, str(exc), {"gds": gds}, run.output)
    if tops != [cell_name]:
        found = ", ".join(sorted(tops)) or "(none)"
        return StepResult(
            name,
            False,
            f"{gds.name} top cell(s) [{found}] but the flow verifies "
            f"{cell_name!r}; name the Cell after the cell_name argument",
            {"gds": gds},
            run.output,
        )

    return StepResult(
        name,
        True,
        f"{cell_name} -> {rel_to_tool(gds)} ({gds.stat().st_size} bytes)",
        {"gds": gds},
        run.output,
    )


# ---------------------------------------------------------------------------
# render


def render_png(
    gds: os.PathLike[str] | str,
    out_png: os.PathLike[str] | str,
    *,
    width: int = 1400,
    timeout: int = 600,
) -> StepResult:
    """Render ``gds`` to a PNG with ``scripts/gds_to_image.py``.

    A picture is a convenience for a human reader, never evidence, so this
    returns a non-ok :class:`StepResult` rather than raising and must never be
    allowed to decide a verdict.  The canvas is square because the renderer
    scales uniformly to fit: a square never clips a tall cell or a wide one.
    The host is tried first and the container only as a fallback, so the common
    case costs no docker round trip.
    """
    source = _tool_path(gds)
    target = _tool_path(out_png)
    name = "render"
    script = TOOL_DIR / "scripts" / "gds_to_image.py"

    if not script.is_file():
        return StepResult(name, False, f"no renderer at {script}")
    if not source.is_file() or source.stat().st_size == 0:
        return StepResult(name, False, f"no readable GDS at {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        try:
            target.unlink()
        except OSError as exc:
            return StepResult(name, False, f"cannot remove stale {target}: {exc}")

    args = [str(source), str(target), "--width", str(width), "--height", str(width)]
    run = run_host([sys.executable, str(script), *args], cwd=TOOL_DIR, timeout=timeout)
    where = "host"
    if not run.ok:
        command = " ".join(
            ["python3", rel_to_tool(script), rel_to_tool(source), rel_to_tool(target),
             "--width", str(width), "--height", str(width)]
        )
        fallback = run_in_container(command, timeout=timeout)
        if fallback.ok:
            run, where = fallback, "container"
        else:
            return StepResult(
                name,
                False,
                "gds_to_image.py failed on the host and in the container",
                output=run.tail(20) + "\n---- container ----\n" + fallback.tail(20),
            )

    if not target.is_file() or target.stat().st_size == 0:
        return StepResult(
            name,
            False,
            f"gds_to_image.py exited 0 on the {where} but wrote no image at {target}",
            output=run.tail(20),
        )
    return StepResult(
        name,
        True,
        f"{rel_to_tool(target)} ({target.stat().st_size} bytes, {where})",
        {"png": target},
        run.output,
    )


# ---------------------------------------------------------------------------
# DRC and LVS -- delegations, not reimplementations


def drc(
    gds: os.PathLike[str] | str,
    work_dir: os.PathLike[str] | str,
    *,
    cell_name: Optional[str] = None,
) -> Tuple[DrcReport, DrcReport]:
    """Run Magic and KLayout DRC on ``gds`` and return both parsed reports.

    ``cell_name``, when given, is checked against the GDS file stem rather than
    passed on: :func:`verification.run_drc` names its report directories after
    that stem, so a file called something else would leave the reports where
    nothing looks for them.
    """
    source = _tool_path(gds)
    work = _tool_path(work_dir)
    if not source.is_file():
        raise StepError(f"no GDS to check at {source}")
    if source.stat().st_size == 0:
        raise StepError(f"{source} is empty; there is nothing to check")
    if cell_name is not None and source.stem != cell_name:
        raise StepError(
            f"{source.name} would file its DRC reports under {source.stem!r}, "
            f"not {cell_name!r}; name the GDS {cell_name}.gds"
        )
    return _v.run_drc(source, work)


def lvs(
    gds: os.PathLike[str] | str,
    netlist: os.PathLike[str] | str,
    cell_name: str,
    work_dir: os.PathLike[str] | str,
) -> LvsReport:
    """Extract ``gds`` with Magic and compare it to ``netlist`` with Netgen."""
    source = _tool_path(gds)
    spice = _tool_path(netlist)
    work = _tool_path(work_dir)
    if not source.is_file() or source.stat().st_size == 0:
        raise StepError(f"no readable GDS at {source}")
    if not spice.is_file():
        raise StepError(f"no reference netlist at {spice}")
    if spice.stat().st_size == 0:
        raise StepError(f"{spice} is empty; there is nothing to compare against")
    return _v.run_lvs(source, spice, cell_name, work)


# ---------------------------------------------------------------------------
# KLayout per-table logs
#
# ``sak-drc.sh -l macro`` runs one rule table at a time and writes
# ``<gds>_<top>_<table>.log`` beside the databases, plus two logs that are not a
# table: the concatenated ``<cell>.drc.log`` and the wrapper's own
# ``drc_run_<timestamp>.log``.  A healthy table log ends with
#
#     KLayout DRC run for tables 'metal1' completed in 0.22 seconds
#
# and no per-table log of either a clean or a violating run contains an error
# signature at all, which is what makes both checks below safe to apply
# together.
#
# Only the per-table logs are scanned.  The wrapper log and the concatenated
# ``<cell>.drc.log`` use ERROR as a *severity level* for the banner every dirty
# run prints -- "| ERROR | KLayout DRC Check Failed: Violations were detected"
# -- so scanning them turned every honest DRC violation into three spurious
# "a rule table died" problems and graded a plain FAIL as ERROR.  A tool saying
# it found violations is the DRC verdict's business, not this function's.
#
# The error patterns use word boundaries for the same reason: a plural "errors"
# appears in healthy KLayout and Magic prose ("No DRC errors"), and a check that
# fires on every clean run is a check nobody keeps.
# ---------------------------------------------------------------------------

#: A per-table log: ``<prefix>_<table>.log``.  ``<cell>.drc.log`` fails to match
#: (its last component is preceded by ``.``, not ``_``); ``drc_run_*.log`` does
#: match, so it is excluded by name below.
_TABLE_LOG_RE = re.compile(r"^(?P<prefix>.+)_(?P<table>[A-Za-z0-9]+)\.log$")
#: Logs written by the wrapper rather than by a rule table.
_WRAPPER_LOG_PREFIX = "drc_run"

#: The line a rule table prints when, and only when, it finished.  The names it
#: quotes are also the census of what completed, read out of the run log below.
_TABLE_DONE_RE = re.compile(
    r"KLayout DRC run for tables '(?P<tables>[^']*)' completed in", re.IGNORECASE
)
#: The line the runner prints once per rule table it was asked to execute.
_TABLE_SELECTED_RE = re.compile(r"tables selected:\s*(?P<tables>.+)")

_LOG_ERROR_RES = (
    re.compile(r"traceback", re.IGNORECASE),
    re.compile(r"\berror\b", re.IGNORECASE),
    re.compile(r"\bexception\b", re.IGNORECASE),
    re.compile(r"no such file", re.IGNORECASE),
)


def _log_table_name(name: str) -> Optional[str]:
    """Return the rule table ``name`` belongs to, or ``None`` if it is not one."""
    if name.startswith(_WRAPPER_LOG_PREFIX) or name.endswith(".drc.log"):
        return None
    match = _TABLE_LOG_RE.match(name)
    return match.group("table") if match else None


def _scan_text(text: str) -> List[str]:
    """Return every error-signature line found in ``text``, flattened."""
    hits: List[str] = []
    for line in text.splitlines():
        if any(pattern.search(line) for pattern in _LOG_ERROR_RES):
            hits.append(_flatten(line, 160))
            if len(hits) >= 3:
                break
    return hits


def _run_log_tables(directory: Path) -> Tuple[Set[str], Set[str], List[str]]:
    """Return ``(selected, completed, problems)`` read from the KLayout run log.

    ``run_drc.py`` prints ``tables selected: <name>`` as each rule table starts
    and ``... for tables '<name>' completed in`` as it ends, and the wrapper
    redirects all of that into one ``<cell>.drc.log`` beside the per-table logs.
    That file is therefore the run's own record of which tables it meant to
    execute -- the only thing on disk that can tell a table whose log was never
    written from a run that only ever had one table.  Nothing here scans it for
    error signatures: it also carries the violation banner every dirty run
    prints at severity ERROR (see the section comment above).
    """
    runs = sorted(p for p in directory.glob("*.drc.log") if p.is_file())
    if not runs:
        return set(), set(), [
            f"no *.drc.log run log in {rel_to_tool(directory)}: nothing records "
            "which rule tables the run was asked to execute"
        ]
    if len(runs) > 1:
        return set(), set(), [
            "more than one *.drc.log run log in "
            + rel_to_tool(directory)
            + " ("
            + ", ".join(p.name for p in runs)
            + "); refusing to guess which run to grade"
        ]
    try:
        text = runs[0].read_text(errors="replace")
    except OSError as exc:
        return set(), set(), [f"run log {runs[0].name} is unreadable: {exc}"]

    selected = {
        name
        for match in _TABLE_SELECTED_RE.finditer(text)
        for name in match.group("tables").split()
    }
    completed = {
        name
        for match in _TABLE_DONE_RE.finditer(text)
        for name in match.group("tables").split()
    }
    problems: List[str] = []
    if not selected:
        problems.append(
            f"run log {runs[0].name} names no selected rule table, so nothing "
            "says which tables this run was supposed to execute"
        )
    return selected, completed, problems


def _log_for_table(names: List[str], table: str) -> bool:
    """True when one of ``names`` is a log of ``table``.

    With ``--mp`` each table gets its own ``<prefix>_<table>.log``, which is the
    exact match tried first.  A run that batches several tables into one process
    names the log after all of them (``<prefix>_<a>_<b>.log``), so a containment
    match is kept as a fallback -- loose, but loose in the direction that
    reports fewer problems only when a log genuinely covers several tables.
    """
    if any(name.endswith(f"_{table}.log") for name in names):
        return True
    return any(f"_{table}_" in name for name in names)


def klayout_table_logs(
    work_dir: os.PathLike[str] | str,
    cell_name: str,
) -> Tuple[int, Tuple[str, ...]]:
    """Check that every KLayout rule table actually ran, and return what it found.

    Returns ``(table_count, problems)``.  The receipt the DRC step writes proves
    the databases on disk are the ones the run produced; it cannot prove that
    each rule table *executed*.  A table that dies leaves a log carrying the
    failure and contributes no items to the merge, and zero items is what a
    clean layout also looks like -- so a run with no problems here is the other
    half of the evidence that a zero-violation KLayout verdict means anything.

    Anything short of positive proof is a problem: no directory, no per-table
    logs, a log with an error signature, an empty log, a log with no completion
    marker, a rule table the run log says was selected and that left no log or
    never reported completion, and a cell whose logs appear in more than one
    canonical directory at once.  The wrapper and concatenated logs are not
    scanned for error signatures -- see the section comment above for the banner
    that made scanning them wrong -- but the concatenated one is read for the
    census of table names, which is the only record of what should have run.
    """
    work = _tool_path(work_dir)
    problems: List[str] = []

    dirs = canonical_report_dirs(work, cell_name, KLAYOUT_DRC_DIR_SUFFIX)
    if not dirs:
        return 0, (
            f"no {cell_name}.{KLAYOUT_DRC_DIR_SUFFIX}/ directory under "
            f"{rel_to_tool(work)}: the KLayout half of the DRC run left no logs",
        )
    if len(dirs) > 1:
        return 0, (
            f"{cell_name}.{KLAYOUT_DRC_DIR_SUFFIX}/ exists in "
            + str(len(dirs))
            + " places ("
            + ", ".join(rel_to_tool(d) for d in dirs)
            + "); refusing to guess which run to grade",
        )
    directory = dirs[0]

    logs = sorted(p for p in directory.glob("*.log") if p.is_file())
    tables: List[Path] = []
    for path in logs:
        table = _log_table_name(path.name)
        if table is None:
            continue
        tables.append(path)
        try:
            text = path.read_text(errors="replace")
        except OSError as exc:
            problems.append(f"rule table {table!r}: log unreadable: {exc}")
            continue
        if not text.strip():
            problems.append(f"rule table {table!r}: log {path.name} is empty")
            continue
        for hit in _scan_text(text):
            problems.append(f"rule table {table!r}: {hit}")
        if not _TABLE_DONE_RE.search(text):
            problems.append(
                f"rule table {table!r}: log {path.name} carries no completion "
                "marker, so nothing says the table ran to the end"
            )

    # The census.  Reading the logs that are present can only find a table that
    # died loudly; it cannot find one that left nothing behind, and a directory
    # holding one healthy log looks exactly as good as one holding all of them.
    # The run log says which tables the run selected, so every selected table
    # has to answer for itself here.
    selected, completed, log_problems = _run_log_tables(directory)
    problems.extend(log_problems)
    names = [path.name for path in tables]
    for table in sorted(selected):
        if not _log_for_table(names, table):
            problems.append(
                f"rule table {table!r} was selected by the run and left no log: "
                "nothing says it ran"
            )
        if table not in completed:
            problems.append(
                f"rule table {table!r} was selected by the run and never reported "
                "completion, so its rules were not applied to this layout"
            )

    if not tables:
        problems.append(
            f"no per-rule-table logs in {rel_to_tool(directory)}: nothing proves "
            "any rule table ran"
        )
    return len(tables), tuple(problems)


# ---------------------------------------------------------------------------
# the graded chain


def _grade_drc(report: Optional[DrcReport], label: str,
               errors: List[str], failures: List[str]) -> None:
    """Sort one DRC report into "could not tell" and "is wrong".

    Every cause is named once and only once.  Completeness is graded here
    rather than by the caller because a report that is not clean *because* its
    extent is unknown would otherwise be reported twice -- as the completeness
    fault and again as the unexplained un-cleanliness -- and a list of reasons
    that repeats itself teaches a reader to skim it.
    """
    if report is None:
        errors.append(f"{label} DRC did not run")
        return
    if not report.available:
        errors.append(
            f"{label} DRC produced no usable report: "
            f"{_flatten(report.unavailable_reason or 'no report file')}"
        )
        return

    named = False
    if report.unparsed_files:
        errors.append(
            f"{label} DRC left {report.unparsed_files} report file(s) that could "
            "not be parsed"
        )
        named = True
    if report.location_note:
        errors.append(f"{label} DRC report is not where the tool writes it: "
                      f"{_flatten(report.location_note)}")
        named = True
    if report.completeness in (COMPLETENESS_DEGRADED, COMPLETENESS_UNVERIFIED):
        errors.append(
            f"{label} DRC completeness is {report.completeness}: "
            f"{_flatten(report.completeness_note or 'no receipt')}"
        )
        for missing in report.missing_databases:
            errors.append(
                f"{label} DRC database promised by the receipt and missing: "
                f"{_flatten(missing, 80)}"
            )
        named = True
    if report.violations:
        failures.append(
            f"{label} DRC: {len(report.violations)} violation(s) in "
            + ", ".join(_flatten(c, 60) for c in list(report.categories)[:6])
        )
        named = True
    if not report.clean and not named:
        # The report says it is not clean and none of the causes above explains
        # it: report that rather than let an unexplained verdict pass silently.
        errors.append(
            f"{label} DRC is not clean and gives no reason this grader "
            f"understands: {_flatten(report.completeness_note or 'no detail')}"
        )


def _grade_lvs(report: Optional[LvsReport], errors: List[str],
               failures: List[str]) -> None:
    """Sort the LVS report the same way."""
    if report is None:
        errors.append("LVS did not run")
        return
    if report.location_note:
        errors.append(f"LVS report is not where Netgen writes it: "
                      f"{_flatten(report.location_note)}")
    if report.verdict in ("no_final_result", "uncertain"):
        errors.append(
            f"LVS produced no usable verdict ({report.verdict}): "
            f"{_flatten(report.message, 200)}"
        )
        return
    if not report.clean:
        detail = f"LVS: {report.verdict}"
        if report.device_total:
            detail += f"; devices {report.device_total[0]}/{report.device_total[1]}"
        if report.net_counts:
            detail += f"; nets {report.net_counts[0]}/{report.net_counts[1]}"
        if report.disconnected_nodes:
            detail += "; disconnected " + ", ".join(
                _flatten(n, 40) for n in report.disconnected_nodes[:6]
            )
        failures.append(detail)


def verify(
    module_path: os.PathLike[str] | str,
    cell_name: str,
    netlist: os.PathLike[str] | str,
    work_dir: os.PathLike[str] | str,
    *,
    skip_build: bool = False,
) -> Verdict:
    """Build, check and measure one cell, and return its single verdict.

    The layout is ``<work_dir>/<cell_name>.gds`` and the reports land in
    ``<work_dir>/drc`` and ``<work_dir>/lvs`` -- both runners wipe the directory
    they are given, which is why they are given subdirectories and not the work
    directory that holds the GDS.

    A failed build stops the chain, because every later step reads the file it
    did not write.  After that the chain runs to the end even when a step
    fails: a model fixing a layout wants every complaint from one run, not the
    first one in report order.
    """
    work = _tool_path(work_dir)
    gds = work / f"{cell_name}.gds"
    errors: List[str] = []
    failures: List[str] = []

    if not skip_build:
        built = build_gds(module_path, cell_name, gds)
        if not built.ok:
            reason = built.detail
            if built.output.strip():
                reason += "\n" + built.output
            return Verdict(cell_name, None, None, None, None, RESULT_ERROR, (reason,))
    elif not gds.is_file() or gds.stat().st_size == 0:
        return Verdict(
            cell_name, None, None, None, None, RESULT_ERROR,
            (f"skip_build was asked for but there is no readable GDS at {gds}",),
        )

    magic_drc: Optional[DrcReport] = None
    klayout_drc: Optional[DrcReport] = None
    try:
        magic_drc, klayout_drc = drc(gds, work / "drc", cell_name=cell_name)
    except (StepError, VerificationError, OSError) as exc:
        errors.append(f"DRC could not run: {_flatten(exc, 400)}")

    lvs_report: Optional[LvsReport] = None
    try:
        lvs_report = lvs(gds, netlist, cell_name, work / "lvs")
    except (StepError, VerificationError, OSError) as exc:
        errors.append(f"LVS could not run: {_flatten(exc, 400)}")

    geometry: Optional[CellGeometry] = None
    try:
        geometry = gds_boundary(gds, cell_name)
    except MetricsError as exc:
        errors.append(f"geometry could not be measured: {_flatten(exc, 300)}")

    _grade_drc(magic_drc, "Magic", errors, failures)
    _grade_drc(klayout_drc, "KLayout", errors, failures)

    table_count, table_problems = klayout_table_logs(work / "drc", cell_name)
    for problem in table_problems:
        errors.append(f"KLayout rule tables ({table_count} log(s)): {_flatten(problem, 240)}")

    _grade_lvs(lvs_report, errors, failures)

    if geometry is not None and not geometry.row_legal:
        failures.append(
            "geometry is not row-legal: " + "; ".join(
                _flatten(p, 160) for p in geometry.problems
            )
        )

    # What a cell does to its neighbours is DRC-clean, LVS-clean and row-legal
    # on its own, and then takes step 7 down an hour later -- DRT-0073 in pin
    # access, or thousands of Cnt.b violations once the rails abut.  Neither is
    # visible in a cell by itself, so both are graded here from the geometry,
    # inside the drawing loop where they can still be fixed.
    drawn = None
    try:
        drawn = drawn_shapes(gds, cell_name=cell_name)
    except MetricsError as exc:
        errors.append(
            f"the geometry of {cell_name} could not be read from {gds.name}, "
            "so it was not checked for what abutting it would do: "
            f"{_flatten(exc, 200)}"
        )

    ports = declared_ports(gds)
    if ports is None:
        errors.append(
            f"the ports of {cell_name} could not be read from "
            f"{gds.name}{PORTS_SUFFIX}, so they were not checked against the "
            "routing track grid; rebuild the cell"
        )
    else:
        signal_ports = [
            port for port in ports
            if port[0].upper() not in POWER_PIN_NAMES
        ]
        for problem in port_access_problems(signal_ports, drawn):
            # 400, like the DRC and LVS reasons: these end with what to do
            # about the problem, and a reason truncated before that is a
            # reason the model cannot act on.
            failures.append(_flatten(problem, 400))

    if drawn is not None:
        height_nm = (geometry.height_um if geometry else ROW_HEIGHT_UM) * 1000.0
        for problem in tap_contact_problems(drawn.get("Cont", ()), height_nm):
            failures.append(_flatten(problem, 400))

    if errors:
        result = RESULT_ERROR
    elif failures:
        result = RESULT_FAIL
    else:
        result = RESULT_PASS
    return Verdict(
        cell=cell_name,
        magic_drc=magic_drc,
        klayout_drc=klayout_drc,
        lvs=lvs_report,
        geometry=geometry,
        result=result,
        reasons=tuple(errors + failures),
    )


# ---------------------------------------------------------------------------
# rendering the verdict


def _where(violation: DrcViolation) -> str:
    """Where a violation is, or an honest statement that the report does not say.

    KLayout files a spacing violation as an ``edge-pair`` value that carries no
    box, and those reach here as ``(0,0)-(0,0)``.  Printed as a location that
    sends a model to the origin to look for a violation that is somewhere else,
    so the absence is named instead.  The rule description printed beside it is
    then the only handle the model has, which is why it is worth the width.
    """
    if tuple(violation.bbox_um) == (0.0, 0.0, 0.0, 0.0):
        return "<report gives no coordinates>"
    return violation.bbox_str


def _drc_block(label: str, report: Optional[DrcReport]) -> List[str]:
    """Return the lines describing one DRC report, unindented."""
    head = f"{label + ' DRC':<12}"
    if report is None:
        return [head + "ERROR - did not run"]
    if not report.available:
        return [head + "ERROR - " + _flatten(report.unavailable_reason or "no report")]

    state = "clean" if report.clean else "NOT CLEAN"
    line = f"{head}{state} - {len(report.violations)} violation(s)"
    if report.reported_count is not None:
        line += f" (tool reported {report.reported_count})"
    if report.completeness:
        line += f"; completeness {report.completeness}"
    lines = [line]
    if report.completeness_note:
        lines.append("  " + _flatten(report.completeness_note, 200))
    if report.unparsed_files:
        lines.append(f"  {report.unparsed_files} report file(s) could not be parsed")
    if report.location_note:
        lines.append("  " + _flatten(report.location_note, 200))
    for name in report.missing_databases[:6]:
        lines.append("  missing database " + _flatten(name, 80))

    # A category name plus one real bounding box is the difference between a
    # verdict a model can act on and "DRC failed".
    by_category: dict = {}
    for violation in report.violations:
        by_category.setdefault(violation.category, []).append(violation)
    for category, items in list(by_category.items())[:8]:
        boxes = " ".join(_where(v) for v in items[:3])
        more = f" (+{len(items) - 3} more)" if len(items) > 3 else ""
        rule = _flatten(items[0].description, 90)
        note = f" -- {rule}" if rule and rule not in category else ""
        lines.append(f"  {_flatten(category, 70)} x{len(items)}: {boxes}{more}{note}")
    if len(by_category) > 8:
        lines.append(f"  (+{len(by_category) - 8} more categories)")
    return lines


def _lvs_block(report: Optional[LvsReport]) -> List[str]:
    """Return the lines describing the LVS report, unindented."""
    head = f"{'LVS':<12}"
    if report is None:
        return [head + "ERROR - did not run"]
    state = "clean" if report.clean else "NOT CLEAN"
    line = f"{head}{state} - {report.verdict}"
    if report.device_total:
        line += f"; devices {report.device_total[0]}/{report.device_total[1]}"
    if report.net_counts:
        line += f"; nets {report.net_counts[0]}/{report.net_counts[1]}"
    lines = [line]
    if report.message:
        lines.append("  " + _flatten(report.message, 200))
    if report.location_note:
        lines.append("  " + _flatten(report.location_note, 200))
    for device, (layout_n, source_n) in list(report.device_counts.items())[:8]:
        flag = "" if layout_n == source_n else "   <- differs"
        lines.append(f"  {_flatten(device, 40)}: layout {layout_n} vs netlist {source_n}{flag}")
    if report.disconnected_nodes:
        lines.append(
            "  disconnected nodes: "
            + ", ".join(_flatten(n, 40) for n in report.disconnected_nodes[:8])
        )
    for layout_pin, source_pin in report.unmatched_pins[:8]:
        lines.append(f"  unmatched pin: layout {_flatten(layout_pin, 40)} vs "
                     f"netlist {_flatten(source_pin, 40)}")
    return lines


def render_verdict(v: Verdict) -> str:
    """Render the block a model reads to decide its next edit.

    Exactly one line begins at column 0, and it is the ``RESULT:`` line.  Every
    other line -- including any line that came out of a tool report -- is
    indented, so no report text can ever be mistaken for the verdict.
    """
    body: List[str] = [f"{'cell':<12}{_flatten(v.cell, 80)}"]
    body += _drc_block("Magic", v.magic_drc)
    body += _drc_block("KLayout", v.klayout_drc)
    body += _lvs_block(v.lvs)

    if v.geometry is None:
        body.append(f"{'geometry':<12}ERROR - not measured")
    else:
        body.append(f"{'geometry':<12}{_flatten(v.geometry.describe(), 200)}")
        for problem in v.geometry.problems:
            body.append("  " + _flatten(problem, 200))

    if v.reasons:
        body.append(f"{'failing':<12}{len(v.reasons)} condition(s):")
        for i, reason in enumerate(v.reasons, 1):
            body.append(f"  {i}. {reason}")

    lines: List[str] = []
    for chunk in body:
        for line in (chunk.splitlines() or [""]):
            lines.append("  " + line)
    lines.append(f"RESULT: {v.result}")
    return "\n".join(lines)


def write_report(v: Verdict, path: os.PathLike[str] | str) -> Path:
    """Write :func:`render_verdict` to ``path`` and return where it landed.

    The file holds the same text the model was shown, so a run can be re-read
    later without re-running the tools -- and so nobody has to trust a summary
    of a summary.
    """
    target = _tool_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_verdict(v) + "\n")
    return target


__all__ = [
    "RESULT_ERROR",
    "RESULT_FAIL",
    "RESULT_PASS",
    "StepError",
    "StepResult",
    "Verdict",
    "build_gds",
    "drc",
    "klayout_table_logs",
    "lvs",
    "render_png",
    "render_verdict",
    "verify",
    "write_report",
]
