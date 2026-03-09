#!/bin/bash
set -euo pipefail
# Build .deb package for CTForge
# Usage: ./packaging/build-deb.sh <version>  (e.g. 2.0.0)

VERSION="${1:?Usage: $0 <version>}"
ARCH="amd64"
PKG="ctforge"
PKG_DIR="${PKG}_${VERSION}_${ARCH}"

echo "[*] Building .deb for CTForge v${VERSION} ..."

rm -rf "${PKG_DIR}"
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps"

# Binary (must be built first via PyInstaller)
cp dist/ctforge "${PKG_DIR}/usr/bin/ctforge"
chmod 755 "${PKG_DIR}/usr/bin/ctforge"

# Desktop entry
cp packaging/ctforge.desktop "${PKG_DIR}/usr/share/applications/"

# Icon
cp packaging/ctforge.svg "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps/"

# Control file
cat > "${PKG_DIR}/DEBIAN/control" <<EOF
Package: ${PKG}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: libwebkit2gtk-4.1-0
Maintainer: Md. Shahin Alam <alam15-3186@diu.edu.bd>
Homepage: https://github.com/uchihashahin01/ctf-tools-installer
Description: CTForge — CTF Tools Installer
 A comprehensive CTF tools installer with a native desktop app,
 web dashboard, and CLI. Supports 40+ tools across 7 categories.
EOF

dpkg-deb --build --root-owner-group "${PKG_DIR}"
echo "[+] Built: ${PKG_DIR}.deb"
