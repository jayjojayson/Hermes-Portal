# Changelog

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) ·
Versionsschema: [SemVer](https://semver.org/lang/de/).

---

## [Unreleased]

### Added
- _(noch nichts)_

---

## [1.0.10] — 2026-05-24

Vier konkrete HA-Fixes (Briefing-Style, Chat-Editor, i18n-Vermischung,
Zeitzonen) plus weitere Template-Übersetzungen.

### Fixed
- **Briefing-iframe in HA**: vom Agent gelieferte HTML hatte hardcoded
  `/blog/style.css` und `/blog/site-header.js` — die liefen ohne
  Ingress-Prefix gegen die HA-Origin → 404. `api_briefing_render` rewritet
  jetzt alle absoluten `/`-URLs und injiziert zusätzlich unser Portal-
  Stylesheet, damit Cards/Farben konsistent zur restlichen UI aussehen.
  Plus: iframe-Höhe auf `calc(100vh - 220px)`, interner Scrollbar fast
  immer weg.
- **Chat-Editor leer, `loader.js 404`**: Monaco-Loader-Script-Tag in
  `chat.html` nutzte hardcoded `/static/...`-Pfad. Der DOM-Patcher
  in `base.html` rewritet zwar dynamisch, aber bei `<script>`-Tags zu
  spät — der Browser hat den 404 schon gefeuert. Fix: `{{ url_for() }}`
  server-side, sodass der Pfad SCHON beim Render korrekt ist.
- **Sprache-Mix nach Sprachwechsel**: nach Save in Settings → 🌐 Sprache
  reloadet die Seite jetzt **automatisch** (`location.reload()`), damit
  das neue i18n-Bundle sofort überall greift. Vorher musste man manuell
  die Seite wechseln, und manche i18n'd-Templates zeigten noch die alte
  Sprache → wirkte wie wilder Mix.
- **Settings-Cronjobs zeigten UTC als lokal**: der alte Code stripte
  `+00:00` aus dem ISO-Timestamp und behandelte den Rest als lokal —
  ergo wurde `16:00 UTC` als „16:00 lokal" angezeigt statt korrekt
  „18:00" (UTC+2). Fix: neuer Helper `window.formatLocalTime()`, der
  fehlende TZ als UTC annimmt (Hermes-Konvention) und sauber in die
  Browser-TZ konvertiert.

### Added
- **🕐 Zeitzonen-Helper in `base.html`**:
  - `window.formatLocalTime(iso)` — UTC-ISO → User-Browser-Lokal-String
    in der aktiven UI-Sprache
  - `window.userTimezone()` — z.B. `"Europe/Berlin"`
  - `window.userTzOffset()` — z.B. `"UTC+02:00"`
- **TZ-Hinweis in Settings → Cronjobs-Toolbar**: zeigt dezent die
  Browser-Zeitzone (z.B. „🕐 UTC+02:00 · Europe/Berlin") mit Tooltip,
  der erklärt: Cron-Pattern werden vom Agent in dessen Zeitzone (UTC)
  interpretiert, die Spalten „Nächster/Letzter Lauf" in deiner Browser-TZ.
- **Dashboard-Cronjob-Tile**: Tooltip auf der Time-Pill zeigt jetzt die
  absolute Lokal-Zeit zusätzlich zur relativen („in 2h 15min").

### Changed
- **Mehr Templates auf `t()` umgestellt**:
  - **Chat** (`chat.html`): Session-Liste, Suche, Empty-State-Greeting,
    Eingabefeld-Placeholder, alle Toolbar-Buttons (🎤/📎/📁/📂),
    Send-Button-Labels.
  - **Briefing** (`briefing.html`): Header, „Jetzt erzeugen"/„Neu laden"-
    Buttons, Config-Block-Titel, GitHub/Wetter/Zeitzone-Felder.
  - **Wiki-Index** (`index.html`): Wiki-Such-Box, Import/Export-Karte.

### Notes
- **Empfehlung zur Zeitzonen-Lösung**: Browser-TZ ist 95%-Lösung ohne
  jede Konfiguration. Falls jemand den Portal-Container in einer
  anderen TZ läuft als sein Browser (selten, z.B. HA-Hostzeit von
  Smartphone aus aufrufen), könnte man später einen TZ-Override in
  Settings hinzufügen. Aktuell: nicht nötig, der Browser kennt seine
  TZ zuverlässig.

---

## [1.0.9] — 2026-05-23

i18n-Vollausbau-Release. Übersetzungs-Tables auf ~150 Keys pro Sprache
ausgebaut (× 4 Sprachen = ~600 Übersetzungen), Dashboard + Settings +
Blog-Missing-Page komplett auf `t()`-Helper umgestellt.

### Added
- **Komplette Übersetzungen** für alle 4 Sprachen (en/de/es/fr) inkl.:
  - **Dashboard**: Greetings (Tageszeit-abhängig), Hermes-Card,
    System-Card (CPU/RAM/Disk/Logfile), Quick-Prompt, Cronjobs-Box,
    Token-Usage, News, Wiki-Recent, Activity-Preview.
  - **Settings → 🛰️ App**: alle Sektionen (Sprache, Visibility, Identity,
    Connection, Paths), alle Field-Labels, alle Hilfe-Texte (Folder-
    Struktur-Erklärung, Briefing-Template-Tipp, RSS-Verhalten).
  - **Settings-Tabs**: Cronjobs, Personality & Memory, Skills,
    References, Usage, App, Support.
  - **Blog-Missing-Page**: vollständig übersetzt (Title, Body, Causes,
    Hide-Hint).
  - **Common-Strings**: Save/Cancel/Delete/Edit/New/Reload/Search/…
    plus „Loading…", „No data", „Never", „Today" etc.
- **Greeting-Logik** in `dashboard.html` nutzt jetzt `window.t()` mit
  Fallback auf Tageszeit-spezifische Schlüssel
  (`greeting.morning/afternoon/evening/night`).

### Changed
- **JSON-Tables** in `_wiki_server/i18n/{en,de,es,fr}.json` von ~30 auf
  ~150 Keys aufgestockt. Jeder neue Key, der noch nicht in einer Sprache
  übersetzt ist, fällt automatisch auf den Englisch-Wert zurück (und
  dann auf den Key-Namen). So bleibt das UI nutzbar während Community-
  Übersetzungen nachgereicht werden.

### Notes
- **Templates noch nicht komplett umgestellt**: index.html (Wiki),
  chat.html (innere UI), briefing.html (Settings-Block), activity.html,
  explorer.html — die nutzen weiterhin teilweise hardcodierte deutsche
  Strings. Die JSON-Keys sind aber bereits da → Community-PRs zum
  Umstellen sind willkommen, kein Code-Change nötig, nur
  `<text>` → `{{ t('xyz') }}`.
- **Sprache wechseln**: Settings → 🛰️ App → 🌐 Sprache. Nach Save
  reloadet die Seite automatisch und die neue Sprache greift.

---

## [1.0.8] — 2026-05-23

Zwei HA-Bug-Fixes (Briefing-iframe, Chat-Editor) + grosser Schritt
Richtung Mehrsprachigkeit. Macht das Portal für nicht-deutsche User
endlich nutzbar.

### Added
- **🌐 Mehrsprachiges UI** — Sprache wählbar in Settings → 🛰️ App →
  „Sprache · Language · Idioma · Langue".
  - **Englisch (Default), Deutsch, Spanisch, Französisch** — Neuinstalls
    starten jetzt auf Englisch (weil das die meisten User verstehen),
    bestehende User behalten ihre bisherige Sprache.
  - Übersetzungen liegen als flache JSON-Tables in `_wiki_server/i18n/`
    — Community-Beiträge per PR willkommen (neue Sprache = neue
    `<code>.json` reinlegen, taucht automatisch im Switcher auf).
  - Aktuell sind übersetzt: Nav-Labels, Settings-Tab-Titel, Standard-
    Buttons (Save/Cancel/…). Restliche Strings folgen Stück für Stück.
  - JS-Side via `window.t('nav.dashboard')` Helper + `window.HP_I18N`
    Lookup-Tabelle in `base.html`.
- **`_wiki_server/i18n.py`** — leichtgewichtiges Übersetzungs-Modul
  (kein Babel/gettext-Overhead), Fallback-Reihenfolge:
  `lang → en → key`.
- **`_wiki_server/templates/briefing_default.html`** — Beispiel-Vorlage
  für eigene Briefing-HTML. User können das als Startpunkt zu sich auf
  den Agent kopieren und ihr `daily_briefing.py` darauf aufsetzen.
- **Hilfe-Box „Empfohlene Ordner-Struktur"** in Settings → 🛰️ App →
  Pfade-Section. Erklärt die `<austausch>/wiki/{scripts,blog}/`-Struktur,
  verweist auf `briefing_default.html`, klärt RSS-Feed-Verhalten
  (Portal-Feed ≠ News-Generator-Feed des Agents).

### Fixed
- **Briefing-Seite zeigte 404** in HA — `<iframe src="/api/briefing/render">`
  war hardcodiert, der v1.0.6-Patcher hatte `<iframe>` nicht in seiner
  Selector-Liste. Jetzt nutzt das Template `url_for(...)`, plus der
  Patcher kennt `iframe`/`source` als zusätzliche Selektoren.
- **Chat-Editor blieb leer** mit `TypeError: Cannot read properties of
  null (reading 'then')` — Monaco-AMD-Loader hatte hardcodierten Pfad
  `paths: { vs: '/static/vendor/monaco/vs' }`, lud also unter Ingress
  alle Module gegen die HA-Origin → 404 → `monaco.editor` undefined →
  `MONACO_READY` blieb `null`. Jetzt: `paths: { vs: window.hpUrl(...) }`.

### Notes
- **macOS-DMG**: aus dem Test-Loop ausgenommen — wir bauen für v1.1.0
  ohnehin komplett auf native pywebview-Window-Architektur um, der
  Browser-+-Terminal-Hybrid-Build aus v1.0.x wird obsolet.
- **RSS-Feeds in Settings ≠ News-Generator-Feeds**: das hat die
  Hilfe-Box jetzt explizit dokumentiert. Portal speichert die Feed-
  Liste in `config.json`, gibt aber nur den `briefing_forum_rss` als
  ENV an dein Briefing-Script weiter. Für die News-Generierung musst
  du weiterhin deinen agent-seitigen `daily_news.py` manuell pflegen.

---

## [1.0.7] — 2026-05-23

Echte native Desktop-App-Experience auf macOS und Windows — kein Browser-
Tab mehr, kein Terminal-Fenster. Plus PyInstaller-Bootloader-Fix für
macOS-Finder-Launch.

### Changed
- **`console=False` für macOS-Build** in `hermes_portal.spec`. Der
  PyInstaller-Bootloader stürzte beim Finder-Doppelklick in den
  v1.0.3–v1.0.6-Builds lautlos ab — wahrscheinliche Ursache:
  `console=True` erwartet ein Controlling-Terminal, das eine via Finder
  gestartete .app aber nicht hat. **Damit sollte der mac-Crash endlich
  weg sein.**
- **`entry_pyinstaller.py` startet jetzt ein natives Fenster via
  `pywebview`** statt den Default-Browser zu öffnen. Auf macOS nutzt
  pywebview WKWebView (= Safari-Engine), auf Windows den eingebauten
  Edge-WebView2 — beides ist Teil des Betriebssystems, **kein
  zusätzlicher Install für den End-User**.
- **Server läuft im Background-Thread** statt blockierend; das native
  Fenster zeigt erst nach erfolgreichem Port-Connect die UI, damit
  keine weiße „Server-noch-nicht-bereit"-Seite mehr aufblitzt.

### Added
- **Browser-Fallback** wenn pywebview im Bundle fehlt (Linux-AppImage
  startet weiter im Browser — GTK-/QT-WebKit-Libs sind in AppImage
  nicht zuverlässig bündelbar, kommt vielleicht in v1.1.x via
  Tauri-Refactor).

### Notes
- **macOS**: keine Terminal-Fenster mehr, keine Browser-Tabs.
  Doppelklick → Fenster mit Hermes Portal öffnet sich direkt.
- **Windows**: WebView2-Runtime ist auf Windows 10/11 vorinstalliert,
  sollte ohne Extra-Setup laufen. Falls nicht: Setup-Wizard installiert
  WebView2 automatisch nach.
- **Linux**: AppImage öffnet weiterhin im Default-Browser. Pure-Native
  via Tauri ist Kandidat für v1.1.0.

---

## [1.0.6] — 2026-05-23

Drei wichtige Bug-Fixes für den HA-Add-on-Modus. Native-Window-Refactor
(pywebview) wandert in v1.1.0.

### Fixed
- **Wiki-Posts gaben 404 in HA** — Wiki-Index zeigte Einträge an, aber
  jeder Klick auf einen Beitrag landete auf „404 Not Found". Ursache:
  Templates wie `index.html` benutzen hardcodierte `href="/entity/…"`
  ohne `url_for()` → kein Ingress-Prefix → HA-Route findet die URL nicht.
  Fix: globaler JS-Patcher in `base.html` rewritet jetzt alle
  `<a href="/…">`, `<img src="/…">`, `<link href="/…">` und
  `<script src="/…">` auf DOM-Ready + via `MutationObserver` auch
  dynamisch nachgeladene Inhalte. Statt 100+ Templates anzufassen.
- **Pfade in Settings → 🛰️ App resetten nach Reload** — gespeicherte
  Werte wurden bei jedem Page-Load von `HP_*`-Env-Variablen (HA-Add-on-
  Options) überschrieben, weil `_apply_env` immer lief. Jetzt: Env-Vars
  sind nur noch **Initial-Seed beim allerersten Container-Start**,
  spätere UI-Änderungen sind sticky. **Migration**: wenn die alte
  config.json schon falsche Pfade enthält, einmal in der UI auf
  korrekte Werte setzen + speichern.
- **Aufgaben / News / Briefing-Layout immer noch karg** — vom Hermes-Agent
  gelieferte Blog-HTMLs hatten in v1.0.5 zwar korrekte Ingress-URLs, aber
  unser `portal/style.css` war nicht eingebunden. `_serve_blog_file`
  injiziert das CSS jetzt mit Cache-Buster, damit Cards, Buttons, Farben
  konsistent aussehen.

### Notes
- **Logo auf App-Tab + Personality-Verweis**: war derselbe Ingress-Bug
  (`<img src="/static/portal/logo.png">` ohne Prefix). Wird durch den
  erweiterten `img[src^="/"]`-Rewriter oben automatisch gefixt — kein
  Template-Touch nötig.
- **macOS-DMG „App startet nicht / nichts passiert"**: zur Diagnose
  bitte nach Start einmal in `~/Desktop/hermes-portal-started.txt`
  schauen — wenn die Datei da ist, ist Python gestartet (Crash danach);
  wenn nicht, killt sich der PyInstaller-Bootloader. Echte Lösung
  (native Fenster statt Browser, kein Terminal) folgt in **v1.1.0**.

---

## [1.0.5] — 2026-05-23

HA-Blog-Layout-Fix + UI-Polish + tiefere macOS-Crash-Diagnostik +
PyInstaller-Codesign-Integration.

### Fixed
- **Aufgaben / News / Briefing-Seiten in HA hatten kein Layout** — gleiches
  Muster wie der ursprüngliche Ingress-Header-Bug, nur an einer anderen
  Stelle: `_serve_blog_file` reicht vom Hermes-Agent generierte HTML-Files
  durch, die wiederum hardcodierte `/static/...`- und `/blog/...`-URLs
  enthalten. Diese URLs werden jetzt am Ende der HTML-Verarbeitung per
  regex um den Ingress-Prefix ergänzt. Zusätzlich landet `window.HP_INGRESS_PATH`
  + ein Mini-`fetch`-Patcher in jedem Blog-HTML.

### Changed
- **Toggle-Button-Text** in Settings → 🛰️ App → „📑 Menü-Punkte sichtbar"
  gekürzt: „📰 News anzeigen" statt „📰 News im Menü anzeigen", Grid auf
  `minmax(160px, 1fr)` → alle 4 Buttons passen jetzt nebeneinander
  (auf Handy fallen sie automatisch in 2× 2-Layout).
- **PyInstaller-Codesign integriert** — Spec-File setzt jetzt
  `codesign_identity='-'` auf macOS, damit PyInstaller jeden Mach-O
  während des Builds selbst ad-hoc signiert (in korrekter Reihenfolge,
  inner-most-first). Unser `sign_macos_app.py`-Script läuft danach als
  Safety-Net.

### Added
- **Startup-Marker für mac-Crash-Diagnose** — `entry_pyinstaller.py`
  schreibt jetzt als ALLER-erstes (vor jedem komplexen Import) eine Datei
  `~/Desktop/hermes-portal-started.txt` mit PID, Python-Version,
  CWD, HOME, `_MEIPASS` etc. Damit lässt sich diagnostizieren:
  - **Datei existiert + App startet trotzdem nicht** → Crash NACH
    Python-Start, schau in `~/Desktop/Hermes-Portal-Crash.log`
  - **Datei existiert nicht** → Crash IM PyInstaller-Bootloader (vor
    Python). Schau in `~/Library/Logs/DiagnosticReports/` nach einem
    macOS-Kernel-Crash-Report mit „hermes-portal".

---

## [1.0.4] — 2026-05-23

Diagnostik- und Robustness-Release. macOS-Crash bleibt schwer zu
reproduzieren — daher mehr Logging, das _definitiv_ irgendwo landet.
Außerdem SSH-Banner-Timeout für HA-Container-Setups erhöht und das
Nav-Toggle-Set vervollständigt.

### Added
- **Nav-Toggles vervollständigt** — Settings → 🛰️ App → „📑 Menü-Punkte
  sichtbar" bietet jetzt **alle** vier optionalen Hauptpunkte:
  📚 Wiki, 📰 News, ☕ Briefing, ✅ Aufgaben. Volle Kontrolle für User,
  die nur Teilfunktionen nutzen (z.B. nur Chat + Dashboard).
  - Neue Config-Keys `show_wiki` und `show_aufgaben` (Defaults `true`).
  - Filter greift wie gehabt über `window.HP_NAV_HIDE` in `base.html`
    und `navItems()` in `site-header.js` — Header **und** Sidebar
    blenden den Eintrag synchron aus.

### Changed
- **SSH-Banner-Timeout** in `hermes_client.py` von 15 s (paramiko-Default)
  auf 30 s, plus `auth_timeout=15`. Plus **Single-Retry** bei
  `banner`/`transport`/`eof`-Fehlern (Container-Netzwerke wie HA-Add-on
  zeigen sporadisch flaky Banner-Exchanges beim ersten Verbinden).
  Auth-Fehler fliegen weiterhin sofort durch.
- **Crash-Log-Fallback-Chain** in `entry_pyinstaller.py`:
  1. `~/Desktop/Hermes-Portal-Crash.log` (sichtbar!)
  2. `~/Library/Application Support/Hermes Portal/crash.log`
  3. `$TMPDIR/hermes-portal-crash.log`
  4. `$CWD/hermes-portal-crash.log`
  Egal wo es klemmt — irgendwo wird der Traceback landen.
- **Crash-Output zusätzlich auf `stderr`** mit `flush=True` und klarer
  Marker-Zeile (`=== HERMES PORTAL CRASH ===`). Wer die App aus dem
  Terminal startet, sieht den Fehler sofort live.

### Notes
- **macOS-Debug-Anleitung:** wenn die App per Doppelklick immer noch
  sofort beendet, ohne Crash-Log auf dem Desktop, dann liegt der Fehler
  _unter_ Python (PyInstaller-Bootloader, Gatekeeper-Library-Validation).
  Diagnose: einmal direkt aus dem Terminal starten:
  ```
  "/Applications/Hermes Portal.app/Contents/MacOS/hermes-portal"
  ```

---

## [1.0.3] — 2026-05-22

Desktop-Launch-Fix. v1.0.2 hat den Sign-Bug gelöst, jetzt startete die
.app aber stumm und schloss sich sofort wieder.

### Fixed
- **macOS-App startet wieder.** `entry_pyinstaller.py` versuchte das
  Daten-Verzeichnis in `[bundle]/Contents/MacOS/hermes-portal-data/`
  anzulegen — `/Applications/` ist für Normaluser nicht writable
  → `PermissionError` → ungefangene Exception → App stirbt im
  Millisekunden-Bereich. Jetzt plattform-konventionelle User-Data-Pfade:
  - **macOS:**   `~/Library/Application Support/Hermes Portal/`
  - **Windows:** `%APPDATA%\Hermes Portal\`
  - **Linux:**   `$XDG_DATA_HOME/hermes-portal/` (Fallback `~/.local/share/…`)

### Added
- **Crash-Handler in `entry_pyinstaller.py`** — Tracebacks landen in
  `<data-dir>/crash.log`. Auf macOS außerdem ein nativer Dialog mit
  „Beim Start ist ein Fehler aufgetreten…" via `osascript`, damit
  per-Doppelklick gestartete .app-Bundles nicht mehr lautlos sterben.
- **Startup-Log** zeigt jetzt das aktive Daten-Verzeichnis im Terminal
  (für Power-User die das Binary aus der Shell starten).

### Notes
- **Daten-Migration:** wenn du vorher die portable Variante aus
  `Downloads/` gestartet hattest, liegen deine Daten dort in
  `hermes-portal-data/`. Die .app-Variante nutzt jetzt
  `~/Library/Application Support/Hermes Portal/` — bei Bedarf den
  Ordner-Inhalt manuell rüberkopieren.

---

## [1.0.2] — 2026-05-22

Bugfix für den Bugfix: der macOS-Sign-Loop aus v1.0.1 hatte selbst einen
Bug und hat de facto NICHTS signiert.

### Fixed
- **macOS-DMG „beschädigt" — endgültiger Fix.** Das `awk` in v1.0.1
  zur Pfad-Extraktion aus der `file`-Ausgabe hat fundamental falsch
  geschnitten (entfernte das letzte Wort statt nur die Type-Description),
  so dass `codesign` mit Phantasie-Pfaden aufgerufen wurde und **kein
  einziges Mach-O-File tatsächlich signiert** wurde. Das Python-Framework
  blieb damit weiterhin unsigned → Apple-Silicon-Gatekeeper hart
  abgelehnt. Komplett neu in Python (`_wiki_server/scripts/sign_macos_app.py`)
  mit lesbarem Code und verifizierbaren Counts im Build-Log.

### Changed
- **`_wiki_server/scripts/sign_macos_app.py`** als wartbares Tool im
  Repo statt fragiler Bash-Pipe im Workflow. Findet alle Mach-O-Files
  per `file`-Magic-Check, sortiert nach Pfad-Tiefe (innerste zuerst),
  signiert ad-hoc, gibt Statistik aus.

### Notes
- **HA-Panel-Icon `mdi:robot-happy`** wird oft nicht direkt nach einem
  Update sichtbar — HA-Supervisor cached die Panel-Registration vom
  Installationszeitpunkt. Workaround: Add-on **einmal deinstallieren
  und neu installieren** (oder `ha core restart`). Die Add-on-Daten
  in `/data/` bleiben dabei erhalten.

---

## [1.0.1] — 2026-05-22

Hotfix-Welle nach den ersten produktiven 1.0-Installationen.

### Added
- **Update-Check via GitHub Releases API** (`/api/version/check`).
  Antwortet `{current, latest, update_available, url}`, In-Memory-Cache
  60 Min, robust gegen Offline/Rate-Limit. Sidebar zeigt einen kleinen
  gelben „⬆ vX.Y.Z"-Badge neben der Versionsnummer, wenn ein neuerer
  Release verfügbar ist — Klick öffnet die GitHub-Release-Seite.
  Hauptnutzen für Desktop-Installer (AppImage/.dmg/.exe), wo es sonst
  keinen Hinweis auf neue Versionen gibt. HA-Add-on bleibt unberührt
  (HA-Supervisor liefert den Hinweis selbst).
- **Freundliche Fallback-Seite** für `/blog/index.html`,
  `/blog/aufgaben.html`, `/blog/briefing.html`, wenn die Datei (noch)
  nicht existiert: neues Template `blog_missing.html` erklärt, dass
  News/Aufgaben/Briefing vom Hermes-Agent erzeugt werden, listet
  typische Ursachen und verlinkt auf Settings + Briefing-„Jetzt erzeugen".

### Changed
- **HA-Add-on Panel-Icon** von `mdi:satellite-uplink` auf `mdi:robot-happy`.
- **macOS-DMG-Workaround** in README + Release-Body korrigiert: xattr
  muss **vor** dem Kopieren in Programme ausgeführt werden (entweder
  an der DMG-Datei im Downloads-Ordner oder am gemounteten Volume) —
  vorher dokumentierter `/Applications/Hermes Portal.app`-Pfad existiert
  nicht, weil Finder die App schon vor dem Kopieren ablehnt.

### Fixed
- **HA-Header-Logo fehlte** im Sidebar-Panel: zwei Stellen in
  `site-header.js` (Header-Brand + Footer-Logo) nutzten noch das
  hardcodierte `/static/portal/logo.png` ohne Ingress-Prefix. Beide
  durch `withPrefix(...)` ersetzt.
- **News/Aufgaben/Briefing-404** ist jetzt eine erklärende Seite statt
  nacktem „Not Found" — vorher dachte man, das Add-on sei kaputt.
- **macOS-DMG „beschädigt"** bei jeder Installation: PyInstaller bündelt
  Mach-O-Files ohne Extension (z.B. `_internal/Python`-Framework), unser
  alter Sign-Loop filterte aber nur `*.dylib`/`*.so` → Python-Framework
  blieb unsigned → Apple-Silicon-Gatekeeper hart abgelehnt. Neuer
  Sign-Loop identifiziert Mach-O-Files per `file`-Magic-Check (alle ~30 s
  durch) und signiert inner-most zuerst, damit verschachtelte Bundles
  korrekt aufgebaut sind.

---

## [1.0.0] — 2026-05-22

Erstes 1.0-Release. Markiert den Punkt, an dem alle Plattform-Pfade
(Desktop-Installer, Docker, Home-Assistant-Add-on) durchgängig
nutzbar sind.

### Added
- **HA-Ingress-Support** in `_wiki_server/wiki_app.py` als WSGI-Middleware
  (`_IngressMiddleware`): liest den `X-Ingress-Path`-Header vom HA-Supervisor
  und mappt ihn auf WSGIs `SCRIPT_NAME`. Damit erzeugt Flask's `url_for(...)`
  automatisch korrekt geprefixte URLs für Static-Assets und Endpoints.
- **`window.HP_INGRESS_PATH`** in `base.html` aus `request.script_root`.
  Plus globaler Patcher: wrappt `window.fetch` und rewritet `<form action="/…">`,
  damit die 46 hardcodierten `/api/…`-Calls im Frontend ohne einzelne
  Anpassung unter Ingress funktionieren.
- **`hermes_portal/CHANGELOG.md`** — HA-Supervisor zeigt diese Datei im
  Update-Dialog des Add-ons (vorher: "No changelog found").

### Changed
- **macOS-Intel-Build aus dem Release-Workflow entfernt**: `macos-13`-Runner
  sind seit Q2 2026 stark rationiert (Wartezeit Stunden, oft Timeout). Einziges
  macOS-Asset ist jetzt `Hermes-Portal-macOS.dmg` (Apple Silicon, arm64).
  Intel-Mac-User können das Repo lokal klonen und `pyinstaller` selbst laufen
  lassen oder die Docker-Variante nutzen.
- **`pyproject.toml`** Development Status von Beta (4) auf Production/Stable (5).
- **`base.html`** Static-Asset-URLs auf `url_for('static', filename=…)` statt
  hardcodierter `/static/…`-Pfade (CSS, Logo, Favicon, site-header.js).

### Fixed
- **HA-Add-on: kaputtes Layout im Sidebar-Panel** — Browser holte CSS, JS und
  Logos gegen die HA-Origin statt gegen die Ingress-URL → 404, nackte HTML-Seite,
  kein Header. Behoben durch Ingress-Middleware + URL-Prefix in `base.html` +
  Prefix-Anwendung in `site-header.js` (Nav-Links + Status-Polling).

Hotfix-Release. v0.8.0 ließ sich zwar im HA-Supervisor bauen, aber der
Container startete nicht — und der macOS-Intel-Build hing 20+ Minuten am
Sign-Loop.

### Fixed
- **HA-Add-on startet wieder** — `tini` liegt auf Alpine unter `/sbin/tini`,
  nicht unter `/usr/bin/tini` wie auf Debian. Der Container scheiterte mit
  `exec: "/usr/bin/tini": stat … no such file or directory`. Pfad im
  `hermes_portal/Dockerfile` korrigiert.
- **macOS-Sign-Loop 10× schneller** — alter Code rief für *jede* Datei
  im Bundle (~500–2000 Files) erst `file`, dann `codesign` auf, jeweils
  als eigenen Prozess. Jetzt:
  - Filter per Extension (`*.dylib`, `*.so`) statt `file`-Magic-Check,
  - Batch-Mode (`-exec … {} +`) statt Einzelausführung (`\;`),
  - macos-13-Runner ist nicht mehr der Stau-Engpass im Release-Workflow.

---

## [0.8.0] — 2026-05-22

Release-Streamlining und macOS-Härten.

### Added
- **Zwei separate macOS-DMGs** statt einer universellen Datei:
  - `Hermes-Portal-macOS-AppleSilicon.dmg` (arm64, native Build auf
    `macos-14`).
  - `Hermes-Portal-macOS-Intel.dmg` (x86_64, native Build auf `macos-13`).
- **Ad-hoc-Codesignatur** für die macOS-App (Identity `-`): alle nested
  Mach-O-Binaries werden signiert, anschließend das Bundle als Ganzes.
  Anschließend werden xattrs vollständig gestrippt.
- **Quarantine-Workaround** im Release-Body und README dokumentiert
  (`xattr -dr com.apple.quarantine …`) — nötig, weil ohne kostenpflichtigen
  Apple-Developer-Account keine Notarisierung möglich ist.

### Changed
- **GitHub-Release enthält ab v0.8.0 nur noch native Installer**
  (`.dmg` × 2, `.exe`, `.AppImage`). Die portablen Archive
  (`.zip` / `.tar.gz`) entfallen — wer den rohen Build-Ordner braucht,
  baut selbst per `pyinstaller` (Spec liegt unverändert im Repo).
- **HA-Add-on `build.yaml`** auf das Nötigste reduziert: nur noch
  `build_from:` mit den HA-Base-Images für `amd64` + `aarch64`. Die
  deprecated Felder `labels:` und `args:` sind raus — Labels liegen jetzt
  als `LABEL`-Direktiven direkt in `hermes_portal/Dockerfile`.

### Fixed
- **macOS „App ist beschädigt"-Fehler** beim Öffnen des heruntergeladenen
  DMG: ursache war fehlende Code-Signatur + Chrome-Quarantine-Flag. Mit
  ad-hoc-Sign + xattr-strip + dokumentiertem User-Workaround ist die App
  jetzt startfähig.
- **macOS-Sign-Build-Fehler** „bundle format unrecognized … flask-X.Y.Z
  .dist-info": `codesign --deep` versucht jeden Unterordner als nested
  Bundle zu signieren und scheitert an Python-Metadaten-Folders. Fix:
  alle Mach-O-Files (Binary, `.dylib`, `.so`) einzeln signieren, das
  Bundle als Ganzes **ohne** `--deep`.
- **HA-Add-on-Build-Fehler** „base name ($BUILD_FROM) should not be
  blank": entstand durch komplettes Entfernen der `build.yaml`. Der
  HA-Supervisor liefert `BUILD_FROM` nur dann als Build-Arg, wenn
  `build.yaml` mit `build_from:` vorhanden ist. Datei wieder da, in
  minimaler Form.

---

## [0.7.0] — 2026-05-22

Hotfix- und Distribution-Release. Macht das Home-Assistant-Add-on installierbar
und liefert echte native Installer für alle Desktop-Plattformen.

### Added
- **Native Installer** im Release-Workflow:
  - **macOS** → `Hermes-Portal-macOS.dmg` (`.app`-Bundle mit `.icns`-Icon,
    in DMG verpackt via `hdiutil`).
  - **Windows** → `Hermes-Portal-Setup.exe` (Inno Setup 6, mit Start-Menü-
    Eintrag, optionalem Desktop-Icon, Uninstaller, deutscher Übersetzung).
  - **Linux** → `Hermes-Portal-Linux.AppImage` (self-contained,
    `chmod +x` reicht zum Start).
- **Portable Archive** (`.zip` / `.tar.gz`) bleiben zusätzlich für Power-User
  erhalten — beide Varianten landen am Release dran.
- **HA-Add-on-Logo + -Icon**: `hermes_portal/logo.png` (250×250) und
  `hermes_portal/icon.png` (128×128) → HA zeigt jetzt das Hermes-Caduceus
  im Add-on-Store statt Default-Platzhalter.

### Changed
- **HA-Add-on Dockerfile** komplett umgebaut: zieht die Portal-Sourcen beim
  Build self-contained per `git clone --branch v${BUILD_VERSION}` aus
  GitHub, statt vorgenerierte `rootfs/app/`-Artefakte zu erwarten.
  - `hermes_portal/prepare.sh` ist damit obsolet und entfällt.
  - `hermes_portal/rootfs/` entfällt, `run.sh` liegt jetzt direkt im
    Add-on-Root.
  - `.gitignore`-Einträge für `rootfs/app/` und `rootfs/requirements.txt`
    aufgeräumt.

### Fixed
- **HA-Add-on Build-Fehler** „failed to compute cache key … '/rootfs/app':
  not found" — Build funktioniert jetzt 1:1 auf dem HA-Supervisor, ohne
  dass `prepare.sh` vorher lokal ausgeführt werden musste.

---

## [0.6.0] — 2026-05-22

Erstes Wartungs-Release nach dem öffentlichen Launch. Lizenz-Wechsel,
neue UI-Toggles und projektweite Changelog-Dokumentation.

### Added
- **CHANGELOG.md** im Keep-a-Changelog-Format — ab jetzt werden alle
  Releases hier dokumentiert.
- **Nav-Toggles** im Settings → App-Tab — neue Sektion „📑 Menü-Punkte
  sichtbar" mit Checkboxen für **News** und **Briefing**. Wer diese
  Features nicht nutzt, kann sie aus Header und Sidebar ausblenden.
  - Neue Config-Keys `show_news` / `show_briefing` (Default `true`),
    sowohl in `config.py` als auch in `config.defaults.json`.
  - Frontend-Filter via `window.HP_NAV_HIDE` in `base.html`,
    `site-header.js` rendert Header **und** Sidebar dynamisch.
- **Docker-Workflow** (`.github/workflows/docker.yml`) — rollender
  Multi-Arch-Build auf jeden `main`-Push, der Docker-relevante Dateien
  betrifft. Tags: `:main` (HEAD) + `:sha-<short>` (Rollback-Anker).
- **`repository.yaml`** im Repo-Root + Add-on-Folder auf `hermes_portal/`
  verschoben → Repo kann jetzt direkt als Home-Assistant-Add-on-Quelle
  hinzugefügt werden.

### Changed
- **Lizenz** auf **Apache License 2.0** umgestellt (vorher gemischt
  zwischen MIT lokal und CC BY-NC-SA 3.0 auf GitHub). Alle Referenzen
  konsistent aktualisiert: `LICENSE`, `README.md`, `pyproject.toml`
  (Classifier), `.github/workflows/release.yml` (OCI-Label),
  `hermes_portal/build.yaml` (OCI-Label).
- **HA-Add-on-Pfad**: `homeassistant/hermes_portal/` → `hermes_portal/`
  (HA-Supervisor scannt nur Repo-Root nach Add-on-Foldern).
- **HA-Add-on-Version** in `hermes_portal/config.yaml` von `0.1.0` auf
  `0.6.0` synchronisiert.

### Fixed
- **Type-Import-Reihenfolge** in `_wiki_server/wiki_app.py`:
  `from typing import Optional` an den Datei-Anfang verschoben (vorher
  Zeile 3292 → CI-Smoke-Import-Fehler bei Annotation in Zeile 3120).
- **Windows-Unicode-Crash** in `_wiki_server/scripts/fetch_monaco.py`:
  Stdout/Stderr explizit auf UTF-8 reconfiguriert, damit der
  PyInstaller-Build auf `windows-latest` nicht an `cp1252`-Encoding
  von Unicode-Pfeilen/Häkchen scheitert.
- **PyInstaller-Icon-Konvertierung**: `pillow` als Build-Dep ergänzt,
  damit das PNG-Logo auf Windows automatisch zu `.ico` konvertiert wird
  (vorher: `ValueError: Received icon image … which is not in the
  correct format`).

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

[Unreleased]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.10...HEAD
[1.0.10]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.9...v1.0.10
[1.0.9]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.8...v1.0.9
[1.0.8]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/jayjojayson/Hermes-Portal/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/jayjojayson/Hermes-Portal/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/jayjojayson/Hermes-Portal/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/jayjojayson/Hermes-Portal/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/jayjojayson/Hermes-Portal/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/jayjojayson/Hermes-Portal/releases/tag/v0.5.0
