# CouchTomato — Path to a Runnable App

Scoped checklist for the Python 2 → 3 upgrade, up through "server boots and the web UI
works." Check items off as they land (each should correspond to a commit). For full
project background, decisions, and *why* behind each item, see `CLAUDE.md` — this file
is just the actionable list.

## 1. Mechanical Py2 → Py3 pass

- [x] Run `lib2to3` over `couchpotato/` (51 files)
- [x] Run `lib2to3` over `libs/` (383 files across two passes)
- [x] Fix non-UTF8 source files that broke `lib2to3` (`libs/xmpp/session.py`,
      `libs/dateutil/parser.py` — re-encoded from ISO-8859-1)
- [ ] Decide fate of the 14 `libs/` files `lib2to3` couldn't parse at all (Py2-only
      syntax): `chardet/chardetect.py`, `git/repository.py`, `pytwitter/__init__.py`,
      `pyutil/benchutil.py`, `pyutil/benchmarks/bench_xor.py`,
      `pyutil/scripts/{time_comparisons,try_decoding,verinfo}.py`, `rsa/{cli,util}.py`,
      `tornado/{autoreload,options,template,testing}.py`
      — `chardet`, `git`, `tornado` resolved by replacing the vendored lib entirely (see §2)

## 2. Replace vendored `libs/` with real pip packages

Vendored because CouchPotato patched 2013-era versions in-tree; most have modern,
actively maintained PyPI equivalents now. `libs/` is prepended to `sys.path`, so
`pip install X` + `rm -rf libs/X` is a clean swap as long as the API held up.

- [x] `tornado` → pip (API changed a lot — see §3 below, that's the code-fix side)
- [x] `chardet` → pip
- [x] `git` → pip `GitPython`
- [x] `requests` → pip (vendored copy broke on `collections.MutableMapping`)
- [ ] `six`
- [ ] `dateutil` → pip `python-dateutil`
- [ ] `certifi`
- [ ] `bs4` → pip `beautifulsoup4`
- [ ] `html5lib`
- [ ] `oauthlib`
- [ ] `httplib2`
- [ ] `apscheduler`
- [ ] `rsa`
- [ ] `pyasn1`
- [ ] `guessit` (modern PyPI version is actively maintained, worth checking API drift)
- [ ] `subliminal` (same — check API drift)
- [ ] `pynma`, `gntp`, `qbittorrent`, `rtorrent`, `deluge_client` (notification/download
      client libs — check if still needed / have maintained equivalents)
- [ ] `oauth2`, `ndg`, `pio`, `bencode`, `cache`, `backports`, `argparse.py`,
      `multipartpost.py`, `color_logs.py`, `daemon.py`, `importhelper`, `logr`,
      `pkg_resources.py` — audit each: pip-replaceable, stdlib-replaceable (e.g.
      `argparse` is stdlib now), or dead weight to delete
- [ ] Keep + hand-port with 2to3/manual fixes (CouchPotato-specific, no PyPI
      equivalent): `axl` (axel event lib), `caper`, `CodernityDB`, `enzyme`
- [ ] `requirements.txt` fully reflects every pip swap made above

## 3. Get `python3 CouchPotato.py --help` working

- [x] Fix `couchpotato/api.py`: removed `@asynchronous` tornado decorator →
      `self._auto_finish = False`
- [x] Fix `couchpotato/core/_base/_core.py`: removed private `IOLoop._closing` checks
- [x] Fix `couchpotato/core/helpers/encoding.py` `sp()`: bytes/str mixing
- [x] Fix `couchpotato/core/logger.py` `safeMessage()`: bytes/str mixing
- [x] Fix `libs/CodernityDB/database.py`: Py2 unbound-method `.__func__` idiom
- [x] **`--help` runs cleanly end to end** ✅

## 4. Get the server actually booting (`--data_dir ... --console_log --debug`)

- [ ] Fix `libs/CodernityDB/database.py` `_add_single_index` → `header_for_indexes(...)`
      bytes/str `TypeError` at `f.write(...)` (next blocker — check
      `header_for_indexes`'s real return type before wrapping in `toUnicode()`, the
      target here may legitimately need bytes since it's a binary file write)
- [ ] Continue iterating: run the server, fix whatever error comes next, one at a time,
      commit after each fix
- [ ] Server starts without crashing and stays up
- [ ] Web UI is reachable in a browser (default port)
- [ ] Can navigate the UI without immediate errors (add/search a movie, open settings)

## 5. Sanity pass once it boots

- [ ] No `ss()` bytes-vs-str landmines left in hot paths (grep `ss(` — same pattern
      already found twice in §3; expect more in providers/renamer)
- [ ] `grep -r "__pycache__"` clean, `.gitignore` covers build artifacts
- [ ] Smoke-test core flows manually in a browser: add movie to wanted list, trigger a
      search, check settings pages load

---

**Not in scope for "runnable"** — tracked in `CLAUDE.md`'s next-steps for after this
milestone: provider plugin fixes (NZB/torrent/download clients), full rebrand
(CouchPotato → CouchTomato strings/paths/config dir), CI, packaging/Docker.
