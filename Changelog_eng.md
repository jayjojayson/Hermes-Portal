# Changelog

All notable changes to this project are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
Versioning scheme: [SemVer](https://semver.org/).

> 🇩🇪 **Deutsche Version** → [CHANGELOG.md](CHANGELOG.md)

---

## [Unreleased]

### Added
- _(nothing yet)_

---

## [1.3.3] — 2026-05-28

🎨 **Settings UX polish: denser usage header, cleaner Identity-box layout,
extra-categories dropdown on all code paths.**

### Changed
- **📊 Usage tab header compacted** — the three separate rows (API
  Requests / Token Usage / Range Usage) now live in a 3-column grid
  with their own sub-headlines. Cards are more compact (95 px min
  instead of 140 px, smaller values, tighter gap). On wide screens all
  12 KPIs fit into one row instead of three. Blocks auto-stack on
  narrow screens.
- **👤 Identity box restructured** — two clearly separated rows:
  row 1 = `Your name` + `Agent name` (person names),
  row 2 = `Category: Entities` + `Category: Concepts` +
  `Extra wiki categories` (all three category labels together).
  The `wiki_extra_dirs` field moves out of the paths block into the
  Identity box where it belongs semantically.

### Fixed
- **🗂 New-page form: extra-categories dropdown** was invisible on POST
  error fallbacks (3 different `render_template` calls in
  `new_page()` didn't pass `extra_categories`). Now uniformly via the
  `_render_new()` helper — the dropdown is guaranteed visible on EVERY
  path (GET, empty title, existing URL, write error).

---

## [1.3.2] — 2026-05-26

📊 **Usage chart actually fixed + weekly/monthly usage + wiki multi-categories.**

### Fixed
- **📊 Usage tab bar chart now actually displays data** —
  v1.3.1 used `d.hourly[hk].total`, but the token hourlies live under
  `d.tokens.hourly[hk].total` (`.count` at top-level `d.hourly` are
  HTTP requests, not tokens). Tooltip now names all three values:
  `XX:XX — Y tokens · Z model calls · W HTTP requests`.

### Added
- **📅 Weekly + monthly usage cards** on the Usage tab — four new
  stat cards (tokens/calls × 7d/30d) aggregated from `agent.log` via
  the new endpoint `GET /api/settings/usage/range?days=N`. Loads
  in parallel to the day detail, cached separately.
- **🗂 Wiki multi-categories** via Settings → 🛰️ App →
  "Additional wiki categories" (comma-separated subdir names,
  e.g. `recipes, projects, todo`). Each folder is indexed, read and
  edited just like `concepts/`. **The 2-box layout of the
  wiki overview stays intact** — extras are counted into the
  "Concepts" box and shown as a small chip list with counts below it.
  The new-page form offers the extras as dropdown options, the
  backend validates against a whitelist (no path traversal).
- **🔧 `_coerce()`** now accepts JSON AND comma-separated strings for
  list fields (was JSON only). Useful for settings text fields the
  user types directly.

---

## [1.3.1] — 2026-05-26

🐛 **References-save bug + Usage tab chart styled like Dashboard.**

### Fixed
- **📁 References save: "File not found"** despite the file being open.
  Frontend was sending only the filename (`growbox-report.py`) in the
  `PUT /api/references/...` URL, but the backend resolver expects the
  `source_type/rel_path` key (`references/growbox-report.py`). Fix:
  - JS now tracks `_currentRefUrlKey` (routing key) alongside
    `_currentRefName` (display). Save/delete use the URL key.
  - URL path segments encoded individually instead of as a whole —
    the Flask route `<path:url_key>` needs slashes unquoted,
    otherwise nothing matches. (Hidden secondary bug that would have
    surfaced once subdirectories were used.)
  - Cache lookup by `url_key` instead of `name` (filenames are not
    unique across `source_types`).
  - Skills tab was unaffected (uses its own `POST` endpoint with
    `url_key` in the JSON body).
- **📊 Usage tab bar chart now matches the Dashboard widget** —
  shows token usage per hour (was request count) with a tooltip that
  names tokens AND requests, current hour fully opaque, the rest
  dimmed. Scales to the day's max value, minimum 2 % height so even
  quiet hours stay visible as a column.

---

## [1.3.0] — 2026-05-26

🛠 **Agent script bundle, RSS bridge, longer chat timeout.**

### Added
- **🛠 Bundled agent scripts (`blog_generator.py` + `daily_briefing.py`)**
  under `_wiki_server/templates/agent_scripts/`. Settings → 🛰️ App
  has a new "Agent scripts (one-click install)" box — clicking
  *Install* copies the script via local FS or SFTP onto the
  Hermes Agent (default paths: `blog/blog_generator.py` and
  `scripts/daily_briefing.py`). Existing scripts are only overwritten
  with explicit confirmation.
- **🔌 ENV bridge Portal → agent scripts** — `cfg.portal_env()` sets
  the following on cronjob invocation:
  - `PORTAL_BLOG_DIR`, `PORTAL_POSTS_SUBDIR`,
    `PORTAL_AGENT_NAME`, `PORTAL_USER_NAME`
  - `NEWS_RSS_FEEDS` (full RSS list as JSON)
  This way the default scripts **automatically** use the RSS feeds
  configured in the Portal — no code tweaks needed.
- **⏱ Chat response timeout configurable** (new settings field
  `chat_timeout_sec` in Settings → 🛰️ App, default 300 s = 5 min,
  max 1800 s). Backend uses the value for `client.hermes(["-z", …])`.
  Plus: on timeout the chat now shows a clear multi-line explanation
  with a direct link into Settings instead of "Try a shorter message"
  (which was misleading — the problem was response time, not message
  length).
- **📖 README update (en + de)** — a "Setup in 2 clicks" section for
  News that explains the new agent-script installation from the
  Settings tab.

### Fixed
- **🌐 Misleading RSS hint** in the App tab corrected. Previously:
  "RSS feeds … NOT automatically passed to your news generator".
  Now: the Portal **does** pass the feeds through — as long as you
  use the bundled `blog_generator.py`.

---

## [1.2.2] — 2026-05-25

📂 **News detail pages via posts/ subdir, pagination, subdir setting.**

### Added
- **📄 Pagination on the news overview** — 9 entries per page,
  prev/next + page numbers centred below, "«" jumps to the first,
  "»" to the last. Soft scroll to top on page change.
  Translated to en/de/es/fr.
- **⚙️ Settings → 🛰️ App → Blog posts subdir** — new field
  `blog_posts_subdir` (default `"posts"`). If your structure is
  flat, leave the string empty.

### Fixed
- **🔗 Click on news card → 404 because of wrong path** — the
  Hermes Agent blog generator places per-day reports under
  `BLOG_DIR/posts/<file>.html`, but the Portal was looking directly
  under `BLOG_DIR/`. As of v1.2.2:
  - `_post_detail_url` builds slug URLs as `/blog/<posts_subdir>/<slug>.html`
    (instead of `/blog/<slug>.html`).
  - The `/blog/<filename>` route falls back to `posts/<filename>` if
    the file isn't at top level — works both locally and over SSH
    (via `client.exists`).
  Existing user setups with the "posts" subdir keep working without
  config changes since that's the default.

---

## [1.2.1] — 2026-05-25

🖼 **News cards with hero images + functional detail links.**

### Fixed
- **📰 News cards have images back** — v1.2.0 rendered a bare text
  grid because the backend was only forwarding
  `title/url/summary/category/source` from `posts.json`. As of v1.2.1
  the backend pulls every common image field (`image`, `cover`,
  `thumb`, `hero`, `og_image`, …), categories as a list, tags, and
  resolves relative paths to `/blog/<asset>`. Cards now show a 16:9
  hero (or a placeholder gradient + 📰 icon if the post has no image).
- **🔗 Card clicks open the daily report detail page** — previously
  the click opened the news overview in a new tab because I had set
  `target="_blank"` on the title link and only used the first random
  URL from `posts.json` (often the external source) as href. Now:
  - The entire card is `<a>` (larger click target)
  - Backend supplies `detail_url` from `path`/`filename`/`slug` and
    resolves to `/blog/<file>.html` (the morning/noon/evening reports
    formatted by the Hermes Agent)
  - No more `target="_blank"` — navigates in the same tab
  - The original source stays as `source_url` separately in the
    payload, in case a "🔗 original article" button is added later

---

## [1.2.0] — 2026-05-25

📰 **Portal-native news page, status-pill fix, chat welcome i18n,
cronjob edit truncation fix, update diagnose in support tab,
clean Mac desktop.**

### Added
- **📰 News page completely Portal-native** (`/news/`) — own template
  replaces the previously Hermes-Agent-generated `/blog/index.html`.
  - Card grid with title, date, category, summary, source.
  - Reload button + live counter.
  - Collapsible cron note below with copy/paste prompt for
    `blog_generator.py` (recommendation: 3× per day morning/noon/evening).
  - List of configured RSS feeds from Settings (direct link to the
    App tab for editing).
  - When `posts.json` is empty, automatic open of the cron note plus
    a friendly hint instead of a 404.
  - Fully translated in en/de/es/fr (15 new i18n keys).
- **🔍 Update check diagnose** in the Support tab — collapsible box
  shows the raw `/api/version/check` JSON including the `error`
  field. Users can see directly whether the API call works or why
  no update banner appears.
- **📖 README block "News page — Hermes fetches your RSS feeds"**
  (en + de) parallel to the existing tasks-cronjob hint.
- **2–4h frequency recommendation** in the cron hint of the tasks page.

### Fixed
- **🌐 Hermes status pill** no longer shows `hermes.status.online` as
  the raw key — the i18n keys had accidentally dropped during refactor.
  Now correctly "Hermes online / idle / offline / no signal" in all
  4 languages.
- **💬 Chat welcome screen fully translated** — intro "I'm %agent% —
  your personal chat …" and all 4 quick-action boxes
  (Explore the Wiki / Recent activity / Offer help / Blank chat)
  now run through `t()`. Quick prompts also localized in
  English/Spanish/French (12 new i18n keys).
- **⏰ Cronjob edit: full prompt visible** — on edit
  `job.command || job.prompt` was loaded, but `command` is truncated
  to 120 characters on the backend for the list display. Frontend
  now uses `job.prompt || job.command` (prompt contains the full text).

### Changed
- **🍎 Clean Mac desktop** — `hermes-portal-started.txt` and
  `hermes-portal-trace.log` are no longer written to the desktop by
  default. Re-enable with `HP_DEBUG=1` env var at startup (for
  future startup-crash diagnostics).
- **📰 Nav link "News"** now points to `/news/` (Portal route)
  instead of `/blog/`. Active state detection recognises both as
  the "news" page.

---

## [1.1.9] — 2026-05-25

🎯 **Portal-native tasks page, Mac update banner fix, status-pill i18n,
cronjob editor with full prompt view.**

### Added
- **✅ Tasks page completely Portal-native** (`/aufgaben/`) — own
  template replaces the previously Hermes-Agent-generated
  `aufgaben.html`. Hermes Agent no longer needs to generate anything,
  the page works directly after installation. Features:
  - Prominently at the top: "➕ Add task" form with title,
    assignee dropdown (Agent vs. User) and optional description.
    Auto-sync straight to `aufgaben.md` — no extra sync button.
  - Lists split into "Open" / "Done"; checkbox click moves the task
    to the other section and updates the status in the markdown file.
  - 🗑 per row cleanly removes the task from `aufgaben.md`.
  - Collapsible box with a copy/paste cron prompt for the Hermes
    Agent (`{path}` / `{agent}` / `{user}` are substituted with the
    real values).
  - Fully translated in en/de/es/fr (14 new i18n keys).
- **🌐 Hermes status pill translated** — "Hermes online / idle /
  offline / no signal" at top right of the dashboard now runs
  through `t()`.
- **📖 README block "Tasks page — Hermes does the work"** (en + de)
  explains the interplay Portal ↔ aufgaben.md ↔ Hermes cronjob and
  ships the pre-built prompt template.

### Fixed
- **🍎 Mac update banner finally appears** — `urllib.request.urlopen`
  in the PyInstaller build had no system CA bundle and silently
  failed on the HTTPS call to api.github.com (which kept
  `update_available=False` and the banner invisible). Fix: `certifi`
  bundle added to requirements + explicitly passed as SSL context.
- **⏰ Cronjob editor shows the full prompt** — textarea enlarged
  from 4 to 14 rows (`min-height: 16rem`), modal width extended to
  760 px, monospace + vertical resize. Multi-line prompts (e.g. the
  tasks cronjob with its "IMPORTANT" list) are now fully readable
  and editable.
- **🔘 Wiki "New entry" button** no longer takes the full box width
  (`align-self: flex-start; width: auto`).

### Removed
- **🚮 Agent-generated aufgaben.html no longer expected** — the
  nav link "Tasks" now points to `/aufgaben/` (Portal-native route);
  legacy `/blog/aufgaben.html` calls are still recognised as the
  "aufgaben" page in the site-header active state, but the page
  itself is rendered by the Portal, not by the agent.

---

## [1.1.8] — 2026-05-24

🎯 **Update banner, tasks out-of-the-box, Windows without terminal,
private-key reveal + smaller UX bug fixes.**

### Added
- **🚀 Update banner everywhere** — floating toast at top right on
  every page when a newer Hermes Portal version is published on
  GitHub (user request: "The Mac app didn't show me the update to
  the new version"). The click link goes to the release page, "✕"
  dismisses for that specific version (localStorage). The backend
  endpoint `/api/version/check` with 1h cache already existed —
  only the UI was missing.
- **🔐 Show private key for migration** — new "Reveal private key"
  button under Settings → 🛰️ App → SSH wizard. Collapsible warning
  panel with confirmation, then a plain-text textarea + copy button.
  Lets you copy the Portal's own SSH key to other devices without
  touching the agent's `authorized_keys`. Endpoint:
  `POST /api/settings/app/ssh/reveal`.
- **📋 Tasks page works immediately** — a default `aufgaben.md` is
  automatically created in `BLOG_DIR/aufgaben.md` if missing
  (template: `_wiki_server/templates/aufgaben_default.md`). If the
  Hermes Agent hasn't generated `aufgaben.html`, the Portal now
  shows its own usable tasks page with the "➕ Add task" form at
  the top — auto-sync to `aufgaben.md`, no separate sync button
  anymore.
- **⬅️ Sidebar opens via a clickable arrow button** — replaces the
  invisible hover strip at the left edge that accidentally opened
  when reaching for HA's own sidebar in the Home Assistant frontend.
  The click button is unambiguous + visually present.

### Fixed
- **💬 Chat input clears after send** — previously the text stayed
  in (cosmetic bug since v1.0).
- **🌐 Dashboard empty states translated** — "No upcoming job",
  "No news available.", "No tasks found.", "No wiki entries yet.",
  "No Hermes log file reachable." + sidebar "nothing yet" + chat
  sessions empty list now run through `t()` and follow the UI
  language (en/de/es/fr).
- **🪟 Windows: no terminal window** anymore on double-click of the
  app (PyInstaller spec: `console=False` now also for `win32`,
  previously only `darwin`).

### Removed
- **🚮 Slash command dropdown in chat** removed (user request: "Since
  the CLI commands in chat don't work, let's remove this feature
  entirely"). The button next to the folder picker is gone, along
  with the dropdown markup + JS. Slash commands can still be typed
  manually and sent natively to the agent — they are no longer
  Portal-side intercepted or offered as a quick selection.

---

## [1.1.7] — 2026-05-24

🔑 **SSH key paste import + Settings save bar i18n + README consolidation.**

### Added
- **📥 Import SSH key instead of generating one** — new button in the
  SSH wizard (Settings → 🛰️ App): paste an existing private key via
  copy/paste, the Portal automatically derives the public key (via
  `cryptography` lib) and stores both under `/data/.ssh/id_ed25519`(.pub).
  Use case: use the same identity on multiple Portal installations
  without having to update `authorized_keys` on the Hermes Agent each
  time.
  - Backend endpoint: `POST /api/settings/app/ssh/import`
    (body: `{private_key, public_key?, overwrite, comment}`)
  - Validates BEGIN/END PEM markers, returns 409 if the key exists
    and `overwrite=false`.
  - UI: collapsible box with two textareas + overwrite checkbox,
    translated in 4 languages.

### Fixed
- **💾 Settings save bar fully translated** — the floating box at the
  bottom of the Settings page showed "Unsaved changes / Click 'Save'
  or Ctrl/Cmd+S" hard-coded in German, even when the UI was English.
  All strings (title, hint, "Saved" confirmation, test connection
  button) now run through `t()`.
- **🌐 i18n: 9 new keys** for SSH import in en/de/es/fr.

### Documentation
- **README merge**: `Installproces.md` folded into `README.md`
  (English, default) and `README.de.md` — full troubleshooting table
  (Portal/SSH/Monaco/Wiki/Docker/macOS PKG/Windows SmartScreen/HA
  container) plus a first-time configuration table with all
  App settings. Includes architecture ASCII diagram. Standalone
  file deleted.

---

## [1.1.6] — 2026-05-25

🎯 **Mac app finally launches!** Plus a Find-IP improvement for HA
containers and wiki layout polish.

### Fixed
- **🍎 macOS PKG: Python framework path corrected** — the bootloader
  looks for Python under `Contents/Frameworks/Python` (macOS
  convention), but we had it under `Contents/MacOS/_internal/Python`.
  That caused the `[PYI-15449:ERROR] Failed to load Python shared
  library` crash on launch. Fix: PyInstaller's `BUNDLE` step in
  `hermes_portal.spec` now builds the `.app` itself with the correct
  macOS structure (including Resources↔Versions symlinks). The
  workflow step "manually assemble .app from dist" goes away.
- **📁 Wiki import/export layout** — import button + category
  dropdown on row 1, export button standalone on row 2 (previously
  all on one row + the dropdown overflowed the box edge). The dropdown
  now scales to the container width with `max-width: 100%`.

### Changed
- **🔎 Find IP understands containers** — automatically detects when
  the Portal runs inside a Docker/HA add-on subnet (172.16-31.x.x)
  and therefore can't see the user's LAN. Shows a clear warning +
  offers a manual subnet input field ("e.g. 192.168.178"). Explains
  the problem in 4 languages.

### Notes — Slash commands
The user reports: `/new` starts a new session, but `/usage` and
`/reset` produce hallucinated LLM answers. That's **agent-side**: the
Hermes CLI treats some slash commands as special instructions (e.g.
`/new` triggers a session reset in the wrapper), others it passes
through as a normal prompt to the LLM. The Portal sends ALL slash
commands unchanged to the agent — answer quality depends on the
agent setup. Workaround: ask the agent maintainer to handle
`/usage` / `/reset` etc. also in `-z` mode (instead of REPL only).

### Notes — Mac diagnose success
The `~/Desktop/hermes-portal-trace.log` from v1.1.5 pinpointed the
cause neatly: the bootloader error was clearly in the first phase
(before Python init), exactly what we suspected. BUNDLE in the spec
file is the exact repair PyInstaller offers for that.

---

## [1.1.5] — 2026-05-25

Slash command revert + LAN discovery + wiki IO layout + Support tab i18n
+ aggressive Mac trace logging.

### Changed
- **Slash commands go natively to the Hermes Agent.** Portal-side
  interceptors from v1.1.4 are entirely gone. `/new`, `/reset`,
  `/usage`, `/help` etc. are now sent to the agent unchanged like any
  other chat message — the agent responds accordingly. If the answer
  seems hallucinated, blame it on the agent's invocation pattern
  (`hermes -z` vs. REPL mode), not the Portal.
- **Wiki import/export**: import button + category dropdown + export
  button on desktop in **one row** (previously two). Wraps only
  below 520 px (phone portrait).

### Added
- **🔎 "Find IP" button** in Settings → 🛰️ App → Connection. Scans
  the local `/24` subnet for SSH-capable hosts (port 22 open), shows
  the hits with hostname (reverse DNS), click transfers the IP into
  the agent host field. New endpoint `/api/settings/app/discover`.
- **Support tab fully i18n'd** in 4 languages: section titles
  (Support / GitHub & Community / Version), intro text, all
  card descriptions.
- **📦 Version info section in the Support tab** with update check
  (same API as the sidebar footer badge). Shows current version + an
  ⬆ link to the release page when an update is available.
- **🔍 Step-by-step Mac trace logging** in `entry_pyinstaller.py`:
  every startup step is written to `~/Desktop/hermes-portal-trace.log`.
  On a crash, the last line shows WHERE exactly it died — bootloader,
  imports, server thread, pywebview init, or only at the
  `webview.start()` call.

### Deferred
- **🗂 Additional wiki categories** (request from this round) —
  goes into v1.2.0: needs refactoring `/entity/<id>` and
  `/concept/<id>` to a generic `/category/<key>/<id>` route plus a
  UI to add/manage them in Settings → App → Identity.
- **News/Briefing/Tasks page subtitle**: that's **agent-generated
  content** from your blog HTML (`/blog/index.html` etc.). The Portal
  only strips the header and injects its CSS, the body content
  (title + subtitle) comes 1:1 from your `daily_news.py` / blog
  generator. Translation belongs there, not in the Portal.

### Notes — Mac PKG diagnostics
With the new trace file we're closing in on the silent app death.
After install + launch attempt, please check
`~/Desktop/hermes-portal-trace.log` and send the content — then I'll
see exactly whether it's `pywebview.start()`, a library loading
error, or earlier.

---

## [1.1.4] — 2026-05-25

Slash commands made smart, SSH wizard fully translated,
Mac pywebview crash now has a browser fallback.

### Fixed
- **Slash commands were being hallucinated by the LLM** — the Hermes
  CLI only handles slash commands in REPL mode. When we shell with
  `hermes -z "/usage"`, the model sees the text as a normal prompt
  and answers creatively ("Hold on, I don't have a tool for stats
  handy right now…"). Fix: Portal-side slash handlers in
  `chat.html` — the most important commands are caught locally:
  - `/usage`, `/insights` → link to Settings → 📊 Usage
  - `/new`, `/reset` → starts a new chat session
  - `/stop` → triggers the stop button (or hint if nothing's running)
  - `/help` → shows the list of all available slash commands inline
  - `/quit` → hint that the server keeps running
  Other commands (`/model`, `/tools`, …) still go as text to the
  agent.

- **macOS pywebview no longer dies silently** — `webview.start()` is
  wrapped in try/except. On a WKWebView init error or other runtime
  crashes it falls back to browser mode instead of silently quitting
  the app. The user sees in the terminal log what happened.

### Changed
- **SSH wizard fully translated** (Settings → 🛰️ App):
  - "Copy public key" / "Regenerate" / "Copy prompt" / "Copied!"
  - Collapsible help texts "Manually: how to install the key…" +
    "Automatically: prompt to the Hermes Agent…"
  - 5 manual steps, all sub-strings
  - 4 languages × 17 new keys = 68 new translations
- **i18n tables now 308 keys × 4 languages** (from 280 in v1.1.3)

### Notes — Mac crash diagnose
If the PKG-installed app produces `~/Library/Logs/DiagnosticReports/`
crash reports, please send me the content of a `hermes-portal*.ips`.
With the new browser fallback at least it should now become visible
what's going wrong — Console.app → Process: hermes-portal shows the
stderr output.

---

## [1.1.3] — 2026-05-25

Mega update: macOS PKG, slash commands dropdown, robot avatar, new
default English README, full i18n bug fix for Windows.

### Fixed
- **🔴 "Dashboard.Hermes" bug on Windows/Mac bundles** — the `i18n/`
  folder was not bundled in the PyInstaller spec → `t()` returned the
  raw key instead of the translation. Now added to `datas`. Affected
  all bundled desktop apps since v1.0.9.

### Changed
- **🍎 macOS distribution: DMG → PKG installer**. With `pkgbuild` +
  `productbuild` we build a native macOS installer wizard that
  automatically copies the app to `/Applications/`. No more
  xattr-DMG-mount dance — the user clicks through and is done.
- **📖 Bilingual README** — English `README.md` is now the default
  (more visible on GitHub for international users), German guide
  under `README.de.md`. Both link to each other via a badge at the
  top.

### Added
- **⚡ Slash commands dropdown in chat** — new button next to the
  exchange folder picker. A click opens a curated list of the most
  important Hermes CLI commands:
  - **Session flow**: `/new`, `/reset`, `/resume`, `/retry`, `/undo`,
    `/title`, `/compress`, `/branch`, `/fork`
  - **Background & goals**: `/background`, `/queue`, `/steer`, `/goal`, `/stop`
  - **Models, tools, skills**: `/model`, `/tools`, `/toolsets`,
    `/skills`, `/cron`, `/reload-mcp`, `/reload`, `/update`
  - **Info & help**: `/usage`, `/insights`, `/help`, `/quit`

  Commands without arguments are sent directly; commands with
  arguments (`/model …`) land in the textfield for completion.
- **🎤 Microphone button** is now a clearly recognisable SVG mic icon
  instead of an emoji.
- **🤖 Agent avatar in chat** shows a robot head instead of a 💜 heart.
- **i18n further completed**: Personality tab (intro text + memory
  files section), Skills tab (section title + search box placeholder),
  slash button label, all 4 languages.

### Notes — ideas landing in v1.2.0+
- **Wiki semantic search** (embeddings + vector DB) — bigger
  investment
- **OpenAPI/Swagger docs** for the 60+ endpoints
- **Update manager** (`git pull` + restart from the Portal UI)
- **Auto wiki mentions in chat** (`@page-name` → link)
- **Chat summary** (summarize long conversations via LLM call)
- **Windows SmartScreen warning** — would require an EV code signing
  cert (≈ 300 USD/year), disproportionate for an open-source project
- **Briefcase migration** as an alternative to PyInstaller (plan
  v1.2.0)

---

## [1.1.2] — 2026-05-24

UX polish and more translations.

### Added
- **Mobile padding**: cards/boxes on narrow viewports (`<768 px`)
  no longer stick to the display edge — `5 px` side padding on
  `.container` / `main`. Tablets in landscape and desktop unchanged.

### Changed
- **Settings → App tab** further moved to `t()`:
  - Connection section (mode dropdown options, all field labels)
  - Identity section (user name, agent name, wiki categories)
  - Save/Test buttons (all "💾 Save" → `{{ t('common.save') }}`)
  - Status banner loading text
- **Cronjobs section title**: now uses `t('cron.title')` +
  `t('cron.subtitle')` as a small subtitle.

### Notes
- JSON tables are now built out to ~200 keys per language
  (linter/community-driven additions). The remaining templates
  (Skills tab, References tab, Cron modal, Explorer toolbar) follow
  incrementally — keys are partially there already, only the
  `{{ t() }}` wiring in the template is missing.

---

## [1.1.1] — 2026-05-24

Three UX corrections from the v1.1.0 feedback plus i18n boost to
276 keys × 4 languages (~1,100 translations total).

### Fixed
- **Briefing page really like News/Tasks now** — previously the
  briefing sat in an iframe with a card border, with
  "☕ Briefing · Mode: ssh · …" above it. Now `/briefing/` renders
  via `_serve_blog_file` directly to the agent HTML, with the Portal
  header at the top, then immediately the briefing headline
  (`📰 Daily Briefing — May XX, 2026`) — no extra wrapper, no iframe.
- **Chat editor background**: in v1.1.0 I had set the same colour
  value as before (`#0f1115`) → visually no difference. Now `#1a1d24`
  (= `--bg-secondary`, matches the file tree column to the right
  next to it) → editor + tree feel like one connected block. Plus
  a deeper theme palette (indent guides, scrollbar active colour).

### Added
- **Floating action buttons on the briefing page** (bottom right):
  "▶ Generate briefing now" (triggers `POST /api/briefing/run` +
  auto-reload on success) and "🔄 Refresh". Replace the toolbar
  buttons that go away with the old briefing.html.
- **Briefing configuration** (GitHub user, weather lat/lon/TZ,
  BVG stop, forum RSS) as a new section in **Settings → 🛰️ App** —
  previously only reachable via the old briefing.html. Values are
  passed as ENV vars (`BRIEFING_*`) to the briefing script.
- **i18n tables strongly expanded** to 276 keys × 4 languages:
  - **Explorer**: toolbar (Upload/Mkdir/Refresh/Up), table columns
    (Name/Size/Modified/Actions), Mkdir prompt, upload states.
  - **Cronjob modal**: all fields (Name/Command/Prompt/Schedule),
    all preset buttons (Hourly/Daily/Weekly/Monthly/Custom), status
    labels, action buttons (Run/Pause/Resume/Delete).
  - **Personality/Skills/References/Usage/Support tabs**: section
    titles, intros, empty-state texts, file labels.

### Notes
- **Mac DMG remains dead for now**: user reports that NOT EVEN the
  startup marker lands on the desktop → Python doesn't start, the
  PyInstaller bootloader dies before any user code. Diagnosis from
  afar without a macOS build machine is a dead end. **Workaround
  for Mac users**: use the Docker variant until v1.2.0, everything
  works there. Plan v1.2.0 → switch from PyInstaller to
  **Briefcase** (Python's official cross-platform packager with
  separate code paths per OS — avoids the PyInstaller bootloader
  dead end).
- **Templates still hard-coded German**: some detail strings in
  the wiki edit mode, tags page, search result page. Whoever needs
  it can simply add the JSON keys — the infrastructure is in place.

---

## [1.1.0] — 2026-05-24

First minor release since 1.0. Briefing layout polish, editor theme,
more translations and polish of the desktop pywebview integration.

### Fixed
- **Briefing iframe showed a duplicate header** — the agent-delivered
  HTML contains its own `<div id="site-header">` + `site-header.js`,
  which got re-rendered in the iframe → a second nav bar. Stripping
  in `api_briefing_render`: site-header placeholder, site-header.js
  script tags and all `<header>` elements are removed before the
  Portal stylesheet is injected. Plus `body > *:first-child {margin-top:0}`
  so the briefing headline sits directly at the top.
- **Chat editor visually aligned with the Portal** — the Monaco theme
  `hermes-dark` now has a full colour palette (background, line
  numbers, active line, cursor, selection, gutter, widgets,
  scrollbar). Plus a new `hermes-light` theme that activates in light
  mode. Colours are derived from `--bg-primary` / `--bg-secondary`
  of the Portal CSS variables.

### Added
- **More translations**: activity page (title, toolbar buttons, empty
  logfile hint).
- **pywebview integration more robust** in `entry_pyinstaller.py`:
  - Window title contains the version (`Hermes Portal v1.1.0`)
  - `background_color="#0f1115"` → no white "server-starting" phase
  - Platform-specific GUI backend explicitly set:
    `cocoa` on macOS (= native WKWebView via PyObjC),
    `edgechromium` on Windows (= Edge WebView2, OS default),
    Linux: pywebview picks itself (GTK or QT depending on installation)

### Changed
- **macOS DMG build status**: With the v1.0.7 fixes (`console=False`,
  codesign integration in the spec, `sign_macos_app.py`) PLUS this
  cocoa GUI pinning, the app should now finally start. If not: please
  check the `~/Desktop/hermes-portal-started.txt` marker file, then
  debug targeted.

### Notes — Relationship to nesquena/hermes-webui
The user pointed at <https://github.com/nesquena/hermes-webui> and
asked how SSH automatically works there. **Important to know**:
That's a COMPLETELY DIFFERENT "Hermes". `hermes-webui` is a web
frontend for **Snips/Hermes-MQTT** — a voice assistant protocol. The
components communicate via a local MQTT broker, which is why no SSH
is needed. Our **Hermes Agent** is a CLI tool that manages files and
cronjobs on a separate machine — SSH is the correct transport choice
here, because there is no MQTT daemon for it. The closest analogy
would be Portainer (Docker web UI) ↔ Docker engine.

What we could take from the comparison:
- **mDNS discovery** on the LAN (Hermes Agent broadcasts its IP)
- **One-click SSH setup wizard** (already in Settings → 🛰️ App,
  but could be smoother)
- **Auto detection** via a shared mount path (already implemented
  via `exchange_path`)

### Notes — translation completeness
~80% of the visible UI strings are now in 4 languages. Not yet:
cronjob modal (internal fields), Explorer toolbar, some detail
strings in the chat empty state, Settings Personality/Skills/References
tabs. Continuing incrementally; adding JSON keys, switching templates
is mechanical — community PRs welcome.

---

## [1.0.10] — 2026-05-24

Four concrete HA fixes (briefing style, chat editor, i18n mix-up,
time zones) plus more template translations.

### Fixed
- **Briefing iframe in HA**: agent-delivered HTML had hard-coded
  `/blog/style.css` and `/blog/site-header.js` — they ran without
  ingress prefix against the HA origin → 404. `api_briefing_render`
  now rewrites all absolute `/` URLs and additionally injects our
  Portal stylesheet so cards/colours look consistent with the rest
  of the UI. Plus: iframe height to `calc(100vh - 220px)`, internal
  scrollbar almost always gone.
- **Chat editor empty, `loader.js 404`**: Monaco loader script tag
  in `chat.html` used a hard-coded `/static/...` path. The DOM
  patcher in `base.html` rewrites dynamically, but for `<script>`
  tags too late — the browser had already fired the 404. Fix:
  `{{ url_for() }}` server-side so the path is correct ALREADY at
  render time.
- **Language mix after language switch**: after saving in Settings
  → 🌐 Language, the page now automatically reloads
  (`location.reload()`) so the new i18n bundle takes effect
  everywhere immediately. Previously you had to manually switch
  pages, and some i18n'd templates still showed the old language →
  felt like a wild mix.
- **Settings Cronjobs showed UTC as local**: the old code stripped
  `+00:00` from the ISO timestamp and treated the rest as local —
  so `16:00 UTC` was displayed as "16:00 local" instead of correctly
  "18:00" (UTC+2). Fix: new helper `window.formatLocalTime()`, which
  assumes missing TZ as UTC (Hermes convention) and cleanly converts
  to the browser TZ.

### Added
- **🕐 Time zone helpers in `base.html`**:
  - `window.formatLocalTime(iso)` — UTC ISO → user browser local
    string in the active UI language
  - `window.userTimezone()` — e.g. `"Europe/Berlin"`
  - `window.userTzOffset()` — e.g. `"UTC+02:00"`
- **TZ hint in Settings → Cronjobs toolbar**: subtly shows the
  browser time zone (e.g. "🕐 UTC+02:00 · Europe/Berlin") with a
  tooltip that explains: cron patterns are interpreted by the agent
  in its time zone (UTC), the columns "Next/Last run" in your
  browser TZ.
- **Dashboard cronjob tile**: the tooltip on the time pill now
  shows the absolute local time in addition to the relative one
  ("in 2h 15min").

### Changed
- **More templates switched to `t()`**:
  - **Chat** (`chat.html`): session list, search, empty state
    greeting, input field placeholder, all toolbar buttons
    (🎤/📎/📁/📂), send button labels.
  - **Briefing** (`briefing.html`): header, "Generate now"/"Refresh"
    buttons, config block titles, GitHub/weather/time zone fields.
  - **Wiki index** (`index.html`): wiki search box, import/export
    card.

### Notes
- **Recommendation regarding time zone solution**: browser TZ is a
  95% solution without any configuration. If someone runs the Portal
  container in a different TZ than their browser (rare, e.g. calling
  the HA host time from a smartphone), a TZ override could be added
  in Settings later. Currently: not necessary, the browser knows its
  TZ reliably.

---

## [1.0.9] — 2026-05-23

i18n full-build release. Translation tables expanded to ~150 keys
per language (× 4 languages = ~600 translations), Dashboard +
Settings + Blog-Missing page fully moved to the `t()` helper.

### Added
- **Complete translations** for all 4 languages (en/de/es/fr)
  including:
  - **Dashboard**: greetings (time-of-day-dependent), Hermes card,
    system card (CPU/RAM/Disk/Logfile), quick prompt, cronjobs box,
    token usage, news, wiki recent, activity preview.
  - **Settings → 🛰️ App**: all sections (Language, Visibility,
    Identity, Connection, Paths), all field labels, all help texts
    (folder structure explanation, briefing template tip, RSS
    behaviour).
  - **Settings tabs**: Cronjobs, Personality & Memory, Skills,
    References, Usage, App, Support.
  - **Blog-Missing page**: fully translated (title, body, causes,
    hide hint).
  - **Common strings**: Save/Cancel/Delete/Edit/New/Reload/Search/…
    plus "Loading…", "No data", "Never", "Today" etc.
- **Greeting logic** in `dashboard.html` now uses `window.t()` with
  fallback on time-of-day-specific keys
  (`greeting.morning/afternoon/evening/night`).

### Changed
- **JSON tables** in `_wiki_server/i18n/{en,de,es,fr}.json` boosted
  from ~30 to ~150 keys. Each new key not yet translated in a
  language automatically falls back to the English value (and then
  the key name). That way the UI stays usable while community
  translations come in later.

### Notes
- **Templates not yet fully switched**: index.html (Wiki),
  chat.html (inner UI), briefing.html (Settings block), activity.html,
  explorer.html — they partially still use hard-coded German strings.
  But the JSON keys are already there → community PRs to switch are
  welcome, no code change needed, just
  `<text>` → `{{ t('xyz') }}`.
- **Switch language**: Settings → 🛰️ App → 🌐 Language. After save
  the page reloads automatically and the new language takes effect.

---

## [1.0.8] — 2026-05-23

Two HA bug fixes (briefing iframe, chat editor) + big step towards
multilingual. Makes the Portal finally usable for non-German users.

### Added
- **🌐 Multilingual UI** — language selectable in Settings →
  🛰️ App → "Sprache · Language · Idioma · Langue".
  - **English (default), German, Spanish, French** — new installs
    now start in English (because most users understand it),
    existing users keep their previous language.
  - Translations live as flat JSON tables in `_wiki_server/i18n/`
    — community contributions via PR welcome (new language = new
    `<code>.json` file, automatically appears in the switcher).
  - Currently translated: nav labels, settings tab titles, standard
    buttons (Save/Cancel/…). The remaining strings follow piece by
    piece.
  - JS side via `window.t('nav.dashboard')` helper + `window.HP_I18N`
    lookup table in `base.html`.
- **`_wiki_server/i18n.py`** — lightweight translation module (no
  Babel/gettext overhead), fallback order: `lang → en → key`.
- **`_wiki_server/templates/briefing_default.html`** — example
  template for your own briefing HTML. Users can copy this to their
  agent as a starting point and base their `daily_briefing.py` on it.
- **Help box "Recommended folder structure"** in Settings →
  🛰️ App → Paths section. Explains the
  `<exchange>/wiki/{scripts,blog}/` structure, refers to
  `briefing_default.html`, clarifies RSS feed behaviour (Portal feed
  ≠ news generator feed of the agent).

### Fixed
- **Briefing page showed 404** in HA —
  `<iframe src="/api/briefing/render">` was hard-coded, the v1.0.6
  patcher had not included `<iframe>` in its selector list. Now the
  template uses `url_for(...)`, plus the patcher knows
  `iframe`/`source` as additional selectors.
- **Chat editor stayed empty** with `TypeError: Cannot read
  properties of null (reading 'then')` — the Monaco AMD loader had
  a hard-coded path `paths: { vs: '/static/vendor/monaco/vs' }`, so
  under ingress it loaded all modules against the HA origin → 404
  → `monaco.editor` undefined → `MONACO_READY` stayed `null`.
  Now: `paths: { vs: window.hpUrl(...) }`.

### Notes
- **macOS DMG**: excluded from the test loop — for v1.1.0 we're
  switching entirely to a native pywebview window architecture, the
  browser-plus-terminal hybrid build from v1.0.x becomes obsolete.
- **RSS feeds in Settings ≠ news generator feeds**: the help box
  now documents this explicitly. The Portal stores the feed list in
  `config.json`, but only passes `briefing_forum_rss` as an ENV var
  to your briefing script. For news generation you still need to
  manually maintain your agent-side `daily_news.py`.

---

## [1.0.7] — 2026-05-23

Real native desktop app experience on macOS and Windows — no more
browser tab, no terminal window. Plus PyInstaller bootloader fix for
macOS Finder launch.

### Changed
- **`console=False` for the macOS build** in `hermes_portal.spec`.
  The PyInstaller bootloader silently crashed on Finder double-click
  in the v1.0.3–v1.0.6 builds — most likely cause: `console=True`
  expects a controlling terminal, which a Finder-started .app
  doesn't have. **The mac crash should finally be gone with this.**
- **`entry_pyinstaller.py` now opens a native window via
  `pywebview`** instead of opening the default browser. On macOS
  pywebview uses WKWebView (= Safari engine), on Windows the built-in
  Edge WebView2 — both are part of the operating system, **no extra
  install for the end user**.
- **Server runs in a background thread** instead of blocking; the
  native window shows the UI only after a successful port connect,
  so no more white "server-not-ready" flash.

### Added
- **Browser fallback** when pywebview is missing in the bundle
  (Linux AppImage continues to launch in a browser — GTK/QT WebKit
  libs are not reliably bundled in AppImage, may come in v1.1.x via
  Tauri refactor).

### Notes
- **macOS**: no terminal windows anymore, no browser tabs.
  Double-click → window with Hermes Portal opens directly.
- **Windows**: WebView2 runtime is pre-installed on Windows 10/11,
  should run without extra setup. If not: the setup wizard installs
  WebView2 automatically.
- **Linux**: AppImage still opens in the default browser. Pure native
  via Tauri is a candidate for v1.1.0.

---

## [1.0.6] — 2026-05-23

Three important bug fixes for HA add-on mode. Native-window refactor
(pywebview) moves to v1.1.0.

### Fixed
- **Wiki posts gave 404 in HA** — the wiki index displayed entries,
  but every click on a post landed on "404 Not Found". Cause:
  templates like `index.html` use hard-coded `href="/entity/…"`
  without `url_for()` → no ingress prefix → HA route doesn't find
  the URL. Fix: global JS patcher in `base.html` now rewrites every
  `<a href="/…">`, `<img src="/…">`, `<link href="/…">` and
  `<script src="/…">` on DOM ready + via `MutationObserver` also
  for dynamically loaded content. Instead of touching 100+ templates.
- **Paths in Settings → 🛰️ App reset after reload** — saved values
  were overwritten on every page load from `HP_*` env variables
  (HA add-on options) because `_apply_env` always ran. Now: env
  vars are only **initial seeds on the very first container start**,
  later UI changes are sticky. **Migration**: if the old config.json
  already contains wrong paths, set the correct values once in the
  UI and save.
- **Tasks / News / Briefing layout still bare** — the blog HTMLs
  delivered by the Hermes Agent did have correct ingress URLs in
  v1.0.5, but our `portal/style.css` was not included.
  `_serve_blog_file` now injects the CSS with a cache buster so
  cards, buttons and colours look consistent.

### Notes
- **Logo on App tab + Personality link**: was the same ingress bug
  (`<img src="/static/portal/logo.png">` without prefix). The
  extended `img[src^="/"]` rewriter above fixes it automatically —
  no template touch needed.
- **macOS DMG "App doesn't start / nothing happens"**: for diagnosis,
  please check `~/Desktop/hermes-portal-started.txt` after launch —
  if the file is there, Python started (crash afterwards); if not,
  the PyInstaller bootloader killed itself. The real solution
  (native window instead of browser, no terminal) comes in **v1.1.0**.

---

## [1.0.5] — 2026-05-23

HA blog layout fix + UI polish + deeper macOS crash diagnostics +
PyInstaller codesign integration.

### Fixed
- **Tasks / News / Briefing pages in HA had no layout** — same
  pattern as the original ingress header bug, just at a different
  spot: `_serve_blog_file` passes HTML files generated by the Hermes
  Agent through, which in turn contain hard-coded `/static/...`-
  and `/blog/...`-URLs. These URLs are now appended with the ingress
  prefix at the end of HTML processing via regex. Additionally,
  `window.HP_INGRESS_PATH` + a mini-`fetch` patcher lands in every
  blog HTML.

### Changed
- **Toggle button text** in Settings → 🛰️ App → "📑 Menu items
  visible" shortened: "📰 Show news" instead of "📰 Show news in
  menu", grid to `minmax(160px, 1fr)` → all 4 buttons now fit next
  to each other (on phone they automatically drop to a 2× 2 layout).
- **PyInstaller codesign integrated** — the spec file now sets
  `codesign_identity='-'` on macOS so that PyInstaller signs every
  Mach-O ad-hoc itself during the build (in the correct order,
  inner-most first). Our `sign_macos_app.py` script runs afterwards
  as a safety net.

### Added
- **Startup marker for Mac crash diagnose** — `entry_pyinstaller.py`
  writes as the FIRST thing (before every complex import) a file
  `~/Desktop/hermes-portal-started.txt` with PID, Python version,
  CWD, HOME, `_MEIPASS` etc. This allows diagnosis:
  - **File exists + app still doesn't start** → crash AFTER Python
    start, look in `~/Desktop/Hermes-Portal-Crash.log`
  - **File doesn't exist** → crash IN the PyInstaller bootloader
    (before Python). Look in `~/Library/Logs/DiagnosticReports/`
    for a macOS kernel crash report with "hermes-portal".

---

## [1.0.4] — 2026-05-23

Diagnostic and robustness release. macOS crash remains hard to
reproduce — therefore more logging that _definitely_ lands somewhere.
Plus SSH banner timeout increased for HA container setups and the
nav toggle set completed.

### Added
- **Nav toggles completed** — Settings → 🛰️ App → "📑 Menu items
  visible" now offers **all** four optional main entries:
  📚 Wiki, 📰 News, ☕ Briefing, ✅ Tasks. Full control for users
  who only use partial functions (e.g. only chat + dashboard).
  - New config keys `show_wiki` and `show_aufgaben` (defaults
    `true`).
  - The filter takes effect via `window.HP_NAV_HIDE` in `base.html`
    and `navItems()` in `site-header.js` — header **and** sidebar
    hide the entry synchronously.

### Changed
- **SSH banner timeout** in `hermes_client.py` from 15 s (paramiko
  default) to 30 s, plus `auth_timeout=15`. Plus **single retry**
  on `banner`/`transport`/`eof` errors (container networks like
  HA add-on show sporadic flaky banner exchanges on first connect).
  Auth errors still fail through immediately.
- **Crash log fallback chain** in `entry_pyinstaller.py`:
  1. `~/Desktop/Hermes-Portal-Crash.log` (visible!)
  2. `~/Library/Application Support/Hermes Portal/crash.log`
  3. `$TMPDIR/hermes-portal-crash.log`
  4. `$CWD/hermes-portal-crash.log`
  No matter where it sticks — the traceback will land somewhere.
- **Crash output also on `stderr`** with `flush=True` and a clear
  marker line (`=== HERMES PORTAL CRASH ===`). Whoever launches the
  app from the terminal sees the error live.

### Notes
- **macOS debug guide:** if the app still quits immediately on
  double-click without a crash log on the desktop, the error is
  _below_ Python (PyInstaller bootloader, Gatekeeper library
  validation). Diagnose: start directly from the terminal:
  ```
  "/Applications/Hermes Portal.app/Contents/MacOS/hermes-portal"
  ```

---

## [1.0.3] — 2026-05-22

Desktop launch fix. v1.0.2 solved the sign bug, now the .app started
silently and closed itself again.

### Fixed
- **macOS app starts again.** `entry_pyinstaller.py` tried to create
  the data directory in `[bundle]/Contents/MacOS/hermes-portal-data/`
  — `/Applications/` is not writable for normal users
  → `PermissionError` → uncaught exception → the app dies within
  milliseconds. Now platform-conventional user data paths:
  - **macOS:**   `~/Library/Application Support/Hermes Portal/`
  - **Windows:** `%APPDATA%\Hermes Portal\`
  - **Linux:**   `$XDG_DATA_HOME/hermes-portal/` (fallback
    `~/.local/share/…`)

### Added
- **Crash handler in `entry_pyinstaller.py`** — tracebacks land in
  `<data-dir>/crash.log`. On macOS additionally a native dialog with
  "An error occurred on startup…" via `osascript`, so that
  double-clicked .app bundles no longer die silently.
- **Startup log** now shows the active data directory in the
  terminal (for power users who launch the binary from the shell).

### Notes
- **Data migration:** if you previously launched the portable
  variant from `Downloads/`, your data lives there in
  `hermes-portal-data/`. The .app variant now uses
  `~/Library/Application Support/Hermes Portal/` — copy the folder
  contents over manually if needed.

---

## [1.0.2] — 2026-05-22

Bug fix for the bug fix: the macOS sign loop from v1.0.1 had a bug
itself and de facto signed NOTHING.

### Fixed
- **macOS DMG "damaged" — final fix.** The `awk` in v1.0.1 for path
  extraction from the `file` output cut fundamentally wrong (removed
  the last word instead of just the type description), so that
  `codesign` was called with fantasy paths and **not a single
  Mach-O file was actually signed**. The Python framework therefore
  stayed unsigned → Apple Silicon Gatekeeper hard rejected. Completely
  rewritten in Python (`_wiki_server/scripts/sign_macos_app.py`)
  with readable code and verifiable counts in the build log.

### Changed
- **`_wiki_server/scripts/sign_macos_app.py`** as a maintainable
  tool in the repo instead of a fragile bash pipe in the workflow.
  Finds all Mach-O files via `file` magic check, sorts by path depth
  (innermost first), signs ad-hoc, prints statistics.

### Notes
- **HA panel icon `mdi:robot-happy`** often isn't visible directly
  after an update — the HA supervisor caches the panel registration
  from install time. Workaround: **uninstall and reinstall** the
  add-on once (or `ha core restart`). The add-on data in `/data/`
  is preserved.

---

## [1.0.1] — 2026-05-22

Hotfix wave after the first productive 1.0 installations.

### Added
- **Update check via GitHub Releases API** (`/api/version/check`).
  Returns `{current, latest, update_available, url}`, in-memory
  cache 60 min, robust against offline/rate limit. The sidebar
  shows a small yellow "⬆ vX.Y.Z" badge next to the version number
  when a newer release is available — click opens the GitHub release
  page. Main benefit for desktop installers (AppImage/.dmg/.exe),
  where there is otherwise no hint of new versions. The HA add-on
  remains untouched (HA supervisor delivers the hint itself).
- **Friendly fallback page** for `/blog/index.html`,
  `/blog/aufgaben.html`, `/blog/briefing.html` when the file
  doesn't (yet) exist: new template `blog_missing.html` explains
  that news/tasks/briefing are produced by the Hermes Agent, lists
  typical causes and links to Settings + Briefing "Generate now".

### Changed
- **HA add-on panel icon** from `mdi:satellite-uplink` to
  `mdi:robot-happy`.
- **macOS DMG workaround** in the README + release body corrected:
  xattr must be run **before** copying into Applications (either
  on the DMG file in the Downloads folder or on the mounted volume)
  — the previously documented `/Applications/Hermes Portal.app`
  path doesn't exist because Finder rejects the app already before
  copying.

### Fixed
- **HA header logo missing** in the sidebar panel: two spots in
  `site-header.js` (header brand + footer logo) still used the
  hard-coded `/static/portal/logo.png` without ingress prefix. Both
  replaced with `withPrefix(...)`.
- **News/Tasks/Briefing 404** is now an explanatory page instead
  of bare "Not Found" — previously you thought the add-on was broken.
- **macOS DMG "damaged"** on every install: PyInstaller bundles
  Mach-O files without extension (e.g. `_internal/Python` framework),
  our old sign loop only filtered `*.dylib`/`*.so` → the Python
  framework stayed unsigned → Apple Silicon Gatekeeper hard rejected.
  The new sign loop identifies Mach-O files via `file` magic check
  (all ~30 s through) and signs inner-most first so that nested
  bundles are assembled correctly.

---

## [1.0.0] — 2026-05-22

First 1.0 release. Marks the point at which all platform paths
(desktop installers, Docker, Home Assistant add-on) are usable
end-to-end.

### Added
- **HA ingress support** in `_wiki_server/wiki_app.py` as WSGI
  middleware (`_IngressMiddleware`): reads the `X-Ingress-Path`
  header from the HA supervisor and maps it to WSGI's `SCRIPT_NAME`.
  This makes Flask's `url_for(...)` automatically generate correctly
  prefixed URLs for static assets and endpoints.
- **`window.HP_INGRESS_PATH`** in `base.html` from
  `request.script_root`. Plus a global patcher: wraps `window.fetch`
  and rewrites `<form action="/…">`, so that the 46 hard-coded
  `/api/…` calls in the frontend work under ingress without
  individual adjustments.
- **`hermes_portal/CHANGELOG.md`** — the HA supervisor shows this
  file in the add-on update dialog (previously: "No changelog found").

### Changed
- **macOS Intel build removed from the release workflow**: `macos-13`
  runners have been heavily rationed since Q2 2026 (waiting hours,
  often timeouts). The only macOS asset is now
  `Hermes-Portal-macOS.dmg` (Apple Silicon, arm64). Intel Mac users
  can clone the repo locally and run `pyinstaller` themselves or
  use the Docker variant.
- **`pyproject.toml`** development status from Beta (4) to
  Production/Stable (5).
- **`base.html`** static asset URLs to
  `url_for('static', filename=…)` instead of hard-coded `/static/…`
  paths (CSS, logo, favicon, site-header.js).

### Fixed
- **HA add-on: broken layout in the sidebar panel** — the browser
  fetched CSS, JS and logos against the HA origin instead of the
  ingress URL → 404, bare HTML page, no header. Fixed via the
  ingress middleware + URL prefix in `base.html` + prefix application
  in `site-header.js` (nav links + status polling).

Hotfix release. v0.8.0 could be built in the HA supervisor, but the
container didn't start — and the macOS Intel build hung 20+ minutes
on the sign loop.

### Fixed
- **HA add-on starts again** — `tini` lives on Alpine under
  `/sbin/tini`, not `/usr/bin/tini` as on Debian. The container
  failed with `exec: "/usr/bin/tini": stat … no such file or
  directory`. Path corrected in `hermes_portal/Dockerfile`.
- **macOS sign loop 10× faster** — the old code called for *every*
  file in the bundle (~500–2000 files) first `file`, then `codesign`,
  each as its own process. Now:
  - Filter by extension (`*.dylib`, `*.so`) instead of `file` magic
    check,
  - Batch mode (`-exec … {} +`) instead of individual execution
    (`\;`),
  - The macos-13 runner is no longer the bottleneck in the release
    workflow.

---

## [0.8.0] — 2026-05-22

Release streamlining and macOS hardening.

### Added
- **Two separate macOS DMGs** instead of a universal file:
  - `Hermes-Portal-macOS-AppleSilicon.dmg` (arm64, native build on
    `macos-14`).
  - `Hermes-Portal-macOS-Intel.dmg` (x86_64, native build on
    `macos-13`).
- **Ad-hoc code signature** for the macOS app (identity `-`): all
  nested Mach-O binaries are signed, then the bundle as a whole.
  Afterwards xattrs are fully stripped.
- **Quarantine workaround** documented in the release body and the
  README (`xattr -dr com.apple.quarantine …`) — required because
  without a paid Apple Developer account, no notarization is
  possible.

### Changed
- **GitHub release now contains only native installers as of v0.8.0**
  (`.dmg` × 2, `.exe`, `.AppImage`). The portable archives
  (`.zip` / `.tar.gz`) are dropped — anyone who needs the raw build
  folder builds with `pyinstaller` themselves (the spec lives
  unchanged in the repo).
- **HA add-on `build.yaml`** reduced to the essentials: only
  `build_from:` with the HA base images for `amd64` + `aarch64`.
  The deprecated `labels:` and `args:` fields are gone — labels now
  live as `LABEL` directives directly in `hermes_portal/Dockerfile`.

### Fixed
- **macOS "App is damaged" error** when opening the downloaded DMG:
  cause was the missing code signature + Chrome quarantine flag.
  With ad-hoc sign + xattr strip + documented user workaround the
  app is now bootable.
- **macOS sign build error** "bundle format unrecognized …
  flask-X.Y.Z.dist-info": `codesign --deep` tries to sign every
  subfolder as a nested bundle and fails on Python metadata
  folders. Fix: sign all Mach-O files (binary, `.dylib`, `.so`)
  individually, the bundle as a whole **without** `--deep`.
- **HA add-on build error** "base name ($BUILD_FROM) should not be
  blank": caused by completely removing `build.yaml`. The HA
  supervisor only supplies `BUILD_FROM` as a build arg when
  `build.yaml` with `build_from:` is present. File back, in
  minimal form.

---

## [0.7.0] — 2026-05-22

Hotfix and distribution release. Makes the Home Assistant add-on
installable and delivers real native installers for all desktop
platforms.

### Added
- **Native installers** in the release workflow:
  - **macOS** → `Hermes-Portal-macOS.dmg` (`.app` bundle with
    `.icns` icon, packed in a DMG via `hdiutil`).
  - **Windows** → `Hermes-Portal-Setup.exe` (Inno Setup 6, with
    Start menu entry, optional desktop icon, uninstaller, German
    translation).
  - **Linux** → `Hermes-Portal-Linux.AppImage` (self-contained,
    `chmod +x` suffices to launch).
- **Portable archives** (`.zip` / `.tar.gz`) remain in addition for
  power users — both variants land on the release as well.
- **HA add-on logo + icon**: `hermes_portal/logo.png` (250×250) and
  `hermes_portal/icon.png` (128×128) → HA now shows the Hermes
  caduceus in the add-on store instead of the default placeholder.

### Changed
- **HA add-on Dockerfile** completely rebuilt: pulls the Portal
  sources self-contained at build time via
  `git clone --branch v${BUILD_VERSION}` from GitHub, instead of
  expecting pre-generated `rootfs/app/` artefacts.
  - `hermes_portal/prepare.sh` is therefore obsolete and removed.
  - `hermes_portal/rootfs/` removed, `run.sh` now lives directly
    in the add-on root.
  - `.gitignore` entries for `rootfs/app/` and
    `rootfs/requirements.txt` tidied.

### Fixed
- **HA add-on build error** "failed to compute cache key …
  '/rootfs/app': not found" — the build now works 1:1 on the HA
  supervisor without `prepare.sh` having to be executed locally
  first.

---

## [0.6.0] — 2026-05-22

First maintenance release after the public launch. License change,
new UI toggles and project-wide changelog documentation.

### Added
- **CHANGELOG.md** in Keep a Changelog format — from now on all
  releases are documented here.
- **Nav toggles** in the Settings → App tab — a new section
  "📑 Menu items visible" with checkboxes for **News** and
  **Briefing**. Whoever doesn't use these features can hide them
  from the header and sidebar.
  - New config keys `show_news` / `show_briefing` (default `true`),
    both in `config.py` and in `config.defaults.json`.
  - Frontend filter via `window.HP_NAV_HIDE` in `base.html`,
    `site-header.js` renders header **and** sidebar dynamically.
- **Docker workflow** (`.github/workflows/docker.yml`) — rolling
  multi-arch build on every `main` push that touches Docker-relevant
  files. Tags: `:main` (HEAD) + `:sha-<short>` (rollback anchor).
- **`repository.yaml`** in the repo root + add-on folder moved to
  `hermes_portal/` → the repo can now be added directly as a Home
  Assistant add-on source.

### Changed
- **License** changed to **Apache License 2.0** (previously mixed
  between MIT locally and CC BY-NC-SA 3.0 on GitHub). All references
  consistently updated: `LICENSE`, `README.md`, `pyproject.toml`
  (classifier), `.github/workflows/release.yml` (OCI label),
  `hermes_portal/build.yaml` (OCI label).
- **HA add-on path**: `homeassistant/hermes_portal/` →
  `hermes_portal/` (the HA supervisor only scans the repo root
  for add-on folders).
- **HA add-on version** in `hermes_portal/config.yaml` from `0.1.0`
  synchronized to `0.6.0`.

### Fixed
- **Type import order** in `_wiki_server/wiki_app.py`:
  `from typing import Optional` moved to the start of the file
  (previously line 3292 → CI smoke import error on an annotation
  at line 3120).
- **Windows Unicode crash** in `_wiki_server/scripts/fetch_monaco.py`:
  stdout/stderr explicitly reconfigured to UTF-8 so the PyInstaller
  build on `windows-latest` doesn't fail on `cp1252` encoding of
  Unicode arrows/checkmarks.
- **PyInstaller icon conversion**: `pillow` added as a build dep
  so the PNG logo is automatically converted to `.ico` on Windows
  (previously: `ValueError: Received icon image … which is not in
  the correct format`).

---

## [0.5.0] — 2026-05-22

First public release. The Hermes Portal is operational as a complete
web frontend for the [Hermes Agent](https://github.com/jayjojayson/Hermes-Portal)
— locally in the Hermes VM, as a Docker container or as a Home
Assistant add-on.

### Added

#### Architecture
- **`hermes_client.py`** — abstraction layer over `local` and `ssh`
  backends (paramiko, thread-safe via RLock). All FS operations and
  CLI calls go through the same client.
- **`config.py`** — central configuration via `data/config.json`
  with override via environment variables (`HP_*`).
- **Dynamic path refresh** — `exchange_path` / `hermes_home` /
  `wiki_subpath` can be changed live in the UI, no app restart.
- **Versioning** — `_wiki_server/__version__.py` as a single source
  of truth, displayed in the sidebar footer as a clickable release
  link.

#### Pages & features
- **🏠 Dashboard** — agent status (live dot polls every 30 s),
  system stats (CPU/RAM/Disk from the Hermes host), next cronjobs
  (with "overdue" display on TZ-aware time calculation), task
  overview, briefing snippet, news headlines, token usage (mini
  chart), last 5 wiki posts with deep link.
- **📚 Wiki** — Markdown editor with a toolbar (H1–H4, bold,
  italic, code, list, numbered list, link), wikilink resolver,
  tags, full-text search, import/export (`.md` upload + ZIP
  download), configurable category labels.
- **📰 News** — RSS aggregator over configurable feeds, the static
  blog HTML is enriched server-side with Portal branding (logo,
  footer, brand-aware `<title>`).
- **☕ Briefing** — own page with iframe preview, "Generate now"
  button, collapsible settings (GitHub user, weather coordinates,
  BVG stop, RSS, paths).
- **✅ Tasks** — read/write of `aufgaben.md`, the assignee dropdown
  uses the configured names (instead of hard-coded Wally/Jan).
- **📂 Explorer** — file browser with textually safe path resolution
  (traversal protection), upload, mkdir, delete, download (with
  SSH stream).
- **💬 Chat** — sessions sidebar (left, collapsible), chat area
  (centre), code editor column (Monaco, opens on click of a file),
  file tree column (right, collapsible). The splitter between chat
  and editor uses flex ratios (no layout break on file tree toggle).
- **💬 Chat toolbar** — 🎤 voice input (Web Speech API, German),
  📎 file attachment, 📁 server-side folder picker (with SMB/mount
  guide in the modal), 📂 quick button for the configured exchange
  folder, send/stop toggle (`/stop` to Hermes + AbortController).
- **⚡ Activity** — live tail of the Hermes log, mtime-based
  versioning for polling.
- **⚙️ Settings** — six tabs:
  - **⏰ Cronjobs** — list + create/edit/pause/run/delete via
    `hermes cron`
  - **🧠 Personality & Memory** — SOUL.md / USER.md / MEMORY.md /
    config.yaml, plus a reference to the identity settings in the
    App tab
  - **🛠️ Skills** — flat list of all skills (Hermes + built-in +
    custom)
  - **📚 References** — all skill references + Hermes scripts
    editable
  - **📊 Usage** — KPI cards, SVG line chart token progress
    (total/input/output), mini bars for requests, day switch
    (prev/next/date picker)
  - **🛰️ App** — identity (agent/user/category labels),
    connection (local/ssh, SSH wizard with key generation +
    Hermes setup prompt), paths, RSS feeds, sticky save bar
  - **❤️ Support** — PayPal, Ko-fi, GitHub project/discussions/issues
- **🎨 Branding** — own Hermes caduceus logo
  (`hermes-portal-logo.png`) everywhere (header, tab buttons,
  section titles, footer, favicon), dynamic via `window.HP_BRAND`
  + Portal name.

#### Distribution
- **Dockerfile** (multi-stage, multi-arch via Buildx) +
  `docker-compose.yml`.
- **Home Assistant add-on** — `homeassistant/hermes_portal/` with
  `config.yaml`, `Dockerfile`, `build.yaml`, `prepare.sh`, its own
  README.
- **GitHub release workflow** (`.github/workflows/release.yml`) —
  on tag `v*.*.*`: parallel PyInstaller builds on Mac/Linux/Windows,
  multi-arch Docker push to GHCR, GitHub release with all artefacts
  + notes.
- **CI workflow** (`.github/workflows/ci.yml`) — on every PR:
  bytecode compile, route smoke (≥70 routes expected), Docker build.
- **`scripts/fetch_monaco.py`** — downloads Monaco editor (~14 MB)
  once into `static/vendor/monaco/` for offline usage in the chat
  editor.
- **`entry_pyinstaller.py`** + `hermes_portal.spec` — standalone
  bundle with Waitress WSGI server + automatic browser launch.
- **`docs/systemd.service`** — sample unit file for Linux deployment.
- **`pyproject.toml`** — clean project metadata.

### Security
- **Path traversal protection** in the Explorer (textual
  normalization instead of `Path.resolve()`, blocks `..` and `\x00`).
- **paramiko lock** — all SFTP/exec operations serialized, since
  Flask's multi-threading otherwise caused SFTP deadlocks.
- **TZ-aware time calculation** — `client.time_offset_seconds()`
  determines the VM clock once per minute and corrects comparisons
  with naive timestamps from `jobs.json` / logs.
- **Connection cleanup** — `reset_client()` cleanly closes old SSH
  connections on every settings save.

### Fixed
- **Header live dot** now reflects the real Hermes status instead
  of always pulsing green (Online/Idle/Offline/Unknown).
- **Cache busting** — `?v=<hash>` suffix for `style.css` and
  `site-header.js`, automatic on every asset change.
- **Blog pages** pull the Portal CSS via style injection so logo,
  footer and live dot look consistent.
- **Briefing page** is served via iframe + `/api/briefing/render`
  → also works in SSH mode with remote paths.

---

[Unreleased]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.3.3...HEAD
[1.3.3]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.3.2...v1.3.3
[1.3.2]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.2.2...v1.3.0
[1.2.2]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.9...v1.2.0
[1.1.9]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.8...v1.1.9
[1.1.8]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.7...v1.1.8
[1.1.7]: https://github.com/jayjojayson/Hermes-Portal/compare/v1.1.6...v1.1.7
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
