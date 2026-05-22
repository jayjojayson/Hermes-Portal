ARG BUILD_FROM
FROM $BUILD_FROM

# Home-Assistant-Add-on: Hermes Portal
# ------------------------------------
# Baut sich self-contained — zieht die Portal-Sourcen direkt aus dem Git-Tag
# `v${BUILD_VERSION}` (BUILD_VERSION wird von HA-Supervisor automatisch aus
# `config.yaml` → `version:` gesetzt). Damit gibt es keine vorgenerierten
# rootfs/-Artefakte im Repo und der Build läuft 1:1 wie auf einem Maintainer-PC.

ARG BUILD_VERSION

# OCI-Labels (vorher in der seit HA 2024 deprecated build.yaml)
LABEL org.opencontainers.image.title="Hermes Portal" \
      org.opencontainers.image.description="Webfrontend für den Hermes-Agent" \
      org.opencontainers.image.source="https://github.com/jayjojayson/Hermes-Portal" \
      org.opencontainers.image.licenses="Apache-2.0"

RUN apk add --no-cache python3 py3-pip openssh-client tzdata curl tini git

WORKDIR /app

# Portal-Sourcen aus dem getaggten Release ziehen
RUN git clone --depth 1 --branch "v${BUILD_VERSION}" \
        https://github.com/jayjojayson/Hermes-Portal.git /tmp/portal \
    && cp -a /tmp/portal/_wiki_server/. /app/ \
    && rm -rf /tmp/portal

# Python-Dependencies installieren (Alpine: --break-system-packages nötig)
RUN pip install --break-system-packages --no-cache-dir -r /app/requirements.txt

# Monaco-Editor offline-bundeln (~14 MB JS/CSS für Chat-Code-Editor)
RUN python3 /app/scripts/fetch_monaco.py

# HA-spezifischer Entry-Point (bashio-Wrapper, liest Add-on-Optionen)
COPY run.sh /run.sh
RUN chmod +x /run.sh

ENV HP_DATA_DIR=/data \
    HP_CONFIG_FILE=/data/config.json

EXPOSE 8090
# Auf Alpine landet `tini` unter /sbin/tini (nicht /usr/bin/tini wie auf Debian).
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/run.sh"]
