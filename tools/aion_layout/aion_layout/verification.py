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
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


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
    """Structured result of a DRC run."""

    tool: str
    clean: bool
    violations: Sequence[DrcViolation]
    categories: Sequence[str]

    @property
    def error_count(self) -> int:
        return len(self.violations)


@dc.dataclass(frozen=True)
class LvsReport:
    """Structured result of an LVS run."""

    tool: str
    clean: bool
    message: str
    device_counts: Dict[str, Tuple[int, int]] = dc.field(default_factory=dict)


class VerificationError(RuntimeError):
    """Raised when a verification command fails or reports are missing."""


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
        raise VerificationError(f"KLayout DRC report not found: {path}")

    tree = ET.parse(path)
    root = tree.getroot()

    categories: Dict[str, str] = {}
    for cat in root.iter("category"):
        name = _text(cat, "name")
        desc = _text(cat, "description")
        if name:
            categories[name] = desc or ""

    violations: List[DrcViolation] = []
    for item in root.iter("item"):
        cat_name = (_text(item, "category") or "unknown").strip("'\"")
        cell_name = _text(item, "cell") or ""
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


def parse_magic_drc_report(path: os.PathLike[str]) -> DrcReport:
    """Parse a Magic DRC ``*.magic.drc.rpt`` file.

    The report is split into sections by rule name.  Each section header is a
    delimiter line, a title line, and another delimiter line; the section body
    lists the bounding boxes of the violations in microns as ``x1 y1 x2 y2``.
    """
    path = Path(path)
    if not path.exists():
        raise VerificationError(f"Magic DRC report not found: {path}")

    lines = path.read_text().splitlines()
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
                current_category = title
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
            try:
                x1, y1, x2, y2 = (float(p) for p in parts)
            except ValueError:
                i += 1
                continue
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

    return DrcReport(
        tool="magic",
        clean=len(violations) == 0,
        violations=violations,
        categories=list(dict.fromkeys(categories)),
    )


# ---------------------------------------------------------------------------
# Netgen LVS report parsing
# ---------------------------------------------------------------------------

_LVS_FINAL_RE = re.compile(r"Final result:\s*Circuits match uniquely", re.IGNORECASE)
_LVS_FINAL_FAIL_RE = re.compile(r"Final result:\s*Circuits do not match", re.IGNORECASE)
_LVS_DEV_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+\(\s*(\d+)\s*\)\s+\|\s*([A-Za-z_][A-Za-z0-9_]*)\s+\(\s*(\d+)\s*\)",
    re.MULTILINE,
)


def parse_netgen_lvs_report(path: os.PathLike[str]) -> LvsReport:
    """Parse a Netgen ``*.lvs.out`` or ``*.lvs.log`` file."""
    path = Path(path)
    if not path.exists():
        raise VerificationError(f"Netgen LVS report not found: {path}")

    text = path.read_text()
    clean = bool(_LVS_FINAL_RE.search(text))
    failed = bool(_LVS_FINAL_FAIL_RE.search(text))
    if clean:
        message = "Circuits match uniquely."
    elif failed:
        message = "Circuits do not match."
    else:
        message = "LVS result is inconclusive; check the log."

    device_counts: Dict[str, Tuple[int, int]] = {}
    for match in _LVS_DEV_RE.finditer(text):
        dev = match.group(1)
        c1 = int(match.group(2))
        c2 = int(match.group(4))
        device_counts[dev] = (c1, c2)

    return LvsReport(
        tool="netgen",
        clean=clean,
        message=message,
        device_counts=device_counts,
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
    """Return the project root directory that docker_run.sh mounts.

    The wrapper lives at ``<aion_layout>/scripts/docker_run.sh``.
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
        raise VerificationError(f"DRC runner script not found: {script}")

    # The docker_run.sh wrapper mounts the project directory at
    # /foss/designs/aion_flow and the sak-* scripts are invoked from
    # tools/aion_layout.  Paths passed to sak-* must therefore be relative to
    # tools/aion_layout.
    aion_layout_root = _repo_root(script) / "tools" / "aion_layout"
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
            raise VerificationError(f"DRC runner failed:\n{output}")

    cell_name = gds_path.stem
    magic_rpt = _find_magic_drc_report(work_dir, cell_name)
    klayout_rpt = _find_klayout_lyrdb(work_dir, cell_name)
    return parse_magic_drc_report(magic_rpt), parse_klayout_lyrdb(klayout_rpt)


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
        raise VerificationError(f"LVS runner script not found: {script}")

    aion_layout_root = _repo_root(script) / "tools" / "aion_layout"
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
            raise VerificationError(f"LVS runner failed:\n{output}")

    lvs_out = _find_netgen_lvs_report(work_dir, cell_name)
    return parse_netgen_lvs_report(lvs_out)


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


def _find_magic_drc_report(work_dir: Path, cell_name: str) -> Path:
    candidates = list(work_dir.rglob(f"{cell_name}.magic.drc.rpt"))
    if not candidates:
        raise VerificationError(f"Magic DRC report not found under {work_dir}")
    return candidates[0]


def _find_klayout_lyrdb(work_dir: Path, cell_name: str) -> Path:
    candidates = list(work_dir.rglob("*_full.lyrdb"))
    if not candidates:
        raise VerificationError(f"KLayout DRC report not found under {work_dir}")
    return candidates[0]


def _find_netgen_lvs_report(work_dir: Path, cell_name: str) -> Path:
    candidates = list(work_dir.rglob("*.lvs.out")) + list(work_dir.rglob("*.lvs.log"))
    if not candidates:
        raise VerificationError(f"Netgen LVS report not found under {work_dir}")
    return candidates[0]
