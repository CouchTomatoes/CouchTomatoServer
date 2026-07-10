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

## Next steps (in order)

**Boot milestone reached 2026-07-10: server starts, web UI renders.** See `TODO.md`
for the detailed, checkbox-tracked list — this section is now the higher-level plan
for what comes after.

1. Manually verify the web UI in an actual browser (not just curl) — add a movie,
   trigger a search, open settings pages. Fix the empty-DB `struct.error` in
   `profile.forceDefaults` noted in the progress log / `TODO.md` §5 if it blocks
   real usage.
2. Work through the long tail of provider/notification/downloader plugin import
   failures listed in `TODO.md` §5 (each is independently non-fatal but disables that
   feature) — likely the largest remaining chunk of work.
3. Replace remaining easy vendored libs (six, dateutil, certifi, bs4, html5lib,
   oauthlib, httplib2, rsa, pyasn1 — tornado/chardet/requests/GitPython/CodernityDB3
   already done) with real pip packages + grow `requirements.txt`.
4. Hand-port the remaining CouchPotato-specific vendored libs with no drop-in
   replacement (axl, caper, enzyme, pynma, gntp, etc.) with 2to3 + manual fixes.
   apscheduler is vendored+patched for now; a real swap to pip APScheduler needs an
   API rewrite (`add_interval_job` → `add_job(trigger='interval', ...)`), not just a
   dependency swap.
5. Rebrand: package name, `~/.couchpotato` → `~/.couchtomato` config dir, UI strings,
   Docker/systemd units, docs.
6. CI + packaging.

## Working conventions

- Development branch: `claude/couch-tomato-parity-e1f5bl`. PR into `master` when ready
  for review (don't push directly to `master` again without the user's explicit say-so —
  that was a one-time exception for the initial history import).
- Commit after each mechanical/logical step, not in one giant diff — makes the porting
  process auditable and bisectable.
- No `.env`/secrets expected in this repo; none encountered so far.
