# BlueBird 🕊️

Face-recognition door check for a single owner, spoken aloud on the host speakers.

One webcam, one face on file. When the owner is in front of the camera, it
greets them by name. When anyone else is, or nobody is, it says so.

## How it works

1. `face_check.py` opens the camera, runs 5 rapid frame checks (0.5 s apart),
   and matches each detected face against the stored owner encoding.
2. **PASS** (3+ matches under the 0.5 distance threshold) → speaks
   "Nice to see you Mauricio!"
3. **FAIL** → speaks "You are not Mauricio!"
4. Speech is generated via OpenClaw TTS and played automatically by the
   `tts-autoplay` watcher (PipeWire), no clicking required.

## Files

| File | Purpose |
|---|---|
| `face_check.py` | Main one-shot check: 5 checks, PASS/FAIL, TTS trigger |
| `face_capture.py` | Capture and save a new reference photo/encoding |
| `face_reference.npy` | The owner's face encoding (the only face that passes) |
| `face_reference_photo.jpg` | The reference photo it was made from |
| `scripts/tts-autoplay/watch.py` | Watches the TTS output dir, plays new clips |
| `scripts/tts-autoplay/start.sh` | Starts the watcher as a user service |

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Record a reference (point the camera at the owner)
.venv/bin/python face_capture.py

# Run a check
.venv/bin/python face_check.py
```

## Notes

- Camera index and brightness/boost are tuned in-script for a C920 on a
  monitor with weak built-in speakers; adjust `CAMERA_INDEX`,
  `CAP_PROP_BRIGHTNESS`, and `BOOST` to match your hardware.
- Match threshold is `0.5` (cosine distance); anything closer matches.
- Only one process may hold the webcam at a time — close other camera apps.
