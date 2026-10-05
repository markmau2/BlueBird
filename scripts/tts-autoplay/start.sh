#!/usr/bin/env bash
# Start (or restart) the TTS autoplay watcher.
#
#   ./start.sh              -> watches ~/.openclaw/media/tool-speech-synthesis
#   PLAY_BACKLOG=1 ./start.sh   -> also plays clips that already exist
#
# Plays every new TTS clip on the host speakers via PipeWire. This exists
# because the Control UI's audio bubble only starts on a user press.
set -euo pipefail

cd "$(dirname "$0")"

LOG="${LOG:-/tmp/tts-autoplay.log}"

# Replace any previous instance. Match the interpreter + script only, and never
# this script or its own process tree, or we kill ourselves before starting.
pids=$(pgrep -f '^python3 watch\.py$' 2>/dev/null | grep -v "^$$\$" || true)
if [ -n "${pids:-}" ]; then
  echo "stopping existing watcher: $(echo $pids | tr '\n' ' ')"
  kill $pids 2>/dev/null || true
  for _ in 1 2 3 4 5; do
    pgrep -f '^python3 watch\.py$' >/dev/null 2>&1 || break
    sleep 1
  done
  pkill -9 -f '^python3 watch\.py$' 2>/dev/null || true
fi

nohup python3 watch.py >"$LOG" 2>&1 &
sleep 2

if pgrep -f '^python3 watch\.py$' >/dev/null 2>&1; then
  echo "tts autoplay watcher up (pid $(pgrep -f '^python3 watch\.py$' | tr '\n' ' '))"
  cat "$LOG"
  echo "log: $LOG"
else
  echo "FAILED to start. Log follows:" >&2
  cat "$LOG" >&2
  exit 1
fi
