<p align="center">
  <img src="docs/branding/logo.png" width="140" alt="CouchTomato logo">
</p>

<h1 align="center">CouchTomato</h1>

<p align="center">
  <a href="https://github.com/CouchTomatoes/CouchTomatoServer/releases"><img src="https://img.shields.io/github/v/release/CouchTomatoes/CouchTomatoServer" alt="Release"></a>
  <a href="https://github.com/CouchTomatoes/CouchTomatoServer/actions/workflows/release.yml"><img src="https://github.com/CouchTomatoes/CouchTomatoServer/actions/workflows/release.yml/badge.svg" alt="Release workflow"></a>
  <a href="license.txt"><img src="https://img.shields.io/badge/license-GPLv3-blue.svg" alt="License: GPLv3"></a>
</p>

<p align="center">
  The maintained Python 3 successor to <a href="https://github.com/CouchPotato/CouchPotatoServer">CouchPotato</a>,
  the automatic NZB and torrent movie downloader.
</p>

**Looking for CouchPotato?** CouchPotato (CouchPotatoServer) stopped being developed in 2020 and never
moved off Python 2. CouchTomato is the same app (same web UI, same providers, same download-client
support) ported to Python 3.11+ and kept working against today's sites, with Windows, macOS and Linux
builds on every release.

CouchPotato stopped receiving updates in 2020 while still stuck on Python 2, with its dependencies
vendored in-tree instead of pip-installed. CouchTomato keeps the entire original commit history intact
(see [`TODO.md`](TODO.md) for the full porting log) while bringing the codebase forward to
Python 3, replacing dead vendored dependencies with maintained pip packages, and working toward full
feature parity with upstream.

Keep a "movies I want"-list, and CouchTomato searches for NZBs/torrents of those movies on a schedule.
Once a good release is found, it's sent straight to your download client, then automatically renamed
and moved into your library once it finishes downloading.

## What Now?

Welcome to CouchTomato! Dive straight in, or read on for what to expect...

* **[Download the latest release](https://github.com/CouchTomatoes/CouchTomatoServer/releases/latest)** —
  Windows installer/zip, macOS universal2 DMG, or Linux tar.gz/AppImage
* **[Run it with Docker](#docker)** — `ghcr.io/couchtomatoes/couchtomato`, for PCs, NAS boxes and the Raspberry Pi
* [Install guides](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Installation) for Windows, macOS, Linux and running from source
* [Migrating from CouchPotato](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Migration) — keep your wanted list, library and settings
* [Screens](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Screens) — every page of the new interface, in light, dark and phone views
* [FAQ / Troubleshooting](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/FAQ) — known issues, dead external services and common questions
* [Architecture & porting status](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Architecture-Overview)

## Providers & Downloaders

CouchTomato searches across a wide range of torrent and NZB sites, and can hand releases off to
whichever download client you already run.

**Torrent providers:** AlphaRatio, AwesomeHD, BitHDTV, Bitsoup, HD4Free, HDBits, IPTorrents,
ILoveTorrents, KickAssTorrents, MagnetDL, MoreThanTV, PassThePopcorn, RARBG, SceneAccess, SceneTime,
ThePirateBay, TorrentBytes, TorrentDay, TorrentLeech, TorrentPotato, TorrentShack, Torrentz, YTS

**NZB providers:** Binsearch, NZBClub, NZBGet-compatible Newznab indexers, OMGWTFNZBS

**Download clients:** Transmission, Deluge, qBittorrent, rTorrent, uTorrent, NZBGet, NZBVortex,
Hadouken, Synology, put.io, SABnzbd, Blackhole

**Notifications:** see `couchpotato/core/notifications/` for the full list (Plex, Kodi/XBMC, Pushover,
Twitter, and more)

**Trakt:** imports your Trakt watchlist and can add finished downloads to your Trakt collection.
CouchTomato uses Trakt but is not endorsed or certified by Trakt. See [PRIVACY.md](PRIVACY.md).

## Screenies

The new interface, page by page ([all screens on the wiki](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Screens)). It is being built one
page at a time; until a page is done it shows the **⟲ Classic** look (the original CouchPotato design),
which stays available on every page for anyone who prefers it.

<table><thead></thead><tbody>
<tr align="center">
  <td><a title="Movie details" href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Screens#1-movie-details"><img src="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/01-movie-details-poster-full.png" width="200" alt="Movie details"></a></td>
  <td><a title="Activity" href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Screens#2-activity"><img src="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/02-activity-table.png" width="200" alt="Activity"></a></td>
  <td><a title="Calendar" href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Screens#3-calendar"><img src="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/03-calendar-month.png" width="200" alt="Calendar"></a></td>
  <td><a title="Home" href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Screens#6-home"><img src="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/06-home-sections.png" width="200" alt="Home"></a></td>
  <td><a title="Search results" href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Screens#11-search-results"><img src="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/11-search-results-posters.png" width="200" alt="Search results"></a></td>
  <td><a title="Settings" href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Screens#12-settings"><img src="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/12-settings-tabs.png" width="200" alt="Settings"></a></td>
</tr>
<tr align="center">
  <td>Movie details<br />View: <a title="Movie details - Light" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/01-movie-details-poster-full.png">Light</a>, <a title="Movie details - Dark" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/01-movie-details-default-dark.png">Dark</a>, <a title="Movie details - Phone" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/01-movie-details-default-phone.png">Phone</a>, <a title="Movie details - Classic" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/01-movie-details-classic.png">Classic</a></td>
  <td>Activity<br />View: <a title="Activity - Light" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/02-activity-table.png">Light</a>, <a title="Activity - Dark" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/02-activity-default-dark.png">Dark</a>, <a title="Activity - Phone" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/02-activity-default-phone.png">Phone</a></td>
  <td>Calendar<br />View: <a title="Calendar - Light" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/03-calendar-month.png">Light</a>, <a title="Calendar - Dark" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/03-calendar-default-dark.png">Dark</a>, <a title="Calendar - Phone" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/03-calendar-default-phone.png">Phone</a></td>
  <td>Home<br />View: <a title="Home - Light" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/06-home-sections.png">Light</a>, <a title="Home - Dark" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/06-home-default-dark.png">Dark</a>, <a title="Home - Phone" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/06-home-default-phone.png">Phone</a>, <a title="Home - Classic" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/06-home-classic.png">Classic</a></td>
  <td>Search results<br />View: <a title="Search results - Light" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/11-search-results-posters.png">Light</a>, <a title="Search results - Dark" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/11-search-results-default-dark.png">Dark</a>, <a title="Search results - Phone" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/11-search-results-default-phone.png">Phone</a>, <a title="Search results - Classic" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/11-search-results-classic.png">Classic</a></td>
  <td>Settings<br />View: <a title="Settings - Light" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/12-settings-tabs.png">Light</a>, <a title="Settings - Dark" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/12-settings-default-dark.png">Dark</a>, <a title="Settings - Phone" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/12-settings-default-phone.png">Phone</a>, <a title="Settings - Classic" href="https://raw.githubusercontent.com/wiki/CouchTomatoes/CouchTomatoServer/images/screens/12-settings-classic.png">Classic</a></td>
</tr>
</tbody>
</table>

Screenshots of the app as it is today, taken during real browser-driven testing, are in
[`docs/screenshots/`](docs/screenshots/).

## Available versions
<table><thead></thead><tbody>
<tr align="center">
  <td>Main (<a title="Main changelog" href="https://github.com/CouchTomatoes/CouchTomatoServer/blob/main/CHANGES.md">changes</a>)</td><td>(stable, released)</td><td><a title="Latest release" href="https://github.com/CouchTomatoes/CouchTomatoServer/releases/latest"><img src="https://img.shields.io/github/v/release/CouchTomatoes/CouchTomatoServer" alt="Latest release"></a></td><td><a title="CI on main" href="https://github.com/CouchTomatoes/CouchTomatoServer/actions/workflows/ci.yml?query=branch%3Amain"><img src="https://github.com/CouchTomatoes/CouchTomatoServer/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI on main"></a></td>
</tr>
<tr align="center">
  <td>Dev (<a title="Dev changelog" href="https://github.com/CouchTomatoes/CouchTomatoServer/blob/dev/CHANGES.md">changes</a>)</td><td>(next release, not live)</td><td>see <i>Unreleased</i></td><td><a title="CI on dev" href="https://github.com/CouchTomatoes/CouchTomatoServer/actions/workflows/ci.yml?query=branch%3Adev"><img src="https://github.com/CouchTomatoes/CouchTomatoServer/actions/workflows/ci.yml/badge.svg?branch=dev" alt="CI on dev"></a></td>
</tr>
<tr align="center">
  <td colspan=4>[ ++ Install <a href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Installation">Guides</a> ++ ][ Frequently <a href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki/FAQ">Asked</a> ][ See the <a href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Screens">Screens</a> ][ Discover <a href="https://github.com/CouchTomatoes/CouchTomatoServer/wiki">Wiki</a> ]</td>
</tr>
</tbody>
</table>

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

Prefer a packaged build instead? See the [Installation wiki page](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Installation) for
platform-specific installers, or the [latest release](https://github.com/CouchTomatoes/CouchTomatoServer/releases/latest)
directly.

## Docker

The official image runs on any 64-bit PC, NAS or Raspberry Pi 4/5 (`linux/amd64` and `linux/arm64`):

```yaml
# docker-compose.yml
services:
  couchtomato:
    image: ghcr.io/couchtomatoes/couchtomato:latest
    container_name: couchtomato
    environment:
      - PUID=1000          # your user id   (run: id -u)
      - PGID=1000          # your group id  (run: id -g)
      - TZ=Europe/London   # your time zone
    volumes:
      - ./config:/config         # settings, database, logs
      - /path/to/downloads:/downloads
      - /path/to/movies:/movies
    ports:
      - 5050:5050
    restart: unless-stopped
```

Then `docker compose up -d` and open `http://<this machine>:5050/`. Or with plain Docker:

```bash
docker run -d --name couchtomato -p 5050:5050 \
  -e PUID=$(id -u) -e PGID=$(id -g) -e TZ=Europe/London \
  -v ./config:/config -v /path/to/downloads:/downloads -v /path/to/movies:/movies \
  --restart unless-stopped ghcr.io/couchtomatoes/couchtomato:latest
```

* In the setup wizard, use the **container** paths: `/downloads` for finished downloads and `/movies`
  for your library. Your download client must see the same files (mount the same host folder into it).
* Files are created as `PUID:PGID`, so they belong to your user on the host.
* **Updating:** `docker compose pull && docker compose up -d`. Inside Docker the app tells you when a new
  version is out but never replaces itself; pin a version with a tag like `:4.0.72` instead of `:latest`.
* Moving from CouchPotato? Point `/config` at a copy of your old data folder. See
  [Migrating from CouchPotato](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Migration).

## Development

Pull requests are welcome, against the `dev` branch. [CONTRIBUTING.md](.github/CONTRIBUTING.md) has
the branches, how to run the tests, and how to rebuild the JavaScript bundles
(`node tools/jsbuild/build.js`). Turn on development mode in the settings to get JavaScript errors in
the browser console instead of the log.

## Project status

This is an active port. See the
[Architecture Overview wiki page](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/Architecture-Overview)
for a summary, and [`TODO.md`](TODO.md) for the porting history and a checkbox-tracked list of what's
left to reach full feature parity with upstream CouchPotato.

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

## Howto

#### Report issues
Found a bug or have a question? Check the [FAQ](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/FAQ) and [`TODO.md`](TODO.md) first in case it is
already a known, tracked item, then [open an issue](https://github.com/CouchTomatoes/CouchTomatoServer/issues)
with your CouchTomato version, platform, what you did, what you expected, and the relevant lines from
**Settings → Logs**.

## Community

* [Wiki](https://github.com/CouchTomatoes/CouchTomatoServer/wiki) · [Contributing](.github/CONTRIBUTING.md) · [Code of conduct](CODE_OF_CONDUCT.md) · [Security](SECURITY.md) · [Releases](https://github.com/CouchTomatoes/CouchTomatoServer/releases) · [Issues](https://github.com/CouchTomatoes/CouchTomatoServer/issues)
