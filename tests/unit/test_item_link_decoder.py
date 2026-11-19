from __future__ import annotations

import pytest

from app.item_link_decoder import decode


@pytest.mark.unit
def test_decode_full_item_link_flags_and_metadata():
    link = "|H1:item:1001:0:50:3001:0:0:3:0:0:0:0:0:0:0:2305:1:1:1:0:42:0|h[Mock Sword]|h"

    data = decode(link)

    assert data["enchant_id"] == 3001
    assert data["is_enchanted"] is True
    assert data["trait_id"] == 3
    assert data["trait_name"] == "Precise"
    assert data["is_transmuted"] is True
    assert data["is_stolen"] is True
    assert data["style_id"] == 1
    assert data["style_name"] == "Breton"
    assert data["is_crafted"] is True
    assert data["is_bound"] is True
    assert data["sell_value"] == 42


@pytest.mark.unit
def test_decode_invalid_links_return_empty_dict():
    assert decode("not an item") == {}
    assert decode("|H1:item:1:2:3|h[bad]|h") == {}


@pytest.mark.unit
def test_decode_20_field_links_preserves_current_offsets():
    link = "|H1:item:1001:0:50:0:0:0:18:0:0:0:0:0:0:2048:0:1:1:0:0:42|h[Mock Cuirass]|h"

    data = decode(link)

    assert data["trait_id"] == 18
    assert data["is_transmuted"] is False
    assert data["is_crafted"] is True
