#!/usr/bin/env python3
"""5-min camera face screening, 20s intervals, spoken TTS responses."""
import time, sys, json, subprocess, glob, os
import face_recognition, cv2, numpy as np

REF = np.load('face_reference.npy')
TOL = 0.5
TTS_DIR = os.path.expanduser('~/.openclaw/media/tool-speech-synthesis')

def boost(img, f=1.5):
    return np.clip(img.astype(np.float32) * f, 0, 255).astype(np.uint8)

def try_open():
    for _ in range(3):
        cam = cv2.VideoCapture(0)
        ok, _ = cam.read()
        if ok:
            return cam
        cam.release()
        time.sleep(2)
    return None

def speak(text):
    """Convert text to speech via openclaw CLI; watcher plays the clip."""
    try:
        r = subprocess.run(
            ['openclaw', 'infer', 'tts', 'convert', '--text', text, '--json'],
            capture_output=True, text=True, timeout=30
        )
        out = r.stdout + r.stderr
        if '"ok": true' in out:
            return True
        print(f'  TTS_ERR: {out[:200]}', flush=True)
    except Exception as e:
        print(f'  TTS_EXC: {e}', flush=True)
    return False

cam = try_open()
if cam is None:
    print('CAM_FAILED', flush=True)
    sys.exit(1)

time.sleep(0.5)
cam.set(cv2.CAP_PROP_BRIGHTNESS, 150)

t0 = time.time()
n = 0
results = []
try:
    while time.time() - t0 < 300:
        ok, raw = cam.read()
        if not ok:
            print(f'{time.strftime("%H:%M:%S")} CAM_ERR', flush=True)
            time.sleep(2)
            continue
        img = boost(raw)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb)
        if not locs:
            print(f'{time.strftime("%H:%M:%S")} NO_FACE', flush=True)
        else:
            embs = face_recognition.face_encodings(rgb, locs)
            d = min(float(np.linalg.norm(e - REF)) for e in embs)
            if d <= TOL:
                print(f'{time.strftime("%H:%M:%S")} MATCH dist={d:.3f}', flush=True)
                speak("Good to see you, Mauricio.")
                results.append('MATCH')
            else:
                print(f'{time.strftime("%H:%M:%S")} STRANGER dist={d:.3f}', flush=True)
                speak("Who are you? Please identify yourself.")
                results.append('STRANGER')
        n += 1
        time.sleep(20)
finally:
    cam.release()
    m = results.count('MATCH'); s = results.count('STRANGER')
    print(f'DONE checks={n} match={m} stranger={s} camera_released', flush=True)
    sys.stdout.flush()
    sys.exit(0)
