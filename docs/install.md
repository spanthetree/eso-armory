# Installing

[Documentation](README.md) · [Back to the README](../README.md)

ESO Armory is a small web server. Run it on the PC you play on, or on any
machine your browser can reach. It runs in Docker or straight from a checkout.

## The addons

Install these in ESO first. [Minion](https://minion.mmoui.com/) or a manual
copy into `Documents\Elder Scrolls Online\live\AddOns\` both work.

| Addon | Needed for |
|---|---|
| [iasync](https://github.com/spanthetree/iasync) | Everything: characters, gear, inventory, builds, achievements, collections (required) |
| [Wizard's Wardrobe](https://www.esoui.com/downloads/info3170-WizardsWardrobe.html) | The Wizards Wardrobe view of saved setups |
| [Tamriel Trade Centre](https://www.esoui.com/downloads/info1245-TamrielTradeCentre.html) | Item prices; see [Configuration](configuration.md#tamriel-trade-centre-prices) |

Use the latest iasync. Older versions still load, but the views that need
newer data stay empty; the [FAQ](faq.md#which-iasync-version-do-i-need) lists
which version added what.

## Docker

Needs [Docker with Compose](https://docs.docker.com/compose/).

```bash
mkdir eso-armory && cd eso-armory
curl -O https://raw.githubusercontent.com/spanthetree/eso-armory/master/compose.yaml
docker compose up -d
```

This pulls `ghcr.io/spanthetree/eso-armory` and serves on port 5000. The first
start downloads the game icons from UESP, which takes about 2 minutes; later
starts skip icons that are already there.

| Task | Command | From a checkout |
|---|---|---|
| Start | `docker compose up -d` | `make up` |
| Stop | `docker compose down` | `make down` |
| Upgrade to the latest release | `docker compose pull && docker compose up -d` | `make upgrade` |
| Run your local code | `docker compose up -d --build` | |

Data lives in two folders next to `compose.yaml`: `uploads/` (the database,
Tamriel Trade Centre tables and `config.json` with its encryption key) and
`assets/` (icons). Stopping, upgrading or removing the container keeps them.

Settings for Compose go in a `.env` file next to `compose.yaml`:

| Variable | Default | Meaning |
|---|---|---|
| `ESO_ARMORY_PORT` | `5000` | Port on the host |
| `ESO_ARMORY_VERSION` | `latest` | Image tag, to pin a release such as `0.2.0-beta.11` |
| `ESO_ARMORY_DIR` | `.` | Folder holding `uploads/` and `assets/` |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | | A shared key for SuperStar import ([Configuration](configuration.md#superstar-import)) |

To change other settings, edit `uploads/config.json`, then
`docker compose restart`.

### Moving to Docker from a source install

Run Compose in the checkout, or set `ESO_ARMORY_DIR` to it. On first start the
container uses that checkout's database, icons and `config.json` (its
`db_secret` decrypts stored API keys). The container runs as the owner of
`uploads/`, so the files stay yours.

### Upgrading from 0.2.0-beta.3 or earlier

Older compose files kept data in a Docker volume. Download the new
`compose.yaml` into the same folder: on first start it copies the volume into
`uploads/` when `uploads/` has no database yet. Icons are downloaded again.

## From source

Needs Python 3.12 or newer, [uv](https://docs.astral.sh/uv/) and
[Node.js](https://nodejs.org/) 18 or newer.

```bash
git clone https://github.com/spanthetree/eso-armory.git && cd eso-armory
uv sync
make ui-build              # build the web app into static/dist/
make assets                # download game icons from UESP (about 2 minutes)
make run                   # http://localhost:5000
PORT=8080 make run         # or another port
```

`make run` is `uv run python -m app`. The first start writes `config.json` in
the checkout; see [Configuration](configuration.md). After `git pull`, run
`uv sync` and `make ui-build` again.

## Hosting on a cloud server

[UESP](https://en.uesp.net/) sits behind Cloudflare, which refuses many cloud
hosts (AWS, Lightsail and others) with HTTP 403. The server then fetches icons
through WordPress.com's public image proxy,
[Photon](https://developer.wordpress.com/docs/photon/) (`i0.wp.com`), for the
next 10 minutes, and saves them in `assets/` like any other icon. Photon
re-encodes some PNGs with a 256-colour palette, which is barely visible. UESP
is always tried first.

The server speaks plain HTTP. On anything but your own PC, put it behind a
reverse proxy with HTTPS; see [Configuration](configuration.md#https).

## Your first upload

1. **Capture each character.** Log in to it with iasync enabled. iasync scans
   on login, `/reloadui` and zone changes, and ESO writes the file when you
   log out or reload. Open your bank once for bank contents, and visit an
   Armory station once for Armory skill bars and Champion stars.
2. **Open the app** and choose **Select files**. Pick `iasync.lua`, and
   `WizardsWardrobe.lua` if you use it, from
   `Documents\Elder Scrolls Online\live\SavedVariables\`.
3. **Set a password** when the app asks. Until then, anyone who uploads a file
   naming your account can claim it.
4. **Optional: watch the folder.** In Chrome or Edge, choose **Select your ESO
   live folder** in the upload dialog (the `live` folder or its
   `SavedVariables` folder both work). The app then uploads new data as you
   play.

If you update iasync while the game is running, `/reloadui` loads the new
version, and a second `/reloadui` writes its data.
