# CouchTomato - official image. Published to ghcr.io/couchtomatoes/couchtomato on every release
# (linux/amd64 + linux/arm64, so it runs on a Raspberry Pi 4/5 too). How to run it: README.md, "Docker".
FROM python:3.11-slim

# Commit and date of this build, so Settings -> About shows the exact version (DockerUpdater).
ARG VCS_REF=unknown
ARG VCS_DATE=0
ARG VERSION=dev

LABEL org.opencontainers.image.title="CouchTomato" \
      org.opencontainers.image.description="Automatic movie downloader for torrents and Usenet: the Python 3 successor to CouchPotato" \
      org.opencontainers.image.source="https://github.com/CouchTomatoes/CouchTomatoServer" \
      org.opencontainers.image.url="https://github.com/CouchTomatoes/CouchTomatoServer/wiki" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}"

ENV PYTHONHASHSEED=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COUCHTOMATO_DOCKER=1 \
    GIT_PYTHON_REFRESH=quiet \
    PUID=1000 \
    PGID=1000 \
    TZ=Etc/UTC

# tzdata: TZ works for schedules and logs. Wheels exist for lxml/pyOpenSSL on amd64 and arm64,
# so no compiler is needed.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN printf '{"hash": "%s", "date": %s}\n' "$VCS_REF" "$VCS_DATE" > docker-version.json \
 && chmod +x packaging/docker/entrypoint.sh

VOLUME ["/config"]
EXPOSE 5050

HEALTHCHECK --interval=60s --timeout=5s --start-period=60s --retries=3 \
  CMD python3 -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:5050/', timeout=4); sys.exit(0)" || exit 1

ENTRYPOINT ["/app/packaging/docker/entrypoint.sh"]
