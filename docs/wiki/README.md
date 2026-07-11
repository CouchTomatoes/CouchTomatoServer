# Wiki content (staged here, not yet a real GitHub Wiki)

The pages in this folder are written to become CouchTomatoServer's GitHub Wiki, but the Wiki feature
isn't enabled on this repository yet (no "Wiki" tab shows up in the repo navigation), and this session's
git credentials aren't authorized to push to the `.wiki.git` companion repo even once enabled — pushing
there failed with an auth error while everything else in this session pushes to the main repo fine.

**To move these onto a real GitHub Wiki:**

1. Go to the repo's **Settings → General → Features** and check **Wikis**.
2. Clone the wiki repo (it's a separate git repo GitHub creates once the feature is enabled):
   ```sh
   git clone https://github.com/CouchTomatoes/CouchTomatoServer.wiki.git
   ```
3. Copy each file from this folder into the wiki clone, renaming `Architecture-Overview.md` etc. to
   match GitHub's wiki page-name convention if you want (GitHub wikis use the filename as the page title).
   `Home.md` is the wiki's landing page by convention.
4. Commit and push:
   ```sh
   cd CouchTomatoServer.wiki
   cp /path/to/CouchTomatoServer/docs/wiki/*.md .
   git add .
   git commit -m "Import wiki pages"
   git push
   ```

Once that's done, update the links in the main `README.md` (currently pointing at
`docs/wiki/*.md`) to point at the real wiki pages (`https://github.com/CouchTomatoes/CouchTomatoServer/wiki/...`)
instead, and this folder can be deleted.

## Pages

- [`Home.md`](Home.md) — wiki landing page / index
- [`Installation.md`](Installation.md) — per-platform install instructions
- [`Migration.md`](Migration.md) — moving from upstream CouchPotato, or between CouchTomato versions
- [`FAQ.md`](FAQ.md) — known issues and troubleshooting
- [`Architecture-Overview.md`](Architecture-Overview.md) — what's been ported, what's left, where to look for detail
