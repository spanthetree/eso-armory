"""Name-based enrichment for ESO items (weapon subtype, armor weight hints).

ESO item links don't encode weapon type or armor weight — those require external
lookups. This module provides fast name-based heuristics for the most common cases.
"""

# Ordered so longer / more-specific substrings are checked before shorter ones.
_WEAPON_KEYWORDS = [
    # Two-handed first (must precede single-handed overlaps)
    ("greatsword",   "Greatsword"),
    ("battle axe",   "Battle Axe"),
    ("great axe",    "Battle Axe"),
    ("maul",         "Maul"),
    ("two-handed",   "Two-Handed"),
    # Staves
    ("inferno staff",  "Inferno Staff"),
    ("lightning staff","Lightning Staff"),
    ("ice staff",      "Ice Staff"),
    ("frost staff",    "Ice Staff"),
    ("restoration staff", "Restoration Staff"),
    ("healing staff",  "Restoration Staff"),
    ("destro staff",   "Destruction Staff"),
    ("resto staff",    "Restoration Staff"),
    ("staff",          "Staff"),
    # Ranged
    ("bow",            "Bow"),
    # One-handed
    ("dagger",         "Dagger"),
    ("sword",          "Sword"),
    ("axe",            "Axe"),
    ("mace",           "Mace"),
    ("hammer",         "Mace"),
    # Shield (filter_type 2 but often named alongside weapons)
    ("shield",         "Shield"),
]


def enrich(item_name: str, filter_type: int) -> dict:
    """Return extra fields inferred from the item name.

    Args:
        item_name:   Display name of the item.
        filter_type: ESO filter type (1=Weapons, 2=Armor, 25=Jewelry, …).

    Returns:
        dict with any keys that could be determined; empty dict if nothing found.
    """
    result = {}
    name_lower = item_name.lower()

    if filter_type == 1:  # Weapons
        for kw, label in _WEAPON_KEYWORDS:
            if kw in name_lower:
                result["weapon_type"] = label
                break

    return result
