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

## Next steps (in order)

1. Fix `header_for_indexes(...)` bytes/str TypeError in `libs/CodernityDB/database.py`
   (`_add_single_index`, line ~177) — next boot blocker, see progress log for details.
2. Keep iterating: run `python3 CouchPotato.py --data_dir <scratch dir> --console_log --debug`,
   fix whatever error comes next, one at a time, committing after each fix, until the
   server actually starts and the web UI is reachable.
3. Once it boots: replace remaining easy vendored libs (requests, six, dateutil, certifi,
   bs4, html5lib, oauthlib, httplib2, apscheduler, rsa, pyasn1, GitPython already done)
   with real pip packages + grow `requirements.txt`.
4. Hand-port the CouchPotato-specific vendored libs (axl, caper, CodernityDB, enzyme,
   pynma, gntp, etc.) with 2to3 + manual fixes since no drop-in replacement exists.
5. Work through provider plugins (NZB/torrent/metadata/download-client) as the real bug
   backlog — likely the largest remaining chunk of work.
6. Rebrand: package name, `~/.couchpotato` → `~/.couchtomato` config dir, UI strings,
   Docker/systemd units, docs.
7. CI + packaging.

## Working conventions

- Development branch: `claude/couch-tomato-parity-e1f5bl`. PR into `master` when ready
  for review (don't push directly to `master` again without the user's explicit say-so —
  that was a one-time exception for the initial history import).
- Commit after each mechanical/logical step, not in one giant diff — makes the porting
  process auditable and bisectable.
- No `.env`/secrets expected in this repo; none encountered so far.
