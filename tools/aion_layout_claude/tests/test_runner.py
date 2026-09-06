# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               An exit status is evidence and is never dropped
# ================================================================

"""The runner's two promises, pinned.

**A command's exit status is never thrown away.**  "Did the tool finish?" and
"did the tool find anything?" are different questions, and only the status
answers the first.  A step that reads a report without checking the status of
the run that wrote it will read a truncated report as a clean one.

**A timeout is a failure, not a hang and not an exception.**  It comes back as
an ordinary :class:`RunResult` with ``timed_out`` set and status 124, carrying
whatever output was captured, so a caller can say *why* it has no artifact.

Nothing here needs Docker: the one containerised entry point is exercised with
:func:`container_available` monkeypatched, which is exactly the path a host with
no container takes anyway.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from aion_layout import runner
from aion_layout.runner import (
    DEFAULT_TIMEOUT,
    REPO_ROOT,
    TOOL_DIR,
    RunResult,
    rel_to_tool,
    run_host,
    run_in_container,
    run_python_isolated,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def test_tool_and_repo_roots_are_what_the_container_mounts():
    """The container cds into TOOL_DIR; a wrong root makes every path wrong."""
    assert (TOOL_DIR / "aion_layout" / "runner.py").is_file(), (
        f"TOOL_DIR must be the directory holding the package, got {TOOL_DIR}"
    )
    assert TOOL_DIR.is_relative_to(REPO_ROOT), (
        f"the tool directory has to sit inside the repository root; "
        f"{TOOL_DIR} is not under {REPO_ROOT}"
    )


@pytest.mark.parametrize(
    "relative",
    ["build/AION_inv_nand2_nor2_1.gds", "tests/fixtures/PROVENANCE.txt", "Makefile"],
)
def test_rel_to_tool_round_trips(relative):
    """A containerised path is spelled relative to TOOL_DIR and must survive that."""
    absolute = TOOL_DIR / relative

    spelled = rel_to_tool(absolute)

    assert spelled == relative, (
        "a path inside the tool directory must come back as the plain relative "
        f"spelling the container uses; {absolute} became {spelled!r}"
    )
    assert (TOOL_DIR / spelled).resolve() == absolute.resolve(), (
        "the round trip has to land on the same file, or a command will read "
        "an artifact other than the one the caller measured"
    )


def test_rel_to_tool_escapes_upwards_rather_than_lying():
    """A path outside the tool directory keeps its '..', it is not clamped."""
    outside = REPO_ROOT / "tools"

    spelled = rel_to_tool(outside)

    assert spelled.startswith(".."), (
        "a path above the tool directory must be spelled with '..' so the "
        f"container resolves the file the caller meant; got {spelled!r}"
    )
    assert (TOOL_DIR / spelled).resolve() == outside.resolve(), (
        "the escaping spelling still has to resolve to the original path"
    )


# ---------------------------------------------------------------------------
# Exit statuses
# ---------------------------------------------------------------------------


def test_zero_status_is_ok():
    result = run_host([sys.executable, "-c", "print('hello')"], timeout=60)

    assert result.status == 0 and result.ok, (
        f"a command that succeeded must report ok: {result}"
    )
    assert "hello" in result.output, (
        "stdout is part of the evidence and must be captured, not discarded"
    )
    assert result.command, (
        "the printable command has to be kept, or an error message cannot say "
        "what was run"
    )


def test_non_zero_status_is_reported_not_raised():
    """A failing tool is a result to report, never an exception to swallow."""
    result = run_host([sys.executable, "-c", "import sys; sys.exit(3)"], timeout=60)

    assert result.status == 3, (
        f"the exit status is evidence and must survive verbatim; got {result.status}"
    )
    assert not result.ok, "ok must be False for any non-zero status"
    assert not result.timed_out, (
        "a clean non-zero exit is not a timeout; conflating them hides which "
        "of the two happened"
    )


def test_stderr_is_captured_alongside_stdout():
    """A tool that only ever writes to stderr must not look silent."""
    result = run_host(
        [sys.executable, "-c", "import sys; sys.stderr.write('boom\\n'); sys.exit(1)"],
        timeout=60,
    )

    assert result.status == 1
    assert "boom" in result.output, (
        "combined output must include stderr; most EDA tools report their "
        "failures there and a caller that loses it reports 'no output'"
    )


def test_a_missing_binary_is_a_status_not_an_exception():
    """An absent tool is a normal failure a step can explain."""
    result = run_host(["/nonexistent/definitely-not-a-tool"], timeout=30)

    assert not result.ok, "a command that could not start has not succeeded"
    assert result.status != 0, (
        f"a failure to exec must carry a non-zero status; got {result.status}"
    )
    assert result.output, (
        "the reason the command could not start is the only evidence there is "
        "and must be kept"
    )


def test_timeout_is_status_124_and_flagged():
    """A hung tool is a failed step with a reason, not a blocked flow."""
    result = run_host(
        [sys.executable, "-c", "import time; time.sleep(30)"], timeout=1
    )

    assert result.timed_out, (
        "a command killed at the deadline must be flagged as timed out; "
        "without the flag a caller cannot tell it apart from a tool that "
        "chose to exit non-zero"
    )
    assert result.status == 124, (
        f"the flow reports a timeout as status 124, got {result.status}"
    )
    assert not result.ok, "a timed-out command never counts as ok"
    assert "timeout" in result.output.lower(), (
        f"the output has to say the run was killed: {result.output!r}"
    )


def test_default_timeout_is_bounded():
    """Every containerised step has a deadline, so no step can block forever."""
    assert 0 < DEFAULT_TIMEOUT <= 3600, (
        f"the default EDA-step budget must be a finite, sane number of seconds: "
        f"{DEFAULT_TIMEOUT}"
    )


def test_tail_returns_only_the_last_lines():
    """Error messages quote a tail; an unbounded one floods the transcript."""
    result = RunResult(status=1, output="\n".join(str(i) for i in range(100)))

    tail = result.tail(5)

    assert tail.splitlines() == ["95", "96", "97", "98", "99"], (
        f"tail(5) must be the last five lines in order: {tail!r}"
    )


# ---------------------------------------------------------------------------
# Running model-written code
# ---------------------------------------------------------------------------


def test_isolated_python_can_import_the_package():
    """A generator is run in a subprocess that can still import aion_layout."""
    result = run_python_isolated(
        "import aion_layout; print(aion_layout.__version__)", timeout=60
    )

    assert result.ok, (
        "the isolated interpreter must have the tool directory on its path, "
        f"or every generator fails at its first import: {result.tail(20)}"
    )
    assert result.output.strip(), "the generator's stdout is evidence and is kept"


def test_isolated_python_returns_the_traceback_of_a_raise():
    """A generator that crashes must hand back the traceback, not a bare status."""
    result = run_python_isolated("raise ValueError('deliberate')", timeout=60)

    assert not result.ok, "a script that raised did not succeed"
    assert "Traceback" in result.output, (
        "the traceback is the only thing that says where the generator broke "
        f"and must be captured: {result.output!r}"
    )
    assert "deliberate" in result.output, (
        f"the exception message must survive to the caller: {result.output!r}"
    )


def test_isolated_python_sys_exit_does_not_kill_the_parent():
    """Model-written code calling sys.exit is a result, not the end of the flow."""
    marker = "the parent is still running"

    result = run_python_isolated(
        "import sys; print('child spoke'); sys.exit(1)", timeout=60
    )

    assert result.status == 1, (
        f"the child's exit status must be reported verbatim: {result.status}"
    )
    assert "child spoke" in result.output, (
        "output printed before the exit is still evidence and must be kept"
    )
    assert marker, "reaching this line at all is the assertion: the parent lives"


def test_isolated_python_does_not_inherit_a_broken_pythonpath(monkeypatch):
    """An existing PYTHONPATH is prepended to, never replaced or dropped."""
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(["/nonexistent/aaa"]))

    result = run_python_isolated(
        "import os, sys; print(os.environ['PYTHONPATH']); import aion_layout",
        timeout=60,
    )

    assert result.ok, (
        "the tool directory must win over whatever PYTHONPATH the caller had: "
        f"{result.tail(20)}"
    )
    assert str(TOOL_DIR) in result.output, (
        f"the tool directory has to be on the child's PYTHONPATH: {result.output!r}"
    )
    assert "/nonexistent/aaa" in result.output, (
        "the caller's own PYTHONPATH must be preserved after it, not discarded"
    )


def test_isolated_python_times_out_like_any_other_command():
    """A generator that loops is killed and reported, not waited on."""
    result = run_python_isolated("while True:\n    pass\n", timeout=1)

    assert result.timed_out and result.status == 124, (
        "an infinite generator has to come back as a timeout so the step can "
        f"report why there is no GDS: {result}"
    )


# ---------------------------------------------------------------------------
# The container, without a container
# ---------------------------------------------------------------------------


def test_container_step_reports_an_absent_container_as_a_result(monkeypatch):
    """No container is a degradation the caller reports, not an exception."""
    monkeypatch.setattr(
        runner, "container_available", lambda: (False, "container 'x' is not running")
    )

    result = run_in_container("sak-drc.sh -d -b -l macro", timeout=5)

    assert isinstance(result, RunResult), (
        "an unavailable container must come back as a normal RunResult so "
        "callers need no special case"
    )
    assert result.status == 125 and not result.ok, (
        f"the flow reports an unavailable container as status 125: {result.status}"
    )
    assert "not running" in result.output, (
        "the result must carry the reason, or the caller will report a missing "
        f"artifact instead of a missing container: {result.output!r}"
    )
    assert result.command == "sak-drc.sh -d -b -l macro", (
        "the command that never ran is still what the caller asked for and "
        "belongs in the result"
    )


def test_container_availability_is_checked_before_the_command(monkeypatch):
    """The probe runs first, so the error names the container not the artifact."""
    calls: list = []

    monkeypatch.setattr(runner, "container_available", lambda: (False, "no docker"))
    monkeypatch.setattr(
        runner, "run_host", lambda *a, **k: calls.append(a) or RunResult(0, "")
    )

    run_in_container("true")

    assert calls == [], (
        "with no container available nothing may be executed on the host; "
        f"run_host was called {len(calls)} time(s)"
    )


@pytest.mark.docker
def test_real_container_probe_answers_one_way_or_the_other():
    """Kept for a machine that has the container; deselected by default."""
    available, reason = runner.container_available()
    assert available or reason, (
        "an unavailable container must always come with a reason a human can "
        "act on"
    )
