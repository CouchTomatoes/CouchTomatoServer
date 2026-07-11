<p align="center">
  <img src="docs/branding/logo.png" width="140" alt="CouchTomato logo">
</p>

CouchTomato
=====

[![Release](https://img.shields.io/github/v/release/CouchTomatoes/CouchTomatoServer)](https://github.com/CouchTomatoes/CouchTomatoServer/releases)
[![Release workflow](https://github.com/CouchTomatoes/CouchTomatoServer/actions/workflows/release.yml/badge.svg)](https://github.com/CouchTomatoes/CouchTomatoServer/actions/workflows/release.yml)
[![License: GPLv3](https://img.shields.io/badge/license-GPLv3-blue.svg)](license.txt)

CouchTomato is a Python 3 port and rebrand of [CouchPotato](https://github.com/CouchPotato/CouchPotatoServer),
the original automatic NZB and torrent downloader, which stopped receiving updates in 2020 while still on
Python 2. This fork keeps the entire original commit history intact (see `CLAUDE.md` for details) and ports
the codebase forward to Python 3 while working toward full feature parity with upstream.

CouchTomato (like CouchPotato before it) is an automatic NZB and torrent downloader. You can keep a "movies I
want"-list and it will search for NZBs/torrents of these movies every X hours. Once a movie is found, it will
send it to SABnzbd or download the torrent to a specified directory.

> **Note on the CouchPotatoApi provider:** upstream CouchPotato shipped with a built-in provider
> (`couchpotato/core/media/movie/providers/info/couchpotatoapi.py`) that calls a hosted backend at
> `api.couchpota.to` for search suggestions, release validation, ETA data, and update messages. That domain
> is now parked/for sale and the hosted service is gone, so this provider fails in CouchTomato. The backend's
> source code is still available at [CouchPotato/CouchPotatoAPI](https://github.com/CouchPotato/CouchPotatoAPI)
> if it's ever worth self-hosting a replacement; tracked as a known issue rather than something fixable by a
> client-side code change alone. That repo is archived (read-only since 2021), Node.js/Express, has no
> license file, and its own README admits setup isn't documented ("I don't really have the steps on how to
> get it running") — self-hosting it would mean reverse-engineering an abandoned app, not a quick deploy.


## Running from Source

CouchTomato requires **Python 3.11+**. It can be run from source, and will use *git* as an updater, so make
sure that is installed too.

* Install [Python 3.11+](https://www.python.org/downloads/) and [git](https://git-scm.com/)
* Clone the repo: `git clone https://github.com/CouchTomatoes/CouchTomatoServer.git`
* Install dependencies: `pip install -r requirements.txt`
* Start it: `python3 CouchTomatoServer/CouchPotato.py`
* Your browser should open up, but if it doesn't go to `http://localhost:5050/`

Docker:
* You can adapt the community CouchPotato Docker images (e.g. [linuxserver.io](https://github.com/linuxserver/docker-couchpotato)) as a starting point — CouchTomato hasn't published its own image yet, see `TODO.md`.


## Development

Be sure you're running Python 3.11 or newer.

If you're going to add styling or doing some javascript work you'll need a few tools that build and compress scss -> css and combine the javascript files. [Node/NPM](https://nodejs.org/), [Grunt](http://gruntjs.com/installing-grunt), [Compass](http://compass-style.org/install/)

After you've got these tools you can install the packages using `npm install`. Once this process has finished you can start CouchTomato using the command `grunt`. This will start all the needed tools and watches any files for changes.
You can now change css and javascript and it wil reload the page when needed.

By default it will combine files used in the core folder. If you're adding a new .scss or .js file, you might need to add it and then restart the grunt process for it to combine it properly.

Don't forget to enable development inside the settings. This disables some functions and also makes sure javascript errors are pushed to console instead of the log.

## Project status

This is an active port — see `CLAUDE.md` for the full history/architecture notes and `TODO.md` for a
checkbox-tracked list of what's left to reach full feature parity with upstream CouchPotato.

## Release History

Full release notes and downloads are on the [Releases page](https://github.com/CouchTomatoes/CouchTomatoServer/releases).
Short summary of what changed and which platforms had working installer/build downloads at each version:

| Version | Highlights | Downloads available |
|---|---|---|
| [v4.0.18](https://github.com/CouchTomatoes/CouchTomatoServer/releases/tag/v4.0.18) | Fixed `lipo` rejecting an identical vendored binary — full platform matrix finally green | **All platforms**: Windows x64 (installer + zip) & arm64 (zip), Linux x64 & arm64 (tar.gz + AppImage), **macOS universal2** (DMG + app.tar.gz — Intel + Apple Silicon combined) |
| [v4.0.17](https://github.com/CouchTomatoes/CouchTomatoServer/releases/tag/v4.0.17) | Fixed missing `dist/` dir in the macOS merge job | Windows x64/arm64, Linux x64/arm64 — macOS still missing (lipo bug) |
| [v4.0.16](https://github.com/CouchTomatoes/CouchTomatoServer/releases/tag/v4.0.16) | Fixed retired `macos-13` GitHub Actions runner label | Windows x64/arm64, Linux x64/arm64 — macOS still missing (dist/ bug) |
| [v4.0.15](https://github.com/CouchTomatoes/CouchTomatoServer/releases/tag/v4.0.15) | Expanded release pipeline to a full platform/arch matrix | Windows x64/arm64, Linux x64/arm64 — macOS job never ran (runner retired) |
| [v4.0.14](https://github.com/CouchTomatoes/CouchTomatoServer/releases/tag/v4.0.14) | Fixed a `RecursionError` in vendored `dateutil` + a Python 3.10 `collections` removal | Windows installer (.exe), macOS DMG (Apple Silicon only) |
| [v4.0.13](https://github.com/CouchTomatoes/CouchTomatoServer/releases/tag/v4.0.13) | Fixed macOS build failing on `.app` icon conversion | Windows installer (.exe), macOS DMG (Apple Silicon only) |
| [v4.0.12](https://github.com/CouchTomatoes/CouchTomatoServer/releases/tag/v4.0.12) | First Windows/macOS installer builds attached to a release | Windows installer (.exe) — macOS build failed (icon bug) |
| v4.0.4 – v4.0.11 | Core Python 3 porting: DB race fix, download-to-library pipeline bugs, wizard crashes, release-notes automation fixes | Source only (no packaged builds yet) |
| v4.0.0 – v4.0.3 | Initial CouchTomato numbering; release automation and CouchPotatoAPI status docs | Source only (no packaged builds yet) |

For the pre-rebrand CouchPotato history (`build/2.x`–`build/3.x` tags), see the
[full release list](https://github.com/CouchTomatoes/CouchTomatoServer/releases).
