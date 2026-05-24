<p align="center">
  <img src="hermes-portal-logo.png" alt="Hermes Portal Logo" width="180">
</p>

<h1 align="center">Hermes Portal GUI</h1>

<p align="center">
  <strong>Modernes Web-Frontend für den Hermes-Agent</strong><br>
  Wiki · News · Briefing · Aufgaben · Datei-Explorer · Code-Editor-Chat · Live-Logs · Settings
</p>

<p align="center">
  <a href="https://github.com/jayjojayson/Hermes-Portal/releases"><img src="https://img.shields.io/github/v/release/jayjojayson/Hermes-Portal?label=Release&color=22c55e" alt="Latest Release"></a>
  <a href="https://github.com/jayjojayson/Hermes-Portal/releases"><img src="https://img.shields.io/github/downloads/jayjojayson/Hermes-Portal/total?color=60a5fa&label=Downloads" alt="Downloads"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/jayjojayson/Hermes-Portal?color=f59e0b" alt="License"></a>
  <a href="https://github.com/jayjojayson/Hermes-Portal/discussions"><img src="https://img.shields.io/badge/💬-Discussions-2ea44f" alt="Discussions"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/🇬🇧-English-000?style=flat" alt="English README"></a>
</p>

<div align="center">
  
[![Buy Me a Coffee](https://img.shields.io/badge/Ko--fi-Buy%20Me%20a%20Coffee-darkgreen?style=flat&logo=ko-fi&logoColor=white)](https://ko-fi.com/jayjojayson)
[![Support](https://img.shields.io/badge/%20-Support%20Me-darkgreen?style=flat&logo=paypal&logoColor=white)](https://www.paypal.me/quadFlyerFW)
</div>

> 🇬🇧 **English readme** → [README.md](README.md)


---

## ✨ Was ist das?

Hermes Portal verbindet sich mit deinem **Hermes-Agent** (lokal in einer VM oder
remote via SSH) und stellt seine Daten und Werkzeuge in einer Dark-Mode-Web-UI
zur Verfügung:

- **🏠 Dashboard** — Agent-Status, offene Aufgaben, News-Schlagzeilen, System-Stats (CPU/RAM/Disk)
- **📚 Wiki** — Markdown-Editor mit Toolbar, Tags, Volltextsuche, .md-Import/-Export
- **📰 News** — RSS-Aggregator (konfigurierbar)
- **☕ Briefing** — täglich generiertes Briefing (Wetter, GitHub, Krypto, …)
- **✅ Aufgaben** — Aufgabenliste mit Bearbeiter (Agent + User)
- **📂 Explorer** — Datei-Browser für deinen Austausch-Ordner
- **💬 Chat** — Direkter Draht zum Agenten, mit:
  - 🎤 Spracheingabe (Browser Web Speech API)
  - 📁 Server-side Folder-Picker (oder SMB-Pfad)
  - 📝 Eingebauter Monaco-Code-Editor
  - ⏹ Stop-Button (`/stop`-Command)
- **⚡ Aktivität** — Live-Log aller Hermes-Aktionen
- **⚙️ Settings** — Cronjobs, Personality/Memory, Skills, References, Usage-Stats, App-Config (mit SSH-Key-Wizard), Support

---

## 🚀 Installation

> Es gibt viele Mglichkeiten das Hermes Portal zu nutzen, du kannst es direkt vom Hermes Agenten in seiner VM installieren lassen, oder als App in Home Assistant einbinden, als Docker lokal oder in proxmox laufen lassen oder direkt als App für dein OS (mac, linux, win) installieren und nutzen.

> Hermes Agent installiert für dich oder du machst es manuell.

### 📦 Docker (empfohlen, alle Plattformen)

```bash
# 1) Repo klonen
git clone https://github.com/jayjojayson/Hermes-Portal.git
cd Hermes-Portal

# 2) Container starten
docker compose up -d

# 3) Browser öffnen
open http://localhost:8090       # macOS
xdg-open http://localhost:8090   # Linux
start http://localhost:8090      # Windows (PowerShell)
```

Beim ersten Start lädt Docker den Monaco-Editor (~14 MB) automatisch mit
herunter. Bei `docker compose up` ohne `-d` siehst du den Live-Log.

**Konfiguration:** alles in der UI unter **⚙️ Settings → 🛰️ App** —
SSH-Verbindung zur Hermes-VM, Agent-Name, Pfade, RSS-Feeds.

---

### 🏠 — Home Assistant Add-on

<details>
<summary><strong>🔌 Hermes Portal — Home Assistant Add-on</strong></summary>

Installation  
In Home Assistant: Einstellungen → Add-ons → Add-on Store → ⋮ → Repositories.  
URL eintragen: `https://github.com/jayjojayson/Hermes-Portal`  

(Das Repo ist seit v0.7.0 ein voll installierbares HA-Add-on: `repository.yaml`  
+ `hermes_portal/` im Root, das Add-on baut sich beim Install self-contained  
direkt aus dem Git-Tag — kein `prepare.sh` mehr nötig.)  

Add-on **Hermes Portal** auswählen und installieren.  
Konfiguration setzen (siehe Optionen unten), dann starten.  

Öffne den Reiter über die Sidebar (Ingress) oder direkt:  

`http://<ha-ip>:8090`

---

### Konfiguration

| Option | Beschreibung | Default |
|---|---|---|
| `agent_name` | Name deines Hermes-Agents (statt "Wally") | `Hermes` |
| `user_name` | Wie der Agent dich anspricht | `Du` |
| `connection_mode` | `local` (im HA-Host) oder `ssh` (Hermes auf anderem PC) | `ssh` |
| `agent_host` | IP/Hostname des Hermes-Agents (bei SSH-Mode) | `""` |
| `ssh_user` | SSH-User auf dem Hermes-Host | `root` |
| `ssh_port` | SSH-Port | `22` |
| `ssh_password` | Optional, falls kein Key verwendet wird | `""` |
| `exchange_path` | Pfad zum Austausch-Ordner auf dem Hermes-Host | `/share` |

Weitere Settings (RSS-Feeds, Persönlichkeit, Pfade) konfigurierst du nach dem Start direkt in der Portal-UI unter ⚙️ Settings → 🛰️ App.  

---

### SSH-Key statt Passwort

In der Portal-UI unter `Settings → App` den Pfad  
`/data/.ssh/id_ed25519` eintragen.  

Lege den Key in deinem HA unter  
`/addon_configs/<slug>/ssh/` ab, dann ist er im Container unter  
`/data/.ssh/` verfügbar.  

(Volume-Mapping ist im `config.yaml` voreingestellt.)

</details>

---

### 🍎 macOS (natives Binary, kein Docker)

<details>
<summary><strong>Schritt-für-Schritt-Anleitung</strong> (5 Minuten)</summary>

```bash
# 1) Voraussetzungen prüfen (Python 3.11+)
python3 --version

# 2) Repo klonen
git clone https://github.com/jayjojayson/Hermes-Portal.git
cd Hermes-Portal

# 3) Virtual Env anlegen + Dependencies installieren
python3 -m venv venv
source venv/bin/activate
pip install -r _wiki_server/requirements.txt

# 4) Monaco-Editor (für Chat-Code-Editor) einmalig holen
python _wiki_server/scripts/fetch_monaco.py

# 5) Starten
python _wiki_server/wiki_app.py
# → Browser öffnet sich nicht automatisch. Manuell: http://127.0.0.1:8090
```

**Als Hintergrund-Dienst (mit launchd):** siehe [`docs/launchd.plist`](docs/launchd.plist).

</details>

<details>
<summary><strong>Alternative: fertiges .dmg-Installer-Image</strong> (kein Python nötig)</summary>

Aus den [Releases](https://github.com/jayjojayson/Hermes-Portal/releases)
`Hermes-Portal-macOS.dmg` laden (Apple Silicon, M1/M2/M3/M4 — Intel-Macs
ab v1.0.0 nicht mehr im Release, dort Repo klonen + `pyinstaller` selbst).
DMG öffnen → `Hermes Portal.app` in den Programme-Ordner ziehen.

**Wichtig — Erster Start (Gatekeeper-Workaround):**
Die App ist ad-hoc-signiert, **nicht** von Apple notarisiert (das würde
einen kostenpflichtigen Apple-Developer-Account voraussetzen). Beim
Doppelklick erscheint daher die Meldung „Hermes Portal.app ist beschädigt".
Workaround **vor** dem Mounten/Kopieren — Quarantine-Flag an der DMG
entfernen:

```bash
xattr -dr com.apple.quarantine ~/Downloads/Hermes-Portal-macOS.dmg
```

Anschließend DMG öffnen und `Hermes Portal.app` ganz normal in den
Programme-Ordner ziehen. Falls du die DMG schon gemountet hast und die
Meldung schon kam, geht es auch direkt am gemounteten Image:

```bash
xattr -dr com.apple.quarantine "/Volumes/Hermes Portal/Hermes Portal.app"
```

Danach in Programme ziehen, startet per Doppelklick.

</details>

---

### 🐧 Linux (Debian/Ubuntu/Fedora)

<details>
<summary><strong>Schritt-für-Schritt-Anleitung</strong> (5 Minuten)</summary>

```bash
# 1) Voraussetzungen
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git

# 2) Repo klonen
git clone https://github.com/jayjojayson/Hermes-Portal.git /opt/hermes-portal
cd /opt/hermes-portal

# 3) Virtual Env + Dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r _wiki_server/requirements.txt
python _wiki_server/scripts/fetch_monaco.py

# 4) Starten
python _wiki_server/wiki_app.py
# → http://localhost:8090
```

**Als systemd-Service** (automatischer Start nach Reboot):

```bash
sudo cp docs/systemd.service /etc/systemd/system/hermes-portal.service
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-portal
```

</details>

<details>
<summary><strong>Alternative: AppImage</strong> (kein Python, kein Install)</summary>

Lade die neueste `Hermes-Portal-Linux.AppImage` aus den
[Releases](https://github.com/jayjojayson/Hermes-Portal/releases) und starte
sie direkt:

```bash
chmod +x Hermes-Portal-Linux.AppImage
./Hermes-Portal-Linux.AppImage
```

Portable Variante (entpacktes Bundle): `Hermes-Portal-Linux.tar.gz`
herunterladen, entpacken, `./hermes-portal/hermes-portal` starten.

</details>

---

### 🪟 Windows

<details>
<summary><strong>Schritt-für-Schritt-Anleitung mit Python</strong> (10 Minuten)</summary>

```powershell
# 1) Python 3.11+ installieren von https://www.python.org/downloads/
#    WICHTIG: "Add Python to PATH" anhaken!

# 2) Repo klonen (Git for Windows: https://gitforwindows.org/)
git clone https://github.com/jayjojayson/Hermes-Portal.git
cd Hermes-Portal

# 3) Virtual Env + Dependencies
python -m venv venv
venv\Scripts\activate
pip install -r _wiki_server\requirements.txt
python _wiki_server\scripts\fetch_monaco.py

# 4) Starten
python _wiki_server\wiki_app.py
# → http://127.0.0.1:8090
```

</details>

<details>
<summary><strong>Alternative: fertiger Installer (.exe)</strong> (kein Python nötig)</summary>

Lade die neueste `Hermes-Portal-Setup.exe` aus den
[Releases](https://github.com/jayjojayson/Hermes-Portal/releases) und führe
den Setup-Wizard aus (Inno Setup, deutsch). Legt Start-Menü-Eintrag und
optional Desktop-Verknüpfung an, Uninstaller über Apps & Features.
Firewall fragt einmal nach Netzwerk-Zugriff → erlauben.

Portable Variante: `Hermes-Portal-Windows.zip` herunterladen, entpacken,
`hermes-portal.exe` direkt starten.

</details>

---

## 🤖 Hermes-Agent-Setup-Prompts

Damit du Hermes nicht jeden Befehl manuell eintippen musst, hier fertige Prompts
zum Einfügen in den Hermes-Chat oder per `hermes -z "<prompt>"`.

<details>
<summary><strong>🔌 SSH-Einrichtung auf der Hermes-VM (automatisch)</strong></summary>

Der gleiche Prompt steckt in der App-Tab → SSH-Wizard → „🤖 Automatisch"-Akkordeon
und wird dort dynamisch mit deinem Pubkey, SSH-User und Port befüllt. Manuell:

```
Hallo Hermes! Richte bitte SSH-Zugriff für das Hermes Portal ein.

Ziel: Das Portal (läuft als Docker auf einem anderen Gerät im LAN) soll dich
via SSH erreichen.

1) Stelle sicher, dass ein SSH-Server läuft:
   • Prüfe ob `sshd` installiert ist: `which sshd` oder `systemctl status ssh`.
   • Falls nicht installiert: `apt install -y openssh-server`
   • Aktiviere und starte: `systemctl enable --now ssh`.

2) Lege den Public-Key für User `root` an:
   • `mkdir -p ~root/.ssh && chmod 700 ~root/.ssh`
   • Hänge folgenden Public-Key an `~root/.ssh/authorized_keys` an
     (Mode 600 setzen): <DEIN_PUBKEY_HIER>
   • `chown -R root:root ~root/.ssh`

3) Stelle sicher, dass SSH-Port 22 nach außen erreichbar ist:
   • `ufw allow 22/tcp` oder firewalld/nftables entsprechend.

4) Teste lokal: `ssh -p 22 root@localhost "echo ok"`.

Melde dich bei Problemen mit OS/Distro, Port, Firewall-Status.
```

</details>

<details>
<summary><strong>📁 SMB-Share von macOS / Windows zur Hermes-VM</strong></summary>

```
Hallo Hermes! Mounte bitte einen SMB-Share von meinem Computer auf dieser VM,
damit ich darin gemeinsam mit dir arbeiten kann.

Mein Setup:
- Mein Computer: <HOST_OR_IP> (im selben LAN)
- Freigegebener Share: <SHARE_NAME>
- Username: <USERNAME>

Bitte:
1) `apt install -y cifs-utils` (oder Distro-Äquivalent)
2) Mountpunkt anlegen: `mkdir -p /mnt/macshare`
3) Credentials-File `/root/.smbcreds` mit username/password anlegen (chmod 600)
4) In /etc/fstab eintragen:
   //<HOST_OR_IP>/<SHARE_NAME> /mnt/macshare cifs credentials=/root/.smbcreds,uid=0,gid=0,iocharset=utf8 0 0
5) `mount -a` und Erfolg melden.

Wenn fertig, kann ich im Hermes-Portal als „Shared Folder" `/mnt/macshare` eintragen.
```

</details>

<details>
<summary><strong>📥 Hermes Portal in eigener VM installieren</strong></summary>

```
Hallo Hermes! Installiere bitte das Hermes Portal lokal auf dir selbst, damit
ich es ohne SSH-Setup nutzen kann.

1) `git clone https://github.com/jayjojayson/Hermes-Portal.git /opt/hermes-portal`
2) `cd /opt/hermes-portal/_wiki_server`
3) `python3 -m venv venv && venv/bin/pip install -r requirements.txt`
4) `venv/bin/python scripts/fetch_monaco.py` (einmalig Monaco holen)
5) systemd-Service einrichten:
   `cp ../docs/systemd.service /etc/systemd/system/hermes-portal.service`
   `systemctl daemon-reload && systemctl enable --now hermes-portal`
6) Firewall: `ufw allow 8090/tcp`
7) Melde dich mit deinem LAN-Hostname + Port, ich öffne dann im Browser
   `http://<host>:8090`.
```

</details>

---

## ⚙️ Konfiguration

Alle Einstellungen liegen in `data/config.json`. Erst-Inbetriebnahme erzeugt
sie aus `_wiki_server/config.defaults.json`. **Du musst nichts manuell anlegen** —
die UI macht das.

### Wichtigste Settings (Settings → 🛰️ App)

| Key                | Beschreibung                                           | Default            |
|--------------------|--------------------------------------------------------|--------------------|
| `agent_name`       | Name deines Agenten (statt „Hermes")                   | `Hermes`           |
| `user_name`        | Wie der Agent dich anspricht                           | `Du`               |
| `connection_mode`  | `local` (gleiche Maschine) oder `ssh` (Remote-Hermes)  | `local`            |
| `agent_host`       | IP/Hostname der Hermes-VM (bei SSH-Mode)               | `127.0.0.1`        |
| `ssh_user`         | SSH-Benutzer                                           | `root`             |
| `ssh_key_path`     | Pfad zum privaten Key (bevorzugt vor Passwort)         | (leer)             |
| `exchange_path`    | Austausch-Ordner auf dem Hermes-Host                   | `/mnt/austausch`   |
| `hermes_home`      | Hermes-Konfig-Verzeichnis                              | `/root/.hermes`    |
| `hermes_bin`       | Pfad/Name der hermes-CLI                               | `hermes`           |
| `rss_feeds`        | Liste `{name, url}` für News-Seite                     | Heise-Defaults     |
| `category_entity_label`  | Label für Wiki-Kategorie 1                       | `Entitäten`        |
| `category_concept_label` | Label für Wiki-Kategorie 2                       | `Konzepte`         |

Jedes Setting auch via **Environment-Variable** überschreibbar:
`HP_AGENT_NAME=Athena`, `HP_AGENT_HOST=192.168.1.42` etc.

---



## 🏗️ Architektur

```
┌──────────────────────┐        ┌──────────────────────┐
│  Hermes Portal       │  HTTP  │     Browser          │
│  (Flask + Gunicorn)  │ ◄────► │  (Dashboard, …)      │
└──────────┬───────────┘        └──────────────────────┘
           │
           │ local : Path() + subprocess
           │ ssh   : paramiko (SFTP + exec) — thread-safe gelockt
           ▼
┌──────────────────────┐
│  Hermes-Agent        │
│  /mnt/austausch      │  Wiki-Inhalte, Briefing-Output, Shared-Folder
│  /root/.hermes       │  SOUL.md, USER.md, MEMORY.md, cron/jobs.json, logs/
└──────────────────────┘
```

Alle Pfadzugriffe und CLI-Calls gehen durch
[`hermes_client.py`](_wiki_server/hermes_client.py). Im `local`-Mode ist das ein
direkter `Path()`+`subprocess`-Aufruf, im `ssh`-Mode läuft alles über paramiko
(SFTP für Dateien, SSH-Exec für Befehle) — mit Lock pro Operation, damit Flasks
threaded-Mode den SFTP-Channel nicht zerschießt.

---

## 🛠️ Entwicklung

```bash
cd _wiki_server
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python scripts/fetch_monaco.py

# Mit eigenen Defaults starten
HP_AGENT_NAME=TestAgent HP_EXCHANGE_PATH=/tmp/exchange \
    venv/bin/python wiki_app.py
```

### Smoke-Tests

```bash
curl -s http://localhost:8090/api/refresh
curl -s http://localhost:8090/api/settings/app | python3 -m json.tool
curl -s http://localhost:8090/api/dashboard/status | python3 -m json.tool
```

### Vollständige Routen-Liste

<details>
<summary><strong>76 HTTP-Routen</strong> (klick zum Ausklappen)</summary>

| Methode | Pfad |
|---------|------|
| GET | `/` |
| GET | `/activity/` |
| GET | `/api/activity/log` |
| GET, POST | `/api/aufgaben` |
| GET | `/api/briefing/config` |
| POST | `/api/briefing/config` |
| GET | `/api/briefing/info` |
| GET | `/api/briefing/render` |
| POST | `/api/briefing/run` |
| POST | `/api/chat/delete/<int:chat_id>` |
| GET | `/api/chat/download/<filename>` |
| GET | `/api/chat/list` |
| GET | `/api/chat/messages` |
| POST | `/api/chat/new` |
| GET | `/api/chat/picker/browse` |
| POST | `/api/chat/send` |
| GET | `/api/chat/shared/browse` |
| GET | `/api/chat/shared/file/<path:filename>` |
| POST | `/api/chat/shared/folder` |
| POST | `/api/chat/shared/folder/exchange` |
| POST | `/api/chat/shared/folder/upload` |
| GET | `/api/chat/shared/read` |
| POST | `/api/chat/shared/write` |
| POST | `/api/chat/upload` |
| GET | `/api/dashboard/status` |
| GET | `/api/pages` |
| POST | `/api/quick-prompt` |
| GET | `/api/references` |
| GET, PUT | `/api/references/<path:url_key>` |
| DELETE | `/api/references/<path:url_key>` |
| GET | `/api/refresh` |
| GET | `/api/settings/app` |
| POST | `/api/settings/app` |
| POST | `/api/settings/app/ssh/generate` |
| GET | `/api/settings/app/ssh/status` |
| POST | `/api/settings/app/test` |
| GET | `/api/settings/memories` |
| POST | `/api/settings/memories/<file_key>` |
| DELETE, PUT | `/api/settings/memories/<file_key>/<int:entry_index>` |
| GET, POST | `/api/settings/memory` |
| GET | `/api/settings/skill-content` |
| POST | `/api/settings/skill-content` |
| DELETE | `/api/settings/skill-content` |
| GET | `/api/settings/skills` |
| GET, POST | `/api/settings/tasks` |
| DELETE, PUT | `/api/settings/tasks/<task_id>` |
| POST | `/api/settings/tasks/<task_id>/run` |
| GET | `/api/settings/usage` |
| GET | `/api/system-status` |
| GET | `/api/uploads` |
| DELETE | `/api/uploads/<filename>` |
| GET | `/api/wiki/export` |
| POST | `/api/wiki/import` |
| GET | `/blog/` |
| GET | `/blog/<path:filename>` |
| GET | `/briefing/` |
| GET | `/chat/` |
| GET | `/concept/<page_id>` |
| GET, POST | `/delete/<section>/<page_id>` |
| GET, POST | `/edit/<section>/<page_id>` |
| GET | `/entity/<page_id>` |
| GET | `/explorer/` |
| GET | `/explorer/<path:subpath>` |
| POST | `/explorer/delete` |
| POST | `/explorer/mkdir` |
| POST | `/explorer/upload` |
| GET | `/favicon.ico` |
| GET, POST | `/new` |
| GET | `/search` |
| GET | `/settings/` |
| GET | `/static/<path:filename>` |
| GET | `/static/uploads/<filename>` |
| GET | `/tags` |
| POST | `/upload/image` |
| GET | `/wiki` |
| GET | `/wiki/` |

</details>

---

## 🛠️ Troubleshooting

| Symptom | Lösung |
|---------|--------|
| Portal lädt, aber keine Agent-Verbindung | SSH manuell testen: `ssh -p 22 root@<agent-ip> "echo ok"`. Klappt das nicht, blockt Firewall oder sshd läuft nicht. |
| SSH-Key wird abgelehnt | Auf dem Agent: `chmod 600 ~/.ssh/authorized_keys`, `chmod 700 ~/.ssh`, `chown -R root:root ~/.ssh`. |
| Monaco-Editor leer im Chat | `python _wiki_server/scripts/fetch_monaco.py` erneut ausführen (nur bei Source-Install — Docker/Desktop bündeln Monaco bereits). |
| Wiki-Seiten erscheinen nicht | `exchange_path` in Settings prüfen — muss auf den richtigen Share zeigen. |
| News/RSS lädt nicht | Feed-URL im Browser testen; manche Feeds sind CORS-geschützt. |
| Briefing aktualisiert sich nicht | `hermes cron list` auf dem Agent prüfen. |
| Docker-Container startet nicht | `docker compose logs` — meist Port-8090-Konflikt oder Volume-Permissions. |
| macOS PKG: „Beschädigt, kann nicht geöffnet werden" | `xattr -dr com.apple.quarantine ~/Downloads/Hermes-Portal-macOS.pkg` vor dem Doppelklick. |
| Windows SmartScreen-Warnung | *Weitere Informationen* → *Trotzdem ausführen*. Wir haben kein EV-Code-Signing-Cert. |
| HA-Add-on Find-IP zeigt Container-Subnetz | Portal läuft im HA-Docker-Netz — manuelles LAN-Subnetz (`192.168.x`) im Scan-Feld eingeben. |
| Mac-App startet nicht (1 s offen, dann zu) | `cat ~/Desktop/hermes-portal-trace.log` zeigt, an welcher Stelle es klemmt. |

**Smoke-Tests nach Installation:**

```bash
curl -s http://localhost:8090/api/refresh
curl -s http://localhost:8090/api/settings/app | python3 -m json.tool
curl -s http://localhost:8090/api/dashboard/status | python3 -m json.tool
```

---

## ❤️ Support

Wenn dir das Projekt gefällt:

- 💙 [PayPal](https://www.paypal.me/quadFlyerFW)
- ☕ [Ko-fi](https://ko-fi.com/jayjojayson)
- ⭐ Star dem [Repository](https://github.com/jayjojayson/Hermes-Portal)
- 💬 [Discussions](https://github.com/jayjojayson/Hermes-Portal/discussions) für Fragen + Ideen
- 🐞 [Issues](https://github.com/jayjojayson/Hermes-Portal/issues) für Bug-Reports

---

## 📄 Lizenz

[Apache License 2.0](LICENSE) — frei für privaten und kommerziellen Gebrauch,
inkl. expliziter Patent-Grant. Beim Weitergeben muss eine Kopie der Lizenz
beiliegen; modifizierte Dateien sollen entsprechend gekennzeichnet werden.
