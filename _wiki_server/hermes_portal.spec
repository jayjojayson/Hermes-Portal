# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Spec für Hermes Portal — Mac/Linux/Windows One-Folder-Build.

Build:
    cd _wiki_server
    pyinstaller --noconfirm hermes_portal.spec

Output: dist/hermes-portal/  (komplettes Verzeichnis mit Binary + Assets)
"""
from PyInstaller.utils.hooks import collect_submodules
import os

block_cipher = None

# Templates + statische Assets ins Bundle aufnehmen
datas = [
    ("templates", "templates"),
    ("static",    "static"),
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
    console=True,
    icon=os.path.join("static", "portal", "logo.png") if os.path.exists(os.path.join("static", "portal", "logo.png")) else None,
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
