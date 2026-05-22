#!/usr/bin/env bashio
# HA-Add-On Startup – initialisiert config.json aus den Add-on-Optionen.
set -e

CONFIG_FILE="${HP_CONFIG_FILE:-/data/config.json}"
DEFAULTS="/app/config.defaults.json"

if [ ! -f "$CONFIG_FILE" ]; then
    bashio::log.info "Erste Inbetriebnahme – kopiere Defaults nach ${CONFIG_FILE}"
    cp "$DEFAULTS" "$CONFIG_FILE"
fi

# Add-on-Optionen aus HA in ENV-Variablen mappen (überschreiben config.json beim Start)
export HP_AGENT_NAME="$(bashio::config 'agent_name')"
export HP_USER_NAME="$(bashio::config 'user_name')"
export HP_CONNECTION_MODE="$(bashio::config 'connection_mode')"
export HP_AGENT_HOST="$(bashio::config 'agent_host')"
export HP_SSH_USER="$(bashio::config 'ssh_user')"
export HP_SSH_PORT="$(bashio::config 'ssh_port')"
export HP_SSH_PASSWORD="$(bashio::config 'ssh_password')"
export HP_EXCHANGE_PATH="$(bashio::config 'exchange_path')"

bashio::log.info "Starte Hermes Portal auf :8090 (mode=${HP_CONNECTION_MODE}, host=${HP_AGENT_HOST:-?})"

cd /app
exec python3 -m gunicorn --bind 0.0.0.0:8090 --workers 2 --threads 4 \
    --timeout 180 --access-logfile - wiki_app:app
