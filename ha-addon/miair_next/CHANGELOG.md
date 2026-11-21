# Changelog

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
