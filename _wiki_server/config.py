#!/usr/bin/env python3
"""Hermes Portal – zentrale Konfiguration.

Lädt Settings aus ``data/config.json`` und erlaubt Overrides via Environment-Variablen
(``HP_<KEY>``). Vor dem ersten Lauf wird ``data/config.json`` aus ``config.defaults.json``
erzeugt, sodass die App auch ohne UI-Konfiguration startet.

Die Klasse :class:`AppConfig` ist ein einfacher Daten-Container mit Helfern, die alle
Pfade gegen das eingestellte Tausch-Verzeichnis auflösen.
"""
from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional


# Verzeichnisse relativ zu diesem Modul (in Docker via HP_DATA_DIR überschreibbar)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("HP_DATA_DIR") or (BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = Path(os.environ.get("HP_CONFIG_FILE") or (DATA_DIR / "config.json"))
DEFAULTS_FILE = BASE_DIR / "config.defaults.json"


# ----- Default-Werte ---------------------------------------------------------

DEFAULT_RSS_FEEDS: List[Dict[str, str]] = [
    {"name": "Heise News",       "url": "https://www.heise.de/rss/heise-atom.xml"},
    {"name": "Heise KI",         "url": "https://www.heise.de/thema/Kuenstliche-Intelligenz?view=atom"},
    {"name": "Heise Smart Home", "url": "https://www.heise.de/thema/Smart-Home?view=atom"},
]

DEFAULTS: Dict[str, Any] = {
    # --- Identität ---------------------------------------------------------
    "agent_name":          "Hermes",       # früher hardcoded "Wally"
    "agent_persona":       "",             # optionaler Free-Text fürs LLM-Prompt
    "user_name":           "Du",           # früher hardcoded "Jan"

    # --- Wiki-Kategorien (anpassbar pro Installation) ---------------------
    "category_entity_label":  "Entitäten",
    "category_concept_label": "Konzepte",

    # --- UI-Toggles für optionale Nav-Punkte ----------------------------
    # Wer einzelne Features nicht nutzt, kann den Menüpunkt komplett
    # ausblenden (Header + Sidebar). Defaults: alles sichtbar.
    "show_wiki":      True,
    "show_news":      True,
    "show_briefing":  True,
    "show_aufgaben":  True,

    # --- Sprache der UI -------------------------------------------------
    # Sprachen unter _wiki_server/i18n/<code>.json. Default 'en' weil es
    # die meisten User verstehen. Weitere: de, es, fr — Beiträge willkommen.
    "language":       "en",

    # --- Verbindung zum Hermes-Agent --------------------------------------
    "connection_mode":     "local",        # "local" oder "ssh"
    "agent_host":          "127.0.0.1",    # IP/Hostname des Hermes-Agents
    "ssh_user":            "root",
    "ssh_port":            22,
    "ssh_key_path":        "",             # Pfad zum privaten SSH-Key auf dem Portal-Host
    "ssh_password":        "",             # nur Fallback – Key wird bevorzugt

    # --- Pfade auf dem Hermes-Agent (= remote bei SSH-Mode) ---------------
    "exchange_path":       "/mnt/austausch",        # früher hardcoded
    "wiki_subpath":        "wiki",                  # Subpfad unter exchange_path
    "hermes_home":         "/root/.hermes",         # früher hardcoded
    "hermes_bin":          "hermes",                # in PATH des Agent
    "briefing_script":     "scripts/daily_briefing.py",  # relativ zu wiki_subpath
    "briefing_output":     "blog/briefing.html",    # relativ zu wiki_subpath
    "blog_posts_subdir":   "posts",                 # Unterordner unter blog/ für die Einzel-Tagesberichte
                                                    # (leer = direkt in blog/). Der Hermes-Agent-Blog-Generator
                                                    # legt die Einzel-HTMLs typischerweise dort ab.

    # --- Briefing-Inhalte (werden an das Script als BRIEFING_* ENV-Vars gereicht) ---
    "briefing_github_user":   "",          # leer = GitHub-Section überspringen
    "briefing_weather_lat":   "52.52",     # Berlin Default
    "briefing_weather_lon":   "13.40",
    "briefing_weather_tz":    "Europe/Berlin",
    "briefing_forum_rss":     "",          # leer = Forum-Section überspringen
    "briefing_bvg_stop":      "",          # leer = BVG-Section überspringen

    # --- News / RSS --------------------------------------------------------
    "rss_feeds":           DEFAULT_RSS_FEEDS,

    # --- Web-Server -------------------------------------------------------
    "bind_host":           "0.0.0.0",
    "bind_port":           8090,
    "secret_key":          "",   # leer = wird beim ersten Start zufällig erzeugt
}


# ----- Loader ----------------------------------------------------------------

_LOCK = RLock()


def _coerce(default: Any, value: Any) -> Any:
    """Castet einen Env-String auf den Typ des Defaults (best effort)."""
    if value is None:
        return default
    if isinstance(default, bool):
        return str(value).strip().lower() in ("1", "true", "yes", "on", "y")
    if isinstance(default, int) and not isinstance(default, bool):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    if isinstance(default, list):
        if isinstance(value, list):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else default
        except (TypeError, ValueError, json.JSONDecodeError):
            return default
    return str(value)


def _apply_env(values: Dict[str, Any]) -> Dict[str, Any]:
    """Übergeschriebene Werte aus ``HP_<KEY>``-Env-Variablen einsetzen."""
    out = dict(values)
    for key, default in DEFAULTS.items():
        env_name = f"HP_{key.upper()}"
        if env_name in os.environ:
            out[key] = _coerce(default, os.environ[env_name])
    return out


def _load_raw() -> Dict[str, Any]:
    """Lädt das JSON; legt eine Default-Datei an, falls keine existiert.

    Beim allerersten Start (config.json fehlt) werden ``HP_*``-Env-Variablen
    als Seed in die neue config.json geschrieben. Bei späteren Reloads
    werden die Env-Variablen ignoriert — sonst würden in der UI gespeicherte
    User-Änderungen bei jedem Page-Load von HA-Add-on-Options o.ä.
    überschrieben (das war der Pfad-Reset-Bug in v1.0.5).
    """
    if not CONFIG_FILE.exists():
        # Erst aus user-bereitstellter Defaults-Datei, sonst aus dem in-code DEFAULTS-Dict
        if DEFAULTS_FILE.exists():
            try:
                seed = json.loads(DEFAULTS_FILE.read_text(encoding="utf-8"))
                if not isinstance(seed, dict):
                    seed = dict(DEFAULTS)
            except (OSError, json.JSONDecodeError):
                seed = dict(DEFAULTS)
        else:
            seed = dict(DEFAULTS)
        # Env-Vars als Initial-Seed übernehmen (z.B. HP_EXCHANGE_PATH aus
        # HA-Add-on-Options). Spätere Restarts ignorieren diese, damit
        # UI-Edits stabil bleiben.
        seed = _apply_env(seed)
        try:
            CONFIG_FILE.write_text(
                json.dumps(seed, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    try:
        loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            loaded = {}
    except (OSError, json.JSONDecodeError):
        loaded = {}

    # Defaults für fehlende Keys auffüllen
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in loaded.items() if k in DEFAULTS})

    # Secret-Key ggf. einmalig erzeugen und persistieren
    if not merged.get("secret_key"):
        merged["secret_key"] = secrets.token_hex(32)
        try:
            CONFIG_FILE.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return merged


# ----- Public API ------------------------------------------------------------


class AppConfig:
    """Komfort-Wrapper um das Settings-Dict mit Pfad-Helfern."""

    def __init__(self, values: Dict[str, Any]):
        self._values = values

    # --- Roh-Zugriff ------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._values)

    # --- Häufig genutzte Properties --------------------------------------
    @property
    def agent_name(self) -> str:        return str(self._values.get("agent_name") or "Hermes")
    @property
    def user_name(self) -> str:         return str(self._values.get("user_name") or "Du")
    @property
    def agent_persona(self) -> str:     return str(self._values.get("agent_persona") or "")
    @property
    def connection_mode(self) -> str:   return str(self._values.get("connection_mode") or "local").lower()
    @property
    def agent_host(self) -> str:        return str(self._values.get("agent_host") or "127.0.0.1")
    @property
    def ssh_user(self) -> str:          return str(self._values.get("ssh_user") or "root")
    @property
    def ssh_port(self) -> int:
        try:
            return int(self._values.get("ssh_port") or 22)
        except (TypeError, ValueError):
            return 22
    @property
    def ssh_key_path(self) -> str:      return str(self._values.get("ssh_key_path") or "")
    @property
    def ssh_password(self) -> str:      return str(self._values.get("ssh_password") or "")
    @property
    def exchange_path(self) -> str:     return str(self._values.get("exchange_path") or "/mnt/austausch")
    @property
    def hermes_home(self) -> str:       return str(self._values.get("hermes_home") or "/root/.hermes")
    @property
    def blog_posts_subdir(self) -> str:
        """Subordner unter blog/, in dem der Hermes-Agent die Einzel-
        Tagesberichts-HTMLs ablegt. Default: ``"posts"``. Leerer String
        bedeutet: direkt in ``blog/``.
        """
        v = self._values.get("blog_posts_subdir")
        # Bewusst keine Defaultierung wenn explizit "" gesetzt
        if v is None:
            return "posts"
        return str(v).strip().strip("/")
    @property
    def hermes_bin(self) -> str:        return str(self._values.get("hermes_bin") or "hermes")
    @property
    def bind_host(self) -> str:         return str(self._values.get("bind_host") or "0.0.0.0")
    @property
    def bind_port(self) -> int:
        try:
            return int(self._values.get("bind_port") or 8090)
        except (TypeError, ValueError):
            return 8090
    @property
    def secret_key(self) -> str:        return str(self._values.get("secret_key") or "hermes-portal-fallback")
    @property
    def rss_feeds(self) -> List[Dict[str, str]]:
        feeds = self._values.get("rss_feeds") or []
        return [f for f in feeds if isinstance(f, dict) and f.get("url")]

    # --- Pfad-Helfer ------------------------------------------------------
    def wiki_dir(self) -> str:
        """Vollständiger Pfad zum Wiki-Root (auf dem Agent-Host)."""
        sub = str(self._values.get("wiki_subpath") or "wiki").lstrip("/")
        return f"{self.exchange_path.rstrip('/')}/{sub}".rstrip("/")

    def wiki_path(self, *parts: str) -> str:
        base = self.wiki_dir().rstrip("/")
        suffix = "/".join(p.strip("/") for p in parts if p)
        return f"{base}/{suffix}".rstrip("/")

    def hermes_path(self, *parts: str) -> str:
        base = self.hermes_home.rstrip("/")
        suffix = "/".join(p.strip("/") for p in parts if p)
        return f"{base}/{suffix}".rstrip("/")

    def briefing_script_path(self) -> str:
        return self.wiki_path(str(self._values.get("briefing_script") or "scripts/daily_briefing.py"))

    def briefing_output_path(self) -> str:
        return self.wiki_path(str(self._values.get("briefing_output") or "blog/briefing.html"))

    def briefing_env(self) -> Dict[str, str]:
        """ENV-Mapping für den Aufruf des Briefing-Scripts (BRIEFING_* Variablen)."""
        return {
            "BRIEFING_GITHUB_USER": str(self._values.get("briefing_github_user") or ""),
            "BRIEFING_WEATHER_LAT": str(self._values.get("briefing_weather_lat") or ""),
            "BRIEFING_WEATHER_LON": str(self._values.get("briefing_weather_lon") or ""),
            "BRIEFING_WEATHER_TZ":  str(self._values.get("briefing_weather_tz")  or "Europe/Berlin"),
            "BRIEFING_FORUM_RSS":   str(self._values.get("briefing_forum_rss")   or ""),
            "BRIEFING_BVG_STOP":    str(self._values.get("briefing_bvg_stop")    or ""),
            "BRIEFING_OUTPUT_PATH": self.briefing_output_path(),
        }

    # --- Persistenz -------------------------------------------------------
    def update(self, patch: Dict[str, Any]) -> None:
        """Übernimmt eine Teil-Aktualisierung und schreibt nach config.json."""
        with _LOCK:
            for key, value in patch.items():
                if key not in DEFAULTS:
                    continue  # unbekannte Keys werden ignoriert
                self._values[key] = _coerce(DEFAULTS[key], value)
            try:
                CONFIG_FILE.write_text(
                    json.dumps(self._values, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except OSError:
                pass

    def reload(self) -> None:
        with _LOCK:
            self._values = _load_raw()  # _apply_env läuft jetzt nur noch beim First-Install in _load_raw


# ----- Singleton --------------------------------------------------------------

_cfg: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _cfg
    if _cfg is None:
        with _LOCK:
            if _cfg is None:
                # _apply_env läuft jetzt nur noch beim First-Install in _load_raw
                _cfg = AppConfig(_load_raw())
    return _cfg


def reload_config() -> AppConfig:
    cfg = get_config()
    cfg.reload()
    return cfg


# Liste der Settings, die niemals nach außen geschickt werden (Secrets-Scrubbing)
SECRET_KEYS = {"ssh_password", "secret_key"}


def public_config_dict() -> Dict[str, Any]:
    """Liefert ein Dict ohne Secrets für die UI/API."""
    data = get_config().as_dict()
    for k in SECRET_KEYS:
        if data.get(k):
            data[k] = "***"
        else:
            data[k] = ""
    return data
