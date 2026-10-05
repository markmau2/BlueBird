#!/usr/bin/env python3
"""BlueBird unlock watcher.

Fires the BlueBird face check on the locked -> unlocked edge, so BlueBird
works on lock/unlock, not just full logout. Full-logout login is handled
separately by the autostart entry.

Two independent sources (either one is enough):
  1. org.gnome.ScreenSaver `ActiveChanged(b)` *signal* (session bus).
     Note: this interface has NO properties — watching PropertiesChanged on
     it never fires, which was the original bug.
  2. logind Session `LockedHint` property (system bus) as a backup.

Both feed one state machine, so an unlock seen by both sources fires once.
De-dup: a check is skipped while the previous check's process is alive.
Runs as a user systemd service (bluebird-watch.service).
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
LOG = os.path.join(LOG_DIR, "bluebird-watch.log")

UNLOCK_DELAY_MS = 1500  # let the desktop repaint before grabbing the camera

locked = False
child = None  # subprocess.Popen of the running check

# Strong refs to the bus connections. Gio.bus_get_sync() returns a shared
# connection GIO only holds weakly: if it's just a local, it gets finalized
# when the function returns and every signal subscription on it silently dies.
session_bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
system_bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)


def log(msg: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def trigger_check() -> bool:
    global child
    if child is not None and child.poll() is None:
        log("check already running — skipping")
        return GLib.SOURCE_REMOVE
    log("unlock -> triggering bluebird check")
    try:
        env = os.environ.copy()
        env["BLUEBIRD_NOW"] = "1"  # already unlocked; skip the login-settle wait
        child = subprocess.Popen(
            ["bash", CHECK],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as e:  # noqa: BLE001
        log(f"trigger failed: {e!r}")
    return GLib.SOURCE_REMOVE


def set_locked(now_locked: bool, source: str) -> None:
    global locked
    if now_locked == locked:
        return  # same state reported by the other source
    locked = now_locked
    log(f"{source}: {'LOCKED' if locked else 'UNLOCKED'}")
    if not locked:
        GLib.timeout_add(UNLOCK_DELAY_MS, trigger_check)


def watch_gnome_screensaver() -> None:
    def on_signal(_conn, _sender, _path, _iface, signal, params, *_):
        if signal == "ActiveChanged":
            set_locked(bool(params.unpack()[0]), "gnome-screensaver")

    bus = session_bus
    # sender=None on purpose: the well-known name org.gnome.ScreenSaver can be
    # owned by the standalone gjs helper (D-Bus activation race at login),
    # which never changes state. gnome-shell emits the real ActiveChanged from
    # its own connection, so match on path/interface/member only.
    bus.signal_subscribe(
        None, "org.gnome.ScreenSaver", "ActiveChanged", "/org/gnome/ScreenSaver",
        None, Gio.DBusSignalFlags.NONE, on_signal,
    )
    log("subscribed: org.gnome.ScreenSaver.ActiveChanged")


def watch_logind() -> None:
    bus = system_bus
    session_id = os.environ.get("XDG_SESSION_ID")
    try:
        if session_id:
            path = bus.call_sync(
                "org.freedesktop.login1", "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager", "GetSession",
                GLib.Variant("(s)", (session_id,)), None,
                Gio.DBusCallFlags.NONE, -1, None,
            ).unpack()[0]
        else:
            # systemd user services don't inherit XDG_SESSION_ID: use the
            # user's graphical "display" session.
            user = bus.call_sync(
                "org.freedesktop.login1", "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager", "GetUser",
                GLib.Variant("(u)", (os.getuid(),)), None,
                Gio.DBusCallFlags.NONE, -1, None,
            ).unpack()[0]
            path = bus.call_sync(
                "org.freedesktop.login1", user,
                "org.freedesktop.DBus.Properties", "Get",
                GLib.Variant("(ss)", ("org.freedesktop.login1.User", "Display")),
                None, Gio.DBusCallFlags.NONE, -1, None,
            ).unpack()[0][1]
    except Exception as e:  # noqa: BLE001
        log(f"logind backup unavailable: {e!r}")
        return
    if not path or path == "/":
        log("logind backup unavailable: no graphical session")
        return

    def on_props(_conn, _sender, _path, _iface, _signal, params, *_):
        iface, changed, _inv = params.unpack()
        if iface == "org.freedesktop.login1.Session" and "LockedHint" in changed:
            set_locked(bool(changed["LockedHint"]), "logind")

    bus.signal_subscribe(
        "org.freedesktop.login1", "org.freedesktop.DBus.Properties",
        "PropertiesChanged", path, None, Gio.DBusSignalFlags.NONE, on_props,
    )
    log(f"subscribed: logind LockedHint on {path}")


def main() -> int:
    global locked
    log("watcher started")
    try:
        # Ask gnome-shell itself, not whoever owns org.gnome.ScreenSaver.
        locked = bool(session_bus.call_sync(
            "org.gnome.Shell", "/org/gnome/ScreenSaver",
            "org.gnome.ScreenSaver", "GetActive", None, None,
            Gio.DBusCallFlags.NONE, -1, None,
        ).unpack()[0])
    except Exception as e:  # noqa: BLE001
        log(f"initial GetActive failed: {e!r}")
    log(f"initial state: {'LOCKED' if locked else 'UNLOCKED'}")

    watch_gnome_screensaver()
    watch_logind()
    log("watcher ready — waiting for lock/unlock events")
    try:
        GLib.MainLoop().run()
    except KeyboardInterrupt:
        pass
    log("watcher stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
