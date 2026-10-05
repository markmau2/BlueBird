#!/usr/bin/env python3
"""Watch the OpenClaw TTS output directory and play new clips on the host speakers.

The Control UI renders TTS as a player widget that only starts on a user press --
there is no autoplay path in the bundle. This plays the same audio locally through
PipeWire instead, so replies are spoken without touching the browser.

Env:
  TTS_DIR        directory to watch (default ~/.openclaw/media/tool-speech-synthesis)
  POLL_SECONDS   poll interval (default 0.5)
  FFMPEG         ffmpeg binary (default ~/.local/bin/ffmpeg)
  PLAY_BACKLOG   "1" to also play clips that already existed at startup
"""

import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

HOME = Path.home()
TTS_DIR = Path(os.environ.get("TTS_DIR", HOME / ".openclaw/media/tool-speech-synthesis"))
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "0.5"))
FFMPEG = os.environ.get("FFMPEG", str(HOME / ".local/bin/ffmpeg"))
PLAY_BACKLOG = os.environ.get("PLAY_BACKLOG", "") == "1"
# Edge TTS returns speech around -20 dB mean, far quieter than the music and video
# that share this sink, so on the monitor's weak built-in speakers it reads as
# silence. Normalize to broadcast loudness before playback. Set to "" to disable.
# Measured on a 15 s Ava clip: raw -22.7 dB mean / -5.2 dB peak becomes -14.5 / -0.9,
# i.e. ~8 dB louder with peaks at the ceiling. Single-pass loudnorm only managed 4 dB
# because it cannot look ahead; speechnorm is built for this and streams fine.
PLAY_FILTER = os.environ.get(
    "PLAY_FILTER", "speechnorm=e=25:r=0.0005:l=1,volume=4dB,alimiter=limit=0.95"
)
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".opus", ".m4a", ".flac"}

play_queue: "queue.Queue[Path]" = queue.Queue()


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def stable_size(path: Path, tries: int = 20, delay: float = 0.15) -> bool:
    """Wait until the file stops growing, so we never decode a partial write."""
    last = -1
    for _ in range(tries):
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size > 0 and size == last:
            return True
        last = size
        time.sleep(delay)
    return last > 0


def play(path: Path) -> None:
    if not stable_size(path):
        log(f"skip (never settled): {path.name}")
        return
    # Decode to WAV on stdout, stream into PipeWire. pw-play's libsndfile
    # cannot be relied on for mp3, so ffmpeg always does the decoding.
    cmd = [FFMPEG, "-v", "error", "-i", str(path)]
    if PLAY_FILTER:
        cmd += ["-af", PLAY_FILTER]
    cmd += ["-ar", "48000", "-ac", "2", "-f", "wav", "-"]
    decode = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    player = subprocess.Popen(["pw-play", "-"], stdin=decode.stdout, stderr=subprocess.PIPE)
    if decode.stdout:
        decode.stdout.close()  # let ffmpeg see EPIPE if the player dies
    player_err = player.communicate()[1]
    decode.wait()
    decode_err = decode.stderr.read() if decode.stderr else b""
    if player.returncode != 0 or decode.returncode != 0:
        log(
            f"FAILED {path.name} ffmpeg={decode.returncode} pw-play={player.returncode} "
            f"{decode_err.decode(errors='replace').strip()} "
            f"{player_err.decode(errors='replace').strip()}"
        )
    else:
        log(f"played {path.name}")


def worker() -> None:
    """Single consumer: clips play one at a time, never over each other."""
    while True:
        path = play_queue.get()
        try:
            play(path)
        except Exception as exc:  # keep the daemon alive through any one bad clip
            log(f"error on {path.name}: {exc}")
        finally:
            play_queue.task_done()


def main() -> int:
    if not TTS_DIR.is_dir():
        log(f"watch dir does not exist: {TTS_DIR}")
        return 1
    if not Path(FFMPEG).exists():
        log(f"ffmpeg not found: {FFMPEG}")
        return 1

    seen = set()
    if not PLAY_BACKLOG:
        seen = {p.name for p in TTS_DIR.iterdir() if p.is_file()}
        log(f"ignoring {len(seen)} existing clip(s)")

    threading.Thread(target=worker, daemon=True).start()
    log(f"watching {TTS_DIR} every {POLL_SECONDS}s -> pw-play")

    while True:
        try:
            entries = sorted(
                (p for p in TTS_DIR.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS),
                key=lambda p: p.stat().st_mtime,
            )
        except FileNotFoundError:
            time.sleep(POLL_SECONDS)
            continue
        for path in entries:
            if path.name not in seen:
                seen.add(path.name)
                log(f"queued {path.name}")
                play_queue.put(path)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
