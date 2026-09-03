# Stage 5 — Curriculum: making the loop converge

**Status:** plan, ready to build
**Prerequisite:** Stages 0–4 are done and tested (203 tests, `make test`)
**Target:** `./orchestrate.sh <netlist> build 10` produces a module the model
actually writes, for **any** standard cell — not just the one under test.

---

## 1. Why the first approach did not work

The harness was rebuilt over three rounds and it works. The loop still never
converged, and the reason is not the harness. It is that **the objective given
to the model in one turn is not answerable in one turn.**

### What was wrong at the start (fixed)

The original loop was blind and its gate could not fail:

| Defect | Evidence |
|---|---|
| The model was shown almost nothing | `report_summary()` greps matched nothing; the entire injected payload was three characters: `---` |
| `report.txt` carried no verdict | `report_verification.py` hunted a `*_full.lyrdb` the KLayout `macro` run does not always write, raised `FileNotFoundError` after printing only its header, leaving 918 bytes with no `DRC:`/`LVS:`/`RESULT:` |
| That failure was silent | the pipeline ran under `if ! run_deterministic_steps...`, and POSIX shells suppress `set -e` for the whole command *including inside called functions*, so `step_report` ignored a non-zero runner and marked itself done |
| DRC could not fail the gate | `float()` on `0.240um` raised `ValueError`, swallowed; 8 real violations parsed as clean |
| The netlist was never in the prompt | the model was told to match a SPICE file it was never shown |

All of that is fixed and pinned by tests. The packet now delivers ~9.5k tokens
of exact ground truth per iteration.

### What is actually blocking convergence (measured)

Once the model could *see* the problem, it stopped hunting for information and
started reasoning about the layout — and never stopped. Measured directly
against the gateway, no agent CLI involved:

```
Kimi-K2.7-Code, the full 38 KB packet:
  max_tokens=256     6s    reasoning=(all)      content=0
  max_tokens=4000    66s   reasoning=16,945 ch  content=0
  max_tokens=16000   289s  reasoning=64,167 ch  content=0     finish=length

Kimi-K2.7-Code, one narrow objective ("place four poly gates at x=..."):
  max_tokens=4000    10s   reasoning=1,293 ch   content=387   finish=stop  ✓

Qwen3.5-397B-A17B, the same full 38 KB packet:
  max_tokens=4000    69s   reasoning=11,235 ch  content=0     finish=length
```

**Both models fail on the whole-cell objective. Kimi answers a narrow one in
ten seconds.** More completion budget buys more reasoning, not output, so
raising `FIX_TIMEOUT` does not help: at ~55 tok/s, thirty minutes is ~99k
tokens of thinking and nothing suggests content appears at any budget.

The uncomfortable part: blocks `[9]`/`[10]`/`[11]` did exactly what they were
designed to do — the model stopped browsing `context/` and stopped hunting for
`building_blocks.py` — and throughput got *worse*, because the recovered budget
went into reasoning about a problem that is too large to answer at once. Tool
calls went 90 → 6 → 0 as the packet got richer. Better evidence cannot rescue
an unanswerable objective.

### Two things that are not the cause (ruled out by measurement)

- **The gateway and the key.** HTTP 200 in 1s for a small prompt, 6s for the
  full 38 KB one (12,626 prompt tokens accepted).
- **The agent CLI.** copilot is slow (~100s/tool call) but does drive the model.
  **opencode is separately broken on this machine**: every invocation hangs at
  `message=init`, before any connection is opened. Identical with a 500-byte
  prompt and a 38 KB one, with the 2.35 GB session DB and a fresh
  `XDG_DATA_HOME`, with `--pure`, and with both the original and patched
  wrapper. That is an upstream bug, not something the harness can route around.
  `AGENT_CLI=opencode` remains wired for when it is fixed; the default is
  `copilot`.

---

## 2. What to read first

Read in this order. Everything below is current as of this plan.

**Start here**
1. `README.md` — architecture, the evidence packet, the two standing
   invariants, known trade-offs. The entry point.
2. `ORCHESTRATION.md` — the harness in depth: `state.json`, every pipeline
   step, the model call, the build gate, finalisation.
3. `FLOW_IMPROVEMENT_PLAN.md` §4 Stage 5 — the original sketch this plan
   replaces. Note its Stages 3 and 4 are now **built**, not pending.

**The code you will change**
4. `orchestrate.sh` — `build_fix_prompt()` (prompt assembly), `request_fix()`,
   `request_fix_and_build()`, the main loop. This is where Stage 5 lands.
   Read the header comment first: it states the two invariants everything
   else follows from.
5. `scripts/evidence.py` — the packet builder. Blocks are `block_*` functions
   assembled in `build_blocks()`; `BLOCK_CAPS` and `TRIM_ORDER` govern the
   byte budget. You will add a per-gate objective block and trim the rest.

**The machinery Stage 5 needs, already built and tested**
6. `scripts/score_iteration.py` — the objective function. **Every gate exit
   criterion below is already a field on `Score`.** Read `Score` and the
   weight constants.
7. `scripts/ledger.py` — host-written per-iteration record, survives a
   timeout, detects a stuck score. `render()` produces the prompt digest.
8. `scripts/pick_reference_cells.py` — Stage 3's ranker. Structural
   fingerprint + weighted distance over the 83-cell PDK corpus.

**Reference, skim**
9. `aion_layout/spice_parser.py` and `netlist_view.py` — the netlist model the
   curriculum must be derived from. `Subckt.pins`, `.nets`, `.nmos_devices`,
   `.pmos_devices`, `.output_net`, `.input_nets`.
10. `aion_layout/building_blocks.py` — the drawing API the model calls.
11. `SKILL.md`, `GDS_PYTHON_API.md` — domain guidance and API reference, both
    named to the model in the prompt.
12. `tests/` — 203 tests. `test_stage3_stage4.py` covers the scorer, ledger and
    ranker; `test_shell_surface.py` asserts what the prompt must and must not
    contain.

**Verify your environment before changing anything**

```bash
make test                                             # 203 passed
AION_DUMP_PROMPT=/tmp/p.txt ./orchestrate.sh AION_inv_nand2_nor2_1_minimized.spice build 2
./orchestrate.sh AION_inv_nand2_nor2_1_minimized.spice build 1   # deterministic chain, no model
```

---

## 3. The design: a general curriculum, not a script for one cell

**Hard requirement: nothing in the curriculum may be specific to
`AION_inv_nand2_nor2_1`.** The user will generate other cells. Every gate's
objective, its geometry hints and its exit criterion must be *derived from the
parsed netlist and the measured artifacts*, never hardcoded.

The existing scope guard (`tests/test_scope_guards.py`) already fails the build
if cell-specific geometry leaks into model-visible files. Extend it to cover the
curriculum.

### The gates

Each gate is one narrow objective per model call. Exit criteria come straight
from `Score`, so the curriculum and the grader cannot disagree.

| # | Gate | Objective, derived from | Passes when |
|---|---|---|---|
| 1 | `build` | — | module imports and `generate()` writes a GDS |
| 2 | `gates` | `{d.gate for d in subckt.devices}` | poly/active crossings == `len(devices)` |
| 3 | `devices` | `subckt.nmos_devices`, `pmos_devices`, W/L per device | `score.device_delta == 0` |
| 4 | `taps` | rails from `subckt.vdd_net`/`vss_net` | no `LU.a`/`LU.b` in `score.drc_by_rule` |
| 5 | `pins` | `subckt.pins` | `score.disconnected == 0` and `unmatched_pins == 0` |
| 6 | `nets` | `subckt` fanout table | `score.lvs_verdict == "match_uniquely"` |
| 7 | `drc` | measured violations | `score.drc_violations == 0` |

Gate 2 is deliberately first after build: it is the smallest objective that
moves a real metric, and it is the one Kimi answered in 10 seconds.

### Prompt manager

New module, `scripts/curriculum.py`:

```python
def gates(subckt: Subckt) -> list[Gate]                # derive the ladder for ANY cell
def current_gate(subckt: Subckt, score: Score) -> Gate # first gate whose exit test fails
def objective_block(gate: Gate, subckt: Subckt, score: Score) -> str
```

- `Gate` carries `key`, `title`, `objective` (text built from the netlist),
  `exit_test(Score) -> bool`, and `blocks` — which evidence blocks are relevant.
- `current_gate` walks the ladder and returns the **first failing** gate. That
  makes progress monotonic and automatically resumes at the right place after a
  regression, with no state to keep.
- A cell with no PMOS, no internal nets, or a single input must produce a valid
  (shorter) ladder. Test with synthetic 1–6 input netlists, as
  `test_auto_scaffold.py` already does.

### Prompt shrinks per gate

The packet is currently ~38 KB / 9.5k tokens and that is part of the problem.
Per gate, include only what the gate needs:

- **always**: block `[1]` target netlist, block `[2]` verdict, the new
  objective block, the current source
- **gate 2–3**: block `[7]` layout digest (crossings, shapes), block `[9]` rules
- **gate 4**: block `[3]`/`[4]` DRC, block `[9]` rules, `draw_tap` docs
- **gate 5–6**: block `[5]` netgen digest, block `[6]` extracted netlist
- **gate 7**: block `[3]`/`[4]` DRC only
- **block `[11]` reference cell**: gate 2–3 only, then drop it

Target **under 4,000 tokens per call**. Put `DEFAULT_MAX_BYTES` back to
`24_000` or lower (it was raised to `40_000` to fit block `[11]`; that was sized
to the context window, but the real constraint is reasoning time per turn).

### Loop changes in `orchestrate.sh`

1. After grading, compute `Score` and append to the ledger with the gate name.
2. Pick the current gate; assemble the prompt for that gate only.
3. Accept/reject on score: keep `best`, and on regression branch from `best`
   rather than advancing. (This is the rest of Stage 4, still unwired.)
4. Advance the gate only when its exit test passes; record gate transitions in
   the ledger so a stuck gate is visible.
5. Set `FIX_TIMEOUT` default from measurement — `10m` is known wrong. With a
   narrow objective a call should take well under a minute; keep a margin.

---

## 4. Validation, in order

1. `make test` still green, plus new tests for `curriculum.py`:
   gate ladder derived for 1–6 input synthetic netlists; `current_gate` returns
   the first failing gate; no cell name or coordinate literal appears in any
   generated objective.
2. `AION_DUMP_PROMPT` per gate: assert each is under the token target and
   contains only the blocks that gate declares.
3. **One model call at gate 2** — the cheapest possible real test, and the one
   the measurement says should succeed in seconds. If it does not write a
   module, stop and re-measure before building further.
4. Then the full loop, `MAX_ITERATIONS=10`.

---

## 5. Cautions learned the hard way

- **Do not edit a file in `GUARD_GRADERS` while a run is in flight.** The
  tamper guard restores it and records the event. That list is in
  `orchestrate.sh`; it includes `orchestrate.sh`, `pipeline.sh`,
  `evidence.py`, `verification.py`, `report_verification.py`, `selfcheck.sh`.
- **Never `pkill -f <pattern>` when your own command line contains the
  pattern.** It matches your shell and kills it. Use explicit PIDs. (Cost two
  shells during the last session.)
- **Kill runs with `SIGTERM`, not `-9`** — the EXIT/INT/TERM trap restores
  `context/` and `state.json`. Verified working.
- `context/` is moved aside (not `chmod`ed) during a model call. `chmod 000`
  makes ripgrep *abort* rather than skip, which broke the model's file search
  and cost a whole run.
- The scaffold starts with 4 `M1.d` minimum-area violations by design; see the
  comment in `aion_layout/auto_scaffold.py`. Do not "fix" it by shrinking
  stubs — that reintroduces the I1/O0 self-short.
- Fixtures in `tests/fixtures/` are read-only and survive `make clean`.

---

## 6. If Stage 5 does not make it converge

Fall back in this order, measuring each:

1. **Shrink further** — one gate may still be too much; split gate 3 per device.
2. **Try `openai/gpt-oss-120b`** — the third model on the gateway, untested on
   this task. `MODEL=` selects it; no code change.
3. **Few-shot the gate** — block `[11]` currently shows a whole reference cell;
   show only the part of it that implements the current gate.
4. **Reconsider the premise** — if no model on this gateway will write a
   standard-cell layout, the loop's value is the harness and the evidence, and
   the honest deliverable is a measurement of what these models cannot do.
