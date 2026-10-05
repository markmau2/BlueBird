#!/usr/bin/env bash
# BlueBird login notification: display a desktop popup with the check result.
# Called by bluebird-login-check.sh after face_check.py finishes.
# Uses zenity (GNOME) or notify-send (any X11/desktop).

RESULT_FILE="$HOME/.openclaw/logs/bluebird-last-result.txt"
NOTIFY="$1"  # "PASS" or "FAIL"

# Determine message
if [ "$NOTIFY" = "PASS" ]; then
  TITLE="BlueBird ✓"
  MSG="Nice to see you, Mauricio!"
  ICON="dialog-information"
else
  TITLE="BlueBird ✗"
  MSG="You are not Mauricio!"
  ICON="dialog-error"
fi

# Try zenity first (GNOME), fall back to notify-send
if command -v zenity &>/dev/null; then
  zenity --info --title="$TITLE" --text="$MSG" --icon-name="$ICON" &
elif command -v notify-send &>/dev/null; then
  notify-send -i "$ICON" "$TITLE" "$MSG" &
fi
