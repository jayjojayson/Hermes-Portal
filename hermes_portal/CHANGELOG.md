# Hermes Portal — Add-on Changelog

> Home Assistant Supervisor zeigt diese Datei beim Update.
> Vollständige Projekt-History: siehe `CHANGELOG.md` im Repo-Root.

## 1.1.8

- **🚀 Update-Banner** auf allen Pages — meldet automatisch, wenn auf GitHub
  eine neuere Version verfügbar ist (HA-User updaten weiterhin über den
  Supervisor; der Banner ist primär für Desktop-/Docker-Installationen,
  zeigt aber auch hier den Hinweis korrekt).
- **🔐 Private-Key anzeigen für Migration** — neuer „Reveal"-Button im
  SSH-Wizard (Settings → 🛰️ App), zum Übernehmen des Portal-Keys auf
  weitere Installationen ohne `authorized_keys` anzufassen.
- **📋 Aufgaben-Page funktioniert direkt** — Default-`aufgaben.md` wird
  beim ersten Aufruf automatisch angelegt; eine native Tasks-Page mit
  „➕ Aufgabe hinzufügen"-Form steht als Fallback bereit, wenn der
  Hermes-Agent noch kein `aufgaben.html` generiert hat.
- **⬅️ Sidebar via Klick-Button öffnen** statt Hover am linken Rand —
  vermeidet Konflikte mit der Home-Assistant-Sidebar im HA-Frontend.
- **💬 Chat-Eingabefeld leert sich nach Send** (vorher blieb der Text drin).
- **🌐 Dashboard- und Sidebar-Empty-States** komplett in en/de/es/fr.
- **🚮 Slash-Command-Dropdown im Chat entfernt** (war nicht funktional).

## 1.1.7

- **📥 SSH-Key importieren statt generieren** — bestehenden Private-Key
  in Settings → 🛰️ App per Copy&Paste einfügen, Portal leitet den
  Public-Key automatisch ab. Praktisch beim Umzug oder Multi-Device-Setup
  — `authorized_keys` auf dem Agent muss nicht angefasst werden.
- **💾 Settings-Save-Bar komplett übersetzt** (vorher partiell deutsch
  hartkodiert).
- **README konsolidiert**: ausführliche Troubleshooting- und
  First-Time-Configuration-Sektionen mit Tabelle für alle App-Settings,
  inkl. macOS-PKG-Quarantäne-Hinweis und HA-Container-Subnetz-Tipp.

## 1.1.6

- **🔎 Find-IP versteht Container** — erkennt HA-Add-on-Subnetz
  (172.x.x.x) und bietet manuelles LAN-Subnetz-Eingabefeld an, weil
  das Portal aus dem Container das User-LAN sonst nicht sieht.
- **📁 Wiki Import/Export-Layout**: Import + Dropdown in einer Zeile,
  Export-Button separat darunter. Dropdown läuft nicht mehr über den
  Box-Rand.

## 1.1.5

- **Slash-Commands gehen wieder nativ an den Agent** — Portal-seitige
  Interceptoren raus, `/usage`/`/new`/`/reset` etc. werden 1:1 zum Agent
  gesendet wie jede andere Chat-Nachricht.
- **🔎 LAN-Discovery für SSH-Host** — neuer „Find IP"-Button in
  Settings → 🛰️ App scant das lokale Netzwerk nach SSH-fähigen Hosts
  und übernimmt die IP per Klick.
- **Wiki Import/Export** auf Desktop in einer Zeile (vorher zwei).
- **Support-Tab vollständig übersetzt** in 4 Sprachen + neuer
  Version-Info-Block mit Update-Hinweis.

## 1.1.4

- **Slash-Commands intelligent gemacht**: `/usage`, `/new`, `/reset`,
  `/stop`, `/help`, `/quit` werden vom Portal direkt behandelt
  (kein LLM-Halluzinieren mehr). Andere Befehle gehen weiter an den Agent.
- **SSH-Wizard komplett übersetzt**: alle Buttons + aufklappbare
  Hilfe-Texte in 4 Sprachen.

## 1.1.3

- **Slash-Commands-Dropdown im Chat** — Hermes-CLI-Befehle (`/new`,
  `/reset`, `/stop`, `/model`, …) als Schnellauswahl rechts neben
  dem Ordner-Picker. Klick sendet den Befehl direkt im Chat.
- **🎤 Mikrofon-Button** mit klar erkennbarem SVG-Icon.
- **🤖 Agent-Avatar** zeigt Roboter-Kopf statt Herz.
- **i18n weiter**: Personality-Tab + Skills-Tab.
- **Bug-Fix Desktop-Bundles**: i18n-Strings (z.B. „Hermes" statt
  „Dashboard.Hermes") werden in PyInstaller-Builds wieder korrekt
  geladen — `i18n/` war nicht im Bundle.

## 1.1.2

- **Mobile-Padding**: Cards/Boxen kleben auf dem Handy nicht mehr am
  Display-Rand (5 px Seitenrand bei `<768px` Viewport).
- **Settings → App-Tab**: Connection-Sektion und Identity-Sektion
  vollständig auf i18n umgestellt.

## 1.1.1

- **Briefing-Seite** rendert jetzt direkt das Agent-HTML (wie News/
  Aufgaben), kein iframe-Border, kein doppelter Wrapper-Header.
- **Floating Action Buttons** auf der Briefing-Seite: ▶ Erzeugen / 🔄 Reload.
- **Chat-Editor-Hintergrund**: jetzt #1a1d24 (matched File-Tree-Spalte).
- **i18n auf 276 Keys × 4 Sprachen**: Explorer, Cronjob-Modal,
  Personality/Skills/References/Usage/Support-Tabs.
- **Briefing-Konfiguration** (GitHub, Wetter, BVG) wieder zugänglich
  in Settings → 🛰️ App.

## 1.1.0

- **Briefing-iframe**: doppelter Header (vom Agent-HTML) wird
  rausgestrippt, Briefing-Überschrift sitzt direkt am Top.
- **Chat-Editor**: vollständiges Monaco-Theme (Dark/Light) passend
  zum Portal-Look — Hintergrund, Gutter, Cursor, Selection.
- **Activity-Seite** übersetzt.
- **Mehr Detail-Strings** in 4 Sprachen.

## 1.0.10

- **Briefing-Seite** sieht im Portal-Style aus (Portal-CSS injiziert,
  hardcoded /blog/... URLs umgeschrieben, iframe-Höhe vergrößert).
- **Chat-Editor** lädt Monaco wieder unter Ingress (loader.js per
  url_for statt JS-Patcher).
- **Sprachwechsel** reloadet die Seite automatisch — keine wilde
  Sprach-Vermischung mehr.
- **🕐 Zeitzonen-Anzeige** der Cronjobs in deiner Browser-TZ (z.B.
  UTC+2 statt rohem UTC). TZ-Hinweis in Settings → Cronjobs sichtbar.
- **Mehr Übersetzungen**: Chat, Briefing-Config, Wiki-Index.

## 1.0.9

- **i18n vollständig** für Dashboard, Settings (alle Sektionen + Hilfe-
  Texte), Blog-Missing-Page. ~600 Übersetzungen in en/de/es/fr.
- Tageszeit-abhängige Greetings („Buenos días" / „Good morning" / …).
- Detail-Templates (Wiki-Index, Chat, Briefing-Settings, Activity,
  Explorer) folgen in den nächsten Patches.

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
