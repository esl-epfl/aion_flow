# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Shell harness and assembled-prompt regressions
# ================================================================

"""The shell half of the loop, checked without Docker and without a model call.

Two historical defects are pinned here:

* ``orchestrate.sh`` called the pipeline as
  ``if ! run_deterministic_steps_for_current_iteration; then``.  A ``!``
  negation makes POSIX shells ignore ``set -e`` for the whole command --
  including inside every function it calls -- so ``step_report`` could ignore a
  non-zero runner status, find the file its own ``>`` redirection had created,
  and mark the step done.  ``step_report`` could never fail.
* The prompt taught the model raw ``sak-drc.sh`` / ``sak-lvs.sh`` recipes whose
  report step silently produced no verdict, and never inlined the netlist it
  told the model to implement.

The prompt is inspected through ``AION_DUMP_PROMPT``, orchestrate.sh's
dump-and-exit mode: no model call, no Docker, no state mutation.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

import pytest

from conftest import CELL, run

SHELL_FILES = ["orchestrate.sh", "pipeline.sh", "scripts/selfcheck.sh"]

#: Facts the model cannot fix the cell without, and the evidence blocks each one
#: lives in.  Since Stage 5 the prompt is scoped to one curriculum rung, so a
#: needle is required exactly when the rung carries a block that contains it --
#: asserting all of them unconditionally would either fail on every scoped
#: prompt or have to be deleted, and deleting them is how the harness went back
#: to injecting three characters of evidence.
#:
#: The block set is a frozenset, not one block: LU.b appears in the verdict AND
#: in both DRC blocks, and naming only one of them turns the "must be absent"
#: half of the check into a false failure.
#:
#: ``None`` means "not part of the packet at all" -- prompt framing that must be
#: present whatever the rung.
PROMPT_NEEDLES = [
    ("AION EVIDENCE PACKET", None, "the evidence packet must be inlined, not summarised away"),
    ("selfcheck.sh", None, "the one self-check command that produces a real verdict"),
    ("OBJECTIVE FOR THIS TURN", None, "the rung being graded must be stated, not left to be inferred"),
    (".subckt AION_inv_nand2_nor2_1", frozenset({1}),
     "the netlist the model must implement was never shown to it"),
    ("I1_bar", frozenset({0, 1, 5, 6}),
     "the fourth gate net is why the layout is one device per type short"),
    ("LU.a", frozenset({2, 3, 4}), "the latch-up rule that fails on the PMOS diffusion"),
    ("LU.b", frozenset({2, 3, 4}), "the latch-up rule that fails on the NMOS diffusion"),
    ("[INFO] COUNT: 8", frozenset({3}),
     "Magic's own violation count, so a blind parser is visible"),
    ("layout=3", frozenset({5}), "the extracted per-type device count"),
    ("schematic=4", frozenset({5}), "the per-type device count the netlist requires"),
    ("a_155_82#", frozenset({5, 6}), "the extracted node I1 and I2 both collapsed onto"),
    ("cross-net overlap", frozenset({7}), "the Metal1 short the starting geometry contains"),
    ("crossings=", frozenset({7}),
     "the poly/active crossing count against the devices required"),
]

#: Every rung of the ladder for the fixture cell, in order.
LADDER = ["build", "gates", "devices", "taps", "shorts", "pins", "nets", "drc"]

#: Text that must NOT be in the prompt.
PROMPT_MUST_NOT_CONTAIN = [
    ("@context", "an @-reference the model cannot resolve and will waste turns chasing"),
    ("sak-drc.sh", "a raw recipe whose report step silently produced no verdict"),
    ("sak-lvs.sh", "a raw recipe whose report step silently produced no verdict"),
    ("py_compile", "a check that proves the file parses and nothing about the layout"),
]


# ---------------------------------------------------------------------------
# Syntax and sourcing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("script", SHELL_FILES)
def test_shell_script_parses(script, repo_root):
    path = repo_root / script
    assert path.is_file(), f"{script} is missing"
    proc = run(["bash", "-n", str(path)])
    assert proc.returncode == 0, (
        f"{script} does not parse:\n{proc.stderr}\nA syntax error here is only "
        "discovered when the loop runs, after a model call has already been paid "
        "for"
    )


def test_pipeline_sources_with_no_globals_set(repo_root):
    """pipeline.sh must be sourceable by selfcheck.sh before any global exists."""
    env = {k: v for k, v in os.environ.items()
           if k not in {"STATE_FILE", "BUILD_DIR", "CELL_NAME", "SPICE_NETLIST"}}
    proc = run(
        [
            "bash", "-c",
            "set -euo pipefail; source ./pipeline.sh; "
            "declare -F step_report_at report_passed_at step_evidence_at "
            "strip_ansi pipeline_abspath >/dev/null; echo SOURCED",
        ],
        env=env,
    )
    assert proc.returncode == 0, (
        f"sourcing pipeline.sh with no globals set failed:\n{proc.stderr}\n"
        "scripts/selfcheck.sh sources it before anything is defined; if that "
        "aborts, the model's only working oracle is unusable"
    )
    assert "SOURCED" in proc.stdout, (
        f"the path-parameterised _at helpers must all exist after sourcing, "
        f"got:\n{proc.stdout}{proc.stderr}"
    )


def test_pipeline_steps_do_not_rely_on_errexit_alone(repo_root):
    """Every step in the chain must check its own status, not trust `set -e`."""
    text = (repo_root / "pipeline.sh").read_text()
    chain = text.split("run_deterministic_steps_for_current_iteration ()", 1)
    assert len(chain) == 2, "the step chain function is missing from pipeline.sh"
    body = chain[1]
    for step in ("step_generate_gds", "step_render", "step_drc", "step_lvs", "step_report"):
        assert f"{step} || return 1" in body, (
            f"{step} is called without an explicit `|| return 1` in:\n{body}\n"
            "orchestrate.sh calls this chain under a `!` negation, which "
            "disables errexit inside every function it reaches -- without the "
            "explicit check a failed step falls through and the chain reports "
            "success"
        )


def test_report_step_requires_a_verdict_not_just_a_file(repo_root):
    text = (repo_root / "pipeline.sh").read_text()
    assert "PIPELINE_VERDICT_RE='^RESULT:[[:space:]]*(PASS|FAIL)[[:space:]]*$'" in text, (
        "the report step must accept a report only when it carries a PASS/FAIL "
        "verdict; `[[ -f $report ]]` is always true because the `>` redirection "
        "created the file before the command ran, which is how step_report "
        "became incapable of failing"
    )
    step = text.split("step_report_at ()", 1)[1].split("\nstep_evidence_at ()", 1)[0]
    assert 'grep -qE "$PIPELINE_VERDICT_RE"' in step, (
        f"step_report_at must grep the report for a verdict, got:\n{step}"
    )
    assert "RESULT: ERROR" not in step.replace("PASS|FAIL", ""), (
        "RESULT: ERROR must not satisfy the verdict pattern -- 'could not "
        "verify' is not a result"
    )


# ---------------------------------------------------------------------------
# scripts/selfcheck.sh -- the model-facing oracle, argument handling only
# ---------------------------------------------------------------------------

def test_selfcheck_help_exits_clean(repo_root):
    proc = run(["bash", str(repo_root / "scripts" / "selfcheck.sh"), "--help"])
    assert proc.returncode == 0, f"--help must exit 0, got {proc.returncode}"
    assert "MODULE.py" in proc.stdout and "WORKDIR" in proc.stdout, (
        f"the usage text must state the arguments, got:\n{proc.stdout}"
    )


def test_selfcheck_rejects_a_missing_module_as_blocked(repo_root, tmp_path):
    proc = run(
        [
            "bash", str(repo_root / "scripts" / "selfcheck.sh"),
            str(tmp_path / "nope.py"), str(tmp_path / "work"),
        ]
    )
    assert proc.returncode == 2, (
        f"a missing module is 'could not check' (exit 2), not 'clean' (0) or "
        f"'dirty' (1); got {proc.returncode}.  Grading an unrun check as clean "
        "is the failure mode this whole harness exists to prevent."
    )
    assert "not found" in proc.stderr.lower(), (
        f"the reason must be stated, got:\n{proc.stderr}"
    )


def test_selfcheck_rejects_paths_outside_the_repository(repo_root, tmp_path):
    """The container mounts the repository; anything outside it is invisible."""
    outside = tmp_path / "outside.py"
    outside.write_text("def generate(name, tech):\n    raise NotImplementedError\n")
    proc = run(["bash", str(repo_root / "scripts" / "selfcheck.sh"), str(outside), str(tmp_path)])
    assert proc.returncode == 2, (
        f"a module outside the repository cannot be checked, got exit "
        f"{proc.returncode}; running anyway makes the tools read a path that "
        "does not exist inside the container and report nothing"
    )
    assert "outside" in proc.stderr.lower(), (
        f"the reason must name the constraint, got:\n{proc.stderr}"
    )


# ---------------------------------------------------------------------------
# The assembled prompt
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def prompt_dumper(tmp_path_factory):
    """Return ``dump(gate) -> str``: the real prompt for one curriculum rung.

    Uses orchestrate.sh's own ``AION_DUMP_PROMPT`` mode, so what is inspected is
    the assembled prompt and not a reimplementation of it.  ``AION_GATE`` forces
    a rung, which is what makes every rung inspectable from a single committed
    fixture -- the fixture's own score only ever reaches one of them.

    A GDS is planted next to the fixture module because the ``build`` rung is
    cleared by one existing, non-empty GDS and the committed tree has none; a
    tree that cannot leave rung 1 would make every other rung untestable.
    """
    from conftest import FIXTURES, ITER0, REPO_ROOT

    if shutil.which("jq") is None:
        pytest.skip("jq is not installed; orchestrate.sh cannot read state.json")
    if "AION_DUMP_PROMPT" not in (REPO_ROOT / "orchestrate.sh").read_text():
        pytest.skip("orchestrate.sh has no prompt dump mode to inspect")

    tmp = tmp_path_factory.mktemp("prompt")
    build_dir = tmp / "build"
    (build_dir / "layout").mkdir(parents=True)
    iter0 = build_dir / "layout" / "iteration_0"
    shutil.copytree(ITER0, iter0)
    shutil.rmtree(iter0 / "__pycache__", ignore_errors=True)
    _plant_gds(iter0 / f"{CELL}.py", iter0 / f"{CELL}.gds")

    cache: dict = {}

    def dump(gate: str) -> str:
        if gate in cache:
            return cache[gate]
        out = tmp / f"prompt.{gate}.txt"
        proc = run(
            [
                "bash", str(REPO_ROOT / "orchestrate.sh"),
                str(FIXTURES / "AION_inv_nand2_nor2_1_minimized.spice"),
                str(build_dir), "2",
            ],
            env={**os.environ, "AION_DUMP_PROMPT": str(out), "AION_GATE": gate},
        )
        assert proc.returncode == 0, (
            f"the prompt dump for rung {gate!r} failed (exit {proc.returncode}):\n"
            f"{proc.stdout}\n{proc.stderr}"
        )
        assert out.is_file(), f"AION_DUMP_PROMPT wrote no file for rung {gate!r}"
        cache[gate] = out.read_text()
        return cache[gate]

    return dump


def _plant_gds(module: Path, gds: Path) -> None:
    """Build the fixture module's GDS beside it, so rung 1 is cleared."""
    import importlib.util
    import sys

    from aion_layout.tech import sg13g2_tech

    spec = importlib.util.spec_from_file_location("aion_fixture_module", module)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.generate(CELL, sg13g2_tech).write_gds(str(gds))
    assert gds.stat().st_size > 0


@pytest.fixture(scope="module")
def dumped_prompt(prompt_dumper):
    """The prompt the loop would actually send: the rung the score selects."""
    return prompt_dumper("auto")


def _blocks_in(prompt: str) -> set:
    """Every evidence block index the packet in ``prompt`` actually carries."""
    return {int(m) for m in re.findall(r"^===== \[(\d+)\] (?!END)", prompt, re.M)}


@pytest.mark.parametrize("gate", LADDER)
@pytest.mark.parametrize("needle,blocks,why", PROMPT_NEEDLES)
def test_prompt_carries_exactly_the_evidence_its_rung_declares(
    prompt_dumper, gate, needle, blocks, why
):
    """A fact is present exactly when the rung carries a block that holds it.

    Both halves matter.  Present-when-declared is the original regression: the
    measured payload the loop used to inject was three characters, a line
    reading ``---``.  Absent-when-not-declared is the Stage 5 one: the whole
    point of a rung is that the turn is not also shown the evidence for six
    other rungs, and a filter that quietly kept everything would look identical
    from the outside.
    """
    prompt = prompt_dumper(gate)
    present = _blocks_in(prompt)

    if blocks is None:
        assert needle in prompt, (
            f"rung {gate!r}: the prompt is missing {needle!r}: {why}.  This is "
            "prompt framing, not evidence, so no rung may drop it."
        )
        return

    expected = bool(blocks & present)
    if expected:
        assert needle in prompt, (
            f"rung {gate!r}: the prompt carries block(s) {sorted(blocks & present)} "
            f"but not {needle!r}: {why}"
        )
    else:
        assert needle not in prompt, (
            f"rung {gate!r} declares blocks {sorted(present)}, none of which is one "
            f"of {sorted(blocks)}, yet {needle!r} is still in the prompt.  The rung "
            "filter is not filtering: the turn is being shown evidence for a rung "
            "it is not on, which is the whole cost Stage 5 exists to remove."
        )


@pytest.mark.parametrize("gate", LADDER)
def test_every_block_the_prompt_names_is_actually_in_it(prompt_dumper, gate):
    """No 'see block [N]' may point at a block this rung dropped.

    An unresolvable reference is not a cosmetic defect here: a measured run was
    lost to one @-reference the model could not resolve and spent its whole
    budget chasing.  The prompt used to assert 'every numeric design rule is in
    block [9]' unconditionally, and the pins and nets rungs do not carry it.
    """
    prompt = prompt_dumper(gate)
    present = _blocks_in(prompt)
    instructions = prompt.split("===== AION EVIDENCE PACKET =====", 1)[0]
    named = {int(m) for m in re.findall(r"block \[(\d+)\]", instructions)}
    missing = sorted(named - present)
    assert not missing, (
        f"rung {gate!r}: the instructions send the model to block(s) {missing}, "
        f"but the packet only carries {sorted(present)}."
    )


@pytest.mark.parametrize("gate", LADDER)
def test_every_rung_states_its_own_exit_criterion(prompt_dumper, gate):
    """Block [0] must say what clears the rung, in a number the host measures."""
    prompt = prompt_dumper(gate)
    assert f"THIS TURN : {gate}" in prompt, (
        f"rung {gate!r}: block [0] does not name the rung being graded"
    )
    assert "PASSES WHEN:" in prompt, (
        f"rung {gate!r}: block [0] states no exit criterion, so the turn has an "
        "instruction but no definition of done -- which is the whole-cell "
        "objective again, in miniature"
    )


@pytest.mark.parametrize("needle,why", PROMPT_MUST_NOT_CONTAIN)
def test_prompt_omits_broken_guidance(dumped_prompt, needle, why):
    assert needle not in dumped_prompt, (
        f"the assembled prompt still contains {needle!r}: {why}"
    )


@pytest.mark.parametrize("gate", LADDER)
def test_every_rung_fits_the_turn_budget(prompt_dumper, gate):
    """Measured, not guessed.

    Kimi-K2.7-Code answered the whole-cell objective with 64,167 characters of
    reasoning and zero output at a 16k completion budget, and answered one rung
    of an 11 KB prompt with a module that builds.  The upper bound here is what
    keeps a rung a rung; the lower bound is what stops the evidence collapsing
    back to a stub.
    """
    prompt = prompt_dumper(gate)
    size = len(prompt.encode("utf-8"))
    assert 6_000 < size < 30_000, (
        f"rung {gate!r}: the assembled prompt is {size} bytes (~{size // 4} tokens). "
        "Under Stage 5 one turn targets under 4,000 tokens; too small means the "
        "evidence collapsed back to a stub, too large means the rung is not narrow."
    )
    assert "(evidence unavailable" not in prompt
    assert "EVIDENCE UNAVAILABLE" not in prompt, (
        "pipeline.sh's step_evidence_at printed its failure banner instead of a "
        "packet"
    )


def test_prompt_names_the_module_to_write_and_the_one_to_leave_alone(dumped_prompt):
    assert "iteration_1/AION_inv_nand2_nor2_1.py" in dumped_prompt, (
        "the prompt must name the exact path for the next module; without it the "
        "model writes somewhere the pipeline never reads"
    )
    assert "iteration_0/AION_inv_nand2_nor2_1.py" in dumped_prompt, (
        "the prompt must show which source is the current one, and say not to "
        "modify it"
    )
    assert "CURRENT SOURCE" in dumped_prompt, (
        "the full current source must be inlined; asking the model to discover "
        "it costs a turn and often fails"
    )


def test_curriculum_off_restores_the_whole_packet(prompt_dumper):
    """AION_GATE=off must be a real escape hatch, not a renamed rung.

    It is what a bisect uses to ask "is the curriculum the reason this run
    behaves differently?", and it is only an answer if it restores the previous
    prompt rather than another scoped one.
    """
    prompt = prompt_dumper("off")
    present = _blocks_in(prompt)
    for index in (1, 2, 3, 4, 5, 6, 7, 9, 10):
        assert index in present, (
            f"AION_GATE=off dropped block [{index}]; it must emit the whole packet"
        )
    assert "OBJECTIVE FOR THIS TURN (the only thing graded)" not in prompt, (
        "AION_GATE=off still injected a per-rung objective"
    )


# ---------------------------------------------------------------------------
# set -e and the helpers the main loop calls unconditionally
# ---------------------------------------------------------------------------

#: Helpers `orchestrate.sh`'s main loop calls with no `||` guard.  Under
#: `set -euo pipefail` any one of them returning non-zero aborts the whole run.
LOOP_HELPERS = [
    "current_gate_key",
    "score_total",
    "record_iteration",
    "accept_or_reject",
    "note_gate_transition",
]


@pytest.mark.parametrize("helper", LOOP_HELPERS)
def test_loop_helpers_cannot_abort_the_run(repo_root, helper):
    """Each must end in an explicit `return 0`.

    This is a bug that happened, and it cost a validation run before anyone
    noticed.  ``note_gate_transition`` ended with

        [[ -n "$previous" && "$previous" != "null" ]] && print_banner ...

    which is the function's exit status.  On the FIRST iteration there is no
    previous rung, so the test is false, the chain returns 1, the function
    returns 1 -- and `set -e` killed the loop between scoring iteration 0 and
    the max-iterations check.  The run left `status: in_progress`, wrote no
    banner, and looked from the outside like it had simply stopped.

    A bare `&&` as the last line of a function is a returned exit status, not a
    conditional statement.  These five are bookkeeping: none of them has a
    failure the loop should die on.
    """
    text = (repo_root / "orchestrate.sh").read_text()
    start = text.find(f"\n{helper}() {{")
    assert start != -1, f"{helper} is gone from orchestrate.sh"
    body = text[start:]
    end = body.find("\n}\n")
    assert end != -1, f"cannot find the end of {helper}"
    body = body[:end]

    last = [
        line.strip()
        for line in body.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ][-1]
    safe = (
        last in ("return 0", "return")
        or last.endswith("|| true")
        or last.startswith("printf")
        or last.startswith("echo")
    )
    assert safe, (
        f"{helper} ends with {last!r}.  The main loop calls it with no `||` "
        "guard under `set -e`, so whatever that line evaluates to becomes the "
        "run's life or death.  End it with an explicit `return 0`."
    )
