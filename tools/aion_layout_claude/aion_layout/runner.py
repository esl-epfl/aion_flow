# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The one place that runs a command
# ================================================================

"""Command execution for the mechanical half of the flow.

Every containerised step goes through :func:`run_in_container`, and every step
that runs model-written code goes through :func:`run_python_isolated`.  Two
rules the rest of the package depends on:

1. **A command's exit status is never thrown away.**  "Did the tool finish?" is
   a different question from "did the tool find anything", and only the status
   answers the first.  Callers get both the status and the combined output.

2. **A timeout is a failure, not a hang.**  Every runner takes one and reports
   the expiry as a normal non-zero result with the output captured so far, so a
   step can report *why* it has no artifact instead of blocking the flow.
"""

from __future__ import annotations

import dataclasses as dc
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence

#: This tool's own directory: ``tools/aion_layout_claude``.
TOOL_DIR = Path(__file__).resolve().parent.parent
#: The repository root, ``<repo>``, three levels above this module.
REPO_ROOT = TOOL_DIR.parent.parent
#: The container wrapper.  It cds into ``TOOL_DIR`` inside the container, so a
#: path handed to a containerised command is spelled relative to ``TOOL_DIR`` --
#: the same spelling that works on the host.
DOCKER_RUN = TOOL_DIR / "scripts" / "docker_run.sh"

#: Default wall-clock budget for one containerised EDA step, in seconds.
DEFAULT_TIMEOUT = 1800


@dc.dataclass(frozen=True)
class RunResult:
    """The complete outcome of one command: status, output, and why it ended."""

    status: int
    output: str
    timed_out: bool = False
    command: str = ""

    @property
    def ok(self) -> bool:
        """True only for a command that finished with status 0."""
        return self.status == 0 and not self.timed_out

    def tail(self, lines: int = 40) -> str:
        """Return the last ``lines`` lines of the output, for an error message."""
        return "\n".join(self.output.splitlines()[-lines:])


def rel_to_tool(path: os.PathLike[str] | str) -> str:
    """Return ``path`` spelled relative to this tool's directory.

    Containerised commands run with the tool directory as their working
    directory, so this is the spelling they need.  A path outside the tool
    directory comes back with ``..`` components, which the container mount
    still resolves as long as it stays inside the repository.
    """
    return os.path.relpath(Path(path).resolve(), TOOL_DIR)


def run_host(
    cmd: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    timeout: int = DEFAULT_TIMEOUT,
    env: Optional[dict] = None,
) -> RunResult:
    """Run ``cmd`` on the host and return its status and combined output."""
    printable = " ".join(shlex.quote(str(c)) for c in cmd)
    try:
        proc = subprocess.run(
            [str(c) for c in cmd],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        captured = (exc.stdout or "") + (exc.stderr or "")
        if isinstance(captured, bytes):  # pragma: no cover - text=True given
            captured = captured.decode("utf-8", "replace")
        return RunResult(
            status=124,
            output=captured + f"\n[timeout] killed after {timeout}s",
            timed_out=True,
            command=printable,
        )
    except OSError as exc:
        return RunResult(status=127, output=f"[oserror] {exc}", command=printable)
    return RunResult(
        status=proc.returncode,
        output=proc.stdout + proc.stderr,
        command=printable,
    )


def container_available() -> tuple[bool, str]:
    """Return ``(available, reason)`` for the EDA container.

    Checked before a containerised step rather than after it fails, so the
    error a caller reports names the container instead of a missing artifact.
    """
    if not DOCKER_RUN.is_file():
        return False, f"container wrapper not found: {DOCKER_RUN}"
    name = os.environ.get("AION_CONTAINER", "iic-osic-tools_shell_uid_1000")
    probe = run_host(
        ["docker", "inspect", "-f", "{{.State.Running}}", name], timeout=30
    )
    if not probe.ok or "true" not in probe.output:
        return False, (
            f"container {name!r} is not running; start the iic-osic-tools "
            "container (or set AION_CONTAINER) and retry"
        )
    return True, ""


def run_in_container(
    command: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
) -> RunResult:
    """Run one shell ``command`` inside the EDA container.

    The working directory is this tool's directory, so relative paths mean the
    same thing inside the container as they do on the host.  A container that
    is not running comes back as a normal failed :class:`RunResult` naming that
    fact -- callers report it, they do not have to catch it.
    """
    available, reason = container_available()
    if not available:
        return RunResult(status=125, output=f"[container] {reason}", command=command)
    return run_host([str(DOCKER_RUN), command], cwd=TOOL_DIR, timeout=timeout)


def run_python_isolated(
    script: str,
    *,
    timeout: int = 300,
    cwd: Optional[Path] = None,
) -> RunResult:
    """Run a Python ``script`` in a subprocess with this tool importable.

    Used for anything that executes a cell generator.  A generator is code the
    model wrote: it may call ``sys.exit``, print to stdout, or loop.  In a
    subprocess all three are results rather than damage.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(TOOL_DIR)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
    )
    return run_host(
        [sys.executable, "-c", script],
        cwd=cwd or TOOL_DIR,
        timeout=timeout,
        env=env,
    )


__all__ = [
    "DEFAULT_TIMEOUT",
    "DOCKER_RUN",
    "REPO_ROOT",
    "TOOL_DIR",
    "RunResult",
    "container_available",
    "rel_to_tool",
    "run_host",
    "run_in_container",
    "run_python_isolated",
]
