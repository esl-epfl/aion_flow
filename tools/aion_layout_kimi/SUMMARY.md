# What I learned about Kimi and about this flow

Measured 2026-09-03/04 against `https://inference.rcp.epfl.ch/v1`, model
`moonshotai/Kimi-K2.7-Code`, while implementing Stage 5 (`NEW_PLAN.md`).

Every number below is from a request I made, not from a doc. Where a claim is
inferred rather than measured, it says so.

---

## 1. The headline: it is the completion budget, and the curriculum is what fits inside it

`NEW_PLAN.md` diagnosed the objective — a whole cell is not answerable in one
turn — and it was right. What it could not see is *why* the failure looks the way
it does, and the answer changes what you reach for when a rung stops working.

| objective | effort | budget | wall clock | reasoning | content | finish |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| whole cell, 39 KB | default | 4k | 66 s | 16,945 ch | **0** | length |
| whole cell, 39 KB | default | 16k | 289 s | 64,167 ch | **0** | length |
| whole cell, 39 KB | `low` | 16k | 239 s | 64,005 ch | **0** | length |
| one rung (`gates`), 11 KB | default | 4k | 55 s | 15,405 ch | **0** | length |
| one rung (`gates`), 11 KB | `low` | 8k | 123 s | 24,684 ch | 2,933 ch | stop |
| **one rung (`gates`), 11 KB** | **default** | **8k** | **45 s** | 13,024 ch | **2,600 ch** | **stop** |
| one rung (`shorts`), 29 KB | `low` | 12k | 132 s | 44,653 ch | **0** | length |
| one rung (`shorts`), 29 KB | `minimal` | 12k | 132 s | 47,203 ch | **0** | length |

### Correcting myself: `reasoning_effort` was a red herring

I spent a while convinced that `--reasoning-effort low` was the fix, and wrote it
into the code. **The last-but-two row is the control that disproves it**: the same
prompt, the same 8k budget, at the *default* effort, returns a clean module in
45 s. `low` did nothing.

On this gateway Kimi treats `default`, `low` and `minimal` identically — a
34-token prompt returns exactly 121 characters of reasoning at all three, and the
`shorts` rung reasons *more* at `minimal` (47,203 ch) than at `low` (44,653 ch).
Only `none` actually suppresses reasoning, and it is a trap of its own (below).

**The variable that mattered was the completion budget.** Rows 4 and 6 are the
same prompt at the same effort; 4000 tokens is spent before the reasoning ends,
8000 is not.

### What that means, and why the curriculum is still the fix

Reasoning length scales with how hard the objective is, and it is not
negotiable — you cannot ask this model to think less. So the only lever is to
make the question smaller:

```
whole cell   > 16,000 tokens of reasoning  -> never finishes, at any budget tried
gates  rung  ~  3,200 tokens               -> answers in 45 s
shorts rung  ~ 11,000 tokens               -> needs > 12,000, still tight
```

That is exactly what a curriculum does. It is not that the model "cannot do
layout" — it is that it will spend however much thinking the question demands,
and the question has to be small enough that the thinking finishes.

The practical consequence for the harness: through `copilot` the output cap is
262144 tokens, so the budget is effectively unlimited and **wall clock** is the
real limit. `FIX_TIMEOUT` is therefore sized to the *hardest* rung measured, not
the easiest.

### The `none` setting is a different trap

`reasoning_effort: "none"` does suppress reasoning — 25,105 characters of content
and none of reasoning. It is still wrong. The thinking does not go away, it moves
into the **content** channel:

> `We need answer with a complete corrected Python module. Need understand
> problem: Current layout has 3 poly gates crossing active…`

25 KB of thinking-out-loud with the module somewhere inside it, instead of a
clean ```python fence.

### It actually works

The working configuration, extracted and run by hand:

```
BUILD OK -> 1404 bytes
crossings: CrossingCount(count=8, reason='')
```

A module that builds, and that raises the poly/active crossing count from 6 to
8 — precisely the `gates` rung's exit criterion. **First try.**

And then through the real harness, `./orchestrate.sh … build.s5 2`, end to end:

```
Host verdict for iteration 0: RESULT: FAIL
score=6270  devices±2  nets±4  disc=6  pins=12  lvs=failed_pin_matching  drc=13  gates=6/8
Score for iteration 0: 6270.0  rung: gates  -> accepted

  REQUESTING FIX: ITERATION 0 -> 1
>> Prompt: 25918 bytes (~6479 tokens)
● Create AION_inv_nand2_nor2_1.py +70
>> Build gate passed.

Host verdict for iteration 1: RESULT: FAIL
score=5230  devices±0  nets±7  disc=7  pins=13  lvs=failed_pin_matching  drc=22  gates=8/8

  CURRICULUM: gates -> taps
```

193 s to write the module, 208 s for the whole turn. The score improved by 1040,
the crossing count reached 8/8, **the device delta went 2 → 0** (it cleared the
next rung as well), and the curriculum advanced on its own. No build failure, no
tamper event.

`memory.md` is also non-empty for the first time in this project's history —
because the module is now written before the note instead of after it.

### The full loop, 10 iterations

```
iter  rung      score   outcome
0     gates     6270    accepted
1     taps      4910    accepted                     (-1360)
2     gates     5990    REJECTED, branching from 1   (+1080)
3     pins      4500    accepted                     (-1490)
```

Four iterations, then a turn ran out of budget reading `GDS_PYTHON_API.md`.

What matters is the shape. The score climbs, the ladder advances
`gates → taps → pins`, and **iteration 2 fell back down to the `gates` rung, was
rejected, and the next call branched from iteration 1** — the regression handling
firing on its own, on a real regression, without being staged.

Before Stage 5, every run in `build*/` reads: `model_calls: 1`, `iteration_1/`
empty, `status: blocked`. Five times.

The turn that died was reading a documentation file the packet had already made
unnecessary. The prompt now says not to, and says why — that read has cost two
turns.

---

## 1b. Where it stops, and what actually makes a rung hard

The loop climbs and then stalls, and the stall is the most useful thing I
measured. It is **not** prompt size, **not** the reasoning setting, and **not**
the completion budget. The `shorts` rung, measured directly:

| budget | wall clock | reasoning | content |
| ---: | ---: | ---: | --- |
| 12k | 132 s | 44,653 ch | 0 |
| 12k (`minimal`) | 132 s | 47,203 ch | 0 |
| 16k (rewritten objective) | 177 s | 57,666 ch | 0 |
| **40k** | **450 s** | **158,775 ch** | **0** |

At 40,000 tokens it produced 158,775 characters of thinking and never wrote a
line. The reasoning does not converge — more budget just buys more of it. That is
the same signature as the whole-cell objective, on a rung that is one eighth of
the work.

**The distinction that predicts it is local-edit versus search:**

| rung | the edit it asks for | reasoning | outcome |
| --- | --- | ---: | --- |
| `gates` | "add a fourth poly stripe on net `I1_bar`" — enumerable, one right answer | 13,024 ch | answers in **45 s** |
| `shorts` | "move or shrink shapes until no two nets touch, without breaking any connection the netlist needs" — a constraint search over the whole floorplan | 158,775 ch | never answers |

A rung is answerable when the model can *name* the edit from the evidence. It is
not answerable when it has to *search* for one, however narrowly the objective is
worded — and no amount of rewording changes that, because the search is in the
problem, not in the sentence.

That is the real design rule a curriculum like this needs, and `NEW_PLAN.md`
could not have known it: **rungs must be split until each one is an edit the
evidence names, not a goal the model has to plan toward.**

### Three things that did NOT fix it

Recorded because negative results are the expensive half, and the next person
should not pay for them twice. Every row is the `shorts` rung of the same
iteration, measured against the gateway:

| intervention | reasoning | content |
| --- | ---: | --- |
| baseline (the rung as first written) | 44,653 ch @ 12k | 0 |
| `reasoning_effort: minimal` | 47,203 ch @ 12k | 0 |
| split `pins` into `shorts` + `pins` | 44,653 ch @ 12k | 0 |
| rewrite the objective so it asserts no false premise | 57,666 ch @ 16k | 0 |
| expose `router.connect_ports` and say the route is a function call | 58,819 ch @ 16k | 0 |
| raise the budget to 40,000 tokens | 158,775 ch | 0 |

The last one is the control that rules out budget. The others rule out the three
plausible content-level explanations: that the rung bundled two jobs, that its
objective pointed at evidence that was not there, and that the model was being
asked to compute a route it had no helper for.

**None of them was the cause.** The rung asks the model to make four ports reach
their terminals in a layout where every shape's position constrains every other
one — and that is a global constraint problem however it is phrased. The two
rungs that *do* work (`gates`, `taps`) both have the property that the edit is
additive and local: put a new stripe here, put a tap there, nothing else moves.

If there is a version of this rung that works, it is one where the **host** has
already done the geometry — "add Metal1 from (x1,y1) to (x2,y2) to connect port
I0 to XN1.gate" — leaving the model to apply a stated edit rather than find one.
At that point it is worth asking what the model is still contributing, which is a
real question about this whole approach and not a rhetorical one.

### One defect the measurement exposed on the way

The first `shorts` objective told the model to work from block [7]'s cross-net
overlap table. On the iteration that reached this rung, that table reads
`(none found)` — the disconnected nodes were *breaks*, not shorts, and the block
even says why it cannot see them ("rectangles matching no Port are
unattributed"). So the prompt asserted the existence of something the evidence
denied, and the model spent its budget trying to reconcile the two.

This is the `@context` failure again in a new costume: an objective that names
evidence which is not there. **Fixed** — the objective now states both causes,
says which one an empty table implies, and points at block [6] to settle it. It
cut the reasoning by roughly a third and did not make the rung answerable, which
is itself the point: the wording was a real bug, and it was not *the* bug.

---

## 1c. gpt-oss-120b: answers the rung Kimi cannot, but the agent CLI eats the gain

Tested because it was the last cheap thing left. Same prompts, same gateway.

**Raw, against the gateway — decisive:**

| | `gates` rung | `shorts` rung (the blocker) |
| --- | --- | --- |
| Kimi-K2.7-Code | 45 s, 13,024 ch reasoning, builds | **never answers** — 158,775 ch at a 40k budget, 0 content |
| **gpt-oss-120b** | **13 s**, 3,079 ch, builds | **28 s**, 10,551 ch, **builds and clears the rung** |

Its `shorts` module, run through the full DRC/LVS chain: **disconnected 4 → 0**,
unmatched ports 10 → 1, score **4500 → 3940**, and the ladder advanced to rung 6
of 8. So the blocker is a property of *Kimi*, not of the task, and not of the
curriculum. gpt-oss is also ~167 tok/s against ~90.

**Through the agent CLI — the gain disappears.** A full 10-call loop:

```
iter  rung      score    outcome
0     gates      6270    accepted
1     taps       4950    accepted
2     gates     10270    rejected -> branch from 1
3     gates     10270    rejected -> branch from 1     <-- identical to iter 2
4     taps       4950    accepted
5     gates     11910    rejected -> branch from 4
6     devices   11400    rejected -> branch from 4
7     shorts     4540    accepted
8     shorts     4750    rejected -> branch from 7
```

Best 4540, against Kimi's 4500 — no net gain, and **worse than the 3940 the same
model produced from a single direct call**. Five of nine iterations were
regressions.

Two things this exposes, both worth more than the model comparison:

- **The agent CLI is costing quality, and that is now measured twice.** The same
  model, the same prompt, produced a *better* layout in one direct gateway call
  than in ten agent-mediated ones. The harness already assembles the entire
  prompt host-side and the model needs no tools to answer a rung — it needs to
  emit one file. This moves §6.5 from "a nice simplification" to the single
  highest-value change left.
- **Branch-from-best is deterministic, and that is a design gap.** Iterations 2
  and 3 scored *identically* (10270): the rejection returned the run to
  iteration 1, which regenerated the same prompt, which produced the same wrong
  edit. Rejecting a regression stops the random walk and replaces it with a
  loop. The ledger digest is in the prompt and names the rejection, and it was
  not enough. A rejected branch needs to carry *what was tried and rejected*
  into the next prompt, not just the score.

**And one failure mode Kimi never showed.** On its first loop run gpt-oss
finished in 41 s and reported: *"Implemented the corrected layout module in
`iteration_1`. Key change: replaced the three tall polysilicon gates with eight
separate gate rectangles..."* — with `Changes +0 -0` and no file on disk. It
described the edit instead of making it. The harness caught it
(`Agent finished but did not write ...`), which is the fail-closed rule earning
its keep on a case nobody designed for. The prompt now says in as many words
that printing the module does not count and the host reads the path off disk.

---

## 2. Kimi-K2.7-Code, characterised

| | |
| --- | --- |
| Throughput | 47–67 tok/s across every call. Consistent. |
| Latency floor | ~1 s for a trivial prompt through the gateway. The gateway is not slow. |
| Reasoning | Always on by default. It emitted 121 characters of reasoning for `add(a, b)`. |
| Reasoning control | `reasoning_effort: none / low / …` **works** on this gateway. So does `chat_template_kwargs: {"thinking": false}`. |
| Reasoning scaling | Reasoning length tracks the *breadth* of the objective, not the prompt size. 39 KB whole-cell → 64k chars; 11 KB one-rung → 24k chars. |
| Failure mode | It never says "this is too big". It reasons until `finish_reason=length` and returns an empty `content`. Silent. |
| Code quality when it does answer | Good. It read the netlist, worked out that gate net `I1_bar` was ungated, and added the fourth poly stripe at a sensible pitch. |

**The one thing to remember:** with this model, `content=""` is not "it could
not do it". It is "the completion budget ran out during thinking". Those need
opposite responses — the first says redesign the task, the second says change a
parameter — and they are indistinguishable without looking at
`reasoning_content` and `finish_reason`.

---

## 3. What is good about this harness

Judged from the code, not from what the docs claim about it.

**The evidence packet is the best thing here.** Everything is recomputed from
raw artifacts, never re-read from a summary file that could be empty. Every cap
states how many bytes it dropped. `_finalise_verdict_line` gives block [2] an
unguessable token so no quoted text can forge the `RESULT:` line, and every
other `RESULT:` in the packet is indented out of column 0. That is a real
threat model, taken seriously.

**"Absence is never cleanliness" is enforced, not asserted.** A Magic report
with no `[INFO] COUNT:` trailer is not clean. A KLayout run is clean only when a
receipt proves every database it wrote was read. `test_absence_is_not_clean.py`
carries this across every artifact. This is the discipline that most agentic
harnesses lack, and it is why the failures here were diagnosable at all.

**Block [7] running the model's generator in a subprocess.** The comment
explains it exactly right: `except BaseException` cannot catch `os._exit`, a
fatal signal, or a C-level abort out of the KLayout binding. Someone worked out
that the artifact being measured can kill the measurer, and fixed it properly.

**The `_at` / state-driven split in `pipeline.sh`.** The host loop and the
model's own `selfcheck.sh` run byte-identical commands. They cannot drift into
two notions of "clean" — which is the single most common way a self-check
becomes a lie.

**The comments explain *why*, with the evidence.** `chmod 000` backfired because
ripgrep aborts rather than skips. The scaffold ships four `M1.d` violations
deliberately, because the alternative merged two nets. These are the notes that
stop the next person re-introducing a fixed bug, and they are everywhere.

---

## 4. What is bad about it

**Nothing in the harness ever looked at `finish_reason`.** Five consecutive runs
recorded `model_calls: 1`, an empty `iteration_1/`, ten minutes each — and the
only thing written down was "the model did not answer". The distinction between
*could not* and *ran out of budget mid-thought* is the whole diagnosis, it is one
field in the response, and it was never captured. The harness records what the
model produced but nothing about how the call ended.

**`copilot-rcp.sh` sets Kimi's output cap to its context window.**

```bash
declare -A MAX_OUTPUT_TOKENS=(
    ["moonshotai/Kimi-K2.7-Code"]="262144"   # every other model: 16000
)
```

262144 is the *input* limit copied into the output field. At the measured
~60 tok/s that is ~73 minutes before `finish_reason=length` can ever fire — so
under any sane `FIX_TIMEOUT` the token budget can never terminate a call and
`timeout` always does. That wrapper is outside this repository (deliberately,
and `test_scope_guards.py` enforces it), so **this one is for you to fix**:
set it to `16000` like the others. With `MODEL_EFFORT=low` the model now stops
on its own, so this is a latent hazard rather than the active blocker — but it
is a one-line fix and it removes a whole class of hang.

**The documentation had drifted from the code, in ways that mattered.** All
found and fixed while implementing:

| claim | reality |
| --- | --- |
| README: "~14 KB of evidence in a ~20.6 KB / ~5.2k-token prompt" | measured 39,628 bytes / ~9,907 tokens |
| README: "188 tests" | 203 at the time, in a document that also said 203 |
| README: "`context/` is `chmod 000`" | it is moved aside — `chmod` was tried and reverted, and the code comment says so |
| ORCHESTRATION: "budget 24 000 bytes" | `DEFAULT_MAX_BYTES` was 40 000 |
| ORCHESTRATION: block table stops at [8] | blocks [9], [10], [11] existed |

Not cosmetic. The prompt-size figure was off by 2× in the direction that mattered
for exactly the diagnosis being made.

**Stage 3 and Stage 4 were built, tested, and never called.** `score_iteration.py`
and `ledger.py` had zero references anywhere in `orchestrate.sh`, `pipeline.sh`
or the `Makefile`. 203 tests were green over a scorer nothing scored with. Tests
passing is not the same as code running. **Now wired.**

**A live dead-reference in the prompt**, of exactly the class the scope guards
exist to prevent. The prompt asserted unconditionally:

> Every numeric design rule is in block [9] of the packet … Do not go looking
> for them: the PDK rule decks under ./context are not readable from this session.

Under Stage 5 the `pins` and `nets` rungs do not carry block [9]. That is the
`@context` failure — a reference the model cannot resolve, plus a statement that
there is nowhere else to look — which had already cost a whole run once. **Fixed**:
the prompt now generates its cross-references from the packet in hand, and a test
asserts that every `block [N]` it names is actually present, at every rung.

**A timed-out call threw away work it had already been given.** `request_fix`
checked the CLI's exit status *before* checking whether the module existed, so a
model that wrote a complete module at t=500s and was still talking at t=600s had
that module deleted unread and the run aborted. **Fixed**: the module is checked
first.

**Finalisation shipped the wrong iteration.** With best-tracking, the
`max_iterations_reached` break fires before the next pass can reject a
regression, so the run would hand over the *worst* module while the ledger
recorded a better one. **Fixed**: it finalises the best.

**`memory.md` is 0 bytes after every run, and always will be.** The prompt asks
the model to write it, inside a hard wall-clock timeout — so it is the first
thing lost on exactly the run whose lessons matter. `ledger.py` was the right
response (the host writes it, from artifacts, before the model is invoked); it
just needed to actually be in the prompt. **Now it is.**

**Two fail-closed holes in the scorer, both of which the curriculum made
load-bearing.** Found by an adversarial review of my own changes, each confirmed
by three independent skeptics, each reproduced against the committed fixture:

- **`score_iteration` re-implemented `DrcReport.degraded` and dropped two of its
  three clauses.** It checked `available` and `completeness == DEGRADED`, but not
  `COMPLETENESS_UNVERIFIED` (no receipt, so the extent of the run is unknown) and
  not `unparsed_files > 0` (a rule database present but corrupt, whose violations
  vanish from the merge). The committed fixture is in the first state and scored
  `degraded: []`. **Fixed**: it now uses the `DrcReport.degraded` property rather
  than a second opinion about what the word means.

- **A Netgen `*.lvs.log` fallback read as a fully measured LVS.** The log carries
  the `Final result:` line and the prose totals but not the per-type device
  table, the disconnected-node lines or the pin-matching table. All three parsed
  as **0** and read as "nothing wrong", so an iteration whose `.lvs.out` was lost
  cleared the `devices` and `pins` rungs off a report whose own text says
  `*** MISMATCH ***` — and scored *better* than the same iteration measured
  properly, so `accept_or_reject` would crown it as `.best_iteration`.
  **Fixed**: the locator's note is kept, and a report with no per-type table is
  tagged `lvs-partial`.

Both are pre-existing Stage 4 defects that nothing depended on until the
curriculum started reading `Score` to decide which rung the model is on. That is
the general lesson: *wiring dead code up is a behaviour change, not a no-op.*

The guards themselves were also the wrong shape. `drc_measured()` and
`lvs_measured()` enumerated the degradation tags they knew about — so the moment
the scorer learned to emit `lvs-partial`, the guard did not recognise it and the
rung passed anyway. An allow-list of ways to be blind fails **open** every time
somebody discovers a new one. They now match by prefix: a tag naming an engine
means that engine's numbers cannot be trusted, whatever its suffix.

**Grader isolation is snapshot-and-compare, not isolation.** The README says so
honestly. A background process outliving the model call defeats it. Fine against
a model drawing a cell; not a security boundary.

**`opencode` is still broken on this machine** — hangs at `message=init` before
opening a connection. Not this harness's fault. `copilot` works: I sanity-checked
the session with a trivial prompt (1 s, clean reply) before spending a real run.

**`copilot` costs ~12.6k tokens of its own system prompt per call**, measured on
a 34-token user prompt. That is more than the entire evidence packet at most
rungs: for a 6k-token rung prompt, two thirds of what reaches the gateway is the
agent CLI's scaffolding.

**And the agent loop, not the model, is now the slow part.** The first real
end-to-end run of the finished curriculum, at the `gates` rung:

```
>> Prompt: 25160 bytes (~6290 tokens)
● Check iteration_1 directory (shell)    ls -la .../iteration_1
● Check memory.md existence (shell)      ls -la .../memory.md
!! copilot exited with status 124 and wrote no module
```

Six minutes, two `ls` calls, nothing written — while the *same rung* answered in
123 s over a direct gateway call. Each agent turn re-sends ~19k prompt tokens
(12.6k CLI scaffolding + 6.3k prompt) and reasons before emitting its tool call,
so exploration is extraordinarily expensive here in a way it is not in a normal
coding-agent setting.

Three things changed in response, all in the prompt rather than the harness:
the module is now written **first** (a turn that times out afterwards still
counts — the host grades whatever is at that path); `memory.md` and the target
directory are created before the call and the prompt says so, so there is
nothing to `ls`; and the note-taking step moved to the end, because the
host-written ledger already does the job memory.md was carrying.

---

## 5. Where I departed from NEW_PLAN.md, and why

Everything in the plan is implemented. Four decisions differ, all measured:

**1. Gate 2's exit criterion is measured from the GDS, not from `Score` alone.**
The plan's criterion — "poly/active crossings == `len(devices)`" — is not a field
on `Score`; it lives in `evidence.py`, which computes it by *running the model's
module*. The scorer is called in-process by `ledger.py`, so one `os._exit(0)` in
a generator would take the run's own history down with it. New module
`aion_layout/layout_metrics.py` counts merged `GatPoly ∩ Activ` regions in the
written GDS — no model code executed, and it is the artifact the DRC and LVS
tools actually read. Verified to agree with block [7]'s independent count (both 6
on the fixture, both 8 after the model's fix).

**2. The taps rung derives its nets from device *bulk* terminals, not from
`vdd_net`/`vss_net`.** Those helpers match the literal pin names `VDD`/`VSS`, so
a cell whose rails are `VPWR`/`VGND` would silently lose the taps rung while the
latch-up rules still fired. The plan's hard requirement is "nothing may be
specific to `AION_inv_nand2_nor2_1`", and a name match is exactly that kind of
specificity. Bulk terminals are topology and are in every netlist. Tested.

**3. A rung's packet is ~20 KB, not the plan's "under 4,000 tokens".** At 14 KB
the LVS rungs were truncating the Netgen digest and the layout digest's crossing
table — the two things those rungs are graded on. The harness's first rule is
that a truncated measurement is one the model cannot act on, and that outranks a
size target. The target was set when prompt size looked like the binding
constraint; row 3 of the table above shows it is not. Block [11], the only block
that is not evidence about this run, is given up whole — and says so — before any
measurement is cut.

**4. Branch-from-best moves a pointer, not files.** The plan's reviewers proposed
copying the best iteration's artifacts into a fresh directory, which brings five
hazards with it (copy the GDS too or it scores as unbuildable; `cp -a` or the
canonical-path check degrades; never copy `build_error.txt`; never overwrite
iteration N…). A `.base_iteration` key in `state.json` avoids all of them: the
best iteration's artifacts are already on disk where they were written, and the
prompt and the packet simply read from there.

**`FIX_TIMEOUT` is 6m, not "well under a minute".** The plan expected a narrow
call to be very fast. Measured, the raw completion is 123 s, and the agent CLI
adds its own system prompt and one completion per tool call on top. 6m is a real
margin over the measurement; 10m was most of an hour across a run.

---

## 6. If it still does not converge

In order, cheapest first:

1. **Check `content` vs `reasoning_content` before anything else.** If content is
   empty and `finish_reason=length`, it is a budget problem, not a task problem.
   Do not redesign the curriculum for it.
2. **Fix the output cap in `copilot-rcp.sh`** (§4). One line.
3. **Decide what to do about the connectivity rungs.** This is the blocker, and
   the three cheap fixes are already spent (§1b). The remaining options, in
   increasing order of how much they give up:

   a. **Host-computed edits.** The host reads both endpoints out of the GDS and
      states the wire: "add Metal1 from (x1,y1) to (x2,y2)". Most likely to work,
      and it moves the placement decision from the model to the harness — which
      the README's own separation of concerns says is not the harness's job. Worth
      doing anyway as a measurement: if the model cannot apply even a fully
      specified edit, that is decisive information.
   b. **A different model.** `openai/gpt-oss-120b` is on the gateway and untested
      on this task. `MODEL=` selects it, no code change. Cheapest thing left.
   c. **Accept the boundary and report it.** Four of eight rungs clear reliably.
      That is a real, reproducible result about what this model can do on a
      standard-cell layout, and `NEW_PLAN.md` §6.4 already names it as a
      legitimate outcome.
4. **Try `openai/gpt-oss-120b`.** Still untested on this task. `MODEL=` selects
   it; no code change.
5. **Reconsider the agent CLI.** The harness assembles the entire prompt
   host-side and the model needs no tools to answer a rung — it needs to emit one
   Python file. A direct gateway call would remove ~12.6k tokens of per-call
   overhead, give exact control of `max_tokens` and `reasoning_effort`, and
   delete the whole class of "the CLI hung" failure. That is a real
   simplification, not a workaround; I did not build it because it is outside
   what `NEW_PLAN.md` asked for.
