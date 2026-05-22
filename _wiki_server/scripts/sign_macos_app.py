#!/usr/bin/env python3
"""Ad-hoc signiert ein macOS-.app-Bundle für Distribution ohne Apple Developer-ID.

Wird aus dem Release-Workflow aufgerufen (`release.yml`, Mac-Step).
Findet alle Mach-O-Files (per ``file``-Magic-Check, nicht per Extension —
PyInstaller bündelt z.B. das Python-Framework als ``_internal/Python``
ohne Extension), signiert sie inner-most-first damit die nested Bundle-
Signaturen valid bleiben, dann das Bundle als Ganzes.

Vorgängerversion war ein bash-Pipe mit kaputtem ``awk``, der `codesign`
mit invaliden Pfaden gefüttert hat → in v1.0.1 wurde de facto NICHTS
signiert → DMG „beschädigt".

Usage:
    sign_macos_app.py path/to/Bundle.app
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path


def find_macho_files(app: Path) -> list[Path]:
    """Alle Mach-O-Files im Bundle, sortiert nach Pfad-Tiefe (tiefste zuerst)."""
    found: list[Path] = []
    for f in app.rglob("*"):
        if not f.is_file() or f.is_symlink():
            continue
        try:
            r = subprocess.run(
                ["file", "-b", str(f)],
                capture_output=True, text=True, timeout=10,
            )
            if "Mach-O" in r.stdout:
                found.append(f)
        except (subprocess.TimeoutExpired, OSError):
            pass
    # Tiefste Pfade zuerst (nested-Bundles vor ihren Parents)
    found.sort(key=lambda p: -len(p.parts))
    return found


def codesign(target: Path) -> tuple[bool, str]:
    """Ad-hoc-Signatur (Identity ``-``). Liefert (ok, message)."""
    r = subprocess.run(
        ["codesign", "--force", "--sign", "-", "--timestamp=none", str(target)],
        capture_output=True, text=True, timeout=60,
    )
    msg = (r.stderr or r.stdout).strip()
    return r.returncode == 0, msg


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: sign_macos_app.py path/to/Bundle.app", file=sys.stderr)
        return 2
    app = Path(argv[1])
    if not app.exists() or not app.is_dir():
        print(f"❌ Bundle nicht gefunden oder kein Verzeichnis: {app}", file=sys.stderr)
        return 1

    print(f"→ Scanne Mach-O-Files in {app.name} …", flush=True)
    machos = find_macho_files(app)
    print(f"  → {len(machos)} Mach-O-Files identifiziert", flush=True)

    print(f"→ Signiere alle (inner-most-first, Identity '-')…", flush=True)
    ok, fail = 0, 0
    for f in machos:
        success, msg = codesign(f)
        if success:
            ok += 1
        else:
            fail += 1
            # Ein paar Fehler dürfen sein (z.B. read-only-Embeds), nur erstes
            # paar zur Diagnose ausgeben — sonst spamt's den Build-Log voll.
            if fail <= 5:
                print(f"  FAIL: {f.relative_to(app)}", flush=True)
                print(f"        {msg[:200]}", flush=True)
    print(f"  → {ok} signiert, {fail} fehlgeschlagen", flush=True)

    print(f"→ Signiere Bundle als Ganzes…", flush=True)
    success, msg = codesign(app)
    if not success:
        print(f"  ⚠ Bundle-Sign warnt: {msg[:300]}", flush=True)
    else:
        print(f"  → ok", flush=True)

    print(f"→ Verify (informativ, ad-hoc Sign blockt nicht den Build):", flush=True)
    r = subprocess.run(
        ["codesign", "--verify", "--verbose=2", str(app)],
        capture_output=True, text=True,
    )
    out = (r.stderr or r.stdout).strip()
    for line in out.splitlines()[:10]:
        print(f"  {line}", flush=True)

    # Wir geben immer 0 zurück — ad-hoc Sign produziert immer Warnings,
    # das soll den Workflow nicht killen.
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
