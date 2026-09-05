#!/bin/bash
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Updated:                   2026-09-03
#  Description:               Agentic DRC/LVS fix loop for AION standard cells
# ================================================================
#
# orchestrate.sh — v5.0
#
# ONE RUNG PER TURN.  The loop does not ask for a finished cell.  It derives a
# ladder from the netlist (scripts/curriculum.py), finds the lowest rung the
# measured score does not clear, and asks for that one thing -- showing only the
# evidence that rung declares.  Measured, a whole-cell objective produced 64,167
# characters of reasoning and zero output; one rung produced a module that
# builds.  Every rung's exit test is a predicate over the same Score the ledger
# records, so the curriculum and the grader cannot drift apart, and every one of
# them fails closed: a rung whose measurement is missing has not been cleared.
#
# The loop also stops advancing unconditionally.  Each iteration is scored the
# moment it is graded, the best score is remembered, and an iteration that
# scores worse is rejected -- the next call branches from the best module
# instead, via .base_iteration.  Nothing is copied to do it; the artifacts are
# still on disk where they were written.
#
# Deterministic pipeline steps (GDS gen, render, DRC, LVS, report) run as
# plain bash — no agent involved, so nothing there can hang on a tool
# permission prompt or loop on a repeated tool call.
#
# The agent-facing half PUSHES evidence instead of asking the model to pull it:
# the whole prompt is assembled host-side from the netlist, the raw verification
# artifacts and the current source, so the model never has to spend context
# discovering what went wrong.
#
# The thing being graded can reach the grader.  The model runs with an edit
# tool, a bash tool and --add-dir "$BUILD_DIR", and its workspace is the
# repository root, so state.json, the checkers and this script are all writable
# while the call is in flight.  Everything the verdict depends on is therefore
# snapshotted OUTSIDE $BUILD_DIR before the call and verified after it, from a
# trap so an interrupted run cannot leave a forged verdict behind.  A modified
# grader is restored, named in a loud banner and recorded in state.json — never
# a reason to abort the run, because an attempt to edit the grader is the most
# interesting measurement the run can make and losing the run loses it.
#
# Two rules govern everything below:
#   * FAIL CLOSED.  A verdict, an artifact or an evidence packet that is absent,
#     empty, truncated or merely not positively confirmed is not clean.
#   * NOTHING MODEL-INFLUENCED BECOMES A VERDICT.  What lands in state.json is
#     read from the report this host wrote, before the model was invoked, and
#     normalised to a fixed literal on the way in.
#
# Usage:
#   ./orchestrate.sh <SPICE_NETLIST> <BUILD_DIR> [MAX_ITERATIONS]
#
# Environment:
#   MODEL                    inference model id (see copilot-rcp.sh --list)
#   CEFPROVIDER_API_KEY      inference gateway key; required for a real run
#   FIX_TIMEOUT              wall-clock budget for one model call (default 12m)
#   MODEL_EFFORT             reasoning effort for the model call (default low).
#                            At the CLI default the whole completion budget goes
#                            to reasoning and the turn writes no code; see the
#                            measurements beside MODEL_EFFORT below.
#   AION_GATE                curriculum rung: "auto" (default) derives it from
#                            the measured score, a rung key forces one, "off"
#                            restores the pre-Stage-5 whole-cell objective
#   MAX_MODEL_CALLS          global model-call budget, build-gate retries
#                            included (default: MAX_ITERATIONS)
#   MAX_BUILD_FAILURES       build-gate retries allowed inside one iteration,
#                            each one spending from MAX_MODEL_CALLS (default 3)
#   HOST_BUILD_TIMEOUT       seconds the host build gate may spend running
#                            model-written code (default 300)
#   EVIDENCE_TIMEOUT         seconds the evidence packet may take, digest
#                            subprocess included (default 300)
#   MEMORY_INLINE_BYTES      bytes of memory.md inlined into the prompt
#   AION_DUMP_PROMPT=<path>  assemble the prompt, write it to <path>, exit — no
#                            model call, no docker, no guard, nothing else runs
#
# Requires: copilot-rcp.sh wrapper, jq, python3, timeout, cmp, mktemp.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/pipeline.sh"

SPICE_NETLIST="${1:?Usage: orchestrate.sh <SPICE_NETLIST> <BUILD_DIR> [MAX_ITERATIONS]}"
BUILD_DIR="${2:?Usage: orchestrate.sh <SPICE_NETLIST> <BUILD_DIR> [MAX_ITERATIONS]}"
MAX_ITERATIONS="${3:-10}"
# The default is measured, not chosen.  Same prompts, same gateway, same day:
#
#                        `gates` rung              `shorts` rung
#   Kimi-K2.7-Code   45 s, 13,024 ch reasoning   NEVER ANSWERS: 158,775 ch of
#                    -> a module that builds     reasoning at a 40,000-token
#                                                budget, zero content, and the
#                                                same at every smaller budget
#   gpt-oss-120b     13 s,  3,079 ch reasoning   28 s, 10,551 ch reasoning
#                    -> a module that builds     -> a module that builds AND
#                                                   clears the rung
#
# The `shorts` rung is the one the loop was stuck on for four iterations.  Kimi
# cannot close it -- not a budget problem, not a prompt problem; five separate
# interventions are recorded in SUMMARY.md, all measured, none of which helped.
# gpt-oss-120b answered it in 28 s on the first try, took the disconnected-node
# count 4 -> 0 and the unmatched ports 10 -> 1, and improved the score 4500 ->
# 3940.  It is also ~167 tok/s against ~90.
#
# Kimi remains selectable and is the better documented failure; Qwen3.5 fails on
# the whole-cell objective exactly as Kimi does and is untested per-rung.
MODEL="${MODEL:-openai/gpt-oss-120b}"
# MODEL="${MODEL:-moonshotai/Kimi-K2.7-Code}"
# MODEL="${MODEL:-Qwen/Qwen3.5-397B-A17B}"

COPILOT_RCP="${COPILOT_RCP:-/home/filippoquadri/phd/aion/copilot-rcp.sh}"
OPENCODE_RCP="${OPENCODE_RCP:-/home/filippoquadri/phd/aion/opencode-rcp.sh}"

# Which agent CLI drives the model.  Both are wired; copilot is the default
# because opencode does not currently run on this machine.
#
# Measured 2026-09-03, opencode 1.18.27: every invocation hangs at startup and
# is killed by the timeout.  With --print-logs --log-level DEBUG the last line
# is always `message=init`, after config load and after "all LSPs are
# disabled" -- it never opens a connection, so no request reaches the gateway.
# Reproduced identically with a 500-byte prompt and a 38 KB one, with the
# 2.35 GB session database and with a fresh XDG_DATA_HOME, with --pure, and
# with the original wrapper.  The gateway itself answers in 1s over curl and
# Kimi returns content in 1-3s, so the fault is local to opencode.
#
# Set AGENT_CLI=opencode to use it once that is fixed; nothing else changes.
AGENT_CLI="${AGENT_CLI:-copilot}"
case "$AGENT_CLI" in
copilot | opencode) ;;
*)
    echo "!! AGENT_CLI must be 'opencode' or 'copilot', got '${AGENT_CLI}'" >&2
    exit 2
    ;;
esac

# Absolute from here on: the guard, the trap and the container path helpers all
# need a path that does not move with the working directory.  A relative
# argument is repository-relative, which is what `make flow` passes.
SPICE_NETLIST="$(pipeline_abspath "$SPICE_NETLIST")"
BUILD_DIR="$(pipeline_abspath "$BUILD_DIR")"

STATE_FILE="${BUILD_DIR}/layout/state.json"
MEMORY_FILE="${BUILD_DIR}/memory.md"

# Wall-clock budget for one model call.  Re-derived from measurement against the
# gateway, not guessed:
#
#   End to end through copilot, Kimi-K2.7-Code, the `gates` rung of the fixture
#   cell (a 25 KB / ~6.3k-token prompt):
#       193 s  to write the module
#       208 s  to finish (module + a note to memory.md)
#   -> the module built, raised the poly/active crossings 6 -> 8, took the
#      device delta 2 -> 0, and advanced the curriculum from `gates` to `taps`.
#
#   But the rungs are not equally hard, and the reasoning scales with the rung:
#       gates  rung : 13,024 ch of reasoning -> answers in 45 s raw
#       shorts rung : 44,653 ch             -> exceeds a 12,000-token budget
#       pins   rung : 42,914 ch             -> exceeds a 12,000-token budget
#   At ~91 tok/s that is ~11k tokens, ~130 s of pure thinking before the first
#   character of output, and through copilot it is more: its own ~12.6k-token
#   system prompt is re-sent every turn.  A 6m budget was enough for `gates` and
#   NOT enough for `shorts` -- that turn produced no tool call at all.
#
# 12m is sized to the hardest rung measured, not the easiest.  It is still well
# under the 79 minutes copilot-rcp.sh's 262144-token output cap would allow (see
# SUMMARY.md), and a hung call still costs minutes rather than an hour.
#
# Note what this number cannot fix: an EXPLORING turn blows any budget.  The
# first run of this curriculum spent a whole 6m on two `ls` calls and a later one
# spent it reading GDS_PYTHON_API.md.  The fix for that is in the prompt -- write
# the module first, open nothing -- not in a bigger number here.
FIX_TIMEOUT="${FIX_TIMEOUT:-12m}"

# Reasoning effort for the model call.
#
# Read the measurements before changing this, because the obvious reading of
# them is wrong.  Same prompt (one rung, 11 KB), same model, measured directly
# against the gateway:
#
#     effort=default, max_tokens  4000 : reason 15,405 ch, content 0     length
#     effort=low,     max_tokens  8000 : reason 24,684 ch, content 2,933 stop
#     effort=DEFAULT, max_tokens  8000 : reason 13,024 ch, content 2,600 stop
#
# The third line is the control, and it is the important one: at the DEFAULT
# effort and the larger budget the model returns a clean module in 45 s.  So
# --reasoning-effort low did nothing -- on this gateway Kimi treats "low" and
# "minimal" exactly as it treats the default (a 34-token prompt returns 121
# characters of reasoning at all three).  The variable that mattered was the
# COMPLETION BUDGET: 4000 tokens is spent before the reasoning ends, 8000 is not.
#
# Only "none" actually suppresses reasoning, and it is a trap: the thinking does
# not disappear, it moves into the content channel, and the reply becomes 25 KB
# of prose with the module somewhere inside it.
#
# The flag is kept because it is free, it is honest about what was tried, and it
# matters for the other models on this gateway.  It is NOT what unblocked the
# loop.  What unblocked the loop is the curriculum: one rung needs ~3.2k tokens
# of reasoning where the whole cell needed more than 16k and never finished.
MODEL_EFFORT="${MODEL_EFFORT:-low}"

# The curriculum: which rung of the ladder this run asks for.  "auto" derives it
# from the measured score (scripts/curriculum.py), a rung key forces one, and
# "off" restores the pre-Stage-5 whole-cell objective and the whole packet.
AION_GATE="${AION_GATE:-auto}"
export AION_GATE

# Build-gate retries allowed inside one iteration.  Each one is a *model call*
# and spends from the global budget below: three silent retries used to burn
# three calls and thirty minutes while .current_iteration never moved and
# nothing durable recorded that it had happened.
MAX_BUILD_FAILURES="${MAX_BUILD_FAILURES:-3}"

# The single global budget every model call is charged against, whatever the
# reason for it.  Defaults to one call per iteration.
MAX_MODEL_CALLS="${MAX_MODEL_CALLS:-$MAX_ITERATIONS}"

# Model-written code runs on this host twice per iteration — once in the
# evidence packet's layout digest, once in the build gate.  Neither may run
# unbounded: `def generate(...): time.sleep(600)` used to stall the loop.
HOST_BUILD_TIMEOUT="${HOST_BUILD_TIMEOUT:-300}"
EVIDENCE_TIMEOUT="${EVIDENCE_TIMEOUT:-300}"

# Bytes of memory.md inlined into the prompt (tail — the most recent entries).
MEMORY_INLINE_BYTES="${MEMORY_INLINE_BYTES:-4000}"

# Written before every model call; scripts/selfcheck.sh reads it to report how
# much of the FIX_TIMEOUT budget is left.
DEADLINE_FILE="${BUILD_DIR}/layout/deadline.epoch"
export AION_DEADLINE_FILE="$DEADLINE_FILE"
export AION_BUILD_DIR="$BUILD_DIR"
export AION_ROOT="$SCRIPT_DIR"

# ---- Banner helper -------------------------------------------------------

print_banner() {
    local fg_color="$1"
    local text="$2"
    local reset="\033[0m"
    local bold="\033[1m"
    echo -e "${bold}${fg_color}"
    echo "========================================================================"
    echo "  ${text}"
    echo "========================================================================"
    echo -e "${reset}"
}

fatal() {
    print_banner "\033[31m" "ORCHESTRATION REFUSED TO START"
    echo "!! $*" >&2
    exit 2
}

# ---- argument and environment validation ---------------------------------

for tool in jq python3 timeout cmp mktemp; do
    command -v "$tool" >/dev/null 2>&1 || fatal "required tool not found: ${tool}"
done

case "$MAX_ITERATIONS" in '' | *[!0-9]*) fatal "MAX_ITERATIONS must be a positive integer, got '${MAX_ITERATIONS}'" ;; esac
case "$MAX_BUILD_FAILURES" in '' | *[!0-9]*) fatal "MAX_BUILD_FAILURES must be a positive integer, got '${MAX_BUILD_FAILURES}'" ;; esac
case "$MAX_MODEL_CALLS" in '' | *[!0-9]*) fatal "MAX_MODEL_CALLS must be a positive integer, got '${MAX_MODEL_CALLS}'" ;; esac
((MAX_ITERATIONS > 0)) || fatal "MAX_ITERATIONS must be > 0"
((MAX_BUILD_FAILURES > 0)) || fatal "MAX_BUILD_FAILURES must be > 0"
((MAX_MODEL_CALLS > 0)) || fatal "MAX_MODEL_CALLS must be > 0"

[[ -s "$SPICE_NETLIST" ]] || fatal "netlist missing or empty: ${SPICE_NETLIST}"

# The container mounts the repository and nothing else, so a build directory
# outside it is invisible to sak-drc.sh, to sak-lvs.sh and to the model's own
# self-check (scripts/selfcheck.sh refuses such a path outright).  Checked here
# rather than discovered eight minutes into the first DRC run.  Prompt-dump mode
# runs no container at all, so there it is a warning, not a refusal.
check_container_visible() {
    local label="$1" path="$2"
    pipeline_in_repo "$path" && return 0
    if [[ -n "${AION_DUMP_PROMPT:-}" ]]; then
        echo "!! WARNING: ${label} is outside ${PIPELINE_ROOT}: ${path}" >&2
        echo "!! WARNING: the container cannot see it; continuing only because this is prompt-dump mode." >&2
        return 0
    fi
    fatal "${label} is outside the repository (${PIPELINE_ROOT}): ${path}
   The verification container mounts the repository, so nothing there would be
   visible to sak-drc.sh, sak-lvs.sh or ./scripts/selfcheck.sh.  Use a path
   inside ${PIPELINE_ROOT}."
}

check_container_visible "BUILD_DIR" "$BUILD_DIR"
check_container_visible "SPICE_NETLIST" "$SPICE_NETLIST"

if ! CELL_NAME="$(grep -m1 -oP '(?<=\.subckt\s)\S+' "$SPICE_NETLIST")" || [[ -z "$CELL_NAME" ]]; then
    fatal "no '.subckt <name>' line in ${SPICE_NETLIST}; there is no cell to build"
fi
case "$CELL_NAME" in
[A-Za-z_]*) ;;
*) fatal "cell name '${CELL_NAME}' does not start with a letter or underscore" ;;
esac
case "$CELL_NAME" in
*[!A-Za-z0-9_]*) fatal "cell name '${CELL_NAME}' contains characters the tools reject" ;;
esac

mkdir -p "${BUILD_DIR}/layout/iteration_0" "${BUILD_DIR}/layout/final"
touch "$MEMORY_FILE"

state_init "$CELL_NAME" "$MAX_ITERATIONS"

# ---- state helpers -------------------------------------------------------

# A jq string literal for arbitrary text, so nothing read off disk can break out
# of the filter it is interpolated into.
json_str() {
    printf '%s' "${1:-}" | jq -Rs .
}

# state_write_atomic that reports instead of aborting: these calls record what
# happened, and losing the record because jq hiccuped is worse than the hiccup.
state_note() {
    state_write_atomic "$1" || echo "!! could not record state update in ${STATE_FILE}: $1" >&2
}

# The verdict that goes into state.json.  Read from the report THIS host wrote,
# before the model was invoked, and normalised to one of three fixed literals:
# a grep over the prompt payload used to let any line the model could influence
# land in .last_result.
host_verdict() {
    local report="${1:-}" line=""
    [[ -f "$report" ]] && line="$(grep -m1 -E "$PIPELINE_VERDICT_RE" "$report" 2>/dev/null || true)"
    case "$line" in
    *PASS*) printf 'RESULT: PASS\n' ;;
    *FAIL*) printf 'RESULT: FAIL\n' ;;
    *) printf 'RESULT: unknown\n' ;;
    esac
}

# ---- tamper guard --------------------------------------------------------
# Everything the verdict depends on is snapshotted into a temp directory OUTSIDE
# $BUILD_DIR.  ${STATE_FILE}.pre lived *inside* the directory the model is given
# --add-dir for, so writing the same forged JSON to both state.json and
# state.json.pre made the comparison agree and the restore reinstate the forgery.

GUARD_DIR=""
GUARD_GRADER_DIR=""
GUARD_STATE_SNAPSHOT=""
GUARD_ARMED=0

# The files that decide the verdict.  All are re-read from the mounted
# repository on every step, so an edit during a call changes the grade of the
# run in progress.  Additions go here.
GUARD_GRADERS=(
    "aion_layout/verification.py"
    "aion_layout/layout_metrics.py"
    "scripts/report_verification.py"
    "scripts/evidence.py"
    "scripts/curriculum.py"
    "scripts/score_iteration.py"
    "scripts/ledger.py"
    "scripts/generate_cell.py"
    "scripts/docker_run.sh"
    "pipeline.sh"
    "scripts/selfcheck.sh"
    "orchestrate.sh"
)

guard_hash() {
    # sha256 of $1, or "" when no hasher is available.  Detection never depends
    # on this — cmp does that — the hash is what gets recorded.
    command -v sha256sum >/dev/null 2>&1 || return 0
    sha256sum "$1" 2>/dev/null | cut -d' ' -f1
}

guard_init() {
    local rel src

    GUARD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/aion-guard-XXXXXX")" ||
        fatal "cannot create the tamper-guard directory"

    # The whole point is that the model cannot reach it.
    if [[ "${GUARD_DIR}/" == "${BUILD_DIR}/"* ]]; then
        rm -rf "$GUARD_DIR"
        GUARD_DIR=""
        fatal "TMPDIR resolves inside BUILD_DIR (${BUILD_DIR}); the snapshot would be writable by the model"
    fi

    GUARD_GRADER_DIR="${GUARD_DIR}/graders"
    GUARD_STATE_SNAPSHOT="${GUARD_DIR}/state.json.pre"
    : >"${GUARD_DIR}/graders.sha256"

    for rel in "${GUARD_GRADERS[@]}"; do
        src="${SCRIPT_DIR}/${rel}"
        [[ -f "$src" ]] || fatal "grader file missing from the checkout: ${rel}"
        mkdir -p "${GUARD_GRADER_DIR}/$(dirname "$rel")"
        cp -p "$src" "${GUARD_GRADER_DIR}/${rel}"
        printf '%s  %s\n' "$(guard_hash "$src")" "$rel" >>"${GUARD_DIR}/graders.sha256"
    done

    echo ">> Grader snapshot: ${#GUARD_GRADERS[@]} files under ${GUARD_DIR} (outside ${BUILD_DIR})"
}

# Restore any grader the model edited, name it loudly, record it in state.json.
# Never fatal: an attempt to edit the checker is diagnostic information about the
# model, and aborting the run would throw the diagnosis away with it.
#   $1 = when this check happened, for the record
guard_verify_graders() {
    local when="${1:-}" rel src expected actual restored=0

    [[ -n "$GUARD_DIR" && -d "$GUARD_GRADER_DIR" ]] || return 0

    for rel in "${GUARD_GRADERS[@]}"; do
        src="${SCRIPT_DIR}/${rel}"
        if [[ ! -f "${GUARD_GRADER_DIR}/${rel}" ]]; then
            # Only reachable when startup aborted part way through the snapshot.
            # Say so rather than "restoring" from a file that does not exist.
            echo "!! no snapshot of ${rel} to verify against" >&2
            continue
        fi
        cmp -s "$src" "${GUARD_GRADER_DIR}/${rel}" && continue

        expected="$(awk -v f="$rel" '$2 == f {print $1}' "${GUARD_DIR}/graders.sha256" 2>/dev/null || true)"
        actual="$(guard_hash "$src")"

        print_banner "\033[31m" "GRADER TAMPERING: ${rel} CHANGED DURING ${when^^}"
        {
            echo "!! The file that decides the verdict was modified by the thing being graded."
            echo "!!   file     : ${src}"
            echo "!!   expected : ${expected:-<unhashed>}"
            echo "!!   found    : ${actual:-<unhashed>}"
            echo "!! Restoring it from the snapshot taken before the run started."
        } >&2
        cp -f "${GUARD_GRADER_DIR}/${rel}" "$src" ||
            echo "!! RESTORE FAILED for ${src} — the run is no longer trustworthy." >&2
        restored=1

        state_note ".grader_tamper_events = ((.grader_tamper_events // 0) + 1)
                  | .last_grader_tamper = {
                        file: $(json_str "$rel"),
                        when: $(json_str "$when"),
                        expected_sha256: $(json_str "$expected"),
                        found_sha256: $(json_str "$actual"),
                        restored: true
                    }"
    done

    ((restored == 0)) || echo "!! Graders restored. The verdict below is the snapshot's, not the model's." >&2
    return 0
}

# Snapshot state.json outside $BUILD_DIR and mark the guard armed.  Called with
# the state already updated for this call (the model-call charge included), so
# the restore reinstates a state that is current apart from the model's writes.
guard_arm_state() {
    cp -f "$STATE_FILE" "$GUARD_STATE_SNAPSHOT" ||
        fatal "cannot snapshot ${STATE_FILE} to ${GUARD_STATE_SNAPSHOT}"
    GUARD_ARMED=1
}

# Restore state.json from the snapshot, unconditionally.  Runs after the model
# call and again from the trap, so a SIGINT or a killed host cannot leave a
# forged verdict on disk for the next run to read as success.
#   $1 = when this restore happened, for the record
guard_restore_state() {
    local when="${1:-}" tampered=0 tmp

    ((GUARD_ARMED)) || return 0
    GUARD_ARMED=0

    [[ -f "$GUARD_STATE_SNAPSHOT" ]] || {
        echo "!! No state snapshot to restore from (${GUARD_STATE_SNAPSHOT})." >&2
        return 0
    }

    if [[ ! -f "$STATE_FILE" ]] || ! cmp -s "$GUARD_STATE_SNAPSHOT" "$STATE_FILE"; then
        tampered=1
        print_banner "\033[31m" "STATE TAMPERING: ${STATE_FILE} CHANGED DURING ${when^^}"
        {
            echo "!! The graded verdict was written by the thing being graded. Restoring."
            echo "!! Model-written state.json was (control characters shown, first 4000 bytes):"
            head -c 4000 "$STATE_FILE" 2>/dev/null | cat -v || echo "(unreadable)"
            echo
        } >&2
    fi

    # Atomic: a restore interrupted halfway would leave a torn state file, which
    # is exactly the "next run reads something it should not trust" case.
    if tmp="$(mktemp "${STATE_FILE}.XXXXXX" 2>/dev/null)"; then
        cp -f "$GUARD_STATE_SNAPSHOT" "$tmp" && mv -f "$tmp" "$STATE_FILE" || {
            rm -f "$tmp"
            cp -f "$GUARD_STATE_SNAPSHOT" "$STATE_FILE"
        }
    else
        cp -f "$GUARD_STATE_SNAPSHOT" "$STATE_FILE"
    fi
    rm -f "$GUARD_STATE_SNAPSHOT"

    ((tampered == 0)) || state_note ".state_tamper_events = ((.state_tamper_events // 0) + 1)
                                   | .last_state_tamper = $(json_str "$when")"
    return 0
}

# ---- context lockout ------------------------------------------------------
#
# context/ holds the PDK rule decks, 83 reference cell generators and 84 SPICE
# netlists: about 4 MB, and roughly 794k tokens against a 262k window.  The
# prompt has not pointed at it since the rewrite, but the directory sits in the
# model's workspace and it has both `view` and `bash`, so "do not go looking for
# more" is advisory text.  A measured run showed it ignored: 90 tool calls, 8
# reads under context/drc/ and 6 under context/drc/rule_decks/, the whole
# 10-minute budget spent, and no module written.
#
# The rules it was hunting for are now block [9] of the evidence packet, so the
# reason to browse is gone.  This removes the opportunity as well.  Nothing in
# the flow reads context/ (verified by grep over every script and Makefile), so
# the lock is invisible to the pipeline.  It is restored by aion_cleanup, which
# runs on a normal exit and on INT/TERM/HUP alike.
# chmod 000 was the first attempt and it backfired: ripgrep, which is what the
# agent's file-search tool shells out to, ABORTS on an unreadable directory
# rather than skipping it.  The model then could not find aion_layout/
# building_blocks.py at all -- "rg: .../context: Permission denied (os error
# 13)" -- and spent its whole budget re-reading GDS_PYTHON_API.md instead.  The
# lock has to make the directory invisible, not forbidden.  Renaming it out of
# the way does that, costs nothing (same filesystem) and leaves the data intact
# under a known name if this process is killed before it can restore.
CONTEXT_DIR="${PIPELINE_ROOT}/context"
CONTEXT_STASH=""

context_lock() {
    local stash="${PIPELINE_ROOT}/.context.locked.$$"
    CONTEXT_STASH=""
    [[ -d "$CONTEXT_DIR" ]] || return 0
    [[ -e "$stash" ]] && return 0
    mv "$CONTEXT_DIR" "$stash" 2>/dev/null && CONTEXT_STASH="$stash"
    return 0
}

context_unlock() {
    [[ -n "$CONTEXT_STASH" && -d "$CONTEXT_STASH" ]] || return 0
    [[ -e "$CONTEXT_DIR" ]] || mv "$CONTEXT_STASH" "$CONTEXT_DIR" 2>/dev/null || true
    CONTEXT_STASH=""
}

# One idempotent cleanup, reached from a normal exit and from a signal alike.
# pipeline.sh installs its own temp-file traps at source time and deliberately
# does not overwrite ours; the contract is that whoever owns the trap calls its
# cleanup, so this one does.
aion_cleanup() {
    local rc=$?
    trap - EXIT INT TERM HUP
    set +e
    context_unlock
    guard_restore_state "an interrupted run"
    guard_verify_graders "the run"
    [[ -n "$GUARD_DIR" && -d "$GUARD_DIR" ]] && rm -rf "$GUARD_DIR"
    GUARD_DIR=""
    declare -F pipeline_cleanup_tmp >/dev/null 2>&1 && pipeline_cleanup_tmp
    return "$rc"
}

trap 'aion_cleanup' EXIT
trap 'aion_cleanup; exit 130' INT
trap 'aion_cleanup; exit 143' TERM
trap 'aion_cleanup; exit 129' HUP

# ---- evidence ------------------------------------------------------------

# Indent text so no line of it can start with a packet marker or a RESULT: line.
# Anything that reaches the prompt from a channel the model can influence goes
# through here first.
quote_text() {
    sed 's/^/  | /'
}

# The shared implementation the host grades with (pipeline.sh's report_summary),
# run in a *timed child shell*.  In-process it could neither be bounded nor
# survive a crash in model-written code; the layout digest inside it imports and
# executes the model's generator.
evidence_packet_shared() {
    local build_err="${1:-}"

    STATE_FILE="$STATE_FILE" \
        BUILD_DIR="$BUILD_DIR" \
        CELL_NAME="$CELL_NAME" \
        SPICE_NETLIST="$SPICE_NETLIST" \
        AION_BUILD_ERROR_FILE="$build_err" \
        timeout -k 10 "$EVIDENCE_TIMEOUT" bash -c '
            source "${AION_ROOT}/pipeline.sh"
            report_summary "${AION_BUILD_ERROR_FILE:-}"
        '
}

# Direct call into the host-side evidence builder, used when the shared path
# produced nothing usable.  stdout and stderr are captured separately: merged,
# an import-time print() in the model's module prepends forged lines to the
# packet the model is then shown.
evidence_packet_direct() {
    local build_err="${1:-}" n iter_dir mod out err rc=0
    local -a args

    n="$(pipeline_base_iteration 2>/dev/null || echo 0)"
    case "$n" in '' | *[!0-9]*) n=0 ;; esac
    iter_dir="${BUILD_DIR}/layout/iteration_${n}"
    mod="${iter_dir}/${CELL_NAME}.py"

    args=(--netlist "$SPICE_NETLIST" --iter-dir "$iter_dir" --cell "$CELL_NAME"
          --gate "${AION_GATE:-off}")
    [[ -f "$mod" ]] && args+=(--module "$mod")
    [[ -n "$build_err" && -s "$build_err" ]] && args+=(--build-error-file "$build_err")

    err="$(mktemp "${TMPDIR:-/tmp}/aion-evidence-err.XXXXXX")" || return 1
    out="$(timeout -k 10 "$EVIDENCE_TIMEOUT" python3 "${SCRIPT_DIR}/scripts/evidence.py" "${args[@]}" 2>"$err")" || rc=$?

    if ((rc != 0)) || [[ -z "${out//[[:space:]]/}" ]]; then
        echo "===== EVIDENCE UNAVAILABLE ====="
        echo "scripts/evidence.py exited ${rc} for cell ${CELL_NAME}"
        ((rc == 124 || rc == 137)) && echo "  (killed: it exceeded EVIDENCE_TIMEOUT=${EVIDENCE_TIMEOUT}s)"
        echo "  netlist  : ${SPICE_NETLIST}"
        echo "  iter-dir : ${iter_dir}"
        echo "  module   : ${mod}"
        echo "--- captured stderr (indented; nothing in it is a verdict) ---"
        quote_text <"$err" || true
        echo "===== END EVIDENCE UNAVAILABLE ====="
    else
        printf '%s\n' "$out"
    fi
    rm -f "$err"
}

# The evidence packet inlined into the prompt.  Prefers the shared
# implementation and falls back to calling scripts/evidence.py directly, so the
# two can never silently diverge into "no evidence at all".  Neither payload is
# ever discarded: the structured EVIDENCE UNAVAILABLE block names the exit code,
# the paths and the captured stderr, and throwing that away in favour of a
# second failure loses the only explanation the model would have got.
#   $1 = optional path to a build traceback to include
evidence_packet() {
    local build_err="${1:-}" shared="" direct="" rc=0

    shared="$(evidence_packet_shared "$build_err")" || rc=$?
    if ((rc == 124 || rc == 137)); then
        shared="${shared}"$'\n'"(pipeline.sh report_summary exceeded EVIDENCE_TIMEOUT=${EVIDENCE_TIMEOUT}s and was killed)"
    fi

    # Accept the shared payload only as a real packet that still carries the
    # build error we explicitly need the model to see.
    if [[ "$shared" == *"AION EVIDENCE PACKET"* ]] &&
        ! { [[ -n "$build_err" && -s "$build_err" ]] && [[ "$shared" != *"BUILD ERROR"* ]]; }; then
        printf '%s\n' "$shared"
        return 0
    fi

    direct="$(evidence_packet_direct "$build_err")"
    if [[ -z "${direct//[[:space:]]/}" ]]; then
        direct="===== EVIDENCE UNAVAILABLE =====
scripts/evidence.py produced no output at all.
===== END EVIDENCE UNAVAILABLE ====="
    fi
    printf '%s\n' "$direct"

    if [[ -n "${shared//[[:space:]]/}" ]]; then
        echo
        echo "===== SECONDARY DIAGNOSTIC — why the shared evidence path was not used ====="
        printf '%s\n' "$shared" | quote_text
        echo "===== END SECONDARY DIAGNOSTIC ====="
    fi
}

# True when the packet carries the recomputed verdict block, i.e. it is a real
# packet and not a diagnostic about why there is none.
# G13: the presence of a block [2] fence says nothing about whether block [2]
# found anything.  An empty iteration directory, and the traceback packet the
# builder emits when it fails, both carry the fence while every tool reads NOT
# AVAILABLE — and the confident "everything you need is inlined below, do not
# go looking for more" preamble printed over exactly those states is what
# prevents the model from recovering.  Gate on the content.
packet_is_gradable() {
    local packet="${1:-}"
    [[ "$packet" == *"===== [2] "* ]] || return 1
    [[ "$packet" == *"NOT AVAILABLE"* ]] && return 1
    grep -qE '^RESULT:[[:space:]]*ERROR' <<<"$packet" && return 1
    return 0
}

# True when state.json's clean claim is backed by the report the host wrote for
# the iteration it names.  Reads the report, never state.json's own verdict.
status_is_backed_by_report() {
    local n
    n="$(state_read '.current_iteration')" || return 1
    [[ "$n" =~ ^[0-9]+$ ]] || return 1
    report_passed_at "${BUILD_DIR}/layout/iteration_${n}/report.txt"
}

# ---- curriculum, score and ledger ----------------------------------------
#
# Stage 5.  The loop used to advance unconditionally on whatever the model
# wrote and to ask for a whole cell every turn.  Both are fixed here:
#
#   * every iteration is scored the moment it is graded, and the score is
#     appended to a host-written ledger that survives a timeout;
#   * the best score seen is remembered, and an iteration that scores worse is
#     REJECTED -- the next call branches from the best module instead of from
#     the regression, which is what stops the run being a random walk;
#   * the model is asked for one rung of a ladder derived from the netlist, and
#     the rung is chosen by the same Score the ledger records, so the
#     curriculum and the grader cannot drift apart.

# Print the curriculum rung for an iteration directory, or "" if it cannot be
# derived.  Never fatal: no rung means the packet falls back to the whole
# thing, which is worse but not wrong.
#   $1 = iteration directory
current_gate_key() {
    local iter_dir="$1" key=""
    key="$(timeout -k 5 60 python3 "${SCRIPT_DIR}/scripts/curriculum.py" \
        --netlist "$SPICE_NETLIST" --cell "$CELL_NAME" \
        --iter-dir "$iter_dir" --print key 2>/dev/null || true)"
    printf '%s' "${key//[$'\n\r']/}"
}

# Print an iteration's total score, or "" when it could not be computed.
#   $1 = iteration directory
score_total() {
    local iter_dir="$1" out=""
    out="$(timeout -k 5 120 python3 "${SCRIPT_DIR}/scripts/score_iteration.py" \
        --iter-dir "$iter_dir" --cell "$CELL_NAME" --netlist "$SPICE_NETLIST" \
        --json 2>/dev/null || true)"
    [[ -n "$out" ]] || return 0
    printf '%s' "$out" | jq -r '.total // empty' 2>/dev/null || true
}

# Append one scored iteration to the ledger, tagged with the rung it was on.
#   $1 = iteration number, $2 = iteration directory, $3 = outcome, $4 = rung
record_iteration() {
    local n="$1" iter_dir="$2" outcome="$3" gate="$4"
    timeout -k 5 120 python3 "${SCRIPT_DIR}/scripts/ledger.py" \
        --build-dir "$BUILD_DIR" append \
        --iteration "$n" --cell "$CELL_NAME" --iter-dir "$iter_dir" \
        --netlist "$SPICE_NETLIST" \
        --outcome "$outcome" --stage "$gate" 2>/dev/null || true
}

# Compare this iteration against the best seen and set .base_iteration to
# whichever the next call should work from.
#
# The comparison is `<=`, not `<`: an equal score means the model moved
# sideways, and preferring the newer of two equal layouts is what lets a run
# escape a plateau instead of re-sending the same source until the budget ends.
#   $1 = iteration number, $2 = its score (may be empty)
# Prints the accept/reject outcome on stdout.
accept_or_reject() {
    local n="$1" score="$2" best best_iter

    if [[ -z "$score" ]]; then
        # Unscored is not "as good as the best".  Keep whatever base we had.
        state_note ".unscored_iterations = ((.unscored_iterations // 0) + 1)"
        echo "unscored"
        return 0
    fi

    best="$(state_read '.best_score // empty')"
    best_iter="$(state_read '.best_iteration // empty')"

    if [[ -z "$best" || "$best" == "null" ]] ||
        awk "BEGIN{exit !($score <= $best)}"; then
        state_note ".best_score = ${score} | .best_iteration = ${n} | .base_iteration = ${n}"
        echo "accepted"
        return 0
    fi

    # Worse than the best. Branch from the best module rather than this one:
    # the artifacts for it are still on disk, so this costs no re-verification.
    state_note ".base_iteration = ${best_iter}
              | .rejected_iterations = ((.rejected_iterations // 0) + 1)"
    echo "rejected (score ${score} > best ${best} at iteration ${best_iter}; branching from there)"
    return 0
}

# Record a rung change in the ledger, so a stuck rung is visible as a stuck
# rung rather than as a flat score somebody has to interpret.
#   $1 = the rung now current
note_gate_transition() {
    local gate="$1" previous
    previous="$(state_read '.gate // empty')"
    [[ -n "$gate" ]] || return 0
    if [[ "$previous" != "$gate" ]]; then
        state_note ".gate = $(json_str "$gate")
                  | .gate_history = ((.gate_history // []) + [$(json_str "$gate")])"
        if [[ -n "$previous" && "$previous" != "null" ]]; then
            print_banner "\033[36m" "CURRICULUM: ${previous} -> ${gate}"
        fi
    else
        state_note ".gate_repeats = ((.gate_repeats // 0) + 1)"
    fi
    # Explicit, and not decoration.  A bare `&&` as the last line of a function
    # IS the function's exit status: this ended with
    #     [[ -n "$previous" ... ]] && print_banner ...
    # which is false on the first iteration, when there is no previous rung.
    # The function returned 1, `set -e` killed the loop between scoring
    # iteration 0 and the max-iterations check, and the run left
    # status:in_progress with no banner and no explanation.
    return 0
}

# ---- build gate ----------------------------------------------------------

# Actually build the module the way the pipeline will: import it, call
# generate(CELL_NAME, sg13g2_tech), write a GDS.  Runs in a subprocess under a
# wall-clock timeout so a crash, a sys.exit() or a sleep in model-written code
# cannot take this script down or stall it.
#   $1 = module path, $2 = file to receive the traceback
build_module() {
    local mod="$1" err="$2" tmp_gds rc=0

    tmp_gds="$(mktemp -t "aion_build_XXXXXX.gds")"

    set +e
    timeout -k 10 "$HOST_BUILD_TIMEOUT" python3 - "$mod" "$CELL_NAME" "$tmp_gds" >"$err" 2>&1 <<'PY'
import importlib.util
import os
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.environ.get("AION_ROOT", "."))

mod_path, cell_name, out_gds = sys.argv[1], sys.argv[2], sys.argv[3]

try:
    from aion_layout.tech import sg13g2_tech

    spec = importlib.util.spec_from_file_location(Path(mod_path).stem, mod_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load a Python module from {mod_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    if not hasattr(module, "generate"):
        raise AttributeError(
            f"{mod_path} does not define generate(cell_name, tech) -> Cell"
        )

    cell = module.generate(cell_name, sg13g2_tech)
    cell.write_gds(out_gds)
except BaseException:
    traceback.print_exc()
    sys.exit(1)

print(f"BUILD OK: {mod_path} -> generate({cell_name!r}, sg13g2_tech) -> {out_gds}")
PY
    rc=$?
    set -e

    # A killed build must read as a build failure with a stated reason, not as
    # an empty traceback the model cannot act on.
    if ((rc == 124 || rc == 137)); then
        {
            echo
            echo "BUILD TIMEOUT: generate('${CELL_NAME}', sg13g2_tech) did not return within"
            echo "HOST_BUILD_TIMEOUT=${HOST_BUILD_TIMEOUT}s and was killed. The module must build"
            echo "in seconds; an unbounded loop, a sleep or a blocking call is a defect in it."
        } >>"$err"
    fi

    rm -f "$tmp_gds"
    return "$rc"
}

# ---- deadline ------------------------------------------------------------

# "10m" / "600" / "2h" -> seconds. Anything unparsable falls back to 600.
timeout_seconds() {
    local spec="$1" num unit
    num="${spec%%[!0-9]*}"
    unit="${spec#"$num"}"
    # A value this cannot parse is one `timeout` will reject too, so guessing a
    # fallback here only makes deadline.epoch disagree with the real kill time:
    # selfcheck.sh then tells the model it has budget left that does not exist.
    [[ -z "$num" ]] && fatal "FIX_TIMEOUT='${spec}' is not a duration (e.g. 90, 6m, 1h)"
    case "$unit" in
    "" | s) echo "$num" ;;
    m) echo $((num * 60)) ;;
    h) echo $((num * 3600)) ;;
    d) echo $((num * 86400)) ;;
    *) fatal "FIX_TIMEOUT='${spec}' has an unknown unit '${unit}' (use s, m, h or d)" ;;
    esac
}

write_deadline() {
    local secs
    secs="$(timeout_seconds "$FIX_TIMEOUT")"
    mkdir -p "$(dirname "$DEADLINE_FILE")"
    echo $(($(date +%s) + secs)) >"$DEADLINE_FILE"
}

# ---- prompt --------------------------------------------------------------

# Assemble the complete prompt for the current iteration on stdout.
#   $1 = the evidence packet, already built by evidence_packet
build_fix_prompt() {
    local packet="${1:?build_fix_prompt needs an evidence packet}"
    local n cur src next_mod work_dir iter_dir report memory evidence_preamble
    local ledger_digest branch_note="" rules_note

    # The next module always lands after the CURRENT iteration, but the source
    # and the evidence come from the BASE one -- the best iteration seen, which
    # is the same thing until a regression is rejected.  Showing a rejected
    # module as "the current source" is how a run keeps editing the worse of two
    # layouts it already has on disk.
    cur="$(state_read '.current_iteration')"
    n="$(pipeline_base_iteration)"
    iter_dir="${BUILD_DIR}/layout/iteration_${n}"
    src="${iter_dir}/${CELL_NAME}.py"
    report="${iter_dir}/report.txt"
    next_mod="${BUILD_DIR}/layout/iteration_$((cur + 1))/${CELL_NAME}.py"
    if [[ "$n" != "$cur" ]]; then
        branch_note="NOTE: iteration ${cur} scored worse than iteration ${n} and was rejected. You are
working from iteration ${n}, the best version so far. The change that caused the
regression is not in the source below -- do not reapply it.

"
    fi
    # Outside the iteration tree on purpose: a self-check writing its own DRC
    # and LVS output into iteration_N+1/ made the next evidence packet read the
    # model's own scratch runs back as if they were the host's measurements.
    work_dir="${BUILD_DIR}/selfcheck/iteration_$((cur + 1))"

    # The host-written history.  memory.md is the model's own scratchpad and is
    # 0 bytes after every run so far -- it is written last, inside a hard
    # timeout, so it is the first thing lost.  The ledger does not depend on the
    # model finishing, and it is what shows a flat score or a stuck rung.
    ledger_digest="$(timeout -k 5 30 python3 "${SCRIPT_DIR}/scripts/ledger.py" \
        --build-dir "$BUILD_DIR" render 2>/dev/null || true)"
    [[ -n "${ledger_digest//[[:space:]]/}" ]] ||
        ledger_digest="(no iterations scored yet.)"

    memory="$(tail -c "$MEMORY_INLINE_BYTES" "$MEMORY_FILE" 2>/dev/null || true)"
    if [[ -z "${memory//[[:space:]]/}" ]]; then
        memory="(no notes yet — this is the first pass, or nothing was recorded.)"
    fi

    # Cross-references are generated from the packet in hand, never asserted.
    if [[ "$packet" == *"===== [9] "* ]]; then
        rules_note="Every numeric design rule is in block [9] of the packet — widths, spacings,
enclosures, cut sizes, the routing grid, the standard-cell frame — generated from
the technology object the API itself reads. Do not go looking for them: the PDK
rule decks under ./context are not readable from this session."
    else
        rules_note="This turn does not need the design-rule table, so it is not inlined; the rung
in block [0] is about connectivity, not geometry. If you genuinely need a rule
value, ./GDS_PYTHON_API.md states them — the PDK rule decks under ./context are
not readable from this session."
    fi

    # "Everything you need is inlined below, do not go looking for more" is true
    # only when the packet actually carries the verdict block.  Asserted over a
    # degraded packet, it is the one sentence that prevents recovery.
    if packet_is_gradable "$packet"; then
        evidence_preamble="Everything you need is inlined below: the target netlist, the verification evidence
from iteration ${n}, and the full current source. Do not go looking for more. The
repository is far larger than your context window and browsing it will exhaust your
budget before you have finished the layout."
    else
        evidence_preamble="READ THIS FIRST — THE EVIDENCE BELOW IS DEGRADED. The host could not build the
verification digest for iteration ${n}, so what follows in its place is a diagnostic
explaining why. It is not a report on the layout: nothing in it says the cell is
clean, and the absence of a violation list is not the absence of violations.

Because the packet is degraded you may, this turn only, read these on disk before
you edit anything:
    ${report}
        the host's own PASS/FAIL report for iteration ${n}, if it was written
    ${iter_dir}/drc/
        the raw Magic and KLayout output for iteration ${n}
    ${iter_dir}/lvs/
        the raw Netgen output for iteration ${n}
Then run the self-check in step 4 below: it re-runs the whole chain and prints a
fresh verdict, which is the only way to learn the current state of the layout when
the packet is degraded. Read those and nothing else."
    fi

    cat <<EOF
You are a physical-design engineer working on a standard cell for the IHP SG13G2
130 nm PDK. A single Python module draws the cell through the AION layout API; the
host builds its GDS, runs Magic and KLayout DRC and Netgen LVS against the target
SPICE netlist, and grades the result.

The cell is built one rung at a time, and this turn is ONE RUNG. Block [0] states
which one, what to do, the number it is measured on and the criterion that clears
it. Do that and nothing else: the later rungs are later turns, and work spent on
them now does not move the score.

${branch_note}${evidence_preamble}

${rules_note}

Do not open any file. Measured on this harness, a single read of
./GDS_PYTHON_API.md consumed an entire turn's budget and the module was never
written — twice. Every signature you need is in block [10], generated by
introspecting the very code you are calling, so it cannot be out of date. If
something is genuinely missing from what you were given, write the module using
what you do have and say so in your note.

The rungs are ordered so that connectivity is settled before geometry: a layout
that implements the wrong circuit cannot be repaired by moving shapes. Never trade
connectivity for area, and never change the SPICE netlist to match the layout —
the netlist is the specification.

============================ SCORED HISTORY (host-written) ============================
Lower is better; 0 is DRC- and LVS-clean. This table is written by the host from
the artifacts, so it is there even for a turn that ran out of time.

${ledger_digest}
========================== END SCORED HISTORY ==========================

========================= NOTES FROM PREVIOUS ITERATIONS =========================
(${MEMORY_FILE})

${memory}
======================= END NOTES FROM PREVIOUS ITERATIONS =======================

$(printf '%s\n' "$packet")

=========== CURRENT SOURCE — iteration ${n} (${src}) ===========
$(cat "$src" 2>/dev/null || echo "(source not available at ${src})")
=========== END CURRENT SOURCE ===========

================================== YOUR TASK ==================================

Your budget is ${FIX_TIMEOUT} of wall clock and every tool call spends a large
slice of it. Do not explore. These are already true and do not need checking:
the directory below exists, ${MEMORY_FILE} exists, and everything you need to
decide is in this prompt.

1. WRITE THE FIX — FIRST, before anything else. USE YOUR FILE-EDITING TOOL to
   create this file:
       ${next_mod}
   It must contain the complete corrected Python module, the whole file and not
   a patch.

   Printing the module in your reply does not count and is not graded. The host
   reads that path off the disk after you stop; if nothing is there, the turn
   produced nothing, however the reply describes it. Create the file, then say
   what you changed in one or two sentences.
   It must define generate(cell_name, tech) -> Cell. Read block [0], make the one
   change that clears THAT rung, and change nothing else: a redesign restarts the
   ladder from the bottom. Do not modify ${src} or any other iteration's files.

   Write it first because a turn that runs out of time after writing the module
   still counts — the host grades whatever is at that path — and a turn that runs
   out of time before writing it produced nothing at all.

   Those two paths are the only files you may write. Everything else — the
   pipeline, the checkers, the verification state — is snapshotted before this
   turn and restored after it, so editing any of it changes no verdict and is
   recorded against this run.

2. SELF-CHECK (optional). This one command runs the identical
   build -> DRC -> LVS -> report chain the host will use to grade you, and prints
   the same verdict:
       ./scripts/selfcheck.sh ${next_mod} ${work_dir}
   At most one round, and only if you have real doubt: it runs the actual tools
   and takes minutes out of the same budget.

3. NOTE WHAT YOU CHANGED. Append one short entry to ${MEMORY_FILE}: what you
   concluded from the evidence, what you changed, and what to watch next time.
   Keep it to a few lines. The host already records the scores, so this is for
   the reasoning behind them, not the numbers.

4. STOP. Once ${next_mod} exists on disk, stop. Do not run anything else.
   Before you stop, confirm to yourself that you actually called the edit tool —
   describing the change is not making it.
EOF
}

# ---- one model call ------------------------------------------------------

# Run one fix request.
# Returns 0 on success, 1 if the model call failed or wrote nothing, 3 if the
# global model-call budget is exhausted.
#   $1 = optional path to a build traceback from the previous attempt
request_fix() {
    local build_err="${1:-}" n src next_mod packet prompt rc=0 used

    n="$(state_read '.current_iteration')"
    src="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.py"
    next_mod="${BUILD_DIR}/layout/iteration_$((n + 1))/${CELL_NAME}.py"
    mkdir -p "$(dirname "$next_mod")" "${BUILD_DIR}/selfcheck/iteration_$((n + 1))"
    # The prompt tells the model these already exist so it does not spend a tool
    # call finding out.  Measured: a turn died having spent its whole budget on
    # two `ls` calls checking exactly this.
    [[ -e "$MEMORY_FILE" ]] || : >"$MEMORY_FILE"

    # Every model call is charged against one global budget, whatever the reason
    # for it: a build-gate retry costs exactly as much wall clock and money as a
    # fresh iteration and used to be spent without being counted anywhere.
    used="$(state_read '.model_calls // 0')"
    case "$used" in '' | *[!0-9]*) used=0 ;; esac
    if ((used >= MAX_MODEL_CALLS)); then
        print_banner "\033[31m" "MODEL CALL BUDGET EXHAUSTED (${used}/${MAX_MODEL_CALLS})"
        echo "!! No model call left. Raise MAX_MODEL_CALLS to allow more." >&2
        return 3
    fi

    packet="$(evidence_packet "$build_err")"
    prompt="$(build_fix_prompt "$packet")"

    print_banner "\033[33m" "REQUESTING FIX: ITERATION ${n} -> $((n + 1))  [model call $((used + 1))/${MAX_MODEL_CALLS}]"
    echo ">> Prompt: $(printf '%s' "$prompt" | wc -c) bytes (~$(($(printf '%s' "$prompt" | wc -c) / 4)) tokens)"
    packet_is_gradable "$packet" ||
        echo "!! Evidence is DEGRADED for this call — the prompt says so and tells the model what it may read instead." >&2
    [[ -n "$build_err" && -s "$build_err" ]] && echo ">> Carrying build traceback from the previous attempt: ${build_err}"
    echo ">> Agent will write code directly to: ${next_mod}"
    echo ">> Agent may self-check with: ./scripts/selfcheck.sh ${next_mod} ${BUILD_DIR}/selfcheck/iteration_$((n + 1))"
    echo ">> Agent will append iteration findings to: ${MEMORY_FILE}"
    echo

    write_deadline

    # Charge the call before making it: a call that dies mid-flight still cost
    # the wall clock and the tokens, so it must still count.  Charged *before*
    # the snapshot so the restore preserves the charge rather than refunding it.
    state_note ".model_calls = $((used + 1)) | .model_call_budget = ${MAX_MODEL_CALLS}"

    guard_arm_state
    context_lock

    set +e
    if [[ "$AGENT_CLI" == "opencode" ]]; then
        # --auto approves tool use without a prompt; there is no interactive
        # terminal here and a permission prompt would hang until FIX_TIMEOUT.
        timeout -k 10 "$FIX_TIMEOUT" "$OPENCODE_RCP" - "$MODEL" -- \
            run "$prompt" \
            --auto \
            --dir "$SCRIPT_DIR"
    else
        timeout -k 10 "$FIX_TIMEOUT" "$COPILOT_RCP" - "$MODEL" -p "$prompt" \
            --reasoning-effort "$MODEL_EFFORT" \
            --allow-tool view \
            --allow-tool edit \
            --allow-tool bash \
            --deny-tool write-outside-workspace \
            --add-dir "$(dirname "$src")" \
            --add-dir "$(dirname "$next_mod")" \
            --add-dir "$BUILD_DIR"
    fi
    rc=$?
    set -e

    context_unlock
    guard_restore_state "the model call"
    guard_verify_graders "the model call"

    echo

    # The module is checked BEFORE the exit status, deliberately.  `timeout`
    # returns 124, and a model that wrote a complete module at t=500s and was
    # still talking at t=600s used to have that module thrown away unread and
    # the whole run aborted -- the most expensive possible way to lose work that
    # was already on disk.  What the turn was asked to produce is the module; if
    # it is there, the turn produced it, whatever the CLI did afterwards.
    if [[ -f "$next_mod" ]]; then
        if [[ $rc -ne 0 ]]; then
            if ((rc == 124 || rc == 137)); then
                echo "!! ${AGENT_CLI} hit FIX_TIMEOUT=${FIX_TIMEOUT} — but it had already written" >&2
                echo "   ${next_mod}, so the build gate grades that." >&2
                state_note '.model_call_timeouts = ((.model_call_timeouts // 0) + 1)'
            else
                echo "!! ${AGENT_CLI} exited with status $rc after writing ${next_mod};" >&2
                echo "   grading what it wrote." >&2
                state_note '.model_call_errors = ((.model_call_errors // 0) + 1)'
            fi
        fi
        return 0
    fi

    if [[ $rc -ne 0 ]]; then
        echo "!! ${AGENT_CLI} exited with status $rc and wrote no module" >&2
        return 1
    fi

    echo "!! Agent finished but did not write ${next_mod}" >&2
    return 1
}

# Record a build-gate failure durably.  An overwritten build_error.txt was the
# only trace three failed attempts left behind.
#   $1 = iteration being built, $2 = attempt number, $3 = traceback file
record_build_failure() {
    local n="$1" attempt="$2" err_file="$3" summary=""

    if [[ -s "$err_file" ]]; then
        # Whole lines only: a byte cut in the middle of the first line records a
        # word fragment where the exception type should be.
        summary="$(grep -v '^[[:space:]]*$' "$err_file" 2>/dev/null | tail -n 5 | cut -c1-200 || true)"
        while ((${#summary} > 500)) && [[ "$summary" == *$'\n'* ]]; do
            summary="${summary#*$'\n'}"
        done
    fi
    [[ -n "$summary" ]] || summary="(build failed but wrote no traceback)"

    state_note ".build_failures = ((.build_failures // 0) + 1)
              | .last_build_failure = {
                    iteration: ${n},
                    attempt: ${attempt},
                    file: $(json_str "$err_file"),
                    error: $(json_str "$summary")
                }"
}

# Ask the model for a fix, then actually build what it wrote. A build failure is
# not fatal: the traceback goes back to the model verbatim and it gets another
# try, up to MAX_BUILD_FAILURES attempts — each one a model call charged against
# the global budget and recorded in state.json.
# Returns 0 on a module that builds, 1 if the model call itself failed, 2 if the
# build gate was never satisfied, 3 if the model-call budget is exhausted.
request_fix_and_build() {
    local n next_mod err_file build_err="" attempt rc=0

    n="$(state_read '.current_iteration')"
    next_mod="${BUILD_DIR}/layout/iteration_$((n + 1))/${CELL_NAME}.py"
    err_file="${BUILD_DIR}/layout/iteration_$((n + 1))/build_error.txt"

    local gate_before="${AION_GATE:-auto}"

    for ((attempt = 1; attempt <= MAX_BUILD_FAILURES; attempt++)); do
        rc=0
        # A retry is answering a traceback, so it is on the `build` rung whatever
        # the ladder said before.  Without this the model is handed, say, the
        # "add well and substrate taps" objective while staring at an
        # ImportError -- an objective it cannot act on and cannot be graded on,
        # because nothing about the layout is measurable until it builds.
        if [[ -n "$build_err" ]]; then
            export AION_GATE=build
        else
            export AION_GATE="$gate_before"
        fi

        request_fix "$build_err" || rc=$?
        export AION_GATE="$gate_before"
        ((rc == 0)) || return "$rc"

        echo ">> Build gate: importing ${next_mod} and calling generate(${CELL_NAME}, sg13g2_tech)..."
        if build_module "$next_mod" "$err_file"; then
            cat "$err_file"
            rm -f "$err_file"
            echo ">> Build gate passed."
            return 0
        fi

        record_build_failure "$((n + 1))" "$attempt" "$err_file"

        print_banner "\033[31m" "BUILD FAILED (attempt ${attempt}/${MAX_BUILD_FAILURES}) — FEEDING THE TRACEBACK BACK"
        echo "!! ${next_mod} imported/ran but did not produce a GDS. Traceback:" >&2
        sed 's/^/   /' "$err_file" >&2
        echo >&2
        build_err="$err_file"
    done

    print_banner "\033[31m" "BUILD GATE NOT SATISFIED AFTER ${MAX_BUILD_FAILURES} ATTEMPTS"
    echo "!! The model could not produce a module that builds. Last traceback: ${err_file}" >&2
    return 2
}

# ---- dump-prompt mode ----------------------------------------------------
# Assemble the prompt for the current iteration and exit. No model call, no
# docker, no guard, no state mutation — this exists so the prompt can be
# inspected and regression-tested offline.

if [[ -n "${AION_DUMP_PROMPT:-}" ]]; then
    mkdir -p "$(dirname "$AION_DUMP_PROMPT")"
    build_fix_prompt "$(evidence_packet "${AION_BUILD_ERROR_FILE:-}")" >"$AION_DUMP_PROMPT"
    echo "Prompt written to ${AION_DUMP_PROMPT} ($(wc -c <"$AION_DUMP_PROMPT") bytes, ~$(($(wc -c <"$AION_DUMP_PROMPT") / 4)) tokens)"
    exit 0
fi

# ---- real run: everything below makes model calls ------------------------

# Under `set -u` an unset key aborted the script at the model call — after the
# whole deterministic pipeline had run and without ever reaching the "blocked"
# handler.  Checked here instead, before anything is spent.  Never echoed: the
# value is a live credential.
CEFPROVIDER_API_KEY="${CEFPROVIDER_API_KEY:-}"
if [[ -z "$CEFPROVIDER_API_KEY" ]]; then
    fatal "CEFPROVIDER_API_KEY is unset or empty; the model call cannot be made.
   Export it before running (its value is never printed by this script)."
fi
# Exported, never passed as an argument.  A command line is world-readable via
# /proc, so a key in argv is visible to every user on the host through `ps` --
# measured on this machine, the live key was sitting in the process listing for
# the whole of each run.  The wrappers take "-" to mean "read it from the
# environment", which children inherit and `ps` never shows.
export CEFPROVIDER_API_KEY
case "$AGENT_CLI" in
copilot) [[ -x "$COPILOT_RCP" ]] || fatal "copilot wrapper not executable: ${COPILOT_RCP}" ;;
opencode) [[ -x "$OPENCODE_RCP" ]] || fatal "opencode wrapper not executable: ${OPENCODE_RCP}" ;;
esac

guard_init

print_banner "\033[36m" "AION LAYOUT ORCHESTRATION v5.0"
echo "Cell: $CELL_NAME | Netlist: $SPICE_NETLIST | Build dir: $BUILD_DIR | Max iter: $MAX_ITERATIONS | Model: $MODEL"
echo "Model-call budget: $(state_read '.model_calls // 0') / ${MAX_MODEL_CALLS} used | build-gate retries per iteration: ${MAX_BUILD_FAILURES}"
echo

# ---- main loop -----------------------------------------------------------

for ((i = 0; i < MAX_ITERATIONS; i++)); do
    status="$(state_read '.status')"
    # A JSON string is not evidence.  SIGKILL is untrappable and an OOM or a
    # power cut leaves whatever was in state.json, so a "verified_clean" that
    # no report backs is demoted here rather than believed: otherwise the next
    # invocation breaks out before verifying anything and finalize declares
    # success over a report that reads RESULT: FAIL.
    if [[ "$status" == "verified_clean" ]] && ! status_is_backed_by_report; then
        echo "!! state.json claims verified_clean but the report for that iteration does not." >&2
        echo "!! Ignoring the claim and re-verifying." >&2
        state_note '.status = "in_progress" | .last_error = "unbacked verified_clean discarded"'
        status="in_progress"
    fi
    [[ "$status" == "verified_clean" || "$status" == "max_iterations_reached" ]] && break

    n="$(state_read '.current_iteration')"

    print_banner "\033[32m" "STARTING ITERATION ${n} / $((MAX_ITERATIONS - 1))"

    if [[ "$n" -eq 0 && ! -f "${BUILD_DIR}/layout/iteration_0/${CELL_NAME}.py" ]]; then
        echo "Generating initial scaffold..."
        step_generate_scaffold
    fi

    echo "Running deterministic pipeline (GDS -> render -> DRC -> LVS -> report)..."
    if ! run_deterministic_steps_for_current_iteration; then
        echo "!! A deterministic step failed outright (not a DRC/LVS violation — an actual command failure)." >&2
        state_write_atomic '.status = "blocked" | .last_error = "deterministic step failed, see stdout"'
        exit 1
    fi

    # The authoritative verdict: read from the report this host just wrote, and
    # recorded now — before the model is invoked and can touch anything.
    iteration_verdict="$(host_verdict "${BUILD_DIR}/layout/iteration_${n}/report.txt")"
    state_note ".last_result = \"${iteration_verdict}\""
    echo "Host verdict for iteration ${n}: ${iteration_verdict}"

    iter_dir="${BUILD_DIR}/layout/iteration_${n}"
    iter_gate="$(current_gate_key "$iter_dir")"
    iter_score="$(score_total "$iter_dir")"
    decision="$(accept_or_reject "$n" "$iter_score")"
    record_iteration "$n" "$iter_dir" "$decision" "$iter_gate"

    # The rung the NEXT call gets is the rung of the iteration it works from,
    # which after a rejection is the best one rather than this one.
    base_n="$(pipeline_base_iteration)"
    if [[ "$base_n" == "$n" ]]; then
        next_gate="$iter_gate"
    else
        next_gate="$(current_gate_key "${BUILD_DIR}/layout/iteration_${base_n}")"
    fi
    note_gate_transition "$next_gate"

    # Pin the rung for this call rather than leaving it at "auto".  The model
    # inherits this variable, so its own ./scripts/selfcheck.sh scores its new
    # module against the SAME rung it was asked to clear -- "did I do the thing"
    # -- instead of re-deriving a rung from its own workdir and being handed a
    # different objective halfway through the turn.
    if [[ -n "$next_gate" ]]; then
        export AION_GATE="$next_gate"
    fi

    echo "Score for iteration ${n}: ${iter_score:-unscored}  rung: ${iter_gate:-unknown}  -> ${decision}"
    [[ "$base_n" == "$n" ]] ||
        echo "Next call works from iteration ${base_n} (rung: ${next_gate:-unknown})"

    if report_passed; then
        print_banner "\033[32m" "SUCCESS: DRC AND LVS PASSED CLEANLY AT ITERATION ${n}"
        state_write_atomic '.status = "verified_clean"'
        break
    fi

    if [[ "$((n + 1))" -ge "$MAX_ITERATIONS" ]]; then
        print_banner "\033[31m" "MAX ITERATIONS (${MAX_ITERATIONS}) REACHED WITHOUT CLEAN RESULT"
        state_write_atomic '.status = "max_iterations_reached"'
        break
    fi

    fix_rc=0
    request_fix_and_build || fix_rc=$?
    if [[ $fix_rc -eq 1 ]]; then
        print_banner "\033[31m" "FIX REQUEST FAILED AT ITERATION ${n}"
        echo "!! The model call failed or wrote no module. Inspect iteration ${n}'s report and ${MEMORY_FILE}." >&2
        state_write_atomic '.status = "blocked" | .last_error = "fix request failed"'
        exit 1
    elif [[ $fix_rc -eq 3 ]]; then
        print_banner "\033[31m" "BLOCKED AT ITERATION ${n}: MODEL CALL BUDGET EXHAUSTED"
        echo "!! $(state_read '.model_calls // 0') of ${MAX_MODEL_CALLS} model calls spent, $(state_read '.build_failures // 0') of them on build-gate retries." >&2
        state_write_atomic '.status = "blocked" | .last_error = "model call budget exhausted"'
        exit 1
    elif [[ $fix_rc -ne 0 ]]; then
        print_banner "\033[31m" "BLOCKED AT ITERATION ${n}: NO BUILDABLE MODULE"
        echo "!! ${MAX_BUILD_FAILURES} consecutive build failures. Inspect ${BUILD_DIR}/layout/iteration_$((n + 1))/build_error.txt." >&2
        state_write_atomic '.status = "blocked" | .last_error = "build gate not satisfied"'
        exit 1
    fi

    next_src="${BUILD_DIR}/layout/iteration_$((n + 1))/${CELL_NAME}.py"
    echo "Accepted and built: $next_src"

    state_write_atomic '.current_iteration += 1 | .steps = {"gds_generated": false, "rendered": false, "drc_done": false, "lvs_done": false, "report_generated": false}'
done

# ---- finalize (deterministic, no LLM, no re-verification) -----------------
# The loop already produced every artifact for the final iteration. Re-running
# DRC and LVS here would only give a second chance to disagree with the verdict
# the run was graded on, so finalize copies rather than re-measures.

final_status="$(state_read '.status')"
if [[ "$final_status" == "verified_clean" ]] && ! status_is_backed_by_report; then
    echo "!! Refusing to finalize as verified_clean: the report for that iteration does not say PASS." >&2
    state_note '.status = "blocked" | .last_error = "unbacked verified_clean at finalize"'
    final_status="blocked"
fi
if [[ "$final_status" == "verified_clean" || "$final_status" == "max_iterations_reached" ]]; then
    n="$(state_read '.current_iteration')"

    # A clean run ships the iteration that passed.  A run that ran out of
    # iterations ships the BEST one it found, which is not always the last: the
    # max-iterations break fires before the next pass can reject a regression,
    # so finalising the newest used to hand over the worse of two layouts the
    # run already had on disk while the ledger recorded the better one.
    if [[ "$final_status" == "max_iterations_reached" ]]; then
        best_n="$(state_read '.best_iteration // empty')"
        if [[ "$best_n" =~ ^[0-9]+$ ]] && [[ "$best_n" != "$n" ]] &&
            [[ -s "${BUILD_DIR}/layout/iteration_${best_n}/${CELL_NAME}.gds" ]]; then
            echo ">> Finalising iteration ${best_n} (score $(state_read '.best_score // "?"')), not ${n}: it scored best."
            state_note ".finalized_iteration = ${best_n} | .finalized_instead_of = ${n}"
            n="$best_n"
        fi
    fi

    iter_dir="${BUILD_DIR}/layout/iteration_${n}"
    final_dir="${BUILD_DIR}/layout/final"
    mkdir -p "$final_dir"

    for artifact in "${CELL_NAME}.py" "${CELL_NAME}.gds" "${CELL_NAME}.png" report.txt; do
        [[ -f "${iter_dir}/${artifact}" ]] && cp -f "${iter_dir}/${artifact}" "${final_dir}/${artifact}"
    done

    for run_dir in drc lvs; do
        if [[ -d "${iter_dir}/${run_dir}" ]]; then
            rm -rf "${final_dir:?}/${run_dir}"
            cp -a "${iter_dir}/${run_dir}" "${final_dir}/${run_dir}"
        fi
    done

    AION_GATE=off evidence_packet >"${final_dir}/evidence.txt"

    state_write_atomic '.status = "finalized"'

    # G14: run the grader check *before* the summary that reports its result.
    # Every tampered run used to end with "Tamper events: ... graders 0" on
    # screen and the GRADER TAMPERING banner printed afterwards by the EXIT
    # trap — the line an operator actually reads was the one under-reporting.
    guard_verify_graders "the run"

    print_banner "\033[35m" "ORCHESTRATION COMPLETE"
    echo "Cell: ${CELL_NAME}"
    echo "Iterations: $((n + 1))"
    echo "Status: ${final_status}"
    echo "Verdict: $(state_read '.last_result // "RESULT: unknown"')"
    echo "Model calls: $(state_read '.model_calls // 0') / ${MAX_MODEL_CALLS} | build failures: $(state_read '.build_failures // 0')"
    echo "Tamper events: state $(state_read '.state_tamper_events // 0') | graders $(state_read '.grader_tamper_events // 0')"
    echo "Final Output: ${final_dir}/"
fi
