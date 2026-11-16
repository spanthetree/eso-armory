# ESO Armory - Agent Notes

## Project Overview
Local web app that reads ESO SavedVariables and presents inventory, equipment, and builds in a WoW-Armory-style browser. FastAPI backend, single-file Alpine.js + Tailwind CDN frontend (no build step). Designed for WSL2 on Windows where the ESO client runs natively.

## Stack
- **Backend**: Python / FastAPI + Uvicorn (`server.py`)
- **Frontend**: `static/index.html` - vendored Alpine.js 3.x from `static/vendor/alpine.min.js`, Tailwind CDN
- **Lua parser**: Custom recursive-descent in `lua_parser.py` (stdlib only, no lupa/lark)
- **Start**: `uv run server.py` → http://localhost:5000 (or `python server.py` if virtualenv active via `uv sync --active`)
- **Tests**: pytest unit/API, Playwright UI (Chromium + Firefox)

## Approval Preference
Before making code or file changes, ask for explicit approval unless the user has already clearly requested implementation in the current turn. Read-only inspection and searches are fine without approval. Git actions are allowed - see Git Workflow.

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
```
Use `make test-all` before release-style validation. The UI suite includes a first-load regression that fails if the browser renders raw Lua or Alpine source text instead of the setup UI.

## Architecture reference
Data formats, API endpoints, server caches, workspaces, TTC storage, admin accounts and the security model live in [docs/architecture.md](docs/architecture.md). Read it before changing the server or data processing, and keep it current in the same PR.

## Icon Normalization (Python + JS must match)
```python
# Python (server.py):
key = re.sub(r'[^a-z0-9]+', '_', icon.stem.lower()).strip('_')
# JS (index.html):
const key = name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')
```
Icons are ZeniMax artwork and are **not committed**: `assets/` is gitignored and filled by `make assets` (`scripts/download_assets.py`) from the URLs in `scripts/assets_manifest.json` (UESP `images.uesp.net` / `esoicons.uesp.net`; needs a browser-like User-Agent). To add an icon, add a `"path": "url"` entry to the manifest and run `make assets`. Never commit image files under `assets/`.

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
