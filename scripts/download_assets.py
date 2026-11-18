#!/usr/bin/env python3
"""Download the game icons listed in scripts/assets_manifest.json from UESP into assets/.

Icons are ZeniMax Online Studios artwork, so they are fetched at setup instead of
being committed. Existing files are skipped; pass --force to re-download.

    uv run scripts/download_assets.py [--dest DIR] [--force]

If UESP refuses this host (HTTP 403, common on cloud servers) the icons come through a public image proxy;
see uesp.py.
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).resolve().parent / "assets_manifest.json"
sys.path.insert(0, str(ROOT))
import uesp  # noqa: E402


def fetch(url: str) -> bytes:
    for attempt in range(3):
        try:
            body = uesp.fetch_png(url, timeout=120)
            if body is None:
                raise FileNotFoundError(f"{url}: 404")
            return body
        except FileNotFoundError:
            raise
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest", type=Path, default=ROOT / "assets")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    manifest: dict[str, str] = json.loads(MANIFEST.read_text())
    todo = {p: u for p, u in manifest.items() if args.force or not (args.dest / p).is_file()}
    print(f"{len(manifest)} icons, {len(todo)} to download")

    def one(item):
        path, url = item
        try:
            body = fetch(url)
        except Exception as exc:
            return path, f"{url}: {exc}"
        out = args.dest / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
        return path, None

    with ThreadPoolExecutor(4) as pool:  # keep load on UESP modest
        failed = [(p, e) for p, e in pool.map(one, todo.items()) if e]

    for path, err in failed:
        print(f"FAILED {path} <- {err}", file=sys.stderr)
    print(f"done: {len(todo) - len(failed)} downloaded, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
