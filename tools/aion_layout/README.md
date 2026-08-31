# AION Layout

Technology-aware standard-cell layout tool for the IHP SG13G2 PDK.

This is a slimmed-down version intended to be driven by a Copilot skill. It
keeps the core layout framework, the CLI scripts, and one example cell.

## Project structure

```text
aion_layout/
├── Makefile                       # Local convenience targets
├── README.md                      # This file
├── pyproject.toml                 # Python dependencies
├── aion_layout/                   # Framework package
│   ├── __init__.py
│   ├── tech.py                    # SG13G2 layers and rules
│   ├── primitives.py              # Point, Rect, transformations
│   ├── shapes.py                  # Layer-aware shapes
│   ├── cell.py                    # Cell container and GDS writer
│   ├── building_blocks.py         # Diffusion, wells, poly, contacts, wires, pins, rails
│   ├── router.py                  # Manual-routing helpers
│   ├── verification.py            # DRC/LVS wrappers
│   ├── spice_parser.py            # SPICE subckt parser
│   ├── netlist_view.py            # Topology helpers
│   ├── auto_scaffold.py           # Starter cell generator from a netlist
│   ├── gds_to_python.py           # GDS to Python converter
│   └── doc_generator.py           # Markdown documentation generator
├── cells/                         # Cell generators
│   ├── __init__.py
│   ├── sg13g2_nand2_1.py          # NAND2 example
│   └── template.py                # Generator template
└── scripts/                       # CLI helpers
    ├── generate_cell.py
    ├── generate_from_netlist.py
    ├── generate_cell_doc.py
    ├── gds_to_python.py
    └── report_verification.py
```

## Quick start

All scripts accept arbitrary file paths; nothing is tied to the `cells/` or
`runs/` directories.

```bash
# Generate a GDS from a Python cell generator
python3 scripts/generate_cell.py cells/sg13g2_nand2_1.py path/to/out.gds

# Scaffold a new cell from a SPICE netlist
python3 scripts/generate_from_netlist.py path/to/netlist.spice -o path/to/cell.py

# Convert a GDS back to Python
python3 scripts/gds_to_python.py path/to/cell.gds -o path/to/cell_from_gds.py

# Run DRC/LVS and print a summary
python3 scripts/report_verification.py \
    --cell sg13g2_nand2_1 \
    --gds path/to/out.gds \
    --netlist path/to/netlist.spice \
    --runs-dir path/to/runs
```

DRC/LVS are executed through the local `scripts/docker_run.sh` wrapper,
which runs `sak-drc.sh` / `sak-lvs.sh` inside the AION Docker container.

## Writing a cell generator

A cell generator is a Python module that exposes:

```python
def generate(name: str, tech: aion_layout.tech.Tech) -> aion_layout.cell.Cell:
    ...
```

See `cells/template.py` for a minimal starting point and
`cells/sg13g2_nand2_1.py` for a complete example.

## Reference documentation

- **[GDS_PYTHON_API.md](GDS_PYTHON_API.md)** — Python API for geometry primitives, layers, shapes, cells, building blocks, and routing helpers.
- **[CLI_REFERENCE.md](CLI_REFERENCE.md)** — Makefile targets, CLI scripts, Docker verification flow, and common workflows.

## Notes

- GDS output uses the KLayout Python API (`klayout.db`).
- The tool is hardcoded to IHP SG13G2.
- LVS consumes a SPICE netlist provided by the upstream step; the tool does not generate it.
