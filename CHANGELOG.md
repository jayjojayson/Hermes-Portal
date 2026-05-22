# Changelog

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) ·
Versionsschema: [SemVer](https://semver.org/lang/de/).

---

## [Unreleased]

### Added
- _(noch nichts)_

---

## [0.5.0] — 2026-05-22

Erstes öffentliches Release. Das Hermes Portal ist als komplettes Web-Frontend
für den [Hermes-Agent](https://github.com/jayjojayson/Hermes-Portal) lauffähig
— lokal in der Hermes-VM, als Docker-Container oder als Home-Assistant-Add-on.

### Added

#### Architektur
- **`hermes_client.py`** — Abstraktionsschicht über `local`- und `ssh`-Backend
  (paramiko, thread-safe per RLock). Sämtliche FS-Operationen und
  CLI-Aufrufe gehen durch denselben Client.
- **`config.py`** — zentrale Konfiguration via `data/config.json` mit
  Override per Environment-Variablen (`HP_*`).
- **Dynamic Path-Refresh** — `exchange_path` / `hermes_home` /
  `wiki_subpath` können live in der UI geändert werden, kein App-Restart.
- **Versionierung** — `_wiki_server/__version__.py` als Single Source of
  Truth, Anzeige im Sidebar-Footer als klickbarer Release-Link.

#### Seiten & Features
- **🏠 Dashboard** — Agent-Status (live-dot pollt alle 30 s), System-Stats
  (CPU/RAM/Disk vom Hermes-Host), nächste Cronjobs (mit „überfällig"-Anzeige
  bei TZ-aware Zeitberechnung), Aufgaben-Übersicht, Briefing-Snippet,
  News-Schlagzeilen, Token-Verbrauch (Mini-Chart), letzte 5 Wiki-Beiträge mit
  Deep-Link.
- **📚 Wiki** — Markdown-Editor mit Toolbar (H1–H4, Bold, Italic, Code, Liste,
  Numerierte Liste, Link), Wikilink-Resolver, Tags, Volltext-Suche,
  Import/Export (`.md`-Upload + ZIP-Download), konfigurierbare
  Kategorie-Labels.
- **📰 News** — RSS-Aggregator über konfigurierbare Feeds, statisches
  Blog-HTML wird serverseitig mit Portal-Branding angereichert (Logo,
  Footer, brand-aware `<title>`).
- **☕ Briefing** — eigene Seite mit iframe-Vorschau, „Jetzt erzeugen"-Button,
  ausklappbare Settings (GitHub-User, Wetter-Koordinaten, BVG-Stop, RSS,
  Pfade).
- **✅ Aufgaben** — Read/Write der `aufgaben.md`, Bearbeiter-Dropdown nutzt
  die konfigurierten Namen (statt hardcoded Wally/Jan).
- **📂 Explorer** — Datei-Browser mit textuell-sicherer Pfad-Auflösung
  (Traversal-Schutz), Upload, Mkdir, Delete, Download (mit SSH-Stream).
- **💬 Chat** — Sessions-Sidebar (links, einklappbar), Chat-Bereich (mittig),
  Code-Editor-Spalte (Monaco, öffnet bei Klick auf Datei), File-Tree-Spalte
  (rechts, einklappbar). Splitter zwischen Chat und Editor verwendet
  Flex-Ratios (kein Layout-Bruch bei File-Tree-Toggle).
- **💬 Chat-Toolbar** — 🎤 Spracheingabe (Web Speech API, deutsch),
  📎 Datei-Anhang, 📁 Server-side Folder-Picker (mit SMB/Mount-Anleitung im
  Modal), 📂 Quick-Button für konfigurierten Austausch-Ordner, Send/Stop-
  Toggle (`/stop` an Hermes + AbortController).
- **⚡ Aktivität** — Live-Tail des Hermes-Logs, mtime-basierte Versionierung
  für Polling.
- **⚙️ Settings** — sechs Tabs:
  - **⏰ Cronjobs** — Liste + Create/Edit/Pause/Run/Delete via `hermes cron`
  - **🧠 Personality & Memory** — SOUL.md / USER.md / MEMORY.md / config.yaml,
    plus Verweis auf Identitäts-Settings im App-Tab
  - **🛠️ Skills** — Flache Liste aller Skills (Hermes + Built-in + Custom)
  - **📚 References** — alle Skill-References + Hermes-Scripts editierbar
  - **📊 Usage** — KPI-Karten, SVG-Linien-Diagramm Token-Verlauf
    (Total/Input/Output), Mini-Bars für Requests, Tageswechsel
    (Prev/Next/Date-Picker)
  - **🛰️ App** — Identität (Agent/User/Kategorie-Labels), Verbindung
    (local/ssh, SSH-Wizard mit Key-Generation + Hermes-Setup-Prompt),
    Pfade, RSS-Feeds, sticky Save-Bar
  - **❤️ Support** — PayPal, Ko-fi, GitHub-Project/Discussions/Issues
- **🎨 Branding** — eigenes Hermes-Caduceus-Logo (`hermes-portal-logo.png`)
  überall (Header, Tab-Buttons, Section-Titles, Footer, Favicon), dynamisch
  via `window.HP_BRAND` + Portal-Name.

#### Distribution
- **Dockerfile** (multi-stage, multi-arch via Buildx) + `docker-compose.yml`.
- **Home-Assistant Add-on** — `homeassistant/hermes_portal/` mit `config.yaml`,
  `Dockerfile`, `build.yaml`, `prepare.sh`, eigenem README.
- **GitHub Release-Workflow** (`.github/workflows/release.yml`) — bei Tag
  `v*.*.*`: parallel PyInstaller-Builds auf Mac/Linux/Windows, Multi-Arch
  Docker-Push nach GHCR, GitHub-Release mit allen Artefakten + Notes.
- **CI-Workflow** (`.github/workflows/ci.yml`) — auf jedem PR:
  Bytecode-Compile, Route-Smoke (≥70 Routen erwartet), Docker-Build.
- **`scripts/fetch_monaco.py`** — lädt Monaco-Editor (~14 MB) einmalig nach
  `static/vendor/monaco/` für Offline-Nutzung im Chat-Editor.
- **`entry_pyinstaller.py`** + `hermes_portal.spec` — Standalone-Bundle mit
  Waitress-WSGI-Server + automatischem Browser-Launch.
- **`docs/systemd.service`** — Beispiel-Unit-File für Linux-Deployment.
- **`pyproject.toml`** — saubere Projekt-Metadaten.

### Security
- **Pfad-Traversal-Schutz** im Explorer (textuelle Normalisierung statt
  `Path.resolve()`, blockiert `..` und `\x00`).
- **paramiko-Lock** — alle SFTP/Exec-Operationen serialisiert, da Flasks
  Multi-Threading sonst SFTP-Deadlocks verursacht hat.
- **TZ-aware Zeitberechnung** — `client.time_offset_seconds()` ermittelt
  einmal pro Minute die VM-Uhrzeit und korrigiert Vergleiche mit naiven
  Timestamps aus `jobs.json` / Logs.
- **Connection-Cleanup** — `reset_client()` schließt alte SSH-Verbindungen
  sauber bei jedem Settings-Save.

### Fixed
- **Header-Live-Dot** spiegelt jetzt den realen Hermes-Status statt immer
  grün zu pulsieren (Online/Idle/Offline/Unknown).
- **Cache-Busting** — `?v=<hash>`-Suffix für `style.css` und
  `site-header.js`, automatisch bei jeder Asset-Änderung.
- **Blog-Pages** ziehen das Portal-CSS via Style-Injection nach, damit Logo,
  Footer und Live-Dot konsistent aussehen.
- **Briefing-Page** wird via iframe + `/api/briefing/render` ausgeliefert →
  funktioniert auch im SSH-Mode mit Remote-Pfaden.

---

[Unreleased]: https://github.com/jayjojayson/Hermes-Portal/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/jayjojayson/Hermes-Portal/releases/tag/v0.5.0
