# Movie details: live status, Subtitles, NEW tags (build plan)

Status: **design approved 2026-11-21** (mockup v10). Not built yet. This file is what the build
follows. One PR per numbered part below, each to `dev`, each with its own CHANGES line.

Mockup: the "CouchTomato screens FINAL v10" artifact, screen 1 (Movie details, Hero and Poster).
⟲ Classic keeps today's page and gets none of this.

## 1. Live status: what updates, how, how fast

These parts of Movie details change on screen **without reloading the page**:

| On screen | Example | Updates without reload | Where it comes from |
|---|---|---|---|
| Download % | `Downloading 64%` (Hero badge, Poster steps). **The pill is itself the progress bar**: the accent colour fills it left → right with the % over a dark track; at 100 % it is fully filled and the connector to `In library` lights up | **every 10 s** while the page is open | Downloader (Transmission `percentDone`) |
| Time left | `downloading for 1 h 12 m · 18 min left` | **every 10 s** while the page is open | Downloader (`eta`; elapsed from `addedDate`, else the snatch date) |
| Done | `downloaded 3 h ago · moving to your library` (s → min → h → days) | recounted in the browser | Downloader (`doneDate`), else the time 100 % was first seen |
| Freshness | **Nothing in normal use.** Only when no update has arrived for > 30 s: grey dot `last update 2 min ago · reconnecting` | counts every second in the browser | time of the last check |
| Relative times | `Snatched 2 h ago from YTS` | recounted **every 60 s** in the browser, no server call | snatch date already in the release |
| Status steps | Wanted → Snatched → Downloading → In library | **within 10 s** of the change | existing `release.update_status` / media update events |
| Search started / ended, new releases found | `Releases (4)` | **at once** (already pushed today) | `movie.searcher.started/ended` |
| Subtitle saved | `✓ chosen` → saved | **at once** | new `subtitle.saved` event (part 3) |

When no browser has such a page open, the server goes back to today's background check every
`renamer.run_every` minutes (default 1). The 10 s rate only exists while someone is looking.

### What exists today (checked in the code, 2026-11-21)

- **The push channel already exists.** The browser keeps one request open to
  `nonblock/notification.listener`; the server answers the moment anything calls
  `fireEvent('notify.frontend', type=..., data=...)`. After each answer the browser re-opens it
  after 1.5 s; on an error it retries after 2 s; every 120 s it restarts it
  (`notifications/core/static/notification.js`). On the page: `App.on('<type>', fn)`.
  **Build on this. Do not add WebSockets or a second polling loop.**
- **Download progress is not pushed, and most of it is thrown away.** `renamer.checkSnatched`
  runs every `run_every` minutes and asks the downloader for status. Transmission's RPC call
  already asks for `percentDone` and `eta`, but `getAllDownloadStatus` only returns `timeleft`,
  and nothing reaches the page unless the status *changes*.

### Build

1. **Downloaders report progress.** Add `progress` (0–100, or `None` when unknown) to each item
   from `getAllDownloadStatus`: Transmission `percentDone`, qBittorrent `progress`, Deluge
   `progress`, put.io, then the others where their API has it. Unknown → the page shows
   `Downloading` with no %, never a made-up number.
2. **Keep it in memory, not in the database.** A `{release_id: {progress, timeleft, status,
   checked_at}}` dict. Writing CodernityDB every 10 s would grow the files and wear the Pi's SD
   card; this data is worthless after the download ends. New API `download.live` returns the dict
   (first paint when a page opens).
3. **Push only what changed.** After each check, `fireEvent('notify.frontend',
   type='release.progress', data=[changed items])`: progress changed by ≥ 1 point, or the ETA
   changed. Nothing changed → nothing is sent.
4. **Fast lane while someone watches.** The Details page (and Activity) sends `download.watch`
   with the release ids it shows, every 30 s. While a watch is fresh (< 60 s old) the server
   checks **only those torrents** every 10 s. No heartbeat for 60 s → the fast lane stops.
   (Fits the idle rule: nothing runs faster than today when nobody is looking.)
5. **Page updates in place.** `App.on('release.progress')` changes only the % text, the
   pill's fill (a CSS variable `--p`, one `linear-gradient`, no extra element), the connector
   and the `downloading for … · … min left` text. **No re-render**: an open Quality ▾ menu or
   the trailer must stay open. There is no "updated N s ago" while updates arrive; if nothing
   arrives for 3× the interval (30 s), a grey dot appears: `last update 40 s ago · reconnecting`,
   and disappears with the next update.
6. **Hidden tab = no fast lane.** Use the Page Visibility API: a hidden tab stops sending
   `download.watch`; when it becomes visible again it calls `download.live` once.
7. **At 100 %** the pill is fully filled, the connector to `In library` lights up and the line reads
   `downloaded just now · moving to your library` (then `5 min ago`, `3 h ago`…); the existing
   renamer events move the steps to `In library`.

### Proof required before the PR is merged (evidence that matches the claim)

- On the **Pi4**, with a real download in Transmission: the % on the page changes at least 3 times
  without a reload, and matches `transmission-remote -l` within 1 point.
- An open Quality ▾ menu stays open through 3 updates.
- Close the tab → the server log shows the fast lane stopping within 60 s. Leave no tab open for
  5 min → the downloader is only asked every `run_every` minutes.
- Stop the server with the page open → the grey `last update … · reconnecting` appears within 30 s;
  start it → it disappears without a reload.
- The pill's fill matches the % text at each update (screenshot at two different %s and at 100 %).
- Unit tests: progress parsing per downloader (including "unknown"), "changed only" push logic,
  heartbeat expiry.

## 2. Hero shows the snatch line too

Under the badges in Hero: `Snatched 2 h ago from YTS · downloading for 1 h 12 m · 18 min left`. It's the same line Poster has under its steps, and it uses the same live fields as part 1.

## 3. Subtitles (Hero: a tab; Poster: a section under Releases)

- **Language ▾** button (same button + menu style as Quality ▾). Default = the subtitle
  language(s) in Settings.
- List from yts-subs.com (no account): subtitle name, language, "made for" (YIFY, FLUX, SDH…),
  rating, and a **matches your release** badge on the one made for the snatched release.
- **Use this** → marked `✓ chosen`. While the movie is still downloading, the choice is saved and
  the file is written when the movie reaches the library. When it's already in the library, the
  button reads **Replace**, writes `<movie>.<lang>.srt` next to the file straight away (keeping
  the old file as `.srt.bak`), and fires `subtitle.saved`.
- No subtitles for a language → `No Urdu subtitles found for this movie on yts-subs.com.`
- New APIs: `subtitle.search` (movie id, language → list) and `subtitle.choose` (movie id,
  subtitle id). Reuse the existing yts-subs code; the automatic download stays as it is.
- Proof: on the Pi4, replace a movie's English subtitle from the page; the new `.en.srt` is on
  disk next to the movie and Plex shows it after a section refresh.

## 4. Show NEW tags (Settings → Screens → Labels)

- Checkbox **Show NEW tags**, default **on**, setting `core.show_new_tags`. It saves on click,
  like the other Screens settings.
- Off → every NEW tag in the app is hidden (one class on `<body>`, `.hide-new .new{display:none}`).
  It changes at once on the current page; other open browsers pick it up on their next page load.
- Each NEW tag is one shared helper/element so the switch covers all of them. No per-page copies.

## Order

Part 4 (small, no risk) → part 2 → part 1 (biggest; needs the Pi4 proof) → part 3.
