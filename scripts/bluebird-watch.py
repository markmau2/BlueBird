#!/usr/bin/env python3
"""BlueBird unlock watcher.

Watches the GNOME screensaver's `active` property. When the session
transitions locked -> unlocked, fires the BlueBird face check — so BlueBird
works on *lock/unlock*, not just full logout.

Full-logout login is handled separately by the autostart entry; this daemon
handles locks. Runs as a user systemd service (bluebird-watch.service).

Uses system Python's pygobject (Gio). De-duplication via a busy-lock file
with a 5-min stale timeout.
"""
import os
import subprocess
import sys
import time

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

WORKSPACE = "/home/mrosas/.openclaw/workspace"
CHECK = os.path.join(WORKSPACE, "scripts/bluebird-login-check.sh")
LOG_DIR = os.path.join(os.path.expanduser("~"), ".openclaw", "logs")
BUSY_LOCK = os.path.join(LOG_DIR, ".bluebird-busy")
LOG = os.path.join(LOG_DIR, "bluebird-watch.log")

SS_BUS = "org.gnome.ScreenSaver"
SS_OBJ = "/org/gnome/ScreenSaver"
SS_IF = "org.gnome.ScreenSaver"


def log(msg: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def trigger_check() -> None:
    """Fire the BlueBird check once (guarded by a busy-lock)."""
    if os.path.exists(BUSY_LOCK):
        try:
            age = time.time() - os.path.getmtime(BUSY_LOCK)
        except OSError:
            age = 0
        if age < 300:
            log("check already running (busy lock < 5 min) — skipping")
            return
        log("stale busy lock — clearing")
        try:
            os.unlink(BUSY_LOCK)
        except OSError:
            pass

    os.makedirs(LOG_DIR, exist_ok=True)
    open(BUSY_LOCK, "a").close()
    log("unlock detected -> triggering bluebird check")
    try:
        env = os.environ.copy()
        env["BLUEBIRD_NOW"] = "1"  # already unlocked; skip the login-settle wait
        subprocess.Popen(
            ["bash", CHECK],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as e:  # noqa: BLE001
        log(f"trigger failed: {e!r}")
    finally:
        try:
            os.unlink(BUSY_LOCK)
        except OSError:
            pass


def main() -> int:
    os.makedirs(LOG_DIR, exist_ok=True)
    log("watcher started")

    # Create a DBus proxy for the screensaver. info can be None — the proxy
    # loads the interface from the bus at runtime.
    proxy = Gio.DBusProxy.new_for_bus_sync(
        Gio.BusType.SESSION,
        Gio.DBusProxyFlags.NONE,
        None,  # info (DBusInterfaceInfo) — None lets it introspect
        SS_BUS,
        SS_OBJ,
        SS_IF,
        None,
    )

    def on_props_changed(_proxy, changed: GLib.Variant, _invalid: object) -> None:
        d = changed.unpack()
        if "active" not in d:
            return
        active = bool(d["active"])
        log(f"state: active={active}")
        if not active:
            # locked -> unlocked edge
            GLib.timeout_add(1500, _defer)

    def _defer() -> bool:
        trigger_check()
        return GLib.SOURCE_REMOVE  # fire once

    proxy.connect("g-properties-changed", on_props_changed)
    log("watcher ready — waiting for lock/unlock events")

    try:
        GLib.MainLoop().run()
    except KeyboardInterrupt:
        pass
    log("watcher stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
