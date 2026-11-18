import { test } from 'node:test';
import assert from 'node:assert/strict';
import { gearSig, importedGearItem, setSource, missingItems, superstarRows } from './compare.js';

const ITEMS = [
  { item_id: 10, trait_id: 18, enchant_id: 0, name: 'Robe of Ruin', trait_name: 'Divines', quality: 5, quality_color: '#c29300', filter_type: 2, locations: [{ bag_id: 2, location_label: 'Bank' }] },
  { item_id: 20, trait_id: 3, enchant_id: 7, name: 'Sword', trait_name: 'Precise', is_crafted: true, locations: [{ bag_id: 0, location_label: 'Seryn' }] },
];
const SETS = [
  { name: 'Ruin', category: 'Dungeons', subcategory: 'Arx Corinium' },
  { name: 'Mara', category: 'Cyrodiil', subcategory: '' },
];

test('gear signature and imported item fallbacks', () => {
  assert.equal(gearSig({ item_id: 10, trait_id: 18 }), '10:18:0');
  const it = importedGearItem({ slot: 2, item_id: 10, trait_id: 99, link_name: '' }, ITEMS);
  assert.equal(it.name, 'Robe of Ruin'); // same base item, different trait
  assert.equal(it.quality_color, '#c29300');
  assert.equal(importedGearItem({ slot: 11, item_id: 5 }, []).filter_type, 25);
});

test('set source flags drops', () => {
  assert.deepEqual(setSource('Ruin', SETS), { text: 'Source: Dungeons / Arx Corinium', dungeon: true, trial: false, arena: false });
  assert.equal(setSource('Nope', SETS).text, 'Source: Nope');
});

test('missing items skip owned rolls and price only buyable gear', () => {
  const gear = [
    { slot: 2, item_id: 10, trait_id: 18, enchant_id: 0, set_name: 'Ruin', link_name: 'Robe of Ruin' }, // owned
    { slot: 3, item_id: 11, set_name: 'Ruin', link_name: 'Ruin Pauldron' }, // dungeon drop
    { slot: 4, item_id: 20, trait_id: 1, set_name: 'Mara', link_name: 'Sword' }, // crafted id
    { slot: 1, item_id: 30, set_name: 'Mara', link_name: 'Mara Necklace' }, // buyable
  ];
  const m = missingItems(gear, ITEMS, SETS);
  assert.deepEqual(m.map((x) => [x.name, x.priced, x.crafted, x.dropLabel]), [
    ['Ruin Pauldron', false, false, 'Dungeon'],
    ['Sword', false, true, ''],
    ['Mara Necklace', true, false, ''],
  ]);
});

test('superstar rows', () => {
  const worn = { 4: { name: 'Sword', trait_name: 'Precise' } };
  const rows = superstarRows(
    [
      { slot: 'Main Hand', slot_id: 4, item_name: 'Sword', trait: 'Precise' },
      { slot: 'Chest', slot_id: 2, item_name: 'Robe of Ruin', trait: 'Infused' },
      { slot: 'Neck', slot_id: 1, item_name: 'Unknown Amulet', trait: '' },
      { slot: 'Ring', slot_id: 11, item_name: '' },
    ],
    worn,
    ITEMS,
  );
  assert.deepEqual(rows.map((r) => r.status), ['equipped', 'wrong_trait', 'missing', 'na']);
  assert.equal(rows[0].statusLabel, '✓ Equipped on Seryn');
  assert.equal(rows[1].statusLabel, '⚠ Bank (Divines)');
  assert.equal(rows[0].curTraitMatch, true);
});
