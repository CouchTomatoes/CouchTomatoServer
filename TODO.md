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

- [x] Fix `libs/CodernityDB/database.py` bytes/str issues in index write/read
- [x] Replace vendored `CodernityDB` entirely with `libs/codernitydb3` (a maintained
      Python-3-native fork, MIT/Apache-2.0-licensed, found on PyPI as `CodernityDB3`;
      vendored the source directly since the PyPI wheel's setup.py doesn't build
      cleanly here) + a thin `libs/CodernityDB/` shim re-exporting it under the old
      import path, since generated index files have `CodernityDB.*` imports baked in
      as literal text (see `header_for_indexes()`)
- [x] Fix `configparser` write mode (`'wb'` → `'w'`) in `couchpotato/core/settings.py`
- [x] Fix `axl/axel.py` event-hash `TypeError` (`hashlib.md5(str(handler))` needs
      `.encode()`) — this one blocked nearly every event registration in the app
- [x] Fix `async` used as a bare variable name in `renamer.py` (reserved keyword since
      Python 3.7) → renamed to `is_async`
- [x] Fix `Thread.isAlive()` → `.is_alive()` in vendored `libs/apscheduler`
- [x] Fix the systemic "md5 needs bytes" pattern across all CodernityDB index classes:
      `couchpotato/core/media/_base/media/index.py`, `couchpotato/core/settings.py`,
      `couchpotato/core/plugins/quality/index.py`,
      `couchpotato/core/plugins/release/index.py` — every `make_key`/`make_key_value`
      must return `bytes` (codernitydb3's own default `make_key` does
      `key.encode('utf8')`; our overrides didn't match that contract)
- [x] Fix JSON serialization crashing on CodernityDB's internal `_rev` bytes field —
      added `jsonBytesDefault()` in `encoding.py`, wired into `api.py`'s `json.dumps`
      and patched `tornado.escape.json_encode` globally (used by all templates)
- [x] Fix `Env.get('x', unicode = True)` template calls → `str = True` (function's
      actual param name; `couchpotato/templates/index.html`)
- [x] Removed dead `from itertools import izip` (Py2-only) from `TitleSearchIndex`'s
      custom_header — unused import was breaking that index's file generation
- [x] **Server starts without crashing and stays up** ✅
- [x] **Web UI is reachable in a browser** ✅ — `GET /` returns real rendered HTML
- [x] **Verified in an actual headless browser (Playwright/Chromium), not just curl** ✅
      — found and fixed two showstopper bugs curl couldn't reveal (see below). The
      setup wizard now renders real, interactive content: "Welcome to the new
      CouchPotato", working form fields, settings sections.
- [x] Fixed **static asset routing order bug** in `couchpotato/runner.py`: the
      catch-all `WebHandler` (`(.*)`) was registered *before* the `StaticFileHandler`
      routes, so Tornado matched the catch-all first and every `/static/*` request
      (all JS/CSS) got redirected instead of served — browser tried to execute the
      returned HTML as JavaScript (`Unexpected token '<'`), so the frontend framework
      (MooTools) never loaded and the page was blank white despite `curl` showing a
      200. Fixed by registering static handlers before the catch-all.
- [x] Fixed the **single highest-impact bug found so far**: `IOLoop.current()` called
      from inside a background worker thread (every API request runs its handler in a
      `Thread` via `api.py`'s `run_handler`/`run_async`) returns a brand-new,
      never-started event loop instead of the real running one — so
      `IOLoop.current().add_callback(self.sendData, ...)` in `ApiHandler.taskFinished`
      silently scheduled the HTTP response on a phantom loop that never runs. Every
      single API call in the app hung forever with no response and no error logged.
      Fixed by capturing `main_ioloop = IOLoop.current()` once at import time in
      `api.py` (main thread, before the loop starts / before any threads exist) and
      using that captured reference in worker-thread callbacks instead of calling
      `IOLoop.current()` fresh. Same fix applied to `core/_base/_core.py`'s
      `shutdown()`/`restart()` (API-routed, same bug) and
      `core/notifications/core/main.py`'s `frontend()` notification broadcaster.
      **If any new code schedules a tornado callback from inside a thread, it must
      import and use `main_ioloop` from `couchpotato.api`, never call
      `IOLoop.current()` directly from that thread.**
- [x] Fixed a genuine upstream bug in vendored `libs/codernitydb3/tree_index.py`:
      `_find_key_many`'s `except ElemNotFound:` handler followed `next_leaf`
      unconditionally, but `next_leaf == 0` legitimately means "no next leaf" (not a
      valid file offset) for a freshly-created empty index — following it as a
      pointer read garbage/random bytes at file offset 0, which then got
      misinterpreted as an even more bogus "next leaf" offset on the next iteration,
      eventually seeking past EOF and crashing with
      `struct.error: unpack requires a buffer of 10 bytes`. Fixed by adding the same
      `if not next_leaf: return` guard that the analogous `_find_key` (singular)
      method already had. Reproduced and verified in isolation before/after the fix
      (see progress log). **Note:** `_find_key_smaller` (~line 1722) has the same
      unguarded-`prev_leaf` pattern but isn't currently exercised by any CouchPotato
      code path — flagged for later, not fixed yet since it's unverified.

## 5. Sanity pass once it boots

- [ ] Minor residual browser console error: `Cannot read properties of null (reading
      'hasClass')` still appears once on page load even though content renders fully
      — cosmetic/non-blocking so far, not yet root-caused.
- [ ] Real bugs found while investigating the above, not yet fixed (all logged
      server-side, none block boot): `couchpotato/core/helpers/encoding.py`
      `tryUrlencode()` does `for letter in ss(s):` — iterating `bytes` in Python 3
      yields `int`s, not 1-character strings, so `new += letter` raises `TypeError:
      can only concatenate str (not "int") to str`. Affects `cp.messages` and likely
      other calls through this helper.
- [ ] TMDB API key is being sent as a literal Python bytes-repr string
      (`api_key=b'e224fe4f...'`) instead of the actual key, causing every TMDB
      request to fail with 401 — breaks movie info/search. Somewhere a bytes value is
      being `str()`-ed instead of `.decode()`-ed before going into request params.
- [ ] `requests.exceptions.InvalidHeader: Header part (1) from ('X-CP-API', 1) must be
      of type str or bytes, not <class 'int'>` — an integer header value needs
      str-conversion before being passed to `requests`.
- [ ] `profile.forceDefaults` still hits `EOFError: EOF read where object expected` in
      `codernitydb3/storage.py`'s `marshal.loads()` when iterating `db.all('id')` on
      a fresh DB — separate from the tree_index bug above (that one's fixed), this is
      a new/different issue in the generic `all()` iteration path, not yet root-caused.
- [ ] Provider/plugin modules still failing to import (non-fatal, loader skips them
      individually): `scanner`/`subtitle` (vendored `subliminal` uses `from .async
      import` — reserved keyword), `notifications.join`, `notifications.xmpp_`,
      `notifications.twitter` (`rfc822` module removed), `downloaders.{deluge,
      hadouken,qbittorrent_,rtorrent_,utorrent}` (`types.StringType` removed), several
      `providers.nzb`/`providers.torrent` modules (`html.parser.HTMLParseError`
      removed), `_base.updater` (`git.repository.LocalRepository` — vendored `git`
      replaced by GitPython, different API, needs a real rewrite not a shim)
- [ ] No `ss()` bytes-vs-str landmines left in hot paths (grep `ss(` — same pattern
      already found twice in §3; expect more in providers/renamer)
- [ ] `grep -r "__pycache__"` clean, `.gitignore` covers build artifacts
- [ ] Smoke-test core flows manually in a real browser: add movie to wanted list,
      trigger a search, check settings pages load

---

**Not in scope for "runnable"** — tracked in `CLAUDE.md`'s next-steps for after this
milestone: provider plugin fixes (NZB/torrent/download clients), full rebrand
(CouchPotato → CouchTomato strings/paths/config dir), CI, packaging/Docker.
