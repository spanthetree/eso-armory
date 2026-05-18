# ESO Armory — Agent Notes

## Project Overview
Local web app that reads ESO SavedVariables and presents inventory, equipment, and builds in a WoW-Armory-style browser. FastAPI backend, Alpine.js + Tailwind CDN frontend (no build step). Designed for WSL2 on Windows where the ESO client runs natively.

## Stack
- **Backend**: Python / FastAPI + Uvicorn (`server.py`)
- **Frontend**: Single-file `static/index.html` — Alpine.js 3.x, Tailwind CDN, no build step
- **Lua parser**: Custom recursive-descent in `lua_parser.py` (stdlib only, no lupa/lark)
- **Start**: `python3 server.py` → http://localhost:5000

## Key Files
| File | Purpose |
|------|---------|
| `server.py` | FastAPI app, file watcher, caches, SSE push, ability icon map |
| `lua_parser.py` | Recursive-descent Lua parser: `parse_lua_variable(path, varname)` |
| `data_processor.py` | `process_iasync()`, `process_iasync_builds()`, `process_ww_builds()` |
| `item_link_decoder.py` | Decodes ESO `\|H1:item:...\|h` links → trait/style/enchant fields |
| `item_db.py` | Name-based item enrichment (weapon type, etc.) |
| `config.json` | Paths to Lua files, port, server region, poll interval |
| `iasync/iasync.lua` | ESO addon (symlinked to Windows AddOns folder) |
| `static/index.html` | Full SPA (Characters, Inventory, Locations tabs) |

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
| `GET /api/ww_builds` | `{builds: {charId: [build, ...]}}` from WizardsWardrobe |
| `GET /api/ability_icons` | `{normalizedName: "/assets/abilities/...png"}` — scanned at startup |
| `GET /api/status` | `{ok, item_count, character_count, last_modified, error}` |
| `GET /events` | SSE stream; sends `"reload"` when iasync file changes |

## Server Caches (server.py)
```python
_cache      = {data_bytes, builds_bytes, mtime, error}   # iasync
_ww_cache   = {ww_builds_bytes, mtime, error}             # WizardsWardrobe
_ability_icon_map: dict                                    # built at startup, static
```
`_ability_icon_map` is built by `_build_ability_icon_map()` at startup — scans `assets/abilities/**/*.png`, normalizes stems to keys.

## Assets System
All icons are served via `app.mount("/assets", StaticFiles(directory="assets"))`.

### Icon normalization (both Python and JS must match)
```python
# Python (server.py _build_ability_icon_map):
key = re.sub(r'[^a-z0-9]+', '_', png.stem.lower()).strip('_')

# JS (index.html abilityIcon()):
const key = name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')
```
"Lava Whip" → `lava_whip` → `/assets/abilities/class/dragonknight/ardent_flame/lava_whip.png`

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

All icons sourced from UESP MediaWiki (`images.uesp.net`). Browser User-Agent required for image downloads: `curl -sL -A "Mozilla/5.0" <url>`.

UESP API for URL resolution: `https://en.uesp.net/w/api.php?action=query&prop=imageinfo&iiprop=url&format=json&titles=File:X|File:Y`

## UI Structure (`static/index.html`)
Single Alpine.js component (`armory()`). Three tabs: Characters, Inventory, Locations.

### App State
```javascript
data         // /api/data response
builds       // /api/builds response  (abilityNames, cpNames, per-char build bars)
wwBuilds     // /api/ww_builds response
abilityIcons // /api/ability_icons response
charMaps     // {charId: {slot: gearItem}} — equipped gear per char, built from data.items
itemIdMap    // {itemId: item} — for WW gear name lookups (WW links lack embedded names)
selectedChar // currently expanded character object
tab          // 'characters' | 'inventory' | 'locations'
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
```

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
fuser -k 5000/tcp && sleep 0.5 && uv run server.py
```
If an existing virtualenv is active (i.e. `uv sync --active` was used), run directly instead:
```bash
fuser -k 5000/tcp && sleep 0.5 && python server.py
```
Use `fuser -k 5000/tcp` (not `pkill`) — it targets the port directly and works reliably in WSL2.

## Known Quirks / Gotchas
- **WW mythic key**: `gear` dict has a `"mythic"` string key alongside integer slot keys — `process_ww_builds` skips non-integer keys with `int(slot_raw)` in a try/except.
- **WW pages index 0**: `pages[zone][0]` is a char→pageNum mapping dict, not a page with a name — `page_info.get("name", f"Page {page_num}")` handles this.
- **Bank currency**: `GetCurrencyAmount(..., CURRENCY_LOCATION_BANK)` returns `nil` when called outside bank context — always guard with `or prevValue` in Lua.
- **Ability names keyed two ways**: iasync_data has both `abilityNames` and `$abilityNames` — `process_iasync_builds` merges both.
- **`x-html` for icons**: Location section icons and skill chips use `x-html` (not `x-text`) to render `<img>` tags. Content is safe — all from our own server.
- **CP values**: WW CP slots contain champion star IDs passed to `GetChampionSkillName()`, not point allocation counts.
- **Mundus icon key**: Strip "The " prefix before looking up: `name.toLowerCase().replace(/^the\s+/, '')` → `/assets/constellations/<key>.png`.
- **SSE reload**: Only fires when iasync.lua changes, not WizardsWardrobe.lua.
- **ESO Lua 5.1**: No `goto`, no `::labels::`. CharIdToName keys are strings after Lua→Python parsing.
