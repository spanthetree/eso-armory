# FAQ

[Documentation](README.md) · [Back to the README](../README.md)

## What it is

### What does ESO Armory do?

It shows your Elder Scrolls Online account in a browser: every character's
gear and builds, everything you own and where it is, achievements,
collections and activities. The game has no way to look at this from outside,
so an addon, [iasync](https://github.com/spanthetree/iasync), writes it to a
file, and ESO Armory reads that file.

### How does the data get from the game to the browser?

1. iasync records your account while you play.
2. ESO writes it to `SavedVariables\iasync.lua` when you log out or type
   `/reloadui`. Addons can't write files at any other time.
3. You upload that file, or the browser uploads it for you when it watches
   the folder.
4. The server parses it, stores the result for your ESO account, and every
   open browser reloads.

### Does it work on console?

No. Console ESO has no addons, so there is nothing to read.

### Is it allowed?

iasync uses only the game's public addon API and reads nothing the game
doesn't show you; ESO Armory never touches the game. Neither automates play.

## Privacy

### What leaves my machine?

Your account data stays on the server you run. The raw SavedVariables files
are parsed in memory and discarded; only the processed result is stored.

To draw the game, the server makes these requests. They carry icon, set or
skill names or ids, never your account data.

| Service | Used for |
|---|---|
| [UESP](https://en.uesp.net/) (`esoicons.uesp.net`, `images.uesp.net`) | Game icons, downloaded once and cached in `assets/` |
| [UESP esolog](https://esolog.uesp.net/) | Names of skills iasync couldn't name, cached in `uploads/ability_names/` |
| [Photon](https://developer.wordpress.com/docs/photon/) (`i0.wp.com`) | Icons, only when UESP refuses the server (common on cloud hosts) |
| [eso-sets.com](https://eso-sets.com/) | Set bonuses and drop locations in tooltips |
| [eso-skillbook.com](https://eso-skillbook.com/) | Skill details in tooltips |
| [OpenAI](https://openai.com/) or [Anthropic](https://www.anthropic.com/) | Reading a SuperStar screenshot, only when you upload one with an API key |

### Who can see my data?

Only browsers you link: the one that uploaded, browsers you log in with your
password, and anyone you give a share code. Share codes are read-only. Set a
password: an account without one can be claimed by anyone who uploads a file
naming it.

### Where is it stored?

In SQLite, in `uploads/armory.db`. Passwords are hashed with bcrypt. API keys
added in the SuperStar view are encrypted with the server's `db_secret`.

## Addons and data

### Which iasync version do I need?

Use the latest. Older versions still load, but views that need newer data are
empty or show less.

| iasync | Adds |
|---|---|
| 1.4.0 | The character's figure (gender) on the Equipped panel |
| 1.5.0 | Max Health, Magicka and Stamina |
| 1.6.0 | Set piece and category icons in Collections |
| 1.7.0 | Transmute costs, piece quality, the game's interface colours |
| 1.9.0 | Collectibles, Housing and Outfit Styles |
| 1.10.0 | Tales of Tribute patrons |
| 1.11.0 | Level, title, riding and guilds; Crafting and Scribing; currencies; the Tamriel Tome, Endeavors and Golden Pursuits; Antiquities |
| 1.12.0 | Mundus and Champion star descriptions |
| 1.13.0 | Each item's own icon |
| 1.14.0 | Descriptions for every Champion star |
| 1.15.0 | Exact skill icons |
| 1.16.0 | Armory builds |
| 1.17.0 | The last item seen in a missing Armory slot |

### Do I need Wizard's Wardrobe or Tamriel Trade Centre?

No. [Wizard's Wardrobe](https://www.esoui.com/downloads/info3170-WizardsWardrobe.html)
adds the Wizards Wardrobe view. The
[Tamriel Trade Centre](https://www.esoui.com/downloads/info1245-TamrielTradeCentre.html)
price tables add item values; see
[Configuration](configuration.md#tamriel-trade-centre-prices).

## Troubleshooting

### A character is missing

ESO only exposes the character you are logged in with. Log in to it once with
iasync enabled, log out or `/reloadui`, then upload again.

### My bank, house chests or guild banks are empty

iasync captures them when you open them: open the bank, enter each house you
own, and view each guild bank (your rank must be able to see it).

### Armory builds show no skill bars

The game hands out Armory skill bars and Champion stars only at an Armory
station. Visit one with iasync enabled, `/reloadui`, and upload again. iasync
keeps them after that.

### An Armory build shows gear in red

That piece is missing (sold, deconstructed, or replaced by another copy of
the same item) or in a house chest, where the Armory can't reach it. The game
tracks the exact copy, so even an identical item doesn't count.

### No build is marked Equipped

A build is marked only when all of its remaining gear is worn and its
attributes and mundus match. Change one piece and no build matches.

### I updated iasync, but nothing new appears

If you updated it while the game was running, `/reloadui` loads the new
version and a second `/reloadui` writes its data. Then upload again.

### Auto-sync stopped after I restarted the browser

The browser asks again for access to the folder after a restart. Choose
**Resume watching** in the top bar.

### Icons are missing on a cloud server

UESP refuses many cloud hosts. The server falls back to the Photon proxy on
its own; if that fails too, the browser loads icons straight from UESP. See
[Installing](install.md#hosting-on-a-cloud-server).

### Something else is wrong

Open an [issue](https://github.com/spanthetree/eso-armory/issues) with the
version you run (the image tag, or `version` in `pyproject.toml`), what you
did, and what you expected. Never attach your SavedVariables files: they hold your whole
account.
