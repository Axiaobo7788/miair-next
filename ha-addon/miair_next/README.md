# MiAir Next for Home Assistant OS

This is a thin Home Assistant App wrapper around the upstream MiAir Next container.

It keeps the MiAir Next runtime unchanged while letting Home Assistant OS manage
its lifecycle and persistent data. Host networking is enabled because MiAir Next
uses multicast discovery for DLNA and AirPlay.

The wrapper currently pins upstream MiAir Next 0.10.1 and is marked experimental
until it has been validated on a real HAOS installation.
