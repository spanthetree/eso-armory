#!/usr/bin/env python3
"""Generate sanitized test fixtures from local ESO SavedVariables.

The committed fixtures are intentionally tiny and deterministic. This script is
a manual helper for refreshing them after the live data shape changes; it does
not need to run during normal tests.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"

REPLACEMENTS = {
    re.compile(r"@[A-Za-z0-9_\-]+"): "@test_account",
    re.compile(r"C:\\Users\\[^\\\n]+", re.IGNORECASE): "C:\\Users\\test_user",
    re.compile(r"/mnt/c/users/[^/\n]+", re.IGNORECASE): "/mnt/c/users/test_user",
}


def sanitize(text: str) -> str:
    for pattern, replacement in REPLACEMENTS.items():
        text = pattern.sub(replacement, text)
    return text


def copy_prefix(src: Path, dest: Path, max_bytes: int) -> None:
    data = src.read_text(encoding="utf-8", errors="replace")[:max_bytes]
    dest.write_text(sanitize(data), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", type=Path, required=True, help="ESO live folder, e.g. .../Documents/Elder Scrolls Online/live")
    parser.add_argument("--max-bytes", type=int, default=200_000)
    args = parser.parse_args()

    sv = args.live / "SavedVariables"
    ttc = args.live / "AddOns" / "TamrielTradeCentre"
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for src, dest_name in (
        (sv / "iasync.lua", "iasync.generated.lua"),
        (sv / "WizardsWardrobe.lua", "WizardsWardrobe.generated.lua"),
        (ttc / "ItemLookUpTable_EN.lua", "ItemLookUpTable_EN.generated.lua"),
        (ttc / "PriceTableNA.lua", "PriceTableNA.generated.lua"),
    ):
        if not src.exists():
            raise FileNotFoundError(src)
        copy_prefix(src, FIXTURE_DIR / dest_name, args.max_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
