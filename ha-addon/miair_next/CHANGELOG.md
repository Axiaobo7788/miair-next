# Changelog

## 0.10.1-ha6

- Mirror MiAirX's safer AirPlay boundary: accept RECORD and buffer first, then issue the Xiaomi play command only after non-silent decoded PCM exists.
- Log first decoded PCM peak/RMS/non-zero sample evidence so silent/decryption failures are distinguishable from Xiaomi playback failures.
- Log the first MP3 encoder output and total encoded bytes sent.
- Re-query Xiaomi playback state after the play command and log speaker status, volume, HTTP client count, PCM bytes, decode errors and decrypt failures.
- Add upstream-source regression tests and HAOS smoke coverage for the audio-ready boundary.

## 0.10.1-ha5

- Add selectable AirPlay downstream format: `auto`, `wav`, or `mp3`.
- In `auto`, prefer MP3 for S12A plus existing known WAV-problematic models; keep WAV elsewhere.
- Apply the compatibility change as a thin build-time overlay on upstream 0.10.1 rather than forking unrelated runtime code.
- Log the selected downstream format at startup and per AirPlay receiver.

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
