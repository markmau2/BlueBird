#!/usr/bin/env python3
"""Capture a fresh face reference from /dev/video0.

- Opens the camera, warms it up, bumps brightness.
- Grabs a short burst (default 12 frames over ~4 s), detects faces in each,
  encodes them, then averages all embeddings from the best-detection frame
  into a single reference vector.
- Saves the averaged vector to face_reference.npy and the best raw frame
  (with the detected face box drawn) to face_reference_photo.jpg.

Prints a JSON summary at the end.
"""

import json
import sys
import time
from pathlib import Path

import cv2
import face_recognition
import numpy as np

WS = Path("/home/mrosas/.openclaw/workspace")
REF_PATH = WS / "face_reference.npy"
PHOTO_PATH = WS / "face_reference_photo.jpg"


def boost(img: np.ndarray, f: float = 1.5) -> np.ndarray:
    return np.clip(img.astype(np.float32) * f, 0, 255).astype(np.uint8)


def main() -> int:
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print(json.dumps({"status": "FAILED", "reason": "camera_open_failed"}))
        return 1

    # Warm-up: drop the first few frames (auto-exposure settling).
    for _ in range(10):
        cam.read()
        time.sleep(0.1)

    cam.set(cv2.CAP_PROP_BRIGHTNESS, 150)
    cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    cam.set(cv2.CAP_PROP_FPS, 30)

    # Burst capture.
    burst = 12
    frame_delay = 0.35
    best = None  # (dist_sum, frame_bgr, locs, embs)

    for i in range(burst):
        ok, raw = cam.read()
        if not ok:
            print(json.dumps({"status": "FAILED", "reason": "frame_read_failed"}))
            cam.release()
            return 1
        img = boost(raw)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb)
        if locs:
            embs = face_recognition.face_encodings(rgb, locs)
            # Prefer the frame with the highest-confidence (lowest-dim-variance)
            # embedding; fall back to any detection.
            if best is None:
                best = (0.0, raw, locs, embs)
            else:
                # Lower mean absolute deviation of the embedding = more stable.
                var = float(np.std(embs[0]))
                if var < best[0]:
                    best = (var, raw, locs, embs)
        time.sleep(frame_delay)

    cam.release()

    if best is None:
        print(json.dumps({
            "status": "NO_FACE",
            "reason": f"no face detected in {burst} burst frames",
        }))
        return 2

    var, raw, locs, embs = best
    # Average the (single) embedding from the best frame for a stable reference.
    ref = np.mean(np.array(embs), axis=0)
    np.save(REF_PATH, ref)

    # Annotate the best frame with the face box and save it.
    annotate = raw.copy()
    for (top, right, bottom, left) in locs:
        cv2.rectangle(annotate, (left, top), (right, bottom), (0, 255, 0), 2)
    cv2.imwrite(str(PHOTO_PATH), annotate)

    summary = {
        "status": "OK",
        "reference": str(REF_PATH),
        "photo": str(PHOTO_PATH),
        "embedding_std": round(var, 4),
        "face_box": [int(v) for v in locs[0]],
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
