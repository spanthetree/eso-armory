"""ESO Armory — FastAPI server."""

import asyncio
import json
import os
import platform
import re
import sys
import time
import urllib.parse
import urllib.request
from contextlib import asynccontextmanager
from html.parser import HTMLParser
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from lua_parser import LuaParser, parse_lua_variable
from data_processor import process_iasync, process_iasync_builds, process_iasync_achievements, process_iasync_stickerbook, process_ww_builds


def _setup_logging():
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )
    Path("logs").mkdir(exist_ok=True)
    logger.add(
        "logs/armory.log",
        level="DEBUG",
        rotation="10 MB",
        retention=5,
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    )


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


def _eso_addon_path(*parts: str) -> str:
    """Return the platform-appropriate path inside the ESO AddOns folder."""
    eso_rel = Path("Elder Scrolls Online") / "live" / "AddOns" / Path(*parts)
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


CONFIG_PATH  = Path("config.json")
UPLOADS_DIR  = Path("uploads")
DEFAULT_CONFIG = {
    "iasync_lua_path": _eso_sv_path("iasync.lua"),
    "ww_lua_path":     _eso_sv_path("WizardsWardrobe.lua"),
    "ttc_addon_path":  _eso_addon_path("TamrielTradeCentre"),
    "ttc_lookup_table_path": _eso_addon_path("TamrielTradeCentre", "ItemLookUpTable_EN.lua"),
    "ttc_price_table_path":  "",
    "port": 5000,
    "server": "NA",
    "poll_interval_seconds": 5,
}

_config: dict = {}
_cache: dict = {
    "data_bytes":         None,
    "builds_bytes":       None,
    "achievements_bytes":  None,
    "stickerbook_bytes":   None,
    "mtime":               None,
    "error":               None,
}
_ww_cache: dict = {
    "ww_builds_bytes": None,
    "mtime":           None,
    "error":           None,
}
_sse_queues: set[asyncio.Queue] = set()
_ability_icon_map: dict = {}
_set_bonus_cache: dict  = {}  # set_id  -> {bonuses, url} or {bonuses, url, error}
_skill_info_cache: dict = {}  # slug    -> {cast_time, cost, type, location, description, ...}
_ttc_tables: dict = {"lookup": None, "price": None, "lookup_mtime": None, "price_mtime": None, "price_path": None}
_ttc_price_cache: dict = {}


def _build_ability_icon_map() -> dict:
    abilities_dir = Path("assets/abilities")
    if not abilities_dir.exists():
        return {}
    result = {}
    for png in sorted(abilities_dir.rglob("*.png")):
        key = re.sub(r'[^a-z0-9]+', '_', png.stem.lower()).strip('_')
        result[key] = "/" + png.as_posix()
    return result


class _TextExtractor(HTMLParser):
    _SKIP  = frozenset({'script', 'style', 'noscript', 'head'})
    _BLOCK = frozenset({
        'div', 'p', 'li', 'ol', 'ul', 'tr', 'td', 'th', 'br',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'section', 'article', 'header', 'footer', 'nav', 'main',
    })

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._depth: int = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._SKIP:
            self._depth += 1
        elif tag in self._BLOCK and self._depth == 0:
            self._parts.append('\n')

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._depth > 0:
            self._depth -= 1
        elif tag in self._BLOCK and self._depth == 0:
            self._parts.append('\n')

    def handle_data(self, data: str) -> None:
        if self._depth == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        raw = ''.join(self._parts)
        lines = [re.sub(r'[ \t]+', ' ', ln).strip() for ln in raw.split('\n')]
        return '\n'.join(ln for ln in lines if ln)


def _set_name_to_slug(name: str) -> str:
    slug = re.sub(r"['‘’‚′]", "", name)
    slug = slug.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    return slug.strip('-')


_BONUS_LINE = re.compile(r'^\((\d+)\s+items?\)\s*(.*)$')
# Lines that mark end of a set's bonus block (metadata / page chrome)
_META_LINE  = re.compile(
    r'^(?:Name:|Type:|Location:|Obtainable|LEVEL\s+\d|Drop\s|ArmorSet|Found a mistake|Discord|ESO-Hub)'
)


def _fetch_set_bonuses(slug: str) -> list[dict]:
    url = f"https://eso-sets.com/set/{slug}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ESO-Armory/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    extractor = _TextExtractor()
    extractor.feed(html)
    lines = [l for l in extractor.get_text().split('\n') if l.strip()]

    bonuses: list[dict] = []
    last_pieces  = 0
    cur_pieces:   int | None = None
    cur_parts:    list[str]  = []

    def _flush():
        nonlocal cur_pieces, cur_parts
        if cur_pieces is not None and cur_parts:
            bonuses.append({"pieces": cur_pieces, "text": ' '.join(cur_parts)})
        cur_pieces = None
        cur_parts = []

    for line in lines:
        bm = _BONUS_LINE.match(line)
        if bm:
            _flush()
            pieces = int(bm.group(1))
            if pieces <= last_pieces:
                break  # piece count reset → entered a new set's section
            cur_pieces  = pieces
            last_pieces = pieces
            text = bm.group(2).strip()
            if text:
                cur_parts = [text]
        elif cur_pieces is not None:
            if _META_LINE.match(line):
                _flush()
                # A meta line after collecting bonuses means we've crossed into a
                # related set's section (common on mythic pages); stop here.
                if bonuses:
                    break
            else:
                cur_parts.append(line)

    _flush()
    return bonuses


_SKILL_STOP = re.compile(
    r'^(?:New effect|Name:|Other morph|Base ability|Found a mistake|Discord|Skills and icons)'
)


def _fetch_skill_info(slug: str) -> dict:
    url = f"https://eso-skillbook.com/skill/{slug}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ESO-Armory/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    extractor = _TextExtractor()
    extractor.feed(html)
    lines = [l for l in extractor.get_text().split('\n') if l.strip()]

    result: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]

        if "cast_time" not in result and (m := re.match(r'^Cast Time:\s*(.+)$', line)):
            try:
                ms = int(m.group(1).strip())
                result["cast_time"] = "Instant" if ms == 0 else f"{ms / 1000:.1f}s"
            except ValueError:
                result["cast_time"] = m.group(1).strip()

        elif "target" not in result and (m := re.match(r'^Target:\s*(.+)$', line)):
            result["target"] = m.group(1).strip()

        elif "range" not in result and (m := re.match(r'^Range:\s*(.+)$', line)):
            result["range"] = m.group(1).strip()

        elif "cost" not in result and (m := re.match(r'^Cost:\s*(.+)$', line)):
            result["cost"] = m.group(1).strip()

        elif "type" not in result and (m := re.match(r'^Type:\s*(.+)$', line)):
            result["type"] = m.group(1).strip()

        elif "location" not in result and (m := re.match(r'^Location:\s*(.+)$', line)):
            result["location"] = m.group(1).strip()

        elif "description" not in result and line == "Skill description":
            parts: list[str] = []
            i += 1
            while i < len(lines) and not _SKILL_STOP.match(lines[i]):
                parts.append(lines[i])
                i += 1
            result["description"] = ' '.join(parts)
            continue  # i already past description; let outer loop process stop line

        i += 1

    return result


def _parse_lua_assignment(path: Path, lhs: str) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    marker = f"{lhs}="
    idx = text.find(marker)
    if idx == -1:
        marker = f"{lhs} ="
        idx = text.find(marker)
    if idx == -1:
        raise ValueError(f"Lua assignment {lhs!r} not found in {path}")
    parser = LuaParser(text)
    parser.pos = idx + len(marker)
    return parser._parse_value()


def _ttc_price_table_path() -> Path:
    configured = _config.get("ttc_price_table_path") or ""
    if configured:
        p = Path(configured)
        if p.exists():
            return p
    region = "EU" if str(_config.get("server", "NA")).upper() == "EU" else "NA"
    addon = Path(_config.get("ttc_addon_path") or "")
    return addon / f"PriceTable{region}.lua"


def _ttc_search_url(name: str) -> str:
    region = "eu" if str(_config.get("server", "NA")).upper() == "EU" else "us"
    return f"https://{region}.tamrieltradecentre.com/pc/Trade/SearchResult?ItemNamePattern={urllib.parse.quote(name)}"


def _ensure_ttc_tables() -> tuple[dict, dict, int | None, Path]:
    lookup_path = Path(_config.get("ttc_lookup_table_path") or "")
    price_path = _ttc_price_table_path()
    lookup_mtime = os.path.getmtime(lookup_path)
    price_mtime = os.path.getmtime(price_path)

    if (
        _ttc_tables["lookup"] is not None
        and _ttc_tables["price"] is not None
        and _ttc_tables["lookup_mtime"] == lookup_mtime
        and _ttc_tables["price_mtime"] == price_mtime
        and _ttc_tables["price_path"] == str(price_path)
    ):
        price_time = _ttc_tables["price"].get("TimeStamp") if isinstance(_ttc_tables["price"], dict) else None
        return _ttc_tables["lookup"], _ttc_tables["price"], price_time, price_path

    t0 = time.monotonic()
    lookup = _parse_lua_assignment(lookup_path, "self.ItemLookUpTable")
    price = _parse_lua_assignment(price_path, "self.PriceTable")
    _ttc_tables.update({
        "lookup": lookup,
        "price": price,
        "lookup_mtime": lookup_mtime,
        "price_mtime": price_mtime,
        "price_path": str(price_path),
    })
    _ttc_price_cache.clear()
    logger.info("TTC tables loaded from {} in {:.2f}s", price_path.name, time.monotonic() - t0)
    return lookup, price, price.get("TimeStamp"), price_path


def _first_ttc_item_id(item_ids_by_specialized_type: dict) -> int | None:
    for item_id in item_ids_by_specialized_type.values():
        if isinstance(item_id, int):
            return item_id
    return None


def _first_ttc_price_dict(node, trail: list[int | str] | None = None) -> tuple[dict | None, list[int | str]]:
    trail = trail or []
    if isinstance(node, dict):
        if any(k in node for k in ("A", "Avg")):
            return node, trail
        for key, value in node.items():
            found, found_trail = _first_ttc_price_dict(value, trail + [key])
            if found is not None:
                return found, found_trail
    return None, trail


def _fmt_ttc_time(ts) -> str | None:
    if not isinstance(ts, (int, float)):
        return None
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    except (OverflowError, OSError, ValueError):
        return None


def _fetch_ttc_price(name: str) -> dict:
    clean_name = re.sub(r"\s+", " ", name or "").strip()
    url = _ttc_search_url(clean_name)
    if not clean_name:
        return {"name": clean_name, "url": url, "error": "name is required"}

    cache_key = clean_name.lower()
    if cache_key in _ttc_price_cache:
        return _ttc_price_cache[cache_key]

    fetched_at = int(time.time())
    lookup, price_table, price_time, price_path = _ensure_ttc_tables()
    item_ids = lookup.get(cache_key)
    if not isinstance(item_ids, dict):
        result = {
            "name": clean_name,
            "fetchedAt": fetched_at,
            "fetchedAtText": _fmt_ttc_time(fetched_at),
            "priceTableTime": price_time,
            "priceTableTimeText": _fmt_ttc_time(price_time),
            "source": "TTC local PriceTable",
            "attribution": "Data from Tamriel Trade Centre",
            "url": url,
            "error": "No TTC item match",
        }
        _ttc_price_cache[cache_key] = result
        return result

    item_id = _first_ttc_item_id(item_ids)
    item_node = (price_table.get("Data") or {}).get(item_id) if item_id is not None else None
    price, trail = _first_ttc_price_dict(item_node)
    if not price:
        result = {
            "name": clean_name,
            "itemId": item_id,
            "fetchedAt": fetched_at,
            "fetchedAtText": _fmt_ttc_time(fetched_at),
            "priceTableTime": price_time,
            "priceTableTimeText": _fmt_ttc_time(price_time),
            "source": "TTC local PriceTable",
            "attribution": "Data from Tamriel Trade Centre",
            "url": url,
            "error": "No TTC price data",
        }
        _ttc_price_cache[cache_key] = result
        return result

    result = {
        "name": clean_name,
        "itemId": item_id,
        "avg": price.get("Avg", price.get("A")),
        "min": price.get("Min", price.get("N")),
        "max": price.get("Max", price.get("X")),
        "entryCount": price.get("EntryCount", price.get("EC")),
        "amountCount": price.get("AmountCount", price.get("AC")),
        "suggestedPrice": price.get("SuggestedPrice", price.get("S")),
        "saleAvg": price.get("SaleAvg", price.get("SA")),
        "saleEntryCount": price.get("SaleEntryCount", price.get("SE")),
        "saleAmountCount": price.get("SaleAmountCount", price.get("SAC")),
        "variantPath": trail,
        "priceTableTime": price_time,
        "priceTableTimeText": _fmt_ttc_time(price_time),
        "fetchedAt": fetched_at,
        "fetchedAtText": _fmt_ttc_time(fetched_at),
        "source": f"TTC local {price_path.name}",
        "attribution": "Data from Tamriel Trade Centre",
        "url": url,
    }
    _ttc_price_cache[cache_key] = result
    return result


def _load_config():
    global _config
    if CONFIG_PATH.exists():
        _config = json.loads(CONFIG_PATH.read_text())
    else:
        _config = dict(DEFAULT_CONFIG)
        CONFIG_PATH.write_text(json.dumps(_config, indent=2))
        logger.info("Created default config: {}", CONFIG_PATH)
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
        logger.debug("Parsing iasync: {}", path)
        t0 = time.monotonic()
        raw          = parse_lua_variable(path, "iasync_data")
        data         = process_iasync(raw, server=_config.get("server", "NA"))
        builds       = process_iasync_builds(raw)
        achievements = process_iasync_achievements(raw)
        stickerbook  = process_iasync_stickerbook(raw)
        elapsed = time.monotonic() - t0
        data["meta"]["parse_ms"] = int(elapsed * 1000)
        _cache["data_bytes"]          = json.dumps(data).encode()
        _cache["builds_bytes"]        = json.dumps(builds).encode()
        _cache["achievements_bytes"]  = json.dumps(achievements).encode()
        _cache["stickerbook_bytes"]   = json.dumps(stickerbook).encode()
        _cache["mtime"]              = mtime
        _cache["error"]              = None
        n = data["meta"]["item_count"]
        c = data["meta"]["character_count"]
        logger.info("iasync: {} items, {} chars in {:.2f}s", n, c, elapsed)
    except FileNotFoundError:
        _cache["error"] = f"iasync.lua not found: {path}"
        logger.error("iasync.lua not found: {}", path)
    except Exception as exc:
        _cache["error"] = str(exc)
        logger.error("iasync parse error: {}", exc)


def _parse_ww():
    path = _config.get("ww_lua_path", "")
    if not path:
        _ww_cache["error"] = "ww_lua_path not configured"
        return
    try:
        mtime = os.path.getmtime(path)
        if _ww_cache["mtime"] == mtime:
            return
        logger.debug("Parsing WW: {}", path)
        raw    = parse_lua_variable(path, "WizardsWardrobeSV")
        builds = process_ww_builds(raw)
        _ww_cache["ww_builds_bytes"] = json.dumps(builds).encode()
        _ww_cache["mtime"]           = mtime
        _ww_cache["error"]           = None
        n = sum(len(v) for v in builds["builds"].values())
        logger.info("WW: {} builds", n)
    except FileNotFoundError:
        _ww_cache["error"] = f"WizardsWardrobe.lua not found: {path}"
        logger.error("WizardsWardrobe.lua not found: {}", path)
    except Exception as exc:
        _ww_cache["error"] = str(exc)
        logger.error("WW parse error: {}", exc)


async def _file_watcher():
    while True:
        await asyncio.sleep(_config.get("poll_interval_seconds", 5))
        loop = asyncio.get_event_loop()

        iasync_path = _config.get("iasync_lua_path", "")
        if iasync_path:
            try:
                mtime = os.path.getmtime(iasync_path)
                if mtime != _cache["mtime"]:
                    prev_mtime = _cache["mtime"]
                    await loop.run_in_executor(None, _parse_iasync)
                    if _cache["mtime"] != prev_mtime:
                        for q in list(_sse_queues):
                            try:
                                q.put_nowait("reload")
                            except asyncio.QueueFull:
                                pass
            except Exception as exc:
                logger.warning("File watcher error (iasync): {}", exc)

        ww_path = _config.get("ww_lua_path", "")
        if ww_path:
            try:
                mtime = os.path.getmtime(ww_path)
                if mtime != _ww_cache["mtime"]:
                    await loop.run_in_executor(None, _parse_ww)
            except Exception as exc:
                logger.warning("File watcher error (WW): {}", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_logging()
    UPLOADS_DIR.mkdir(exist_ok=True)
    _load_config()
    _parse_iasync()
    _parse_ww()
    _ability_icon_map.update(_build_ability_icon_map())
    logger.info("Ability icons: {} loaded", len(_ability_icon_map))
    asyncio.create_task(_file_watcher())
    yield


app = FastAPI(title="ESO Armory", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path.startswith(("/static", "/assets")):
        return await call_next(request)
    t0 = time.monotonic()
    response = await call_next(request)
    ms = int((time.monotonic() - t0) * 1000)
    logger.info("{} {} → {} {}ms", request.method, request.url.path, response.status_code, ms)
    return response


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


@app.get("/api/achievements")
async def api_achievements():
    if _cache["achievements_bytes"] is None:
        return JSONResponse({"error": _cache.get("error", "No data loaded")}, status_code=503)
    return Response(
        content=_cache["achievements_bytes"],
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/stickerbook")
async def api_stickerbook():
    if _cache["stickerbook_bytes"] is None:
        return JSONResponse({"error": _cache.get("error", "No data loaded")}, status_code=503)
    return Response(
        content=_cache["stickerbook_bytes"],
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


@app.post("/api/upload")
async def api_upload(
    iasync: UploadFile | None = File(None),
    ww:     UploadFile | None = File(None),
):
    """Accept uploaded iasync.lua and/or WizardsWardrobe.lua files."""
    loop = asyncio.get_event_loop()
    results = {}

    if iasync and iasync.filename:
        dest = UPLOADS_DIR / "iasync.lua"
        data = await iasync.read()
        dest.write_bytes(data)
        _config["iasync_lua_path"] = str(dest)
        # Reset mtime so _parse_iasync re-parses
        _cache["mtime"] = None
        await loop.run_in_executor(None, _parse_iasync)
        if _cache["error"]:
            results["iasync"] = {"ok": False, "error": _cache["error"]}
        else:
            meta = json.loads(_cache["data_bytes"])["meta"]
            results["iasync"] = {"ok": True, "items": meta["item_count"], "chars": meta["character_count"]}
            for q in list(_sse_queues):
                try:
                    q.put_nowait("reload")
                except asyncio.QueueFull:
                    pass
        logger.info("Uploaded iasync.lua ({} bytes) → {}", len(data), dest)

    if ww and ww.filename:
        dest = UPLOADS_DIR / "WizardsWardrobe.lua"
        data = await ww.read()
        dest.write_bytes(data)
        _config["ww_lua_path"] = str(dest)
        _ww_cache["mtime"] = None
        await loop.run_in_executor(None, _parse_ww)
        if _ww_cache["error"]:
            results["ww"] = {"ok": False, "error": _ww_cache["error"]}
        else:
            builds = json.loads(_ww_cache["ww_builds_bytes"])
            n = sum(len(v) for v in builds["builds"].values())
            results["ww"] = {"ok": True, "builds": n}
        logger.info("Uploaded WizardsWardrobe.lua ({} bytes) → {}", len(data), dest)

    if not results:
        return JSONResponse({"error": "No files received"}, status_code=400)
    return JSONResponse(results)


@app.get("/api/set_bonus")
async def api_set_bonus(set_id: int, set_name: str):
    slug = _set_name_to_slug(set_name)
    cache_key = set_id if set_id else slug
    if cache_key in _set_bonus_cache:
        return JSONResponse(_set_bonus_cache[cache_key])
    url = f"https://eso-sets.com/set/{slug}"
    try:
        loop = asyncio.get_event_loop()
        bonuses = await loop.run_in_executor(None, lambda: _fetch_set_bonuses(slug))
        result: dict = {"bonuses": bonuses, "url": url}
        logger.info("Set bonus: {} → {} bonuses", set_name, len(bonuses))
    except Exception as exc:
        result = {"bonuses": [], "url": url, "error": str(exc)}
        logger.warning("Set bonus fetch failed: {} — {}", set_name, exc)
    _set_bonus_cache[cache_key] = result
    return JSONResponse(result)


@app.get("/api/skill_info")
async def api_skill_info(name: str):
    slug = _set_name_to_slug(name)
    if slug in _skill_info_cache:
        return JSONResponse(_skill_info_cache[slug])
    url = f"https://eso-skillbook.com/skill/{slug}"
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: _fetch_skill_info(slug))
        result: dict = {**info, "url": url}
        logger.info("Skill info: {} → {}", name, list(info.keys()))
    except Exception as exc:
        result = {"url": url, "error": str(exc)}
        logger.warning("Skill info fetch failed: {} — {}", name, exc)
    _skill_info_cache[slug] = result
    return JSONResponse(result)


@app.get("/api/ttc_price")
async def api_ttc_price(name: str):
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: _fetch_ttc_price(name))
        logger.info("TTC price: {} → {}", name, "ok" if not result.get("error") else result.get("error"))
    except Exception as exc:
        result = {
            "name": name,
            "fetchedAt": int(time.time()),
            "fetchedAtText": _fmt_ttc_time(int(time.time())),
            "source": "TTC",
            "attribution": "Data from Tamriel Trade Centre",
            "url": _ttc_search_url(name),
            "error": str(exc),
        }
        logger.warning("TTC price fetch failed: {} — {}", name, exc)
    return JSONResponse(result)


@app.get("/api/ability_icons")
async def api_ability_icons():
    fresh = _build_ability_icon_map()
    if fresh != _ability_icon_map:
        _ability_icon_map.clear()
        _ability_icon_map.update(fresh)
    return JSONResponse(_ability_icon_map)


@app.get("/events")
async def sse(request: Request):
    client = request.client.host if request.client else "unknown"
    q: asyncio.Queue = asyncio.Queue(maxsize=10)
    _sse_queues.add(q)
    logger.info("SSE connect: {}", client)

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
            logger.info("SSE disconnect: {}", client)

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

    _setup_logging()
    _load_config()
    port = args.port or _config.get("port", 5000)
    logger.info("ESO Armory → http://localhost:{}", port)
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level="warning",
        reload=False,
    )
