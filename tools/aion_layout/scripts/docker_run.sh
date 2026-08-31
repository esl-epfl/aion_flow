#!/usr/bin/env bash
set -euo pipefail

HOST_PWD="${HOST_PWD:-$PWD}"
REL_RUN_DIR="$(pwd)"
if [[ "$REL_RUN_DIR" = "$HOST_PWD"* ]]; then
    REL_RUN_DIR="${REL_RUN_DIR#$HOST_PWD}"
    REL_RUN_DIR="${REL_RUN_DIR#/}"
fi
RUN_DIR="/foss/designs/aion_flow${REL_RUN_DIR:+/}$REL_RUN_DIR"

CMD="${1:-}"

if [ "$CMD" = "librelane" ]; then
    CONFIG_REL="${2:?config path required for librelane}"
    shift 2
    ARGS="$CMD $CONFIG_REL $*"
else
    ARGS="$*"
fi

DOCKER_FLAGS="-i"
if [ -t 1 ]; then
    DOCKER_FLAGS="-it"
fi

exec docker exec ${DOCKER_FLAGS} -u "$(id -u):$(id -g)" iic-osic-tools_shell_uid_1000 \
    bash -lc "export PDK=ihp-sg13g2; export AION_IN_DOCKER=1; cd ${RUN_DIR} && \
        printf '\n\033[1;36m========== AION CONTAINER OUTPUT ==========\033[0m\n\n' && \
        ${ARGS}"
