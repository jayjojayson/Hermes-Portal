#!/usr/bin/env python3
"""Hermes Portal — Default News Generator
=========================================

Liest RSS-Feeds, baut für jeden Tagesabschnitt (morgens/mittags/nachmittags)
einen HTML-Bericht unter ``<BLOG_DIR>/posts/<datum>-<slug>.html`` und schreibt
parallel eine ``<BLOG_DIR>/posts.json`` mit der Liste aller Beiträge, die das
Hermes Portal auf der /news/-Seite anzeigt.

Konfiguration (ENV, vom Portal beim Cronjob-Aufruf gesetzt):
    PORTAL_BLOG_DIR     — Absoluter Pfad zu blog/ (z.B. /mnt/austausch/wiki/blog)
    PORTAL_POSTS_SUBDIR — Subordner für Einzel-HTMLs (Default: ``posts``)
    NEWS_RSS_FEEDS      — JSON-Liste, z.B.
                          [{"name":"Heise","url":"https://www.heise.de/rss/heise-atom.xml"}]
    PORTAL_AGENT_NAME   — Anzeige-Name im HTML-Footer
    PORTAL_USER_NAME    — Eigentümer-Name im HTML-Footer

Wenn die ENV-Variablen fehlen werden vernünftige Defaults benutzt. So kannst
du das Script auch ohne Portal manuell testen:

    PORTAL_BLOG_DIR=/tmp/blog python3 blog_generator.py

Ein politischer Filter (`is_political`) entfernt offensichtliche Politik-
schlagzeilen — anpassen wenn unerwünscht.

Dieses Skript ist Public Domain (CC0). Friemel es nach Geschmack um.
"""
from __future__ import annotations

import datetime
import html
import json
import os
import re
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

# ─── Konfiguration aus ENV ─────────────────────────────────────────────
BLOG_DIR     = Path(os.environ.get("PORTAL_BLOG_DIR", "/mnt/austausch/wiki/blog"))
POSTS_SUBDIR = os.environ.get("PORTAL_POSTS_SUBDIR", "posts")
AGENT_NAME   = os.environ.get("PORTAL_AGENT_NAME", "Wally")
USER_NAME    = os.environ.get("PORTAL_USER_NAME", "Jan")

DEFAULT_FEEDS = [
    {"name": "Heise News",          "url": "https://www.heise.de/rss/heise-atom.xml"},
    {"name": "t3n",                 "url": "https://t3n.de/rss.xml"},
    {"name": "Golem",               "url": "https://rss.golem.de/rss.php?feed=ATOM1.0"},
]
try:
    _feeds_env = os.environ.get("NEWS_RSS_FEEDS", "").strip()
    FEEDS = json.loads(_feeds_env) if _feeds_env else DEFAULT_FEEDS
    if not isinstance(FEEDS, list) or not FEEDS:
        FEEDS = DEFAULT_FEEDS
except (ValueError, TypeError):
    FEEDS = DEFAULT_FEEDS

POSTS_DIR = BLOG_DIR / POSTS_SUBDIR
POSTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Politik-Filter (einfache Heuristik) ──────────────────────────────
POLITICAL_KEYWORDS = [
    "wahl", "wahlen", "partei", "kanzler", "bundestag", "afd", "spd", "cdu",
    "grüne", "fdp", "präsident", "regierung", "minister", "trump", "biden",
    "putin", "ukraine-krieg", "gaza", "israel", "palästina",
]
def is_political(text: str) -> bool:
    low = (text or "").lower()
    return any(kw in low for kw in POLITICAL_KEYWORDS)

# ─── RSS-Parser (lightweight, ohne Dependencies) ──────────────────────
def fetch_feed(url: str, timeout: int = 10) -> list[dict]:
    """Liest RSS/Atom, gibt Liste mit dict-Posts zurück."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Hermes-Portal-BlogGenerator/1.0",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except (urllib.error.URLError, OSError, TimeoutError) as ex:
        print(f"  ⚠️  {url}: {ex}", file=sys.stderr)
        return []

    items: list[dict] = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as ex:
        print(f"  ⚠️  {url} (XML parse): {ex}", file=sys.stderr)
        return []

    # Atom oder RSS — beides unterstützen
    ns = {"a": "http://www.w3.org/2005/Atom"}
    is_atom = root.tag.endswith("feed")
    if is_atom:
        for entry in root.findall("a:entry", ns):
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
            link_el = entry.find("a:link", ns)
            link = link_el.get("href") if link_el is not None else ""
            summary = (entry.findtext("a:summary", default="", namespaces=ns)
                       or entry.findtext("a:content", default="", namespaces=ns) or "").strip()
            published = (entry.findtext("a:updated", default="", namespaces=ns)
                         or entry.findtext("a:published", default="", namespaces=ns) or "")
            items.append({"title": title, "url": link, "summary": _strip_html(summary)[:400],
                          "date": published})
    else:
        # Klassisches RSS 2.0
        for entry in root.iter("item"):
            title = (entry.findtext("title") or "").strip()
            link = (entry.findtext("link") or "").strip()
            summary = (entry.findtext("description") or "").strip()
            published = (entry.findtext("pubDate") or "")
            # Bild aus enclosure oder media:thumbnail
            img = ""
            for enc in entry.iter():
                tag = enc.tag.split("}")[-1].lower()
                if tag in ("enclosure", "thumbnail", "content"):
                    url2 = enc.get("url")
                    if url2 and any(url2.lower().endswith(e) for e in (".jpg",".jpeg",".png",".webp",".gif")):
                        img = url2
                        break
            items.append({"title": title, "url": link, "summary": _strip_html(summary)[:400],
                          "date": published, "image": img})
    return items


_TAG_RE = re.compile(r"<[^>]+>")
def _strip_html(s: str) -> str:
    return html.unescape(_TAG_RE.sub("", s or "").strip())


# ─── Berichts-Generator ──────────────────────────────────────────────
def slot_for_hour(h: int) -> tuple[str, str]:
    """(slug, label) für eine gegebene Stunde."""
    if h < 11:
        return ("morgendlicher-tech-ueberblick", "Morgendlicher Tech-Überblick")
    if h < 16:
        return ("mittags-update-tech-news", "Mittags-Update: Die wichtigsten Tech-News")
    return ("nachmittags-spotlight-hardware-trends", "Nachmittags-Spotlight: Hardware & Trends")


def build_post(now: datetime.datetime) -> dict:
    """Sammelt alle Feeds, filtert Politik, erzeugt einen Tagesbericht."""
    slot_slug, slot_label = slot_for_hour(now.hour)
    date_str = now.strftime("%Y-%m-%d")
    date_human = now.strftime("%d.%m.%Y")
    slug = f"{date_str}-{slot_slug}-{now.strftime('%d-%m-%Y')}"
    filename = f"{slug}.html"

    sections: dict[str, list[dict]] = {}
    for feed in FEEDS:
        name = feed.get("name", "RSS")
        items = fetch_feed(feed["url"])
        kept = []
        for it in items[:5]:  # max. 5 pro Feed
            if is_political(it["title"]) or is_political(it.get("summary", "")):
                continue
            it["source"] = name
            kept.append(it)
        if kept:
            sections[name] = kept

    # HTML rendern
    html_parts: list[str] = []
    html_parts.append(f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(slot_label)} – {date_human}</title>
<link rel="icon" href="/static/portal/logo.png" type="image/png">
<link rel="stylesheet" href="/blog/style.css">
<script src="/blog/site-header.js" defer></script>
</head>
<body data-page="news">
<div id="site-header"></div>
<main>
<article class="post full">
<h2>{html.escape(slot_label)} – {date_human}</h2>
<p class="meta">{date_str} | Quellen: {", ".join(html.escape(s) for s in sections)}</p>
<div class="content">""")

    for section_name, items in sections.items():
        html_parts.append(f"<h3>{html.escape(section_name)}</h3>")
        html_parts.append('<div class="news-grid">')
        for it in items:
            img = it.get("image", "")
            img_html = (f'<div class="news-img"><img src="{html.escape(img)}" '
                        'alt="" loading="lazy" onerror="this.parentElement.remove()"></div>'
                        if img else "")
            html_parts.append(f"""<div class="news-item">
{img_html}
<h4 class="news-title">{html.escape(it["title"])}</h4>
<div class="news-summary">
  <p class="news-desc">{html.escape(it.get("summary",""))}</p>
  <button class="read-more-btn" onclick="toggleArticle(this)">Weiterlesen</button>
</div>
<div class="news-full">
  <p>{html.escape(it.get("summary",""))}</p>
  <a href="{html.escape(it.get("url",""))}" class="external-link" target="_blank" rel="noopener">
    Vollständigen Artikel auf {html.escape(it["source"])} lesen →
  </a>
</div>
<p class="news-meta"><span class="source">Quelle: {html.escape(it["source"])}</span> | {html.escape(it.get("date",""))}</p>
</div>""")
        html_parts.append("</div>")

    html_parts.append(f"""</div>
<p class="back-link"><a href="/news/">← Zurück zur Übersicht</a></p>
</article>
</main>
<footer><p>© {now.year} {html.escape(USER_NAME)} · generiert von {html.escape(AGENT_NAME)}</p></footer>
</body>
</html>""")

    (POSTS_DIR / filename).write_text("\n".join(html_parts), encoding="utf-8")

    # Hero-Bild für die Übersicht: erstes verfügbares Bild aus den Items
    hero = ""
    for items in sections.values():
        for it in items:
            if it.get("image"):
                hero = it["image"]
                break
        if hero:
            break

    return {
        "title":      f"{slot_label} – {date_human}",
        "slug":       slug,
        "path":       f"{POSTS_SUBDIR}/{filename}",
        "date":       date_str,
        "summary":    "; ".join(it["title"] for items in sections.values() for it in items[:3])[:300],
        "categories": list(sections.keys()),
        "tags":       ["news", "auto-generated", date_str, slot_slug.split('-')[0]],
        "image":      hero,
        "source":     ", ".join(sections.keys()),
    }


def main() -> int:
    now = datetime.datetime.now()
    print(f"📰 Generiere Tagesbericht für {now.strftime('%Y-%m-%d %H:%M')}…")
    new_post = build_post(now)
    print(f"  ✓ {new_post['path']}")

    # posts.json aktualisieren — vorhandene Liste laden, neuen Post oben
    # einfügen, doppelte slugs entfernen, max. 200 behalten.
    posts_json_path = BLOG_DIR / "posts.json"
    try:
        existing = json.loads(posts_json_path.read_text(encoding="utf-8")) if posts_json_path.exists() else []
        if isinstance(existing, dict):
            existing = existing.get("posts", [])
    except (OSError, json.JSONDecodeError):
        existing = []

    existing = [p for p in existing if p.get("slug") != new_post["slug"]]
    merged = [new_post] + existing
    merged = merged[:200]
    posts_json_path.write_text(json.dumps({"posts": merged}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ posts.json — {len(merged)} Beiträge insgesamt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
