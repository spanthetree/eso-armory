import { test } from 'node:test';
import assert from 'node:assert/strict';
import { categorySummary, totals, sections, searchSets } from './collections.js';

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
