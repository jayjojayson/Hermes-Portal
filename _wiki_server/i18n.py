"""Leichtgewichtige JSON-basierte Übersetzung für das Hermes Portal.

Statt schwergewichtiger Babel/gettext-Infrastruktur halten wir alle
Strings als flache Key→Value-Dicts in ``_wiki_server/i18n/<code>.json``.

Verwendung in Templates:

    {{ t('nav.dashboard') }}

In Python:

    from i18n import t
    t('button.save', lang='de')

Sprachen werden beim ersten Aufruf gelesen und im Prozess gecached.
Neue Sprachen einfach als ``<code>.json`` ins ``i18n/``-Verzeichnis
legen — sie werden automatisch verfügbar.

Fallback-Reihenfolge:
    1. requested lang
    2. English (canonical)
    3. Key selbst (zeigt fehlende Übersetzung sichtbar an)
"""
from __future__ import annotations
import json
import threading
from pathlib import Path
from typing import Any, Dict, List

_I18N_DIR = Path(__file__).resolve().parent / "i18n"
_TRANSLATIONS: Dict[str, Dict[str, str]] = {}
_LOCK = threading.RLock()


def _load_all() -> None:
    """Liest alle .json-Files aus i18n/ einmalig (idempotent)."""
    with _LOCK:
        if _TRANSLATIONS:
            return
        if not _I18N_DIR.is_dir():
            return
        for f in sorted(_I18N_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    _TRANSLATIONS[f.stem] = data
            except (OSError, json.JSONDecodeError):
                # Defekte Datei → nicht laden, aber andere weiter probieren.
                continue


def reload() -> None:
    """Cache leeren und neu laden (nach Hot-Edit der .json-Dateien)."""
    with _LOCK:
        _TRANSLATIONS.clear()
    _load_all()


def t(key: str, lang: str = "en") -> str:
    """Liefert die Übersetzung; fällt zurück auf en → key."""
    _load_all()
    table = _TRANSLATIONS.get(lang)
    if table and key in table:
        return table[key]
    en = _TRANSLATIONS.get("en") or {}
    if key in en:
        return en[key]
    return key


def available_languages() -> List[Dict[str, str]]:
    """Liste aller geladenen Sprachen für den UI-Switcher.

    Liefert z.B. ``[{"code":"en","name":"English","native":"English"}, …]``.
    """
    _load_all()
    out: List[Dict[str, str]] = []
    for code, data in sorted(_TRANSLATIONS.items()):
        out.append({
            "code":   code,
            "name":   data.get("_meta_name", code),
            "native": data.get("_meta_native", data.get("_meta_name", code)),
        })
    return out


def translation_table(lang: str = "en") -> Dict[str, str]:
    """Komplette Tabelle einer Sprache (für JS-Übergabe via window.HP_I18N)."""
    _load_all()
    en = _TRANSLATIONS.get("en") or {}
    table = _TRANSLATIONS.get(lang) or {}
    # Merge: en als Fallback-Layer, lang überschreibt
    merged: Dict[str, str] = dict(en)
    merged.update(table)
    # _meta-Keys aus Output ausschließen (interna)
    return {k: v for k, v in merged.items() if not k.startswith("_meta")}
