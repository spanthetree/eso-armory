# Development

[Documentation](README.md) · [Back to the README](../README.md)

## Setting up

Needs Python 3.12 or newer, [uv](https://docs.astral.sh/uv/) and
[Node.js](https://nodejs.org/) 18 or newer. Docker and CI build with Node 22;
Vite is pinned to 6 so the frontend still builds on Node 18.

```bash
git clone https://github.com/spanthetree/eso-armory.git && cd eso-armory
uv sync --dev
make ui-build            # the frontend, into static/dist/
make assets              # game icons from UESP, into assets/
make playwright-install  # Chromium for the browser tests
make run                 # http://localhost:5000
```

For frontend work, run `make ui-dev` beside the server: Vite serves the app on
port 5173 with hot reload and forwards `/api`, `/events`, `/assets` and
`/esoicons` to port 5000.

## Project layout

| Path | Contents |
|---|---|
| `app/` | The server package. `python -m app` starts it |
| `app/server.py` | FastAPI app: API, uploads, workspaces, caches, live updates, icon and tooltip lookups |
| `app/data_processor.py` | iasync and Wizard's Wardrobe data to API payloads |
| `app/lua_parser.py` | SavedVariables Lua parser (standard library only) |
| `app/item_link_decoder.py` | ESO item links to trait, style and enchantment fields |
| `app/db.py` | SQLite account storage (SQLAlchemy) |
| `app/uesp.py` | UESP image fetches, with the Photon fallback |
| `frontend/` | Svelte 5 app: `src/App.svelte` is the shell, `src/lib/` the views, components and logic |
| `tests/` | `unit/`, `api/` and `ui/` (Playwright) tests; sanitized `fixtures/` |
| `scripts/` | `download_assets.py` and its `assets_manifest.json`, `make_demo.py`, `generate_test_fixtures.py` |
| `demo/` | `demo.json.gz`, the demo account |
| `docker/` | `Dockerfile` and `entrypoint.sh`; the build context is the repository root |
| `docs/` | These docs, the header artwork and `config.example.json` |

Created at run time and never committed: `config.json`, `uploads/` (database,
price tables, share codes, cached skill names), `assets/` (icons), `logs/`
and `static/dist/`.

[Architecture](architecture.md) covers the data formats, every endpoint,
storage and the security model. Read it before changing the server or the
data processing, and update it in the same pull request.

## The frontend

[Svelte 5](https://svelte.dev/) with runes, in plain JavaScript with JSDoc
types, built by [Vite](https://vite.dev/). Pure logic lives in
`frontend/src/lib/*.js` with `*.test.js` unit tests beside it; components are
in `frontend/src/lib/<area>/`. Fonts are bundled, so the app loads nothing
from a CDN.

- **Two looks.** Classic rules are scoped as
  `:global(:root[data-ui='classic']) .x`, so Simple stays unchanged. Classic
  textures are cut from the game's art in `lib/eso/tex.js`; layouts follow the
  game's own interface files in [esoui/esoui](https://github.com/esoui/esoui).
- **Game data colours** (item quality, Health, Magicka, Stamina) are fixed.
  Everything else comes from the tokens in `lib/styles/tokens.css`.
- **One screen.** Views fit a 1400x900 window without page scrolling; long
  lists scroll inside their panel.
- **Untrusted text.** Names come from uploaded files and share codes. Svelte
  escapes text by default; never render them with `{@html}`.

## Tests

| Command | Runs |
|---|---|
| `make test-fast` | Python unit and API tests, with coverage (at least 60%) |
| `make frontend-test` | JavaScript unit tests (`node --test`) |
| `make test-ui` | Builds the frontend, then the Playwright tests in Chromium |
| `make test-all` | All of the above; run it before opening a pull request |

The browser suite includes a first-load check that fails if the page ever
shows raw Lua or source code instead of the setup screen.

Fixtures in `tests/fixtures/` are sanitized. Never commit real SavedVariables,
screenshots or logs: they contain an entire account.

## Game icons

Icons are ZeniMax artwork and are never committed. `scripts/assets_manifest.json`
maps each path under `assets/` to its URL on [UESP](https://en.uesp.net/);
`make assets` downloads them. To add one, add its entry and run `make assets`.
An icon requested before it is downloaded, and every `/esoicons/` icon, is
fetched on first use and saved into `assets/`.

UESP needs a browser-like User-Agent. When it refuses the host (HTTP 403), the
server uses the [Photon](https://developer.wordpress.com/docs/photon/) proxy
for 10 minutes.

## The demo account

`demo/demo.json.gz` is built from real SavedVariables with every account,
character, guild and setup name replaced:

```bash
uv run scripts/make_demo.py path/to/iasync.lua path/to/WizardsWardrobe.lua
```

The script refuses to write if any source name remains. The server loads the
file on start when it has changed. Rebuild it after any change to the
payloads, so every view has data.

## Releases

Every pull request bumps the version in `pyproject.toml`, runs `uv lock`, and
adds a dated section to `CHANGELOG.md`. Merging a version bump to `master`
releases it: the `release` workflow builds `ghcr.io/spanthetree/eso-armory`
for amd64 and arm64, tags the commit `vX.Y.Z`, and creates a GitHub release
from the changelog section. Never tag by hand. See
[Contributing](../.github/CONTRIBUTING.md) for the rest.
