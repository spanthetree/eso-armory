import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildIndex, achievementsIn, extraSubcats, pct, achievementIcon } from './achievements.js';

const DATA = {
  account_items: [
    { id: 1, name: 'Dungeon Delver', desc: 'Clear a dungeon', cat: 'Dungeons', subcat: 'Base', complete: false },
    { id: 2, name: 'Account Thing', desc: '', cat: 'Dungeons', subcat: 'Base', complete: true },
  ],
  items_by_char: {
    c1: [
      { id: 1, name: 'Dungeon Delver', desc: 'Clear a dungeon', cat: 'Dungeons', subcat: 'Base', complete: true },
      { id: 3, name: 'Solo Hero', desc: 'Alone', cat: 'Dungeons', subcat: 'Base', complete: false },
    ],
  },
};

test('merges account and character items; the character copy wins', () => {
  const idx = buildIndex(DATA);
  const list = achievementsIn(idx, 'Dungeons', 'Base', 'c1');
  assert.deepEqual(list.map((a) => a.id), [1, 2, 3]);
  assert.equal(list[0].complete, true);
  assert.deepEqual(achievementsIn(idx, 'Dungeons', 'Base', 'nobody').map((a) => a.id), [1, 2]);
  assert.deepEqual(achievementsIn(idx, 'Dungeons', 'Other', 'c1'), []);
});

test('search matches name or description', () => {
  const idx = buildIndex(DATA);
  assert.deepEqual(achievementsIn(idx, 'Dungeons', 'Base', 'c1', 'ALONE').map((a) => a.id), [3]);
});

test('pct and icon paths', () => {
  assert.equal(pct(15, 1065), 1);
  assert.equal(pct(0, 0), 0);
  assert.equal(achievementIcon('/esoui/art/icons/achievement_vengeance_25.dds'), '/esoicons/achievement_vengeance_25.png');
  assert.equal(achievementIcon('/esoui/art/other/thing.dds'), null);
  assert.equal(achievementIcon(''), null);
});

test('extraSubcats surfaces achievements filed under unlisted subcategories', () => {
  const idx = buildIndex({
    account_items: [],
    items_by_char: { c1: [
      { id: 7, cat: 'Dungeons', subcat: 'Group Dungeons', points: 10, complete: true },
      { id: 8, cat: 'Dungeons', subcat: 'Group Dungeons', points: 5, complete: false },
      { id: 9, cat: 'Dungeons', subcat: 'Arx Corinium', points: 5, complete: false },
    ] },
  });
  const extra = extraSubcats(idx, { name: 'Dungeons', subcats: [{ name: 'Arx Corinium' }] }, 'c1');
  assert.deepEqual(extra, [{ name: 'Group Dungeons', key: 'Group Dungeons', total: 2, complete: 1, totalPts: 15, earnedPts: 10 }]);
});
