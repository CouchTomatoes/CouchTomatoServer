#!/bin/sh
# Starts CouchTomato as PUID:PGID (default 1000:1000) so files in /config, /downloads and /movies
# belong to your user on the host, not to root. Run with --user instead and this step is skipped.
set -eu

CONFIG=/config
mkdir -p "$CONFIG"

# First start: a browser can't open inside a container, and the port must match EXPOSE.
if [ ! -f "$CONFIG/settings.conf" ]; then
    printf '[core]\nport = 5050\nlaunch_browser = False\n' > "$CONFIG/settings.conf"
fi

set -- python3 /app/CouchPotato.py --data_dir "$CONFIG" --config_file "$CONFIG/settings.conf" --console_log "$@"

if [ "$(id -u)" = "0" ]; then
    chown "$PUID:$PGID" "$CONFIG"
    # Only fix ownership when it is wrong, so a big library isn't walked on every start
    [ "$(find "$CONFIG" \! -user "$PUID" -print -quit 2>/dev/null)" ] && chown -R "$PUID:$PGID" "$CONFIG"
    exec setpriv --reuid="$PUID" --regid="$PGID" --clear-groups "$@"
fi
exec "$@"
