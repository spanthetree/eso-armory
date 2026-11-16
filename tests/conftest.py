from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import server


FIXTURES = Path(__file__).parent / "fixtures"
TEST_SESSION = "00000000-0000-4000-8000-000000000001"


def fresh_cache() -> dict:
    return {
        "data_bytes": None,
        "builds_bytes": None,
        "achievements_bytes": None,
        "stickerbook_bytes": None,
        "mtime": None,
        "error": None,
        "meta": None,
    }


def fresh_ww_cache() -> dict:
    return {"ww_builds_bytes": None, "mtime": None, "error": None}


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def isolated_server(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    uploads = tmp_path / "uploads"
    database_url = f"sqlite:///{(tmp_path / 'armory.db').as_posix()}"
    monkeypatch.setattr(server, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(server, "SHARE_REGISTRY_PATH", uploads / "share_registry.json")
    monkeypatch.setattr(server, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(server, "_config", {"server": "NA", "database_url": database_url})
    monkeypatch.setattr(server, "_cache", fresh_cache())
    monkeypatch.setattr(server, "_ww_cache", fresh_ww_cache())
    server._sessions.clear()
    server._share_registry.clear()
    server._share_registry.update({"codes": {}})
    server._ttc_tables.update({
        "lookup_mtime": None,
        "price_mtime": None,
        "lookup_path": None,
        "price_path": None,
        "db_path": None,
        "db_ready": False,
        "price_time": None,
        "price_cache": {},
    })
    import db
    db._ENGINE = None
    db._SESSION_MAKER = None
    db.init_db(database_url)
    uploads.mkdir(parents=True, exist_ok=True)
    return server


@pytest.fixture
def client(isolated_server):
    return TestClient(isolated_server.app)


@pytest.fixture
def uploaded_workspace(client: TestClient, fixtures_dir: Path):
    """Upload iasync + WW for a normal (non-admin) account."""
    files = {
        "iasync": ("iasync.lua", fixtures_dir.joinpath("iasync.lua").read_bytes(), "text/plain"),
        "ww": ("WizardsWardrobe.lua", fixtures_dir.joinpath("WizardsWardrobe.lua").read_bytes(), "text/plain"),
    }
    response = client.post(f"/api/upload?session={TEST_SESSION}", files=files)
    assert response.status_code == 200, response.text
    return json.loads(response.text)


@pytest.fixture
def admin_uploaded_workspace(client: TestClient, isolated_server, fixtures_dir: Path):
    """Upload iasync + WW, make the account an admin, then upload TTC files."""
    import bcrypt
    import db as db_module

    # Upload iasync + WW first to create the account
    files = {
        "iasync": ("iasync.lua", fixtures_dir.joinpath("iasync.lua").read_bytes(), "text/plain"),
        "ww": ("WizardsWardrobe.lua", fixtures_dir.joinpath("WizardsWardrobe.lua").read_bytes(), "text/plain"),
    }
    r = client.post(f"/api/upload?session={TEST_SESSION}", files=files)
    assert r.status_code == 200, r.text

    # Admin = listed in config + password set
    isolated_server._config["admin_accounts"] = ["@test_account"]
    assert db_module.set_account_password("@test_account", bcrypt.hashpw(b"password123", bcrypt.gensalt(rounds=4)).decode())

    # Upload TTC files (now allowed)
    ttc_files = {
        "ttc_lookup": ("ItemLookUpTable_EN.lua", fixtures_dir.joinpath("ItemLookUpTable_EN.lua").read_bytes(), "text/plain"),
        "ttc_price": ("PriceTableNA.lua", fixtures_dir.joinpath("PriceTableNA.lua").read_bytes(), "text/plain"),
    }
    r2 = client.post(f"/api/upload?session={TEST_SESSION}", files=ttc_files)
    assert r2.status_code == 200, r2.text
    body = json.loads(r2.text)
    assert body.get("ttc_lookup", {}).get("ok"), f"TTC lookup upload failed: {body}"
    assert body.get("ttc_price", {}).get("ok"), f"TTC price upload failed: {body}"
    return body
