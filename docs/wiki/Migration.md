# Migration

## From upstream CouchPotato

CouchTomato is a direct fork of CouchPotato's real commit history (see `CLAUDE.md`'s "History policy"
section) — it's the same application, ported to Python 3, not a rewrite. Your existing CouchPotato data
directory (database, settings) should work as-is:

1. Stop your existing CouchPotato instance.
2. Install CouchTomato (see [Installation](Installation.md)).
3. Point CouchTomato at your existing CouchPotato data directory using `--data_dir` (or the equivalent
   settings if you're running a packaged build), e.g.:
   ```sh
   python3 CouchPotato.py --data_dir /path/to/existing/couchpotato/data
   ```
4. Start it and confirm your movie list, settings, and quality profiles all carried over.

CouchTomato hasn't yet renamed its default config directory away from `~/.couchpotato` (tracked in
`TODO.md` under rebranding), so no path translation is needed for the default location either — this
only matters if a *future* release changes that default, at which point this page will be updated with
the exact steps.

**Known migration-relevant fact:** if your existing setup relied on the `CouchPotatoApi` provider
(movie suggestions, ETA, or update messages from `api.couchpota.to`), that stops working after
migrating — not because of anything CouchTomato changed, but because that upstream hosted service
itself is gone. See the [FAQ](FAQ.md#the-couchpotatoapi-provider-doesnt-work) for details.

## Between CouchTomato versions

Releases are numbered `v4.x.x` and are cumulative — there's no special migration step between versions
in this series. Just install the newer version over (or alongside, if using a portable build) the old
one; your data directory and settings are untouched by the app itself.

If you're running from source and using the built-in git-based updater, it should pick up new commits
automatically; if you installed a packaged build (installer/zip/AppImage/DMG), just download and
install the newer release manually — there's no in-app auto-updater for packaged builds yet.
