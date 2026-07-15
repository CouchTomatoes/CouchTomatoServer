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

**2026-07-10: the project moved. `CouchTomatoes/CouchTomatoServer` is now canonical.**

- **If you're a session working in `CouchTomatoes/CouchTomatoServer`**: that's the
  canonical repo now — carry on exactly as the rest of this file describes, just
  mentally substitute `CouchTomatoes/CouchTomatoServer` anywhere `CodeAhmed/
  CouchTomato` is referenced (including in the progress log below, which predates
  the move and still says `CodeAhmed/CouchTomato` throughout — that's accurate
  history, not a mistake to fix). Full history — `master`, the
  `claude/couch-tomato-parity-e1f5bl` dev branch, and every tag — was pushed there
  directly (`git push`, not a rewrite), and all GitHub Releases were mirrored to
  match via `.github/workflows/mirror-releases-to-target.yml` (verified beforehand:
  its read/parse/iterate logic was dry-run tested against the real ~25-release
  dataset here first — see the 2026-07-10 progress log entry and `SUGGESTIONS.md`).
  Working conventions (dev branch name, PR-before-merge, etc.) all still apply
  unchanged, just in the new repo.
- **If you're a session working in `CodeAhmed/CouchTomato` (this repo)**: it's now
  the **historical origin / legacy mirror**, not where active development
  continues. Nothing here is invalidated — it still holds the authentic imported
  upstream history and everything built on top through the move — but new work
  should happen in `CouchTomatoServer` going forward. Why: the user wanted the
  project living under their `CouchTomatoes` account, matching where the earlier
  .NET scaffold and manual-replay attempt also live. This session's GitHub/git
  access is permanently scoped to `codeahmed`-owned repos for its whole lifetime
  (confirmed by testing both `add_repo` and a direct authenticated `git push`
  against `CouchTomatoes/CouchTomatoServer` — both refused, independent of actual
  GitHub collaborator permissions), so it cannot itself push further changes there;
  a genuinely fresh session started with `CouchTomatoServer` as its *initial* repo
  source is required to work there directly.

Other repos in play:

- `CouchTomatoes/CouchTomato` — an earlier manual attempt (48 commits hand-replaying
  real CouchPotato history one commit at a time while porting). **Superseded, not
  canonical.** Unrelated to the move above — don't confuse with `CouchTomatoServer`,
  and don't import work from it or treat it as a merge source unless the user asks.
- `CouchTomatoes/CouchTomatoServer-DotNet-WIP` — the .NET 8 rewrite scaffold (ASP.NET
  Core API, early stage, tags v0.1.0–v0.3.0). Renamed from `CouchTomatoServer` by
  the user to free up that name for the Python project's move. **Still explicitly
  paused** by user decision — focus is Python parity first. Revisit later, possibly
  as a from-scratch v2 using the finished Python app as the functional/feature
  reference (there is no mechanical way to get git-history parity across a language
  rewrite — track feature parity via a checklist instead, not via commits).
- `CodeAhmed/CouchPotatoAPI` — a fork of the archived, unlicensed `CouchPotato/
  CouchPotatoAPI` (source for the dead `api.couchpota.to` backend; see `TODO.md`
  §5 and `README.md`'s "Project status" note). The user also asked for this
  mirrored into a `CouchTomatoes` repo, same reasoning as the main move — check
  `SUGGESTIONS.md` for whether that's been done yet.

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

**2026-07-10 (cont'd, mirrored all upstream tags + releases)**
- PR #2 (docs + the one-off tag-mirroring workflow) merged, which also correctly
  triggered `release.yml` again — `v1.0.1` was created automatically, confirming the
  "release on every push to master" behavior works as intended across multiple merges.
- Ran the one-off `mirror-upstream-tags.yml` workflow via `workflow_dispatch`.
  **First attempt had a bug**: the workflow added a second git remote (`upstream`) to
  fetch tags from, which confused `gh`'s automatic repo-detection — all 12
  `gh release create` calls silently targeted `CouchPotato/CouchPotatoServer` instead
  of `CodeAhmed/CouchTomato` and failed with `403 Resource not accessible by
  integration`. Caught via job logs (`get_job_logs`), not from the run's overall
  "success" status — the shell script's `|| echo` swallowed the failures so the step
  still exited 0. **Fix:** pass `--repo "$GITHUB_REPOSITORY"` explicitly to `gh
  release create` rather than relying on ambient detection. Re-ran successfully
  against the feature branch directly (confirmed `workflow_dispatch` only needs the
  workflow *registered* on the default branch once — after that it can be dispatched
  against any ref, including a branch with an unmerged fix).
- **Result**: all 27 upstream tags now on this repo. 12 of them
  (`build/2.0.8`–`build/3.0.1`) had real GitHub Release objects upstream and got
  their title/body mirrored verbatim — confirmed by reading the actual release notes
  back (original changelog badges, `RuudBurger/CouchPotatoServer/compare/...` links,
  even the original author's jokes in the release bodies). The other 15 tags are
  bare, matching upstream (they never had Release pages either). Removed the
  workflow file afterward since it was explicitly single-use.

**2026-07-10 (cont'd, release automation polish + resumed browser click-through testing)**
- User asked to renumber releases to start at `v4.0.0` (retiring v1.0.0–v1.0.2 as a
  false start) and to style auto-generated release notes like the mirrored upstream
  ones (green NEW / red FIX badge-icon bullets instead of GitHub's default "What's
  Changed" summary). Updated `.github/workflows/release.yml` accordingly; deleted
  the v1.0.x releases/tags via a one-off `cleanup-old-releases.yml` workflow (same
  pattern as the tag-mirroring one-off — proxy blocks direct tag deletion from this
  session, `GITHUB_TOKEN` in Actions doesn't). First release (`v4.0.0`) initially
  only summarized the single triggering push; fixed `release.yml` so a genuine
  "first release" pulls full history since the upstream import boundary (`7260c12f`)
  instead, and backfilled `v4.0.0`'s notes the same way via another one-off workflow.
  All one-off workflow files removed after running, per established convention.
- At the user's request, forked `CouchPotato/CouchPotatoAPI` (the dead
  `api.couchpota.to` backend's source) into `CodeAhmed/CouchPotatoAPI` — this
  session's GitHub App can't fork cross-org or create repos itself, so did a mirror
  `git clone` + the user manually clicked GitHub's own Fork button, then this session
  cloned the fork locally to inspect it. Confirmed the fork's routes/auth headers
  match our `couchpotatoapi.py` client exactly (no protocol changes needed if it were
  ever revived), and that it's a bigger dependency than just movie suggestions —
  `trakt/main.py` and `putio/main.py` both also hit `api.couchpota.to` for OAuth
  relay. Documented all of this, plus the fork being archived/unlicensed/undocumented
  for setup, in `README.md`'s "Project status" note and `TODO.md` §5.
- **Resumed the "next steps" #2 browser click-through task** (previously blocked
  behind the release-automation detour) and immediately found the exact
  `profile.forceDefaults` `ElemNotFound` bug flagged as unresolved — it now
  reproduces on essentially every fresh-DB boot, not just occasionally.
  **Root-caused it**: `couchpotato/core/event.py`'s `fireEvent` dispatches any event
  with more than one subscribed handler (`app.load`, `app.initialize`, etc.) across a
  10-thread pool via `axl.axel.Event`. Many plugins touch the database from those
  handlers, but `libs/codernitydb3/database.py`'s `Database` class does
  unsynchronized `seek`+`read`/`write` on shared index file handles — concurrent
  writes from different plugins race on the same on-disk files, most visibly the
  shared `id` index every document type writes through. One thread reads a bucket
  pointer another thread just wrote before the corresponding entry bytes are in
  place, and gets back a short read (`struct.error`) or a stale offset
  (`ElemNotFound`). **Fix**: added a single `threading.RLock()` to `Database`, held
  across every public entry point (`insert`/`update`/`get`/`get_many`/`all`/
  `delete`) — RLock specifically because e.g. `all(with_doc=True)` calls back into
  `get()` on the same thread while already holding the lock. Verified: reproduced
  the crash reliably before the fix, then got 3 consecutive clean fresh-DB boots
  after it. **This was likely always a latent bug in the original vendored
  CodernityDB too** (Python 2's GIL + different timing may have mostly hidden it) —
  not something the codernitydb3 swap introduced, just something the swap didn't
  fix either.
- Continuing the click-through, found and fixed a real (if minor) wizard bug:
  `Page.Wizard` never set `default_action` (unlike the Settings page, which gets it
  wired up externally by `page/about.js`), so `Page.Settings.openTab()`'s fallback
  chain (`action == 'index' ? default_action : action`) resolved to `undefined` on
  the wizard's normal first-load path (`create()`'s parameterless
  `self.openTab()` call), crashing `toggleTab`'s `tab_name.split('/')` with
  `Cannot read properties of undefined (reading 'split')` — confirmed via a Playwright
  harness that this happened on the real final `/#wizard/` page, not a transient
  redirect artifact. Fixed by adding `default_action: 'welcome'` to `Page.Wizard` in
  both `couchpotato/core/plugins/wizard/static/wizard.js` and the pre-built
  `combined.plugins.min.js` bundle it ships as (this repo doesn't have a working
  `grunt` build pipeline set up in-sandbox, so the served bundle is hand-patched to
  match source — flagged as a real gap, see `TODO.md`).
- Also found (separately) a **cosmetic-only, pre-existing class of console error**:
  the wizard's index page does a synchronous client-side redirect
  (`window.location = '.../wizard/'`) before `<body>` finishes settling, and several
  unrelated `domready` handlers (`page/login.js`'s `hasClass` check was the first
  one hit) can fire on the *old, already-being-discarded* document mid-navigation,
  where `document.body` intermittently reads back `null`. Confirmed via a Playwright
  harness (diffing `readyState`/`href` at the moment of each error) that this is
  fully confined to the torn-down old document and never affects the real page users
  land on. Added a defensive `if(!b) return;` guard to `login.js` (source +
  `combined.base.min.js`) to silence the one instance actually hit in practice;
  there may be others further down the same `domready` handler queue that never got
  reached once this one was silenced — not chased further since they're provably
  inert, logged in `TODO.md` §5 as a known, low-priority, cosmetic-only item.
- Also noted a stray broken image reference (`https://couchpota.to/media/images/
  userscript.gif`, `net::ERR_CONNECTION_RESET`) — same dead-domain root cause as the
  `CouchPotatoApi` provider, just a static asset this time instead of an API call.
  Not fixed yet, logged in `TODO.md` §5.

**2026-07-10 (cont'd, the download-to-library pipeline — 6 bugs, verified against a real transmission-daemon)**
- User asked the real question this whole port has been building toward: does adding
  a movie actually send it to Transmission, and once a download completes, do the
  background jobs (renamer/scanner) reliably move it into the library? Answer at the
  start of this investigation: **no, at multiple points** — verified by actually
  running the pipeline, not just reading the code.
- Installed a real `transmission-daemon` in this sandbox (RPC-authenticated,
  `rpc-username`/`rpc-password` set) instead of mocking anything. Used
  `transmission-create` + `truncate -s 250M` to make a legitimately-sized dummy movie
  file and pre-seed it into Transmission's own `download-dir`, so adding the torrent
  hash-checks against already-present data and reports 100% complete instantly — a
  standard way to exercise a real torrent client without waiting on network/trackers.
- **Found and fixed 6 bugs, all the same root cause**: Python 2 code where
  `.encode()` on a string (or iterating the result of one) used to behave like `str`
  now returns real `bytes` in Python 3, and the call site never decoded back:
  1. `couchpotato/core/settings.py`: `Settings.saveView()` did
     `value.encode('unicode_escape')` and stored the raw **bytes** straight into
     `RawConfigParser` — **every setting saved through the UI/API was silently
     corrupted**. Booleans came back `False` forever (`getBool()`'s fallback compares
     `bytes == 1`, always False); text came back as the literal string
     `"b'http://localhost:9091'"` (`toUnicode()`'s `str(bytes)` fallback). This alone
     broke the Transmission downloader ("port is missing" — because the trailing `'`
     from the bytes-repr broke the host:port split). Fixed: decode back to `str`
     before storing.
  2. `couchpotato/core/helpers/encoding.py`: `toSafeString()` did
     `.encode('ASCII', 'ignore')` without decoding back, so `for c in cleaned_filename`
     yielded `int`s instead of characters (`'in <string>' requires string as left
     operand, not int`). `getImdb()`/`simplifyString()` call this unconditionally, so
     **`movie.add()` was completely broken** for a normal "add by IMDB id" — the
     single most basic user action in the whole app. Fixed: decode back to `str`.
  3. `couchpotato/core/plugins/scanner.py`: `os.path.join(sp(root), ss(filename))`
     mixed a `str` with `ss()`'s intentional `bytes` return
     (`TypeError: Can't mix strings and bytes in path components`), crashing the
     `os.walk()`-based folder scan outright — the renamer's scan of the downloads
     folder always found 0 files. Fixed by dropping the unnecessary `ss()` (filenames
     from `os.walk()` are already `str`). Also cleaned up 3 more `ss()` misuses in
     `get3dType()`/`getMeta()` in the same file that don't crash today (not exercised
     by a non-3D test file) but would corrupt 3D-tag and embedded-title matching the
     same way once real files hit those paths.
  4. `couchpotato/core/plugins/quality/main.py`: `containsTagScore()` checked
     `ss(alt.lower()) in words` where `words` is a list of `str` — `bytes in
     list-of-str` doesn't raise, it just always evaluates `False`. **Quality *tag*
     matching (1080p, BluRay, x264, etc.) has been silently dead this whole time**,
     quietly falling back to weaker extension-only scoring for every release. This is
     the dangerous variant of the bug class — no traceback, no log, just wrong
     behavior — found by noticing multiple qualities (2160p/1080p/720p) all "matched"
     a single-quality test filename equally via extension only.
  5. `couchpotato/core/plugins/renamer.py`: `doReplace()` — the function that builds
     *every* destination file/folder name during a rename — returned `ss(...)`
     instead of `str`, so `scan()`'s final
     `os.path.join(destination, final_folder_name, final_file_name)` crashed the same
     way as #3. **This is the bug that directly blocked "move the finished download
     into the library."**
  6. `couchpotato/core/plugins/file.py`: same pattern in
     `Filesystem.download()`'s cache-path construction, breaking movie
     poster/backdrop image caching (`file.download` event errors during rename).
  Each bug was confirmed individually by reproducing its exact traceback before
  applying the fix, not just inferred from reading the diff.
- **Full pipeline verified working, twice, from a fresh DB**: configured Transmission
  + renamer `from`/`to` folders via the real settings API →
  `download.transmission.test` → `true` → added "The Matrix" via `movie.add` (real
  TMDB metadata pulled in) → seeded torrent shows 100% complete in Transmission →
  `renamer.scan()` API call detects the file, correctly identifies `the matrix 1999`
  via filename parsing, matches it against the movie added above (confirmed via
  `couchpotatoapi.py`'s `/search/` fallback when TMDB direct lookup didn't fire),
  scores its quality, and moves+renames it to `Matrix, The (1999)/The Matrix.mkv` in
  the configured library folder, removing it from the downloads folder. Movie status
  and release status both flip to `done`. Repeated the whole cycle a second time
  from a completely fresh DB/config with the same result.
- Two things intentionally **not** chased as bugs after checking them: a 200MB
  minimum-file-size filter (`scanner.py`'s `file_sizes['movie']['min']`, working as
  designed — my first test file was 5MB and correctly got skipped as a
  sample/trailer) and a 1-minute "still unpacking" freshness guard on newly-created
  files (also working as designed).
- PR #8 merged same day, at the user's explicit direction (part of asking to move
  the stable project to `CouchTomatoes` — see below).

**2026-07-10 (cont'd, release notes were silently broken — two compounding bugs)**
- User reported releases were auto-generating with "No notable changes" even
  though real commits had landed (v4.0.2, v4.0.3, v4.0.5, v4.0.6 all affected;
  v4.0.1 and v4.0.4 were showing *incomplete* notes, missing one commit each).
  Root-caused as **two separate, compounding bugs** in `release.yml`, found by
  reproducing the exact failing script locally rather than guessing from the
  YAML:
  1. The notes range was computed from `github.event.before` (the push event's
     previous-SHA field), which turned out to be **unreliable when several PR
     merges land in quick succession** (exactly what happens during an active
     session — 5 merges within ~10 minutes). Confirmed by diffing the actual
     previous release *tag* against each broken release's target commit: the
     real commits were always there in git, `event.before` just didn't point
     where expected. Fixed by computing the range from the **latest existing
     release tag** instead (`latest_tag..HEAD`) — derived from real git state,
     immune to event-delivery timing.
  2. Even after fixing #1, the very next release (v4.0.7) *still* came out "No
     notable changes" despite a provably-correct `v4.0.6..HEAD` range. Second
     root cause, found by reproducing the notes-generation script locally line
     by line: `git log --pretty=format:'%s'` deliberately omits a trailing
     newline after the last log entry, and a bare `while IFS= read -r subject;
     do ... done` **silently drops any final line that isn't
     newline-terminated**. For a single-commit range — the common case for a
     one-commit PR — that's the *only* line, so the loop body never executes
     at all. For multi-commit ranges it silently dropped just the last
     (chronologically oldest) commit, which is exactly why v4.0.4 was missing
     one of its four entries. Fixed with the standard bash idiom
     `while IFS= read -r subject || [ -n "$subject" ]`.
  Verified each fix by reproducing the failure locally first (`bash -c` with
  the exact script + exact tag range), confirming the fix resolves it, before
  touching the workflow file.
- Backfilled v4.0.1 through v4.0.7's release notes with the corrected logic via
  a one-off `backfill-release-notes.yml` workflow (same established pattern),
  then removed the workflow file after running. All releases now show accurate,
  complete NEW/FIX-badge notes. The next natural release (v4.0.8, from the fix
  commit's own merge) came out correct with zero manual intervention, confirming
  the fix holds going forward.

**2026-07-10 (cont'd, moved canonical repo to CouchTomatoes/CouchTomatoServer)**
- User created a fresh empty repo at `CouchTomatoes/CouchTomatoServer` (having
  renamed the previous occupant of that name — the paused .NET scaffold — to
  `CouchTomatoes/CouchTomatoServer-DotNet-WIP` first) and asked to move this
  project there as the new canonical home, plus mirror the `CouchPotatoAPI` fork
  into `CouchTomatoes` too. Clarified up front via three quick questions: target
  repo (new one, confirmed empty and ready), move-vs-mirror (**move** —
  `CouchTomatoServer` becomes canonical, this repo becomes historical), and
  whether to also mirror `CouchPotatoAPI` (yes).
- This session's git/GitHub access turned out to be **permanently locked to
  `codeahmed`-owned repos for its whole lifetime** — confirmed by directly testing
  both `add_repo` (refused: "cross-tier adds are not supported") and an
  authenticated `git push` to `CouchTomatoServer` (refused by the proxy: "not in
  this session's authorized repository set"), the second time re-tested *after*
  the user added `CodeAhmed` as a `CouchTomatoServer` collaborator specifically to
  rule out a permissions explanation — still refused identically, confirming it's
  a session-tier architectural lock, not a GitHub permission gap. So the actual
  `git push` had to be done by the user themselves, using the exact commands
  logged in `SUGGESTIONS.md`.
- Before handing that off, built and **verified** (rather than just handed over
  untested) `.github/workflows/mirror-releases-to-target.yml`, since a plain
  `git push --tags` only moves git tags — GitHub Release objects (the styled
  NEW/FIX notes) are separate per-repo metadata that never transfers with git.
  Verification method, since this session can't write-test against the real
  target: added a throwaway `TEST-dry-run-mirror.yml` that ran the exact
  read/parse/iterate logic (pagination, `jq` field extraction, the EOF-safe
  while-read loop from the release-notes fix above) against the real ~25-release
  dataset in *this* repo, without calling `gh release create/edit`. Result:
  **PASS — processed all 25 releases** (10 `v4.x` + 15 mirrored upstream
  `build/*`) with correct tag/title/body, none dropped. Deleted the test
  workflow afterward; the real mirror workflow's only untested part is the final
  `gh release create/edit` call, which reuses the exact command pattern already
  proven twice elsewhere in this project.
- **User confirmed the move is done**: pushed the full project (`master`/`main` +
  `claude/couch-tomato-parity-e1f5bl` + tags) to `CouchTomatoServer` and ran
  `mirror-releases-to-target.yml` there themselves. Verified from this session
  (read-only, since public-repo `git ls-remote`/fetch works regardless of the
  session's write-access lock): `CouchTomatoServer`'s default branch is `main`
  (not `master`), and it has the dev branch + all tags present at the expected
  commit. Could not independently verify the Releases page itself (same
  write-access wall blocks reads through the GitHub API/App route too, only
  plain anonymous git fetch/ls-remote works) — take the user's confirmation on
  that part at face value unless they report otherwise.
- Re-tested write access once more after the user added `CodeAhmed` as a
  collaborator there (see above) — still refused, so **this repo's session
  cannot do any further work in `CouchTomatoServer` directly, ever, for the rest
  of its lifetime.** Explained this clearly to the user: the only way to get a
  session with real working access there is to start a genuinely new session
  with `CouchTomatoServer` as its *initial* repo source (new Claude Code Web/
  Cowork session picking that repo, or `claude` run from a local clone of it) —
  cannot be done by asking this session to somehow "switch."
- Updated this file's "Repo landscape" section to formally flip canonical status
  to `CouchTomatoServer` and demote this repo to historical/legacy, plus a note
  in "Working conventions" about the default branch name difference (`main` vs
  `master`). **This specific edit (the one you're reading) exists only in
  `CodeAhmed/CouchTomato` as of when it was written** — it was NOT pushed to
  `CouchTomatoServer` (same access wall), so if you're reading this from a fresh
  session in `CouchTomatoServer`, its copy of `CLAUDE.md` may be one commit
  behind this one. Worth a quick `git log`/diff check; if it's missing, the
  fix is trivial since both repos share full git history — from a
  `CouchTomatoServer` clone: `git fetch https://github.com/CodeAhmed/CouchTomato.git
  claude/couch-tomato-parity-e1f5bl && git cherry-pick <this-commit-sha>` (or just
  re-apply the same Repo-landscape/Working-conventions edits by hand — they're
  short).

**2026-07-11 (fresh session working directly in `CouchTomatoServer`, full wizard
click-through + live provider search — 4 real bugs found and fixed)**
- This session's GitHub/git access was scoped to `CouchTomatoes/CouchTomatoServer`
  directly (confirmed via `git remote -v` and a real `git push`) — the first
  session since the move with genuine write access here, exactly the "start a
  fresh session with `CouchTomatoServer` as the initial repo source" path the
  previous session's entries said would be needed.
- Small side task first: fixed stale `CodeAhmed/CouchTomato` links in `README.md`
  (badges + clone URL, left over from before the move), added a GPLv3 license
  badge, and added a generated social-preview image + a plain-tomato-icon logo
  under `docs/branding/` for the repo's GitHub "About" page (that setting isn't
  exposed via the API, so it's a manual upload — documented in
  `docs/branding/README.md`). Merged as PR #1.
- Rebuilt the runtime environment from scratch (fresh container had none of the
  previously-installed pip packages or the test `transmission-daemon` from prior
  sessions) and picked up the "click through the wizard + real provider search"
  item from `TODO.md` §5, using Playwright against a real headless Chromium
  exactly as established — this is what actually found the bugs below, not
  reading the code.
- **Bug 1 & 2**: two more instances of the `document.body` null-during-teardown
  crash class (the same one `login.js` was already guarded against, per
  `TODO.md`'s "there may be others further down the domready queue" note).
  `library/uniform.js`'s `Uniform` class (initialized on every single page load,
  not just login) crashed first, which meant `index.html`'s own inline
  `domready` block (setting the `data-api` attribute) never got a chance to run
  either — fixing the first one revealed the second. Both fixed with the same
  `if (!b) return` guard pattern.
- **Bug 3 — the big one**: `couchpotato/core/plugins/base.py`'s `urlopen()`
  (the core HTTP helper every provider/notification/API client in the app goes
  through) imported `Timeout` from `requests.packages.urllib3` — but that's the
  request-timeout *config* class, not an exception. Its `except (IOError,
  MaxRetryError, Timeout):` clause therefore raised `TypeError: catching classes
  that do not inherit from BaseException is not allowed` on *every single
  genuine network failure* (timeouts, proxy errors, connection errors) instead of
  logging it cleanly and running the existing failed-host backoff logic. This has
  silently broken graceful network-error handling for the entire app's whole
  lifetime post-port. Found by watching KickAssTorrents'/ThePirateBay's real
  proxy-discovery loop (which tries ~20 mirror domains, expecting most to fail)
  flood the log with this `TypeError` instead of clean debug lines. Fixed by
  importing `urllib3.exceptions.TimeoutError` instead (the real exception base
  class) as `Timeout`. Verified: zero occurrences of the `TypeError` across a
  full clean wizard + add + search run afterward, and confirmed a working proxy
  domain now gets found and used for KickAssTorrents (`Using proxy for
  KickAssTorrents: https://kat.how`).
- **Bug 4**: five torrent providers did plain string-containment checks directly
  against `urlopen()`/`getHTMLData()`'s `bytes` return value —
  `kickasstorrents.py`'s and `thepiratebay.py`'s `correctProxy()` (used by the
  same proxy-discovery loop above), `thepiratebay.py`'s `doTest()`, and
  `iptorrents.py`'s/`bitsoup.py`'s "nothing found!" empty-result check. Same
  root cause as every other bytes/str bug already fixed in this port
  (`urlopen()` returns real `bytes` in Py3, call site never decoded back) —
  fixed all five with `toUnicode()` at the call site.
- Result: the wizard now completes end to end (Welcome → General → Downloaders
  → Providers → Renamer → Automation → Finish → save) with **zero** console
  errors, landing on the real main app. Added "The Matrix" through the actual
  search-and-add UI (not an API call), enabled Binsearch/ThePirateBay/
  KickAssTorrents/YTS through the wizard (the providers that don't need an
  account), and triggered a real search against them — confirmed clean, no
  crashes, proxy discovery working. Screenshots in `docs/screenshots/` (see its
  README for the 2026-07-11 entry).
- **One remaining, not-yet-root-caused finding**: a `struct.error: argument for
  's' must be a bytes object` / `codernitydb3.index.ElemNotFound` seen once when
  clicking "Add" on a movie that was already in the library while a background
  provider search was still running (`movie/_base/main.py`'s `add()` →
  `db.update(m)`). Did not reproduce on a clean retry (single `movie.add` API
  call, no concurrent search) — looks like a race between the search threads and
  the update, not a deterministic key-encoding bug like the ones just fixed
  above. Logged in `TODO.md` §5 for a future targeted concurrency repro rather
  than guessing at a fix.

**2026-07-11 (cont'd, checked the Home page's "top movies" charts feature at the
user's request — found and fixed 2 more real bugs)**
- User specifically asked to check whether the main page's "top movies from
  sources" feature actually works. It didn't — `charts.view` returned
  `{"charts": [], "count": 0}` every time, so the Home page's chart section was
  just silently absent, no visible error anywhere in the UI.
- **Bug 5**: `couchpotato/core/media/movie/providers/automation/base.py`'s
  `search()` — called by every chart-provider plugin (`bluray.py`, `imdb.py`,
  etc.) — did `name.decode('utf-8').encode('ascii', 'ignore')`, but `name` is
  already a `str` in Python 3 (this is the *opposite* direction of the usual
  bytes/str bug in this port: Py2 code decoding an already-decoded value,
  instead of failing to decode a still-bytes one). Crashed
  `automation.get_chart_list` on every single call, for every provider, with
  `AttributeError: 'str' object has no attribute 'decode'`. Fixed by encoding to
  ASCII and decoding back to `str` instead of the unneeded `.decode()` first.
- **Bug 6 — the bigger one**: even after fixing #5, `charts.view` returned real
  data (confirmed via direct API call — Blu-ray.com's "New Releases" chart, full
  TMDB metadata, real posters) but posters rendered as blank gray boxes in the
  browser, for *both* the new charts feature and the already-added "Matrix, The"
  movie in the Wanted list. Traced the poster `<img>` URL
  (`/api/<key>/file.cache/<hash>.jpg`) and found it returned the API's generic
  `"API call doesn't seem to exist"` JSON error instead of the image, even
  though the file existed on disk in the cache directory. Root cause: the exact
  same registration-order class of bug as the already-fixed `/static/*` issue
  (see the 2026-07-10 entry), but in a different pair of routes.
  `couchpotato/runner.py` registered the generic `ApiHandler` catch-all
  (`r'/api/<key>/(.*)(/?)'`) *before* `loader.run()` loads plugins — but
  `couchpotato/core/plugins/file.py`'s `showCacheFile()` (registered via
  `addApiView('file.cache/(.*)', ..., static = True)`, which calls
  `application.add_handlers()` directly instead of going through the normal
  dynamic `api` dict) only runs *during* plugin loading, i.e. strictly after
  that catch-all was already in place. Since Tornado's `RuleRouter` tries
  same-host-pattern rule groups in registration order and stops at the first
  one whose own internal routes match, and `/api/<key>/(.*)`  matches literally
  any path under the API base, the earlier-registered `ApiHandler` catch-all
  permanently shadowed `file.cache`'s later-registered `StaticFileHandler` —
  meaning **every locally-cached poster/backdrop image in the entire app was
  silently broken** the whole time, not just for charts. This is a distinct
  instance of the same principle already documented in the file (the comment
  right above the static-paths registration), just not applied to
  plugin-registered static routes. Fixed by moving `loader.run()` (plugin
  loading) to happen *before* the API/web catch-all handlers are registered,
  so any plugin's static routes land earlier in Tornado's routing table.
  Verified: `curl` against a `file.cache` URL now returns `image/jpeg` instead
  of the JSON error, and posters render correctly in both the Wanted list and
  the Home page charts (screenshots in `docs/screenshots/`).
- Both fixes verified via a full fresh-DB run: wizard → add movie → Home page
  showing the real Blu-ray.com chart with working poster images, and the Wanted
  list showing The Matrix's actual poster instead of a blank box.

**2026-07-11 (cont'd, enumerated every Home-page API call, found 2 more real bugs)**
- User asked to check for any other APIs the Home page loads, and to re-verify
  the added movie's poster + the server log. Captured every network request via
  Playwright: `media.list`, `dashboard.soon`, `suggestion.view`,
  `notification.listener`, `charts.view`, one `file.cache/*` per poster, and
  `updater.info` — all 200, and the log was clean apart from the
  already-documented external-service noise (dead `couchpota.to`, IMDB blocking
  automated `/boxoffice/` scraping, an invalid/placeholder OMDB API key).
- While confirming that, the wizard run surfaced two new frontend JS errors
  ("Cannot read properties of undefined (reading 'getElements')" and "...
  (reading 'set')") paired with a server-side "Failed getting directory" error.
  Root cause, found by reading the traceback: `couchpotato/core/plugins/
  browser.py`'s `is_hidden()` wrapped a path in `ss()` (bytes) then called
  `.startswith('.')` with a `str` literal — yet another instance of the
  recurring `ss()`-misuse pattern this file's progress log has flagged
  repeatedly ("expect this pattern elsewhere, grep for `ss(`"). This crashed
  `directory.list` on every single call, which is the API behind every
  Directory-type settings field's folder-browser popup. Fixed by dropping the
  unnecessary `ss()` (matches the established fix pattern: paths should stay
  `str` throughout in Py3).
- Fixing that revealed the frontend errors were only *partly* a downstream
  symptom — `static/scripts/page/settings.js`'s `Option.Directory.
  filterDirectory()` and `.fillBrowser()` both unconditionally reference
  `self.dir_list`/`self.back_button`, which are only created once the
  folder-browser *popup* has actually been opened via `showBrowser()`. But
  `filterDirectory()` runs on every `change`/`keyup`/`paste` of the plain text
  input regardless of whether the popup was ever opened — i.e., any real user
  who types or pastes a directory path directly (a completely normal workflow)
  hits this. This is the same underlying class of bug as the `show_hidden` fix
  earlier in this session (`getDirs()`'s `self.show_hidden.checked`) — just two
  more unguarded references in sibling methods of the same widget that hadn't
  been audited yet. Guarded both the same way (early-return / conditional
  branch when the popup-only elements don't exist). Hand-patched
  `combined.base.min.js` to match, as with every other frontend fix this
  session.
- Verified via a full fresh-DB wizard + add-movie run: zero "Failed getting
  directory" errors, zero frontend JS errors reported to the API log, and
  `directory.list` called directly now returns a real directory listing
  instead of a 500.

**2026-07-11 (cont'd, Windows/macOS installer builds + a critical release-automation
bug found along the way)**
- User asked about packaging a Windows/macOS app and attaching it to releases.
  Checked first rather than assuming: no `.mako` file, no PyInstaller/py2app/
  Briefcase/Electron config, no Windows/macOS build scripts existed anywhere in
  the repo — this was net-new work, not something to "update." Asked the user
  to pick an approach (PyInstaller onefile vs. full installer vs. something
  else); they chose the full-installer route (NSIS on Windows, DMG on macOS).
- **Before touching packaging, found a much bigger, unrelated bug while
  checking how release artifacts would actually get attached**: `release.yml`
  has **never fired even once** in this repo. Its push trigger listened for
  `branches: [master]`, but this repo's default branch is `main` (confirmed via
  the Actions API — `list_workflow_runs` for `release.yml` returns
  `total_count: 0`). Every v4.x release visible on this repo was mirrored over
  from the old `CodeAhmed/CouchTomato` repo during the 2026-07-10 move (see that
  day's entries) — none were ever actually cut by this workflow running here,
  including after this session's own PR #1 merge, which silently should have
  triggered one and didn't. Fixed with a one-line change (`master` → `main`) —
  the highest-value fix in this whole entry, since the packaging work below is
  pointless without a release trigger that actually fires.
- **Packaging approach**: CouchTomato's plugin system
  (`couchpotato/core/loader.py`) imports every provider/notification/downloader
  module dynamically by walking the filesystem and calling `import_module()`
  with computed names — PyInstaller's static import-graph analysis can't trace
  any of that, so a naive frozen build would silently load zero plugins (a
  failure mode that's easy to ship without noticing, since the server still
  boots and the web UI still renders with an empty plugin list). Rather than
  fight PyInstaller's analysis, `packaging/couchtomato.spec` bundles
  `couchpotato/` and `libs/` (the vendored packages with no PyPI equivalent) as
  **loose data trees** alongside the frozen bootstrap, exactly mirroring how
  they sit next to `CouchPotato.py` in a normal source checkout — the app's own
  existing `sys.path.insert(0, .../libs)` then makes the same dynamic imports
  work at runtime inside the frozen build, unchanged.
- **Validated the hard part locally before trusting it to CI**: this sandbox
  has no Windows/macOS toolchain, but PyInstaller's Linux target exercises the
  exact same risky mechanism (loose-data-tree dynamic imports), so built and
  *ran* the frozen app here first — found and fixed 3 real gaps this way,
  each confirmed by reading the actual `ModuleNotFoundError` the frozen build
  produced, not by guessing:
  - Every pip-installed dependency (`GitPython`, `beautifulsoup4`, `bencode.py`,
    etc.) is only ever imported from *inside* the loose `couchpotato`/`libs`
    trees, never from `CouchPotato.py`'s own static import chain — so
    PyInstaller's analysis never traced any of them. Fixed with explicit
    `collect_submodules()` hidden imports for each of `requirements.txt`'s
    packages, plus a couple of stdlib modules (`xml.etree`, `distutils`,
    `email.mime`, `telnetlib`) that turned out to only be reachable
    dynamically too.
  - `couchpotato/core/_base/updater/main.py` does `import version` (no dot) —
    a bare top-level import relying on Python's implicit script-directory
    `sys.path` entry that only exists when running `python3 CouchPotato.py`
    directly from the repo root (where a `version.py` placeholder file lives).
    That implicit entry doesn't exist in a frozen build. Fixed by explicitly
    bundling `version.py` as a data file at the bundle root, next to
    `couchpotato`/`libs`.
  - Excluded `OpenSSL`/`cryptography` from the build entirely — PyInstaller's
    isolated-subprocess hook collection for `cryptography` crashed with a Rust
    `PanicException` in this sandbox even though the package imports fine
    directly, and it's already an optional dependency
    (`couchpotato/core/_base/_core.py` logs a warning and continues without it
    when absent) — not worth fighting, and excluding it sidesteps the crash.
  - **Result**: a clean local Linux PyInstaller build loads all 104 plugins (0
    skipped, matching a from-source run) and renders the real wizard UI in a
    real headless browser — confirmed the core packaging mechanism works
    before ever touching a Windows or macOS runner.
- **Windows**: `packaging/windows/installer.nsi` — a standard NSIS script that
  installs the PyInstaller onedir output to Program Files, creates Start Menu
  shortcuts and a registry-registered uninstaller. Syntax-verified locally by
  installing NSIS in this sandbox (`apt-get install nsis`) and actually
  compiling the script end to end with fake paths — Linux's NSIS compiler
  produces real Windows `.exe` installers, it just can't run them, so this
  validates the script itself without validating the real Windows runtime
  behavior.
- **macOS**: PyInstaller's `BUNDLE()` step (a no-op on Linux/Windows, real on
  macOS) produces `CouchTomato.app` directly from the same onedir output; the
  workflow then wraps it in a DMG via `hdiutil` (built into every macOS
  runner, no extra tooling needed).
- Wired both into `release.yml` as `build-windows`/`build-macos` jobs gated on
  `needs: release`, uploading the installer/DMG to the just-created release via
  `gh release upload`.
- **What's genuinely unverified**: actually running the NSIS-built installer on
  real Windows, and building/mounting the `.app`/DMG on real macOS — this
  sandbox has no toolchain for either, so this can only be proven by the real
  `windows-latest`/`macos-latest` GitHub Actions runners on the next push to
  `main`. First runs of a new packaging pipeline commonly need a round or two
  of CI-log-driven fixes even after a clean local dry run — plan to watch the
  next release's Actions run closely rather than assume it's done.

**2026-07-11 (cont'd, merged PR #2, watched the real first run, fixed the one
real gap — pipeline is now fully green)**
- User said to merge PR #2. Marked it ready for review (it was still a draft)
  and merged it, which pushed to `main` and fired `release.yml` for real for
  the very first time (confirmed via the Actions API: `run_number: 1`).
- **Result of that first real run**: `release` job succeeded (cut `v4.0.12`);
  `build-windows` **succeeded completely** on the first try — PyInstaller
  build, NSIS install, installer build, and upload to the release all green,
  no fixes needed. `build-macos` failed at PyInstaller's `BUNDLE()` step:
  `ValueError: ... only ('icns',) images may be used as icons. If Pillow is
  installed, automatic conversion will be attempted.` Pillow wasn't installed
  in that job. Everything before that (the PyInstaller onedir build itself)
  had completed cleanly on macOS too, matching the already-validated Linux
  build — only the `.app` icon conversion was missing a dependency.
- Verified the fix locally before pushing: installed Pillow in this sandbox
  and confirmed `PyInstaller.building.icon.normalize_icon_type()` actually
  produces a real `.icns` file from the existing `favicon.ico` once Pillow is
  present. Opened PR #3 with the one-line fix (`pip install pyinstaller
  pillow`), merged it (small, low-risk, CI-only, already verified — matches
  the spirit of "get this pipeline working" rather than needing a fresh
  round of confirmation for every one-line CI fix).
- **That merge fired `release.yml` again (`run_number: 2`) — fully green this
  time**: `release`, `build-windows`, and `build-macos` all succeeded.
  Confirmed with concrete proof via `get_release_by_tag`, not just green
  checkmarks: release `v4.0.13`'s assets list shows both
  `CouchTomato-4.0.13.dmg` (22.8 MB) and `CouchTomato-Setup-4.0.13.exe`
  (20 MB) actually `"state":"uploaded"`.
- **The Windows/macOS packaging effort from this session is done and proven
  working end to end on real CI, not just locally**: every future merge to
  `main` now automatically cuts a release with both installers attached.
  First-run friction was exactly one real issue (the Pillow/icns gap), fixed
  in one round — in line with the expectation logged above that a new
  packaging pipeline commonly needs a round or two of CI-log-driven fixes
  even after a clean local dry run.

**2026-07-11/14 (full platform/arch release matrix — Windows/Linux/macOS
x64+arm64, macOS universal2, wiki setup — 6 real CI bugs found and fixed)**
- User asked to expand the release matrix to match another project's page
  (Ryujinx/ryubing-ci style): Windows x64 (installer + portable zip) and
  arm64 (zip, best-effort installer), Linux x64/arm64 (tar.gz + AppImage),
  macOS **universal2** (dmg + app.tar.gz, x64+arm64 merged into one binary).
  Scoped via `AskUserQuestion` first; user picked all four options (not just
  the easy subset), so full scope was explicitly authorized. Implemented in
  PR #5: rewrote `release.yml` to 8 jobs, added `packaging/linux/
  build-appimage.sh` (AppDir + `appimagetool`, validated locally minus the
  actual `appimagetool` download which this sandbox's proxy blocks) and
  `packaging/macos/merge-universal.sh` (lipo-merge two single-arch builds
  file-by-file). ARM64 jobs use `continue-on-error: true` since
  `windows-11-arm`/`ubuntu-24.04-arm` were unverified preview labels.
- **`build-macos-universal` took 4 real-CI rounds to get green the first
  time** (all found via actually watching the run, not assumed from a clean
  local dry run — this sandbox has zero macOS/ARM toolchain so none of this
  was testable locally beyond syntax checks):
  1. **PR #6**: `build-macos-x64`'s `macos-13` runner label was fully
     retired by GitHub on 2025-12-04 (confirmed via web search) — the job
     queued forever, never got a runner. Fixed by switching to
     `macos-15-intel`, GitHub's current Intel-runner replacement.
  2. **PR #7**: with the runner fixed, the merge job then failed
     `cp: dist/CouchTomato.app: No such file or directory` — `build-macos-
     universal` only downloads artifacts, it never runs a PyInstaller build,
     so `dist/` never gets created. Fixed with `mkdir -p
     "$(dirname "$out_dir")"` before the copy.
  3. **PR #8**: next, `lipo` fatally refused to merge
     `libs/unrar2/unrar` (a legacy vendored i386-only tool bundled as a data
     file, not built per-arch by PyInstaller) because both arch trees
     carried the *same* architecture — lipo won't fat-merge two slices of
     one arch. Fixed by `cmp -s`-skipping byte-identical files before
     attempting the lipo merge. **v4.0.18 shipped fully green — all 10
     assets, verified via `get_release_by_tag`.**
  4. User later noticed (comparing asset *counts* across releases, 11 vs 9)
     that every release after v4.0.18 (v4.0.19/20/21) had silently lost the
     macOS assets again, with the *exact same* "same architectures (i386)"
     error. **Root cause of the regression**: `cmp -s`'s byte-equality check
     was never reliable — PyInstaller/macOS apparently apply per-build
     ad-hoc signing or embed build-specific metadata into bundled Mach-O
     binaries, so the *same* vendored `unrar` tool comes out byte-different
     between the independently-run x64/arm64 jobs even though it's still the
     same single architecture. **PR #12** fixed this properly: compare
     actual architectures via `lipo -archs` (the same check `lipo` itself
     makes) instead of raw bytes — robust to signing/metadata churn, still
     correctly lipo-merges genuinely different-arch files. Verified via a
     real CI run: `build-macos-universal` succeeded, "Architectures in the
     fat file: ... are: x86_64 arm64" confirmed in the job log.
- **Real-world Gatekeeper bug, caught by the user actually running the
  downloaded app on a Mac** (a class of bug this whole project's testing
  philosophy says to expect — CI green ≠ works for a real user): extracting
  `.app.tar.gz` and opening it showed **"CouchTomato is damaged and can't be
  opened. You should move it to the Trash"** — a harsher, no-bypass Gatekeeper
  dialog than the already-documented "unidentified developer" one, shown
  specifically when a downloaded app has *zero* code signature at all (not
  even ad-hoc). Gave the user an immediate unblock (`xattr -cr
  CouchTomato.app` strips the quarantine flag Safari applies) while fixing
  the pipeline:
  - **PR #13** added a `codesign --force --deep --sign - dist/CouchTomato.app`
    step after the lipo merge (lipo doesn't preserve per-slice signatures
    across a merge, so signing must happen post-merge). This **immediately
    broke the job**: `--deep` recursively signs every subcomponent, and
    PyInstaller's bundle includes non-standard ones (`Contents/Frameworks/
    python3.11`) that don't parse as valid nested bundles —
    `bundle format unrecognized, invalid, or unsuitable`.
  - **PR #14** fixed it by dropping `--deep` — signing just the top-level
    `.app` is what Gatekeeper's basic launch check actually looks at, and is
    the standard workaround for ad-hoc-signing PyInstaller apps for this
    exact reason. **Not yet verified by a real CI run as of this write-up —
    check the next release run's `build-macos-universal` job first thing
    next session** (the codesign step specifically) before assuming it's
    fixed. This is still only an ad-hoc signature (no paid Apple Developer
    ID cert available), so the normal "unidentified developer, right-click
    to open" Gatekeeper prompt is expected and correct — that's the
    documented, acceptable UX, not a bug to chase further.
- **README + wiki, SickGear-style** (user wanted the repo/docs polished to
  match github.com/sickgear/sickgear as a reference): scoped via
  `AskUserQuestion` (structure+polish only, reuse existing content, no new
  marketing copy) then implemented:
  - PR #9: added a release-history table (per-version highlights + which
    platform downloads actually worked at that version — useful precisely
    because the macOS asset availability kept flipping during the rounds
    above).
  - PR #10: restructured `README.md` into SickGear-style sections (quick
    links, Providers & Downloaders list pulled from the real plugin
    directories — not invented, screenshots gallery, Community section).
    Also wrote 4 wiki pages (Installation, Migration, FAQ, Architecture
    Overview) plus a Home landing page, staged under `docs/wiki/` since the
    GitHub Wiki feature wasn't enabled on the repo yet, and this session's
    git access can't push to the `.wiki.git` companion repo even once it is
    (tested: real auth error, `add_repo`/direct GitHub tools both refused
    it — `.wiki` repos aren't addressable as normal repos through any tool
    available this session). Documented the exact enable+push steps in
    `docs/wiki/README.md` for whoever has real access.
  - User enabled the Wiki feature and pushed the pages themselves (note:
    a plain `git clone .wiki.git` 404s until the *first* page is saved via
    the web UI at least once — GitHub doesn't provision the wiki's git repo
    until then, which briefly looked like a contradiction of "wiki already
    enabled" but isn't). **PR #11**: once confirmed live (`https://github.com/
    CouchTomatoes/CouchTomatoServer/wiki` showing all 5 pages), updated
    `README.md`'s links to point at the real wiki and deleted the now-
    redundant `docs/wiki/` staging folder.
- General pattern reconfirmed this session: **the user catching real-world
  discrepancies (asset counts across releases, an actual Gatekeeper error on
  real hardware) found bugs that green CI checkmarks alone did not** — same
  lesson as this file's established testing philosophy, just now extended to
  "the user actually running the shipped artifact," not just "browser-testing
  the web UI."

## Next steps (in order)

**Boot milestone reached 2026-07-10: server starts, web UI renders and is verified
interactive in a real headless browser (setup wizard works end to end). Provider
plugin import backlog cleared same day: 0 remaining loader failures, down from ~50.**
See `TODO.md` for the detailed, checkbox-tracked list — this section is now the
higher-level plan for what comes after.

1. ~~Root-cause the `profile.forceDefaults` `ElemNotFound` finding~~ — **done
   2026-07-10**: real cross-thread data race in `codernitydb3`'s `Database`, fixed
   with a global lock. See progress log.
2. Continue clicking through the actual UI in the browser (wizard → save → main app →
   settings → try adding a movie, try triggering a real search against one of the
   now-loading torrent/nzb providers) to find the next layer of real runtime bugs —
   this approach found several major ones already (DB race, wizard `default_action`
   crash, and 6 bytes/str bugs blocking the whole download-to-library pipeline);
   curl/import-success alone won't catch them. The wizard's Welcome/General steps
   load cleanly, and add-movie → Transmission → renamer is now verified working
   end to end via the API — next: get through the wizard's remaining steps
   (Downloaders/Providers/Renamer/Automation/Finish, save) and exercise a **real**
   torrent/NZB provider search in the browser UI itself (everything so far was
   driven via direct API calls + a self-seeded test torrent, not actual clicks
   through the search/snatch UI against a live provider).
3. Fix the JS build pipeline gap noted in the progress log: `combined.*.min.js` are
   pre-built bundles with no verified-working `grunt` build in this sandbox, so any
   frontend JS fix currently needs hand-patching both the source file *and* the
   matching bundle. Worth getting `npm install` + `grunt` actually working (or
   documenting why not) so this stops being manual.
4. Replace remaining easy vendored libs (six, dateutil, certifi, html5lib, oauthlib,
   rsa, pyasn1 — tornado/chardet/requests/GitPython/CodernityDB3/bs4/bencode/httplib2
   already done) with real pip packages + grow `requirements.txt`.
5. Hand-port the remaining CouchPotato-specific vendored libs with no drop-in
   replacement (axl, caper, enzyme, pynma, gntp, etc.) with 2to3 + manual fixes.
   apscheduler is vendored+patched for now; a real swap to pip APScheduler needs an
   API rewrite (`add_interval_job` → `add_job(trigger='interval', ...)`), not just a
   dependency swap.
6. Rebrand: package name, `~/.couchpotato` → `~/.couchtomato` config dir, UI strings,
   Docker/systemd units, docs. (README.md partially rebranded 2026-07-10.)
7. CI + packaging. **2026-07-11: Windows/macOS installer builds done** — see progress
   log. Still open: Linux packaging (.deb/AppImage) and Docker/systemd (still #6 above).
8. Decide on the tag-mirroring question in `SUGGESTIONS.md` (blocked on repo owner
   input, not something to keep retrying) — mostly moot now, tags are already mirrored.

## Working conventions

- **Do this in whichever repo is canonical for your session** — `CouchTomatoes/
  CouchTomatoServer` if that's where you're working (see Repo landscape above),
  `CodeAhmed/CouchTomato` only if you're deliberately doing something in the
  legacy/historical mirror.
- Development branch: `claude/couch-tomato-parity-e1f5bl`. PR into `master` (or that
  repo's default branch — note `CouchTomatoServer`'s is `main`, not `master`) when
  ready for review (don't push directly to the default branch without the user's
  explicit say-so — that was a one-time exception for the initial history import).
- Commit after each mechanical/logical step, not in one giant diff — makes the porting
  process auditable and bisectable.
- No `.env`/secrets expected in this repo; none encountered so far.
- **Whenever you browser-test something (Playwright/headless Chromium), save a
  screenshot to `docs/screenshots/` and commit it in the same PR as the fix it
  verifies.** Name it `YYYY-MM-DD-what-was-tested.png`, one shot per distinct thing
  verified (not every frame). See `docs/screenshots/README.md` for the full
  convention. This makes "I tested it and it works" checkable by the user without
  them having to re-run anything.
