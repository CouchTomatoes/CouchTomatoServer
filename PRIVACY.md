# Privacy

CouchTomato is free, open-source (GPLv3), **self-hosted** software. Each user runs their own copy on
their own computer or home server. The CouchTomato project runs **no servers**, has **no accounts**,
and **collects no data** — no telemetry, no analytics, no crash reports.

## What stays on your machine

Everything CouchTomato knows lives in its data folder on the machine you run it on: your settings
(`settings.conf`), your movie database, logs and cached images. Nothing is sent to the project.

## Services you choose to connect

CouchTomato only talks to third-party services that you switch on in its settings (search sites,
download clients, metadata sources, notification services). Each request goes directly from your
machine to that service, under that service's own privacy policy.

### Trakt

If you sign in to Trakt, CouchTomato uses Trakt's device-code sign-in. The access token Trakt issues
is stored only in your own `settings.conf`; you can revoke it at any time from your Trakt account
(Settings → Connected Apps) or by signing out in CouchTomato. CouchTomato uses Trakt to:

- read the movies on your Trakt watchlist, so it can search for them;
- add a movie to your Trakt collection once it has finished downloading (optional);
- remove that movie from your Trakt watchlist (optional).

It does not read or change anything else in your Trakt account.

CouchTomato uses Trakt but is not endorsed or certified by Trakt.

## Contact

Questions or concerns: open an issue at
<https://github.com/CouchTomatoes/CouchTomatoServer/issues>.
