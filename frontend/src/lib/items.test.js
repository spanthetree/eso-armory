import { test } from 'node:test';
import assert from 'node:assert/strict';
import { forCharacter, filterItems, sortItems, displayRows, emptyFilters, hasFilters, duplicateNames, withValues, summarize, applyPreset, isPreset, PRESETS } from './items.js';

const loc = (type, key, bag, quantity = 1) => ({ location_type: type, location_key: key, bag_id: bag, quantity });
const ITEMS = [
  { key: 'a', name: 'Sword of Ruin', quality: 4, filter_type: 1, trait_id: 3, set_name: 'Ruin', is_crafted: true, total_quantity: 3, locations: [loc('character', 'c1', 0), loc('bank', 'bank', 0, 2)] },
  { key: 'b', name: 'Potion', quality: 1, filter_type: 3, trait_id: 0, set_name: '', total_quantity: 10, locations: [loc('character', 'c1', 1, 4), loc('character', 'c2', 1, 6)] },
  { key: 'c', name: 'Robe of Ruin', quality: 5, filter_type: 2, trait_id: 18, set_name: 'Ruin', is_transmuted: true, total_quantity: 1, locations: [loc('character', 'c2', 0)] },
];
const f = (o) => ({ ...emptyFilters(), ...o });
const names = (list) => list.map((i) => i.name);

test('forCharacter narrows locations and quantity to that character', () => {
  const c1 = forCharacter(ITEMS, 'c1');
  assert.deepEqual(names(c1), ['Sword of Ruin', 'Potion']);
  assert.equal(c1[1].total_quantity, 4);
  assert.equal(c1[1].key, 'b::c1');
});

test('filters combine', () => {
  assert.deepEqual(names(filterItems(ITEMS, f({ search: 'RUIN' }))), ['Sword of Ruin', 'Robe of Ruin']);
  assert.deepEqual(names(filterItems(ITEMS, f({ quality: '5' }))), ['Robe of Ruin']);
  assert.deepEqual(names(filterItems(ITEMS, f({ types: ['1', '3'] }))), ['Sword of Ruin', 'Potion']);
  assert.deepEqual(names(filterItems(ITEMS, f({ traits: ['any'] }))), ['Sword of Ruin', 'Robe of Ruin']);
  assert.deepEqual(names(filterItems(ITEMS, f({ traits: ['18'] }))), ['Robe of Ruin']);
  assert.deepEqual(names(filterItems(ITEMS, f({ transmuted: true }))), ['Robe of Ruin']);
  assert.deepEqual(names(filterItems(ITEMS, f({ crafted: true }))), ['Sword of Ruin']);
  assert.deepEqual(names(filterItems(ITEMS, f({ locTypes: ['bank'] }))), ['Sword of Ruin']);
  // bag and character must match on the same location
  assert.deepEqual(names(filterItems(ITEMS, f({ chars: ['c2'], bags: ['0'] }))), ['Robe of Ruin']);
});

test('hasFilters ignores whitespace-only search', () => {
  assert.equal(hasFilters(f({ search: '  ' })), false);
  assert.equal(hasFilters(f({ bags: ['1'] })), true);
});

test('sort by string and number', () => {
  assert.deepEqual(names(sortItems(ITEMS, 'name', 'asc')), ['Potion', 'Robe of Ruin', 'Sword of Ruin']);
  assert.deepEqual(names(sortItems(ITEMS, 'total_quantity', 'desc')), ['Potion', 'Sword of Ruin', 'Robe of Ruin']);
});

test('group by set puts No Set last', () => {
  const rows = displayRows(ITEMS, 'set');
  assert.deepEqual(rows.map((r) => (r.t === 'h' ? `#${r.set}:${r.count}` : r.item.key)), ['#Ruin:2', 'a', 'c', '#No Set:1', 'b']);
  assert.equal(displayRows(ITEMS, '').length, 3);
});

const GEAR = [
  ...ITEMS,
  { key: 'd', name: 'Robe of Ruin', quality: 4, filter_type: 2, trait_id: 11, set_name: 'Ruin', is_bound: true, total_quantity: 1, locations: [loc('bank', 'bank', 0)] },
];

test('duplicates are gear held more than once by name', () => {
  assert.deepEqual([...duplicateNames(GEAR)], ['Sword of Ruin', 'Robe of Ruin']); // Sword x3; Robe twice; Potion is not gear
  assert.deepEqual(names(filterItems(GEAR, f({ dupes: true }))), ['Sword of Ruin', 'Robe of Ruin', 'Robe of Ruin']);
  assert.deepEqual(names(filterItems(GEAR, f({ unbound: true, hasSet: true }))), ['Sword of Ruin', 'Robe of Ruin']);
});

test('values skip bound and unpriced items; summary splits by type and location', () => {
  const v = withValues(GEAR, { 'sword of ruin': 100, 'robe of ruin': 50 });
  assert.deepEqual(v.map((i) => i.value), [300, null, 50, null]);
  const s = summarize(v);
  assert.equal(s.value, 350);
  assert.deepEqual(s.types['2'], { count: 2, value: 50 });
  assert.deepEqual(s.locs.bank, { count: 2, value: 200 });
  assert.deepEqual(s.locs.character, { count: 3, value: 150 });
  assert.deepEqual(names(sortItems(v, 'value', 'asc')), ['Robe of Ruin', 'Sword of Ruin', 'Potion', 'Robe of Ruin']);
});

test('presets apply over empty filters and are recognised', () => {
  const p = PRESETS[1].f;
  const applied = applyPreset(p);
  assert.equal(isPreset(applied, p), true);
  applied.types.push('3');
  assert.equal(isPreset(applied, p), false);
  assert.deepEqual(p.types, ['1', '2', '25']); // preset not mutated
});

test('a location filter narrows each row to its matching locations', () => {
  const item = { key: 'k', name: 'Soul Gem', filter_type: 4, quality: 1, trait_id: 0, unit: 10, value: 1000, total_quantity: 100,
    locations: [{ location_type: 'bank', location_key: 'Bank', bag_id: 2, quantity: 30 }, { location_type: 'guild_bank', location_key: 'G', bag_id: 3, quantity: 70 }] };
  const f = { ...emptyFilters(), locTypes: ['bank'] };
  const [row] = filterItems([item], f);
  assert.deepEqual(row.locations.map((l) => l.location_type), ['bank']);
  assert.equal(row.total_quantity, 30);
  assert.equal(row.value, 300);
  assert.equal(filterItems([item], emptyFilters())[0], item); // no location filter: untouched
});
