<div align="center">
  <img src="header.svg" alt="ESO Armory" width="860"/>

**A web armory for your Elder Scrolls Online account.**

[![Tests](https://github.com/spanthetree/eso-armory/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/spanthetree/eso-armory/actions/workflows/tests.yml)
![Status](https://img.shields.io/badge/status-beta-yellow)

[Getting started](#getting-started) ·
[Configuration](#configuration) ·
[Development](#development) ·
[Architecture](docs/architecture.md) ·
[Changelog](CHANGELOG.md)

</div>

ESO has no way to see your account outside the game. Gear is spread across characters, banks, the craft bag and house chests, and builds live in addon menus. ESO Armory reads the data the [iasync](https://github.com/spanthetree/iasync) and [WizardsWardrobe](https://www.esoui.com/downloads/info3432-WizardsWardrobe.html) addons save, and shows every character's gear, builds, inventory, achievements and set collections in one browser page.

## Features

- **Characters.** Equipped gear for every character, with the current skill bars, Champion Points, attributes and Mundus Stone. Saved WizardsWardrobe setups appear beside each character.
- **Inventory.** Every item across characters, bank, ESO Plus bank, craft bag, house chests and guild banks. Search and filter by quality, type, trait, location and character, or group by set.
- **Build compare.** Export a build as a short code, import someone else's, and compare gear side by side. Missing pieces are listed with their source (dungeon, trial, arena) and an estimated Tamriel Trade Centre cost.
- **SuperStar import.** Upload a screenshot from the SuperStar addon and compare that build against your gear, slot by slot. Needs an Anthropic API key.
- **Achievements.** Account-wide progress by category, with per-character completions and recent unlocks.
- **Collections.** Set collection progress by category, with Tamriel Trade Centre prices on each piece.
- **Workspaces.** Each ESO account's data is stored once and reopens without re-uploading. Share a workspace with a pairing code, or load a second account beside your own.
- **Auto-sync.** In Chrome and Edge, point the app at your ESO folder once and it uploads changed files as you play.
- **Themes.** Five colour palettes.

## How it works

1. iasync and WizardsWardrobe write `SavedVariables` files when you log out or `/reloadui`.
2. You upload those files in the browser, or the folder watcher uploads them for you.
3. The server parses the Lua, stores the processed result per ESO account in SQLite, and discards the raw file.
4. Open browsers refresh automatically when new data arrives.

## Getting started

### Requirements

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Elder Scrolls Online with these addons:
  - [iasync](https://github.com/spanthetree/iasync) (required)
  - [WizardsWardrobe](https://www.esoui.com/downloads/info3432-WizardsWardrobe.html) (for saved builds)
  - [Tamriel Trade Centre](https://www.tamrieltradecentre.com/) (optional, for prices)

### Run

```bash
uv sync
uv run server.py              # port 5000
uv run server.py --port 8080  # or another port
```

Open the server's address in a browser. The setup screen walks through the upload:

1. Log in to each character in ESO so iasync captures it. Open your bank once to capture bank contents.
2. Upload `iasync.lua` and `WizardsWardrobe.lua` from `Documents\Elder Scrolls Online\live\SavedVariables\`.

## Configuration

`config.json` is created on first run:

```json
{
  "ttc_addon_path": "path/to/AddOns/TamrielTradeCentre",
  "ttc_lookup_table_path": "path/to/AddOns/TamrielTradeCentre/ItemLookUpTable_EN.lua",
  "ttc_price_table_path": "",
  "database_url": "sqlite:///uploads/armory.db",
  "port": 5000,
  "server": "NA"
}
```

| Key | Meaning |
|---|---|
| `server` | Price region: `NA` or `EU` |
| `ttc_*` | Tamriel Trade Centre files for price lookups. Leave `ttc_price_table_path` empty to pick the table for `server`. Admin accounts can upload these files instead. |
| `database_url` | Where workspaces are stored |
| `port` | HTTP port |

Set `ANTHROPIC_API_KEY` (or `anthropic_api_key` in `config.json`) to enable SuperStar import. Restart the server after changing the config.

The server speaks plain HTTP. Put it behind a reverse proxy such as Caddy or nginx for HTTPS.

## Development

```bash
uv sync --dev
make playwright-install  # once, for browser tests
make test-fast           # unit + API tests
make test-ui             # Playwright, Chromium + Firefox
make test-all            # both
```

How the server, storage and API fit together: [docs/architecture.md](docs/architecture.md).

Test fixtures in `tests/fixtures/` are sanitized. Do not commit live account data.

| Path | Purpose |
|---|---|
| `server.py` | FastAPI app, API, uploads, price lookups |
| `db.py` | SQLite workspace storage |
| `lua_parser.py` | SavedVariables Lua parser |
| `data_processor.py` | iasync and WizardsWardrobe data to API payloads |
| `item_link_decoder.py` | ESO item link decoder |
| `static/index.html` | Single-file frontend (Alpine.js + Tailwind) |
| `assets/` | Gear and ability icons |

## Status

ESO Armory is in beta. Expect breaking changes between releases; the [changelog](CHANGELOG.md) lists them.

ESO Armory is not affiliated with ZeniMax Online Studios or Bethesda.
