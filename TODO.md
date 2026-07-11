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
- [x] Fixed `tryUrlencode()` iterating `bytes` byte-by-byte (Python 3 yields `int`s,
      not 1-character strings) — simplified to a single `quote_plus(ss(s))` call
      since `quote_plus` accepts bytes directly.
- [x] Fixed TMDB API key bytes-repr leak (`api_key=b'e224fe4f...'`) — `base64.b64decode()`
      returns `bytes` in Python 3 (was `str` in Python 2); added `.decode('utf-8')`.
      Same pattern fixed in `userscript/main.py`'s self-test helper.
- [x] Fixed `requests.exceptions.InvalidHeader` — `couchpotatoapi.py`'s
      `getRequestHeaders()` had two raw non-str header values (`int`, `float`);
      same bug independently in `trakt/main.py`'s `'trakt-api-version': 2`. Wrapped
      all in `str()`.
- [x] `profile.forceDefaults`'s `EOFError` no longer reproduces — was very likely a
      downstream symptom of the IOLoop/routing bugs fixed earlier, not a separate
      root cause. Verified clean across multiple fresh-DB boots.
- [x] Root-caused (not a bug): `CouchPotatoApi` provider's "Failed to parsing
      CouchPotatoApi" error — `couchpota.to` (upstream CouchPotato's own API domain)
      is now a permanently parked/for-sale domain, returning an HTML placeholder
      instead of JSON. This is a dead external service, not something fixable in
      code. This provider (suggestions/messages) will never work again as-is.
      **2026-07-10 update:** user found the backend's source is still public at
      https://github.com/CouchPotato/CouchPotatoAPI — noted in README.md's
      "Project status" section. Self-hosting a replacement is a possible future
      task (would need its own server/deploy, not a client code change) — not
      started, just documented so the option isn't lost. Checked the repo:
      archived (read-only since 2021), Node.js/Express, no license file, and
      the author's own README says setup isn't documented ("I don't really
      have the steps on how to get it running"). So this is a real but
      nontrivial option — reverse-engineering an abandoned, unlicensed app —
      not a quick self-host.
- [x] **All provider/plugin import failures fixed — 0 remaining, down from ~50.**
      Root causes were shared across many files: vendored `bs4` (→ pip
      `beautifulsoup4`, fixed 38 providers at once), vendored `bencode` (→ pip
      `bencode.py`, fixed 5 downloaders), vendored `httplib2`/`pytwitter` (→ pip
      `httplib2` + `email.utils` swap), vendored `xmpp` (Py2 raise syntax, implicit
      imports, removed `sha`/`md5` modules), vendored `subliminal` (`from .async
      import` — reserved keyword, file renamed since a full pip swap isn't viable,
      old `subliminal.videos.Video`-era API is used throughout scanner.py/subtitle.py),
      `multipartpost.py` (removed `mimetools`, old `urllib2.Request` methods,
      rewritten to work in bytes throughout), and `_base.updater` (rewrote
      `GitUpdater` against GitPython's real API — not a mechanical swap, the object
      model differs). Full details in `CLAUDE.md`'s progress log.
- [x] Root-caused and fixed the `profile.forceDefaults` `ElemNotFound`/`struct.error`
      finding (2026-07-10) — not a timing interaction with the updater's `git fetch`
      as first suspected. Real cause: `couchpotato/core/event.py` dispatches any
      event with 2+ handlers (`app.load`, `app.initialize`, etc.) across a 10-thread
      pool, and `libs/codernitydb3/database.py`'s `Database` did unsynchronized
      file I/O — concurrent plugin writes raced on shared index files, especially
      the global `id` index. Fixed with a `threading.RLock()` around every public
      `Database` entry point. Verified: reliably reproduced before the fix, 3
      consecutive clean fresh-DB boots after it.
- [x] Found and fixed a wizard crash while browser-testing (2026-07-10):
      `Page.Wizard` never set `default_action`, so its normal first-load path hit
      `toggleTab(undefined)` → `Cannot read properties of undefined (reading
      'split')` on the real `/#wizard/` page (confirmed via Playwright, not a
      redirect artifact). Fixed by adding `default_action: 'welcome'` in
      `wizard.js`. **Gap found along the way**: this repo has no verified-working
      `grunt`/`npm` build for the `combined.*.min.js` bundles actually served —
      had to hand-patch the pre-built `combined.plugins.min.js` to match. Worth
      fixing properly (see `CLAUDE.md` next-steps #3) so future frontend fixes
      don't need manual bundle patching.
- [ ] Cosmetic-only, low-priority: a few `domready` handlers (`page/login.js` was
      the one actually hit) can throw when the wizard's client-side redirect tears
      down the old document mid-navigation (`document.body` reads back `null`
      transiently). Confirmed via Playwright this never affects the real page users
      land on. Added a defensive guard to `login.js` for the one instance hit in
      practice; there may be others further down the same handler queue that were
      never reached once this one was silenced. Not chased further — provably inert.
- [ ] Stray broken image: `https://couchpota.to/media/images/userscript.gif` fails
      with `net::ERR_CONNECTION_RESET` (same dead-domain cause as the CouchPotatoApi
      provider, just a static asset). Not fixed yet.
- [x] **The whole download-to-library pipeline was broken end to end — found and
      fixed 6 bytes/str bugs (2026-07-10), verified against a real transmission-daemon
      running in this sandbox.** All the same root cause (Python 2 `.encode()`/bytes-
      iteration idiom that returned `str` in Py2, returns real `bytes` in Py3, never
      decoded back at the call site):
      - `core/settings.py`'s `saveView()` stored raw bytes into the config —
        **every setting saved through the UI/API was silently corrupted**
        (booleans stuck `False`, text came back as literal `"b'...'"` strings).
        Broke Transmission's host:port parsing.
      - `core/helpers/encoding.py`'s `toSafeString()` iterated bytes as ints —
        **`movie.add()` was completely broken** for a normal IMDB-id add
        (`getImdb()`/`simplifyString()` call it unconditionally).
      - `core/plugins/scanner.py`: `os.path.join()` mixing str+bytes crashed
        `os.walk()`-based folder scanning outright — renamer's scan of the
        downloads folder always found 0 files. Also fixed 3 more latent
        instances (3D-tag/embedded-title matching, not crash-triggering with a
        non-3D test file but same bug).
      - `core/plugins/quality/main.py`: quality *tag* matching (1080p, BluRay,
        etc.) silently always evaluated `False` (bytes `in` list-of-str never
        matches, no exception) — quietly dead this whole time, falling back to
        weaker extension-only scoring for every release.
      - `core/plugins/renamer.py`: `doReplace()` — builds every destination
        file/folder name — returned bytes, crashing the actual move/rename
        step. **This is the one that blocked "move the finished download into
        the library."**
      - `core/plugins/file.py`: same pattern breaking poster/backdrop image
        caching.
      Verified via a real `transmission-daemon` (RPC-authenticated) + a
      pre-seeded dummy movie file, twice from a fresh DB: `movie.add()` →
      `download.transmission.test` succeeds → torrent shows 100% complete →
      `renamer.scan()` detects/matches/scores/moves the file into the library
      → movie + release status both flip to `done`. Left as PR #8 (draft, not
      auto-merged — substantive core logic change). Full writeup in
      `CLAUDE.md`'s 2026-07-10 progress log entry.
- [ ] No `ss()` bytes-vs-str landmines left in hot paths (grep `ss(` — pattern found
      repeatedly now: §3, the wizard-testing entry above, and the pipeline entry
      just above. `renamer.py` has one more instance in `checkSnatched()` — appends
      `ss(...)` into a list used only for a debug log message, doesn't crash,
      not yet fixed, low priority)
- [ ] `grep -r "__pycache__"` clean, `.gitignore` covers build artifacts
- [x] Smoke-test core flows manually in a real browser: wizard confirmed clean
      through Welcome/General with 0 console errors; add-movie → Transmission →
      renamer confirmed working end to end, but driven via direct API calls +
      a self-seeded test torrent, not actual clicks through the UI against a
      live provider — still need Downloaders/Providers/Renamer/Automation/Finish
      wizard steps, save, and a real in-browser search/snatch against a live
      torrent/NZB provider
      **2026-07-11 update:** done — clicked through Downloaders (Transmission)/
      Providers (Binsearch, ThePirateBay, KickAssTorrents, YTS)/Renamer/Automation/
      Finish, saved, landed on the main app, added "The Matrix" through the real
      search-and-add UI, and triggered a real search against the live providers
      enabled above. Found and fixed 4 real bugs along the way (see progress log):
      two `domready` null-`document.body` crashes (`uniform.js`, `index.html`), a
      `urlopen()` exception-handling bug that turned every network failure across
      the *entire app* into an unhandled `TypeError` instead of a clean log line,
      and a bytes/str `TypeError` in 5 torrent providers' proxy/login-check code.
      One flaky, not-yet-reproduced-on-demand issue remains: a `struct.error`/
      `ElemNotFound` seen once when re-adding an already-added movie while a
      background search was concurrently running — see the entry below.
- [ ] Investigate a `struct.error: argument for 's' must be a bytes object` /
      `codernitydb3.index.ElemNotFound` seen once (2026-07-11) in
      `movie/_base/main.py`'s `add()` → `db.update(m)`, when clicking "Add" on a
      movie that was already in the library while a background provider search
      was still running. Didn't reproduce on a clean retry (single `movie.add` API
      call, no concurrent search) — looks like a race between the search threads
      and the update, not a deterministic key-encoding bug like the ones already
      fixed. Needs a targeted concurrency repro, not a speculative fix.
- [x] Check that the Home page's "top movies" charts feature (Blu-ray.com New
      Releases etc., via `automation.get_chart_list`) actually loads real data —
      **2026-07-11**: it didn't. `automation/base.py`'s `search()` (called by
      every chart provider, e.g. `bluray.py`) crashed with `AttributeError: 'str'
      object has no attribute 'decode'` on every single call — the opposite
      direction of the usual bytes/str bug (Py2 `.decode()`'d an already-`str`
      value in Py3). This silently emptied `charts.view`'s response every time,
      so the Home page's chart section just never rendered, with no visible
      error anywhere in the UI. Fixed by removing the unneeded `.decode('utf-8')`
      and encoding+decoding back to `str` properly. Verified: `charts.view` now
      returns real chart data (movies, posters, metadata) and it renders on the
      Home page.
- [x] Found and fixed a second routing-order bug in the same class as the
      already-fixed `/static/*` one (2026-07-11): `runner.py` registered the
      `ApiHandler` catch-all (`/api/<key>/(.*)`) *before* plugins load, but
      plugins like `file.py`'s cached-image server register their own static
      routes (`/api/<key>/file.cache/(.*)`) *during* plugin loading — so the
      earlier-registered generic catch-all always shadowed them, and every
      locally-cached poster/backdrop image in the entire app silently failed
      with the API's generic "doesn't seem to exist" error instead of serving
      the image. Fixed by moving plugin loading to happen before the
      API/web-handler `add_handlers` call, matching the existing
      registration-order comment already in the file. Verified: `file.cache`
      URLs now return `image/jpeg` instead of a JSON error, and posters render
      in both the Wanted list and the Home page charts.
- [x] Enumerated every API call the Home page makes on load (2026-07-11, via
      Playwright network capture): `media.list`, `dashboard.soon`,
      `suggestion.view`, `notification.listener`, `charts.view`, `file.cache/*`
      (one per poster), `updater.info`. All return 200 with a clean log (only
      the already-documented external-service noise: dead `couchpota.to`,
      IMDB blocking automated boxoffice-page scraping, invalid/placeholder
      OMDB API key). Found and fixed 2 more real bugs along the way:
      - `couchpotato/core/plugins/browser.py`'s `is_hidden()` (used by the
        Directory-type settings field's folder-browser popup) wrapped a path
        in `ss()` (bytes) then called `.startswith('.')` with a `str` literal —
        another instance of the recurring `ss()`-misuse pattern flagged
        earlier in this file. Crashed `directory.list` on every call, which
        also crashed the corresponding frontend code trying to render the
        (never-received) response.
      - `static/scripts/page/settings.js`'s `Option.Directory.filterDirectory()`
        and `.fillBrowser()` referenced `self.dir_list`/`self.back_button` —
        both only created once the folder-browser popup has been opened via
        `showBrowser()` — but `filterDirectory` runs on every `change`/`keyup`/
        `paste` of the plain text input regardless of whether the popup was
        ever opened (i.e., a user typing or pasting a path directly, a normal
        workflow). Same class of bug as the `show_hidden` fix earlier in this
        session, just two more unguarded references in sibling methods.
        Guarded all of them the same way.

---

**Not in scope for "runnable"** — tracked in `CLAUDE.md`'s next-steps for after this
milestone: provider plugin fixes (NZB/torrent/download clients), full rebrand
(CouchPotato → CouchTomato strings/paths/config dir), CI, packaging/Docker.
