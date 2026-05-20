#!/usr/bin/env bash
# bonsai-launch.sh — thin shim that starts bonsai in a detached tmux session.
#
# Usage:
#   bonsai-launch.sh <plan_path> [--runner tmux_rpc|claude_p] [extra args...]
#
# The session name is derived from the plan directory name.
# If a session with that name already exists, this script exits non-zero.

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <plan_path> [--runner RUNNER] [bonsai-start-args...]" >&2
    exit 1
fi

PLAN_PATH="$1"
shift

PLAN_NAME="$(basename "$(dirname "${PLAN_PATH}")")"
SESSION="bonsai-worker-${PLAN_NAME}"

if tmux has-session -t "${SESSION}" 2>/dev/null; then
    echo "Error: session '${SESSION}' already exists. Use 'bonsai attach ${PLAN_NAME}' to resume." >&2
    exit 1
fi

PLAN_QUOTED=$(printf '%q' "${PLAN_PATH}")
EXTRA=$(printf ' %q' "$@")
tmux new-session -d -s "${SESSION}" \
    "uv tool run bonsai start ${PLAN_QUOTED}${EXTRA}; echo '--- bonsai exited ---'; exec bash"

echo "Started session '${SESSION}'"
echo "Attach: bonsai attach ${PLAN_NAME}"
echo "Kill:   bonsai kill ${PLAN_NAME}"
