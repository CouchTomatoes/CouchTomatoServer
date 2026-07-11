#!/usr/bin/env bash
# Merges two single-arch PyInstaller .app bundles (one built on macos-latest
# /arm64, one on macos-13/x64) into a single universal2 .app. PyInstaller
# doesn't cross-compile and actions/setup-python's macOS interpreters are
# single-arch, so the two builds are produced natively on separate runners
# and merged here with lipo, file by file, rather than attempting a single
# cross-compiled build.
#
# Usage: merge-universal.sh <arm64-app-dir> <x64-app-dir> <output-app-dir>
set -euo pipefail

arm64_dir="$1"
x64_dir="$2"
out_dir="$3"

rm -rf "$out_dir"
cp -a "$arm64_dir" "$out_dir"

# Walk every file present in both trees; lipo-merge the ones that are actual
# Mach-O binaries (the app's own executable plus any compiled .so/.dylib
# dependencies), leave everything else (resources, .py sources, data files)
# as copied from the arm64 tree since they're architecture-independent.
find "$arm64_dir" -type f | while IFS= read -r arm64_file; do
  rel_path="${arm64_file#"$arm64_dir"/}"
  x64_file="$x64_dir/$rel_path"
  out_file="$out_dir/$rel_path"

  [ -f "$x64_file" ] || continue

  if file -b "$arm64_file" | grep -q 'Mach-O'; then
    lipo -create "$arm64_file" "$x64_file" -output "$out_file"
  fi
done

echo "Universal2 app written to $out_dir"
lipo -info "$out_dir/Contents/MacOS/CouchTomato"
