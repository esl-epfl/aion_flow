# AION Layout

Technology-aware standard-cell layout tooling for the IHP SG13G2 PDK, plus a
closed-loop harness that drives a language model to draw a cell from a SPICE
netlist and grades the result with real DRC and LVS.

There are two ways to use this repository, and they are independent:

| | |
|---|---|
| **A Python layout toolkit** | Write a cell generator by hand, build a GDS, run DRC/LVS, get a report. Nothing here needs a model. |
| **A closed-loop flow** | `./orchestrate.sh` scaffolds a starting cell from the netlist, verifies it, hands the model the evidence, takes back a rewritten generator, and repeats until DRC and LVS pass or the iteration budget runs out. |

The model draws the cell. The harness never does — it scaffolds, measures,
reports and grades. That separation is deliberate and is enforced by tests.

---

## Quick start — the flow

```bash
make flow          # ./orchestrate.sh AION_inv_nand2_nor2_1_minimized.spice build 10
```

Requires: the `iic-osic-tools_shell_uid_1000` Docker container running, `jq`,
`python3` with `klayout`, the `copilot` CLI, and `CEFPROVIDER_API_KEY` set.

**Look before you leap.** Two forms cost nothing and call no model:

```bash
# Print the exact prompt the model will receive, then exit.
AION_DUMP_PROMPT=/tmp/prompt.txt ./orchestrate.sh AION_inv_nand2_nor2_1_minimized.spice build 2

# Run the deterministic chain only — scaffold, GDS, render, DRC, LVS, report.
./orchestrate.sh AION_inv_nand2_nor2_1_minimized.spice build 1
```

`MAX_ITERATIONS=1` stops before the first model call, because the loop breaks
when `iteration + 1 >= MAX_ITERATIONS`. Use `2` for exactly one model call —
enough to learn whether the model uses the netlist it can now see, and whether
it addresses all four gate nets instead of three.

---

## What one iteration does

```
                 ┌──────────────────────── deterministic, no model ────────────────────────┐
  netlist ─────► scaffold ─► GDS ─► render ─► Magic+KLayout DRC ─► Magic+Netgen LVS ─► report.txt
                                                       │                                    │
                                                       └────────────► evidence packet ◄─────┘
                                                                            │
                                            ┌───────────────────────────────┘
                                            ▼
                              prompt = evidence + current source
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │   the model     │  writes iteration_N+1/<cell>.py
                                   │  (one call)     │  may run ./scripts/selfcheck.sh
                                   └─────────────────┘
                                            │
                                            ▼
                                  host build gate: import,
                                  generate(), write_gds()
                                            │
                          builds ───────────┴─────────── fails: traceback goes
                             │                            into the next prompt
                             ▼
                    next iteration, or SUCCESS / MAX ITERATIONS
```

Everything left of the model call is plain bash and Python. There is nothing
for an agent to decide there and nothing that can loop.

---

## The evidence packet

This is the centre of the design. Each iteration the host computes ~31 KB of
exact ground truth from the raw artifacts and inlines the part the current
curriculum rung declares — **7–20 KB of evidence in a 12–27 KB prompt**,
depending on the rung. `AION_GATE=off` restores the whole packet (~24 KB).

Which blocks each rung carries is tabulated in **[FLOW.md](FLOW.md)**.

| Block | Contents |
|---|---|
| `[1]` | **Target netlist** — the `.subckt` verbatim, a device table (type, W, L, D/G/S/B), the port vs. internal net split, and per-net fanout |
| `[2]` | **Verdict** — DRC and LVS recomputed from the raw artifacts, *not* read back from `report.txt` |
| `[3]` | **Magic DRC report**, verbatim |
| `[4]` | **KLayout DRC items**, merged from every `*.lyrdb` |
| `[5]` | **Netgen LVS digest** — device counts, net counts, disconnected nodes, unmatched pins, mismatch fragments |
| `[6]` | **Extracted netlist** — what the tools actually see in the layout, so the model can diff it against `[1]` itself |
| `[7]` | **Layout digest** — per-layer shape inventory, every label and port, a cross-net overlap table, and a poly/active crossing table |
| `[8]` | **Build error** — the previous attempt's traceback, when there was one |
| `[9]` | **Design rules** — every numeric rule, generated from `sg13g2_tech`: widths, spacings, enclosures, cut sizes, the routing grid, the standard-cell frame |
| `[10]` | **API reference** — the callable surface, by introspection, narrowed to the calls this rung needs |
| `[11]` | **Reference cell** — a *different*, structurally similar PDK cell, as an API example. The only block that is not evidence about this run, and the first given up when the packet is over budget |
| `[0]` | **Objective** — the one rung this turn is graded on, derived from the netlist and the measured score. See [FLOW.md](FLOW.md) |

Block `[7]` replaces a rendered PNG. The model is text-only, so a picture was a
dead channel; a shape inventory with a cross-net overlap table is not. It is
what names a Metal1 short by coordinates, and what reports "6 crossings,
8 devices required by the netlist" when the layout is short two transistors.

### Why `context/` is locked during the model call

`context/` holds the PDK rule decks, 83 reference generators and 84 netlists —
about 4 MB, roughly 794k tokens against a 262k window. The prompt stopped
pointing at it, but the directory sits in the model's workspace and it has both
`view` and `bash`, so "do not go looking for more" was advisory text.

A measured run showed it ignored: **90 tool calls, zero writes**, 8 reads under
`context/drc/`, the entire 10-minute budget spent reconstructing design-rule
values by hand, and a timeout with no module produced. `GDS_PYTHON_API.md` named
the enclosure keys without their values, so every coordinate would have been a
guess.

Block `[9]` removed the reason to browse. `orchestrate.sh` also removes the
opportunity: `context/` is **moved aside** for the duration of the model call and restored by
`aion_cleanup`, which runs on a normal exit and on `INT`/`TERM`/`HUP` alike.
`chmod 000` was the first attempt and backfired: ripgrep, which the agent's file
search shells out to, *aborts* on an unreadable directory rather than skipping
it, so the model could not find `aion_layout/` at all. Nothing in the flow reads `context/`, so the pipeline cannot notice.

Build it standalone:

```bash
python3 scripts/evidence.py \
    --netlist tests/fixtures/AION_inv_nand2_nor2_1_minimized.spice \
    --iter-dir tests/fixtures/iteration_0 \
    --cell AION_inv_nand2_nor2_1 \
    --module tests/fixtures/iteration_0/AION_inv_nand2_nor2_1.py
```

---

## Why the harness looks like this

The loop previously never converged, and the cause was not model capability.

**The model was shown almost nothing.** `report_summary()` grepped `report.txt`
for `^(DRC|LVS|RESULT):`. Run against the real artifacts, both greps matched
nothing and the entire payload injected into the prompt was three characters:

```
---
```

**Because `report.txt` carried no verdict.** `report_verification.py` searched
for a `*_full.lyrdb` that the KLayout run at level `macro` does not always
write — it can write one database per rule table instead. It raised
`FileNotFoundError` after printing only its `Cell:/GDS:/Netlist:` header,
leaving a 918-byte file with no `DRC:`, no `LVS:` and no `RESULT:` line.

**And that failure was silent.** The pipeline was invoked as
`if ! run_deterministic_steps_for_current_iteration; then`. Under a `!`
negation, POSIX shells suppress `set -e` for the whole command *including inside
called functions*, so `step_report` ignored the runner's non-zero exit, checked
only that the output file existed — which the `>` redirection guarantees — and
marked itself done. It could not fail.

**Meanwhile the gate could not fail either.** The Magic coordinate parser called
`float()` on four whitespace-separated tokens, but Magic writes `0.240um`. Every
`ValueError` was swallowed, so a report listing 8 violations parsed as clean.

**And the netlist was never in the prompt.** The model was told to implement the
"topology implied by the SPICE netlist" while the file was never inlined, never
`@`-referenced, and its path never named.

Three rounds of adversarial verification then found the same bug class —
*silence reading as success* — alive in five more places, including a Magic
report with no `[INFO] COUNT:` trailer parsing clean, and deleting one KLayout
rule database silently removing a whole rule table from the verdict while the
headline still read `PASS`.

---

## The two standing invariants

Everything in the harness follows from these. They are stated at the top of
`orchestrate.sh` and enforced by tests.

**1. Fail closed.** A verdict, an artifact or an evidence packet that is absent,
empty, truncated, unparseable, incomplete, or merely not *positively confirmed*
clean is **not clean**. Only positive evidence of cleanliness counts.

In practice: a Magic report is clean only with an `[INFO] COUNT: 0` trailer; a
KLayout run is clean only when a receipt written by the DRC step proves every
database it produced was read; a missing report is an `ERROR`, never a pass.

**2. Nothing model-influenced becomes a verdict.** What lands in `state.json` is
read from the report the host wrote *before* the model was invoked, and
normalised to a fixed literal on the way in. Artifact discovery uses canonical
paths, never sort order. Exactly one line of the evidence packet may start at
column 0 with `RESULT:`, and it is the one the packet itself computed — every
other candidate is indented out of column 0.

---

## Verifying it yourself

```bash
make test          # 339 tests, no Docker, no model, ~8 s
```

The suite runs against committed fixtures in `tests/fixtures/`, captured from a
real failing run, so it survives `make clean`.

| File | Guards |
|---|---|
| `test_magic_drc.py` | unit-suffixed coordinates; `COUNT` cross-check; no-trailer reports are not clean |
| `test_klayout_drc.py` | multi-database merge; completeness receipts; empty directories |
| `test_netgen_lvs.py` | the full verdict vocabulary; last `Final result:` wins |
| `test_absence_is_not_clean.py` | the governing rule, across every artifact |
| `test_forged_pass.py` | planted reports, newline injection, verdict-line forgery |
| `test_evidence_packet.py` | every required substring, byte caps, budget enforcement |
| `test_evidence_integrity.py` | hard-exiting and stdout-printing generators; unit conversion |
| `test_report_verification_cli.py` | a `RESULT:` line on every path, including failure |
| `test_auto_scaffold.py` | no cross-net Metal1 overlap, 1–6 inputs |
| `test_draw_tap.py` | implants, cuts, enclosures, minimum sizes |
| `test_shell_surface.py` | `bash -n`; the prompt carries the evidence and none of the dead references |
| `test_scope_guards.py` | no cell-specific geometry leaked into model-visible docs |

Ground truth the fixtures pin, and that the parsers must keep reproducing:
Magic 8 violations (`LU.a` ×4, `LU.b` ×4, `COUNT: 8`); KLayout 1 item `LU.b`;
Netgen `failed_pin_matching`, `sg13_lv_nmos` and `sg13_lv_pmos` both
`layout=3 schematic=4`, devices `6|8`, nets `13|9`, disconnected nodes
`I0 I2 O0 VSS VDD`.

---

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `MODEL` | `moonshotai/Kimi-K2.7-Code` | Inference model id; see `copilot-rcp.sh --list` |
| `CEFPROVIDER_API_KEY` | — | Gateway key. Required for a real run |
| `FIX_TIMEOUT` | `12m` | Wall-clock budget for one model call |
| `MODEL_EFFORT` | `low` | Reasoning effort passed to the CLI. Measured to be a **no-op for Kimi** on this gateway; kept because it matters for the other models. See [SUMMARY.md](SUMMARY.md) |
| `AION_GATE` | `auto` | Curriculum rung: `auto` derives it from the score, a rung key forces one, `off` restores the whole-cell objective |
| `MAX_MODEL_CALLS` | `MAX_ITERATIONS` | Global model-call budget, build-gate retries included |
| `MAX_BUILD_FAILURES` | `3` | Build-gate retries inside one iteration, each spending from the global budget |
| `HOST_BUILD_TIMEOUT` | `300` | Seconds the host may spend running model-written code |
| `EVIDENCE_TIMEOUT` | `300` | Seconds the evidence packet may take, digest subprocess included |
| `MEMORY_INLINE_BYTES` | `4000` | Bytes of `memory.md` inlined into the prompt |
| `AION_DUMP_PROMPT` | — | Assemble the prompt, write it to this path, exit |
| `COPILOT_RCP` | `../../copilot-rcp.sh` | Path to the gateway wrapper |

The default is **Kimi**, configured at a 262k window in `copilot-rcp.sh`.
`Qwen/Qwen3.5-397B-A17B` is the other tested option, at 128k. A rung's prompt is
3–7k tokens, so both fit comfortably — prompt size has never been the binding
constraint. See [SUMMARY.md](SUMMARY.md) for what was.

### Make targets

| Target | Does |
|---|---|
| `flow` | The full closed loop |
| `gds` | Build a GDS from `CELL_MODULE` |
| `drc` / `lvs` / `verify` | Run the tools and print a summary |
| `selfcheck` | The same chain the host grades with, on one module |
| `netlist` | Scaffold a generator from a SPICE netlist |
| `doc` / `gds2py` | Documentation and GDS→Python conversion |
| `test` | The pytest suite |
| `clean` | Remove `build/` (fixtures and tests survive) |

---

## The model's self-check

The prompt exposes exactly one verification command:

```bash
./scripts/selfcheck.sh <MODULE.py> <WORKDIR> [<SPICE_NETLIST>]
```

It sources `pipeline.sh` and runs the identical build → DRC → LVS → report
chain the host uses to grade the result, printing the same verdict block. The
model may use it up to twice inside its budget: each round runs the real tools
and takes minutes, and a single rung is narrow enough that a second opinion on
it is rarely worth a whole round.

The work directory must sit outside the graded iteration tree — the guard
resolves symlinks and refuses paths that land inside it, because the host
assembles the next evidence packet from that tree and a self-check run there
would show up as a second, foreign set of results.

---

## Project structure

```text
aion_layout/
├── orchestrate.sh              # The loop: prompt, model call, build gate, state, finalise
├── pipeline.sh                 # Deterministic steps; `_at` variants take explicit paths
├── scripts/
│   ├── evidence.py             # The evidence packet builder
│   ├── selfcheck.sh            # The model's in-turn oracle
│   ├── report_verification.py  # The grader: always prints exactly one RESULT: line
│   ├── docker_run.sh           # Container wrapper for sak-drc.sh / sak-lvs.sh
│   ├── generate_cell.py        # Python generator → GDS
│   ├── generate_from_netlist.py, generate_cell_doc.py, gds_to_python.py, gds_to_image.py
├── aion_layout/                # Framework package
│   ├── tech.py                 # SG13G2 layers, design rules, grid, cell defaults
│   ├── primitives.py           # Point, Rect, transformations
│   ├── shapes.py               # Layer-aware shapes
│   ├── cell.py                 # Cell container and GDS writer
│   ├── building_blocks.py      # Diffusion, wells, poly, contacts, taps, wires, pins, rails
│   ├── verification.py         # DRC/LVS parsing; canonical discovery; completeness receipts
│   ├── spice_parser.py         # SPICE subckt parser
│   ├── netlist_view.py         # Topology helpers
│   ├── auto_scaffold.py        # Starter cell from a netlist — deliberately incomplete
│   ├── router.py, doc_generator.py, gds_to_python.py
├── cells/                      # Hand-written generators: template.py, sg13g2_nand2_1.py
├── tests/                      # 339 tests + committed fixtures from a real failing run
└── build/                      # Run output (gitignored)
```

### Run output

```text
build/
├── memory.md                       # Model-written continuity notes
└── layout/
    ├── state.json                  # Iteration, step flags, budgets, verdict
    ├── iteration_N/
    │   ├── <cell>.py, .gds, .png
    │   ├── drc/<cell>.magic.drc/   drc/<cell>.klayout.drc/   (+ klayout.receipt.json)
    │   ├── lvs/<cell>.magic.lvs/
    │   └── report.txt              # The graded verdict
    ├── selfcheck/iteration_N/      # The model's own runs, outside the graded tree
    └── final/                      # Copies of the last iteration + evidence.txt
```

---

## Writing a cell generator

A generator is a Python module exposing:

```python
def generate(name: str, tech: aion_layout.tech.Tech) -> aion_layout.cell.Cell:
    ...
```

Start from `cells/template.py`; `cells/sg13g2_nand2_1.py` is a complete example.
Standalone CLI use, none of which needs the flow:

```bash
python3 scripts/generate_cell.py cells/sg13g2_nand2_1.py out.gds
python3 scripts/generate_from_netlist.py netlist.spice -o cell.py
python3 scripts/gds_to_python.py cell.gds -o cell_from_gds.py
python3 scripts/report_verification.py --cell <name> --gds out.gds \
        --netlist netlist.spice --runs-dir runs --parse-only
```

`report_verification.py` exits **0** for `PASS`, **1** for `FAIL`, **2** for
`ERROR`, and prints exactly one `RESULT:` line on every path.

---

## Known trade-offs and open items

**The scaffold starts with 4 `M1.d` violations, deliberately.** Separating the
Metal1 bands to fix a self-short — the input bar and output stub overlapped for
any odd input count, merging two nets and silently costing a port — left each
stub about 275 nm tall, under the 0.09 µm² minimum-area rule. Satisfying both
rules needs a wider cell or different stub placement, i.e. a floorplan decision,
and the scaffold does not make floorplan decisions. A minimum-area violation is
reported with its rule name and coordinates and is fixed by enlarging one
rectangle; the overlap it replaced was invisible and unrecoverable. See the
comment in `aion_layout/auto_scaffold.py`.

**The scaffold gates external inputs only.** For the reference cell that means
3 poly gates against 4 gate nets — the internal node `I1_bar` is ungated. This
is a real gap the model is expected to read out of block `[1]` and close. It is
pinned by a test so nobody "helpfully" closes it in the scaffold.

**Grader isolation is not implemented.** The graders and `state.json` are
protected by a snapshot-and-compare taken around the model call. A background
process that outlives that call defeats it. The correct fix is to make the
graded inputs unreachable — run the graders from a copy outside `$BUILD_DIR` —
rather than compare them at two instants. This matters only against a
deliberately adversarial model, not against one trying to draw a cell.

**`state_reconcile` infers step completion from artifact shape**, not from a
receipt the step wrote, so a forged or stale artifact set can survive the resume
of an interrupted run. The KLayout completeness receipt already follows the
right pattern; the other steps do not yet.

**A stray `tools/aion_layout/context/` directory** may exist from a since-fixed
path bug that resolved one level too high inside the container. It is
gitignored and safe to delete.

---

## Current status

The harness is complete and verified (**368 tests**). Stage 5 — the curriculum —
is built: the loop asks for one rung of a netlist-derived ladder per turn, scores
every iteration, keeps the best, and branches from it on a regression.

**It now climbs, and then it stalls, and both halves are measured.**

A real 10-iteration run:

```
iter  rung      score   outcome
0     gates     6270    accepted
1     taps      4910    accepted                     (-1360)
2     gates     5990    REJECTED, branching from 1   (+1080)
3     shorts    4500    accepted                     (-1490)
```

The score improves, the ladder advances `gates → devices → taps → shorts`, and
iteration 2's regression was caught and rejected on its own. Before Stage 5,
every run in `build*/` reads `model_calls: 1`, `iteration_1/` empty, `blocked`.

It stops at the `shorts`/`pins` region, and the cause is not the prompt size, the
reasoning setting or the token budget:

| rung | the edit it asks for | reasoning | outcome |
| --- | --- | ---: | --- |
| `gates` | "add a fourth poly stripe on net `I1_bar`" — enumerable | 13,024 ch | **45 s** |
| `shorts` | "move shapes until no two nets touch, breaking nothing" — a search | 158,775 ch at a 40k budget | never answers |

A rung is answerable when the model can *name* the edit from the evidence, and
not when it has to *search* for one. That is the design rule a curriculum like
this needs, and it is the thing to act on next.

Read **[SUMMARY.md](SUMMARY.md)** before changing anything here — it has the full
measurement tables, a control that disproves the obvious explanation, and the
two fail-closed defects this work turned up.

- **[FLOW.md](FLOW.md)** — the loop, and what is mechanical vs. what the model does
- **[SUMMARY.md](SUMMARY.md)** — what was measured about Kimi and the flow, good and bad
- **[NEW_PLAN.md](NEW_PLAN.md)** — the Stage 5 design this implements
