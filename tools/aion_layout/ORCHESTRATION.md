# AION Standard-Cell Layout Generation — Harness Reference

> **Scope.** This file describes what the AION layout harness — `orchestrate.sh`, `pipeline.sh`,
> `scripts/evidence.py` and `scripts/selfcheck.sh` — actually does, **for a human reader**. It is a
> description, not a procedure: nothing here is addressed to an agent and nothing here is a step for
> anyone to execute. The per-iteration fix agent is asked for exactly one thing — write the next
> iteration's Python layout module — and its domain guidance lives in `SKILL.md`. No agent is
> authorised to write `state.json` or to set a verification status.

---

## Purpose

Turn a SPICE netlist for one standard cell into a DRC/LVS-clean GDS layout, by repeatedly rewriting a
single Python module that draws the cell through the AION layout API.

The loop alternates two halves that never mix:

- **A deterministic half.** Build the GDS, run Magic and KLayout DRC, run Netgen LVS, parse the raw
  artifacts, decide PASS/FAIL. Plain bash and Python, the same commands every time. No model is
  involved, so nothing here can hang on a tool prompt or loop on a repeated tool call.
- **A model half.** One call per iteration that is handed everything it needs inline and is expected
  to write one file. It does not discover state, run the pipeline, or record a verdict.

The deliverable is the last iteration's GDS together with the artifacts that were used to grade it.

---

## Entry point

```bash
./orchestrate.sh <SPICE_NETLIST> <BUILD_DIR> [MAX_ITERATIONS]
```

`MAX_ITERATIONS` defaults to `10`. The cell name is taken from the first `.subckt` line in
`SPICE_NETLIST`.

Environment:

| Variable | Meaning | Default |
| --- | --- | --- |
| `MODEL` | inference model id passed to the CLI wrapper | set in `orchestrate.sh` |
| `COPILOT_RCP` | path to the CLI wrapper that performs the model call | `../../../copilot-rcp.sh` (outside this repository) |
| `FIX_TIMEOUT` | wall-clock budget for one model call | `10m` |
| `MAX_BUILD_FAILURES` | consecutive build-gate failures tolerated before the run is blocked | `3` |
| `MEMORY_INLINE_BYTES` | bytes of `memory.md` (tail) inlined into the prompt | `4000` |
| `AION_DUMP_PROMPT` | assemble the prompt, write it to this path, exit — no model call, no Docker, no state change | unset |

`orchestrate.sh` also exports `AION_BUILD_DIR`, `AION_ROOT` and `AION_DEADLINE_FILE` for the helpers
it invokes.

Requires `jq`, `python3`, the `iic-osic-tools` container reachable through `scripts/docker_run.sh`,
and the CLI wrapper named by `COPILOT_RCP`.

---

## What the run produces

```text
BUILD_DIR/
├── memory.md                     # append-only notes written by the model, tail inlined next turn
└── layout/
    ├── state.json                # the harness's own record of progress
    ├── deadline.epoch            # epoch second at which the current model call's budget ends
    ├── iteration_0/
    │   ├── <CELL_NAME>.py        # the generator for this iteration
    │   ├── <CELL_NAME>.gds
    │   ├── <CELL_NAME>.png
    │   ├── drc/                  # sak-drc.sh run directory (Magic *.rpt, KLayout *.lyrdb)
    │   ├── lvs/                  # sak-lvs.sh run directory (netgen *.lvs.out, *.lvs.log)
    │   ├── report.txt            # DRC:/LVS:/RESULT: verdict from report_verification.py
    │   └── build_error.txt       # only when a model-written module failed the build gate
    ├── iteration_1/
    │   └── ...
    └── final/
        ├── <CELL_NAME>.py
        ├── <CELL_NAME>.gds
        ├── <CELL_NAME>.png
        ├── report.txt
        ├── evidence.txt          # the evidence packet for the graded iteration
        ├── drc/
        └── lvs/
```

`final/` is populated by copying the last iteration's artifacts, plus one freshly written
`evidence.txt`. There is no separate `drc_report.txt`, `lvs_report.txt` or `verification_report.txt`:
`report.txt` carries the verdict and `evidence.txt` carries the parsed detail behind it.

An iteration directory is never overwritten by a later iteration — each iteration writes only its own
directory, and the model is told to write only the next one.

---

## `state.json`

Created by `state_init` in `pipeline.sh` on the first run and never re-created afterwards:

```json
{
  "cell_name": "AION_inv_nand2_nor2_1",
  "current_iteration": 0,
  "max_iterations": 10,
  "steps": {
    "gds_generated": false,
    "rendered": false,
    "drc_done": false,
    "lvs_done": false,
    "report_generated": false
  },
  "last_result": null,
  "last_error": null,
  "status": "in_progress"
}
```

`status` takes one of: `in_progress`, `verified_clean`, `max_iterations_reached`, `blocked`,
`finalized`.

How the harness uses the file:

1. Every write goes through `state_write_atomic`, which runs a `jq` filter into a temporary file in
   the same directory and `mv`s it into place. A failed filter leaves the previous state untouched.
2. `state_reconcile` runs before each iteration's steps and clears any `steps` flag whose artifact is
   missing or implausible — an empty GDS or PNG, a `drc/` with no `*.rpt` or `*.lyrdb`, an `lvs/` with
   no `*.lvs.out` or `*.lvs.log`, a `report.txt` with no `RESULT: PASS|FAIL` line. A flag survives
   only on evidence, so a run killed mid-step resumes correctly instead of skipping the step.
3. Each step sets its flag only after the step function returned zero.
4. On a failing iteration the harness increments `current_iteration`, resets every `steps` flag to
   `false`, and stores the `RESULT:` line from that iteration's evidence packet in `last_result`.
5. `verified_clean` is set only when `report_passed` matched `^RESULT:\s*PASS\s*$` in the iteration's
   `report.txt`. `max_iterations_reached`, `blocked` and `finalized` are set by the harness at the
   corresponding points in the loop.

`state.json` is the graded verdict, so it is protected from the thing being graded: the harness
snapshots it (and the grader files the verdict depends on) before each model call, outside the
directory the model is given write access to, and restores it afterwards. A modification is reported
with a loud banner rather than silently accepted.

---

## The deterministic pipeline (`pipeline.sh`)

`pipeline.sh` is sourced by both `orchestrate.sh` and `scripts/selfcheck.sh`. Every step exists twice:

- a **path-parameterised `_at` variant** that reads no globals and takes explicit paths, and
- a **state-driven wrapper** that resolves paths from `BUILD_DIR` / `CELL_NAME` / `SPICE_NETLIST` /
  `STATE_FILE`, calls the `_at` variant, and records the step in `state.json` on success.

The host loop and the model-facing oracle therefore run byte-identical commands and cannot drift
apart into two different notions of "clean".

| Step | Command it runs in the container | Success condition |
| --- | --- | --- |
| `step_generate_scaffold_at` | `scripts/generate_from_netlist.py <netlist> -o <module> --summary` | non-empty module written |
| `step_generate_gds_at` | `scripts/generate_cell.py <module> <gds>` | stale GDS removed first, non-empty GDS written |
| `step_render_at` | `scripts/gds_to_image.py <gds> <png> --width 1600 --height 1200` | non-empty PNG written |
| `step_drc_at` | `sak-drc.sh -d -b -l macro -w <drc_dir> <gds>` | exit ≤ 1 **and** a `*.rpt` or `*.lyrdb` newer than the run's stamp file |
| `step_lvs_at` | `sak-lvs.sh -d -b -w <lvs_dir> -s <netlist> -l <gds> -c <cell>` | exit ≤ 1 **and** a `*.lvs.out` or `*.lvs.log` newer than the stamp file |
| `step_report_at` | `scripts/report_verification.py --cell … --parse-only` | the report contains a `RESULT: PASS` or `RESULT: FAIL` line |
| `step_evidence_at` | `scripts/evidence.py` on the host | non-empty packet on stdout |

Three invariants are load-bearing here:

- **Exit 1 is a result, not a failure.** `sak-drc.sh` exits 1 when it finds violations and
  `sak-lvs.sh` exits 1 on a mismatch. Those are the findings the loop exists to consume, so only
  exit statuses above 1 stop the run.
- **A step succeeds only on a fresh artifact.** Existence proves nothing when a `>` redirection
  created the file before the command ran, so each step takes a `mktemp` stamp first and requires a
  matching artifact newer than it.
- **`set -e` is not trusted.** `orchestrate.sh` calls the chain as
  `if ! run_deterministic_steps_for_current_iteration; then`, and a `!` negation makes POSIX shells
  ignore `errexit` inside every function called by that command. Every step therefore checks the
  runner's status explicitly and returns non-zero itself, and the chain has an explicit
  `|| return 1` after each step.

`report_passed_at` treats only an explicit `RESULT: PASS` line as a pass. A missing file, an empty
file and `RESULT: ERROR` all read as "not passed".

Container rules: `pipeline_docker` always runs `scripts/docker_run.sh` from the repository root,
because that script derives the container working directory from `$PWD`. Nothing nests one
`docker_run.sh` call inside another — once inside the container, `sak-drc.sh`, `sak-lvs.sh` and
`python3` are invoked directly, with `PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout`. Paths
outside this repository are invisible to the container and are rejected rather than mangled.
`strip_ansi` removes the container banner's escape sequences from anything that is stored or shown.

---

## The evidence packet (`scripts/evidence.py`)

The packet is what the model is shown. It is built on the host from the *raw* artifacts, not from
`report.txt`, and it is inlined into the prompt so the model never has to go looking. The same
builder produces `final/evidence.txt` and the packet `scripts/selfcheck.sh` prints.

It is one text document with a header, numbered blocks, and a footer:

| Block | Content | Byte cap |
| --- | --- | --- |
| 1 | `TARGET NETLIST` — the `.subckt` the layout must implement, its devices and net fan-out | never capped |
| 2 | `VERDICT` — DRC/LVS status recomputed from the raw artifacts | never capped |
| 3 | `MAGIC DRC REPORT` — verbatim, capped so every rule header and the trailer survive | 8000 |
| 4 | `KLAYOUT DRC ITEMS` — merged from every `*.lyrdb` in the run directory | 5000 |
| 5 | `NETGEN LVS DIGEST` — parsed device/net/pin comparison | 8000 |
| 6 | `EXTRACTED NETLIST` — what the tools see in the layout | 5000 |
| 7 | `LAYOUT DIGEST` — shapes, ports and crossings taken from the generator module | 12000 |
| 8 | `BUILD ERROR` — present only when the previous module failed the build gate | 5000 |

The header names the cell, netlist, iteration directory, module and the blocks present; the footer
gives the packet size against the budget (24 000 bytes by default) and names every block that was
shortened. When the packet is over budget, `enforce_budget` shortens low-priority blocks first and
never drops blocks 1–3.

Three rules make the packet safe to put in front of a model, and they are the reason it exists:

- **It never fails.** A missing or unparsable artifact becomes an explicit `(not available: …)` note
  and the exit status stays 0.
- **It never truncates silently.** Every cap states how many bytes it dropped.
- **It never reads absence as cleanliness.** Verdicts are recomputed from the raw artifacts, and an
  artifact that is absent, empty, truncated or unparsable reads as `NOT AVAILABLE` — not as `PASS`.

The layout digest replaces the rendered PNG as the model's view of its own geometry: the model is
text-only, so a picture carried no information for it, while the digest states shapes, layers, ports
and poly/active crossings in text that can be compared against the netlist. The PNG is still rendered
and kept as a human artifact.

`step_evidence_at` in `pipeline.sh` wraps the builder so that a non-zero exit or an empty packet
prints an `EVIDENCE UNAVAILABLE` block naming the cell, the paths and the captured stderr —
on stdout, where the caller is looking. `orchestrate.sh` additionally rejects any summary that does
not look like a packet, or that dropped a build error it was asked to carry, and falls back to
calling `scripts/evidence.py` directly.

---

## The model call

Once an iteration's report says FAIL and iterations remain, `orchestrate.sh` assembles the whole
prompt host-side and makes one call. The prompt contains:

- the task framing and the fix-priority order (topology and connectivity, then shorts, then spacing
  and enclosure, then area);
- the tail of `BUILD_DIR/memory.md`, the model's own notes from previous iterations;
- the complete evidence packet for the current iteration;
- the complete current source of the iteration's module;
- four numbered instructions: diagnose, append a note to `memory.md`, write the full corrected module
  to the next iteration's path, optionally self-check, then stop.

The call is made through the `COPILOT_RCP` wrapper under `timeout "$FIX_TIMEOUT"`, with the `view`,
`edit` and `bash` tools allowed, `write-outside-workspace` denied, and `--add-dir` limited to the
current and next iteration directories and `BUILD_DIR`.

The prompt tells the model that the repository is far larger than its context window and that only
two files are worth opening if it is stuck: `SKILL.md` for domain guidance and `GDS_PYTHON_API.md`
for the API. It contains no unresolvable file references, and no raw `sak-drc.sh` / `sak-lvs.sh`
recipe — those were removed because their report step could silently produce no verdict, which is the
failure this harness is built to prevent.

`AION_DUMP_PROMPT=<path> ./orchestrate.sh …` writes the assembled prompt to `<path>` and exits
without calling a model, touching Docker, or changing state. `tests/test_shell_surface.py` uses that
mode to assert what the prompt must and must not contain.

The call returns a failure to the harness when the wrapper exits non-zero or when the module the
prompt asked for was not written.

---

## The build gate

A model-written module is not accepted on the strength of being a file. `build_module` runs it in a
subprocess: it imports the module by path, requires a `generate(cell_name, tech) -> Cell`, calls it
with `sg13g2_tech`, and writes a GDS to a temporary file. A crash or a `sys.exit()` in model-written
code therefore cannot take the harness down, and stdout and stderr are captured to a traceback file
rather than mixed into the run's output.

If the build fails, the traceback is fed back to the model verbatim in the next prompt's `BUILD ERROR`
block and another attempt is made, up to `MAX_BUILD_FAILURES` consecutive failures. Each attempt is a
full model call against the same `FIX_TIMEOUT` budget. When the gate is still unsatisfied after the
last attempt the run stops with `status: blocked` and `last_error: "build gate not satisfied"`; the
final traceback stays at `iteration_N+1/build_error.txt`.

---

## `scripts/selfcheck.sh`

The one command the prompt gives the model for grading its own work in-turn:

```bash
./scripts/selfcheck.sh <MODULE.py> <WORKDIR> [<SPICE_NETLIST>]
```

It sources `pipeline.sh` and runs the identical `_at` chain the host runs — build GDS, Magic +
KLayout DRC, Netgen LVS, report, evidence packet — then prints the verdict block from the report. The
model's self-check and the host's grade are produced by the same code and cannot disagree.

- The cell name is the module's file stem. The netlist comes from the third argument, then
  `$SPICE_NETLIST`, then the netlist in this repository whose `.subckt` matches the cell name.
- Both paths must be inside the repository; the container cannot see anything else.
- Each step's very verbose container log is captured to `WORKDIR/logs/` so it does not swamp the
  evidence packet; on failure the tail of the log is printed, because the model has to see *why* a
  step failed and not just that it did.
- Exit status: `0` clean, `1` checked and dirty, `2` blocked — the check could not be run at all (bad
  arguments, a module that did not build, a tool that produced no report). A blocked check is never
  reported as clean.
- If a `DEADLINE` file holding one epoch second is reachable (`AION_DEADLINE_FILE`, or `DEADLINE` /
  `deadline.epoch` next to the work directory), the script prints how much of the turn's budget is
  left before and after the run. `orchestrate.sh` writes that file before every model call.

The work directory it is given is kept out of the iteration directories the host grades, so a
self-check's own DRC and LVS output can never be picked up as part of the host's evidence for that
iteration.

`make selfcheck CELL_MODULE=… RUNS_DIR=…` runs the same script. It is a full containerised
verification run, not a static check.

---

## Finalisation

When the loop ends with `verified_clean` or `max_iterations_reached`, `orchestrate.sh` finalises
deterministically: it copies the graded iteration's `.py`, `.gds`, `.png` and `report.txt` into
`final/`, copies the `drc/` and `lvs/` run directories, writes `final/evidence.txt`, and sets
`status: finalized`.

Nothing is re-verified at this point. The loop already produced every artifact for the graded
iteration, and a second DRC/LVS run could only produce a second opinion that disagrees with the
verdict the run was actually graded on.

`max_iterations_reached` is preserved in `state.json` and printed in the closing banner. A finalised
run is not a clean run unless the status that preceded finalisation was `verified_clean`.

---

## Failure and blocking

| Situation | What the harness does |
| --- | --- |
| A deterministic step fails outright (a command failure, not a violation) | `status: blocked`, `last_error: "deterministic step failed, see stdout"`, exit 1 |
| The model call fails or writes no module | `status: blocked`, `last_error: "fix request failed"`, exit 1 |
| `MAX_BUILD_FAILURES` consecutive build-gate failures | `status: blocked`, `last_error: "build gate not satisfied"`, exit 1 |
| DRC/LVS still failing at the last iteration | `status: max_iterations_reached`, then finalise |
| DRC and LVS both pass | `status: verified_clean`, then finalise |

---

## Standing invariants

1. **Fail closed.** An artifact that is absent, empty, truncated, unparsable or merely not positively
   confirmed clean is not clean. Only positive evidence of cleanliness — a `RESULT: PASS` line, a
   Magic report carrying its own zero count — counts as a pass.
2. **The graded is not the grader.** The verdict lives in files the model cannot write; they are
   snapshotted before each call and restored after it, and any modification is reported loudly.
3. **The netlist is the specification.** LVS compares against the original `SPICE_NETLIST`. The
   netlist is never edited to make a comparison pass.
4. **One generator per iteration.** Each iteration writes only its own directory; no iteration's
   source is overwritten by a later one.
5. **Evidence is pushed, not pulled.** Everything the model needs is assembled host-side and inlined,
   so a turn is not spent discovering what went wrong and the packet's contents are testable offline.
6. **The two halves run the same code.** The host loop and the model's self-check both go through
   `pipeline.sh`'s `_at` steps, so there is only one definition of "verified".

---

## Offline surfaces

- `PYTHONPATH=. python3 -m pytest tests/ -q` — the host-side suite. No container and no PDK are
  needed: the parsers, the evidence packet, the scaffold and the shell surface are all checked
  against fixtures under `tests/fixtures/`.
- `AION_DUMP_PROMPT=<path> ./orchestrate.sh <netlist> <build_dir>` — assemble and inspect the prompt
  with no model call and no state change.
- `make test`, `make verify`, `make selfcheck` — see `Makefile` and `CLI_REFERENCE.md`.
