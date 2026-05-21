#!/usr/bin/env bash
# Synct die Portal-Sourcen aus _wiki_server/ in den HA-Add-on Build-Kontext.
# Vor `ha addons build` ausführen.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(cd "$HERE/../../_wiki_server" && pwd)"

echo "→ Kopiere Portal-Sourcen aus $SRC nach $HERE/rootfs/app/"
rm -rf "$HERE/rootfs/app"
mkdir -p "$HERE/rootfs/app"
rsync -a \
    --exclude '__pycache__' \
    --exclude 'venv' \
    --exclude '.DS_Store' \
    --exclude 'data/chat.db' \
    --exclude 'data/uploads' \
    --exclude 'data/shared' \
    "$SRC/" "$HERE/rootfs/app/"

cp "$SRC/requirements.txt" "$HERE/rootfs/requirements.txt"

echo "✓ Fertig. Jetzt 'ha addons build hermes_portal' im HA-Host ausführen."
