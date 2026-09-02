---
name: draw-layout-AI
description: Draw the layout of a standard cell using an iterative AI flow
---

# AION Standard-Cell Layout Generation

## Purpose

Generate a transistor-level standard-cell layout from a SPICE netlist and iteratively refine it until it is DRC/LVS clean.

The agent must:

1. Convert the SPICE netlist into an initial Python layout generator.
2. Generate a GDS layout.
3. Render the layout to PNG.
4. Run DRC and LVS.
5. Analyze both the verification reports and the rendered layout.
6. Modify the Python layout generator to fix issues.
7. Repeat until DRC/LVS pass or the iteration limit is reached.
8. Preserve every iteration for traceability.

The final deliverable is a DRC/LVS-verified GDS layout and its rendered image.

---

## Execution Mode

This skill supports two invocation styles:

**A. Long-running session** — one CLI session runs the whole loop start to finish, calling itself iteration by iteration.

**B. Orchestrated (recommended)** — a small outer driver script (`orchestrate.sh`, in `tools/aion_layout/`, two directories up from this file) invokes the CLI once per iteration as a short-lived, non-interactive call, then checks `state.json` to decide whether to invoke again, stop, or finalize. See "Orchestration" at the end of this file.

Mode B is strongly preferred, especially on models (e.g. Kimi K2/K2.x) that are prone to losing track of tool-call history after a context compaction and re-issuing the same tool call repeatedly. Each invocation in Mode B starts with a small, fresh context — the state file plus the current iteration's artifacts — so there is no long session to compact and nothing stale to lose track of.

Because of this, **every step below must be written and read assuming the agent might be starting a brand-new context right now.** Never assume you remember what happened earlier in this file's execution — always check `state.json` first.

---

## Inputs

The skill receives:

- `SPICE_NETLIST`: path to a SPICE netlist containing one standard-cell `.subckt`.
- `BUILD_DIR`: directory where all generated artifacts must be stored.

Optional:

- `MAX_ITERATIONS`: maximum number of layout iterations. Default: `10`.

Determine the cell name from the first `.subckt` declaration in `SPICE_NETLIST`.

---

## Expected Outputs

The final artifacts must be placed in:

```text
BUILD_DIR/layout/final/
├── <CELL_NAME>.gds
├── <CELL_NAME>.png
├── drc_report.txt
├── lvs_report.txt
└── verification_report.txt
```

Every iteration must additionally be preserved:

```text
BUILD_DIR/layout/
├── state.json
├── iteration_0/
│   ├── <CELL_NAME>.py
│   ├── <CELL_NAME>.gds
│   ├── <CELL_NAME>.png
│   ├── drc/
│   ├── lvs/
│   └── report.txt
├── iteration_1/
│   └── ...
└── final/
    └── ...
```

Never overwrite a previous iteration's Python source.

---

## Step 0 — State File (read this before every single step)

Maintain `BUILD_DIR/layout/state.json`. This file is the single source of truth for progress. It must survive across separate invocations, so nothing here may depend on conversational memory.

Schema:

```json
{
  "cell_name": "INV_X1",
  "current_iteration": 0,
  "max_iterations": 10,
  "last_completed_step": "none",
  "steps": {
    "gds_generated": false,
    "rendered": false,
    "drc_done": false,
    "lvs_done": false,
    "report_generated": false,
    "analyzed": false
  },
  "last_result": null,
  "retry_count": 0,
  "last_error": null,
  "status": "in_progress"
}
```

Rules for using it:

1. **Before doing anything else**, read `state.json` if it exists. If it doesn't exist, create it at `current_iteration: 0` with all `steps` false.
2. Determine the current iteration and the current incomplete step from `steps`. Resume from there — do **not** redo a step already marked `true` for the current iteration.
3. Update `state.json` immediately after each sub-step completes (GDS generated, rendered, DRC done, LVS done, report generated, analyzed) — before starting the next sub-step. Small, frequent writes, not one write at the end.
4. When you finish analyzing an iteration and decide DRC/LVS still fail, reset `steps` to all `false`, increment `current_iteration`, and set `retry_count: 0` before starting the next iteration's work.
5. When DRC and LVS both pass, set `"status": "verified_clean"`. When `current_iteration` reaches `max_iterations` without passing, set `"status": "max_iterations_reached"`.
6. If you are about to run a command and `state.json` shows you already ran that exact step for the current iteration, **stop** — re-read `state.json` and act on what it says instead of re-running the command.

---

## Required Context

On the **first ever invocation only** (iteration 0, `state.json` does not yet exist or `current_iteration == 0` and no steps completed), read exactly these two files:

```text
@GDS_PYTHON_API.md
@CLI_REFERENCE.md
```

and the content of this exact folder:

```text
@context
```

These files define the available layout API and CLI commands. If running in orchestrated mode (separate invocation per iteration), you will not remember having read these on later iterations — re-read the two reference files at the start of every invocation, since they're small; do **not** re-read the full history of previous iterations' logs or reports, since `state.json` and `last_result` already summarize what you need to know from prior iterations.

Do not read unrelated source files during initial setup.

Do not explore the repository unnecessarily.

During layout refinement, use the API reference, CLI reference, generated layout source, rendered PNG, and verification reports **for the current iteration only** as the primary sources of information.

---

## Required Environment

The flow uses:

- Python 3.10+
- AION Docker container: `iic-osic-tools`
- KLayout
- `sak-drc.sh`
- `sak-lvs.sh`
- Repository wrapper:

```text
../../scripts/docker_run.sh
```

All Python layout scripts must run inside the Docker container with:

```text
PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout
```

The Python package is not installed globally inside the container.

---

# Workflow

## Step 1 — Setup

Read `state.json` (Step 0). If this is a fresh run (no `state.json`), determine `CELL_NAME` from the first `.subckt` line in `SPICE_NETLIST`, write it into `state.json`, and create:

```bash
mkdir -p "BUILD_DIR/layout/iteration_0"
mkdir -p "BUILD_DIR/layout/final"
```

Define:

```text
CELL_MODULE_N = BUILD_DIR/layout/iteration_N/<CELL_NAME>.py
GDS_N         = BUILD_DIR/layout/iteration_N/<CELL_NAME>.gds
IMG_N         = BUILD_DIR/layout/iteration_N/<CELL_NAME>.png
```

where `N` is `current_iteration` from `state.json`.

Use absolute paths internally whenever possible to avoid path concatenation errors.

If `state.json` already exists and shows steps completed for the current iteration, **skip straight to the first incomplete step** — do not redo setup.

---

# Step 2 — Generate Initial Layout

Only runs when `current_iteration == 0` and `steps.gds_generated == false`.

Generate the initial Python layout representation using:

```bash
../../scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/generate_from_netlist.py SPICE_NETLIST -o CELL_MODULE_0 --summary"
```

The generated scaffold should provide the initial:

- cell boundary
- power rails
- active regions
- poly gates
- pins
- transistor placement

The scaffold is only a starting point. It is expected to require routing and geometry refinement (and possibly some extra devices).

Update `state.json` when done.

---

# Step 3 — Iterative Layout Optimization

**In orchestrated mode, each invocation executes ONE iteration (Steps 3.1–3.6 below) for `current_iteration` as read from `state.json`, then stops. It does not loop internally and does not decide on its own to continue to the next iteration — that decision belongs to the outer driver script, or to Step 4 if verification passed.**

If running in long-session mode instead, you may proceed automatically to the next iteration after finishing Step 3.6 — but still write and check `state.json` at every step, and still obey the retry caps below.

Default:

```text
MAX_ITERATIONS = 10
```

For the current iteration, perform the following steps in order, **skipping any step already marked complete in `state.json`**.

---

## Step 3.1 — Generate GDS

Skip if `steps.gds_generated == true`.

Convert the current Python layout generator into GDS:

```bash
../../scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/generate_cell.py CELL_MODULE_N GDS_N"
```

If GDS generation fails:

1. Inspect the Python source and error message.
2. Fix the current iteration source.
3. Retry GDS generation — **maximum 2 retries for this step** (increment `state.json`'s `retry_count` on each attempt).
4. If it still fails after 2 retries with the same or an equivalent error, **stop**. Write `"status": "blocked"` and `last_error` into `state.json` describing the failure, and report it to the user instead of continuing to retry. Do not attempt a third retry.

Never run this command a second time with byte-identical arguments and an unchanged source file — check `retry_count` and the file's contents before retrying.

Update `state.json` (`steps.gds_generated = true`, `retry_count = 0`) on success.

---

## Step 3.2 — Render Layout

Skip if `steps.rendered == true`.

Render the generated GDS:

```bash
../../scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/gds_to_image.py GDS_N IMG_N --width 1600 --height 1200"
```

The PNG is an important debugging artifact. Use it to inspect:

- transistor placement
- diffusion geometry
- poly routing
- contacts
- metal routing
- pin accessibility
- shorts
- disconnected regions
- spacing problems
- obviously incorrect topology
- overall cell structure

Apply the same 2-retry cap and stop-and-report rule as Step 3.1 if rendering fails.

Update `state.json` on success.

---

## Step 3.3 — Run DRC

Skip if `steps.drc_done == true`.

Create:

```text
BUILD_DIR/layout/iteration_N/drc
```

Run DRC:

```bash
../../scripts/docker_run.sh "cd tools/aion_layout && sak-drc.sh -d -b -l macro -w DRC_DIR GDS_N"
```

Important: **Never nest `docker_run.sh` calls.** `docker_run.sh` launches the container. Once inside the container, invoke `sak-drc.sh` and `sak-lvs.sh` directly.

Apply the same 2-retry cap as Step 3.1 for actual command failures (not for DRC reporting violations — a DRC run that completes and reports violations is a _success_ of this step; violations get fixed in the next iteration, not by re-running DRC).

Update `state.json` on success.

---

## Step 3.4 — Run LVS

Skip if `steps.lvs_done == true`.

Create:

```text
BUILD_DIR/layout/iteration_N/lvs
```

Run:

```bash
../../scripts/docker_run.sh "cd tools/aion_layout && sak-lvs.sh -d -b -w LVS_DIR -s SPICE_NETLIST -l GDS_N -c CELL_NAME"
```

LVS must compare the generated layout against the original `SPICE_NETLIST`. Do not modify the SPICE netlist to make LVS pass. The layout must be corrected instead.

Same 2-retry cap for command failures; an LVS run that completes and reports mismatches is a step success, not a failure to retry.

Update `state.json` on success.

---

## Step 3.5 — Generate Verification Report

Skip if `steps.report_generated == true`.

Run:

```bash
../../scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/report_verification.py --cell CELL_NAME --gds GDS_N --netlist SPICE_NETLIST --runs-dir BUILD_DIR/layout/iteration_N --parse-only > BUILD_DIR/layout/iteration_N/report.txt"
```

The report is the primary machine-readable source for DRC/LVS status.

Update `state.json` on success, and copy the report's top-line PASS/FAIL summary into `state.json`'s `last_result` field (a short string, not the full report — see note on context size below).

---

# Step 3.6 — Analyze the Result

Skip if `steps.analyzed == true`.

Read the **summary lines** of:

```text
BUILD_DIR/layout/iteration_N/report.txt
```

Don't pull the entire report into context if it's long — read the PASS/FAIL lines and violation counts first, and only read further detail (specific violation descriptions) for violations you're about to act on. The same applies to raw docker/DRC/LVS command output: summarize rather than carrying full logs forward. Every iteration's context is meant to start small; large logs are the main thing that pushes a session toward a compaction, which is exactly when tool-call loops have been observed.

Also inspect:

```text
BUILD_DIR/layout/iteration_N/<CELL_NAME>.png
```

Always use **both** sources. Do not rely solely on the DRC/LVS report.

---

## If DRC and LVS PASS

If the report contains:

```text
DRC: PASS
LVS: PASS
```

or equivalent: set `state.json`'s `"status": "verified_clean"`, mark `steps.analyzed = true`, and **stop here**. Do not perform unnecessary modifications to an already clean layout. Proceed to Step 4 — Finalize (either now, if in long-session mode, or on the driver script's next invocation, if orchestrated).

---

## If Verification Fails

If DRC or LVS fails and `current_iteration + 1 < max_iterations`:

1. Mark `steps.analyzed = true` and record a short `last_result` summary in `state.json` (e.g. `"LVS: OUT disconnected from drain"`).
2. Create:

```bash
mkdir -p "BUILD_DIR/layout/iteration_N+1"
```

3. Copy the current Python generator: `CELL_MODULE_N → CELL_MODULE_N+1`.
4. Modify only the new iteration's Python file. Diagnose the failure using: DRC report summary, LVS report summary, rendered PNG, SPICE topology, `GDS_PYTHON_API.md`, `CLI_REFERENCE.md`.
5. Update `state.json`: increment `current_iteration`, reset all `steps` to `false`, reset `retry_count` to `0`.
6. **Stop here if orchestrated** — the driver script will invoke the next iteration. If in long-session mode, continue directly into Step 3.1 for the new iteration.

Never modify the previous iteration's Python source.

---

# Layout Debugging Strategy

When deciding what to modify, prioritize problems in this order:

1. **Incorrect transistor topology**
2. **Missing or incorrect source/drain connections**
3. **Missing contacts/vias**
4. **Missing power connections**
5. **Missing input/output connections**
6. **LVS connectivity mismatches**
7. **DRC shorts**
8. **DRC spacing violations**
9. **DRC enclosure violations**
10. **Other geometric/design-rule issues**
11. **Layout compactness and visual quality**

Do not optimize area before connectivity and verification are correct.

---

## First Iteration Special Rule

On `iteration == 0`, do not spend significant effort performing detailed DRC/LVS diagnosis. The automatically generated scaffold provides limited information.

Instead, focus on completing the obvious physical implementation: source connections, drain connections, transistor interconnect, missing devices, contacts, vias, input routing, output routing, power routing, topology implied by the SPICE netlist.

After the first iteration, use detailed DRC/LVS feedback to drive optimization.

---

# LVS Debugging

When LVS fails, determine whether the problem is:

### Missing connection

A net exists in SPICE but is disconnected in the layout. Fix the physical routing.

### Incorrect connection

Two nets are accidentally shorted. Fix the metal/poly/diffusion geometry.

### Missing device

A MOS device exists in SPICE but cannot be extracted from the layout. Check: active region, poly gate, source/drain geometry, contacts, layer combinations, transistor dimensions.

### Incorrect device parameters

Check the extracted transistor geometry against the SPICE instance. Do not alter the SPICE netlist to hide the mismatch.

---

# DRC Debugging

Use the exact DRC violation information to determine which geometry is incorrect. Typical fixes include: increasing spacing, enlarging enclosure, correcting via/contact placement, extending metal, moving poly, separating nets, correcting diffusion geometry, removing accidental overlaps, respecting minimum widths.

Prefer small, targeted modifications over completely redesigning the cell.

---

# Iteration Philosophy

Each iteration should make a concrete improvement. Do not randomly modify geometry. For every modification, have a reason such as:

```text
LVS reports OUT disconnected from drain → add metal connection.
DRC reports M1 spacing violation → move routing by minimum legal spacing.
LVS reports missing PMOS → correct active/poly/contact geometry.
```

Keep the generated layout structurally simple unless the topology requires otherwise. Preserve working portions of the previous iteration.

---

# Step 4 — Finalise

Runs when `state.json` shows `"status": "verified_clean"` or `"status": "max_iterations_reached"`.

Select the last generated layout as `GDS_LAST` and `IMG_LAST` (from `current_iteration` in `state.json`).

Create:

```bash
FINAL_DIR="BUILD_DIR/layout/final"
mkdir -p "$FINAL_DIR"
```

Run DRC one final time:

```bash
../../scripts/docker_run.sh "cd tools/aion_layout && sak-drc.sh -d -b -l macro -w ${FINAL_DIR}/drc GDS_LAST"
```

Run LVS one final time:

```bash
../../scripts/docker_run.sh "cd tools/aion_layout && sak-lvs.sh -d -b -w ${FINAL_DIR}/lvs -s SPICE_NETLIST -l GDS_LAST -c CELL_NAME"
```

Generate the final verification report:

```bash
../../scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/report_verification.py --cell CELL_NAME --gds GDS_LAST --netlist SPICE_NETLIST --runs-dir ${FINAL_DIR} --parse-only > ${FINAL_DIR}/verification_report.txt"
```

Apply the same 2-retry cap to each of these three commands as elsewhere in this skill.

## Copy Final Artifacts

```bash
cp GDS_LAST "${FINAL_DIR}/${CELL_NAME}.gds"
cp IMG_LAST "${FINAL_DIR}/${CELL_NAME}.png"
```

The final directory must therefore contain:

```text
BUILD_DIR/layout/final/
├── <CELL_NAME>.gds
├── <CELL_NAME>.png
├── verification_report.txt
├── drc/
└── lvs/
```

---

# Step 4.1 — DRC/LVS Summary Files

Generate:

```text
BUILD_DIR/layout/final/drc_report.txt
BUILD_DIR/layout/final/lvs_report.txt
```

The summaries should contain the relevant verification result and violation information extracted from `verification_report.txt`.

Prefer using the verification reporter directly rather than fragile text-processing pipelines when possible.

If shell extraction is required, use:

```bash
# DRC
../../scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/report_verification.py --cell CELL_NAME --gds GDS_LAST --netlist SPICE_NETLIST --runs-dir ${FINAL_DIR} --parse-only" \
  | sed -n '/^DRC/,/^LVS/p' | head -n -1 \
  > "${FINAL_DIR}/drc_report.txt"
```

and:

```bash
# LVS
../../scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/report_verification.py --cell CELL_NAME --gds GDS_LAST --netlist SPICE_NETLIST --runs-dir ${FINAL_DIR} --parse-only" \
  | sed -n '/^LVS/,/^RESULT/p' \
  > "${FINAL_DIR}/lvs_report.txt"
```

Mark `state.json`'s `"status": "finalized"` once done.

---

# Failure at Maximum Iterations

If `current_iteration == max_iterations - 1` and DRC/LVS is still failing:

1. Stop iterating.
2. Finalise using the last generated layout (Step 4).
3. Generate the final reports.
4. Clearly report that the iteration limit was reached.
5. Do **not** claim that the layout is DRC/LVS clean.

The final status must accurately reflect the verification result.

---

# Important Rules

## Rule 1 — Docker

Always run Python layout scripts through `../../scripts/docker_run.sh` with `PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout`.

## Rule 2 — No Nested Docker

Never execute `docker_run.sh` from inside another `docker_run.sh` command. Inside the container, directly execute `sak-drc.sh`, `sak-lvs.sh`, `klayout`, `python3` as required.

## Rule 3 — Preserve Iterations

Maintain exactly one Python layout generator per iteration (`iteration_0/<CELL_NAME>.py`, `iteration_1/<CELL_NAME>.py`, ...). Never overwrite previous iterations.

## Rule 4 — Use Absolute Paths

Resolve `SPICE_NETLIST` and `BUILD_DIR` to absolute paths before constructing derived paths whenever possible.

## Rule 5 — Do Not Modify the Netlist

The SPICE netlist is the source of truth for connectivity. Fix the layout, not the netlist.

## Rule 6 — Verification Is Mandatory

Never declare success based only on visual inspection. A final layout is considered clean only when both `DRC = PASS` and `LVS = PASS` have been confirmed by the verification flow.

## Rule 7 — Use Image + Reports

When fixing an iteration, always consider: verification report summary + DRC/LVS details + rendered PNG + SPICE topology.

## Rule 8 — Avoid Unnecessary Exploration

Do not browse unrelated source code or repository files. On the first invocation, read only `@GDS_PYTHON_API.md`, `@CLI_REFERENCE.md`, `@context/`. During iterations, inspect only files required to understand or fix the current iteration.

## Rule 9 — No Repeated Identical Actions

Never issue the same tool call (same command, same arguments) twice in a row. Before running any command, check `state.json` to confirm this step hasn't already been completed for the current iteration. If a command's output would be identical to the last time you ran it, stop and re-read `state.json` instead of running it again.

## Rule 10 — State Before Memory

Always trust `state.json` over your own recollection of what happened earlier in this task. If they disagree, `state.json` wins. This matters most across separate invocations (see Orchestration below), but applies even within a single long session.

## Rule 11 — Keep Context Small

Prefer summaries over full logs. Read report/DRC/LVS output at the summary level first; only pull in full detail for the specific violation you're currently fixing. Don't re-read previous iterations' full artifacts — `state.json`'s `last_result` field is the intended summary of prior iterations.

---

# Final Response

At the end (Step 4 completed), return a concise report in this format:

```text
AION Standard-Cell Layout Generation

Cell: <CELL_NAME>
Iterations: <N>

DRC: PASS/FAIL
LVS: PASS/FAIL

GDS:
BUILD_DIR/layout/final/<CELL_NAME>.gds

Layout image:
BUILD_DIR/layout/final/<CELL_NAME>.png

DRC report:
BUILD_DIR/layout/final/drc_report.txt

LVS report:
BUILD_DIR/layout/final/lvs_report.txt

Verification report:
BUILD_DIR/layout/final/verification_report.txt
```

If verification failed, explicitly state:

```text
The maximum iteration count was reached and the final layout is not DRC/LVS clean.
```

Never report PASS unless it is confirmed by the final verification run.

---

# Orchestration (recommended execution mode)

Rather than running this skill as one long CLI session for the whole loop, invoke the CLI once per iteration using the companion driver script `orchestrate.sh` (in `tools/aion_layout/`, two directories up from this file). The driver:

1. Invokes the CLI non-interactively with a prompt telling it to execute one iteration (or Step 4, once verified/exhausted) and to consult `state.json` first.
2. Waits for that invocation to exit.
3. Reads `state.json` to decide whether to invoke again for the next iteration, stop, or call the finalize step.

Because each invocation is short and starts fresh, there's no long session to compact and no stale tool-call history to lose track of — the two conditions that have been observed to trigger repeated-identical-tool-call loops on some models. This costs a small amount of redundant work per invocation (re-reading the two reference docs each time) but removes the main structural cause of runaway loops.

See `orchestrate.sh` for the reference driver implementation.
