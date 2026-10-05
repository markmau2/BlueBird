#!/usr/bin/env python3
"""Camera face screening with robust retry and TTS voice output."""
import subprocess, sys, time

sys.path.insert(0, '/home/mrosas/.openclaw/workspace/.venv/lib/python3.10/site-packages')
import numpy as np
import face_recognition
import cv2

REF = np.load('/home/mrosas/.openclaw/workspace/face_reference.npy')
TOL = 0.5
TTS = 'openclaw'
TTS_ARGS = ['infer', 'tts', 'convert', '--text', '', '--json']

def speak(text: str):
    try:
        r = subprocess.run(
            [TTS] + TTS_ARGS[:3] + [text] + TTS_ARGS[4:],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and r.stdout.strip():
            print(f"TTS_OK len={len(r.stdout)}", flush=True)
    except Exception as e:
        print(f"TTS_FAIL {e}", flush=True)

# Camera open with retries
cap = None
for attempt in range(10):
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print(f"camera_open attempt={attempt+1}", flush=True)
        break
    cap.release()
    print(f"cam_retry {attempt+1}", flush=True)
    time.sleep(3)

if cap is None or not cap.isOpened():
    print("CAM_FAILED", flush=True)
    sys.exit(1)

cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)
BOOST = 1.5
start = time.time()
DURATION = 300
INTERVAL = 20

try:
    while time.time() - start < DURATION:
        t0 = time.time()
        ok, frame = cap.read()
        if not ok:
            print(f"{time.strftime('%H:%M:%S')} FRAME_FAIL", flush=True)
        else:
            bgr = np.clip(frame.astype(np.float32) * BOOST, 0, 255).astype(np.uint8)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_encodings(rgb, model='hog')
            if faces:
                best = min(np.linalg.norm(np.array(f) - REF) for f in faces)
                label = "MATCH" if best <= TOL else "STRANGER"
                print(f"{time.strftime('%H:%M:%S')} faces={len(faces)} dist={best:.3f} -> {label}", flush=True)
                if label == "MATCH":
                    print("SPEAK_GREETING", flush=True)
                    speak("Good morning Mauricio!")
                else:
                    print("SPEAK_CHALLENGE", flush=True)
                    speak("Who are you?")
            else:
                print(f"{time.strftime('%H:%M:%S')} NO_FACE", flush=True)
        elapsed = time.time() - t0
        sleep = max(0, INTERVAL - elapsed)
        if time.time() + sleep - start >= DURATION:
            break
        time.sleep(sleep)
finally:
    cap.release()
    print("DONE camera released", flush=True)
