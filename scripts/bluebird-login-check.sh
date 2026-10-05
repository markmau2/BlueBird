#!/usr/bin/env bash
# Login gate: run the face check once after desktop login.
# Runs from ~/.config/autostart/bluebird-facecheck.desktop (GNOME/X11).
# Waits for the desktop to settle, then runs the check (blocking), and shows
# a desktop popup + TTS voice with the result.
#
# Robust in both a real GNOME autostart session and a manual/cron invocation:
# all output goes to the log file; no reliance on inherited TTY/stdout.

export PATH="/home/mrosas/.npm-global/bin:/home/mrosas/.local/bin:$PATH"
WORKSPACE="/home/mrosas/.openclaw/workspace"
PY="$WORKSPACE/.venv/bin/python"
LOG_DIR="$HOME/.openclaw/logs"
LOG="$LOG_DIR/bluebird-login-check.log"
NOTIFY_FILE="$LOG_DIR/bluebird-last-result.txt"
MARKER="$WORKSPACE/.bluebird-last-run.txt"
WORK_OUT="$LOG_DIR/.bluebird-work.out"

mkdir -p "$LOG_DIR"

# Let the session finish starting (screen, audio, display manager).
# Skip the wait when run manually (BLUEBIRD_NOW=1) so debugging is fast.
if [ -z "${BLUEBIRD_NOW:-}" ]; then
  sleep 10
fi

# Record that a login run started (visible to the user on unlock).
date -u +"RUN STARTED %Y-%m-%d %H:%M:%S UTC" > "$MARKER" 2>/dev/null

# Run the check, capturing all output to a work file (and the persistent log).
"$PY" "$WORKSPACE/face_check.py" > "$WORK_OUT" 2>&1
tee -a "$LOG" < "$WORK_OUT" >/dev/null

# Parse the result.
if grep -q "^PASS$" "$WORK_OUT"; then
  RESULT="PASS"
elif grep -q "^FAIL$" "$WORK_OUT"; then
  RESULT="FAIL"
else
  RESULT="UNKNOWN"
fi

echo "$RESULT" > "$NOTIFY_FILE" 2>/dev/null
date -u +"RUN FINISHED %Y-%m-%d %H:%M:%S UTC -> $RESULT" >> "$MARKER" 2>/dev/null

# Show a desktop popup (zenity/notify-send). No-op headless.
bash "$WORKSPACE/scripts/bluebird-notify.sh" "$RESULT" >/dev/null 2>&1 || true

exit 0
