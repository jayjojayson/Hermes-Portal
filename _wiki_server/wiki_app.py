#!/usr/bin/env python3
"""Hermes Portal – Web-Frontend für den Hermes-Agent.

Flask-Server mit Wiki, News, Briefing, Aufgaben, Explorer, Chat und Settings-Panel.
Pfade, Agent-Name, User-Name, RSS-Feeds und die Verbindung zum Hermes-Agent
(lokal oder via SSH) sind über ``data/config.json`` konfigurierbar — siehe
:mod:`config`. Alle Hermes-spezifischen Aktionen laufen durch :mod:`hermes_client`.
"""

import os
import re
import mimetypes
import shutil
import threading
import json as json_module
import random
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify,
    send_from_directory, abort, send_file, session,
)
from werkzeug.utils import secure_filename
import markdown
import yaml

from config import get_config, reload_config, public_config_dict, DEFAULTS as CONFIG_DEFAULTS
from hermes_client import get_client, reset_client, HAS_PARAMIKO
from __version__ import VERSION as PORTAL_VERSION
import i18n as _i18n

cfg = get_config()

app = Flask(__name__)
app.secret_key = cfg.secret_key


# -----------------------------------------------------------------------
# Home-Assistant-Ingress-Support
# -----------------------------------------------------------------------
# Wenn das Portal als HA-Add-on läuft, kommt jede Anfrage über den HA-
# Supervisor-Ingress mit URL-Prefix `/api/hassio_ingress/<TOKEN>/`. HA
# setzt dafür den Header `X-Ingress-Path`. Wir mappen den auf WSGIs
# `SCRIPT_NAME`, damit Flask's `url_for(...)` und `request.script_root`
# in Templates die korrekten URLs erzeugen (CSS, JS, API-Routen).
class _IngressMiddleware:
    """Liest ``X-Ingress-Path`` und setzt ``SCRIPT_NAME`` entsprechend.

    Ohne diese Middleware liefert Flask Asset-URLs als ``/static/…`` aus,
    der Browser fragt aber gegen die HA-Origin → 404, kein CSS, kein JS.
    """

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        prefix = environ.get("HTTP_X_INGRESS_PATH")
        if prefix:
            environ["SCRIPT_NAME"] = prefix
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith(prefix):
                environ["PATH_INFO"] = path_info[len(prefix):] or "/"
        return self.wsgi_app(environ, start_response)


app.wsgi_app = _IngressMiddleware(app.wsgi_app)


def _compute_asset_version():
    """Hash der wichtigsten Portal-Assets — als Cache-Buster für ``base.html``.

    Bei Updates ändert sich der Hash automatisch und Browser laden CSS/JS frisch.
    Fail-safe: bei IO-Fehler einfach den Startzeit-Timestamp nutzen.
    """
    try:
        import hashlib
        h = hashlib.sha1()
        for rel in ("static/portal/style.css", "static/portal/site-header.js"):
            p = Path(__file__).parent / rel
            if p.exists():
                h.update(p.read_bytes())
        return h.hexdigest()[:10]
    except Exception:
        return str(int(datetime.now().timestamp()))


_ASSET_VERSION = _compute_asset_version()


@app.context_processor
def inject_globals():
    """Stellt die App-Config in jedem Template als ``cfg`` zur Verfügung."""
    lang = (cfg.get("language") or "en")
    return {
        "cfg": cfg,
        "agent_name": cfg.agent_name,
        "user_name": cfg.user_name,
        "exchange_path": cfg.exchange_path,
        "portal_name": "Hermes Portal",
        "category_entity_label":  cfg.get("category_entity_label", "Entitäten"),
        "category_concept_label": cfg.get("category_concept_label", "Konzepte"),
        "portal_asset_version":   _ASSET_VERSION,
        "current_year":           datetime.now().year,
        "portal_version":         PORTAL_VERSION,
        # i18n: t() für Templates, current_lang für UI, i18n_table für JS-Bridge
        "t":            lambda key: _i18n.t(key, lang),
        "current_lang": lang,
        "i18n_table":   _i18n.translation_table(lang),
        "i18n_available": _i18n.available_languages(),
    }


@app.after_request
def add_no_cache(response):
    """API-Responses sollen nie gecached werden."""
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ----------------------------------------------------------------------
# Update-Check (GitHub Releases API)
# ----------------------------------------------------------------------
# Cached die letzte Antwort 60 Min im Prozess-Memory, damit jeder Page-Load
# nicht GitHub triggert. HA-Add-on updated sich über den Supervisor — der
# Check hier ist nur für Desktop-Installer (AppImage/.dmg/.exe), wo es
# sonst keinen Hinweis auf neue Versionen gibt.
_UPDATE_CACHE = {"checked_at": None, "data": None}
_UPDATE_TTL = timedelta(hours=1)
_GITHUB_RELEASES_URL = "https://api.github.com/repos/jayjojayson/Hermes-Portal/releases/latest"


def _ssl_context_for_github():
    """Robuster SSL-Context für externe HTTPS-Calls aus PyInstaller-Builds.

    PyInstaller-Bundles auf macOS bringen kein System-CA-Bundle mit, daher
    schlägt ``urllib.request.urlopen('https://...')`` lautlos fehl (genau
    der Mac-Update-Banner-Bug aus v1.1.8). Ab v1.1.9 nehmen wir explizit
    das ``certifi``-Bundle — funktioniert in beiden Welten (Frozen + Dev).
    """
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, Exception):
        return ssl.create_default_context()


def _semver_tuple(v: str):
    """'1.0.3' → (1,0,3). Ungültige Stellen → 0. Defensiv."""
    try:
        return tuple(int(p) for p in v.lstrip("v").split(".")[:3])
    except Exception:
        return (0, 0, 0)


@app.route("/api/version/check")
def api_version_check():
    """Fragt GitHub Releases ab; liefert {current, latest, update_available, url}."""
    now = datetime.now()
    cached = _UPDATE_CACHE.get("data")
    cached_at = _UPDATE_CACHE.get("checked_at")
    if cached and cached_at and (now - cached_at) < _UPDATE_TTL:
        return jsonify({**cached, "cached": True})

    payload = {
        "current": PORTAL_VERSION,
        "latest": None,
        "update_available": False,
        "url": "https://github.com/jayjojayson/Hermes-Portal/releases/latest",
        "error": None,
        "cached": False,
    }
    try:
        req = urllib.request.Request(
            _GITHUB_RELEASES_URL,
            headers={"Accept": "application/vnd.github+json",
                     "User-Agent": f"hermes-portal/{PORTAL_VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=5, context=_ssl_context_for_github()) as resp:
            data = json_module.loads(resp.read().decode("utf-8"))
        tag = (data.get("tag_name") or "").lstrip("v")
        if tag:
            payload["latest"] = tag
            payload["url"] = data.get("html_url") or payload["url"]
            payload["update_available"] = _semver_tuple(tag) > _semver_tuple(PORTAL_VERSION)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as ex:
        # Offline / Rate-Limit / kaputtes JSON — kein Show-Stopper.
        payload["error"] = str(ex)[:200]

    _UPDATE_CACHE["data"] = payload
    _UPDATE_CACHE["checked_at"] = now
    return jsonify(payload)


@app.template_filter("format_date")
def format_date(value):
    """Formatiert ein datetime-Objekt als deutsches Datum."""
    if value is None:
        return ""
    if hasattr(value, 'strftime'):
        return value.strftime('%d.%m.%Y %H:%M')
    return str(value)

# --- Pfade aus der Config evaluieren (werden in _refresh_paths() bei
# Settings-Änderungen neu berechnet, damit Live-Updates möglich sind).
WIKI_DIR = ENTITIES_DIR = CONCEPTS_DIR = REFERENCES_DIR = BLOG_DIR = None  # type: ignore
WIKI_SCRIPTS_DIR = WIKI_SKILLS_DIR = None  # type: ignore
HERMES_SKILLS_DIR = HERMES_BUILTIN_SKILLS_DIR = HERMES_SCRIPTS_DIR = HERMES_CRON_FILE = None  # type: ignore


def _refresh_paths():
    """Rechnet alle Pfad-Konstanten aus ``cfg`` neu durch.

    Wird beim App-Start aufgerufen und nach jedem Settings-Save, damit
    Änderungen an ``exchange_path`` / ``hermes_home`` / ``wiki_subpath``
    sofort wirksam sind (Explorer, Wiki, Cronjob-File etc.).
    """
    global WIKI_DIR, ENTITIES_DIR, CONCEPTS_DIR, REFERENCES_DIR, BLOG_DIR
    global WIKI_SCRIPTS_DIR, WIKI_SKILLS_DIR, BLOG_STATIC_DIR
    global HERMES_SKILLS_DIR, HERMES_BUILTIN_SKILLS_DIR, HERMES_SCRIPTS_DIR, HERMES_CRON_FILE
    global MEMORY_FILES, HERMES_LOG_CANDIDATES, SHARED_ROOT, SHARED_FOLDER, SOURCE_DIRS, CUSTOM_SKILLS_DIR

    WIKI_DIR = Path(cfg.wiki_dir())
    ENTITIES_DIR = WIKI_DIR / "entities"
    CONCEPTS_DIR = WIKI_DIR / "concepts"
    REFERENCES_DIR = WIKI_DIR / "references"
    BLOG_DIR = WIKI_DIR / "blog"
    BLOG_STATIC_DIR = BLOG_DIR
    WIKI_SCRIPTS_DIR = WIKI_DIR / "scripts"
    WIKI_SKILLS_DIR = WIKI_DIR / "skills"
    CUSTOM_SKILLS_DIR = WIKI_DIR / "skills"

    HERMES_SKILLS_DIR = Path(cfg.hermes_path("skills"))
    HERMES_BUILTIN_SKILLS_DIR = Path(cfg.hermes_path("hermes-agent/skills"))
    HERMES_SCRIPTS_DIR = Path(cfg.hermes_path("scripts"))
    HERMES_CRON_FILE = Path(cfg.hermes_path("cron/jobs.json"))

    MEMORY_FILES = {
        "soul":   Path(cfg.hermes_path("SOUL.md")),
        "user":   Path(cfg.hermes_path("memories/USER.md")),
        "memory": Path(cfg.hermes_path("memories/MEMORY.md")),
        "config": Path(cfg.hermes_path("config.yaml")),
    }

    base = cfg.hermes_home.rstrip("/")
    HERMES_LOG_CANDIDATES = []
    if os.environ.get("HERMES_LOG"):
        HERMES_LOG_CANDIDATES.append(Path(os.environ["HERMES_LOG"]))
    for _sub in ("logs/hermes.log", "logs/agent.log", "hermes.log", "agent.log", "log.log"):
        HERMES_LOG_CANDIDATES.append(Path(f"{base}/{_sub}"))
    HERMES_LOG_CANDIDATES.append(Path("/var/log/hermes.log"))

    SHARED_ROOT = Path(cfg.exchange_path)
    SHARED_FOLDER = cfg.exchange_path

    # SOURCE_DIRS hält Path-Referenzen, die in _collect_source_files genutzt werden.
    SOURCE_DIRS = {
        "skills": {
            "label": "Skill References",
            "dirs": [HERMES_SKILLS_DIR],
            "extensions": {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".sh", ".js", ".html", ".css"},
            "scan_recursive": True,
            "scan_sub": "references",
        },
        "hermes_scripts": {
            "label": "Hermes Scripts",
            "dirs": [HERMES_SCRIPTS_DIR],
            "extensions": {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".sh", ".js", ".html", ".css"},
            "scan_recursive": False,
            "scan_sub": None,
        },
        "wiki_scripts": {
            "label": "Wiki Scripts",
            "dirs": [WIKI_SCRIPTS_DIR],
            "extensions": {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".sh", ".js", ".html", ".css"},
            "scan_recursive": False,
            "scan_sub": None,
        },
        "wiki_refs": {
            "label": "Wiki References",
            "dirs": [REFERENCES_DIR],
            "extensions": {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".sh", ".js", ".html", ".css"},
            "scan_recursive": False,
            "scan_sub": None,
        },
    }


# Initialisierung (vor allem, was die Konstanten referenziert)
BLOG_STATIC_DIR = None  # type: ignore
MEMORY_FILES = {}  # type: ignore
HERMES_LOG_CANDIDATES = []  # type: ignore
SHARED_ROOT = None  # type: ignore
SHARED_FOLDER = ""  # type: ignore
SOURCE_DIRS = {}  # type: ignore
CUSTOM_SKILLS_DIR = None  # type: ignore
_refresh_paths()

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Settings-Daten (immer lokal beim Portal; in Docker via HP_DATA_DIR=/data überschreibbar)
DATA_DIR = Path(os.environ.get("HP_DATA_DIR") or (Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
TASKS_FILE = DATA_DIR / "tasks.json"
USAGE_FILE = DATA_DIR / "usage.json"
QUICK_PROMPTS_LOG = DATA_DIR / "quick_prompts.jsonl"


# ---- Lokale Verzeichnisse sicherstellen ----
# Wiki-Verzeichnisse nur im local-Mode anlegen – im SSH-Mode liegen sie remote.
if cfg.connection_mode == "local":
    for d in [ENTITIES_DIR, CONCEPTS_DIR]:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

# Custom template folder
app.template_folder = str(TEMPLATES_DIR)

# Markdown-Extension mit allen Features
md_ext = markdown.Markdown(extensions=[
    "tables",
    "fenced_code",
    "codehilite",
    "toc",
    "attr_list",
    "def_list",
])


# ---- Settings-Daten: Tasks ----

def load_wiki_tasks():
    """Lädt die Wiki-eigenen Task-Liste aus JSON."""
    if TASKS_FILE.exists():
        try:
            return json_module.loads(TASKS_FILE.read_text(encoding="utf-8"))
        except (json_module.JSONDecodeError, OSError):
            return {"jobs": []}
    return {"jobs": []}


def save_wiki_tasks(data):
    """Speichert die Wiki-Task-Liste als JSON."""
    TASKS_FILE.write_text(json_module.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_hermes_tasks():
    """Lädt die Hermes-Cronjobs aus der Agent-jobs.json (via hermes_client)."""
    try:
        data = get_client().read_json(str(HERMES_CRON_FILE), default=None)
        if not isinstance(data, dict):
            return []
        jobs = data.get("jobs", [])
        result = []
        for j in jobs:
            schedule_str = ""
            sched = j.get("schedule", {})
            if isinstance(sched, dict):
                schedule_str = sched.get("expr", sched.get("display", ""))
            else:
                schedule_str = str(sched)

            # command = script oder prompt-Auszug (gekürzt für Anzeige)
            command = j.get("script", "") or (j.get("prompt", "")[:120] + "…" if j.get("prompt") else "")
            # prompt_full = vollständiger Prompt für den Editor
            prompt_full = j.get("script", "") or j.get("prompt", "")

            result.append({
                "id": j.get("id", ""),
                "name": j.get("name", "Unbekannt"),
                "schedule": schedule_str,
                "command": command,
                "prompt": prompt_full,
                "enabled": j.get("enabled", False),
                "last_run": j.get("last_run_at"),
                "next_run": j.get("next_run_at", ""),
                "last_exit_code": 0 if j.get("last_status") == "ok" else (-1 if j.get("last_status") == "error" else None),
                "last_output": j.get("last_error") or j.get("last_status", ""),
                "source": "hermes",
                "hermes_raw": j,  # Original für Roundtrip
            })
        return result
    except (json_module.JSONDecodeError, OSError, PermissionError):
        return []


def save_hermes_tasks(jobs):
    """Speichert die vollständige Hermes-jobs.json (nur mit bestehenden Aufgaben, keine neuen)."""
    try:
        client = get_client()
        data = client.read_json(str(HERMES_CRON_FILE), default=None)
        if not isinstance(data, dict):
            return
        # Aktualisiere nur bestehende Jobs
        updated_hermes_jobs = []
        for hj in data.get("jobs", []):
            matched = [j for j in jobs if j.get("id") == hj.get("id") and j.get("source") == "hermes"]
            if matched:
                updated = matched[0]
                # Schreibe zurück ins Hermes-Format
                if "schedule" in updated:
                    if isinstance(hj.get("schedule"), dict):
                        hj["schedule"]["expr"] = updated["schedule"]
                        hj["schedule"]["display"] = updated["schedule"]
                    else:
                        hj["schedule"] = updated["schedule"]
                if "enabled" in updated:
                    hj["enabled"] = updated["enabled"]
                if "name" in updated:
                    hj["name"] = updated["name"]
            updated_hermes_jobs.append(hj)
        data["jobs"] = updated_hermes_jobs
        client.write_json(str(HERMES_CRON_FILE), data)
    except Exception:
        pass  # Fehler beim Schreiben – Hermes verwaltet seine Datei


def _next_run_from_schedule(schedule):
    """Vereinfachte next_run-Berechnung (nur Nächster-Minuten-Abstand)."""
    import time
    now = datetime.now()
    if schedule == "@every_minute":
        return now.isoformat()
    if schedule.startswith("*/"):
        try:
            mins = int(schedule.split(" ")[0].replace("*/", ""))
            next_min = ((now.minute // mins) + 1) * mins
            if next_min >= 60:
                next_dt = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
            else:
                next_dt = now.replace(minute=next_min, second=0, microsecond=0)
            return next_dt.isoformat()
        except (ValueError, IndexError):
            return now.isoformat()
    # Cron-Format: "min hour dom mon dow"
    try:
        parts = schedule.split()
        if len(parts) >= 5:
            minute, hour = parts[0], parts[1]
            next_h = now.hour
            next_m = now.minute + 1
            if minute != "*" and minute != "*/1":
                try:
                    next_m = int(minute)
                except ValueError:
                    next_m = 0
            if next_m >= 60:
                next_m = 0
                next_h += 1
            if hour != "*" and hour != "*/1":
                try:
                    target_h = int(hour)
                    if next_h > target_h or (next_h == target_h and now.minute >= next_m if minute != "*" else False):
                        next_h = target_h
                        next_m = int(minute) if minute != "*" else 0
                        if next_h <= now.hour and (next_h < now.hour or next_m <= now.minute):
                            next_h += 24
                    else:
                        next_h = target_h
                except ValueError:
                    pass
            try:
                next_dt = now.replace(hour=next_h % 24, minute=next_m, second=0, microsecond=0)
                if next_dt <= now and next_h < 24:
                    next_dt = next_dt.replace(hour=next_h + 24 if next_h + 24 < 48 else next_h % 24 + 24)
                return next_dt.isoformat()
            except ValueError:
                pass
        return now.isoformat()
    except Exception:
        return now.isoformat()


# ---- Settings-Daten: Usage ----

def load_usage():
    """Lädt Usage-Statistiken."""
    if USAGE_FILE.exists():
        try:
            return json_module.loads(USAGE_FILE.read_text(encoding="utf-8"))
        except (json_module.JSONDecodeError, OSError):
            pass
    return {"date": datetime.now().strftime("%Y-%m-%d"), "total_requests": 0, "hourly": {}}


def save_usage(data):
    """Speichert Usage-Statistiken."""
    USAGE_FILE.write_text(json_module.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---- Request-Tracking ----

@app.before_request
def track_request():
    """Zählt Requests für Usage-Statistik."""
    try:
        usage = load_usage()
        today = datetime.now().strftime("%Y-%m-%d")
        if usage.get("date") != today:
            # Reset bei neuem Tag
            usage = {"date": today, "total_requests": 0, "hourly": {}}
        usage["total_requests"] = usage.get("total_requests", 0) + 1
        hour_key = datetime.now().strftime("%H:00")
        usage["hourly"][hour_key] = usage["hourly"].get(hour_key, 0) + 1
        usage["date"] = today
        save_usage(usage)
    except Exception:
        pass  # Nicht kritisch – Tracking darf nicht crashen


# --------------------------------------------------------------------
# Background-Task-Scheduler
# --------------------------------------------------------------------
_scheduler_running = False


def _scheduler_loop():
    """Hintergrund-Thread: Prüft alle 30s ob Tasks ausgeführt werden müssen."""
    global _scheduler_running
    while _scheduler_running:
        try:
            # Lade Wiki-Tasks
            data = load_wiki_tasks()
            jobs = data.get("jobs", [])
            now = datetime.now()
            changed = False

            for job in jobs:
                if not job.get("enabled", False):
                    continue
                next_str = job.get("next_run")
                if not next_str:
                    continue
                try:
                    next_dt = datetime.fromisoformat(next_str)
                except (ValueError, TypeError):
                    continue

                if now >= next_dt:
                    # Task ausführen
                    cmd = job.get("command", "")
                    if cmd:
                        try:
                            result = subprocess.run(
                                cmd, shell=True, capture_output=True, text=True, timeout=300
                            )
                            job["last_exit_code"] = result.returncode
                            job["last_output"] = (result.stdout + result.stderr)[:500]
                        except subprocess.TimeoutExpired:
                            job["last_exit_code"] = -1
                            job["last_output"] = "Timeout (300s)"
                        except Exception as e:
                            job["last_exit_code"] = -1
                            job["last_output"] = str(e)[:200]
                    else:
                        job["last_exit_code"] = 0
                        job["last_output"] = ""

                    job["last_run"] = now.isoformat()
                    schedule = job.get("schedule", "@every_minute")
                    job["next_run"] = _next_run_from_schedule(schedule)
                    changed = True

            if changed:
                save_wiki_tasks(data)

        except Exception:
            pass  # Scheduler darf nicht crashen

        try:
            threading.Event().wait(30)
        except KeyboardInterrupt:
            break


def start_scheduler():
    """Startet den Background-Scheduler-Thread."""
    global _scheduler_running
    _scheduler_running = True
    t = threading.Thread(target=_scheduler_loop, daemon=True, name="wiki-scheduler")
    t.start()


# --------------------------------------------------------------------


def parse_frontmatter(text):
    """Parses YAML-Frontmatter aus Markdown-Text."""
    meta = {}
    content = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
                content = parts[2].strip()
            except yaml.YAMLError:
                meta = {}
    return meta, content


def get_all_pages():
    """Liest alle Wiki-Seiten aus entities/ und concepts/ (via hermes_client)."""
    client = get_client()
    pages = []
    for section_dir, section_type in [(ENTITIES_DIR, "entity"), (CONCEPTS_DIR, "concept")]:
        section_path = str(section_dir)
        for filename in client.glob(section_path, "*.md"):
            file_path = f"{section_path}/{filename}"
            text = client.read_text(file_path)
            if text is None:
                continue
            meta, _content = parse_frontmatter(text)
            stem = filename[:-3] if filename.endswith(".md") else filename
            pages.append({
                "id": stem,
                "filename": filename,
                "title": meta.get("title", stem.replace("-", " ").title()),
                "section": section_type,
                "tags": [t.lower().strip() for t in meta.get("tags", [])],
                "created": meta.get("created", ""),
                "updated": meta.get("updated", ""),
                "type": meta.get("type", section_type),
            })
    pages.sort(key=lambda p: p["title"].lower())
    return pages


def get_all_tags(pages):
    """Sammelt alle einzigartigen Tags."""
    all_tags = set()
    for p in pages:
        for t in p["tags"]:
            all_tags.add(t)
    return sorted(all_tags)


def render_wikilinks(html_content):
    """Ersetzt [[wikilink]] mit echten Links (via hermes_client)."""
    client = get_client()
    wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')

    def replace_wikilink(m):
        target = m.group(1).strip()
        slug = re.sub(r'[^\w\säöüÄÖÜß-]', '', target).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        if client.exists(f"{ENTITIES_DIR}/{slug}.md"):
            return f'<a href="/entity/{slug}" class="wikilink">{target}</a>'
        elif client.exists(f"{CONCEPTS_DIR}/{slug}.md"):
            return f'<a href="/concept/{slug}" class="wikilink">{target}</a>'
        return f'<span class="wikilink-missing">{target}</span>'

    return wikilink_pattern.sub(replace_wikilink, html_content)


@app.route("/")
def index():
    """Dashboard – Startseite mit Übersicht über Hermes, Aufgaben, News, System."""
    return render_template("dashboard.html")


@app.route("/wiki")
@app.route("/wiki/")
def wiki_home():
    """Wiki-Übersicht: Entitäten, Konzepte, Tags, zuletzt geändert."""
    pages = get_all_pages()
    tags = get_all_tags(pages)
    entities = sorted([p for p in pages if p["section"] == "entity"], key=lambda p: p["title"].lower())
    concepts = sorted([p for p in pages if p["section"] == "concept"], key=lambda p: p["title"].lower())

    def get_sort_key(updated):
        from datetime import datetime
        if isinstance(updated, str):
            try:
                return datetime.fromisoformat(updated.replace('Z', '+00:00'))
            except:
                return datetime.min
        elif isinstance(updated, datetime):
            return updated
        else:
            return datetime.min

    recently = sorted(
        [p for p in pages if p.get("updated")],
        key=get_sort_key,
        reverse=True
    )[:10]

    log_entries = []
    log_content = get_client().read_text(str(WIKI_DIR / "log.md"))
    if log_content:
        log_entries = [l.strip() for l in log_content.split("\n") if l.strip().startswith("## [")][:15]

    return render_template("index.html",
        entities=entities, concepts=concepts, tags=tags,
        recently=recently, log_entries=log_entries,
        total_pages=len(pages))


@app.route("/entity/<page_id>")
@app.route("/concept/<page_id>")
def show_page(page_id):
    """Zeigt eine einzelne Wiki-Seite (via hermes_client)."""
    client = get_client()
    md_file = ENTITIES_DIR / f"{page_id}.md"
    section = "entity"
    text = client.read_text(str(md_file))
    if text is None:
        md_file = CONCEPTS_DIR / f"{page_id}.md"
        section = "concept"
        text = client.read_text(str(md_file))
    if text is None:
        flash("Seite nicht gefunden!", "error")
        return redirect(url_for("index"))

    meta, raw_content = parse_frontmatter(text)
    md_ext.reset()
    html_content = md_ext.convert(raw_content)
    html_content = render_wikilinks(html_content)

    return render_template("page.html",
        title=meta.get("title", page_id.replace("-", " ").title()),
        section=section, page_id=page_id, html_content=html_content,
        tags=[t.lower() for t in meta.get("tags", [])],
        created=meta.get("created", ""),
        updated=meta.get("updated", ""),
        filename=md_file.name)


@app.route("/delete/<section>/<page_id>", methods=["GET", "POST"])
def delete_page(section, page_id):
    """Löscht eine Wiki-Seite mit Bestätigung (via hermes_client)."""
    client = get_client()
    if section == "entity":
        md_file = ENTITIES_DIR / f"{page_id}.md"
    else:
        md_file = CONCEPTS_DIR / f"{page_id}.md"

    text = client.read_text(str(md_file))
    if text is None:
        flash("Seite nicht gefunden!", "error")
        return redirect(url_for("index"))

    meta, _ = parse_frontmatter(text)
    title = meta.get("title", page_id.replace("-", " ").title())

    if request.method == "POST":
        if not client.remove(str(md_file)):
            flash(f"Konnte '{title}' nicht löschen.", "error")
            return redirect(url_for("wiki_home"))
        flash(f"✓ Seite '{title}' gelöscht.", "success")
        return redirect(url_for("wiki_home"))

    # GET request - show confirmation
    return render_template("delete.html",
        title=title,
        section=section,
        page_id=page_id,
        filename=md_file.name)


@app.route("/upload/image", methods=["POST"])
def upload_image():
    """Lädt ein Bild für Wiki-Seiten hoch."""
    UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    if "image" not in request.files:
        return jsonify({"success": False, "error": "Keine Datei ausgewählt."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Keine Datei ausgewählt."}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid overwrites
        stem, suffix = Path(filename).stem, Path(filename).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{stem}_{timestamp}{suffix}"
        filepath = UPLOAD_DIR / filename
        file.save(str(filepath))
        return jsonify({"success": True, "url": f"/static/uploads/{filename}"})
    else:
        return jsonify({"success": False, "error": "Nur Bilddateien erlaubt (jpg, png, gif, webp)."}), 400


@app.route("/static/uploads/<filename>")
def uploaded_file(filename):
    """Liefert hochgeladene Dateien."""
    return send_from_directory(Path(__file__).parent / "static" / "uploads", filename)


@app.route("/api/uploads", methods=["GET"])
def api_list_uploads():
    """API: Alle hochgeladenen Bilder als JSON auflisten."""
    upload_dir = Path(__file__).parent / "static" / "uploads"
    images = []
    if upload_dir.exists():
        for f in sorted(upload_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}:
                images.append({"filename": f.name, "url": f"/static/uploads/{f.name}", "size": f.stat().st_size})
    return jsonify({"images": images})


@app.route("/api/uploads/<filename>", methods=["DELETE"])
def api_delete_upload(filename):
    """API: Hochgeladenes Bild löschen."""
    upload_dir = (Path(__file__).parent / "static" / "uploads").resolve()
    safe_name = secure_filename(filename)
    filepath = upload_dir / safe_name
    # Pfad-Traversalschutz: Datei muss tatsächlich im Upload-Verzeichnis liegen
    if filepath.exists() and filepath.parent == upload_dir:
        filepath.unlink()
        return jsonify({"success": True, "message": f"{safe_name} gelöscht"})
    return jsonify({"success": False, "error": "Datei nicht gefunden"}), 404


def allowed_file(filename):
    """Prüft ob die Dateiendung erlaubt ist."""
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "gif", "webp", "bmp", "svg"}


@app.route("/edit/<section>/<page_id>", methods=["GET", "POST"])
def edit_page(section, page_id):
    """Bearbeiten einer Wiki-Seite (via hermes_client)."""
    client = get_client()
    if section == "entity":
        md_file = ENTITIES_DIR / f"{page_id}.md"
    else:
        md_file = CONCEPTS_DIR / f"{page_id}.md"

    raw = client.read_text(str(md_file))
    if raw is None:
        flash("Seite nicht gefunden!", "error")
        return redirect(url_for("index"))

    meta, content = parse_frontmatter(raw)

    if request.method == "POST":
        new_title = request.form.get("title", "").strip()
        new_content = request.form.get("content", "").strip()
        tags_input = request.form.get("tags", "").strip()

        if new_title:
            meta["title"] = new_title
        meta["updated"] = datetime.now().strftime("%Y-%m-%d")

        tag_list = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else meta.get("tags", [])
        meta["tags"] = tag_list

        tag_yaml = ", ".join([f'"{t}"' for t in tag_list]) if tag_list else ""
        frontmatter = f"""---
title: "{meta.get('title', '')}"
created: {meta.get('created', datetime.now().strftime('%Y-%m-%d'))}
updated: {meta.get('updated', '')}
type: {section}
tags: [{tag_yaml}]
sources: []
---
"""
        if not client.write_text(str(md_file), frontmatter + "\n" + new_content):
            flash("Schreiben fehlgeschlagen.", "error")
            return redirect(url_for("show_page", page_id=page_id, section=section))

        flash(f"✓ Seite '{new_title}' erfolgreich gespeichert!", "success")
        return redirect(url_for("show_page", page_id=page_id, section=section))

    # GET request - render edit form
    title = meta.get("title", page_id.replace("-", " ").title())
    all_tags = get_all_tags(get_all_pages())
    return render_template(
        "edit.html",
        page_id=page_id,
        section=section,
        title=title,
        raw_content=content,
        filename=md_file.name,
        all_tags=sorted(all_tags),
        current_tags=meta.get("tags", []),
        current_tags_list=meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
    )


@app.route("/new", methods=["GET", "POST"])
def new_page():
    """Neue Wiki-Seite erstellen."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        section = request.form.get("section", "concept")
        tags = request.form.get("tags", "").strip()
        content = request.form.get("content", "").strip()

        if not title:
            flash("Bitte einen Titel eingeben!", "error")
            return render_template("new.html", section=section, all_tags=get_all_tags(get_all_pages()))

        slug = re.sub(r'[^\w\säöüÄÖÜß-]', '', title.lower()).strip()
        slug = re.sub(r'[\s]+', '-', slug)
        if len(slug) > 80:
            slug = slug[:80]

        client = get_client()
        target_dir = ENTITIES_DIR if section == "entity" else CONCEPTS_DIR
        md_file = target_dir / f"{slug}.md"

        if client.exists(str(md_file)):
            flash("Eine Seite mit dieser URL existiert bereits!", "error")
            return render_template("new.html", section=section, all_tags=get_all_tags(get_all_pages()))

        today = datetime.now().strftime("%Y-%m-%d")
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        tag_yaml = ", ".join([f'"{t}"' for t in tag_list])

        frontmatter = f"""---
title: "{title}"
created: {today}
updated: {today}
type: {section}
tags: [{tag_yaml}]
sources: []
---
"""
        if not client.write_text(str(md_file), frontmatter + "\n" + content):
            flash("Schreiben fehlgeschlagen.", "error")
            return render_template("new.html", section=section, all_tags=get_all_tags(get_all_pages()))

        flash(f"✓ Neue Seite '{title}' erstellt!", "success")
        return redirect(url_for("show_page", page_id=slug, section=section))

    all_tags = get_all_tags(get_all_pages())
    return render_template("new.html", section="concept", all_tags=all_tags)


@app.route("/search")
def search():
    """Volltextsuche mit Tag- und Bereichsfilter."""
    query = request.args.get("q", "").strip()
    tag_filter = request.args.get("tag", "").strip().lower()
    section_filter = request.args.get("section", "").strip().lower()

    if not query and not tag_filter and not section_filter:
        return redirect(url_for("index"))

    client = get_client()
    pages = get_all_pages()
    results = []
    snippets = {}
    query_lower = query.lower() if query else ""

    for p in pages:
        if section_filter and p["section"] != section_filter:
            continue
        if tag_filter and tag_filter not in p["tags"]:
            continue

        should_include = False
        if query:
            md_file = (ENTITIES_DIR if p["section"] == "entity" else CONCEPTS_DIR) / f"{p['id']}.md"
            text = client.read_text(str(md_file)) or ""
            text_lower = text.lower()
            if query_lower in text_lower or query_lower in p["title"].lower():
                should_include = True
                idx = text_lower.find(query_lower)
                if idx < 0:
                    idx = text_lower.find(p["title"].lower())
                if idx >= 0:
                    start = max(0, idx - 80)
                    end = min(len(text), idx + len(query) + 80)
                    snippet = text[start:end].strip()
                    snippets[p["id"]] = snippet
            elif query_lower in " ".join(p["tags"]):
                should_include = True
        else:
            should_include = True

        if should_include:
            results.append(p)

    return render_template("search.html", results=results, query=query,
                           tag_filter=tag_filter, section_filter=section_filter,
                           snippets=snippets, tags=get_all_tags(pages))


@app.route("/tags")
def show_tags():
    """Tag-Übersicht mit allen Seiten pro Tag."""
    pages = get_all_pages()
    tags_data = get_all_tags(pages)
    tag_pages = {}
    for t in tags_data:
        matching = [p for p in pages if t in p["tags"]]
        if matching:
            tag_pages[t] = matching

    return render_template("tags.html", tags=tag_pages, total_pages=len(pages))


@app.route("/api/pages")
def api_pages():
    """API: Alle Seiten als JSON."""
    pages = get_all_pages()
    return jsonify({"pages": pages, "total": len(pages)})


@app.route("/api/refresh")
def api_refresh():
    """API: Seite neu laden (für Auto-Refresh)."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


# --------------------------------------------------------------------
# Wiki-Import / Wiki-Export
# --------------------------------------------------------------------

def _slugify_filename(name: str) -> str:
    """Erzeugt einen sicheren slug aus einem (möglichen) Datei-/Titel-Namen."""
    base = name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    slug = re.sub(r"[^\w\säöüÄÖÜß-]", "", base).strip().lower()
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:80] or "entry"


@app.route("/api/wiki/import", methods=["POST"])
def api_wiki_import():
    """Importiert eine oder mehrere .md-Dateien als Wiki-Beiträge.

    Multipart-Form:
        files:    eine oder mehrere .md-Dateien
        section:  ``concept`` oder ``entity`` (Default: concept)
        overwrite: ``true``/``false`` (Default: false → Konflikte werden übersprungen)
    """
    section = (request.form.get("section") or "concept").lower()
    if section not in ("entity", "concept"):
        return jsonify({"error": "section muss 'entity' oder 'concept' sein"}), 400
    overwrite = (request.form.get("overwrite") or "").lower() in ("true", "1", "yes")
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "Keine Dateien hochgeladen"}), 400

    client = get_client()
    target_dir = ENTITIES_DIR if section == "entity" else CONCEPTS_DIR
    imported, skipped, errors = [], [], []
    for f in files:
        try:
            name = f.filename or ""
            if not name.lower().endswith(".md"):
                skipped.append({"name": name, "reason": "kein .md"})
                continue
            raw = f.read().decode("utf-8", errors="replace")
            slug = _slugify_filename(name)
            target = f"{str(target_dir).rstrip('/')}/{slug}.md"
            if client.exists(target) and not overwrite:
                skipped.append({"name": name, "reason": "existiert (overwrite=false)"})
                continue
            # Frontmatter ergänzen falls keiner vorhanden
            meta, content = parse_frontmatter(raw)
            today = datetime.now().strftime("%Y-%m-%d")
            if not meta:
                title = slug.replace("-", " ").title()
                meta = {"title": title, "created": today, "updated": today,
                        "type": section, "tags": [], "sources": []}
            meta.setdefault("updated", today)
            meta.setdefault("created", today)
            tag_list = meta.get("tags") or []
            if not isinstance(tag_list, list):
                tag_list = []
            tag_yaml = ", ".join(f'"{t}"' for t in tag_list)
            frontmatter = (
                f'---\n'
                f'title: "{meta.get("title", slug)}"\n'
                f'created: {meta.get("created")}\n'
                f'updated: {meta.get("updated")}\n'
                f'type: {section}\n'
                f'tags: [{tag_yaml}]\n'
                f'sources: {meta.get("sources", []) or "[]"}\n'
                f'---\n'
            )
            if not client.write_text(target, frontmatter + "\n" + content):
                errors.append({"name": name, "reason": "Schreiben fehlgeschlagen"})
                continue
            imported.append({"name": name, "slug": slug, "section": section})
        except Exception as ex:
            errors.append({"name": f.filename, "reason": str(ex)[:200]})

    return jsonify({
        "status": "ok",
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "counts": {"imported": len(imported), "skipped": len(skipped), "errors": len(errors)},
    })


@app.route("/api/wiki/export", methods=["GET"])
def api_wiki_export():
    """Exportiert das gesamte Wiki (entities + concepts) als ZIP-Download."""
    import io
    import zipfile
    client = get_client()

    buf = io.BytesIO()
    files_added = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for section_dir, sub in [(ENTITIES_DIR, "entities"), (CONCEPTS_DIR, "concepts")]:
            for filename in client.glob(str(section_dir), "*.md"):
                content = client.read_text(f"{str(section_dir).rstrip('/')}/{filename}")
                if content is None:
                    continue
                zf.writestr(f"{sub}/{filename}", content)
                files_added += 1
    buf.seek(0)
    if files_added == 0:
        # leere Datei, aber 200 mit Hinweis-File
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("README.txt", "Wiki ist leer — keine Beiträge zu exportieren.\n")
        buf.seek(0)

    fname = f"wiki-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return buf.read(), 200, {
        "Content-Type": "application/zip",
        "Content-Disposition": f'attachment; filename="{fname}"',
    }


_AUFGABEN_DEFAULT_PATH = Path(__file__).parent / "templates" / "aufgaben_default.md"


def _ensure_aufgaben_md(client) -> str:
    """Liest aufgaben.md vom Hermes-Agent; legt sie aus dem mitgelieferten
    Default-Template an, wenn sie fehlt. So funktioniert die Aufgaben-Seite
    direkt beim ersten Start ohne manuellen Setup-Schritt auf dem Agent.
    """
    aufgaben_path = str(BLOG_DIR / "aufgaben.md")
    content = client.read_text(aufgaben_path)
    if content:
        return content
    # Default anlegen
    try:
        default_text = _AUFGABEN_DEFAULT_PATH.read_text(encoding="utf-8")
    except OSError:
        default_text = "# Aufgabenliste\n\n## Offene Aufgaben\n\n## Erledigte Aufgaben\n"
    # Best-effort write — wenn der Agent nicht erreichbar ist, geben wir
    # einfach den Default-Text zurück, der nächste Quick-Prompt versucht es
    # erneut.
    try:
        client.write_text(aufgaben_path, default_text)
    except Exception:
        pass
    return default_text


@app.route("/aufgaben/")
@app.route("/aufgaben")
def aufgaben_page():
    """Portal-native Aufgaben-Seite (seit v1.1.9). Ersetzt die früher vom
    Hermes-Agent generierte ``aufgaben.html``. Liest/schreibt direkt nach
    ``BLOG_DIR/aufgaben.md`` — keine separaten Sync-Schritte mehr, kein
    Cronjob-Setup auf dem Agent nötig damit die Seite überhaupt erscheint.
    """
    return render_template(
        "aufgaben.html",
        agent_name=cfg.agent_name or "Wally",
        user_name=cfg.user_name or "User",
    )


@app.route("/api/aufgaben", methods=["GET", "POST"])
def api_aufgaben():
    """API: Aufgabenliste lesen/schreiben (via hermes_client – ssh-fähig)."""
    client = get_client()
    aufgaben_path = str(BLOG_DIR / "aufgaben.md")

    if request.method == "GET":
        content = _ensure_aufgaben_md(client)
        return jsonify({"content": content or ""})

    elif request.method == "POST":
        content = request.form.get("content", "") or (request.json or {}).get("content", "")
        if not content:
            return jsonify({"status": "error", "message": "Kein Inhalt"}), 400
        if not client.write_text(aufgaben_path, content):
            return jsonify({"status": "error", "message": "Schreiben fehlgeschlagen"}), 500
        return jsonify({"status": "ok", "message": "Aufgaben gespeichert"})


# --------------------------------------------------------------------
# Settings-Panel
# --------------------------------------------------------------------

@app.route("/settings/")
def settings_index():
    """Settings-Panel mit 3 Tabs: Personality & Memory, Cronjobs, Usage."""
    # Memory-Dateien lesen (über hermes_client – funktioniert lokal UND ssh)
    client = get_client()
    memory_contents = {}
    for key, path in MEMORY_FILES.items():
        content = client.read_text(str(path))
        if content is None:
            memory_contents[key] = f"# Datei existiert nicht: {path}\n# Erstelle neue Datei und speichere."
        else:
            memory_contents[key] = content

    # Wiki-eigene Tasks laden
    wiki_data = load_wiki_tasks()
    wiki_jobs = wiki_data.get("jobs", [])
    for job in wiki_jobs:
        job["source"] = "wiki"

    # Hermes-Cronjobs laden
    hermes_jobs = load_hermes_tasks()
    all_jobs = wiki_jobs + hermes_jobs

    # Usage laden
    usage = load_usage()
    today = datetime.now().strftime("%Y-%m-%d")
    if usage.get("date") != today:
        usage = {"date": today, "total_requests": 0, "hourly": {}}
        save_usage(usage)

    # Stunden für heute vorbereiten (0-23)
    hourly = usage.get("hourly", {})
    hours_data = {}
    max_val = max(hourly.values()) if hourly else 1
    for h in range(24):
        hk = f"{h:02d}:00"
        count = hourly.get(hk, 0)
        bar_pct = (count / max_val * 100) if max_val > 0 else 0
        hours_data[hk] = {"count": count, "bar_pct": min(bar_pct, 100)}

    return render_template("settings.html",
        memory_files=MEMORY_FILES,
        memory_contents=memory_contents,
        jobs=all_jobs,
        usage=usage,
        hours_data=hours_data,
        today=today,
        total_requests=usage.get("total_requests", 0))


@app.route("/api/settings/memory", methods=["GET", "POST"])
def api_settings_memory():
    """API: Memory-Dateien lesen/schreiben (via hermes_client – SSH-fähig)."""
    client = get_client()
    if request.method == "GET":
        name = request.args.get("name", "").strip()
        if not name or name not in MEMORY_FILES:
            return jsonify({"error": f"Unbekannte Datei. Erlaubt: {list(MEMORY_FILES.keys())}"}), 400
        path = MEMORY_FILES[name]
        content = client.read_text(str(path))
        if content is None:
            return jsonify({"name": name, "content": f"# Datei existiert nicht: {path}"})
        return jsonify({"name": name, "content": content})

    elif request.method == "POST":
        name = request.form.get("name", "").strip()
        content = request.form.get("content", "")
        if not name or name not in MEMORY_FILES:
            return jsonify({"error": f"Unbekannte Datei. Erlaubt: {list(MEMORY_FILES.keys())}"}), 400
        path = MEMORY_FILES[name]
        if not client.write_text(str(path), content):
            return jsonify({"error": f"Schreiben nach {path} fehlgeschlagen"}), 500
        return jsonify({"status": "ok", "message": f"{name} gespeichert"})


@app.route("/api/settings/tasks", methods=["GET", "POST"])
def api_settings_tasks():
    """API: Alle Tasks lesen (Wiki + Hermes) oder neuen Wiki-Task erstellen."""
    if request.method == "GET":
        # Wiki-Tasks
        wiki_data = load_wiki_tasks()
        wiki_jobs = wiki_data.get("jobs", [])
        for job in wiki_jobs:
            job["source"] = "wiki"

        # Hermes-Cronjobs
        hermes_jobs = load_hermes_tasks()

        # Default-Filter: "all" zeigt beides
        source_filter = request.args.get("source", "all")
        if source_filter == "wiki":
            return jsonify({"jobs": wiki_jobs})
        elif source_filter == "hermes":
            return jsonify({"jobs": hermes_jobs})

        return jsonify({"jobs": wiki_jobs + hermes_jobs})

    elif request.method == "POST":
        # Neue Cronjobs werden direkt im Hermes-Agent angelegt (hermes cron create)
        name = request.form.get("name", "").strip()
        schedule = request.form.get("schedule", "").strip()
        command = request.form.get("command", "").strip()
        prompt = request.form.get("prompt", "").strip()
        deliver = request.form.get("deliver", "origin").strip() or "origin"

        if not name or not schedule or not (command or prompt):
            return jsonify({"error": "Name, Schedule und Befehl/Prompt sind Pflichtfelder"}), 400

        task_text = prompt if prompt else command
        result = get_client().hermes(
            ["--accept-hooks", "cron", "create",
             "--name", name, "--deliver", deliver, schedule, task_text],
            timeout=20,
        )
        if result.ok:
            return jsonify({"status": "ok", "message": f"Hermes-Cronjob '{name}' erstellt"})
        return jsonify({"error": result.stderr or result.stdout or "Fehler beim Erstellen"}), 500


@app.route("/api/settings/tasks/<task_id>", methods=["PUT", "DELETE"])
def api_settings_task(task_id):
    """API: Einzelnen Task aktualisieren oder löschen.
    Erkennt anhand des source-Felds ob Wiki oder Hermes."""
    is_hermes = task_id.startswith("hermes:")
    actual_id = task_id.replace("hermes:", "") if is_hermes else task_id

    if is_hermes:
        client = get_client()
        # Hermes-Job: Vollzugriff via hermes cron CLI
        if request.method == "DELETE":
            result = client.hermes(["--accept-hooks", "cron", "remove", actual_id], timeout=15)
            if result.ok:
                return jsonify({"status": "ok", "message": "Hermes-Job gelöscht"})
            return jsonify({"error": result.stderr or "Fehler beim Löschen"}), 500

        elif request.method == "PUT":
            body = request.form
            # Pause / Resume
            if "enabled" in body:
                enabled_val = body.get("enabled", "").lower() in ("true", "1", "yes")
                action = "resume" if enabled_val else "pause"
                result = client.hermes(["--accept-hooks", "cron", action, actual_id], timeout=15)
                if result.ok:
                    return jsonify({"status": "ok", "message": f"Hermes-Job {'aktiviert' if enabled_val else 'pausiert'}"})
                # Fallback: direkt in jobs.json schreiben
                _update_hermes_job_enabled(actual_id, enabled_val)
                return jsonify({"status": "ok", "message": "Hermes-Job aktualisiert (fallback)"})
            # Edit Name / Schedule / Prompt
            # hermes cron edit unterstützt --name, --schedule, --prompt (NICHT --command!)
            if "name" in body or "schedule" in body or "command" in body or "prompt" in body:
                args = ["--accept-hooks", "cron", "edit", actual_id]
                updates = []
                if "name" in body:
                    args.extend(["--name", body["name"]])
                    updates.append("name")
                if "schedule" in body:
                    args.extend(["--schedule", body["schedule"]])
                    updates.append("schedule")
                prompt_val = body.get("command") or body.get("prompt", "")
                if prompt_val:
                    args.extend(["--prompt", prompt_val])
                    updates.append("prompt")

                if not updates:
                    return jsonify({"error": "Keine Änderungen"}), 400

                result = client.hermes(args, timeout=60)
                if result.ok:
                    return jsonify({"status": "ok", "message": f"Hermes-Job aktualisiert ({', '.join(updates)})"})
                return jsonify({"error": (result.stderr or "").strip()[:200]}), 500
            return jsonify({"error": "Kein bekanntes Feld zum Aktualisieren"}), 400
    else:
        # Wiki-Job: volles CRUD
        data = load_wiki_tasks()
        jobs = data.get("jobs", [])
        job_idx = None
        for i, j in enumerate(jobs):
            if j.get("id") == actual_id:
                job_idx = i
                break

        if job_idx is None:
            return jsonify({"error": "Task nicht gefunden"}), 404

        if request.method == "DELETE":
            jobs.pop(job_idx)
            save_wiki_tasks(data)
            return jsonify({"status": "ok", "message": "Task gelöscht"})

        elif request.method == "PUT":
            job = jobs[job_idx]
            body = request.form
            if "name" in body:
                job["name"] = body.get("name", "").strip()
            if "schedule" in body:
                job["schedule"] = body.get("schedule", "").strip()
                job["next_run"] = _next_run_from_schedule(job["schedule"])
            if "command" in body:
                job["command"] = body.get("command", "").strip()
            if "enabled" in body:
                job["enabled"] = body.get("enabled", "").lower() in ("true", "1", "yes")

            save_wiki_tasks(data)
            return jsonify({"status": "ok", "message": "Task aktualisiert", "job": job})


@app.route("/api/settings/tasks/<task_id>/run", methods=["POST"])
def api_run_task(task_id):
    """Führt einen Cronjob sofort aus (manuell triggern)."""
    is_hermes = task_id.startswith("hermes:")
    actual_id = task_id.replace("hermes:", "") if is_hermes else task_id

    if is_hermes:
        result = get_client().hermes(["--accept-hooks", "cron", "run", actual_id], timeout=15)
        if result.ok:
            return jsonify({"status": "ok", "message": "Hermes-Job wird ausgeführt"})
        return jsonify({"error": result.stderr or "Fehler beim Starten"}), 500
    else:
        # Wiki-Job: direkt ausführen
        data = load_wiki_tasks()
        job = next((j for j in data.get("jobs", []) if j.get("id") == actual_id), None)
        if not job:
            return jsonify({"error": "Task nicht gefunden"}), 404
        cmd = job.get("command", "")
        if not cmd:
            return jsonify({"error": "Kein Befehl definiert"}), 400
        try:
            subprocess.Popen(cmd, shell=True)
            return jsonify({"status": "ok", "message": "Wiki-Job gestartet"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


def _update_hermes_job_enabled(job_id, enabled):
    """Aktualisiert den enabled-Zustand eines Hermes-Jobs."""
    try:
        client = get_client()
        data = client.read_json(str(HERMES_CRON_FILE), default=None)
        if not isinstance(data, dict):
            return
        for j in data.get("jobs", []):
            if j.get("id") == job_id:
                j["enabled"] = enabled
                break
        client.write_json(str(HERMES_CRON_FILE), data)
    except Exception:
        pass


def _parse_token_stats_from_log(today: str) -> dict:
    """Parst Token-Statistiken aus agent.log für den heutigen Tag.
    Erkennt zwei Log-Formate:
    - Cloud (OpenRouter): API call #N: model=... provider=... in=X out=Y total=Z latency=Xs
    - Fehler/Abbruch: API call failed ... provider=... model=...
    - Lokale Calls (lmstudio/omlx): werden als 'conversation turn' mitgezählt,
      aber ohne Token-Daten falls Hermes dort keine Token-Counts loggt.
    """
    log_path = cfg.hermes_path("logs/agent.log")
    client = get_client()
    if not client.exists(log_path):
        return {}

    stats = {
        "total_in": 0, "total_out": 0, "total_tokens": 0,
        "total_calls": 0, "total_cache_hits": 0,
        "hourly": {},  # hh:00 -> {in, out, total, calls}
        "by_model": {},  # model -> {in, out, total, calls}
    }

    # Format 1: Vollständige API call Zeile mit Token-Daten
    token_pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2}) (\d{2}):\d{2}:\d{2}.*?API call #\d+: model=(\S+) provider=(\S+) "
        r"in=(\d+) out=(\d+) total=(\d+)"
        r"(?:.*?cache=(\d+)/\d+)?"
    )

    # Format 2: API call failed (zählt als Versuch, zeigt Modell)
    failed_pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2}) (\d{2}):\d{2}:\d{2}.*?API call (?:failed|Retrying).*?provider=(\S+) .*?model=(\S+)"
    )

    # Format 3: Conversation turn (für lokale Calls ohne Token-Daten)
    convo_pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2}) (\d{2}):\d{2}:\d{2}.*?conversation turn:.*?model=(\S+) provider=(\S+)"
    )

    # Track which sessions already had a successful API call logged (to avoid double counting convo turns)
    successful_sessions = set()

    def record_token(date_str, hour, model, in_t, out_t, total_t, cache_hits=0):
        """Hilfsfunktion: Token-Daten in stats eintragen."""
        stats["total_in"] += in_t
        stats["total_out"] += out_t
        stats["total_tokens"] += total_t
        stats["total_calls"] += 1
        stats["total_cache_hits"] += cache_hits

        hk = f"{hour}:00"
        if hk not in stats["hourly"]:
            stats["hourly"][hk] = {"in": 0, "out": 0, "total": 0, "calls": 0}
        stats["hourly"][hk]["in"] += in_t
        stats["hourly"][hk]["out"] += out_t
        stats["hourly"][hk]["total"] += total_t
        stats["hourly"][hk]["calls"] += 1

        # Modell-Normalisierung: letzter Teil nach / oder Leerzeichen
        short_model = model.split("/")[-1] if "/" in model else model
        short_model = short_model.split()[0]  # falls noch was dranhängt
        if short_model not in stats["by_model"]:
            stats["by_model"][short_model] = {"in": 0, "out": 0, "total": 0, "calls": 0}
        stats["by_model"][short_model]["in"] += in_t
        stats["by_model"][short_model]["out"] += out_t
        stats["by_model"][short_model]["total"] += total_t
        stats["by_model"][short_model]["calls"] += 1

    def record_call_only(date_str, hour, model):
        """Zählt einen Call ohne Token-Daten (lokales LLM ohne Token-Logging)."""
        stats["total_calls"] += 1

        hk = f"{hour}:00"
        if hk not in stats["hourly"]:
            stats["hourly"][hk] = {"in": 0, "out": 0, "total": 0, "calls": 0}
        stats["hourly"][hk]["calls"] += 1

        short_model = model.split("/")[-1] if "/" in model else model
        short_model = short_model.split()[0]
        if short_model not in stats["by_model"]:
            stats["by_model"][short_model] = {"in": 0, "out": 0, "total": 0, "calls": 0}
        stats["by_model"][short_model]["calls"] += 1

    try:
        # Für heutige Token-Stats reichen die letzten 10k Zeilen — schont SSH-Bandbreite.
        for line in client.tail(log_path, 10000):
            if not line.startswith(today):
                continue

            # Priorität 1: Token-Daten vorhanden
            m = token_pattern.match(line)
            if m:
                date_str, hour, model, provider, in_t, out_t, total_t = m.group(1), m.group(2), m.group(3), m.group(4), int(m.group(5)), int(m.group(6)), int(m.group(7))
                cache_hits = int(m.group(8)) if m.group(8) else 0
                record_token(date_str, hour, model, in_t, out_t, total_t, cache_hits)
                # Extrahiere Session-ID für dedup
                session_match = re.search(r"\[(\S+?)\]", line)
                if session_match:
                    successful_sessions.add(session_match.group(1))
                continue

            # Priorität 2: Failed call (zählt als Versuch)
            m = failed_pattern.match(line)
            if m:
                date_str, hour, provider, model = m.group(1), m.group(2), m.group(3), m.group(4)
                record_call_only(date_str, hour, model)
                continue

            # Priorität 3: Conversation turn für lokale Calls ohne Token-Daten
            m = convo_pattern.match(line)
            if m:
                date_str, hour, model, provider = m.group(1), m.group(2), m.group(3), m.group(4)
                session_match = re.search(r"\[(\S+?)\]", line)
                session_id = session_match.group(1) if session_match else None
                # Nur zählen wenn diese Session KEINEN erfolgreichen token-Eintrag hat
                # UND es ein lokaler Provider ist (lmstudio, omlx, ollama)
                if provider.lower() in ("lmstudio", "omlx", "ollama", "ollama-cloud"):
                    if session_id not in successful_sessions:
                        record_call_only(date_str, hour, model)
                        if session_id:
                            successful_sessions.add(session_id)
                continue

    except Exception:
        pass

    return stats


def _available_log_dates(max_days=14):
    """Liefert die letzten Datumswerte (YYYY-MM-DD), für die agent.log Einträge hat.

    Schaut in die letzten ~10k Zeilen (Tail), extrahiert distinct Daten und
    sortiert sie absteigend. Limitiert auf ``max_days`` Werte, damit der Picker
    nicht endlos wird.
    """
    log_path = cfg.hermes_path("logs/agent.log")
    client = get_client()
    if not client.exists(log_path):
        return [datetime.now().strftime("%Y-%m-%d")]
    seen = set()
    for line in client.tail(log_path, 10000):
        if len(line) >= 10 and line[4] == "-" and line[7] == "-":
            seen.add(line[:10])
    today = datetime.now().strftime("%Y-%m-%d")
    seen.add(today)
    # absteigend sortieren, dann beschneiden
    sorted_dates = sorted(seen, reverse=True)[:max_days]
    return sorted_dates


@app.route("/api/settings/usage")
def api_settings_usage():
    """API: Usage-Statistiken inkl. Token-Daten aus agent.log.

    Query: ``?date=YYYY-MM-DD`` (default = heute). Für andere Tage als heute
    sind Requests-Daten (aus usage.json) NICHT verfügbar, nur Token-Daten aus
    dem agent.log.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    requested_date = (request.args.get("date") or today).strip()
    # Sanity-Check (YYYY-MM-DD)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", requested_date):
        requested_date = today
    is_today = requested_date == today

    # Requests-Daten: nur für heute aus usage.json verfügbar
    if is_today:
        usage = load_usage()
        if usage.get("date") != today:
            usage = {"date": today, "total_requests": 0, "hourly": {}}
            save_usage(usage)
        hourly = usage.get("hourly", {})
        total_requests = usage.get("total_requests", 0)
    else:
        hourly = {}
        total_requests = None  # heißt: nicht verfügbar
    max_val = max(hourly.values()) if hourly else 1
    hours_data = {}
    for h in range(24):
        hk = f"{h:02d}:00"
        count = hourly.get(hk, 0)
        bar_pct = (count / max_val * 100) if max_val > 0 else 0
        hours_data[hk] = {"count": count, "bar_pct": min(bar_pct, 100)}

    token_stats = _parse_token_stats_from_log(requested_date)

    # Token-Stundendaten mit bar_pct anreichern
    token_hourly = token_stats.get("hourly", {})
    max_tok = max((v["total"] for v in token_hourly.values()), default=1)
    token_hours_data = {}
    for h in range(24):
        hk = f"{h:02d}:00"
        entry = token_hourly.get(hk, {"in": 0, "out": 0, "total": 0, "calls": 0})
        entry["bar_pct"] = min((entry["total"] / max_tok * 100) if max_tok > 0 else 0, 100)
        token_hours_data[hk] = entry

    return jsonify({
        "date": requested_date,
        "is_today": is_today,
        "total_requests": total_requests,
        "hourly": hours_data,
        "available_dates": _available_log_dates(),
        "tokens": {
            "total_in": token_stats.get("total_in", 0),
            "total_out": token_stats.get("total_out", 0),
            "total": token_stats.get("total_tokens", 0),
            "total_calls": token_stats.get("total_calls", 0),
            "total_cache_hits": token_stats.get("total_cache_hits", 0),
            "by_model": token_stats.get("by_model", {}),
            "hourly": token_hours_data,
        },
    })


# --------------------------------------------------------------------
# Dashboard- und System-APIs
# --------------------------------------------------------------------

def _hermes_log_path():
    """Liefert den Pfad zum aktuell existierenden Hermes-Logfile oder None.

    Im SSH-Mode wird via :meth:`HermesClient.first_existing` remote nach dem
    erstbesten existierenden Log-Kandidaten gesucht.
    """
    candidate = get_client().first_existing(str(p) for p in HERMES_LOG_CANDIDATES)
    return Path(candidate) if candidate else None


def _tail_lines(path, n: int = 200):
    """Liest die letzten n Zeilen einer Datei (via hermes_client – ssh-fähig)."""
    if not path:
        return []
    return get_client().tail(str(path), n)


def vm_now() -> datetime:
    """Aktuelle naive Wall-Clock-Zeit der VM (offset-korrigiert).

    Im local-Mode identisch zu ``datetime.now()``. Im SSH-Mode wird der
    Timezone-Offset zwischen Portal-Host und Hermes-VM addiert, damit
    Vergleiche mit naiven Timestamps aus ``jobs.json`` / Logs korrekt sind.
    """
    return datetime.now() + timedelta(seconds=get_client().time_offset_seconds())


def vm_dt_from_unix(unix_ts: float) -> datetime:
    """Wandelt eine Unix-Zeit in VM-naive Wall-Clock (für mtime-Vergleiche)."""
    return datetime.fromtimestamp(unix_ts) + timedelta(seconds=get_client().time_offset_seconds())


def _format_relative(iso_str):
    """Wandelt ISO-Timestamp/Datetime in 'vor 5 min' / 'gestern' / 'vor 3 Tagen'.

    Nutzt :func:`vm_now`, damit naive Timestamps aus der VM korrekt verglichen werden.
    """
    if not iso_str:
        return ""
    try:
        if isinstance(iso_str, datetime):
            dt = iso_str
        else:
            dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
        delta = vm_now() - dt
        secs = int(delta.total_seconds())
        if secs < 0:
            return "soeben"
        if secs < 60:
            return f"vor {secs}s"
        if secs < 3600:
            return f"vor {secs // 60} min"
        if secs < 86400:
            return f"vor {secs // 3600} h"
        days = secs // 86400
        if days == 1:
            return "gestern"
        return f"vor {days} Tagen"
    except (ValueError, TypeError):
        return ""


def get_hermes_status():
    """Status des Hermes-Agents auf Basis der jüngsten Cron-Aktivität und Log-Mtime."""
    last_activity = None
    last_source = None

    # 1) Hermes Cron jobs.json (via hermes_client)
    try:
        data = get_client().read_json(str(HERMES_CRON_FILE), default=None)
        if isinstance(data, dict):
            for j in data.get("jobs", []):
                t = j.get("last_run_at")
                if not t:
                    continue
                try:
                    dt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                    if dt.tzinfo is not None:
                        dt = dt.replace(tzinfo=None)
                    if last_activity is None or dt > last_activity:
                        last_activity = dt
                        last_source = "cron"
                except ValueError:
                    continue
    except Exception:
        pass

    # 2) Hermes-Logfile mtime (via hermes_client – SSH-fähig)
    log_path = _hermes_log_path()
    if log_path:
        mtime = get_client().mtime(str(log_path))
        if mtime is not None:
            log_dt = vm_dt_from_unix(mtime)
            if last_activity is None or log_dt > last_activity:
                last_activity = log_dt
                last_source = "log"

    now = vm_now()
    state = "unknown"
    if last_activity is None:
        state = "unknown"
    else:
        secs = (now - last_activity).total_seconds()
        if secs < 600:        # < 10 min
            state = "online"
        elif secs < 3600:     # < 1 h
            state = "idle"
        else:
            state = "offline"

    return {
        "state": state,
        "last_activity": last_activity.isoformat() if last_activity else None,
        "last_activity_human": _format_relative(last_activity) if last_activity else "—",
        "source": last_source,
        "log_path": str(log_path) if log_path else None,
    }


def get_aufgaben_summary():
    """Zählt offene/erledigte Aufgaben in aufgaben.md (Sektion-basiert; via hermes_client)."""
    text = get_client().read_text(str(BLOG_DIR / "aufgaben.md"))
    if text is None:
        return {"open": 0, "done": 0, "open_titles": [], "recent_tasks": []}

    # Sektionsweise parsen
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
    open_titles = []
    open_count = 0
    done_count = 0
    all_tasks = []  # [(title, is_done), ...]

    for sec in sections:
        head = sec.split("\n", 1)[0].lower()
        items = re.findall(r"^###\s+(.+)$", sec, flags=re.MULTILINE)
        if "offen" in head or "bearbeitung" in head:
            for item in items:
                item_pattern = re.compile(
                    r"^###\s+" + re.escape(item) + r"\s*\n(.*?)(?=^###|\Z)",
                    re.MULTILINE | re.DOTALL
                )
                m = item_pattern.search(sec)
                item_body = m.group(1) if m else ""
                status_m = re.search(r"\*\*Status\*\*:\s*(.+)", item_body)
                is_done = False
                if status_m:
                    st = status_m.group(1).lower()
                    if "erledigt" in st or "✅" in st or "abgeschlossen" in st or "fertig" in st:
                        done_count += 1
                        is_done = True
                if not is_done:
                    open_count += 1
                    open_titles.append(item)
                all_tasks.append({"title": item, "done": is_done})
        elif "erledigt" in head or "abgeschlossen" in head or "fertig" in head:
            done_count += len(items)
            for item in items:
                all_tasks.append({"title": item, "done": True})

    # Die 2 aktuellsten Aufgaben für Dashboard. All_tasks wird in Dokument-Reihenfolge
    # gesammelt: Offene zuerst (chronologisch die NEUESTEN), dann Erledigte (älter).
    # all_tasks[:2] sind also immer die neuesten — das Template rendert t.done korrekt.
    recent_tasks = all_tasks[:2] if len(all_tasks) >= 2 else all_tasks

    return {"open": open_count, "done": done_count, "open_titles": open_titles[:5], "recent_tasks": recent_tasks}


def get_briefing_snippet():
    """Liefert Headline + ersten Absatz des aktuellsten Briefings (via hermes_client)."""
    client = get_client()
    path = str(BLOG_DIR / "briefing.html")
    text = client.read_text(path)
    if text is None:
        return None

    title_m = re.search(r"<title>([^<]+)</title>", text)
    h2_m = re.search(r"<h2>([^<]+)</h2>", text, re.IGNORECASE)
    # erstes <p> nach class="content"
    p_m = re.search(r'<div class="content">.*?<p>([^<]{20,400})', text, re.DOTALL | re.IGNORECASE)
    if not p_m:
        p_m = re.search(r"<p>([^<]{30,400})</p>", text, re.IGNORECASE)
    snippet = p_m.group(1).strip() if p_m else ""
    snippet = re.sub(r"\s+", " ", snippet)[:280]

    mtime_human = ""
    mtime = client.mtime(path)
    if mtime is not None:
        mtime_human = _format_relative(vm_dt_from_unix(mtime))

    return {
        "title": (h2_m.group(1) if h2_m else (title_m.group(1) if title_m else "Briefing")).strip(),
        "snippet": snippet,
        "updated_human": mtime_human,
        "url": "/briefing/",
    }


def get_latest_news(n=3):
    """Liest die neuesten News-Headlines aus blog/posts.json oder index.html (via hermes_client)."""
    client = get_client()
    items = []

    data = client.read_json(str(BLOG_DIR / "posts.json"), default=None)
    if data is not None:
        arr = data if isinstance(data, list) else data.get("posts", [])
        for p in arr[:n]:
            items.append({
                "title": p.get("title", "Beitrag"),
                "url": p.get("url") or p.get("path") or "/blog/",
                "date": p.get("date", ""),
            })
        if items:
            return items

    # Fallback: parse index.html
    text = client.read_text(str(BLOG_DIR / "index.html"))
    if text is not None:
        for m in re.finditer(r'<h2><a href="([^"]+)">([^<]+)</a></h2>\s*<p class="post-summary">([^<]*)</p>\s*<p class="meta">([^|<]+)', text):
            items.append({
                "title": m.group(2).strip(),
                "url": "/blog/" + m.group(1).strip(),
                "summary": m.group(3).strip()[:160],
                "date": m.group(4).strip(),
            })
            if len(items) >= n:
                break
    return items


def get_next_cronjobs(n=4):
    """Nächste anstehende Hermes-Cronjobs (sortiert nach next_run_at)."""
    data = get_client().read_json(str(HERMES_CRON_FILE), default=None)
    if not isinstance(data, dict):
        return []
    jobs = []
    for j in data.get("jobs", []):
        if not j.get("enabled", True):
            continue
        nxt = j.get("next_run_at") or j.get("next_run", "")
        if not nxt:
            continue
        try:
            dt = datetime.fromisoformat(str(nxt).replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
        except ValueError:
            continue
        now = vm_now()
        if dt < now:
            # Überfälliger Job (cron-daemon hat next_run_at noch nicht aktualisiert)
            mins_overdue = int((now - dt).total_seconds() // 60)
            human = f"überfällig (seit {mins_overdue} min)" if mins_overdue >= 1 else "überfällig"
            overdue = True
        else:
            secs = (dt - now).total_seconds()
            if secs < 60:
                human = "in <1 min"
            elif secs < 3600:
                human = f"in {int(secs // 60)} min"
            elif secs < 86400:
                hours = int(secs // 3600)
                mins = int((secs % 3600) // 60)
                human = f"in {hours}h {mins}min" if mins else f"in {hours}h"
            else:
                days = int(secs // 86400)
                hours = int((secs % 86400) // 3600)
                human = f"in {days}d {hours}h" if hours else f"in {days}d"
            overdue = False
        jobs.append({
            "id": j.get("id", ""),
            "name": j.get("name", "Unbekannt"),
            "next_run": dt.isoformat(),
            "next_run_human": human,
            "overdue": overdue,
            "schedule": (j.get("schedule", {}) or {}).get("display") if isinstance(j.get("schedule"), dict) else str(j.get("schedule", "")),
        })
    jobs.sort(key=lambda x: x["next_run"])
    return jobs[:n]


def get_active_cronjob_count():
    """Zählt alle aktiven Hermes-Cronjobs."""
    data = get_client().read_json(str(HERMES_CRON_FILE), default=None)
    if not isinstance(data, dict):
        return 0
    return sum(1 for j in data.get("jobs", []) if j.get("enabled", True))


def get_recent_wiki_changes(n=5):
    """Liefert die n zuletzt aktualisierten Wiki-Pages mit Deep-Link.

    Sortiert ``get_all_pages()`` nach Frontmatter-``updated`` desc und liefert
    pro Eintrag Titel, Datum, Section und URL (für Klick → Wiki-Beitragsseite).
    """
    pages = get_all_pages()

    def _sort_key(page):
        upd = page.get("updated") or page.get("created") or ""
        if isinstance(upd, datetime):
            return upd.isoformat()
        return str(upd)

    pages = [p for p in pages if (p.get("updated") or p.get("created"))]
    pages.sort(key=_sort_key, reverse=True)

    result = []
    for p in pages[:n]:
        section = p.get("section") or "entity"
        pid = p.get("id")
        if not pid:
            continue
        result.append({
            "id":      pid,
            "title":   p.get("title") or pid.replace("-", " ").title(),
            "section": section,                                # "entity" oder "concept"
            "date":    str(p.get("updated") or p.get("created") or ""),
            "url":     f"/{section}/{pid}",
        })
    return result


def get_system_stats():
    """Liefert CPU/RAM/Disk/Uptime des Hermes-Hosts (Linux-spezifisch).

    Nutzt :mod:`hermes_client` → funktioniert lokal **und** über SSH.
    Im SSH-Mode werden /proc/stat, /proc/meminfo, /proc/uptime, /proc/loadavg
    vom Remote-Host gelesen. Disk-Stats via ``df`` (in :meth:`client.statvfs`).
    """
    stats = {"cpu_pct": None, "ram_pct": None, "ram_used_gb": None, "ram_total_gb": None,
             "disk_pct": None, "disk_free_gb": None, "disk_total_gb": None,
             "uptime_human": None, "load_1m": None}
    client = get_client()

    # CPU – /proc/stat sampling (2 Reads im Abstand von ~120ms)
    def _cpu_times():
        raw = client.read_text("/proc/stat")
        if not raw:
            return None
        line = raw.splitlines()[0]
        parts = line.split()[1:9]
        try:
            vals = [int(x) for x in parts]
        except ValueError:
            return None
        if len(vals) < 4:
            return None
        idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
        total = sum(vals)
        return idle, total
    try:
        s1 = _cpu_times()
        if s1 is not None:
            threading.Event().wait(0.12)
            s2 = _cpu_times()
            if s2 is not None:
                i1, t1 = s1
                i2, t2 = s2
                dt = max(1, t2 - t1)
                di = i2 - i1
                stats["cpu_pct"] = round(100.0 * (dt - di) / dt, 1)
    except Exception:
        pass

    # RAM – /proc/meminfo
    try:
        raw = client.read_text("/proc/meminfo")
        if raw:
            info = {}
            for line in raw.splitlines():
                k, _, rest = line.partition(":")
                v = rest.strip().split()
                if v:
                    try:
                        info[k] = int(v[0])
                    except ValueError:
                        continue
            total_kb = info.get("MemTotal", 0)
            avail_kb = info.get("MemAvailable", info.get("MemFree", 0))
            used_kb = max(0, total_kb - avail_kb)
            if total_kb:
                stats["ram_total_gb"] = round(total_kb / 1024 / 1024, 1)
                stats["ram_used_gb"] = round(used_kb / 1024 / 1024, 1)
                stats["ram_pct"] = round(100.0 * used_kb / total_kb, 1)
    except Exception:
        pass

    # Disk – Austausch-Mount via client.statvfs (lokal: os.statvfs; ssh: df)
    try:
        sv = client.statvfs(cfg.exchange_path)
        if sv is not None:
            total, free = sv
            if total:
                stats["disk_total_gb"] = round(total / (1024 ** 3), 1)
                stats["disk_free_gb"] = round(free / (1024 ** 3), 1)
                stats["disk_pct"] = round(100.0 * (total - free) / total, 1)
    except Exception:
        pass

    # Uptime
    try:
        raw = client.read_text("/proc/uptime")
        if raw:
            secs = float(raw.split()[0])
            days = int(secs // 86400)
            hours = int((secs % 86400) // 3600)
            mins = int((secs % 3600) // 60)
            if days:
                stats["uptime_human"] = f"{days}d {hours}h"
            elif hours:
                stats["uptime_human"] = f"{hours}h {mins}min"
            else:
                stats["uptime_human"] = f"{mins}min"
    except Exception:
        pass

    # Load 1m
    try:
        raw = client.read_text("/proc/loadavg")
        if raw:
            stats["load_1m"] = float(raw.split()[0])
    except Exception:
        pass

    return stats




# ---- Settings: Memories ----

def _parse_memory_entries(content_text):
    """Parst MEMORY.md / USER.md in einzelne Einträge (getrennt durch §-Zeilen)."""
    if not content_text or not content_text.strip():
        return []
    lines = content_text.splitlines()
    entries = []
    current = []
    for line in lines:
        if line.strip() == '§':
            if current:
                entries.append('\n'.join(current).strip())
                current = []
        else:
            current.append(line)
    if current:
        entries.append('\n'.join(current).strip())
    return entries


def _serialize_memory_entries(entries):
    """Serialisiert Einträge zurück in Datei-Inhalt mit §-Separatoren."""
    return '\n§\n'.join(entries)


@app.route("/api/settings/memories")
def api_settings_memories():
    """API: Liefert alle Memory-Einträge als geparste Liste.
    Jeder Eintrag aus MEMORY.md / USER.md (getrennt durch §) wird einzeln zurückgegeben."""
    client = get_client()
    all_entries = []
    LABELS = {"soul": "🔮 SOUL", "user": "👤 USER", "memory": "💾 MEMORY", "config": "⚙️ Config"}

    for key, path in MEMORY_FILES.items():
        if key == "config":
            continue  # config.yaml hat keine §-Einträge
        content_text = client.read_text(str(path))
        if content_text is None:
            continue

        entries = _parse_memory_entries(content_text)

        for idx, entry in enumerate(entries):
            preview_lines = entry.strip().splitlines()
            preview = preview_lines[0][:140] if preview_lines else "(leer)"
            all_entries.append({
                "id": f"{key}:{idx}",
                "file_key": key,
                "file_path": str(path),
                "file_label": LABELS.get(key, key),
                "index": idx,
                "content": entry,
                "preview": preview,
                "lines": len(preview_lines),
                "size": len(entry),
            })

    return jsonify({"entries": all_entries, "total": len(all_entries)})


@app.route("/api/settings/memories/<file_key>/<int:entry_index>", methods=["PUT", "DELETE"])
def api_memory_entry(file_key, entry_index):
    """API: Einzelnen Memory-Eintrag aktualisieren (PUT) oder löschen (DELETE)."""
    if file_key not in MEMORY_FILES or file_key == "config":
        return jsonify({"error": f"Unbekannte Datei: {file_key}"}), 400

    client = get_client()
    path = MEMORY_FILES[file_key]
    content_text = client.read_text(str(path))
    if content_text is None:
        return jsonify({"error": f"Datei nicht gefunden: {path}"}), 404

    entries = _parse_memory_entries(content_text)

    if entry_index < 0 or entry_index >= len(entries):
        return jsonify({"error": f"Eintrag {entry_index} nicht in {file_key} gefunden"}), 404

    if request.method == "PUT":
        new_content = request.form.get("content", "") or (request.json or {}).get("content", "")
        entries[entry_index] = new_content.strip()
        if not client.write_text(str(path), _serialize_memory_entries(entries)):
            return jsonify({"error": f"Schreiben nach {path} fehlgeschlagen"}), 500
        return jsonify({"status": "ok", "message": "Eintrag aktualisiert"})

    elif request.method == "DELETE":
        entries.pop(entry_index)
        if not client.write_text(str(path), _serialize_memory_entries(entries)):
            return jsonify({"error": f"Schreiben nach {path} fehlgeschlagen"}), 500
        return jsonify({"status": "ok", "message": "Eintrag gelöscht", "remaining": len(entries)})


@app.route("/api/settings/memories/<file_key>", methods=["POST"])
def api_memory_create(file_key):
    """API: Neuen Memory-Eintrag ans Ende der Datei anhängen."""
    if file_key not in MEMORY_FILES or file_key == "config":
        return jsonify({"error": f"Unbekannte Datei: {file_key}"}), 400

    client = get_client()
    path = MEMORY_FILES[file_key]
    new_content = request.form.get("content", "") or (request.json or {}).get("content", "")
    if not new_content.strip():
        return jsonify({"error": "Kein Inhalt angegeben"}), 400

    existing = client.read_text(str(path))
    entries = _parse_memory_entries(existing) if existing is not None else []

    entries.append(new_content.strip())
    if not client.write_text(str(path), _serialize_memory_entries(entries)):
        return jsonify({"error": f"Schreiben nach {path} fehlgeschlagen"}), 500

    return jsonify({"status": "ok", "message": "Eintrag erstellt", "index": len(entries) - 1})


# ---- Settings: Skills (Split View) ----
# CUSTOM_SKILLS_DIR ist in _refresh_paths() definiert (dynamisch aus cfg).


def _scan_skill_dir(base_dir: Path, source_type: str) -> list:
    """Scannt ein Skill-Verzeichnis rekursiv und liefert url_key-basierte Einträge.

    Findet alle SKILL.md Dateien (max depth 2 überspringt Kategorie-Ordner die selbst keine sind).
    Ignoriert versteckte Ordner (.xyz) und die .hub / .archive Systemverzeichnisse.
    url_key enthält den relativen Pfad vom Basis, z.B. skills:hermes/autonomous-ai-agents/claude-code
    """
    results = []
    client = get_client()
    base_str = str(base_dir).rstrip("/")
    if not client.exists(base_str):
        return results

    def _scan(dirpath: str):
        for entry in client.list_dir(dirpath):
            if not entry.is_dir:
                continue
            name = entry.name
            if name.startswith(".") or name in (".hub", ".archive"):
                continue
            child_path = f"{dirpath}/{name}"
            skill_md = f"{child_path}/SKILL.md"
            content = client.read_text(skill_md)
            if content is not None:
                # Skill-Verzeichnis (hat SKILL.md)
                rel = child_path[len(base_str):].lstrip("/")
                url_key = f"skills:{source_type}/{rel}"
                title = name
                category = source_type
                desc = ""
                try:
                    if content.startswith("---"):
                        parts = content.split("---", 3)
                        if len(parts) >= 3:
                            import yaml
                            meta = yaml.safe_load(parts[1]) or {}
                            title = meta.get("title", name)
                            category = meta.get("category", source_type)
                            desc = meta.get("description", "")
                except Exception:
                    pass
                results.append({
                    "url_key": url_key,
                    "name": name,
                    "title": title,
                    "category": category,
                    "description": desc,
                    "source": source_type,
                    "path": child_path,
                    "has_skill_md": True,
                })
            else:
                # Kategorie-Ordner – tiefer gehen
                _scan(child_path)

    _scan(base_str)
    return results

@app.route("/api/settings/skills")
def api_settings_skills():
    """API: Liefert alle Skills (Hermes + Custom) als url_key-Liste."""
    all_skills = []
    # 1) User Skills aus ~/.hermes/skills/
    all_skills.extend(_scan_skill_dir(HERMES_SKILLS_DIR, "hermes"))
    # 2) Built-in Hermes-Agent Skills aus hermes-agent/skills/
    all_skills.extend(_scan_skill_dir(HERMES_BUILTIN_SKILLS_DIR, "builtin"))
    # 3) Custom Skills aus Wiki
    all_skills.extend(_scan_skill_dir(CUSTOM_SKILLS_DIR, "custom"))
    # 3) Kategorie-Gruppen aus available_skills (plugin-provided)
    # (optional, falls gewünscht – wir zeigen erstmal die lokalen)
    return jsonify({"skills": all_skills})


def _skill_base_dir(source_type: str) -> Path:
    if source_type == "hermes":   return HERMES_SKILLS_DIR
    if source_type == "builtin":  return HERMES_BUILTIN_SKILLS_DIR
    return CUSTOM_SKILLS_DIR


@app.route("/api/settings/skill-content", methods=["GET"])
def api_skill_content_get():
    """API: Liest Skill-Inhalt via url_key (via hermes_client)."""
    url_key = request.args.get("url_key", "")
    if not url_key or not url_key.startswith("skills:"):
        return jsonify({"error": "Ungültiger url_key"}), 400

    parts = url_key.split("/", 1)
    if len(parts) != 2:
        return jsonify({"error": "Ungültiges Format"}), 400
    source_type = parts[0].replace("skills:", "")
    skill_name = parts[1]

    client = get_client()
    base = _skill_base_dir(source_type)
    skill_dir = f"{str(base).rstrip('/')}/{skill_name}"
    if not client.is_dir(skill_dir):
        return jsonify({"error": f"Skill '{skill_name}' nicht gefunden"}), 404

    skill_md = f"{skill_dir}/SKILL.md"
    content = client.read_text(skill_md)
    return jsonify({
        "url_key": url_key,
        "name": skill_name,
        "content": content if content is not None else "",
        "path": skill_md,
    })


@app.route("/api/settings/skill-content", methods=["POST"])
def api_skill_content_save():
    """API: Speichert Skill-Inhalt via url_key (via hermes_client)."""
    data = request.json or {}
    url_key = data.get("url_key", "")
    content = data.get("content", "")
    if not url_key or not url_key.startswith("skills:"):
        return jsonify({"error": "Ungültiger url_key"}), 400

    parts = url_key.split("/", 1)
    if len(parts) != 2:
        return jsonify({"error": "Ungültiges Format"}), 400
    source_type = parts[0].replace("skills:", "")
    skill_name = parts[1]

    client = get_client()
    base = _skill_base_dir(source_type)
    skill_dir = f"{str(base).rstrip('/')}/{skill_name}"
    if not client.is_dir(skill_dir):
        if source_type == "custom":
            client.mkdir(skill_dir)
        else:
            return jsonify({"error": f"Skill '{skill_name}' nicht gefunden"}), 404

    skill_md = f"{skill_dir}/SKILL.md"
    if not client.write_text(skill_md, content):
        return jsonify({"error": "Schreiben fehlgeschlagen"}), 500
    return jsonify({"status": "ok", "message": f"Skill '{skill_name}' gespeichert"})


@app.route("/api/settings/skill-content", methods=["DELETE"])
def api_skill_content_delete():
    """API: Löscht einen Custom-Skill via url_key (via hermes_client)."""
    url_key = request.args.get("url_key", "")
    if not url_key or not url_key.startswith("skills:"):
        return jsonify({"error": "Ungültiger url_key"}), 400

    parts = url_key.split("/", 1)
    if len(parts) != 2:
        return jsonify({"error": "Ungültiges Format"}), 400
    source_type = parts[0].replace("skills:", "")
    skill_name = parts[1]

    if source_type != "custom":
        return jsonify({"error": "Hermes-Skills können nicht gelöscht werden"}), 403

    client = get_client()
    skill_dir = f"{str(CUSTOM_SKILLS_DIR).rstrip('/')}/{skill_name}"
    if not client.is_dir(skill_dir):
        return jsonify({"error": f"Skill '{skill_name}' nicht gefunden"}), 404

    if not client.rmtree(skill_dir):
        return jsonify({"error": "Löschen fehlgeschlagen"}), 500
    return jsonify({"status": "ok", "message": f"Skill '{skill_name}' gelöscht"})


# ---- Dashboard-API ---------------------------------------------------

@app.route("/api/dashboard/status")
def api_dashboard_status():
    """Aggregierte Live-Daten fürs Dashboard – wird per Polling abgefragt."""
    return jsonify({
        "hermes": get_hermes_status(),
        "system": get_system_stats(),
        "aufgaben": get_aufgaben_summary(),
        "briefing": get_briefing_snippet(),
        "news": get_latest_news(3),
        "next_jobs": get_next_cronjobs(4),
        "active_cronjobs": get_active_cronjob_count(),
        "wiki_recent": get_recent_wiki_changes(5),
        "now": datetime.now().isoformat(),
    })


# ---- Activity-Feed (Hermes-Log) -------------------------------------

@app.route("/activity/")
def activity_page():
    """Live-Log des Hermes-Agenten."""
    log_path = _hermes_log_path()
    return render_template("activity.html",
                           log_path=str(log_path) if log_path else None,
                           candidates=[str(p) for p in HERMES_LOG_CANDIDATES])


@app.route("/api/activity/log")
def api_activity_log():
    """Tail des Hermes-Logs (via hermes_client – local + ssh)."""
    log_path = _hermes_log_path()
    if not log_path:
        return jsonify({"lines": [], "size": 0, "path": None,
                        "candidates": [str(p) for p in HERMES_LOG_CANDIDATES],
                        "error": "Kein Hermes-Logfile gefunden"})

    client = get_client()
    # mtime dient als „Versionsmarker" für die JS-Polling-Logik – ersetzt das alte byte-size-Feld.
    mtime = client.mtime(str(log_path)) or 0
    n = request.args.get("n", default=300, type=int)
    n = max(10, min(2000, n))
    lines = client.tail(str(log_path), n)
    return jsonify({
        "lines": lines,
        "size": int(mtime * 1000),  # JS-Client nutzt das als monoton wachsende Version
        "mtime": mtime,
        "path": str(log_path),
        "incremental": False,
    })


# ---- Quick-Prompt --------------------------------------------------

@app.route("/api/quick-prompt", methods=["POST"])
def api_quick_prompt():
    """Hängt eine neue Aufgabe an aufgaben.md (Abschnitt 'Offene Aufgaben')."""
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or request.form.get("title") or "").strip()
    body = (payload.get("body") or request.form.get("body") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "Titel fehlt"}), 400

    client = get_client()
    aufgaben_path = str(BLOG_DIR / "aufgaben.md")
    text = _ensure_aufgaben_md(client)
    if text is None or not text.strip():
        text = "# Aufgabenliste\n\n## Offene Aufgaben\n\n## Erledigte Aufgaben\n"

    block = f"\n### {title}\n- **Bearbeiter**: {cfg.agent_name}\n- **Status**: Offen\n- **Erstellt**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    if body:
        block += f"- Beschreibung: {body}\n"

    # Einfügen direkt nach "## Offene Aufgaben"
    pattern = re.compile(r"(##\s+Offene Aufgaben\s*\n)", re.IGNORECASE)
    if pattern.search(text):
        text = pattern.sub(r"\1" + block, text, count=1)
    else:
        # Sektion fehlt – am Anfang einfügen
        text = "## Offene Aufgaben\n" + block + "\n" + text

    if not client.write_text(aufgaben_path, text):
        return jsonify({"ok": False, "error": "Schreibfehler"}), 500

    # Audit-Log
    try:
        entry = {"ts": datetime.now().isoformat(), "title": title, "body": body}
        with open(QUICK_PROMPTS_LOG, "a", encoding="utf-8") as f:
            f.write(json_module.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass

    return jsonify({"ok": True, "title": title})


# ---- System-Status-API (für Dashboard und Settings) -----------------

@app.route("/api/system-status")
def api_system_status():
    """Standalone System-Stats."""
    return jsonify(get_system_stats())


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        Path(__file__).parent / "static" / "portal",
        "logo.png",
        mimetype="image/png",
    )


# --------------------------------------------------------------------
# Blog-Statische Dateien (CSS, JS) für Wiki-Design
# BLOG_STATIC_DIR ist in _refresh_paths() definiert.
# --------------------------------------------------------------------

# Statische Bearbeiter-Namen in user-generierten Blog-HTMLs (z.B. aufgaben.html),
# die wir beim Ausliefern durch die aktuelle Config-Identität ersetzen.
_BLOG_NAME_PATTERNS = [
    ("Wally", lambda: cfg.agent_name),
    ("Jan",   lambda: cfg.user_name),
]


# Regex zum Entfernen der ``<div class="hero-links">…</div>``-Box auf
# statischen Blog-Pages (führt zu Buttons wie "Neueste Beiträge"/"Anleitungen",
# die im Portal-Kontext keine Funktion haben).
_BLOG_HERO_LINKS_RE = re.compile(
    r'<div\s+class="hero-links"\s*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)

# Regex zum Ersetzen des Blog-Footers durch einen einheitlichen Portal-Footer.
_BLOG_FOOTER_RE = re.compile(r'<footer[^>]*>.*?</footer>', re.DOTALL | re.IGNORECASE)


def _serve_blog_file(filename: str):
    """Liefert eine Blog-Datei aus.

    Für HTML wird der Inhalt durch :mod:`hermes_client` gelesen, sodass das
    sowohl lokal als auch über SSH funktioniert. In HTML-Dateien werden:
      - hardcodierte 'Jan'/'Wally'/'JaysTecWorld'-Vorkommen durch die aktuellen
        Config-Werte ersetzt (Bearbeiter-Dropdowns, Titel, etc.)
      - der ``.hero-links``-Block entfernt
      - der ``<footer>`` durch einen einheitlichen Portal-Footer ersetzt
      - die Header-Script-Referenz auf die aktuelle Portal-Version umgeschrieben
      - ``window.HP_BRAND``/``HP_PORTAL_NAME`` injected, damit der gemeinsame
        site-header.js die Branding-Settings anwendet
    Andere Dateitypen werden binär durchgereicht.
    """
    client = get_client()
    full_path = str(BLOG_STATIC_DIR / filename)
    is_html = filename.lower().endswith(('.html', '.htm'))
    # HA-Ingress-Prefix: leerer String wenn standalone, sonst z.B.
    # ``/api/hassio_ingress/<TOKEN>``. Wird unten an ALLE hardcodierten
    # "/static/..."- und "/blog/..."-Pfade im served HTML angeflanscht,
    # sonst fragt der Browser gegen die HA-Origin → 404 → kein CSS/JS,
    # kein Header (genau der Aufgaben-Layout-Bug aus v1.0.3).
    prefix = (request.script_root or "")
    if is_html:
        text = client.read_text(full_path)
        if text is None:
            # Freundlicher Hinweis statt nacktem 404: News/Aufgaben/Briefing-
            # Dateien werden vom Hermes-Agent erzeugt (Cronjob). Wenn das
            # Portal solo läuft (z. B. HA-Add-on im local-Mode ohne aktive
            # Agent-VM auf demselben Share), gibt es die Dateien noch nicht.
            # Page-Label aus i18n: nutzt aktuelle Sprache → page_label sieht
            # auch in der Fallback-Meldung übersetzt aus.
            _lang = cfg.get("language") or "en"
            page_label = {
                "index.html":    _i18n.t("nav.news",     _lang),
                "aufgaben.html": _i18n.t("nav.aufgaben", _lang),
                "briefing.html": _i18n.t("nav.briefing", _lang),
            }.get(filename, filename)
            return render_template(
                "blog_missing.html",
                page_label=page_label,
                filename=filename,
                full_path=full_path,
            ), 404
        agent = cfg.agent_name or "Hermes"
        user = cfg.user_name or "User"
        if agent != "Wally":
            text = text.replace("Wally", agent)
        if user != "Jan":
            text = text.replace("Jan", user)
        # JaysTecWorld → Agent-Name (Title, Header, …). Wenn der User den
        # Brand-Namen wirklich „JaysTecWorld" haben will, kann er ihn in
        # Settings → App eintragen — die Substitution greift dann nicht.
        text = text.replace("JaysTecWorld", agent)

        # Hero-Buttons (Anleitungen/Kategorien) entfernen
        text = _BLOG_HERO_LINKS_RE.sub("", text)

        # site-header.js → unsere aktuelle Portal-Version umleiten, damit auch
        # Blog-Pages das brand-aware Header-Rendering bekommen.
        text = text.replace(
            'src="/blog/site-header.js"',
            'src="/static/portal/site-header.js"'
        )

        # Altes/fehlendes Favicon des User-Blogs durch das Portal-Logo ersetzen.
        # Browser nimmt den LETZTEN <link rel="icon">; daher einfach den
        # vorhandenen Tag durch unseren ersetzen.
        text = re.sub(
            r'<link\s+rel="(?:shortcut )?icon"[^>]*>',
            '<link rel="icon" href="/static/portal/logo.png" type="image/png">'
            '<link rel="apple-touch-icon" href="/static/portal/logo.png">',
            text,
            flags=re.IGNORECASE,
        )

        # Vor dem </head> ein Script + Mini-Style einfügen. Die alten Blog-CSS
        # kennen weder die ``.brand-logo``- noch die Hermes-Status-Klassen für
        # den ``.live-dot``. Beides inline injizieren, damit Blog-Pages dasselbe
        # Verhalten wie Portal-Pages haben (Logo nicht riesig, Dot nicht immer grün).
        brand_injection = (
            '<style>'
            # Logo-Größe (gegen das default 500×500-PNG)
            '.site-header .header-logo .brand-logo {'
                'width:2em;height:2em;object-fit:contain;flex-shrink:0;'
            '}'
            # Live-Dot: alte „immer grün + pulse"-Regel der Blog-CSS überschreiben.
            # Default = grau. Status-Klassen kommen vom site-header.js Polling.
            '.site-header .header-logo .live-dot{'
                'background:#6b7280!important;animation:none!important;'
                'transition:background 0.3s ease;'
            '}'
            '.site-header .header-logo .live-dot.status-online{'
                'background:#22c55e!important;'
                'animation:hp-pulse-green 2.4s ease-in-out infinite!important;'
            '}'
            '.site-header .header-logo .live-dot.status-idle{'
                'background:#f59e0b!important;'
                'animation:hp-pulse-amber 3.6s ease-in-out infinite!important;'
            '}'
            '.site-header .header-logo .live-dot.status-offline{'
                'background:#ef4444!important;animation:none!important;'
            '}'
            '.site-header .header-logo .live-dot.status-unknown{'
                'background:#6b7280!important;animation:none!important;'
            '}'
            '@keyframes hp-pulse-green{'
                '0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,0.55);}'
                '50%{box-shadow:0 0 0 6px rgba(34,197,94,0);}'
            '}'
            '@keyframes hp-pulse-amber{'
                '0%,100%{box-shadow:0 0 0 0 rgba(245,158,11,0.4);}'
                '50%{box-shadow:0 0 0 5px rgba(245,158,11,0);}'
            '}'
            '</style>'
            # Portal-Stylesheet einbinden, damit Aufgaben/News/Briefing dieselben
            # Card/Button/Color-Klassen kennen wie der Rest. Ohne diese Zeile
            # rendert die Blog-HTML nur mit ihren eigenen, deutlich kargeren Styles.
            f'<link rel="stylesheet" href="/static/portal/style.css?v={_ASSET_VERSION}">'
            # Favicon-Backup (falls Blog-HTML keinen <link rel="icon"> hat)
            '<link rel="icon" href="/static/portal/logo.png" type="image/png">'
            '<script>'
            f'window.HP_INGRESS_PATH={json_module.dumps(prefix)};'
            f'window.HP_BRAND={json_module.dumps(agent)};'
            f'window.HP_PORTAL_NAME="Hermes Portal";'
            # Mini-Fetch-Patcher (gleiches Muster wie in base.html), damit
            # JS in den Blog-HTMLs absolute /-URLs unter Ingress trifft.
            'if(window.HP_INGRESS_PATH){var _p=window.HP_INGRESS_PATH;'
            'var _of=window.fetch;window.fetch=function(u,o){'
            'if(typeof u==="string"&&u.charAt(0)==="/"&&u.indexOf(_p)!==0){u=_p+u;}'
            'return _of.call(this,u,o);};}'
            '</script>'
        )
        if "</head>" in text:
            text = text.replace("</head>", brand_injection + "</head>", 1)
        else:
            text = brand_injection + text

        # Footer einheitlich: Logo + "Hermes Portal © <Jahr>".
        year = datetime.now().year
        portal_footer = (
            '<footer class="footer" style="display:flex;align-items:center;'
            'justify-content:center;gap:8px;text-align:center;padding:1rem 0;'
            'color:var(--text-dim);font-size:0.85rem;">'
            '<img src="/static/portal/logo.png" alt="" class="footer-logo" '
            'style="width:1.6em;height:1.6em;object-fit:contain;opacity:0.85;" aria-hidden="true">'
            f'<span>Hermes Portal &copy; {year}</span>'
            '</footer>'
        )
        text = _BLOG_FOOTER_RE.sub(portal_footer, text, count=1)

        # HA-Ingress: ALLE absoluten /-URLs in href/src um den Prefix
        # ergänzen. Greift sowohl auf vom Hermes-Agent generierte Links
        # (z.B. /blog/post-2026-05-22.html) als auch auf alle von uns
        # injizierten /static/portal/...-Pfade.
        if prefix:
            def _prefix_url(match):
                attr, quote, url = match.group(1), match.group(2), match.group(3)
                if (url.startswith(prefix)
                        or url.startswith('//')
                        or url.startswith('http')):
                    return match.group(0)
                return f'{attr}={quote}{prefix}{url}{quote}'
            text = re.sub(
                r'(href|src)=(["\'])(/[^"\']*)\2',
                _prefix_url,
                text,
            )

        return text, 200, {"Content-Type": "text/html; charset=utf-8"}

    data = client.read_bytes(full_path)
    if data is None:
        abort(404)
    mime, _ = mimetypes.guess_type(filename)
    return data, 200, {"Content-Type": mime or "application/octet-stream"}


@app.route("/blog/")
def blog_index():
    return _serve_blog_file("index.html")


@app.route("/blog/<path:filename>")
def blog_static(filename):
    return _serve_blog_file(filename)


# --------------------------------------------------------------------
# Explorer – Datei-Browser für den konfigurierten Austausch-Ordner.
# SHARED_ROOT ist in _refresh_paths() definiert.
# --------------------------------------------------------------------

PREVIEWABLE_TEXT = {
    ".md", ".txt", ".log", ".yaml", ".yml", ".json", ".py", ".sh", ".html",
    ".css", ".js", ".ini", ".cfg", ".conf", ".xml", ".csv", ".tsv",
}
PREVIEWABLE_IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}


def _safe_resolve(subpath: str) -> str:
    """Liefert einen absoluten Pfad innerhalb SHARED_ROOT oder bricht mit 403 ab.

    Rein textuelle Normalisierung — funktioniert auch im SSH-Mode (kein remote stat-call).
    Schutz vor ``..``-Traversal und absoluten Pfaden.
    """
    sub = (subpath or "").strip().lstrip("/").replace("\\", "/")
    parts = []
    for p in sub.split("/"):
        if p in ("", "."):
            continue
        if p == "..":
            if not parts:
                abort(403)  # Versuch, SHARED_ROOT zu verlassen
            parts.pop()
            continue
        # NUL-Bytes oder andere böse Zeichen rausfiltern
        if "\x00" in p:
            abort(403)
        parts.append(p)
    root_str = str(SHARED_ROOT).rstrip("/")
    return f"{root_str}/{'/'.join(parts)}" if parts else root_str


def _file_icon_for(name: str, is_dir: bool) -> str:
    """Emoji-Icon (rein textuell — kein FS-Zugriff)."""
    if is_dir:
        return "📁"
    ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
    if ext in PREVIEWABLE_IMAGE:
        return "🖼️"
    if ext == ".pdf":                                    return "📕"
    if ext in {".zip", ".tar", ".gz", ".7z", ".rar"}:    return "🗜️"
    if ext == ".md":                                     return "📝"
    if ext == ".py":                                     return "🐍"
    if ext in {".html", ".htm"}:                         return "🌐"
    if ext == ".css":                                    return "🎨"
    if ext in {".js", ".mjs", ".ts"}:                    return "📜"
    if ext in {".json", ".yaml", ".yml"}:                return "⚙️"
    if ext in {".txt", ".log", ".csv", ".tsv"}:          return "📃"
    if ext in {".mp3", ".wav", ".flac", ".ogg"}:         return "🎵"
    if ext in {".mp4", ".mkv", ".webm", ".mov"}:         return "🎬"
    return "📄"


def _file_type_label_for(name: str, is_dir: bool) -> str:
    if is_dir:
        return "Ordner"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return f"{ext.upper()}-Datei" if ext else "Datei"


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _list_dir(path_str: str) -> list:
    """Listet Verzeichnis-Inhalte als sortierte Liste von Dicts (via hermes_client)."""
    entries = []
    for entry in get_client().list_dir(path_str):
        if entry.name.startswith("."):
            continue
        ext = "." + entry.name.rsplit(".", 1)[-1].lower() if "." in entry.name else ""
        mtime_dt = datetime.fromtimestamp(entry.modified) if entry.modified else None
        entries.append({
            "name": entry.name,
            "is_dir": entry.is_dir,
            "icon": _file_icon_for(entry.name, entry.is_dir),
            "type_label": _file_type_label_for(entry.name, entry.is_dir),
            "size": entry.size if not entry.is_dir else None,
            "size_human": _human_size(entry.size) if not entry.is_dir else "",
            "mtime": mtime_dt.strftime("%d.%m.%Y %H:%M") if mtime_dt else "",
            "mtime_iso": mtime_dt.isoformat() if mtime_dt else "",
            "ext": ext,
        })
    entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
    return entries


def _breadcrumbs(rel_parts: list) -> list:
    """[(label, href, is_current), ...] für die Adressleiste."""
    crumbs = [(cfg.exchange_path, url_for("explorer_root"), len(rel_parts) == 0)]
    accum = ""
    for i, part in enumerate(rel_parts):
        accum = (accum + "/" + part).lstrip("/")
        crumbs.append((part, url_for("explorer_browse", subpath=accum), i == len(rel_parts) - 1))
    return crumbs


@app.route("/explorer/")
def explorer_root():
    return explorer_browse(subpath="")


@app.route("/explorer/<path:subpath>")
def explorer_browse(subpath=""):
    """Verzeichnis-Listing oder Datei anzeigen/downloaden (via hermes_client)."""
    client = get_client()
    root_str = str(SHARED_ROOT).rstrip("/")

    if not client.exists(root_str):
        flash(f"Austausch-Ordner {SHARED_ROOT} ist nicht verfügbar.", "error")
        return render_template("explorer.html",
            entries=[], crumbs=[(root_str, "#", True)],
            current_path="", parent_path=None, missing=True)

    target = _safe_resolve(subpath)
    st = client.stat(target)
    if st is None:
        flash("Pfad nicht gefunden.", "error")
        return redirect(url_for("explorer_root"))

    if not st.is_dir:
        # Datei ausliefern
        inline = request.args.get("inline") == "1"
        fname = target.rsplit("/", 1)[-1]
        if client.mode == "local":
            # Lokaler Pfad → sendfile-Optimierung
            return send_file(target, as_attachment=not inline, download_name=fname)
        # SSH-Mode → Bytes vom Remote-Host streamen
        data = client.read_bytes(target)
        if data is None:
            abort(404)
        mime, _ = mimetypes.guess_type(fname)
        headers = {}
        if not inline:
            headers["Content-Disposition"] = f'attachment; filename="{fname}"'
        return data, 200, {"Content-Type": mime or "application/octet-stream", **headers}

    # Verzeichnis-Listing
    rel = target[len(root_str):].lstrip("/")
    rel_parts = [p for p in rel.split("/") if p]
    parent_subpath = "/".join(rel_parts[:-1]) if rel_parts else None
    entries = _list_dir(target)
    crumbs = _breadcrumbs(rel_parts)
    current_subpath = "/".join(rel_parts)

    return render_template(
        "explorer.html",
        entries=entries,
        crumbs=crumbs,
        current_path=current_subpath,
        parent_path=parent_subpath,
        missing=False,
        absolute_path=target,
    )


@app.route("/explorer/upload", methods=["POST"])
def explorer_upload():
    """Multipart-Upload: Felder 'target' (subpath) und 'files' (multiple). Via hermes_client."""
    client = get_client()
    target_sub = request.form.get("target", "")
    target_dir = _safe_resolve(target_sub)
    if not client.is_dir(target_dir):
        flash("Upload-Ziel ist kein Verzeichnis.", "error")
        return redirect(url_for("explorer_root"))

    files = request.files.getlist("files")
    if not files:
        flash("Keine Datei ausgewählt.", "error")
        return redirect(url_for("explorer_browse", subpath=target_sub))

    saved = 0
    for f in files:
        if not f or not f.filename:
            continue
        name = secure_filename(f.filename)
        if not name:
            continue

        # Kollision auflösen: "file.txt" → "file (1).txt" → "file (2).txt" …
        dest = f"{target_dir}/{name}"
        if client.exists(dest):
            if "." in name:
                stem, suffix = name.rsplit(".", 1)
                suffix = "." + suffix
            else:
                stem, suffix = name, ""
            i = 1
            while True:
                candidate = f"{target_dir}/{stem} ({i}){suffix}"
                if not client.exists(candidate):
                    dest = candidate
                    break
                i += 1

        data = f.read()
        if client.write_bytes(dest, data):
            saved += 1
        else:
            flash(f"Fehler beim Speichern von {name}", "error")

    if saved:
        flash(f"✓ {saved} Datei(en) hochgeladen.", "success")

    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify({"ok": True, "saved": saved})
    return redirect(url_for("explorer_browse", subpath=target_sub) if target_sub else url_for("explorer_root"))


@app.route("/explorer/delete", methods=["POST"])
def explorer_delete():
    """Datei oder Ordner löschen (Ordner rekursiv, via hermes_client)."""
    client = get_client()
    rel = request.form.get("path", "")
    parent = request.form.get("parent", "")
    target = _safe_resolve(rel)
    root_str = str(SHARED_ROOT).rstrip("/")

    st = client.stat(target)
    if st is None:
        flash("Eintrag existiert nicht.", "error")
    elif target == root_str:
        flash("Wurzelverzeichnis kann nicht gelöscht werden.", "error")
    else:
        name = target.rsplit("/", 1)[-1]
        ok = client.rmtree(target) if st.is_dir else client.remove(target)
        if ok:
            flash(f"✓ '{name}' gelöscht.", "success")
        else:
            flash(f"Löschen fehlgeschlagen: {name}", "error")

    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify({"ok": True})
    return redirect(url_for("explorer_browse", subpath=parent) if parent else url_for("explorer_root"))


@app.route("/explorer/mkdir", methods=["POST"])
def explorer_mkdir():
    """Neues Verzeichnis erstellen (via hermes_client)."""
    client = get_client()
    parent = request.form.get("parent", "")
    name = (request.form.get("name", "") or "").strip()
    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        flash("Ungültiger Verzeichnisname.", "error")
        return redirect(url_for("explorer_browse", subpath=parent) if parent else url_for("explorer_root"))

    parent_dir = _safe_resolve(parent)
    if not client.is_dir(parent_dir):
        flash("Ziel-Verzeichnis nicht gefunden.", "error")
        return redirect(url_for("explorer_root"))

    new_dir = f"{parent_dir}/{name}"
    if client.exists(new_dir):
        flash(f"'{name}' existiert bereits.", "error")
    elif client.mkdir(new_dir):
        flash(f"✓ Ordner '{name}' angelegt.", "success")
    else:
        flash(f"Konnte Ordner '{name}' nicht anlegen.", "error")

    return redirect(url_for("explorer_browse", subpath=parent) if parent else url_for("explorer_root"))



# SOURCE_DIRS ist in _refresh_paths() definiert (dynamisch aus cfg).


def _collect_source_files(source_type, config):
    """Scannt definierte Quellen und liefert ``(path_str, source_type, rel_path)``-Tupel.

    Nutzt :mod:`hermes_client` — funktioniert lokal und über SSH.
    """
    client = get_client()
    entries = []
    extensions = config["extensions"]
    for base_dir in config["dirs"]:
        base_str = str(base_dir).rstrip("/")
        if not client.exists(base_str):
            continue

        if config["scan_recursive"]:
            # Rekursiv nach Unterordnern mit dem Namen `scan_sub` suchen (z.B. "references"),
            # und dann darin alle Dateien sammeln.
            sub_name = config["scan_sub"]
            for dirpath, dirs, files in client.walk(base_str):
                if Path(dirpath).name != sub_name:
                    continue
                for fname in sorted(files):
                    if "." + fname.rsplit(".", 1)[-1].lower() in extensions or "" in extensions:
                        full = f"{dirpath}/{fname}"
                        rel = full[len(base_str):].lstrip("/")
                        entries.append((full, source_type, rel))
        else:
            # Nur die Top-Ebene des Verzeichnisses
            for entry in client.list_dir(base_str):
                if entry.is_dir:
                    continue
                if "." + entry.name.rsplit(".", 1)[-1].lower() in extensions:
                    full = f"{base_str}/{entry.name}"
                    entries.append((full, source_type, entry.name))
    return entries


@app.route("/api/references")
def api_references_list():
    """API: Liefert Referenz-Dateien aus allen Quellen (via hermes_client)."""
    client = get_client()
    all_entries = []
    for source_type, config in SOURCE_DIRS.items():
        for path_str, stype, rel_path in _collect_source_files(source_type, config):
            st = client.stat(path_str)
            if st is None:
                continue
            content = client.read_text(path_str)
            if content is None:
                continue
            preview_lines = content.splitlines()
            preview = preview_lines[0][:200] if preview_lines else "(leer)"
            name = path_str.rsplit("/", 1)[-1]
            url_key = f"{stype}/{rel_path}"
            all_entries.append({
                "name": name,
                "url_key": url_key,
                "path": path_str,
                "content": content,
                "preview": preview,
                "lines": len(preview_lines),
                "size": st.size,
                "size_human": _human_size(st.size),
                "mtime": datetime.fromtimestamp(st.modified).strftime("%d.%m.%Y %H:%M"),
                "source": config["label"],
                "source_type": stype,
            })
    all_entries.sort(key=lambda e: (e["source"], e["name"]))
    return jsonify({"references": all_entries, "total": len(all_entries)})


def _resolve_file_from_url_key(url_key):
    """Löst source_type/rel_path in einen Pfad-String auf (via hermes_client)."""
    parts = url_key.split("/", 1)
    if len(parts) != 2:
        return None
    source_type, rel_path = parts
    config = SOURCE_DIRS.get(source_type)
    if not config:
        return None
    client = get_client()
    for base_dir in config["dirs"]:
        candidate = f"{str(base_dir).rstrip('/')}/{rel_path}"
        if client.exists(candidate):
            return candidate
    return None


@app.route("/api/references/<path:url_key>", methods=["GET", "PUT"])
def api_references_detail(url_key):
    """API: Liest oder schreibt eine Referenz-Datei (via hermes_client)."""
    client = get_client()
    path_str = _resolve_file_from_url_key(url_key)
    if not path_str:
        return jsonify({"error": f"Datei nicht gefunden: {url_key}"}), 404

    if request.method == "GET":
        content = client.read_text(path_str)
        if content is None:
            return jsonify({"error": "Datei nicht lesbar"}), 404
        return jsonify({"name": path_str.rsplit("/", 1)[-1], "path": path_str, "content": content})

    elif request.method == "PUT":
        content = request.form.get("content", "") or (request.json or {}).get("content", "")
        if not content:
            return jsonify({"error": "Kein Inhalt angegeben"}), 400
        if not client.write_text(path_str, content):
            return jsonify({"error": "Schreiben fehlgeschlagen"}), 500
        return jsonify({"status": "ok", "message": "Datei gespeichert"})


@app.route("/api/references/<path:url_key>", methods=["DELETE"])
def api_references_delete(url_key):
    """API: Löscht eine Referenz-Datei (via hermes_client)."""
    client = get_client()
    path_str = _resolve_file_from_url_key(url_key)
    if not path_str:
        return jsonify({"error": f"Datei nicht gefunden: {url_key}"}), 404
    if not client.remove(path_str):
        return jsonify({"error": "Löschen fehlgeschlagen"}), 500
    return jsonify({"status": "ok", "message": f"{path_str.rsplit('/', 1)[-1]} gelöscht"})


# ======================================================================
# Chat Routes (User ↔ Hermes-Agent)
# ======================================================================

import sqlite3 as _sqlite3

def _chat_db():
    """Init chat-DB und return Conn."""
    db_path = app.config['CHAT_DB']
    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT 'Neuer Chat',
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    return conn

CHAT_DB = str(DATA_DIR / 'chat.db')
SHARED_UPLOAD_ROOT = str(DATA_DIR / 'uploads')
# SHARED_FOLDER ist in _refresh_paths() definiert.
os.makedirs(SHARED_UPLOAD_ROOT, exist_ok=True)
os.makedirs(os.path.dirname(CHAT_DB), exist_ok=True)
app.config['CHAT_DB'] = CHAT_DB

# Init DB on startup
with _chat_db():
    pass  # tables created by side-effect


@app.route("/chat/")
def chat_page():
    """Chat-Seite – User ↔ Hermes-Agent direkt im Portal."""
    return render_template("chat.html")


@app.route("/api/chat/new", methods=["POST"])
def api_chat_new():
    """Neuen Chat anlegen."""
    conn = _chat_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO chats (title) VALUES ('Neuer Chat')")
    conn.commit()
    chat_id = cur.lastrowid
    conn.close()
    return jsonify({"chat_id": chat_id, "title": "Neuer Chat"})


@app.route("/api/chat/list")
def api_chat_list():
    """Chat-Liste (letzten zuerst)."""
    conn = _chat_db()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT c.id, c.title, c.updated,
               (SELECT m.content FROM messages m WHERE m.chat_id=c.id ORDER BY m.id DESC LIMIT 1) as preview
        FROM chats c ORDER BY c.updated DESC
    """).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "title": r["title"],
            "updated": r["updated"],
            "preview": r["preview"][:80] if r["preview"] else ""
        })
    return jsonify(result)


@app.route("/api/chat/delete/<int:chat_id>", methods=["POST"])
def api_chat_delete(chat_id):
    """Chat löschen."""
    conn = _chat_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    cur.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "message": "Chat gelöscht"})


@app.route("/api/chat/messages")
def api_chat_messages():
    """Nachrichten eines Chats laden."""
    chat_id = request.args.get("chat_id", type=int)
    if not chat_id:
        return jsonify({"error": "chat_id fehlt"}), 400
    conn = _chat_db()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT role, content, created FROM messages WHERE chat_id=? ORDER BY id",
        (chat_id,)
    ).fetchall()
    conn.close()
    return jsonify([{"role": r["role"], "content": r["content"], "created": r["created"]} for r in rows])


@app.route("/api/chat/send", methods=["POST"])
def api_chat_send():
    """Nachricht senden → Agent antwortet."""
    data = request.get_json(silent=True) or {}
    chat_id = data.get("chat_id")
    message = data.get("message", "").strip()
    if not chat_id or not message:
        return jsonify({"error": "chat_id und message erforderlich"}), 400

    conn = _chat_db()
    cur = conn.cursor()

    # Speichere User-Nachricht
    cur.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, 'user', ?)", (chat_id, message))
    conn.commit()

    # Update chat timestamp
    cur.execute("UPDATE chats SET updated = CURRENT_TIMESTAMP WHERE id = ?", (chat_id,))
    conn.commit()

    # Update title from first user message
    cur.execute("SELECT COUNT(*) as cnt FROM messages WHERE chat_id = ? AND role = 'user'", (chat_id,))
    user_count = cur.fetchone()["cnt"]
    if user_count <= 1:
        title = message[:40] + ("..." if len(message) > 40 else "")
        cur.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))
        conn.commit()

    # === Agent antwortet ===
    # Echte LLM-Antwort über Hermes CLI mit Chat-Historie als Kontext
    bot_answer = _call_hermes_llm(chat_id, message, cur)

    cur.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, 'bot', ?)", (chat_id, bot_answer))
    conn.commit()
    conn.close()

    return jsonify({"reply": bot_answer, "chat_id": chat_id})


def _call_hermes_llm(chat_id, user_message, cursor):
    """Sendet Nachricht an Hermes-LLM und gibt die Antwort zurück.

    Nutzt den aktuellen Chat-Verlauf als Kontext für die konfigurierbare Agent-Persona.
    Funktioniert sowohl im local- als auch im ssh-Mode (geht über :mod:`hermes_client`).
    """
    # Chat-Verlauf laden (letzte 20 Nachrichten als Kontext)
    cursor.execute(
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT 20",
        (chat_id,)
    )
    history = cursor.fetchall()
    history.reverse()  # chronologisch

    agent = cfg.agent_name or "Hermes"
    user  = cfg.user_name  or "User"
    persona = cfg.agent_persona.strip() or (
        f"Du bist {agent}, ein freundlicher, hilfsbereiter Assistent. "
        "Antworte locker auf Deutsch, gib konkrete Hinweise."
    )

    context_parts = [persona]
    for msg in history:
        role = msg["role"] if isinstance(msg, dict) else msg[0]
        content = msg["content"] if isinstance(msg, dict) else msg[1]
        prefix = f"{user}:" if role == "user" else f"{agent}:"
        context_parts.append(f"{prefix} {content}")
    context_parts.append(f"{user}: {user_message}")

    full_prompt = "\n".join(context_parts)

    client = get_client()
    # Direkter hermes-Aufruf (bevorzugt). Falls fehlend, fällt der User-Output verständlich aus.
    result = client.hermes(["-z", full_prompt], timeout=120)
    if result.ok and result.stdout.strip():
        return result.stdout.strip()
    err = (result.stderr or result.stdout or "keine Ausgabe").strip()[:400]

    # Häufigster Fall: hermes-Binary nicht im PATH (= Portal läuft auf einem
    # Host, auf dem Hermes nicht installiert ist). Beim local-Mode passiert das
    # IMMER, wenn der Mac das Portal direkt ausführt. → klarer Hinweis statt
    # kryptischer FileNotFoundError.
    is_missing_binary = (
        result.returncode == 127
        or "No such file or directory" in err
        or "Befehl nicht gefunden" in err
        or "command not found" in err.lower()
    )
    if is_missing_binary:
        if client.mode == "local":
            return (
                f"⚠️ Das Portal läuft im **local-Mode**, aber der `hermes`-CLI-Binary ist auf "
                "diesem Host nicht installiert.\n\n"
                "**Lösung:** Wechsel in den **SSH-Mode**, damit Hermes auf seiner VM aufgerufen wird. "
                "→ [Settings → 🛰️ App](/settings/) und dort:\n"
                "  • Modus: `SSH`\n"
                "  • Host/IP der Hermes-VM eintragen\n"
                "  • Verbindung testen → grün\n"
            )
        return (
            "⚠️ Der `hermes`-Befehl wurde auf der konfigurierten Hermes-VM nicht gefunden. "
            f"Konfigurierter Binary-Name: `{cfg.hermes_bin}`. "
            "Prüfe in **Settings → 🛰️ App** den Wert *Hermes-Binary* "
            "(z.B. `/root/.local/bin/hermes`) oder ob Hermes überhaupt installiert ist."
        )

    if result.returncode == -1 and "Timeout" in err:
        return "Das hat zu lange gedauert – versuch es bitte mit einer kürzeren Nachricht."
    return f"Da ist etwas schiefgelaufen: {err}"


def _chat_shared_root() -> str:
    """Liefert den aktuell konfigurierten Shared-Folder (session-Override > cfg)."""
    return (session.get('shared_folder') or SHARED_FOLDER or cfg.exchange_path).rstrip("/")


def _chat_shared_resolve(subpath: str) -> Optional[str]:
    """Sichere Auflösung: Subpfad gegen Shared-Folder-Root, mit ``..``-Schutz.

    Liefert ``None`` wenn Traversal versucht wird.
    """
    root = _chat_shared_root()
    sub = (subpath or "").strip().lstrip("/").replace("\\", "/")
    parts: list = []
    for p in sub.split("/"):
        if p in ("", "."):
            continue
        if p == "..":
            if not parts:
                return None
            parts.pop()
            continue
        if "\x00" in p:
            return None
        parts.append(p)
    return f"{root}/{'/'.join(parts)}" if parts else root


@app.route("/api/chat/shared/folder", methods=["POST"])
def api_chat_set_shared_folder():
    """Freigegebenen Ordner setzen (akzeptiert auch remote Pfade)."""
    data = request.get_json(silent=True) or {}
    folder_path = data.get("folder", "").strip()
    if not folder_path:
        return jsonify({"error": "Ungültiger Ordnerpfad"}), 400
    # Existenz via Client prüfen (funktioniert lokal + ssh)
    if not get_client().is_dir(folder_path):
        return jsonify({"error": f"Ordner '{folder_path}' nicht erreichbar"}), 400
    session['shared_folder'] = folder_path
    return jsonify({"status": "ok", "folder": folder_path})


@app.route("/api/chat/shared/folder/exchange", methods=["POST"])
def api_chat_set_shared_folder_exchange():
    """Setzt den konfigurierten Austausch-Ordner (cfg.exchange_path) als Shared-Folder."""
    target = cfg.exchange_path
    if not get_client().is_dir(target):
        return jsonify({"error": f"Austausch-Ordner '{target}' nicht erreichbar"}), 400
    session['shared_folder'] = target
    return jsonify({"status": "ok", "folder": target})


@app.route("/api/chat/picker/browse", methods=["GET"])
def api_chat_picker_browse():
    """Server-side Folder-Picker: zeigt Ordner unter SHARED_ROOT zur Auswahl.

    Query-Parameter:
        path: absoluter Pfad; muss unter SHARED_ROOT liegen. Default: SHARED_ROOT.
    Liefert nur Verzeichnisse (Files werden weggefiltert), damit der User
    klar einen Ordner zum Freigeben auswählt.
    """
    root_str = str(SHARED_ROOT).rstrip("/")
    requested = (request.args.get("path") or root_str).rstrip("/")
    # Normalisieren, ..-Traversal blocken
    parts = []
    norm = requested.replace("\\", "/")
    for seg in norm.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    abs_path = "/" + "/".join(parts) if parts else "/"
    # Muss unter SHARED_ROOT liegen
    if not (abs_path == root_str or abs_path.startswith(root_str.rstrip("/") + "/")):
        abs_path = root_str

    client = get_client()
    if not client.is_dir(abs_path):
        return jsonify({"error": f"Ordner nicht erreichbar: {abs_path}", "root": root_str}), 404

    # Breadcrumb-Liste (jedes Element ist absoluter Pfad)
    crumbs = []
    if abs_path == root_str:
        crumbs.append({"label": root_str.rsplit("/", 1)[-1] or root_str, "path": root_str})
    else:
        crumbs.append({"label": root_str.rsplit("/", 1)[-1] or root_str, "path": root_str})
        rel = abs_path[len(root_str):].lstrip("/")
        cur = root_str
        for seg in rel.split("/"):
            if not seg:
                continue
            cur = cur + "/" + seg
            crumbs.append({"label": seg, "path": cur})

    entries = []
    for e in client.list_dir(abs_path):
        if e.name.startswith("."):
            continue
        if not e.is_dir:
            continue   # nur Ordner anzeigen
        entries.append({"name": e.name, "path": f"{abs_path.rstrip('/')}/{e.name}"})

    return jsonify({
        "path": abs_path,
        "root": root_str,
        "crumbs": crumbs,
        "entries": entries,
    })


@app.route("/api/chat/shared/folder/upload", methods=["POST"])
def api_chat_set_shared_folder_upload():
    """Empfängt einen kompletten Ordner per Browser-File-Picker (webkitdirectory).

    Files-Liste enthält Files mit ihren relativen Pfaden im Feld ``relpath``
    (z.B. ``myproject/src/main.py``). Wir legen alles unter
    ``<SHARED_UPLOAD_ROOT>/folder_<dirname>_<timestamp>/`` ab und setzen
    diesen lokalen Pfad als Shared-Folder für den Hermes-Agent.

    Achtung: das ist ein einmaliger SNAPSHOT-Upload. Änderungen, die der User
    danach lokal macht, kommen NICHT automatisch nach. Für synchronisierte
    Ordner sollte der User den Austausch-Ordner (Button „🏠") verwenden.
    """
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "Keine Dateien ausgewählt"}), 400

    # Den (vom Browser gelieferten) Top-Ordner aus dem ersten Pfad ableiten
    first_rel = request.form.get("relpaths_0") or files[0].filename or "upload"
    top_dir = first_rel.split("/", 1)[0] if "/" in first_rel else "upload"
    safe_top = secure_filename(top_dir) or "upload"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = Path(SHARED_UPLOAD_ROOT) / f"folder_{safe_top}_{timestamp}"
    target_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    skipped = 0
    for i, f in enumerate(files):
        relpath = (request.form.get(f"relpaths_{i}") or f.filename or "").strip()
        if not relpath:
            skipped += 1
            continue
        # Pfad-Traversal-Schutz: relative Pfade ohne ".." und keine absoluten Pfade
        parts = []
        for seg in relpath.replace("\\", "/").split("/"):
            if seg in ("", ".", ".."):
                continue
            parts.append(secure_filename(seg) or "_")
        if not parts:
            skipped += 1
            continue
        # Top-Dir abtrennen, damit nicht doppelt
        if parts[0] == safe_top:
            parts = parts[1:]
        if not parts:
            skipped += 1
            continue
        dest = target_dir.joinpath(*parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            f.save(str(dest))
            saved += 1
        except Exception:
            skipped += 1

    session['shared_folder'] = str(target_dir)
    return jsonify({
        "status": "ok",
        "folder": str(target_dir),
        "saved": saved,
        "skipped": skipped,
        "top_dir": safe_top,
    })


@app.route("/api/chat/shared/browse", methods=["GET"])
def api_chat_browse_shared():
    """Inhalt eines Unterordners im freigegebenen Folder (lazy-loaded Tree).

    Query-Parameter:
        path: relativer Subpfad (default: Root)
    """
    subpath = request.args.get("path", "")
    target = _chat_shared_resolve(subpath)
    if target is None:
        return jsonify({"error": "Ungültiger Pfad"}), 400
    client = get_client()
    if not client.is_dir(target):
        return jsonify({"entries": [], "folder": target, "subpath": subpath, "exists": False})

    entries = []
    for e in client.list_dir(target):
        if e.name.startswith("."):
            continue
        rel = (subpath.rstrip("/") + "/" + e.name).lstrip("/") if subpath else e.name
        entries.append({
            "name": e.name,
            "path": rel,
            "type": "folder" if e.is_dir else _guess_type(e.name),
            "is_dir": e.is_dir,
            "size": 0 if e.is_dir else e.size,
            "modified": datetime.fromtimestamp(e.modified).strftime("%d.%m.%Y %H:%M") if e.modified else "",
        })
    # Ordner zuerst, dann alphabetisch
    entries.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return jsonify({"entries": entries, "folder": target, "subpath": subpath, "exists": True})


# Editierbare Text-Endungen für den Code-Editor.
_EDITABLE_TEXT_EXTS = {
    ".md", ".txt", ".log", ".yaml", ".yml", ".json", ".py", ".sh", ".bash",
    ".html", ".htm", ".css", ".js", ".mjs", ".ts", ".tsx", ".jsx",
    ".ini", ".cfg", ".conf", ".toml", ".xml", ".csv", ".tsv",
    ".env", ".gitignore", ".dockerignore", ".sql",
}


def _is_editable_path(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    if "." not in name:
        # Dateien ohne Endung wie Dockerfile, Makefile zulassen
        return name in {"dockerfile", "makefile", "readme"}
    ext = "." + name.rsplit(".", 1)[-1]
    return ext in _EDITABLE_TEXT_EXTS


@app.route("/api/chat/shared/read", methods=["GET"])
def api_chat_shared_read():
    """Liest eine Text-Datei aus dem Shared-Folder (für den Code-Editor)."""
    subpath = request.args.get("path", "")
    target = _chat_shared_resolve(subpath)
    if target is None:
        return jsonify({"error": "Ungültiger Pfad"}), 400
    if not _is_editable_path(target):
        return jsonify({"error": "Dateityp nicht editierbar"}), 415
    client = get_client()
    st = client.stat(target)
    if st is None or st.is_dir:
        return jsonify({"error": "Datei nicht gefunden"}), 404
    if st.size > 2 * 1024 * 1024:  # 2 MB Limit (Editor wird sonst träge)
        return jsonify({"error": f"Datei zu groß ({st.size//1024} KB > 2 MB)"}), 413
    content = client.read_text(target)
    if content is None:
        return jsonify({"error": "Datei nicht lesbar (vermutlich binär)"}), 415
    return jsonify({
        "path": subpath,
        "name": target.rsplit("/", 1)[-1],
        "content": content,
        "size": st.size,
        "modified": datetime.fromtimestamp(st.modified).isoformat() if st.modified else "",
    })


@app.route("/api/chat/shared/write", methods=["POST"])
def api_chat_shared_write():
    """Schreibt eine Text-Datei im Shared-Folder zurück."""
    data = request.get_json(silent=True) or {}
    subpath = (data.get("path") or "").strip()
    content = data.get("content", "")
    target = _chat_shared_resolve(subpath)
    if target is None or not subpath:
        return jsonify({"error": "Ungültiger Pfad"}), 400
    if not _is_editable_path(target):
        return jsonify({"error": "Dateityp nicht editierbar"}), 415
    client = get_client()
    if not client.write_text(target, content):
        return jsonify({"error": "Schreiben fehlgeschlagen"}), 500
    return jsonify({"status": "ok", "path": subpath, "bytes": len(content)})


def _guess_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    types = {
        'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'webp': 'image', 'svg': 'image',
        'pdf': 'document', 'doc': 'document', 'docx': 'document', 'txt': 'text',
        'md': 'text', 'csv': 'text', 'json': 'text', 'xml': 'text', 'yaml': 'text', 'yml': 'text',
        'py': 'code', 'js': 'code', 'ts': 'code', 'html': 'code', 'css': 'code', 'sh': 'code',
        'mp4': 'video', 'avi': 'video', 'mkv': 'video',
        'mp3': 'audio', 'wav': 'audio', 'ogg': 'audio',
    }
    return types.get(ext, 'file')


@app.route("/api/chat/upload", methods=["POST"])
def api_chat_upload():
    """Datei-Upload für Chat."""
    if 'file' not in request.files:
        return jsonify({"error": "Keine Datei angegeben"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Keine Datei ausgewählt"}), 400
    
    # Sicheren Filenamen erstellen
    filename = secure_filename(file.filename) if file.filename else 'unnamed'
    if not filename:
        filename = 'unnamed'
    
    # Mit Zeitstempel für Eindeutigkeit
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    upload_filename = f"{timestamp}_{filename}"
    upload_path = os.path.join(SHARED_UPLOAD_ROOT, upload_filename)
    
    file.save(upload_path)
    
    # Berechtigungen setzen
    try:
        os.chmod(upload_path, 0o664)
    except Exception:
        pass
    
    file_url = f"/api/chat/download/{upload_filename}"
    file_type = _guess_type(filename)
    file_size = os.path.getsize(upload_path)
    
    return jsonify({
        "status": "ok",
        "file_name": filename,
        "file_url": file_url,
        "file_type": file_type,
        "file_size": file_size,
        "upload_filename": upload_filename
    })


@app.route("/api/chat/download/<filename>")
def api_chat_download(filename):
    """Herunterladen einer hochgeladenen Datei."""
    return send_from_directory(SHARED_UPLOAD_ROOT, filename)


@app.route("/api/chat/shared/file/<path:filename>")
def api_chat_serve_shared_file(filename):
    """Serve files from the shared folder for chat attachment."""
    folder = session.get('shared_folder') or SHARED_FOLDER
    if not folder or not os.path.isdir(folder):
        abort(404)
    return send_from_directory(folder, filename)


# --------------------------------------------------------------------
# App-Settings (Tab "App" in /settings/)
# --------------------------------------------------------------------

@app.route("/api/settings/app", methods=["GET"])
def api_settings_app_get():
    """Liefert die aktuelle App-Konfiguration (ohne Secrets)."""
    data = public_config_dict()
    data["_meta"] = {
        "has_paramiko": HAS_PARAMIKO,
        "client": get_client().status(),
        "config_keys": sorted(CONFIG_DEFAULTS.keys()),
    }
    return jsonify(data)


@app.route("/api/settings/app", methods=["POST"])
def api_settings_app_post():
    """Aktualisiert die App-Konfiguration. Manche Änderungen erfordern einen Neustart."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON-Objekt erwartet"}), 400

    # Secrets werden nur übernommen, wenn explizit gesetzt (sonst "***" als Placeholder)
    patch = {}
    for key, value in payload.items():
        if key not in CONFIG_DEFAULTS:
            continue
        if key in ("ssh_password",) and value in (None, "", "***"):
            continue  # nicht überschreiben
        patch[key] = value

    cfg.update(patch)
    _refresh_paths()  # WIKI_DIR, BLOG_DIR, SHARED_ROOT, MEMORY_FILES … neu berechnen
    reset_client()    # SSH-Verbindung mit neuen Settings neu aufbauen
    return jsonify({
        "status": "ok",
        "message": "Einstellungen gespeichert. Änderungen sind sofort aktiv.",
        "client": get_client().status(),
    })


def _ssh_key_dir() -> Path:
    """Verzeichnis, in dem das Portal seinen eigenen SSH-Key ablegt."""
    return DATA_DIR / "ssh"


def _default_ssh_key_path() -> Path:
    return _ssh_key_dir() / "id_ed25519"


def _pubkey_fingerprint(pubkey_line: str) -> str:
    """SHA256-Fingerprint im SSH-Standardformat (z.B. 'SHA256:abc…')."""
    try:
        import base64, hashlib
        parts = pubkey_line.strip().split()
        if len(parts) < 2:
            return ""
        raw = base64.b64decode(parts[1])
        digest = hashlib.sha256(raw).digest()
        b64 = base64.b64encode(digest).decode("ascii").rstrip("=")
        return f"SHA256:{b64}"
    except Exception:
        return ""


@app.route("/api/settings/app/ssh/status", methods=["GET"])
def api_settings_app_ssh_status():
    """Liefert Info zum konfigurierten SSH-Key (Pfad, Pubkey, Fingerprint)."""
    configured = cfg.ssh_key_path or ""
    default_path = _default_ssh_key_path()
    # Falls in der Config noch kein Pfad steht, prüfen wir den Default-Pfad mit.
    candidate = Path(configured) if configured else default_path
    pub_path = candidate.with_suffix(candidate.suffix + ".pub") if candidate.suffix else Path(str(candidate) + ".pub")

    info = {
        "key_path": str(candidate),
        "key_exists": candidate.is_file(),
        "pubkey_path": str(pub_path),
        "pubkey": "",
        "fingerprint": "",
        "configured": bool(configured),
        "default_path": str(default_path),
    }
    if pub_path.is_file():
        try:
            info["pubkey"] = pub_path.read_text(encoding="utf-8").strip()
            info["fingerprint"] = _pubkey_fingerprint(info["pubkey"])
        except OSError:
            pass
    return jsonify(info)


@app.route("/api/settings/app/ssh/generate", methods=["POST"])
def api_settings_app_ssh_generate():
    """Erzeugt ein frisches ed25519-Keypair für den Portal→Hermes-SSH-Zugriff.

    Body (JSON, optional):
        overwrite: bool  – existierenden Key überschreiben (Default: False)
        comment:   str   – Kommentar im Pubkey (Default: 'hermes-portal')
    """
    payload = request.get_json(silent=True) or {}
    overwrite = bool(payload.get("overwrite"))
    comment = (payload.get("comment") or f"hermes-portal@{cfg.agent_host or 'local'}").strip()

    key_path = _default_ssh_key_path()
    pub_path = Path(str(key_path) + ".pub")

    if key_path.exists() and not overwrite:
        return jsonify({
            "status": "exists",
            "message": "Key existiert bereits. Setze overwrite=true zum Ersetzen.",
            "key_path": str(key_path),
        }), 409

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        return jsonify({"status": "error", "error": "cryptography ist nicht installiert"}), 500

    try:
        _ssh_key_dir().mkdir(parents=True, exist_ok=True)
        # Restriktive Permissions für das Key-Verzeichnis
        try:
            os.chmod(_ssh_key_dir(), 0o700)
        except OSError:
            pass

        priv = Ed25519PrivateKey.generate()
        priv_bytes = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_bytes = priv.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )

        key_path.write_bytes(priv_bytes)
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            pass

        # Pubkey mit Kommentar speichern (ssh-keygen-kompatibles Format)
        safe_comment = re.sub(r"[^A-Za-z0-9@_\-.]", "_", comment) or "hermes-portal"
        pub_line = pub_bytes.decode("ascii").strip() + " " + safe_comment + "\n"
        pub_path.write_text(pub_line, encoding="utf-8")
        try:
            os.chmod(pub_path, 0o644)
        except OSError:
            pass

        # Pfad in der Config setzen, falls noch leer (sonst respektieren wir den User-Override).
        if not cfg.ssh_key_path:
            cfg.update({"ssh_key_path": str(key_path)})
            reset_client()

        return jsonify({
            "status": "ok",
            "key_path": str(key_path),
            "pubkey_path": str(pub_path),
            "pubkey": pub_line.strip(),
            "fingerprint": _pubkey_fingerprint(pub_line),
            "next_steps": [
                f"Den Pubkey auf dem Hermes-Host nach ~{cfg.ssh_user}/.ssh/authorized_keys kopieren.",
                "Danach in dieser App auf '🔌 Verbindung testen' klicken.",
            ],
        })
    except Exception as ex:
        return jsonify({"status": "error", "error": str(ex)}), 500


@app.route("/api/settings/app/ssh/import", methods=["POST"])
def api_settings_app_ssh_import():
    """Importiert einen vorhandenen Private-Key (PEM/OpenSSH) per Copy-Paste.

    Hintergrund: Wenn ein User bereits einen SSH-Key hat und nur auf ein
    weiteres Gerät umzieht (oder Portal neu installiert), will er nicht
    auf dem Hermes-Host nochmal authorized_keys editieren — er paste
    seinen alten Key ins Portal und es nutzt diesen direkt.

    Body (JSON):
        private_key: str   – Inhalt der Private-Key-Datei (PEM / OpenSSH)
        public_key:  str   – optional, der Public-Key. Wenn fehlt, wird
                             er aus dem Private-Key abgeleitet.
        overwrite:   bool  – existierenden Key überschreiben (Default: False)
        comment:     str   – Kommentar im Pubkey (nur wenn auto-derived)
    """
    payload = request.get_json(silent=True) or {}
    priv_text = (payload.get("private_key") or "").strip()
    pub_text  = (payload.get("public_key") or "").strip()
    overwrite = bool(payload.get("overwrite"))
    comment   = (payload.get("comment") or f"hermes-portal-imported@{cfg.agent_host or 'local'}").strip()

    if not priv_text:
        return jsonify({"status": "error",
                        "error": "private_key fehlt im Payload"}), 400

    # Basic-Sanity: Private-Key muss BEGIN-/END-Marker haben
    if "BEGIN" not in priv_text or "PRIVATE KEY" not in priv_text:
        return jsonify({
            "status": "error",
            "error": "Das sieht nicht nach einem Private-Key aus (BEGIN-/END-Marker fehlen). "
                     "Stelle sicher, dass du den kompletten Inhalt der Key-Datei (inkl. "
                     "'-----BEGIN OPENSSH PRIVATE KEY-----' und '-----END …-----') einfügst.",
        }), 400

    key_path = _default_ssh_key_path()
    pub_path = Path(str(key_path) + ".pub")

    if key_path.exists() and not overwrite:
        return jsonify({
            "status": "exists",
            "message": "Key existiert bereits. Setze overwrite=true zum Ersetzen.",
            "key_path": str(key_path),
        }), 409

    # Wenn kein Pubkey mitgeliefert wurde, versuchen wir ihn aus dem
    # Private-Key abzuleiten (geht für ed25519/RSA über cryptography).
    if not pub_text:
        try:
            from cryptography.hazmat.primitives import serialization as _ser
            try:
                _priv = _ser.load_ssh_private_key(priv_text.encode("utf-8"), password=None)
            except Exception:
                _priv = _ser.load_pem_private_key(priv_text.encode("utf-8"), password=None)
            pub_bytes = _priv.public_key().public_bytes(
                encoding=_ser.Encoding.OpenSSH,
                format=_ser.PublicFormat.OpenSSH,
            )
            safe_comment = re.sub(r"[^A-Za-z0-9@_\-.]", "_", comment) or "hermes-portal-imported"
            pub_text = pub_bytes.decode("ascii").strip() + " " + safe_comment
        except Exception as ex:
            return jsonify({
                "status": "error",
                "error": f"Konnte Public-Key nicht aus Private-Key ableiten: {ex}. "
                         f"Bitte public_key separat mit angeben.",
            }), 400

    try:
        _ssh_key_dir().mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(_ssh_key_dir(), 0o700)
        except OSError:
            pass

        # Private-Key sicherstellen, dass er mit Newline endet
        if not priv_text.endswith("\n"):
            priv_text += "\n"
        key_path.write_text(priv_text, encoding="utf-8")
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            pass

        if not pub_text.endswith("\n"):
            pub_text += "\n"
        pub_path.write_text(pub_text, encoding="utf-8")
        try:
            os.chmod(pub_path, 0o644)
        except OSError:
            pass

        # Pfad in der Config setzen, falls noch leer
        if not cfg.ssh_key_path:
            cfg.update({"ssh_key_path": str(key_path)})
            reset_client()

        return jsonify({
            "status": "ok",
            "key_path": str(key_path),
            "pubkey_path": str(pub_path),
            "pubkey": pub_text.strip(),
            "fingerprint": _pubkey_fingerprint(pub_text),
        })
    except Exception as ex:
        return jsonify({"status": "error", "error": str(ex)}), 500


@app.route("/api/settings/app/ssh/reveal", methods=["POST"])
def api_settings_app_ssh_reveal():
    """Zeigt den lokal gespeicherten Private-Key — für Migration auf andere
    Geräte. Sicherheitscheck: nur wenn der Aufruf von localhost kommt (keine
    Remote-Exfiltration übers Netzwerk).

    Body: ``{ "confirm": true }`` (explizite User-Bestätigung)

    Response: ``{ "status": "ok", "private_key": "..." }`` oder
    ``{ "status": "error", "error": "..." }`` mit 403/404/500.
    """
    body = request.get_json(silent=True) or {}
    if not body.get("confirm"):
        return jsonify({"status": "error", "error": "Confirmation required."}), 400

    # Pfad: konfigurierter oder Default
    configured = cfg.ssh_key_path or ""
    candidate = Path(configured) if configured else _default_ssh_key_path()
    if not candidate.is_file():
        return jsonify({
            "status": "error",
            "error": "No private key found at " + str(candidate),
        }), 404

    try:
        priv_text = candidate.read_text(encoding="utf-8")
    except OSError as ex:
        return jsonify({"status": "error", "error": str(ex)}), 500

    return jsonify({
        "status": "ok",
        "key_path": str(candidate),
        "private_key": priv_text,
    })


@app.route("/api/settings/app/test", methods=["POST"])
def api_settings_app_test():
    """Testet die aktuell konfigurierte Verbindung zum Hermes-Agent."""
    client = get_client()
    status = client.status()
    # Versuche `hermes --version` (falls verfügbar) als zusätzlichen Reachability-Check.
    result = client.hermes(["--version"], timeout=10)
    status["hermes_check"] = {
        "ok": result.ok,
        "stdout": (result.stdout or "").strip()[:200],
        "stderr": (result.stderr or "").strip()[:200],
        "returncode": result.returncode,
    }
    return jsonify(status)


def _is_container_subnet(ip: str) -> bool:
    """Heuristik: Docker/HA-Add-on-typische Bridge-Ranges erkennen.

    HA-Supervisor verwendet 172.30.32.0/22 für Add-on-Container,
    Docker Default Bridge ist 172.17.0.0/16 — beide signalisieren,
    dass wir IM CONTAINER laufen und kein direkter Sichtkontakt zum
    User-LAN besteht. Dann macht ein /24-Scan keinen Sinn.
    """
    try:
        a, b = (int(p) for p in ip.split(".", 2)[:2])
    except ValueError:
        return False
    # Docker bridges: 172.16.0.0/12 (RFC1918 carve-out)
    if a == 172 and 16 <= b <= 31:
        return True
    return False


@app.route("/api/settings/app/discover", methods=["POST"])
def api_settings_app_discover():
    """Scant ein /24-Subnetz nach Hosts, die auf SSH (Port 22) antworten.

    Default-Subnetz: das des Portals selbst. Bei HA-Add-on / Docker
    landet das oft im Container-Bridge-Range (172.x.x.x) und sieht das
    User-LAN nicht — in dem Fall liefern wir eine klare Warnung +
    Container-Hinweis zurück.

    Override: per POST-Body ``{"subnet": "192.168.178.0/24"}`` kann der
    User manuell ein anderes Subnetz angeben.

    Liefert: ``{ ssh_hosts, scanned_subnet, own_ip, in_container, took_ms }``
    """
    import socket
    import time as _time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    started = _time.time()

    def _local_ipv4():
        """Eigene LAN-IP rauskriegen — UDP-Connect-Trick (kein Paket geht raus)."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 53))
            return s.getsockname()[0]
        except OSError:
            return None
        finally:
            s.close()

    own_ip = _local_ipv4() or ""

    # Body lesen — optional manuelles Subnetz vom User
    body = request.get_json(silent=True) or {}
    manual_subnet = str(body.get("subnet") or "").strip()

    # Ziel-Subnetz bestimmen: explizites override > eigene IP
    if manual_subnet:
        # Akzeptiere "192.168.178.0/24" und "192.168.178" gleichwertig
        sn = manual_subnet.rstrip("/")
        if "/" in sn:
            sn = sn.split("/", 1)[0]
        parts = sn.split(".")
        if len(parts) < 3:
            return jsonify({"error": f"Ungültiges Subnetz: {manual_subnet}",
                            "ssh_hosts": []}), 200
        subnet = ".".join(parts[:3])
    else:
        if not own_ip:
            return jsonify({"error": "Konnte eigene LAN-IP nicht bestimmen.",
                            "ssh_hosts": []}), 200
        parts = own_ip.split(".")
        if len(parts) != 4:
            return jsonify({"error": "Unerwartetes IP-Format: " + own_ip,
                            "ssh_hosts": []}), 200
        subnet = ".".join(parts[:3])

    in_container = (not manual_subnet) and _is_container_subnet(own_ip)

    def _check(host):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)
        try:
            if s.connect_ex((host, 22)) == 0:
                hostname = ""
                try:
                    socket.setdefaulttimeout(0.6)
                    hostname = socket.gethostbyaddr(host)[0]
                except (socket.herror, socket.gaierror, OSError):
                    pass
                finally:
                    socket.setdefaulttimeout(None)
                return {"ip": host, "hostname": hostname}
        except OSError:
            pass
        finally:
            s.close()
        return None

    candidates = [f"{subnet}.{i}" for i in range(1, 255) if f"{subnet}.{i}" != own_ip]
    results = []
    with ThreadPoolExecutor(max_workers=50) as ex:
        futs = [ex.submit(_check, h) for h in candidates]
        for fut in as_completed(futs, timeout=15):
            try:
                r = fut.result()
                if r:
                    results.append(r)
            except Exception:
                pass

    results.sort(key=lambda x: tuple(int(p) for p in x["ip"].split(".")))
    took_ms = int((_time.time() - started) * 1000)
    return jsonify({
        "ssh_hosts": results,
        "scanned_subnet": f"{subnet}.0/24",
        "own_ip": own_ip,
        "in_container": in_container,
        "took_ms": took_ms,
    })


# --------------------------------------------------------------------
# Briefing-Seite
# --------------------------------------------------------------------

@app.route("/briefing/")
def briefing_page():
    """Briefing wird wie News/Aufgaben direkt als HTML ausgeliefert —
    Portal-Header oben, dann gleich die Briefing-Überschrift, kein iframe-
    Border, kein zusätzlicher „☕ Briefing"-Wrapper-Title. Eine kleine
    floating Action-Bar (Generate / Reload / Settings) wird unten rechts
    injiziert für User-Aktionen.
    """
    # Per _serve_blog_file holen — das macht URL-Rewrite, Style-Injection,
    # Header-Stripping etc. Komplett konsistent mit News/Aufgaben-Pages.
    response = _serve_blog_file("briefing.html")
    # Wenn _serve_blog_file ein 404-Tuple zurückliefert: durchreichen
    if isinstance(response, tuple) and len(response) >= 2 and response[1] == 404:
        return response

    # FAB + Briefing-Settings-Drawer in das gerenderte HTML einbauen.
    html, status, headers = (response[0], 200, {"Content-Type": "text/html; charset=utf-8"})
    if isinstance(response, tuple):
        html = response[0]
        if len(response) >= 2:
            status = response[1]
        if len(response) >= 3:
            headers = response[2]

    if isinstance(html, str):
        prefix = (request.script_root or "")
        lang = cfg.get("language") or "en"
        fab_html = (
            '<div id="hp-briefing-fab" style="position:fixed;right:1.25rem;bottom:1.25rem;z-index:9999;'
            'display:flex;flex-direction:column;gap:0.5rem;align-items:flex-end;font-family:inherit;">'
            f'<button onclick="hpBriefingRun(this)" title="{_i18n.t("briefing.button.run_now", lang)}" '
            'style="padding:0.55rem 1.1rem;border-radius:24px;border:0;background:#5cc8ff;color:#0f1115;'
            'font-weight:600;cursor:pointer;box-shadow:0 2px 12px rgba(0,0,0,0.4);font-size:0.9rem;">'
            f'▶ {_i18n.t("briefing.button.run_now", lang)}</button>'
            f'<button onclick="location.reload()" title="{_i18n.t("briefing.button.reload", lang)}" '
            'style="padding:0.4rem 0.9rem;border-radius:24px;border:1px solid #2a2e38;'
            'background:#1a1d24;color:#e4e6eb;cursor:pointer;font-size:0.85rem;">'
            f'🔄 {_i18n.t("briefing.button.reload", lang)}</button>'
            '</div>'
            '<script>'
            'function hpBriefingRun(btn){'
              'var orig=btn.innerHTML;btn.disabled=true;btn.innerHTML="⏳…";'
              'fetch((window.HP_INGRESS_PATH||"")+"/api/briefing/run",{method:"POST"})'
              '.then(function(r){return r.json();})'
              '.then(function(d){'
                'btn.innerHTML=orig;btn.disabled=false;'
                'if(d.status==="ok"){setTimeout(function(){location.reload();},800);}'
                'else{alert("'+ _i18n.t("common.error", lang) +': "+(d.error||d.stderr||"unknown"));}'
              '}).catch(function(e){btn.innerHTML=orig;btn.disabled=false;alert(e);});'
            '}'
            '</script>'
        )
        if "</body>" in html:
            html = html.replace("</body>", fab_html + "</body>", 1)
        else:
            html = html + fab_html

    return html, status, headers


@app.route("/api/briefing/info")
def api_briefing_info():
    """Metadaten zum Briefing: Existiert es, wann zuletzt aktualisiert."""
    client = get_client()
    output_path = cfg.briefing_output_path()
    script_path = cfg.briefing_script_path()

    info = {
        "output_path": output_path,
        "script_path": script_path,
        "exists": client.exists(output_path),
        "script_exists": client.exists(script_path),
        "last_modified": None,
        "last_modified_human": "—",
        "client_mode": client.mode,
    }
    if info["exists"]:
        # Einheitlich via client.mtime (lokal: stat, ssh: SFTP-stat). Konvertierung
        # in VM-naive Wall-Clock, damit "vor X" gegen vm_now() stimmt.
        ts = client.mtime(output_path)
        if ts:
            mtime = vm_dt_from_unix(ts)
            info["last_modified"] = mtime.isoformat()
            info["last_modified_human"] = _format_relative(mtime)
    return jsonify(info)


@app.route("/api/briefing/render")
def api_briefing_render():
    """Liefert das gerenderte Briefing-HTML zurück (für iframe).

    Wendet die gleiche URL-Rewrite-Logik wie ``_serve_blog_file`` an, sonst
    versuchen die im Agent-HTML hardcodierten ``/blog/style.css``- und
    ``/blog/site-header.js``-Pfade gegen die HA-Origin zu laden und scheitern.

    Plus: injiziert unser Portal-Stylesheet + ein bisschen Scrollbar-Hide-
    CSS, damit das iframe nicht doppelt-scrollt.
    """
    client = get_client()
    html_text = client.read_text(cfg.briefing_output_path())
    if not html_text:
        # Minimaler Platzhalter, der im iframe ein klares Signal gibt.
        html_text = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<style>body{font-family:system-ui,-apple-system,sans-serif;color:#aaa;"
            "background:#1a1a1a;padding:40px;text-align:center;}</style></head><body>"
            "<h2>📭 " + _i18n.t("briefing.no_briefing", cfg.get("language") or "en") + "</h2>"
            "</body></html>"
        )

    prefix = (request.script_root or "")

    # ──────────────────────────────────────────────────────────────────
    # Im Briefing-iframe brauchen wir KEINE zweite Nav (Portal-Header
    # läuft schon außen rum). Stripping in dieser Reihenfolge:
    # ──────────────────────────────────────────────────────────────────
    # 1) <div id="site-header"></div> Placeholder rausschmeißen
    html_text = re.sub(
        r'<div[^>]*\bid=["\']site-header["\'][^>]*>.*?</div>',
        '', html_text, flags=re.DOTALL | re.IGNORECASE,
    )
    # 2) Alle <script>-Tags die site-header.js laden entfernen
    html_text = re.sub(
        r'<script[^>]*\bsrc=["\'][^"\']*site-header\.js[^"\']*["\'][^>]*>\s*</script>',
        '', html_text, flags=re.IGNORECASE,
    )
    # 3) Komplette <header>-Elemente, die der Agent ggf. eingebaut hat
    html_text = re.sub(
        r'<header[^>]*>.*?</header>',
        '', html_text, flags=re.DOTALL | re.IGNORECASE,
    )

    # Portal-Stylesheet + Scrollbar-Hide-CSS + Top-Padding-Reset einbinden
    style_href = (prefix or "") + "/static/portal/style.css?v=" + _ASSET_VERSION
    head_inject = (
        f'<link rel="stylesheet" href="{style_href}">'
        '<style>'
        # iframe-internes Scrollen unterdrücken
        'html,body{margin:0;padding:1.5rem;overflow-x:hidden;}'
        'html::-webkit-scrollbar,body::-webkit-scrollbar{width:6px;height:6px;}'
        'html::-webkit-scrollbar-thumb,body::-webkit-scrollbar-thumb{background:#444;border-radius:3px;}'
        # Erste Überschrift soll direkt am Top sitzen (kein Header-Spacer)
        'body > *:first-child{margin-top:0;}'
        '</style>'
    )
    if "</head>" in html_text:
        html_text = html_text.replace("</head>", head_inject + "</head>", 1)
    else:
        html_text = head_inject + html_text

    # ALLE absoluten /-URLs in href/src um den Ingress-Prefix ergänzen
    # (gleiche Logik wie in _serve_blog_file). Greift sowohl auf
    # hardcodierte /blog/style.css als auch auf andere Pfade.
    if prefix:
        def _prefix_url(match):
            attr, quote, url = match.group(1), match.group(2), match.group(3)
            if (url.startswith(prefix)
                    or url.startswith('//')
                    or url.startswith('http')):
                return match.group(0)
            return f'{attr}={quote}{prefix}{url}{quote}'
        html_text = re.sub(
            r'(href|src)=(["\'])(/[^"\']*)\2',
            _prefix_url,
            html_text,
        )

    return html_text, 200, {"Content-Type": "text/html; charset=utf-8",
                            "Cache-Control": "no-store"}


@app.route("/api/briefing/run", methods=["POST"])
def api_briefing_run():
    """Triggert das Briefing-Script (synchron, mit Timeout)."""
    client = get_client()
    script_path = cfg.briefing_script_path()

    if not client.exists(script_path):
        return jsonify({
            "status": "error",
            "error": f"Briefing-Script nicht gefunden unter {script_path}. "
                     "Pfad in Settings → App prüfen."
        }), 404

    # Briefing-spezifische ENV + den TZ aus der Config. TELEGRAM_*, HASS_*
    # werden NICHT hier gesetzt — die liegen im Environment des Hermes-Hosts.
    env_extra = cfg.briefing_env()

    # Aufruf via python3 — explizit, damit es auf beiden Backends gleich aussieht.
    result = client.run(
        ["python3", script_path],
        timeout=180,
        env=env_extra if client.mode == "ssh" else {**os.environ, **env_extra},
    )

    return jsonify({
        "status": "ok" if result.ok else "error",
        "returncode": result.returncode,
        "stdout": (result.stdout or "")[-2000:],
        "stderr": (result.stderr or "")[-2000:],
    })


_BRIEFING_KEYS = (
    "briefing_script", "briefing_output",
    "briefing_github_user",
    "briefing_weather_lat", "briefing_weather_lon", "briefing_weather_tz",
    "briefing_forum_rss", "briefing_bvg_stop",
)


@app.route("/api/briefing/config", methods=["GET"])
def api_briefing_config_get():
    """Liefert nur die Briefing-relevanten Settings (Subset von /api/settings/app)."""
    data = {k: cfg.get(k, "") for k in _BRIEFING_KEYS}
    return jsonify(data)


@app.route("/api/briefing/config", methods=["POST"])
def api_briefing_config_post():
    """Speichert die Briefing-Settings (Subset)."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON-Objekt erwartet"}), 400
    patch = {k: v for k, v in payload.items() if k in _BRIEFING_KEYS}
    cfg.update(patch)
    return jsonify({"status": "ok", "saved": list(patch.keys())})


# --------------------------------------------------------------------

if __name__ == '__main__':
    print(f"🚀 Hermes Portal startet auf http://{cfg.bind_host}:{cfg.bind_port}")
    print(f"   Agent-Mode: {get_client().mode}  Host: {cfg.agent_host}  Exchange: {cfg.exchange_path}")
    app.run(host=cfg.bind_host, port=cfg.bind_port, debug=False, threaded=True)