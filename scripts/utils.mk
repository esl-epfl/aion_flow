# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-11 23:17:17
#  Updated:                   2026-08-27 16:23:36
#  Description:               Utils Makefile
# ================================================================

RTL_ROOT ?=

# ==============================================================================
# Color Definitions for Terminal Output
# ==============================================================================
C_RESET = \033[0m
C_BOLD  = \033[1m
C_CYAN  = \033[36m
C_GREEN = \033[32m
C_YELLO = \033[33m
C_MAGEN = \033[35m

.PHONY: help
help:	
	@echo ""
	@echo "========================================================================"
	@echo "  AION Flow - Command Center"
	@echo "========================================================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?##/ {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2} /^##@/ {printf "\n\033[1;34m%s\033[0m\n", substr($$0, 5)}' $(MAKEFILE_LIST)
	@echo ""

help_no_color:
	@awk 'BEGIN {FS = ":.*?## "; printf "  %-24s %s\n  %-24s %s\n", "COMMAND", "DESCRIPTION", "-------", "-----------"} \
		/^[a-zA-Z_-]+:.*?##/ {printf "  %-24s %s\n", $$1, $$2} \
		/^##@/ {printf "\n  ─── %s ──────────────────────────────────────────\n", substr($$0, 5)}' $(MAKEFILE_LIST)
	@echo ""

