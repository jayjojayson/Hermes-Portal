# Hermes Portal — Home Assistant Add-on

## Installation

1. In Home Assistant: **Einstellungen → Add-ons → Add-on Store → ⋮ → Repositories**.
2. URL deines Forks/Repos eintragen, z.B. `https://github.com/USER/hermes-portal`.
3. Add-on **Hermes Portal** auswählen und installieren.
4. Konfiguration setzen (siehe Optionen unten), dann starten.
5. Öffne den Reiter über die Sidebar (Ingress) oder direkt `http://<ha-ip>:8090`.

## Konfiguration

| Option            | Beschreibung                                            | Default          |
|-------------------|---------------------------------------------------------|------------------|
| `agent_name`      | Name deines Hermes-Agents (statt "Wally")               | `Hermes`         |
| `user_name`       | Wie der Agent dich anspricht                            | `Du`             |
| `connection_mode` | `local` (im HA-Host) oder `ssh` (Hermes auf anderem PC) | `ssh`            |
| `agent_host`      | IP/Hostname des Hermes-Agents (bei SSH-Mode)            | `""`             |
| `ssh_user`        | SSH-User auf dem Hermes-Host                            | `root`           |
| `ssh_port`        | SSH-Port                                                | `22`             |
| `ssh_password`    | Optional, falls kein Key verwendet wird                 | `""`             |
| `exchange_path`   | Pfad zum Austausch-Ordner auf dem Hermes-Host           | `/share`         |

Weitere Settings (RSS-Feeds, Persönlichkeit, Pfade) konfigurierst du **nach** dem Start
direkt in der Portal-UI unter `⚙️ Settings → 🛰️ App`.

## SSH-Key statt Passwort

In der Portal-UI unter Settings → App den Pfad `/data/.ssh/id_ed25519` eintragen.
Lege den Key in deinem HA `/addon_configs/<slug>/ssh/` ab, dann ist er im Container unter
`/data/.ssh/` verfügbar (Volume-Mapping ist im `config.yaml` voreingestellt).
