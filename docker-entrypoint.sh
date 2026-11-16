#!/bin/sh
set -e
# Fetch game icons into the assets volume on first start; later starts skip existing files.
python scripts/download_assets.py || echo "warning: some icons failed to download; the app still runs" >&2
exec python server.py "$@"
