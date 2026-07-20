# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

datas = []
if os.path.isfile("icon.ico"):
    datas.append(("icon.ico", "."))

# On Windows, bundle the MSVC runtime so the .exe runs without the user first
# installing the "Visual C++ Redistributable". PyInstaller ships Qt and Python but
# not these system DLLs, and Qt6Core.dll depends on them (their absence is the
# classic "DLL load failed while importing QtCore" error). No-op on Linux.
binaries = []
if sys.platform == "win32":
    _system32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    for _name in (
        "vcruntime140.dll",
        "vcruntime140_1.dll",
        "msvcp140.dll",
        "msvcp140_1.dll",
        "msvcp140_2.dll",
        "concrt140.dll",
    ):
        _path = os.path.join(_system32, _name)
        if os.path.isfile(_path):
            binaries.append((_path, "."))

analysis = Analysis(
    ["run.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
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
