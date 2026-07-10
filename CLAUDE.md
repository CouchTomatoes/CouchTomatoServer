# CouchTomato — Project Memory

Read this fully before doing anything else in this repo. It exists so work can resume
across sessions without re-deriving decisions or re-reading the whole codebase.

## What this project is

CouchTomato is a Python 3 port + rebrand of **CouchPotato** (an automatic
NZB/torrent movie downloader). Upstream CouchPotato (github.com/CouchPotato/CouchPotatoServer)
died in Feb 2020, stuck on Python 2, with dependencies vendored in-tree instead of pip.
Goal: a working, modern, Python 3 CouchTomato with full feature parity, keeping the
entire original commit history intact (GPLv3 — rebrand/modification is allowed, license
must stay GPLv3).

## Repo landscape — READ BEFORE TOUCHING OTHER REPOS

There are/were three repos in play. Decisions already made with the user:

- **`CodeAhmed/CouchTomato` (THIS repo) — canonical, active.** All Python porting work
  happens here. Chosen over the alternative because it already has full, authentic
  upstream history imported (see below) instead of hand-replayed commits.
- `CouchTomatoes/CouchTomato` — an earlier manual attempt (48 commits hand-replaying
  real CouchPotato history one commit at a time while porting). **Superseded, not
  canonical.** Don't import work from it or treat it as a merge source unless the user
  asks — it's slower/lower-fidelity than the bulk import already done here.
- `CouchTomatoes/CouchTomatoServer` — a .NET 8 rewrite scaffold (ASP.NET Core API,
  early stage, tags v0.1.0–v0.3.0). **Explicitly paused** by user decision — focus is
  Python parity first. Revisit later, possibly as a from-scratch v2 using the finished
  Python app as the functional/feature reference (there is no mechanical way to get
  git-history parity across a language rewrite — track feature parity via a checklist
  instead, not via commits).

## History policy — DO NOT VIOLATE

`master` on this repo is a **direct, unmodified git import of real upstream
CouchPotato's `master` branch** (5,257 commits, ending at commit `7260c12f`,
"Merge pull request #7319 from CouchPotato/develop", 2020-02-04). This was done via
`git fetch` from `https://github.com/CouchPotato/CouchPotatoServer.git` + push — NOT
a manual replay — so every original commit's SHA, author, timestamp, and message is
preserved exactly. This satisfies the user's hard requirement: **never lose a commit**.

Rules going forward:
- Never rewrite, rebase, or force-push over the imported history on `master`.
- All modernization work happens as new commits **on top of** that history, on a
  feature branch (currently `claude/couch-tomato-parity-e1f5bl`), merged into `master`
  via normal fast-forward/merge — never squash the imported history away.
- If a fresher upstream snapshot is ever wanted, fetch again the same way; don't hand-edit.

## Architecture facts learned (avoid re-discovering these)

- No Python 2 interpreter exists in the sandbox — only Python 3.11. Porting targets 3.11+.
- `CouchPotato.py` does `sys.path.insert(0, 'libs')` — vendored packages in `libs/`
  shadow real pip packages by import name. This means: `pip install X` + `rm -rf libs/X`
  is often a clean, near-zero-code-change swap **if the API didn't change**. Check each
  one — some (tornado) changed drastically between the vendored version and modern.
- Database layer is **CodernityDB** (pure-Python embedded NoSQL), not SQLAlchemy/sqlite
  as might be assumed from similar projects. Don't plan a SQLAlchemy migration step.
- `libs/` originally held 46 vendored packages (~8.3MB). Many have modern, actively
  maintained PyPI equivalents (requests, six, beautifulsoup4→bs4, python-dateutil,
  certifi, rsa, pyasn1, oauthlib, httplib2, html5lib, apscheduler, GitPython, chardet,
  guessit, subliminal). Some are CouchPotato-specific forks with no PyPI equivalent
  (axl/axel event lib, caper, CodernityDB, enzyme) — port these with 2to3 + manual fixes,
  don't try to replace them.
- `lib2to3` (via `python3 -m lib2to3`) is available in this Python 3.11 sandbox (removed
  in 3.12+) and was used for the first mechanical pass. It chokes on: non-UTF8 source
  files (found 2, re-encoded from ISO-8859-1), and a handful of files with syntax it
  can't parse (see progress log) — those need manual/replacement treatment instead.

## Progress log (append here each session — don't delete old entries)

**2026-07-10**
- Imported full real CouchPotato `master` history into `origin/master` (5,257 commits).
- Branch `claude/couch-tomato-parity-e1f5bl` reset to that history, pushed to origin.
- Ran `lib2to3` over `couchpotato/` (51 files changed) — committed.
- Ran `lib2to3` over `libs/` (383 files changed across two passes; hit one UnicodeDecodeError,
  fixed by re-encoding `libs/xmpp/session.py` and `libs/dateutil/parser.py` from
  ISO-8859-1 to UTF-8) — committed.
- 14 files in `libs/` failed to parse under lib2to3 (Py2-only syntax lib2to3's parser
  rejects): `chardet/chardetect.py`, `git/repository.py`, `pytwitter/__init__.py`,
  `pyutil/benchutil.py`, `pyutil/benchmarks/bench_xor.py`,
  `pyutil/scripts/{time_comparisons,try_decoding,verinfo}.py`, `rsa/{cli,util}.py`,
  `tornado/{autoreload,options,template,testing}.py`. Decided: replace these vendored
  packages with pip equivalents rather than hand-fixing 2013-era code.
- Replaced vendored `tornado`, `chardet`, `git` with pip packages (`GitPython` for the
  `git` import name). Started `requirements.txt` (currently: tornado, chardet,
  GitPython, requests).
- **Current blocker**: modern tornado (6.5.7) removed the old `@asynchronous` decorator
  and `IOLoop.instance()` API that CouchPotato's handlers use. This is real porting work
  (async/await rewrite), not mechanical. Affects 8 files:
  `couchpotato/__init__.py`, `couchpotato/api.py`, `couchpotato/runner.py`,
  `couchpotato/core/_base/_core.py`, `couchpotato/core/notifications/core/main.py`,
  `couchpotato/core/plugins/base.py`, `couchpotato/core/plugins/file.py`,
  `couchpotato/core/plugins/renamer.py`, `couchpotato/core/plugins/userscript/main.py`.
  **Not yet started.**
- App does not boot yet (`python3 CouchPotato.py --help` fails on the tornado import above).

**2026-07-10 (cont'd)**
- Ported the 8 tornado-dependent files: only `couchpotato/api.py` actually used the
  removed `@asynchronous` decorator — fixed by setting `self._auto_finish = False`
  (confirmed via `tornado.web.RequestHandler._execute` source that this is exactly
  what `@asynchronous` did internally). `_core.py` used private `IOLoop._closing`
  (no longer exists on the asyncio-based IOLoop in modern tornado) — removed those
  checks, `add_callback`/`stop()` are safe to call unconditionally here.
- Found and fixed a **systemic pattern**: `couchpotato/core/helpers/encoding.py`'s
  `ss()` helper encodes to `bytes` (a Py2 "safe string" idiom). Several call sites
  pass its result into `str`-only APIs (`os.path.normpath`+`rstrip` in `sp()`,
  `re.sub` in `logger.py`'s `safeMessage()`), which breaks in Py3. Fixed both call
  sites by using `toUnicode()` instead of `ss()` — paths and log messages should
  stay `str` throughout in Py3, there's no need to round-trip through bytes.
  **Expect this same `ss()`-misuse pattern elsewhere in the codebase** (providers,
  renamer, etc.) — grep for `ss(` when hitting bytes/str TypeErrors.
- Removed vendored `libs/requests` (ancient version uses `collections.MutableMapping`,
  which moved to `collections.abc` in Py3.10+) — pip-installed `requests` was already
  in `requirements.txt`, just needed the vendored copy out of the way.
- Fixed a Py2 unbound-method idiom in vendored `libs/CodernityDB/database.py`:
  `new_index.__class__.__init__.__func__.__code__` — `.__func__` doesn't exist in Py3
  (plain functions aren't wrapped), just drop it.
- **Result: `python3 CouchPotato.py --help` now works end to end.** Actually starting
  the server (`python3 CouchPotato.py --data_dir ... --console_log --debug`) gets
  through CLI parsing and into `db.create()`, then fails inside CodernityDB's
  `_add_single_index` → `header_for_indexes(...)`: `TypeError: a bytes-like object is
  required, not 'str'` at `libs/CodernityDB/database.py:177` (`f.write(...)`). This is
  the **next thing to fix** — likely the same bytes/str theme, but this time the
  target (a binary file write) may legitimately need bytes, so check `header_for_indexes`'s
  return type before blindly wrapping in `toUnicode()`.
- Opened a PR from `claude/couch-tomato-parity-e1f5bl` into `master` (draft, WIP),
  assigned to the repo owner, to make progress visible/reviewable while porting continues.
- Added `TODO.md`: a scoped, checkbox-style checklist (separate from this file) tracking
  specifically "what's needed to reach a runnable Python 3 app" — check it for granular
  status instead of duplicating that detail here going forward.

**2026-07-10 (cont'd, boot to a working web UI)**
- Replaced vendored `CodernityDB` (Python 2, would have needed ~50+ manual
  `struct.pack`/`unpack` bytes fixes across `hash_index.py`/`tree_index.py`) with
  **`libs/codernitydb3`** — a maintained Python-3-native fork found on PyPI as
  `CodernityDB3` (Apache 2.0). The PyPI wheel's `setup.py` doesn't build cleanly in
  this sandbox (old distutils `install_layout` incompatibility with modern
  setuptools), so the source was vendored directly from the sdist instead of
  `pip install`-ed. **Important:** generated index files (via
  `header_for_indexes()`) contain the literal string `from CodernityDB.tree_index
  import ...` baked in as text and `exec`'d at runtime — so a plain rename wasn't an
  option. Solved with a thin compatibility shim at `libs/CodernityDB/` (5 small files
  re-exporting from `codernitydb3`) so every existing `from CodernityDB.X import Y`
  import — including the ones embedded in generated files — keeps working unchanged.
- Fixed `axl/axel.py` (CouchPotato's vendored event dispatch lib): `hashlib.md5(str(handler))`
  needs `.encode()`. This one is high-value — nearly every event registration in the
  app (`addEvent`) goes through this hash, so it was silently breaking most
  `app.load`/`database.setup`/etc. event handlers even after the server "started".
- Fixed `async` used as a bare variable name in `couchpotato/core/plugins/renamer.py`
  (reserved keyword since Python 3.7, was a `SyntaxError` that killed the whole
  renamer plugin's import) — renamed to `is_async`, kept the `'async'` string key in
  the public API kwargs unchanged.
- Fixed `Thread.isAlive()` → `.is_alive()` in vendored `libs/apscheduler` (removed in
  Python 3.9). Apscheduler is still on the "replace with pip" list in `TODO.md`
  eventually, but modern APScheduler 3.x changed the scheduling API significantly
  (`add_interval_job` → `add_job(trigger='interval', ...)`), so that's a real rewrite,
  not a drop-in swap — left as vendored + patched for now.
- **Found and fixed the single biggest recurring bug class**: every CodernityDB index
  class's `make_key`/`make_key_value` methods (in
  `couchpotato/core/media/_base/media/index.py`, `couchpotato/core/settings.py`,
  `couchpotato/core/plugins/quality/index.py`,
  `couchpotato/core/plugins/release/index.py`) return `str`, but codernitydb3's
  struct-based storage format requires `bytes` for lookup/storage keys (its own
  default `make_key` does exactly `key.encode('utf8')` — our overrides need to match
  that contract). Fixed every occurrence to `.encode('utf-8')` the final key value.
  **If a new/updated index class ever gets added, make sure its `make_key`/
  `make_key_value` return bytes, not str** — this is easy to get wrong again.
- Fixed JSON serialization crashing on CodernityDB's own internal `_rev` field, which
  is intentionally `bytes` at the storage-engine level (needed for its packed binary
  format) but leaks into documents returned to the API/template layer. Rather than
  fighting that through the DB internals, added `jsonBytesDefault()` in
  `couchpotato/core/helpers/encoding.py` (decodes stray bytes to str) and wired it
  into (a) `api.py`'s explicit `json.dumps()` call and (b) a global monkeypatch of
  `tornado.escape.json_encode` in `couchpotato/__init__.py` — tornado's templates
  (`index.html` etc.) and `RequestHandler.finish(dict)` both route through that
  function, so patching it once covers both.
- Fixed `Env.get('x', unicode = True)` calls in `couchpotato/templates/index.html` —
  the function's actual parameter is named `str`, not `unicode` (someone modernized
  the signature at some point but not the 3 call sites).
- Removed a dead `from itertools import izip` (Py2-only) baked into
  `TitleSearchIndex`'s `custom_header` — unused by the class's methods, was just
  breaking that index's generated file.
- Removed a stray `print(locals())` debug leftover in vendored
  `libs/codernitydb3/storage.py` that was spamming the log with internal doc metadata
  on every read.
- **Result: the server now boots cleanly and the web UI actually renders.**
  `python3 CouchPotato.py --data_dir <dir> --console_log --debug` starts, binds port
  5050, and `curl http://127.0.0.1:5050/` returns a full rendered HTML page (verified
  — not yet checked in an actual browser). This is the milestone `TODO.md` section 4
  was tracking.
- Known remaining non-fatal issue: `profile.forceDefaults` on a fresh/empty DB hits a
  `struct.error` reading an empty B-tree leaf in `codernitydb3/tree_index.py` — caught
  gracefully by the event system so it doesn't block boot, but likely affects
  "first movie added" flows. See `TODO.md` §5.
- A long tail of individual provider/notification/downloader plugin modules still fail
  to import (each is caught and skipped independently by the loader, so none of them
  block boot) — full list is in `TODO.md` §5, this is the "provider plugins" bucket
  from the next-steps list below, now that the app actually runs.

**2026-07-10 (cont'd, verified in a real browser — found and fixed the two real showstoppers)**
- `curl` showing a 200 with rendered HTML was misleading — actually drove the app in
  headless Chromium (Playwright, `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`;
  no `playwright` npm package locally but it's installed globally — `require(execSync('npm
  root -g') + '/playwright')`). Found the page was **blank white** despite the curl
  "success". This is exactly the gap the project's testing guidance warns about:
  curl/test suites verify the response exists, not that the feature works.
- **Bug 1 — static asset routing order.** `couchpotato/runner.py` registered the
  catch-all `WebHandler` route in one `application.add_handlers()` call, then
  `StaticFileHandler` routes in a *second, later* call. Tornado matches handlers in
  registration order, so the catch-all always won and every `/static/scripts/*.js`
  request got redirected to `/#static/scripts/...` instead of served. The browser
  then tried to execute the redirect target's HTML as JavaScript
  (`Unexpected token '<'`), so the frontend framework (MooTools) never initialized.
  **Fix: register static handlers before the catch-all.** Simple reordering, no logic
  change.
- **Bug 2 — the big one.** Every API response was silently vanishing:
  `curl .../api/<key>/settings/` just hung forever, no error, no timeout. Diagnosed
  with `py-spy dump --pid <pid>` (had to `pip install py-spy`) — found the API
  worker thread had already *finished*, not blocked, meaning the handler ran to
  completion but its response never got sent. Root cause: `couchpotato/api.py`'s
  `ApiHandler.taskFinished()` runs inside a background `Thread` (every API call goes
  through `run_handler`'s `@run_async` thread-per-request pattern) and called
  `IOLoop.current().add_callback(self.sendData, ...)` — but `IOLoop.current()` called
  from a thread that isn't running an event loop **creates and returns a brand-new,
  never-started IOLoop**, not the real running one. So the callback got scheduled on
  a phantom loop that never executes, and the HTTP response never got sent — for
  every single API call in the entire app. Confirmed with a minimal repro
  (`IOLoop.current()` on main thread vs. inside a `threading.Thread` returns two
  different `id()`s). **Fix:** capture `main_ioloop = IOLoop.current()` once at
  `api.py` import time (which happens on the main thread, before the server starts
  and before any worker threads exist), export it, and use that captured reference
  instead of calling `IOLoop.current()` fresh inside any worker-thread callback.
  Applied the same fix to `core/_base/_core.py`'s `shutdown()`/`restart()` (also
  API-routed → also worker-thread-called → same bug) and
  `core/notifications/core/main.py`'s `frontend()` notification broadcaster.
  **Any future code that schedules a tornado callback from inside a thread must use
  `main_ioloop` from `couchpotato.api`, never call `IOLoop.current()` directly from
  that thread** — this is a sharp edge that will bite again if forgotten.
- **Bug 3.** While chasing why `profile.forceDefaults` failed on a fresh DB, found a
  genuine upstream bug in vendored `libs/codernitydb3/tree_index.py`:
  `_find_key_many`'s `except ElemNotFound:` handler blindly followed `next_leaf` as a
  file offset, but `next_leaf == 0` legitimately means "no next leaf" for a
  freshly-created empty index (not a valid offset) — following it read garbage bytes
  at file offset 0 (the file header), which decoded into an even more bogus "next
  leaf" pointer on the next iteration, eventually seeking miles past EOF and crashing
  with `struct.error: unpack requires a buffer of 10 bytes`. The analogous singular
  `_find_key` method already had the correct `if next_leaf:` guard — `_find_key_many`
  was just missing it. Reproduced in isolation with a minimal standalone script before
  fixing, verified fixed the same way. Note: `_find_key_smaller` (~line 1722 in that
  file) has the same unguarded-`prev_leaf` pattern but isn't exercised by any current
  CouchPotato code path — left alone, flagged in `TODO.md`.
- **Result: the setup wizard actually renders and is interactive** — "Welcome to the
  new CouchPotato", real form fields (Username/Password/Port etc.), confirmed via
  screenshot. This is the first time the frontend has been proven to *work*, not just
  "return 200."
- Along the way, found (but did NOT yet fix — logged in `TODO.md` §5) three more real
  bugs surfaced by the now-working API layer: `tryUrlencode()` iterating `bytes` in
  Python 3 (yields `int`s, not chars), a bytes-repr literally leaking into the TMDB
  API key parameter (`b'e224...'` sent as the actual key, breaks all TMDB requests),
  and an integer being passed directly as an HTTP header value where `requests`
  needs a string. `profile.forceDefaults` still has one more DB-layer issue
  (`EOFError` in `marshal.loads`) separate from the tree_index bug — not yet
  root-caused.
- Cleaned up: removed `py-spy` install artifacts aren't committed (pip-installed to
  the system, not the repo); temp repro scripts lived only in the scratchpad dir, not
  the repo.

**2026-07-10 (cont'd, second bug batch + full provider plugin backlog cleared)**
- Fixed the second batch of bugs from browser-testing: `tryUrlencode()`'s
  bytes-iteration (`quote_plus` accepts bytes directly, simplified to one call
  instead of the old char-by-char loop), the TMDB API key bytes-repr leak
  (`base64.b64decode()` returns `bytes` in Py3, needed `.decode('utf-8')`), and two
  independent instances of raw int/float HTTP header values (`couchpotatoapi.py`,
  `trakt/main.py`) that `requests` rejects. The `profile.forceDefaults` `EOFError`
  no longer reproduced — was a downstream symptom of the routing/IOLoop fixes, not
  a separate bug. Root-caused (not fixable) the `CouchPotatoApi` "Failed to parsing"
  error: `couchpota.to` is a permanently parked/for-sale domain now.
- Added a tomato icon (favicon/touch icons/mask icon, light+dark) sourced from the
  🍅 emoji in `CouchTomatoServer`'s README, rendered via headless Chromium
  (`Noto Color Emoji` font) and resized into every format/size the templates already
  reference — no template changes needed.
- Attempted to mirror upstream CouchPotato's 27 git tags into this repo. Fetching
  them works fine over plain git, but **pushing tags is hard-blocked with HTTP 403
  at the proxy layer** this session's git traffic runs through (confirmed with
  `GIT_CURL_VERBOSE=1` — same result on a disposable test tag, so it's not
  content-specific). No `create_ref`/`create_release` tool exists in the GitHub MCP
  server either. Documented options in `SUGGESTIONS.md` for the repo owner to decide
  — this needs their input, not something to keep retrying.
- **Fixed the entire provider/notification/downloader plugin import backlog: ~50
  failing imports down to 0.** First widened `logger.py`'s context field (was
  hard-truncating module names to the last 25 characters — `self.context[-25:]` —
  making it hard to tell which module actually failed); then grouped the ~50
  failures by root-cause exception instead of fixing file-by-file, which turned it
  into ~8 fixes instead of ~50:
  - 38 provider files (torrent/nzb/automation/userscript/trailer) all failed on the
    exact same line in vendored `bs4`: `HTMLParseError` removed from `html.parser`.
    Replaced vendored `bs4` with pip `beautifulsoup4` — one swap fixed all 38.
  - 5 downloader clients (deluge, hadouken, qbittorrent, rtorrent, utorrent) all
    failed on vendored `bencode` importing removed `types.StringType` etc. Replaced
    with pip `bencode.py`, which happens to expose the exact same `bencode`/`bdecode`
    function names the call sites already use — clean swap.
  - `notifications.twitter`: vendored `pytwitter` imported the removed `rfc822`
    module (`email.utils` has a drop-in `parsedate`), which transitively needed
    vendored `httplib2`, which imported the renamed `email.Utils` → `email.utils`.
    Replaced vendored `httplib2` with pip `httplib2` too rather than patch both.
  - `notifications.xmpp_` / `plugins.scanner` / `plugins.subtitle`: vendored `xmpp`
    had Python 2 string-exception `raise` syntax (`raise 'msg', arg` — 4 occurrences
    in `debug.py`), implicit intra-package imports (`import dispatcher` instead of
    `from . import dispatcher` — Python 3 requires explicit relative imports), and
    the removed `sha`/`md5` modules inside its SASL DIGEST-MD5 auth code
    (`auth.py`) — had to keep the whole `H()`/`HH()`/`C()` hash-chaining helper
    trio consistently in bytes rather than naively encoding each call site, since
    they feed into each other and DIGEST-MD5 needs the raw digest bytes, not a
    decoded string, fed back into the next hash. Vendored `subliminal` had
    `from .async import Pool` (`async` became a reserved keyword in Python 3.7) —
    renamed the module file (`async.py` → `async_pool.py`) rather than replacing
    vendored subliminal with the pip package, since modern subliminal 2.x's API
    changed too much (`scanner.py`/`subtitle.py` use the old
    `subliminal.videos.Video`-era structure throughout — a pip swap here would need
    rewriting the calling code, not just the import).
  - `downloaders.utorrent`: vendored `multipartpost.py` used the removed
    `mimetools` module and old `urllib2.Request.get_data()`/`.add_data()` methods
    (don't exist on Python 3's `urllib.request.Request` — it uses a plain `.data`
    attribute). Rewrote the whole multipart encoder to work in bytes throughout,
    since the actual payload (`.torrent` file content) is binary — patching just the
    `mimetools` import would have left a silent bytes+str concatenation crash one
    layer deeper.
  - `_base.updater`: rewrote `GitUpdater` against GitPython's real API (`git.Repo`,
    `.remote()`, `.active_branch`, `.head.commit`, `.refs`, etc.) — not a mechanical
    swap since the object model differs from the old `git.repository.LocalRepository`
    (e.g. remote branch refs come back named `origin/master`, needed `.remote_head`
    to get the bare branch name back for comparison). This surfaced a second bug:
    `git.refresh('git')` resolves a bare command name relative to cwd instead of
    searching `$PATH`, silently breaking the default (most common) case — fixed by
    only calling `git.refresh()` when a real custom git path is configured.
  - `torrentleech`: a plain `TabError` (mixed tabs/spaces), unrelated to the above.
- **Verified via full boot: 0 remaining loader import failures**, homepage still
  renders 200. One new non-fatal finding, now that the updater actually runs instead
  of being silently crash-skipped: a `profile.forceDefaults` `ElemNotFound` during
  initial profile cleanup, possibly a timing interaction with the updater's `git
  fetch` now running at startup — logged in `TODO.md` §5, not yet root-caused.
- **PR #1 merged into `master`.** Added `.github/workflows/release.yml` first (fires
  on every push to `master`, auto-tags starting at `v1.0.0` then increments the patch
  version from the latest `vN.N.N` tag each time) so it would take effect on this
  exact merge. It did: `v1.0.0` was created successfully right after merging,
  confirmed via the Actions run (`conclusion: success`) and `GET
  /releases/tags/v1.0.0`. Notably, this proves the tag-push `403` documented in
  `SUGGESTIONS.md` is specific to this session's proxied git credentials, not a
  GitHub-side restriction — a GitHub Actions run using the repo's own `GITHUB_TOKEN`
  can create tags fine. Added a 4th option to `SUGGESTIONS.md` on that basis (a
  one-off `workflow_dispatch` job to mirror upstream's tags from inside an Action).
- Branch `claude/couch-tomato-parity-e1f5bl` reset to the new `master` tip
  (`f4b76a5f`) per the merged-PR restart convention in this file's working
  conventions section, ready for the next round of work.

## Next steps (in order)

**Boot milestone reached 2026-07-10: server starts, web UI renders and is verified
interactive in a real headless browser (setup wizard works end to end). Provider
plugin import backlog cleared same day: 0 remaining loader failures, down from ~50.**
See `TODO.md` for the detailed, checkbox-tracked list — this section is now the
higher-level plan for what comes after.

1. Root-cause the new `profile.forceDefaults` `ElemNotFound` finding (see progress
   log) — possibly a timing interaction with the updater's `git fetch` now running
   at startup, now that the updater plugin actually loads instead of being silently
   skipped.
2. Continue clicking through the actual UI in the browser (wizard → save → main app →
   settings → try adding a movie, try triggering a real search against one of the
   now-loading torrent/nzb providers) to find the next layer of real runtime bugs —
   this approach found several major ones already; curl/import-success alone won't
   catch them.
3. Replace remaining easy vendored libs (six, dateutil, certifi, html5lib, oauthlib,
   rsa, pyasn1 — tornado/chardet/requests/GitPython/CodernityDB3/bs4/bencode/httplib2
   already done) with real pip packages + grow `requirements.txt`.
4. Hand-port the remaining CouchPotato-specific vendored libs with no drop-in
   replacement (axl, caper, enzyme, pynma, gntp, etc.) with 2to3 + manual fixes.
   apscheduler is vendored+patched for now; a real swap to pip APScheduler needs an
   API rewrite (`add_interval_job` → `add_job(trigger='interval', ...)`), not just a
   dependency swap.
5. Rebrand: package name, `~/.couchpotato` → `~/.couchtomato` config dir, UI strings,
   Docker/systemd units, docs.
6. CI + packaging.
7. Decide on the tag-mirroring question in `SUGGESTIONS.md` (blocked on repo owner
   input, not something to keep retrying).

## Working conventions

- Development branch: `claude/couch-tomato-parity-e1f5bl`. PR into `master` when ready
  for review (don't push directly to `master` again without the user's explicit say-so —
  that was a one-time exception for the initial history import).
- Commit after each mechanical/logical step, not in one giant diff — makes the porting
  process auditable and bisectable.
- No `.env`/secrets expected in this repo; none encountered so far.
