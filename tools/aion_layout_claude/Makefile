# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The human-facing front door to the flow
# ================================================================
#
# Every target is one call to `python3 -m aion_layout`, and nothing else.  The
# CLI owns the logic; this file owns the paths.  That is the point: a target
# that composed several steps in shell would be a second implementation of the
# flow, free to disagree with the one the CLI runs, and the two would drift.
#
# The CLI exits 0 PASS/WIN, 1 FAIL/LOSS, 2 ERROR, and make stops on any of the
# non-zero ones -- so `make verify` failing *is* the verdict, and there is
# deliberately no `-` prefix or `|| true` anywhere below.  GNU make reports its
# own failure as status 2 whatever the recipe returned, so FAIL and ERROR are
# told apart by the verdict line, or by running the CLI command directly; the
# recipes are not @-silenced precisely so that command can be copied off the
# screen and re-run by hand.

# ---- What is being built.  Override any of these on the command line. -------
CELL          ?= AION_inv_nand2_nor2_1
CELL_MODULE   ?= cells/$(CELL).py
# The worked example's transistor-level netlist is not named $(CELL).spice, so
# it is spelled out; for any other cell override NETLIST along with CELL.
NETLIST       ?= AION_inv_nand2_nor2_1_minimized.spice
# The same logic as the PDK standard cells it replaces -- what CELL must beat.
BASELINE      ?= AION_inv_nand2_nor2.spice

# `make resize` widens the series stacks of NETLIST and writes a NEW cell here;
# it never edits NETLIST, because that file is what LVS grades the layout
# against.  MIN_DEPTH leaves stacks this deep and shallower alone -- the PDK
# does not widen 2-high stacks either, so a cell that did would be the odd one
# out in the library it has to live beside.
RESIZED       ?= $(CELL)s.spice
MIN_DEPTH     ?= 2

# ---- Where it is built. -----------------------------------------------------
BUILD_DIR     ?= build/$(CELL)
FINAL_DIR     ?= $(BUILD_DIR)/final
BASELINE_DIR  ?= $(BUILD_DIR)/baseline
CHAR_DIR      ?= $(BUILD_DIR)/char
GDS           ?= $(BUILD_DIR)/$(CELL).gds
PNG           ?= $(BUILD_DIR)/$(CELL).png
PEX_DIR       ?= $(BUILD_DIR)/pex

# ---- How it is built. -------------------------------------------------------
# The corner set `flow` characterizes over: typ is the typical corner alone,
# all adds slow and fast.  It applies to `make flow` only -- the standalone
# `characterize` target takes characterize.DEFAULT_CORNERS (all three), and
# spelling those out here would duplicate the PDK section names this Makefile
# has no business knowing.  Override them per run with `--corner` if needed.
CORNERS       ?= typ
JOBS          ?= 8
PYTHON        ?= python3
PYTEST        ?= $(PYTHON) -m pytest
AION           = $(PYTHON) -m aion_layout

# ---- Comparison inputs. -----------------------------------------------------
# Recursively expanded on purpose: the wildcards are evaluated when the compare
# target runs, which is after characterize has written the files they match.
BASELINE_CELL  ?= $(basename $(notdir $(BASELINE)))
# export takes every corner; compare takes one, and it has to be the typical
# one on both sides or the two halves are not the same measurement.
CANDIDATE_LIBS ?= $(wildcard $(CHAR_DIR)/*.lib)
BASELINE_LIBS  ?= $(wildcard $(BASELINE_DIR)/char/*.lib)
CANDIDATE_LIB  ?= $(firstword $(wildcard $(CHAR_DIR)/*_typ_*.lib) $(CANDIDATE_LIBS))
BASELINE_LIB   ?= $(firstword $(wildcard $(BASELINE_DIR)/char/*_typ_*.lib) $(BASELINE_LIBS))
# The extractor's file name is its own business, so the netlist is found rather
# than assumed; the guard below turns "found nothing" into a stop, not into a
# command line with an empty argument in it.
PEX_SPICE      ?= $(firstword $(wildcard $(PEX_DIR)/$(CELL)_pex*.spice) \
                             $(wildcard $(PEX_DIR)/*.spice))
BASELINE_GDS   ?= $(BASELINE_DIR)/$(BASELINE_CELL).gds
# No --candidate-lef/--baseline-lef here on purpose: both areas then come
# from the same source (the prBoundary), and an area comparison whose two
# halves were measured differently would decide the result by accident.

# The package is importable straight from the checkout; there is no install
# step to get out of date with the source.
export PYTHONPATH := $(CURDIR)$(if $(PYTHONPATH),:$(PYTHONPATH))

.DEFAULT_GOAL := help
.PHONY: help scaffold gds png drc lvs verify pex evidence baseline \
        characterize compare export flow test clean

help: ## Show this help and the current variable values
	@echo "usage: make <target> [CELL=... NETLIST=... BASELINE=... BUILD_DIR=...]"
	@echo ""
	@echo "targets:"
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-13s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "current settings:"
	@echo "  CELL          = $(CELL)"
	@echo "  CELL_MODULE   = $(CELL_MODULE)"
	@echo "  NETLIST       = $(NETLIST)"
	@echo "  BASELINE      = $(BASELINE)"
	@echo "  BUILD_DIR     = $(BUILD_DIR)"
	@echo "  FINAL_DIR     = $(FINAL_DIR)"
	@echo "  CORNERS       = $(CORNERS)   JOBS = $(JOBS)"
	@echo ""
	@echo "exit status: 0 PASS/WIN, 1 FAIL/LOSS, 2 ERROR (the step could not run)"

resize: ## Widen NETLIST's series stacks into RESIZED, area-capped by BASELINE
	@mkdir -p $(BUILD_DIR)
	$(AION) resize $(NETLIST) -o $(RESIZED) --cell $(CELL) \
		--baseline $(BASELINE) --min-depth $(MIN_DEPTH) \
		--report $(BUILD_DIR)/$(CELL).resize.md

scaffold: ## Write CELL_MODULE from NETLIST
	$(AION) scaffold $(NETLIST) -o $(CELL_MODULE) --cell $(CELL)

gds: ## Build BUILD_DIR/CELL.gds from CELL_MODULE
	$(AION) build $(CELL_MODULE) --cell $(CELL) -o $(GDS)

png: ## Build the GDS and render it to BUILD_DIR/CELL.png
	$(AION) build $(CELL_MODULE) --cell $(CELL) -o $(GDS) --png $(PNG)

drc: gds ## Run Magic + KLayout DRC on the GDS
	$(AION) drc $(GDS) -w $(BUILD_DIR)/drc --cell $(CELL)

lvs: gds ## Run Magic + Netgen LVS of the GDS against NETLIST
	$(AION) lvs $(GDS) $(NETLIST) --cell $(CELL) -w $(BUILD_DIR)/lvs

verify: ## Build + DRC + LVS and print RESULT: PASS|FAIL|ERROR
	$(AION) verify $(CELL_MODULE) --cell $(CELL) --netlist $(NETLIST) \
		-w $(BUILD_DIR) --report $(BUILD_DIR)/$(CELL).report.md

pex: gds ## Extract parasitics from the GDS into PEX_DIR
	$(AION) pex $(GDS) --cell $(CELL) -w $(PEX_DIR)

evidence: ## Write the evidence packet for CELL into BUILD_DIR
	$(AION) evidence --cell $(CELL) --netlist $(NETLIST) \
		--gds $(GDS) --module $(CELL_MODULE) \
		-o $(BUILD_DIR)/$(CELL).evidence.md

baseline: ## Abut the PDK cells of BASELINE, then DRC + LVS + PEX + characterize
	$(AION) baseline $(BASELINE) -o $(BASELINE_DIR) \
		--verify --pex --characterize

characterize: ## Characterize CELL from its PEX netlist into CHAR_DIR
	@test -n "$(PEX_SPICE)" || { echo "no PEX netlist in $(PEX_DIR); run 'make pex' first" >&2; exit 2; }
	$(AION) characterize $(PEX_SPICE) --cell $(CELL) \
		-o $(CHAR_DIR) --jobs $(JOBS) --area-gds $(GDS)

compare: ## Compare CELL against BASELINE_CELL; prints COMPARE: WIN|LOSS
	@test -n "$(CANDIDATE_LIB)" || { echo "no Liberty in $(CHAR_DIR); run 'make characterize' first" >&2; exit 2; }
	@test -n "$(BASELINE_LIB)"  || { echo "no Liberty in $(BASELINE_DIR)/char; run 'make baseline' first" >&2; exit 2; }
	$(AION) compare --cell $(CELL) --baseline-cell $(BASELINE_CELL) \
		--candidate-lib $(CANDIDATE_LIB) --baseline-lib $(BASELINE_LIB) \
		--candidate-gds $(GDS) --baseline-gds $(BASELINE_GDS) \
		--json $(BUILD_DIR)/$(CELL).compare.json \
		--markdown $(BUILD_DIR)/$(CELL).compare.md

# --pex-spice is passed only when a PEX netlist was found: an empty PEX_DIR
# would otherwise expand to a bare `--pex-spice -o DIR`, and argparse would
# answer a missing file with a usage error instead of a named one.  The pin
# list then comes from the schematic netlist, which is what exporters does
# without it anyway.
export: ## Write the gds/lef/lib/v/spice/cdl views into FINAL_DIR
	@test -n "$(CANDIDATE_LIBS)" || { echo "no Liberty in $(CHAR_DIR); run 'make characterize' first" >&2; exit 2; }
	$(AION) export --cell $(CELL) --gds $(GDS) --spice $(NETLIST) \
		$(foreach lib,$(CANDIDATE_LIBS),--lib $(lib)) \
		$(if $(PEX_SPICE),--pex-spice $(PEX_SPICE)) -o $(FINAL_DIR)

flow: ## Run the whole chain: verify, pex, baseline, characterize, export, compare
	$(AION) flow $(NETLIST) --cell $(CELL) --module $(CELL_MODULE) \
		--baseline $(BASELINE) -o $(BUILD_DIR) \
		--corners $(CORNERS) --jobs $(JOBS)

test: ## Run the host-side test suite (no container, no PDK)
	$(PYTEST) tests/ -q

clean: ## Remove BUILD_DIR
	rm -rf $(BUILD_DIR)
