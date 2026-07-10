# Testing Screenshots

Visual evidence from manual/browser-driven testing sessions — captured with
headless Chromium via Playwright, per `CLAUDE.md`'s testing guidance ("curl/import
success alone won't catch real bugs, drive the actual UI").

## Convention

- Name files `YYYY-MM-DD-what-was-tested.png` (e.g.
  `2026-07-10-wizard-welcome-general.png`).
- One screenshot per distinct thing verified, not every frame of a session —
  pick the shot that actually shows the result (a fixed error, a working page,
  a completed state), not intermediate steps.
- Commit screenshots in the same PR as the fix/feature they verify, so the
  before/after context is in the diff.
- This folder is evidence, not a test suite — it doesn't replace or duplicate
  `TODO.md`'s checkbox list; cross-reference from there/`CLAUDE.md`'s progress
  log instead of re-explaining context here.

## 2026-07-10 — wizard fix + download-to-library pipeline (PR #8)

- `2026-07-10-wizard-welcome-general.png` — the wizard's Welcome/General steps
  rendering cleanly after the `Page.Wizard` `default_action` crash fix (previously
  threw a JS error before reaching this render).
- `2026-07-10-homepage-movie-downloaded.png` — homepage showing "Matrix, The 1999"
  under "Snatched & Available" with quality DVD-Rip highlighted, after a full
  add-movie → Transmission → renamer cycle completed against a real
  `transmission-daemon` running in the test sandbox.
- `2026-07-10-settings-downloaders-transmission.png` — Downloaders settings page
  with Transmission enabled and the host field showing the clean string
  `http://localhost:9091` (before the `settings.py` bytes-encoding fix, this field
  rendered the literal corrupted text `b'http://localhost:9091'`).
- `2026-07-10-settings-renamer.png` — Renamer settings page with clean `From`/`To`
  folder paths, same underlying fix.
