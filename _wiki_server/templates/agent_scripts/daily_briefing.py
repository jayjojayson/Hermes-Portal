#!/usr/bin/env python3
"""Hermes Portal — Default Daily Briefing
=========================================

Baut einen einfachen Tages-Briefing-Report unter
``<BLOG_DIR>/briefing.html`` zusammen — Wetter, optional ein Forum-RSS
und ein freundlicher Tagesspruch. Das Hermes Portal zeigt die Datei
direkt auf der /briefing/-Seite an.

Konfiguration (ENV, vom Portal beim Cronjob-Aufruf gesetzt):
    PORTAL_BLOG_DIR        — Absoluter Pfad zu blog/ (Default: /mnt/austausch/wiki/blog)
    BRIEFING_WEATHER_LAT   — Breitengrad (Default 52.52, Berlin)
    BRIEFING_WEATHER_LON   — Längengrad (Default 13.40)
    BRIEFING_WEATHER_TZ    — Zeitzone (Default Europe/Berlin)
    BRIEFING_FORUM_RSS     — Optionale Forum-Feed-URL
    BRIEFING_GITHUB_USER   — Optional, für GitHub-Aktivität
    PORTAL_AGENT_NAME / PORTAL_USER_NAME — Anrede

Manuell testen:
    PORTAL_BLOG_DIR=/tmp/blog python3 daily_briefing.py

Public Domain (CC0). Friemel es nach Geschmack um.
"""
from __future__ import annotations

import datetime
import html
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

BLOG_DIR   = Path(os.environ.get("PORTAL_BLOG_DIR", "/mnt/austausch/wiki/blog"))
LAT        = float(os.environ.get("BRIEFING_WEATHER_LAT") or 52.52)
LON        = float(os.environ.get("BRIEFING_WEATHER_LON") or 13.40)
TZ         = os.environ.get("BRIEFING_WEATHER_TZ") or "Europe/Berlin"
FORUM_RSS  = os.environ.get("BRIEFING_FORUM_RSS") or ""
GITHUB_USR = os.environ.get("BRIEFING_GITHUB_USER") or ""
AGENT_NAME = os.environ.get("PORTAL_AGENT_NAME", "Wally")
USER_NAME  = os.environ.get("PORTAL_USER_NAME", "Jan")

BLOG_DIR.mkdir(parents=True, exist_ok=True)


def fetch_weather() -> dict:
    """Open-Meteo-Snapshot (kostenlos, ohne Key)."""
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
               f"&current=temperature_2m,weather_code,wind_speed_10m"
               f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
               f"&timezone={urllib.parse.quote(TZ)}")
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Portal/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as ex:
        print(f"  ⚠️  Wetter-API: {ex}", file=sys.stderr)
        return {}


WMO_CODES = {
    0: "☀️ Klar", 1: "🌤 Überwiegend klar", 2: "⛅ Teils bewölkt", 3: "☁️ Bewölkt",
    45: "🌫 Nebel", 48: "🌫 Reifnebel",
    51: "🌧 Leichter Nieselregen", 53: "🌧 Nieselregen", 55: "🌧 Starker Nieselregen",
    61: "🌧 Leichter Regen", 63: "🌧 Regen", 65: "🌧 Starker Regen",
    71: "🌨 Leichter Schnee", 73: "🌨 Schnee", 75: "🌨 Starker Schnee",
    80: "🌦 Leichte Schauer", 81: "🌦 Schauer", 82: "⛈ Starke Schauer",
    95: "⛈ Gewitter", 96: "⛈ Gewitter mit Hagel", 99: "⛈ Schweres Gewitter",
}


def main() -> int:
    now = datetime.datetime.now()
    weather = fetch_weather()
    cur = (weather.get("current") or {})
    daily = (weather.get("daily") or {})

    weather_html = ""
    if cur:
        code = int(cur.get("weather_code", 0))
        cond = WMO_CODES.get(code, f"Code {code}")
        weather_html = f"""
<section class="briefing-section">
  <h3>🌤 Wetter</h3>
  <p>Aktuell: <strong>{cur.get("temperature_2m", "—")} °C</strong> · {html.escape(cond)} · Wind {cur.get("wind_speed_10m","—")} km/h</p>
  {f'<p>Heute: <strong>{daily.get("temperature_2m_min", ["—"])[0]} – {daily.get("temperature_2m_max", ["—"])[0]} °C</strong> · Niederschlag {daily.get("precipitation_sum", ["—"])[0]} mm</p>' if daily else ''}
</section>
"""

    forum_html = ""
    if FORUM_RSS:
        try:
            req = urllib.request.Request(FORUM_RSS, headers={"User-Agent": "Hermes-Portal/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.read())
                items = root.iter("item")
                links = []
                for it in list(items)[:5]:
                    t = (it.findtext("title") or "").strip()
                    u = (it.findtext("link") or "").strip()
                    if t and u:
                        links.append(f'<li><a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(t)}</a></li>')
                if links:
                    forum_html = f"""
<section class="briefing-section">
  <h3>💬 Forum</h3>
  <ul>{"".join(links)}</ul>
</section>
"""
        except Exception as ex:
            print(f"  ⚠️  Forum-RSS: {ex}", file=sys.stderr)

    out = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Briefing für {now.strftime('%d.%m.%Y')}</title>
<link rel="icon" href="/static/portal/logo.png" type="image/png">
<link rel="stylesheet" href="/blog/style.css">
<script src="/blog/site-header.js" defer></script>
</head>
<body data-page="briefing">
<div id="site-header"></div>
<main>
<article class="post full">
  <h2>☕ Briefing für {html.escape(USER_NAME)} – {now.strftime('%d.%m.%Y')}</h2>
  <p class="meta">Generiert um {now.strftime('%H:%M')} von {html.escape(AGENT_NAME)}</p>
  {weather_html}
  {forum_html}
</article>
</main>
<footer><p>© {now.year} {html.escape(USER_NAME)} · generiert von {html.escape(AGENT_NAME)}</p></footer>
</body>
</html>"""

    target = BLOG_DIR / "briefing.html"
    target.write_text(out, encoding="utf-8")
    print(f"  ✓ {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
