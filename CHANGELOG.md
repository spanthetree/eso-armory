# Changelog

## [Unreleased]

## [0.1.0-beta.20] - 2026-05-21

### Fixed
- **Workspace sharing docs and release metadata** — README, AGENTS, changelog, and package version now reflect the pairing-code shared workspace flow

## [0.1.0-beta.19] - 2026-05-21

### Added
- **Workspace pairing codes** — hosted browsers can now create or join a shared workspace from the header, copy a share link, or enter a pairing code so the same uploaded ESO data is available on a second browser or device later

### Changed
- **Shared workspace resolution** — `/api/data`, `/api/builds`, `/api/achievements`, `/api/stickerbook`, `/api/ww_builds`, `/api/upload`, `/api/status`, `/events`, and `/api/ttc_price` now resolve through a canonical shared workspace when a pairing code is present, while private browser sessions remain the default

## [0.1.0-beta.18] - 2026-05-21

### Changed
- **Manual TTC upload guidance** — docs now reflect the manual TTC lookup/price table upload path in the browser modal and the live-folder watcher flow

## [0.1.0-beta.17] - 2026-05-21

### Added
- **Manual TTC table upload** — the upload modal now includes file pickers for `ItemLookUpTable_EN.lua` and `PriceTableNA.lua` / `PriceTableEU.lua`, letting hosted users seed Collections pricing even without a live folder watcher

## [0.1.0-beta.16] - 2026-05-21

### Changed
- **Hosted live-folder upload flow** — the browser folder watcher now targets the ESO `live` folder instead of `SavedVariables/`, auto-uploads `SavedVariables/iasync.lua`, `SavedVariables/WizardsWardrobe.lua`, and Tamriel Trade Centre tables from `AddOns/TamrielTradeCentre/`, and passes the browser session through to `/api/ttc_price`
- **TTC session source selection** — `/api/ttc_price` now prefers the uploaded session TTC tables when they exist, falling back to the host machine's configured local TTC paths otherwise

## [0.1.0-beta.15] - 2026-05-21

### Added
- **Server wake-up spinner** — on page load the app polls `/api/status` before fetching data; if the server returns 503 the loading message switches to "Server is waking up…" and retries every 3 s until the server responds, then proceeds normally

### Fixed
- **Achievements character selector** — the drill-down now merges `account_items` with the selected character's `items_by_char` slice, so mixed-persistence achievements render correctly for the chosen character instead of showing only the per-character subset

## [0.1.0-beta.14] - 2026-05-21

### Added
- **Per-browser session isolation** — each browser generates a UUID on first load (`crypto.randomUUID()`) persisted to `localStorage` as `eso-session-id`; all data, upload, status, and SSE requests include `?session=<uuid>` so multiple users on the same hosted instance see only their own data
- **Per-session server storage** — uploaded files go to `uploads/<session_id>/` and parsed data is held in a per-session in-memory cache; sessions without uploads fall back to the global cache transparently (local users running against `config.json` paths are unaffected)
- **Session SSE isolation** — `/events?session=<id>` connects to a session-specific queue; upload reload events notify only the uploading session's connected browsers
- **Session cleanup** — background task runs every 5 minutes and evicts sessions idle for more than 2 hours, deleting their `uploads/<session_id>/` directory
- **UUID path-traversal guard** — session IDs are validated against a strict UUID regex before use as filesystem paths; invalid values fall back to the global cache

### Changed
- `_parse_iasync()` and `_parse_ww()` refactored into `_parse_iasync_into(path, cache)` / `_parse_ww_into(path, cache)` that accept explicit path and cache targets; the original functions are now thin wrappers around the global config and cache — enables per-session parsing without code duplication

## [0.1.0-beta.13] - 2026-05-21

### Added
- **File upload endpoint** — `POST /api/upload` accepts `iasync.lua` and/or `WizardsWardrobe.lua` as multipart form uploads, writes them to `uploads/`, re-parses immediately, and returns item/character/build counts; enables hosting the app for others to test without server-side ESO path access
- **First-run setup screen** — when no data is loaded the app shows a centered card with a "Select Files…" button linking to the upload modal, replacing the blank error state
- **Upload modal** — accessible via "⬆ Upload" header button or the setup screen; drag-and-drop or click-to-select inputs for `iasync.lua` (inventory) and `WizardsWardrobe.lua` (optional builds); shows parse results and closes on success
- **Folder watcher (Chrome/Edge)** — "Auto-Watch Folder" section in the upload modal uses the File System Access API (`showDirectoryPicker`) to select the SavedVariables directory; polls every 5 s, re-uploads any file whose `lastModified` has changed, and toasts on update
- **IndexedDB persistence** — the selected `FileSystemDirectoryHandle` is stored in `indexedDB` (`eso-armory/kv`); permission is re-verified on page load without a user gesture and the watcher resumes automatically if still granted
- **Refresh button** — "↻ Refresh" in the header checks for updates on demand: with a folder handle it compares file `lastModified`; without one it calls `/api/status` and compares server-side mtime against the last fetched ETag; toasts "Data updated ✓" or "No updates"
- **Watching indicator** — a gold dot and folder name appear in the header when the folder watcher is active
- `python-multipart>=0.0.9` dependency added (required by FastAPI for multipart upload)

## [0.1.0-beta.12] - 2026-05-21

### Fixed
- **TTC tooltip price display diagnostics** — missing `/api/ttc_price` route responses now surface as explicit HTTP errors in the tooltip, making stale server processes obvious; restart the server after route changes so the price endpoint is registered.

## [0.1.0-beta.11] - 2026-05-21

### Changed
- **Character detail inventory panel polish** — character drill-down pages now lay out as Current Build → Character Inventory → WW Saved Builds, compact the character inventory filters into a dedicated search row plus short dropdown labels, hide item icons in the character-scoped table to save width, and height-match the Inventory and WW panels to the Current Build panel on wide screens

## [0.1.0-beta.10] - 2026-05-21

### Added
- **TTC price tooltips for Collections pieces** — individual stickerbook pieces now fetch local Tamriel Trade Centre price data on hover, showing lowest/average/highest prices, listing counts, TTC table timestamp, ESO Armory fetch time, and TTC attribution while preserving click-through search links

### Fixed
- **TTC tooltip error visibility** — failed `/api/ttc_price` requests now display the HTTP/error status in the tooltip instead of leaving the price area blank

## [0.1.0-beta.9] - 2026-05-21

### Fixed
- **Theme consistency — Collections progress bars** — stickerbook category nav bars, summary total bar, per-category grid bars, set card progress bars (all 3 card views: search, direct, subcategorized), and the stickerbook set tooltip bar all now use `var(--t-progress)` via inline style instead of `bg-eso-gold` Tailwind classes; complete vs incomplete sets distinguished by `opacity:1` vs `opacity:0.5`; matches the achievements tab's existing pattern

## [0.1.0-beta.8] - 2026-05-21

### Added
- **Character detail inventory panel** — character drill-down pages now include a character-scoped inventory panel alongside Current Build and WW Saved Builds, with search, quality/type/location/trait filters, Transmuted and Crafted toggles, Group by Set, sorting, tooltips, and set links

### Changed
- Character detail inventory filters are more compact: search now sits on its own row, dropdown labels are shortened, quality/Transmuted/Crafted live in a single dropdown, item icons are hidden in the character-scoped table, and Group by Set remains a visible toggle; the inventory and WW build panels are height-matched on wide screens with internal scrolling

### Fixed
- **Mythic set tooltip** — `_fetch_set_bonuses` now stops after the first (1-piece) bonus instead of continuing into related sets listed lower on the eso-sets.com page; previously all 4–5 bonus lines from an adjacent regular set were shown
- **Set bonus tooltip for mythic items** — `fetchSetBonus` and the tooltip template no longer require a non-zero `set_id`; when `set_id=0` the name slug is used as the cache key so the fetch fires and the bonuses section renders correctly
- **Server-side set bonus cache collision** — `_set_bonus_cache` now keys by `slug` instead of `0` when `set_id=0`, preventing all mythic items from sharing one cache slot

## [0.1.0-beta.7] - 2026-05-21

### Added
- **Dark theme** — GitHub-dark-inspired palette: near-black navy background, blue accent (`#58a6ff`), cyan progress bars
- **Light theme** — warm parchment palette: cream background, white cards, darkened amber accent readable on light backgrounds
- **Synthwave theme** — deep purple background (`#0d001a`), electric violet accent (`#bf5fff`), neon cyan progress bars

### Changed
- Theme dropdown button always displays "Theme" rather than the active theme name
- "ESO Classic" theme renamed to "Gold"; any saved `eso` value in localStorage migrated automatically
- Dropdown emoji removed; theme list order: Gold → Light → Dark → Synthwave → Outrun

## [0.1.0-beta.6] - 2026-05-21

### Added
- **Color themes** — swappable UI color palettes with a "Theme" dropdown in the header; selection persists to `localStorage`
  - **Gold** — the original amber/gold-on-dark palette (default, formerly "ESO Classic")
  - **Outrun** — deep navy background, hot-pink primary accent, cyan progress bars
- **Theme architecture** — all UI chrome colors converted to CSS custom properties (`--t-*`); theme-specific overrides injected as a `<style>` block at runtime so Tailwind CDN class names respond correctly; FOUC prevented by a pre-Alpine inline script

## [0.1.0-beta.5] - 2026-05-20

### Added
- **Multiselect inventory filters** — Type, Location, Character, and Trait dropdowns now accept multiple selections simultaneously; active selections highlight gold, clear individually or via the Clear button
- **Transmuted filter button** — dedicated toggle button on the filter bar (removed from the Trait dropdown); filters to items with bit 11 set in the item link flags field
- **Crafted filter button** — dedicated toggle button alongside Transmuted; filters to items where `is_crafted` is true
- **Group by Set toggle** — button that switches the inventory table into a grouped view with set-name headers and per-group item counts; items not belonging to a set appear last
- **Gear icons for all slot/weight combinations** — Breton-style webp artwork added for heavy, medium, and light armor (7 slots each), weapons (10 types), and jewelry (neck/ring); stored in `assets/gear/`

### Changed
- Inventory filter bar split into two rows: search + dropdowns on row 1; quality pills + toggle buttons (Transmuted, Crafted, Group by Set, Clear) on row 2
- Trait dropdown no longer contains a "Transmuted" entry — use the dedicated Transmuted toggle button instead
- Group by Set is now a button (was a checkbox label)
- Dropdown options rendered as highlighted `<div>` rows (no checkbox icons) — selected items shown with gold background tint

## [0.1.0-beta.4] - 2026-05-20

### Added
- **Armor weight and weapon type tags** in item tooltip — iasync now supplies `armorType` (Light/Medium/Heavy) and `weaponType` (Sword, Bow, etc.) directly; both appear as badge tags alongside trait/style/enchant
- **Gear icons** replace generic interface icons for all items — inventory list, character equipment panels, and character drilldown all use slot-specific Breton-style webp artwork from `assets/gear/`
  - Armor: correct slot piece per weight class (e.g. heavy helm for head slot, light shirt for chest)
  - Weapons: specific icon per type (dagger, 1h/2h sword/axe/hammer, bow, staff, shield)
  - Jewelry: neck vs. ring distinguished by slot
- **Name-based weapon icon fallback** — when `weaponType` is null or stale, item name keywords resolve the correct icon so old/unscanned characters still show meaningful icons

### Changed
- `item_db.py` removed — name-based weapon type heuristics replaced by reading `weaponType`/`armorType` directly from iasync item data
- Shield icon fix: shields have `filter_type = 2` (Armor) but carry `weaponType = "Shield"`; icon logic now checks `weapon_type` before the armor-weight lookup
- Stale iasync slot data guard: if `weaponType` claims a staff type but item name disagrees, the type is discarded and name-based detection runs instead

## [0.1.0-beta.3] - 2026-05-19

### Added
- **Achievements tab** — replaces Locations tab; account-wide achievement summary with category/subcategory drill-down, per-character filtering, progress bars for incomplete criteria, and a recent completions panel
- **`/api/achievements` endpoint** — parses `iasync_data.achievements` into category summaries, per-character item lists, and a top-10 recent completions list
- **Achievement tooltips** — hover over recent achievement icons to see name, description, points, completion date, and criteria progress
- **Loguru logging** — replaces `print()` throughout `server.py`; two sinks: colored console (INFO+) and rotating file `logs/armory.log` (DEBUG+, 10 MB max, 5 files, gzip compression)
- **HTTP request middleware** — logs method, path, status code, and elapsed ms for every non-static request
- **SSE connection logging** — logs client IP on connect and disconnect

### Fixed
- **Lua string escape sequences** — `lua_parser.py` `_parse_string` now correctly handles `\"`, `\n`, `\t`, `\r`, and `\\` escape sequences instead of stopping at the first backslash
- **Account name detection** — `process_iasync()` now checks `raw["accountName"]` key first before scanning for `@`-prefixed keys
- **File watcher silent errors** — bare `except: pass` blocks in `_file_watcher` now log a `WARNING` instead of swallowing exceptions

### Changed
- SSE reload event now also refreshes achievements data alongside inventory

## [0.1.0-beta.2] - 2026-05-19

### Changed
- **uv** replaces pip for dependency management — `pyproject.toml` + `uv.lock` added, `requirements.txt` removed; use `uv sync` (or `uv sync --active` if a virtualenv is already active)

### Fixed
- **Blank inventory locator column** for items stacked across multiple bag slots — `_add_slot` now merges same-character/same-bag location entries instead of appending duplicates, eliminating the Alpine.js `x-for` key collision that suppressed all location badges

## [0.1.0-beta.1] - 2026-05-19

### Added
- **iasync addon** — companion ESO addon that exports data IIfA doesn't persist:
  - Ability names (`GetAbilityName`) and Champion Point star names (`GetChampionSkillName`) for WizardsWardrobe builds
  - Bank currency (gold, AP, Telvar Stones, Writ Vouchers) via `CURRENCY_LOCATION_BANK`
  - Active character's live currency via `CURRENCY_LOCATION_CHARACTER` (overrides stale IIfA asset on load)
  - Falls back to previously saved bank values if bank API returns nil (e.g. not at bank)

- **WizardsWardrobe builds** — new builds view accessible by clicking a character card:
  - Gear list with item names, quality colors, and tooltip on hover
  - Skills section: primary and backup bars, slots 3–7 as ability chips, slot 8 (ultimate) highlighted in gold
  - Champion Points section: three-column grid with tree color coding (Warfare green / Fitness blue / Craft orange)
  - Food buff display

- **Character detail view** — clicking a character now navigates into a detail page with paper-doll on the left and WW builds on the right, replacing the former separate Builds tab

- **Currency totals in header** — gold, Alliance Points, Telvar Stones, and Writ Vouchers summed across all characters + bank; AP and TV hidden when zero

- **Telvar Stones** — added `tv` field to character assets; displayed on character cards and in header

- **Bank currency** — `data.bank` in API response aggregates currency from IIfA asset entries not mapped to a known character (likely account bank entries)

- **`/api/builds` endpoint** — returns WW builds, iasync ability/CP name maps, bank currency, and active character live currency

- **`parse_lua_variable()`** — generic Lua SavedVariable parser used for iasync_DATA

- **`parse_ww_data()`** — parser for WizardsWardrobeSV

- **`process_builds()`** — transforms raw WW data into flat build list; decodes item links for trait/style/enchant info per gear piece

- **Platform-aware path detection** — `_eso_sv_path()` auto-detects SavedVariables paths on Windows and WSL2

- **`wv` (Writ Vouchers)** field surfaced from IIfA assets

### Changed
- Characters tab cards are now clickable; cards with WW builds show a gold ring accent
- Header right side replaced static item count with character count + full currency breakdown
- `DEFAULT_CONFIG` now includes `ww_lua_path` and `iasync_lua_path` with platform-detected defaults
- File watcher polls all three SavedVariables files independently
- `data_processor.process()` now returns a `bank` key with aggregated currency from non-character asset entries
- Character cards and detail panel show TV alongside gold and AP

### Fixed
- WW gear `["mythic"]` string key no longer causes a crash in `process_builds()` (non-integer slot keys are skipped)
- iasync Lua rewritten to remove `goto`/`::label::` syntax (ESO uses Lua 5.1, which lacks these)
- Bank currency `GetCurrencyAmount(..., CURRENCY_LOCATION_BANK)` returns `nil` outside bank context — guarded with `or prevValue` fallback to preserve last known value across sessions
