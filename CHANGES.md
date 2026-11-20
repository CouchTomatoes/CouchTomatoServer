# Changes

One entry per change that someone using CouchTomato would notice. Add your line under
**Unreleased** in the same PR as the change. When `dev` is merged into `main`, the
release workflow tags the next version, and the Unreleased heading gets that version
number and date.

Releases up to v4.0.69 have their notes on the
[GitHub Releases page](https://github.com/CouchTomatoes/CouchTomatoServer/releases).

### Unreleased

* Change: development now happens on the `dev` branch. `main` only gets deliberate,
  numbered releases, so the built-in updater installs a release, not every merge
* Fix the X (Twitter) notifier: it now posts through X's current API (v2) with 280-character
  posts and v2 direct messages. Fill in your own X developer app's four keys; X charges per
  post since February 2026, so there is no shared project app. "Sign in with X" still works
  once your app's API key and secret are filled in
