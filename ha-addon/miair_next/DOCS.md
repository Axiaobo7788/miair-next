# MiAir Next — Home Assistant OS

This App runs the upstream MiAir Next container under Home Assistant Supervisor.
It exposes compatible Xiaomi XiaoAI speakers as DLNA, AirPlay and Spotify
Connect receivers.

## Install

1. Open **Settings → Apps → Install app** in Home Assistant.
2. Open the repositories menu and add:
   `https://github.com/Axiaobo7788/miair-next`
3. Refresh the App store and install **MiAir Next**.
4. Start the App and use **Open Web UI**.
5. Complete MiAir Next's normal first-run setup and add the desired Xiaomi
   speakers.

## Network

The App deliberately uses Home Assistant's host network. MiAir Next requires
local multicast/broadcast discovery for DLNA and AirPlay, so a normal bridged
container network is not sufficient.

The Web UI listens on TCP 8300 on the HAOS host. Do not expose this port directly
to the public Internet.

Experimental AirPlay 2 also uses the ports required by Shairport Sync/NQPTP,
including mDNS and PTP. A port conflict with another host service may prevent
that experimental mode from starting. AirPlay 1/DLNA should be tested
independently before diagnosing AirPlay 2.

## Persistent data

Supervisor's private App data directory is mounted directly at `/app/data`,
which is the data path expected by MiAir Next. Accounts, keys, the SQLite
database and protocol configuration therefore survive App restarts and updates.

MiAir Next stores sensitive Xiaomi/Spotify credentials in this data. Treat HAOS
backups containing this App as sensitive.

## Updates

This wrapper currently uses upstream image `mrdeer1997/miair-next:0.10.1`.
The wrapper has its own version (`0.10.1-ha2`) so Home Assistant-specific fixes
can be released independently without modifying MiAir Next's application code.

When updating the pinned upstream image, validate both amd64 and aarch64 and
confirm that `/api/v1/health`, DLNA discovery and AirPlay discovery still work
on HAOS.

## Current limitations

- This first HAOS wrapper is experimental and has not yet been validated on the
  target HAOS host.
- The Web UI uses direct LAN access on port 8300 rather than Home Assistant
  Ingress. This avoids changing MiAir Next's absolute API/WebSocket paths and
  preserves its own authentication.
- The wrapper intentionally does not request privileged mode, Docker access,
  host D-Bus, or extra Linux capabilities.
- MiAir Next's experimental AirPlay 2 path does not guarantee acoustic
  synchronization with other receivers; Xiaomi speaker buffering remains
  outside the bridge's clock control.

If the App starts but discovery fails, first check for host-port conflicts and
verify that HAOS and the Xiaomi speakers are on the same multicast-capable LAN.

## Silent AirPlay playback on HAOS

If the AirPlay receiver is visible but the Xiaomi speaker produces no sound,
open the App configuration and set **HAOS LAN IP** to the Home Assistant
host IPv4 address reachable by the speaker (for example `192.168.1.20`).
The wrapper exports this value as `MIAIR_HOSTNAME` before starting MiAir Next.

MiAir Next uses that address in the HTTP audio URL that the Xiaomi speaker
pulls. A loopback, container, VPN or otherwise unreachable address can make
the AirPlay receiver discoverable while playback remains silent.
