#!/usr/bin/env python3
"""Download ESO guild ability icons from UESP MediaWiki."""
import json, os, re, sys, time, urllib.request, urllib.parse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
API = "https://en.uesp.net/w/api.php"
BASE = os.path.join(os.path.dirname(__file__), "assets", "abilities", "guild")

# (MediaWiki filename, output dir, output filename)
ICONS = [
    # Dark Brotherhood
    ("ON-icon-skill-Dark Brotherhood-Blade of Woe.png",              "dark_brotherhood", "blade_of_woe.png"),
    ("ON-icon-skill-Dark Brotherhood-Padomaic Sprint.png",           "dark_brotherhood", "padomaic_sprint.png"),
    ("ON-icon-skill-Dark Brotherhood-Scales of Pitiless Justice.png","dark_brotherhood", "scales_of_pitiless_justice.png"),
    ("ON-icon-skill-Dark Brotherhood-Shadow Rider.png",              "dark_brotherhood", "shadow_rider.png"),
    ("ON-icon-skill-Dark Brotherhood-Shadowy Supplier.png",          "dark_brotherhood", "shadowy_supplier.png"),
    ("ON-icon-skill-Dark Brotherhood-Spectral Assassin.png",         "dark_brotherhood", "spectral_assassin.png"),
    # Fighters Guild
    ("ON-icon-skill-Fighters Guild-Banish the Wicked.png",           "fighters_guild", "banish_the_wicked.png"),
    ("ON-icon-skill-Fighters Guild-Barbed Trap.png",                 "fighters_guild", "barbed_trap.png"),
    ("ON-icon-skill-Fighters Guild-Bounty Hunter.png",               "fighters_guild", "bounty_hunter.png"),
    ("ON-icon-skill-Fighters Guild-Camouflaged Hunter.png",          "fighters_guild", "camouflaged_hunter.png"),
    ("ON-icon-skill-Fighters Guild-Circle of Protection.png",        "fighters_guild", "circle_of_protection.png"),
    ("ON-icon-skill-Fighters Guild-Dawnbreaker of Smiting.png",      "fighters_guild", "dawnbreaker_of_smiting.png"),
    ("ON-icon-skill-Fighters Guild-Dawnbreaker.png",                 "fighters_guild", "dawnbreaker.png"),
    ("ON-icon-skill-Fighters Guild-Evil Hunter.png",                 "fighters_guild", "evil_hunter.png"),
    ("ON-icon-skill-Fighters Guild-Expert Hunter.png",               "fighters_guild", "expert_hunter.png"),
    ("ON-icon-skill-Fighters Guild-Flawless Dawnbreaker.png",        "fighters_guild", "flawless_dawnbreaker.png"),
    ("ON-icon-skill-Fighters Guild-Intimidating Presence.png",       "fighters_guild", "intimidating_presence.png"),
    ("ON-icon-skill-Fighters Guild-Lightweight Beast Trap.png",      "fighters_guild", "lightweight_beast_trap.png"),
    ("ON-icon-skill-Fighters Guild-Ring of Preservation.png",        "fighters_guild", "ring_of_preservation.png"),
    ("ON-icon-skill-Fighters Guild-Silver Bolts.png",                "fighters_guild", "silver_bolts.png"),
    ("ON-icon-skill-Fighters Guild-Silver Leash.png",                "fighters_guild", "silver_leash.png"),
    ("ON-icon-skill-Fighters Guild-Silver Shards.png",               "fighters_guild", "silver_shards.png"),
    ("ON-icon-skill-Fighters Guild-Skilled Tracker.png",             "fighters_guild", "skilled_tracker.png"),
    ("ON-icon-skill-Fighters Guild-Slayer.png",                      "fighters_guild", "slayer.png"),
    ("ON-icon-skill-Fighters Guild-Trap Beast.png",                  "fighters_guild", "trap_beast.png"),
    ("ON-icon-skill-Fighters Guild-Turn Evil.png",                   "fighters_guild", "turn_evil.png"),
    # Mages Guild
    ("ON-icon-skill-Mages Guild-Balance.png",                        "mages_guild", "balance.png"),
    ("ON-icon-skill-Mages Guild-Degeneration.png",                   "mages_guild", "degeneration.png"),
    ("ON-icon-skill-Mages Guild-Entropy.png",                        "mages_guild", "entropy.png"),
    ("ON-icon-skill-Mages Guild-Equilibrium.png",                    "mages_guild", "equilibrium.png"),
    ("ON-icon-skill-Mages Guild-Everlasting Magic.png",              "mages_guild", "everlasting_magic.png"),
    ("ON-icon-skill-Mages Guild-Fire Rune.png",                      "mages_guild", "fire_rune.png"),
    ("ON-icon-skill-Mages Guild-Ice Comet.png",                      "mages_guild", "ice_comet.png"),
    ("ON-icon-skill-Mages Guild-Inner Light.png",                    "mages_guild", "inner_light.png"),
    ("ON-icon-skill-Mages Guild-Mage Adept.png",                     "mages_guild", "mage_adept.png"),
    ("ON-icon-skill-Mages Guild-Magelight.png",                      "mages_guild", "magelight.png"),
    ("ON-icon-skill-Mages Guild-Magicka Controller.png",             "mages_guild", "magicka_controller.png"),
    ("ON-icon-skill-Mages Guild-Meteor.png",                         "mages_guild", "meteor.png"),
    ("ON-icon-skill-Mages Guild-Might of the Guild.png",             "mages_guild", "might_of_the_guild.png"),
    ("ON-icon-skill-Mages Guild-Persuasive Will.png",                "mages_guild", "persuasive_will.png"),
    ("ON-icon-skill-Mages Guild-Radiant Magelight.png",              "mages_guild", "radiant_magelight.png"),
    ("ON-icon-skill-Mages Guild-Scalding Rune.png",                  "mages_guild", "scalding_rune.png"),
    ("ON-icon-skill-Mages Guild-Shooting Star.png",                  "mages_guild", "shooting_star.png"),
    ("ON-icon-skill-Mages Guild-Spell Symmetry.png",                 "mages_guild", "spell_symmetry.png"),
    ("ON-icon-skill-Mages Guild-Structured Entropy.png",             "mages_guild", "structured_entropy.png"),
    ("ON-icon-skill-Mages Guild-Volcanic Rune.png",                  "mages_guild", "volcanic_rune.png"),
    # Psijic Order
    ("ON-icon-skill-Psijic Order-Accelerate.png",                    "psijic_order", "accelerate.png"),
    ("ON-icon-skill-Psijic Order-Borrowed Time.png",                 "psijic_order", "borrowed_time.png"),
    ("ON-icon-skill-Psijic Order-Channeled Acceleration.png",        "psijic_order", "channeled_acceleration.png"),
    ("ON-icon-skill-Psijic Order-Clairvoyance.png",                  "psijic_order", "clairvoyance.png"),
    ("ON-icon-skill-Psijic Order-Concentrated Barrier.png",          "psijic_order", "concentrated_barrier.png"),
    ("ON-icon-skill-Psijic Order-Crushing Weapon.png",               "psijic_order", "crushing_weapon.png"),
    ("ON-icon-skill-Psijic Order-Deep Thoughts.png",                 "psijic_order", "deep_thoughts.png"),
    ("ON-icon-skill-Psijic Order-Deliberation.png",                  "psijic_order", "deliberation.png"),
    ("ON-icon-skill-Psijic Order-Elemental Weapon.png",              "psijic_order", "elemental_weapon.png"),
    ("ON-icon-skill-Psijic Order-Imbue Weapon.png",                  "psijic_order", "imbue_weapon.png"),
    ("ON-icon-skill-Psijic Order-Introspection.png",                 "psijic_order", "introspection.png"),
    ("ON-icon-skill-Psijic Order-Meditate.png",                      "psijic_order", "meditate.png"),
    ("ON-icon-skill-Psijic Order-Mend Spirit.png",                   "psijic_order", "mend_spirit.png"),
    ("ON-icon-skill-Psijic Order-Mend Wounds.png",                   "psijic_order", "mend_wounds.png"),
    ("ON-icon-skill-Psijic Order-Precognition.png",                  "psijic_order", "precognition.png"),
    ("ON-icon-skill-Psijic Order-Race Against Time.png",             "psijic_order", "race_against_time.png"),
    ("ON-icon-skill-Psijic Order-See the Unseen.png",                "psijic_order", "see_the_unseen.png"),
    ("ON-icon-skill-Psijic Order-Spell Orb.png",                     "psijic_order", "spell_orb.png"),
    ("ON-icon-skill-Psijic Order-Symbiosis.png",                     "psijic_order", "symbiosis.png"),
    ("ON-icon-skill-Psijic Order-Temporal Guard.png",                "psijic_order", "temporal_guard.png"),
    ("ON-icon-skill-Psijic Order-Time Freeze.png",                   "psijic_order", "time_freeze.png"),
    ("ON-icon-skill-Psijic Order-Time Stop.png",                     "psijic_order", "time_stop.png"),
    ("ON-icon-skill-Psijic Order-Undo.png",                          "psijic_order", "undo.png"),
    # Thieves Guild
    ("ON-icon-skill-Thieves Guild-Clemency.png",                     "thieves_guild", "clemency.png"),
    ("ON-icon-skill-Thieves Guild-Finders Keepers.png",              "thieves_guild", "finders_keepers.png"),
    ("ON-icon-skill-Thieves Guild-Haggling.png",                     "thieves_guild", "haggling.png"),
    ("ON-icon-skill-Thieves Guild-Swiftly Forgotten.png",            "thieves_guild", "swiftly_forgotten.png"),
    ("ON-icon-skill-Thieves Guild-Timely Escape.png",                "thieves_guild", "timely_escape.png"),
    ("ON-icon-skill-Thieves Guild-Veil of Shadows.png",              "thieves_guild", "veil_of_shadows.png"),
    # Undaunted
    ("ON-icon-skill-Undaunted-Blood Altar.png",                      "undaunted", "blood_altar.png"),
    ("ON-icon-skill-Undaunted-Bone Shield.png",                      "undaunted", "bone_shield.png"),
    ("ON-icon-skill-Undaunted-Bone Surge.png",                       "undaunted", "bone_surge.png"),
    ("ON-icon-skill-Undaunted-Energy Orb.png",                       "undaunted", "energy_orb.png"),
    ("ON-icon-skill-Undaunted-Inner Beast.png",                      "undaunted", "inner_beast.png"),
    ("ON-icon-skill-Undaunted-Inner Fire.png",                       "undaunted", "inner_fire.png"),
    ("ON-icon-skill-Undaunted-Inner Rage.png",                       "undaunted", "inner_rage.png"),
    ("ON-icon-skill-Undaunted-Mystic Orb.png",                       "undaunted", "mystic_orb.png"),
    ("ON-icon-skill-Undaunted-Necrotic Orb.png",                     "undaunted", "necrotic_orb.png"),
    ("ON-icon-skill-Undaunted-Overflowing Altar.png",                "undaunted", "overflowing_altar.png"),
    ("ON-icon-skill-Undaunted-Sanguine Altar.png",                   "undaunted", "sanguine_altar.png"),
    ("ON-icon-skill-Undaunted-Shadow Silk.png",                      "undaunted", "shadow_silk.png"),
    ("ON-icon-skill-Undaunted-Spiked Bone Shield.png",               "undaunted", "spiked_bone_shield.png"),
    ("ON-icon-skill-Undaunted-Tangling Webs.png",                    "undaunted", "tangling_webs.png"),
    ("ON-icon-skill-Undaunted-Trapping Webs.png",                    "undaunted", "trapping_webs.png"),
]


def api_resolve(titles):
    """Resolve a batch of File: titles to direct image URLs via MediaWiki API."""
    params = urllib.parse.urlencode({
        "action": "query",
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
        "titles": "|".join(f"File:{t}" for t in titles),
    })
    req = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    url_map = {}
    for page in data["query"]["pages"].values():
        title = page["title"].removeprefix("File:")
        if "imageinfo" in page:
            url_map[title] = page["imageinfo"][0]["url"]
    return url_map


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    with open(dest, "wb") as f:
        f.write(data)


def main():
    # Batch resolve URLs (max 50 per call)
    print(f"Resolving {len(ICONS)} icon URLs via MediaWiki API...")
    all_titles = [mw for mw, _, _ in ICONS]
    url_map = {}
    for i in range(0, len(all_titles), 50):
        batch = all_titles[i:i+50]
        url_map.update(api_resolve(batch))
        if i + 50 < len(all_titles):
            time.sleep(0.5)

    ok = skip = fail = 0
    for mw_title, subdir, filename in ICONS:
        dest = os.path.join(BASE, subdir, filename)
        if os.path.exists(dest):
            skip += 1
            continue
        url = url_map.get(mw_title)
        if not url:
            print(f"  MISSING URL: {mw_title}")
            fail += 1
            continue
        try:
            download(url, dest)
            print(f"  OK  {subdir}/{filename}")
            ok += 1
        except Exception as e:
            print(f"  ERR {subdir}/{filename}: {e}")
            fail += 1
        time.sleep(0.1)

    print(f"\nDone: {ok} downloaded, {skip} skipped (exist), {fail} failed")


if __name__ == "__main__":
    main()
