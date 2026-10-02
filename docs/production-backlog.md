# Production backlog — found by running CouchTomato for real (2026-09-30 → 10-01)

CouchTomato replaced a live CouchPotato install on a Raspberry Pi 4 (Python 3.11 venv, Transmission
downloader, data migrated by export/import). Everything below was observed on that install or found by
reading the code while chasing what was observed. Paths are relative to this repo at `main` @ `1b32b31f`.
Counts come from roughly one hour of the live log plus three `--debug` test logs.

Nothing here is fixed yet. The checklist is in [`TODO.md`](../TODO.md) §6; tick items off there as their PRs land.

## 1. ⭐ FIRST — live notifications only update after a page reload

- Seen on a real snatch (YTS 1080p → Transmission): the bottom-left bell count and popup did not change until the
  page was **reloaded**; after the reload the badge showed 1.
- **Cause (found by reading + probing; fix not yet written):**
  - The live channel itself works. With the page open, `nonblock/notification.listener` is held open (pending);
    firing a harmless frontend event (`media.refresh?id=<nonexistent>` → `media.busy`) answered it at once
    (200 after 34.6 s of waiting).
  - The bell only listens for page events named `'notification'` —
    `couchpotato/core/notifications/core/static/notification.js:14` `App.on('notification', self.notify…)`;
    the page fires `App.trigger(result._t || result.type)` (`processData`).
  - On **reload**, `notification.listener?init=true` returns stored docs with `_t = 'notification'`, so the bell
    counts them.
  - **Live**, `CoreNotifier.notify()` (`couchpotato/core/notifications/core/main.py:149-173`) pushes
    `self.frontend(type = listener, data = n)`. `type` is the event name (`'movie.snatched'`, `'renamer.after'`,
    `'media.available'`…) and `message` is None. So the page fires `'movie.snatched'`, which **no script listens
    to** (grep: zero JS listeners); the bell never hears it, and no popup shows (`showMessage` needs `result.message`).
  - **Inherited from CouchPotato**, not introduced by the port: against the pre-port upstream commit, this file only
    changed the IOLoop handle and a `list(map())`; the JS is unchanged.
- **Fix direction:** in `notify()`, push the stored doc as a `'notification'` event with its message — e.g.
  `self.frontend(type = 'notification', data = n, message = n['message'])` (keep the listener-typed push too if other
  UI code wants it), or have `processData` route results whose `data._t == 'notification'` to the bell.
  The bell's `notify()` expects the stored doc shape (`_id`, `message`, `read`), so pass `n`.
- **Done =** snatch (or `notify.<core>.test`) with the page open → badge +1 and popup **without a reload**.
- Ruled out on the way: the Tornado loop handle (`main_ioloop` is the serving loop — the blocking API uses it fine);
  bytes in the JSON (`couchpotato/__init__.py:16-20` patches `escape.json_encode` for bytes).

## 2. Branding — still says CouchPotato

- Sidebar logo flips **"Couch" / "Potato"** on hover → should be "Couch" / "Tomato".
- `couchpotato/templates/index.html:5` and `login.html:23,27` `<title>` / `<h1>CouchPotato`; `api.html:10`
  "CouchPotato API Documentation".
- `couchpotato/static/scripts/couchpotato.js`: "About CouchPotato" (153), shutdown/restart prompts (286, 313),
  `+CouchPotato` bookmarklet (428); also `page/about.js`, `wizard.js`, `log.js`, `userscript.js`.
- Images `static/images/couch.png`, `notify.couch.*.png`. The bundled `combined.*.min.js/css` need rebuilding too —
  there is no working grunt build yet (see `CLAUDE.md`), so edits must hit source AND bundle.
- Default data dir is still `~/.couchpotato`; log file `CouchPotato.log`; entry script `CouchPotato.py`.

## 3. Search misses real titles

- `couchpotato/core/media/movie/providers/info/themoviedb.py` `search(self, q, limit = 3)` keeps only TMDB's first 3.
  "wall.e" → TMDB ranks WALL·E (2008) **4th** (after two shorts and a featurette), so it never shows.
  Raise to ~10. Workaround today: search the IMDb id (`tt0910970`) or `wall-e 2008`.

## 4. External APIs — every host CouchTomato actually called

Counts are calls; status is the HTTP code the log recorded; endpoints are what `Opening url` showed.

| Host / endpoint | Used for | Calls | Result | Work needed |
|---|---|---|---|---|
| `api.themoviedb.org/3` (`search/movie`, `movie/<id>`, `configuration`) | Movie search + info (built-in keys) | 114 | ✅ 200 | Only the `limit = 3` cut (item 3) |
| `image.tmdb.org/t` | Posters/backdrops | 11 | ✅ 200 | — |
| `api.couchpota.to` (`/search` 41, `/ismovie` 14, `/suggest` 7, `/messages` 5, `/eta` 5, `/info` 1) | Search suggestions, "is it a movie", ETA, update messages | 73 | ❌ domain **parked**: 200 with a for-sale HTML page → "Failed to parsing CouchPotatoApi"; plus 14 timeouts, 1× 429 | Self-host (item 8); it also slows shutdown |
| `www.omdbapi.com` (`?t=` title, `?i=` imdb id) | Exact-title + id fallback, ratings | 12 | ❌ **401** on all 12 — the configured key was rejected | Document getting a free key; surface the 401 in the UI |
| `www.magnetdl.com` (`/a/…`, `/s/…`, …) | Torrent search | 18 | ❌ 301 → **403 Cloudflare challenge** every time | Route via FlareSolverr, or drop |
| `yts.am/api/v2/list_movies.json` | Torrent search (YTS) | 10 | ✅ 301 → `yts.gg` 200 (API notice: moving to `movies-api.accel.li`) | Update base URL before the redirect dies |
| `www.imdb.com` (`/chart`, `/boxoffice`, `/movies-in-theaters`) | Automation: auto-add charts | 9 | ❌ 301 → **202** (bot challenge) → "unexpected html" ×9 | Rewrite scraper or use TMDB lists |
| `www.blu-ray.com/rss` | Home "Blu-ray.com - New Releases" | 2 | ✅ 301 → 200 | — |
| `webservice.fanart.tv/v3` | Extra artwork | 2 | UNVERIFIED (no status logged) | Check with debug on |
| `torcache.net/torrent`, `itorrents.org` → `itorrents.net` | Magnet → .torrent file (blackhole path) | 4 | ⚠ 200s, but torcache.net has been dead for years — likely a parked page, not a torrent | Verify the bytes; drop torcache |
| Transmission RPC `localhost:9091` | Downloader | — | ✅ "Torrent sent to Transmission successfully" | — |

## 5. Python 3 port bugs

- `couchpotato/core/plugins/dashboard.py:88` `getSoonView`: `TypeError: '<' not supported between 'NoneType' and
  'float'` (6×) → the home page's "soon" panel fails and the browser logs `Cannot read properties of undefined
  (reading 'length')` at `combined.plugins.min.js:870`.
- Release validation sends a Python bytes repr in the URL: `api.couchpota.to/validate/b'd2FsbMK3…'` — a base64
  `bytes` formatted with `%s`; needs `.decode()` (matters once item 8 self-hosts the API).
- `couchpotato/core/downloaders/blackhole.py:85` writes a magnet `str` into a `'wb'` file → `TypeError`
  (not hit with `magnet_file = 0`, where Transmission takes magnets directly).
- No in-app `PYTHONHASHSEED` handling: codernitydb3 `hash_index._calculate_position` uses `hash()`, which Python 3
  randomises per process, so a DB is unreadable after restart unless the seed is fixed. Proven: same DB, seed 0 →
  0/32 lookup failures; seed 123 or random → 32/32. Today the systemd unit sets `PYTHONHASHSEED=0`. Fix in code
  (deterministic hash, or re-exec with the seed) — an existing seed-0 DB must stay readable.
- Shutdown takes 40–80 s; `runner.py:366` "coroutine 'HTTPServer.close_all_connections' was never awaited".
- `SyntaxWarning: "is" with a literal` in renamer.py, providers, media, sabnzbd, scanner, log, notifications.

## 6. Make it actually download

- A working torrent provider: TPB via apibay + FlareSolverr — the approach that fixed the same Cloudflare problem in
  SickGear. YTS already works (yts.am → yts.gg redirect; proven snatch to Transmission).

### 6a. FlareSolverr support (requested 2026-10-02)

**Why:** YTS is the only provider that answers. It posts a movie only after the digital/Blu-ray release, so
anything YTS lacks is never found. MagnetDL is the only other enabled provider, and every search returns **403**
(Cloudflare challenge): `Failed opening url in MagnetDL: … 403 Client Error: Forbidden` (live log, 2026-10-02).
CouchTomato has **no FlareSolverr support at all**: no setting, and grep finds no `flaresolverr`/`cloudscraper` anywhere.

**Evidence that FlareSolverr solves it** (one request each through a FlareSolverr 3.5.2 instance, from the same home IP):

| Site | Result |
|---|---|
| `apibay.org/q.php?q=…&cat=200` (TPB's JSON search API) | HTTP 200 in 2.5 s, "Challenge not detected", real JSON results |
| `www.magnetdl.com/i/<slug>/se/desc/1/` | HTTP 200 in 21.8 s, but the page had **0 magnet links**. The provider's scraper may be stale too; check before relying on it |

**What to build:**
1. A `flaresolverr_host` setting (core or searcher section, empty = off), shown in Settings.
2. In the shared URL fetch (`couchpotato/core/plugins/base.py` `urlopen`), when a response is a Cloudflare challenge
   (403/503 with `cf-mitigated` / "Just a moment…") and the host is set, retry as FlareSolverr `request.get`
   and return `solution.response`. ⚠ For JSON APIs the browser wraps the body in `<pre>…</pre>`; strip that
   before `json.loads`. SickGear needed exactly this, and passing only the browser flag still crashed its TPB
   provider on the wrapped body.
3. Rewrite `thepiratebay.py` against apibay's JSON API (`q.php`, then build the magnet from `info_hash`) instead
   of the dead HTML site. Then re-check `magnetdl.py`'s parser.
4. Never route through FlareSolverr when the host is empty. Plain requests must stay the default.

**Done means:** a real movie that YTS does not have is found through TPB and **snatched to Transmission**. "No
errors" and a passing Test button are not proof: SickGear's Test button passed while its searches still failed.

**Note:** for a movie still in cinemas, TPB has only TELESYNC/CAM releases. The default quality profiles reject
those, correctly. FlareSolverr widens what can be found; it does not make early releases appear.
- Add `lxml` and `pyOpenSSL` to `requirements.txt` (both logged as missing at every boot).

## 7. Docs

- The wiki "Migration" page says to point `--data_dir` at an existing CouchPotato dir. **That damages the CouchPotato
  DB:** the Py2-generated `database/_indexes/*.py` fail to import on Py3 and CodernityDB renames them `*_broken`.
  Replace it with an export/import procedure (export every doc from the Py2 DB as JSON, import into a fresh
  CouchTomato data dir with the same `PYTHONHASHSEED`, verify doc counts).

## 8. Self-host the API backend — `CouchTomatoes/CouchTomatoAPI` (in scope)

The goal is to get the `api.couchpota.to` features working again, not to switch them off. The server source is
<https://github.com/CouchTomatoes/CouchTomatoAPI> (fork of the original; Node.js, Express + Redis, 251 commits; the
original author's README: "I don't really have the steps on how to get it running").

**What the client calls (all hard-coded to `https://api.couchpota.to`):**
- `couchpotato/core/media/movie/providers/info/couchpotatoapi.py:19-26` — `validate`, `search`, `info`, `ismovie`,
  `eta`, `suggest`, `updater`, `messages` (73 calls in ~1 h, all failing — see item 4).
- `couchpotato/core/downloaders/putio/main.py:19` — put.io OAuth goes through `api.couchpota.to/authorize/putio/`.
- `couchpotato.to` images/links in `notifications/discord.py:73` and `plugins/userscript/static/userscript.js:77,104`.
→ Make the API base URL a **setting** (default: the self-hosted one), not a constant.

**Server work found by reading it (not yet run):**
- Routes only accept **7-digit IMDb ids** — `app.js:92-94` `tt:imdb(\d{7})` for `eta`/`ismovie`/`info`. Modern ids are
  8 digits (e.g. `tt28037987`, `tt27032419`) and would 404 → widen to `\d{7,8}`.
- Needs **Redis** (`libs/api.js:7` `redis.createClient()`); deps are 2014-era (`request` is deprecated) — check it runs
  on current Node.
- `config.example.js`: the `mdb` block (`proxy_url`, `info_url`, `eta_url`, `ismovie_url`) is **blank** — those were
  the original author's private services; ETA/ismovie/info need a replacement source (TMDB/OMDb).
  Other sources it uses: TMDB, OMDb, Rotten Tomatoes, Movie Insider (`mi`), VETA, orlydb, corrupt-net (release
  validation), trakt `api-v2launch`, Twitter/put.io OAuth — each UNVERIFIED alive; check before relying on it.
- `whitelisted_ips` + `libs/restrict.js` gate access — set for the LAN it runs on.

## Not a bug — quality-profile defaults

The default 1080p profile minimum of 4000 MB rejects YTS 1080p encodes (~2.3 GB) as "too small to be 1080p".
Lowering the 720p/1080p minimums made YTS snatches work. Worth considering a lower default, or a hint in the UI
when every result is rejected on size.
