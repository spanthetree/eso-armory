"""ESO Armory — FastAPI server."""

import asyncio
import json
import os
import platform
import re
import shutil
import sys
import time
import secrets
import urllib.parse
import urllib.request
from contextlib import asynccontextmanager
from html.parser import HTMLParser
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Query, Request, UploadFile
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
SHARE_REGISTRY_PATH = UPLOADS_DIR / "share_registry.json"
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

# Per-browser-session state (keyed by UUID from localStorage)
_SESSION_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
_SESSION_TTL = 7200  # seconds before an idle session is evicted
_sessions: dict[str, dict] = {}
_share_registry: dict = {"codes": {}}

_ability_icon_map: dict = {}
_set_bonus_cache: dict  = {}  # set_id  -> {bonuses, url} or {bonuses, url, error}
_skill_info_cache: dict = {}  # slug    -> {cast_time, cost, type, location, description, ...}
_ttc_tables: dict = {
    "lookup": None,
    "price": None,
    "lookup_mtime": None,
    "price_mtime": None,
    "lookup_path": None,
    "price_path": None,
}

_SHARE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_SHARE_CODE_LEN = 8


def _load_share_registry() -> None:
    global _share_registry
    if not SHARE_REGISTRY_PATH.exists():
        _share_registry = {"codes": {}}
        return
    try:
        data = json.loads(SHARE_REGISTRY_PATH.read_text(encoding="utf-8"))
        codes = data.get("codes") if isinstance(data, dict) else {}
        if not isinstance(codes, dict):
            raise ValueError("share registry missing codes map")
        _share_registry = {"codes": codes}
    except Exception as exc:
        logger.warning("Share registry load failed: {}", exc)
        _share_registry = {"codes": {}}


def _save_share_registry() -> None:
    SHARE_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SHARE_REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(_share_registry, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(SHARE_REGISTRY_PATH)


def _normalize_share_code(code: str | None) -> str | None:
    raw = re.sub(r"[^A-Za-z0-9]", "", code or "").upper()
    if len(raw) != _SHARE_CODE_LEN:
        return None
    return f"{raw[:4]}-{raw[4:]}"


def _generate_share_code() -> str:
    while True:
        raw = "".join(secrets.choice(_SHARE_CODE_ALPHABET) for _ in range(_SHARE_CODE_LEN))
        code = f"{raw[:4]}-{raw[4:]}"
        if code not in _share_registry["codes"]:
            return code


def _session_share_code(session_id: str) -> str | None:
    for code, entry in _share_registry["codes"].items():
        if entry.get("session_id") == session_id:
            return code
    return None


def _resolve_shared_session_id(share_code: str | None) -> str | None:
    code = _normalize_share_code(share_code)
    if not code:
        return None
    entry = _share_registry["codes"].get(code)
    if not isinstance(entry, dict):
        return None
    return _valid_session(entry.get("session_id"))


def _session_is_shared(session_id: str) -> bool:
    return _session_share_code(session_id) is not None


def _share_url(code: str | None) -> str:
    code = _normalize_share_code(code)
    return f"/?share={code}" if code else ""


def _rehydrate_session_from_disk(session_id: str, sess: dict) -> None:
    upload_dir: Path = sess["upload_dir"]
    s_cache = sess["cache"]
    s_ww_cache = sess["ww_cache"]
    s_ttc_cache = sess["ttc_cache"]

    iasync_path = upload_dir / "SavedVariables" / "iasync.lua"
    if iasync_path.exists():
        _parse_iasync_into(str(iasync_path), s_cache)

    ww_path = upload_dir / "SavedVariables" / "WizardsWardrobe.lua"
    if ww_path.exists():
        _parse_ww_into(str(ww_path), s_ww_cache)

    lookup_path = upload_dir / "AddOns" / "TamrielTradeCentre" / "ItemLookUpTable_EN.lua"
    if lookup_path.exists():
        try:
            s_ttc_cache["lookup"] = _parse_lua_assignment(lookup_path, "self.ItemLookUpTable")
            s_ttc_cache["lookup_mtime"] = os.path.getmtime(lookup_path)
            s_ttc_cache["lookup_path"] = str(lookup_path)
            s_ttc_cache["error"] = None
        except Exception as exc:
            s_ttc_cache["error"] = str(exc)

    price_path = upload_dir / "AddOns" / "TamrielTradeCentre" / (
        "PriceTableEU.lua" if str(_config.get("server", "NA")).upper() == "EU" else "PriceTableNA.lua"
    )
    if not price_path.exists():
        alt = upload_dir / "AddOns" / "TamrielTradeCentre" / (
            "PriceTableNA.lua" if str(_config.get("server", "NA")).upper() == "EU" else "PriceTableEU.lua"
        )
        if alt.exists():
            price_path = alt
    if price_path.exists():
        try:
            s_ttc_cache["price"] = _parse_lua_assignment(price_path, "self.PriceTable")
            s_ttc_cache["price_mtime"] = os.path.getmtime(price_path)
            s_ttc_cache["price_path"] = str(price_path)
            s_ttc_cache["error"] = None
        except Exception as exc:
            s_ttc_cache["error"] = str(exc)


def _resolve_session_context(session_id: str | None, share_code: str | None = None) -> tuple[str | None, str | None]:
    sid = _valid_session(session_id)
    code = _normalize_share_code(share_code)
    if share_code and not code:
        return None, "invalid share code"
    if code:
        shared_sid = _resolve_shared_session_id(code)
        if not shared_sid:
            return None, "share code not found"
        return shared_sid, None
    return sid, None


def _build_ability_icon_map() -> dict:
    abilities_dir = Path("assets/abilities")
    if not abilities_dir.exists():
        return {}
    result = {}
    for icon in sorted(
        p for p in abilities_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".png", ".webp"}
    ):
        key = re.sub(r'[^a-z0-9]+', '_', icon.stem.lower()).strip('_')
        result[key] = "/" + icon.as_posix()
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


def _ttc_lookup_table_path(root: Path | None = None) -> Path:
    if root is not None:
        return root / "AddOns" / "TamrielTradeCentre" / "ItemLookUpTable_EN.lua"

    configured = _config.get("ttc_lookup_table_path") or ""
    if configured:
        p = Path(configured)
        if p.exists():
            return p

    addon = Path(_config.get("ttc_addon_path") or "")
    return addon / "ItemLookUpTable_EN.lua"


def _ttc_price_table_path(root: Path | None = None) -> Path:
    region = "EU" if str(_config.get("server", "NA")).upper() == "EU" else "NA"
    other = "NA" if region == "EU" else "EU"
    if root is not None:
        addon = root / "AddOns" / "TamrielTradeCentre"
        for candidate in (addon / f"PriceTable{region}.lua", addon / f"PriceTable{other}.lua"):
            if candidate.exists():
                return candidate
        return addon / f"PriceTable{region}.lua"

    configured = _config.get("ttc_price_table_path") or ""
    if configured:
        p = Path(configured)
        if p.exists():
            return p
    addon = Path(_config.get("ttc_addon_path") or "")
    for candidate in (addon / f"PriceTable{region}.lua", addon / f"PriceTable{other}.lua"):
        if candidate.exists():
            return candidate
    return addon / f"PriceTable{region}.lua"


def _ttc_search_url(name: str) -> str:
    region = "eu" if str(_config.get("server", "NA")).upper() == "EU" else "us"
    return f"https://{region}.tamrieltradecentre.com/pc/Trade/SearchResult?ItemNamePattern={urllib.parse.quote(name)}"


def _ensure_ttc_tables(cache: dict | None = None, root: Path | None = None) -> tuple[dict, dict, int | None, Path]:
    cache = cache or _ttc_tables
    lookup_path = _ttc_lookup_table_path(root)
    price_path = _ttc_price_table_path(root)
    lookup_mtime = os.path.getmtime(lookup_path)
    price_mtime = os.path.getmtime(price_path)

    if (
        cache["lookup"] is not None
        and cache["price"] is not None
        and cache["lookup_mtime"] == lookup_mtime
        and cache["price_mtime"] == price_mtime
        and cache["lookup_path"] == str(lookup_path)
        and cache["price_path"] == str(price_path)
    ):
        price_time = cache["price"].get("TimeStamp") if isinstance(cache["price"], dict) else None
        return cache["lookup"], cache["price"], price_time, price_path

    t0 = time.monotonic()
    lookup = _parse_lua_assignment(lookup_path, "self.ItemLookUpTable")
    price = _parse_lua_assignment(price_path, "self.PriceTable")
    cache.update({
        "lookup": lookup,
        "price": price,
        "lookup_mtime": lookup_mtime,
        "price_mtime": price_mtime,
        "lookup_path": str(lookup_path),
        "price_path": str(price_path),
    })
    cache["price_cache"] = {}
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


def _resolve_ttc_cache(session_id: str | None) -> tuple[dict, Path | None]:
    sid = _valid_session(session_id)
    if sid:
        sess = _get_or_create_session(sid)
        ttc_cache = sess["ttc_cache"]
        if ttc_cache["lookup"] is not None and ttc_cache["price"] is not None:
            return ttc_cache, sess["upload_dir"]
    return _ttc_tables, None


def _fetch_ttc_price(name: str, session_id: str | None = None) -> dict:
    clean_name = re.sub(r"\s+", " ", name or "").strip()
    url = _ttc_search_url(clean_name)
    if not clean_name:
        return {"name": clean_name, "url": url, "error": "name is required"}

    cache_key = clean_name.lower()
    cache, root = _resolve_ttc_cache(session_id)
    price_cache = cache.setdefault("price_cache", {})
    if cache_key in price_cache:
        return price_cache[cache_key]

    fetched_at = int(time.time())
    lookup, price_table, price_time, price_path = _ensure_ttc_tables(cache, root)
    item_ids = lookup.get(cache_key)
    if not isinstance(item_ids, dict):
        result = {
            "name": clean_name,
            "fetchedAt": fetched_at,
            "fetchedAtText": _fmt_ttc_time(fetched_at),
            "priceTableTime": price_time,
            "priceTableTimeText": _fmt_ttc_time(price_time),
            "source": f"TTC {'uploaded' if root is not None else 'local'} PriceTable",
            "attribution": "Data from Tamriel Trade Centre",
            "url": url,
            "error": "No TTC item match",
        }
        price_cache[cache_key] = result
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
            "source": f"TTC {'uploaded' if root is not None else 'local'} PriceTable",
            "attribution": "Data from Tamriel Trade Centre",
            "url": url,
            "error": "No TTC price data",
        }
        price_cache[cache_key] = result
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
        "source": f"TTC {'uploaded' if root is not None else 'local'} {price_path.name}",
        "attribution": "Data from Tamriel Trade Centre",
        "url": url,
    }
    price_cache[cache_key] = result
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


def _parse_iasync_into(path: str, cache: dict) -> None:
    """Parse iasync.lua at *path* and populate *cache* in-place."""
    if not path:
        cache["error"] = "iasync_lua_path not configured"
        return
    try:
        mtime = os.path.getmtime(path)
        if cache["mtime"] == mtime:
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
        cache["data_bytes"]         = json.dumps(data).encode()
        cache["builds_bytes"]       = json.dumps(builds).encode()
        cache["achievements_bytes"] = json.dumps(achievements).encode()
        cache["stickerbook_bytes"]  = json.dumps(stickerbook).encode()
        cache["mtime"]              = mtime
        cache["error"]              = None
        logger.info("iasync: {} items, {} chars in {:.2f}s",
                    data["meta"]["item_count"], data["meta"]["character_count"], elapsed)
    except FileNotFoundError:
        cache["error"] = f"iasync.lua not found: {path}"
        logger.error("iasync.lua not found: {}", path)
    except Exception as exc:
        cache["error"] = str(exc)
        logger.error("iasync parse error: {}", exc)


def _parse_iasync():
    _parse_iasync_into(_config.get("iasync_lua_path", ""), _cache)


def _parse_ww_into(path: str, cache: dict) -> None:
    """Parse WizardsWardrobe.lua at *path* and populate *cache* in-place."""
    if not path:
        cache["error"] = "ww_lua_path not configured"
        return
    try:
        mtime = os.path.getmtime(path)
        if cache["mtime"] == mtime:
            return
        logger.debug("Parsing WW: {}", path)
        raw    = parse_lua_variable(path, "WizardsWardrobeSV")
        builds = process_ww_builds(raw)
        cache["ww_builds_bytes"] = json.dumps(builds).encode()
        cache["mtime"]           = mtime
        cache["error"]           = None
        n = sum(len(v) for v in builds["builds"].values())
        logger.info("WW: {} builds", n)
    except FileNotFoundError:
        cache["error"] = f"WizardsWardrobe.lua not found: {path}"
        logger.error("WizardsWardrobe.lua not found: {}", path)
    except Exception as exc:
        cache["error"] = str(exc)
        logger.error("WW parse error: {}", exc)


def _parse_ww():
    _parse_ww_into(_config.get("ww_lua_path", ""), _ww_cache)


def _valid_session(session_id: str | None) -> str | None:
    """Return session_id if it looks like a UUID, else None."""
    if session_id and _SESSION_RE.match(session_id):
        return session_id
    return None


def _get_or_create_session(session_id: str) -> dict:
    if session_id not in _sessions:
        _sessions[session_id] = {
            "cache": {"data_bytes": None, "builds_bytes": None,
                      "achievements_bytes": None, "stickerbook_bytes": None,
                      "mtime": None, "error": None},
            "ww_cache": {"ww_builds_bytes": None, "mtime": None, "error": None},
            "ttc_cache": {
                "lookup": None,
                "price": None,
                "lookup_mtime": None,
                "price_mtime": None,
                "lookup_path": None,
                "price_path": None,
                "price_cache": {},
            },
            "upload_dir": UPLOADS_DIR / session_id,
            "sse_queues": set(),
            "last_active": time.time(),
        }
        (UPLOADS_DIR / session_id).mkdir(parents=True, exist_ok=True)
        logger.info("Session created: {}", session_id[:8])
    sess = _sessions[session_id]
    sess["last_active"] = time.time()
    if sess["cache"]["data_bytes"] is None and sess["upload_dir"].exists():
        _rehydrate_session_from_disk(session_id, sess)
    return sess


def _resolve_cache(session_id: str | None, share_code: str | None = None) -> dict:
    sid, err = _resolve_session_context(session_id, share_code)
    if err:
        return {"data_bytes": None, "builds_bytes": None, "achievements_bytes": None,
                "stickerbook_bytes": None, "mtime": None, "error": err}
    if sid:
        sess = _get_or_create_session(sid)
        sess["last_active"] = time.time()
        if sess["cache"]["data_bytes"] is not None:
            return sess["cache"]
    return _cache


def _resolve_ww_cache(session_id: str | None, share_code: str | None = None) -> dict:
    sid, err = _resolve_session_context(session_id, share_code)
    if err:
        return {"ww_builds_bytes": None, "mtime": None, "error": err}
    if sid:
        sess = _get_or_create_session(sid)
        sess["last_active"] = time.time()
        if sess["ww_cache"]["ww_builds_bytes"] is not None:
            return sess["ww_cache"]
    return _ww_cache


async def _session_cleanup():
    while True:
        await asyncio.sleep(300)
        cutoff = time.time() - _SESSION_TTL
        expired = [sid for sid, s in list(_sessions.items()) if s["last_active"] < cutoff and not _session_is_shared(sid)]
        for sid in expired:
            sess = _sessions.pop(sid, None)
            if sess:
                shutil.rmtree(sess["upload_dir"], ignore_errors=True)
                logger.info("Session expired + cleaned: {}", sid[:8])


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
    _load_share_registry()
    _parse_iasync()
    _parse_ww()
    _ability_icon_map.update(_build_ability_icon_map())
    logger.info("Ability icons: {} loaded", len(_ability_icon_map))
    asyncio.create_task(_file_watcher())
    asyncio.create_task(_session_cleanup())
    yield


app = FastAPI(title="ESO Armory", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path.startswith(("/static", "/assets")):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response
    t0 = time.monotonic()
    response = await call_next(request)
    ms = int((time.monotonic() - t0) * 1000)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    logger.info("{} {} → {} {}ms", request.method, request.url.path, response.status_code, ms)
    return response


@app.get("/")
async def root():
    return FileResponse(
        "static/index.html",
        media_type="text/html; charset=utf-8",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.head("/")
async def root_head():
    return Response(
        media_type="text/html; charset=utf-8",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.get("/api/data")
async def api_data(session: str | None = Query(None), share: str | None = Query(None)):
    cache = _resolve_cache(session, share)
    if cache["data_bytes"] is None:
        return JSONResponse({"error": cache.get("error", "No data loaded")}, status_code=503)
    return Response(
        content=cache["data_bytes"],
        media_type="application/json",
        headers={"ETag": str(cache["mtime"]), "Cache-Control": "no-store"},
    )


@app.get("/api/builds")
async def api_builds(session: str | None = Query(None), share: str | None = Query(None)):
    cache = _resolve_cache(session, share)
    if cache["builds_bytes"] is None:
        return JSONResponse({"error": cache.get("error", "No data loaded")}, status_code=503)
    return Response(
        content=cache["builds_bytes"],
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/achievements")
async def api_achievements(session: str | None = Query(None), share: str | None = Query(None)):
    cache = _resolve_cache(session, share)
    if cache["achievements_bytes"] is None:
        return JSONResponse({"error": cache.get("error", "No data loaded")}, status_code=503)
    return Response(
        content=cache["achievements_bytes"],
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/stickerbook")
async def api_stickerbook(session: str | None = Query(None), share: str | None = Query(None)):
    cache = _resolve_cache(session, share)
    if cache["stickerbook_bytes"] is None:
        return JSONResponse({"error": cache.get("error", "No data loaded")}, status_code=503)
    return Response(
        content=cache["stickerbook_bytes"],
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/ww_builds")
async def api_ww_builds(session: str | None = Query(None), share: str | None = Query(None)):
    ww = _resolve_ww_cache(session, share)
    if ww["ww_builds_bytes"] is None:
        return JSONResponse({"error": ww.get("error", "No WW data loaded")}, status_code=503)
    return Response(
        content=ww["ww_builds_bytes"],
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/status")
async def api_status(session: str | None = Query(None), share: str | None = Query(None)):
    cache = _resolve_cache(session, share)
    if cache["data_bytes"] is None:
        return {"ok": False, "item_count": 0, "character_count": 0,
                "last_modified": None, "error": cache.get("error")}
    meta = json.loads(cache["data_bytes"])["meta"]
    return {
        "ok":              True,
        "item_count":      meta["item_count"],
        "character_count": meta["character_count"],
        "last_modified":   cache["mtime"],
        "error":           None,
    }


@app.post("/api/upload")
async def api_upload(
    iasync: UploadFile | None = File(None),
    ww:     UploadFile | None = File(None),
    ttc_lookup: UploadFile | None = File(None),
    ttc_price: UploadFile | None = File(None),
    session: str | None = Query(None),
    share: str | None = Query(None),
):
    """Accept uploaded live-folder files for iasync, WW, and TTC tables."""
    sid, err = _resolve_session_context(session, share)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)

    sess = _get_or_create_session(sid)
    upload_dir: Path = sess["upload_dir"]
    s_cache    = sess["cache"]
    s_ww_cache = sess["ww_cache"]
    s_ttc_cache = sess["ttc_cache"]

    loop = asyncio.get_event_loop()
    results = {}

    def _write_upload(dest: Path, data: bytes) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    if iasync and iasync.filename:
        dest = upload_dir / "SavedVariables" / "iasync.lua"
        data = await iasync.read()
        _write_upload(dest, data)
        s_cache["mtime"] = None
        iasync_path = str(dest)
        await loop.run_in_executor(None, lambda: _parse_iasync_into(iasync_path, s_cache))
        if s_cache["error"]:
            results["iasync"] = {"ok": False, "error": s_cache["error"]}
        else:
            meta = json.loads(s_cache["data_bytes"])["meta"]
            results["iasync"] = {"ok": True, "items": meta["item_count"], "chars": meta["character_count"]}
            for q in list(sess["sse_queues"]):
                try:
                    q.put_nowait("reload")
                except asyncio.QueueFull:
                    pass
        logger.info("Session {} uploaded iasync.lua ({} bytes)", sid[:8], len(data))

    if ww and ww.filename:
        dest = upload_dir / "SavedVariables" / "WizardsWardrobe.lua"
        data = await ww.read()
        _write_upload(dest, data)
        s_ww_cache["mtime"] = None
        ww_path = str(dest)
        await loop.run_in_executor(None, lambda: _parse_ww_into(ww_path, s_ww_cache))
        if s_ww_cache["error"]:
            results["ww"] = {"ok": False, "error": s_ww_cache["error"]}
        else:
            builds = json.loads(s_ww_cache["ww_builds_bytes"])
            n = sum(len(v) for v in builds["builds"].values())
            results["ww"] = {"ok": True, "builds": n}
        logger.info("Session {} uploaded WizardsWardrobe.lua ({} bytes)", sid[:8], len(data))

    if ttc_lookup and ttc_lookup.filename:
        dest = upload_dir / "AddOns" / "TamrielTradeCentre" / "ItemLookUpTable_EN.lua"
        data = await ttc_lookup.read()
        _write_upload(dest, data)
        s_ttc_cache["lookup"] = None
        s_ttc_cache["price_cache"] = {}
        try:
            s_ttc_cache["lookup"] = _parse_lua_assignment(dest, "self.ItemLookUpTable")
            s_ttc_cache["lookup_mtime"] = os.path.getmtime(dest)
            s_ttc_cache["lookup_path"] = str(dest)
            s_ttc_cache["error"] = None
            results["ttc_lookup"] = {"ok": True}
        except Exception as exc:
            s_ttc_cache["error"] = str(exc)
            results["ttc_lookup"] = {"ok": False, "error": str(exc)}
        logger.info("Session {} uploaded TTC lookup ({} bytes)", sid[:8], len(data))

    if ttc_price and ttc_price.filename:
        dest = upload_dir / "AddOns" / "TamrielTradeCentre" / ("PriceTableEU.lua" if str(_config.get("server", "NA")).upper() == "EU" else "PriceTableNA.lua")
        data = await ttc_price.read()
        _write_upload(dest, data)
        s_ttc_cache["price"] = None
        s_ttc_cache["price_cache"] = {}
        try:
            s_ttc_cache["price"] = _parse_lua_assignment(dest, "self.PriceTable")
            s_ttc_cache["price_mtime"] = os.path.getmtime(dest)
            s_ttc_cache["price_path"] = str(dest)
            s_ttc_cache["error"] = None
            results["ttc_price"] = {"ok": True}
        except Exception as exc:
            s_ttc_cache["error"] = str(exc)
            results["ttc_price"] = {"ok": False, "error": str(exc)}
        logger.info("Session {} uploaded TTC price table ({} bytes)", sid[:8], len(data))

    if not results:
        return JSONResponse({"error": "No files received"}, status_code=400)
    return JSONResponse(results)


@app.get("/api/share")
async def api_share(session: str | None = Query(None), share: str | None = Query(None)):
    sid, err = _resolve_session_context(session, share)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    sess = _get_or_create_session(sid)
    code = _session_share_code(sid)
    return JSONResponse({
        "code": code,
        "shareUrl": _share_url(code),
        "shared": bool(code),
        "session": sid,
        "sharedSession": sid if code else None,
    })


@app.post("/api/share")
async def api_share_create(session: str | None = Query(None), share: str | None = Query(None)):
    sid, err = _resolve_session_context(session, share)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    sess = _get_or_create_session(sid)
    code = _session_share_code(sid)
    if not code:
        code = _generate_share_code()
        _share_registry["codes"][code] = {
            "session_id": sid,
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
        }
        _save_share_registry()
        logger.info("Share code created for session {}: {}", sid[:8], code)
    sess["last_active"] = time.time()
    return JSONResponse({
        "code": code,
        "shareUrl": _share_url(code),
        "shared": True,
        "session": sid,
        "sharedSession": sid,
    })


@app.post("/api/share/join")
async def api_share_join(session: str | None = Query(None), code: str | None = Query(None)):
    sid = _valid_session(session)
    normalized = _normalize_share_code(code)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    if not normalized:
        return JSONResponse({"error": "valid pairing code required"}, status_code=400)
    shared_sid = _resolve_shared_session_id(normalized)
    if not shared_sid:
        return JSONResponse({"error": "pairing code not found"}, status_code=404)
    sess = _get_or_create_session(shared_sid)
    sess["last_active"] = time.time()
    return JSONResponse({
        "code": normalized,
        "shareUrl": _share_url(normalized),
        "shared": True,
        "session": sid,
        "sharedSession": shared_sid,
    })


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
async def api_ttc_price(name: str, session: str | None = Query(None), share: str | None = Query(None)):
    try:
        sid, err = _resolve_session_context(session, share)
        if err:
            return JSONResponse({"error": err}, status_code=400)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: _fetch_ttc_price(name, sid))
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
async def sse(request: Request, session: str | None = Query(None), share: str | None = Query(None)):
    client = request.client.host if request.client else "unknown"
    q: asyncio.Queue = asyncio.Queue(maxsize=10)

    sid, err = _resolve_session_context(session, share)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    if sid and sid in _sessions and _sessions[sid]["cache"]["data_bytes"] is not None:
        target: set = _sessions[sid]["sse_queues"]
    else:
        target = _sse_queues
    target.add(q)
    logger.info("SSE connect: {} (session={})", client, sid[:8] if sid else "global")

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
            target.discard(q)
            logger.info("SSE disconnect: {} (session={})", client, sid[:8] if sid else "global")

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
