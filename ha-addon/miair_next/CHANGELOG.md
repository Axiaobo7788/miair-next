# Changelog

## 0.10.1-ha4

- Automatically select the HAOS IPv4 address from the default-route interface.
- Keep `host_ip` as an optional manual override instead of a required setting.
- Fall back to MiAir Next's own detection only if wrapper-level detection cannot find a usable address.
- Log the selected address and its source at startup.

## 0.10.1-ha3

- Add an optional HAOS LAN IP override and export it as `MIAIR_HOSTNAME`.
- Use the standard Supervisor `/data` path for persistent MiAir Next state.
- Add a wrapper entrypoint while preserving upstream Avahi/D-Bus and privilege-drop startup.
- Document the AirPlay-visible-but-silent recovery path.

## 0.10.1-ha2

- Fix Home Assistant Supervisor validation for the Web UI URL by using the required `[PORT:8300]` placeholder.
- This fixes the repository being accepted while the MiAir Next App itself was skipped from the App store.

## 0.10.1-ha1

- Add an experimental Home Assistant OS App wrapper.
- Pin the upstream MiAir Next 0.10.1 multi-architecture image.
- Use host networking for DLNA/AirPlay discovery.
- Persist MiAir Next data through Supervisor at `/app/data`.
- Add direct Web UI and health-watchdog integration.
- Keep the wrapper unprivileged and separate from upstream application code.
