#!/usr/bin/env bash

set -u
set -o pipefail

cd ~/rebot_control
source .venv/bin/activate

STAMP=$(date +%Y%m%d_%H%M%S)
RUN_DIR="$HOME/trix_logs/run_$STAMP"

mkdir -p "$RUN_DIR"

CAN_LOG="$RUN_DIR/can_raw.log"
CONSOLE_LOG="$RUN_DIR/controller_console.log"
META="$RUN_DIR/run_metadata.txt"

echo "============================================================"
echo "TRIX LOGGED RUN"
echo "============================================================"
echo "RUN DIRECTORY:"
echo "$RUN_DIR"
echo

# ------------------------------------------------------------
# Snapshot exact software/config used.
# ------------------------------------------------------------

cp examples/trix_large_v2.py \
   "$RUN_DIR/trix_large_v2.py"

cp config/rebotarm_rs.yaml \
   "$RUN_DIR/rebotarm_rs.yaml"

{
    echo "timestamp=$STAMP"
    echo "hostname=$(hostname)"
    echo "kernel=$(uname -a)"
    echo "working_directory=$(pwd)"
    echo

    echo "POWER_CONFIGURATION_EXPECTED"
    echo "voltage=48V"
    echo "current_limit=15A"
    echo "mode=CV"
    echo

    echo "SCRIPT"
    sha256sum examples/trix_large_v2.py
    echo

    echo "CONFIG"
    sha256sum config/rebotarm_rs.yaml
    echo

    echo "GIT"
    git rev-parse HEAD 2>/dev/null || echo "not a git repo"
    git status --short 2>/dev/null || true

} > "$META"

# ------------------------------------------------------------
# CAN state BEFORE run.
# ------------------------------------------------------------

ip -details -statistics link show can0 \
    > "$RUN_DIR/can_state_before.txt"

# ------------------------------------------------------------
# Start completely passive raw CAN capture.
# -L gives absolute timestamps.
# ------------------------------------------------------------

echo "Starting passive CAN logger..."

candump -L can0 > "$CAN_LOG" &
CAN_PID=$!

sleep 0.5

if ! kill -0 "$CAN_PID" 2>/dev/null; then
    echo "ERROR: candump logger failed to start."
    exit 1
fi

echo "CAN logger PID: $CAN_PID"
echo "CAN log: $CAN_LOG"
echo "Console log: $CONSOLE_LOG"
echo

cleanup() {

    echo
    echo "Stopping CAN logger..."

    kill "$CAN_PID" 2>/dev/null || true
    wait "$CAN_PID" 2>/dev/null || true

    ip -details -statistics link show can0 \
        > "$RUN_DIR/can_state_after.txt"

    {
        echo
        echo "end_timestamp=$(date +%Y%m%d_%H%M%S)"
        echo "can_log_bytes=$(stat -c%s "$CAN_LOG" 2>/dev/null || echo 0)"
        echo "console_log_bytes=$(stat -c%s "$CONSOLE_LOG" 2>/dev/null || echo 0)"
    } >> "$META"

    echo
    echo "============================================================"
    echo "RUN EVIDENCE SAVED"
    echo "============================================================"
    echo "$RUN_DIR"
}

trap cleanup EXIT

# ------------------------------------------------------------
# RUN ROBOT
#
# tee gives us the complete controller telemetry while still
# displaying it live.
#
# Ctrl+C continues to go to the Python controller, whose
# existing behavior is:
#
#     DISABLE ALL MOTORS + EXIT
#
# ------------------------------------------------------------

echo "============================================================"
echo "STARTING TRIX LARGE V2"
echo "J1 preposition: +102 deg relative"
echo "Slightly increased speeds"
echo "48 V / 15 A / CV expected"
echo "============================================================"
echo

python3 -u examples/trix_large_v2.py \
    2>&1 | tee "$CONSOLE_LOG"

ROBOT_RC=${PIPESTATUS[0]}

echo
echo "Robot process exit code: $ROBOT_RC" \
    | tee -a "$CONSOLE_LOG"

exit "$ROBOT_RC"
