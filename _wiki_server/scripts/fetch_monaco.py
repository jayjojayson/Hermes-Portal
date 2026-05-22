#!/usr/bin/env python3
"""Lädt den Monaco-Editor (VS-Code-Editor) als Offline-Bundle nach
``_wiki_server/static/vendor/monaco/``.

Wird beim Docker-Build sowie einmalig nach lokaler Installation aufgerufen.
Bei erneuten Aufrufen wird der bestehende Bundle gelöscht und frisch geladen.

Größe: ~6 MB komprimiert / ~25 MB entpackt (nur `min/vs/`-Bundle).
"""
from __future__ import annotations
import io
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

# Windows-Default-Shell nutzt cp1252 → Unicode-Pfeile/Häkchen in Prints sprengen
# den Build. Hier explizit UTF-8 erzwingen (mit ASCII-Fallback), damit der
# Release-Workflow auf windows-latest sauber durchläuft.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MONACO_VERSION = "0.50.0"
NPM_TARBALL_URL = f"https://registry.npmjs.org/monaco-editor/-/monaco-editor-{MONACO_VERSION}.tgz"

HERE = Path(__file__).resolve().parent.parent  # _wiki_server/
TARGET_DIR = HERE / "static" / "vendor" / "monaco"


def main() -> int:
    print(f"→ Lade monaco-editor {MONACO_VERSION} von npm …")
    try:
        req = urllib.request.Request(NPM_TARBALL_URL, headers={"User-Agent": "hermes-portal-installer"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except Exception as ex:
        print(f"❌ Download fehlgeschlagen: {ex}", file=sys.stderr)
        return 1

    print(f"✓ {len(data)/1024/1024:.1f} MB geladen, extrahiere min/vs/ …")
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # NPM-tarballs haben den Inhalt unter "package/" gepackt.
    PREFIX = "package/min/vs/"
    extracted = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.startswith(PREFIX):
                continue
            rel = member.name[len(PREFIX):]
            out_path = TARGET_DIR / "vs" / rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            extractor = tar.extractfile(member)
            if extractor is None:
                continue
            with open(out_path, "wb") as fh:
                shutil.copyfileobj(extractor, fh)
            extracted += 1

    if extracted == 0:
        print("❌ Im Tarball wurde kein min/vs/-Bundle gefunden.", file=sys.stderr)
        return 2

    print(f"✓ {extracted} Dateien nach {TARGET_DIR}/vs/ extrahiert.")
    print(f"  Loader-URL für die App: /static/vendor/monaco/vs/loader.js")
    return 0


if __name__ == "__main__":
    sys.exit(main())
