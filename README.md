# ESO Armory

![ESO Armory header](header.svg)

![Version](https://img.shields.io/badge/version-0.1.0--beta.24-orange)
![Status](https://img.shields.io/badge/status-beta-yellow)

> **Beta:** This is early software. Expect rough edges and breaking changes between releases.

A local web app that reads your Elder Scrolls Online SavedVariables and presents your inventory, equipped gear, and WizardsWardrobe builds in a browser — inspired by the old WoW Armory.

## Features

- **Characters tab** — all characters at a glance with equipped gear paper-doll using slot-specific gear icons; click any character to see current build details, character-scoped inventory, and WizardsWardrobe builds
- **Builds** — gear, skills (primary + backup bars), Champion Points, and food for each WW setup; ability icons are discovered from PNG and WebP assets, including scribing skills such as Chilling Throw and Shocking Contingency
- **Inventory tab** — full cross-character inventory with search, multiselect quality/type/trait/location/character filters, Transmuted and Crafted toggle buttons, Group by Set view, and sortable columns; items show weapon-type and armor-weight tags and slot-specific gear icons
- **Achievements tab** — account-wide achievement summary with category/subcategory drill-down, a character selector that merges account-wide and character-specific completions, progress bars, recent completions, and completion attribution
- **Collections tab** — stickerbook set drill-down with TTC links for individual pieces; if Tamriel Trade Centre is installed locally, piece hovers show TTC price data with attribution and timestamps
- **Currency totals** — gold, AP, Telvar Stones, and Writ Vouchers across all characters + bank in the header
- **Color themes** — five palettes (Gold, Light, Dark, Synthwave, Outrun) switchable via a "Theme" dropdown in the header; selection persists across sessions
- **Live reload** — watches SavedVariables files and updates the browser automatically via SSE
- **File upload / remote use** — upload `iasync.lua`, `WizardsWardrobe.lua`, and optional Tamriel Trade Centre tables directly via the browser instead of relying on local file paths; hosted users can seed TTC pricing manually even without a live watcher
- **Workspace sharing** — create a pairing code or share link from the header so another browser or device can join the same uploaded workspace later; private sessions remain the default
- **Shared workspace persistence** — pairing codes are backed by a small server-side registry so the same uploaded data can be reopened on another browser later without re-uploading
- **Folder watcher** (Chrome/Edge) — select your ESO `live` folder once and the app polls for changes every 5 s, re-uploading `SavedVariables/` and Tamriel Trade Centre tables from `AddOns/TamrielTradeCentre/` automatically; directory handle persists across sessions via IndexedDB
- **Refresh button** — manually check for updated data at any time; toasts "Data updated ✓" or "No updates"
- **Session isolation** — each browser gets a UUID stored in `localStorage`; multiple users on the same hosted instance see only their own uploaded data by default, but a browser can opt into a shared workspace with a pairing code; private sessions still expire after 2 hours of inactivity
- **Static serving hardening** — the app shell is explicitly served as `text/html` with `nosniff` headers, and upload failures from proxies/CDNs show actionable HTTP/content messages instead of raw JSON parser errors

## Requirements

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Elder Scrolls Online with the following addons installed:
  - [Inventory Insight from Scratch (IIfA)](https://www.esoui.com/downloads/info2486-InventoryInsightfromScratch.html)
  - [WizardsWardrobe](https://www.esoui.com/downloads/info3432-WizardsWardrobe.html)
  - **iasync** — included in this repo (see setup below)
  - Optional: [Tamriel Trade Centre](https://www.tamrieltradecentre.com/) for Collections tab piece-price tooltips

## Setup

### 1. Install Python dependencies

```bash
uv sync
```

If you have an existing virtualenv already active for this project (e.g. via virtualenvwrapper), use `--active` to install into it instead:

```bash
uv sync --active
```

### 2. Install the iasync addon

iasync is a companion addon that exports in-game data that IIfA doesn't persist to disk: ability names, Champion Point names, bank currency, weapon types, armor weights, achievement progress, completion attribution, and stickerbook collection state.

The `iasync/` directory in this repo is symlinked to your ESO AddOns folder. If the symlink is missing or broken:

```bash
# WSL2 / Linux
ln -s "/mnt/c/Users/<you>/Documents/Elder Scrolls Online/live/AddOns/iasync" iasync
```

Or on Windows, copy the `iasync/` folder directly into your AddOns directory.

### 3. Configure paths (optional)

On first run a `config.json` is created automatically with paths detected for your platform. Edit it if needed:

```json
{
  "lua_path":        "path/to/IIfA.lua",
  "ww_lua_path":     "path/to/WizardsWardrobe.lua",
  "iasync_lua_path": "path/to/iasync.lua",
  "ttc_addon_path":  "path/to/AddOns/TamrielTradeCentre",
  "ttc_lookup_table_path": "path/to/AddOns/TamrielTradeCentre/ItemLookUpTable_EN.lua",
  "ttc_price_table_path": "",
  "port": 5000,
  "server": "NA",
  "poll_interval_seconds": 5
}
```

`server` should be `"NA"` or `"EU"`. Leave `ttc_price_table_path` empty to use `PriceTableNA.lua` or `PriceTableEU.lua` automatically from `ttc_addon_path`.

### 4. First run in-game

Load into a character and run `/reloadui`. This flushes SavedVariables to disk and lets iasync export bank currency and ability/CP names.

For accurate currency totals across all characters, log into each character once and `/reloadui`.

### 5. Start the server

```bash
uv run server.py
# or if using an active virtualenv (uv sync --active):
python server.py
```

Then open [http://localhost:5000](http://localhost:5000).

## Running

```bash
uv run server.py
# or on a custom port:
uv run server.py --port 8080
# if using an active virtualenv (uv sync --active), run directly:
python server.py --port 8080
```

The server polls your SavedVariables files every 5 seconds (configurable) and pushes a reload event to the browser when anything changes.

## Testing

Install dev dependencies:

```bash
uv sync --dev
```

Common test commands:

```bash
make test-fast          # unit + API tests
make test               # alias for test-fast
make playwright-install # install Chromium + Firefox for Playwright
make playwright-install-deps # install Linux system libraries for browsers
make test-ui            # browser tests in Chromium + Firefox
make test-ui-chromium   # browser tests in Chromium only
make test-ui-firefox    # browser tests in Firefox only
make test-all           # fast tests + browser tests
make test-mutation-core # mutmut for parser/decoder/data processing
make test-mutation      # mutmut for all backend modules
```

Use `make test-fast` before small backend changes, `make test-ui` for frontend/upload/share changes, and `make test-all` before release-style validation. Mutation tests are intentionally manual because they are slower than the normal suite.

On Linux, Playwright may also need system browser libraries. If Chromium or Firefox fails to launch with a missing shared library, run `make playwright-install-deps` in a shell with sudo access.

The UI suite includes first-load regressions that assert the browser renders the upload/setup screen instead of dumping HTML, Lua, or inline Alpine source text. It also exercises non-JSON upload responses so CDN/proxy errors are visible to users.

The committed test fixtures in `tests/fixtures/` are sanitized and deterministic. To refresh local generated samples from your ESO live folder, run:

```bash
uv run scripts/generate_test_fixtures.py
```

Generated live-derived files are for review only; committed tests should continue using sanitized fixtures and must not depend on `/mnt/c/...` paths.

## Project Structure

```
server.py              # FastAPI app + file watcher + TTC price lookups
lua_parser.py          # Recursive-descent Lua parser
data_processor.py      # iasync + WW data → JSON model
item_link_decoder.py   # ESO item link decoder (trait/style/enchant)
static/index.html      # Single-file frontend (Alpine.js + Tailwind CDN)
header.svg             # Project header artwork for README/release surfaces
assets/gear/           # Slot-specific gear icons (weapon/armor/jewelry)
assets/abilities/      # Skill icons used by current builds and WW saved builds
iasync/                # Companion ESO addon (symlink to AddOns folder)
config.json            # Auto-generated on first run
```

## Notes

- SavedVariables are only written to disk on `/reloadui` or character logout. The web app shows whatever was last flushed.
- Bank currency (gold, AP, Telvar, Writ Vouchers) is not saved by IIfA — iasync captures it separately.
- Ability and CP names in build cards require iasync to have run at least once in-game.
- Collections piece-price tooltips use Tamriel Trade Centre `ItemLookUpTable_EN.lua` and `PriceTableNA.lua`/`PriceTableEU.lua` files from the selected live folder when available, or configured local TTC paths on self-hosted installs; hosted users can also upload those TTC files manually. Restart the server after changing TTC config paths or updating routes. If tooltip prices are missing, check `/api/ttc_price` and server logs first.
