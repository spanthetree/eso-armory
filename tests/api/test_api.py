from __future__ import annotations

import json

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
    assert uploaded_workspace["iasync"]["ok"] is True
    assert uploaded_workspace["iasync"]["items"] == 6
    assert uploaded_workspace["iasync"]["chars"] == 2
    assert uploaded_workspace["iasync"]["slot_updated"] == "primary"
    assert uploaded_workspace["ww"]["ok"] is True
    assert uploaded_workspace["ww"]["builds"] == 1
    assert uploaded_workspace["ww"]["slot_updated"] == "primary"
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


@pytest.mark.api
def test_uploaded_workspace_survives_in_memory_session_clear(client, isolated_server, uploaded_workspace):
    isolated_server._sessions.clear()

    data = client.get(f"/api/data?session={TEST_SESSION}")
    builds = client.get(f"/api/builds?session={TEST_SESSION}")
    achievements = client.get(f"/api/achievements?session={TEST_SESSION}")

    assert data.status_code == 200
    assert builds.status_code == 200
    assert achievements.status_code == 200
    assert data.json()["meta"]["account"] == "@test_account"
    assert builds.json()["abilityNames"]["101"] == "Mock Whip"
    assert achievements.json()["earnedPts"] == 10


@pytest.mark.api
def test_uploaded_workspace_reads_from_db_when_account_files_are_removed(client, isolated_server, uploaded_workspace):
    account_root = isolated_server.UPLOADS_DIR / "accounts" / "test_account"
    for path in [
        account_root / "SavedVariables" / "iasync.lua",
        account_root / "SavedVariables" / "WizardsWardrobe.lua",
    ]:
        if path.exists():
            path.unlink()

    isolated_server._sessions.clear()

    data = client.get(f"/api/data?session={TEST_SESSION}")
    achievements = client.get(f"/api/achievements?session={TEST_SESSION}")
    stickerbook = client.get(f"/api/stickerbook?session={TEST_SESSION}")
    ww = client.get(f"/api/ww_builds?session={TEST_SESSION}")

    assert data.status_code == 200
    assert achievements.status_code == 200
    assert stickerbook.status_code == 200
    assert ww.status_code == 200
    assert data.json()["meta"]["account"] == "@test_account"
    assert achievements.json()["earnedPts"] == 10
    assert stickerbook.json()["sets"][0]["name"] == "Mock Set"
    assert ww.json()["builds"]["char-a"][0]["name"] == "Mock Raid Build"


@pytest.mark.api
def test_different_account_upload_populates_shadow_slot(client, fixtures_dir):
    files = {
        "iasync": ("iasync.lua", fixtures_dir.joinpath("iasync.lua").read_bytes(), "text/plain"),
        "ww": ("WizardsWardrobe.lua", fixtures_dir.joinpath("WizardsWardrobe.lua").read_bytes(), "text/plain"),
    }
    first = client.post(f"/api/upload?session={TEST_SESSION}", files=files)
    assert first.status_code == 200

    alt_iasync = fixtures_dir.joinpath("iasync.lua").read_bytes().replace(b"@test_account", b"@alt_account", 1)
    alt_ww = fixtures_dir.joinpath("WizardsWardrobe.lua").read_bytes().replace(b"@test_account", b"@alt_account", 1)
    second = client.post(
        f"/api/upload?session={TEST_SESSION}",
        files={"iasync": ("iasync.lua", alt_iasync, "text/plain"), "ww": ("WizardsWardrobe.lua", alt_ww, "text/plain")},
    )
    assert second.status_code == 200
    body = second.json()
    assert body["iasync"]["ok"] is True
    assert body["iasync"]["slot_updated"] == "shadow"
    assert body["ww"]["slot_updated"] == "shadow"

    workspace = client.get(f"/api/workspace?session={TEST_SESSION}")
    assert workspace.status_code == 200
    assert workspace.json()["primary"]["account"] == "@test_account"
    assert workspace.json()["shadow"]["account"] == "@alt_account"
    assert workspace.json()["activeSlot"] == "shadow"


@pytest.mark.api
def test_workspace_slot_switch_and_delete_shadow(client, fixtures_dir):
    base_files = {
        "iasync": ("iasync.lua", fixtures_dir.joinpath("iasync.lua").read_bytes(), "text/plain"),
        "ww": ("WizardsWardrobe.lua", fixtures_dir.joinpath("WizardsWardrobe.lua").read_bytes(), "text/plain"),
    }
    client.post(f"/api/upload?session={TEST_SESSION}", files=base_files)
    alt_iasync = fixtures_dir.joinpath("iasync.lua").read_bytes().replace(b"@test_account", b"@alt_account", 1)
    client.post(f"/api/upload?session={TEST_SESSION}", files={"iasync": ("iasync.lua", alt_iasync, "text/plain")})

    switched = client.post(f"/api/workspace/slot?session={TEST_SESSION}&slot=primary")
    assert switched.status_code == 200
    assert switched.json()["activeSlot"] == "primary"

    data = client.get(f"/api/data?session={TEST_SESSION}")
    assert data.status_code == 200
    assert data.json()["meta"]["account"] == "@test_account"

    deleted = client.delete(f"/api/workspace/shadow?session={TEST_SESSION}")
    assert deleted.status_code == 200
    assert deleted.json()["shadow"]["account"] is None
    assert deleted.json()["activeSlot"] == "primary"


@pytest.mark.api
def test_third_unmatched_account_upload_conflicts(client, fixtures_dir):
    client.post(
        f"/api/upload?session={TEST_SESSION}",
        files={"iasync": ("iasync.lua", fixtures_dir.joinpath("iasync.lua").read_bytes(), "text/plain")},
    )
    alt_iasync = fixtures_dir.joinpath("iasync.lua").read_bytes().replace(b"@test_account", b"@alt_account", 1)
    client.post(f"/api/upload?session={TEST_SESSION}", files={"iasync": ("iasync.lua", alt_iasync, "text/plain")})
    third_iasync = fixtures_dir.joinpath("iasync.lua").read_bytes().replace(b"@test_account", b"@third_account", 1)

    third = client.post(f"/api/upload?session={TEST_SESSION}", files={"iasync": ("iasync.lua", third_iasync, "text/plain")})
    assert third.status_code == 200
    assert third.json()["iasync"]["ok"] is False
    assert third.json()["iasync"]["conflict"] is True


@pytest.mark.api
def test_ww_transient_parse_keeps_previous_cache(isolated_server, fixtures_dir, tmp_path):
    ww_path = tmp_path / "WizardsWardrobe.lua"
    ww_path.write_bytes((fixtures_dir / "WizardsWardrobe.lua").read_bytes())

    cache = {
        "ww_builds_bytes": None,
        "mtime": None,
        "error": None,
        "source_path": None,
    }
    isolated_server._parse_ww_into(str(ww_path), cache)
    first = json.loads(cache["ww_builds_bytes"])

    ww_path.write_text("-- transient partial save\n", encoding="utf-8")
    cache["mtime"] = None
    isolated_server._parse_ww_into(str(ww_path), cache)

    assert cache["error"] is None
    assert json.loads(cache["ww_builds_bytes"]) == first


@pytest.mark.api
def test_build_export_and_compare_import_cycle(client, uploaded_workspace):
    exported = client.post(f"/api/build_export?session={TEST_SESSION}&character_id=char-a")
    assert exported.status_code == 200
    code = exported.json()["code"]
    assert code

    imported = client.post(f"/api/compare_builds/import?session={TEST_SESSION}&character_id=char-a&code={code}")
    assert imported.status_code == 200
    assert imported.json()["ok"] is True

    listed = client.get(f"/api/compare_builds?session={TEST_SESSION}")
    assert listed.status_code == 200
    body = listed.json()
    assert "char-a" in body["imported"]
    assert body["imported"]["char-a"]["source_code"] == code
    assert body["imported"]["char-a"]["build"]["char_id"] == "char-a"

    deleted = client.delete(f"/api/compare_builds?session={TEST_SESSION}&character_id=char-a")
    assert deleted.status_code == 200
    listed_after = client.get(f"/api/compare_builds?session={TEST_SESSION}")
    assert listed_after.status_code == 200
    assert "char-a" not in listed_after.json()["imported"]
