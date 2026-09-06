#!/usr/bin/env bash
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Description:               Run one command inside the EDA container,
#                             always from this tool's directory.
# ================================================================
#
# Every containerised step of this tool goes through here, so there is exactly
# one place that knows the container name and the mount point.  The command is
# executed with the working directory set to this tool's directory inside the
# container, which means every path handed to it may be written relative to
# tools/aion_layout_claude -- the same spelling that works on the host.
set -euo pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$TOOL_DIR/../.." && pwd)"
REL_TOOL_DIR="${TOOL_DIR#"$REPO_ROOT"/}"

CONTAINER="${AION_CONTAINER:-iic-osic-tools_shell_uid_1000}"
MOUNT="${AION_CONTAINER_MOUNT:-/foss/designs/aion_flow}"
RUN_DIR="$MOUNT/$REL_TOOL_DIR"

if [ "$#" -eq 0 ]; then
    echo "usage: $0 <command ...>" >&2
    exit 3
fi

if ! docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true; then
    echo "docker_run.sh: container '$CONTAINER' is not running." >&2
    echo "docker_run.sh: start the iic-osic-tools container, or set AION_CONTAINER." >&2
    exit 4
fi

DOCKER_FLAGS="-i"
if [ -t 1 ]; then
    DOCKER_FLAGS="-it"
fi

exec docker exec ${DOCKER_FLAGS} -u "$(id -u):$(id -g)" "$CONTAINER" \
    bash -lc "export PDK=ihp-sg13g2; export PDK_ROOT=/foss/pdks; export AION_IN_DOCKER=1; \
        cd '${RUN_DIR}' && $*"
