#!/usr/bin/env python3
"""Fill in the icons a server cannot download itself, from a machine UESP serves.

UESP's Cloudflare refuses many cloud hosts (HTTP 403), so a server there lacks the icons it never managed to
fetch. The server sends browsers to UESP for those and records them in uploads/missing_assets.txt. Run this
from your desktop now and then: it reads that list over SSH (plus any manifest icons absent on the server),
downloads them here, copies them into the server's assets/ with rsync, and drops them from the list.

    uv run scripts/sync_icons.py user@host [--dir /srv/eso-armory] [--dry-run]

Needs ssh and rsync, and sudo on the server (assets/ belongs to the app's user).
"""
import argparse
import json
import re
import shlex
import subprocess
import sys
import tempfile
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from download_assets import MANIFEST, fetch

# Paths come from the server's request log: accept only plain icon paths and UESP image URLs.
SAFE_PATH = re.compile(r"^(?!.*\.\.)[a-z0-9_][a-z0-9_./-]{0,200}\.png$")
SAFE_URL = re.compile(r"^https://(esoicons|images)\.uesp\.net/[A-Za-z0-9_./%-]+\.png$")
SPLIT = "--- assets ---"


def ssh(host: str, cmd: str, stdin: str | None = None) -> str:
    return subprocess.run(["ssh", host, cmd], input=stdin, capture_output=True, text=True, check=True).stdout


def parse_missing(text: str) -> dict[str, str]:
    """`<path> <url>` lines from missing_assets.txt; anything malformed or unsafe is ignored."""
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and SAFE_PATH.match(parts[0]) and SAFE_URL.match(parts[1]):
            out[parts[0]] = parts[1]
    return out


def plan(manifest: dict[str, str], missing: dict[str, str], present: set[str]) -> dict[str, str]:
    """Icons to fetch: listed as missing or in the manifest, and not on the server."""
    todo = {p: u for p, u in manifest.items() if p not in present}
    todo.update({p: u for p, u in missing.items() if p not in present})
    return todo


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("host", help="ssh destination, e.g. ubuntu@armory.example.com")
    ap.add_argument("--dir", default="/srv/eso-armory", help="folder with compose.yaml, uploads/ and assets/")
    ap.add_argument("--dry-run", action="store_true", help="only report what is missing")
    args = ap.parse_args()
    d = shlex.quote(args.dir.rstrip("/"))

    report = ssh(args.host, f"sudo cat {d}/uploads/missing_assets.txt 2>/dev/null; echo {shlex.quote(SPLIT)}; "
                            f"sudo stat -c %u:%g {d}/assets && cd {d}/assets && sudo find . -type f -name '*.png'")
    log_text, _, rest = report.partition(SPLIT + "\n")
    owner, *files = rest.splitlines()
    present = {f.removeprefix("./") for f in files}
    missing = parse_missing(log_text)
    manifest = json.loads(MANIFEST.read_text())
    todo = plan(manifest, missing, present)
    print(f"server has {len(present)} icons; {len(missing)} recorded as missing; {len(todo)} to fetch")
    if args.dry_run:
        for p in sorted(todo):
            print(f"  {p}")
        return 0

    done, gone, failed = [], [], []
    with tempfile.TemporaryDirectory() as tmp:
        def one(item):
            path, url = item
            try:
                body = fetch(url)
            except urllib.error.HTTPError as exc:
                return path, "gone" if exc.code == 404 else str(exc)
            except Exception as exc:
                return path, str(exc)
            out = Path(tmp) / path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(body)
            return path, None

        with ThreadPoolExecutor(4) as pool:  # keep load on UESP modest
            for path, err in pool.map(one, todo.items()):
                (done if err is None else gone if err == "gone" else failed).append((path, err))

        if done:
            subprocess.run(["rsync", "-a", "--rsync-path=sudo rsync", f"--chown={owner}", f"{tmp}/",
                            f"{args.host}:{args.dir.rstrip('/')}/assets/"], check=True)

    # Drop what the server now has (or UESP doesn't have) from its list; keep failures for next time.
    settled = present | {p for p, _ in done} | {p for p, _ in gone}
    if log_text.strip():
        keep = "".join(f"{p} {u}\n" for p, u in missing.items() if p not in settled)
        ssh(args.host, f"sudo tee {d}/uploads/missing_assets.txt >/dev/null", stdin=keep)

    for path, err in failed:
        print(f"FAILED {path}: {err}", file=sys.stderr)
    if gone:
        print(f"{len(gone)} not on UESP (skipped): " + ", ".join(p for p, _ in gone[:5]) + (" ..." if len(gone) > 5 else ""))
    print(f"copied {len(done)} icons to {args.host}:{args.dir}/assets; {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
