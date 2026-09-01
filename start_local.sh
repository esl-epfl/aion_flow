#!/bin/bash
# ========================================================================
# Start script for ICD@JKU docker images (shell)
#
# SPDX-FileCopyrightText: 2022-2026 Harald Pretl and Georg Zachl
# Johannes Kepler University, Department for Integrated Circuits
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# SPDX-License-Identifier: Apache-2.0
# ========================================================================
#
# Generalized launcher: everything that used to be a hardwired path is now
# either a command-line flag or an environment variable. Run with -h/--help
# for the full option list, or see the "Running the EDA docker container"
# section in README.md for a walkthrough.

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

# Extra host directories to bind-mount, each as "host_path:container_name".
declare -a MOUNTS=()

usage() {
    cat <<EOF
Usage: ${SCRIPT_NAME} [OPTIONS]

Starts (or resumes) the ICD@JKU EDA docker/podman container used to run
the open-source ASIC tools (Xschem, Magic, KLayout, ngspice, Yosys,
OpenROAD, OpenSTA, Netgen, LibreLane, cocotb, ...).

Every design repository the container should see must be bind-mounted
explicitly with --mount; nothing is mounted by default except an empty
base "designs" directory.

Options:
  -d, --designs-dir DIR       Base directory mounted at /foss/designs
                               (default: \$HOME/eda/designs, created if
                               missing). Individual --mount entries are
                               layered inside /foss/designs alongside it.
  -m, --mount HOST[:NAME]     Bind-mount HOST (a host directory, e.g. a
                               repo checkout) into the container at
                               /foss/designs/NAME. NAME defaults to the
                               basename of HOST. Repeatable: pass -m
                               once per repo you want visible inside the
                               container.
  -u, --docker-user NAME      Docker Hub user/org owning the image
                               (default: hpretl, or \$DOCKER_USER).
  -i, --image NAME            Image name (default: iic-osic-tools, or
                               \$DOCKER_IMAGE).
  -t, --tag TAG                Image tag (default: latest, or \$DOCKER_TAG).
  -r, --registry REGISTRY      Registry prefix, e.g. docker.io (default:
                               \$DOCKER_REGISTRY, or docker.io). Pass an
                               empty string to use an unqualified image
                               name: --registry ""
  -e, --engine docker|podman   Container engine (default: auto-detected;
                               docker preferred, then podman).
  -n, --name NAME              Container name (default:
                               iic-osic-tools_shell_uid_<your uid>).
      --container-user ID      UID to run as inside the container
                               (default: 0, i.e. root).
      --container-group ID     GID to run as inside the container
                               (default: 0).
  -h, --help                    Show this help and exit.

Every flag has an equivalent environment variable (DESIGNS, DOCKER_USER,
DOCKER_IMAGE, DOCKER_TAG, DOCKER_REGISTRY, CONTAINER_ENGINE,
CONTAINER_NAME, CONTAINER_USER, CONTAINER_GROUP) for scripting; flags
take precedence when both are set. Set DRY_RUN=1 to print the docker/
podman commands instead of running them.

Example (mount this repo plus a sibling design repo):
  ./${SCRIPT_NAME} \\
      --mount "\$(pwd)" \\
      --mount ../SG13G2_ASIC-Design-FLL

See README.md for a full "for dummies" walkthrough.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        -d|--designs-dir)
            DESIGNS="$2"
            shift 2
            ;;
        -m|--mount)
            MOUNTS+=("$2")
            shift 2
            ;;
        -u|--docker-user)
            DOCKER_USER="$2"
            shift 2
            ;;
        -i|--image)
            DOCKER_IMAGE="$2"
            shift 2
            ;;
        -t|--tag)
            DOCKER_TAG="$2"
            shift 2
            ;;
        -r|--registry)
            DOCKER_REGISTRY="$2"
            shift 2
            ;;
        -e|--engine)
            CONTAINER_ENGINE="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --container-user)
            CONTAINER_USER="$2"
            shift 2
            ;;
        --container-group)
            CONTAINER_GROUP="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "[ERROR] Unknown argument: $1"
            echo
            usage
            exit 1
            ;;
    esac
done

if [ -n "${DRY_RUN:-}" ]; then
    echo "[INFO] This is a dry run, all commands will be printed to the shell (Commands printed but not executed are marked with $)!"
    ECHO_IF_DRY_RUN="echo $"
fi

# Select the container engine (Docker or Podman), can be overridden by
# setting CONTAINER_ENGINE or passing --engine.
if [ -z ${CONTAINER_ENGINE+z} ]; then
    if command -v docker >/dev/null 2>&1; then
        CONTAINER_ENGINE="docker"
    elif command -v podman >/dev/null 2>&1; then
        CONTAINER_ENGINE="podman"
    else
        echo "[ERROR] No container engine found, please install Docker or Podman!"
        exit 1
    fi
    [ -z "${IIC_OSIC_TOOLS_QUIET:-}" ] && echo "[INFO] Container engine auto-set to ${CONTAINER_ENGINE}."
fi

# Detect Podman rootless mode on Linux (the docker CLI can also be the
# podman-docker alias, so check the version string).
if [[ "$OSTYPE" == "linux"* ]] && ${CONTAINER_ENGINE} --version 2>/dev/null | grep -qi "podman"; then
    if ${CONTAINER_ENGINE} info --format '{{.Host.Security.Rootless}}' 2>/dev/null | grep -qi "true"; then
        ENGINE_IS_ROOTLESS=1
        [ -z "${IIC_OSIC_TOOLS_QUIET:-}" ] && echo "[INFO] Podman rootless mode detected."
    fi
fi

# Base "designs" directory mounted at /foss/designs. Set with -d/--designs-dir
# or the DESIGNS env var. Individual repos are layered inside it via --mount.
if [ -z ${DESIGNS+z} ]; then
    DESIGNS="$HOME/eda/designs"
    if [ ! -d "$DESIGNS" ]; then
        ${ECHO_IF_DRY_RUN:-} mkdir -p "$DESIGNS"
    fi
    [ -z "${IIC_OSIC_TOOLS_QUIET:-}" ] && echo "[INFO] Design directory auto-set to $DESIGNS."
fi

if [ -z ${DOCKER_USER+z} ]; then
    DOCKER_USER="hpretl"
fi

if [ -z ${DOCKER_IMAGE+z} ]; then
    DOCKER_IMAGE="iic-osic-tools"
fi

if [ -z ${DOCKER_TAG+z} ]; then
    DOCKER_TAG="latest"
fi

# Fully qualify the image name (Podman does not resolve short names
# non-interactively); set DOCKER_REGISTRY="" to use unqualified names.
if [ -z ${DOCKER_REGISTRY+z} ]; then
    DOCKER_REGISTRY="docker.io"
fi
if [ -n "${DOCKER_REGISTRY}" ]; then
    IMAGE_NAME="${DOCKER_REGISTRY}/${DOCKER_USER}/${DOCKER_IMAGE}:${DOCKER_TAG}"
else
    IMAGE_NAME="${DOCKER_USER}/${DOCKER_IMAGE}:${DOCKER_TAG}"
fi

# Shell starts as root per default.
if [ -z ${CONTAINER_USER+z} ]; then
    CONTAINER_USER="0"
fi

if [ -z ${CONTAINER_GROUP+z} ]; then
    CONTAINER_GROUP="0"
fi

if [ -z ${CONTAINER_NAME+z} ]; then
    CONTAINER_NAME="iic-osic-tools_shell_uid_"$(id -u)
fi

if [ -z ${DISP+z} ]; then
    DISP="${DISPLAY:-:0}"
fi

# Display / Wayland support
DISPLAY_PARAMS=""

# X11 support
if [ -n "${DISPLAY:-}" ]; then
    DISPLAY_PARAMS="${DISPLAY_PARAMS} -e DISPLAY=${DISPLAY}"
    DISPLAY_PARAMS="${DISPLAY_PARAMS} -v /tmp/.X11-unix:/tmp/.X11-unix:rw"
fi

# Wayland support
if [ -n "${WAYLAND_DISPLAY:-}" ] && [ -n "${XDG_RUNTIME_DIR:-}" ]; then
    WAYLAND_SOCKET="${XDG_RUNTIME_DIR}/${WAYLAND_DISPLAY}"

    if [ -S "${WAYLAND_SOCKET}" ]; then
        [ -z "${IIC_OSIC_TOOLS_QUIET:-}" ] && echo "[INFO] Wayland display detected: ${WAYLAND_DISPLAY}"

        DISPLAY_PARAMS="${DISPLAY_PARAMS} -e WAYLAND_DISPLAY=${WAYLAND_DISPLAY}"
        DISPLAY_PARAMS="${DISPLAY_PARAMS} -e XDG_RUNTIME_DIR=/tmp/runtime"
        DISPLAY_PARAMS="${DISPLAY_PARAMS} -e QT_QPA_PLATFORM=wayland;xcb"
        DISPLAY_PARAMS="${DISPLAY_PARAMS} -e GDK_BACKEND=wayland,x11"
        DISPLAY_PARAMS="${DISPLAY_PARAMS} -v ${WAYLAND_SOCKET}:/tmp/runtime/${WAYLAND_DISPLAY}"
    fi
fi

# GPU acceleration
if [ -d /dev/dri ]; then
    DISPLAY_PARAMS="${DISPLAY_PARAMS} --device /dev/dri"
fi

# Check for UIDs and GIDs below 1000, except 0 (root)
if [[ ${CONTAINER_USER} -ne 0 ]] && [[ ${CONTAINER_USER} -lt 1000 ]]; then
    prt_str="# [WARNING] Selected User ID ${CONTAINER_USER} is below 1000. This ID might interfere with User-IDs inside the container and cause undefined behavior! #"
    printf -- '#%.0s' $(seq 1 ${#prt_str})
    echo
    echo "${prt_str}"
    printf -- '#%.0s' $(seq 1 ${#prt_str})
    echo
fi

if [[ ${CONTAINER_GROUP} -ne 0 ]] && [[ ${CONTAINER_GROUP} -lt 1000 ]]; then
    prt_str="# [WARNING] Selected Group ID ${CONTAINER_GROUP} is below 1000. This ID might interfere with Group-IDs inside the container and cause undefined behavior! #"
    printf -- '#%.0s' $(seq 1 ${#prt_str})
    echo
    echo "${prt_str}"
    printf -- '#%.0s' $(seq 1 ${#prt_str})
    echo
fi

# Fixed potential errors in the container due to reduced access to syscalls.
DOCKER_EXTRA_PARAMS="--security-opt seccomp=unconfined ${DOCKER_EXTRA_PARAMS:-}"

# In Podman rootless mode, keep the host UID/GID inside the container so
# bind-mounted files keep their ownership (see README section 5.1). Not
# needed for the default root shell, where container root maps to the host
# user anyway.
if [ -n "${ENGINE_IS_ROOTLESS:-}" ] && [ "${CONTAINER_USER}" != "0" ]; then
    if ! echo "${DOCKER_EXTRA_PARAMS}" | grep -q "userns"; then
        [ -z "${IIC_OSIC_TOOLS_QUIET:-}" ] && echo "[INFO] Adding --userns=keep-id for Podman rootless mode."
        DOCKER_EXTRA_PARAMS="${DOCKER_EXTRA_PARAMS} --userns=keep-id"
    fi
fi

if [ -n "${IIC_OSIC_TOOLS_QUIET:-}" ]; then
    DOCKER_EXTRA_PARAMS="${DOCKER_EXTRA_PARAMS} -e IIC_OSIC_TOOLS_QUIET=1"
fi

# Build one -v flag per --mount entry, mounted at /foss/designs/<name>.
# HOST[:NAME] -> -v HOST:/foss/designs/NAME:rw  (NAME defaults to basename(HOST))
MOUNT_PARAMS=""
for entry in "${MOUNTS[@]+"${MOUNTS[@]}"}"; do
    host_path="${entry%%:*}"
    if [[ "${entry}" == *:* ]]; then
        mount_name="${entry#*:}"
    else
        mount_name=""
    fi

    if [ -z "${host_path}" ]; then
        echo "[ERROR] Empty host path in --mount \"${entry}\"."
        exit 1
    fi
    if [ ! -d "${host_path}" ]; then
        echo "[ERROR] --mount host path does not exist or is not a directory: ${host_path}"
        exit 1
    fi
    # Resolve to an absolute path so it also works from other directories.
    host_path="$(cd "${host_path}" && pwd)"

    if [ -z "${mount_name}" ]; then
        mount_name="$(basename "${host_path}")"
    fi

    [ -z "${IIC_OSIC_TOOLS_QUIET:-}" ] && echo "[INFO] Mounting ${host_path} -> /foss/designs/${mount_name}"
    MOUNT_PARAMS="${MOUNT_PARAMS} -v ${host_path}:/foss/designs/${mount_name}:rw"
done

# Check if the container exists and if it is running.
if [ "$(${CONTAINER_ENGINE} ps -q -f name="${CONTAINER_NAME}")" ]; then
    echo "[WARNING] Container is running!"
    echo "[HINT] It can also be stopped with \"${CONTAINER_ENGINE} stop ${CONTAINER_NAME}\" and removed with \"${CONTAINER_ENGINE} rm ${CONTAINER_NAME}\" if required."
    echo
    echo -n "Press \"s\" to stop, and \"r\" to stop & remove: "
    read -r -n 1 k </dev/tty
    echo
    if [[ $k = s ]]; then
        ${ECHO_IF_DRY_RUN:-} "${CONTAINER_ENGINE}" stop "${CONTAINER_NAME}"
    elif [[ $k = r ]]; then
        ${ECHO_IF_DRY_RUN:-} "${CONTAINER_ENGINE}" stop "${CONTAINER_NAME}"
        ${ECHO_IF_DRY_RUN:-} "${CONTAINER_ENGINE}" rm "${CONTAINER_NAME}"
    fi
# If the container exists but is exited, it is restarted.
elif [ "$(${CONTAINER_ENGINE} ps -aq -f name="${CONTAINER_NAME}")" ]; then
    echo "[WARNING] Container ${CONTAINER_NAME} exists."
    echo "[HINT] It can also be restarted with \"${CONTAINER_ENGINE} start ${CONTAINER_NAME}\" or removed with \"${CONTAINER_ENGINE} rm ${CONTAINER_NAME}\" if required."
    echo
    echo -n "Press \"s\" to start, and \"r\" to remove: "
    read -r -n 1 k </dev/tty
    echo
    if [[ $k = s ]]; then
        ${ECHO_IF_DRY_RUN:-} "${CONTAINER_ENGINE}" start -a -i "${CONTAINER_NAME}"
    elif [[ $k = r ]]; then
        ${ECHO_IF_DRY_RUN:-} "${CONTAINER_ENGINE}" rm "${CONTAINER_NAME}"
    fi
else
    [ -z "${IIC_OSIC_TOOLS_QUIET:-}" ] && echo "[INFO] Container does not exist, creating ${CONTAINER_NAME} ..."
    if [ -z "${MOUNTS[*]+set}" ]; then
        echo "[WARNING] No --mount given: only the empty base directory ${DESIGNS} will be visible inside the container."
        echo "[HINT] Pass one or more --mount HOST_DIR flags to make your design repos visible, e.g.:"
        echo "         ./${SCRIPT_NAME} --mount \"\$(pwd)\""
    fi
    # Finally, run the container, and set DISPLAY to the local display number
    #${ECHO_IF_DRY_RUN} "${CONTAINER_ENGINE}" pull "${IMAGE_NAME}"
    # Disable SC2086, $PARAMS must be globbed and splitted.
    # shellcheck disable=SC2086
    echo "[INFO] THIS SCRIPT ALLOWS FOR UI CONTENT (CUSTOM MODIFICATION)"
    ${ECHO_IF_DRY_RUN:-} "${CONTAINER_ENGINE}" run -it \
        --name "${CONTAINER_NAME}" \
        --user "${CONTAINER_USER}:${CONTAINER_GROUP}" \
        ${DISPLAY_PARAMS} \
        $DOCKER_EXTRA_PARAMS \
        -v "${DESIGNS}":"/foss/designs":rw \
        ${MOUNT_PARAMS} \
        "${IMAGE_NAME}" \
        -s /bin/bash
fi
