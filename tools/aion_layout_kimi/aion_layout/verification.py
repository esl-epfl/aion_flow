# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               DRC/LVS report parsing and runners
# ================================================================

"""Parse and run DRC/LVS verification for AION-generated layouts.

The module supports two workflows:

1. **Parse-only**: point it at existing report files and get structured data.
2. **Run + parse**: invoke the Docker runner (e.g. ``scripts/docker_run.sh sak-drc.sh``)
   and parse the generated reports.
"""

from __future__ import annotations

import dataclasses as dc
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# DRC completeness receipts
#
# Deleting a single rule database used to delete a whole rule *table* from the
# verdict in silence.  Removing ``*_latchup.lyrdb`` from a run left 30 readable,
# item-free databases behind, and the merge reported "PASS - 0 violations across
# 30 rule databases": the only real violation in the run had vanished and the
# headline read clean.  Nothing recorded how many databases the run had actually
# written, so "at least one readable file" was the entire completeness check.
#
# A count taken from the surviving files can never detect a missing file.  The
# DRC step therefore leaves a *receipt* beside the databases, naming what it
# produced, and the merge grades itself against that receipt:
#
#     <work_dir>/<cell>.klayout.drc/klayout.receipt.json
#     {
#       "tool": "klayout",
#       "cell": "AION_inv_nand2_nor2_1",
#       "exit_status": 1,
#       "databases": [
#         "AION_inv_nand2_nor2_1_AION_inv_nand2_nor2_1_activ.lyrdb",
#         "AION_inv_nand2_nor2_1_AION_inv_nand2_nor2_1_latchup.lyrdb"
#       ]
#     }
#
# ``databases``    -- one bare file name (no directory component) for every
#                     ``.lyrdb`` the runner wrote.  Required.
# ``exit_status``  -- the DRC runner's own exit status.  ``0`` (no violations)
#                     and ``1`` (violations found) are its two normal outcomes;
#                     any other value means it did not finish.  Required.
# ``tool``/``cell``-- informational, never graded on.
#
# Three cases, and only the first may ever be graded clean:
#
#   receipt matches what is on disk -> VERIFIED    a 0-item result may be clean
#   receipt names a file not found  -> DEGRADED    never clean; names the files
#   no receipt at all               -> UNVERIFIED  the items found are reported,
#                                                  but a 0-item result is NOT
#                                                  clean -- nothing says the run
#                                                  was whole
#
# The last case is what the committed fixtures exercise: they predate the
# receipt, carry one real LU.b item, and must keep reporting it and failing.
# ---------------------------------------------------------------------------

#: File name of the completeness receipt, inside the KLayout work directory.
KLAYOUT_RECEIPT_NAME = "klayout.receipt.json"

#: Completeness is not a question this artifact answers (e.g. a Magic report,
#: whose own ``[INFO] COUNT:`` trailer already says whether the tool finished).
COMPLETENESS_NOT_APPLICABLE = ""
#: A receipt was found and everything it names is present: 0 items may be clean.
COMPLETENESS_VERIFIED = "verified"
#: A receipt was found and does not match what is on disk, or the run did not
#: finish.  Never clean, whatever the item count says.
COMPLETENESS_DEGRADED = "degraded"
#: No receipt: the items found are real, but nothing proves they are all of
#: them, so a zero-item result is not evidence of a clean layout.
COMPLETENESS_UNVERIFIED = "unverified"

#: Exit statuses the DRC runner uses for a completed run (0 clean, 1 dirty).
_RECEIPT_NORMAL_EXITS = (0, 1)


@dc.dataclass(frozen=True)
class DrcViolation:
    """A single DRC violation with a category and bounding box."""

    category: str
    description: str
    cell: str
    bbox_um: Tuple[float, float, float, float]
    message: str = ""

    @property
    def bbox_str(self) -> str:
        """Return the bbox as a compact string."""
        x1, y1, x2, y2 = self.bbox_um
        return f"({x1:.3f},{y1:.3f})-({x2:.3f},{y2:.3f})"


@dc.dataclass(frozen=True)
class DrcReport:
    """Structured result of a DRC run.

    ``reported_count`` is the violation count the tool itself printed (Magic's
    ``[INFO] COUNT: <n>`` trailer), kept so a caller can detect a parser that
    went blind.  ``available`` is ``False`` when no report file existed at all
    *or* when the file that exists carries no evidence that the tool finished;
    such a report is never ``clean`` because nothing was actually verified, and
    ``unavailable_reason`` says which of the two it was.  ``unparsed_files``
    counts report files that could not be read, which also forces ``clean`` to
    ``False``.  ``location_note`` is set when the report was read from outside
    the canonical ``<cell>.<tool>.drc/`` directory *or* under a name the tool
    does not write; such a report can never be ``clean``.

    ``completeness`` says whether the *set* of files graded is known to be the
    set the run produced -- one of :data:`COMPLETENESS_VERIFIED`,
    :data:`COMPLETENESS_DEGRADED`, :data:`COMPLETENESS_UNVERIFIED` or
    :data:`COMPLETENESS_NOT_APPLICABLE` -- and ``completeness_note`` says why in
    words a reader can act on.  ``missing_databases`` names the files a receipt
    promised and disk did not deliver.  Only ``COMPLETENESS_VERIFIED`` (or
    ``COMPLETENESS_NOT_APPLICABLE``, for an artifact that carries its own
    completeness proof) lets a zero-violation report be ``clean``.
    """

    tool: str
    clean: bool
    violations: Sequence[DrcViolation]
    categories: Sequence[str]
    reported_count: Optional[int] = None
    available: bool = True
    unparsed_files: int = 0
    unavailable_reason: Optional[str] = None
    location_note: str = ""
    completeness: str = COMPLETENESS_NOT_APPLICABLE
    completeness_note: str = ""
    missing_databases: Tuple[str, ...] = ()

    @property
    def error_count(self) -> int:
        return len(self.violations)

    @property
    def degraded(self) -> bool:
        """True when the report is missing, partly parsed, or of unknown extent."""
        return (
            (not self.available)
            or self.unparsed_files > 0
            or self.completeness in (COMPLETENESS_DEGRADED, COMPLETENESS_UNVERIFIED)
        )


#: Every value :data:`LvsReport.verdict` may take.
LVS_VERDICTS = (
    "match_uniquely",
    "match_with_warnings",
    "do_not_match",
    "failed_pin_matching",
    "no_final_result",
    "uncertain",
)


@dc.dataclass(frozen=True)
class LvsReport:
    """Structured result of an LVS run.

    ``verdict`` is the classified Netgen ``Final result:`` line, one of
    :data:`LVS_VERDICTS`.  ``clean`` is ``True`` only for ``match_uniquely``
    read from a file the tool itself named; ``location_note``, when set, says
    the report was read from a non-canonical path or under a name Netgen does
    not write, and forces ``clean`` to ``False``.
    """

    tool: str
    clean: bool
    message: str
    device_counts: Dict[str, Tuple[int, int]] = dc.field(default_factory=dict)
    verdict: str = "uncertain"
    disconnected_nodes: List[str] = dc.field(default_factory=list)
    net_counts: Optional[Tuple[int, int]] = None
    device_total: Optional[Tuple[int, int]] = None
    unmatched_pins: List[Tuple[str, str]] = dc.field(default_factory=list)
    location_note: str = ""


class VerificationError(RuntimeError):
    """Raised when a verification command fails or reports are missing."""


# ---------------------------------------------------------------------------
# Output sanitising
#
# Report files, captured tool output and even path components are attacker
# reachable: the model under test writes into the build directory this module
# later parses.  A newline in any of them would let that content forge a line
# of its own -- ``RESULT: PASS`` at column 0 -- in the verdict stream the shell
# greps.  Everything externally controlled therefore leaves this module either
# scrubbed of control characters (:func:`_scrub`, :func:`_q`) or indented so no
# line of it can start at column 0 (:func:`_indent_block`).
# ---------------------------------------------------------------------------

#: Cap on one scrubbed value, so a huge path cannot flood a message.
_MAX_SCRUB_LEN = 400
#: Cap on how many lines of captured tool output an exception quotes.
_MAX_QUOTED_LINES = 200


def _scrub(value: object, max_len: int = _MAX_SCRUB_LEN, strip: bool = True) -> str:
    """Return ``value`` as a single line with control characters removed.

    Non-printable characters (newline, carriage return, ANSI escapes) become
    spaces rather than disappearing, so tokens cannot be glued together.
    """
    text = "".join(ch if ch.isprintable() else " " for ch in str(value))
    if strip:
        text = text.strip()
    else:
        text = text.rstrip()
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text


def _q(value: object) -> str:
    """Quote an externally controlled value for a single-line message.

    ``repr`` escapes newlines and terminal escapes; :func:`_scrub` then removes
    anything ``repr`` might have passed through.
    """
    return _scrub(repr(str(value)))


def _indent_block(text: str, prefix: str = "  | ") -> str:
    """Indent captured tool output so none of its lines can start at column 0."""
    lines = [_scrub(line, strip=False) for line in str(text).splitlines()]
    if len(lines) > _MAX_QUOTED_LINES:
        dropped = len(lines) - _MAX_QUOTED_LINES
        lines = lines[:_MAX_QUOTED_LINES] + [f"... {dropped} more line(s) omitted"]
    if not lines:
        lines = ["(no output)"]
    return "\n".join(prefix + line for line in lines)


# ---------------------------------------------------------------------------
# KLayout .lyrdb parsing
# ---------------------------------------------------------------------------

def parse_klayout_lyrdb(path: os.PathLike[str]) -> DrcReport:
    """Parse a KLayout DRC ``.lyrdb`` database.

    Returns a :class:`DrcReport` whose ``violations`` list contains every
    ``<item>`` in the report.
    """
    path = Path(path)
    if not path.exists():
        raise VerificationError(f"KLayout DRC report not found: {_q(path)}")

    tree = ET.parse(path)
    root = tree.getroot()

    categories: Dict[str, str] = {}
    for cat in root.iter("category"):
        # XML text is externally controlled: scrub it before it can reach a
        # verdict line the harness greps.
        name = _scrub(_text(cat, "name") or "")
        desc = _scrub(_text(cat, "description") or "")
        if name:
            categories[name] = desc

    violations: List[DrcViolation] = []
    for item in root.iter("item"):
        cat_name = _scrub((_text(item, "category") or "unknown").strip("'\""))
        cell_name = _scrub(_text(item, "cell") or "")
        desc = categories.get(cat_name, "")
        bbox = _parse_item_bbox(item)
        msg = f"{cat_name}: {desc}".strip()
        violations.append(
            DrcViolation(
                category=cat_name,
                description=desc,
                cell=cell_name,
                bbox_um=bbox,
                message=msg,
            )
        )

    return DrcReport(
        tool="klayout",
        clean=len(violations) == 0,
        violations=violations,
        categories=list(categories.keys()),
    )


def _read_klayout_receipt(directory: Path) -> Tuple[Optional[Dict[str, object]], str]:
    """Return ``(receipt, problem)`` for ``directory``'s completeness receipt.

    ``receipt`` is ``None`` both when the file is absent -- ``problem`` empty,
    which callers read as "completeness unverified" -- and when it exists but
    cannot be used, in which case ``problem`` says why.  The two are kept apart
    deliberately: a receipt that is present and unusable is a run that broke or
    a file that was edited, never merely a run that predates receipts.
    """
    path = directory / KLAYOUT_RECEIPT_NAME
    if not path.is_file():
        return None, ""
    try:
        data = json.loads(path.read_text(errors="replace"))
    except (OSError, ValueError) as exc:
        return None, f"the receipt {_q(path)} could not be read: {_scrub(exc)}"
    if not isinstance(data, dict):
        return None, f"the receipt {_q(path)} is not a JSON object"
    databases = data.get("databases")
    if not isinstance(databases, list) or not all(
        isinstance(name, str) for name in databases
    ):
        return None, (
            f"the receipt {_q(path)} carries no 'databases' list of file names, "
            "so it cannot say what the run produced"
        )
    return data, ""


def _klayout_completeness(
    directory: Path,
    found: Sequence[str],
) -> Tuple[str, Tuple[str, ...], str]:
    """Grade the merged database set against the receipt the DRC step left.

    Returns ``(completeness, missing_databases, note)``.  See the receipt
    section at the top of this module for the format and the three cases.
    ``found`` is the bare file name of every ``.lyrdb`` the merge picked up,
    readable or not: a file that exists but could not be parsed is a *parse*
    failure, counted separately, not a missing file.
    """
    receipt, problem = _read_klayout_receipt(directory)
    if problem:
        return COMPLETENESS_DEGRADED, (), problem
    if receipt is None:
        return (
            COMPLETENESS_UNVERIFIED,
            (),
            f"no {KLAYOUT_RECEIPT_NAME} in {_q(directory)}: nothing records the "
            "database set the run wrote, so a missing rule table would be "
            "invisible here and a zero-item result cannot be called clean",
        )

    declared = list(
        dict.fromkeys(Path(_scrub(name)).name for name in receipt["databases"])
    )
    present = set(found)
    missing = tuple(name for name in declared if name not in present)
    extra = tuple(sorted(name for name in present if name not in declared))
    exit_status = receipt.get("exit_status")

    faults: List[str] = []
    if missing:
        faults.append(
            f"{len(missing)} of the {len(declared)} rule database(s) named by "
            "the receipt are missing: " + ", ".join(_q(name) for name in missing)
        )
    if extra:
        faults.append(
            f"{len(extra)} database(s) the receipt does not name were found: "
            + ", ".join(_q(name) for name in extra)
        )
    if isinstance(exit_status, bool) or not isinstance(exit_status, int):
        faults.append(
            f"the receipt records no integer 'exit_status' ({_q(exit_status)}), "
            "so nothing says the runner finished"
        )
    elif exit_status not in _RECEIPT_NORMAL_EXITS:
        faults.append(
            f"the DRC runner exited {exit_status}, which is neither 0 (no "
            "violations) nor 1 (violations found): the run did not finish"
        )
    if faults:
        return COMPLETENESS_DEGRADED, missing, "; ".join(faults)
    return (
        COMPLETENESS_VERIFIED,
        (),
        f"receipt matches: all {len(declared)} rule database(s) the run wrote "
        "were read",
    )


def parse_klayout_reports(
    work_dir: os.PathLike[str],
    cell_name: Optional[str] = None,
) -> DrcReport:
    """Merge every KLayout ``.lyrdb`` under ``work_dir`` into a single report.

    ``sak-drc.sh -k`` at level ``macro`` writes one database *per rule table*
    (``*_activ.lyrdb``, ``*_latchup.lyrdb``, ...) and never a combined
    ``*_full.lyrdb``, so the reports must be merged.  ``cell_name``, when given,
    restricts the merge to files whose name mentions that cell (ignored when no
    file matches).

    Files that are not readable XML are skipped and counted in
    ``unparsed_files`` instead of aborting the merge.  A work directory holding
    no ``.lyrdb`` at all yields ``available=False`` rather than an exception --
    a missing KLayout run is a degradation to report, not a crash.  Neither a
    missing nor a partially read report is ever ``clean``.

    Nor is a report whose *extent* is unknown.  Counting items across the files
    that happen to be present cannot notice a file that is not: deleting
    ``*_latchup.lyrdb`` used to turn the run's only violation into
    "0 violations across 30 rule databases".  The merge therefore grades itself
    against the receipt the DRC step leaves in the database directory (see
    :data:`KLAYOUT_RECEIPT_NAME` and the receipt section at the top of this
    module) and reports the result in ``completeness``: only a run whose
    database set is confirmed whole may be ``clean`` with zero items.

    Only the canonical ``<cell>.klayout.drc/`` directory is merged (see
    :func:`_klayout_lyrdb_sources`); databases read from anywhere else are
    flagged in ``location_note`` and can never be ``clean``.
    """
    work_dir = Path(work_dir)
    paths, location_note = _klayout_lyrdb_sources(work_dir, cell_name)
    if not paths:
        return DrcReport(
            tool="klayout",
            clean=False,
            violations=[],
            categories=[],
            available=False,
            unavailable_reason=(
                f"no *.lyrdb in the canonical "
                f"<cell>.{KLAYOUT_DRC_DIR_SUFFIX}/ directory under {_q(work_dir)}"
            ),
        )

    violations: List[DrcViolation] = []
    unparsed = 0
    for path in paths:
        try:
            report = parse_klayout_lyrdb(path)
        except (ET.ParseError, VerificationError, OSError):
            unparsed += 1
            continue
        violations.extend(report.violations)

    # Only categories that actually carry an item are interesting: every rule
    # table declares its category even when it found nothing.
    categories = list(dict.fromkeys(v.category for v in violations))

    completeness, missing, note = _klayout_completeness(
        paths[0].parent, [path.name for path in paths]
    )
    if location_note:
        # Databases read from a directory no tool writes are not a set anyone
        # vouched for, whatever a receipt sitting beside them claims.
        completeness = COMPLETENESS_DEGRADED
        note = f"{location_note}; {note}" if note else location_note

    return DrcReport(
        tool="klayout",
        clean=(
            not violations
            and unparsed == 0
            and completeness == COMPLETENESS_VERIFIED
        ),
        violations=violations,
        categories=categories,
        reported_count=len(violations),
        available=True,
        unparsed_files=unparsed,
        location_note=location_note,
        completeness=completeness,
        completeness_note=note,
        missing_databases=missing,
    )


def _text(parent: ET.Element, tag: str) -> Optional[str]:
    elem = parent.find(tag)
    return elem.text if elem is not None else None


def _parse_item_bbox(item: ET.Element) -> Tuple[float, float, float, float]:
    """Extract the bbox from a KLayout ``<item>`` element.

    KLayout reports items as a ``<box>`` element, a list of ``<point>``
    vertices, or as a ``<values>`` polygon string.  We return
    ``(x1, y1, x2, y2)`` in microns.
    """
    box = item.find("box")
    if box is not None:
        return _parse_box(box)

    points: List[Tuple[float, float]] = []
    for point in item.iter("point"):
        x = _float_text(point, "x")
        y = _float_text(point, "y")
        if x is not None and y is not None:
            points.append((x, y))
    if points:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return (min(xs), min(ys), max(xs), max(ys))

    # KLayout macro DRC writes polygon coordinates inside <values>.
    values = item.find("values")
    if values is not None:
        for value in values.iter("value"):
            text = value.text or ""
            if "polygon:" in text:
                pts = _parse_polygon_value(text)
                if pts:
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    return (min(xs), min(ys), max(xs), max(ys))

    return (0.0, 0.0, 0.0, 0.0)


_POLYGON_VALUE_RE = re.compile(r"\(\s*([^)]+)\s*\)")


def _parse_polygon_value(text: str) -> List[Tuple[float, float]]:
    """Parse ``polygon: (x1,y1;x2,y2;...)`` into a list of points."""
    match = _POLYGON_VALUE_RE.search(text)
    if not match:
        return []
    points: List[Tuple[float, float]] = []
    for pair in match.group(1).split(";"):
        pair = pair.strip()
        if not pair:
            continue
        parts = pair.split(",")
        if len(parts) != 2:
            continue
        try:
            points.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue
    return points


def _parse_box(box: ET.Element) -> Tuple[float, float, float, float]:
    x1 = _float_text(box, "x1") or 0.0
    y1 = _float_text(box, "y1") or 0.0
    x2 = _float_text(box, "x2") or 0.0
    y2 = _float_text(box, "y2") or 0.0
    return (x1, y1, x2, y2)


def _float_text(parent: ET.Element, tag: str) -> Optional[float]:
    text = _text(parent, tag)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Magic DRC report parsing
# ---------------------------------------------------------------------------

_MAGIC_DELIM_RE = re.compile(r"^-{5,}\s*$")
_MAGIC_COUNT_RE = re.compile(r"^\s*\[INFO\]\s*COUNT:\s*(\d+)", re.MULTILINE)
_LENGTH_RE = re.compile(
    r"^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*(um|nm|u|n)?$"
)
#: Multiplier that converts a recognised unit suffix into microns.
_LENGTH_UNITS_UM = {None: 1.0, "um": 1.0, "u": 1.0, "nm": 1e-3, "n": 1e-3}


def _parse_length_um(token: str) -> Optional[float]:
    """Parse a length token such as ``0.240um``, ``240nm`` or ``0.24`` to microns.

    Returns ``None`` for anything that is not a length, so callers can use it to
    tell coordinate rows apart from prose.
    """
    match = _LENGTH_RE.match(token.strip())
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value * _LENGTH_UNITS_UM[match.group(2)]


def parse_magic_drc_report(
    path: os.PathLike[str],
    *,
    location_note: str = "",
) -> DrcReport:
    """Parse a Magic DRC ``*.magic.drc.rpt`` file.

    The report is split into sections by rule name.  Each section header is a
    delimiter line, a title line, and another delimiter line; the section body
    lists the bounding boxes of the violations in microns as ``x1 y1 x2 y2``.

    A report is only ``clean`` when Magic's own ``[INFO] COUNT: 0`` trailer says
    so.  A file with no trailer at all -- 0 bytes, header only, truncated
    mid-table, binary garbage, or a future format this parser cannot read -- is
    returned with ``clean=False`` and ``available=False``: nothing in it is
    evidence that Magic ran to completion, and absence of evidence has never
    been evidence of a clean layout.

    ``location_note``, when the caller passes one, records that the file was not
    at the path or under the name Magic writes -- see
    :func:`locate_magic_drc_report`.  The rows in such a file are still reported,
    because a violation is evidence whoever wrote it, but the report is marked
    :data:`COMPLETENESS_DEGRADED` and can never come back ``clean``: a
    ``planted.magic.drc.rpt`` carrying ``[INFO] COUNT: 0`` is not Magic saying
    the layout is clean.
    """
    path = Path(path)
    if not path.exists():
        raise VerificationError(f"Magic DRC report not found: {_q(path)}")

    # A report full of binary garbage must degrade to "unreadable", never to an
    # unhandled UnicodeDecodeError and never to silence.
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    count_matches = _MAGIC_COUNT_RE.findall(text)
    reported_count = int(count_matches[-1]) if count_matches else None
    violations: List[DrcViolation] = []
    categories: List[str] = []
    current_category = "unknown"
    current_description = ""

    def non_empty_index(start: int) -> int:
        while start < len(lines) and lines[start].strip() == "":
            start += 1
        return start

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if _MAGIC_DELIM_RE.match(line):
            title_idx = non_empty_index(i + 1)
            if title_idx >= len(lines):
                break
            title = lines[title_idx].strip()
            next_delim_idx = non_empty_index(title_idx + 1)
            if next_delim_idx < len(lines) and _MAGIC_DELIM_RE.match(lines[next_delim_idx].strip()):
                # Valid section header: delimiter + title + delimiter.
                # The title is file content: scrub it before it can become a
                # line of its own in a printed verdict.
                current_category = _scrub(title)
                categories.append(current_category)
                if "(" in current_category:
                    current_description = current_category[
                        current_category.find("(") + 1 : current_category.find(")")
                    ]
                else:
                    current_description = current_category
                i = next_delim_idx + 1
                continue

        parts = line.split()
        if len(parts) == 4:
            coords = [_parse_length_um(p) for p in parts]
            if any(c is None for c in coords):
                i += 1
                continue
            x1, y1, x2, y2 = coords  # type: ignore[assignment]
            violations.append(
                DrcViolation(
                    category=current_category,
                    description=current_description,
                    cell="",
                    bbox_um=(x1, y1, x2, y2),
                    message=f"{current_category}: ({x1:.3f},{y1:.3f})-({x2:.3f},{y2:.3f})",
                )
            )
        i += 1

    if reported_count is not None and reported_count > 0 and not violations:
        raise VerificationError(
            f"Magic reported {reported_count} DRC violation(s) in {_q(path)} but "
            "none could be parsed; refusing to report a clean layout."
        )

    if reported_count is None:
        # No ``[INFO] COUNT:`` trailer: Magic never said it finished.  Whatever
        # rows did parse are kept as evidence, but the report is degraded, not
        # clean -- a 0-byte or truncated file used to read as a clean layout.
        return DrcReport(
            tool="magic",
            clean=False,
            violations=violations,
            categories=list(dict.fromkeys(categories)),
            reported_count=None,
            available=False,
            location_note=location_note,
            completeness=(
                COMPLETENESS_DEGRADED if location_note
                else COMPLETENESS_NOT_APPLICABLE
            ),
            completeness_note=location_note,
            unavailable_reason=(
                f"no '[INFO] COUNT:' trailer in {_q(path)} ({len(text)} chars, "
                f"{len(violations)} row(s) parsed): the report is empty, "
                "truncated or in an unknown format, so Magic cannot be said to "
                "have finished"
            ),
        )

    return DrcReport(
        tool="magic",
        clean=not violations and reported_count == 0 and not location_note,
        violations=violations,
        categories=list(dict.fromkeys(categories)),
        reported_count=reported_count,
        location_note=location_note,
        completeness=(
            COMPLETENESS_DEGRADED if location_note else COMPLETENESS_NOT_APPLICABLE
        ),
        completeness_note=location_note,
    )


# ---------------------------------------------------------------------------
# Netgen LVS report parsing
# ---------------------------------------------------------------------------

_LVS_FINAL_MARKER = "Final result:"
_LVS_DEV_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+\(\s*(\d+)\s*\)\s+\|\s*([A-Za-z_][A-Za-z0-9_]*)\s+\(\s*(\d+)\s*\)",
    re.MULTILINE,
)
_LVS_DISCONNECTED_RE = re.compile(
    r"^Cell\s+\S+\s+\(\s*\d+\s*\)\s+disconnected node:\s*(\S+)", re.MULTILINE
)
_LVS_NETS_RE = re.compile(
    r"Number of nets:\s*(\d+)[^|\n]*\|[^|\n]*Number of nets:\s*(\d+)"
)
_LVS_DEVICES_RE = re.compile(
    r"Number of devices:\s*(\d+)[^|\n]*\|[^|\n]*Number of devices:\s*(\d+)"
)
#: ``*.lvs.log`` states the same totals in prose instead of a two-column table.
_LVS_LOG_NETS_RE = re.compile(
    r"Circuit 1 contains\s*(\d+)\s*nets?,\s*Circuit 2 contains\s*(\d+)\s*nets?"
)
_LVS_LOG_DEVICES_RE = re.compile(
    r"Circuit 1 contains\s*(\d+)\s*devices?,\s*Circuit 2 contains\s*(\d+)\s*devices?"
)
_LVS_PINS_HEADER = "Subcircuit pins:"
_LVS_TABLE_END_RE = re.compile(r"^-{5,}$")
_LVS_NO_PIN_RE = re.compile(r"^\((?:no pin, node is\b|no matching pin\b)")

_LVS_VERDICT_MESSAGES = {
    "match_uniquely": "Circuits match uniquely.",
    "match_with_warnings": (
        "Circuits match, but Netgen reported property errors or warnings."
    ),
    "do_not_match": "Circuits do not match.",
    "failed_pin_matching": (
        "Top level cell failed pin matching: the layout ports do not correspond "
        "to the schematic ports."
    ),
    "no_final_result": (
        "Netgen printed no 'Final result:' line; the LVS run did not complete."
    ),
    "uncertain": "Netgen reported an unrecognised final result.",
}


def _lvs_final_result_text(lines: Sequence[str]) -> Optional[str]:
    """Return the text of the *last* ``Final result:`` line, or ``None``.

    Netgen prints one such line per compared cell; only the last one is the
    top-level verdict.  In ``*.lvs.log`` the verdict is wrapped onto the
    following line, so an empty remainder continues on the next non-empty line.
    """
    index = None
    for i, line in enumerate(lines):
        if _LVS_FINAL_MARKER in line:
            index = i
    if index is None:
        return None

    text = lines[index].split(_LVS_FINAL_MARKER, 1)[1].strip()
    j = index + 1
    while not text and j < len(lines):
        text = lines[j].strip()
        j += 1
    return text


def _classify_lvs_verdict(text: Optional[str]) -> str:
    """Classify a Netgen final-result sentence into one of :data:`LVS_VERDICTS`."""
    if text is None:
        return "no_final_result"
    low = text.lower()
    if not low:
        return "uncertain"
    if "pin" in low and ("fail" in low or "mismatch" in low):
        return "failed_pin_matching"
    if "do not match" in low or "does not match" in low:
        return "do_not_match"
    if "match uniquely" in low:
        if "propert" in low or "warning" in low or "error" in low:
            return "match_with_warnings"
        return "match_uniquely"
    if "match" in low:
        if "fail" in low or "mismatch" in low:
            return "do_not_match"
        return "match_with_warnings"
    return "uncertain"


def _parse_lvs_unmatched_pins(lines: Sequence[str]) -> List[Tuple[str, str]]:
    """Return the unmatched rows of the final ``Subcircuit pins:`` table.

    A row is unmatched when either side reads ``(no pin, node is X)`` or
    ``(no matching pin)``.
    """
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith(_LVS_PINS_HEADER):
            start = i
    if start is None:
        return []

    rows: List[Tuple[str, str]] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if _LVS_TABLE_END_RE.match(stripped):
            break
        if "|" not in line:
            continue
        left, right = (part.strip() for part in line.split("|", 1))
        if _LVS_NO_PIN_RE.match(left) or _LVS_NO_PIN_RE.match(right):
            rows.append((_scrub(left), _scrub(right)))
    return rows


def _last_int_pair(*patterns: re.Pattern[str], text: str) -> Optional[Tuple[int, int]]:
    """Return the last ``(a, b)`` pair matched by the first pattern that hits."""
    for pattern in patterns:
        matches = pattern.findall(text)
        if matches:
            return (int(matches[-1][0]), int(matches[-1][1]))
    return None


def parse_netgen_lvs_report(
    path: os.PathLike[str],
    *,
    location_note: str = "",
) -> LvsReport:
    """Parse a Netgen ``*.lvs.out`` or ``*.lvs.log`` file.

    ``location_note`` records that the file was not at the path or under the
    name ``sak-lvs.sh`` writes -- see :func:`locate_netgen_lvs_report`.  Its
    contents are still reported, but ``clean`` is forced to ``False``: a
    ``match uniquely`` in a file nobody can attribute to Netgen is not a pass.
    """
    path = Path(path)
    if not path.exists():
        raise VerificationError(f"Netgen LVS report not found: {_q(path)}")

    text = path.read_text(errors="replace")
    lines = text.splitlines()

    final_text = _lvs_final_result_text(lines)
    verdict = _classify_lvs_verdict(final_text)
    message = _LVS_VERDICT_MESSAGES[verdict]
    if verdict in ("uncertain", "do_not_match") and final_text:
        # ``final_text`` is file content and ends up in a printed report.
        message = f"{message} Netgen said: {_scrub(final_text)}"

    device_counts: Dict[str, Tuple[int, int]] = {}
    for match in _LVS_DEV_RE.finditer(text):
        device_counts[match.group(1)] = (int(match.group(2)), int(match.group(4)))

    disconnected_nodes = list(
        dict.fromkeys(_scrub(node) for node in _LVS_DISCONNECTED_RE.findall(text))
    )

    net_counts = _last_int_pair(_LVS_NETS_RE, _LVS_LOG_NETS_RE, text=text)
    device_total = _last_int_pair(_LVS_DEVICES_RE, _LVS_LOG_DEVICES_RE, text=text)

    return LvsReport(
        tool="netgen",
        clean=verdict == "match_uniquely" and not location_note,
        message=message,
        device_counts=device_counts,
        verdict=verdict,
        disconnected_nodes=disconnected_nodes,
        net_counts=net_counts,
        device_total=device_total,
        unmatched_pins=_parse_lvs_unmatched_pins(lines),
        location_note=location_note,
    )


# ---------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------

_RunResult = Tuple[bool, str]


def _run_cmd(cmd: Sequence[str], cwd: Optional[Path] = None) -> _RunResult:
    proc = subprocess.run(
        list(cmd),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    output = proc.stdout + proc.stderr
    return proc.returncode == 0, output


def _default_run_script() -> Path:
    """Return the local docker_run.sh path relative to this module."""
    return Path(__file__).resolve().parent.parent / "scripts" / "docker_run.sh"


def _repo_root(run_script: Path) -> Path:
    """Return the ``tools/aion_layout`` directory the sak-* scripts run from.

    The wrapper lives at ``<aion_layout>/scripts/docker_run.sh``, so its
    grandparent *is* ``tools/aion_layout``; callers must not append those two
    components again.
    """
    return run_script.resolve().parent.parent


def run_drc(
    gds_path: os.PathLike[str],
    work_dir: os.PathLike[str],
    run_script: os.PathLike[str] = _default_run_script(),
) -> Tuple[DrcReport, DrcReport]:
    """Run both Magic and KLayout DRC and return parsed reports.

    ``work_dir`` must not exist or will be removed before the run so that stale
    reports are not parsed by accident.
    """
    script = Path(run_script).resolve()
    if not script.exists():
        raise VerificationError(f"DRC runner script not found: {_q(script)}")

    # The docker_run.sh wrapper mounts the project directory at
    # /foss/designs/aion_flow and the sak-* scripts are invoked from
    # tools/aion_layout.  Paths passed to sak-* must therefore be relative to
    # tools/aion_layout, which is exactly what _repo_root() returns: appending
    # "tools"/"aion_layout" again resolved every relative path one level too
    # high inside the container.
    aion_layout_root = _repo_root(script)
    gds_path = Path(gds_path)
    work_dir = Path(work_dir)

    def rel(p: Path) -> str:
        return os.path.relpath(p.resolve(), aion_layout_root)

    if work_dir.exists():
        import shutil

        shutil.rmtree(work_dir)

    success, output = _run_cmd(
        [
            str(script),
            "cd tools/aion_layout && sak-drc.sh",
            "-d", "-b", "-l", "macro",
            "-w", rel(work_dir),
            rel(gds_path),
        ],
        cwd=_repo_root(script),
    )
    if not success and "No DRC errors" not in output:
        # The script exits 1 only when violations are found; that is still a
        # valid report, so we only raise on a real runner failure.
        if not work_dir.exists():
            raise VerificationError(
                "DRC runner failed; captured output follows, indented so no "
                "line of it can be read as a verdict:\n" + _indent_block(output)
            )

    cell_name = gds_path.stem
    magic_rpt, magic_note = locate_magic_drc_report(work_dir, cell_name)
    return (
        parse_magic_drc_report(magic_rpt, location_note=magic_note),
        parse_klayout_reports(work_dir, cell_name),
    )


def run_lvs(
    gds_path: os.PathLike[str],
    netlist_path: os.PathLike[str],
    cell_name: str,
    work_dir: os.PathLike[str],
    run_script: os.PathLike[str] = _default_run_script(),
) -> LvsReport:
    """Run Magic+Netgen LVS and return a parsed report."""
    script = Path(run_script).resolve()
    if not script.exists():
        raise VerificationError(f"LVS runner script not found: {_q(script)}")

    aion_layout_root = _repo_root(script)  # already <repo>/tools/aion_layout
    gds_path = Path(gds_path)
    netlist_path = Path(netlist_path)
    work_dir = Path(work_dir)

    def rel(p: Path) -> str:
        return os.path.relpath(p.resolve(), aion_layout_root)

    if work_dir.exists():
        import shutil

        shutil.rmtree(work_dir)

    success, output = _run_cmd(
        [
            str(script),
            "cd tools/aion_layout && sak-lvs.sh",
            "-d", "-b",
            "-w", rel(work_dir),
            "-s", rel(netlist_path),
            "-l", rel(gds_path),
            "-c", cell_name,
        ],
        cwd=_repo_root(script),
    )
    if not success and "match" not in output.lower():
        if not work_dir.exists():
            raise VerificationError(
                "LVS runner failed; captured output follows, indented so no "
                "line of it can be read as a verdict:\n" + _indent_block(output)
            )

    lvs_out, lvs_note = locate_netgen_lvs_report(work_dir, cell_name)
    return parse_netgen_lvs_report(lvs_out, location_note=lvs_note)


def verify(
    cell_name: str,
    gds_path: os.PathLike[str],
    netlist_path: os.PathLike[str],
    runs_dir: os.PathLike[str] = Path("runs"),
    run_script: os.PathLike[str] = _default_run_script(),
) -> Dict[str, object]:
    """Run DRC and LVS for ``cell_name`` and return a combined summary dict.

    The layout used is ``<runs_dir>/<cell_name>.gds`` and reports are written
    to ``<runs_dir>/drc/<cell_name>`` and ``<runs_dir>/lvs/<cell_name>``.
    """
    runs_dir = Path(runs_dir)
    gds_path = Path(gds_path)
    netlist_path = Path(netlist_path)

    drc_work = runs_dir / "drc" / cell_name
    lvs_work = runs_dir / "lvs" / cell_name

    magic_drc, klayout_drc = run_drc(gds_path, drc_work, run_script)
    lvs = run_lvs(gds_path, netlist_path, cell_name, lvs_work, run_script)

    return {
        "cell": cell_name,
        "gds": str(gds_path),
        "netlist": str(netlist_path),
        "drc": {
            "magic": magic_drc,
            "klayout": klayout_drc,
            "clean": magic_drc.clean and klayout_drc.clean,
        },
        "lvs": lvs,
        "passed": magic_drc.clean and klayout_drc.clean and lvs.clean,
    }


# ---------------------------------------------------------------------------
# Canonical artifact discovery
#
# ``sak-drc.sh`` / ``sak-lvs.sh`` write exactly these directories under the
# work directory they are given, so discovery targets them by name.  It never
# walks the tree: ``sorted(rglob(...))[0]`` let a planted
# ``drc/AAAA/<cell>.magic.drc.rpt`` (alphabetically ahead of the real
# ``drc/<cell>.magic.drc/``) outrank the genuine report and flip a dirty layout
# to RESULT: PASS.  A report that is not where the tool puts it is refused by
# name, or -- for the merged KLayout databases, where the caller may legitimately
# point at a directory of its own -- reported through ``location_note``.
#
# The *directory* was not enough.  Enforcing the canonical directory while
# leaving the file name free meant that deleting the real report and dropping a
# ``planted.magic.drc.rpt`` carrying ``[INFO] COUNT: 0`` into the very same
# directory produced "Magic : PASS - 0 violations": a lone match won by being
# lone.  The exact name the tool writes is now required, and a differently-named
# lone match is accepted only carrying a note that travels to the printed
# summary and forbids a clean grade.
#
# :func:`canonical_report_dirs` is the single definition of "canonical" for the
# whole flow; ``scripts/evidence.py`` imports it rather than restating it, so the
# two graders cannot disagree about where a report may live.  They did: one
# resolved ``<iter>/<cell>.magic.drc`` before ``<iter>/drc/<cell>.magic.drc``,
# the opposite of where the tools write, and a disagreement between two graders
# is a place to plant a report.
# ---------------------------------------------------------------------------

#: Directory ``sak-drc.sh`` writes the Magic DRC report into.
MAGIC_DRC_DIR_SUFFIX = "magic.drc"
#: Directory ``sak-drc.sh -k`` writes the per-rule-table KLayout databases into.
KLAYOUT_DRC_DIR_SUFFIX = "klayout.drc"
#: Directory ``sak-lvs.sh`` writes the Netgen reports into.
MAGIC_LVS_DIR_SUFFIX = "magic.lvs"


def canonical_report_dirs(
    work_dir: os.PathLike[str],
    cell_name: Optional[str],
    suffix: str,
    *,
    existing_only: bool = True,
) -> List[Path]:
    """Return the directories a report of kind ``suffix`` may legitimately sit in.

    This is the one definition of "canonical" in the flow.  Import it; do not
    restate it.  In priority order:

    1. ``<work_dir>/drc|lvs/<cell>.<suffix>`` -- where the tools write when the
       caller hands over the *iteration* directory, which is what ``pipeline.sh``
       does;
    2. ``<work_dir>/<cell>.<suffix>`` -- the same directory when the caller hands
       over the ``drc/`` or ``lvs/`` work directory itself;
    3. ``work_dir`` when it already *is* such a directory.

    The order only decides which name an error message leads with: a caller that
    finds a report in more than one of these refuses outright rather than
    preferring one (see :func:`_one_canonical_dir`).

    With ``existing_only`` (the default) only directories that exist come back,
    and a call with no ``cell_name`` may additionally discover ``*.<suffix>/``
    immediately below ``work_dir``.  With ``existing_only=False`` the two named
    spellings are returned whether or not they exist, so a caller can say in an
    error message where it looked; that form needs a ``cell_name`` and returns
    an empty list without one.

    Raises :class:`VerificationError` for a ``cell_name`` that is not a single
    path component: a name with a separator in it would let the caller point
    discovery anywhere at all.
    """
    work_dir = Path(work_dir)
    if cell_name and Path(cell_name).name != cell_name:
        raise VerificationError(
            f"cell name {_q(cell_name)} is not a single path component; refusing "
            "to build a report path from it."
        )
    parent = "lvs" if suffix.endswith(".lvs") else "drc"
    candidates: List[Path] = []
    if cell_name:
        candidates.append(work_dir / parent / f"{cell_name}.{suffix}")
        candidates.append(work_dir / f"{cell_name}.{suffix}")
    if not existing_only:
        return candidates
    if work_dir.name.endswith(f".{suffix}"):
        candidates.append(work_dir)
    elif not cell_name:
        # Without a cell name the canonical directory can only be recognised by
        # its suffix, and only immediately below the work directory.
        candidates.extend(sorted(p for p in work_dir.glob(f"*.{suffix}") if p.is_dir()))
    dirs: List[Path] = []
    for candidate in candidates:
        if candidate.is_dir() and candidate not in dirs:
            dirs.append(candidate)
    return dirs


#: Former private spelling of :func:`canonical_report_dirs`, kept so an existing
#: import keeps working.  New callers use the public name.
_canonical_report_dirs = canonical_report_dirs


def _dirs_holding(dirs: Sequence[Path], patterns: Sequence[str]) -> List[Path]:
    """Return the directories of ``dirs`` that hold at least one match."""
    holders: List[Path] = []
    for directory in dirs:
        for pattern in patterns:
            if any(path.is_file() for path in directory.glob(pattern)):
                holders.append(directory)
                break
    return holders


def _one_canonical_dir(
    work_dir: Path,
    cell_name: Optional[str],
    suffix: str,
    patterns: Sequence[str],
    kind: str,
) -> Optional[Path]:
    """Return the single canonical directory holding a report, or ``None``.

    Two canonical directories holding the same kind of report is an ambiguity,
    not a preference: exactly one of them is where the tool wrote, and guessing
    which is how a planted report answers for a real one.  Refusing costs an
    ERROR verdict; guessing costs a false PASS.
    """
    holders = _dirs_holding(
        canonical_report_dirs(work_dir, cell_name, suffix), patterns
    )
    if len(holders) > 1:
        raise VerificationError(
            f"{kind}: {len(holders)} canonical directories under {_q(work_dir)} "
            "hold one -- "
            + ", ".join(_q(directory) for directory in holders)
            + "; only one of them can be the run's, and choosing between them "
            "would mean grading a report the tool may never have written."
        )
    return holders[0] if holders else None


def _single_file(
    directory: Path,
    exact: str,
    pattern: str,
    kind: str,
) -> Tuple[Optional[Path], str]:
    """Return ``(path, note)`` for the one ``pattern`` file in ``directory``.

    ``directory/exact`` -- the name the tool itself writes -- wins outright and
    comes back with an empty note.  A lone match under a *different* name is
    accepted, because its contents may still be the only evidence there is, but
    never silently: the note it comes back with reaches the printed summary and
    forbids a clean grade.  Two matches with no exact name is an ambiguity, not
    a preference: choosing the first of a sorted list is how a planted file wins.
    """
    candidate = directory / exact
    if candidate.is_file():
        return candidate, ""
    matches = sorted(p for p in directory.glob(pattern) if p.is_file())
    if len(matches) == 1:
        return matches[0], (
            f"{kind} was read from {_q(matches[0].name)} in {_q(directory)}, but "
            f"the tool writes {_q(exact)}; a file under any other name is not "
            "evidence that the tool produced it, so this result cannot be "
            "graded clean"
        )
    if len(matches) > 1:
        raise VerificationError(
            f"{kind}: {len(matches)} files match {_q(pattern)} in {_q(directory)} "
            f"and none is named {_q(exact)}: "
            + ", ".join(_q(p.name) for p in matches)
            + "; refusing to guess which one carries the verdict."
        )
    return None, ""


def locate_magic_drc_report(
    work_dir: os.PathLike[str],
    cell_name: str,
) -> Tuple[Path, str]:
    """Return ``(path, note)`` for the canonical Magic DRC report.

    ``note`` is empty for ``<cell>.magic.drc.rpt`` in a canonical directory and
    otherwise says what was read instead; pass it to
    :func:`parse_magic_drc_report` as ``location_note``.  Absence raises: a
    whole-tree glob would let any writable subdirectory plant a clean report
    that outranks the real one.
    """
    work_dir = Path(work_dir)
    directory = _one_canonical_dir(
        work_dir, cell_name, MAGIC_DRC_DIR_SUFFIX, ("*.magic.drc.rpt",),
        "Magic DRC report",
    )
    if directory is not None:
        found, note = _single_file(
            directory,
            f"{cell_name}.magic.drc.rpt",
            "*.magic.drc.rpt",
            "Magic DRC report",
        )
        if found is not None:
            return found, note
    raise VerificationError(
        "Magic DRC report not found: expected "
        f"{_q(work_dir / f'{cell_name}.{MAGIC_DRC_DIR_SUFFIX}' / f'{cell_name}.magic.drc.rpt')}"
        f"; only the canonical *.{MAGIC_DRC_DIR_SUFFIX}/ directories under "
        f"{_q(work_dir)} are searched."
    )


def _find_magic_drc_report(work_dir: Path, cell_name: str) -> Path:
    """Return only the path from :func:`locate_magic_drc_report`.

    Kept for callers that just want the file (the documentation generator).  A
    grader must use :func:`locate_magic_drc_report` instead: dropping the note
    is dropping the reason the report may not be trustworthy.
    """
    return locate_magic_drc_report(work_dir, cell_name)[0]


def _klayout_lyrdbs_in(directory: Path, cell_name: Optional[str]) -> List[Path]:
    """Return the ``*.lyrdb`` files directly inside ``directory``, sorted."""
    if not directory.is_dir():
        return []
    paths = sorted(p for p in directory.glob("*.lyrdb") if p.is_file())
    if cell_name:
        matching = [p for p in paths if cell_name in p.name]
        if matching:
            return matching
    return paths


def _klayout_lyrdb_sources(
    work_dir: Path,
    cell_name: Optional[str] = None,
) -> Tuple[List[Path], str]:
    """Return ``(databases, location_note)`` for a KLayout run.

    The canonical ``<cell>.klayout.drc/`` directory wins outright.  A caller
    that points straight at a directory holding databases is honoured -- that is
    a deliberate choice, not a discovered path -- but the non-canonical location
    is reported back so it cannot pass unnoticed, and it costs the run its
    completeness grade.  Subdirectories are never searched.
    """
    work_dir = Path(work_dir)
    directory = _one_canonical_dir(
        work_dir, cell_name, KLAYOUT_DRC_DIR_SUFFIX, ("*.lyrdb",),
        "KLayout DRC databases",
    )
    if directory is not None:
        paths = _klayout_lyrdbs_in(directory, cell_name)
        if paths:
            return paths, ""
    paths = _klayout_lyrdbs_in(work_dir, cell_name)
    if paths:
        return paths, (
            f"read from {_q(work_dir)}, which is not a canonical "
            f"*.{KLAYOUT_DRC_DIR_SUFFIX}/ directory"
        )
    return [], ""


def _find_klayout_lyrdbs(work_dir: Path, cell_name: Optional[str] = None) -> List[Path]:
    """Return the KLayout ``.lyrdb`` databases to merge, sorted by path.

    There is no combined ``*_full.lyrdb``: KLayout writes one database per rule
    table, so the caller merges them.  The list is empty when KLayout did not
    run, which callers report as a degradation rather than an error.  How many
    databases the run *should* have written is a separate question, answered by
    the receipt -- see :func:`_klayout_completeness`.
    """
    return _klayout_lyrdb_sources(work_dir, cell_name)[0]


def locate_netgen_lvs_report(
    work_dir: os.PathLike[str],
    cell_name: str,
) -> Tuple[Path, str]:
    """Return ``(path, note)`` for the canonical Netgen report.

    ``*.lvs.out`` is preferred over the ``*.lvs.log`` fallback; absence raises
    rather than falling back to a whole-tree glob.  ``note`` is empty only for
    the exact name ``sak-lvs.sh`` writes; pass it to
    :func:`parse_netgen_lvs_report` as ``location_note``.
    """
    work_dir = Path(work_dir)
    directory = _one_canonical_dir(
        work_dir, cell_name, MAGIC_LVS_DIR_SUFFIX, ("*.lvs.out", "*.lvs.log"),
        "Netgen LVS report",
    )
    if directory is not None:
        for exact, pattern in (
            (f"{cell_name}.lvs.out", "*.lvs.out"),
            (f"{cell_name}.lvs.log", "*.lvs.log"),
        ):
            found, note = _single_file(directory, exact, pattern, "Netgen LVS report")
            if found is not None:
                return found, note
    raise VerificationError(
        "Netgen LVS report not found: expected "
        f"{_q(work_dir / f'{cell_name}.{MAGIC_LVS_DIR_SUFFIX}' / f'{cell_name}.lvs.out')}"
        f"; only the canonical *.{MAGIC_LVS_DIR_SUFFIX}/ directories under "
        f"{_q(work_dir)} are searched."
    )


def _find_netgen_lvs_report(work_dir: Path, cell_name: str) -> Path:
    """Return only the path from :func:`locate_netgen_lvs_report`."""
    return locate_netgen_lvs_report(work_dir, cell_name)[0]
