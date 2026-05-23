# Hermes Portal — Add-on Changelog

> Home Assistant Supervisor zeigt diese Datei beim Update.
> Vollständige Projekt-History: siehe `CHANGELOG.md` im Repo-Root.

## 1.0.8

- **Briefing-Seite** zeigt wieder den Inhalt (iframe-Ingress-Fix).
- **Chat-Editor** lädt Monaco korrekt unter Ingress (Pfad-Prefix-Fix).
- **🌐 Mehrsprachiges UI** — Sprache wählbar in Settings → 🛰️ App:
  Englisch (Default), Deutsch, Spanisch, Französisch. Inhalte vom
  Agenten (News, Briefing) werden nicht übersetzt.
- **Hilfe-Box** in Settings → App erklärt die empfohlene
  Ordner-Struktur (`/wiki/scripts`, `/wiki/blog`) und das RSS-Feed-
  Verhalten (Portal vs. News-Generator).

## 1.0.7

- Keine HA-spezifischen Änderungen — Release ist primär ein macOS-
  Native-Window-Sprung (kein Browser/Terminal mehr beim Desktop-DMG).
  HA-Container nutzt weiterhin gunicorn ohne pywebview.

## 1.0.6

- **Wiki-Beiträge öffnen** jetzt korrekt (404 in HA behoben — globaler
  Ingress-Prefix-Patcher für `<a>`/`<img>`/`<link>`/`<script>` + dynamische
  DOM-Mutations via MutationObserver).
- **Pfade in Settings → 🛰️ App resetten nicht mehr** — HA-Add-on-Options
  überschreiben jetzt nur noch beim allerersten Container-Start die
  Defaults, UI-Edits sind danach sticky.
- **Aufgaben / News / Briefing** bekommen jetzt unser Portal-Stylesheet
  eingebunden — Cards, Buttons, Farben sehen aus wie der Rest.
- **App-Tab-Logo** wird wieder angezeigt (war derselbe Ingress-Bug).

## 1.0.5

- **Aufgaben / News / Briefing zeigen Layout + Header korrekt** im HA-
  Sidebar-Panel — vom Hermes-Agent generierte HTML-Files werden jetzt
  beim Ausliefern um den Ingress-Prefix ergänzt (CSS, JS, Logo, Links).
- **Settings → 🛰️ App → „📑 Menü-Punkte sichtbar"**: Buttons kürzer
  beschriftet („📰 News anzeigen"), alle 4 passen jetzt nebeneinander.

## 1.0.4

- **SSH-Verbindung robuster** — Banner-Timeout 15→30 s, neuer Single-
  Retry bei `Error reading SSH protocol banner` (typisch für HA-Add-on
  Container-Netzwerke beim ersten Verbinden).

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
