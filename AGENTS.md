# ESO Armory - Agent Notes

## Project Overview
Local web app that reads ESO SavedVariables and presents inventory, equipment, and builds in a WoW-Armory-style browser. FastAPI backend, single-file Alpine.js + Tailwind CDN frontend (no build step). Designed for WSL2 on Windows where the ESO client runs natively.

## Stack
- **Backend**: Python / FastAPI + Uvicorn (`server.py`)
- **Frontend**: `static/index.html` - vendored Alpine.js 3.x from `static/vendor/alpine.min.js`, Tailwind CDN
- **Lua parser**: Custom recursive-descent in `lua_parser.py` (stdlib only, no lupa/lark)
- **Start**: `uv run server.py` → http://localhost:5000 (or `python server.py` if virtualenv active via `uv sync --active`)
- **Tests**: pytest unit/API, Playwright UI (Chromium + Firefox), mutmut mutation tests

## Approval Preference
Before making code or file changes, ask for explicit approval unless the user has already clearly requested implementation in the current turn. Read-only inspection and searches are fine without approval.

## Key Files
| File | Purpose |
|------|---------|
| `server.py` | FastAPI app, file watcher, caches, SSE push, ability icon map, set bonus + skill info scrapers |
| `lua_parser.py` | `parse_lua_variable(path, varname)` |
| `data_processor.py` | `process_iasync()`, `process_iasync_builds()`, `process_iasync_achievements()`, `process_iasync_stickerbook()`, `process_ww_builds()` |
| `item_link_decoder.py` | Decodes ESO `\|H1:item:...\|h` links → trait/style/enchant fields |
| `config.json` | TTC addon paths, port, server region (`NA`/`EU`), database URL |
| `static/index.html` | Full SPA (Characters, Inventory, Achievements, Collections tabs) |
| `tests/fixtures/` | Sanitized deterministic Lua/TTC fixtures; do not commit live user data |

## Testing Commands
```bash
make test-fast          # unit + API tests with coverage
make test               # alias for test-fast
make test-ui            # Playwright in Chromium + Firefox
make test-all           # fast tests + browser tests
make test-mutation-core # scoped mutmut run for parser/decoder/data processing
```
Use `make test-all` before release-style validation. Mutation tests are manually run (slow). The UI suite includes a first-load regression that fails if the browser renders raw Lua or Alpine source text instead of the setup UI.

## Data Sources
| File | Variable | Purpose |
|------|----------|---------|
| `iasync.lua` | `iasync_data` | Inventory, equipped gear, build bars, currency, ability/CP names |
| `WizardsWardrobe.lua` | `WizardsWardrobeSV` | Saved build setups (gear, skills, CP, food) |

Data reaches the server via browser upload or the folder watcher - the server does not poll SavedVariables from disk directly.

**ESO Lua version:** Lua 5.1 - no `goto`, no `::labels::`. Use nested `if` guards. CharIdToName keys are strings after Lua→Python parsing.

## iasync_data Structure
```
iasync_data
  .chars[charId]         -- keyed by tostring(GetCurrentCharacterId())
    .name, .gold/ap/tv/wv, .spaceUsed/.spaceMax
    .bags[bagId][slot]   -- item: link, name, qty, traitType/Name, enchantId/Name, setId/Name,
                         --   quality, filterType, weaponType (per-slot, may be stale), armorType
                         --   bagId: 0=Worn, 1=Backpack
    .build_bars.primary/backup[slot]  -- abilityId; slots 3-7=skills, 8=ultimate
    .build_attributes.health/magicka/stamina
    .build_mundus        -- list of stone names (stripped "Boon: " prefix)
    .build_cp.earned + .slots[1..12]  -- abilityId per HOTBAR_CATEGORY_CHAMPION slot
  .bank
    .gold/ap/tv/wv       -- only valid after bank is opened
    .bags[bagId][slot]   -- bagId: 2=Bank, 5=CraftBag, 6=ESO+ Bank
  .houses[houseKey].name + .chests[bagId].slots[slot] + .capacity/.chestNum/.lastUpdate
  .guildBanks[guildName].slots[slot]
  .abilityNames[abilityId]  -- GetAbilityName(); also keyed as $abilityNames - both are merged
  .cpNames[starId]           -- GetChampionSkillName()
  .stickerbook.sets[setId]  -- name, category, subcategory, numCollected, numTotal,
                             --   pieces[i].{collected, name}
  .lastUpdate
```

## WizardsWardrobe Data Structure
```
WizardsWardrobeSV["Default"]["@account"][charId]
  .$LastCharacterName
  .pages[zoneTag][pageNum] = {name}   -- index 0 is char→pageNum map (not a named page)
  .setups[zoneTag][pageNum][setupNum]
    .name     -- skip if "" or "empty" (case-insensitive)
    .gear[slotIndex]  -- integer keys only; skip "mythic" string key
      .id, .link      -- WW links lack |h[name]|h; fall back to itemIdMap[item_id].name
    .skills[bar][slot]  -- bar 0=primary, 1=backup; slots 3-7=abilities, 8=ultimate
    .cp[1..12]          -- champion star IDs (not point allocations)
    .food = {id, link}
```

## Equipment Slots
`0=Head, 1=Neck, 2=Chest, 3=Shoulders, 4=Main Hand, 5=Off Hand, 6=Waist, 8=Legs, 9=Feet, 10=Costume, 11=Ring 1, 12=Ring 2, 13=Poison, 14=Backup Poison, 16=Gloves, 20=Backup Main, 21=Backup Off`

## Bag IDs
`2=Bank, 5=CraftBag (virtual), 6=ESO Plus Bank, 7+=House containers (HOUSE_BAG_START)`

## API Endpoints
| Endpoint | Returns |
|----------|---------|
| `GET /api/data` | `{meta, characters, bank, house_chests, items}` |
| `GET /api/builds` | `{builds, abilityNames, cpNames}` |
| `GET /api/achievements` | `{totalPts, earnedPts, categories, account_items, items_by_char, chars, recent}` |
| `GET /api/stickerbook` | `{sets: [{setId, name, category, subcategory, numCollected, numTotal, complete, pieces}], lastUpdate}` |
| `GET /api/ww_builds` | `{builds: {charId: [build, ...]}}` |
| `GET /api/set_bonus?set_id=&set_name=` | Set bonuses from eso-sets.com (memory cached) |
| `GET /api/skill_info?name=` | Skill details from eso-skillbook.com (memory cached) |
| `GET /api/ttc_price?name=&session=&share=` | TTC price from uploaded or local price tables |
| `GET/POST /api/share?session=&share=` | Get/create pairing code for workspace sharing |
| `POST /api/share/join?session=&code=` | Bind browser to shared workspace via pairing code |
| `GET /api/workspace?session=&share=` | `{primary, shadow, activeSlot, activeAccount}` |
| `POST /api/workspace/slot?session=&slot=` | Switch active slot (`primary`/`shadow`) |
| `DELETE /api/workspace/shadow?session=` | Remove shadow slot |
| `POST /api/build_export?session=&share=&character_id=` | Export current build to short code (one row per account+character; re-export overwrites) |
| `GET /api/compare_builds?session=&share=` | Imported compare builds keyed by destination `character_id` |
| `POST /api/compare_builds/import?session=&share=&character_id=&code=` | Store imported compare build |
| `DELETE /api/compare_builds?session=&share=&character_id=` | Delete imported compare build |
| `GET /api/ability_icons` | `{normalizedName: "/assets/abilities/..."}` - static, built at startup |
| `GET /api/status?session=&share=` | `{ok, item_count, character_count, last_modified, error, is_admin}` |
| `POST /api/upload?session=&share=` | Multipart: `iasync`, `ww`, `ttc_lookup`, `ttc_price` files; iasync/WW parsed in memory → all payloads stored to SQLite by ESO accountName (no raw bytes retained); `ttc_lookup`/`ttc_price` admin-only → written to global `uploads/ttc/` |
| `POST /api/parse_superstar` | Multipart `image` upload → Claude Vision parses SuperStar addon screenshot → `{character, mundus, gear[{slot, slot_id, item_name, set_name, trait, enchantment}]}` - requires `ANTHROPIC_API_KEY` env var or `anthropic_api_key` in `config.json` |
| `GET /events?session=&share=` | SSE stream; sends `"reload"` on data change (iasync only - not WW) |

## Server Architecture

### Caches
```python
_cache           # global iasync: {data_bytes, builds_bytes, achievements_bytes, stickerbook_bytes, mtime, error}
_ww_cache        # global WW: {ww_builds_bytes, mtime, error}
_sessions        # per-browser UUID: {cache, ww_cache, sse_queues, last_active}
_ability_icon_map  # built at startup; scans assets/abilities/**/*.{png,webp}
_set_bonus_cache   # (set_id or name_slug) → {bonuses, url}; mythic set_id=0 so slug is key
_skill_info_cache  # slug → {details}
_ttc_tables        # global TTC state: {lookup_mtime, price_mtime, lookup_path, price_path, db_path, db_ready, price_time, price_cache, error}
_TTC_BUILD_LOCK    # threading.Lock - serialises SQLite build; double-checked inside lock to avoid race on first load
```

### DB-backed workspaces (`uploads/armory.db`)
- `account_states`: one row per ESO `accountName`; stores processed API payload blobs (data, builds, achievements, stickerbook); raw Lua is never persisted
- `workspace_sessions`: maps browser UUID → `primary_account_id`, `shadow_account_id`, `active_slot`
- `_resolve_cache(session_id, share)`: shared workspace → DB account state → global cache
- Share codes in `uploads/share_registry.json`; shared sessions skip the 2-hour idle cleanup
- All four iasync payloads are built upfront on upload; `_ensure_iasync_aux_bytes` raises 503 if any are missing (re-upload required)

### Primary/shadow slots
- Upload matching primary account → updates `primary`; different account → fills `shadow` (if empty)
- Third unmatched account when both slots occupied → conflict (no silent replace)
- Only `shadow` is deletable from UI

### TTC storage
- Uploaded TTC files go to `uploads/ttc/ItemLookUpTable_EN.lua` and `uploads/ttc/PriceTable{NA|EU}.lua` - one global copy, any admin upload upserts it
- Derived SQLite at `uploads/ttc.sqlite3`; rebuilt by `_ensure_ttc_db()` when raw file mtime is newer than last build
- Config-path TTC (`ttc_addon_path`, `ttc_lookup_table_path`) is a fallback when no uploaded file exists
- `_ttc_upload_dir()` returns `UPLOADS_DIR / "ttc"` dynamically (picks up monkeypatched `UPLOADS_DIR` in tests)
- TTC upload is admin-only (`is_admin` DB column); `@admin_account` auto-granted on first upload

### Admin accounts
```python
_ADMIN_ACCOUNTS = frozenset({"@admin_account", "@admin_account_2"})  # auto-granted is_admin on first upload
db.is_account_admin(account_name)  # check DB flag
```
- `/api/status` returns `is_admin` for the current session's account
- Frontend shows a gold "admin" badge in the header when `isAdmin` is true
- Admin-only: TTC file upload, TTC sync in folder watcher

### TTC Config (`config.json`)
```json
{ "ttc_addon_path": "...", "ttc_lookup_table_path": "...", "ttc_price_table_path": "" }
```
Leave `ttc_price_table_path` empty to auto-select NA/EU table. Uploaded files in `uploads/ttc/` take precedence over config paths. Restart required after config changes.

## Icon Normalization (Python + JS must match)
```python
# Python (server.py):
key = re.sub(r'[^a-z0-9]+', '_', icon.stem.lower()).strip('_')
# JS (index.html):
const key = name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')
```
Icons served from `assets/` via `app.mount("/assets", ...)`. UESP source: `images.uesp.net` - needs `curl -sL -A "Mozilla/5.0"`.

## Theme System
CSS custom properties (`--t-*`) on `:root`; `[data-theme="name"]` blocks override them. Pre-Alpine `<script>` sets `data-theme` from localStorage before Alpine boots (prevents FOUC). **Progress bars:** always `style="background:var(--t-progress);width:X%"` - never `bg-eso-gold` Tailwind class on a fill. **Adding a theme:** CSS var block + `themes` object entry with `label` + `bgR/cardR/borderR/goldR/textR/mutedR/hoverR` RGB triplets.

**Quality/resource colors are NOT themed** - hardcoded game data (fine `#2dc50e`, superior `#5199ff`, epic `#a02ee4`).

## Restarting the Server
```bash
fuser -k 5000/tcp 2>/dev/null; sleep 1 && uv run server.py &
# If virtualenv active via uv sync --active:
fuser -k 5000/tcp 2>/dev/null; sleep 1 && python server.py &
```
Use `fuser -k 5000/tcp` (not `pkill`) - targets the port directly, works reliably in WSL2.

## Git Workflow
The user handles all git actions themselves. For pre-commit checks:
1. Update `README.md` if anything user-facing changed
2. Update `CHANGELOG.md` with a summary
3. Bump version in `pyproject.toml`
4. Draft commit message and list files to stage
5. **Do not run any git commands**

PRs branch from `master` and target `master` on GitHub.

## Item Link Decoder (`item_link_decoder.py`)
`|H1:item:F0:F1:...:F20|h[name]|h` - key fields (0-indexed after `item:`):
`[0]`=item_id, `[3]`=enchant_id, `[6]`=trait_id, `[14]`=flags (bit8=stolen, bit11=transmuted), `[15]`=style_id, `[16]`=crafted, `[17]`=bound, `[19]`=sell_value

**20-field bug (deferred):** Some links have 20 fields; flags shift to `[13]`, `[16]` may be missing. Fix: check `len(raw)` and adjust offsets. Transmuted and reconstructed both set bit 11 - no bit-level distinction.

## Security Model

### Response headers
`_apply_security_headers()` in the middleware sets these on every response:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`

### Upload limits
```python
_MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB - iasync, WW, TTC
_MAX_IMAGE_BYTES  =  20 * 1024 * 1024  # 20 MB - SuperStar image
```
`_read_upload_bytes()` and `_stream_to_path()` raise `ValueError` on oversize; callers return HTTP 413.

### Login protection
- **Rate limiting**: `_check_login_rate_limit(ip)` / `_record_login_failure(ip)` - 5 failures in 60 s → 5-min lockout; HTTP 429
- **Timing oracle**: always runs `bcrypt.checkpw` (against a dummy hash when the account doesn't exist); bcrypt offloaded to thread executor to avoid blocking the event loop

### XSS - `x-html` with user data
Any function that uses `x-html` to render user-supplied text **must** call `escapeHtml(s)` before interpolating. Example: `abilitySlotHtml` / `abilitySlotHtmlCompare` escape ability names before placing them in `<span>` tags. Ability names come from uploaded Lua data and imported build payloads and are shared across users via share codes - escaping is required.

### SSE connection cap
Session-scoped SSE queue sets are capped at `_MAX_SSE_PER_SESSION = 10`; excess connections return HTTP 429.

### Encryption
Per-session Anthropic API keys are Fernet-encrypted in SQLite using a key stored under `db_secret` in `config.json`. `config.json` is gitignored and must not be exposed via the web server document root. HTTPS should be terminated by a reverse proxy (nginx/Caddy) - the app speaks plain HTTP.

## Known Quirks / Gotchas
- **`helpOpen` tooltip pattern**: upload modal help popovers are controlled by a single `helpOpen: ''` string (key of the open popover; `''` = none) and `toggleHelp(key)` method. Only one open at a time; escape and click-away close it. Separate from `#eso-tip` game-data tooltips.
- **`fetchData` 503 behavior**: HTTP 503 from `/api/data` means no data has been uploaded yet - treat it silently (`this.data = null`, do NOT set `this.error`). The function uses if/else with no early `return` or `throw` so `finally { loading = false }` always fires. Do not add early returns or rethrows inside the `try` block.
- **WW mythic key**: `gear` dict has `"mythic"` string key alongside integer slot keys - skip via `int(slot_raw)` in try/except.
- **Mythic `set_id=0`**: Use `set_id || _slugify(set_name)` as cache key everywhere (Python + JS). Server `_fetch_set_bonuses` breaks on second bonus line when `first_pieces==1` to avoid multi-set bleed.
- **`getBonusEntry(item)`**: Use this frontend helper (not `setBonusCache[item.set_id]`) to handle mythic `set_id=0`.
- **Bank currency**: `GetCurrencyAmount(..., CURRENCY_LOCATION_BANK)` returns `nil` outside bank context - guard with `or prevValue` in Lua.
- **`weaponType` stale**: recorded per-slot at scan time; discard when it claims "Staff" but item name disagrees, then fall back to name-based detection.
- **Shields**: `filter_type 2` (Armor) with `weaponType="Shield"` and `armorType=nil` - check `weapon_type === 'Shield'` before armor-weight lookup.
- **Mundus icon key**: Strip "The " prefix: `name.toLowerCase().replace(/^the\s+/, '')`.
- **`x-html` for icons**: Use `x-html` (not `x-text`) for location icons and skill chips to render `<img>` tags. **Any user-supplied text interpolated into `x-html` template literals must go through `escapeHtml(s)` first** - see Security Model section.
- **`GetEquipmentFilterTypeForItemSetCollectionSlot` is misnamed**: returns armor/weapon sub-type integers, not `ITEM_FILTER_TYPE_*`. Use piece names from `GetItemLinkName` instead.
- **Achievements mixed-persistence**: `achievItemsByCatSubcat()` must merge `account_items` with character-specific `items_by_char` and dedupe by achievement id.
