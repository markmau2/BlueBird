#!/usr/bin/env bash
# Login gate: run the face check once after desktop login and speak the result.
# Runs from ~/.config/autostart/bluebird-facecheck.desktop (GNOME/X11).
# Waits for the desktop to settle, then executes the check in the background
# so it never blocks the login session.

export PATH="/home/mrosas/.npm-global/bin:/home/mrosas/.local/bin:$PATH"
WORKSPACE="/home/mrosas/.openclaw/workspace"
PY="$WORKSPACE/.venv/bin/python"
LOG="$HOME/.openclaw/logs/bluebird-login-check.log"

# Let the session finish starting (screen, audio, display manager).
sleep 10

# Run the check detached; append to a log for later inspection.
(
  "$PY" "$WORKSPACE/face_check.py" 2>&1 | tee -a "$LOG"
) </dev/null >/dev/null 2>&1 &

disown
exit 0
