# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Updated:                   2026-08-30
#  Description:               AION layout tool — minimal local interface
# ================================================================

# Paths (override from the command line).
CELL_MODULE  ?= cells/sg13g2_nand2_1.py
CELL_NAME    ?= $(basename $(notdir $(CELL_MODULE)))
SPICE        ?= $(CELL_NAME).spice
NETLIST      ?= $(CELL_NAME).spice
RUNS_DIR     ?= build
GDS_FILE      = $(RUNS_DIR)/$(CELL_NAME).gds
DRC_RUN_DIR   = $(RUNS_DIR)/drc/$(CELL_NAME)
LVS_RUN_DIR   = $(RUNS_DIR)/lvs/$(CELL_NAME)
RUN_SCRIPT   ?= scripts/docker_run.sh

.PHONY: gds drc lvs verify netlist doc gds2py clean help

# Generate the GDS for CELL_MODULE.
gds:
	mkdir -p $(RUNS_DIR)
	python3 scripts/generate_cell.py $(CELL_MODULE) $(GDS_FILE)

# Run KLayout DRC on the generated GDS.
drc: gds
	mkdir -p $(DRC_RUN_DIR)
	$(RUN_SCRIPT) sak-drc.sh -d -b -l macro -w $(DRC_RUN_DIR) $(GDS_FILE)

# Run LVS against the provided SPICE netlist.
lvs: gds
	mkdir -p $(LVS_RUN_DIR)
	$(RUN_SCRIPT) sak-lvs.sh -d -b -w $(LVS_RUN_DIR) -s $(NETLIST) -l $(GDS_FILE) -c $(CELL_NAME)

# Run gds + drc + lvs and print a one-page summary.
verify: gds drc lvs
	python3 scripts/report_verification.py \
		--cell $(CELL_NAME) --gds $(GDS_FILE) --netlist $(NETLIST) --runs-dir $(RUNS_DIR) --parse-only

# Scaffold a new cell generator from a SPICE netlist.
netlist:
	python3 scripts/generate_from_netlist.py $(SPICE) -o $(CELL_MODULE)

# Generate markdown documentation for a verified cell.
doc:
	python3 scripts/generate_cell_doc.py \
		--cell-module $(CELL_MODULE) --netlist $(NETLIST) -o $(RUNS_DIR)/$(CELL_NAME).md --runs-dir $(RUNS_DIR)

# Convert an existing GDS into a Python generator.
gds2py:
	python3 scripts/gds_to_python.py $(GDS_FILE) -o $(CELL_MODULE)

# Remove all generated artifacts.
clean:
	rm -rf $(RUNS_DIR)

flow:
	./orchestrate.sh AION_inv_nand2_nor2_1_minimized.spice build 10

# Show usage.
help:
	@echo "Usage: make <target> CELL_MODULE=<path/to/cell.py> [NETLIST=<netlist>]"
	@echo ""
	@echo "Targets:"
	@echo "  gds     Generate $(RUNS_DIR)/<CELL_NAME>.gds"
	@echo "  drc     Run DRC on the generated GDS"
	@echo "  lvs     Run LVS against NETLIST"
	@echo "  verify  Run gds + drc + lvs"
	@echo "  netlist Scaffold CELL_MODULE from SPICE"
	@echo "  doc     Generate $(RUNS_DIR)/<CELL_NAME>.md"
	@echo "  gds2py  Convert GDS to CELL_MODULE"
	@echo "  clean   Remove $(RUNS_DIR)/"
	@echo ""
	@echo "Examples:"
	@echo "  make verify CELL_MODULE=cells/sg13g2_nand2_1.py NETLIST=nand2.spice"
	@echo "  make netlist CELL_MODULE=cells/my_cell.py SPICE=my_cell.spice"
