# Installation

Every push to `main` automatically cuts a new [GitHub Release](https://github.com/CouchTomatoes/CouchTomatoServer/releases)
with installers/builds for every platform below. Grab the [latest release](https://github.com/CouchTomatoes/CouchTomatoServer/releases/latest)
rather than an older one — see the main README's Release History table if you need to know which
version first got a given platform working.

## Windows

Two options are attached to each release:

- **`CouchTomato-Setup-<version>.exe`** — a standard NSIS installer. Installs to Program Files, adds
  Start Menu shortcuts and a registry-registered uninstaller.
- **`CouchTomato-<version>-win_x64.zip`** — a portable build. Unzip anywhere and run `CouchTomato.exe`
  directly, no installation needed.

An **arm64** build (`CouchTomato-<version>-win_arm64.zip`) is also published for Windows-on-ARM
devices, as a portable zip (best-effort installer support — see the release notes for that version).

## macOS

- **`CouchTomato-<version>.dmg`** — mount it and drag `CouchTomato.app` into `Applications`.
- **`CouchTomato-<version>-macos_universal.app.tar.gz`** — the same `.app`, as a plain tarball, if you
  prefer not to use the DMG.

Both are **universal2** binaries — a single download that runs natively on both Intel and Apple
Silicon Macs (see [FAQ](FAQ.md#why-is-the-macos-download-so-much-bigger-than-the-windows-one) for why
it's a larger download than the Windows build).

Because the app isn't signed with an Apple Developer certificate, Gatekeeper will show an
"unidentified developer" warning the first time you open it — see the
[FAQ entry](FAQ.md#macos-says-the-app-cant-be-opened-because-its-from-an-unidentified-developer) for
how to get past that.

## Linux

- **`CouchTomato-<version>-x86_64.AppImage`** / **`CouchTomato-<version>-aarch64.AppImage`** — download,
  `chmod +x`, and run directly. No installation, no root required.
- **`CouchTomato-<version>-linux_x64.tar.gz`** / **`CouchTomato-<version>-linux_arm64.tar.gz`** — a plain
  extracted build, if you'd rather manage it yourself (e.g. via your own systemd unit).

## Running from Source (any platform)

Requires **Python 3.11+** and `git`:

```sh
git clone https://github.com/CouchTomatoes/CouchTomatoServer.git
cd CouchTomatoServer
pip install -r requirements.txt
python3 CouchPotato.py
```

Your browser should open automatically; if not, go to `http://localhost:5050/`.

## Docker

CouchTomato doesn't publish its own Docker image yet (tracked in `TODO.md`). In the meantime, the
community CouchPotato images (e.g. [linuxserver.io's](https://github.com/linuxserver/docker-couchpotato))
are a reasonable starting point to adapt.
