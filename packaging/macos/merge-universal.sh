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
mkdir -p "$(dirname "$out_dir")"
cp -a "$arm64_dir" "$out_dir"

# Walk every file present in both trees; lipo-merge the ones that are actual
# Mach-O binaries (the app's own executable plus any compiled .so/.dylib
# dependencies), leave everything else (resources, .py sources, data files)
# as copied from the arm64 tree since they're architecture-independent.
# Some vendored data files (e.g. libs/unrar2/unrar) are legacy single-arch
# binaries bundled as-is rather than built per-arch by PyInstaller, so both
# trees carry the same architecture - lipo refuses to fat-merge two slices
# of the same architecture, so skip those rather than fail the build.
#
# A byte-equality check (cmp) isn't reliable here: PyInstaller/macOS appear
# to apply per-build ad-hoc signing or embed build-specific metadata into
# bundled Mach-O binaries, so the *same* vendored tool can come out
# byte-different between the independently-run x64 and arm64 build jobs
# even though it's still the same single architecture on both sides.
# Comparing actual architectures via `lipo -archs` (the same check lipo
# itself makes) is what actually determines whether a merge is possible or
# meaningful.
find "$arm64_dir" -type f | while IFS= read -r arm64_file; do
  rel_path="${arm64_file#"$arm64_dir"/}"
  x64_file="$x64_dir/$rel_path"
  out_file="$out_dir/$rel_path"

  [ -f "$x64_file" ] || continue
  file -b "$arm64_file" | grep -q 'Mach-O' || continue

  arm64_archs="$(lipo -archs "$arm64_file" 2>/dev/null || true)"
  x64_archs="$(lipo -archs "$x64_file" 2>/dev/null || true)"
  [ "$arm64_archs" = "$x64_archs" ] && continue

  lipo -create "$arm64_file" "$x64_file" -output "$out_file"
done

# PyInstaller has been observed producing two copies of the same
# lib-dynload directory in a single build - one named literally
# "pythonX.Y" and one with the dot escaped as "pythonX__dot__Y" - with
# identical content. The literal-dot name matches Apple's own
# Python.framework version-directory convention closely enough that
# macOS's codesign bundle-format validation tries to structurally
# interpret it as nested code and hard-fails signing the whole app, while
# the escaped name is treated as ordinary data and signs fine. Since the
# escaped copy is a complete functional duplicate, drop the literal-dot
# one before signing - but only when the escaped fallback actually
# exists, so this is a no-op if a future PyInstaller version stops
# producing the duplicate (or only ever produces the escaped name).
dotted_pydir=$(find "$out_dir/Contents/Frameworks" -mindepth 1 -maxdepth 1 -type d -name 'python[0-9].[0-9]*' 2>/dev/null | head -n1)
if [ -n "$dotted_pydir" ]; then
  escaped_pydir="$(dirname "$dotted_pydir")/$(basename "$dotted_pydir" | sed 's/\./__dot__/')"
  if [ -d "$escaped_pydir" ]; then
    echo "Removing duplicate $dotted_pydir (escaped copy $escaped_pydir already present)"
    rm -rf "$dotted_pydir"
  fi
fi

# Same underlying problem, different shape: pip/setuptools .dist-info and
# .egg-info directories (e.g. "setuptools-65.5.0.dist-info") carry a
# dotted version number in their own name, which trips the exact same
# codesign structural-validation false positive as the python3.11 case
# above ("bundle format unrecognized, invalid, or unsuitable") once
# python3.11 itself stopped being the first thing it tripped over. These
# are pure packaging metadata (version/dependency info for pip's own
# bookkeeping) - CouchTomato's own code never reads them at runtime - so
# they're safe to drop entirely rather than rename around the collision.
find "$out_dir/Contents/Frameworks" -mindepth 1 -maxdepth 1 -type d \( -name '*.dist-info' -o -name '*.egg-info' \) -print0 |
  while IFS= read -r -d '' metadir; do
    echo "Removing packaging metadata dir $metadir (not needed at runtime)"
    rm -rf "$metadir"
  done

echo "Universal2 app written to $out_dir"
lipo -info "$out_dir/Contents/MacOS/CouchTomato"
