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
    assert acct["rewards"] == [{"type": "title", "name": "Mock Title", "id": 7}]
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
