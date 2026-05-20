# Changelog

## [Unreleased]

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
