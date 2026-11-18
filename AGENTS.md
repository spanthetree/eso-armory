# ESO Armory - Agent Notes

## Project Overview
Local web app that reads ESO SavedVariables and presents inventory, equipment, and builds in a web-based armory. FastAPI backend, Svelte 5 + Vite frontend in `frontend/` built into `static/dist/`. Designed for WSL2 on Windows where the ESO client runs natively.

## Stack
- **Backend**: Python / FastAPI + Uvicorn (`server.py`)
- **Frontend**: Svelte 5 (runes, plain JS with JSDoc, no TypeScript) + Vite 6 in `frontend/`. `make ui-build` builds it into `static/dist/` (gitignored); the server serves `static/dist/index.html` at `/`. Vite is pinned to 6 so it builds on Node 18; Docker/CI use Node 22. Fonts are bundled via `@fontsource` (no CDN).
- **Lua parser**: Custom recursive-descent in `lua_parser.py` (stdlib only, no lupa/lark)
- **Start**: `make ui-build` once (and after frontend changes), then `uv run server.py` → http://localhost:5000 (or `python server.py` if virtualenv active via `uv sync --active`)
- **Tests**: pytest unit/API, `node --test` frontend units (`frontend/src/lib/*.test.js`), Playwright UI (Chromium + Firefox)

## Approval Preference
Before making code or file changes, ask for explicit approval unless the user has already clearly requested implementation in the current turn. Read-only inspection and searches are fine without approval. Git actions are allowed - see Git Workflow.

## Key Files
| File | Purpose |
|------|---------|
| `server.py` | FastAPI app, file watcher, caches, SSE push, ability icon map, set bonus + skill info scrapers |
| `lua_parser.py` | `parse_lua_variable(path, varname)` |
| `data_processor.py` | `process_iasync()`, `process_iasync_builds()`, `process_iasync_achievements()`, `process_iasync_stickerbook()` (includes `process_iasync_collectibles()`), `process_ww_builds()` |
| `item_link_decoder.py` | Decodes ESO `\|H1:item:...\|h` links → trait/style/enchant fields |
| `config.json` | TTC addon paths, port, server region (`NA`/`EU`), database URL |
| `frontend/src/App.svelte` | App shell: top bar, hero, tabs, character sub-views, dialogs |
| `frontend/src/lib/store.svelte.js` | App state and API loaders (payloads are `$state.raw`), live updates (SSE), sharing, auth, compare/SuperStar calls |
| `frontend/src/lib/api.js` | Session id + share code (same localStorage keys as before), URL building, `readJson` error handling |
| `frontend/src/lib/{gear,items,achievements,collections,compare,route}.js` | Pure, unit-tested logic: icons/slots, item filters, achievement merge, collection grouping, build compare, URL hash routing |
| `frontend/src/lib/ui/` | Building blocks: Frame, Slot, Tabs, Segmented, MultiSelect, Modal, Progress, CountBar (in-game teal count bar), ResourceBar, tooltip host |
| `frontend/src/lib/{character,inventory,achievements,collections,shell,tips}/` | Views, tabs, dialogs and tooltip components |
| `frontend/src/lib/styles/tokens.css` | Design tokens (colours, fonts, motion) |
| `tests/fixtures/` | Sanitized deterministic Lua/TTC fixtures; do not commit live user data |

## Testing Commands
```bash
make test-fast          # unit + API tests with coverage
make test               # alias for test-fast
make frontend-test      # JS unit tests (node --test)
make test-ui            # builds the frontend, then Playwright in Chromium + Firefox
make test-all           # build + JS tests + fast tests + browser tests
make ui-dev             # Vite dev server on :5173 with hot reload (proxies /api, /events, /assets, /esoicons to :5000)
```
Use `make test-all` before release-style validation. The UI suite includes a first-load regression that fails if the browser renders raw Lua or source text instead of the setup UI.

## Architecture reference
Data formats, API endpoints, server caches, workspaces, TTC storage, admin accounts and the security model live in [docs/architecture.md](docs/architecture.md). Read it before changing the server or data processing, and keep it current in the same PR.

## Icon Normalization (Python + JS must match)
```python
# Python (server.py):
key = re.sub(r'[^a-z0-9]+', '_', icon.stem.lower()).strip('_')
# JS (frontend/src/lib/eso.js iconKey):
const key = name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')
```
Icons are ZeniMax artwork and are **not committed**: `assets/` is gitignored and filled by `make assets` (`scripts/download_assets.py`) from the URLs in `scripts/assets_manifest.json` (UESP `images.uesp.net` / `esoicons.uesp.net`; needs a browser-like User-Agent). To add an icon, add a `"path": "url"` entry to the manifest and run `make assets`. Never commit image files under `assets/`. A host UESP refuses (Cloudflare 403, common on cloud IPs) redirects browsers to UESP for missing `/assets/...` (manifest) and `/esoicons/...` icons and records them in `uploads/missing_assets.txt`; `scripts/sync_icons.py user@host` (run from a desktop) downloads those and rsyncs them into the server's `assets/`.

## Design System
Two looks, switched by the top-bar **UI** dropdown (`lib/uimode.svelte.js`, mirrored on `<html data-ui>`):
- **Classic** (default): the ESO keyboard UI. Game textures come from UESP via `make assets` (`assets/esoui/`, never committed); `lib/eso/tex.js` cuts them up (TextureCoords crops, 8-segment backdrop edge files) into CSS variables on `:root`. `lib/eso/eso.css` has the in-game building blocks (`.eso-*`), `lib/eso/classic.css` re-skins shared tokens/classes, and components add Classic rules as `:global(:root[data-ui='classic']) .x`. Achievements and Collections are redrawn on `EsoWindow`'s 995x800 stage in the game's own pixels, copied from the esoui XML templates (github.com/esoui/esoui). Colours come from iasync `uiColors` (`applyUiColors`) with approximations as fallback. The game font (Univers 57/67 Condensed) is used only if installed locally; Barlow Condensed is the fallback. Keep every Classic rule scoped so Simple stays unchanged.
- **Simple**: the "Obsidian" look below. `AchievementsSimple.svelte` / `CollectionsSimple.svelte` keep the Simple tabs.

"Obsidian" (Simple) look: near-black translucent panels (`Frame`) with gold rules, Cinzel (display) + Barlow Condensed (UI), white text. Tokens live in `frontend/src/lib/styles/tokens.css`; gold (`--accent`, `--accent-hi`) is for rules, frames and ornaments only. There are no themes or alliance tinting (both were removed on purpose).

**Quality/resource colours are NOT tokens to restyle** - they are game data (`--q-*`, `--res-*`, and `item.quality_color` from the server).

**Fit one screen:** character views and the Inventory/Achievements/Collections tabs are designed to fit a 1400x900 viewport without page scrolling; long lists scroll inside their panel. Check with a real account after layout changes.

**Game icons are 64px:** keep gear/skill icons at or below 64 CSS px so they stay sharp. Class/faction emblems are luminance masks (white-on-black icons) and the hero emblems run through an SVG sharpening filter.

## Restarting the Server
```bash
fuser -k 5000/tcp 2>/dev/null; sleep 1 && uv run server.py &
# If virtualenv active via uv sync --active:
fuser -k 5000/tcp 2>/dev/null; sleep 1 && python server.py &
```
Use `fuser -k 5000/tcp` (not `pkill`) - targets the port directly, works reliably in WSL2.

## Git Workflow
Agents may run git and `gh` commands (branch, commit, push, open PRs).
- Make every change on a new branch cut from a freshly pulled `master` (`git checkout master && git pull && git checkout -b <branch>`). Never commit to `master` directly.
- One PR per issue, with each phase as its own commit.
- Before running `gh pr create`, make a final commit on the branch that:
  1. Updates `README.md` if anything user-facing changed
  2. Adds a dated `## [x.y.z] - YYYY-MM-DD` section to `CHANGELOG.md`
  3. Bumps the version in `pyproject.toml` and runs `uv lock` so `uv.lock` matches
- Run `make test-all` before opening the PR.
- PRs target `master` on GitHub. The user merges.
- Merging a version bump releases it: `.github/workflows/release.yml` builds and pushes `ghcr.io/spanthetree/eso-armory`, tags `vX.Y.Z`, and creates a GitHub release from the CHANGELOG section. Never tag by hand.
- No force-push, history rewrite, or branch deletion without asking.

## Item Link Decoder (`item_link_decoder.py`)
`|H1:item:F0:F1:...:F20|h[name]|h` - key fields (0-indexed after `item:`):
`[0]`=item_id, `[3]`=enchant_id, `[6]`=trait_id, `[14]`=flags (bit8=stolen, bit11=transmuted), `[15]`=style_id, `[16]`=crafted, `[17]`=bound, `[19]`=sell_value

**20-field bug (deferred):** Some links have 20 fields; flags shift to `[13]`, `[16]` may be missing. Fix: check `len(raw)` and adjust offsets. Transmuted and reconstructed both set bit 11 - no bit-level distinction.

## Known Quirks / Gotchas
- **Tooltips**: one app-wide tooltip (`ui/tooltip.svelte.js` + `TooltipHost`). Elements opt in with `use:tooltip={{ component, props }}`; tooltip components live in `lib/tips/` and fetch their own data (set bonuses, skill info, TTC prices) on first view via `lookups.svelte.js`.
- **`/api/data` 503 behavior**: HTTP 503 means no data has been uploaded yet - `loadData` keeps it silent (value `null`, no error). Achievements/collections DO surface errors (the UI tests expect "User data not loaded" + the server message).
- **WW mythic key**: `gear` dict has `"mythic"` string key alongside integer slot keys - skip via `int(slot_raw)` in try/except.
- **Mythic `set_id=0`**: Use `set_id || _slugify(set_name)` as cache key everywhere (Python + JS). Server `_fetch_set_bonuses` breaks on second bonus line when `first_pieces==1` to avoid multi-set bleed.
- **`setKey(item)`** (`gear.js`): set-bonus cache key, `set_id` or the slug for mythics (`set_id=0`). Use it, not `set_id` directly.
- **Bank currency**: `GetCurrencyAmount(..., CURRENCY_LOCATION_BANK)` returns `nil` outside bank context - guard with `or prevValue` in Lua.
- **`weaponType` stale**: recorded per-slot at scan time; discard when it claims "Staff" but item name disagrees, then fall back to name-based detection.
- **Shields**: `filter_type 2` (Armor) with `weaponType="Shield"` and `armorType=nil` - check `weapon_type === 'Shield'` before armor-weight lookup.
- **Mundus icon key**: Strip "The " prefix (`mundusIcon` in `gear.js`).
- **No `{@html}`**: Svelte escapes text by default; don't introduce `{@html}` with user-supplied strings (ability names and imported builds come from uploaded files and share codes).
- **`GetEquipmentFilterTypeForItemSetCollectionSlot` is misnamed**: returns armor/weapon sub-type integers, not `ITEM_FILTER_TYPE_*`. Use piece names from `GetItemLinkName` instead.
- **Achievements mixed-persistence**: `achievementsIn()` (`achievements.js`) merges `account_items` with character-specific `items_by_char`, deduped by id (character copy wins). `extraSubcats()` surfaces achievements filed under a subcategory the category doesn't list (e.g. "Group Dungeons").
- **Duplicate keys**: Svelte `{#each}` keys must be unique or the render aborts (`each_key_duplicate`); `recent` achievements can repeat an id, so key by position there.
- **Unnamed abilities**: iasync only names abilities that were slotted when it scanned; `SkillBars` asks `/api/ability_names` (UESP) for the rest.
- **`/esoicons/<name>.png`**: achievement and other `/esoui/art/icons` textures are fetched from UESP on first use into `assets/esoicons/` (gitignored). `/esoicons/<folder>/<name>.png` does the same for `treeicons`, `collections` and `achievements` (category tree icons). Use `gameIcon(path)` (`achievements.js`) to turn a `.dds` path into either URL.
- **Set collection `filterType`** is `EQUIPMENT_FILTER_TYPE_*` (1 Light, 2 Medium, 3 Heavy, 4 Necklace, 5 Ring, 6 One-Handed, 7 Shield, 8 Two-Handed, 9 Destruction, 10 Restoration, 11 Bow), not the inventory `filter_type`.
- **No `structuredClone` on state**: it throws on Svelte `$state` proxies; use `$state.snapshot` or a JSON copy.
- **Collectibles ride in `/api/stickerbook`** (`collectibles`, about 4 MB for a full account, served gzipped by `_payload_response`). There is no gzip middleware on purpose: it would buffer the `/events` SSE stream. The Collections tab's book (`#/collections/<book>`, `BOOKS` in `collections.js`) picks Set Items or `CollectiblesBook` (one component, both looks).
- **Inventory values** come from one `POST /api/ttc_prices` per item list (`loadAvgPrices`); don't call `/api/ttc_price` per row.
