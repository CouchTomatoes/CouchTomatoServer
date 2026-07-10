# Open Suggestions / Decisions Needed

Items that need a decision from the repo owner rather than something Claude can
resolve unilaterally. Append new items here as they come up; check them off (or
delete) once decided/resolved.

## Mirroring upstream CouchPotato's release tags

**Status: blocked from this session, needs your input.**

Upstream `CouchPotato/CouchPotatoServer` has 27 git tags (`build/2.0.0.pre1` through
`build/3.0.1`) marking old Python 2 release builds. All 27 were fetched successfully
into the local working copy of `claude/couch-tomato-parity-e1f5bl` — that part works
fine over plain `git`. Pushing them to `CodeAhmed/CouchTomato` does not: it fails with
a hard `403` from the Anthropic proxy this session's git traffic runs through
(`CCR Upstream Proxy CA`), regardless of which tag or content — confirmed with
`GIT_CURL_VERBOSE=1`, same result on a fresh throwaway tag. Regular branch pushes work
fine through the same proxy, so this looks like a deliberate guardrail specifically on
tag-ref creation, not a GitHub permissions problem or a fluke.

Separately, checking whether upstream even has real GitHub "Releases" (release notes/
assets, not just tags) isn't possible from here either — this session's GitHub API
access is scoped to `CodeAhmed`-owned repos only, and adding a repo owned by a
different account (`CouchPotato`) mid-session isn't supported ("cross-tier adds are
not supported").

**Options:**

1. **Do it yourself locally** — quickest path:
   ```
   git fetch --tags https://github.com/CouchPotato/CouchPotatoServer.git
   git push origin --tags
   ```
   against your own clone of `CodeAhmed/CouchTomato`, with your own credentials.
   Should take well under a minute.

2. **Claude writes out the tag list as a reference file** (names, SHAs, which commit
   each points to) checked into the repo, and you decide later whether/how to cut
   actual releases from it — without ever needing tags pushed.

3. **Skip mirroring old tags entirely** — worth considering on its own merits: these
   are old CouchPotato 2.x/3.x *Python 2* build tags. Once the Python 3 port +
   CouchTomato rebrand lands, they may be more confusing than useful sitting on this
   repo. Could make more sense to start CouchTomato's own version tags fresh from the
   first real CouchTomato release forward, and only reference the upstream tags in
   docs/changelog prose rather than as actual refs on this repo.

No action taken yet — waiting on which of the above (or a different approach) you'd
prefer.
