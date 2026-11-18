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
    .build_pools.health/magicka/stamina  -- max pools as on the character sheet (iasync >= 1.5.0)
    .build_mundus        -- list of stone names (stripped "Boon: " prefix)
    .build_cp.earned + .slots[1..12]  -- abilityId per HOTBAR_CATEGORY_CHAMPION slot
  .bank
    .gold/ap/tv/wv       -- only valid after bank is opened
    .bags[bagId][slot]   -- bagId: 2=Bank, 5=CraftBag, 6=ESO+ Bank
  .houses[houseKey].name + .chests[bagId].slots[slot] + .capacity/.chestNum/.lastUpdate
  .guildBanks[guildName].slots[slot]
  .abilityNames[abilityId]  -- legacy names; also keyed as $abilityNames - both are merged
  .chars[charId].abilityNames[abilityId]  -- retained names for equipped and saved Wizards Wardrobe skills
  .chars[charId].abilityIcons[abilityId]  -- GetAbilityIcon() texture path, iasync 1.15.0
  .cpNames[starId]           -- GetChampionSkillName()
  .stickerbook.sets[setId]  -- name, category, subcategory, numCollected, numTotal,
                             --   pieces[i].{filterType, collected, name, icon}
  .stickerbook.categoryIcons[name]  -- top-level category tree icon (iasync 1.6.0)
  .collectibles.categories[topIdx]  -- name, icon, specialization (0 Collectibles, 1 Stories, 2 Housing, 3 Outfit Styles,
                                       4 Tribute Patrons), numUnlocked, numTotal, hidesLocked, subcats[subIdx] (iasync 1.9.0)
  .collectibles.items[collectibleId] -- name, icon, unlocked, categoryType, cat, sub (0 = directly under the category)
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
| `GET /api/builds` | `{builds, abilityNames, abilityIcons, cpNames}` |
| `uiColors` | Present on `/api/data`, `/api/achievements` and `/api/stickerbook`: the client's interface colours from iasync 1.7.0 (`{textNormal, textSelected, …, xpStart, xpEnd}` as `rrggbb`, only well-formed values), used by the Classic UI |
| `GET /api/achievements` | `{totalPts, earnedPts, categories, account_items, items_by_char, chars, recent, uiColors}`; `categories[].icon` is the tree icon (iasync 1.6.0); `recent` is the 50 newest completions, one per achievement; items carry `rewards` (`[{type: title\|dye\|collectible\|item, name, id?, icon?}]`) and `lineBaseId`/`linePreviousId`/`lineNextId` (tiered lines) |
| Demo account | On startup `demo/demo.json.gz` (`{data, builds, achievements, stickerbook, ww}` payloads, `scripts/make_demo.py`) is stored as `@armory-demo` when its hash changed, bound to a session derived from `db_secret`, and given the share code `DEMA-RMRY`; `/api/status` reports `demo_code`. Uploads for `@armory-demo` are rejected |
| `GET /api/data` (iasync 1.11.0+) | Also `currencies: [{key, name, icon, account, bank}]`, `activities: {timed: [{id, name, icon, description, type, progress, max, endTime, currencyType, reward, claimed, claimable}], campaigns: [{…, completed, capstone, milestones, activities}], tome: {name, tier, progressToNext, endTime, premium, tiers: [{tier, total, free, premium}]}, resets}`, `antiquities: [{id, name, icon, quality, set, zone, repeatable, recovered, lore, loreTotal, lead, leadExpires}]`; characters add `level, cp, title, zone, ava_rank(_name), riding, guilds, currencies, research, motifs, recipes, scribing`. Builds add `mundusDescriptions` and `cpDescriptions` (iasync 1.12.0) |
| `GET /api/stickerbook` | `{sets: [{setId, name, category, subcategory, numCollected, numTotal, complete, pieces: [{filterType, filterName, collected, name, icon, quality}], reconCost, reconCurrency}], categoryIcons, lastUpdate, uiColors}`; `filterType` is `EQUIPMENT_FILTER_TYPE_*` (1 Light … 11 Bow); `icon`/`categoryIcons` need iasync 1.6.0; `quality`, `reconCost` (transmute cost) and `uiColors` need iasync 1.7.0. Also `collectibles: {categories: [{idx, name, icon, specialization, unlocked, total, hidesLocked, subcats: [{idx, name, icon, unlocked, total}]}], items: [{id, name, icon, unlocked, cat, sub}], patrons: [{id, name, icon, category, categoryOrder, categoryIcon, collectibleId, unlocked}], lastUpdate}` (iasync 1.9.0, patrons 1.10.0 and only those in the in-game tree; empty lists before). `/api/data`, `/api/builds`, `/api/achievements`, `/api/stickerbook` and `/api/ww_builds` are gzipped when the client accepts it and the body is over 1 KB |
| `GET /api/ww_builds` | `{builds: {charId: [build, ...]}}` |
| `GET /api/set_bonus?set_id=&set_name=` | Set bonuses from eso-sets.com (memory cached) |
| `GET /api/skill_info?name=` | Skill details from eso-skillbook.com (memory cached) |
| `GET /api/ability_names?ids=` | Names for up to 40 ability ids iasync could not resolve (e.g. skills only in Wizards Wardrobe setups), from UESP's mined skill data (memory cached) |
| `GET /esoicons/<name>.png` | Game icon from `/esoui/art/icons/` (e.g. achievement icons). Downloaded from esoicons.uesp.net on first request into `assets/esoicons/` (never committed), then served locally; names must match `[a-z0-9_]+`. Fetched through `uesp.py`: UESP, or WordPress.com's Photon proxy (`i0.wp.com`) for 10 minutes after UESP answers 403. If both fail, `307` to the UESP URL (`Cache-Control: no-store`). Missing manifest icons under `/assets/` are fetched and saved the same way |
| `GET /esoicons/<folder>/<name>.png` | Same, from `/esoui/art/<folder>/` for `treeicons`, `collections`, `achievements` (category tree icons) |
| `GET /api/ttc_price?name=&session=&share=` | TTC price from uploaded or local price tables |
| `POST /api/ttc_prices?session=&share=` | Body `{names: [...]}` (≤ 10,000) → `{prices: {lowercased name: avg}, priceTableTime}`; names without a price are left out. Without TTC tables: `{prices: {}, error}` |
| `GET/POST /api/share?session=&share=` | Get/create pairing code for workspace sharing |
| `POST /api/share/join?session=&code=` | Bind browser to shared workspace via pairing code |
| `GET /api/workspace?session=&share=` | `{primary, shadow, activeSlot, activeAccount}` |
| `POST /api/workspace/slot?session=&slot=` | Switch active slot (`primary`/`shadow`) |
| `DELETE /api/workspace/shadow?session=` | Remove shadow slot |
| `POST /api/build_export?session=&share=&character_id=` | Export current build to short code (one row per account+character; re-export overwrites) |
| `GET /api/compare_builds?session=&share=` | Imported compare builds keyed by destination `character_id` |
| `POST /api/compare_builds/import?session=&character_id=&code=` | Store imported compare build |
| `DELETE /api/compare_builds?session=&character_id=` | Delete imported compare build |
| `GET /api/ability_icons` | `{normalizedName: "/assets/abilities/..."}` - static, built at startup |
| `GET /api/status?session=&share=` | `{ok, item_count, character_count, last_modified, error, is_admin}` |
| `GET /api/auth/status?session=` | `{account_name, has_password}` for this browser's own active account (a share code is ignored) |
| `POST /api/auth/set_password?session=` | Body `{password, current_password}` (≥ 8 chars) → bcrypt hash on this browser's active account; `current_password` is required once one is set |
| `POST /api/auth/login?session=` | Body `{account_name, password}` → binds this browser to the account as primary; rate-limited per IP |
| `POST /api/auth/logout?session=` | Deletes this browser's `workspace_sessions` row and imported compare builds, and drops share-registry entries pointing at it. Account data stays |
| `POST /api/upload?session=` | Multipart: `iasync`, `ww`, `ttc_lookup`, `ttc_price` files; iasync/WW parsed in memory → all payloads stored to SQLite by ESO accountName (no raw bytes retained); `ttc_lookup`/`ttc_price` admin-only → written to global `uploads/ttc/` |
| `POST /api/parse_superstar` | Multipart `image` upload → OpenAI (Chat Completions, `gpt-4o` or `openai_model`, JSON mode) or Anthropic vision reads the SuperStar screenshot → `{character, mundus, gear[{slot, slot_id, item_name, set_name, trait, enchantment}]}`. Key: the session's (`POST /api/session/apikey` with `api_key` and `provider` `openai`/`anthropic`, stored Fernet-encrypted as `{provider, key}`; older plain keys are Anthropic), else `OPENAI_API_KEY`/`openai_api_key`, else `ANTHROPIC_API_KEY`/`anthropic_api_key`. `/api/status` adds `session_api_provider` |
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
_ability_name_cache  # ability id → name; successful lookups persist in uploads/ability_names/<id>.txt
_ttc_tables        # global TTC state: {lookup_mtime, price_mtime, lookup_path, price_path, db_path, db_ready, price_time, price_cache, error}
_TTC_BUILD_LOCK    # threading.Lock - serialises SQLite build; double-checked inside lock to avoid race on first load
```

Game images under `/assets/` and `/esoicons/` have `Cache-Control: public, max-age=31536000, immutable`. Files remain on the persistent assets mount across container restarts. Browsers may retain them for a year without revalidation, subject to eviction. Replace an image at a new URL when its content changes. Errors and upstream fallback redirects do not receive immutable caching.

Skill bars prefer the exported `abilityIcons` map keyed by ability ID, converting game texture paths through `gameIcon()` to locally cached `/esoicons/` URLs. Old uploads fall back to the name-based icon map. Build exports include their skills' icon paths in `build.abilityIcons`, which Compare preserves on import. Live reloads refresh build metadata along with inventory.

Successful UESP ability-name lookups are written atomically to `uploads/ability_names/<id>.txt` and read before contacting UESP. Empty results and failures are not persisted. The frontend permits unresolved names to retry on a later view.

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

### Share codes are read-only
A share code lets another browser read the sharer's workspace. Writes ignore `share` and act only on the caller's own session: upload (including admin TTC files), set_password, auth status and compare-build import/delete. `build_export` still accepts `share`; it only publishes a code for a build the viewer can already see.

### Login protection
- **Rate limiting**: `_check_login_rate_limit(ip)` / `_record_login_failure(ip)` - 5 failures in 60 s → 5-min lockout; HTTP 429
- **Timing oracle**: always runs `bcrypt.checkpw` (against a dummy hash when the account doesn't exist); bcrypt offloaded to thread executor to avoid blocking the event loop

### XSS - user-supplied text in the UI
Ability names, CP names and build payloads come from uploaded Lua files and share codes. The Svelte frontend renders them as text (escaped by default) and never uses `{@html}`; keep it that way. Links built from names (eso-sets, eso-skillbook, TTC) go through `slugify` / `encodeURIComponent`.

### SSE connection cap
Session-scoped SSE queue sets are capped at `_MAX_SSE_PER_SESSION = 10`; excess connections return HTTP 429.

### Encryption
Per-session Anthropic API keys are Fernet-encrypted in SQLite using a key stored under `db_secret` in `config.json`. `config.json` is gitignored and must not be exposed via the web server document root. HTTPS should be terminated by a reverse proxy (nginx/Caddy) - the app speaks plain HTTP.
