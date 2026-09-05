# `aion_minimizer`

`aion_minimizer` takes a small gate-level SPICE netlist — instances of standard
cells — and re-implements it as one transistor-level SPICE cell. It reads the
Boolean function out of the PDK transistors, partitions the gate DAG into the
cheapest set of complementary CMOS stages, sizes the devices, and can prove the
result equivalent by exhaustive switch-level simulation.

Outputs land under `build/aion_minimizer/` by default when run through the root
`Makefile`.

## Quick start

```bash
make aion-minimizer-run
make aion-minimizer-test
```

## Contents

- [How it works](#how-it-works)
- [Why not one big gate](#why-not-one-big-gate)
- [Inverted inputs](#inverted-inputs)
- [Sizing](#sizing)
- [Commands](#commands)
- [Configuration flags](#configuration-flags)
- [Module map](#module-map)
- [Tests](#tests)

## How it works

```
top.spice ──┐
            ├─> parse ─> gate truth tables ─> flatten ─> per-output truth table
lib.spice ──┘                                                    │
                                              partition into complementary stages
                                                       ┌─────────┴─────────┐
                                              resynthesized stage    PDK cell kept
                                                       └─────────┬─────────┘
                                                    size ─> render ─> .subckt
                                                                 │
                                                    exhaustive equivalence check
```

**1. Read the cells.** Every `.subckt` in the gate library that contains
transistors is simulated as ideal switches over all input vectors, which yields
its truth table. Cells that are not single-output combinational gates — flops,
tie cells, fill — are skipped, and the reason is recorded so a later "unknown
gate cell" can say *why* the cell was unavailable.

**2. Flatten.** The top-level netlist is topologically sorted, checked for
combinational loops and multiple drivers, and evaluated over every primary-input
vector. Several primary outputs are supported.

**3. Partition.** Each part of the partition becomes either one resynthesized
complementary stage or the original PDK cell, untouched. See
[below](#why-not-one-big-gate).

**4. Minimize each stage.** `SOPform`/`POSform` give the exact two-level forms;
both output polarities are costed and the cheaper wins.

**5. Size and render.** Devices are folded to the PDK's finger widths, one
inverter is built per complemented signal, and everything is emitted into a
single `.subckt` whose pin list is the original one, verbatim.

**6. Verify.** `--verify` re-simulates the generated transistors and compares
against the flattened truth tables, per output.

### Costing the two polarities

A function can be built directly, or built inverted and restored with an output
inverter. Which is cheaper depends on how many *input* inverters each polarity
needs, and the rule differs between the two networks:

| Network | Built from | Needs `X_bar` for |
|---------|-----------|-------------------|
| NMOS pull-down | SOP of `!F` | a **complemented** literal `~X` |
| PMOS pull-up | POS of `F` | a **plain** literal `X` |

The pull-up rule is the counter-intuitive one: a PMOS conducts when its gate is
low, so a literal `X` in the POS form is applied as `X_bar`. Getting it backwards
is expensive — AND3 comes out as three input inverters driving an inverted-input
NAND3 (12 devices) instead of a NAND3 plus an output inverter (8).

## Why not one big gate

Merging everything into a single complementary gate is only a good idea while
the two-level form stays small. It does not for non-unate functions: an n-input
XOR has 2^(n-1) prime implicants of n literals each, so the devices grow
exponentially.

| Netlist | Standard cells | One merged gate | What the tool emits |
|---------|---------------:|----------------:|--------------------:|
| `xor2` | 10 | 12 | 10 |
| `xor2 → xor2` | 20 | 30 | 20 |
| `xor2, xor2 → xor2` | 30 | **72** | 30 |
| `and2 → and2` | 12 | 8 | 8 |
| `nand2, nand2 → nand2` | 12 | 10 | 10 |
| 8-gate reconvergent blob | 32 | 20 | 20 |

So the tool searches over ways to *partition* the gate DAG instead. A part is
legal when only its root's net escapes it — every consumer of an absorbed
instance must be absorbed too — which also lets it merge across reconvergence:
a net with two consumers can still be swallowed when both consumers end up in
the same part. Flattening everything is simply the partition with a single
part, so nothing that used to be found is lost.

Each part is then costed both ways, as a resynthesized stage and as the PDK
cells left alone, and the cheaper one is taken. **The result is therefore never
worse than the netlist it was given.** A part is also rejected outright if its
series stacks exceed `--max-stack-depth`.

Two useful side effects: a part whose function is constant collapses to a
two-device tie cell, and anything that only fed it is then dead and dropped.

`--single-stage` restores the unconditional merge, which is handy for measuring
what the partitioning bought.

## Inverted inputs

When a merged stage needs `~I1`, the cell can either build that inverter itself
or take the complement on an extra port:

```bash
# the cell builds its own inverter (default)
python -m aion_minimizer run cell.spice --gates lib.spice --inverted-inputs internal
#   .subckt AION_x I0 I1 I2 O0 VDD VSS          8 transistors

# the complement arrives on a port
python -m aion_minimizer run cell.spice --gates lib.spice --inverted-inputs external
#   .subckt AION_x I0 I1 I2 O0 I1_bar VDD VSS   6 transistors
```

Externalizing takes two devices out of the cell and hands the caller an
obligation: whoever instantiates it must drive `I1_bar` with `~I1`. That is free
when the parent netlist already carries the complement — very common, since `I1`
is often produced by an inverter whose own input is exactly `~I1` — and a wash
when a new inverter has to be inserted. Which is why the decision is per input
and belongs to whoever can see the parent netlist:

```bash
--inverted-inputs auto --external-inputs I1,I3
```

`--report cell.json` writes the interface for that caller to act on:

```json
{
  "cell": "AION_inv_nand2_nor2",
  "ports": ["I0", "I1", "I2", "O0", "I1_bar", "VDD", "VSS"],
  "transistors": 6,
  "original_transistors": 10,
  "complemented_inputs": {"internal": [], "external": ["I1"], "nets": []},
  "complement_ports": {"I1_bar": "I1"},
  "devices_saved_per_externalized_input": 2
}
```

Only primary inputs are eligible. A complemented *internal* net has no port to
hang off, so its inverter always stays inside; those appear under `"nets"`.

Extra ports are inserted ahead of the supplies, so `VDD VSS` stay last as they
do in every SG13G2 cell, and the existing pins keep their order — a cell with
nothing to externalize keeps a byte-identical pin list.

`--verify` checks the externalized cell by driving each `_bar` port with the
inverse of its source, so it fails if the cell needs anything more than that.

## Sizing

SG13G2 describes a device as a *total* width `w` split into `ng` fingers, and
the finger width never changes:

| Cell | NMOS | PMOS | `ng` |
|------|------|------|-----:|
| `inv_1` | `740n` | `1.12u` | 1 |
| `inv_4` | `2.96u` | `4.48u` | 4 |
| `inv_16` | `11.84u` | `17.92u` | 16 |

So drive strength is expressed by folding, never by a bare width — a wider
finger does not fit the cell row. `--drive N` reproduces exactly the table
above.

`nand4_1` and `nor4_1` also use precisely the widths of `inv_1`, so the PDK does
not compensate series stacks at x1 either. `--stack-sizing` turns compensation
on for those who want it; it widens by stack depth and folds accordingly, and
`--max-fingers` bounds the result.

## Commands

### `aion-minimizer-run`

```bash
make aion-minimizer-run
make aion-minimizer-run \
    AION_MIN_INPUT=examples/aion_minimizer/AION_a21o_and2_xor2.spice \
    AION_MIN_GATES=tech/spice/sg13g2_stdcell.spice \
    AION_MIN_MODE=transistor \
    AION_MIN_OUTPUT=build/aion_minimizer/mega.spice
```

Direct CLI:

```bash
python -m aion_minimizer run cell.spice \
    --gates tech/spice/sg13g2_stdcell.spice \
    -o build/aion_minimizer/cell_minimized.spice \
    --verify
```

It prints what the partitioner decided, per stage:

```
8 transistors vs 10 original (+2), 1 merged stage(s), 0 cell(s) kept, 1 inverter(s), max stack 3
  O0: merged Xg0+Xg2+Xg1
  complemented inputs built inside: I1
Equivalence: PASS
```

### `aion-minimizer-verify-spice`

Runs `make aion-char-verify-spice` on a minimized cell against a reference cell
in `examples/aion_char/aion_cells.v`.

```bash
make aion-minimizer-verify-spice CELL=AION_inv_nand2_nor2_16 \
                                 SPICE=build/aion_minimizer/AION_inv_nand2_nor2_minimized.spice
```

### `aion-minimizer-test` / `aion-minimizer-clean`

```bash
make aion-minimizer-test
make aion-minimizer-clean
```

## Configuration flags

Makefile variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `AION_MIN_INPUT` | `examples/aion_minimizer/AION_inv_nand2_nor2.spice` | Top-level gate-level SPICE netlist |
| `AION_MIN_GATES` | `examples/aion_minimizer/sg13g2_stdcell.spice` | Gate-definition library (repeatable via CLI) |
| `AION_MIN_MODE` | `transistor` | `transistor`, `area` or `balance` |
| `AION_MIN_OUTPUT` | `$(BUILD_DIR)/aion_minimizer/AION_inv_nand2_nor2_minimized.spice` | Output netlist |

CLI options:

| Option | Default | Description |
|--------|---------|-------------|
| `--gates` | (required) | Gate-definition library; repeatable |
| `--top-name` | (inferred) | Which `.subckt` to minimize when the file holds several |
| `-o`, `--output` | `mega.spice` | Output SPICE file |
| `--mode` | `transistor` | `transistor`, `area` or `balance` |
| `--max-stack-depth` | `4` | Maximum series devices between a rail and the output |
| `--max-cluster-inputs` | `8` | Maximum boundary inputs of one merged stage |
| `--no-inline` | off | Resynthesize every stage even when the PDK cell is cheaper |
| `--single-stage` | off | Flatten everything into one gate, cost regardless |
| `--inverted-inputs` | `internal` | `internal`, `external` or `auto` — see [above](#inverted-inputs) |
| `--external-inputs` | (none) | Pins to externalize under `auto` |
| `--report` | (none) | Write the cell-interface JSON |
| `--wn` / `--wp` | `0.74u` / `1.12u` | Width of one finger |
| `--l` | `0.13u` | Transistor length |
| `--drive` | `1` | Drive strength; folds width and `ng` together |
| `--stack-sizing` | off | Widen a device by its series stack depth |
| `--max-fingers` | `16` | Upper bound on fingers per device |
| `--max-inputs` | `6` | Refuse netlists with more primary inputs |
| `--verify` | off | Exhaustive switch-level equivalence check |

## Module map

| Module | Responsibility |
|--------|----------------|
| `cli.py` | Argument parsing and reporting |
| `synthesis.py` | Orchestration; inverted-input policy; the result object |
| `spice_parser.py` | `.subckt` / MOSFET / instance parsing |
| `gate_extractor.py` | Truth table of a PDK cell by ideal-switch simulation |
| `netlist_evaluator.py` | Flatten and evaluate the gate netlist |
| `decompose.py` | Partition the gate DAG into stages; per-part cost |
| `minimizer.py` | Two-level forms, polarity choice, complement accounting |
| `pn_network.py` | Series/parallel P and N networks from those forms |
| `sizing.py` | Device geometry and folding |
| `render.py` | Sized networks, inverters, tie cells → MOSFET list |
| `inline.py` | PDK cells → MOSFET list, unchanged |
| `spice_writer.py` | `.subckt` emission |
| `equivalence.py` | Exhaustive truth-table check of the generated netlist |
| `cost_model.py` | Shared `Inverter` type |

## Tests

```bash
make aion-minimizer-test
# or
python -m pytest tools/aion_minimizer/tests -q
```

| File | Covers |
|------|--------|
| `test_synthesis.py` | Per-netlist invariants: equivalence, never-worse, stack budget, port order, determinism |
| `test_decompose.py` | Partition legality, reconvergent merges, dead-stage pruning |
| `test_minimizer.py` | Polarity costing, complement rules, constants, the XOR blow-up itself |
| `test_sizing.py` | Folding against the real `inv_1`/`inv_4`/`inv_16` geometries |
| `test_inverted_inputs.py` | `internal`/`external`/`auto`, port placement, the report |
| `test_gate_extractor.py` | PDK cell functions; skipped cells carry a reason |
| `test_spice_parser.py` | Continuations, inline comments, subckt parameters, malformed input |
| `test_cli.py` | The command line as the Makefile drives it |

The suite needs only `sympy` and `networkx`; no EDA container.
