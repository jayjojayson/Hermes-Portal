"""Entry-Point für PyInstaller-Build (Mac/Linux/Windows Standalone-Binary).

Startet den Flask-Server im Background-Thread und öffnet automatisch den
Standard-Browser auf http://127.0.0.1:8090. Beim Schließen des Konsolenfensters
beendet sich der Server.

Wird nicht direkt vom User benutzt — nur als ``--onefile``-Build-Target.
"""
from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────
# STARTUP-MARKER — wird als allererstes geschrieben, BEVOR irgendein
# komplexer Import läuft. Wenn die Datei auf dem Desktop erscheint,
# wissen wir: Python ist gestartet, PyInstaller-Bootloader hat geklappt.
# Wenn sie NICHT erscheint, ist der Crash _unter_ Python (Bootloader,
# dyld-Library-Loading, Gatekeeper-Library-Validation). Diagnostik nur,
# kostet beim normalen Start ~5 ms.
# ──────────────────────────────────────────────────────────────────────
try:
    import os as _os_marker
    import sys as _sys_marker
    from pathlib import Path as _Path_marker
    from datetime import datetime as _dt_marker
    _marker = _Path_marker.home() / "Desktop" / "hermes-portal-started.txt"
    _marker.write_text(
        f"Hermes Portal Startup-Marker\n"
        f"────────────────────────────\n"
        f"Zeit:       {_dt_marker.now().isoformat()}\n"
        f"PID:        {_os_marker.getpid()}\n"
        f"Python:     {_sys_marker.version.split(chr(10))[0]}\n"
        f"Executable: {_sys_marker.executable}\n"
        f"argv:       {_sys_marker.argv}\n"
        f"CWD:        {_os_marker.getcwd()}\n"
        f"HOME:       {_os_marker.environ.get('HOME', '<unset>')}\n"
        f"_MEIPASS:   {getattr(_sys_marker, '_MEIPASS', '<not frozen>')}\n"
        f"frozen:     {getattr(_sys_marker, 'frozen', False)}\n"
        f"\nWenn diese Datei existiert aber die App trotzdem nicht startet:\n"
        f"  → Crash passiert NACH Python-Start. Schau in:\n"
        f"     ~/Desktop/Hermes-Portal-Crash.log\n"
        f"     ~/Library/Application Support/Hermes Portal/crash.log\n",
        encoding="utf-8",
    )
except Exception:
    pass

import os
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path


def _resource_path(rel: str) -> str:
    """Pfad zu eingebetteten Ressourcen — funktioniert bei PyInstaller und im Dev."""
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
    return str(Path(base) / rel)


def _user_data_dir() -> Path:
    """Plattform-konventioneller Schreib-Ort für User-Daten.

    NICHT im App-Bundle/Programme-Ordner — das ist read-only (macOS Gatekeeper,
    Windows UAC, Linux/usr) und würde außerdem die Code-Signatur sprengen.

    - macOS:   ``~/Library/Application Support/Hermes Portal/``
    - Windows: ``%APPDATA%\\Hermes Portal\\``  (i.d.R. ``…/AppData/Roaming/``)
    - Linux:   ``$XDG_DATA_HOME/hermes-portal/`` oder ``~/.local/share/hermes-portal/``
    """
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Hermes Portal"
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Hermes Portal"
        return Path.home() / "AppData" / "Roaming" / "Hermes Portal"
    # Linux / BSD
    xdg = os.environ.get("XDG_DATA_HOME")
    return (Path(xdg) if xdg else Path.home() / ".local" / "share") / "hermes-portal"


def _ensure_runtime_dirs() -> Path:
    """Stellt HP_DATA_DIR sicher und gibt den Pfad zurück (für den Crash-Log)."""
    if os.environ.get("HP_DATA_DIR"):
        p = Path(os.environ["HP_DATA_DIR"])
        p.mkdir(parents=True, exist_ok=True)
        return p

    data_dir = _user_data_dir()
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # Letzter Ausweg: temporäres Verzeichnis im /tmp bzw. %TEMP%, damit
        # die App wenigstens startet — User sieht in der UI eine Warnung.
        import tempfile
        data_dir = Path(tempfile.gettempdir()) / "hermes-portal-data"
        data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HP_DATA_DIR"] = str(data_dir)
    return data_dir


def _open_browser(url: str, delay: float = 1.5) -> None:
    """Browser nach kurzer Verzögerung öffnen, damit der Server schon antwortet."""
    def _later():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_later, daemon=True).start()


def _show_crash_dialog_macos(log_path: Path, exc_text: str) -> None:
    """Zeigt einen nativen macOS-Dialog mit dem Crash-Hinweis.

    Wichtig, weil .app-Bundles per Doppelklick gestartet kein sichtbares
    Terminal haben — sonst stirbt die App lautlos und der User rätselt.
    """
    if sys.platform != "darwin":
        return
    try:
        import subprocess
        title = "Hermes Portal — Startfehler"
        # AppleScript escaping: " → \\\", \\ → \\\\
        def esc(s): return s.replace('\\', '\\\\').replace('"', '\\"')
        body = (
            f"Beim Start ist ein Fehler aufgetreten:\\n\\n"
            f"{esc(exc_text[:300])}\\n\\n"
            f"Vollständiger Log:\\n{esc(str(log_path))}"
        )
        subprocess.run([
            "osascript", "-e",
            f'display dialog "{body}" with title "{esc(title)}" buttons {{"OK"}} with icon stop'
        ], timeout=15, check=False)
    except Exception:
        pass


def main() -> int:
    data_dir = _ensure_runtime_dirs()

    # sys.path so erweitern, dass alle relativen Imports funktionieren
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    import wiki_app
    cfg = wiki_app.cfg
    host = cfg.bind_host if cfg.bind_host != "0.0.0.0" else "127.0.0.1"
    port = cfg.bind_port
    url = f"http://{host}:{port}/"

    print()
    print("=" * 60)
    print(f"  🛰️  Hermes Portal — startet auf {url}")
    print(f"     Daten:   {data_dir}")
    print("=" * 60)
    print("  Browser öffnet sich gleich automatisch.")
    print("  Beenden mit Strg+C bzw. Schließen dieses Fensters.")
    print()
    _open_browser(url)

    # Production-Server (wenn waitress vorhanden, sonst Flask-Dev)
    try:
        from waitress import serve as _serve
        _serve(wiki_app.app, host=cfg.bind_host, port=port, threads=8)
    except ImportError:
        wiki_app.app.run(host=cfg.bind_host, port=port, threaded=True)
    return 0


def _emergency_log(tb: str) -> Path:
    """Schreibt den Crash-Log an die ERSTE Stelle, die akzeptiert wird.

    Reihenfolge: Desktop (sichtbar!) → User-Data-Dir → tempdir → cwd.
    Gibt den tatsächlich geschriebenen Pfad zurück (oder einen Phantasie-
    Pfad, falls _alles_ scheitert — dann steht der Traceback wenigstens
    noch im stderr).
    """
    from datetime import datetime
    stamp = f"\n=== {datetime.now().isoformat()} ===\n{tb}\n"
    candidates = [
        Path.home() / "Desktop" / "Hermes-Portal-Crash.log",
        _user_data_dir() / "crash.log",
    ]
    try:
        import tempfile
        candidates.append(Path(tempfile.gettempdir()) / "hermes-portal-crash.log")
    except Exception:
        pass
    candidates.append(Path.cwd() / "hermes-portal-crash.log")

    for path in candidates:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(stamp)
            return path
        except Exception:
            continue
    return candidates[0]  # Phantasie-Pfad, wenn alles scheitert


if __name__ == "__main__":
    # Ohne Crash-Handler ist die .app per Doppelklick eine Black-Box:
    # exception → lautlos beendet, kein Terminal-Output sichtbar. Wir
    # schreiben den Traceback an MEHRERE Stellen (zuerst Desktop, damit der
    # User es definitiv findet) UND zeigen einen nativen Dialog.
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as ex:  # noqa: BLE001 — wir wollen hier ALLES fangen
        tb = traceback.format_exc()
        # IMMER auf stderr — wenn aus Terminal gestartet, sieht User es live
        print("\n=== HERMES PORTAL CRASH ===", file=sys.stderr, flush=True)
        print(tb, file=sys.stderr, flush=True)
        # IMMER auf Disk an mind. einer Stelle
        log_path = _emergency_log(tb)
        print(f"=== Log: {log_path} ===\n", file=sys.stderr, flush=True)
        # Bonus auf macOS: nativer Dialog (damit Doppelklick-User es merken)
        _show_crash_dialog_macos(log_path, str(ex))
        sys.exit(1)
