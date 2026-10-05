#!/usr/bin/env bash
# BlueBird status: show whether the login-triggered face check ran,
# when it ran, and the latest PASS/FAIL result.
#
#   ./status.sh           -> summary
#   ./status.sh --log     -> last 30 lines of the run log

WORKSPACE="/home/mrosas/.openclaw/workspace"
NOTIFY="$WORKSPACE/.bluebird-last-run.txt"
LOG="$HOME/.openclaw/logs/bluebird-login-check.log"

echo "=== BlueBird login-check status ==="

if [ -f "$NOTIFY" ]; then
  echo "Login run marker:"
  cat "$NOTIFY"
else
  echo "Login run marker: (none yet — the check has not run since login)"
fi

echo
if [ -f "$LOG" ]; then
  echo "Last result (from log):"
  grep -E "^(PASS|FAIL|RESULT|CAM_FAILED)" "$LOG" | tail -3
  echo
  echo "Log size: $(wc -l < "$LOG") lines, last updated: $(stat -c %y "$LOG" 2>/dev/null | cut -d'.' -f1)"
else
  echo "Log: (no log file yet — the check has not run)"
fi

if [ "$1" = "--log" ]; then
  echo
  echo "=== Last 30 lines of log ==="
  tail -30 "$LOG"
fi
