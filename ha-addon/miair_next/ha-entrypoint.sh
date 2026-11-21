#!/bin/sh
set -eu

OPTIONS_FILE="/data/options.json"

# Resolve the address advertised to Xiaomi speakers.
# Priority: explicit user override -> HAOS host default-route interface ->
# MiAir Next built-in detection.  host_network=true means /proc/net/route and
# interface ioctls below describe the HAOS host network namespace.
detect_result="$(python3 - "$OPTIONS_FILE" <<'PY'
import fcntl
import ipaddress
import json
import os
import socket
import struct
import sys

options_path = sys.argv[1]
try:
    with open(options_path, encoding="utf-8") as f:
        options = json.load(f)
except Exception:
    options = {}

manual = str(options.get("host_ip") or "").strip()

def usable_ipv4(value):
    try:
        addr = ipaddress.IPv4Address(value)
    except Exception:
        return False
    return not (
        addr.is_loopback
        or addr.is_link_local
        or addr.is_unspecified
        or addr.is_multicast
    )

def iface_ipv4(name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        request = struct.pack("256s", name.encode("utf-8")[:15])
        response = fcntl.ioctl(sock.fileno(), 0x8915, request)  # SIOCGIFADDR
        return socket.inet_ntoa(response[20:24])
    except Exception:
        return ""
    finally:
        sock.close()

if manual:
    if usable_ipv4(manual):
        print(f"manual|{manual}|user")
        raise SystemExit
    print(
        f"[MiAir Next HAOS] warning: invalid manual host_ip={manual}; falling back to automatic detection",
        file=sys.stderr,
    )

virtual_markers = (
    "docker", "veth", "tailscale", "zerotier", "tun", "tap", "wg",
    "hassio", "br-", "virbr", "vmnet",
)
routes = []
try:
    with open("/proc/net/route", encoding="ascii") as f:
        next(f, None)
        for line in f:
            fields = line.split()
            if len(fields) < 8:
                continue
            iface, destination, _gateway, flags_hex, _refcnt, _use, metric_text = fields[:7]
            if destination != "00000000":
                continue
            try:
                flags = int(flags_hex, 16)
                metric = int(metric_text)
            except ValueError:
                continue
            if not (flags & 0x1):  # RTF_UP
                continue
            ip = iface_ipv4(iface)
            if not ip or not usable_ipv4(ip):
                continue
            virtual = any(marker in iface.lower() for marker in virtual_markers)
            routes.append((1 if virtual else 0, metric, iface, ip))
except Exception:
    pass

if routes:
    routes.sort()
    _virtual, _metric, iface, ip = routes[0]
    print(f"auto|{ip}|default-route:{iface}")
    raise SystemExit

# Last wrapper-level fallback: ask the kernel which source address it would use.
for target in ("8.8.8.8", "1.1.1.1"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((target, 53))
        ip = sock.getsockname()[0]
        if usable_ipv4(ip):
            print(f"auto|{ip}|kernel-route")
            raise SystemExit
    except Exception:
        pass
    finally:
        sock.close()

print("fallback||miair")
PY
)"

mode="$(printf "%s" "$detect_result" | cut -d "|" -f 1)"
host_ip="$(printf "%s" "$detect_result" | cut -d "|" -f 2)"
source="$(printf "%s" "$detect_result" | cut -d "|" -f 3-)"

case "$mode" in
  manual)
    export MIAIR_HOSTNAME="$host_ip"
    printf '%s\n' "[MiAir Next HAOS] LAN address: $MIAIR_HOSTNAME (manual override)"
    ;;
  auto)
    export MIAIR_HOSTNAME="$host_ip"
    printf '%s\n' "[MiAir Next HAOS] LAN address: $MIAIR_HOSTNAME (auto, $source)"
    ;;
  *)
    printf '%s\n' "[MiAir Next HAOS] wrapper could not determine a LAN address; using MiAir Next auto-detection"
    unset MIAIR_HOSTNAME || true
    ;;
esac

export MIAIR_DATA="${MIAIR_DATA:-/data}"

# Preserve upstream discovery, Avahi/D-Bus setup and privilege drop.
exec /bin/sh /app/backend/scripts/entrypoint.sh "$@"
