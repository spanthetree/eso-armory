<div align="center">
  <img src="header.svg" alt="ESO Armory" width="860"/>

**A web armory for your Elder Scrolls Online account.**

[![Tests](https://github.com/spanthetree/eso-armory/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/spanthetree/eso-armory/actions/workflows/tests.yml)
![Status](https://img.shields.io/badge/status-beta-yellow)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/license-PolyForm%20Noncommercial-lightgrey)](LICENSE)

[Getting started](#getting-started) ·
[Configuration](#configuration) ·
[Development](#development) ·
[Architecture](docs/architecture.md) ·
[Changelog](CHANGELOG.md) ·
[Contributing](CONTRIBUTING.md)

</div>

ESO has no way to see your account outside the game. Gear is spread across characters, banks, the craft bag and house chests, and builds live in addon menus. ESO Armory reads the data the [iasync](https://github.com/spanthetree/iasync) and [WizardsWardrobe](https://www.esoui.com/downloads/info3432-WizardsWardrobe.html) addons save, and shows every character's gear, builds, inventory, achievements and collections in one browser page.

## Features

- **Skill icons.** iasync 1.15.0 exports ability names and exact icon paths for equipped bars and saved Wizards Wardrobe builds. Armory uses those paths through its cached UESP image route. Older exports retain name-based icon lookup, with successful fallback names saved across server restarts. Backgrounds and game icons use one-year immutable browser caching.
- **Characters.** Each character's equipped gear on an in-game style "Equipped" panel with each item's own icon, plus level, title, skill bars, Champion Points, attributes, max Health/Magicka/Stamina, Mundus Stone, Alliance War rank, riding and guilds, with tooltips for sets, the mundus and champion stars. Switch a character between Sheet, Crafting (trait research, motifs, recipes), Scribing, Wardrobe (saved WizardsWardrobe setups), Bags, Compare and SuperStar views.
- **Inventory.** Every item across characters, bank, ESO Plus bank, craft bag, house chests and guild banks. Search and filter by quality, type, trait, location and character, or group by set. Tamriel Trade Centre values per item with totals by type and location, a duplicate-gear finder, and filter chips you can save.
- **Build compare.** Export a build as a short code, import someone else's, and compare gear side by side. Missing pieces are listed with their source (dungeon, trial, arena) and an estimated Tamriel Trade Centre cost.
- **SuperStar import.** Upload a screenshot from the SuperStar addon and compare that build against your gear, slot by slot. Needs an OpenAI (default) or Anthropic API key.
- **Two looks.** *Classic* (the default) redraws the app in the game's own keyboard UI art: the main menu icon bar, window backdrops, buttons, dropdowns, list rows and progress bars, over a darkened loading screen. Equipment panels keep compact top and bottom fades so the backdrop covers every gear slot. *Simple* is the plain web look. Switch with the **UI** dropdown in the top bar; the choice is remembered in your browser.
- **Demo.** "Open the demo account" on the landing page shows a full sample armory before you upload anything (read-only).
- **Activities.** The Tamriel Tome reward track, weekly and seasonal Endeavors and Golden Pursuits, plus every account currency (needs iasync 1.11.0).
- **Journal.** Achievements laid out like the in-game journal (category tree, progress bars, recent unlocks, a timeline, criteria progress per character, search) and Antiquities (leads, zones, recovered counts and Codex progress).
- **Collections.** The in-game Collections book with its tabs: Collectibles, Housing, Outfit Styles, Set Items and Tales of Tribute. Each has the game's category tree, a keyword filter and a locked/unlocked filter, with unlocked counts per category (collectibles need iasync 1.9.0). Set Items shows every set as a grid of its pieces, filtered by apparel and weapon type, completion and locked pieces, with where each piece drops and its Tamriel Trade Centre price.
- **Workspaces.** Each ESO account's data is stored once and reopens without re-uploading. Set a password to open it from another device with your ESO account name. Share a read-only view with a pairing code, or load an alt account beside your own.
- **Auto-sync.** In Chrome and Edge, point the app at your ESO `live` folder (or its `SavedVariables` folder) once and it uploads changed files as you play (checked every 10 seconds; **Refresh** forces a sync).
- **Looks like the game.** Dark panels with gold rules, the game's own icons, animated loading and transitions, and a layout that fits one screen.

## How it works

1. iasync and WizardsWardrobe write `SavedVariables` files when you log out or `/reloadui`.
2. You upload those files in the browser, or the folder watcher uploads them for you.
3. The server parses the Lua, stores the processed result per ESO account in SQLite, and discards the raw file.
4. Open browsers refresh automatically when new data arrives.

## Getting started

### Requirements

- Docker with Compose, or Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Elder Scrolls Online with these addons:
  - [iasync](https://github.com/spanthetree/iasync) (required)
  - [WizardsWardrobe](https://www.esoui.com/downloads/info3432-WizardsWardrobe.html) (for saved builds)
  - [Tamriel Trade Centre](https://www.tamrieltradecentre.com/) (optional, for prices)

### Run with Docker

```bash
curl -O https://raw.githubusercontent.com/spanthetree/eso-armory/master/compose.yaml
docker compose up -d
```

This pulls `ghcr.io/spanthetree/eso-armory` and serves on port 5000. The first start downloads the game icons from UESP (about 2 minutes).

| Task | Command | From a checkout |
|------|---------|-----------------|
| Start | `docker compose up -d` | `make up` |
| Stop | `docker compose down` | `make down` |
| Upgrade to the latest release | `docker compose pull && docker compose up -d` | `make upgrade` |
| Run your local code | `docker compose up -d --build` | |

Data lives in two folders next to `compose.yaml`, the same ones a source install uses: `uploads/` (accounts, TTC tables, `config.json` with its encryption key) and `assets/` (icons). Stopping, upgrading or removing the container keeps them.

- **Existing source install:** run compose in that checkout, or set `ESO_ARMORY_DIR=/path/to/checkout`. On first start the container uses its database, icons and `config.json` (whose `db_secret` decrypts the database). The container runs as the owner of `uploads/`, so the files stay yours.
- **Upgrading from an earlier release:** older compose files kept data in a Docker volume. Download the new `compose.yaml` into the same folder; the first start copies the volume into `uploads/` when `uploads/` has no database yet. Icons are downloaded again.
- **Nothing there yet:** the container creates a new database and config.
- `ESO_ARMORY_PORT=8080` changes the port; `ESO_ARMORY_VERSION=0.2.0-beta.4` pins a release. Both can go in a `.env` file next to `compose.yaml`.
- Put `ANTHROPIC_API_KEY=...` in `.env` to enable SuperStar import.
- To change [configuration](#configuration), edit `uploads/config.json`, then `docker compose restart`.

#### Hosting on a cloud server

UESP's Cloudflare refuses many cloud hosts (AWS, Lightsail and others) with HTTP 403. The server then fetches icons through WordPress.com's public image proxy (`i0.wp.com`) instead, and saves them in `assets/` like any other icon. The proxy re-encodes some PNGs with a 256-colour palette, which is barely visible. UESP is always tried first.

### Run from source

Also needs [Node.js](https://nodejs.org/) 18 or newer to build the frontend.

```bash
uv sync
make ui-build                 # install frontend packages and build the app into static/dist
make assets                   # download game icons from UESP (about 2 minutes)
uv run server.py              # port 5000
uv run server.py --port 8080  # or another port
```

Open the server's address in a browser. The setup screen walks through the upload:

1. Log in to each character in ESO so iasync captures it (use the latest iasync: item icons, crafting, scribing and champion star names need 1.11.0 to 1.14.0). Open your bank once to capture bank contents. With iasync 1.15.0, scan each character to collect saved-build skill names and icons. After updating the addon, reload the UI, wait for the scan, then reload again to write the new metadata.
2. Upload `iasync.lua` and `WizardsWardrobe.lua` from `Documents\Elder Scrolls Online\live\SavedVariables\`.

## Configuration

`config.json` is created on first run:

```json
{
  "ttc_addon_path": "path/to/AddOns/TamrielTradeCentre",
  "ttc_lookup_table_path": "path/to/AddOns/TamrielTradeCentre/ItemLookUpTable_EN.lua",
  "ttc_price_table_path": "",
  "database_url": "sqlite:///uploads/armory.db",
  "admin_accounts": [],
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
| `admin_accounts` | ESO account names (e.g. `@name`) allowed to upload TTC files. An account only counts as admin after it sets a password. |

SuperStar import reads build screenshots with an AI service that can read images: OpenAI (default) or Anthropic. Each visitor can add their own key in the SuperStar view (stored encrypted for their browser session), with a link to create one. To provide a key for everyone, set `OPENAI_API_KEY` (or `openai_api_key` in `config.json`; `OPENAI_MODEL` / `openai_model` picks the model, default `gpt-4o`) or `ANTHROPIC_API_KEY` (or `anthropic_api_key`); OpenAI is used when both are set. Restart the server after changing the config.

The server speaks plain HTTP. Put it behind a reverse proxy such as Caddy or nginx for HTTPS.

## Development

```bash
uv sync --dev
make playwright-install  # once, for browser tests
make ui-dev              # frontend with hot reload on :5173; run the server on :5000 alongside
make test-fast           # Python unit + API tests
make frontend-test       # JavaScript unit tests
make test-ui             # builds the frontend, then Playwright in Chromium + Firefox
make test-all            # all of the above
```

The frontend is [Svelte 5](https://svelte.dev/) built with Vite, in `frontend/`. `make ui-build` writes it to `static/dist/`, which the server serves at `/`. Game data colours (item quality, resources) are fixed; everything else comes from the tokens in `frontend/src/lib/styles/tokens.css`.

How the server, storage and API fit together: [docs/architecture.md](docs/architecture.md).

Test fixtures in `tests/fixtures/` are sanitized. Do not commit live account data.

| Path | Purpose |
|---|---|
| `server.py` | FastAPI app, API, uploads, price lookups |
| `db.py` | SQLite workspace storage |
| `lua_parser.py` | SavedVariables Lua parser |
| `data_processor.py` | iasync and WizardsWardrobe data to API payloads |
| `item_link_decoder.py` | ESO item link decoder |
| `frontend/` | Svelte 5 frontend: `src/App.svelte` shell, `src/lib/` tabs, components and logic (unit-tested `*.test.js`) |
| `scripts/make_demo.py` | Rebuilds `demo/demo.json.gz`, the demo account, from a real `iasync.lua` (and `WizardsWardrobe.lua`), anonymised |
| `scripts/assets_manifest.json` | Game icon sources; `make assets` downloads them into `assets/` |
| `uesp.py` | Fetches UESP images, through a public image proxy when UESP refuses the host |

## Contributing

Bug reports, ideas and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), and report security issues privately as described in [SECURITY.md](SECURITY.md).

## License

ESO Armory is source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE): free to use, modify and share for any noncommercial purpose. Commercial use needs a separate license.

## Status

ESO Armory is in beta. Expect breaking changes between releases; the [changelog](CHANGELOG.md) lists them.

ESO Armory is not affiliated with, endorsed by or sponsored by ZeniMax Online Studios or Bethesda. The Elder Scrolls Online and its artwork are theirs. This repository contains no game artwork: `make assets` downloads icons from [UESP](https://en.uesp.net).
