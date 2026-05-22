# ESO Armory — Agent Notes

## Project Overview
Local web app that reads ESO SavedVariables and presents inventory, equipment, and builds in a WoW-Armory-style browser. FastAPI backend, local Alpine.js + Tailwind CDN frontend (no build step). Designed for WSL2 on Windows where the ESO client runs natively.

## Stack
- **Backend**: Python / FastAPI + Uvicorn (`server.py`)
- **Frontend**: Single-file `static/index.html` — vendored Alpine.js 3.x from `static/vendor/alpine.min.js`, Tailwind CDN, no build step
- **Lua parser**: Custom recursive-descent in `lua_parser.py` (stdlib only, no lupa/lark)
- **Start**: `uv run server.py` → http://localhost:5000 (or `python server.py` if a virtualenv is active via `uv sync --active`)
- **Tests**: pytest unit/API tests, Playwright UI tests for Chromium and Firefox, mutmut mutation tests for backend confidence

## Approval Preference
Before making code or file changes, ask for explicit approval unless the user has already clearly requested implementation in the current turn. Read-only inspection, searches, and non-mutating checks are fine without approval.

## Key Files
| File | Purpose |
|------|---------|
| `server.py` | FastAPI app, file watcher, caches, SSE push, ability icon map, set bonus + skill info scrapers |
| `lua_parser.py` | Recursive-descent Lua parser: `parse_lua_variable(path, varname)` |
| `data_processor.py` | `process_iasync()`, `process_iasync_builds()`, `process_iasync_achievements()`, `process_iasync_stickerbook()`, `process_ww_builds()` |
| `item_link_decoder.py` | Decodes ESO `\|H1:item:...\|h` links → trait/style/enchant fields |
| `config.json` | Paths to Lua files, port, server region, poll interval |
| `iasync/iasync.lua` | ESO addon (symlinked to Windows AddOns folder) |
| `static/index.html` | Full SPA (Characters, Inventory, Achievements, Collections tabs) |
| `static/vendor/alpine.min.js` | Vendored Alpine.js runtime loaded by the app shell so CDN reachability does not block boot |
| `header.svg` | README/release header artwork; ANSI-style SVG matching sibling addon headers |
| `tests/fixtures/` | Sanitized deterministic Lua/TTC fixtures; do not commit live user data |
| `tests/ui/test_critical_flows.py` | Chromium/Firefox first-load, upload, share, and inventory browser flows |

## Testing Commands
```bash
make test-fast          # unit + API tests with coverage
make test               # alias for test-fast
make test-ui            # Playwright in Chromium + Firefox
make test-ui-chromium   # Playwright in Chromium only
make test-ui-firefox    # Playwright in Firefox only
make test-all           # fast tests + browser tests
make test-mutation-core # scoped mutmut run for parser/decoder/data processing
make test-mutation      # broader mutmut run
```

Use `make test-all` before release-style validation. Mutation tests are intentionally manual because they are much slower than the normal suite. The UI suite includes a first-load regression that fails if the browser renders HTML, Lua data, or inline Alpine source text instead of the setup UI.

## Data Sources
Two SavedVariables files are parsed:

| File | Variable | Purpose |
|------|----------|---------|
| `iasync.lua` | `iasync_data` | Inventory, equipped gear, build bars, currency, ability/CP names |
| `WizardsWardrobe.lua` | `WizardsWardrobeSV` | Saved build setups (gear, skills, CP, food) |

The server polls both files every `poll_interval_seconds` (default 5s). mtime is used to detect changes — inotify doesn't work on WSL2 `/mnt/c` paths.

## iasync Addon (`iasync/iasync.lua`)
Lives at `iasync/iasync.lua`, symlinked to `C:\Users\<you>\Documents\Elder Scrolls Online\live\AddOns\iasync\`.

**Triggers:**
- `EVENT_ADD_ON_LOADED` — initializes `iasync_data` structure
- `EVENT_PLAYER_ACTIVATED` (2s delay) — scans character bags + build bars + resolves names; (3s delay) scans house chests
- `EVENT_OPEN_BANK` — scans bank bags + craft bag + records bank currency
- `EVENT_OPEN_GUILD_BANK` — scans guild bank
- `EVENT_INVENTORY_SINGLE_SLOT_UPDATE` — real-time single-slot updates for all bag types

**Manual trigger:** `/script iasync_scan()` in-game chat.

**To flush to disk:** `/reloadui` — ESO writes SavedVariables on logout or reloadui. Server picks up within `poll_interval_seconds`.

**ESO Lua version:** Lua 5.1 — no `goto`, no `::labels::`. Use nested `if` guards.

### iasync_data Structure
```
iasync_data
  .chars[charId]              -- keyed by tostring(GetCurrentCharacterId())
    .name                     -- character display name
    .gold/ap/tv/wv            -- character currencies (CURRENCY_LOCATION_CHARACTER)
    .spaceUsed / spaceMax     -- backpack slots used / total
    .bags[bagId][slot]        -- item data per slot (bagId: 0=Worn, 1=Backpack)
      .link, .name, .qty
      .traitType, .traitName
      .enchantId, .enchantName
      .setId, .setName
      .quality, .filterType
      .weaponType              -- string (e.g. "Sword", "Restoration Staff") or nil; per-slot, may be stale
      .armorType               -- string ("Light", "Medium", "Heavy") or nil; nil for shields
    .build_bars
      .primary[slot]          -- abilityId; slots 3-7=skills, 8=ultimate
      .backup[slot]
    .build_attributes
      .health/magicka/stamina -- GetAttributeSpentPoints() values
    .build_mundus             -- list of stone names (stripped "Boon: " prefix)
    .build_cp
      .earned                 -- GetPlayerChampionPointsEarned()
      .slots[1..12]           -- abilityId per HOTBAR_CATEGORY_CHAMPION slot
  .bank
    .gold/ap/tv/wv            -- bank currencies (only valid after bank is opened)
    .bags[bagId][slot]        -- item data (bagId: 2=Bank, 5=CraftBag, 6=ESO+ Bank)
  .houses[houseKey]
    .name                     -- house display name
    .chests[bagId]
      .slots[slot]            -- item data
      .capacity, .chestNum, .lastUpdate
  .guildBanks[guildName]
    .slots[slot]              -- item data
  .abilityNames[abilityId]    -- resolved by GetAbilityName()
  .cpNames[starId]            -- resolved by GetChampionSkillName()
  .stickerbook
    .sets[setId]              -- keyed by ESO item set ID (integer)
      .name                   -- GetItemSetName(setId)
      .category               -- top-level category name (e.g. "Dungeons", "Cyrodiil")
      .subcategory            -- specific location (e.g. "Elden Hollow"); empty if same as category
      .numCollected           -- GetNumItemSetCollectionSlotsUnlocked(setId)
      .numTotal               -- GetNumItemSetCollectionPieces(setId)
      .pieces[i]
        .filterType           -- GetEquipmentFilterTypeForItemSetCollectionSlot(slot) — NOT ITEM_FILTER_TYPE; returns armor/weapon type values
        .collected            -- IsItemSetCollectionSlotUnlocked(setId, slot)
        .name                 -- GetItemLinkName(GetItemSetCollectionPieceItemLink(pieceId))
    .lastUpdate               -- GetTimeStamp() of last stickerbook scan
  .lastUpdate                 -- GetTimeStamp() of last full scan
```

## WizardsWardrobe Data Structure
```
WizardsWardrobeSV["Default"]["@account"][charId]
  .$LastCharacterName
  .pages[zoneTag][pageNum] = {name}        -- page metadata; index 0 = char→pageNum map
  .setups[zoneTag][pageNum][setupNum]
    .name                   -- build name; skip if "" or "empty" (case-insensitive)
    .gear[slotIndex]        -- integer keys only; skip non-integer keys (e.g. "mythic")
      .id, .link
    .skills[bar][slot]      -- bar 0=primary, 1=backup; slots 3-7=abilities, 8=ultimate
    .cp[1..12]              -- champion star IDs (not point allocations)
    .food = {id, link}
```
WW item links don't embed `|h[name]|h` so `link_name` is always empty — fall back to `itemIdMap[item_id].name` in the frontend.

## Equipment Slots
`0=Head, 1=Neck, 2=Chest, 3=Shoulders, 4=Main Hand, 5=Off Hand, 6=Waist, 8=Legs, 9=Feet, 10=Costume, 11=Ring 1, 12=Ring 2, 13=Poison, 14=Backup Poison, 16=Gloves, 20=Backup Main, 21=Backup Off`

## Bag IDs (Python constants in data_processor.py)
`2=Bank, 5=CraftBag (virtual), 6=ESO Plus Bank, 7+=House containers (HOUSE_BAG_START)`

## API Endpoints
| Endpoint | Returns |
|----------|---------|
| `GET /api/data` | `{meta, characters, bank, house_chests, items}` from iasync |
| `GET /api/builds` | `{builds, abilityNames, cpNames}` from iasync |
| `GET /api/achievements` | `{totalPts, earnedPts, categories, account_items, items_by_char, chars, recent}` from iasync |
| `GET /api/stickerbook` | `{sets: [{setId, name, category, subcategory, numCollected, numTotal, complete, pieces: [{filterType, filterName, collected, name}]}], lastUpdate}` |
| `GET /api/ww_builds` | `{builds: {charId: [build, ...]}}` from WizardsWardrobe |
| `GET /api/set_bonus?set_id=&set_name=` | Fetches set bonuses from eso-sets.com (cached in memory) |
| `GET /api/skill_info?name=` | Fetches skill details from eso-skillbook.com (cached in memory) |
| `GET /api/ttc_price?name=&session=&share=` | Looks up TTC price data for a stickerbook piece from uploaded session TTC tables or configured local Tamriel Trade Centre price tables |
| `GET /api/share?session=&share=` | Returns the current pairing code for a workspace if one exists |
| `POST /api/share?session=&share=` | Creates a pairing code for the resolved workspace if none exists yet |
| `POST /api/share/join?session=&code=` | Validates a pairing code and binds the browser to the shared workspace |
| `GET /api/workspace?session=&share=` | Returns `{primary, shadow, activeSlot, activeAccount}` for the current browser workspace |
| `POST /api/workspace/slot?session=&slot=` | Switches the active browser workspace slot between `primary` and `shadow` |
| `DELETE /api/workspace/shadow?session=` | Removes the browser session's shadow workspace; only deletes the canonical account row if it is no longer referenced elsewhere |
| `POST /api/build_export?session=&share=&character_id=` | Serializes the selected character's current build into a short export code (schema v2 payload: `build` + scoped `ability_names` + `cp_names`; server enriches gear metadata from equipped `/api/data` items before storing). Export persistence is one row per `account_name + character_id` and re-export overwrites that row/code |
| `GET /api/compare_builds?session=&share=` | Returns imported compare builds keyed by destination `character_id` for the active workspace/account |
| `POST /api/compare_builds/import?session=&share=&character_id=&code=` | Resolves a build export code and stores/replaces one imported compare build for that destination character |
| `DELETE /api/compare_builds?session=&share=&character_id=` | Deletes the imported compare build bound to that destination character |
| `GET /api/ability_icons` | `{normalizedName: "/assets/abilities/...png|.webp"}` — scanned at startup |
| `GET /api/status?session=&share=` | `{ok, item_count, character_count, last_modified, error}` |
| `POST /api/upload?session=&share=` | Accepts `iasync`, `ww`, `ttc_lookup`, and `ttc_price` multipart file fields; requires valid UUID session; writes to `uploads/<session_id>/`, parses, persists raw source + processed payloads into SQLite by ESO `accountName`, updates the session's `primary` or `shadow` slot, and returns upload status including `slot_updated` for armory files |
| `GET /events?session=&share=` | SSE stream; joins the shared workspace queue when `share` resolves, otherwise the browser's own session queue if it has data, else global queue; sends `"reload"` on data change |

### Static serving expectations
`GET /` and `HEAD /` must serve the app shell as `text/html; charset=utf-8` with `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`. Static/assets responses also set `nosniff`. Alpine is loaded from `/static/vendor/alpine.min.js`; if a hosted browser shows a white page with a failed `cdn.min.js` request, it is probably running an older cached `index.html`. If a hosted browser appears to dump `function armory()` or other source text, first verify response headers for `/` and `/static/index.html`, then check CDN/proxy cache behavior.

## Server Caches (server.py)
```python
_cache           = {data_bytes, builds_bytes, achievements_bytes, stickerbook_bytes, mtime, error}  # global iasync (local users)
_ww_cache        = {ww_builds_bytes, mtime, error}    # global WizardsWardrobe (local users)
_sessions: dict[str, dict]                             # per-browser-session state (keyed by UUID)
  # session = {cache, ww_cache, ttc_cache, upload_dir: Path, sse_queues: set, last_active: float}
  # upload_dir mirrors the ESO live folder layout: SavedVariables/ and AddOns/TamrielTradeCentre/
  # ttc_cache stores uploaded TTC lookup/price tables plus a per-name price cache
  # cache / ww_cache have same shape as global _cache / _ww_cache
_ability_icon_map: dict                                # built at startup, static
_set_bonus_cache: dict                                 # (set_id or name_slug) → {bonuses, url}; populated on demand; mythic items have set_id=0 so slug is used as key
_skill_info_cache: dict                                # slug → {details}; populated on demand
_ttc_tables      = {lookup, price, lookup_mtime, price_mtime, lookup_path, price_path, price_cache}  # local TTC Lua tables, lazy-loaded
_ttc_price_cache: dict                                 # normalized piece name → TTC price result/error
```
`_ability_icon_map` is built by `_build_ability_icon_map()` at startup — scans `assets/abilities/**/*.{png,webp}`, normalizes stems to keys.

### DB-backed uploaded workspaces
Uploaded/browser workspaces are now canonicalized into `uploads/armory.db`:
- `account_states` stores one canonical row per ESO `accountName`
- raw `iasync.lua` / `WizardsWardrobe.lua` contents are stored in `raw_iasync_lua` / `raw_ww_lua`
- processed API payload blobs (`data_bytes`, `builds_bytes`, `achievements_bytes`, `stickerbook_bytes`, `ww_builds_bytes`) are stored alongside source metadata
- `workspace_sessions` maps a browser UUID to `primary_account_id`, optional `shadow_account_id`, and `active_slot`

For uploaded workspaces, `/api/data`, `/api/builds`, `/api/achievements`, `/api/stickerbook`, and `/api/ww_builds` should resolve from the DB-backed account row. The copied account-scoped files under `uploads/accounts/<account>/...` are mirrors/metadata, not the primary read path.

### Session isolation
`_resolve_cache(session_id, share)` / `_resolve_ww_cache(session_id, share)` return the shared workspace cache when `share` resolves to a canonical session, otherwise the browser's own session cache if it has data, else the global cache. `_SESSION_RE` validates UUIDs before using them as filesystem paths (`uploads/<session_id>/`). Pairing codes live in `uploads/share_registry.json` and map short share codes back to the canonical session id. Shared sessions are treated as persistent workspaces and are skipped by the idle cleanup task; private sessions still expire after 2 hours. Parse functions refactored: `_parse_iasync_into(path, cache)` / `_parse_ww_into(path, cache)` take explicit targets; `_parse_iasync()` / `_parse_ww()` are thin wrappers for the global case.

### Primary/shadow workspace behavior
- A browser session now has one `primary` armory slot and one optional `shadow` slot.
- Uploading an armory file for the current primary account updates `primary`.
- Uploading a different ESO account fills `shadow` when empty instead of replacing `primary`.
- If both slots are already occupied and a third unmatched account is uploaded, the upload returns a conflict instead of silently replacing existing workspace state.
- The active slot is switchable from the header, and only the shadow slot is deletable from the UI.

### Workspace sharing
The header Share button is the entry point for cross-device reuse. `POST /api/share` creates a pairing code for the canonical session, `POST /api/share/join` validates and binds a browser to that code, and the client stores the code in `localStorage` as `eso-share-code`. All workspace-scoped fetches and SSE use `?share=` when present so the same uploaded data appears on another device without a re-upload. The share code is a convenience token, not strong authentication.

### Tamriel Trade Centre Price Lookup
Optional local TTC integration powers Collections piece-price tooltips. Config keys:
```json
{
  "ttc_addon_path": "path/to/AddOns/TamrielTradeCentre",
  "ttc_lookup_table_path": "path/to/AddOns/TamrielTradeCentre/ItemLookUpTable_EN.lua",
  "ttc_price_table_path": ""
}
```
Leave `ttc_price_table_path` empty to select `PriceTableNA.lua` or `PriceTableEU.lua` from `ttc_addon_path` using `server`.

Hosted users can also upload `ItemLookUpTable_EN.lua` and `PriceTableNA.lua` / `PriceTableEU.lua` manually through the upload modal; those files are stored in the session's live-folder mirror and take precedence for `/api/ttc_price`.

`/api/ttc_price?name=&session=` resolves a lowercased piece name through `ItemLookUpTable_EN.lua`, uses the first/default TTC item id, then returns the first available price row from the session-uploaded TTC tables when present, otherwise the configured local price table: `avg`, `min`, `max`, listing counts, suggested/sale values when present, `priceTableTimeText`, `fetchedAtText`, `source`, `attribution`, and the TTC search `url`. TTC website scraping is intentionally avoided because search pages are undocumented and CAPTCHA-prone. Restart the server after changing TTC config paths or adding the endpoint; a stale running process returns 404 for new routes.

If Collections piece tooltips render but price rows are missing, check `/api/ttc_price?name=<piece>&session=<id>` and `logs/armory.log`. A `404` means the running server has not been restarted with the route registered; frontend fetch handling should display the HTTP status instead of a blank price area.

## Assets System
All icons are served via `app.mount("/assets", StaticFiles(directory="assets"))`.

`header.svg` is a root-level project header image for README/release surfaces. Keep its 860×162 SVG format and terminal-style composition aligned with the sibling `Tools4Nerds` and `iasync` addon headers unless the user asks for a redesign.

### Icon normalization (both Python and JS must match)
```python
# Python (server.py _build_ability_icon_map):
key = re.sub(r'[^a-z0-9]+', '_', icon.stem.lower()).strip('_')

# JS (index.html abilityIcon()):
const key = name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')
```
"Lava Whip" → `lava_whip` → `/assets/abilities/class/dragonknight/ardent_flame/lava_whip.png`
"Chilling Throw" → `chilling_throw` → `/assets/abilities/scribing/chilling_throw.webp`

### Asset Directories
| Path | Contents | Size |
|------|----------|------|
| `assets/favicon.png` | Armory icon | 64×64 |
| `assets/currencies/` | `gold.png`, `ap.png`, `tv.png`, `wv.png` | 32×32 |
| `assets/constellations/` | 13 mundus stone icons (apprentice…warrior) | 64×64 |
| `assets/services/bank.png` | Bank icon | 64×64 |
| `assets/containers/` | `backpack.png`, `strongbox.png`, `small_chest.png` | 64×64 |
| `assets/interface/` | `health.png`, `magicka.png`, `stamina.png`, `system.png` | 64×64 |
| `assets/class/` | 7 class icons (arcanist, dragonknight, necromancer, nightblade, sorcerer, templar, warden) | 64×64 |
| `assets/alliance/` | `aldmeri.png`, `daggerfall.png`, `ebonheart.png` | 250×250 |
| `assets/races/` | 10 race icons (altmer, argonian, bosmer, breton, dunmer, imperial, khajiit, nord, orc, redguard) | 64×64 |
| `assets/abilities/class/dragonknight/{ardent_flame,draconic_power,earthen_heart}/` | ~76 DK ability icons | 64×64 |
| `assets/abilities/weapons/{bow,destruction_staff,dual_wield,one_hand_and_shield,restoration_staff,two_handed}/` | ~197 weapon ability icons | 64×64 |
| `assets/abilities/alliance_war/{assault,support}/` | ~40 alliance war icons | 64×64 |
| `assets/abilities/scribing/` | Scribing ability icons, including Chilling Throw and Shocking Contingency | png/webp |
| `assets/gear/weapon/` | 10 Breton-style weapon icons (dagger, 1h/2h sword/axe/hammer, bow, shield, staff) | webp |
| `assets/gear/armor/{heavy,medium,light}/` | 7 slot icons per weight class (head, shoulders, hands, chest/shirt, waist, legs, feet) | webp |
| `assets/gear/jewelry/` | neck and ring icons | webp |

All icons sourced from UESP MediaWiki (`images.uesp.net`). Browser User-Agent required for image downloads: `curl -sL -A "Mozilla/5.0" <url>`.

UESP API for URL resolution: `https://en.uesp.net/w/api.php?action=query&prop=imageinfo&iiprop=url&format=json&titles=File:X|File:Y`

## UI Structure (`static/index.html`)
Single Alpine.js component (`armory()`). Tabs: Characters, Inventory, Achievements, Collections.

### App State
```javascript
data         // /api/data response
builds       // /api/builds response  (abilityNames, cpNames, per-char build bars)
wwBuilds     // /api/ww_builds response
abilityIcons // /api/ability_icons response
achievData   // /api/achievements response, including account_items + per-character items_by_char
sbData       // /api/stickerbook response
sbCat        // selected top-level category string; null = summary view
sbSearch     // search string; when non-empty overrides sbCat view with global results
charMaps     // {charId: {slot: gearItem}} — equipped gear per char, built from data.items
itemIdMap    // {itemId: item} — for WW gear name lookups (WW links lack embedded names)
selectedChar // currently expanded character object
tab          // 'characters' | 'inventory' | 'achievements' | 'stickerbook'
serverWaking // bool — true while init() is polling /api/status waiting for server to come up (503 cold-start)
theme        // 'gold' | 'light' | 'dark' | 'synthwave' | 'outrun' — persisted to localStorage under 'eso-theme'
themes       // {gold|light|dark|synthwave|outrun: {label, bgR, cardR, borderR, goldR, textR, mutedR, hoverR}}
             //   *R fields are RGB triplets ('r,g,b') for rgba() math in Tailwind overrides
// Session
_sessionId       // UUID string from localStorage('eso-session-id'); generated via crypto.randomUUID() on first load
                 // appended as ?session= to: /api/data, /api/builds, /api/ww_builds, /api/achievements,
                 // /api/stickerbook, /api/upload, /api/status, /events
                 // NOT sent to: /api/ability_icons, /api/set_bonus, /api/skill_info, /api/ttc_price (global caches)
workspace        // {primary:{account}, shadow:{account}, activeSlot, activeAccount}; sourced from /api/workspace
// Upload / folder watcher
uploading, uploadOpen, uploadStatus, uploadIasyncName, uploadWWName
dirHandle        // FileSystemDirectoryHandle | null — active folder watcher handle
watchInterval    // setInterval ID | null
iasyncLastMod    // last seen lastModified for iasync.lua (0 = never checked)
wwLastMod        // last seen lastModified for WizardsWardrobe.lua
refreshing       // bool — true while manualRefresh() is in flight
lastKnownMtime   // float parsed from ETag header of last /api/data response
hasDirectoryPicker // bool — true if window.showDirectoryPicker is available (Chrome/Edge)
// Character detail inventory panel
charInvSearch, charInvQuality, charInvTypes, charInvLocTypes, charInvTraits
charInvTransmuted, charInvCrafted, charInvGroupBySet
detailPanelHeight // measured current-build panel height for wide-screen panel matching
compareMode, compareImportCode, compareBusy, compareStatus
importedCompareBuilds // map keyed by destination character_id from /api/compare_builds
importedAbilityNames  // map keyed by destination character_id from /api/compare_builds ability_names
importedCpNames       // map keyed by destination character_id from /api/compare_builds cp_names
exportedBuildCodes    // last export code per character in the active browser session
```

### Key JS Methods
```javascript
charBuilds(charId)           // → build[] from builds.builds (iasync live gear/skills)
charWWBuilds(charId)         // → build[] from wwBuilds.builds (WW saved setups)
abilityName(id)              // → string from builds.abilityNames[id]
abilityIcon(id)              // → URL string or null (normalizes name, looks up abilityIcons)
abilitySlotHtml(id, isUlt)  // → <img> or <span> HTML for skill chips
mundusIcon(name)             // → /assets/constellations/<key>.png
wwGearName(g)                // → name from itemIdMap or link_name
wwGearColor(g)               // → quality_color hex from itemIdMap
buildHasSkills(build)        // → bool
buildHasCP(build)            // → bool
locationSections             // computed getter — groups items by location with icons
// Collections tab
sbCategories()               // → sorted top-level category name[]
sbCategorySummary()          // → [{name, collected, total}] for summary grid
sbCatPct(catName)            // → 0-100 integer percent for left-nav progress bar
sbSetsInCat(catName)         // → filtered set[] for category view (respects sbSearch)
sbSearchResults()            // → set[] matching sbSearch across all categories
sbSubcategories(catName)     // → sorted subcategory name[] within a top-level category
sbSetsInSubcat(catName, sub) // → set[] for a specific subcategory
setEsoSetsUrl(setName)       // → https://eso-sets.com/set/<slug>
ttcUrl(pieceName)            // → TTC search URL (us/eu from data.meta.server)
fetchTtcPrice(name)          // → caches /api/ttc_price response by normalized name
tipShowSbSet(s, evt)         // shows set tooltip with bonuses from eso-sets.com
tipShowSbPiece(name, evt)    // shows TTC piece-price tooltip; displays HTTP/error status on failure
// Upload / folder watcher
uploadFiles()                // reads $refs.iasyncInput / $refs.wwInput, POSTs to /api/upload, refreshes data
fetchWorkspace()             // refreshes primary/shadow slot metadata from /api/workspace
switchWorkspaceSlot(slot)    // POST /api/workspace/slot, reloads all workspace-scoped data
switchWorkspaceSlotAndHome(slot) // returns to Characters home view, clears drilldown/compare state, then switches slot
deleteShadowWorkspace()      // DELETE /api/workspace/shadow, reloads all workspace-scoped data
openFolderPicker()           // showDirectoryPicker() → persists handle to IDB, checkDirForChanges(true), startDirWatch()
restoreDirHandle()           // on init: loads handle from IDB, queryPermission check (no gesture needed), resumes watch
startDirWatch()              // setInterval(5s) calling checkDirForChanges(false); toasts on change
stopDirWatch()               // clearInterval
clearDirHandle()             // stopDirWatch + null + _idbDel('dirHandle')
checkDirForChanges(force)    // reads iasync.lua + WW.lua via FSAPI, skips if lastModified unchanged (unless force),
                             //   uploads changed files, updates iasyncLastMod/wwLastMod; deduped by _uploadInProgress
manualRefresh()              // with dirHandle: checkDirForChanges(false) + toast; without: /api/status mtime compare
_idbOp/Get/Set/Del           // thin IndexedDB wrappers (DB: 'eso-armory', store: 'kv')
// Theme
setTheme(name)               // sets data-theme on <html>, persists to localStorage, calls _applyThemeTailwind
_applyThemeTailwind(name)    // injects <style id="theme-tw"> with !important overrides for all eso-* Tailwind classes
                             //   uses themes[name].*R RGB triplets for rgba() math; no-op (clears tag) for 'gold'
// Build compare
fetchCompareBuilds()         // GET /api/compare_builds
exportCurrentBuild(charId)   // POST /api/build_export, copies code to clipboard when allowed
                             // export storage is single-code-per-account+character; repeated exports overwrite
openCompare(charId)          // opens compare mode for selected character
returnToCharacterDrilldown() // exits compare mode and returns to normal drilldown layout
importCompareBuild(charId)   // POST /api/compare_builds/import with build code
deleteCompareBuild(charId)   // DELETE /api/compare_builds
compareImportedBuild(charId) // returns imported compare record for destination character
compareMissingItems          // computed strict-match missing list; crafted or Dungeon/Trial/Arena sourced rows skip TTC price lookup
compareMissingTotal          // computed total of TTC-priced purchasable rows only
```

### Theme System
All UI chrome colors are CSS custom properties (`--t-*`) on `:root` (Gold palette defaults); per-theme blocks in `[data-theme="name"]` override them. A small pre-Alpine inline `<script>` reads `localStorage` and sets `data-theme` before Alpine boots (prevents FOUC). At runtime `setTheme()` also injects `<style id="theme-tw">` with `!important` overrides for all Tailwind CDN `eso-*` classes. Key `eso-theme` in localStorage; legacy value `'eso'` is migrated to `'gold'` automatically.

**Current themes (in dropdown order):** `gold` (warm amber, default), `light` (parchment/cream, dark amber accent), `dark` (GitHub-dark navy, blue accent), `synthwave` (deep purple, violet + cyan), `outrun` (deep navy, hot pink + cyan)

**Color vars:** `--t-bg`, `--t-card`, `--t-border`, `--t-border-subtle` (30% α), `--t-border-line` (70% α), `--t-border-ghost` (90% α), `--t-gold`, `--t-gold-dark`, `--t-gold-dim` (33% α), `--t-gold-faint` (50% α), `--t-text`, `--t-muted`, `--t-muted-dim`, `--t-hover`, `--t-header-bg`, `--t-tip-bg` (gradient), `--t-tip-border`, `--t-tip-inset`, `--t-achiev-bg`, `--t-progress`

**Game data colors (NOT themed):** Quality colors (fine `#2dc50e`, superior `#5199ff`, epic `#a02ee4`, etc.), magicka/stamina/health resource colors — these come from game data and stay hardcoded.

**Progress bar rule:** All progress bars across every tab use `style="background:var(--t-progress);width:X%"` inline (never `bg-eso-gold` Tailwind on a progress fill). Complete vs incomplete state is expressed via `opacity:1` vs `opacity:0.5` on the fill element.

**Adding a new theme:** (1) Add `[data-theme="name"]` CSS var block in `<style>`; (2) Add entry to `themes` object in `armory()` with `label` + all `*R` RGB triplet fields (`bgR`, `cardR`, `borderR`, `goldR`, `textR`, `mutedR`, `hoverR`).

### CSS Classes
```css
.cur-icon   { width:16px; height:16px; display:inline; vertical-align:middle; }
.skill-icon { width:24px; height:24px; display:inline-block; vertical-align:middle; }
```

### Skill Chip Rendering
All three skill chip locations use `x-html="abilitySlotHtml(id, slot===8)"` (not `x-text`).
`abilitySlotHtml` returns an `<img class="skill-icon">` when an icon is found, else a `<span>`.

## Platform Detection (server.py)
```python
if sys.platform == "win32":
    return str(Path.home() / "Documents" / eso_rel)
if "microsoft" in platform.uname().release.lower():  # WSL2
    # Scan /mnt/c/Users/<user>/Documents/...
    skip = {"Public", "Default", "Default User", "All Users"}
    for u in sorted(Path("/mnt/c/Users").iterdir()):
        if u.is_dir() and u.name not in skip: ...
```

## Restarting the Server
```bash
fuser -k 5000/tcp 2>/dev/null; sleep 1 && uv run server.py &
```
If an existing virtualenv is active (i.e. `uv sync --active` was used), run directly instead:
```bash
fuser -k 5000/tcp 2>/dev/null; sleep 1 && python server.py &
```
Use `fuser -k 5000/tcp` (not `pkill`) — it targets the port directly and works reliably in WSL2.

## Git Workflow
The user handles all git actions (staging, committing, pushing) themselves. When asked to do pre-commit checks or a pre-commit workflow:
1. Update `README.md` if anything user-facing has changed
2. Update `CHANGELOG.md` with a summary of changes
3. Bump the version in `pyproject.toml`
4. Draft a commit message and list the files to stage
5. **Do not run any git commands** (`git add`, `git commit`, `git push`, etc.)

## Inventory Filter Architecture (`static/index.html`)

### Filter State Variables
```javascript
search: '',
filterQuality: '',          // single string (quality pill — mutually exclusive)
filterTypes: [],            // multiselect: '1'=Weapons, '2'=Armor, '6'=Jewelry, etc.
filterLocTypes: [],         // multiselect: 'equipped', 'backpack', 'bank', 'craft_bag', 'house', 'guild_bank'
filterChars: [],            // multiselect: charId strings
filterTraits: [],           // multiselect: trait_id strings OR 'any' (sentinel = "has any trait")
filterTransmuted: false,    // toggle button
filterCrafted: false,       // toggle button
filterGroupBySet: false,    // toggle button — changes table layout
```

### Computed Getters
- `filteredItems` — applies all active filters to `data.items`; `filterTraits` special-cases `'any'` (truthy trait_id)
- `groupedItems` — groups `filteredItems` by `set_name`, sorted alpha; no-set items go last
- `displayItems` — flat list of sentinel objects:
  - If `!filterGroupBySet`: `filteredItems.map(item => ({t:'item', item}))`
  - If `filterGroupBySet`: interleaves `{t:'h', set, count}` headers between item groups
- Label getters: `filterTypeLabel`, `filterLocTypeLabel`, `filterCharLabel`, `filterTraitLabel` — return "All X", single name, or "Name +N"

### Table Rendering Pattern (Group By Set)
Single `x-for="row in displayItems"` with `:key="row.t === 'h' ? 'h_' + row.set : row.item.key"`.
Each `<tr>` uses `x-show` on individual `<td>` elements to switch between header and item layouts — avoids nested `x-for` and keeps Alpine reactive updates fast.

### Dropdown Style (Multiselect)
Custom `x-data="{open:false}"` + `@click.outside="open=false"` wrappers. Options rendered as `<div>` rows — no `<input type="checkbox">`. Selected state shown via `bg-eso-gold/10 text-eso-gold` highlight; unselected via `text-eso-text hover:bg-eso-hover`. No checkmark icon. Trait dropdown has non-clickable group headers (Armor / Weapon / Jewelry) styled as `text-[10px] text-eso-muted uppercase`.

### Helper
```javascript
toggleFilter(arr, val) {
  const idx = arr.indexOf(val);
  if (idx >= 0) arr.splice(idx, 1); else arr.push(val);
}
```

## Character Detail Inventory Panel (`static/index.html`)

The character drill-down view is ordered Current Build → Character Inventory → WW Saved Builds. On `2xl` screens this is a three-column grid; below that, panels stack/wrap naturally. A compare-mode panel can temporarily replace this grid for side-by-side current vs imported build review.

### Character-Scoped Inventory State
The panel has its own filter state so it does not disturb the global Inventory tab:
```javascript
charInvSearch: '',
charInvQuality: '',
charInvTypes: [],
charInvLocTypes: [],     // bag ids as strings: '0'=Equipped, '1'=Backpack
charInvTraits: [],
charInvTransmuted: false,
charInvCrafted: false,
charInvGroupBySet: false,
detailPanelHeight: 0,
```

### Computed Getters / Helpers
- `charInventoryItems` — starts from `data.items`, keeps only locations where `location_type === 'character'` and `location_key === selectedChar.id`, then rewrites `locations`, `total_quantity`, and `key` for the selected character scope.
- `charFilteredItems` — applies the character panel filters to `charInventoryItems`.
- `charGroupedItems` / `charDisplayItems` — mirror the main Inventory tab group-by-set sentinel row pattern.
- `charInvTypeLabel`, `charInvLocLabel`, `charInvTraitLabel`, `charInvExtraFilterLabel` — compact labels for the character panel controls.
- `charItemLocations(item)` — returns the already-scoped `item.locations` for rendering.
- `clearCharInvFilters()` — resets only character-panel filters.
- `syncDetailPanelHeights()` — measures `x-ref="currentBuildPanel"` and sets `detailPanelHeight` only at `2xl` widths (`>=1536px`). Character Inventory and WW Saved Builds use `detailPanelHeightStyle` and internal scrolling so their bottoms align with Current Build.

### Rendering Notes
- Search gets its own full-width row; Type, Slots, Traits, More, Group by Set, and Clear share the second row.
- `More` contains quality pills plus Transmuted/Crafted toggles. `Group by Set` remains a visible button.
- The character-scoped inventory table intentionally omits the icon column to preserve width; the main Inventory tab still renders icons.
- The table still uses `tipShow(row.item, $event)` and set-name click-through behavior from the main Inventory tab.

## Achievements Tab (`static/index.html`)

`/api/achievements` carries mixed-persistence data:
- `account_items` — account-wide achievements
- `items_by_char` — character-persistent achievements keyed by `charId`
- `categories`, `earnedPts`, `totalPts` — account-level summary data

The character selector only changes the drill-down rows. `achievItemsByCatSubcat(catName, subcatName)` must merge the account bucket with the selected character bucket and dedupe by achievement id so mixed-persistence achievements render correctly for the active character.

## Item Link Decoder (`item_link_decoder.py`)

### Standard 21-field format
`|H1:item:F0:F1:...:F20|h[name]|h` — fields 0-indexed after `item:`:
| Field | Meaning |
|-------|---------|
| [0] | item_id |
| [2] | level requirement |
| [3] | enchant_id (0 = none) |
| [6] | trait_id |
| [14] | flags: bit8=stolen, bit11=transmuted |
| [15] | style_id |
| [16] | crafted (0/1) |
| [17] | bound (0/1) |
| [19] | sell_value |

### Known Bug — 20-field links
Some older/truncated item links have 20 fields (not 21). The decoder reads flags from `[14]` and crafted from `[16]` regardless — but in a 20-field link the flags are actually at `[13]`, and `[16]` may be missing or shifted. Fix (deferred): check `len(raw)` and adjust offsets accordingly.

### Transmuted vs Reconstructed
Both operations set bit 11 in the flags field. There is **no bit-level distinction** between a transmuted item and a reconstructed item — both appear as `is_transmuted=True`. The `is_crafted` flag (`[16]==1`) is unreliable as a discriminator due to the 20-field decoder bug.

## Known Quirks / Gotchas
- **WW mythic key**: `gear` dict has a `"mythic"` string key alongside integer slot keys — `process_ww_builds` skips non-integer keys with `int(slot_raw)` in a try/except.
- **Mythic items have `set_id=0`**: ESO doesn't populate `setId` for single-piece mythic sets. `fetchSetBonus` and the tooltip template use `set_id || _slugify(set_name)` as the cache key so mythics still get bonuses fetched. `_fetch_set_bonuses` on the server tracks `first_pieces` and breaks on the second bonus line when `first_pieces==1` — eso-sets.com pages for mythics list related multi-piece sets below the fold whose `(2-5 item)` lines would otherwise bleed through the `pieces <= last_pieces` guard.
- **`getBonusEntry(item)`** (frontend helper): looks up `setBonusCache` by `set_id || slug`; use this instead of `setBonusCache[item.set_id]` everywhere in templates to handle the mythic `set_id=0` case.
- **WW pages index 0**: `pages[zone][0]` is a char→pageNum mapping dict, not a page with a name — `page_info.get("name", f"Page {page_num}")` handles this.
- **Bank currency**: `GetCurrencyAmount(..., CURRENCY_LOCATION_BANK)` returns `nil` when called outside bank context — always guard with `or prevValue` in Lua.
- **Ability names keyed two ways**: iasync_data has both `abilityNames` and `$abilityNames` — `process_iasync_builds` merges both.
- **`x-html` for icons**: Location section icons and skill chips use `x-html` (not `x-text`) to render `<img>` tags. Content is safe — all from our own server.
- **`weaponType` is per-slot, not per-item**: iasync records it when a slot is scanned; if an item is swapped in after the last scan the old type sticks. `slotEquipIcon`/`itemIconHtml` discard the type when it claims "Staff" but the item name disagrees, then fall back to full name-based detection.
- **Shields are `filter_type 2`** (Armor) with `weaponType = "Shield"` and `armorType = nil`. Icon code checks `weapon_type === 'Shield'` before the armor-weight lookup.
- **CP values**: WW CP slots contain champion star IDs passed to `GetChampionSkillName()`, not point allocation counts.
- **Mundus icon key**: Strip "The " prefix before looking up: `name.toLowerCase().replace(/^the\s+/, '')` → `/assets/constellations/<key>.png`.
- **SSE reload**: Only fires when iasync.lua changes, not WizardsWardrobe.lua.
- **ESO Lua 5.1**: No `goto`, no `::labels::`. CharIdToName keys are strings after Lua→Python parsing.
- **`GetEquipmentFilterTypeForItemSetCollectionSlot` is misnamed**: Despite the name, it does NOT return `ITEM_FILTER_TYPE_*` values. It returns armor/weapon sub-type integers that are not useful for display. In `process_iasync_stickerbook`, `filterName` was dropped and piece names from `GetItemLinkName` are used instead.
