#!/usr/bin/env python3
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

def make_proxy(name, obj, iface):
    return Gio.DBusProxy.new_for_bus_sync(
        Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE,
        None, name, obj, iface, None,
    )

def try_get(proxy, iface, prop):
    try:
        r = proxy.call_sync(
            "Get",
            GLib.Variant("(ss)", (iface, prop)),
            Gio.DBusCallFlags.NONE, -1, None,
        )
        return r.unpack()[0]
    except Exception as e:
        return f"ERR {e!r}"

def introspect(proxy):
    try:
        xml = proxy.call_sync(
            "Introspect", None,
            Gio.DBusCallFlags.NONE, -1, None,
        ).unpack()[0]
        import re
        props = re.findall(r'name="([^"]+)"\s+type="([^"]+)"[^>]*access="([^"]+)"', xml)
        sifs = re.findall(r'interface name="([^"]+)"', xml)
        return props, sifs, xml
    except Exception as e:
        return None, None, f"ERR {e!r}"

for name, obj, iface, prop in [
    ("org.gnome.ScreenSaver", "/org/gnome/ScreenSaver", "org.gnome.ScreenSaver", "active"),
    ("org.freedesktop.ScreenSaver", "/org/freedesktop/ScreenSaver", "org.freedesktop.ScreenSaver", "Active"),
]:
    print(f"=== {name} / {obj} / {iface} ===")
    try:
        p = make_proxy(name, obj, iface)
    except Exception as e:
        print("  proxy create ERR:", repr(e)); print(); continue
    print("  prop", prop, "=>", try_get(p, iface, prop))
    props, sifs, xml = introspect(p)
    print("  sub-interfaces:", sifs)
    print("  properties:", props)
    if isinstance(xml, str) and xml.startswith("ERR"):
        print("  (introspect failed)")
    print()
