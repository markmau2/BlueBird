#!/home/mrosas/.openclaw/workspace/.venv/bin/python
"""Face screening: compare webcam frame against a saved reference face.

- Same person  -> "Good morning!" (spoken aloud via TTS)
- Different person -> "I don't know you"
- No face      -> "No face detected"

Usage:
  face_screen.py register            # capture reference face
  face_screen.py check               # single check
  face_screen.py loop [seconds]      # continuous; default 1s interval
  face_screen.py run <minutes>       # run for N minutes, 5s interval
"""
import sys, time, os
import numpy as np
import face_recognition

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
REF_PATH = os.path.join(WORKSPACE, "face_reference.npy")
TOLERANCE = 0.5
BOOST = 1.5
GREETING = "Good morning Mauricio!"
CHALLENGE = "Who Are you?"


def grab():
    import cv2
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap = cv2.VideoCapture("/dev/video0")
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("could not read webcam frame")
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb = np.clip(rgb.astype(np.float32) * BOOST, 0, 255).astype(np.uint8)
    return rgb


def check():
    rgb = grab()
    locs = face_recognition.face_locations(rgb, model="cnn")
    if not locs:
        return "No face detected", None
    encs = face_recognition.face_encodings(rgb, locs)
    ref = np.load(REF_PATH).reshape(-1, 128)
    d = float(face_recognition.face_distance(ref, encs).min())
    if d < TOLERANCE:
        return "Good morning!", d
    return "I don't know you", d


def register():
    rgb = grab()
    locs = face_recognition.face_locations(rgb, model="cnn")
    if not locs:
        print("No face detected. Adjust and retry.")
        sys.exit(1)
    encs = face_recognition.face_encodings(rgb, locs)
    np.save(REF_PATH, np.array(encs).astype(np.float64))
    print(f"Registered {len(encs)} face(s) -> {REF_PATH}")


def loop(interval=1):
    print(f"Screening loop started (every {interval}s). Ctrl+C to stop.")
    while True:
        verdict, d = check()
        tag = f" dist={d:.3f}" if d is not None else ""
        print(time.strftime("%H:%M:%S"), verdict, tag, flush=True)
        if verdict == "Good morning!":
            print(f"[[tts:{GREETING}]]", flush=True)
        elif verdict == "I don't know you":
            print(f"[[tts:{CHALLENGE}]]", flush=True)
        time.sleep(interval)


def run(minutes, interval=15):
    duration = minutes * 60
    start = time.time()
    while time.time() - start < duration:
        verdict, d = check()
        tag = f" dist={d:.3f}" if d is not None else ""
        print(time.strftime("%H:%M:%S"), verdict, tag, flush=True)
        if verdict == "Good morning!":
            print(f"[[tts:{GREETING}]]", flush=True)
        elif verdict == "I don't know you":
            print(f"[[tts:{CHALLENGE}]]", flush=True)
        time.sleep(15)
    print("done", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "register":
        register()
    elif cmd == "check":
        v, d = check()
        print(v, (f"dist={d:.3f}" if d is not None else ""))
    elif cmd == "loop":
        interval = float(sys.argv[2]) if len(sys.argv) > 2 else 1
        loop(interval)
    elif cmd == "run":
        run(float(sys.argv[2]) if len(sys.argv) > 2 else 1)
    else:
        print(__doc__)
