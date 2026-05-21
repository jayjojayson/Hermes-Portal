ARG BUILD_FROM
FROM $BUILD_FROM

# Home-Assistant Base hat bereits Python + bashio.
# Wir installieren Python-Deps und kopieren das Portal in /app.

RUN apk add --no-cache python3 py3-pip openssh-client tzdata curl tini

WORKDIR /app

COPY rootfs/requirements.txt /tmp/requirements.txt
RUN pip install --break-system-packages --no-cache-dir -r /tmp/requirements.txt

COPY rootfs/app/ /app/
COPY rootfs/run.sh /run.sh
RUN chmod +x /run.sh

ENV HP_DATA_DIR=/data \
    HP_CONFIG_FILE=/data/config.json

EXPOSE 8090
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/run.sh"]
