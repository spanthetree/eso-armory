# Changelog

## [Unreleased]

## [0.1.0-beta.37] - 2026-06-11

### Added
- **World ability icons** - icons added for all seven world skill trees: Bestial Transformation, Excavation, Legerdemain, Scrying, Soul Magic, Vampire, and Werewolf

### Fixed
- **Account name input placeholder** - login input now reads "accountname (case sensitive)" to clarify the expected format and that the value is case-sensitive

## [0.1.0-beta.36] - 2026-05-28

### Added
- **Onboarding tooltips** - `?` popover buttons in the upload modal explain what each file is and where to find it (`iasync.lua`, `WizardsWardrobe.lua`, live-folder watcher); only one tooltip open at a time; closes on Escape or click-away
- **Guided empty state** - the setup card now shows a numbered 3-step guide (log in, find SavedVariables folder, upload) instead of a plain paragraph

### Fixed
- **503 no longer shown as error on first load** - HTTP 503 from `/api/data` (expected when no data has been uploaded) is now treated silently: `data` is cleared but `error` is not set; error text is also guarded so it cannot appear while the page is in the empty/setup state
- **Incognito infinite loading** - `fetchData` was restructured to never `return` or `throw` inside the `try` block, guaranteeing `finally { loading = false }` always runs; previously a 503 response could leave the page stuck in a loading spinner in fresh browser sessions

### Changed
- **Error messages unified** - "No data loaded", "Achievements unavailable", "Collections unavailable" all replaced with "User data not loaded" for consistent language across all tabs and endpoints

## [0.1.0-beta.35] - 2026-05-28

### Changed
- **Folder watcher - change-detection only** - removed the 15-minute force-sync; the watcher now uploads files only when their `lastModified` timestamp has advanced since the last sync; the manual Refresh button still triggers an immediate check-and-upload pass; eliminates ~50 MB of unnecessary inbound traffic every 15 minutes for admin accounts with large TTC price tables

## [0.1.0-beta.34] - 2026-05-28

### Security
- **Stored XSS fix** - ability names from uploaded Lua files and imported build payloads are now HTML-escaped before injection via Alpine `x-html` (`abilitySlotHtml` / `abilitySlotHtmlCompare`); a crafted Lua file with HTML in an ability name could previously execute script in any viewer's browser when accessed via a share code or build import code
- **Upload size limits** - all upload paths now enforce a 100 MB cap per file (iasync, WW, TTC); SuperStar image uploads are capped at 20 MB; oversized requests return HTTP 413
- **Login rate limiting** - per-IP brute-force protection: 5 failures within 60 s triggers a 5-minute lockout; blocked requests return HTTP 429
- **Login timing oracle fixed** - when an account does not exist the server now compares the submitted password against a dummy bcrypt hash instead of returning immediately, preventing account-existence enumeration via response timing; the bcrypt check is also offloaded to a thread executor to avoid blocking the event loop
- **Security response headers** - all responses now include `X-Frame-Options: DENY` (clickjacking prevention) and `Referrer-Policy: no-referrer` in addition to the existing `X-Content-Type-Options: nosniff`
- **SSE connection cap** - session-scoped SSE connection sets are now capped at 10 concurrent connections; excess attempts return HTTP 429

## [0.1.0-beta.33] - 2026-05-26

### Added
- **Admin badge in header** - when the active account has `is_admin`, a small gold "admin" badge appears inline after the account · server · items line

### Fixed
- **TTC concurrent build race** - multiple simultaneous TTC price requests no longer race to build the SQLite database; `_TTC_BUILD_LOCK` serialises the build step with a double-checked guard so only the first thread builds and waiters reuse the finished DB, eliminating "table already exists", "no such table: meta", and "database disk image is malformed" errors on first page load

### Changed
- **Global TTC storage** - uploaded TTC files are now stored at `uploads/ttc/` (shared across all sessions) instead of per-account or per-session directories; any admin upload upserts the single global copy; the derived SQLite is rebuilt whenever the raw file mtime is newer than the last build
- **Session simplification** - sessions no longer hold a per-session `ttc_cache`, `upload_dir`, or on-disk directory; TTC lookup always uses the global `_ttc_tables` cache

### Removed
- Per-account TTC file storage (`uploads/accounts/<account>/AddOns/TamrielTradeCentre/`) - replaced by global `uploads/ttc/`
- `_empty_ttc_cache`, `_resolve_ttc_cache`, `_rehydrate_session_from_disk` - no longer needed
- Per-session upload directories - sessions are now purely in-memory

## [0.1.0-beta.32] - 2026-05-26

### Changed
- **Upload-only data ingestion** - the server no longer reads `iasync.lua` or `WizardsWardrobe.lua` from local disk paths; data reaches the server exclusively via browser upload or the folder watcher, making the app safe to host remotely
- **Parse-all-upfront on upload** - all four iasync payload types (inventory/data, builds, achievements, stickerbook) are parsed in memory on upload and stored to SQLite immediately; raw Lua bytes are discarded after parsing and never persisted on disk
- **Admin-only TTC upload** - Tamriel Trade Centre file upload is now restricted to accounts flagged `is_admin` in the database; non-admin uploads receive a clear error; `@admin_account` is auto-granted admin on first upload
- **Folder watcher timing** - metadata-only `lastModified` check every 60 s (no file content read unless changed); full force-sync every 15 minutes; admin accounts also sync TTC tables from `AddOns/TamrielTradeCentre/`
- **Per-file sync status** - the folder watcher UI shows last-synced time per file (iasync, WW, TTC lookup, TTC price) and a last-checked timestamp
- **Recovery error clarity** - if DB payloads are missing and no source is available, endpoints return HTTP 503 with a "please re-upload" message instead of attempting to reconstruct from missing data

### Removed
- Server-side SavedVariables path detection (WSL2 / Windows auto-discovery) and local file polling - no longer needed
- `source_path`, `source_bytes`, `ww_source_path`, `ww_source_bytes`, `raw_iasync_lua`, and `raw_ww_lua` from session caches and DB rows - raw data is not retained after parse
- `poll_interval_seconds` config key
- `iasync_lua_path` and `ww_lua_path` config keys

## [0.1.0-beta.31] - 2026-05-25

### Added
- **SuperStar Compare** - upload or paste a screenshot from the ESO SuperStar addon; Claude Vision (claude-sonnet-4-6) parses the build and produces a slot-by-slot comparison against the currently equipped gear for the selected character, with colour-coded status: equipped, have it (wrong slot), wrong trait, or missing; supports paste (Ctrl+V), drag-and-drop, and file picker
- **`POST /api/parse_superstar`** - accepts a multipart image upload, sends it to the Anthropic API with a structured extraction prompt, annotates each gear slot with its numeric `slot_id`, and returns the parsed build JSON; requires `ANTHROPIC_API_KEY` in the environment or `anthropic_api_key` in `config.json`

## [0.1.0-beta.30] - 2026-05-23

### Fixed
- **Render/shared export context** - `POST /api/build_export` now resolves account and cache state with the active `share` context instead of treating hosted/shared browsers as unbound local sessions, fixing `upload armory data before exporting a build` failures on Render-hosted workspaces
- **Hosted export error visibility** - export failures and clipboard-blocked exports now surface through toasts even outside compare mode, so drilldown users get visible feedback instead of silent no-op behavior

## [0.1.0-beta.29] - 2026-05-22

### Changed
- **Single export code per character** - `POST /api/build_export` now overwrites the existing export for the same `account_name + character_id` instead of creating additional rows/codes on repeated exports
- **Export row dedupe on overwrite** - if legacy duplicate export rows exist for the same account+character, the export upsert path now keeps one row and removes extras

## [0.1.0-beta.28] - 2026-05-22

### Changed
- **Export build fidelity** - build exports now include stronger per-slot gear metadata coverage (quality, quality color/name, armor weight, weapon type, filter type, level, enchant/trait/set fallbacks) and server-side export enrichment from equipped `/api/data` state to prevent stale/missing metadata in exported codes
- **Imported compare name fidelity** - compare imports now carry/export scoped `ability_names` and `cp_names` so imported skills and slotted CP names render even when the active workspace lacks those ids
- **Missing-item pricing gate** - compare missing-items now classifies each row before TTC lookup and only price-checks truly purchasable items; crafted and stickerbook Dungeon/Trial/Arena sourced items are explicitly skipped and excluded from purchasable totals
- **Workspace pill navigation** - clicking `Primary` or `Shadow` workspace pills now returns to the Characters home view while switching context

## [0.1.0-beta.27] - 2026-05-22

### Added
- **Character drilldown build compare** - added `Export Build Code` and `Compare Build` actions in character drilldown, with a dedicated compare view that supports import-by-code and return-to-drilldown navigation
- **Clipboard export UX** - exporting a build code now attempts to copy to clipboard automatically and shows a toast when successful
- **Persistent compare build storage** - added DB-backed build export/import models and APIs:
  - `POST /api/build_export`
  - `GET /api/compare_builds`
  - `POST /api/compare_builds/import`
  - `DELETE /api/compare_builds`

### Changed
- **Compare missing-items panel** - compare mode now highlights missing imported-build gear, source hints from stickerbook metadata, and TTC-based purchasable totals when available
- **Workspace-scoped compare state** - imported compare builds are stored per workspace/account/character and reload from SQLite with the rest of uploaded workspace state

## [0.1.0-beta.26] - 2026-05-22

### Added
- **SQLite-backed uploaded workspaces** - uploaded `iasync.lua` and `WizardsWardrobe.lua` raw source plus processed API payloads are now persisted in `uploads/armory.db`, so uploaded account workspaces can be reopened directly from the database
- **Workspace slot controls** - the header now includes a primary/shadow workspace selector beneath the account name, plus an inline shadow-delete control when the shadow slot is active

### Changed
- **Uploaded workspace routing** - browser sessions now track one primary account and one optional shadow account; a second distinct uploaded ESO account fills the shadow slot instead of replacing the primary workspace
- **Hosted read path** - uploaded `/api/data`, `/api/builds`, `/api/achievements`, `/api/stickerbook`, and `/api/ww_builds` requests now resolve from DB-backed account state rather than depending on copied uploaded SavedVariables files

### Fixed
- **WizardsWardrobe parser compatibility** - `WizardsWardrobeSV={` assignments without a space before `=` are now accepted, avoiding false parse failures for valid SavedVariables files

## [0.1.0-beta.25] - 2026-05-22

### Fixed
- **Frontend startup reliability** - Alpine.js is now served from `static/vendor/alpine.min.js` instead of the jsDelivr CDN, preventing a white page when hosted browsers cannot reach `cdn.min.js`

## [0.1.0-beta.24] - 2026-05-22

### Added
- **Project header artwork** - added `header.svg`, an ESO Armory-branded terminal-style header matching the sibling addon header style and highlighting inventory, equipment, builds, and collections

## [0.1.0-beta.23] - 2026-05-22

### Added
- **Static serving regression coverage** - Playwright now checks first-load rendering in Chromium and Firefox and fails if the page dumps HTML, Lua data, or inline Alpine source instead of the setup UI
- **Response header API coverage** - tests now verify `/`, `HEAD /`, and `/static/index.html` return HTML content types with `X-Content-Type-Options: nosniff`

### Changed
- **App shell delivery** - `/` now explicitly serves `static/index.html` as `text/html; charset=utf-8` with `Cache-Control: no-store` and `nosniff` headers
- **Upload failure messaging** - malformed JSON or proxy HTML responses now show concise upload errors rather than browser `JSON.parse` wording
- **Repository hygiene** - Vim swap files are ignored by git

## [0.1.0-beta.22] - 2026-05-22

### Added
- **Test harness** - added pytest unit/API coverage, Playwright UI test scaffolding for Chromium and Firefox, mutmut mutation-test configuration, Makefile test commands, and CI workflow entries
- **Sanitized fixtures** - added committed sanitized fixtures plus fixture-safety checks for parser, processor, upload, sharing, and TTC price flows
- **Per-browser UI test targets** - added `make test-ui-chromium` and `make test-ui-firefox` alongside the existing all-browser `make test-ui` target

### Changed
- **Upload error handling** - non-JSON proxy errors now surface as actionable HTTP/content messages instead of JSON parse failures

## [0.1.0-beta.21] - 2026-05-21

### Changed
- **Ability icon discovery** - current builds and WizardsWardrobe saved builds now resolve ability icons from both PNG and WebP assets, enabling the new scribing icons for Chilling Throw and Shocking Contingency

## [0.1.0-beta.20] - 2026-05-21

### Fixed
- **Workspace sharing docs and release metadata** - README, AGENTS, changelog, and package version now reflect the pairing-code shared workspace flow

## [0.1.0-beta.19] - 2026-05-21

### Added
- **Workspace pairing codes** - hosted browsers can now create or join a shared workspace from the header, copy a share link, or enter a pairing code so the same uploaded ESO data is available on a second browser or device later

### Changed
- **Shared workspace resolution** - `/api/data`, `/api/builds`, `/api/achievements`, `/api/stickerbook`, `/api/ww_builds`, `/api/upload`, `/api/status`, `/events`, and `/api/ttc_price` now resolve through a canonical shared workspace when a pairing code is present, while private browser sessions remain the default

## [0.1.0-beta.18] - 2026-05-21

### Changed
- **Manual TTC upload guidance** - docs now reflect the manual TTC lookup/price table upload path in the browser modal and the live-folder watcher flow

## [0.1.0-beta.17] - 2026-05-21

### Added
- **Manual TTC table upload** - the upload modal now includes file pickers for `ItemLookUpTable_EN.lua` and `PriceTableNA.lua` / `PriceTableEU.lua`, letting hosted users seed Collections pricing even without a live folder watcher

## [0.1.0-beta.16] - 2026-05-21

### Changed
- **Hosted live-folder upload flow** - the browser folder watcher now targets the ESO `live` folder instead of `SavedVariables/`, auto-uploads `SavedVariables/iasync.lua`, `SavedVariables/WizardsWardrobe.lua`, and Tamriel Trade Centre tables from `AddOns/TamrielTradeCentre/`, and passes the browser session through to `/api/ttc_price`
- **TTC session source selection** - `/api/ttc_price` now prefers the uploaded session TTC tables when they exist, falling back to the host machine's configured local TTC paths otherwise

## [0.1.0-beta.15] - 2026-05-21

### Added
- **Server wake-up spinner** - on page load the app polls `/api/status` before fetching data; if the server returns 503 the loading message switches to "Server is waking up…" and retries every 3 s until the server responds, then proceeds normally

### Fixed
- **Achievements character selector** - the drill-down now merges `account_items` with the selected character's `items_by_char` slice, so mixed-persistence achievements render correctly for the chosen character instead of showing only the per-character subset

## [0.1.0-beta.14] - 2026-05-21

### Added
- **Per-browser session isolation** - each browser generates a UUID on first load (`crypto.randomUUID()`) persisted to `localStorage` as `eso-session-id`; all data, upload, status, and SSE requests include `?session=<uuid>` so multiple users on the same hosted instance see only their own data
- **Per-session server storage** - uploaded files go to `uploads/<session_id>/` and parsed data is held in a per-session in-memory cache; sessions without uploads fall back to the global cache transparently (local users running against `config.json` paths are unaffected)
- **Session SSE isolation** - `/events?session=<id>` connects to a session-specific queue; upload reload events notify only the uploading session's connected browsers
- **Session cleanup** - background task runs every 5 minutes and evicts sessions idle for more than 2 hours, deleting their `uploads/<session_id>/` directory
- **UUID path-traversal guard** - session IDs are validated against a strict UUID regex before use as filesystem paths; invalid values fall back to the global cache

### Changed
- `_parse_iasync()` and `_parse_ww()` refactored into `_parse_iasync_into(path, cache)` / `_parse_ww_into(path, cache)` that accept explicit path and cache targets; the original functions are now thin wrappers around the global config and cache - enables per-session parsing without code duplication

## [0.1.0-beta.13] - 2026-05-21

### Added
- **File upload endpoint** - `POST /api/upload` accepts `iasync.lua` and/or `WizardsWardrobe.lua` as multipart form uploads, writes them to `uploads/`, re-parses immediately, and returns item/character/build counts; enables hosting the app for others to test without server-side ESO path access
- **First-run setup screen** - when no data is loaded the app shows a centered card with a "Select Files…" button linking to the upload modal, replacing the blank error state
- **Upload modal** - accessible via "⬆ Upload" header button or the setup screen; drag-and-drop or click-to-select inputs for `iasync.lua` (inventory) and `WizardsWardrobe.lua` (optional builds); shows parse results and closes on success
- **Folder watcher (Chrome/Edge)** - "Auto-Watch Folder" section in the upload modal uses the File System Access API (`showDirectoryPicker`) to select the SavedVariables directory; polls every 5 s, re-uploads any file whose `lastModified` has changed, and toasts on update
- **IndexedDB persistence** - the selected `FileSystemDirectoryHandle` is stored in `indexedDB` (`eso-armory/kv`); permission is re-verified on page load without a user gesture and the watcher resumes automatically if still granted
- **Refresh button** - "↻ Refresh" in the header checks for updates on demand: with a folder handle it compares file `lastModified`; without one it calls `/api/status` and compares server-side mtime against the last fetched ETag; toasts "Data updated ✓" or "No updates"
- **Watching indicator** - a gold dot and folder name appear in the header when the folder watcher is active
- `python-multipart>=0.0.9` dependency added (required by FastAPI for multipart upload)

## [0.1.0-beta.12] - 2026-05-21

### Fixed
- **TTC tooltip price display diagnostics** - missing `/api/ttc_price` route responses now surface as explicit HTTP errors in the tooltip, making stale server processes obvious; restart the server after route changes so the price endpoint is registered.

## [0.1.0-beta.11] - 2026-05-21

### Changed
- **Character detail inventory panel polish** - character drill-down pages now lay out as Current Build → Character Inventory → WW Saved Builds, compact the character inventory filters into a dedicated search row plus short dropdown labels, hide item icons in the character-scoped table to save width, and height-match the Inventory and WW panels to the Current Build panel on wide screens

## [0.1.0-beta.10] - 2026-05-21

### Added
- **TTC price tooltips for Collections pieces** - individual stickerbook pieces now fetch local Tamriel Trade Centre price data on hover, showing lowest/average/highest prices, listing counts, TTC table timestamp, ESO Armory fetch time, and TTC attribution while preserving click-through search links

### Fixed
- **TTC tooltip error visibility** - failed `/api/ttc_price` requests now display the HTTP/error status in the tooltip instead of leaving the price area blank

## [0.1.0-beta.9] - 2026-05-21

### Fixed
- **Theme consistency - Collections progress bars** - stickerbook category nav bars, summary total bar, per-category grid bars, set card progress bars (all 3 card views: search, direct, subcategorized), and the stickerbook set tooltip bar all now use `var(--t-progress)` via inline style instead of `bg-eso-gold` Tailwind classes; complete vs incomplete sets distinguished by `opacity:1` vs `opacity:0.5`; matches the achievements tab's existing pattern

## [0.1.0-beta.8] - 2026-05-21

### Added
- **Character detail inventory panel** - character drill-down pages now include a character-scoped inventory panel alongside Current Build and WW Saved Builds, with search, quality/type/location/trait filters, Transmuted and Crafted toggles, Group by Set, sorting, tooltips, and set links

### Changed
- Character detail inventory filters are more compact: search now sits on its own row, dropdown labels are shortened, quality/Transmuted/Crafted live in a single dropdown, item icons are hidden in the character-scoped table, and Group by Set remains a visible toggle; the inventory and WW build panels are height-matched on wide screens with internal scrolling

### Fixed
- **Mythic set tooltip** - `_fetch_set_bonuses` now stops after the first (1-piece) bonus instead of continuing into related sets listed lower on the eso-sets.com page; previously all 4–5 bonus lines from an adjacent regular set were shown
- **Set bonus tooltip for mythic items** - `fetchSetBonus` and the tooltip template no longer require a non-zero `set_id`; when `set_id=0` the name slug is used as the cache key so the fetch fires and the bonuses section renders correctly
- **Server-side set bonus cache collision** - `_set_bonus_cache` now keys by `slug` instead of `0` when `set_id=0`, preventing all mythic items from sharing one cache slot

## [0.1.0-beta.7] - 2026-05-21

### Added
- **Dark theme** - GitHub-dark-inspired palette: near-black navy background, blue accent (`#58a6ff`), cyan progress bars
- **Light theme** - warm parchment palette: cream background, white cards, darkened amber accent readable on light backgrounds
- **Synthwave theme** - deep purple background (`#0d001a`), electric violet accent (`#bf5fff`), neon cyan progress bars

### Changed
- Theme dropdown button always displays "Theme" rather than the active theme name
- "ESO Classic" theme renamed to "Gold"; any saved `eso` value in localStorage migrated automatically
- Dropdown emoji removed; theme list order: Gold → Light → Dark → Synthwave → Outrun

## [0.1.0-beta.6] - 2026-05-21

### Added
- **Color themes** - swappable UI color palettes with a "Theme" dropdown in the header; selection persists to `localStorage`
  - **Gold** - the original amber/gold-on-dark palette (default, formerly "ESO Classic")
  - **Outrun** - deep navy background, hot-pink primary accent, cyan progress bars
- **Theme architecture** - all UI chrome colors converted to CSS custom properties (`--t-*`); theme-specific overrides injected as a `<style>` block at runtime so Tailwind CDN class names respond correctly; FOUC prevented by a pre-Alpine inline script

## [0.1.0-beta.5] - 2026-05-20

### Added
- **Multiselect inventory filters** - Type, Location, Character, and Trait dropdowns now accept multiple selections simultaneously; active selections highlight gold, clear individually or via the Clear button
- **Transmuted filter button** - dedicated toggle button on the filter bar (removed from the Trait dropdown); filters to items with bit 11 set in the item link flags field
- **Crafted filter button** - dedicated toggle button alongside Transmuted; filters to items where `is_crafted` is true
- **Group by Set toggle** - button that switches the inventory table into a grouped view with set-name headers and per-group item counts; items not belonging to a set appear last
- **Gear icons for all slot/weight combinations** - Breton-style webp artwork added for heavy, medium, and light armor (7 slots each), weapons (10 types), and jewelry (neck/ring); stored in `assets/gear/`

### Changed
- Inventory filter bar split into two rows: search + dropdowns on row 1; quality pills + toggle buttons (Transmuted, Crafted, Group by Set, Clear) on row 2
- Trait dropdown no longer contains a "Transmuted" entry - use the dedicated Transmuted toggle button instead
- Group by Set is now a button (was a checkbox label)
- Dropdown options rendered as highlighted `<div>` rows (no checkbox icons) - selected items shown with gold background tint

## [0.1.0-beta.4] - 2026-05-20

### Added
- **Armor weight and weapon type tags** in item tooltip - iasync now supplies `armorType` (Light/Medium/Heavy) and `weaponType` (Sword, Bow, etc.) directly; both appear as badge tags alongside trait/style/enchant
- **Gear icons** replace generic interface icons for all items - inventory list, character equipment panels, and character drilldown all use slot-specific Breton-style webp artwork from `assets/gear/`
  - Armor: correct slot piece per weight class (e.g. heavy helm for head slot, light shirt for chest)
  - Weapons: specific icon per type (dagger, 1h/2h sword/axe/hammer, bow, staff, shield)
  - Jewelry: neck vs. ring distinguished by slot
- **Name-based weapon icon fallback** - when `weaponType` is null or stale, item name keywords resolve the correct icon so old/unscanned characters still show meaningful icons

### Changed
- `item_db.py` removed - name-based weapon type heuristics replaced by reading `weaponType`/`armorType` directly from iasync item data
- Shield icon fix: shields have `filter_type = 2` (Armor) but carry `weaponType = "Shield"`; icon logic now checks `weapon_type` before the armor-weight lookup
- Stale iasync slot data guard: if `weaponType` claims a staff type but item name disagrees, the type is discarded and name-based detection runs instead

## [0.1.0-beta.3] - 2026-05-19

### Added
- **Achievements tab** - replaces Locations tab; account-wide achievement summary with category/subcategory drill-down, per-character filtering, progress bars for incomplete criteria, and a recent completions panel
- **`/api/achievements` endpoint** - parses `iasync_data.achievements` into category summaries, per-character item lists, and a top-10 recent completions list
- **Achievement tooltips** - hover over recent achievement icons to see name, description, points, completion date, and criteria progress
- **Loguru logging** - replaces `print()` throughout `server.py`; two sinks: colored console (INFO+) and rotating file `logs/armory.log` (DEBUG+, 10 MB max, 5 files, gzip compression)
- **HTTP request middleware** - logs method, path, status code, and elapsed ms for every non-static request
- **SSE connection logging** - logs client IP on connect and disconnect

### Fixed
- **Lua string escape sequences** - `lua_parser.py` `_parse_string` now correctly handles `\"`, `\n`, `\t`, `\r`, and `\\` escape sequences instead of stopping at the first backslash
- **Account name detection** - `process_iasync()` now checks `raw["accountName"]` key first before scanning for `@`-prefixed keys
- **File watcher silent errors** - bare `except: pass` blocks in `_file_watcher` now log a `WARNING` instead of swallowing exceptions

### Changed
- SSE reload event now also refreshes achievements data alongside inventory

## [0.1.0-beta.2] - 2026-05-19

### Changed
- **uv** replaces pip for dependency management - `pyproject.toml` + `uv.lock` added, `requirements.txt` removed; use `uv sync` (or `uv sync --active` if a virtualenv is already active)

### Fixed
- **Blank inventory locator column** for items stacked across multiple bag slots - `_add_slot` now merges same-character/same-bag location entries instead of appending duplicates, eliminating the Alpine.js `x-for` key collision that suppressed all location badges

## [0.1.0-beta.1] - 2026-05-19

### Added
- **iasync addon** - companion ESO addon that exports data IIfA doesn't persist:
  - Ability names (`GetAbilityName`) and Champion Point star names (`GetChampionSkillName`) for WizardsWardrobe builds
  - Bank currency (gold, AP, Telvar Stones, Writ Vouchers) via `CURRENCY_LOCATION_BANK`
  - Active character's live currency via `CURRENCY_LOCATION_CHARACTER` (overrides stale IIfA asset on load)
  - Falls back to previously saved bank values if bank API returns nil (e.g. not at bank)

- **WizardsWardrobe builds** - new builds view accessible by clicking a character card:
  - Gear list with item names, quality colors, and tooltip on hover
  - Skills section: primary and backup bars, slots 3–7 as ability chips, slot 8 (ultimate) highlighted in gold
  - Champion Points section: three-column grid with tree color coding (Warfare green / Fitness blue / Craft orange)
  - Food buff display

- **Character detail view** - clicking a character now navigates into a detail page with paper-doll on the left and WW builds on the right, replacing the former separate Builds tab

- **Currency totals in header** - gold, Alliance Points, Telvar Stones, and Writ Vouchers summed across all characters + bank; AP and TV hidden when zero

- **Telvar Stones** - added `tv` field to character assets; displayed on character cards and in header

- **Bank currency** - `data.bank` in API response aggregates currency from IIfA asset entries not mapped to a known character (likely account bank entries)

- **`/api/builds` endpoint** - returns WW builds, iasync ability/CP name maps, bank currency, and active character live currency

- **`parse_lua_variable()`** - generic Lua SavedVariable parser used for iasync_DATA

- **`parse_ww_data()`** - parser for WizardsWardrobeSV

- **`process_builds()`** - transforms raw WW data into flat build list; decodes item links for trait/style/enchant info per gear piece

- **Platform-aware path detection** - `_eso_sv_path()` auto-detects SavedVariables paths on Windows and WSL2

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
- Bank currency `GetCurrencyAmount(..., CURRENCY_LOCATION_BANK)` returns `nil` outside bank context - guarded with `or prevValue` fallback to preserve last known value across sessions
