# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Updated:                   2026-09-03
#  Description:               AION layout tool — minimal local interface
# ================================================================

# Paths (override from the command line).
CELL_MODULE  ?= cells/sg13g2_nand2_1.py
CELL_NAME    ?= $(basename $(notdir $(CELL_MODULE)))
SPICE        ?= $(CELL_NAME).spice
NETLIST      ?= $(CELL_NAME).spice
RUNS_DIR     ?= build
GDS_FILE      = $(RUNS_DIR)/$(CELL_NAME).gds
# One drc/ and one lvs/ directory per run directory — the same layout
# pipeline.sh writes and report_verification.py globs.
DRC_RUN_DIR   = $(RUNS_DIR)/drc
LVS_RUN_DIR   = $(RUNS_DIR)/lvs
RUN_SCRIPT   ?= scripts/docker_run.sh
PYTHON       ?= python3
PYTEST       ?= $(PYTHON) -m pytest

# docker_run.sh always lands in the flow root, so every containerised command
# has to cd into this tool first — exactly as pipeline.sh does.
IN_TOOL       = cd tools/aion_layout &&

# The helpers import aion_layout from the repository root; make it importable
# without an editable install, mirroring the PYTHONPATH pipeline.sh exports.
export PYTHONPATH := $(CURDIR)$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: gds drc lvs verify netlist doc gds2py test selfcheck flow clean help

# Generate the GDS for CELL_MODULE.
gds:
	mkdir -p $(RUNS_DIR)
	$(PYTHON) scripts/generate_cell.py $(CELL_MODULE) $(GDS_FILE)

# Run Magic + KLayout DRC on the generated GDS (-b both engines, -l macro).
drc: gds
	mkdir -p $(DRC_RUN_DIR)
	$(RUN_SCRIPT) "$(IN_TOOL) sak-drc.sh -d -b -l macro -w $(DRC_RUN_DIR) $(GDS_FILE)"

# Run LVS against the provided SPICE netlist.
lvs: gds
	mkdir -p $(LVS_RUN_DIR)
	$(RUN_SCRIPT) "$(IN_TOOL) sak-lvs.sh -d -b -w $(LVS_RUN_DIR) -s $(NETLIST) -l $(GDS_FILE) -c $(CELL_NAME)"

# Run gds + drc + lvs and print the verdict.  Exits 0 PASS, 1 FAIL, 2 ERROR.
verify: gds drc lvs
	$(PYTHON) scripts/report_verification.py \
		--cell $(CELL_NAME) --gds $(GDS_FILE) --netlist $(NETLIST) --runs-dir $(RUNS_DIR) --parse-only

# Scaffold a new cell generator from a SPICE netlist.
netlist:
	$(PYTHON) scripts/generate_from_netlist.py $(SPICE) -o $(CELL_MODULE)

# Generate markdown documentation for a verified cell.
doc:
	$(PYTHON) scripts/generate_cell_doc.py \
		--cell-module $(CELL_MODULE) --netlist $(NETLIST) -o $(RUNS_DIR)/$(CELL_NAME).md --runs-dir $(RUNS_DIR)

# Convert an existing GDS into a Python generator.
gds2py:
	$(PYTHON) scripts/gds_to_python.py $(GDS_FILE) -o $(CELL_MODULE)

# Run the host-side test suite (no container, no PDK needed).
test:
	$(PYTEST) tests/ -q

# Grade a cell generator exactly the way the loop grades it: build the GDS,
# run Magic + KLayout DRC and Netgen LVS, report, print the evidence packet.
# This runs sak-drc.sh and sak-lvs.sh in the container — not a static check.
selfcheck:
	./scripts/selfcheck.sh $(CELL_MODULE) $(RUNS_DIR)

# Remove all generated artifacts.
clean:
	rm -rf $(RUNS_DIR)

flow:
	./orchestrate.sh AION_inv_nand2_nor2_1_minimized.spice build 2

# Show usage.
help:
	@echo "Usage: make <target> CELL_MODULE=<path/to/cell.py> [NETLIST=<netlist>] [RUNS_DIR=<dir>]"
	@echo ""
	@echo "Targets:"
	@echo "  gds       Generate $(RUNS_DIR)/<CELL_NAME>.gds"
	@echo "  drc       Run Magic + KLayout DRC into $(DRC_RUN_DIR)/"
	@echo "  lvs       Run Magic + Netgen LVS against NETLIST into $(LVS_RUN_DIR)/"
	@echo "  verify    Run gds + drc + lvs, then print DRC:/LVS:/RESULT: (0 PASS, 1 FAIL, 2 ERROR)"
	@echo "  netlist   Scaffold CELL_MODULE from SPICE"
	@echo "  doc       Generate $(RUNS_DIR)/<CELL_NAME>.md"
	@echo "  gds2py    Convert GDS to CELL_MODULE"
	@echo "  test      Run the pytest suite in tests/"
	@echo "  selfcheck Run the full Docker build+DRC+LVS+report chain on CELL_MODULE"
	@echo "  flow      Run the whole agentic orchestrate.sh loop (Docker + model calls)"
	@echo "  clean     Remove $(RUNS_DIR)/"
	@echo ""
	@echo "Examples:"
	@echo "  make verify CELL_MODULE=cells/sg13g2_nand2_1.py NETLIST=nand2.spice"
	@echo "  make netlist CELL_MODULE=cells/my_cell.py SPICE=my_cell.spice"
	@echo "  make selfcheck CELL_MODULE=build/layout/iteration_0/cell.py RUNS_DIR=build"
	@echo "  make test"
