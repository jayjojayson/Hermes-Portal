# Changelog

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) ·
Versionsschema: [SemVer](https://semver.org/lang/de/).

> 🇬🇧 **English version** → [Changelog_eng.md](Changelog_eng.md)

---

## [Unreleased]

### Added
- _(noch nichts)_

---

## [1.3.6] — 2026-05-29

🐛 **Hotfix für drei v1.3.5-Chat-Bugs.**

### Fixed
- **🖼 Bild- & PDF-Vorschau war leer** — die Helper-Funktionen
  `_detectFileKind()` und `_showEditorMode()` wurden in v1.3.5
  aufgerufen, aber ihre Definitionen waren nie in `chat.html`
  gelandet (Tooling-Glitch beim Release). Ergebnis: stiller
  `ReferenceError` in `openEditorForPath`, kein Bild/PDF wurde
  gerendert, Titel hing auf „⏳". Funktionen jetzt sauber definiert,
  Vorschau funktioniert für jpg/png/gif/bmp/webp/svg/ico/avif/pdf.
- **🔽 Scroll-Buttons (↑/↓) waren unsichtbar** — der `.chat-scroll-fab`-
  Container war `position: absolute`, aber sein Vorfahre `.chat-area`
  hatte kein `position: relative` → die FABs wurden gegen ein
  weiter außen liegendes Element positioniert (oft außerhalb des
  sichtbaren Bereichs). Fix: `position: relative` auf `.chat-area`.
- **📭 Erste Session scrollte nicht zur neuesten Nachricht** — beim
  initialen Auto-Select via `loadChats()` wurde `scrollToBottom()`
  nach 50 ms gefeuert, aber zu diesem Zeitpunkt war der gerade erst
  sichtbar gewordene `.chat-messages`-Container noch nicht ausge-
  layoutet → `scrollHeight = 0` → kein Scroll. Fix: doppelter
  `requestAnimationFrame`-Tick (nach Paint) plus später Fallback-
  Tick bei 250 ms für nachladende Bilder.

---

## [1.3.5] — 2026-05-29

💬 **Chat-Upgrades: Bild-/PDF-Vorschau, Scroll-Komfort, Session-Umbenennen.**

### Added
- **🖼 Bild- & PDF-Vorschau im Chat-Editor** — Klick auf eine
  Bild-Datei (jpg/png/gif/bmp/webp/svg) oder PDF im Datei-Tree öffnet
  jetzt eine echte Vorschau statt des leeren Monaco-Editors. Neuer
  Backend-Endpoint `GET /api/chat/shared/raw` streamt die Datei mit
  korrektem MIME-Type (local via `send_file`, SSH via SFTP-In-Memory).
  Bilder rendern als `<img>`, PDFs als `<embed>`. Read-only — der
  Speichern-Button wird in der Vorschau ausgeblendet. Code/Text-
  Dateien öffnen weiterhin im editierbaren Monaco.
  - Neue `read_bytes()`-Methode in beiden hermes_client-Backends
    (local + ssh).
- **↑↓ Scroll-Komfort im Chat** — beim Öffnen einer Session wird
  jetzt direkt zur neuesten Nachricht gescrollt (statt am Anfang zu
  starten). Plus zwei schwebende Buttons unten rechts: „↑ ganz oben"
  und „↓ ganz unten". Erscheinen nur wenn der Verlauf scrollbar ist
  und blenden sich am jeweiligen Rand einzeln aus.
- **✎ Session umbenennen** — neuer Stift-Button neben dem Lösch-×
  in jeder Session-Zeile. Klick öffnet einen Prompt mit dem aktuellen
  Titel, speichert via `POST /api/chat/rename`. Vorher wurde immer
  der erste Satz der ersten Nachricht als Titel verwendet — jetzt
  frei benennbar für saubere Sortierung (Auto-Titel greift nur noch
  solange die Session „Neuer Chat" heißt).

### Documentation
- **📖 README Slash-Command-Klarstellung** — der README-Chat-Abschnitt
  warb noch mit dem in v1.1.8 entfernten Slash-Command-Dropdown.
  Jetzt korrekt: Slash-Befehle werden **nicht** vom Portal
  interpretiert, sondern 1:1 an den Agent gesendet; ob `/reset` &
  Co. wirken, hängt davon ab, ob der Agent sie im `hermes -z`-Mode
  behandelt (viele nur im interaktiven REPL). Der ⏹ Stop-Button ist
  die Ausnahme — er läuft Portal-seitig via AbortController. Für eine
  frische Session den **+**-Button in der Session-Sidebar nutzen.

---

## [1.3.4] — 2026-05-28

🧹 **Mikro-Polish: Zeitraum-Verbrauch in 2×2, Identity-Label kürzer,
Release-Notes auf Englisch.**

### Changed
- **📅 Zeitraum-Verbrauch in 2×2-Grid** — vorher auto-fit (4 Karten
  nebeneinander), jetzt feste 2 Spalten: Zeile 1 = Tokens · 7 Tage +
  Calls · 7 Tage, Zeile 2 = Tokens · 30 Tage + Calls · 30 Tage. So
  gehören Woche und Monat visuell sauber zusammen.
- **🗂 Extra-Wiki-Categories Label gekürzt** — vorher
  „Extra wiki categories (comma-separated subdir names)" über zwei
  Zeilen, jetzt einzeilig „Extra wiki categories" in 4 Sprachen.
  Damit stehen alle drei Identity-Zeile-2-Felder sauber in einer
  Linie, ohne dass das mittlere Feld sich tiefer schiebt.
- **📋 GitHub-Release-Notes auf Englisch** als Standard, mit
  Quick-Links zu beiden Changelogs (en + de) und beiden READMEs am
  Anfang des Bodies. Englisch ist die bessere Wahl für die
  internationale GitHub-Audience.

---

## [1.3.3] — 2026-05-28

🎨 **Settings-UX-Politur: dichterer Usage-Header, klarer Identity-Box-Aufbau,
Extra-Kategorien-Dropdown in allen Pfaden.**

### Changed
- **📊 Usage-Tab Header verdichtet** — die drei separaten Zeilen (API
  Requests / Token-Verbrauch / Zeitraum-Verbrauch) liegen jetzt in
  einem 3-Spalten-Grid mit eigenen Sub-Headlines. Karten sind kompakter
  (95 px min statt 140 px, kleinere Werte, dichteres Gap). Auf wide
  Screens passen alle 12 Kennzahlen in eine Reihe statt in drei.
  Auf schmalen Screens stapeln sich die Blöcke wieder automatisch.
- **👤 Identity-Box neu strukturiert** — zwei klar getrennte Zeilen:
  Zeile 1 = `Your name` + `Agent name` (Personen-Namen),
  Zeile 2 = `Category: Entities` + `Category: Concepts` +
  `Extra wiki categories` (alle drei Kategorie-Labels zusammen).
  Das `wiki_extra_dirs`-Feld wandert aus dem Paths-Block in die
  Identity-Box, wo es semantisch hingehört.

### Fixed
- **🗂 Neue-Seiten-Form: Extra-Kategorien-Dropdown** war bei POST-Fehler-
  Fallbacks unsichtbar (3 verschiedene `render_template`-Aufrufe in
  `new_page()` haben `extra_categories` nicht durchgereicht). Jetzt
  einheitlich über `_render_new()`-Helper — Dropdown ist garantiert
  in JEDEM Pfad sichtbar (GET, leerer Titel, existierende URL,
  Schreibfehler).

---

## [1.3.2] — 2026-05-26

📊 **Usage-Chart wirklich gefixt + Wochen/Monatsverbrauch + Wiki-Multi-Kategorien.**

### Fixed
- **📊 Usage-Tab Balkendiagramm zeigt jetzt tatsächlich Daten** —
  v1.3.1 hatte `d.hourly[hk].total` benutzt, aber die Token-Hourlies
  liegen unter `d.tokens.hourly[hk].total` (`.count` im top-level
  `d.hourly` sind HTTP-Requests, nicht Tokens). Tooltip nennt jetzt
  alle drei Werte: `XX:XX — Y Tokens · Z Model-Calls · W HTTP-Requests`.

### Added
- **📅 Wochen- + Monatsverbrauch-Karten** im Usage-Tab — vier neue
  Stat-Karten (Tokens/Calls × 7d/30d) aggregiert aus `agent.log` über
  den neuen Endpoint `GET /api/settings/usage/range?days=N`. Lädt
  parallel zum Tages-Detail, separat zwischengespeichert.
- **🗂 Wiki-Multi-Kategorien** via Settings → 🛰️ App →
  „Zusätzliche Wiki-Kategorien" (Komma-getrennte Subordner-Namen,
  z.B. `rezepte, projekte, todo`). Jeder Ordner wird wie `concepts/`
  indexiert, gelesen und editiert. **Das 2-Box-Layout der
  Wiki-Übersicht bleibt unangetastet** — Extras zählen zur
  „Konzepte"-Box dazu und werden als kleine Chip-Liste mit Counts
  darunter angezeigt. Neue-Seiten-Form bietet die Extras als Dropdown-
  Optionen, Backend validiert gegen Whitelist (kein Path-Traversal).
- **🔧 `_coerce()`** akzeptiert für Listen-Felder jetzt JSON UND
  Komma-getrennte Strings (vorher nur JSON). Praktisch für Settings-
  Textfelder, die der User direkt tippt.

---

## [1.3.1] — 2026-05-26

🐛 **References-Save-Bug + Usage-Tab-Chart wie Dashboard.**

### Fixed
- **📁 References-Save: „Datei nicht gefunden"** trotz geöffneter Datei.
  Frontend sandte beim `PUT /api/references/...` nur den Dateinamen
  (`growbox-report.py`), der Backend-Resolver erwartet aber den
  `source_type/rel_path`-Key (`references/growbox-report.py`). Fix:
  - JS trackt jetzt `_currentRefUrlKey` (Routing-Key) zusätzlich zu
    `_currentRefName` (Anzeige). Beim Speichern/Löschen wird der
    URL-Key benutzt.
  - URL-Pfad-Segmente einzeln encoded statt einmal komplett — die
    Flask-Route `<path:url_key>` braucht die Slashes ungequoted, sonst
    matcht nichts. (War zusätzlich versteckter Bug, der bei Subdirs
    relevant geworden wäre.)
  - Cache-Lookup nach `url_key` statt `name` (Dateinamen sind über
    `source_types` hinweg nicht eindeutig).
  - Skills-Tab war nicht betroffen (nutzt eigenen `POST`-Endpoint mit
    `url_key` im JSON-Body).
- **📊 Usage-Tab Balkendiagramm jetzt wie Dashboard-Widget** — zeigt
  Token-Verbrauch pro Stunde (vorher Request-Count), mit Tooltip der
  Tokens UND Requests nennt, aktueller Stunde voll opak hervorgehoben,
  inaktiver Rest dezent. Skaliert auf den Tages-Max-Wert, mindestens
  2 % Höhe damit auch leise Stunden als Spalte sichtbar bleiben.

---

## [1.3.0] — 2026-05-26

🛠 **Agent-Skript-Bundle, RSS-Bridge, längerer Chat-Timeout.**

### Added
- **🛠 Mitgelieferte Agent-Skripte (`blog_generator.py` + `daily_briefing.py`)**
  unter `_wiki_server/templates/agent_scripts/`. Settings → 🛰️ App
  hat eine neue Box „Agent-Skripte (One-Click-Installation)" — Klick
  auf *Install* kopiert das Skript via local FS oder SFTP an den
  Hermes-Agent (Default-Pfade: `blog/blog_generator.py` und
  `scripts/daily_briefing.py`). Vorhandene Skripte werden nur mit
  expliziter Bestätigung überschrieben.
- **🔌 ENV-Bridge Portal → Agent-Skripte** — `cfg.portal_env()` setzt
  beim Cronjob-Aufruf:
  - `PORTAL_BLOG_DIR`, `PORTAL_POSTS_SUBDIR`,
    `PORTAL_AGENT_NAME`, `PORTAL_USER_NAME`
  - `NEWS_RSS_FEEDS` (komplette RSS-Liste als JSON)
  Damit nutzen die Default-Skripte **automatisch** die im Portal
  konfigurierten RSS-Feeds — keine Code-Anpassung mehr nötig.
- **⏱ Chat-Antwort-Timeout konfigurierbar** (neues Settings-Feld
  `chat_timeout_sec` in Settings → 🛰️ App, Default 300 s = 5 min,
  max. 1800 s). Backend nimmt den Wert für `client.hermes(["-z", …])`.
  Plus: bei Timeout zeigt der Chat jetzt eine klare Mehrzeilen-
  Erklärung mit Direktlink ins Settings statt „Versuch eine kürzere
  Nachricht" (war irreführend — das Problem war Antwortzeit, nicht
  Nachrichtenlänge).
- **📖 README-Update (en + de)** — „Setup in 2 Klicks"-Abschnitt für
  News, der die neue Agent-Skript-Installation aus dem Settings-Tab
  erklärt.

### Fixed
- **🌐 Irreführender RSS-Hinweis** im App-Tab korrigiert. Vorher:
  „RSS feeds … NOT automatically passed to your news generator".
  Jetzt: das Portal reicht die Feeds **doch** durch — solange du
  das mitgelieferte `blog_generator.py` nutzt.

---

## [1.2.2] — 2026-05-25

📂 **News-Detailseiten via posts/-Subdir, Pagination, Subdir-Setting.**

### Added
- **📄 Pagination auf der News-Übersicht** — 9 Beiträge pro Seite,
  Prev/Next + Seitenzahlen unten zentriert, „«" springt zur ersten,
  „»" zur letzten. Bei Page-Wechsel sanfter Scroll an den Anfang.
  Übersetzt in en/de/es/fr.
- **⚙️ Settings → 🛰️ App → Blog-Posts-Subordner** — neues Feld
  `blog_posts_subdir` (Default `"posts"`). Wer eine flache
  Verzeichnisstruktur hat trägt leeren String ein.

### Fixed
- **🔗 Klick auf News-Karte → 404 weil falscher Pfad** — der
  Hermes-Agent-Blog-Generator legt die Einzel-Tagesberichte unter
  `BLOG_DIR/posts/<datei>.html` ab, das Portal hat aber direkt unter
  `BLOG_DIR/` gesucht. Ab v1.2.2:
  - `_post_detail_url` baut Slug-URLs als `/blog/<posts_subdir>/<slug>.html`
    (statt `/blog/<slug>.html`).
  - `/blog/<filename>`-Route fällt auf `posts/<filename>` zurück, wenn
    die Datei nicht top-level existiert — funktioniert sowohl lokal
    als auch über SSH (via `client.exists`).
  Bestehende User-Setups mit Subdir „posts" funktionieren ohne
  Config-Änderung, weil das der Default ist.

---

## [1.2.1] — 2026-05-25

🖼 **News-Karten mit Hero-Bildern + funktionierende Detail-Links.**

### Fixed
- **📰 News-Karten haben Bilder zurück** — v1.2.0 hat das nackte
  Text-Grid gerendert, weil das Backend `posts.json` nur auf
  `title/url/summary/category/source` reduziert hat. Ab v1.2.1 zieht das
  Backend alle üblichen Bild-Felder (`image`, `cover`, `thumb`, `hero`,
  `og_image`, …), Kategorien als Liste, Tags und löst relative Pfade
  zu `/blog/<asset>` auf. Karten zeigen jetzt 16:9-Hero (oder
  Platzhalter-Gradient + 📰-Icon, wenn der Beitrag kein Bild hat).
- **🔗 Karte klickt zur Tagesbericht-Detailseite** — vorher öffnete der
  Klick im neuen Tab die News-Übersicht selbst, weil ich
  `target="_blank"` auf den Titel-Link gesetzt hatte und nur die erste
  beste URL aus `posts.json` (oft die externe Quelle) als href
  verwendete. Jetzt:
  - Komplette Karte ist `<a>` (größere Click-Target)
  - Backend liefert `detail_url` aus `path`/`filename`/`slug` und
    löst auf `/blog/<datei>.html` auf (die vom Hermes-Agent
    formatierten Morgens/Mittags/Abends-Berichte)
  - Kein `target="_blank"` mehr — navigiert in derselben Tab
  - Original-Quelle bleibt als `source_url` separat im Payload,
    falls künftig ein „🔗 Originalartikel"-Button gewünscht ist

---

## [1.2.0] — 2026-05-25

📰 **Portal-native News-Seite, Status-Pill-Fix, Chat-Welcome-i18n,
Cronjob-Edit-Truncation-Fix, Update-Diagnose im Support-Tab, Mac-Desktop
sauber.**

### Added
- **📰 News-Seite komplett Portal-nativ** (`/news/`) — eigenes Template
  ersetzt die früher vom Hermes-Agent generierte `/blog/index.html`.
  - Karten-Grid mit Titel, Datum, Kategorie, Summary, Quelle.
  - Reload-Button + Live-Counter.
  - Aufklappbare Cron-Note unten mit Copy-Paste-Prompt für den
    `blog_generator.py` (Empfehlung: 3× täglich morgens/mittags/abends).
  - Liste der konfigurierten RSS-Feeds aus Settings (Direkt-Link
    zum App-Tab zum Bearbeiten).
  - Bei leerem `posts.json` automatisches Öffnen der Cron-Note +
    freundlicher Hinweis statt 404.
  - Vollständig in en/de/es/fr übersetzt (15 neue i18n-Keys).
- **🔍 Update-Check-Diagnose** im Support-Tab — aufklappbare Box zeigt
  das rohe `/api/version/check`-JSON inkl. `error`-Feld. So sieht man
  als User direkt, ob der API-Call funktioniert oder warum kein
  Update-Banner erscheint.
- **📖 README-Block „News page — Hermes fetches your RSS feeds"** (en + de)
  parallel zum bestehenden Aufgaben-Cronjob-Hinweis.
- **2–4h-Frequenz-Empfehlung** im Cron-Hinweis der Aufgaben-Seite.

### Fixed
- **🌐 Hermes-Status-Pill** zeigt nicht mehr `hermes.status.online`
  als rohen Schlüssel — die i18n-Keys waren beim Refactor versehentlich
  rausgeflogen. Jetzt korrekt „Hermes online / inaktiv / offline /
  kein Signal" in allen 4 Sprachen.
- **💬 Chat-Welcome-Screen vollständig übersetzt** — Intro „Ich bin %agent% —
  dein persönlicher Chat …" und alle 4 Quick-Action-Boxen
  (Wiki erkunden / Aktivitäten ansehen / Hilfe anbieten / Leerer Chat)
  laufen jetzt über `t()`. Auch die Quick-Prompts in
  Englisch/Spanisch/Französisch lokalisiert (12 neue i18n-Keys).
- **⏰ Cronjob-Edit: voller Prompt sichtbar** — beim Edit wurde
  `job.command || job.prompt` geladen, aber `command` ist im Backend
  auf 120 Zeichen für die Listen-Anzeige gekürzt. Frontend nutzt jetzt
  `job.prompt || job.command` (Prompt enthält den vollen Text).

### Changed
- **🍎 Mac-Desktop sauber** — `hermes-portal-started.txt` und
  `hermes-portal-trace.log` werden nicht mehr standardmäßig auf den
  Desktop geschrieben. Mit `HP_DEBUG=1` als Env-Var beim Start wieder
  aktivierbar (für künftige Startup-Crash-Diagnose).
- **📰 Nav-Link „News"** zeigt jetzt auf `/news/` (Portal-Route) statt
  `/blog/`. Active-State-Detection erkennt beides als „news"-Page.

---

## [1.1.9] — 2026-05-25

🎯 **Portal-native Aufgaben-Seite, Mac-Update-Banner-Fix, Status-Pill-i18n,
Cronjob-Editor mit voller Prompt-Sicht.**

### Added
- **✅ Aufgaben-Seite komplett Portal-nativ** (`/aufgaben/`) — eigenes
  Template ersetzt die früher vom Hermes-Agent generierte `aufgaben.html`.
  Hermes-Agent muss nichts mehr generieren, die Seite funktioniert direkt
  nach Installation. Features:
  - Prominent ganz oben: „➕ Aufgabe hinzufügen"-Form mit Titel,
    Bearbeiter-Dropdown (Agent vs. User) und optionaler Beschreibung.
    Auto-Sync sofort nach `aufgaben.md` — kein extra Sync-Button mehr.
  - Listen nach „Offen" / „Erledigt" getrennt; Checkbox-Klick verschiebt
    die Aufgabe in die andere Sektion und updated den Status in der
    Markdown-Datei.
  - 🗑 pro Zeile löscht die Aufgabe sauber aus `aufgaben.md`.
  - Aufklappbare Box mit Copy-Paste-Cron-Prompt für den Hermes-Agent
    (`{path}` / `{agent}` / `{user}` werden mit den echten Werten
    substituiert).
  - Vollständig übersetzt in en/de/es/fr (14 neue i18n-Keys).
- **🌐 Hermes-Status-Pill übersetzt** — „Hermes online / idle / offline /
  kein Signal" oben rechts auf dem Dashboard läuft jetzt über `t()`.
- **📖 README-Block „Tasks page — Hermes does the work"** (en + de)
  erklärt das Zusammenspiel Portal ↔ aufgaben.md ↔ Hermes-Cronjob und
  liefert das vorgefertigte Prompt-Template.

### Fixed
- **🍎 Mac-Update-Banner erscheint endlich** — `urllib.request.urlopen`
  hatte im PyInstaller-Build kein System-CA-Bundle und scheiterte still
  beim HTTPS-Call an api.github.com (deshalb blieb `update_available=False`
  und der Banner unsichtbar). Fix: `certifi`-Bundle in den
  Requirements + explizit als SSL-Context durchgereicht.
- **⏰ Cronjob-Editor zeigt den vollständigen Prompt** — Textarea
  vergrößert von 4 auf 14 Zeilen (`min-height: 16rem`), Modal-Breite
  auf 760 px erweitert, Monospace + vertical resize. Multi-Zeilen-Prompts
  (z.B. der Aufgaben-Cronjob mit „WICHTIG"-Liste) sind jetzt vollständig
  lesbar und editierbar.
- **🔘 Wiki-„New entry"-Button** nimmt nicht mehr die volle Box-Breite
  ein (`align-self: flex-start; width: auto`).

### Removed
- **🚮 Agent-generierte aufgaben.html nicht mehr erwartet** — Nav-Link
  „Tasks" zeigt jetzt auf `/aufgaben/` (Portal-native Route); alte
  `/blog/aufgaben.html`-Aufrufe werden im Site-Header-Active-State weiter
  als „aufgaben"-Page erkannt, aber die Seite selbst wird vom Portal
  gerendert, nicht mehr vom Agent.

---

## [1.1.8] — 2026-05-24

🎯 **Update-Banner, Aufgaben-Out-of-the-Box, Windows ohne Terminal, Private-Key-Reveal
+ kleinere UX-Bugfixes.**

### Added
- **🚀 Update-Banner überall** — schwebende Toast oben rechts auf jeder Page,
  wenn eine neuere Hermes-Portal-Version auf GitHub veröffentlicht wurde
  (User-Wunsch: „In der Mac App wurde mir keine Update auf die neue Version
  angezeigt"). Klick-Link führt zur Release-Page, „✕" dismissed für genau
  diese Version (localStorage). Backend-Endpoint `/api/version/check` mit
  1h-Cache existierte schon — nur die UI fehlte.
- **🔐 Private-Key anzeigen für Migration** — neuer „Reveal private key"-Button
  unter Settings → 🛰️ App → SSH-Wizard. Aufklappbares Warn-Panel mit
  Bestätigung, danach Klartext-Textarea + Copy-Button. So lässt sich der
  Portal-eigene SSH-Key auf andere Geräte kopieren, ohne die `authorized_keys`
  des Agents anzufassen. Endpoint: `POST /api/settings/app/ssh/reveal`.
- **📋 Aufgaben-Page funktioniert direkt** — Default-`aufgaben.md` wird
  automatisch in `BLOG_DIR/aufgaben.md` angelegt, wenn sie noch fehlt
  (Template: `_wiki_server/templates/aufgaben_default.md`). Wenn der
  Hermes-Agent keine `aufgaben.html` generiert hat, zeigt das Portal jetzt
  selbst eine bedienbare Tasks-Page mit „➕ Aufgabe hinzufügen"-Form ganz
  oben — Auto-Sync nach `aufgaben.md`, kein separater Sync-Button mehr.
- **⬅️ Sidebar-Öffnen via klickbarem Pfeil-Button** — ersetzt den
  unsichtbaren Hover-Strip am linken Rand, der sich versehentlich öffnete,
  wenn man im Home-Assistant-Frontend die HA-eigene Sidebar bedienen
  wollte. Klick-Button ist eindeutig + visuell sichtbar.

### Fixed
- **💬 Chat-Eingabefeld leert sich nach Send** — vorher blieb der Text
  drin (kosmetischer Bug seit v1.0).
- **🌐 Dashboard-Empty-States übersetzt** — „Kein anstehender Job",
  „Keine News verfügbar.", „Keine Aufgaben gefunden.", „Noch keine
  Wiki-Beiträge vorhanden.", „Kein Hermes-Logfile erreichbar."
  + Sidebar-„noch keine" + Chat-Sessions-leere-Liste laufen jetzt über
  `t()` und folgen der UI-Sprache (en/de/es/fr).
- **🪟 Windows: kein Terminal-Fenster mehr** beim Doppelklick auf die App
  (PyInstaller-Spec: `console=False` jetzt auch für `win32`, vorher nur
  `darwin`).

### Removed
- **🚮 Slash-Command-Dropdown im Chat** entfernt (User-Wunsch: „Da die
  CLI-Kommandos im Chat nicht funktionieren, entfernen wir diese Funktion
  wieder vollständig"). Button neben dem Ordner-Picker ist weg, samt
  Dropdown-Markup + JS. Slash-Befehle können weiterhin manuell getippt
  und nativ an den Agent gesendet werden — sie werden Portal-seitig
  nicht mehr interceptiert oder als Schnellauswahl angeboten.

---

## [1.1.7] — 2026-05-24

🔑 **SSH-Key paste-import + Settings-Save-Bar i18n + README-Konsolidierung.**

### Added
- **📥 SSH-Key importieren statt generieren** — neuer Button im SSH-Wizard
  (Settings → 🛰️ App): bestehenden Private-Key per Copy&Paste einfügen,
  Portal leitet automatisch den Public-Key ab (via `cryptography`-Lib) und
  legt beide unter `/data/.ssh/id_ed25519`(.pub) ab. Use-Case: dieselbe
  Identität auf mehreren Portal-Installationen verwenden, ohne den
  `authorized_keys` auf dem Hermes-Agent jedes Mal aktualisieren zu müssen.
  - Backend-Endpoint: `POST /api/settings/app/ssh/import`
    (Body: `{private_key, public_key?, overwrite, comment}`)
  - Validiert BEGIN/END-PEM-Marker, gibt 409 zurück wenn Key existiert
    und `overwrite=false`.
  - UI: aufklappbare Box mit zwei Textareas + Überschreiben-Checkbox,
    übersetzt in 4 Sprachen.

### Fixed
- **💾 Settings-Save-Bar komplett übersetzt** — die schwebende Box am
  unteren Settings-Rand zeigte „Ungespeicherte Änderungen / Klick „Speichern"
  oder Strg/Cmd+S" hartkodiert auf Deutsch, auch wenn UI auf Englisch
  stand. Alle Strings (Titel, Hinweis, „Gespeichert"-Bestätigung,
  Test-Verbindung-Button) laufen jetzt über `t()`.
- **🌐 i18n: 9 neue Keys** für SSH-Import in en/de/es/fr.

### Documentation
- **README-Merge**: `Installproces.md` in `README.md` (Englisch, Default)
  und `README.de.md` aufgegangen — komplette Troubleshooting-Tabelle
  (Portal/SSH/Monaco/Wiki/Docker/macOS-PKG/Windows-SmartScreen/HA-Container)
  plus First-Time-Configuration-Tabelle mit allen App-Settings. Inkl.
  Architektur-ASCII-Diagramm. Standalone-Datei gelöscht.

---

## [1.1.6] — 2026-05-25

🎯 **Mac-App startet endlich!** Plus Find-IP-Verbesserung für HA-Container
und Wiki-Layout-Politur.

### Fixed
- **🍎 macOS PKG: Python-Framework-Pfad korrigiert** — der Bootloader sucht
  Python unter `Contents/Frameworks/Python` (macOS-Konvention), wir hatten
  es aber unter `Contents/MacOS/_internal/Python`. Das führte zum
  `[PYI-15449:ERROR] Failed to load Python shared library`-Crash beim
  Start. Fix: PyInstaller's `BUNDLE`-Step in `hermes_portal.spec` baut die
  `.app` jetzt selbst mit korrekter macOS-Struktur (inkl. Symlinks
  Resources↔Versions). Der Workflow-Schritt „manuell .app aus dist
  zusammenbauen" entfällt.
- **📁 Wiki Import/Export-Layout** — Import-Button + Kategorie-Dropdown
  in Zeile 1, Export-Button alleinstehend in Zeile 2 (vorher alles in
  einer Zeile + Dropdown ragte über den Box-Rand). Dropdown skaliert
  jetzt auf Container-Breite mit `max-width: 100%`.

### Changed
- **🔎 Find IP versteht Container** — erkennt jetzt automatisch, wenn das
  Portal in einem Docker/HA-Add-on-Subnetz (172.16-31.x.x) läuft und
  daher nicht das User-LAN sieht. Zeigt eine klare Warnung + bietet ein
  manuelles Subnet-Eingabefeld („z.B. 192.168.178"). Erklärt das Problem
  in 4 Sprachen.

### Notes — Slash-Commands
Der User berichtet: `/new` startet eine neue Session, aber `/usage` und
`/reset` liefern halluzinierte LLM-Antworten. Das ist **agent-side**: der
Hermes-CLI behandelt manche Slash-Commands als spezielle Anweisungen
(z.B. `/new` triggert Session-Reset im Wrapper), andere reicht er als
normalen Prompt weiter zum LLM. Das Portal sendet ALLE Slash-Commands
unverändert an den Agent — die Antwortqualität hängt vom Agent-Setup ab.
Workaround: dem Agent-Maintainer melden, dass `/usage` / `/reset` etc.
auch im `-z`-Mode handled werden sollten (statt nur in REPL).

### Notes — Mac-Diagnose-Erfolg
Der `~/Desktop/hermes-portal-trace.log` aus v1.1.5 hat die Ursache
sauber lokalisiert: der Bootloader-Error war eindeutig in der ersten
Phase (vor Python-Init), exakt was wir vermutet hatten. BUNDLE im
Spec-File ist genau die Reparatur, die PyInstaller dafür vorsieht.

---

## [1.1.5] — 2026-05-25

Slash-Command-Revert + LAN-Discovery + Wiki-IO-Layout + Support-Tab i18n
+ aggressives Mac-Trace-Logging.

### Changed
- **Slash-Commands gehen nativ an den Hermes-Agent.** Portal-seitige
  Interceptoren aus v1.1.4 sind komplett raus. `/new`, `/reset`,
  `/usage`, `/help` etc. werden jetzt wie jede andere Chat-Nachricht
  unverändert an den Agent gesendet — der antwortet entsprechend. Wenn
  die Antwort halluziniert wirkt, liegt's am Invocation-Pattern des
  Agenten (`hermes -z` vs. REPL-Mode), nicht am Portal.
- **Wiki Import/Export**: Import-Button + Kategorie-Dropdown + Export-
  Button auf Desktop in **einer Zeile** (vorher zwei). Wrappt nur noch
  unter 520 px (Phone-Portrait).

### Added
- **🔎 „Find IP"-Button** in Settings → 🛰️ App → Connection. Scant das
  lokale `/24`-Subnetz auf SSH-fähige Hosts (Port 22 offen), zeigt die
  Treffer mit Hostname (Reverse-DNS), Klick übernimmt die IP ins
  Agent-Host-Feld. Neuer Endpoint `/api/settings/app/discover`.
- **Support-Tab vollständig i18n** in 4 Sprachen: Section-Titel
  (Support / GitHub & Community / Version), Intro-Text, alle
  Card-Beschreibungen.
- **📦 Version-Info-Sektion im Support-Tab** mit Update-Check (gleiche
  API wie der Sidebar-Footer-Badge). Zeigt aktuelle Version + bei
  verfügbarem Update einen ⬆-Link zur Release-Page.
- **🔍 Step-by-Step Mac-Trace-Logging** in `entry_pyinstaller.py`:
  jeder Schritt im Startup wird in `~/Desktop/hermes-portal-trace.log`
  geschrieben. Bei Crash sehen wir in der letzten Zeile WO genau
  gestorben wurde — Bootloader, Imports, Server-Thread, pywebview-
  Init, oder erst beim `webview.start()`-Call.

### Deferred
- **🗂 Weitere Wiki-Kategorien** (Wunsch aus dieser Runde) — wird in
  v1.2.0 angegangen: braucht Refactor von `/entity/<id>` und
  `/concept/<id>` auf eine generische `/category/<key>/<id>`-Route
  plus UI zum Hinzufügen/Verwalten in Settings → App → Identity.
- **News/Briefing/Tasks-Seiten-Subtitle**: das ist **agent-generierter
  Content** aus deinem Blog-HTML (`/blog/index.html` etc.). Das Portal
  strippt nur den Header und injiziert sein CSS, der Body-Inhalt
  (Titel + Untertitel) kommt 1:1 von deinem `daily_news.py` / Blog-
  Generator. Übersetzung wäre dort fällig, nicht im Portal.

### Notes — Mac-PKG-Diagnostik
Mit dem neuen Trace-File kommen wir dem stillen App-Tod auf die Spur.
Nach Install + Start-Versuch bitte `~/Desktop/hermes-portal-trace.log`
prüfen und Inhalt schicken — dann sehe ich exakt, ob's der
`pywebview`-`start()` ist, ein Library-Loading-Fehler, oder schon
früher.

---

## [1.1.4] — 2026-05-25

Slash-Commands intelligent gemacht, SSH-Wizard fertig übersetzt,
Mac-pywebview-Crash bekommt jetzt einen Browser-Fallback.

### Fixed
- **Slash-Commands wurden vom LLM halluziniert** — Hermes-CLI behandelt
  Slash-Befehle nur im REPL-Mode. Wenn wir per `hermes -z "/usage"`
  shell-en, sieht das Modell den Text als normalen Prompt und
  antwortet kreativ („Hold on, ich hab grad kein Tool für die Stats
  parat…"). Fix: Portal-seitige Slash-Handler in `chat.html` —
  die wichtigsten Befehle werden lokal abgefangen:
  - `/usage`, `/insights` → Link auf Settings → 📊 Usage
  - `/new`, `/reset` → startet neue Chat-Session
  - `/stop` → triggert den Stop-Button (oder Hinweis wenn nichts läuft)
  - `/help` → zeigt Liste aller verfügbaren Slash-Commands inline
  - `/quit` → Hinweis dass Server weiterläuft
  Andere Befehle (`/model`, `/tools`, …) gehen weiterhin als Text
  an den Agent.
- **macOS pywebview stirbt jetzt nicht mehr lautlos** — `webview.start()`
  ist in einen Try/Except gewrappt. Bei WKWebView-Init-Fehler oder
  anderen Runtime-Crashes wird auf Browser-Fallback umgeschaltet
  statt die App lautlos zu beenden. User sieht im Terminal-Log was
  passiert ist.

### Changed
- **SSH-Wizard komplett übersetzt** (Settings → 🛰️ App):
  - „Pubkey kopieren" / „Neu erzeugen" / „Prompt kopieren" / „Kopiert!"
  - Aufklappbare Hilfe-Texte „Manuell: Wie installiere ich den Key…" +
    „Automatisch: Prompt an den Hermes-Agent…"
  - 5 Manual-Schritte, alle Sub-Strings
  - 4 Sprachen × 17 neue Keys = 68 neue Übersetzungen
- **i18n-Tables jetzt 308 Keys × 4 Sprachen** (von 280 in v1.1.3)

### Notes — Mac-Crash-Diagnose
Wenn die PKG-installierte App `~/Library/Logs/DiagnosticReports/`-
Crash-Reports erzeugt, bitte mir den Inhalt eines `hermes-portal*.ips`
schicken. Mit dem neuen Browser-Fallback sollte aber wenigstens
sichtbar werden, was schiefgeht — Console.app → Process: hermes-portal
zeigt die stderr-Ausgabe.

---

## [1.1.3] — 2026-05-25

Mega-Update: macOS-PKG, Slash-Commands-Dropdown, Roboter-Avatar, neue
englische Default-README, vollständiger i18n-Bug-Fix für Windows.

### Fixed
- **🔴 „Dashboard.Hermes"-Bug auf Windows/Mac-Bundles** — der `i18n/`-
  Ordner war nicht in der PyInstaller-Spec gebündelt → `t()` returned
  den Raw-Key statt der Übersetzung. Jetzt in `datas` aufgenommen.
  Betraf alle gebundelten Desktop-Apps seit v1.0.9.

### Changed
- **🍎 macOS-Distribution: DMG → PKG-Installer**. Mit `pkgbuild` +
  `productbuild` wird ein nativer macOS-Installer-Wizard gebaut, der
  die App automatisch nach `/Applications/` kopiert. Kein xattr-DMG-
  Mount-Tanz mehr — User klickt durch und ist fertig.
- **📖 README zweisprachig** — englische `README.md` ist jetzt Default
  (sichtbarer auf GitHub für internationale User), deutsche Anleitung
  unter `README.de.md`. Beide verlinken aufeinander via Badge oben.

### Added
- **⚡ Slash-Commands-Dropdown im Chat** — neuer Button rechts neben
  dem Austausch-Ordner-Picker. Klick öffnet eine kuratierte Liste der
  wichtigsten Hermes-CLI-Befehle:
  - **Sitzungsfluss**: `/new`, `/reset`, `/resume`, `/retry`, `/undo`,
    `/title`, `/compress`, `/branch`, `/fork`
  - **Hintergrund & Ziele**: `/background`, `/queue`, `/steer`, `/goal`, `/stop`
  - **Modelle, Tools, Skills**: `/model`, `/tools`, `/toolsets`,
    `/skills`, `/cron`, `/reload-mcp`, `/reload`, `/update`
  - **Info & Hilfe**: `/usage`, `/insights`, `/help`, `/quit`

  Befehle ohne Argument werden direkt abgeschickt; Befehle mit Argument
  (`/model …`) landen im Textfeld zum Vervollständigen.
- **🎤 Mikrofon-Button** ist jetzt ein klar erkennbares SVG-Mic-Icon
  statt Emoji.
- **🤖 Agent-Avatar im Chat** zeigt Roboter-Kopf statt 💜-Herz.
- **i18n weiter komplettiert**: Personality-Tab (Intro-Text +
  Memory-Dateien-Section), Skills-Tab (Section-Title + Search-Box-
  Placeholder), Slash-Button-Label, je 4 Sprachen.

### Notes — Ideen, die in v1.2.0+ landen
- **Wiki Semantic Search** (Embeddings + Vector DB) — größere Investition
- **OpenAPI/Swagger Docs** für die 60+ Endpoints
- **Update-Manager** (`git pull` + Restart von der Portal-UI aus)
- **Auto-Wiki-Mentions im Chat** (`@page-name` → Link)
- **Chat-Summary** (lange Verläufe zusammenfassen via LLM-Call)
- **Windows SmartScreen-Warning** — würde EV-Code-Signing-Cert
  (≈ 300 USD/Jahr) erfordern, für ein Open-Source-Projekt
  unverhältnismäßig
- **Briefcase-Migration** als Alternative zu PyInstaller (Plan v1.2.0)

---

## [1.1.2] — 2026-05-24

UX-Politur und mehr Übersetzungen.

### Added
- **Mobile-Padding**: Cards/Boxen kleben auf schmalen Viewports
  (`<768 px`) nicht mehr am Display-Rand — `5 px` Seitenrand am
  `.container` / `main`. Tablets im Querformat und Desktop unverändert.

### Changed
- **Settings → App-Tab** weiter auf `t()` umgestellt:
  - Connection-Sektion (Modus-Dropdown-Optionen, alle Field-Labels)
  - Identity-Sektion (User-Name, Agent-Name, Wiki-Kategorien)
  - Save-/Test-Buttons (alle „💾 Speichern" → `{{ t('common.save') }}`)
  - Status-Banner-Loading-Text
- **Cronjobs-Section-Title**: nutzt jetzt `t('cron.title')` +
  `t('cron.subtitle')` als kleines Untertitel.

### Notes
- JSON-Tables sind mittlerweile auf ~200 Keys pro Sprache ausgebaut
  (linter-/community-getriebene Ergänzungen). Restliche Templates
  (Skills-Tab, References-Tab, Cron-Modal, Explorer-Toolbar) folgen
  inkrementell — Keys sind teilweise schon da, nur das `{{ t() }}`-
  Wiring im Template fehlt noch.

---

## [1.1.1] — 2026-05-24

Drei UX-Korrekturen aus dem v1.1.0-Feedback plus i18n-Aufstockung
auf 276 Keys × 4 Sprachen (~1.100 Übersetzungen total).

### Fixed
- **Briefing-Seite jetzt wirklich „wie News/Aufgaben"** — vorher saß das
  Briefing in einem iframe mit Card-Border, oben drüber stand
  „☕ Briefing · Modus: ssh · …". Jetzt rendert `/briefing/` über
  `_serve_blog_file` direkt das Agent-HTML, der Portal-Header sitzt
  oben, dann gleich die Briefing-Überschrift (`📰 Tägliches Briefing —
  XX. Mai 2026`) — kein zusätzlicher Wrapper, kein iframe.
- **Chat-Editor-Hintergrund**: in v1.1.0 hatte ich denselben Farbwert
  wie vorher gesetzt (`#0f1115`) → optisch null Unterschied. Jetzt
  `#1a1d24` (= `--bg-secondary`, matched die File-Tree-Spalte rechts
  daneben) → Editor + Tree wirken als ein zusammenhängender Block.
  Plus tiefere Theme-Palette (Indent-Guides, Scrollbar-Active-Farbe).

### Added
- **Floating Action Buttons auf der Briefing-Seite** (bottom-right):
  „▶ Briefing jetzt erzeugen" (löst `POST /api/briefing/run` + auto-
  Reload nach Erfolg) und „🔄 Neu laden". Ersetzen die wegfallenden
  Toolbar-Buttons aus der alten briefing.html.
- **Briefing-Konfiguration** (GitHub-User, Wetter-Lat/Lon/TZ, BVG-Stop,
  Forum-RSS) als neue Section in **Settings → 🛰️ App** — vorher nur
  über das alte briefing.html erreichbar. Werte werden als ENV-Vars
  (`BRIEFING_*`) ans Briefing-Script weitergereicht.
- **i18n-Tables stark ausgebaut** auf 276 Keys × 4 Sprachen:
  - **Explorer**: Toolbar (Upload/Mkdir/Refresh/Up), Tabellen-Spalten
    (Name/Size/Modified/Actions), Mkdir-Prompt, Upload-States.
  - **Cronjob-Modal**: alle Felder (Name/Command/Prompt/Schedule), alle
    Preset-Buttons (Hourly/Daily/Weekly/Monthly/Custom), Status-Labels,
    Action-Buttons (Run/Pause/Resume/Delete).
  - **Personality/Skills/References/Usage/Support-Tabs**: Section-Titel,
    Intros, leere-Zustands-Texte, File-Beschriftungen.

### Notes
- **Mac-DMG bleibt vorerst tot**: User berichtet, dass NICHT MAL der
  Startup-Marker auf dem Desktop landet → Python startet nicht, der
  PyInstaller-Bootloader stirbt vor allem User-Code. Diagnostik aus
  der Ferne ohne macOS-Build-Maschine ist Sackgasse. **Workaround
  für mac-User**: bis v1.2.0 Docker-Variante nutzen, dort funktioniert
  alles. Plan v1.2.0 → Wechsel von PyInstaller auf **Briefcase**
  (Python's offizieller cross-platform packager mit getrennten Code-
  pfaden je OS — vermeidet die PyInstaller-Bootloader-Sackgasse).
- **Templates noch hardcodiert deutsch**: einige Detail-Strings im
  Wiki-Edit-Modus, Tags-Page, Search-Result-Page. Wer's braucht, kann
  die JSON-Keys einfach ergänzen — die Infrastruktur greift.

---

## [1.1.0] — 2026-05-24

Erstes Minor-Release seit 1.0. Briefing-Layout-Politur, Editor-Theme,
mehr Übersetzungen und Politur der Desktop-pywebview-Integration.

### Fixed
- **Briefing-iframe zeigte doppelten Header** — vom Agent gelieferte
  HTML enthält einen eigenen `<div id="site-header">` + `site-header.js`,
  die im iframe re-rendered wurden → zweite Nav-Leiste. Stripping in
  `api_briefing_render`: site-header-Placeholder, site-header.js-Script-
  Tags und alle `<header>`-Elemente werden entfernt, bevor das Portal-
  Stylesheet eingefügt wird. Plus `body > *:first-child {margin-top:0}`,
  damit die Briefing-Überschrift direkt am Top sitzt.
- **Chat-Editor optisch passend zum Portal** — Monaco-Theme `hermes-dark`
  bekommt jetzt vollständige Farbpalette (Hintergrund, Zeilennummern,
  aktive Zeile, Cursor, Selection, Gutter, Widgets, Scrollbar). Plus
  neues `hermes-light`-Theme das im Light-Mode aktiv wird. Farben sind
  abgeleitet aus `--bg-primary` / `--bg-secondary` der Portal-CSS-Variablen.

### Added
- **Mehr Übersetzungen**: Activity-Seite (Titel, Toolbar-Buttons, leerer
  Logfile-Hinweis).
- **pywebview-Integration robuster** in `entry_pyinstaller.py`:
  - Window-Titel enthält Version (`Hermes Portal v1.1.0`)
  - `background_color="#0f1115"` → keine weiße „Server-startet"-Phase
  - Plattform-spezifisches GUI-Backend explizit gesetzt:
    `cocoa` auf macOS (= native WKWebView via PyObjC),
    `edgechromium` auf Windows (= Edge WebView2, OS-Standard),
    Linux: pywebview wählt selbst (GTK oder QT je nach Installation)

### Changed
- **macOS-DMG-Build-Status**: Mit den v1.0.7-Fixes (`console=False`,
  Codesign-Integration im Spec, `sign_macos_app.py`) PLUS dieser
  Cocoa-GUI-Pinnung sollte die App jetzt endlich starten. Falls noch
  nicht: bitte das `~/Desktop/hermes-portal-started.txt`-Marker-File
  prüfen, dann gezielt debuggen.

### Notes — Verhältnis zu nesquena/hermes-webui
Der User hat auf <https://github.com/nesquena/hermes-webui> hingewiesen
und gefragt, wie dort SSH automatisch funktioniert. **Wichtig zu wissen**:
Das ist ein KOMPLETT ANDERES „Hermes". `hermes-webui` ist ein Web-Frontend
für **Snips/Hermes-MQTT** — das ist ein Voice-Assistant-Protokoll. Die
Komponenten kommunizieren über einen lokalen MQTT-Broker, deshalb braucht
es kein SSH. Unser **Hermes-Agent** ist ein CLI-Tool, das Dateien und
Cronjobs auf einer separaten Maschine verwaltet — SSH ist hier die
korrekte Transportwahl, weil's keinen MQTT-Daemon dafür gibt. Vergleichbar
wäre eher Portainer (Docker-Web-UI) ↔ Docker-Engine.

Was wir aus dem Vergleich übernehmen könnten:
- **mDNS-Discovery** auf dem LAN (Hermes-Agent broadcastet seine IP)
- **One-click SSH-Setup-Wizard** (bereits in Settings → 🛰️ App vorhanden,
  aber könnte glatter werden)
- **Auto-Detection** via gemeinsamen Mount-Pfad (bereits implementiert
  über `exchange_path`)

### Notes — Übersetzungs-Vollständigkeit
~80% der sichtbaren UI-Strings sind jetzt in 4 Sprachen. Noch nicht:
Cronjob-Modal (interne Felder), Explorer-Toolbar, einige Detail-Strings
im Chat-Empty-State, Settings-Personality/Skills/References-Tabs.
Inkrementell weiter; JSON-Keys ergänzen, Templates umstellen ist
mechanisch — Community-PRs willkommen.

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

[Unreleased]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.6...HEAD
[1.1.6]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.5...v1.1.6
[1.1.5]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.0.10...v1.1.0
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
