from __future__ import annotations

import socket
import threading
import time
import urllib.request
from pathlib import Path

import pytest
import uvicorn

import server
from tests.conftest import fresh_cache, fresh_ww_cache


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def app_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    uploads = tmp_path / "uploads"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        """{
  "iasync_lua_path": "",
  "ww_lua_path": "",
  "ttc_addon_path": "",
  "ttc_lookup_table_path": "",
  "ttc_price_table_path": "",
  "port": 0,
  "server": "NA",
  "poll_interval_seconds": 3600
}""",
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(server, "SHARE_REGISTRY_PATH", uploads / "share_registry.json")
    monkeypatch.setattr(server, "CONFIG_PATH", config_path)
    monkeypatch.setattr(server, "_cache", fresh_cache())
    monkeypatch.setattr(server, "_ww_cache", fresh_ww_cache())
    server._sessions.clear()
    server._share_registry.clear()
    server._share_registry.update({"codes": {}})
    uploads.mkdir(parents=True, exist_ok=True)

    port = _free_port()
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="warning")
    srv = uvicorn.Server(config)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{url}/api/status", timeout=0.5).read()
            break
        except Exception:
            time.sleep(0.1)
    else:
        srv.should_exit = True
        raise RuntimeError("test server did not start")

    yield url

    srv.should_exit = True
    thread.join(timeout=5)
