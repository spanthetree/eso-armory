"""Transform raw iasync_data dict into clean JSON API models."""

import re
import time

from item_link_decoder import decode as decode_link

QUALITY_NAMES = {
    0: "Trash", 1: "Normal", 2: "Fine", 3: "Superior",
    4: "Epic", 5: "Legendary", 6: "Mythic",
}
QUALITY_COLORS = {
    0: "#8b8b8b", 1: "#cccccc", 2: "#2dc50e", 3: "#5199ff",
    4: "#a02ee4", 5: "#c29300", 6: "#e87800",
}
FILTER_TYPE_NAMES = {
    1: "Weapons", 2: "Armor", 3: "Consumables", 4: "Materials",
    5: "Miscellaneous", 6: "Glyphs", 21: "Furnishings", 25: "Jewelry",
}
# EQUIPMENT_FILTER_TYPE_*: what GetEquipmentFilterTypeForItemSetCollectionSlot really returns
EQUIPMENT_FILTER_NAMES = {
    1: "Light", 2: "Medium", 3: "Heavy", 4: "Necklace", 5: "Ring", 6: "One-Handed",
    7: "Shield", 8: "Two-Handed", 9: "Destruction Staff", 10: "Restoration Staff", 11: "Bow",
}
FILTER_TYPE_ICONS = {
    1: "⚔", 2: "🛡", 3: "⚗", 4: "🔩",
    5: "📦", 6: "✨", 21: "🏛", 25: "💍",
}
EQUIP_SLOTS = {
    0: "Head", 1: "Neck", 2: "Chest", 3: "Shoulders",
    4: "Main Hand", 5: "Off Hand", 6: "Waist", 8: "Legs",
    9: "Feet", 10: "Costume", 11: "Ring 1", 12: "Ring 2",
    13: "Poison", 14: "Backup Poison", 16: "Gloves",
    20: "Backup Main", 21: "Backup Off",
}

# ESO bag IDs referenced by iasync
_BAG_VIRTUAL         = 5   # craft bag
_BAG_SUBSCRIBER_BANK = 6   # ESO Plus overflow bank
_HOUSE_BAG_START     = 7   # BAG_HOUSE_CONTAINER_1

_ITEM_LINK_RE       = re.compile(r'\|H\d+:item:(\d+):')
_ITEM_LINK_FIELDS_RE = re.compile(r'\|H\d+:item:([\d:]+)\|')
_ITEM_LINK_NAME_RE  = re.compile(r'\|h\[([^\]]+)\]\|h')
_LOCALE_SUFFIX_RE   = re.compile(r'\^[a-z]+$', re.IGNORECASE)


def _strip_locale(name: str) -> str:
    return _LOCALE_SUFFIX_RE.sub("", name)


def _parse_link_level(link: str) -> int:
    m = _ITEM_LINK_FIELDS_RE.search(link)
    if not m:
        return 0
    parts = m.group(1).split(":")
    if len(parts) > 2:
        try:
            return int(parts[2])
        except ValueError:
            pass
    return 0


def _process_characters(chars_raw: dict) -> dict:
    characters = {}
    for char_id, c in chars_raw.items():
        characters[char_id] = {
            "id":         char_id,
            "name":       c.get("name", ""),
            "race":       c.get("race", ""),
            "class":      c.get("class", ""),
            "alliance":   c.get("alliance", ""),
            "gender":     c.get("gender", ""),  # iasync >= 1.4.0; "" for older SavedVariables
            "gold":       int(c.get("gold", 0)),
            "ap":         int(c.get("ap", 0)),
            "tv":         int(c.get("tv", 0)),
            "wv":         int(c.get("wv", 0)),
            "space_used": int(c.get("spaceUsed", 0)),
            "space_max":  int(c.get("spaceMax", 0)),
        }
    return characters


def _new_item_entry(link: str, iid: int | None, item_data: dict) -> dict:
    quality     = int(item_data.get("quality", 1))
    filter_type = int(item_data.get("filterType", 5))
    decoded     = decode_link(link)
    # iasync captures trait/enchant via ESO's GetItemTrait/GetItemLinkInfo APIs,
    # which are more reliable than link-field decoding for armor traits.
    trait_id    = int(item_data.get("traitType", 0)) or decoded.get("trait_id", 0)
    trait_name  = item_data.get("traitName") or decoded.get("trait_name")
    enchant_id  = decoded.get("enchant_id", 0) or int(item_data.get("enchantId", 0))
    enchant_name = item_data.get("enchantName") or ""
    is_enchanted = bool(enchant_name) or decoded.get("is_enchanted", False)
    return {
        "key":              link,
        "item_id":          iid,
        "name":             _strip_locale(item_data.get("name", "Unknown")),
        "quality":          quality,
        "quality_name":     QUALITY_NAMES.get(quality, "Unknown"),
        "quality_color":    QUALITY_COLORS.get(quality, "#cccccc"),
        "filter_type":      filter_type,
        "filter_type_name": FILTER_TYPE_NAMES.get(filter_type, "Miscellaneous"),
        "filter_type_icon": FILTER_TYPE_ICONS.get(filter_type, "📦"),
        "level":            _parse_link_level(link),
        "total_quantity":   0,
        "locations":        [],
        "trait_id":         trait_id,
        "trait_name":       trait_name,
        "is_transmuted":    decoded.get("is_transmuted", False),
        "style_id":         decoded.get("style_id", 0),
        "style_name":       decoded.get("style_name"),
        "is_crafted":       decoded.get("is_crafted", False),
        "is_bound":         decoded.get("is_bound", False),
        "is_stolen":        decoded.get("is_stolen", False),
        "is_enchanted":     is_enchanted,
        "enchant_id":       enchant_id,
        "enchant_name":     enchant_name,
        "set_id":           int(item_data.get("setId", 0)),
        "set_name":         item_data.get("setName") or "",
        "sell_value":       decoded.get("sell_value", 0),
        "weapon_type":      item_data.get("weaponType") or None,
        "armor_type":       item_data.get("armorType") or None,
    }


def _add_slot(item_map: dict, item_data: dict, slot, loc_type: str, loc_key: str,
              loc_label: str, bag_id: int, bag_label: str):
    link = item_data.get("link", "")
    if not link:
        return
    m = _ITEM_LINK_RE.search(link)
    iid = int(m.group(1)) if m else None
    qty = int(item_data.get("qty", 1))

    if link not in item_map:
        item_map[link] = _new_item_entry(link, iid, item_data)

    item_map[link]["total_quantity"] += qty
    existing = next((l for l in item_map[link]["locations"]
                     if l["location_key"] == loc_key and l["bag_id"] == bag_id), None)
    if existing:
        existing["quantity"] += qty
        existing["bag_slots"][str(slot)] = qty
    else:
        item_map[link]["locations"].append({
            "location_key":   loc_key,
            "location_type":  loc_type,
            "location_label": loc_label,
            "bag_id":         bag_id,
            "bag_label":      bag_label,
            "quantity":       qty,
            "bag_slots":      {str(slot): qty},
        })


def _collect_char_items(item_map: dict, chars_raw: dict, characters: dict):
    # Character bags (bag 0 = equipped, bag 1 = backpack)
    # location_key must be char_id so the frontend's charMaps lookup works.
    for char_id, c in chars_raw.items():
        char_name = characters[char_id]["name"]
        for bag_id_raw, bag in c.get("bags", {}).items():
            bag_id    = int(bag_id_raw)
            bag_label = "Equipped" if bag_id == 0 else "Inventory"
            for slot, item_data in bag.items():
                _add_slot(item_map, item_data, slot, "character", char_id, char_name, bag_id, bag_label)


def _collect_bank_items(item_map: dict, bank_raw: dict):
    for bag_id_raw, bag in bank_raw.get("bags", {}).items():
        bag_id = int(bag_id_raw)
        if bag_id == _BAG_VIRTUAL:
            loc_type, loc_label, bag_label = "craftbag", "Craft Bag", "Craft Bag"
        elif bag_id == _BAG_SUBSCRIBER_BANK:
            loc_type, loc_label, bag_label = "bank", "Bank", "ESO Plus Bank"
        else:
            loc_type, loc_label, bag_label = "bank", "Bank", "Bank"
        for slot, item_data in bag.items():
            _add_slot(item_map, item_data, slot, loc_type, loc_label, loc_label, bag_id, bag_label)


def _collect_house_chests(item_map: dict, houses_raw: dict) -> dict:
    # Storage chests (BAG_HOUSE_BANK_*) are account-wide: iasync saves the same chests under every house it
    # scanned. Use one copy per chest, the newest non-empty one (an empty copy only when there is no other).
    best: dict[int, tuple] = {}
    for house_data in houses_raw.values():
        if not isinstance(house_data, dict):
            continue
        for chest_id_raw, chest in house_data.get("chests", {}).items():
            if not isinstance(chest, dict):
                continue
            chest_id = int(chest_id_raw)
            rank = (bool(chest.get("slots")), int(chest.get("lastUpdate") or house_data.get("lastUpdate") or 0))
            if chest_id not in best or rank > best[chest_id][0]:
                best[chest_id] = (rank, chest)

    house_chests: dict[str, dict] = {}
    for chest_id, (_, chest) in sorted(best.items()):
        chest_num = chest.get("chestNum", chest_id - _HOUSE_BAG_START + 1)
        label     = f"House Chest {chest_num}"
        house_chests[str(chest_id)] = {
            "bag_id":   chest_id,
            "label":    label,
            "capacity": int(chest.get("capacity", 0)),
        }
        for slot, item_data in chest.get("slots", {}).items():
            _add_slot(item_map, item_data, slot, "house_chest", label, label, chest_id, label)
    return house_chests


def _collect_guild_bank_items(item_map: dict, guild_banks_raw: dict):
    for guild_name, guild in guild_banks_raw.items():
        slots = guild.get("slots", guild) if isinstance(guild, dict) else {}
        if not isinstance(slots, dict):
            continue
        label = str(guild_name)
        for slot, item_data in slots.items():
            if isinstance(item_data, dict):
                _add_slot(item_map, item_data, slot, "guild_bank", label, label, 3, "Guild Bank")


def process_iasync(raw: dict, server: str = "NA") -> dict:
    """Build the /api/data response from iasync_data."""
    t0 = time.monotonic()

    account_name = raw.get("accountName") or next((k for k in raw if isinstance(k, str) and k.startswith("@")), None)
    chars_raw  = raw.get("chars", {})
    bank_raw   = raw.get("bank", {})
    houses_raw = raw.get("houses", {})

    characters = _process_characters(chars_raw)

    bank = {
        "gold": int(bank_raw.get("gold", 0)),
        "ap":   int(bank_raw.get("ap", 0)),
        "tv":   int(bank_raw.get("tv", 0)),
        "wv":   int(bank_raw.get("wv", 0)),
        "space_used": 0,
        "space_max":  0,
    }

    # Items: aggregate by link across all storage locations
    item_map: dict[str, dict] = {}
    _collect_char_items(item_map, chars_raw, characters)
    _collect_bank_items(item_map, bank_raw)
    house_chests = _collect_house_chests(item_map, houses_raw)
    _collect_guild_bank_items(item_map, raw.get("guildBanks", {}))

    items = list(item_map.values())
    parse_ms = int((time.monotonic() - t0) * 1000)

    return {
        "meta": {
            "account":         account_name,
            "server":          server,
            "item_count":      len(items),
            "character_count": len(characters),
            "parse_ms":        parse_ms,
            "last_modified":   raw.get("lastUpdate", 0),
        },
        "characters":   characters,
        "bank":         bank,
        "house_chests": house_chests,
        "items":        items,
        "uiColors":     ui_colors(raw),
    }


def process_ww_builds(raw: dict) -> dict:
    """Process WizardsWardrobeSV into per-character saved build lists."""
    default = raw.get("Default", {})
    account_data: dict = {}
    for k, v in default.items():
        if isinstance(k, str) and k.startswith("@"):
            account_data = v
            break

    builds_by_char: dict[str, list] = {}

    for char_id_raw, char_data in account_data.items():
        if not isinstance(char_data, dict):
            continue
        char_id = str(char_id_raw)
        setups_root = char_data.get("setups", {})
        pages_root  = char_data.get("pages", {})
        char_builds: list[dict] = []

        for zone_tag, zone_data in setups_root.items():
            if not isinstance(zone_data, dict):
                continue
            for page_num, page_data in zone_data.items():
                if not isinstance(page_data, dict):
                    continue
                page_info = ((pages_root.get(zone_tag) or {}).get(page_num)) or {}
                page_name = page_info.get("name", f"Page {page_num}")

                for setup_num, setup in page_data.items():
                    if not isinstance(setup, dict):
                        continue
                    name = setup.get("name", "")
                    if not name or name.lower() == "empty":
                        continue

                    # Gear: sorted by slot
                    gear: list[dict] = []
                    for slot_raw, slot_data in setup.get("gear", {}).items():
                        if not isinstance(slot_data, dict):
                            continue
                        link = slot_data.get("link") or ""
                        if not link:
                            continue
                        try:
                            slot = int(slot_raw)
                        except (TypeError, ValueError):
                            continue
                        decoded = decode_link(link)
                        m  = _ITEM_LINK_RE.search(link)
                        nm = _ITEM_LINK_NAME_RE.search(link)
                        gear.append({
                            "slot":          slot,
                            "slot_name":     EQUIP_SLOTS.get(slot, f"Slot {slot}"),
                            "link":          link,
                            "item_id":       int(m.group(1)) if m else None,
                            "link_name":     _strip_locale(nm.group(1)) if nm else "",
                            "trait_id":      decoded.get("trait_id", 0),
                            "trait_name":    decoded.get("trait_name"),
                            "is_transmuted": decoded.get("is_transmuted", False),
                            "style_id":      decoded.get("style_id", 0),
                            "style_name":    decoded.get("style_name"),
                            "is_crafted":    decoded.get("is_crafted", False),
                            "is_bound":      decoded.get("is_bound", False),
                            "is_enchanted":  decoded.get("is_enchanted", False),
                            "enchant_id":    decoded.get("enchant_id", 0),
                            "enchant_name":  "",
                            "set_name":      "",
                            "sell_value":    decoded.get("sell_value", 0),
                        })
                    gear.sort(key=lambda g: g["slot"])

                    # Skills: WW bar 0=primary, 1=backup
                    skills: dict[str, dict] = {}
                    for bar_raw, bar_data in setup.get("skills", {}).items():
                        if not isinstance(bar_data, dict):
                            continue
                        bar_key = "primary" if int(bar_raw) == 0 else "backup"
                        skills[bar_key] = {
                            str(s): aid for s, aid in bar_data.items()
                            if aid and int(aid) > 0
                        }

                    # CP: {str(1-12): abilityId}
                    cp = {
                        str(k): v for k, v in setup.get("cp", {}).items()
                        if v and int(v) > 0
                    }

                    # Food
                    food_data = setup.get("food") or {}
                    food_link = food_data.get("link") or ""
                    food = None
                    if food_link:
                        fm  = _ITEM_LINK_RE.search(food_link)
                        fnm = _ITEM_LINK_NAME_RE.search(food_link)
                        food = {
                            "link":      food_link,
                            "item_id":   int(fm.group(1)) if fm else None,
                            "link_name": _strip_locale(fnm.group(1)) if fnm else "",
                        }

                    char_builds.append({
                        "zone":      zone_tag,
                        "page":      page_num,
                        "page_name": page_name,
                        "setup":     setup_num,
                        "name":      name,
                        "gear":      gear,
                        "skills":    skills,
                        "cp":        cp,
                        "food":      food,
                    })

        if char_builds:
            builds_by_char[char_id] = char_builds

    return {"builds": builds_by_char}


_REWARD_FIELDS = ("type", "name", "id", "icon", "patronId", "cardIndex")
_REWARD_TYPES = ("title", "dye", "collectible", "item", "tribute_card_upgrade")
_HEX6 = re.compile(r"^[0-9a-fA-F]{6}$")


def _parse_rewards(raw) -> list[dict]:
    """Achievement rewards (title, dye, collectible, item, Tales of Tribute card upgrade) as iasync records them; Lua arrays may arrive as dicts."""
    items = raw.values() if isinstance(raw, dict) else raw if isinstance(raw, list) else []
    out = []
    for r in items:
        if isinstance(r, dict) and r.get("type") in _REWARD_TYPES:
            out.append({k: r[k] for k in _REWARD_FIELDS if r.get(k) not in (None, "")})
    return out


def ui_colors(raw: dict) -> dict:
    """In-game interface colours (iasync 1.7.0 ``uiColors``), only well-formed ``rrggbb`` values."""
    src = raw.get("uiColors") or {}
    return {str(k): v.lower() for k, v in src.items() if isinstance(v, str) and _HEX6.match(v)} if isinstance(src, dict) else {}


def process_iasync_achievements(raw: dict) -> dict:
    """Parse account-level category summaries and per-character individual achievements."""
    achiev_raw = raw.get("achievements", {})

    # ── Category summaries (account-level) ──────────────────────────────────────
    cats_raw = achiev_raw.get("categories", {})
    categories = []
    for idx in sorted(cats_raw.keys(), key=lambda x: (int(x) if isinstance(x, int) else x)):
        cat = cats_raw[idx]
        subcats_raw = cat.get("subcats", {})
        subcats = []
        for sidx in sorted(subcats_raw.keys(), key=lambda x: (int(x) if isinstance(x, int) else x)):
            s = subcats_raw[sidx]
            subcats.append({
                "name":           s.get("name", ""),
                "total":          int(s.get("total", 0)),
                "complete":       int(s.get("complete", 0)),
                "totalPts":       int(s.get("totalPts", 0)),
                "earnedPts":      int(s.get("earnedPts", 0)),
                "numAchievements": int(s.get("numAchievements", 0)),
                "hidesUnearned":  bool(s.get("hidesUnearned", False)),
            })
        categories.append({
            "name":           cat.get("name", ""),
            "icon":           cat.get("icon") or "",
            "total":          int(cat.get("total", 0)),
            "complete":       int(cat.get("complete", 0)),
            "totalPts":       int(cat.get("totalPts", 0)),
            "earnedPts":      int(cat.get("earnedPts", 0)),
            "numAchievements": int(cat.get("numAchievements", 0)),
            "hidesUnearned":  bool(cat.get("hidesUnearned", False)),
            "subcats":        subcats,
        })

    # ── Individual achievements, kept per-character ──────────────────────────────
    chars_raw = raw.get("chars", {})
    items_by_char: dict[str, list] = {}
    chars_with_achiev: list[dict] = []
    seen_ids: set[int] = set()
    all_achiev: list[dict] = []
    recent_candidates: list[tuple[int, dict]] = []

    def _parse_achiev(a: dict, aid: int) -> dict:
        criteria = []
        for cidx in sorted(a.get("criteria", {}).keys(),
                            key=lambda x: (int(x) if isinstance(x, int) else x)):
            c = a["criteria"][cidx]
            if isinstance(c, dict):
                criteria.append({
                    "desc": c.get("desc", ""),
                    "cur":  int(c.get("cur", 0)),
                    "req":  int(c.get("req", 1)),
                })
        return {
            "id":                  aid,
            "name":                a.get("name", ""),
            "desc":                a.get("desc", ""),
            "cat":                 a.get("cat", ""),
            "subcat":              a.get("subcat", ""),
            "points":              int(a.get("points", 0)),
            "icon":                a.get("icon", ""),
            "complete":            bool(a.get("complete", False)),
            "completionDate":      a.get("completionDate", ""),
            "completedByCharName": a.get("completedByCharName", ""),
            "criteria":            criteria,
            "rewards":             _parse_rewards(a.get("rewards")),
            "lineBaseId":          int(a.get("lineBaseId") or aid),
            "linePreviousId":      int(a.get("linePreviousId") or 0),
            "lineNextId":          int(a.get("lineNextId") or 0),
        }

    account_items: list[dict] = []
    account_raw = achiev_raw.get("account", {})
    for achiev_id, a in account_raw.items():
        if not isinstance(a, dict):
            continue
        aid = int(achiev_id)
        item = _parse_achiev(a, aid)
        account_items.append(item)
        if item["complete"]:
            recent_candidates.append((int(a.get("completionTimestamp", 0)), item))
        if aid not in seen_ids:
            seen_ids.add(aid)
            all_achiev.append(item)

    for char_id, char_data in chars_raw.items():
        if not isinstance(char_data, dict):
            continue
        char_achievs = char_data.get("achievements", {})
        if not char_achievs:
            continue
        char_items = []
        for achiev_id, a in char_achievs.items():
            if not isinstance(a, dict):
                continue
            aid = int(achiev_id)
            item = _parse_achiev(a, aid)
            char_items.append(item)
            if item["complete"]:
                recent_candidates.append((int(a.get("completionTimestamp", 0)), item))
            if aid not in seen_ids:
                seen_ids.add(aid)
                all_achiev.append(item)
        if char_items:
            items_by_char[str(char_id)] = char_items
            chars_with_achiev.append({
                "id":   str(char_id),
                "name": char_data.get("name", str(char_id)),
            })

    # Recent = completed across all chars, newest first, one entry per achievement (timeline)
    recent = []
    recent_ids: set[int] = set()
    for ts, a in sorted(recent_candidates, key=lambda x: x[0], reverse=True):
        if a["id"] not in recent_ids:
            recent_ids.add(a["id"])
            recent.append((ts, a))
        if len(recent) >= 50:
            break

    return {
        "totalPts":      int(achiev_raw.get("totalPts", 0)),
        "earnedPts":     int(achiev_raw.get("earnedPts", 0)),
        "lastUpdate":    int(achiev_raw.get("lastUpdate", 0)),
        "categories":    categories,
        "account_items": account_items,
        "items_by_char": items_by_char,
        "chars":         chars_with_achiev,
        "recent":        [a for _, a in recent],
        "uiColors":      ui_colors(raw),
    }


def process_iasync_builds(raw: dict) -> dict:
    """Build the /api/builds response from iasync_data."""
    chars_raw = raw.get("chars", {})
    builds = []

    for char_id, c in chars_raw.items():
        char_name = c.get("name", "")

        # Gear from equipped bag (bag 0 = BAG_WORN)
        gear = []
        for slot_raw, item_data in c.get("bags", {}).get(0, {}).items():
            link = item_data.get("link", "")
            if not link:
                continue
            slot    = int(slot_raw)
            m       = _ITEM_LINK_RE.search(link)
            item_id = int(m.group(1)) if m else None
            nm      = _ITEM_LINK_NAME_RE.search(link)
            decoded = decode_link(link)
            quality = int(item_data.get("quality", 1))
            filter_type = int(item_data.get("filterType", 5))
            trait_id   = int(item_data.get("traitType", 0)) or decoded.get("trait_id", 0)
            trait_name = item_data.get("traitName") or decoded.get("trait_name")
            enchant_id = decoded.get("enchant_id", 0) or int(item_data.get("enchantId", 0))
            gear.append({
                "slot":           slot,
                "slot_name":      EQUIP_SLOTS.get(slot, f"Slot {slot}"),
                "link":           link,
                "item_id":        item_id,
                "link_name":      nm.group(1) if nm else item_data.get("name"),
                "quality":        quality,
                "quality_name":   QUALITY_NAMES.get(quality, "Unknown"),
                "quality_color":  QUALITY_COLORS.get(quality, "#cccccc"),
                "filter_type":    filter_type,
                "filter_type_name": FILTER_TYPE_NAMES.get(filter_type, "Miscellaneous"),
                "weapon_type":    item_data.get("weaponType") or None,
                "armor_type":     item_data.get("armorType") or None,
                "level":          _parse_link_level(link),
                "trait_id":       trait_id,
                "trait_name":     trait_name,
                "is_transmuted":  decoded.get("is_transmuted", False),
                "style_id":       decoded.get("style_id", 0),
                "style_name":     decoded.get("style_name"),
                "is_crafted":     decoded.get("is_crafted", False),
                "is_bound":       decoded.get("is_bound", False),
                "is_enchanted":   bool(item_data.get("enchantName")) or decoded.get("is_enchanted", False),
                "enchant_id":     enchant_id,
                "enchant_name":   item_data.get("enchantName") or "",
                "set_id":         int(item_data.get("setId", 0)),
                "set_name":       item_data.get("setName") or "",
            })
        gear.sort(key=lambda g: g["slot"])

        # Skills: primary/backup bars; keyed by string slot number
        build_bars = c.get("build_bars", {})
        skills = {
            "primary":   {str(k): v for k, v in build_bars.get("primary",   {}).items()},
            "backup":    {str(k): v for k, v in build_bars.get("backup",    {}).items()},
            "werewolf":  {str(k): v for k, v in build_bars.get("werewolf",  {}).items()},
        }

        # CP: flat slot → abilityId map
        build_cp = c.get("build_cp", {})
        cp = {str(k): v for k, v in build_cp.get("slots", {}).items()}

        # Mundus: stored as {1: "The Lady"}, pull values
        build_mundus = c.get("build_mundus") or {}
        mundus = list(build_mundus.values()) if isinstance(build_mundus, dict) else list(build_mundus)

        builds.append({
            "char_id":    char_id,
            "char_name":  char_name,
            "race":       c.get("race", ""),
            "class":      c.get("class", ""),
            "alliance":   c.get("alliance", ""),
            "gear":       gear,
            "skills":     skills,
            "cp":         cp,
            "cp_earned":  build_cp.get("earned", 0),
            "attributes": c.get("build_attributes", {}),
            "pools":      c.get("build_pools", {}),  # max health/magicka/stamina, iasync >= 1.5.0
            "mundus":     mundus,
        })

    # Merge ability/CP names from all characters (each char stores its own on login)
    # plus legacy top-level dicts for backward compatibility.
    ability_names: dict[str, str] = {}
    cp_names: dict[str, str] = {}
    for key in ("abilityNames", "$abilityNames"):
        ability_names.update({str(k): v for k, v in raw.get(key, {}).items()})
    for key in ("cpNames", "$cpNames"):
        cp_names.update({str(k): v for k, v in raw.get(key, {}).items()})
    for c in chars_raw.values():
        if isinstance(c, dict):
            ability_names.update({str(k): v for k, v in c.get("abilityNames", {}).items()})
            cp_names.update({str(k): v for k, v in c.get("cpNames", {}).items()})

    return {
        "builds":       builds,
        "abilityNames": ability_names,
        "cpNames":      cp_names,
    }


def _indexed(table) -> list[tuple[int, dict]]:
    """Lua array-like tables arrive as dicts with int or str keys (in any order) or as lists; sorted (index, row)."""
    pairs = table.items() if isinstance(table, dict) else enumerate(table or [], 1)
    out = []
    for k, v in pairs:
        try:
            out.append((int(k), v))
        except (TypeError, ValueError):
            continue
    return sorted((kv for kv in out if isinstance(kv[1], dict)), key=lambda kv: kv[0])


def process_iasync_collectibles(raw: dict) -> dict:
    """iasync 1.9.0 ``collectibles``: the in-game Collections book. ``specialization`` picks the book tab
    (0 Collectibles, 1 Stories, 2 Housing, 3 Outfit Styles, 4 Tribute Patrons); items point at their
    category by ``cat`` and ``sub`` (0 = directly under the category)."""
    src = raw.get("collectibles") or {}
    if not isinstance(src, dict):
        src = {}
    categories = []
    for idx, c in _indexed(src.get("categories")):
        categories.append({
            "idx":            idx,
            "name":           str(c.get("name") or ""),
            "icon":           str(c.get("icon") or ""),
            "specialization": int(c.get("specialization") or 0),
            "unlocked":       int(c.get("numUnlocked") or 0),
            "total":          int(c.get("numTotal") or 0),
            "hidesLocked":    bool(c.get("hidesLocked")),
            "subcats": [{
                "idx":      sidx,
                "name":     str(sc.get("name") or ""),
                "icon":     str(sc.get("icon") or ""),
                "unlocked": int(sc.get("numUnlocked") or 0),
                "total":    int(sc.get("numTotal") or 0),
            } for sidx, sc in _indexed(c.get("subcats"))],
        })
    items = []
    for cid, it in _indexed(src.get("items")):
        items.append({
            "id":       cid,
            "name":     str(it.get("name") or ""),
            "icon":     str(it.get("icon") or ""),
            "unlocked": bool(it.get("unlocked")),
            "cat":      int(it.get("cat") or 0),
            "sub":      int(it.get("sub") or 0),
        })
    items.sort(key=lambda i: i["name"].lower())

    # iasync 1.10.0: Tales of Tribute patrons as the in-game tree groups them (category headers by categoryOrder).
    # categoryOrder 0 = not in that tree (early 1.10.0 builds saved those too). collectibleId 0 = everyone has it.
    unlocked_ids = {i["id"] for i in items if i["unlocked"]}
    patrons = []
    for pid, p in _indexed(src.get("patrons")):
        order = int(p.get("categoryOrder") or 0)
        if order <= 0:
            continue
        cid = int(p.get("collectibleId") or 0)
        patrons.append({
            "id":            pid,
            "name":          str(p.get("name") or ""),
            "icon":          str(p.get("icon") or ""),
            "category":      str(p.get("category") or ""),
            "categoryOrder": order,
            "categoryIcon":  str(p.get("categoryIcon") or ""),
            "collectibleId": cid,
            "unlocked":      cid == 0 or cid in unlocked_ids,
        })
    patrons.sort(key=lambda p: (p["categoryOrder"], p["name"].lower()))
    return {"categories": categories, "items": items, "patrons": patrons, "lastUpdate": int(src.get("lastUpdate") or 0)}


def process_iasync_stickerbook(raw: dict) -> dict:
    """Build the /api/stickerbook response from iasync_data.stickerbook."""
    sb_raw   = raw.get("stickerbook", {})
    sets_raw = sb_raw.get("sets", {})

    sets = []
    for set_id, s in sets_raw.items():
        if not isinstance(s, dict):
            continue

        num_collected = int(s.get("numCollected", 0))
        num_total     = int(s.get("numTotal", 0))

        pieces = []
        for pidx in sorted(s.get("pieces", {}).keys(),
                            key=lambda x: int(x) if str(x).isdigit() else 0):
            p = s["pieces"][pidx]
            if not isinstance(p, dict):
                continue
            filter_type = int(p.get("filterType", 0))
            pieces.append({
                "filterType": filter_type,
                "filterName": EQUIPMENT_FILTER_NAMES.get(filter_type, ""),
                "collected":  bool(p.get("collected", False)),
                "name":       p.get("name", ""),
                "icon":       p.get("icon") or "",
                "quality":    int(p.get("quality") or 0),
            })

        sets.append({
            "setId":        int(set_id) if str(set_id).isdigit() else set_id,
            "name":         s.get("name", ""),
            "category":     s.get("category", ""),
            "subcategory":  s.get("subcategory", ""),
            "numCollected": num_collected,
            "numTotal":     num_total,
            "complete":     num_total > 0 and num_collected >= num_total,
            "pieces":       pieces,
            "reconCost":    int(s["reconCost"]) if isinstance(s.get("reconCost"), (int, float)) else None,
            "reconCurrency": int(s["reconCurrency"]) if isinstance(s.get("reconCurrency"), (int, float)) else None,
        })

    sets.sort(key=lambda s: s["name"].lower())

    return {
        "sets":          sets,
        "categoryIcons": {str(k): v for k, v in (sb_raw.get("categoryIcons") or {}).items() if isinstance(v, str)},
        "lastUpdate":    int(sb_raw.get("lastUpdate", 0)),
        "uiColors":      ui_colors(raw),
        "collectibles":  process_iasync_collectibles(raw),
    }
