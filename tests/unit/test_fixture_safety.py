from __future__ import annotations

import re
from pathlib import Path

import pytest


FORBIDDEN = [
    "/mnt/c/",
    "C:\\Users",
]


@pytest.mark.unit
def test_committed_fixtures_are_sanitized(fixtures_dir: Path):
    for path in fixtures_dir.glob("*.lua"):
        text = path.read_text(encoding="utf-8")
        for needle in FORBIDDEN:
            assert needle.lower() not in text.lower(), f"{needle!r} leaked in {path}"
        accounts = set(re.findall(r"@[A-Za-z0-9_\-]+", text))
        assert accounts <= {"@test_account"}, f"real account names leaked in {path}: {accounts}"
        assert path.stat().st_size < 250_000, f"{path} is too large for a committed test fixture"
