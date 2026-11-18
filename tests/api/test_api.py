from __future__ import annotations

import json

import pytest
from sqlalchemy import select

import db

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
    assert stickerbook.json()["collectibles"] == {"categories": [], "items": [], "patrons": [], "lastUpdate": 0}  # no iasync 1.9.0 data


@pytest.mark.api
def test_ttc_price_uses_uploaded_tables(client, admin_uploaded_workspace):
    response = client.get(f"/api/ttc_price?session={TEST_SESSION}&name=Mock%20Sword")

    assert response.status_code == 200
    body = response.json()
    assert body["itemId"] == 1001
    assert body["avg"] == 1200
    assert body["source"].startswith("TTC uploaded")


@pytest.mark.api
def test_ttc_prices_batch(client, admin_uploaded_workspace):
    ok = client.post(f"/api/ttc_prices?session={TEST_SESSION}", json={"names": ["Mock Sword", "mock  sword", "Missing Item", 5]})
    bad = client.post(f"/api/ttc_prices?session={TEST_SESSION}", json={"names": "Mock Sword"})

    assert ok.status_code == 200
    assert ok.json()["prices"] == {"mock sword": 1200}
    assert bad.status_code == 400


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
def test_share_code_is_read_only(client, uploaded_workspace, fixtures_dir):
    code = client.post(f"/api/share?session={TEST_SESSION}").json()["code"]
    viewer = "00000000-0000-4000-8000-000000000002"
    q = f"session={viewer}&share={code}"

    assert client.get(f"/api/data?{q}").status_code == 200
    assert client.get(f"/api/auth/status?{q}").json()["account_name"] is None
    assert client.post(f"/api/auth/set_password?{q}", json={"password": "password123"}).status_code == 403
    assert client.get(f"/api/auth/status?session={TEST_SESSION}").json()["has_password"] is False

    files = {"iasync": ("iasync.lua", fixtures_dir.joinpath("iasync.lua").read_bytes(), "text/plain")}
    client.post(f"/api/upload?{q}", files=files)
    # The upload lands in the viewer's own workspace, never the sharer's.
    assert client.get(f"/api/workspace?session={TEST_SESSION}").json()["shadow"]["account"] is None

    build_code = client.post(f"/api/build_export?session={TEST_SESSION}&character_id=char-a").json()["code"]
    client.post(f"/api/compare_builds/import?{q}&character_id=char-a&code={build_code}")
    assert "char-a" not in client.get(f"/api/compare_builds?session={TEST_SESSION}").json()["imported"]


@pytest.mark.api
def test_iasync_upload_without_account_name_is_rejected(client, uploaded_workspace):
    files = {"iasync": ("iasync.lua", b'iasync_data = { ["chars"] = {} }', "text/plain")}
    result = client.post(f"/api/upload?session={TEST_SESSION}", files=files).json()["iasync"]
    assert result["ok"] is False
    assert "no ESO account name" in result["error"]
    workspace = client.get(f"/api/workspace?session={TEST_SESSION}").json()
    assert (workspace["primary"]["account"], workspace["shadow"]["account"]) == ("@test_account", None)
    assert client.get(f"/api/data?session={TEST_SESSION}").json()["meta"]["item_count"] == 6


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
    root_head = client.head("/")
    assert root_head.status_code == 200
    assert root_head.headers["content-type"].startswith("text/html")
    assert root_head.headers["x-content-type-options"] == "nosniff"

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
def test_share_and_ttc_error_contracts(client, admin_uploaded_workspace):
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
def test_uploaded_workspace_all_payloads_built_upfront(client, uploaded_workspace):
    # All payloads (including achievements + stickerbook) are built on upload, not lazily.
    state = db.get_account_state("@test_account")
    assert state is not None
    assert state.data_bytes is not None
    assert state.builds_bytes is not None
    assert state.achievements_bytes is not None
    assert state.stickerbook_bytes is not None


@pytest.mark.api
def test_uploaded_workspace_recovery_returns_clear_error_when_data_missing(client, isolated_server, uploaded_workspace):
    with db.session_scope() as session:
        row = session.scalar(select(db.AccountState).where(db.AccountState.account_name == "@test_account"))
        assert row is not None
        row.data_bytes = None
        row.builds_bytes = None
        row.achievements_bytes = None
        row.stickerbook_bytes = None

    isolated_server._sessions.clear()

    achievements = client.get(f"/api/achievements?session={TEST_SESSION}")
    stickerbook = client.get(f"/api/stickerbook?session={TEST_SESSION}")

    assert achievements.status_code == 503
    assert stickerbook.status_code == 503
    assert "re-upload" in achievements.json()["detail"]
    assert "re-upload" in stickerbook.json()["detail"]


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
def test_ww_parse_from_bytes_sets_error_on_bad_input(isolated_server, fixtures_dir):
    # Good parse populates the cache
    good_bytes = (fixtures_dir / "WizardsWardrobe.lua").read_bytes()
    cache = isolated_server._empty_ww_cache()
    isolated_server._parse_ww_from_bytes(good_bytes, cache)
    assert cache["error"] is None
    assert cache["ww_builds_bytes"] is not None
    first = json.loads(cache["ww_builds_bytes"])
    assert first["builds"]

    # Bad bytes set an error but do not raise
    bad_cache = isolated_server._empty_ww_cache()
    isolated_server._parse_ww_from_bytes(b"-- truncated", bad_cache)
    assert bad_cache["error"] is not None
    assert bad_cache["ww_builds_bytes"] is None


@pytest.mark.api
def test_build_export_and_compare_import_cycle(client, uploaded_workspace, fixtures_dir):
    source = (fixtures_dir / "iasync.lua").read_text().replace(
        'iasync_data = {',
        'iasync_data = { ["abilityIcons"] = { [101] = "/esoui/art/icons/mock_whip.dds" },',
        1,
    )
    assert client.post(f"/api/upload?session={TEST_SESSION}", files={"iasync": ("iasync.lua", source)}).status_code == 200
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
    assert body["imported"]["char-a"]["build"]["abilityIcons"] == {"101": "/esoui/art/icons/mock_whip.dds"}

    deleted = client.delete(f"/api/compare_builds?session={TEST_SESSION}&character_id=char-a")
    assert deleted.status_code == 200
    listed_after = client.get(f"/api/compare_builds?session={TEST_SESSION}")
    assert listed_after.status_code == 200
    assert "char-a" not in listed_after.json()["imported"]


OTHER_SESSION = "00000000-0000-4000-8000-000000000002"


def _upload_iasync(client, fixtures_dir, session):
    files = {"iasync": ("iasync.lua", fixtures_dir.joinpath("iasync.lua").read_bytes(), "text/plain")}
    return client.post(f"/api/upload?session={session}", files=files).json()


@pytest.mark.api
def test_upload_for_password_protected_account_requires_login(client, uploaded_workspace, fixtures_dir):
    assert client.post(f"/api/auth/set_password?session={TEST_SESSION}", json={"password": "password123"}).status_code == 200

    forged = _upload_iasync(client, fixtures_dir, OTHER_SESSION)
    assert forged["iasync"]["ok"] is False
    assert "password-protected" in forged["iasync"]["error"]
    assert client.get(f"/api/workspace?session={OTHER_SESSION}").json()["primary"]["account"] is None

    login = client.post(f"/api/auth/login?session={OTHER_SESSION}", json={"account_name": "@test_account", "password": "password123"})
    assert login.status_code == 200
    assert _upload_iasync(client, fixtures_dir, OTHER_SESSION)["iasync"]["ok"] is True


@pytest.mark.api
def test_changing_password_needs_current_password(client, uploaded_workspace):
    url = f"/api/auth/set_password?session={TEST_SESSION}"
    assert client.post(url, json={"password": "password123"}).status_code == 200
    assert client.post(url, json={"password": "newpassword1"}).status_code == 403
    assert client.post(url, json={"password": "newpassword1", "current_password": "wrong-one"}).status_code == 403
    assert client.post(url, json={"password": "newpassword1", "current_password": "password123"}).status_code == 200


@pytest.mark.api
def test_logout_unbinds_browser_but_keeps_account(client, uploaded_workspace):
    client.post(f"/api/auth/set_password?session={TEST_SESSION}", json={"password": "password123"})
    assert client.post(f"/api/auth/logout?session={TEST_SESSION}").json() == {"ok": True}
    assert client.get(f"/api/workspace?session={TEST_SESSION}").json()["primary"]["account"] is None
    assert client.get(f"/api/auth/status?session={TEST_SESSION}").json()["account_name"] is None

    login = client.post(f"/api/auth/login?session={OTHER_SESSION}", json={"account_name": "@test_account", "password": "password123"})
    assert login.status_code == 200
    assert client.get(f"/api/data?session={OTHER_SESSION}").status_code == 200


@pytest.mark.api
def test_admin_requires_config_entry_and_password(client, isolated_server, uploaded_workspace):
    status = lambda: client.get(f"/api/status?session={TEST_SESSION}").json()["is_admin"]
    assert status() is False
    isolated_server._config["admin_accounts"] = ["@test_account"]
    assert status() is False  # listed but no password: a forged upload must not get admin
    client.post(f"/api/auth/set_password?session={TEST_SESSION}", json={"password": "password123"})
    assert status() is True


@pytest.mark.api
def test_root_serves_built_app_or_explains_missing_build(client, isolated_server, tmp_path, monkeypatch):
    monkeypatch.setattr(isolated_server, "_APP_HTML", tmp_path / "dist" / "index.html")
    missing = client.get("/")
    assert missing.status_code == 503
    assert missing.headers["content-type"].startswith("text/html")
    assert "make ui-build" in missing.text

    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "index.html").write_text('<div id="app"></div>')
    built = client.get("/")
    assert built.status_code == 200
    assert built.headers["content-type"].startswith("text/html")
    assert built.headers["cache-control"] == "no-store"
    assert built.headers["x-content-type-options"] == "nosniff"


@pytest.mark.api
def test_ability_names_resolves_and_validates(client, isolated_server, monkeypatch):
    calls = []

    def fake_fetch(aid):
        calls.append(aid)
        return {20323: "Shatterspike Mantle"}.get(aid, "")

    monkeypatch.setattr(isolated_server, "_fetch_ability_name", fake_fetch)
    isolated_server._ability_name_cache.clear()

    first = client.get("/api/ability_names?ids=20323,99,20323")
    again = client.get("/api/ability_names?ids=20323")
    bad = client.get("/api/ability_names?ids=1,abc")
    too_many = client.get("/api/ability_names?ids=" + ",".join(str(i) for i in range(1, 50)))

    assert first.json() == {"names": {"20323": "Shatterspike Mantle"}}
    assert again.json() == {"names": {"20323": "Shatterspike Mantle"}}
    isolated_server._ability_name_cache.clear()  # simulate a restart with UESP unavailable
    def offline(aid):
        raise OSError("offline")
    monkeypatch.setattr(isolated_server, "_fetch_ability_name", offline)
    assert client.get("/api/ability_names?ids=20323").json() == first.json()
    assert not (isolated_server.UPLOADS_DIR / "ability_names" / "99.txt").exists()
    assert calls == [20323, 99]  # deduped, and cached across requests (unknown ids too)
    assert bad.status_code == 400
    assert too_many.status_code == 400


@pytest.mark.api
def test_game_icon_downloads_once_and_validates(client, isolated_server, monkeypatch, tmp_path):
    png = b"\x89PNG\r\n\x1a\nfake"
    calls = []

    def fake_fetch(name, folder="icons"):
        calls.append(name if folder == "icons" else f"{folder}/{name}")
        return png if name in ("achievement_x", "tree_x") else None

    monkeypatch.setattr(isolated_server, "_fetch_game_icon", fake_fetch)
    monkeypatch.setattr(isolated_server, "_GAME_ICON_DIR", tmp_path / "esoicons")
    isolated_server._game_icon_missing.clear()

    first = client.get("/esoicons/achievement_x.png")
    second = client.get("/esoicons/ACHIEVEMENT_X.png")
    missing = client.get("/esoicons/nope.png")
    missing_again = client.get("/esoicons/nope.png")
    bad = client.get("/esoicons/..%2Fsecrets.png")
    tree = client.get("/esoicons/treeicons/tree_x.png")
    bad_folder = client.get("/esoicons/etc/tree_x.png")

    assert first.status_code == 200 and first.content == png
    assert first.headers["content-type"] == "image/png"
    assert second.status_code == 200
    assert missing.status_code == 404 and missing_again.status_code == 404
    assert tree.status_code == 200 and (tmp_path / "esoicons" / "treeicons" / "tree_x.png").exists()
    assert bad_folder.status_code == 400
    assert first.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert calls == ["achievement_x", "nope", "treeicons/tree_x"]  # cached on disk / remembered as missing
    assert bad.status_code in (400, 404)


@pytest.mark.api
def test_missing_icons_are_fetched_and_saved_or_sent_to_uesp(client, isolated_server, monkeypatch, tmp_path):
    import urllib.error

    png = b"\x89PNG\r\n\x1a\nfake"
    asked = []

    def fetch(url, timeout=30):
        asked.append(url)
        if "broken" in url:
            raise urllib.error.HTTPError(url, 502, "Bad Gateway", {}, None)
        return None if "gone" in url else png

    monkeypatch.setattr(isolated_server.uesp, "fetch_png", fetch)
    monkeypatch.setattr(isolated_server, "_GAME_ICON_DIR", tmp_path / "esoicons")
    monkeypatch.setattr(isolated_server, "_asset_manifest", {
        "esoui/x/new.png": "https://esoicons.uesp.net/esoui/art/x/new.png",
        "esoui/x/broken.png": "https://esoicons.uesp.net/esoui/art/x/broken.png",
    })
    isolated_server._game_icon_missing.clear()
    assets = next(r.app for r in isolated_server.app.routes if getattr(r, "path", "") == "/assets")
    monkeypatch.setattr(assets, "all_directories", [str(tmp_path / "assets")])
    (tmp_path / "assets").mkdir()

    icon = client.get("/esoicons/broken_icon.png", follow_redirects=False)
    asset = client.get("/assets/esoui/x/new.png")
    again = client.get("/assets/esoui/x/new.png")
    down = client.get("/assets/esoui/x/broken.png", follow_redirects=False)
    unknown = client.get("/assets/not/in/manifest.png", follow_redirects=False)

    assert icon.status_code == 307 and icon.headers["location"] == "https://esoicons.uesp.net/esoui/art/icons/broken_icon.png"
    assert icon.headers["cache-control"] == "no-store"
    assert asset.status_code == 200 and asset.content == png  # fetched, saved, served
    assert asset.headers["cache-control"] == "public, max-age=31536000, immutable"
    cached = client.get("/assets/esoui/x/new.png", headers={"If-None-Match": asset.headers["etag"]})
    assert cached.status_code == 304
    assert cached.headers["cache-control"] == asset.headers["cache-control"]
    assert again.status_code == 200 and asked.count("https://esoicons.uesp.net/esoui/art/x/new.png") == 1
    assert (tmp_path / "assets" / "esoui" / "x" / "new.png").read_bytes() == png
    assert down.status_code == 307 and down.headers["location"] == "https://esoicons.uesp.net/esoui/art/x/broken.png"
    assert unknown.status_code == 404
    assert "immutable" not in unknown.headers.get("cache-control", "")
    assert down.headers["cache-control"] == "no-store"


@pytest.mark.api
def test_large_payloads_are_gzipped_when_accepted(isolated_server):
    import gzip as gz
    from starlette.requests import Request

    def req(enc):
        return Request({"type": "http", "headers": [(b"accept-encoding", enc.encode())]})

    body = json.dumps({"items": ["x" * 50] * 100}).encode()
    zipped = isolated_server._payload_response(req("gzip, deflate"), body, {"Cache-Control": "no-store"})
    plain = isolated_server._payload_response(req("identity"), body, {})
    small = isolated_server._payload_response(req("gzip"), b"{}", {})
    assert zipped.headers["content-encoding"] == "gzip" and gz.decompress(zipped.body) == body
    assert zipped.headers["cache-control"] == "no-store" and zipped.headers["vary"] == "Accept-Encoding"
    assert "content-encoding" not in plain.headers and plain.body == body
    assert "content-encoding" not in small.headers


def _with_fernet(server, monkeypatch):
    """Session API keys are encrypted with the config's db_secret; give the isolated server one (nothing written)."""
    from cryptography.fernet import Fernet
    monkeypatch.setitem(server._config, "db_secret", Fernet.generate_key().decode())
    server._init_db_fernet()


@pytest.mark.api
def test_superstar_reads_with_the_saved_provider(client, isolated_server, monkeypatch):
    _with_fernet(isolated_server, monkeypatch)
    calls = []
    monkeypatch.setattr(isolated_server, "_read_screenshot_openai", lambda k, m, b: calls.append(("openai", k)) or {"gear": [{"slot": "Head"}]})
    monkeypatch.setattr(isolated_server, "_read_screenshot_anthropic", lambda k, m, b: calls.append(("anthropic", k)) or {"gear": []})
    monkeypatch.setattr(isolated_server, "_server_vision_key", lambda: ("", ""))
    png = {"image": ("s.png", b"\x89PNG\r\n\x1a\nfake", "image/png")}

    none = client.post(f"/api/parse_superstar?session={TEST_SESSION}", files=png)
    bad = client.post(f"/api/session/apikey?session={TEST_SESSION}", data={"api_key": "x", "provider": "nope"})
    client.post(f"/api/session/apikey?session={TEST_SESSION}", data={"api_key": "sk-openai"})  # provider defaults to OpenAI
    status = client.get(f"/api/status?session={TEST_SESSION}").json()
    read = client.post(f"/api/parse_superstar?session={TEST_SESSION}", files=png)
    client.post(f"/api/session/apikey?session={TEST_SESSION}", data={"api_key": "sk-ant-x", "provider": "anthropic"})
    client.post(f"/api/parse_superstar?session={TEST_SESSION}", files=png)

    assert none.status_code == 503 and bad.status_code == 400
    assert status["has_session_api_key"] is True and status["session_api_provider"] == "openai"
    assert read.status_code == 200 and read.json()["gear"][0]["slot_id"] is not None
    assert calls == [("openai", "sk-openai"), ("anthropic", "sk-ant-x")]


@pytest.mark.api
def test_keys_saved_before_providers_are_anthropic(isolated_server, monkeypatch):
    _with_fernet(isolated_server, monkeypatch)
    isolated_server._db_save_session_api_key(TEST_SESSION, isolated_server._encrypt_api_key("sk-ant-legacy"))
    assert isolated_server._session_vision_key(TEST_SESSION) == ("anthropic", "sk-ant-legacy")
    assert isolated_server._json_reply('```json\n{"a": 1}\n```') == {"a": 1}


@pytest.mark.api
def test_demo_account_is_a_read_only_share(client, isolated_server, monkeypatch):
    _with_fernet(isolated_server, monkeypatch)
    monkeypatch.setattr(isolated_server, "_demo_ready", False)
    isolated_server._ensure_demo_account()  # the real demo/demo.json.gz
    isolated_server._ensure_demo_account()  # unchanged file: no reload, same binding

    status = client.get(f"/api/status?session={TEST_SESSION}").json()
    joined = client.post(f"/api/share/join?session={TEST_SESSION}&code={isolated_server.DEMO_CODE}")
    data = client.get(f"/api/data?session={TEST_SESSION}&share={isolated_server.DEMO_CODE}").json()
    sticker = client.get(f"/api/stickerbook?session={TEST_SESSION}&share={isolated_server.DEMO_CODE}").json()
    claim = client.post(f"/api/upload?session={TEST_SESSION}", files={"iasync": (
        "iasync.lua", b'iasync_data = { ["accountName"] = "@armory-demo", ["chars"] = {} }', "text/plain")}).json()

    assert status["demo_code"] == isolated_server.DEMO_CODE
    assert joined.status_code == 200
    assert data["meta"]["account"] == "@armory-demo" and data["characters"] and data["items"]
    assert all(c["name"] and not c["id"].isdigit() for c in data["characters"].values())  # generated, not real ids
    assert sticker["sets"] and sticker["collectibles"]["items"]
    assert claim["iasync"]["ok"] is False and "reserved" in claim["iasync"]["error"]
    assert isolated_server._demo_session_id() != TEST_SESSION and len(isolated_server._demo_session_id()) == 36
