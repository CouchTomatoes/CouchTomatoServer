# FAQ / Troubleshooting

## The CouchPotatoApi provider doesn't work

Upstream CouchPotato shipped with a built-in provider that calls a hosted backend at
`api.couchpota.to` for movie search suggestions, release validation, ETA data, and update messages.
That domain is now parked/for sale, so this provider fails. It's a dead external service, not a
CouchTomato bug — there's nothing to fix client-side. The backend's source is still available at
[CouchPotato/CouchPotatoAPI](https://github.com/CouchPotato/CouchPotatoAPI) if self-hosting a
replacement is ever worth it, but that repo is archived, undocumented, and has no license file, so
that's a real project on its own, not a quick fix.

## IMDB box office / "New releases" automation isn't finding movies

IMDB blocks automated scraping of its box-office pages. This affects any automation provider that
relies on scraping IMDB directly; providers that use a real feed or API (e.g. Blu-ray.com's RSS feed)
aren't affected.

## I see an OMDB-related error in the log

The bundled OMDB API key is a placeholder. Get your own free key from [omdbapi.com](https://www.omdbapi.com/apikey.aspx)
and set it in CouchTomato's settings if you want OMDB-sourced metadata.

## macOS says the app "can't be opened because it's from an unidentified developer"

CouchTomato's macOS build isn't signed with a paid Apple Developer ID certificate, so Gatekeeper shows
this warning on first launch — this is expected for any unsigned app, not specific to CouchTomato.
To open it anyway:

1. Right-click (or Control-click) `CouchTomato.app` in Finder and choose **Open**.
2. Click **Open** in the dialog that appears (this only needs to be done once).

Alternatively: **System Settings → Privacy & Security**, scroll down to the Security section, and
click **Open Anyway** next to the CouchTomato warning.

## Why is the macOS download so much bigger than the Windows one?

The macOS build is a **universal2** binary — a single file containing full native code for *both*
Intel (x64) and Apple Silicon (arm64) Macs, merged with Apple's `lipo` tool. That's one download that
works on any Mac, at the cost of roughly doubling the size of every compiled binary inside the app
bundle (the Python interpreter itself, plus every compiled C-extension module) compared to a
single-architecture build. The Windows and Linux builds are single-architecture per download (there's
a separate x64 and arm64 build for each), so they don't have this size increase.

## Why did some releases only have Windows/Linux downloads and not macOS?

While the multi-platform release pipeline was being built out (see the main README's Release History
table, versions v4.0.15–v4.0.17), the macOS build hit three separate CI issues in a row before it
finally succeeded at v4.0.18: a GitHub-retired runner label, a missing build directory in one job, and
`lipo` correctly refusing to merge a legacy vendored 32-bit tool that was byte-identical in both
architecture builds. All three are fixed as of v4.0.18 onward.

## The frontend build (`grunt`) doesn't work / I had to hand-edit a `.min.js` file

There's currently no verified-working `npm install` + `grunt` pipeline in this repo's CI/development
environment — tracked in `CLAUDE.md`'s next-steps and `TODO.md`. Until that's fixed, any change to
`.scss`/`.js` source files needs the corresponding pre-built `combined.*.min.js`/`combined.min.css`
bundle hand-patched to match, since those are what the app actually serves.

## Something else is wrong / I found a bug

Please [open an issue](https://github.com/CouchTomatoes/CouchTomatoServer/issues) — check `TODO.md`
first in case it's already a known, tracked item (it has a running list of everything found and fixed,
plus what's still open).
