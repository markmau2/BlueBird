#!/usr/bin/env python3
"""Screen the camera for 5 minutes, checking every 20s.
Ensures camera is released on ALL exit paths (try/finally).
"""
import time
import sys
import face_recognition
import cv2
import numpy as np

REF = np.load('face_reference.npy')
TOL = 0.5

def boost(img, f=1.5):
    return np.clip(img.astype(np.float32) * f, 0, 255).astype(np.uint8)

def try_open():
    for attempt in range(3):
        cam = cv2.VideoCapture(0)
        ok, _ = cam.read()
        if ok:
            return cam
        cam.release()
        time.sleep(2)
    return None

cam = try_open()
if cam is None:
    print('CAM_FAILED', flush=True)
    sys.exit(1)

time.sleep(0.5)
cam.set(cv2.CAP_PROP_BRIGHTNESS, 150)

t0 = time.time()
n = 0
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
            who = 'MATCH' if d <= TOL else 'STRANGER'
            print(f'{time.strftime("%H:%M:%S")} {who} dist={d:.3f}', flush=True)
        n += 1
        time.sleep(20)
finally:
    # ALWAYS release the camera, no matter how we exit
    cam.release()
    print(f'DONE checks={n} camera_released', flush=True)
    sys.stdout.flush()
    sys.exit(0)
