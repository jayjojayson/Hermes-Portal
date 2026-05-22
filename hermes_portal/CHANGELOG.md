# Hermes Portal — Add-on Changelog

> Home Assistant Supervisor zeigt diese Datei beim Update.
> Vollständige Projekt-History: siehe `CHANGELOG.md` im Repo-Root.

## 1.0.3

- Keine HA-spezifischen Änderungen — Release ist primär ein
  macOS-Desktop-Launch-Fix.

## 1.0.2

- Keine HA-spezifischen Änderungen — Release ist primär ein mac-Sign-Fix.
- **Hinweis zum Panel-Icon:** falls `mdi:robot-happy` nach diesem Update
  immer noch nicht erscheint, einmal Add-on deinstallieren + neu
  installieren (HA-Supervisor cached die Panel-Registration vom
  Install-Zeitpunkt; Add-on-Daten in `/data/` bleiben erhalten).

## 1.0.1

- **Logo im Header** wird wieder angezeigt (Ingress-Prefix-Fix in
  `site-header.js`).
- **Panel-Icon** in der HA-Sidebar von `satellite-uplink` auf
  `robot-happy` (`mdi:robot-happy`).
- **News/Aufgaben/Briefing 404** zeigt jetzt eine erklärende Seite —
  diese Inhalte werden vom Hermes-Agent erzeugt, nicht vom Portal.
- **Update-Check** (Sidebar-Footer) ist hier irrelevant — HA-Supervisor
  zeigt Updates eh selbst an.

## 1.0.0

- **HA-Ingress-Layout-Bug behoben** — Asset-URLs (CSS/JS/Logo) und
  API-Calls werden jetzt automatisch um den Ingress-Prefix ergänzt.
  Header und Styling laden wieder korrekt im HA-Sidebar-Panel.

## 0.9.0

- Container startet wieder: `tini` liegt auf Alpine unter `/sbin/tini`
  (nicht `/usr/bin/tini` wie auf Debian).
- macOS-Sign-Loop 10× schneller (Release-Workflow).

## 0.8.0

- `build.yaml` minimiert: nur noch `build_from:`.
- OCI-Labels via `LABEL`-Direktiven im Dockerfile.

## 0.7.0

- Add-on self-contained: Dockerfile zieht Portal-Sourcen per
  `git clone --branch v${BUILD_VERSION}` aus GitHub. Kein
  `prepare.sh`-Lauf vor dem Build mehr nötig.
- Add-on-Logo + -Icon im Repo-Root des Add-ons.
