# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

block_cipher = None

hiddenimports = []
for name in ("easyocr", "torch", "torchvision", "pywinctl"):
    hiddenimports += collect_submodules(name)

datas = []
for name in ("easyocr",):
    datas += collect_data_files(name)

if os.path.isfile("icon.ico"):
    datas.append(("icon.ico", "."))

if os.path.isdir("models"):
    datas.append(("models", "models"))

analysis = Analysis(
    ["gw2chatlogger_app/main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name="gw2chatlogger",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon="icon.ico" if os.path.isfile("icon.ico") else None,
)
