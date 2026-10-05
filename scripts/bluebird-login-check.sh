#!/usr/bin/env bash
# Login gate: run the face check once after desktop login and speak the result.
# Runs from ~/.config/autostart/bluebird-facecheck.desktop (GNOME/X11).
# Waits for the desktop to settle, then executes the check in the background
# so it never blocks the login session.

export PATH="/home/mrosas/.npm-global/bin:/home/mrosas/.local/bin:$PATH"
WORKSPACE="/home/mrosas/.openclaw/workspace"
PY="$WORKSPACE/.venv/bin/python"
LOG="$HOME/.openclaw/logs/bluebird-login-check.log"
NOTIFY="$WORKSPACE/.bluebird-last-run.txt"

# Let the session finish starting (screen, audio, display manager).
sleep 10

# Record that a login run started (visible to the user on unlock).
date -u +"RUN STARTED %Y-%m-%d %H:%M:%S UTC" > "$NOTIFY" 2>/dev/null

# Run the check detached; append to a log for later inspection.
(
  "$PY" "$WORKSPACE/face_check.py" 2>&1 | tee -a "$LOG"
  # Stamp the finished time next to the run marker.
  date -u +"RUN FINISHED %Y-%m-%d %H:%M:%S UTC" >> "$NOTIFY" 2>/dev/null
) </dev/null >/dev/null 2>&1 &

disown
exit 0
