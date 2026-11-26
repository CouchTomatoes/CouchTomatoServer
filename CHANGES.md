# Changes

One entry per change that someone using CouchTomato would notice. Add your line under
**Unreleased** in the same PR as the change. When `dev` is merged into `main`, the
release workflow tags the next version, and the Unreleased heading gets that version
number and date.

Releases up to v4.0.69 have their notes on the
[GitHub Releases page](https://github.com/CouchTomatoes/CouchTomatoServer/releases).

### Unreleased

* New: Add a movie has Dropdown and Full page views next to Classic (switch above the search results, or
  Settings → Screens). Dropdown shows the best 4 matches and View all N results; Full page is a poster grid with
  In wanted / In library tags and a one-click + Add (pick the quality with "change").
* New: Home's Snatched & Available list has Cards and Table views next to Classic (switch beside its title, or
  Settings → Screens). Each release shows its state (Downloading %, Stuck, Gone, Available, In library) with Try next
  release, Download again, Ignore release and Details; Table adds quality, size, age, score and provider.
* New: Activity page (menu → Activity): every snatched download with live progress and time left, and the ones that
  need you (Stuck, Failed, Gone, Can't import) with a Fix… button: Try another release or Keep waiting. Table or Cards
  view (switch top right, or Settings → Screens).
* Fix: "Try another release" did nothing (a database lookup crashed), and the automatic retry after a failed download
  never ran either. Database index upgrades now take effect on the first start instead of the second.
* New: Wanted gets status chips (All / Snatched / Available / Still wanted, with counts), and its List view shows
  Quality, Status, Added and Last search columns; Manage's List view shows each movie's folder.
* New: Torznab searcher, so CouchTomato can search your Prowlarr or Jackett indexers (Settings → Searcher → Torznab,
  one row per indexer). It asks by IMDb id first, falls back to title + year, and sends magnet links when the indexer has them.
* Fix: with debug logging on, the log no longer contains your indexers' API keys and passkeys (a low-level HTTP
  library was writing every request URL unmasked).
* New: Home has a view switch (top right): Sections (each list as one row of posters with "See all") and Dashboard
  (Wanted / Snatched / Available / In library counts, then every list as a compact card), next to Classic, which stays
  the default. Settings → Screens → Home sets it too, and the choice is saved for every browser.
* New: Wanted and Manage have the same switch: Posters or List show the search box, A–Z and the page's buttons
  (Search all wanted, Manual folder scan / Full library refresh, Quick library scan) right on the page instead of in
  menus. Classic stays the default; Settings → Screens has one picker per page.

### v4.0.75 (2026-11-25)

* Fix: the Telegram notifier no longer writes your bot token into the log when a message fails to send
  (the log names the bot by its public number instead). If you've shared a log, make a new token with @BotFather.

### v4.0.74 (2026-11-25)

* Fix: the Windows x64 downloads are back. v4.0.73 shipped without the x64 portable zip, and its
  `CouchTomato-Setup-4.0.73.exe` held the arm64 build (it won't run on a normal Windows PC). The
  Windows on ARM installer, when it builds, now has its own name (`…-arm64.exe`).

### v4.0.73 (2026-11-25)

* New: Movie details has Subtitles (Poster: under Releases; Hero: a tab). Pick a language, see what yts-subs.com has
  for the movie with the one made for your release marked, and choose one: in the library it replaces
  `<movie>.<lang>.srt` at once (the old file kept as `.srt.bak`); still downloading, it's used when the movie arrives.
* Fix: automatic subtitles now find Spanish and Persian (they never matched), and yts-subs ratings are read again
  (every subtitle scored 0, so the best-rated one wasn't preferred).
* New: Movie details shows a download live: the "Downloading" step fills up as a progress bar with the %, the
  line under it adds "downloading for 1 h 12 m · 18 min left", and it all updates every 10 s without a reload while
  the page is open (Transmission, Deluge, qBittorrent, rTorrent, uTorrent, SABnzbd, NZBGet, put.io).
* New: Movie details (Hero and Poster) now says where the movie is in one line under the steps:
  "Snatched 2 h ago from YTS", "Downloaded 3 h ago · moving to your library" or "In your library since …".
  The times count up by themselves while the page is open.

* New: a small NEW tag marks things added in recent updates (the History page and Settings → Screens for
  now). Turn them all off in Settings → Screens → Show NEW tags; each tag also goes away by itself after a
  few months.

* New: a redesigned movie details page. Pick **Poster** (poster and facts on the left), **Hero** (a wide
  banner) or **Classic** (the old look), and a **Full**, **Small** or no backdrop, with the switch at the
  top of the page or in Settings → Screens. Your choice is saved on the server, so every browser and phone
  opens the same way. It shows where the movie is (Wanted → Snatched → Downloading → In library) and adds
  Search now, a Trailer pop-up, and Quality and Category menus right on the page.

* New: an official Docker image, `ghcr.io/couchtomatoes/couchtomato` (amd64 and arm64, so it runs on a
  Raspberry Pi too), published with every release. Files are written as your own user (`PUID`/`PGID`),
  and inside Docker the updater tells you when to pull a new image instead of trying to update itself.

### v4.0.72 (2026-11-25)

* Fix: Settings → About and the bookmarklet no longer load anything from couchpota.to. The old
  domain is parked and its page sends visitors on to ad campaigns. The menu's Donate link now
  opens the CouchTomato GitHub repo.

### v4.0.71 (2026-11-24)

* Fix: the nightly History clean-up crashed when an event field was stored as bytes, so
  nothing older than the Keep history limit was ever moved into an archive file.

### v4.0.70 (2026-11-20)

* New: a History page, a dated timeline of what happened to each movie (added, snatched,
  downloaded, moved, replaced, failed, subtitles) and to the app (updates, sign-ins). It starts
  filled from your existing notifications and finished downloads. Settings → General → History
  keeps 90 days (default), 1 year or Forever; older events go into archive files you can import
  back. Making Keep longer brings archived events that are now inside it back onto the page, and
  making it shorter adds to the existing files instead of creating files whose dates overlap
* Change: development now happens on the `dev` branch. `main` only gets deliberate,
  numbered releases, so the built-in updater installs a release, not every merge
* Fix the X (Twitter) notifier: it now posts through X's current API (v2) with 280-character
  posts and v2 direct messages. Fill in your own X developer app's four keys; X charges per
  post since February 2026, so there is no shared project app. "Sign in with X" still works
  once your app's API key and secret are filled in
