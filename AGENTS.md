# ESO Armory - Agent Notes

Decisions, rules and context that the code and git history don't show. For
the layout, commands and data formats, read [docs/development.md](docs/development.md)
and [docs/architecture.md](docs/architecture.md) (keep the latter current in
the same PR as any server, storage or API change).

## Working here
- **Approval:** before changing code or files, get explicit approval unless the user asked for the implementation in the current turn. Read-only inspection is always fine.
- **Environment:** developed on WSL2; the ESO client runs on Windows and writes SavedVariables to `/mnt/c/Users/<user>/Documents/Elder Scrolls Online/live/SavedVariables/`.
- **Restarting the server:** `fuser -k 5000/tcp 2>/dev/null; sleep 1 && uv run python -m app &`. Use `fuser` on the port, not `pkill`: it is the reliable way on WSL2.
- **Check layouts in a real browser** with a real account (and the demo) at 1400x900 in both looks after any UI change.
- **iasync is the data source, in its own repo** ([spanthetree/iasync](https://github.com/spanthetree/iasync)). When the server needs data the file doesn't have, or the file is wrong, fix it in iasync rather than working around it here; keep a defensive guard here only so older files still display correctly.

## Git workflow
Agents may run git and `gh` (branch, commit, push, open PRs).
- Branch from a freshly pulled `master`; never commit to `master`.
- One PR per issue, each phase its own commit. The user sometimes asks to roll several changes into one PR; then fold their changelog entries into that PR's version.
- The branch's last commit before `gh pr create`: update `README.md` and `docs/` if anything user-facing changed, add a dated `## [x.y.z] - YYYY-MM-DD` section to `CHANGELOG.md`, bump `pyproject.toml` and run `uv lock`.
- Run `make test-all` before opening the PR. The user merges.
- Merging a version bump releases it (`.github/workflows/release.yml`); never tag by hand.
- No force-push, history rewrite or branch deletion without asking.
- `gh pr edit` fails on this repo (a Projects-classic deprecation error); update PRs with `gh api -X PATCH repos/spanthetree/eso-armory/pulls/<n>`.

## Repository layout decisions
- As few files as possible at the root; everything else has a home (`app/`, `docker/`, `docs/`, `.github/`, `scripts/`).
- `compose.yaml` stays at the root: the install docs download it from `raw.githubusercontent.com/.../master/compose.yaml`, so moving it breaks existing instructions.
- The Docker build context is the repo root (`docker/Dockerfile`); `.dockerignore` must stay at the root.

## Design decisions
- **Two looks.** *Classic* (the default) redraws the app in the game's own keyboard UI: real textures from UESP and layouts copied from the esoui XML templates ([esoui/esoui](https://github.com/esoui/esoui)). When a game screen exists for something, build it from that screen's templates and textures; otherwise match the rest of the Classic art. *Simple* ("Obsidian") is the plain look. Scope every Classic rule as `:global(:root[data-ui='classic']) .x` so Simple never changes.
- **No themes and no alliance/faction tinting.** Both were built and removed on purpose; text is neutral white/grey.
- **Gold** (`--accent`, `--accent-hi`) is for rules, frames and ornaments only, never text.
- **Game data colours are not design tokens:** item quality and Health/Magicka/Stamina colours (`--q-*`, `--res-*`, `item.quality_color`) come from the game and must not be restyled.
- **Fit one screen:** character views and the Inventory, Achievements and Collections tabs fit 1400x900 without page scrolling; long lists scroll inside their panel. Drop or shrink panels before letting the page scroll (the Armory view has no Sets panel for this reason, like the game's Armory).
- **Game icons are 64px:** keep gear and skill icons at or below 64 CSS px.
- **The Armory view's switcher icon** is the plain white `armory/builditem_icon` (the game has no up/over/down set for it). A tinted version was tried and rejected; leave it white.
- **The game font** (Univers 57/67 Condensed) can't be shipped; it is used only if installed locally, with Barlow Condensed as the fallback.
- **Vite is pinned to 6** so the frontend builds on the user's local Node 18; Docker and CI use Node 22.

## Policies
- **Never commit game artwork.** Icons and textures come from UESP into `assets/` (gitignored) via `scripts/assets_manifest.json`.
- **Never commit live account data** (SavedVariables, screenshots, logs). Use the sanitized `tests/fixtures/`.
- **The demo account must stay generic:** regenerate `demo/demo.json.gz` with `scripts/make_demo.py` after payload changes, and give any new user-named data (builds, outfits, setups) generic names there, not the source account's.
- **Untrusted text:** names come from uploaded files and share codes; never render them with `{@html}`.

## Documentation style
- README stays short (what it is, features, privacy, getting started, limitations, a docs index, related projects); detail goes in `docs/`, user-facing first, then architecture and development.
- Plain, factual voice; short sentences; no marketing words; state limits plainly. Prose hard-wrapped at about 78 columns (tables and code are not).
- Link every external app, addon and service the server uses (UESP, esolog, Photon, eso-sets.com, eso-skillbook.com, OpenAI/Anthropic, the addons) and check each link opens. esoui addon IDs are easy to get wrong.
- Don't mention other projects used only as style references.
- Docs must match the code: check new claims against it.

## Known issues and quirks
- **20-field item links (deferred):** some links have 20 fields, which shifts the flags to `[13]` and may drop `[16]`; `app/item_link_decoder.py` doesn't handle it yet. Transmuted and reconstructed items both set flag bit 11, so they can't be told apart.
- **Mythics have `set_id` 0:** key set-bonus caches by `setKey(item)` (`gear.js`), never `set_id` directly.
- **No `structuredClone` on Svelte state:** it throws on `$state` proxies; use `$state.snapshot` or a JSON copy.
- **`{#each}` keys must be unique** or the render aborts; `recent` achievements can repeat an id, so key those by position.
- **`/api/data` 503** means nothing is uploaded yet and stays silent; Achievements and Collections do surface their errors (the UI tests expect "User data not loaded").
- **Prices:** fetch them with one `POST /api/ttc_prices` per item list, never `/api/ttc_price` per row.
- **Armory data limits (game side):** skill bars and Champion stars reach the client only at an Armory station; no API reports the loaded build; a missing piece comes with a placeholder location (backpack slot 0), so its item fields must be ignored.
