# AION Layout CLI & Makefile Reference

This document describes the command-line interface and Makefile targets for the `tools/aion_layout` standard-cell layout generator. It is intended as a quick reference for AI agents and human users who want to drive the tool without reading the source code.

---

## Table of contents

1. [Makefile targets](#makefile-targets)
2. [Makefile variables](#makefile-variables)
3. [CLI scripts](#cli-scripts)
4. [Docker-based verification](#docker-based-verification)
5. [Typical workflows](#typical-workflows)

---

## Makefile targets

Run all commands from `tools/aion_layout`.

| Target | Description | Depends on |
|--------|-------------|------------|
| `gds` | Generate `runs/<CELL_NAME>.gds` from `CELL_MODULE`. | — |
| `drc` | Run Magic and KLayout DRC on the generated GDS. | `gds` |
| `lvs` | Run Magic+Netgen LVS against `NETLIST`. | `gds` |
| `verify` | Run `gds` + `drc` + `lvs` and print a one-page summary. | `gds`, `drc`, `lvs` |
| `netlist` | Scaffold `CELL_MODULE` from `SPICE`. | — |
| `doc` | Generate `runs/<CELL_NAME>.md` documentation. | — (expects prior reports) |
| `gds2py` | Convert the generated GDS back into `CELL_MODULE`. | — (expects GDS) |
| `clean` | Remove the `runs/` directory. | — |
| `help` | Show usage summary. | — |

### Important notes

- `drc`, `lvs`, and `verify` invoke the AION Docker container through `scripts/docker_run.sh`.
- The local environment may not have `klayout` installed; run these targets from inside the container or ensure the container is available.
- `doc` reads existing DRC/LVS reports produced by `verify`.
- `gds2py` overwrites `CELL_MODULE` with Python code generated from the GDS.

---

## Makefile variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CELL_MODULE` | `cells/sg13g2_nand2_1.py` | Path to the Python cell generator. |
| `CELL_NAME` | stem of `CELL_MODULE` | Top-level cell name and base for output files. |
| `SPICE` | `$(CELL_NAME).spice` | Input SPICE netlist for `make netlist`. |
| `NETLIST` | `$(CELL_NAME).spice` | SPICE/CDL netlist for LVS and doc generation. |
| `RUNS_DIR` | `runs` | Directory for generated artifacts. |
| `RUN_SCRIPT` | `scripts/docker_run.sh` | Path to the Docker runner wrapper. |

Derived paths:

- `GDS_FILE = $(RUNS_DIR)/$(CELL_NAME).gds`
- `DRC_RUN_DIR = $(RUNS_DIR)/drc/$(CELL_NAME)`
- `LVS_RUN_DIR = $(RUNS_DIR)/lvs/$(CELL_NAME)`

### Examples

```bash
# Default NAND2 cell
make gds

# Custom cell
make gds CELL_MODULE=cells/my_cell.py

# Full verification flow
make verify CELL_MODULE=cells/sg13g2_nand2_1.py NETLIST=nand2.spice

# Scaffold from netlist
make netlist CELL_MODULE=cells/my_cell.py SPICE=my_cell.spice

# Convert GDS back to Python
make gds2py CELL_MODULE=cells/sg13g2_nand2_1.py

# Clean everything
make clean
```

---

## CLI scripts

All scripts live in `tools/aion_layout/scripts/`. They can be run directly with `python3 scripts/<script>.py ...`.

### `generate_cell.py`

Generate a GDS file from a Python cell generator.

```bash
python3 scripts/generate_cell.py <cell.py|module.path> <output.gds>
```

Options:

- `--cell-name NAME` — override the top-level cell name.
- `--tech module.path:tech_obj` — override the technology object (default: `aion_layout.tech:sg13g2_tech`).

Examples:

```bash
python3 scripts/generate_cell.py cells/sg13g2_nand2_1.py runs/sg13g2_nand2_1.gds
python3 scripts/generate_cell.py cells.my_cell runs/my_cell.gds --cell-name my_cell
```

### `generate_from_netlist.py`

Scaffold a starter cell generator from a SPICE netlist.

```bash
python3 scripts/generate_from_netlist.py <netlist.spice> -o <output.py>
```

Options:

- `-o, --output PATH` — required output Python file.
- `--width NM` — override the scaffolded cell width.
- `--summary` — print a netlist summary before writing.
- `--force` — overwrite an existing output file.

Example:

```bash
python3 scripts/generate_from_netlist.py nand2.spice -o cells/nand2_scaffold.py --summary
```

### `gds_to_python.py`

Convert a GDSII layout back into a runnable AION Python generator.

```bash
python3 scripts/gds_to_python.py <input.gds>
python3 scripts/gds_to_python.py <input.gds> -o <output.py>
```

Options:

- `-o, --output PATH` — write to file instead of stdout.
- `--cell NAME` — select a specific top cell.
- `--tech module.path:tech_obj` — override technology.
- `--no-ports` — skip reconstructing `Port` objects from text labels.

Example:

```bash
python3 scripts/gds_to_python.py runs/sg13g2_nand2_1.gds -o cells/sg13g2_nand2_1_from_gds.py
```

### `generate_cell_doc.py`

Generate markdown documentation for a verified cell.

```bash
python3 scripts/generate_cell_doc.py \
    --cell-module <cell.py> \
    --netlist <netlist.spice> \
    -o <output.md> \
    --runs-dir <runs>
```

Options:

- `--cell-module PATH` — required cell generator.
- `--cell-name NAME` — override cell name (default: module stem).
- `--netlist PATH` — required SPICE netlist.
- `-o, --output PATH` — required output markdown file.
- `--runs-dir PATH` — required directory containing DRC/LVS reports.

Example:

```bash
python3 scripts/generate_cell_doc.py \
    --cell-module cells/sg13g2_nand2_1.py \
    --netlist nand2.spice \
    -o runs/sg13g2_nand2_1.md \
    --runs-dir runs
```

### `report_verification.py`

Print a one-page DRC/LVS summary.

```bash
python3 scripts/report_verification.py \
    --cell <name> \
    --gds <gds> \
    --netlist <netlist> \
    --runs-dir <runs> \
    [--parse-only]
```

Options:

- `--cell NAME` — required cell name.
- `--gds PATH` — required GDS file.
- `--netlist PATH` — required SPICE/CDL netlist.
- `--runs-dir PATH` — required runs directory.
- `--parse-only` — parse existing reports instead of running tools.
- `--run-script PATH` — override the Docker runner path.

Example:

```bash
python3 scripts/report_verification.py \
    --cell sg13g2_nand2_1 \
    --gds runs/sg13g2_nand2_1.gds \
    --netlist nand2.spice \
    --runs-dir runs \
    --parse-only
```

---

## Docker-based verification

DRC and LVS run inside the AION Docker container (`iic-osic-tools`). The wrapper script is in this directory:

```bash
scripts/docker_run.sh <command>
```

Inside the container, the project is mounted at `/foss/designs/aion_flow` and the PDK is set to `ihp-sg13g2`.

### Running make targets inside Docker

Because `docker_run.sh` uses `docker exec`, nested `docker_run.sh` calls do not work inside the container. Run the underlying `sak-*` scripts directly:

```bash
# From tools/aion_layout on the host
scripts/docker_run.sh make gds

# DRC directly
scripts/docker_run.sh sak-drc.sh -d -b -l macro -w runs/drc/sg13g2_nand2_1 runs/sg13g2_nand2_1.gds

# LVS directly
scripts/docker_run.sh sak-lvs.sh -d -b -w runs/lvs/sg13g2_nand2_1 -s nand2.spice -l runs/sg13g2_nand2_1.gds -c sg13g2_nand2_1
```

### Report locations

After a successful run:

- Magic DRC: `runs/drc/<cell>/<cell>.magic.drc/<cell>.magic.drc.rpt`
- KLayout DRC: `runs/drc/<cell>/<cell>.klayout.drc/*_full.lyrdb`
- Netgen LVS: `runs/lvs/<cell>/<cell>.magic.lvs/<cell>.lvs.out`

---

## Typical workflows

### 1. Generate and verify a cell

```bash
make gds CELL_MODULE=cells/sg13g2_nand2_1.py
scripts/docker_run.sh sak-drc.sh -d -b -l macro -w runs/drc/sg13g2_nand2_1 runs/sg13g2_nand2_1.gds
scripts/docker_run.sh sak-lvs.sh -d -b -w runs/lvs/sg13g2_nand2_1 -s nand2.spice -l runs/sg13g2_nand2_1.gds -c sg13g2_nand2_1
python3 scripts/report_verification.py --cell sg13g2_nand2_1 --gds runs/sg13g2_nand2_1.gds --netlist nand2.spice --runs-dir runs --parse-only
```

### 2. Scaffold a new cell from a netlist

```bash
python3 scripts/generate_from_netlist.py my_cell.spice -o cells/my_cell.py --summary
# Then edit cells/my_cell.py to complete routing and contacts.
```

### 3. Convert an existing GDS to Python

```bash
python3 scripts/gds_to_python.py runs/sg13g2_nand2_1.gds -o cells/sg13g2_nand2_1_from_gds.py
```

### 4. Generate documentation

```bash
python3 scripts/generate_cell_doc.py \
    --cell-module cells/sg13g2_nand2_1.py \
    --netlist nand2.spice \
    -o runs/sg13g2_nand2_1.md \
    --runs-dir runs
```
