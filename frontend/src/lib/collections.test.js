import { test } from 'node:test';
import assert from 'node:assert/strict';
import { categorySummary, totals, sections, searchSets, pieceSource, pieceIcon, subSummary, gridSets, emptyGridFilters } from './collections.js';
import { gameIcon } from './achievements.js';

const SETS = [
  { name: 'Mara', category: 'Cyrodiil', subcategory: '', numCollected: 3, numTotal: 10 },
  { name: 'Brace', category: 'Dungeons', subcategory: "Scrivener's Hall", numCollected: 11, numTotal: 22 },
  { name: 'Alpha', category: 'Dungeons', subcategory: 'Arx', numCollected: 1, numTotal: 2 },
  { name: 'Loose', category: 'Dungeons', subcategory: '', numCollected: 0, numTotal: 5 },
];

test('category summary and totals', () => {
  assert.deepEqual(categorySummary(SETS), [
    { name: 'Cyrodiil', collected: 3, total: 10 },
    { name: 'Dungeons', collected: 12, total: 29 },
  ]);
  assert.deepEqual(totals(SETS), { collected: 15, total: 39 });
});

test('sections: loose sets first, then subcategories A-Z', () => {
  assert.deepEqual(sections(SETS, 'Dungeons').map((g) => [g.heading, g.sets.map((s) => s.name)]), [
    ['', ['Loose']],
    ['Arx', ['Alpha']],
    ["Scrivener's Hall", ['Brace']],
  ]);
});

test('search is case-insensitive and empty for blank queries', () => {
  assert.deepEqual(searchSets(SETS, 'BR').map((s) => s.name), ['Brace']);
  assert.deepEqual(searchSets(SETS, '  '), []);
});

const piece = (filterType, collected, name) => ({ filterType, collected, name });
const GRID = [
  { name: 'Warlock', category: 'Dungeons', subcategory: 'Arx', numCollected: 1, numTotal: 3, pieces: [piece(1, true, 'Hat of the Warlock'), piece(6, false, 'Dagger of the Warlock'), piece(5, false, 'Ring of the Warlock')] },
  { name: 'Done', category: 'Dungeons', subcategory: '', numCollected: 2, numTotal: 2, pieces: [piece(3, true, 'Done Cuirass'), piece(11, true, 'Done Bow')] },
  { name: 'Far', category: 'Trials', subcategory: 'Sanctum', numCollected: 0, numTotal: 1, pieces: [piece(8, false, 'Far Greatsword')] },
];
const g = (o) => ({ ...emptyGridFilters(), ...o });
const show = (rows) => rows.map((r) => `${r.set.name}:${r.pieces.length}`);

test('grid scope, type filters, locked pieces and completion', () => {
  assert.deepEqual(show(gridSets(GRID, 'Dungeons', null, g({}))), ['Warlock:3', 'Done:2']);
  assert.deepEqual(show(gridSets(GRID, 'Dungeons', 'Arx', g({}))), ['Warlock:3']);
  assert.deepEqual(show(gridSets(GRID, 'Dungeons', '', g({}))), ['Done:2']);
  assert.deepEqual(show(gridSets(GRID, 'Dungeons', null, g({ weapons: ['6', '11'] }))), ['Warlock:1', 'Done:1']);
  assert.deepEqual(show(gridSets(GRID, 'Dungeons', null, g({ apparel: ['5'] }))), ['Warlock:1']);
  assert.deepEqual(show(gridSets(GRID, 'Dungeons', null, g({ showLocked: false }))), ['Warlock:1', 'Done:2']);
  assert.deepEqual(show(gridSets(GRID, 'Dungeons', null, g({ completion: 'near' }))), ['Warlock:3']);
  assert.deepEqual(show(gridSets(GRID, 'Dungeons', null, g({ completion: 'complete' }))), ['Done:2']);
  assert.deepEqual(show(gridSets(GRID, null, null, g({ completion: 'untouched', search: 'great' }))), ['Far:1']); // search spans categories and piece names
});

test('piece icons fall back to slot silhouettes', () => {
  assert.equal(pieceIcon({ icon: '/esoui/art/icons/gear_x.dds', filterType: 1 }, gameIcon), '/esoicons/gear_x.png');
  assert.equal(pieceIcon({ filterType: 2, name: 'Arm Cops of the Bear' }, gameIcon), '/assets/interface/gearslot_shoulders.png');
  assert.equal(pieceIcon({ filterType: 1, name: 'Robe of Stuff' }, gameIcon), '/assets/interface/gearslot_chest.png');
  assert.equal(pieceIcon({ filterType: 5, name: 'Ring' }, gameIcon), '/assets/interface/gearslot_ring.png');
  assert.equal(pieceIcon({ filterType: 7, name: 'Shield' }, gameIcon), '/assets/interface/gearslot_offhand.png');
  assert.equal(pieceIcon({ filterType: 10, name: 'Staff' }, gameIcon), '/assets/interface/gearslot_mainhand.png');
});

test('subcategory summary', () => {
  assert.deepEqual(subSummary(GRID, 'Dungeons'), [{ name: '', collected: 2, total: 2 }, { name: 'Arx', collected: 1, total: 3 }]);
});

test('piece source and whether TTC prices apply', () => {
  assert.deepEqual(pieceSource({ category: 'Dungeons', subcategory: 'Arx' }), { where: 'Dungeons › Arx', kind: 'Dungeon', priced: false });
  assert.deepEqual(pieceSource({ category: 'Overland', subcategory: '' }), { where: 'Overland', kind: '', priced: true });
});

test('collectible books: categories by tab, items by category, search, show filter and hidesLocked', async () => {
  const { bookCategories, bookItems } = await import('./collections.js');
  const col = {
    categories: [
      { idx: 1, name: 'Mounts', specialization: 0, hidesLocked: false },
      { idx: 2, name: 'Upgrade', specialization: 0, hidesLocked: true },
      { idx: 3, name: 'Armor Styles', specialization: 3, hidesLocked: false },
    ],
    items: [
      { id: 10, name: 'Horse', cat: 1, sub: 1, unlocked: true },
      { id: 11, name: 'Bear', cat: 1, sub: 1, unlocked: false },
      { id: 12, name: 'Camel', cat: 1, sub: 0, unlocked: false },
      { id: 13, name: 'Bag Space', cat: 2, sub: 0, unlocked: false },
      { id: 14, name: 'Horse Helm', cat: 3, sub: 2, unlocked: true },
    ],
  };
  const cats = bookCategories(col, 0);
  assert.deepEqual(cats.map((c) => c.name), ['Mounts', 'Upgrade']);
  const ids = (/** @type {any} */ at, f = {}) => bookItems(col, cats, at, { search: '', show: 'all', ...f }).map((i) => i.id);
  assert.deepEqual(ids({ cat: 1, sub: 1 }), [10, 11]);
  assert.deepEqual(ids({ cat: 1, sub: null }), [12]); // sub 0: directly under the category
  assert.deepEqual(ids({ cat: 1, sub: 1 }, { show: 'locked' }), [11]);
  assert.deepEqual(ids({ cat: 1, sub: 1 }, { show: 'unlocked' }), [10]);
  assert.deepEqual(ids({ cat: 2, sub: null }), []); // hidesLocked
  assert.deepEqual(ids({ cat: null, sub: null }, { search: 'horse' }), [10]); // search stays inside this tab
});
