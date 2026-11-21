#!/bin/sh
set -eu

OPTIONS_FILE="/data/options.json"
host_ip=""
if [ -f "$OPTIONS_FILE" ]; then
    host_ip="$(python3 - "$OPTIONS_FILE" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as f:
        value = json.load(f).get("host_ip", "")
except Exception:
    value = ""

print(str(value or "").strip())
PY
)"
fi

if [ -n "$host_ip" ]; then
    export MIAIR_HOSTNAME="$host_ip"
    printf '%s\n' "[MiAir Next HAOS] forcing LAN address: $MIAIR_HOSTNAME"
else
    printf '%s\n' "[MiAir Next HAOS] no LAN address override configured; using MiAir Next auto-detection"
fi

export MIAIR_DATA="${MIAIR_DATA:-/data}"

# Preserve upstream discovery, Avahi/D-Bus setup and privilege drop.
exec /bin/sh /app/backend/scripts/entrypoint.sh "$@"
