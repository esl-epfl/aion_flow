#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Updated:                   2026-09-03
#  Description:               One-page DRC/LVS verification summary
# ================================================================

"""Print a machine-parseable DRC/LVS verdict for a generated cell.

The agentic layout loop feeds this program's stdout back to the model and
``pipeline.sh`` greps it for ``^RESULT:``, so three properties matter more than
anything the program says about a layout:

1. **It always prints a verdict.**  Every exit path -- a parser crash, a missing
   report, a bad argument -- ends with a ``DRC:`` line, an ``LVS:`` line and a
   final ``RESULT: PASS|FAIL|ERROR`` line.  A run that printed only the
   ``Cell:`` header is what previously made the loop blind.

2. **It prints exactly one ``^RESULT:`` line, and it is the last line.**  Every
   other line leaves this program through :class:`_VerdictStream`, which scrubs
   control characters out of externally sourced text and neutralises any line
   that would otherwise start with ``RESULT:``.  Report files, tool output,
   exception messages and even ``argv`` are attacker reachable -- the model
   under test writes the directory this program parses -- so a newline inside
   any of them must not be able to forge a verdict at column 0.

3. **Absence is never a pass.**  Reports are discovered only at the canonical
   paths the ``sak-*`` wrappers write (``<cell>.magic.drc/``,
   ``<cell>.klayout.drc/``, ``<cell>.magic.lvs/``) *and only under the exact
   names those wrappers give them*; a whole-tree glob used to let a planted
   ``drc/<cell>/<cell>.magic.drc.rpt`` outrank the real report, and enforcing the
   directory alone still let a ``planted.magic.drc.rpt`` carrying
   ``[INFO] COUNT: 0`` answer for a deleted 8-violation report.  ``PASS``
   requires positive evidence from every artifact; anything missing, empty,
   truncated, only partly readable or merely differently named is labelled
   ``NOT AVAILABLE`` / ``DEGRADED`` and can never be one of them.

4. **A count is only as complete as the file set it was taken from.**  Deleting
   one KLayout rule database deleted a whole rule table from the verdict and the
   headline read ``PASS - 0 violations across 30 rule databases``.  The DRC step
   leaves a receipt naming the databases it wrote (see
   ``aion_layout.verification.KLAYOUT_RECEIPT_NAME``); this program prints the
   completeness grade that comes back from checking the files against it, and a
   zero-item KLayout result whose completeness is not ``VERIFIED`` is never
   ``PASS``.

The status vocabulary is shared with ``scripts/evidence.py``, so the two things
the model is shown cannot disagree about what it is looking at: ``PASS`` /
``FAIL`` / ``NOT AVAILABLE`` / ``DEGRADED`` per artifact, ``RESULT:
PASS|FAIL|ERROR`` overall, ``PASS`` only when every artifact is positively
clean, and ``ERROR`` reserved for the run that could not be graded at all --
the Magic or the Netgen report is not on disk.

Exit status: ``0`` for PASS, ``1`` for FAIL, ``2`` for ERROR.

Invocation contract
-------------------

The graders run on the host, from a copy of the package kept outside the build
directory the model writes, so nothing here assumes it is running inside the
repository:

* **``aion_layout`` comes from ``PYTHONPATH`` when ``PYTHONPATH`` provides it.**
  The ``__file__``-derived fallback is consulted only when the import would
  otherwise fail, and is *appended* to ``sys.path``, never inserted in front of
  it.  Inserting a repository path at ``sys.path[0]`` -- what this program used
  to do -- let the working tree shadow the isolated copy being graded.
  ``AION_ROOT`` is honoured as one of the fallbacks, not as an override.
* **Every path argument is used exactly as given.**  ``--runs-dir``, ``--gds``
  and ``--netlist`` may be absolute and may live anywhere; none of them is
  resolved against the repository root, against ``__file__`` or against the
  current working directory, and the process never chdirs.  The caller does not
  have to run from the repository root.
* **``--parse-only`` starts no tool.**  It is pure Python plus the ``klayout``
  module and needs neither Docker nor ``scripts/docker_run.sh`` to exist;
  ``--run-script`` (default ``$AION_RUN_SCRIPT`` or ``docker_run.sh`` beside this
  file) is consulted only on the non-``--parse-only`` path.

So the host-side, isolated-copy invocation is::

    PYTHONPATH=/guard python3 /guard/scripts/report_verification.py \\
        --cell CELL --gds /guard/CELL.gds --netlist /guard/CELL.spice \\
        --runs-dir /build/iteration_3 --parse-only

Examples
--------

Parse existing reports only (fast)::

    python3 scripts/report_verification.py --cell cell --gds cell.gds \\
        --netlist cell.spice --runs-dir path/to/iteration_0 --parse-only

Run the full verification flow::

    python3 scripts/report_verification.py --cell cell --gds cell.gds \\
        --netlist cell.spice --runs-dir path/to/runs
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


def _ensure_package_importable() -> None:
    """Make ``aion_layout`` importable without overriding an explicit PYTHONPATH.

    The graders are run from a copy of the package outside the repository, so
    whatever the caller put on ``PYTHONPATH`` is the copy that must be graded.
    This program used to insert its own ``__file__``-derived repository root at
    ``sys.path[0]``, which silently shadowed that copy with the working tree.
    The fallback roots below are therefore tried only when the import would
    otherwise fail, and are appended rather than inserted.
    """
    if importlib.util.find_spec("aion_layout") is not None:
        return
    here = Path(__file__).resolve()
    for root in (os.environ.get("AION_ROOT"), here.parent.parent, here.parent):
        if not root:
            continue
        candidate = Path(root)
        if (candidate / "aion_layout" / "__init__.py").is_file():
            sys.path.append(str(candidate))
            return


_ensure_package_importable()

# The leading-underscore helpers are the canonical artifact-discovery API of
# aion_layout.verification: they resolve the exact directories the sak-* scripts
# write and refuse anything else.  Re-deriving discovery here is what let this
# program and the library disagree, and a disagreement is a place to plant a
# report.  They are imported, not reimplemented.
from aion_layout.verification import (  # noqa: E402
    COMPLETENESS_DEGRADED,
    COMPLETENESS_NOT_APPLICABLE,
    COMPLETENESS_UNVERIFIED,
    COMPLETENESS_VERIFIED,
    DrcReport,
    LvsReport,
    VerificationError,
    locate_magic_drc_report,
    locate_netgen_lvs_report,
    parse_klayout_reports,
    parse_magic_drc_report,
    parse_netgen_lvs_report,
    run_drc,
    run_lvs,
)
from aion_layout.verification import (  # noqa: E402
    _find_klayout_lyrdbs as find_klayout_lyrdbs,
)

#: How the printed summary spells each ``DrcReport.completeness`` value.  A run
#: whose extent nobody recorded is not a graded run, so the word reaches the
#: reader on a line of its own rather than being folded into a count.
COMPLETENESS_LABELS = {
    COMPLETENESS_VERIFIED: "VERIFIED",
    COMPLETENESS_DEGRADED: "DEGRADED",
    COMPLETENESS_UNVERIFIED: "UNVERIFIED",
}

#: Exit statuses.  The caller distinguishes "verified and failed" from
#: "could not verify"; conflating them is what let a broken run read as clean.
EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_ERROR = 2

#: How many individual violations / pins to list per section.
MAX_LISTED = 8

_LABEL_W = 9

# ---------------------------------------------------------------------------
# Status taxonomy -- shared verbatim with scripts/evidence.py
# ---------------------------------------------------------------------------

#: Positive evidence that the artifact was produced and is clean.
STATUS_PASS = "PASS"
#: Positive evidence that the artifact was produced and records violations.
STATUS_FAIL = "FAIL"
#: The artifact does not exist, is empty, or carries no verdict of its own.
STATUS_UNAVAILABLE = "NOT AVAILABLE"
#: The artifact exists but could only be read in part.
STATUS_DEGRADED = "DEGRADED"

#: Statuses that mean "nothing was actually verified".  Any of them forces
#: ``RESULT: ERROR``: absence of evidence is not evidence of a clean layout.
STATUS_UNVERIFIED = (STATUS_UNAVAILABLE, STATUS_DEGRADED)

#: ``verification.LVS_VERDICTS`` members that carry no information either way.
#: The same set, under the same name, gates ``evidence.py``'s LVS verdict.
LVS_UNKNOWN_TOKENS = frozenset({"no_final_result", "uncertain"})


# ---------------------------------------------------------------------------
# Output sanitising
#
# Everything this program prints is composed from a literal prefix plus values
# that came from a report file, a tool, an exception or argv.  Each value is
# scrubbed to a single printable line before interpolation, so no value can ever
# begin a line; captured multi-line text goes through _VerdictStream.block(),
# which indents every line.  _VerdictStream then neutralises any line that would
# still start with "RESULT:", leaving exactly one -- the one finish() writes.
# ---------------------------------------------------------------------------

#: Cap on one interpolated value, so a huge path cannot flood a line.
_MAX_SCRUB_LEN = 400
#: Cap on an exception message, which legitimately names full paths.
_MAX_MESSAGE_LEN = 2000
#: Cap on how many lines of captured text a quoted block prints.
_MAX_BLOCK_LINES = 200

_RESULT_LINE_RE = re.compile(r"^RESULT\s*:", re.IGNORECASE)


def _scrub(value: object, max_len: int = _MAX_SCRUB_LEN, strip: bool = True) -> str:
    """Return ``value`` as a single line with control characters removed.

    Non-printable characters (newline, carriage return, ANSI escapes) become
    spaces rather than disappearing, so tokens cannot be glued together.
    """
    text = "".join(ch if ch.isprintable() else " " for ch in str(value))
    text = text.strip() if strip else text.rstrip()
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text


def _q(value: object) -> str:
    """Quote an externally controlled value for a single-line message."""
    return _scrub(repr(str(value)))


class _VerdictStream:
    """The program's only way out to stdout.

    ``line`` emits one scrubbed physical line; ``block`` emits indented,
    scrubbed captured text; ``finish`` emits the single ``RESULT:`` line and is
    called exactly once, from :func:`main`.
    """

    def __init__(self, stream=None) -> None:
        self._stream = stream if stream is not None else sys.stdout
        self._finished = False

    def _write(self, text: str) -> None:
        # A line that would start with "RESULT:" can only be injected content:
        # nothing in this program composes one except finish().
        if _RESULT_LINE_RE.match(text):
            text = "  (quoted) " + text
        self._stream.write(text + "\n")

    def line(self, text: str = "") -> None:
        """Emit one line; embedded control characters become spaces."""
        self._write(_scrub(text, max_len=_MAX_MESSAGE_LEN, strip=False))

    def block(self, text: str, prefix: str = "  ") -> None:
        """Emit captured text, indented so no line of it starts at column 0."""
        lines = str(text).splitlines()
        if len(lines) > _MAX_BLOCK_LINES:
            dropped = len(lines) - _MAX_BLOCK_LINES
            lines = lines[:_MAX_BLOCK_LINES] + [f"... {dropped} more line(s) omitted"]
        if not lines:
            lines = ["(no output)"]
        for raw in lines:
            self._write(prefix + _scrub(raw, max_len=_MAX_MESSAGE_LEN, strip=False))

    def finish(self, verdict: str) -> None:
        """Emit the one and only ``RESULT:`` line and flush."""
        if self._finished:  # pragma: no cover - main calls finish once
            raise RuntimeError("the verdict stream was already finished")
        self._finished = True
        self._stream.write(f"RESULT: {verdict}\n")
        self._stream.flush()


# ---------------------------------------------------------------------------
# Report discovery
#
# Canonical paths only.  sorted(rglob(...))[0] used to prefer whatever sorted
# first, so planting drc/<cell>/<cell>.magic.drc.rpt -- or drc/AAAA/... -- with
# an "[INFO] COUNT: 0" trailer replaced the real 8-violation report.  Discovery
# now targets <cell>.magic.drc/, <cell>.klayout.drc/ and <cell>.magic.lvs/ by
# name; a report anywhere else is not found, and not finding one is an error.
#
# The canonical *file name* is enforced too, by the same library call.  A lone
# match under another name still comes back -- refusing to read it would throw
# away the only evidence there is -- but carrying a note that this program
# prints and that forbids the report a clean grade.
# ---------------------------------------------------------------------------


def _collect_reports(
    cell_name: str,
    runs_dir: Path,
) -> Tuple[DrcReport, DrcReport, LvsReport, List[Path]]:
    """Parse the reports already on disk under ``runs_dir``.

    Returns ``(magic, klayout, lvs, lyrdbs)``.  A missing Magic or Netgen report
    raises :class:`VerificationError`: those two carry the verdict, so guessing
    would mean reporting a layout as clean that nothing ever checked.  A missing
    KLayout database is not fatal here -- it comes back as an unavailable report
    and is graded ``NOT AVAILABLE`` -- because the merge already knows how to say
    "no database", and saying so is more useful than a traceback.

    The ``locate_*`` calls return a note alongside the path, empty only when the
    file carried the exact name its tool writes.  The note is handed straight to
    the parser, which records it and refuses to call such a report clean; losing
    it here would restore the defect it exists to close.
    """
    magic_rpt, magic_note = locate_magic_drc_report(runs_dir, cell_name)
    lvs_rpt, lvs_note = locate_netgen_lvs_report(runs_dir, cell_name)
    klayout = parse_klayout_reports(runs_dir, cell_name)
    lyrdbs = find_klayout_lyrdbs(runs_dir, cell_name)
    return (
        parse_magic_drc_report(magic_rpt, location_note=magic_note),
        klayout,
        parse_netgen_lvs_report(lvs_rpt, location_note=lvs_note),
        lyrdbs,
    )


# ---------------------------------------------------------------------------
# Status classification
# ---------------------------------------------------------------------------

def _drc_status(report: DrcReport) -> Tuple[str, str]:
    """Return ``(status, reason)`` for one DRC engine.

    A report is ``PASS`` only on positive evidence: the tool ran, wrote the file
    it names, its whole output was read, the file *set* it produced is accounted
    for, and it recorded nothing.  Anything short of that is ``NOT AVAILABLE`` or
    ``DEGRADED`` -- never ``PASS``.

    ``reason`` is left empty where :func:`_emit_drc_tool` already prints the
    explanation on the ``completeness:`` line, so the reader is told once.
    """
    if not report.available:
        return STATUS_UNAVAILABLE, report.unavailable_reason or "no report file found"
    if report.violations:
        # Violations are positive evidence of failure however the run was
        # degraded; the degradation is still printed, just not as the headline.
        return STATUS_FAIL, ""
    if report.completeness == COMPLETENESS_DEGRADED:
        return STATUS_DEGRADED, ""
    if report.unparsed_files:
        return (
            STATUS_DEGRADED,
            f"{_plural(report.unparsed_files, 'report file')} could not be parsed, "
            "so a clean result cannot be confirmed",
        )
    if report.completeness == COMPLETENESS_UNVERIFIED:
        # Zero items out of a file set nobody vouched for.  The deleted rule
        # database that took the run's only violation with it looked exactly
        # like this.
        return STATUS_DEGRADED, ""
    return (STATUS_PASS if report.clean else STATUS_FAIL), ""


def _lvs_status(report: LvsReport) -> Tuple[str, str]:
    """Return ``(status, reason)`` for the Netgen run."""
    if report.verdict == "no_final_result":
        return STATUS_UNAVAILABLE, "Netgen printed no 'Final result:' line"
    if report.verdict == "uncertain":
        return STATUS_DEGRADED, "Netgen's final result could not be classified"
    if report.location_note and report.verdict == "match_uniquely":
        # A "match uniquely" nobody can attribute to Netgen is not a pass, and
        # it is not a measured failure either: it is an ungraded run.
        return STATUS_DEGRADED, report.location_note
    return (STATUS_PASS if report.clean else STATUS_FAIL), ""


def _overall(statuses: Sequence[str]) -> Tuple[str, int]:
    """Return ``(verdict, exit status)`` for a set of artifact statuses.

    ``PASS`` needs every artifact to be positively clean.  Everything else is
    ``FAIL``: a missing KLayout database, a Magic report with no ``COUNT``
    trailer, a partly-read merge and an unclassifiable Netgen verdict are all
    "not clean", and none of them is a reason to abort the loop that is trying
    to fix the layout.

    ``ERROR`` is reserved for a run that could not be graded at all -- the Magic
    or the Netgen report is not on disk -- which :func:`_collect_reports` raises
    on and :func:`main` reports.  ``evidence.py`` grades with the same tokens
    and the same precedence, so the two things the model is shown agree.
    """
    if all(status == STATUS_PASS for status in statuses):
        return "PASS", EXIT_PASS
    return "FAIL", EXIT_FAIL


def _unverified(*labelled: Tuple[str, str]) -> List[str]:
    """Return the labels of artifacts that produced no usable verdict."""
    return [label for label, status in labelled if status in STATUS_UNVERIFIED]


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _by_category(report: DrcReport) -> List[Tuple[str, int]]:
    """Return ``(category, count)`` pairs, most frequent first."""
    counts: Dict[str, int] = {}
    for violation in report.violations:
        counts[violation.category] = counts.get(violation.category, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def _emit_completeness(out: _VerdictStream, report: DrcReport) -> None:
    """Print how much of the run the count above was actually taken from.

    A violation count says nothing about the files it was *not* taken from.
    Deleting one rule database used to remove a whole rule table from the
    verdict without a word; the completeness grade is the word.  It is printed
    for a clean receipt too -- positive evidence that the set was whole is worth
    as much on the page as the absence of one.
    """
    if report.completeness == COMPLETENESS_NOT_APPLICABLE:
        return
    label = COMPLETENESS_LABELS.get(report.completeness, report.completeness)
    note = report.completeness_note
    out.line(f"    completeness: {label}{' - ' + note if note else ''}")
    if report.missing_databases:
        shown = list(report.missing_databases[:MAX_LISTED])
        out.line(
            f"    MISSING: {_plural(len(report.missing_databases), 'rule database')} "
            "named by the receipt were not on disk:"
        )
        for name in shown:
            out.line(f"      {name}")
        if len(report.missing_databases) > len(shown):
            out.line(f"      ... and {len(report.missing_databases) - len(shown)} more")


def _emit_drc_tool(
    out: _VerdictStream,
    label: str,
    report: DrcReport,
    status: str,
    reason: str,
    scanned: Optional[int] = None,
) -> None:
    """Print one DRC engine's result, never implying "clean" from silence."""
    if status == STATUS_UNAVAILABLE:
        out.line(f"  {label:<{_LABEL_W}}: {STATUS_UNAVAILABLE} ({reason})")
        return

    extra = ""
    mismatched = (
        report.reported_count is not None and report.reported_count != report.error_count
    )
    if report.reported_count is not None and (mismatched or report.tool == "magic"):
        extra = f" (tool reported COUNT: {report.reported_count})"
    if scanned is not None:
        extra += f" across {_plural(scanned, 'rule database')}"

    out.line(
        f"  {label:<{_LABEL_W}}: {status} - "
        f"{_plural(report.error_count, 'violation')}{extra}"
    )
    _emit_completeness(out, report)
    if reason:
        out.line(f"    NOT VERIFIED: {reason}")
    if mismatched:
        out.line(
            f"    WARNING: the tool reported {report.reported_count} violations but "
            f"{report.error_count} could be parsed"
        )
    if report.unparsed_files and status != STATUS_DEGRADED:
        # A DEGRADED report already said this on its NOT VERIFIED line.
        out.line(
            f"    WARNING: {_plural(report.unparsed_files, 'report file')} "
            "could not be parsed"
        )
    if report.location_note:
        out.line(f"    WARNING: NOT CANONICAL - {report.location_note}")
    if not report.violations:
        return

    out.line("    by category:")
    for category, count in _by_category(report):
        out.line(f"      {count:>4}  {category}")
    shown = list(report.violations[:MAX_LISTED])
    out.line(f"    first {len(shown)} of {report.error_count}:")
    for violation in shown:
        out.line(f"      {violation.bbox_str}  {violation.category}")
    if report.error_count > len(shown):
        out.line(f"      ... and {report.error_count - len(shown)} more")


def _emit_drc(
    out: _VerdictStream,
    magic: DrcReport,
    klayout: DrcReport,
    magic_status: Tuple[str, str],
    klayout_status: Tuple[str, str],
    klayout_scanned: Optional[int],
) -> None:
    """Print the ``DRC:`` block.  The header line is greppable as ``^DRC:``."""
    def part(label: str, report: DrcReport, status: str) -> str:
        # A count is only meaningful when the report was read whole; otherwise
        # the header must carry the status, or "klayout=0" reads as clean.
        if status in STATUS_UNVERIFIED:
            return f"{label}={status}"
        return f"{label}={report.error_count}"

    parts = [
        part("magic", magic, magic_status[0]),
        part("klayout", klayout, klayout_status[0]),
    ]
    status, _ = _overall([magic_status[0], klayout_status[0]])
    out.line(f"DRC: {status} ({', '.join(parts)})")
    _emit_drc_tool(out, "Magic", magic, magic_status[0], magic_status[1])
    _emit_drc_tool(
        out, "KLayout", klayout, klayout_status[0], klayout_status[1], klayout_scanned
    )


def _emit_lvs(out: _VerdictStream, report: LvsReport, status: Tuple[str, str]) -> None:
    """Print the ``LVS:`` block.  The header line is greppable as ``^LVS:``."""
    out.line(f"LVS: {status[0]} (verdict={report.verdict}, tool={report.tool})")
    out.line(f"  {report.message}")
    if report.location_note:
        out.line(f"  WARNING: NOT CANONICAL - {report.location_note}")
    if status[1] and status[1] != report.location_note:
        out.line(f"  NOT VERIFIED: {status[1]}")

    if report.device_total is not None:
        layout, schematic = report.device_total
        mark = "ok" if layout == schematic else "MISMATCH"
        out.line(f"  devices  : layout={layout} schematic={schematic}  {mark}")
    if report.net_counts is not None:
        layout, schematic = report.net_counts
        mark = "ok" if layout == schematic else "MISMATCH"
        out.line(f"  nets     : layout={layout} schematic={schematic}  {mark}")

    if report.device_counts:
        out.line("  device counts by type:")
        for device, (layout, schematic) in sorted(report.device_counts.items()):
            mark = "ok" if layout == schematic else "MISMATCH"
            out.line(f"    {mark:<8} {device}: layout={layout} schematic={schematic}")

    if report.disconnected_nodes:
        nodes = ", ".join(report.disconnected_nodes)
        out.line(f"  disconnected nodes ({len(report.disconnected_nodes)}): {nodes}")

    if report.unmatched_pins:
        out.line(f"  unmatched pins ({len(report.unmatched_pins)}):")
        for left, right in report.unmatched_pins[:MAX_LISTED]:
            out.line(f"    {left} | {right}")
        if len(report.unmatched_pins) > MAX_LISTED:
            out.line(f"    ... and {len(report.unmatched_pins) - MAX_LISTED} more")


def _emit_error(out: _VerdictStream, exc: BaseException, stage: str) -> None:
    """Print a verdict block for a run that could not produce one.

    This is the guard that keeps the program from ever exiting after the
    ``Cell:`` header alone.  The exception message and the traceback are
    attacker-reachable text, so the message is scrubbed to one line and the
    traceback is indented: neither can spell a verdict at column 0.
    """
    out.line(f"DRC: ERROR (no verdict: {stage})")
    out.line(f"LVS: ERROR (no verdict: {stage})")
    out.line()
    out.line(f"ERROR: {type(exc).__name__}: {_scrub(exc, max_len=_MAX_MESSAGE_LEN)}")
    out.line("Traceback:")
    out.block(
        "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    )
    out.line()


def _stderr_note(exc: BaseException) -> None:
    """Mirror the one-line error on stderr, scrubbed like everything else."""
    try:
        sys.stderr.write(
            f"{type(exc).__name__}: {_scrub(exc, max_len=_MAX_MESSAGE_LEN)}\n"
        )
        sys.stderr.flush()
    except Exception:  # pragma: no cover - stderr is not the verdict channel
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _default_run_script() -> str:
    """Return the DRC/LVS runner wrapper to use when one is not given.

    ``$AION_RUN_SCRIPT`` wins, so a caller running this program from a copy of
    the package outside the repository can point at the real wrapper without
    passing ``--run-script``.  Otherwise it is ``docker_run.sh`` beside this
    file.  Either way the value is only *consulted* on the non-``--parse-only``
    path: ``--parse-only`` starts no tool, so the wrapper need not exist for the
    host-side grading run to work.
    """
    env = os.environ.get("AION_RUN_SCRIPT")
    if env:
        return env
    return str(Path(__file__).resolve().parent / "docker_run.sh")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="One-page DRC/LVS summary for an AION cell.",
    )
    parser.add_argument("--cell", required=True, help="Cell name.")
    parser.add_argument(
        "--runs-dir",
        required=True,
        help="Directory containing generated artifacts.",
    )
    parser.add_argument(
        "--gds",
        required=True,
        help="Path to the GDS file.",
    )
    parser.add_argument(
        "--netlist",
        required=True,
        help="Path to the SPICE/CDL netlist.",
    )
    parser.add_argument(
        "--parse-only",
        action="store_true",
        help="Do not run tools; parse existing reports only.",
    )
    parser.add_argument(
        "--run-script",
        default=_default_run_script(),
        help="Path to the sak-drc.sh / sak-lvs.sh wrapper (default: scripts/docker_run.sh).",
    )
    return parser


def _run(out: _VerdictStream, args: argparse.Namespace) -> Tuple[str, int]:
    """Print the summary and return ``(verdict, exit status)``.

    May raise; :func:`main` catches everything and still emits a verdict.
    """
    runs_dir = Path(args.runs_dir)
    gds_path = Path(args.gds)
    netlist_path = Path(args.netlist)

    out.line(f"Cell:      {_scrub(args.cell)}")
    out.line(f"GDS:       {_scrub(gds_path)}")
    out.line(f"Netlist:   {_scrub(netlist_path)}")
    out.line(f"Runs dir:  {_scrub(runs_dir)}")
    out.line()

    if args.parse_only:
        magic_drc, klayout_drc, lvs, lyrdbs = _collect_reports(args.cell, runs_dir)
    else:
        if not gds_path.exists():
            raise VerificationError(f"GDS file not found: {_q(gds_path)}")
        if not netlist_path.exists():
            raise VerificationError(f"Netlist not found: {_q(netlist_path)}")
        # sak-drc.sh / sak-lvs.sh write <work_dir>/<cell>.<tool>.<step>/, and
        # pipeline.sh gives them iteration_N/drc and iteration_N/lvs.  Using the
        # same two work directories here is what makes a run and a later
        # --parse-only of the same tree look at the very same files.
        drc_work = runs_dir / "drc"
        lvs_work = runs_dir / "lvs"
        magic_drc, klayout_drc = run_drc(gds_path, drc_work, args.run_script)
        lvs = run_lvs(gds_path, netlist_path, args.cell, lvs_work, args.run_script)
        lyrdbs = find_klayout_lyrdbs(drc_work, args.cell)

    magic_status = _drc_status(magic_drc)
    klayout_status = _drc_status(klayout_drc)
    lvs_status = _lvs_status(lvs)

    _emit_drc(
        out,
        magic_drc,
        klayout_drc,
        magic_status,
        klayout_status,
        len(lyrdbs) or None,
    )
    out.line()
    _emit_lvs(out, lvs, lvs_status)
    out.line()

    verdict, status = _overall([magic_status[0], klayout_status[0], lvs_status[0]])
    unverified = _unverified(
        ("Magic DRC", magic_status[0]),
        ("KLayout DRC", klayout_status[0]),
        ("Netgen LVS", lvs_status[0]),
    )
    if unverified:
        out.line(
            f"  reason: {' and '.join(unverified)} produced no usable verdict; a "
            "report that is absent, empty, truncated or unreadable is NOT clean."
        )
        out.line()
    return verdict, status


def main(argv: Optional[List[str]] = None) -> int:
    """Parse arguments, print the summary, and never leave stdout verdict-free.

    Exactly one ``RESULT:`` line reaches stdout, written by
    :meth:`_VerdictStream.finish`, which is called on every path but ``--help``
    (argparse exits 0 there having printed usage and nothing a harness would
    read as a grade).
    """
    out = _VerdictStream()
    try:
        args = _build_parser().parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else EXIT_ERROR
        if code == EXIT_PASS:  # --help: usage text only, deliberately no verdict
            return EXIT_PASS
        _emit_error(out, exc, "invalid command line")
        out.finish("ERROR")
        return EXIT_ERROR

    try:
        verdict, status = _run(out, args)
    except BaseException as exc:  # noqa: BLE001 - the verdict must survive anything
        try:
            _emit_error(out, exc, "verification reporting raised")
        except BaseException:  # pragma: no cover - reporting the error failed
            out.line("ERROR: the error reporter itself raised; see stderr")
        out.finish("ERROR")
        _stderr_note(exc)
        return EXIT_ERROR

    out.finish(verdict)
    return status


if __name__ == "__main__":
    sys.exit(main())
