# Branches and releases

CouchTomato works the way SickGear does: development on `dev`, and only deliberate,
numbered releases on `main`.

| Branch | What lands there | Goes live? |
|---|---|---|
| `dev` | every pull request | No. Nothing installs from `dev` |
| `main` | a merge of `dev`, when it is ready to ship | Yes. Every push cuts a release, and installs update from `main` |

## Day to day

1. Branch from `dev` and open the pull request **against `dev`** (`gh pr create --base dev`).
2. Add a line to `CHANGES.md` under **Unreleased**.
3. CI (`ci.yml`, which calls `_verify.yml`) must be green before the merge. It runs on the
   self-hosted runner.

## Cutting a release

1. Check that `dev` is green and has been tried on a real install.
2. Rename **Unreleased** in `CHANGES.md` to the next version and date (the next patch
   after the latest `vX.Y.Z` tag), on `dev`.
3. Open a pull request from `dev` into `main` and merge it with a merge commit (never a
   squash, so `main` and `dev` keep the same history).
4. `release.yml` (on hosted runners) tags the version, writes the NEW/FIX release notes
   from the commit subjects, and attaches the Windows, Linux and macOS builds.
5. Installs that follow `main`, including the built-in updater, pick it up on their next
   update check.

## Commit subjects

Release notes are built from commit subjects: `fix…`, `fixed…`, `bugfix…` and `hotfix…`
become FIX lines, and everything else becomes NEW. Merge commits are skipped.
