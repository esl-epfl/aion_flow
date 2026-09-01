#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               One-page DRC/LVS verification summary
# ================================================================

"""Print a concise DRC/LVS summary for a generated cell.

Examples
--------

Parse existing reports only (fast)::

    python3 scripts/report_verification.py --gds path/to/cell.gds --netlist path/to/cell.spice --runs-dir path/to/runs --parse-only

Run the full verification flow::

    python3 scripts/report_verification.py --gds path/to/cell.gds --netlist path/to/cell.spice --runs-dir path/to/runs --cell cell_name
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aion_layout.verification import (
    DrcReport,
    LvsReport,
    parse_klayout_lyrdb,
    parse_magic_drc_report,
    parse_netgen_lvs_report,
    run_drc,
    run_lvs,
)


def _print_drc(name: str, report: DrcReport) -> None:
    status = "PASS" if report.clean else f"FAIL ({report.error_count})"
    print(f"  {name:12} : {status}")
    if not report.clean:
        by_category: dict[str, int] = {}
        for v in report.violations:
            by_category[v.category] = by_category.get(v.category, 0) + 1
        for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
            print(f"    - {category}: {count}")
        for v in report.violations[:5]:
            print(f"       {v.bbox_str}  {v.category}")
        if report.error_count > 5:
            print(f"       ... and {report.error_count - 5} more")


def _print_lvs(report: LvsReport) -> None:
    status = "PASS" if report.clean else "FAIL"
    print(f"  {'LVS':12} : {status} ({report.tool})")
    print(f"    {report.message}")
    if report.device_counts:
        print("    device counts:")
        for dev, (c1, c2) in sorted(report.device_counts.items()):
            mark = "✓" if c1 == c2 else "✗"
            print(f"      {mark} {dev}: layout={c1} schematic={c2}")


def _parse_existing(cell_name: str, runs_dir: Path) -> tuple[DrcReport, DrcReport | None, LvsReport]:
    # The sak-* wrappers create either ``<runs_dir>/drc/<cell>/`` or
    # ``<runs_dir>/drc_test/`` style directories.  Try both layouts.
    drc_dirs = [
        runs_dir / "drc" / cell_name,
        runs_dir / "drc_test",
        runs_dir,
    ]
    lvs_dirs = [
        runs_dir / "lvs" / cell_name,
        runs_dir / "lvs_test",
        runs_dir,
    ]

    magic_rpt = _find_report_in_candidates(drc_dirs, f"{cell_name}.magic.drc.rpt")
    klayout_rpt = _find_report_in_candidates(drc_dirs, "*_full.lyrdb")
    lvs_rpt = (
        _find_report_in_candidates(lvs_dirs, "*.lvs.out")
        or _find_report_in_candidates(lvs_dirs, "*.lvs.log")
    )

    if magic_rpt is None:
        raise FileNotFoundError(f"Magic DRC report not found under {runs_dir}")
    if lvs_rpt is None:
        raise FileNotFoundError(f"Netgen LVS report not found under {runs_dir}")

    # KLayout DRC is not implemented by sak-drc.sh for every PDK (e.g.
    # ihp-sg13g2), so no ``.lyrdb`` will ever be produced there. Treat it as
    # skipped rather than a hard failure.
    klayout_drc = parse_klayout_lyrdb(klayout_rpt) if klayout_rpt is not None else None

    return (
        parse_magic_drc_report(magic_rpt),
        klayout_drc,
        parse_netgen_lvs_report(lvs_rpt),
    )


def _find_report_in_candidates(dirs: list[Path], pattern: str) -> Path | None:
    """Return the first file matching ``pattern`` under any existing directory."""
    for work_dir in dirs:
        if not work_dir.exists():
            continue
        candidates = list(work_dir.rglob(pattern))
        if candidates:
            return candidates[0]
    return None


def _default_run_script() -> str:
    """Return the local docker_run.sh path relative to this script."""
    return str(Path(__file__).resolve().parent.parent / "scripts" / "docker_run.sh")


def main(argv: list[str] | None = None) -> int:
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
        help="Path to the sak-drc.sh / sak-lvs.sh wrapper script (default: scripts/docker_run.sh).",
    )
    args = parser.parse_args(argv)

    runs_dir = Path(args.runs_dir)
    gds_path = Path(args.gds)
    netlist_path = Path(args.netlist)

    print(f"Cell:      {args.cell}")
    print(f"GDS:       {gds_path}")
    print(f"Netlist:   {netlist_path}")
    print()

    if args.parse_only:
        magic_drc, klayout_drc, lvs = _parse_existing(args.cell, runs_dir)
    else:
        if not gds_path.exists():
            print(f"Error: GDS file not found: {gds_path}", file=sys.stderr)
            return 2
        if not netlist_path.exists():
            print(f"Error: netlist not found: {netlist_path}", file=sys.stderr)
            return 2
        drc_work = runs_dir / "drc" / args.cell
        lvs_work = runs_dir / "lvs" / args.cell
        magic_drc, klayout_drc = run_drc(gds_path, drc_work, args.run_script)
        lvs = run_lvs(gds_path, netlist_path, args.cell, lvs_work, args.run_script)

    print("DRC")
    _print_drc("Magic", magic_drc)
    if klayout_drc is not None:
        _print_drc("KLayout", klayout_drc)
    else:
        print(f"  {'KLayout':12} : SKIPPED (not supported for this PDK)")
    print()
    print("LVS")
    _print_lvs(lvs)
    print()

    passed = magic_drc.clean and (klayout_drc is None or klayout_drc.clean) and lvs.clean
    print("RESULT:    " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
