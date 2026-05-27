"""ESO Armory — FastAPI server."""

import asyncio
import base64
import collections
import json
import os
import platform
import shutil
import re
import sqlite3
import sys
import threading
import time
import secrets
import urllib.parse
import urllib.request
import gc
from contextlib import asynccontextmanager
from html.parser import HTMLParser
from pathlib import Path

import bcrypt
import uvicorn
from fastapi import FastAPI, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from lua_parser import LuaParser, parse_iasync_core_text, parse_lua_text_variable
from data_processor import process_iasync, process_iasync_builds, process_iasync_achievements, process_iasync_stickerbook, process_ww_builds
from db import (
    AccountPayload,
    bind_session as _db_bind_session,
    delete_imported_build as _db_delete_imported_build,
    delete_shadow_slot as _db_delete_shadow_slot,
    find_share_code_for_account as _db_find_share_code_for_account,
    find_session_for_account as _db_find_session_for_account,
    get_account_state as _db_get_account_state,
    get_account_state_for_session as _db_get_account_state_for_session,
    get_or_create_share_code as _db_get_or_create_share_code,
    get_workspace_binding as _db_get_workspace_binding,
    init_db as _db_init,
    list_imported_builds as _db_list_imported_builds,
    resolve_account_for_share_code as _db_resolve_account_for_share_code,
    resolve_build_export as _db_resolve_build_export,
    session_slot_for_account as _db_session_slot_for_account,
    set_active_slot as _db_set_active_slot,
    touch_session as _db_touch_session,
    update_account_blobs as _db_update_account_blobs,
    upsert_build_export_for_character as _db_upsert_build_export_for_character,
    upsert_imported_build as _db_upsert_imported_build,
    upsert_account_payload as _db_upsert_account_payload,
    save_session_api_key as _db_save_session_api_key,
    get_session_api_key as _db_get_session_api_key,
    delete_session_api_key as _db_delete_session_api_key,
    set_account_password as _db_set_account_password,
    get_account_password_hash as _db_get_account_password_hash,
    is_account_admin as _db_is_account_admin,
)


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


_HERE        = Path(__file__).resolve().parent
CONFIG_PATH  = _HERE / "config.json"
UPLOADS_DIR  = _HERE / "uploads"
SHARE_REGISTRY_PATH = UPLOADS_DIR / "share_registry.json"
DEFAULT_CONFIG = {
    "ttc_addon_path":  _eso_addon_path("TamrielTradeCentre"),
    "ttc_lookup_table_path": _eso_addon_path("TamrielTradeCentre", "ItemLookUpTable_EN.lua"),
    "ttc_price_table_path":  "",
    "port": 5000,
    "server": "NA",
    "database_url": "sqlite:///uploads/armory.db",
}

_config: dict = {}
_cache: dict = {
    "data_bytes":         None,
    "builds_bytes":       None,
    "achievements_bytes": None,
    "stickerbook_bytes":  None,
    "mtime":              None,
    "error":              None,
    "meta":               None,
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
_SESSION_MEMORY_TTL = 1800  # seconds before idle session memory is evicted
_MAX_LOADED_SESSIONS = 2
_sessions: dict[str, dict] = {}
_share_registry: dict = {"codes": {}}

_ability_icon_map: dict = {}
_set_bonus_cache: collections.OrderedDict = collections.OrderedDict()  # set_id -> payload
_skill_info_cache: collections.OrderedDict = collections.OrderedDict()  # slug -> payload
_ttc_tables: dict = {
    "lookup_mtime": None,
    "price_mtime": None,
    "lookup_path": None,
    "price_path": None,
    "db_path": None,
    "db_ready": False,
    "price_time": None,
    "price_cache": collections.OrderedDict(),
}

_db_fernet = None       # Fernet instance for encrypting per-session API keys

_SHARE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_SHARE_CODE_LEN = 8
_BUILD_CODE_ALPHABET = _SHARE_CODE_ALPHABET
_BUILD_CODE_LEN = 8
_EXTERNAL_CACHE_MAX = 256
_TTC_PRICE_CACHE_MAX = 512
_IASYNC_PARSE_LOCK = threading.Lock()
_WW_PARSE_LOCK = threading.Lock()

# Upload limits
_MAX_UPLOAD_BYTES = 100 * 1024 * 1024   # 100 MB per file
_MAX_IMAGE_BYTES  = 20  * 1024 * 1024   # 20 MB for SuperStar images

# Login brute-force protection (in-memory, resets on server restart)
_LOGIN_FAILURES: dict[str, list[float]] = {}  # ip → list of failure timestamps
_LOGIN_WINDOW   = 60    # seconds to count failures in
_LOGIN_MAX_FAILS = 5    # failures before lockout
_LOGIN_LOCKOUT  = 300   # seconds to lock out an IP
_login_lock     = threading.Lock()

# SSE connection cap per session (prevents trivial connection exhaustion)
_MAX_SSE_PER_SESSION = 10
_TTC_BUILD_LOCK = threading.Lock()


def _json_bytes(obj: dict) -> bytes:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _lru_get(cache: collections.OrderedDict, key):
    if key not in cache:
        return None
    cache.move_to_end(key)
    return cache[key]


def _lru_put(cache: collections.OrderedDict, key, value, limit: int) -> None:
    cache[key] = value
    cache.move_to_end(key)
    while len(cache) > limit:
        cache.popitem(last=False)


def _check_login_rate_limit(ip: str) -> bool:
    """Return True if the IP is currently locked out."""
    now = time.time()
    with _login_lock:
        failures = _LOGIN_FAILURES.get(ip, [])
        # Prune old entries
        failures = [t for t in failures if now - t < _LOGIN_WINDOW]
        _LOGIN_FAILURES[ip] = failures
        if len(failures) >= _LOGIN_MAX_FAILS:
            # Check if still within lockout window from the first failure in the window
            if now - failures[0] < _LOGIN_LOCKOUT:
                return True
    return False


def _record_login_failure(ip: str) -> None:
    now = time.time()
    with _login_lock:
        failures = _LOGIN_FAILURES.get(ip, [])
        failures = [t for t in failures if now - t < _LOGIN_WINDOW]
        failures.append(now)
        _LOGIN_FAILURES[ip] = failures


def _account_fs_key(account_name: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", (account_name or "").lower()).strip("_")
    return key or "unknown_account"


def _account_upload_dir(account_name: str) -> Path:
    return UPLOADS_DIR / "accounts" / _account_fs_key(account_name)


def _account_file_path(account_name: str, *parts: str) -> Path:
    return _account_upload_dir(account_name).joinpath(*parts)


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


def _normalize_build_code(code: str | None) -> str | None:
    raw = re.sub(r"[^A-Za-z0-9]", "", code or "").upper()
    if len(raw) != _BUILD_CODE_LEN:
        return None
    return f"{raw[:4]}-{raw[4:]}"


def _generate_build_code() -> str:
    for _ in range(256):
        raw = "".join(secrets.choice(_BUILD_CODE_ALPHABET) for _ in range(_BUILD_CODE_LEN))
        code = f"{raw[:4]}-{raw[4:]}"
        if _db_resolve_build_export(code) is None:
            return code
    raise RuntimeError("failed to allocate build code")


def _session_share_code(session_id: str) -> str | None:
    account = _db_get_account_state_for_session(session_id)
    if account:
        code = _db_find_share_code_for_account(account.account_name)
        if code:
            return code
    for code, entry in _share_registry["codes"].items():
        if entry.get("session_id") == session_id:
            return code
    return None


def _resolve_shared_session_id(share_code: str | None) -> str | None:
    code = _normalize_share_code(share_code)
    if not code:
        return None
    entry = _share_registry["codes"].get(code)
    if isinstance(entry, dict):
        sid = _valid_session(entry.get("session_id"))
        if sid:
            return sid
    account_name = _db_resolve_account_for_share_code(code)
    if account_name:
        return _db_find_session_for_account(account_name)
    return None


def _session_is_shared(session_id: str) -> bool:
    return _session_share_code(session_id) is not None


def _share_url(code: str | None) -> str:
    code = _normalize_share_code(code)
    return f"/?share={code}" if code else ""




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


def _resolve_account_name(session_id: str | None, share_code: str | None = None) -> tuple[str | None, str | None]:
    sid, err = _resolve_session_context(session_id, share_code)
    if err:
        return None, err
    if not sid:
        return None, None
    state = _db_get_account_state_for_session(sid)
    if state:
        return state.account_name, None
    return None, None


def _workspace_info(session_id: str | None) -> dict:
    sid = _valid_session(session_id)
    if not sid:
        return {"primary_account": None, "shadow_account": None, "active_slot": "primary"}
    return _db_get_workspace_binding(sid)


def _select_upload_slot(session_id: str, account_name: str) -> tuple[str | None, str | None]:
    slot = _db_session_slot_for_account(session_id, account_name)
    if slot:
        return slot, None
    workspace = _db_get_workspace_binding(session_id)
    if not workspace["primary_account"]:
        return "primary", None
    if not workspace["shadow_account"]:
        return "shadow", None
    return None, f"Workspace already has primary {workspace['primary_account']} and shadow {workspace['shadow_account']}. Delete shadow or switch uploads."


def _active_account_label(workspace: dict) -> str:
    slot = workspace.get("active_slot") or "primary"
    if slot == "shadow":
        return workspace.get("shadow_account")
    return workspace.get("primary_account")


def _prune_share_registry_for_account(account_name: str) -> None:
    stale = [code for code, entry in _share_registry["codes"].items() if entry.get("account_name") == account_name]
    for code in stale:
        _share_registry["codes"].pop(code, None)
    if stale:
        _save_share_registry()


def _state_to_cache(state) -> dict:
    return {
        "data_bytes": state.data_bytes,
        "builds_bytes": state.builds_bytes,
        "achievements_bytes": state.achievements_bytes,
        "stickerbook_bytes": state.stickerbook_bytes,
        "mtime": state.data_mtime,
        "error": state.last_error,
        "meta": {
            "account": state.account_name,
            "server": state.server,
            "item_count": state.item_count or 0,
            "character_count": state.character_count or 0,
            "parse_ms": state.parse_ms or 0,
            "last_modified": state.source_last_update or 0,
        },
        "ww_builds_bytes": state.ww_builds_bytes,
        "ww_mtime": state.ww_mtime,
    }


def _find_build_for_char(cache: dict, character_id: str) -> dict | None:
    payload = cache.get("builds_bytes")
    if not payload:
        return None
    parsed = json.loads(payload)
    for build in parsed.get("builds", []):
        if str(build.get("char_id")) == str(character_id):
            return build
    return None


def _equipped_item_map_for_char(cache: dict, character_id: str) -> dict[int, dict]:
    """Return equipped slot -> item metadata from /api/data cache for one character."""
    payload = cache.get("data_bytes")
    if not payload:
        return {}
    try:
        parsed = json.loads(payload)
    except Exception:
        return {}
    slot_map: dict[int, dict] = {}
    for item in parsed.get("items", []):
        for loc in item.get("locations", []):
            if str(loc.get("location_key")) != str(character_id):
                continue
            if int(loc.get("bag_id", -1)) != 0:  # BAG_WORN / equipped only
                continue
            for slot_raw in (loc.get("bag_slots") or {}).keys():
                try:
                    slot = int(slot_raw)
                except Exception:
                    continue
                slot_map[slot] = item
    return slot_map


def _enrich_build_for_export(cache: dict, build: dict) -> dict:
    """Backfill export build gear metadata from equipped item cache."""
    if not isinstance(build, dict):
        return build
    gear = build.get("gear")
    char_id = build.get("char_id")
    if not isinstance(gear, list) or not char_id:
        return build
    equipped = _equipped_item_map_for_char(cache, str(char_id))
    if not equipped:
        return build

    enriched = dict(build)
    out_gear: list[dict] = []
    for g in gear:
        if not isinstance(g, dict):
            out_gear.append(g)
            continue
        slot = g.get("slot")
        src = equipped.get(int(slot)) if isinstance(slot, int) else None
        if not src:
            out_gear.append(g)
            continue
        merged = dict(g)
        merged["quality"] = src.get("quality", merged.get("quality"))
        merged["quality_name"] = src.get("quality_name", merged.get("quality_name"))
        merged["quality_color"] = src.get("quality_color", merged.get("quality_color"))
        merged["filter_type"] = src.get("filter_type", merged.get("filter_type"))
        merged["filter_type_name"] = src.get("filter_type_name", merged.get("filter_type_name"))
        merged["weapon_type"] = src.get("weapon_type", merged.get("weapon_type"))
        merged["armor_type"] = src.get("armor_type", merged.get("armor_type"))
        merged["level"] = src.get("level", merged.get("level"))
        if not merged.get("trait_name"):
            merged["trait_name"] = src.get("trait_name")
        if not merged.get("enchant_name"):
            merged["enchant_name"] = src.get("enchant_name", "")
        if not merged.get("set_name"):
            merged["set_name"] = src.get("set_name", "")
        if not merged.get("link_name"):
            merged["link_name"] = src.get("name", merged.get("link_name"))
        out_gear.append(merged)
    enriched["gear"] = out_gear
    return enriched


def _parse_export_payload(payload_json: str) -> tuple[dict | None, dict, dict]:
    """Backward-compatible export payload parser.

    Returns (build, ability_names, cp_names) where name maps may be empty.
    """
    try:
        parsed = json.loads(payload_json)
    except Exception:
        return None, {}, {}
    if isinstance(parsed, dict) and isinstance(parsed.get("build"), dict):
        return (
            parsed.get("build"),
            parsed.get("ability_names") or {},
            parsed.get("cp_names") or {},
        )
    if isinstance(parsed, dict):
        return parsed, {}, {}
    return None, {}, {}


def _character_ids_for_cache(cache: dict) -> set[str]:
    payload = cache.get("data_bytes")
    if not payload:
        return set()
    parsed = json.loads(payload)
    chars = parsed.get("characters", {})
    return {str(cid) for cid in chars.keys()}


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


def _empty_cache() -> dict:
    return {
        "data_bytes": None,
        "builds_bytes": None,
        "achievements_bytes": None,
        "stickerbook_bytes": None,
        "mtime": None,
        "error": None,
        "meta": None,
    }


def _empty_ww_cache() -> dict:
    return {
        "ww_builds_bytes": None,
        "mtime": None,
        "error": None,
    }


def _ttc_upload_dir() -> Path:
    return UPLOADS_DIR / "ttc"


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


def _ttc_lookup_table_path() -> Path:
    uploaded = _ttc_upload_dir() / "ItemLookUpTable_EN.lua"
    if uploaded.exists():
        return uploaded
    configured = _config.get("ttc_lookup_table_path") or ""
    if configured:
        p = Path(configured)
        if p.exists():
            return p
    addon = Path(_config.get("ttc_addon_path") or "")
    return addon / "ItemLookUpTable_EN.lua"


def _ttc_price_table_path() -> Path:
    region = "EU" if str(_config.get("server", "NA")).upper() == "EU" else "NA"
    other = "NA" if region == "EU" else "EU"
    upload_dir = _ttc_upload_dir()
    for candidate in (upload_dir / f"PriceTable{region}.lua", upload_dir / f"PriceTable{other}.lua"):
        if candidate.exists():
            return candidate
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


def _ttc_db_path() -> Path:
    return UPLOADS_DIR / "ttc.sqlite3"


def _ensure_ttc_db(cache: dict | None = None) -> tuple[Path, int | None, Path]:
    cache = cache or _ttc_tables
    lookup_path = _ttc_lookup_table_path()
    price_path = _ttc_price_table_path()
    if not lookup_path.exists():
        raise FileNotFoundError(
            f"TTC lookup table not found ({lookup_path}). "
            "Upload ItemLookUpTable_EN.lua via the admin upload, or set ttc_addon_path / ttc_lookup_table_path in config.json."
        )
    if not price_path.exists():
        raise FileNotFoundError(
            f"TTC price table not found ({price_path}). "
            "Upload a PriceTable{{NA|EU}}.lua via the admin upload, or set ttc_addon_path / ttc_price_table_path in config.json."
        )
    lookup_mtime = os.path.getmtime(lookup_path)
    price_mtime = os.path.getmtime(price_path)
    db_path = _ttc_db_path()

    if (
        cache.get("db_ready")
        and cache.get("db_path") == str(db_path)
        and db_path.exists()
        and cache["lookup_mtime"] == lookup_mtime
        and cache["price_mtime"] == price_mtime
        and cache["lookup_path"] == str(lookup_path)
        and cache["price_path"] == str(price_path)
    ):
        return db_path, cache.get("price_time"), price_path

    with _TTC_BUILD_LOCK:
        # Re-check inside the lock — another thread may have finished the build while we waited.
        if (
            cache.get("db_ready")
            and cache.get("db_path") == str(db_path)
            and db_path.exists()
            and cache["lookup_mtime"] == lookup_mtime
            and cache["price_mtime"] == price_mtime
            and cache["lookup_path"] == str(lookup_path)
            and cache["price_path"] == str(price_path)
        ):
            return db_path, cache.get("price_time"), price_path

        t0 = time.monotonic()
        lookup = _parse_lua_assignment(lookup_path, "self.ItemLookUpTable")
        price = _parse_lua_assignment(price_path, "self.PriceTable")
        tmp_path = db_path.with_suffix(".tmp")
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(tmp_path)
        try:
            conn.executescript("""
                PRAGMA journal_mode=OFF;
                PRAGMA synchronous=OFF;
                PRAGMA temp_store=MEMORY;
                DROP TABLE IF EXISTS lookup;
                DROP TABLE IF EXISTS prices;
                DROP TABLE IF EXISTS meta;
                CREATE TABLE lookup (
                    item_name TEXT PRIMARY KEY,
                    item_id INTEGER NOT NULL
                );
                CREATE TABLE prices (
                    item_id INTEGER PRIMARY KEY,
                    avg INTEGER,
                    min INTEGER,
                    max INTEGER,
                    entry_count INTEGER,
                    amount_count INTEGER,
                    suggested_price INTEGER,
                    sale_avg INTEGER,
                    sale_entry_count INTEGER,
                    sale_amount_count INTEGER,
                    variant_path TEXT
                );
                CREATE TABLE meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)

            lookup_rows = []
            for name, item_ids in lookup.items():
                if not isinstance(item_ids, dict):
                    continue
                item_id = _first_ttc_item_id(item_ids)
                if item_id is not None:
                    lookup_rows.append((name, item_id))
            conn.executemany("INSERT OR REPLACE INTO lookup(item_name, item_id) VALUES (?, ?)", lookup_rows)

            price_rows = []
            for item_id, item_node in (price.get("Data") or {}).items():
                found, trail = _first_ttc_price_dict(item_node)
                if found is None:
                    continue
                try:
                    int_item_id = int(item_id)
                except (TypeError, ValueError):
                    continue
                price_rows.append((
                    int_item_id,
                    found.get("Avg", found.get("A")),
                    found.get("Min", found.get("N")),
                    found.get("Max", found.get("X")),
                    found.get("EntryCount", found.get("EC")),
                    found.get("AmountCount", found.get("AC")),
                    found.get("SuggestedPrice", found.get("S")),
                    found.get("SaleAvg", found.get("SA")),
                    found.get("SaleEntryCount", found.get("SE")),
                    found.get("SaleAmountCount", found.get("SAC")),
                    json.dumps(trail, separators=(",", ":")),
                ))
            conn.executemany("""
                INSERT OR REPLACE INTO prices(
                    item_id, avg, min, max, entry_count, amount_count, suggested_price,
                    sale_avg, sale_entry_count, sale_amount_count, variant_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, price_rows)

            price_time = price.get("TimeStamp")
            conn.executemany(
                "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
                [
                    ("price_time", str(price_time or "")),
                    ("lookup_path", str(lookup_path)),
                    ("price_path", str(price_path)),
                ],
            )
            conn.commit()
        finally:
            conn.close()

        tmp_path.replace(db_path)
        cache.update({
            "lookup_mtime": lookup_mtime,
            "price_mtime": price_mtime,
            "lookup_path": str(lookup_path),
            "price_path": str(price_path),
            "db_path": str(db_path),
            "db_ready": True,
            "price_time": price.get("TimeStamp"),
            "error": None,
        })
        cache["price_cache"] = collections.OrderedDict()
        logger.info("TTC SQLite built from {} in {:.2f}s", price_path.name, time.monotonic() - t0)
    return db_path, cache.get("price_time"), price_path


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


def _fetch_ttc_price(name: str, session_id: str | None = None) -> dict:
    clean_name = re.sub(r"\s+", " ", name or "").strip()
    url = _ttc_search_url(clean_name)
    if not clean_name:
        return {"name": clean_name, "url": url, "error": "name is required"}

    cache_key = clean_name.lower()
    price_cache = _ttc_tables.setdefault("price_cache", {})
    cached = _lru_get(price_cache, cache_key)
    if cached is not None:
        return cached

    fetched_at = int(time.time())
    db_path, price_time, price_path = _ensure_ttc_db()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT item_id FROM lookup WHERE item_name = ?",
            (cache_key,),
        ).fetchone()
        if row is None:
            result = {
                "name": clean_name,
                "fetchedAt": fetched_at,
                "fetchedAtText": _fmt_ttc_time(fetched_at),
                "priceTableTime": price_time,
                "priceTableTimeText": _fmt_ttc_time(price_time),
                "source": f"TTC {'uploaded' if (_ttc_upload_dir() / 'ItemLookUpTable_EN.lua').exists() else 'local'} PriceTable",
                "attribution": "Data from Tamriel Trade Centre",
                "url": url,
                "error": "No TTC item match",
            }
            _lru_put(price_cache, cache_key, result, _TTC_PRICE_CACHE_MAX)
            return result

        item_id = row[0]
        price_row = conn.execute("""
            SELECT avg, min, max, entry_count, amount_count, suggested_price,
                   sale_avg, sale_entry_count, sale_amount_count, variant_path
            FROM prices WHERE item_id = ?
        """, (item_id,)).fetchone()

    if price_row is None:
        result = {
            "name": clean_name,
            "itemId": item_id,
            "fetchedAt": fetched_at,
            "fetchedAtText": _fmt_ttc_time(fetched_at),
            "priceTableTime": price_time,
            "priceTableTimeText": _fmt_ttc_time(price_time),
            "source": f"TTC {'uploaded' if (_ttc_upload_dir() / 'ItemLookUpTable_EN.lua').exists() else 'local'} PriceTable",
            "attribution": "Data from Tamriel Trade Centre",
            "url": url,
            "error": "No TTC price data",
        }
        _lru_put(price_cache, cache_key, result, _TTC_PRICE_CACHE_MAX)
        return result

    result = {
        "name": clean_name,
        "itemId": item_id,
        "avg": price_row[0],
        "min": price_row[1],
        "max": price_row[2],
        "entryCount": price_row[3],
        "amountCount": price_row[4],
        "suggestedPrice": price_row[5],
        "saleAvg": price_row[6],
        "saleEntryCount": price_row[7],
        "saleAmountCount": price_row[8],
        "variantPath": json.loads(price_row[9]) if price_row[9] else [],
        "priceTableTime": price_time,
        "priceTableTimeText": _fmt_ttc_time(price_time),
        "fetchedAt": fetched_at,
        "fetchedAtText": _fmt_ttc_time(fetched_at),
        "source": f"TTC {'uploaded' if (_ttc_upload_dir() / 'ItemLookUpTable_EN.lua').exists() else 'local'} {price_path.name}",
        "attribution": "Data from Tamriel Trade Centre",
        "url": url,
    }
    _lru_put(price_cache, cache_key, result, _TTC_PRICE_CACHE_MAX)
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


def _init_db_fernet() -> None:
    """Generate (or load) the master Fernet key used to encrypt per-session API keys.

    The key is stored as a base64 string under ``db_secret`` in config.json.
    If it is absent, a new key is generated and the config file is updated.
    """
    global _db_fernet
    from cryptography.fernet import Fernet  # type: ignore[import]
    if "db_secret" not in _config:
        _config["db_secret"] = Fernet.generate_key().decode()
        CONFIG_PATH.write_text(json.dumps(_config, indent=2))
        logger.info("Generated new db_secret and saved to {}", CONFIG_PATH)
    _db_fernet = Fernet(_config["db_secret"].encode())


def _encrypt_api_key(raw: str) -> bytes:
    if _db_fernet is None:
        raise RuntimeError("db_fernet not initialised")
    return _db_fernet.encrypt(raw.encode())


def _decrypt_api_key(blob: bytes) -> str | None:
    if _db_fernet is None:
        return None
    try:
        return _db_fernet.decrypt(blob).decode()
    except Exception:
        return None


def _reset_session_memory(sess: dict) -> None:
    sess["cache"] = _empty_cache()
    sess["ww_cache"] = _empty_ww_cache()


def _evict_idle_session_memory(force: bool = False) -> None:
    cutoff = time.time() - _SESSION_MEMORY_TTL
    loaded = [
        (sid, sess) for sid, sess in _sessions.items()
        if sess["cache"]["data_bytes"] is not None or sess["ww_cache"]["ww_builds_bytes"] is not None
    ]

    for sid, sess in loaded:
        if force or (sess["last_active"] < cutoff and not sess["sse_queues"]):
            _reset_session_memory(sess)

    loaded = [
        (sid, sess) for sid, sess in _sessions.items()
        if sess["cache"]["data_bytes"] is not None or sess["ww_cache"]["ww_builds_bytes"] is not None
    ]
    if len(loaded) <= _MAX_LOADED_SESSIONS:
        return

    loaded.sort(key=lambda item: item[1]["last_active"])
    for sid, sess in loaded[:-_MAX_LOADED_SESSIONS]:
        if sess["sse_queues"]:
            continue
        _reset_session_memory(sess)


def _parse_iasync_from_bytes(raw_bytes: bytes, cache: dict) -> None:
    """Parse iasync from raw Lua bytes, build all payloads upfront, discard source bytes."""
    with _IASYNC_PARSE_LOCK:
        try:
            t0 = time.monotonic()
            text = raw_bytes.decode("utf-8", errors="replace")

            # Core parse: inventory + builds
            raw_core = parse_iasync_core_text(text)
            data = process_iasync(raw_core, server=_config.get("server", "NA"))
            builds = process_iasync_builds(raw_core)
            del raw_core

            # Full parse: achievements + stickerbook
            raw_full = parse_lua_text_variable(text, "iasync_data")
            achievements = process_iasync_achievements(raw_full)
            stickerbook = process_iasync_stickerbook(raw_full)
            del raw_full, text

            gc.collect()
            elapsed = time.monotonic() - t0
            data["meta"]["parse_ms"] = int(elapsed * 1000)

            cache["data_bytes"]         = _json_bytes(data)
            cache["builds_bytes"]       = _json_bytes(builds)
            cache["achievements_bytes"] = _json_bytes(achievements)
            cache["stickerbook_bytes"]  = _json_bytes(stickerbook)
            cache["mtime"]              = time.time()
            cache["error"]              = None
            cache["meta"]               = data["meta"]
            logger.info("iasync: {} items, {} chars in {:.2f}s",
                        data["meta"]["item_count"], data["meta"]["character_count"], elapsed)
        except Exception as exc:
            cache["error"] = str(exc)
            logger.error("iasync parse error: {}", exc)


def _parse_ww_from_bytes(raw_bytes: bytes, cache: dict) -> None:
    """Parse WizardsWardrobe from raw Lua bytes, discard source bytes."""
    with _WW_PARSE_LOCK:
        try:
            text = raw_bytes.decode("utf-8", errors="replace")
            raw = parse_lua_text_variable(text, "WizardsWardrobeSV")
            builds = process_ww_builds(raw)
            del raw, text
            gc.collect()
            cache["ww_builds_bytes"] = _json_bytes(builds)
            cache["mtime"]           = time.time()
            cache["error"]           = None
            n = sum(len(v) for v in builds["builds"].values())
            logger.info("WW: {} builds", n)
        except Exception as exc:
            cache["error"] = str(exc)
            logger.error("WW parse error: {}", exc)






def _ensure_iasync_aux_bytes(cache: dict, which: str) -> None:
    if cache.get(which) is not None:
        return
    raise FileNotFoundError("No iasync source available — please re-upload your data")


def _recover_uploaded_iasync_cache(
    cache: dict,
    *,
    account_name: str | None,
    session_id: str | None,
    share_code: str | None,
    need_aux: str | None = None,
) -> tuple[bool, str | None]:
    if cache.get("data_bytes") is not None and (need_aux is None or cache.get(need_aux) is not None):
        return True, None
    if not account_name:
        msg = "missing resolved workspace/account"
        logger.warning("iasync recovery unavailable: {} (session={}, share={})", msg, session_id, share_code)
        return False, msg

    state = _db_get_account_state(account_name)
    if state is None:
        msg = f"missing account state for {account_name}"
        logger.warning("iasync recovery failed: {}", msg)
        return False, msg

    # Populate cache from DB state
    if cache.get("data_bytes") is None and state.data_bytes is not None:
        cache["data_bytes"] = state.data_bytes
    if cache.get("builds_bytes") is None and state.builds_bytes is not None:
        cache["builds_bytes"] = state.builds_bytes
    if cache.get("achievements_bytes") is None and state.achievements_bytes is not None:
        cache["achievements_bytes"] = state.achievements_bytes
    if cache.get("stickerbook_bytes") is None and state.stickerbook_bytes is not None:
        cache["stickerbook_bytes"] = state.stickerbook_bytes
    if cache.get("mtime") is None and state.data_mtime is not None:
        cache["mtime"] = state.data_mtime
    if cache.get("meta") is None:
        cache["meta"] = {
            "account": state.account_name,
            "server": state.server,
            "item_count": state.item_count or 0,
            "character_count": state.character_count or 0,
            "parse_ms": state.parse_ms or 0,
            "last_modified": state.source_last_update or 0,
        }

    if cache.get("data_bytes") is None:
        msg = f"no data available for {account_name} — please re-upload your files"
        logger.warning("iasync recovery failed: {}", msg)
        return False, msg

    if need_aux and cache.get(need_aux) is None:
        msg = f"no {need_aux} available for {account_name} — please re-upload your files"
        logger.warning("iasync recovery failed: {}", msg)
        cache["error"] = msg
        return False, msg

    return True, None


def _extract_ww_account_name_from_bytes(source_bytes: bytes) -> str | None:
    text = source_bytes.decode("utf-8", errors="replace")
    raw = parse_lua_text_variable(text, "WizardsWardrobeSV")
    default = raw.get("Default", {})
    for key in default:
        if isinstance(key, str) and key.startswith("@"):
            return key
    return None


def _persist_account_source(account_name: str, source_path: Path, relative_parts: tuple[str, ...]) -> str:
    dest = _account_file_path(account_name, *relative_parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, dest)
    return str(dest)


def _valid_session(session_id: str | None) -> str | None:
    """Return session_id if it looks like a UUID, else None."""
    if session_id and _SESSION_RE.match(session_id):
        return session_id
    return None



def _get_or_create_session(session_id: str) -> dict:
    if session_id not in _sessions:
        _sessions[session_id] = {
            "cache": _empty_cache(),
            "ww_cache": _empty_ww_cache(),
            "sse_queues": set(),
            "last_active": time.time(),
        }
        logger.info("Session created: {}", session_id[:8])
    sess = _sessions[session_id]
    sess["last_active"] = time.time()
    _db_touch_session(session_id)
    _evict_idle_session_memory()
    return sess


def _resolve_cache(session_id: str | None, share_code: str | None = None) -> dict:
    account_name, account_err = _resolve_account_name(session_id, share_code)
    if account_err:
        return {"data_bytes": None, "builds_bytes": None, "achievements_bytes": None,
                "stickerbook_bytes": None, "mtime": None, "error": account_err}
    if account_name:
        state = _db_get_account_state(account_name)
        if state and state.data_bytes is not None:
            return _state_to_cache(state)
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
    account_name, account_err = _resolve_account_name(session_id, share_code)
    if account_err:
        return {"ww_builds_bytes": None, "mtime": None, "error": account_err}
    if account_name:
        state = _db_get_account_state(account_name)
        if state and state.ww_builds_bytes is not None:
            return {"ww_builds_bytes": state.ww_builds_bytes, "mtime": state.ww_mtime, "error": state.last_error}
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
        _evict_idle_session_memory()
        cutoff = time.time() - _SESSION_TTL
        expired = [sid for sid, s in list(_sessions.items()) if s["last_active"] < cutoff and not _session_is_shared(sid)]
        for sid in expired:
            _sessions.pop(sid, None)
            logger.info("Session expired + cleaned: {}", sid[:8])


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_logging()
    UPLOADS_DIR.mkdir(exist_ok=True)
    _load_config()
    _init_db_fernet()
    _db_init(_config["database_url"])
    _load_share_registry()
    _ability_icon_map.update(_build_ability_icon_map())
    logger.info("Ability icons: {} loaded", len(_ability_icon_map))
    asyncio.create_task(_session_cleanup())
    yield


app = FastAPI(title="ESO Armory", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


def _apply_security_headers(response) -> None:
    """Apply security headers to every response."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path.startswith(("/static", "/assets")):
        response = await call_next(request)
        _apply_security_headers(response)
        return response
    t0 = time.monotonic()
    response = await call_next(request)
    ms = int((time.monotonic() - t0) * 1000)
    _apply_security_headers(response)
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
    account_name, _ = _resolve_account_name(session, share)
    if cache["data_bytes"] is None:
        recovered, reason = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: _recover_uploaded_iasync_cache(
                cache,
                account_name=account_name,
                session_id=session,
                share_code=share,
                need_aux="achievements_bytes",
            ),
        )
        if not recovered:
            return JSONResponse(
                {"error": cache.get("error") or "No data loaded", "detail": reason},
                status_code=503,
            )
    if cache["achievements_bytes"] is None:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: _ensure_iasync_aux_bytes(cache, "achievements_bytes"))
            if account_name and cache["achievements_bytes"] is not None:
                _db_update_account_blobs(account_name, achievements_bytes=cache["achievements_bytes"])
        except Exception as exc:
            logger.exception("achievements payload generation failed for {}: {}", account_name or "<no-account>", exc)
            return JSONResponse({"error": str(exc)}, status_code=500)
    if cache["achievements_bytes"] is None:
        return JSONResponse(
            {"error": "Achievements payload unavailable", "detail": "aux payload was not generated"},
            status_code=503,
        )
    return Response(
        content=cache["achievements_bytes"],
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/stickerbook")
async def api_stickerbook(session: str | None = Query(None), share: str | None = Query(None)):
    cache = _resolve_cache(session, share)
    account_name, _ = _resolve_account_name(session, share)
    if cache["data_bytes"] is None:
        recovered, reason = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: _recover_uploaded_iasync_cache(
                cache,
                account_name=account_name,
                session_id=session,
                share_code=share,
                need_aux="stickerbook_bytes",
            ),
        )
        if not recovered:
            return JSONResponse(
                {"error": cache.get("error") or "No data loaded", "detail": reason},
                status_code=503,
            )
    if cache["stickerbook_bytes"] is None:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: _ensure_iasync_aux_bytes(cache, "stickerbook_bytes"))
            if account_name and cache["stickerbook_bytes"] is not None:
                _db_update_account_blobs(account_name, stickerbook_bytes=cache["stickerbook_bytes"])
        except Exception as exc:
            logger.exception("stickerbook payload generation failed for {}: {}", account_name or "<no-account>", exc)
            return JSONResponse({"error": str(exc)}, status_code=500)
    if cache["stickerbook_bytes"] is None:
        return JSONResponse(
            {"error": "Stickerbook payload unavailable", "detail": "aux payload was not generated"},
            status_code=503,
        )
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
    sid = _valid_session(session) if session else None
    has_server_key = bool(os.environ.get("ANTHROPIC_API_KEY") or _config.get("anthropic_api_key", ""))
    has_session_key = bool(_db_get_session_api_key(sid)) if sid else False
    account_name, _ = _resolve_account_name(sid, share)
    is_admin = _db_is_account_admin(account_name) if account_name else False
    if cache["data_bytes"] is None:
        return {"ok": False, "item_count": 0, "character_count": 0,
                "last_modified": None, "error": cache.get("error"),
                "has_server_api_key": has_server_key, "has_session_api_key": has_session_key,
                "is_admin": is_admin}
    meta = cache.get("meta") or {}
    return {
        "ok":                 True,
        "item_count":         meta["item_count"],
        "character_count":    meta["character_count"],
        "last_modified":      cache["mtime"],
        "error":              None,
        "has_server_api_key": has_server_key,
        "has_session_api_key": has_session_key,
        "is_admin":           is_admin,
    }


@app.get("/api/workspace")
async def api_workspace(session: str | None = Query(None), share: str | None = Query(None)):
    sid, err = _resolve_session_context(session, share)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    workspace = _workspace_info(sid)
    return JSONResponse({
        "primary": {"account": workspace["primary_account"]},
        "shadow": {"account": workspace["shadow_account"]},
        "activeSlot": workspace["active_slot"],
        "activeAccount": _active_account_label(workspace),
    })


@app.post("/api/workspace/slot")
async def api_workspace_slot(session: str | None = Query(None), slot: str | None = Query(None)):
    sid = _valid_session(session)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    if slot not in {"primary", "shadow"}:
        return JSONResponse({"error": "valid slot required"}, status_code=400)
    if not _db_set_active_slot(sid, slot):
        return JSONResponse({"error": f"{slot} slot is empty"}, status_code=400)
    workspace = _workspace_info(sid)
    return JSONResponse({
        "ok": True,
        "primary": {"account": workspace["primary_account"]},
        "shadow": {"account": workspace["shadow_account"]},
        "activeSlot": workspace["active_slot"],
        "activeAccount": _active_account_label(workspace),
    })


@app.delete("/api/workspace/shadow")
async def api_workspace_delete_shadow(session: str | None = Query(None)):
    sid = _valid_session(session)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    account_name, deleted = _db_delete_shadow_slot(sid)
    if not account_name:
        return JSONResponse({"error": "shadow slot is empty"}, status_code=400)
    if deleted:
        shutil.rmtree(_account_upload_dir(account_name), ignore_errors=True)
        _prune_share_registry_for_account(account_name)
    workspace = _workspace_info(sid)
    return JSONResponse({
        "ok": True,
        "deletedAccount": account_name,
        "deletedCanonical": deleted,
        "primary": {"account": workspace["primary_account"]},
        "shadow": {"account": workspace["shadow_account"]},
        "activeSlot": workspace["active_slot"],
        "activeAccount": _active_account_label(workspace),
    })


@app.post("/api/build_export")
async def api_build_export(
    session: str | None = Query(None),
    share: str | None = Query(None),
    character_id: str | None = Query(None),
):
    sid, err = _resolve_session_context(session, share)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    if not character_id:
        return JSONResponse({"error": "character_id is required"}, status_code=400)

    account_name, account_err = _resolve_account_name(sid, share)
    if account_err:
        return JSONResponse({"error": account_err}, status_code=400)
    if not account_name:
        return JSONResponse({"error": "upload armory data before exporting a build"}, status_code=400)

    cache = _resolve_cache(sid, share)
    build = _find_build_for_char(cache, character_id)
    if not build:
        return JSONResponse({"error": "character build not found"}, status_code=404)
    build = _enrich_build_for_export(cache, build)

    code = _generate_build_code()
    parsed_builds = json.loads(cache.get("builds_bytes") or "{}")
    ability_names = parsed_builds.get("abilityNames") or {}
    cp_names = parsed_builds.get("cpNames") or {}
    skill_ids: set[str] = set()
    for bar in ("primary", "backup"):
        for _, skill_id in (build.get("skills", {}).get(bar, {}) or {}).items():
            if skill_id:
                skill_ids.add(str(skill_id))
    cp_ids = {str(v) for _, v in (build.get("cp", {}) or {}).items() if v}
    payload = {
        "schema_version": 2,
        "build": build,
        "ability_names": {sid: ability_names.get(sid, "") for sid in skill_ids},
        "cp_names": {sid: cp_names.get(sid, "") for sid in cp_ids},
    }
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    code = _db_upsert_build_export_for_character(
        code=code,
        account_name=account_name,
        character_id=str(character_id),
        payload_json=payload_json,
    )

    return JSONResponse({
        "ok": True,
        "code": code,
        "character_id": str(character_id),
        "build": build,
    })


@app.get("/api/compare_builds")
async def api_compare_builds(session: str | None = Query(None), share: str | None = Query(None)):
    sid, err = _resolve_session_context(session, share)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    account_name, account_err = _resolve_account_name(sid, share)
    if account_err:
        return JSONResponse({"error": account_err}, status_code=400)
    if not account_name:
        return JSONResponse({"imported": {}}, status_code=200)

    imported = {}
    for row in _db_list_imported_builds(sid, account_name):
        payload, ability_names, cp_names = _parse_export_payload(row["payload_json"])
        if not payload:
            continue
        imported[str(row["character_id"])] = {
            "character_id": str(row["character_id"]),
            "build_name": row["build_name"],
            "source_code": row["source_code"],
            "exported_from_account": row["exported_from_account"],
            "exported_from_character_id": row["exported_from_character_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "build": payload,
            "ability_names": ability_names,
            "cp_names": cp_names,
        }
    return JSONResponse({"imported": imported})


@app.post("/api/compare_builds/import")
async def api_compare_builds_import(
    session: str | None = Query(None),
    share: str | None = Query(None),
    character_id: str | None = Query(None),
    code: str | None = Query(None),
):
    sid, err = _resolve_session_context(session, share)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    if not character_id:
        return JSONResponse({"error": "character_id is required"}, status_code=400)
    normalized_code = _normalize_build_code(code)
    if not normalized_code:
        return JSONResponse({"error": "valid build code required"}, status_code=400)

    account_name, account_err = _resolve_account_name(sid, share)
    if account_err:
        return JSONResponse({"error": account_err}, status_code=400)
    if not account_name:
        return JSONResponse({"error": "upload armory data before importing a compare build"}, status_code=400)

    cache = _resolve_cache(sid, share)
    valid_chars = _character_ids_for_cache(cache)
    if str(character_id) not in valid_chars:
        return JSONResponse({"error": "character_id is not in the active workspace"}, status_code=400)

    source = _db_resolve_build_export(normalized_code)
    if not source:
        return JSONResponse({"error": "build code not found"}, status_code=404)

    payload, _, _ = _parse_export_payload(source["payload_json"])
    if not payload:
        return JSONResponse({"error": "build code payload is invalid"}, status_code=500)

    _db_upsert_imported_build(
        workspace_session_id=sid,
        account_name=account_name,
        character_id=str(character_id),
        build_name=payload.get("char_name") or "Imported Build",
        source_code=normalized_code,
        exported_from_account=source.get("account_name"),
        exported_from_character_id=str(source.get("character_id") or ""),
        payload_json=source["payload_json"],
    )
    return JSONResponse({"ok": True, "character_id": str(character_id), "source_code": normalized_code})


@app.delete("/api/compare_builds")
async def api_compare_builds_delete(
    session: str | None = Query(None),
    share: str | None = Query(None),
    character_id: str | None = Query(None),
):
    sid, err = _resolve_session_context(session, share)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    if not character_id:
        return JSONResponse({"error": "character_id is required"}, status_code=400)
    account_name, account_err = _resolve_account_name(sid, share)
    if account_err:
        return JSONResponse({"error": account_err}, status_code=400)
    if not account_name:
        return JSONResponse({"error": "no active workspace account"}, status_code=400)
    deleted = _db_delete_imported_build(sid, account_name, str(character_id))
    if not deleted:
        return JSONResponse({"error": "no imported build for character"}, status_code=404)
    return JSONResponse({"ok": True, "character_id": str(character_id)})


_SUPERSTAR_SLOT_IDS = {
    "head": 0, "shoulders": 3, "chest": 2, "hands": 16, "waist": 6,
    "legs": 8, "feet": 9, "ring 1": 11, "ring 2": 12, "neck": 1,
    "main hand": 4, "off hand": 5, "main hand backup": 20,
    "off-hand backup": 21, "off hand backup": 21,
}



_SUPERSTAR_PROMPT = """
You are parsing a screenshot from the ESO SuperStar addon. Extract the build data as JSON.

Return ONLY a JSON object with this exact structure (no markdown, no explanation):
{
  "character": {
    "name": "<full display name e.g. Khajiit Templar>",
    "race": "<race>",
    "class": "<class>",
    "cp": <champion points as integer>
  },
  "mundus": "<stone name without 'Boon: ' prefix, e.g. The Thief>",
  "gear": [
    {
      "slot": "<slot label as shown, e.g. Head, Shoulders, Main Hand Backup>",
      "item_name": "<full item name e.g. Tide-Born Helmet>",
      "set_name": "<set name or null if no set>",
      "set_completion": "<e.g. 5/5 or null>",
      "trait": "<trait name e.g. Divines, or null>",
      "enchantment": "<enchantment name e.g. Maximum Stamina Enchantment, or null>"
    }
  ]
}

Rules:
- Include every gear slot shown, even if the item is N/A.
- For N/A slots set item_name to null and all other fields to null.
- trait is the word directly below the item name (e.g. Divines, Infused, Bloodthirsty).
- enchantment is the line below the trait (e.g. Maximum Stamina Enchantment).
- set_name is the base set name only (not the item type), e.g. "Tide-Born" not "Tide-Born Helmet".
- For mythic items with Set: 1/1, set set_completion to "1/1".
""".strip()


@app.post("/api/session/apikey")
async def api_save_session_apikey(
    api_key: str = Form(...),
    session: str | None = Query(None),
):
    """Encrypt and persist an Anthropic API key for this browser session."""
    sid = _valid_session(session)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    if not api_key.strip():
        return JSONResponse({"error": "api_key must not be empty"}, status_code=400)
    encrypted = _encrypt_api_key(api_key.strip())
    _db_save_session_api_key(sid, encrypted)
    return {"ok": True}


@app.delete("/api/session/apikey")
async def api_delete_session_apikey(session: str | None = Query(None)):
    """Remove the stored API key for this browser session."""
    sid = _valid_session(session)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    _db_delete_session_api_key(sid)
    return {"ok": True}


@app.post("/api/parse_superstar")
async def api_parse_superstar(
    image: UploadFile = File(...),
    session: str | None = Query(None),
    share: str | None = Query(None),
):
    """Accept a SuperStar screenshot and return extracted build JSON via Claude Vision."""
    api_key = ""
    sid = _valid_session(session) if session else None
    if sid:
        blob = _db_get_session_api_key(sid)
        if blob:
            api_key = _decrypt_api_key(blob) or ""
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY") or _config.get("anthropic_api_key", "")

    if not api_key:
        return JSONResponse({"error": "No Anthropic API key configured. Enter your key via the key icon."}, status_code=503)

    image_bytes = await image.read(_MAX_IMAGE_BYTES + 1)
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        return JSONResponse({"error": f"Image exceeds {_MAX_IMAGE_BYTES // (1024*1024)} MB limit"}, status_code=413)
    media_type = image.content_type or "image/png"
    if media_type not in ("image/png", "image/jpeg", "image/gif", "image/webp"):
        media_type = "image/png"

    image_b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        import anthropic as _anthropic
        client = _anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                    {"type": "text", "text": _SUPERSTAR_PROMPT},
                ],
            }],
        )
        raw = msg.content[0].text.strip()
        parsed = json.loads(raw)
    except Exception as exc:
        logger.error("SuperStar Claude parse error: {}", exc)
        return JSONResponse({"error": f"Parse failed: {exc}"}, status_code=500)

    # Annotate each gear slot with its numeric slot_id for frontend lookup
    for slot in parsed.get("gear", []):
        slot["slot_id"] = _SUPERSTAR_SLOT_IDS.get((slot.get("slot") or "").lower())

    return JSONResponse(parsed)


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
    s_cache    = sess["cache"]
    s_ww_cache = sess["ww_cache"]
    workspace = _workspace_info(sid)
    active_account = _active_account_label(workspace)

    loop = asyncio.get_event_loop()
    results = {}

    async def _read_upload_bytes(upload: UploadFile, max_bytes: int = _MAX_UPLOAD_BYTES) -> bytes:
        chunks = []
        total = 0
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"Upload exceeds {max_bytes // (1024*1024)} MB limit")
            chunks.append(chunk)
        return b"".join(chunks)

    async def _stream_to_path(upload: UploadFile, dest: Path, max_bytes: int = _MAX_UPLOAD_BYTES) -> int:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        total = 0
        with dest.open("wb") as fh:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    dest.unlink(missing_ok=True)
                    raise ValueError(f"Upload exceeds {max_bytes // (1024*1024)} MB limit")
                fh.write(chunk)
        return total

    if iasync and iasync.filename:
        try:
            raw_bytes = await _read_upload_bytes(iasync)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=413)
        size = len(raw_bytes)
        s_cache["mtime"] = None
        await loop.run_in_executor(None, lambda: _parse_iasync_from_bytes(raw_bytes, s_cache))
        del raw_bytes
        if s_cache["error"]:
            results["iasync"] = {"ok": False, "error": s_cache["error"]}
        else:
            meta = s_cache.get("meta") or {}
            account_name = meta.get("account") or active_account
            if account_name:
                slot, conflict = _select_upload_slot(sid, account_name)
                if not slot:
                    results["iasync"] = {"ok": False, "error": conflict, "conflict": True, "account_name": account_name}
                else:
                    _db_upsert_account_payload(AccountPayload(
                        account_name=account_name,
                        server=str(meta.get("server") or _config.get("server", "NA")),
                        data_bytes=s_cache["data_bytes"],
                        builds_bytes=s_cache["builds_bytes"],
                        achievements_bytes=s_cache["achievements_bytes"],
                        stickerbook_bytes=s_cache["stickerbook_bytes"],
                        data_mtime=s_cache["mtime"],
                        item_count=meta.get("item_count"),
                        character_count=meta.get("character_count"),
                        parse_ms=meta.get("parse_ms"),
                        source_last_update=meta.get("last_modified"),
                    ))
                    _db_bind_session(sid, account_name, slot, make_active=True)
                    workspace = _workspace_info(sid)
                    active_account = _active_account_label(workspace)
                    results["iasync"] = {
                        "ok": True,
                        "items": meta["item_count"],
                        "chars": meta["character_count"],
                        "account_name": account_name,
                        "slot_updated": slot,
                    }
                    for q in list(sess["sse_queues"]):
                        try:
                            q.put_nowait("reload")
                        except asyncio.QueueFull:
                            pass
            else:
                results["iasync"] = {"ok": False, "error": "account name missing from upload"}
        logger.info("Session {} uploaded iasync.lua ({} bytes)", sid[:8], size)

    if ww and ww.filename:
        try:
            raw_bytes = await _read_upload_bytes(ww)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=413)
        size = len(raw_bytes)
        s_ww_cache["mtime"] = None
        await loop.run_in_executor(None, lambda: _parse_ww_from_bytes(raw_bytes, s_ww_cache))
        account_name_for_ww = _extract_ww_account_name_from_bytes(raw_bytes) or active_account
        del raw_bytes
        if s_ww_cache["error"]:
            results["ww"] = {"ok": False, "error": s_ww_cache["error"]}
        else:
            account_name = account_name_for_ww
            if account_name:
                slot, conflict = _select_upload_slot(sid, account_name)
                if not slot:
                    results["ww"] = {"ok": False, "error": conflict, "conflict": True, "account_name": account_name}
                else:
                    _db_upsert_account_payload(AccountPayload(
                        account_name=account_name,
                        server=str(_config.get("server", "NA")),
                        ww_builds_bytes=s_ww_cache["ww_builds_bytes"],
                        ww_mtime=s_ww_cache["mtime"],
                    ))
                    _db_bind_session(sid, account_name, slot, make_active=True)
                    workspace = _workspace_info(sid)
                    active_account = _active_account_label(workspace)
                    builds = json.loads(s_ww_cache["ww_builds_bytes"])
                    n = sum(len(v) for v in builds["builds"].values())
                    results["ww"] = {"ok": True, "builds": n, "account_name": account_name, "slot_updated": slot}
            else:
                results["ww"] = {"ok": False, "error": "account name missing from upload"}
        logger.info("Session {} uploaded WizardsWardrobe.lua ({} bytes)", sid[:8], size)

    if ttc_lookup and ttc_lookup.filename:
        if not active_account or not _db_is_account_admin(active_account):
            results["ttc_lookup"] = {"ok": False, "error": "TTC upload requires admin account"}
        else:
            ttc_dir = _ttc_upload_dir()
            ttc_dir.mkdir(parents=True, exist_ok=True)
            dest = ttc_dir / "ItemLookUpTable_EN.lua"
            try:
                size = await _stream_to_path(ttc_lookup, dest)
            except ValueError as exc:
                results["ttc_lookup"] = {"ok": False, "error": str(exc)}
            else:
                _ttc_tables["db_ready"] = False
                _ttc_tables["price_cache"] = collections.OrderedDict()
                _ttc_tables["error"] = None
                results["ttc_lookup"] = {"ok": True}
                logger.info("Session {} uploaded TTC lookup ({} bytes)", sid[:8], size)

    if ttc_price and ttc_price.filename:
        if not active_account or not _db_is_account_admin(active_account):
            results["ttc_price"] = {"ok": False, "error": "TTC upload requires admin account"}
        else:
            ttc_dir = _ttc_upload_dir()
            ttc_dir.mkdir(parents=True, exist_ok=True)
            region = "EU" if str(_config.get("server", "NA")).upper() == "EU" else "NA"
            dest = ttc_dir / f"PriceTable{region}.lua"
            try:
                size = await _stream_to_path(ttc_price, dest)
            except ValueError as exc:
                results["ttc_price"] = {"ok": False, "error": str(exc)}
            else:
                _ttc_tables["db_ready"] = False
                _ttc_tables["price_time"] = None
                _ttc_tables["price_cache"] = collections.OrderedDict()
                _ttc_tables["error"] = None
                results["ttc_price"] = {"ok": True}
                logger.info("Session {} uploaded TTC price table ({} bytes)", sid[:8], size)

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
    account_name, _ = _resolve_account_name(sid, None)
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
    account_name, _ = _resolve_account_name(sid, None)
    if not account_name:
        return JSONResponse({"error": "upload armory data before sharing"}, status_code=400)
    code = _session_share_code(sid)
    if not code:
        code = _generate_share_code()
        _db_get_or_create_share_code(code, account_name)
        _share_registry["codes"][code] = {
            "session_id": sid,
            "account_name": account_name,
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


@app.get("/api/auth/status")
async def api_auth_status(session: str | None = Query(None), share: str | None = Query(None)):
    sid = _valid_session(session)
    account_name, _ = _resolve_account_name(sid, share)
    if not account_name:
        return JSONResponse({"has_password": False, "account_name": None})
    state = _db_get_account_state(account_name)
    has_password = bool(state and state.password_hash)
    return JSONResponse({"has_password": has_password, "account_name": account_name})


@app.post("/api/auth/set_password")
async def api_auth_set_password(request: Request, session: str | None = Query(None), share: str | None = Query(None)):
    sid = _valid_session(session)
    account_name, _ = _resolve_account_name(sid, share)
    if not account_name:
        return JSONResponse({"error": "no account bound to this session"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    password = body.get("password", "")
    if len(password) < 8:
        return JSONResponse({"error": "password must be at least 8 characters"}, status_code=400)
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    ok = _db_set_account_password(account_name, hashed)
    if not ok:
        return JSONResponse({"error": "account not found"}, status_code=404)
    return JSONResponse({"ok": True})


@app.post("/api/auth/login")
async def api_auth_login(request: Request, session: str | None = Query(None)):
    client_ip = request.client.host if request.client else "unknown"
    sid = _valid_session(session)
    if not sid:
        return JSONResponse({"error": "valid session required"}, status_code=400)
    if _check_login_rate_limit(client_ip):
        return JSONResponse({"error": "Too many failed attempts. Try again later."}, status_code=429)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    raw_name = str(body.get("account_name", "")).strip()
    password = body.get("password", "")
    if not raw_name or not password:
        return JSONResponse({"error": "account_name and password are required"}, status_code=400)
    account_name = raw_name if raw_name.startswith("@") else f"@{raw_name}"
    stored_hash = _db_get_account_password_hash(account_name)
    _INVALID = {"error": "Invalid account or password"}
    # Always run bcrypt to prevent account-existence timing oracle.
    # If no stored hash, compare against a dummy hash (always fails).
    _DUMMY_HASH = "$2b$12$GhvMmNVjRW29ulnudl.LbuAnUtN/LRfe1JsBm1Vf3nGJFRtcjpB9."
    check_hash = stored_hash if stored_hash is not None else _DUMMY_HASH
    loop = asyncio.get_event_loop()
    ok = await loop.run_in_executor(None, lambda: bcrypt.checkpw(password.encode(), check_hash.encode()))
    if stored_hash is None or not ok:
        _record_login_failure(client_ip)
        return JSONResponse(_INVALID, status_code=401)
    _db_bind_session(sid, account_name, "primary", make_active=True)
    return JSONResponse({"ok": True, "account_name": account_name})


@app.get("/api/set_bonus")
async def api_set_bonus(set_id: int, set_name: str):
    slug = _set_name_to_slug(set_name)
    cache_key = set_id if set_id else slug
    cached = _lru_get(_set_bonus_cache, cache_key)
    if cached is not None:
        return JSONResponse(cached)
    url = f"https://eso-sets.com/set/{slug}"
    try:
        loop = asyncio.get_event_loop()
        bonuses = await loop.run_in_executor(None, lambda: _fetch_set_bonuses(slug))
        result: dict = {"bonuses": bonuses, "url": url}
        logger.info("Set bonus: {} → {} bonuses", set_name, len(bonuses))
    except Exception as exc:
        result = {"bonuses": [], "url": url, "error": str(exc)}
        logger.warning("Set bonus fetch failed: {} — {}", set_name, exc)
    _lru_put(_set_bonus_cache, cache_key, result, _EXTERNAL_CACHE_MAX)
    return JSONResponse(result)


@app.get("/api/skill_info")
async def api_skill_info(name: str):
    slug = _set_name_to_slug(name)
    cached = _lru_get(_skill_info_cache, slug)
    if cached is not None:
        return JSONResponse(cached)
    url = f"https://eso-skillbook.com/skill/{slug}"
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: _fetch_skill_info(slug))
        result: dict = {**info, "url": url}
        logger.info("Skill info: {} → {}", name, list(info.keys()))
    except Exception as exc:
        result = {"url": url, "error": str(exc)}
        logger.warning("Skill info fetch failed: {} — {}", name, exc)
    _lru_put(_skill_info_cache, slug, result, _EXTERNAL_CACHE_MAX)
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
        if len(target) >= _MAX_SSE_PER_SESSION:
            return JSONResponse({"error": "Too many SSE connections for this session"}, status_code=429)
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
    _init_db_fernet()
    port = args.port or _config.get("port", 5000)
    logger.info("ESO Armory → http://localhost:{}", port)
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level="warning",
        reload=False,
    )
