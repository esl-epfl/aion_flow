# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Regressions for verdicts forged by the graded party
# ================================================================

"""The thing being graded must not be able to write its own grade.

The model rewrites the tree these programs parse, runs with an edit tool and a
bash tool, and is given ``--add-dir $BUILD_DIR``.  Every string that reaches a
verdict stream from that tree is therefore hostile input.  Four exploits are
pinned here, all of them reproduced:

* **F2/F19** a directory name or an exception message containing a newline
  forged a line reading ``RESULT: PASS`` at column 0 in the stream the harness
  greps.
* **F3/F18** a report planted in ``drc/<cell>/`` or ``drc/AAAA/`` outranked the
  genuine ``<cell>.magic.drc/`` report, because discovery was
  ``sorted(rglob(...))[0]`` and ``AAAA`` sorts first.
* **F28** ``state.json.pre`` lived *inside* ``$BUILD_DIR``, so writing the same
  forged JSON to both files made the anti-tamper comparison agree and the
  restore reinstate the forgery.
* **F23** a stale or planted report survived into the next run and answered for
  a run that never produced one.
"""

from __future__ import annotations

import os
import re
import shutil
import uuid

import pytest

from conftest import run

#: The line the exploit is trying to forge.  ``pipeline.sh`` greps report.txt
#: with ``^RESULT:[[:space:]]*(PASS|FAIL)`` and ``orchestrate.sh`` records the
#: first match, so one such line at column 0 rewrites the run's history.
FORGED = "RESULT: PASS"

#: A path component carrying the forged line.  ``/`` is the only character a
#: path component cannot hold; a newline is perfectly legal, which is the whole
#: point -- nobody expects a directory to be able to speak.
MALICIOUS_COMPONENT = f"evil\n{FORGED}\ntail"


def result_lines(text: str) -> list[str]:
    """Return every line of ``text`` that starts at column 0 with ``RESULT:``."""
    return [line for line in text.split("\n") if line.startswith("RESULT:")]


# ---------------------------------------------------------------------------
# F2/F19 -- a newline in a path or an exception message must not forge a verdict
# ---------------------------------------------------------------------------

def test_newline_in_runs_dir_cannot_forge_a_report_verdict(
    tmp_path, cell_name, netlist_path
):
    """report_verification.py's stdout is what pipeline.sh grades the run on."""
    evil = tmp_path / MALICIOUS_COMPONENT
    evil.mkdir()

    proc = run(
        [
            "python3", "scripts/report_verification.py",
            "--cell", cell_name,
            "--gds", str(tmp_path / "nope.gds"),
            "--netlist", str(netlist_path),
            "--runs-dir", str(evil),
            "--parse-only",
        ]
    )

    lines = result_lines(proc.stdout)
    assert lines == ["RESULT: ERROR"], (
        f"expected exactly one verdict line, 'RESULT: ERROR', got {lines}.\n"
        f"The runs directory is named {MALICIOUS_COMPONENT!r}; its newline "
        "reached the output unscrubbed and spelled a verdict at column 0.  "
        "pipeline.sh greps for the first such line, so this is a PASS written "
        f"by the thing being graded.\n--- stdout ---\n{proc.stdout}"
    )
    assert proc.returncode == 2, (
        f"a run that could not be graded must exit 2 (ERROR), got "
        f"{proc.returncode}"
    )
    # The path is legitimately echoed back in the error message, so the forged
    # text may well appear -- but only ever indented out of column 0, which is
    # the only column the harness's grep reads.
    at_column_zero = [
        line for line in proc.stdout.split("\n") if line.startswith(FORGED)
    ]
    assert not at_column_zero, (
        f"the forged text reached column 0: {at_column_zero}\n{proc.stdout}"
    )


def test_newline_in_cell_name_cannot_forge_a_report_verdict(tmp_path, netlist_path):
    """``--cell`` is argv, and argv comes from a file the model can rewrite."""
    proc = run(
        [
            "python3", "scripts/report_verification.py",
            "--cell", f"X\n{FORGED}",
            "--gds", str(tmp_path / "nope.gds"),
            "--netlist", str(netlist_path),
            "--runs-dir", str(tmp_path),
            "--parse-only",
        ]
    )

    lines = result_lines(proc.stdout)
    assert lines == ["RESULT: ERROR"], (
        f"a newline inside --cell forged a verdict line; got {lines}.\n"
        f"--- stdout ---\n{proc.stdout}"
    )


def test_newline_in_iter_dir_cannot_forge_an_evidence_verdict(
    tmp_path, cell_name, netlist_path
):
    """orchestrate.sh reads the packet's first ``^RESULT:`` line as the outcome.

    ``scripts/evidence.py`` documents the invariant itself: exactly one line of
    the packet may start at column 0 with ``RESULT:``, and it is block [2]'s.
    The iteration directory is a path the harness builds from ``$BUILD_DIR``,
    and a component of it carrying a newline must not be able to write that
    line instead.
    """
    evil = tmp_path / MALICIOUS_COMPONENT
    evil.mkdir()

    proc = run(
        [
            "python3", "scripts/evidence.py",
            "--netlist", str(netlist_path),
            "--iter-dir", str(evil),
            "--cell", cell_name,
        ]
    )

    lines = result_lines(proc.stdout)
    assert lines == ["RESULT: ERROR"], (
        f"expected the packet's single verdict line to be 'RESULT: ERROR' -- "
        f"nothing was on disk to grade -- got {lines}.\n"
        f"The iteration directory is named {MALICIOUS_COMPONENT!r}.  Its newline "
        "travels through the discovery 'reason' strings into block [2]'s "
        "headlines, where it opens a line of its own; "
        "_enforce_single_result_line then keeps the *first* RESULT: line inside "
        "block [2] -- the forged one -- and indents the genuine verdict.\n"
        f"--- stdout ---\n{proc.stdout}"
    )


def test_evidence_verdict_survives_a_newline_in_the_module_path(
    tmp_path, cell_name, netlist_path, iteration_tree, iter0_module
):
    """The same exploit through ``--module``, which names a model-written file."""
    iter_dir = iteration_tree()
    evil_dir = tmp_path / MALICIOUS_COMPONENT
    evil_dir.mkdir()
    module = evil_dir / f"{cell_name}.py"
    module.write_text(iter0_module.read_text())

    proc = run(
        [
            "python3", "scripts/evidence.py",
            "--netlist", str(netlist_path),
            "--iter-dir", str(iter_dir),
            "--cell", cell_name,
            "--module", str(module),
        ]
    )

    lines = result_lines(proc.stdout)
    assert lines == ["RESULT: FAIL"], (
        f"the module path carries a newline and forged a verdict; expected the "
        f"single line 'RESULT: FAIL' from the dirty fixture tree, got {lines}.\n"
        f"--- stdout ---\n{proc.stdout[:4000]}"
    )


# ---------------------------------------------------------------------------
# F3/F18 -- a planted report must not outrank the canonical one
# ---------------------------------------------------------------------------

#: Where the model would plant a clean report.  ``AAAA`` and ``aaa`` are chosen
#: to sort ahead of ``drc``/the real directory under the old
#: ``sorted(rglob(...))[0]`` discovery; ``drc/<cell>/`` is the path the *old*
#: pipeline itself used, so it looks entirely legitimate.
PLANT_DIRS = ["drc/{cell}", "drc/AAAA", "aaa", "drc/{cell}.magic.drc.bak"]

#: A Magic report that claims a clean layout, complete with the COUNT trailer
#: that D1 requires -- so the plant is refused for *where* it is, not for what
#: it says.
CLEAN_MAGIC = "{cell}\n[INFO] COUNT: 0\n"


@pytest.mark.parametrize("plant", PLANT_DIRS)
def test_planted_clean_report_does_not_outrank_the_canonical_one_in_the_cli(
    iteration_tree, cell_name, netlist_path, plant
):
    iter_dir = iteration_tree()
    planted_dir = iter_dir / plant.format(cell=cell_name)
    planted_dir.mkdir(parents=True)
    (planted_dir / f"{cell_name}.magic.drc.rpt").write_text(
        CLEAN_MAGIC.format(cell=cell_name)
    )

    proc = run(
        [
            "python3", "scripts/report_verification.py",
            "--cell", cell_name,
            "--gds", str(iter_dir / f"{cell_name}.gds"),
            "--netlist", str(netlist_path),
            "--runs-dir", str(iter_dir),
            "--parse-only",
        ]
    )

    assert "RESULT: FAIL" in proc.stdout, (
        f"planting a clean Magic report in {plant!r} changed the verdict.\n"
        "The canonical report under <cell>.magic.drc/ lists 8 latch-up "
        "violations; discovery must target that directory by name and never "
        "prefer whatever sorts first.\n"
        f"--- stdout ---\n{proc.stdout}"
    )
    assert "magic=8" in proc.stdout, (
        f"the DRC header must still carry the real 8 violations, got:\n"
        f"{proc.stdout}"
    )
    assert proc.returncode == 1, (
        f"a dirty layout must exit 1 (FAIL), got {proc.returncode}"
    )


@pytest.mark.parametrize("plant", PLANT_DIRS)
def test_planted_clean_report_does_not_become_the_evidence(
    evidence, iteration_tree, cell_name, netlist_path, plant
):
    iter_dir = iteration_tree()
    planted_dir = iter_dir / plant.format(cell=cell_name)
    planted_dir.mkdir(parents=True)
    (planted_dir / f"{cell_name}.magic.drc.rpt").write_text(
        CLEAN_MAGIC.format(cell=cell_name)
    )

    artifacts = evidence.discover_artifacts(iter_dir, cell_name)
    assert artifacts.magic_drc is not None, "the canonical report was not found at all"
    assert artifacts.magic_drc.parent.name == f"{cell_name}.magic.drc", (
        f"discovery read the Magic report from {artifacts.magic_drc.parent}; only "
        f"{cell_name}.magic.drc/ is a place the tools write one"
    )

    packet = evidence.build_evidence(netlist_path, iter_dir, cell_name, None)
    assert "MAGIC DRC   : FAIL - 8 violations" in packet, (
        f"the planted report in {plant!r} replaced the real one in block [2].\n"
        f"--- block 2 ---\n{packet[:3000]}"
    )
    assert any("IGNORED" in line for line in packet.split("\n")), (
        "a refused report must be *named* as refused; silently ignoring it is "
        "the same blindness, only quieter"
    )


def test_planted_report_in_the_canonical_directory_is_an_ambiguity_not_a_choice(
    iteration_tree, cell_name, netlist_path
):
    """Two reports in the real directory must be refused, never ranked.

    Picking the first of a sorted list is exactly how a plant wins, so a second
    ``*.magic.drc.rpt`` beside the genuine one has to stop discovery rather than
    let a name like ``AAAA.magic.drc.rpt`` come first.
    """
    iter_dir = iteration_tree()
    magic_dir = iter_dir / "drc" / f"{cell_name}.magic.drc"
    (magic_dir / "AAAA.magic.drc.rpt").write_text(CLEAN_MAGIC.format(cell=cell_name))

    proc = run(
        [
            "python3", "scripts/report_verification.py",
            "--cell", cell_name,
            "--gds", str(iter_dir / f"{cell_name}.gds"),
            "--netlist", str(netlist_path),
            "--runs-dir", str(iter_dir),
            "--parse-only",
        ]
    )

    assert "RESULT: PASS" not in proc.stdout, (
        f"a second report planted beside the genuine one produced a PASS:\n"
        f"{proc.stdout}"
    )
    assert "magic=8" in proc.stdout or "RESULT: ERROR" in proc.stdout, (
        "the exact-name match must win, or the ambiguity must be refused "
        f"outright; got:\n{proc.stdout}"
    )


# ---------------------------------------------------------------------------
# F23 -- a stale report must be cleared before the step that would find it
# ---------------------------------------------------------------------------

def test_step_drc_clears_a_planted_report_before_running(
    repo_root, tmp_path, cell_name
):
    """A report the step did not produce must not be able to answer for it.

    The container runner is stubbed with a no-op, so the only report that could
    satisfy the step is the clean one planted beforehand.  The step must clear
    the run directory first and then fail for want of evidence.
    """
    iter_dir = tmp_path / "iter"
    iter_dir.mkdir()
    (iter_dir / f"{cell_name}.gds").write_text("GDS")
    drc = iter_dir / "drc"

    (drc / f"{cell_name}.magic.drc").mkdir(parents=True)
    (drc / f"{cell_name}.klayout.drc").mkdir(parents=True)
    planted = drc / f"{cell_name}.magic.drc" / f"{cell_name}.magic.drc.rpt"
    planted.write_text(CLEAN_MAGIC.format(cell=cell_name))
    (drc / f"{cell_name}.klayout.drc" / "planted.lyrdb").write_text("<report/>\n")

    noop = tmp_path / "noop_runner.sh"
    noop.write_text("#!/bin/bash\nexit 0\n")
    noop.chmod(0o755)

    proc = run(
        [
            "bash", "-c",
            f'set -uo pipefail\nsource "{repo_root}/pipeline.sh"\nset +e\n'
            f'step_drc_at "{iter_dir / (cell_name + ".gds")}" "{drc}"\n'
            'echo "rc=$?"\n',
        ],
        env={**os.environ, "PIPELINE_RUN_SCRIPT": str(noop)},
    )

    assert "rc=0" not in proc.stdout, (
        f"step_drc_at succeeded on a report it never produced:\n"
        f"{proc.stdout}{proc.stderr}"
    )
    assert not planted.exists(), (
        f"the planted report at {planted} survived the step.  Every run "
        "directory is emptied before the tool starts precisely so a stale or "
        "planted report cannot stand in for a run that produced none."
    )


# ---------------------------------------------------------------------------
# F28 -- the state snapshot must live where the model cannot reach it
# ---------------------------------------------------------------------------

def test_state_snapshot_path_is_not_derived_from_the_state_file(repo_root):
    """``${STATE_FILE}.pre`` sat inside the directory the model may write."""
    text = (repo_root / "orchestrate.sh").read_text()
    # Comments legitimately name the old path while explaining why it is gone;
    # what must not survive is a line of *code* that still builds it.
    code = "\n".join(
        line for line in text.split("\n") if not line.lstrip().startswith("#")
    )

    assert "${STATE_FILE}.pre" not in code and "$STATE_FILE.pre" not in code, (
        "the state snapshot is still derived from STATE_FILE, which lives under "
        "$BUILD_DIR -- the directory the model is given --add-dir for.  Writing "
        "the same forged JSON to state.json and state.json.pre made the "
        "comparison agree and the restore reinstate the forgery."
    )
    assert 'GUARD_STATE_SNAPSHOT="${GUARD_DIR}/state.json.pre"' in text, (
        "the snapshot must live under GUARD_DIR, the temp directory created "
        "outside $BUILD_DIR"
    )
    assert 'GUARD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/aion-guard-XXXXXX")"' in text, (
        "GUARD_DIR must be a fresh temp directory, not a path under the build "
        "tree the model can enumerate and rewrite"
    )


def test_guard_refuses_a_snapshot_directory_inside_build_dir(repo_root):
    """The refusal is what makes 'outside $BUILD_DIR' a guarantee, not a hope."""
    text = (repo_root / "orchestrate.sh").read_text()
    guard_init = text.split("guard_init() {", 1)
    assert len(guard_init) == 2, "guard_init is missing from orchestrate.sh"
    body = guard_init[1].split("\n}", 1)[0]

    assert '"${GUARD_DIR}/" == "${BUILD_DIR}/"*' in body, (
        f"guard_init does not test whether the snapshot directory landed inside "
        f"$BUILD_DIR:\n{body}\nWith TMPDIR pointing into the build tree the "
        "snapshot is writable by the model again, and nothing would say so."
    )
    assert "fatal " in body, (
        "the check must abort the run; a warning leaves the guard disarmed while "
        "claiming to be armed"
    )


def test_graders_are_restored_from_a_trap(repo_root):
    """An interrupted run must not be able to leave a forged grader behind."""
    text = (repo_root / "orchestrate.sh").read_text()

    for signal in ("EXIT", "INT", "TERM", "HUP"):
        assert re.search(rf"^trap 'aion_cleanup[^']*' {signal}$", text, re.M), (
            f"no cleanup trap for {signal}; a Ctrl-C during the model call would "
            "leave the model's edits to the graders and its forged state.json in "
            "place for the next run to read as success"
        )
    cleanup = text.split("aion_cleanup() {", 1)
    assert len(cleanup) == 2, "aion_cleanup is missing from orchestrate.sh"
    body = cleanup[1].split("\n}", 1)[0]
    assert "guard_restore_state" in body and "guard_verify_graders" in body, (
        f"the trap does not restore the state snapshot and re-verify the "
        f"graders:\n{body}"
    )


def test_every_file_that_decides_the_verdict_is_snapshotted(repo_root):
    """A grader nobody snapshots is a grader the model can rewrite for free."""
    text = (repo_root / "orchestrate.sh").read_text()
    listed = text.split("GUARD_GRADERS=(", 1)[1].split(")", 1)[0]

    for grader in (
        "aion_layout/verification.py",
        "scripts/report_verification.py",
        "scripts/evidence.py",
        "pipeline.sh",
        "scripts/selfcheck.sh",
        "orchestrate.sh",
    ):
        assert grader in listed, (
            f"{grader} decides the verdict but is not in GUARD_GRADERS:\n{listed}"
        )


@pytest.fixture
def repo_local_build_dir(repo_root):
    """A scratch $BUILD_DIR inside the repository, removed however the test ends.

    ``orchestrate.sh`` refuses a build directory outside the repository -- the
    container mounts the repository and nothing else -- so this one cannot live
    in ``tmp_path``.
    """
    path = repo_root / f".pytest-aion-{uuid.uuid4().hex[:12]}"
    try:
        path.mkdir()
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_orchestrate_refuses_to_start_when_the_snapshot_would_be_writable(
    repo_root, repo_local_build_dir, netlist_path
):
    """End to end: TMPDIR inside $BUILD_DIR must stop the run before it starts.

    Nothing here reaches Docker or a model: ``guard_init`` runs before the loop,
    and it aborts.
    """
    if shutil.which("jq") is None:
        pytest.skip("jq is not installed; orchestrate.sh cannot read state.json")

    inside = repo_local_build_dir / "tmp"
    inside.mkdir()

    proc = run(
        [
            "bash", str(repo_root / "orchestrate.sh"),
            str(netlist_path), str(repo_local_build_dir), "1",
        ],
        env={
            **os.environ,
            "TMPDIR": str(inside),
            "CEFPROVIDER_API_KEY": "not-a-real-key",
            # Executable, so the wrapper check passes and guard_init is reached.
            "COPILOT_RCP": "/bin/true",
            "AION_DUMP_PROMPT": "",
        },
        timeout=120,
    )

    assert proc.returncode == 2, (
        f"orchestrate.sh exited {proc.returncode} with TMPDIR inside $BUILD_DIR; "
        f"it must refuse to start (exit 2).\n{proc.stdout}\n{proc.stderr}"
    )
    assert "TMPDIR resolves inside BUILD_DIR" in proc.stderr, (
        f"the refusal must name the reason, got:\n{proc.stderr}"
    )
    assert not list(repo_local_build_dir.rglob("state.json.pre")), (
        "a state snapshot was written inside $BUILD_DIR anyway; that is the "
        "file the model overwrites to make the tamper check agree with itself"
    )
