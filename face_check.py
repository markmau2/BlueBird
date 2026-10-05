#!/usr/bin/env python3
"""Single face detection with 5 rapid checks (0.5s interval).
Pass = 3+ MATCH, Fail = 2 or fewer MATCH.
TTS voice output on result."""
import subprocess, sys, time

sys.path.insert(0, '/home/mrosas/.openclaw/workspace/.venv/lib/python3.10/site-packages')
import numpy as np
import face_recognition
import cv2

# One row per reference (e.g. daylight + night). A face matches if it is
# within TOL of ANY reference.
REF = np.load('/home/mrosas/.openclaw/workspace/face_reference.npy').reshape(-1, 128)
TOL = 0.5
BOOST = 1.5
CHECKS = 5
INTERVAL = 0.5

# Camera open with retries
cap = None
for attempt in range(10):
    cap = cv2.VideoCapture(1)
    if cap.isOpened():
        print(f"camera_open attempt={attempt+1}", flush=True)
        break
    cap.release()
    print(f"cam_retry {attempt+1}", flush=True)
    time.sleep(2)

if cap is None or not cap.isOpened():
    print("CAM_FAILED", flush=True)
    sys.exit(1)

cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)
# Drop frames while auto-exposure settles after the brightness change, so all
# checks see the same image the reference was captured with.
for _ in range(15):
    cap.read()

def speak(text: str):
    try:
        r = subprocess.run(
            ['openclaw', 'infer', 'tts', 'convert', '--text', text, '--json'],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and r.stdout.strip():
            print(f"TTS_OK", flush=True)
    except Exception as e:
        print(f"TTS_FAIL {e}", flush=True)

try:
    matches = 0
    for i in range(CHECKS):
        ok, frame = cap.read()
        if not ok:
            print(f"check {i+1}: FRAME_FAIL", flush=True)
            time.sleep(INTERVAL)
            continue
        bgr = np.clip(frame.astype(np.float32) * BOOST, 0, 255).astype(np.uint8)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_encodings(rgb, model='hog')
        if faces:
            best = min(np.linalg.norm(REF - np.array(f), axis=1).min() for f in faces)
            label = "MATCH" if best <= TOL else "STRANGER"
            print(f"check {i+1}: {label} dist={best:.3f}", flush=True)
            if label == "MATCH":
                matches += 1
        else:
            print(f"check {i+1}: NO_FACE", flush=True)
        time.sleep(INTERVAL)

    print(f"RESULT: {matches}/{CHECKS} matches", flush=True)
    if matches >= 3:
        print("PASS", flush=True)
        speak("Nice to see you Mauricio!")
    else:
        print("FAIL", flush=True)
        speak("You are not Mauricio!")
finally:
    cap.release()
    print("DONE camera released", flush=True)
