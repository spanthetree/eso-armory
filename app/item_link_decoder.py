"""Decode ESO item link fields into human-readable metadata.

ESO item link format (21 fields confirmed from real data):
  |H1:item:F0:F1:F2:F3:F4:F5:F6:F7:...F14:F15:F16:F17:F18:F19:F20|h[name]|h

Key fields (0-indexed after "item:"):
  [0]  item_id
  [2]  level requirement (0 or 50 for endgame items)
  [3]  enchant_id (0 = no enchant)
  [6]  trait_id for ALL traited items; when [14] bit11=transmuted this is the NEW trait
  [14] flags: bit0=bound (mirrors [17]), bit8=stolen, bit11=transmuted
  [15] style_id
  [16] crafted (0/1)
  [17] bound (0/1)
  [19] sell_value (gold; capped at 10000 for most endgame items)
"""
import re

_FIELDS_RE = re.compile(r'\|H\d+:item:([\d:]+)\|')

TRAIT_NAMES = {
    0: None,
    # Weapon traits (1-10, 26=Nirnhoned)
    1: "Powered",     2: "Charged",     3: "Precise",
    4: "Infused",     5: "Defending",   6: "Training",
    7: "Sharpened",   8: "Decisive",    9: "Intricate",
    10: "Ornate",     26: "Nirnhoned",
    # Armor traits (11-20, 25=Nirnhoned)
    11: "Sturdy",         12: "Impenetrable", 13: "Reinforced",
    14: "Well-Fitted",    15: "Training",     16: "Infused",
    17: "Prosperous",     18: "Divines",      19: "Ornate",
    20: "Intricate",      25: "Nirnhoned",
    # Jewelry traits (21-24, 27-33; Summerset+)
    21: "Healthy",    22: "Arcane",       23: "Robust",
    24: "Ornate",     27: "Intricate",    28: "Swift",
    29: "Harmony",    30: "Triune",       31: "Bloodthirsty",
    32: "Protective", 33: "Infused",
    # PvP / newer jewelry traits
    52: "Quickened",  53: "Prolific",     54: "Focused",
    55: "Shattering", 56: "Aggressive",   57: "Soothing",
    58: "Augmented",  59: "Bolstered",    60: "Vigorous",
}

# ITEMSTYLE_* constants from ESO client API
STYLE_NAMES = {
    0: None,
    # Racial styles (base game)
    1: "Breton",       2: "Redguard",    3: "High Elf",
    4: "Dark Elf",     5: "Nord",        6: "Argonian",
    7: "Khajiit",      8: "Orc",         9: "Wood Elf",
    10: "Imperial",
    # Classic non-racial
    11: "Daedric",     12: "Ancient Elf", 13: "Barbaric",
    14: "Primal",      15: "Dwemer",      16: "Reach",
    17: "Akaviri",     18: "Soul Shriven",
    19: "Trinimac",    20: "Malacath",
    # Orsinium / Justice / Imperial City
    21: "Dark Brotherhood", 22: "Thieves Guild", 23: "Outlaw",
    24: "Xivkyn",
    # Clockwork City
    25: "Clockwork",   26: "Apostle",    27: "Ebonshadow",
    # Morrowind
    28: "Hlaalu",      29: "Redoran",    30: "Telvanni",
    31: "Buoyant Armiger", 32: "Morag Tong",
    # Shadows of the Hist
    33: "Silken Ring", 34: "Mazzatun",
    # Holiday
    35: "Grim Harlequin",
    # Summerset
    36: "Glass",       37: "Abah's Watch", 38: "Assassins League",
    # Murkmire
    39: "Elder Argonian", 40: "Dro-m'Athra",
    # Elsweyr
    41: "Dragon Bone", 42: "New Moon Priest", 43: "Sunspire",
    44: "Pellitine",   45: "Coldsnap Goblin",  46: "Sea Giant",
    # Greymoor
    47: "Ancestral Nord", 48: "Skinchanger",   49: "Ancestral Breton",
    50: "Greymoor Deep",
    # Markarth
    51: "Ancestral Reach", 52: "Arkthzand",
    # Blackwood
    53: "Ra Gada",     54: "Order of the Hour",
    # Deadlands
    55: "Waking Flame", 56: "Steadfast Society",
    57: "Bloodcrown",  58: "Fargrave Prisoner",
    # High Isle
    59: "Ascending Tide", 60: "Crimson Oath",
    61: "Ancestral High Elf",
    # Necrom
    62: "Ancestral Dark Elf", 63: "Telvanni Peninsula",
    64: "Scribes of Fate",    65: "Annihilarch's",
    # Gold Road
    66: "Recollection", 67: "Gold Road",
}

_FLAG_STOLEN = 1 << 8
_FLAG_TRANSMUTED = 1 << 11


def decode(link_str: str) -> dict:
    """Return decoded metadata from an ESO item link string.

    Returns an empty dict if the string is not a valid item link.
    """
    m = _FIELDS_RE.search(link_str)
    if not m:
        return {}

    raw = m.group(1).split(":")
    if len(raw) < 18:
        return {}

    try:
        p = [int(x) for x in raw]
    except ValueError:
        return {}

    enchant_id = p[3]
    trait_id = p[6]
    flags = p[14]
    style_id = p[15]
    is_crafted = p[16] == 1
    is_bound = p[17] == 1
    sell_value = p[19] if len(p) > 19 else 0

    is_transmuted = bool(flags & _FLAG_TRANSMUTED)
    is_stolen = bool(flags & _FLAG_STOLEN)

    trait_name = TRAIT_NAMES.get(trait_id, f"Trait {trait_id}" if trait_id else None)
    style_name = STYLE_NAMES.get(style_id, f"Style {style_id}" if style_id else None)

    return {
        "enchant_id": enchant_id,
        "is_enchanted": enchant_id != 0,
        "trait_id": trait_id,
        "trait_name": trait_name,
        "is_transmuted": is_transmuted,
        "style_id": style_id,
        "style_name": style_name,
        "is_crafted": is_crafted,
        "is_bound": is_bound,
        "is_stolen": is_stolen,
        "sell_value": sell_value,
    }
