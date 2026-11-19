#!/usr/bin/env python3
"""Build the demo account (demo/demo.json.gz) from a real iasync.lua and WizardsWardrobe.lua, anonymised.

The demo shows visitors a full armory before they upload their own: real items, sets, achievements, collections,
activities and antiquities, but under the account @armory-demo with generated character and guild names. Every
string that identifies the source account (account, character ids and names, guild names, Wizards Wardrobe setup
and page names, Armory build and outfit names) is replaced, and the script refuses to write if any of them still appears in the output.

    uv run scripts/make_demo.py <iasync.lua> [<WizardsWardrobe.lua>]

The server loads demo/demo.json.gz on start (server.py _ensure_demo_account).
"""
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from data_processor import (  # noqa: E402
    process_iasync, process_iasync_achievements, process_iasync_builds, process_iasync_stickerbook, process_ww_builds,
)
from lua_parser import parse_lua_variable  # noqa: E402

OUT = ROOT / "demo" / "demo.json.gz"
ACCOUNT = "@armory-demo"
NAMES = ["Aldric Vane", "Seryn Thorne", "Drevis Ulvo", "Kaela Sunshield", "Mira Ashfall", "Torvald Ironhand",
         "Jhazri-Ko", "Velis Dunmere", "Brannoc the Grey", "Ysolde Marr", "Rhazir", "Teodora Valen",
         "Hakon Frostmane", "Nirili Swiftreed", "Orsa gro-Bagol", "Caius Ventor", "Lyra Duskwhisper", "Ezen-Tei"]
# Armory builds get role names, so the demo doesn't copy the source account's build list.
ARMORY_NAMES = ["Trial DPS", "Dungeon DPS", "Off-Tank", "Healer", "PvP Brawler", "PvP Tank", "Solo Arena", "Overland",
                "Main Tank", "Support"]
GUILDS = ["Order of the Silver Quill", "The Ashen Lantern", "Coin and Crown Traders", "Wardens of the Rift", "Hollow Oak Society"]


def build(iasync_path: Path, ww_path: Path | None) -> dict:
    raw = parse_lua_variable(str(iasync_path), "iasync_data")
    payload = {
        "data": process_iasync(raw, server="NA"),
        "builds": process_iasync_builds(raw),
        "achievements": process_iasync_achievements(raw),
        "stickerbook": process_iasync_stickerbook(raw),
        "ww": process_ww_builds(parse_lua_variable(str(ww_path), "WizardsWardrobeSV")) if ww_path else {"builds": {}},
    }

    # Everything that identifies the source account, mapped to a stand-in.
    data = payload["data"]
    swap: dict[str, str] = {data["meta"]["account"]: ACCOUNT}
    for n, (cid, c) in enumerate(sorted(data["characters"].items())):
        swap[cid] = f"demo-{n + 1}"
        swap[c["name"]] = NAMES[n % len(NAMES)]
    guilds = {g["name"] for c in data["characters"].values() for g in c.get("guilds", [])}
    guilds |= {l["location_label"] for i in data["items"] for l in i["locations"] if l["location_type"] == "guild_bank"}
    for n, g in enumerate(sorted(guilds)):
        swap[g] = GUILDS[n % len(GUILDS)] if n < len(GUILDS) else f"Guild {n + 1}"
    for setups in payload["ww"]["builds"].values():
        for n, s in enumerate(setups):
            s["name"], s["page_name"] = f"Setup {n + 1}", f"Page {s.get('page', 1)}"
    armory_src = {b[k] for a in payload["builds"].get("armory", {}).values() for b in a for k in ("name", "outfit_name") if b.get(k)}
    for armory in payload["builds"].get("armory", {}).values():
        for n, b in enumerate(armory):
            b["name"] = ARMORY_NAMES[n % len(ARMORY_NAMES)]
            if b.get("outfit_name"):
                b["outfit_name"] = f"Outfit {b['outfit_index'] or n + 1}"

    # Longest first, so a name containing another is replaced whole; substrings too (achievements store "Name^Mx").
    keys = sorted((k for k in swap if k), key=len, reverse=True)

    def scrub(v):
        if isinstance(v, dict):
            return {scrub(k): scrub(x) for k, x in v.items()}
        if isinstance(v, list):
            return [scrub(x) for x in v]
        if isinstance(v, str):
            if v in swap:
                return swap[v]
            for k in keys:
                if len(k) >= 4 and k in v:
                    v = v.replace(k, swap[k])
            return v
        return v

    out = scrub(payload)
    fill_in(out)
    out["data"]["meta"].update(account=ACCOUNT, server="NA", item_count=len(out["data"]["items"]),
                               character_count=len(out["data"]["characters"]))
    text = json.dumps(out, ensure_ascii=False)
    leaks = [k for k in keys if k not in swap.values() and len(k) >= 4 and k in text]
    armory_json = json.dumps(out["builds"].get("armory", {}), ensure_ascii=False)
    leaks += [n for n in armory_src if n not in ARMORY_NAMES and f'"{n}"' in armory_json]
    if leaks:
        raise SystemExit(f"refusing to write: source names still present: {leaks[:5]}")
    return out


# Character details only characters logged in with a recent iasync have (crafting, scribing, profile, currencies).
DETAILS = ("level", "cp", "title", "zone", "ava_rank", "ava_rank_name", "riding", "guilds", "currencies",
           "research", "motifs", "recipes", "scribing")


def fill_in(out: dict) -> None:
    """Every demo character gets every section: drop characters with no equipped gear, and lend the fullest
    character's details and Wizards Wardrobe setups to the others (real data, shared across characters)."""
    data, chars = out["data"], out["data"]["characters"]
    geared = {l["location_key"] for i in data["items"] for l in i["locations"] if l["location_type"] == "character" and l["bag_id"] == 0}
    for cid in [c for c in chars if c not in geared]:
        del chars[cid]
        out["builds"]["builds"] = [b for b in out["builds"]["builds"] if b["char_id"] != cid]
        out["ww"]["builds"].pop(cid, None)
        out["builds"].get("armory", {}).pop(cid, None)
        out["achievements"].get("items_by_char", {}).pop(cid, None)
        out["achievements"]["chars"] = [c for c in out["achievements"].get("chars", []) if c.get("id") != cid]
        for i in data["items"]:
            i["locations"] = [l for l in i["locations"] if not (l["location_type"] == "character" and l["location_key"] == cid)]
            i["total_quantity"] = sum(l["quantity"] for l in i["locations"])
        data["items"] = [i for i in data["items"] if i["locations"]]
    donors = [c for c in chars.values() if c.get("level")]
    for n, c in enumerate(c for c in chars.values() if not c.get("level")):
        if donors:
            c.update({k: donors[n % len(donors)][k] for k in DETAILS if k in donors[n % len(donors)]})
    ww_donor = next(iter(out["ww"]["builds"].values()), None)
    armory = out["builds"].setdefault("armory", {})
    # Lent Armory builds aren't what the borrower wears, so none of them is "equipped".
    armory_donor = [dict(b, active=False, worn=0) for b in next(iter(armory.values()), [])]
    for cid in chars:
        if ww_donor and cid not in out["ww"]["builds"]:
            out["ww"]["builds"][cid] = ww_donor
        if armory_donor and cid not in armory:
            armory[cid] = armory_donor


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out = build(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(gzip.compress(json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode(), 9))
    d = out["data"]
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size // 1024} KB, {len(d['characters'])} characters, "
          f"{len(d['items'])} items, {len(out['stickerbook'].get('sets', []))} sets, "
          f"{len(out['stickerbook'].get('collectibles', {}).get('items', []))} collectibles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
