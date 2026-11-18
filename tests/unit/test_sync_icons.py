import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import sync_icons  # noqa: E402


def test_parse_missing_keeps_only_safe_icon_lines():
    text = "\n".join([
        "esoicons/a.png https://esoicons.uesp.net/esoui/art/icons/a.png",
        "abilities/b.png https://images.uesp.net/2/26/ON-icon-b.png",
        "../etc/passwd.png https://esoicons.uesp.net/x.png",
        "esoicons/c.png https://evil.example.com/c.png",
        "esoicons/d.png",
        "",
    ])
    assert sync_icons.parse_missing(text) == {
        "esoicons/a.png": "https://esoicons.uesp.net/esoui/art/icons/a.png",
        "abilities/b.png": "https://images.uesp.net/2/26/ON-icon-b.png",
    }


def test_plan_fetches_manifest_gaps_and_recorded_misses_not_on_the_server():
    manifest = {"m/1.png": "https://esoicons.uesp.net/1.png", "m/2.png": "https://esoicons.uesp.net/2.png"}
    missing = {"esoicons/x.png": "https://esoicons.uesp.net/x.png", "esoicons/y.png": "https://esoicons.uesp.net/y.png"}
    present = {"m/1.png", "esoicons/y.png"}
    assert sync_icons.plan(manifest, missing, present) == {
        "m/2.png": "https://esoicons.uesp.net/2.png",
        "esoicons/x.png": "https://esoicons.uesp.net/x.png",
    }
