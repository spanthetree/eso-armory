"""ESO Armory — FastAPI server."""

import asyncio
import json
import os
import platform
import re
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from lua_parser import parse_lua_variable
from data_processor import process_iasync, process_iasync_builds, process_ww_builds


def _eso_sv_path(filename: str) -> str:
    """Return the platform-appropriate path to an ESO SavedVariables file."""
    eso_rel = Path("Elder Scrolls Online") / "live" / "SavedVariables" / filename
    if sys.platform == "win32":
        return str(Path.home() / "Documents" / eso_rel)
    if "microsoft" in platform.uname().release.lower():
        skip = {"Public", "Default", "Default User", "All Users"}
        users = Path("/mnt/c/Users")
        if users.exists():
            for u in sorted(users.iterdir()):
                if u.is_dir() and u.name not in skip:
                    candidate = u / "Documents" / eso_rel
                    if candidate.parent.exists():
                        return str(candidate)
    return ""


CONFIG_PATH = Path("config.json")
DEFAULT_CONFIG = {
    "iasync_lua_path": _eso_sv_path("iasync.lua"),
    "ww_lua_path":     _eso_sv_path("WizardsWardrobe.lua"),
    "port": 5000,
    "server": "NA",
    "poll_interval_seconds": 5,
}

_config: dict = {}
_cache: dict = {
    "data_bytes":    None,
    "builds_bytes":  None,
    "mtime":         None,
    "error":         None,
}
_ww_cache: dict = {
    "ww_builds_bytes": None,
    "mtime":           None,
    "error":           None,
}
_sse_queues: set[asyncio.Queue] = set()
_ability_icon_map: dict = {}


def _build_ability_icon_map() -> dict:
    abilities_dir = Path("assets/abilities")
    if not abilities_dir.exists():
        return {}
    result = {}
    for png in sorted(abilities_dir.rglob("*.png")):
        key = re.sub(r'[^a-z0-9]+', '_', png.stem.lower()).strip('_')
        result[key] = "/" + png.as_posix()
    return result


def _load_config():
    global _config
    if CONFIG_PATH.exists():
        _config = json.loads(CONFIG_PATH.read_text())
    else:
        _config = dict(DEFAULT_CONFIG)
        CONFIG_PATH.write_text(json.dumps(_config, indent=2))
        print(f"Created default config: {CONFIG_PATH}")
    for k, v in DEFAULT_CONFIG.items():
        _config.setdefault(k, v)


def _parse_iasync():
    path = _config.get("iasync_lua_path", "")
    if not path:
        _cache["error"] = "iasync_lua_path not configured"
        return
    try:
        mtime = os.path.getmtime(path)
        if _cache["mtime"] == mtime:
            return
        print(f"Parsing {path} ...", end=" ", flush=True)
        t0 = time.monotonic()
        raw = parse_lua_variable(path, "iasync_data")
        data   = process_iasync(raw, server=_config.get("server", "NA"))
        builds = process_iasync_builds(raw)
        elapsed = time.monotonic() - t0
        data["meta"]["parse_ms"] = int(elapsed * 1000)
        _cache["data_bytes"]   = json.dumps(data).encode()
        _cache["builds_bytes"] = json.dumps(builds).encode()
        _cache["mtime"]        = mtime
        _cache["error"]        = None
        n = data["meta"]["item_count"]
        c = data["meta"]["character_count"]
        print(f"done ({n} items, {c} chars, {elapsed:.2f}s)")
    except FileNotFoundError:
        _cache["error"] = f"iasync.lua not found: {path}"
        print(f"\nNot found: {path}", file=sys.stderr)
    except Exception as exc:
        _cache["error"] = str(exc)
        print(f"\nParse error: {exc}", file=sys.stderr)


def _parse_ww():
    path = _config.get("ww_lua_path", "")
    if not path:
        _ww_cache["error"] = "ww_lua_path not configured"
        return
    try:
        mtime = os.path.getmtime(path)
        if _ww_cache["mtime"] == mtime:
            return
        print(f"Parsing WW {path} ...", end=" ", flush=True)
        raw = parse_lua_variable(path, "WizardsWardrobeSV")
        builds = process_ww_builds(raw)
        _ww_cache["ww_builds_bytes"] = json.dumps(builds).encode()
        _ww_cache["mtime"]           = mtime
        _ww_cache["error"]           = None
        n = sum(len(v) for v in builds["builds"].values())
        print(f"done ({n} WW builds)")
    except FileNotFoundError:
        _ww_cache["error"] = f"WizardsWardrobe.lua not found: {path}"
        print(f"\nNot found: {path}", file=sys.stderr)
    except Exception as exc:
        _ww_cache["error"] = str(exc)
        print(f"\nWW parse error: {exc}", file=sys.stderr)


async def _file_watcher():
    while True:
        await asyncio.sleep(_config.get("poll_interval_seconds", 5))
        loop = asyncio.get_event_loop()

        iasync_path = _config.get("iasync_lua_path", "")
        if iasync_path:
            try:
                mtime = os.path.getmtime(iasync_path)
                if mtime != _cache["mtime"]:
                    await loop.run_in_executor(None, _parse_iasync)
                    for q in list(_sse_queues):
                        try:
                            q.put_nowait("reload")
                        except asyncio.QueueFull:
                            pass
            except Exception:
                pass

        ww_path = _config.get("ww_lua_path", "")
        if ww_path:
            try:
                mtime = os.path.getmtime(ww_path)
                if mtime != _ww_cache["mtime"]:
                    await loop.run_in_executor(None, _parse_ww)
            except Exception:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_config()
    _parse_iasync()
    _parse_ww()
    _ability_icon_map.update(_build_ability_icon_map())
    print(f"Ability icons: {len(_ability_icon_map)} loaded")
    asyncio.create_task(_file_watcher())
    yield


app = FastAPI(title="ESO Armory", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
async def root():
    return FileResponse("static/index.html", headers={"Cache-Control": "no-store"})


@app.get("/api/data")
async def api_data():
    if _cache["data_bytes"] is None:
        return JSONResponse({"error": _cache.get("error", "No data loaded")}, status_code=503)
    return Response(
        content=_cache["data_bytes"],
        media_type="application/json",
        headers={"ETag": str(_cache["mtime"]), "Cache-Control": "no-store"},
    )


@app.get("/api/builds")
async def api_builds():
    if _cache["builds_bytes"] is None:
        return JSONResponse({"error": _cache.get("error", "No data loaded")}, status_code=503)
    return Response(
        content=_cache["builds_bytes"],
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/ww_builds")
async def api_ww_builds():
    if _ww_cache["ww_builds_bytes"] is None:
        return JSONResponse({"error": _ww_cache.get("error", "No WW data loaded")}, status_code=503)
    return Response(
        content=_ww_cache["ww_builds_bytes"],
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/status")
async def api_status():
    if _cache["data_bytes"] is None:
        return {"ok": False, "item_count": 0, "character_count": 0,
                "last_modified": None, "error": _cache.get("error")}
    meta = json.loads(_cache["data_bytes"])["meta"]
    return {
        "ok":              True,
        "item_count":      meta["item_count"],
        "character_count": meta["character_count"],
        "last_modified":   _cache["mtime"],
        "error":           None,
    }


@app.get("/api/ability_icons")
async def api_ability_icons():
    fresh = _build_ability_icon_map()
    if fresh != _ability_icon_map:
        _ability_icon_map.clear()
        _ability_icon_map.update(fresh)
    return JSONResponse(_ability_icon_map)


@app.get("/events")
async def sse(request: Request):
    q: asyncio.Queue = asyncio.Queue(maxsize=10)
    _sse_queues.add(q)

    async def stream():
        try:
            yield "data: connected\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            _sse_queues.discard(q)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ESO Armory server")
    parser.add_argument("--port", type=int, help="Override port from config")
    args = parser.parse_args()

    _load_config()
    port = args.port or _config.get("port", 5000)
    print(f"ESO Armory → http://localhost:{port}")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level="warning",
        reload=False,
    )
