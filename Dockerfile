# Hermes Portal – Webfrontend für den Hermes-Agent.
# Bauen:  docker build -t hermes-portal .
# Start:  docker run --rm -p 8090:8090 -v hermes_portal_data:/data hermes-portal
#
# Persistente Daten liegen in /data (config.json, chat.db, uploads).
# Co-located Mode: mounte zusätzlich den Austausch-Ordner und ~/.hermes:
#   -v /mnt/austausch:/mnt/austausch -v /root/.hermes:/root/.hermes
#
# Multi-Arch ready (linux/amd64 + linux/arm64).

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HP_DATA_DIR=/data \
    HP_CONFIG_FILE=/data/config.json

# Systempakete: curl für Healthcheck, ssh-Client (für SSH-Mode + Key-Gen), tini als PID-1
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl tini openssh-client tzdata locales && \
    sed -i 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=de_DE.UTF-8 LC_ALL=de_DE.UTF-8 TZ=Europe/Berlin

WORKDIR /app

# Dependencies separat installieren (besseres Layer-Caching)
COPY _wiki_server/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Applikationscode
COPY _wiki_server/ /app/

# Monaco-Editor (für Chat-Code-Editor) – einmalig herunterladen, dann offline nutzbar.
RUN python /app/scripts/fetch_monaco.py

# Persistentes Datenverzeichnis (Volume-Mount-Point)
RUN mkdir -p /data /data/uploads

VOLUME ["/data"]

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8090/api/refresh >/dev/null || exit 1

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["gunicorn", "--bind", "0.0.0.0:8090", "--workers", "2", "--threads", "4", \
     "--timeout", "180", "--access-logfile", "-", "wiki_app:app"]
