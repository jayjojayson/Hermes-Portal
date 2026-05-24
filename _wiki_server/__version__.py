"""Hermes Portal — Version-Konstante (einzige Quelle der Wahrheit).

Bei Releases wird VERSION hier (und in den GitHub-Tags) angehoben. Das
Backend liefert sie via :func:`get_config().version` an Templates und an
``site-header.js`` weiter, damit die Sidebar den Wert anzeigt.
"""
VERSION = "1.1.4"
