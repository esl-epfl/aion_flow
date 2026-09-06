# AION Layout — AI Flow Improvement Plan

**Status:** proposal, for review
**Scope:** the agentic harness only (`orchestrate.sh`, `pipeline.sh`, prompt, skill, feedback
plumbing, verification parsers, context selection). **No cell layout is designed here.** Kimi
remains the only agent that draws the cell.
**Target run:** `make clean flow` → `./orchestrate.sh AION_inv_nand2_nor2_1_minimized.spice build 10`
**Model:** `moonshotai/Kimi-K2.7-Code`, 262,144-token window (`copilot-rcp.sh:27`)

---

## 1. Executive summary

The loop has never converged, and the evidence says the dominant cause is **not model capability**.
The harness computes roughly 13 KB of exact ground truth every iteration, injects **two lines** of
it into the prompt, and withholds the SPICE netlist that defines the correct answer.

Measured against the real artifacts in `build/layout/iteration_0/`, this is the *complete*
diagnostic payload Kimi receives at `orchestrate.sh:153`:

```
RESULT:    FAIL
---
```

Everything else — 8 Magic DRC violations with coordinates, the netgen pin table showing `I1` and
`I2` shorted onto node `a_155_82#`, device counts `layout=3 schematic=4` — is written to disk and
then discarded by two greps that cannot match.

Three compounding facts:

1. **The netlist is never in the prompt.** `orchestrate.sh:118` orders the model to implement
   "topology implied by the SPICE netlist"; the file is never inlined, never `@`-referenced, and
   its path is never named. Kimi cannot know there are 8 devices, or that `I1_bar` is an internal
   net needing a 4th gate.
2. **DRC can never fail the gate.** `verification.py:260-266` requires four `float()`-parseable
   tokens; Magic writes `0.240um`. The `except ValueError: continue` swallows every violation, so
   `report.txt` printed `Magic : PASS` over 8 real latch-up violations.
3. **The API cannot express the fix.** The only DRC violations are `LU.a`/`LU.b`, which require
   well/substrate tap rows. The words *tap*, *tie*, *latch-up* appear **zero times** across
   `building_blocks.py`, `GDS_PYTHON_API.md`, `CLI_REFERENCE.md` and `SKILL.md`.

A useful way to hold it: today the loop asks the model to fix a circuit it cannot see, using a
report it is not shown, against a rule it has no vocabulary for, and grades it with a check that
cannot fail.

---

## 2. The context-budget principle: replace *pull* with *push*

Your restriction — "don't let Kimi read files, it drowns and has no room left to lay out" — was
**correct, and this plan keeps it**. The measurements justify it completely:

| What the prompt currently points Kimi at | Size |
|---|---:|
| `@context` (221 files) | **~794,000 tok — 3× its entire window** |
| ├─ `context/drc/` (54 files) | ~413,000 tok |
| ├─ `context/py/` (83 files) | ~332,000 tok |
| └─ `context/spice/` (84 files) | ~50,000 tok |
| `SKILL.md`, auto-injected via `--add-dir` | ~6,700 tok |

| What Kimi actually needs, and is denied | Size |
|---|---:|
| The SPICE netlist it must match | 161 tok |
| Magic DRC report, all 8 violations + coordinates | 178 tok |
| Netgen pin/device mismatch digest (parsed) | ~300 tok |
| Extracted vs. schematic netlist pair | 383 tok |
| **One** host-selected reference cell | ~1,700 tok |
| **Total actionable packet** | **≈ 3,300 tok — 1.3% of the window** |

So the flow hands Kimi a haystack three times larger than its context window, forbids it from
reading anything *else*, and the needle it is missing costs 1.3%.

**The fix is not to lift the ban. It is to change who does the selecting.**

> Host-side selection is free, deterministic, repeatable and cannot blow the window.
> Model-side selection costs context to discover it picked wrong.

Every `@directory` reference becomes a bounded, host-computed, inlined block with a hard byte cap.
The prompt keeps a *read-scope* rule, but it changes from *"read nothing"* (which starves it) to
*"everything you need is already inlined below; do not go looking for more"* (which protects it).

Projected budget after this plan:

| | Today | After |
|---|---:|---:|
| Total prompt | ~9,300 tok | ~4,800 tok |
| …of which is **evidence** | **~10 tok** | **~3,300 tok** |
| Fraction of Kimi's window | 3.5% | 1.8% |

**Half the context, ~300× the evidence.**

---

## 3. What the evidence actually says (verified on disk)

| Finding | Where | Consequence |
|---|---|---|
| `report_summary` emits 2 lines | `pipeline.sh:142-149` vs `report_verification.py:175,182` print bare `DRC`/`LVS` with no colon; detail lines indented | Model is blind |
| Netlist absent from prompt | `orchestrate.sh:64-186` | Model cannot know the target topology |
| `float('0.240um')` raises | `verification.py:260-266` | 8 violations parsed as `clean=True`; `Magic : PASS` |
| Netgen verdict unrecognised | `Final result: Top level cell failed pin matching.` matches neither regex | Falls through to "inconclusive"; correct by accident |
| No tap primitive | `building_blocks.py` | `LU.a`/`LU.b` inexpressible in-API |
| Scaffold stubs self-short | `I1` bar `1295..1585 × 1390..1820` overlaps `O0` stub `1310..1570 × 1330..2060` | This *is* netgen's `I1`,`I2` → `a_155_82#` short |
| Scaffold gates external inputs only | `auto_scaffold` via `suggest_gate_order` → `input_nets` | `I1_bar` ungated → 3 devices vs 4 |
| Prompt teaches broken commands | `orchestrate.sh:169,172` use `-b`, which `pipeline.sh:99-101` documents as broken for this PDK | Model's inner loop grades itself with a tool that writes no report |
| `py_compile` is the wrong gate | `orchestrate.sh:223` | Runtime errors pass, then kill the run one pass later at `pipeline.sh:76` |
| `SKILL.md` is a competing architecture | injected as trusted config; `SKILL.md:122,124,395` tell the agent to write `state.json` and set `status: verified_clean` | Model has `edit` + `--add-dir $BUILD_DIR`; **the PASS verdict is forgeable** |
| No progress metric, no rollback | `orchestrate.sh:276` advances unconditionally | Unfiltered random walk, regressions permanent |
| `memory.md` is 0 bytes | write is mandated as the *last* action inside a hard 10 m kill | Continuity fails exactly when it is needed |
| No recorded convergence, ever | `git show e92fb33^:tools/aion_layout/typescript` — 5 iterations → `MAX ITERATIONS REACHED` | — |

---

## 4. Staged plan

Ordered by leverage ÷ risk. **Every stage is validatable without a full LLM run**, using the
existing `build/layout/iteration_0/` artifacts as fixtures.

### Stage 0 — Stop the information leaks *(the whole thesis; ~40 lines net)*

| File | Change |
|---|---|
| `pipeline.sh` | Rewrite `report_summary()` (142-149). Strip ANSI, then emit four labelled fenced blocks: **VERDICT** (from `report.txt`), **MAGIC DRC** (`cat` the `.rpt` verbatim — it is 641 B), **NETGEN DIGEST** (parsed: verdict line, device-count table, `disconnected node:` list, unmatched-pin groups), **EXTRACTED vs SCHEMATIC** (`.ext.spc` + `.sch.spc`, 383 tok). Hard-cap each block. |
| `orchestrate.sh` | Insert the target netlist as the **first** evidence block: the `.subckt` verbatim plus a host-computed device/net table (from the *existing* `spice_parser` + `netlist_view`) — per-device type/W/L/gate/drain/source, and the port-vs-internal net split. |
| `orchestrate.sh` | Restate the read-scope rule as *scoped*, not *forbidding*: "Everything you need is inlined below. Do not open other files; you will run out of context before you finish the layout." Keeps your defence, removes the starvation. |

**Validation:** run the new `report_summary` against the committed `iteration_0` artifacts and diff
the output. Assert it contains `LU.a`, `LU.b`, `a_155_82#`, `layout=3 schematic=4`. Zero LLM calls.

### Stage 1 — Make the gate honest *(do this before any run, or a SUCCESS banner is meaningless)*

| File | Change |
|---|---|
| `verification.py` | Strip unit suffixes before `float()`. Then **fail loudly**: parse `[INFO] COUNT: N` and raise `VerificationError` if `N > 0` but zero violations were recovered — a parser that goes blind must never report clean. |
| `verification.py` | Anchor the netgen verdict on the **last** `Final result:` line and classify the full vocabulary, including `failed pin matching`. |
| `orchestrate.sh` | Replace `py_compile` (223) with a real build gate: import → `generate(CELL, sg13g2_tech)` → `write_gds` to temp. On failure, feed the **traceback verbatim** into the next prompt instead of `exit 1`. |
| `orchestrate.sh` | Make the verdict non-forgeable: `cp state.json state.json.pre` before the model call, restore after. (Two lines. Closes the `verified_clean` forgery path.) |
| `orchestrate.sh` | Replace the finalize block (289-296) with copies of what the loop already produced — deletes 3 docker calls, both broken greps and the `-b` re-verification. |

**Validation:** golden test asserting `not clean`, 8 violations, `{LU.a:4, LU.b:4}`,
verdict `failed_pin_matching`, devices `{nmos:(3,4), pmos:(3,4)}` against the fixtures.

### Stage 2 — Give the model an oracle it can actually use in-turn

The prompt already invites 5 inner rounds and grants a 10-minute budget — but hands it the **broken
`-b` commands**. So its self-checks are graded by a tool that writes no report, and silence reads as
success.

| File | Change |
|---|---|
| `pipeline.sh` | Refactor each step into a path-parameterised `_at` variant (`step_drc_at <gds> <dir>` …); the state-driven versions become 3-line wrappers. Makes host/model oracle drift *structurally impossible*. |
| `scripts/selfcheck.sh` *(new)* | The single command the prompt exposes. Sources `pipeline.sh`, runs the identical build→DRC→LVS→score chain, prints the same verdict block. Writes a `DEADLINE` epoch file so it can print remaining budget. |
| `orchestrate.sh` | Delete the three raw `sak-*` recipes (166-172), the malformed `@context:drc:` (159), and the ~50 lines duplicating `SKILL.md`'s taxonomies. Replace with one line pointing at `selfcheck.sh`. |
| `Makefile` | Fix `drc`/`lvs` targets' stale `-b`/`-l macro` → `-d -m`/`-d`. |

This converts each 10-minute call from **one blind edit** into **~5 measured edits**. Largest single
gain per hour of work after Stage 0.

**Validation:** run `selfcheck.sh` on `iteration_0/*.py` and confirm it reproduces the known verdict.

### Stage 3 — Curated few-shot, and the missing vocabulary

| File | Change |
|---|---|
| `scripts/pick_reference_cells.py` *(new, ~50 lines)* | Host-side selection. Parse the target and all 83 `context/spice/*.spice` with the existing parser; rank on `(n_nmos, n_pmos, n_ports, n_internal_nets, pun_depth, pdn_depth)`. Inline the top-1 `context/py/*.py` verbatim (~1,700 tok, capped). One design agent verified this ranker uniquely selects **`sg13g2_or3_1`** — exact match on all six features. |
| `building_blocks.py` | Add generic `draw_tap(rect, tap_type, net, tech)` beside `draw_contact`: Activ + correct implant + Cont array at rule pitch + Metal1 landing + label. **See §5 — I want your ruling before touching this.** |
| `GDS_PYTHON_API.md` | Machine-generate the rule table from `sg13g2_tech` (a `scripts/dump_rules.py` writing between markers) so it cannot drift: all enclosures, `tech.grid.tracks_y_nm`, site width, cell height, rail convention. Today the doc names enclosure keys with **no values**, so every coordinate is guesswork. |

### Stage 4 — Turn the random walk into a climb

| File | Change |
|---|---|
| `scripts/score_iteration.py` *(new)* | Objective function from raw artifacts only: DRC count by rule, LVS verdict, device deltas, unmatched nets/pins, disconnected nodes. Every input already sits on disk. |
| `orchestrate.sh` | Accept/reject on score. Keep `best`. On regression, branch from `best` rather than advancing. Reject byte-identical resubmissions. |
| `orchestrate.sh` | Host-written `ledger.md`: one record per iteration (stage, score vector, deltas, verdict). Inline the last 3 in each prompt. Replaces the 0-byte model-written `memory.md` as the continuity mechanism. |

### Stage 5 — Optional: stage curriculum

Split the monolithic "fix everything" objective into gated sub-goals
(`build → devices → taps → pins → nets → LVS → DRC`), one narrow objective per call. Highest
ceiling, largest change. **Recommend deferring until Stages 0–2 have produced one measured run** —
we should see how far Kimi gets once it can actually see the problem before restructuring the loop
around it.

---

## 5. Decisions I need from you

1. **`draw_tap` — does this cross your line?** It is generic, reusable API infrastructure (a sibling
   of the existing `draw_contact`), not this cell's geometry. But it is the one item where I'd be
   adding layout-domain capability rather than pure plumbing. My read: it is legitimate and
   necessary — the model cannot descend a gradient whose step doesn't exist in its action space.
   **Your call.**
2. **Is Kimi-K2.7-Code vision-capable?** `orchestrate.sh:150` attaches the PNG and `SKILL.md`
   mandates visual inspection in three places. If it's text-only, that channel is dead and should be
   replaced by a text digest (shape inventory + label list + poly/active crossing table). The render
   is near-unusable regardless — alpha 60/255 on pure black, and `gds_to_image.py` silently drops
   every `TextShape`, so all pin labels are invisible.
3. **Split `SKILL.md`?** It is injected as trusted config and describes a *competing* architecture
   (Mode A: agent runs the whole loop and sets `status: verified_clean`), directly contradicting the
   prompt's "write one file and stop". Proposal: ship a `fix-cell` skill with domain guidance only,
   and keep the orchestration/state-machine text out of the per-iteration injection.
4. **Fix the scaffold, or leave it?** It manufactures two of the failures (self-overlapping stubs →
   the `I1`/`I2` short; external-inputs-only gating → 3 devices vs 4). Fixing it is harness work, but
   arguably makes the model's job easier in a way you may want to keep honest. My recommendation:
   fix the *self-short* (a bug), keep the sparseness (a legitimate starting point).
5. **Scope for the first iteration of work:** Stages 0–2 only, then measure? Or straight through
   Stage 4?

---

## 6. Explicitly NOT doing *(constraint audit)*

- Not writing or hand-fixing the cell layout.
- Not hardcoding this cell's geometry, coordinates, device placement or routing anywhere.
- Not precomputing the answer and feeding it to Kimi.
- Not replacing the Kimi fix step with Claude or any other agent.
- Not relaxing the acceptance gate to let a failing layout pass.
- The reference cell inlined in Stage 3 is **selected** by a structural netlist metric, never
  authored — and it is a *different* cell than the target, shown as an example of the API and of
  tap/implant conventions, not as an answer.
- The netlist inlined in Stage 0 is the flow's own **input**, which the prompt already orders the
  model to match. Supplying it removes a prohibition; it does not supply a solution.

---

## 7. How we will know it worked

Short of a full run, per stage:

- **Stage 0:** the assembled prompt, dumped to a file, contains `LU.a`, `LU.b`, `a_155_82#`,
  `layout=3 schematic=4`, and the `.subckt` — and totals under 6,000 tokens.
- **Stage 1:** golden test on the fixtures fails `clean`, reports 8 violations, and classifies the
  netgen verdict correctly.
- **Stage 2:** `selfcheck.sh` on a known-bad module reproduces the host's verdict exactly.
- **Stage 3:** the ranker selects `sg13g2_or3_1` for this target, and the inlined example is under
  the byte cap.

Then one real `make clean flow`, with these as the observable signals:

| Signal | Today | Target |
|---|---|---|
| Devices extracted | 3 / 4 | 4 / 4 |
| `LU.a` + `LU.b` violations | 8 (misreported as PASS) | 0 |
| Shorted pin groups | 2 | 0 |
| Iterations before device count matches | never | ≤ 2 |
| Run reaches `finalize` | never | yes |

The honest framing for the first run: the goal is **not** guaranteed DRC/LVS-clean silicon. It is to
find out what Kimi does when it can see the problem, has a working self-check, and is graded by a
gate that can actually fail. Everything above is the harness earning the right to attribute the next
failure to the model.
