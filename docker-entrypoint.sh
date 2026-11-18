#!/bin/sh
set -e
cd /app

# Started as root: run the app as whoever owns the data directory, so a bind-mounted source install keeps its owner.
# A directory Docker just created (root-owned) goes to the owner of the compose folder, else the image's armory user.
if [ "$(id -u)" = 0 ]; then
    mkdir -p uploads assets logs
    uid=$(stat -c %u uploads)
    gid=$(stat -c %g uploads)
    if [ "$uid" = 0 ]; then
        uid=$(stat -c %u /import 2>/dev/null || echo 0)
        gid=$(stat -c %g /import 2>/dev/null || echo 0)
        [ "$uid" = 0 ] && uid=10001 gid=10001
        chown "$uid:$gid" uploads
    fi
    [ "$(stat -c %u assets)" = 0 ] && chown "$uid:$gid" assets
    chown -R "$uid:$gid" logs
    exec su-exec "$uid:$gid" "$0" "$@"
fi

# First start: reuse what is already there instead of starting empty.
# 1. Data from the named `data` volume of compose files before 0.2.0-beta.4.
if [ ! -f uploads/armory.db ] && [ -f /import-volume/armory.db ]; then
    cp -a /import-volume/. uploads/
    echo "Copied existing data from the old data volume into uploads/"
fi
# 2. A source install's config.json: its db_secret decrypts the existing database.
config=${ESO_ARMORY_CONFIG:-/app/uploads/config.json}
if [ ! -f "$config" ] && [ -f /import/config.json ]; then
    cp /import/config.json "$config"
    echo "Using config.json from the source install"
fi

# Fetch game icons on first start; later starts skip existing files.
python scripts/download_assets.py || echo "warning: some icons failed to download; the app still runs" >&2
# The container always listens on 5000 inside (compose maps the host port), whatever port the config names.
exec python server.py --port 5000 "$@"
