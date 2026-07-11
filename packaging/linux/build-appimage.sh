#!/usr/bin/env bash
# Wraps a PyInstaller onedir build (as produced by packaging/couchtomato.spec)
# in an AppDir and runs appimagetool over it. CouchTomato's plugin loader
# imports providers/notifications/downloaders dynamically at runtime (see
# CLAUDE.md), so the AppDir must ship the onedir output as-is rather than
# trying to re-freeze it - this script only handles the AppDir wrapper, all
# the dynamic-import handling already happened in the PyInstaller build.
#
# Usage: build-appimage.sh <onedir-path> <arch> <output-filename>
#   onedir-path      path to the PyInstaller COLLECT output (e.g. dist/CouchTomato)
#   arch             ARCH value appimagetool expects (x86_64 or aarch64)
#   output-filename  name of the .AppImage file to produce, in the cwd
set -euo pipefail

onedir_path="$1"
arch="$2"
output_filename="$3"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
work_dir="$(mktemp -d)"
appdir="$work_dir/AppDir"

mkdir -p "$appdir/usr/bin"
cp -a "$onedir_path/." "$appdir/usr/bin/"

cat > "$appdir/AppRun" <<'EOF'
#!/usr/bin/env bash
here="$(dirname "$(readlink -f "$0")")"
exec "$here/usr/bin/CouchTomato" "$@"
EOF
chmod +x "$appdir/AppRun"

cat > "$appdir/couchtomato.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=CouchTomato
Comment=Automatic NZB/torrent movie downloader
Exec=CouchTomato
Icon=couchtomato
Categories=Network;
Terminal=true
EOF

cp "$repo_root/couchpotato/static/images/icons/android.png" "$appdir/couchtomato.png"

appimagetool="$work_dir/appimagetool"
curl -fL -o "$appimagetool" \
  "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${arch}.AppImage"
chmod +x "$appimagetool"

# Hosted runners generally lack a working FUSE mount for AppImages to
# extract themselves in-place, so run it pre-extracted instead.
( cd "$work_dir" && "$appimagetool" --appimage-extract >/dev/null )

ARCH="$arch" "$work_dir/squashfs-root/AppRun" "$appdir" "$output_filename"
