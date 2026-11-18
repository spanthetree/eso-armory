from __future__ import annotations

import pytest

from data_processor import (
    process_iasync,
    process_iasync_achievements,
    process_iasync_builds,
    process_iasync_stickerbook,
    process_ww_builds,
)
from lua_parser import parse_lua_variable


@pytest.fixture
def raw_iasync(fixtures_dir):
    return parse_lua_variable(str(fixtures_dir / "iasync.lua"), "iasync_data")


@pytest.fixture
def raw_ww(fixtures_dir):
    return parse_lua_variable(str(fixtures_dir / "WizardsWardrobe.lua"), "WizardsWardrobeSV")


@pytest.mark.unit
def test_process_iasync_aggregates_locations(raw_iasync):
    data = process_iasync(raw_iasync, server="NA")
    potion = next(item for item in data["items"] if item["name"] == "Mock Potion")

    assert data["meta"]["account"] == "@test_account"
    assert data["meta"]["character_count"] == 2
    assert potion["total_quantity"] == 10
    assert {loc["location_type"] for loc in potion["locations"]} == {"character", "bank"}


@pytest.mark.unit
def test_process_iasync_passes_gender_with_fallback(raw_iasync):
    chars = process_iasync(raw_iasync)["characters"]

    assert chars["char-a"]["gender"] == "female"
    assert chars["char-b"]["gender"] == ""  # SavedVariables from iasync < 1.4.0


@pytest.mark.unit
def test_process_iasync_labels_storage_locations(raw_iasync):
    data = process_iasync(raw_iasync)
    locations = {
        loc["location_type"]
        for item in data["items"]
        for loc in item["locations"]
    }

    assert {"character", "bank", "craftbag", "house_chest", "guild_bank"} <= locations
    assert data["house_chests"]["7"]["capacity"] == 30
    assert data["house_chests"]["7"]["label"] == "House Chest 1"


def test_house_chests_are_counted_once_across_houses():
    from data_processor import _collect_house_chests

    item = {"link": "|H1:item:5001:0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1:0|h|h", "name": "Box", "qty": 3}
    houses = {  # the same account-wide chest saved under three houses; one copy is stale, one empty
        "1": {"name": "Old", "chests": {"7": {"slots": {"0": dict(item, qty=1)}, "lastUpdate": 100}}},
        "2": {"name": "New", "chests": {"7": {"slots": {"0": item}, "lastUpdate": 300}}},
        "3": {"name": "Visited", "chests": {"7": {"slots": {}, "lastUpdate": 400}}},
    }
    item_map: dict = {}
    chests = _collect_house_chests(item_map, houses)
    (entry,) = item_map.values()
    assert entry["total_quantity"] == 3
    assert [loc["quantity"] for loc in entry["locations"]] == [3]
    assert chests["7"]["label"] == "House Chest 1"


@pytest.mark.unit
def test_process_iasync_builds_uses_equipped_gear_and_names(raw_iasync):
    builds = process_iasync_builds(raw_iasync)
    build = builds["builds"][0]

    assert build["char_id"] == "char-a"
    assert build["gear"][0]["slot_name"] == "Chest"
    assert build["skills"]["primary"]["3"] == 101
    assert builds["abilityNames"]["101"] == "Mock Whip"
    assert builds["cpNames"]["201"] == "Mock Warfare"
    assert build["pools"] == {"health": 21865, "magicka": 41210, "stamina": 12400}
    assert builds["builds"][1]["pools"] == {}  # SavedVariables from iasync < 1.4.0


@pytest.mark.unit
def test_process_achievements_and_stickerbook(raw_iasync):
    achievements = process_iasync_achievements(raw_iasync)
    stickerbook = process_iasync_stickerbook(raw_iasync)

    assert achievements["earnedPts"] == 10
    assert len(achievements["account_items"]) == 1
    assert achievements["items_by_char"]["char-a"][0]["name"] == "Mock Character Achievement"
    assert stickerbook["sets"][0]["name"] == "Mock Set"
    assert stickerbook["sets"][0]["complete"] is False
    pieces = stickerbook["sets"][0]["pieces"]
    assert [p["filterName"] for p in pieces] == ["One-Handed", "Heavy"]
    assert pieces[0]["icon"] == "/esoui/art/icons/gear_mock_1hsword_a.dds"
    assert pieces[1]["icon"] == ""
    assert stickerbook["categoryIcons"] == {"Dungeons": "/esoui/art/collections/collections_categoryicon_dungeons_up.dds"}
    assert achievements["categories"][0]["icon"] == "/esoui/art/treeicons/achievements_indexicon_general_up.dds"
    acct = achievements["account_items"][0]
    assert acct["rewards"] == [{"type": "title", "name": "Mock Title", "id": 7}, {"type": "tribute_card_upgrade", "patronId": 1, "cardIndex": 2}]
    assert (acct["lineBaseId"], acct["linePreviousId"], acct["lineNextId"]) == (8999, 8999, 0)
    assert (stickerbook["sets"][0]["reconCost"], stickerbook["sets"][0]["reconCurrency"]) == (25, 5)
    assert [p["quality"] for p in pieces] == [4, 0]
    assert achievements["uiColors"] == stickerbook["uiColors"] == {"textNormal": "c5c29e"}
    assert process_iasync(raw_iasync)["uiColors"] == {"textNormal": "c5c29e"}


@pytest.mark.unit
def test_process_ww_builds_skips_empty_and_non_integer_gear(raw_ww):
    builds = process_ww_builds(raw_ww)
    char_builds = builds["builds"]["char-a"]

    assert len(char_builds) == 1
    assert char_builds[0]["name"] == "Mock Raid Build"
    assert [g["slot"] for g in char_builds[0]["gear"]] == [4]
    assert char_builds[0]["food"]["link_name"] == "Mock Food"


def test_collectibles_sorted_by_index_with_subcategories():
    from data_processor import process_iasync_collectibles

    raw = {"collectibles": {
        "lastUpdate": 5,
        "categories": {  # Lua arrays arrive as dicts with int or str keys, in any order
            15: {"name": "Armor Styles", "icon": "/esoui/art/treeicons/a_up.dds", "specialization": 3, "numUnlocked": 1, "numTotal": 2,
                 "subcats": {"2": {"name": "Chest", "numUnlocked": 0, "numTotal": 1}, "1": {"name": "Head", "numUnlocked": 1, "numTotal": 1}}},
            "1": {"name": "Stories", "specialization": 1, "numUnlocked": 1, "numTotal": 1, "hidesLocked": True},
        },
        "items": {"7": {"name": "b helm", "icon": "/esoui/art/icons/x.dds", "unlocked": True, "cat": 15, "sub": 1},
                  3: {"name": "A Chest", "unlocked": False, "cat": 15, "sub": 2}, "bad": "skip"},
    }}
    col = process_iasync_collectibles(raw)
    assert [c["name"] for c in col["categories"]] == ["Stories", "Armor Styles"]
    assert col["categories"][0]["hidesLocked"] is True and col["categories"][0]["subcats"] == []
    assert [s["name"] for s in col["categories"][1]["subcats"]] == ["Head", "Chest"]
    assert col["categories"][1]["specialization"] == 3
    assert [(i["id"], i["name"], i["unlocked"], i["sub"]) for i in col["items"]] == [(3, "A Chest", False, 2), (7, "b helm", True, 1)]
    assert col["lastUpdate"] == 5
    assert process_iasync_collectibles({}) == {"categories": [], "items": [], "patrons": [], "lastUpdate": 0}


def test_tribute_patrons_in_tree_order_with_unlock_state():
    from data_processor import process_iasync_collectibles

    raw = {"collectibles": {
        "items": {"500": {"name": "Saint Pelin", "unlocked": True, "cat": 2, "sub": 0}},
        "patrons": {
            "2": {"name": "Treasury", "category": "Neutral", "categoryOrder": 2, "collectibleId": 0, "icon": "/esoui/art/tribute/patrons/patron_coin_neutral.dds"},
            "9": {"name": "Zed", "category": "Patrons", "categoryOrder": 1, "collectibleId": 501},
            "1": {"name": "Saint Pelin", "category": "Patrons", "categoryOrder": 1, "collectibleId": 500},
            "40": {"name": "Not In Tree", "categoryOrder": 0},
        },
    }}
    patrons = process_iasync_collectibles(raw)["patrons"]
    assert [(p["name"], p["category"], p["unlocked"]) for p in patrons] == [
        ("Saint Pelin", "Patrons", True), ("Zed", "Patrons", False), ("Treasury", "Neutral", True)]


def test_iasync_1_11_details_currencies_activities_antiquities():
    from data_processor import process_iasync, process_iasync_builds
    from lua_parser import parse_iasync_core_text

    lua = """iasync_data = {
      ["accountName"] = "@acct",
      ["chars"] = { ["c1"] = { ["name"] = "Hero", ["level"] = 50, ["championPoints"] = 1452, ["title"] = "Tactician",
        ["riding"] = { ["speed"] = 60, ["speedMax"] = 60 }, ["guilds"] = { [1] = { ["name"] = "G", ["rankName"] = "Officer" } },
        ["research"] = { ["blacksmithing"] = { [2] = { ["name"] = "Mace", ["numTraits"] = 9, ["known"] = { [1] = 3, [2] = 1 } },
                                             [1] = { ["name"] = "Axe", ["numTraits"] = 9, ["researching"] = { [1] = { ["traitType"] = 7, ["endTime"] = 99 } } } } },
        ["recipes"] = { [1] = { ["name"] = "Meat", ["total"] = 42, ["known"] = { [1] = "Chicken Breast" } } },
        ["mundusDescriptions"] = { ["The Lady"] = "Increases |cffffff2744|r Resistance" } } },
      ["currencies"] = { ["SEALS"] = { ["name"] = "Seals", ["account"] = 5 }, ["MONEY"] = { ["name"] = "Gold", ["bank"] = 9 } },
      ["activities"] = { ["timed"] = { [1] = { ["name"] = "Complete 1 Arena |t32:32:EsoUI/Art/Icons/mapKey/mapKey_soloTrial.dds|t", ["type"] = "weekly",
                                              ["progress"] = 0, ["maxProgress"] = 1, ["currencyQty"] = 250 } },
                         ["limits"] = { ["weekly"] = { ["resetTime"] = 7 } } },
      ["antiquities"] = { ["items"] = { [3] = { ["name"] = "Totem", ["setId"] = 1, ["zoneId"] = 2, ["hasLead"] = true } },
                          ["sets"] = { [1] = "Set A" }, ["zones"] = { [2] = "Zone B" } },
    }"""
    raw = parse_iasync_core_text(lua)  # the /api/data parser keeps the 1.11.0 account sections
    data = process_iasync(raw)
    c = data["characters"]["c1"]
    assert (c["level"], c["cp"], c["title"], c["riding"]["speed"]) == (50, 1452, "Tactician", 60)
    assert c["guilds"] == [{"name": "G", "rank": "Officer"}]
    assert [l["name"] for l in c["research"]["blacksmithing"]] == ["Axe", "Mace"]
    assert c["research"]["blacksmithing"][1]["known"] == [1, 3]
    assert c["research"]["blacksmithing"][0]["researching"] == [{"trait": 7, "endTime": 99}]
    assert c["recipes"] == [{"name": "Meat", "total": 42, "known": ["Chicken Breast"]}]
    assert [(x["name"], x["account"], x["bank"]) for x in data["currencies"]] == [("Gold", None, 9), ("Seals", 5, None)]
    t = data["activities"]["timed"][0]
    assert (t["name"], t["icon"], t["reward"]) == ("Complete 1 Arena", "/esoui/art/icons/mapkey/mapkey_solotrial.dds", 250)
    assert data["activities"]["resets"] == {"weekly": 7}
    assert data["antiquities"][0] | {} == {**data["antiquities"][0], "name": "Totem", "set": "Set A", "zone": "Zone B", "lead": True}
    assert process_iasync_builds(raw)["builds"][0]["mundusDescriptions"] == {"The Lady": "Increases 2744 Resistance"}
