# Architecture

ESO Armory is a FastAPI server and a single-page frontend. Players upload the `SavedVariables` files written by the iasync and WizardsWardrobe addons; the server parses them once, stores the processed JSON per ESO account in SQLite, and serves it to the browser.

```text
ESO addons ─▶ SavedVariables/*.lua ─▶ browser upload or folder watcher
   ─▶ POST /api/upload ─▶ lua_parser ─▶ data_processor ─▶ SQLite (per account)
   ─▶ GET /api/* ─▶ Svelte app (frontend/ built into static/dist, served at /)
```

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
    .name, .race, .class, .alliance, .gold/ap/tv/wv, .spaceUsed/.spaceMax
    .gender              -- "female"/"male" (iasync >= 1.4.0; missing in older files)
    .bags[bagId][slot]   -- item: link, name, qty, traitType/Name, enchantId/Name, setId/Name,
                         --   quality, filterType, weaponType (per-slot, may be stale), armorType
                         --   bagId: 0=Worn, 1=Backpack
    .build_bars.primary/backup[slot]  -- abilityId; slots 3-7=skills, 8=ultimate
    .build_attributes.health/magicka/stamina
    .build_pools.health/magicka/stamina  -- max pools as on the character sheet (iasync >= 1.4.0)
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
| `GET /api/ability_names?ids=` | Names for up to 40 ability ids iasync could not resolve (e.g. skills only in Wizards Wardrobe setups), from UESP's mined skill data (memory cached) |
| `GET /esoicons/<name>.png` | Game icon from `/esoui/art/icons/` (e.g. achievement icons). Downloaded from esoicons.uesp.net on first request into `assets/esoicons/` (never committed), then served locally; names must match `[a-z0-9_]+` |
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
_ability_icon_map  # built at startup; scans assets/abilities/**/*.{png,webp}; empty until `make assets` runs
_set_bonus_cache   # (set_id or name_slug) → {bonuses, url}; mythic set_id=0 so slug is key
_skill_info_cache  # slug → {details}
_ability_name_cache  # ability id → name ('' when UESP has none); failed lookups are not cached
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
- Account already has a password and this session is not bound to it → rejected; the user must log in first (`_select_upload_slot`)
- Only `shadow` is deletable from UI

### TTC storage
- Uploaded TTC files go to `uploads/ttc/ItemLookUpTable_EN.lua` and `uploads/ttc/PriceTable{NA|EU}.lua` - one global copy, any admin upload upserts it
- Derived SQLite at `uploads/ttc.sqlite3`; rebuilt by `_ensure_ttc_db()` when raw file mtime is newer than last build
- Config-path TTC (`ttc_addon_path`, `ttc_lookup_table_path`) is a fallback when no uploaded file exists
- `_ttc_upload_dir()` returns `UPLOADS_DIR / "ttc"` dynamically (picks up monkeypatched `UPLOADS_DIR` in tests)
- TTC upload is admin-only (`_is_admin`)

### Admin accounts
- `_is_admin(account)`: the account is listed in `config.json` `admin_accounts` **and** has a password set
- The password requirement matters: account names come from uploaded files, so a name alone proves nothing
- `/api/status` returns `is_admin` for the current session's account
- Frontend shows a gold "admin" badge in the header when `isAdmin` is true
- Admin-only: TTC file upload, TTC sync in folder watcher

### TTC Config (`config.json`)
```json
{ "ttc_addon_path": "...", "ttc_lookup_table_path": "...", "ttc_price_table_path": "" }
```
Leave `ttc_price_table_path` empty to auto-select NA/EU table. Uploaded files in `uploads/ttc/` take precedence over config paths. Restart required after config changes.


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

### Account ownership
The ESO account name in an upload is not proof of ownership. An account with no password can be claimed by any upload that names it; once a password is set, only sessions that logged in (or were already bound) can upload to, read, or re-password it. Users should set a password after their first upload.

### Login protection
- **Rate limiting**: `_check_login_rate_limit(ip)` / `_record_login_failure(ip)` - 5 failures in 60 s → 5-min lockout; HTTP 429
- **Timing oracle**: always runs `bcrypt.checkpw` (against a dummy hash when the account doesn't exist); bcrypt offloaded to thread executor to avoid blocking the event loop

### XSS - user-supplied text in the UI
Ability names, CP names and build payloads come from uploaded Lua files and share codes. The Svelte frontend renders them as text (escaped by default) and never uses `{@html}`; keep it that way. Links built from names (eso-sets, eso-skillbook, TTC) go through `slugify` / `encodeURIComponent`.

### SSE connection cap
Session-scoped SSE queue sets are capped at `_MAX_SSE_PER_SESSION = 10`; excess connections return HTTP 429.

### Encryption
Per-session Anthropic API keys are Fernet-encrypted in SQLite using a key stored under `db_secret` in `config.json`. `config.json` is gitignored and must not be exposed via the web server document root. HTTPS should be terminated by a reverse proxy (nginx/Caddy) - the app speaks plain HTTP.
