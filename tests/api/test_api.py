from __future__ import annotations

import pytest

from tests.conftest import TEST_SESSION


@pytest.mark.api
def test_status_without_data_returns_json_error(client):
    response = client.get(f"/api/status?session={TEST_SESSION}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["ok"] is False


@pytest.mark.api
def test_upload_and_read_workspace(client, uploaded_workspace):
    assert uploaded_workspace["iasync"] == {"ok": True, "items": 6, "chars": 2}
    assert uploaded_workspace["ww"] == {"ok": True, "builds": 1}
    assert uploaded_workspace["ttc_lookup"] == {"ok": True}
    assert uploaded_workspace["ttc_price"] == {"ok": True}

    data = client.get(f"/api/data?session={TEST_SESSION}")
    builds = client.get(f"/api/builds?session={TEST_SESSION}")
    ww = client.get(f"/api/ww_builds?session={TEST_SESSION}")
    achievements = client.get(f"/api/achievements?session={TEST_SESSION}")
    stickerbook = client.get(f"/api/stickerbook?session={TEST_SESSION}")

    assert data.status_code == 200
    assert data.json()["characters"]["char-a"]["name"] == "Test Character One"
    assert builds.json()["abilityNames"]["101"] == "Mock Whip"
    assert ww.json()["builds"]["char-a"][0]["name"] == "Mock Raid Build"
    assert achievements.json()["earnedPts"] == 10
    assert stickerbook.json()["sets"][0]["name"] == "Mock Set"


@pytest.mark.api
def test_ttc_price_uses_uploaded_tables(client, uploaded_workspace):
    response = client.get(f"/api/ttc_price?session={TEST_SESSION}&name=Mock%20Sword")

    assert response.status_code == 200
    body = response.json()
    assert body["itemId"] == 1001
    assert body["avg"] == 1200
    assert body["source"].startswith("TTC uploaded")


@pytest.mark.api
def test_share_code_join_resolves_uploaded_workspace(client, uploaded_workspace):
    created = client.post(f"/api/share?session={TEST_SESSION}")
    assert created.status_code == 200
    code = created.json()["code"]

    join_session = "00000000-0000-4000-8000-000000000002"
    joined = client.post(f"/api/share/join?session={join_session}&code={code}")
    assert joined.status_code == 200
    assert joined.json()["sharedSession"] == TEST_SESSION

    shared_data = client.get(f"/api/data?session={join_session}&share={code}")
    assert shared_data.status_code == 200
    assert shared_data.json()["meta"]["item_count"] == 6


@pytest.mark.api
def test_upload_errors_are_json(client, fixtures_dir):
    invalid_session = client.post("/api/upload?session=not-a-uuid")
    empty_upload = client.post(f"/api/upload?session={TEST_SESSION}")
    bad_parse = client.post(
        f"/api/upload?session={TEST_SESSION}",
        files={"iasync": ("iasync.lua", b"iasync_data = { [1] = }", "text/plain")},
    )

    for response in (invalid_session, empty_upload, bad_parse):
        assert response.status_code >= 400 or response.json().get("iasync", {}).get("ok") is False
        assert response.headers["content-type"].startswith("application/json")

    assert invalid_session.json()["error"] == "valid session required"
    assert empty_upload.json()["error"] == "No files received"
    assert bad_parse.json()["iasync"]["ok"] is False


@pytest.mark.api
def test_static_and_cached_lookup_endpoints(client, isolated_server, monkeypatch):
    root = client.get("/")
    root_head = client.head("/")
    static_index = client.get("/static/index.html")
    assert root.status_code == 200
    assert root.headers["content-type"].startswith("text/html")
    assert root.headers["cache-control"] == "no-store"
    assert root.headers["x-content-type-options"] == "nosniff"
    assert root_head.status_code == 200
    assert root_head.headers["content-type"].startswith("text/html")
    assert root_head.headers["x-content-type-options"] == "nosniff"
    assert static_index.status_code == 200
    assert static_index.headers["content-type"].startswith("text/html")
    assert static_index.headers["x-content-type-options"] == "nosniff"

    monkeypatch.setattr(isolated_server, "_build_ability_icon_map", lambda: {"mock_whip": "/assets/abilities/mock.png"})
    icons = client.get("/api/ability_icons")
    assert icons.status_code == 200
    assert icons.json()["mock_whip"] == "/assets/abilities/mock.png"


@pytest.mark.api
def test_external_scraper_endpoints_can_be_mocked(client, isolated_server, monkeypatch):
    monkeypatch.setattr(isolated_server, "_fetch_set_bonuses", lambda slug: [{"pieces": 2, "text": "Adds testing"}])
    monkeypatch.setattr(isolated_server, "_fetch_skill_info", lambda slug: {"type": "Active", "cost": "1 Test"})

    set_bonus = client.get("/api/set_bonus?set_id=500&set_name=Mock%20Set")
    skill = client.get("/api/skill_info?name=Mock%20Whip")

    assert set_bonus.status_code == 200
    assert set_bonus.json()["bonuses"][0]["text"] == "Adds testing"
    assert skill.status_code == 200
    assert skill.json()["type"] == "Active"


@pytest.mark.api
def test_share_and_ttc_error_contracts(client, uploaded_workspace):
    bad_join = client.post(f"/api/share/join?session={TEST_SESSION}&code=bad")
    missing_share = client.get(f"/api/share?session={TEST_SESSION}&share=BAD-CODE")
    missing_price = client.get(f"/api/ttc_price?session={TEST_SESSION}&name=Missing%20Item")
    blank_price = client.get(f"/api/ttc_price?session={TEST_SESSION}&name=")

    assert bad_join.status_code == 400
    assert bad_join.json()["error"] == "valid pairing code required"
    assert missing_share.status_code == 400
    assert missing_share.json()["error"] == "invalid share code"
    assert missing_price.status_code == 200
    assert missing_price.json()["error"] == "No TTC item match"
    assert blank_price.status_code == 200
    assert blank_price.json()["error"] == "name is required"
