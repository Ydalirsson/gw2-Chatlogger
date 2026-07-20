#!/usr/bin/env bash
# Build a portable Linux AppImage of the GW2 Chat Logger viewer.
#
# Requirements: a Python with the project deps + PyInstaller installed
#   pip install -r requirements.txt -r requirements-dev.txt
# Point PYTHON at that interpreter (defaults to `python`), e.g.
#   PYTHON=.venv/bin/python packaging/build-appimage.sh
#
# appimagetool is downloaded on first run. Output:
#   dist/gw2chatlogger-x86_64.AppImage
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

PY="${PYTHON:-python}"
NAME="gw2chatlogger"
APPDIR="build/AppDir"

echo ">> PyInstaller (onedir)"
# --specpath build keeps PyInstaller's generated spec out of the repo root, so it
# never clobbers the hand-maintained onefile gw2chatlogger.spec. With a custom
# specpath PyInstaller resolves relative paths against the spec dir, so pass the
# script and data as absolute paths.
"$PY" -m PyInstaller "$root/run.py" \
  --name "$NAME" --onedir --windowed --noconfirm --clean \
  --specpath build \
  --add-data "$root/icon.ico:."

echo ">> Assembling AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp -a "dist/$NAME/." "$APPDIR/usr/bin/"

# Icon: AppImage wants a PNG/SVG. Convert the bundled .ico via PySide6 (already a
# dependency), so we need no extra image tooling.
QT_QPA_PLATFORM=offscreen "$PY" - "$APPDIR/$NAME.png" <<'PY'
import sys
from PySide6.QtGui import QImage
img = QImage("icon.ico")
if img.isNull():
    raise SystemExit("could not load icon.ico")
if not img.save(sys.argv[1]):
    raise SystemExit("could not write PNG icon")
PY

cat > "$APPDIR/$NAME.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=GW2 Chat Logger
Comment=Live view and session recording for GW2 party/squad chat
Exec=$NAME
Icon=$NAME
Categories=Utility;
Terminal=false
EOF

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/gw2chatlogger" "$@"
EOF
chmod +x "$APPDIR/AppRun"

echo ">> Fetching appimagetool"
tool="build/appimagetool-x86_64.AppImage"
if [ ! -x "$tool" ]; then
  curl -fL -o "$tool" \
    https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x "$tool"
fi

echo ">> Building AppImage"
mkdir -p dist
# --appimage-extract-and-run avoids needing FUSE (works in CI / containers).
ARCH=x86_64 "$tool" --appimage-extract-and-run "$APPDIR" "dist/${NAME}-x86_64.AppImage"

echo ">> Done: dist/${NAME}-x86_64.AppImage"
