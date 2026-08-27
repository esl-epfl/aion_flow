"""Convert a structural Verilog netlist to Yosys JSON on demand."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


_SUFFIXES = {".v", ".sv", ".verilog"}


def is_verilog(path: Path) -> bool:
    """Return True if the path looks like a Verilog netlist."""
    return path.suffix.lower() in _SUFFIXES


def verilog_to_json(
    verilog_path: Path,
    top_module: str | None = None,
    output_json: Path | None = None,
) -> Path:
    """Convert a Verilog netlist to Yosys JSON and return the JSON path.

    If ``output_json`` is not provided, a temporary file is created.
    """
    verilog_path = verilog_path.resolve()
    if output_json is None:
        output_json = Path(tempfile.mkstemp(suffix=".json", prefix="aion_opt_")[1])
    else:
        output_json = output_json.resolve()
        output_json.parent.mkdir(parents=True, exist_ok=True)

    top_arg = f"-top {top_module}" if top_module else "-auto-top"
    script = (
        f"read_verilog {verilog_path}; "
        f"hierarchy {top_arg}; "
        f"write_json {output_json}"
    )

    cmd = ["yosys", "-p", script]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Yosys failed to convert {verilog_path}:\n{result.stderr or result.stdout}"
        )

    if not output_json.exists():
        raise RuntimeError(
            f"Yosys did not produce expected JSON output: {output_json}"
        )

    return output_json


def verilog_to_json_all_modules(
    verilog_path: Path,
    output_json: Path | None = None,
) -> Path:
    """Convert a Verilog file to Yosys JSON, preserving every module.

    Unlike ``verilog_to_json`` this does not run ``hierarchy``/``-auto-top``,
    so multi-module cell libraries remain intact.
    """
    verilog_path = verilog_path.resolve()
    if output_json is None:
        output_json = Path(tempfile.mkstemp(suffix=".json", prefix="aion_opt_all_")[1])
    else:
        output_json = output_json.resolve()
        output_json.parent.mkdir(parents=True, exist_ok=True)

    script = f"read_verilog {verilog_path}; write_json {output_json}"
    cmd = ["yosys", "-p", script]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Yosys failed to convert {verilog_path}:\n{result.stderr or result.stdout}"
        )

    if not output_json.exists():
        raise RuntimeError(
            f"Yosys did not produce expected JSON output: {output_json}"
        )

    return output_json
