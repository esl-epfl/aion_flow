# `aion_minimizer`

`aion_minimizer` takes a small gate-level SPICE netlist (instances of standard
cells) and merges them into a single optimized transistor-level SPICE netlist
(a "megagate"). It performs Boolean minimization, builds complementary P/N
networks, sizes the transistors, and can run an exhaustive truth-table
equivalence check.

All outputs land under `build/aion_minimizer/` by default when run through the
root `Makefile`.

## Quick start

```bash
make aion-minimizer-run
```

## Commands

All commands are available through the root `Makefile` and write into
`BUILD_DIR`.

### `aion-minimizer-run`

Minimizes the default example netlist into a transistor-level SPICE netlist.

```bash
make aion-minimizer-run
```

Output: `$(AION_MIN_OUTPUT)` (default:
`$(BUILD_DIR)/aion_minimizer/AION_inv_nand2_nor2_minimized.spice`)

You can override the input, gate library, mode, and output:

```bash
make aion-minimizer-run \
    AION_MIN_INPUT=examples/aion_minimizer/AION_a21o_and2_xor2.spice \
    AION_MIN_GATES=examples/aion_minimizer/sg13g2_stdcell.spice \
    AION_MIN_MODE=transistor \
    AION_MIN_OUTPUT=build/aion_minimizer/mega.spice
```

### `aion-minimizer-verify-spice`

Runs the minimizer and then invokes `make aion-char-verify-spice` on the
generated netlist. You must pass `CELL=<existing_aion_cell_name>`, where the
name is a cell that already exists in `examples/aion_char/aion_cells.v`.
`aion_char` will verify the minimized SPICE netlist against that reference
cell.

```bash
make aion-minimizer-verify-spice CELL=AION_inv_nand2_nor2_16
```

This is equivalent to running `aion-minimizer-run` followed by:

```bash
make aion-char-verify-spice \
    CELL=AION_inv_nand2_nor2_16 \
    SPICE=build/aion_minimizer/AION_inv_nand2_nor2_minimized.spice
```

### `aion-minimizer-clean`

Removes `build/aion_minimizer/`.

```bash
make aion-minimizer-clean
```

## Direct CLI usage

You can also run the tool directly without `make`:

```bash
python -m aion_minimizer run \
    examples/aion_minimizer/AION_inv_nand2_nor2.spice \
    --gates examples/aion_minimizer/sg13g2_stdcell.spice \
    -o build/aion_minimizer/mega.spice \
    --mode transistor \
    --verify
```

Or use the installed console entry point:

```bash
aion-minimizer run ...
```

## Configuration flags

The following Makefile variables control the minimizer:

| Variable | Default | Description |
|----------|---------|-------------|
| `AION_MIN_INPUT` | `examples/aion_minimizer/AION_inv_nand2_nor2.spice` | Top-level gate-level SPICE netlist |
| `AION_MIN_GATES` | `examples/aion_minimizer/sg13g2_stdcell.spice` | Gate-definition library (repeatable via CLI) |
| `AION_MIN_MODE` | `transistor` | Optimization mode: `transistor`, `area`, or `balance` |
| `AION_MIN_OUTPUT` | `$(BUILD_DIR)/aion_minimizer/AION_inv_nand2_nor2_minimized.spice` | Output transistor-level SPICE netlist |

CLI-only options (pass them to `python -m aion_minimizer run`):

| Option | Default | Description |
|--------|---------|-------------|
| `--wn` | `0.74u` | Base NMOS width |
| `--wp` | `1.48u` | Base PMOS width |
| `--l` | `0.13u` | Transistor length |
| `--max-inputs` | `6` | Maximum primary inputs for exhaustive verification |
| `--verify` | off | Run truth-table equivalence check |

## Examples

The `examples/aion_minimizer/` directory contains example netlists and
standalone runnable scripts:

* `run_example.py` — runs the minimizer on the default example.
* `parse_example.py` — demonstrates SPICE parsing.

Run them with:

```bash
python examples/aion_minimizer/run_example.py
python examples/aion_minimizer/parse_example.py
```