#!/bin/bash
set -euo pipefail
# Build .AppImage for CTForge
# Usage: ./packaging/build-appimage.sh <version>  (e.g. 2.0.0)

VERSION="${1:?Usage: $0 <version>}"
APPDIR="CTForge.AppDir"

echo "[*] Building AppImage for CTForge v${VERSION} ..."

rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/scalable/apps"

# Binary (must be built first via PyInstaller)
cp dist/ctforge "${APPDIR}/usr/bin/ctforge"
chmod 755 "${APPDIR}/usr/bin/ctforge"

# Desktop entry (top-level for AppImage spec)
cp packaging/ctforge.desktop "${APPDIR}/"

# Icons
cp packaging/ctforge.svg "${APPDIR}/ctforge.svg"
cp packaging/ctforge.svg "${APPDIR}/usr/share/icons/hicolor/scalable/apps/"

# AppRun launcher
cat > "${APPDIR}/AppRun" <<'APPRUN'
#!/bin/bash
SELF="$(readlink -f "$0")"
HERE="${SELF%/*}"
exec "${HERE}/usr/bin/ctforge" "$@"
APPRUN
chmod 755 "${APPDIR}/AppRun"

# Download appimagetool if needed
if [ ! -f appimagetool ]; then
    echo "[*] Downloading appimagetool ..."
    wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O appimagetool
    chmod +x appimagetool
fi

ARCH=x86_64 ./appimagetool --no-appstream "${APPDIR}" "CTForge-${VERSION}-x86_64.AppImage"
echo "[+] Built: CTForge-${VERSION}-x86_64.AppImage"
