"""Entry-Point für PyInstaller-Build (Mac/Linux/Windows Standalone-Binary).

Startet den Flask-Server im Background-Thread und öffnet automatisch den
Standard-Browser auf http://127.0.0.1:8090. Beim Schließen des Konsolenfensters
beendet sich der Server.

Wird nicht direkt vom User benutzt — nur als ``--onefile``-Build-Target.
"""
from __future__ import annotations
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _resource_path(rel: str) -> str:
    """Pfad zu eingebetteten Ressourcen — funktioniert bei PyInstaller und im Dev."""
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
    return str(Path(base) / rel)


def _ensure_runtime_dirs() -> None:
    """Beim ersten Start: HP_DATA_DIR neben dem Binary anlegen, damit Configs
    persistent bleiben (auch wenn die Binary verschoben wird)."""
    if os.environ.get("HP_DATA_DIR"):
        return
    # Bei PyInstaller: sys.executable ist der Binary-Pfad
    exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()
    data_dir = exe_dir / "hermes-portal-data"
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HP_DATA_DIR"] = str(data_dir)


def _open_browser(url: str, delay: float = 1.5) -> None:
    """Browser nach kurzer Verzögerung öffnen, damit der Server schon antwortet."""
    def _later():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_later, daemon=True).start()


def main() -> int:
    _ensure_runtime_dirs()

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


if __name__ == "__main__":
    sys.exit(main())
