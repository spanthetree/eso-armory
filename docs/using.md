# Using ESO Armory

[Documentation](README.md) · [Back to the README](../README.md)

The app has five tabs along the top: **Characters**, **Inventory**,
**Achievements**, **Collections** and **Tamriel Tome**. The address bar keeps
your place, so a reload or a shared link opens the same view.

## Characters

The roster lists every character iasync has captured. Open one to see its
views, switched with the icons under the tabs:

| View | Shows |
|---|---|
| **Sheet** | Equipped gear on the game's "Equipped" panel, skill bars, Champion stars, attributes with max Health, Magicka and Stamina, mundus, level, title, Alliance War rank, riding and guilds |
| **Crafting** | Trait research per craft, known motifs and recipes |
| **Scribing** | Grimoires and the scripts each can take |
| **Armory** | The in-game Armory's saved builds ([below](#armory-builds)) |
| **Wizards Wardrobe** | Setups saved with [Wizard's Wardrobe](https://www.esoui.com/downloads/info3170-WizardsWardrobe.html): gear, bars, Champion stars and food |
| **Bags** | The character's equipped and backpack items |
| **Compare** | This character's build next to one imported by code ([below](#build-codes)) |
| **SuperStar** | A [SuperStar](https://www.esoui.com/downloads/info3648-SuperStar-SeasonalUpdate.html) screenshot compared with your gear ([below](#superstar-screenshots)) |

Hover over, or tab to, any item, set, skill, star or mundus stone for its
tooltip. Set bonuses come from [eso-sets.com](https://eso-sets.com/) and skill
details from [eso-skillbook.com](https://eso-skillbook.com/).

### Armory builds

The Armory view lists the builds saved at an Armory station, with their icons,
as the game does. The selected build shows its gear, skill bars, Champion
stars, attributes, mundus, curse (vampirism or lycanthropy) and outfit.

- **Equipped.** The game doesn't report which build is loaded, so the build
  whose remaining gear is all worn, and whose attributes and mundus match the
  character, is marked **Equipped**.
- **Red gear.** A piece in red is missing (sold, deconstructed, or replaced by
  another copy) or in a house chest, where the Armory can't reach it. A
  missing piece shows the item iasync last saw in that slot, if it saw one.
- **Skill bars and Champion stars** appear after you visit an Armory station
  with iasync running; the game provides them only there. iasync then keeps
  them until your next visit.

### Build codes

**Compare** exports this character's build as a short code that anyone can
import. Importing a code shows that build beside yours, slot by slot, with the
pieces you lack, where they drop (dungeon, trial, arena) and their estimated
Tamriel Trade Centre cost.

### SuperStar screenshots

Upload a screenshot of a SuperStar build page. An AI service reads it, and the
view compares that build with your gear, slot by slot. This needs an OpenAI or
Anthropic API key: add your own in the view, or the server's admin can set one
for everyone ([Configuration](configuration.md#superstar-import)).

## Inventory

Every item on the account: characters, bank, ESO Plus bank, craft bag, house
chests and guild banks, with the number held in each place.

- **Search and filter** by name, quality, type, trait, location and character,
  or group items by set. Save a filter as a chip to reuse it.
- **Values.** With price tables loaded, each item shows its Tamriel Trade
  Centre value, with totals by type and location.
- **Duplicates.** Find gear you hold more than one copy of.

## Achievements

- **Achievements** is laid out like the in-game journal: the category tree,
  progress bars, recent unlocks, a timeline, criteria progress per character
  and search.
- **Antiquities** lists leads, zones, recovered counts and Codex progress.

## Collections

The in-game Collections book: **Collectibles**, **Housing**, **Outfit
Styles**, **Set Items** and **Tales of Tribute**. Each has the game's
category tree, a keyword filter and a locked or unlocked filter. Set Items
shows each set as a grid of its pieces, filtered by apparel and weapon type,
with where each piece drops and its price.

## Tamriel Tome

The Tamriel Tome reward track, weekly and seasonal **Endeavors**, and
**Golden Pursuits**. The account's currencies are in the header whenever no
character is open.

## Accounts, passwords and sharing

Data is stored per ESO account, so it reopens in the same browser without
uploading again. The top bar holds the account controls.

- **Password.** Set one after your first upload. It lets you log in from
  another device with your account name, and stops anyone else claiming the
  account by uploading a file that names it.
- **Share.** Create a code such as `ABCD-EFGH`. Anyone who enters it sees
  your data, read-only. Use **Log out** to unlink a browser.
- **Alt.** Uploading a second ESO account fills the **Alt** slot, so you can
  switch between two accounts. Only the Alt slot can be removed.
- **Demo.** **Open the demo account** on the landing page loads a sample
  account (code `DEMA-RMRY`), read-only.

## Keeping data current

- **Upload again** after playing: the server replaces that account's data,
  and every open browser reloads.
- **Watch the folder** (Chrome and Edge). Pick your ESO `live` folder, or its
  `SavedVariables` folder, in the upload dialog. The app checks it every 10
  seconds and uploads files that changed. **Refresh** uploads them at once.
  After a browser restart, choose **Resume watching** to allow access again.
- Without a watched folder, **Refresh** reloads what the server has.

## The two looks

Pick one in the **UI** menu of the top bar. The choice is kept per browser.

- **Classic** (the default) redraws the app in the game's keyboard interface
  art: the main menu icon bar, window backdrops, buttons, list rows and
  progress bars, over a darkened loading screen. The game's font is used if
  it is installed on your PC.
- **Simple** is a plain look: dark panels with gold rules.

Both are designed to fit a 1400x900 window without scrolling the page; long
lists scroll inside their panels.
