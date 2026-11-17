iasync_data = {
  ["accountName"] = "@test_account",
  ["lastUpdate"] = 1700000000,
  ["abilityNames"] = {
    [101] = "Mock Whip",
    [102] = "Mock Shield",
    [108] = "Mock Standard",
  },
  ["cpNames"] = {
    [201] = "Mock Warfare",
  },
  ["chars"] = {
    ["char-a"] = {
      ["name"] = "Test Character One",
      ["race"] = "Breton",
      ["class"] = "Dragonknight",
      ["alliance"] = "Daggerfall Covenant",
      ["gender"] = "female",
      ["gold"] = 1234,
      ["ap"] = 20,
      ["tv"] = 0,
      ["wv"] = 2,
      ["spaceUsed"] = 3,
      ["spaceMax"] = 60,
      ["bags"] = {
        [0] = {
          [4] = {
            ["link"] = "|H1:item:1001:0:50:3001:0:0:3:0:0:0:0:0:0:0:2049:1:1:1:0:42:0|h[Mock Sword^n]|h",
            ["name"] = "Mock Sword^n",
            ["qty"] = 1,
            ["traitType"] = 3,
            ["traitName"] = "Precise",
            ["enchantId"] = 3001,
            ["enchantName"] = "Flame",
            ["setId"] = 500,
            ["setName"] = "Mock Set",
            ["quality"] = 4,
            ["filterType"] = 1,
            ["weaponType"] = "Sword",
          },
          [2] = {
            ["link"] = "|H1:item:1002:0:50:0:0:0:18:0:0:0:0:0:0:0:1:2:0:1:0:25:0|h[Mock Cuirass^n]|h",
            ["name"] = "Mock Cuirass^n",
            ["qty"] = 1,
            ["traitType"] = 18,
            ["traitName"] = "Divines",
            ["setId"] = 500,
            ["setName"] = "Mock Set",
            ["quality"] = 3,
            ["filterType"] = 2,
            ["armorType"] = "Heavy",
          },
        },
        [1] = {
          [12] = {
            ["link"] = "|H1:item:2001:0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:3:0|h[Mock Potion^n]|h",
            ["name"] = "Mock Potion^n",
            ["qty"] = 4,
            ["quality"] = 1,
            ["filterType"] = 3,
          },
        },
      },
      ["build_bars"] = {
        ["primary"] = {
          [3] = 101,
          [4] = 102,
          [8] = 108,
        },
        ["backup"] = {
          [3] = 102,
        },
      },
      ["build_pools"] = {
        ["health"] = 21865,
        ["magicka"] = 41210,
        ["stamina"] = 12400,
      },
      ["build_attributes"] = {
        ["health"] = 10,
        ["magicka"] = 20,
        ["stamina"] = 30,
      },
      ["build_mundus"] = {
        [1] = "The Thief",
      },
      ["build_cp"] = {
        ["earned"] = 900,
        ["slots"] = {
          [1] = 201,
        },
      },
      ["achievements"] = {
        [9001] = {
          ["name"] = "Mock Character Achievement",
          ["desc"] = "Earned by one test character.",
          ["cat"] = "General",
          ["subcat"] = "Testing",
          ["points"] = 5,
          ["complete"] = true,
          ["completionTimestamp"] = 1700000010,
          ["completionDate"] = "2023-11-14",
          ["persistenceLevel"] = 1,
          ["criteria"] = {
            [1] = {
              ["desc"] = "Do the thing",
              ["cur"] = 1,
              ["req"] = 1,
            },
          },
        },
      },
    },
    ["char-b"] = {
      ["name"] = "Test Character Two",
      ["race"] = "High Elf",
      ["class"] = "Templar",
      ["alliance"] = "Aldmeri Dominion",
      ["gold"] = 100,
      ["spaceUsed"] = 0,
      ["spaceMax"] = 60,
      ["bags"] = {},
    },
  },
  ["bank"] = {
    ["gold"] = 5000,
    ["ap"] = 10,
    ["tv"] = 5,
    ["wv"] = 1,
    ["bags"] = {
      [2] = {
        [1] = {
          ["link"] = "|H1:item:2001:0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:3:0|h[Mock Potion^n]|h",
          ["name"] = "Mock Potion^n",
          ["qty"] = 6,
          ["quality"] = 1,
          ["filterType"] = 3,
        },
      },
      [5] = {
        [4] = {
          ["link"] = "|H1:item:3001:0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1:0|h[Mock Material^n]|h",
          ["name"] = "Mock Material^n",
          ["qty"] = 10,
          ["quality"] = 2,
          ["filterType"] = 4,
        },
      },
    },
  },
  ["houses"] = {
    ["test-house"] = {
      ["name"] = "Test House",
      ["chests"] = {
        [7] = {
          ["capacity"] = 30,
          ["chestNum"] = 1,
          ["slots"] = {
            [1] = {
              ["link"] = "|H1:item:4001:0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:2:0|h[Mock Furnishing^n]|h",
              ["name"] = "Mock Furnishing^n",
              ["qty"] = 1,
              ["quality"] = 2,
              ["filterType"] = 21,
            },
          },
        },
      },
    },
  },
  ["guildBanks"] = {
    ["Test Guild"] = {
      ["slots"] = {
        [1] = {
          ["link"] = "|H1:item:6001:0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1:0|h[Mock Guild Item^n]|h",
          ["name"] = "Mock Guild Item^n",
          ["qty"] = 2,
          ["quality"] = 1,
          ["filterType"] = 5,
        },
      },
    },
  },
  ["achievements"] = {
    ["totalPts"] = 50,
    ["earnedPts"] = 10,
    ["lastUpdate"] = 1700000020,
    ["categories"] = {
      [1] = {
        ["name"] = "General",
        ["icon"] = "/esoui/art/treeicons/achievements_indexicon_general_up.dds",
        ["total"] = 2,
        ["complete"] = 1,
        ["totalPts"] = 50,
        ["earnedPts"] = 10,
        ["numAchievements"] = 2,
        ["subcats"] = {
          [1] = {
            ["name"] = "Testing",
            ["total"] = 2,
            ["complete"] = 1,
            ["totalPts"] = 50,
            ["earnedPts"] = 10,
            ["numAchievements"] = 2,
          },
        },
      },
    },
    ["account"] = {
      [9000] = {
        ["name"] = "Mock Account Achievement",
        ["desc"] = "Account wide test achievement.",
        ["cat"] = "General",
        ["subcat"] = "Testing",
        ["points"] = 5,
        ["complete"] = true,
        ["completionTimestamp"] = 1700000005,
        ["completionDate"] = "2023-11-14",
        ["persistenceLevel"] = 0,
        ["criteria"] = {},
        ["lineBaseId"] = 8999,
        ["linePreviousId"] = 8999,
        ["lineNextId"] = 0,
        ["rewards"] = {
          [1] = { ["type"] = "title", ["name"] = "Mock Title", ["id"] = 7 },
          [2] = { ["type"] = "tribute_card_upgrade", ["patronId"] = 1, ["cardIndex"] = 2 },
        },
      },
    },
  },
  ["uiColors"] = {
    ["textNormal"] = "C5C29E",
    ["xpStart"] = "not-a-colour",
  },
  ["stickerbook"] = {
    ["lastUpdate"] = 1700000030,
    ["categoryIcons"] = {
      ["Dungeons"] = "/esoui/art/collections/collections_categoryicon_dungeons_up.dds",
    },
    ["sets"] = {
      [500] = {
        ["name"] = "Mock Set",
        ["category"] = "Dungeons",
        ["subcategory"] = "Test Dungeon",
        ["numCollected"] = 1,
        ["numTotal"] = 2,
        ["reconCurrency"] = 5,
        ["reconCost"] = 25,
        ["pieces"] = {
          [1] = {
            ["id"] = 42,
            ["quality"] = 4,
            ["filterType"] = 6,
            ["collected"] = true,
            ["name"] = "Mock Sword",
            ["icon"] = "/esoui/art/icons/gear_mock_1hsword_a.dds",
          },
          [2] = {
            ["filterType"] = 3,
            ["collected"] = false,
            ["name"] = "Mock Cuirass",
          },
        },
      },
    },
  },
}
