<p align="center">
  <img src="hermes-portal-logo.png" alt="Hermes Portal Logo" width="180">
</p>

<h1 align="center">Hermes Portal GUI</h1>

<p align="center">
  <strong>Modern web frontend for the Hermes Agent</strong><br>
  Wiki · News · Briefing · Tasks · File Explorer · Chat with Monaco Editor · Live Logs · Settings
</p>

<p align="center">
  <a href="https://github.com/jayjojayson/Hermes-Portal/releases"><img src="https://img.shields.io/github/v/release/jayjojayson/Hermes-Portal?label=Release&color=22c55e" alt="Latest Release"></a>
  <a href="https://github.com/jayjojayson/Hermes-Portal/releases"><img src="https://img.shields.io/github/downloads/jayjojayson/Hermes-Portal/total?color=60a5fa&label=Downloads" alt="Downloads"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/jayjojayson/Hermes-Portal?color=f59e0b" alt="License"></a>
  <a href="https://github.com/jayjojayson/Hermes-Portal/discussions"><img src="https://img.shields.io/badge/💬-Discussions-2ea44f" alt="Discussions"></a>
  <a href="README.de.md"><img src="https://img.shields.io/badge/🇩🇪-Deutsch-000?style=flat" alt="Deutsche README"></a>
</p>

<div align="center">

[![Buy Me a Coffee](https://img.shields.io/badge/Ko--fi-Buy%20Me%20a%20Coffee-darkgreen?style=flat&logo=ko-fi&logoColor=white)](https://ko-fi.com/jayjojayson)
[![Support](https://img.shields.io/badge/%20-Support%20Me-darkgreen?style=flat&logo=paypal&logoColor=white)](https://www.paypal.me/quadFlyerFW)
</div>

> 🇩🇪 **Deutsche Anleitung** → [README.de.md](README.de.md)

---

## ✨ What is this?

Hermes Portal connects to your **Hermes Agent** (locally in a VM or
remotely via SSH) and exposes its data and tools through a polished
dark-mode web UI:

- **🏠 Dashboard** — Agent status, open tasks, news headlines, system stats (CPU/RAM/disk)
- **📚 Wiki** — Markdown editor with toolbar, tags, full-text search, .md import/export
- **📰 News** — RSS aggregator (configurable)
- **☕ Briefing** — Daily auto-generated briefing (weather, GitHub, crypto, transit, …)
- **✅ Tasks** — Task list with assignee (agent + user)
- **📂 Explorer** — File browser for your exchange folder
- **💬 Chat** — Direct line to the agent, with:
  - 🎤 Voice input (Browser Web Speech API)
  - 📁 Server-side folder picker (or SMB mount path)
  - 📝 Built-in Monaco code editor (dark + light theme)
  - ⚡ Slash-command dropdown (`/new`, `/reset`, `/model`, `/stop`, …)
  - ⏹ Stop button (sends `/stop` to running generation)
- **⚡ Activity** — Live log of all Hermes actions
- **⚙️ Settings** — Cronjobs, Personality/Memory, Skills, References, Usage stats, App config (with SSH key wizard), Support
- **🌐 UI in 4 languages** — English (default), German, Spanish, French (community-contributable JSON tables under `_wiki_server/i18n/`)

---

## 🚀 Installation

| If you have… | Use… | Notes |
|--------------|------|-------|
| Docker / Proxmox | **Docker** (recommended) | One command, multi-arch image on GHCR |
| Home Assistant | **HA Add-on** | One-click install, integrates with HA Ingress |
| macOS | **`.pkg` installer** | Apple Silicon (M1/M2/M3/M4) — see Gatekeeper note below |
| Windows 10/11 | **`.exe` Setup wizard** | Native installer, Edge WebView2 backend |
| Linux desktop | **`.AppImage`** | `chmod +x` and run |
| Anything else (Python 3.11+) | **From source** | `pip install -r _wiki_server/requirements.txt` |

### 📦 Docker (recommended for headless / Proxmox / NAS)

```bash
git clone https://github.com/jayjojayson/Hermes-Portal.git
cd Hermes-Portal
docker compose up -d
# Open http://localhost:8090
```

On first start the container pulls the Monaco editor (~14 MB) automatically.
All settings (SSH credentials, agent host, RSS feeds, …) live in the UI under
**⚙️ Settings → 🛰️ App** — no environment-variable juggling required after the
first start.

### 🏠 Home Assistant Add-on

In HA: **Settings → Add-ons → Add-on Store → ⋮ → Repositories**, add the URL
`https://github.com/jayjojayson/Hermes-Portal`. The add-on appears in the
store, click *Install*. The repo ships a `repository.yaml` + a self-contained
add-on that pulls its sources directly from the matching git tag — no manual
build steps.

### 🍎 macOS (PKG installer)

Download `Hermes-Portal-macOS.pkg` from the
[Releases](https://github.com/jayjojayson/Hermes-Portal/releases). Since the
PKG is ad-hoc signed (not Apple-notarized — that would require a paid Apple
Developer ID), macOS Gatekeeper may complain on first install. Strip the
quarantine flag once before opening:

```bash
xattr -dr com.apple.quarantine ~/Downloads/Hermes-Portal-macOS.pkg
```

Then double-click the PKG → installer wizard guides you through →
`Hermes Portal.app` lands in `/Applications/`. Launch via Launchpad or
Spotlight. The app opens a native window (WKWebView, no Terminal,
no Browser tab) and stores its data under
`~/Library/Application Support/Hermes Portal/`.

### 🪟 Windows (EXE setup)

Download `Hermes-Portal-Setup.exe` from the
[Releases](https://github.com/jayjojayson/Hermes-Portal/releases). Inno Setup
wizard (German + English UI) installs the app to `Program Files\Hermes Portal\`,
adds Start menu entry and an optional desktop shortcut. Windows SmartScreen
may show a "publisher unknown" warning on first launch — click *More info* →
*Run anyway* (we don't have an EV code signing cert; cost ~$300/year, not
worth it for an open-source project).

The app opens a native window via Edge WebView2 (built into Windows 10/11).
Data is stored under `%APPDATA%\Hermes Portal\`.

### 🐧 Linux (AppImage)

```bash
chmod +x Hermes-Portal-Linux.AppImage
./Hermes-Portal-Linux.AppImage
# Opens default browser to http://localhost:8090
# (Native window via pywebview comes in a later release —
#  GTK-WebKit system libs are tricky to bundle in AppImage.)
```

Data goes to `$XDG_DATA_HOME/hermes-portal/` (default `~/.local/share/hermes-portal/`).

### 🛠 From source (any OS with Python 3.11+)

```bash
git clone https://github.com/jayjojayson/Hermes-Portal.git
cd Hermes-Portal
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
pip install -r _wiki_server/requirements.txt
python _wiki_server/scripts/fetch_monaco.py
python _wiki_server/wiki_app.py
# → http://localhost:8090
```

Run as a systemd service: see [`docs/systemd.service`](docs/systemd.service).
Run as a macOS launch agent: see [`docs/launchd.plist`](docs/launchd.plist).

---

## 🤝 Contributing

- **Bug reports** → [Issues](https://github.com/jayjojayson/Hermes-Portal/issues)
- **Questions / show-and-tell** → [Discussions](https://github.com/jayjojayson/Hermes-Portal/discussions)
- **New language** → drop a `<code>.json` into `_wiki_server/i18n/` (see
  existing `en.json` as template) and open a PR — appears automatically in
  the language switcher
- **Code contributions** → fork, branch, PR. See `CONTRIBUTING.md` (TBD).

---

## 🔐 License

Apache License 2.0 — see [LICENSE](LICENSE).

---

<p align="center">
  <sub>Made with ☕ and 🤖 · <a href="README.de.md">🇩🇪 Deutsche Version</a></sub>
</p>
