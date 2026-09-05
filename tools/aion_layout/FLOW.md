# The flow — what is mechanical, and what the model does

One iteration of `./orchestrate.sh <netlist> <build_dir> <max_iterations>`.

Read this to answer one question: **where in the loop does judgement happen?**
Everywhere else, the answer is already determined by the netlist and the
artifacts on disk, and is computed by bash and Python that cannot loop, cannot
hang and cannot decide anything.

There is exactly one model call per iteration, and it does exactly one thing:
**write the next version of a Python module.** Nothing else in the diagram below
is the model's.

---

## The loop

```
   netlist.spice ─────────────────────────────────────────────────┐
        │                                                          │ (read every
        │  HOST  step_generate_scaffold_at                         │  iteration:
        ▼        (iteration 0 only)                                │  it is the
   iteration_0/<cell>.py ◄── auto_scaffold: rails, active bands,   │  spec, and
        │                    poly per external input, pins.         │  it never
        │                    Deliberately incomplete.               │  changes)
        │                                                           │
        │  ┌─────────────── DETERMINISTIC CHAIN — no model ────────┼──────────┐
        │  │                                                        │          │
        ▼  ▼                                                        │          │
   step_generate_gds   generate_cell.py       → <cell>.gds          │          │
   step_render         gds_to_image.py        → <cell>.png  (humans)│          │
   step_drc            sak-drc.sh   (Docker)  → drc/  magic+klayout │          │
   step_lvs            sak-lvs.sh   (Docker)  → lvs/  magic+netgen  │          │
   step_report         report_verification.py → report.txt          │          │
        │                    exactly one ^RESULT: line              │          │
        └────────────────────────────────────────────────────────────────────┘
        │
        ▼
   HOST  host_verdict(report.txt)          → state.json .last_result
   HOST  score_iteration(iter_dir, cell, netlist)   → Score          ── §Score
   HOST  current_gate(subckt, score)                → the rung       ── §Ladder
   HOST  accept_or_reject(n, score)                 → .base_iteration
   HOST  ledger.append(...)                         → ledger.jsonl
        │
        │  report says PASS ──────────────► SUCCESS, finalise
        │  iterations exhausted ──────────► finalise the BEST iteration
        ▼
   HOST  evidence.py --gate auto
             ├─ builds every block from the RAW artifacts
             ├─ keeps only the blocks this rung declares
             ├─ narrows block [10] to the calls this rung needs
             └─ prepends block [0]: the objective for this turn
        │
        ▼
   HOST  build_fix_prompt: framing + ledger digest + memory.md tail
                         + the packet + the full current source
        │
        ▼
   HOST  guard_arm_state  (snapshot state.json + every grader, OUTSIDE build/)
   HOST  context_lock     (move context/ aside for the duration)
        │
        ▼
   ╔════════════════════════════════════════════════════════════════════╗
   ║  THE MODEL  — one call, timeout $FIX_TIMEOUT                       ║
   ║                                                                    ║
   ║   copilot -p "<prompt>"   (one completion per tool call, and its    ║
   ║     own ~12.6k-token system prompt re-sent on every one of them)   ║
   ║     tools: view, edit, bash                                        ║
   ║     may write:  iteration_N+1/<cell>.py   and   memory.md          ║
   ║     may run:    ./scripts/selfcheck.sh (the same chain, on a       ║
   ║                 workdir OUTSIDE the graded tree)                   ║
   ║                                                                    ║
   ║   Its whole job: read block [0], and write the module that clears  ║
   ║   that one rung.                                                   ║
   ╚════════════════════════════════════════════════════════════════════╝
        │
        ▼
   HOST  context_unlock, guard_restore_state, guard_verify_graders
        │        (a grader the model edited is restored, named in a banner
        │         and recorded — never a reason to abort: the attempt is the
        │         most interesting measurement the run can make)
        ▼
   HOST  build gate: import the module, call generate(), write a GDS
        │
        ├─ builds ──────────► .current_iteration += 1, next pass
        └─ fails ───────────► traceback becomes block [8] of the next prompt,
                              up to MAX_BUILD_FAILURES retries, each one a
                              model call charged to the same global budget
```

---

## HOST vs MODEL, line by line

| Step | Who | Implemented in | Can it decide anything? |
| --- | --- | --- | --- |
| Scaffold the starting module | HOST | `aion_layout/auto_scaffold.py` | No — a fixed function of the netlist |
| GDS, PNG, DRC, LVS, report | HOST | `pipeline.sh` `step_*_at` | No — external tools, exit ≤ 1 is a result |
| The verdict | HOST | `report_verification.py` | No — one `RESULT:` line on every path |
| The score | HOST | `scripts/score_iteration.py` | No — weights are ordered, not tuned |
| **Which rung to ask for** | HOST | `scripts/curriculum.py` | No — first rung the score does not clear |
| Which evidence to show | HOST | `scripts/evidence.py` | No — the rung declares its blocks |
| Accept or reject an iteration | HOST | `orchestrate.sh accept_or_reject` | No — `score <= best` |
| **Write the module** | **MODEL** | — | **Yes. This is the only judgement in the loop.** |
| Note-taking (`memory.md`) | MODEL | — | Yes, but nothing depends on it |
| Build gate | HOST | `orchestrate.sh build_module` | No — it imports and calls `generate()` |
| What ships | HOST | `orchestrate.sh` finalise | No — the passing iteration, else the best |

The model never chooses which problem to work on, never decides whether it
succeeded, and never touches the verdict. It is given one objective and one
file to write.

---

## The ladder {#Ladder}

Derived per netlist by `scripts/curriculum.py`. A rung that could never fail for
a given cell is not in that cell's ladder.

| # | rung | asks for | cleared when | in the ladder if |
| --- | --- | --- | --- | --- |
| 1 | `build` | a module that imports and returns a `Cell` | `score.buildable` | always |
| 2 | `gates` | one poly/active crossing per transistor | GDS crossings == `len(devices)` | the netlist has devices |
| 3 | `devices` | every device extractable, right W/L | `device_delta == 0` | the netlist has devices |
| 4 | `taps` | well and substrate ties | no `LU.*` violation | a bulk net is derivable |
| 5 | `shorts` | no two nets merged into one node | `disconnected == 0` | the netlist has devices |
| 6 | `pins` | every port present and matched | `unmatched_pins == 0` | the netlist has pins |
| 7 | `nets` | the layout implements the netlist | `lvs_verdict == "match_uniquely"` | the netlist has devices |
| 8 | `drc` | clear the remaining geometry | `drc_violations == 0` | always |

Rungs 5 and 6 were one rung, and splitting them is the clearest illustration of
what a rung has to be. Together they asked for two different jobs — unmerge the
shorted nets *and* label every port — and the model spent 42,914 characters of
reasoning on the pair without emitting a line of code. `disconnected` and
`unmatched_pins` are separate fields on `Score`, so the split is not a guess
about what is easier: each half has its own measurement.

Two properties make this work without any stored state:

- **`current_gate` walks from the bottom every pass.** There is no "current
  rung" variable to drift away from the artifacts. A regression resumes at the
  rung that broke, automatically.
- **Every exit test fails closed.** `device_delta == 0` is also true of an
  iteration whose LVS never ran, so each rung first asks whether the tool ran
  at all. An unmeasured rung has *not* been cleared.

The tie nets for rung 4 come from the device **bulk** terminals, not from the
pin names `VDD`/`VSS` — a cell whose rails are called `VPWR`/`VGND` gets the
same rung with the right net names.

---

## The score {#Score}

`scripts/score_iteration.py`. Lower is better; `0` means DRC- and LVS-clean.
The weights are *ordered*, not tuned:

```
100000 × unbuildable        a module that does not build is not measurable
  5000 × degraded artifact  "we could not tell" must never look like progress
  1000 × device delta       connectivity outranks geometry: a layout that
   500 × LVS verdict        implements the wrong circuit cannot be repaired
   200 × net delta          by moving shapes
   150 × disconnected node
   120 × unmatched port
    10 × DRC violation
```

The crossing count is measured and reported but **not** weighted: `device_delta`
already charges for a missing transistor, and charging twice would let one
defect outrank connectivity purely by being counted in two places.

The score is read from the GDS and the tool output — never by running the
model's module. `ledger.py` calls the scorer in-process, and one `os._exit(0)`
in a generator would otherwise take the run's own history down with it.

---

## What the model is shown

The packet is assembled host-side from the raw artifacts. Under the curriculum
each rung carries only the blocks it declares:

| Block | Content | `build` | `gates` | `devices` | `taps` | `shorts` | `pins` | `nets` | `drc` |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| `[0]` | **the objective for this turn** | ● | ● | ● | ● | ● | ● | ● | ● |
| `[1]` | target netlist (the specification) | ● | ● | ● | ● | ● | ● | ● | ● |
| `[2]` | verdict, recomputed from raw output | ● | ● | ● | ● | ● | ● | ● | ● |
| `[3]` | Magic DRC, verbatim | | | | ● | | | | ● |
| `[4]` | KLayout DRC items | | | | ● | | | | ● |
| `[5]` | Netgen LVS digest | | | ● | | ● | ● | ● | |
| `[6]` | extracted netlist | | | | | ● | | ● | |
| `[7]` | layout digest (shapes, ports, crossings) | | ● | ● | ● | ● | ● | ● | |
| `[8]` | build traceback, when there is one | ● | ● | ● | ● | ● | ● | ● | ● |
| `[9]` | design rules from `sg13g2_tech` | | ● | ● | ● | | | | ● |
| `[10]` | API signatures, narrowed to this rung | ● | ● | ● | ● | ● | ● | ● | ● |
| `[11]` | a reference cell, as an example | | ● | ● | | | | | |

Roughly 7–20 KB per rung against ~40 KB for the old whole-cell packet.

Three rules govern the packet, and they outrank the size target:

- **Absence is never cleanliness.** Missing, empty, truncated and unparsable all
  read as `NOT AVAILABLE`.
- **Nothing is truncated silently.** Every cut states how many bytes it dropped,
  and the footer names every block that was shortened.
- **An example is given up before a measurement is cut.** Block `[11]` is the
  only block that is not evidence about this run, so when the packet is over
  budget it goes whole — and the packet says so.

The prompt generates its own cross-references: it only tells the model to read
block `[9]` when this rung actually carries block `[9]`. A reference the model
cannot resolve is not a cosmetic defect here — a run was lost to one.

---

## What is protected, and from what

The thing being graded can reach the grader: the model runs with `edit` and
`bash`, and its workspace is the repository.

- **`state.json` and every grader are snapshotted outside `$BUILD_DIR`** before
  the call and compared after it, from a trap, so an interrupted run cannot
  leave a forged verdict behind. `GUARD_GRADERS` includes the curriculum and the
  scorer: they decide which objective the model gets and which layout the run
  ships.
- **`context/` is moved aside** for the duration — 4 MB, ~794k tokens against a
  262k window. Moved, not `chmod 000`: an unreadable directory makes ripgrep
  *abort* rather than skip, which broke the model's file search and cost a run.
- **Exactly one line of the packet may start at column 0 with `RESULT:`**, and
  it is the one the packet itself computed. Every other candidate is indented.
- **The scorer never executes model-written code.** The evidence packet does, in
  a subprocess, under a wall-clock limit, with stdout and stderr captured
  separately.

This is a snapshot-and-compare, not isolation. A background process that
outlives the call defeats it. That matters against a deliberately adversarial
model, not against one trying to draw a cell.

---

## The two settings that decide whether the loop moves at all

Both were measured against the gateway, not guessed. See `SUMMARY.md`.

| | |
| --- | --- |
| `AION_GATE` (default `auto`) | One rung per turn. This is the one that matters: the whole cell needs >16k tokens of reasoning and never finishes; one rung needs ~3.2k and answers in 45 s. `off` restores the whole-cell objective and the whole packet, which is what a bisect needs to ask whether the curriculum is the difference. |
| `FIX_TIMEOUT` (default `12m`) | Sized to the hardest rung measured, not the easiest. Reasoning scales with the rung — `gates` reasons 13k characters, `shorts` 45k — and through `copilot` the token cap is effectively unlimited, so wall clock is the real limit. |
| `MODEL_EFFORT` (default `low`) | Passed to the CLI. Measured to be a **no-op for Kimi** on this gateway (`default`, `low` and `minimal` all behave identically); kept because it matters for the other models. |
