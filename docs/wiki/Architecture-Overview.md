# Architecture & Porting Status

This is a summary — for full detail, decisions, and the reasoning behind each change, see
[`CLAUDE.md`](../../CLAUDE.md) (the running project log) and [`TODO.md`](../../TODO.md)
(the checkbox-tracked porting checklist).

## What CouchTomato is

A Python 3 port and rebrand of [CouchPotato](https://github.com/CouchPotato/CouchPotatoServer), keeping
the entire original commit history intact. CouchPotato itself stopped receiving updates in 2020 while
still on Python 2, with dependencies vendored in-tree instead of pip-installed.

## Core components

- **Web framework**: [Tornado](https://www.tornadoweb.org/) (upgraded from a heavily patched, ancient
  vendored copy to a modern pip release — required rewriting several async/threading patterns that
  changed between versions).
- **Database**: [CodernityDB3](https://pypi.org/project/CodernityDB3/), a maintained Python 3-native
  fork of the original vendored CodernityDB (a pure-Python embedded NoSQL database) — not SQLite or
  SQLAlchemy.
- **Frontend**: MooTools-based, pre-built/minified JS and CSS bundles (`combined.*.min.js`,
  `combined.min.css`). There's currently no verified-working `grunt` build pipeline in CI, so frontend
  source changes need the matching bundle hand-patched too — see the [FAQ](FAQ.md).
- **Packaging**: PyInstaller, bundling the app's dynamically-loaded plugin system (`couchpotato/`,
  `libs/`) as loose data trees alongside a frozen bootstrap, since PyInstaller's static import
  analysis can't trace runtime `import_module()` calls. See `packaging/couchtomato.spec`.

## Porting status

- ✅ App boots cleanly and the web UI is verified working in a real headless browser (not just `curl`)
- ✅ Full wizard click-through, live provider search, and the add-movie → download client →
  rename-into-library pipeline all verified working end to end against real services
  (a real `transmission-daemon`, live torrent/NZB providers)
- ✅ All ~50 provider/notification/downloader plugin import failures fixed (0 remaining)
- ✅ Home page charts, poster/backdrop image caching, and the directory-browser settings widget all
  verified working
- ✅ Multi-platform release pipeline: Windows (x64/arm64), Linux (x64/arm64), macOS (universal2) —
  installers, portable builds, and CI all verified against real GitHub Actions runs
- 🚧 Full rebrand (config directory, package name, remaining UI strings) — partially done
- 🚧 Vendored dependency replacement — several already swapped for maintained pip packages
  (`beautifulsoup4`, `GitPython`, `httplib2`, `bencode.py`, `requests`, `tornado`, `chardet`,
  `CodernityDB3`), several more still vendored (see `TODO.md` §2)
- 🚧 Docker/systemd packaging — not started
- ❌ Not fixable: the `CouchPotatoApi` provider (upstream's `api.couchpota.to` backend is a dead,
  parked domain) — see the [FAQ](FAQ.md)

## Common bug pattern worth knowing

The single most common class of porting bug found across this codebase is Python 2→3's `bytes`/`str`
split: code written for Python 2's more permissive string handling either needs bytes and silently gets
`str`, or vice versa. Both directions have shown up repeatedly — if you're debugging a `TypeError`
involving `bytes`/`str`, or a value that silently doesn't match when it should, this is the first thing
to check. See `CLAUDE.md`'s progress log for the many specific instances found and fixed.
