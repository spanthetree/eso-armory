# Configuration

[Documentation](README.md) · [Back to the README](../README.md)

The server reads `config.json` on start. A source install keeps it in the
checkout; the Docker image keeps it in `uploads/config.json`. The first start
creates it with the defaults below and a new `db_secret`. Restart the server
after changing it.

```json
{
  "ttc_addon_path": "",
  "ttc_lookup_table_path": "",
  "ttc_price_table_path": "",
  "port": 5000,
  "server": "NA",
  "database_url": "sqlite:///uploads/armory.db",
  "admin_accounts": [],
  "db_secret": "<generated>"
}
```

A copy with every key is in [config.example.json](config.example.json).

## Keys

| Key | Default | Meaning |
|---|---|---|
| `server` | `NA` | Price region, `NA` or `EU`: picks the Tamriel Trade Centre price table |
| `port` | `5000` | HTTP port. `--port` on the command line overrides it; the container always uses 5000 inside |
| `database_url` | `sqlite:///uploads/armory.db` | Where account data is stored |
| `admin_accounts` | `[]` | ESO account names (`@name`) allowed to upload price tables. An account counts as admin only once it has a password |
| `db_secret` | generated | Encryption key for stored API keys. Keep it with the database: without it, those keys can't be read |
| `ttc_addon_path` | found on Windows and WSL | Tamriel Trade Centre addon folder in ESO's `AddOns` |
| `ttc_lookup_table_path` | the addon's `ItemLookUpTable_EN.lua` | Item name table |
| `ttc_price_table_path` | `""` | Price table. Empty picks `PriceTableNA.lua` or `PriceTableEU.lua` for `server` |
| `openai_api_key`, `openai_model` | | Shared OpenAI key and model for SuperStar import |
| `anthropic_api_key` | | Shared Anthropic key for SuperStar import |

| Environment variable | Meaning |
|---|---|
| `ESO_ARMORY_CONFIG` | Path of `config.json` (the Docker image sets `/app/uploads/config.json`) |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | Same as `openai_api_key` and `openai_model`; the model defaults to `gpt-4o` |
| `ANTHROPIC_API_KEY` | Same as `anthropic_api_key` |

## Tamriel Trade Centre prices

Item values come from the price tables of the
[Tamriel Trade Centre](https://www.tamrieltradecentre.com/) addon. The server
reads them from one of two places:

- **Uploaded tables.** An admin account (see `admin_accounts`) can upload
  `ItemLookUpTable_EN.lua` and the price table in the upload dialog, or have
  the folder watcher send them. They are stored once in `uploads/ttc/` and
  used for every account.
- **Local files.** The `ttc_*` paths, when the server runs on the PC with the
  addon. Uploaded tables take precedence.

Refresh the tables by updating the addon's data with its client, then
uploading again.

## SuperStar import

The SuperStar view reads a screenshot from the
[SuperStar](https://www.esoui.com/downloads/info3648-SuperStar-SeasonalUpdate.html)
addon with an AI service that can read images, then compares that build with
your gear. It needs an API key from
[OpenAI](https://platform.openai.com/api-keys) or
[Anthropic](https://console.anthropic.com/).

- **Per browser.** Anyone can add their own key in the SuperStar view. It is
  stored encrypted (with `db_secret`) for that browser session.
- **For everyone.** Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (or the
  `config.json` keys). OpenAI is used when both are set.

## HTTPS

The server speaks plain HTTP and expects a reverse proxy such as
[Caddy](https://caddyserver.com/) or [nginx](https://nginx.org/) to add HTTPS.
The live-update stream, `/events`, sends `X-Accel-Buffering: no`, so nginx
passes it through unbuffered. With Caddy:

```caddyfile
armory.example.com {
    reverse_proxy localhost:5000
}
```
