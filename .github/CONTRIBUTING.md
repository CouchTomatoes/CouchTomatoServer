# Contributing to CouchTomato

Thanks for helping! CouchTomato is the Python 3 successor to CouchPotato, and it stays alive
because people report what breaks and send fixes.

- **Found a bug?** [Open a bug report](https://github.com/CouchTomatoes/CouchTomatoServer/issues/new/choose). Check the
  [FAQ](https://github.com/CouchTomatoes/CouchTomatoServer/wiki/FAQ) and existing issues first.
- **Have an idea?** [Open a feature request](https://github.com/CouchTomatoes/CouchTomatoServer/issues/new/choose).
- **Security problem?** Please report it privately, see [SECURITY.md](SECURITY.md).

## Branches

Like SickGear, CouchTomato has two long-lived branches:

| Branch | What it is |
|---|---|
| `dev` | Where all work lands. **Open your pull request against `dev`.** Not released. |
| `main` | The released code. Merging `dev` into `main` cuts a numbered release (v4.0.x) with installers for Windows, macOS and Linux. |

## Running it from source

```bash
git clone https://github.com/CouchTomatoes/CouchTomatoServer.git
cd CouchTomatoServer
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python CouchPotato.py            # then open http://localhost:5050/
```

Use **Python 3.11**. Newer Pythons can show unrelated test errors.

## Before you open a pull request

```bash
PYTHONHASHSEED=0 python -m unittest discover -s tests     # the same tests CI runs
```

- **JavaScript:** edit the source `.js` files, then rebuild the bundles with
  `cd tools/jsbuild && npm ci && node build.js`. Never edit `combined.*.min.js` by hand; CI
  fails a bundle that doesn't match its sources. The bundler is old, so write ES5 (no arrow
  functions, `let`/`const` or template literals).
- **CHANGES.md:** add one line under **Unreleased** for anything a user would notice
  (`* New: …`, `* Change: …`, `* Fix: …`).
- **Test the real thing.** For a UI change, click through it in a browser. For a provider or
  download client, run a real search or a real hand-off. Say in the PR what you did and what
  you saw.
- **Keep providers.** Don't remove a provider, downloader or notifier because it looks dead.
  Fix it, or say what's wrong in an issue.
- One change per pull request, with a description that makes sense to someone who wasn't
  there.

## Licence

CouchTomato is GPLv3, like CouchPotato before it. By sending a pull request you agree your
contribution is released under the same licence.
