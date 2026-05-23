# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Spec für Hermes Portal — Mac/Linux/Windows One-Folder-Build.

Build:
    cd _wiki_server
    pyinstaller --noconfirm hermes_portal.spec

Output: dist/hermes-portal/  (komplettes Verzeichnis mit Binary + Assets)
"""
from PyInstaller.utils.hooks import collect_submodules
import os
import sys

block_cipher = None

# Auf macOS ad-hoc signieren — PyInstaller signiert dabei jeden Mach-O
# während des Builds in der korrekten Reihenfolge (libs vor Bundle).
# Das ist robuster als Post-hoc-Signing per Bash-Script. Unser
# scripts/sign_macos_app.py läuft trotzdem nochmal als Safety-Net im
# Workflow.
_codesign = "-" if sys.platform == "darwin" else None

# Templates + statische Assets ins Bundle aufnehmen.
# WICHTIG: i18n/-Verzeichnis muss explizit dabei sein, sonst returned t()
# auf Windows/Mac den Raw-Key („dashboard.hermes") statt der Übersetzung
# („Hermes") — Bug aus v1.1.2.
datas = [
    ("templates", "templates"),
    ("static",    "static"),
    ("i18n",      "i18n"),
    ("config.defaults.json", "."),
    ("__version__.py",       "."),
]

# Verstecktes/dynamisches Importe (paramiko etc.)
hiddenimports = (
    collect_submodules("paramiko")
    + collect_submodules("flask")
    + collect_submodules("markdown")
    + collect_submodules("waitress")
)
# pywebview ist optional (nur Desktop-Builds, nicht HA-Container) — wenn
# installiert, in die hidden_imports aufnehmen, damit das native Fenster
# im Bundle funktioniert.
try:
    import webview  # noqa: F401
    hiddenimports += collect_submodules("webview")
except ImportError:
    pass

a = Analysis(
    ["entry_pyinstaller.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="hermes-portal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # macOS: console=False vermeidet Crash beim Finder-Doppelklick (kein
    # Controlling-Terminal → PyInstaller-Bootloader stürzt mit console=True
    # in einigen Versionen lautlos ab, genau das Symptom in v1.0.3-1.0.6).
    # Windows/Linux: bleibt True für Power-User die per CLI starten.
    console=False if sys.platform == "darwin" else True,
    icon=os.path.join("static", "portal", "logo.png") if os.path.exists(os.path.join("static", "portal", "logo.png")) else None,
    codesign_identity=_codesign,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="hermes-portal",
)
