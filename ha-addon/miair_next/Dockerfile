# syntax=docker/dockerfile:1

# Keep the Home Assistant wrapper independent from MiAir Next's source tree.
# Updating the upstream runtime only requires bumping this pinned image tag and
# the app version in config.yaml.
FROM mrdeer1997/miair-next:0.10.1

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL org.opencontainers.image.title="MiAir Next Home Assistant App"
LABEL org.opencontainers.image.source="https://github.com/Axiaobo7788/miair-next"
LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="app" \
      io.hass.arch="${BUILD_ARCH}"

COPY patch_airplay_format.py /tmp/patch_airplay_format.py
RUN python3 /tmp/patch_airplay_format.py && rm /tmp/patch_airplay_format.py

COPY ha-entrypoint.sh /usr/local/bin/ha-entrypoint.sh
RUN chmod 0755 /usr/local/bin/ha-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/ha-entrypoint.sh"]
CMD ["python", "run.py"]
