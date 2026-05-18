# ESO Armory

![Version](https://img.shields.io/badge/version-0.1.0--beta.2-orange)
![Status](https://img.shields.io/badge/status-beta-yellow)

> **Beta:** This is early software. Expect rough edges and breaking changes between releases.

A local web app that reads your Elder Scrolls Online SavedVariables and presents your inventory, equipped gear, and WizardsWardrobe builds in a browser — inspired by the old WoW Armory.

## Features

- **Characters tab** — all characters at a glance with equipped gear paper-doll; click any character to see their WizardsWardrobe builds
- **Builds** — gear, skills (primary + backup bars), Champion Points, and food for each WW setup
- **Inventory tab** — full cross-character inventory with search, quality/type/trait/location filters, and sortable columns
- **Locations tab** — browse by bank, craft bag, house chests, and per-character inventory
- **Currency totals** — gold, AP, Telvar Stones, and Writ Vouchers across all characters + bank in the header
- **Live reload** — watches SavedVariables files and updates the browser automatically via SSE

## Requirements

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Elder Scrolls Online with the following addons installed:
  - [Inventory Insight from Scratch (IIfA)](https://www.esoui.com/downloads/info2486-InventoryInsightfromScratch.html)
  - [WizardsWardrobe](https://www.esoui.com/downloads/info3432-WizardsWardrobe.html)
  - **iasync** — included in this repo (see setup below)

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

iasync is a small companion addon that exports in-game data (ability names, Champion Point names, and bank currency) that IIfA doesn't persist to disk.

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
  "port": 5000,
  "server": "NA",
  "poll_interval_seconds": 5
}
```

`server` should be `"NA"` or `"EU"`.

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

## Project Structure

```
server.py              # FastAPI app + file watcher
lua_parser.py          # Recursive-descent Lua parser
data_processor.py      # IIfA + WW data → JSON model
item_link_decoder.py   # ESO item link decoder (trait/style/enchant)
item_db.py             # Name-based item enrichment
static/index.html      # Single-file frontend (Alpine.js + Tailwind CDN)
iasync/                # Companion ESO addon (symlink to AddOns folder)
config.json            # Auto-generated on first run
```

## Notes

- SavedVariables are only written to disk on `/reloadui` or character logout. The web app shows whatever was last flushed.
- Bank currency (gold, AP, Telvar, Writ Vouchers) is not saved by IIfA — iasync captures it separately.
- Ability and CP names in build cards require iasync to have run at least once in-game.
