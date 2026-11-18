import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseHash, toHash } from './route.js';

test('hash round-trip', () => {
  assert.deepEqual(parseHash(''), { tab: 'characters', charId: null, charView: 'sheet', book: null });
  assert.deepEqual(parseHash('#/inventory'), { tab: 'inventory', charId: null, charView: 'sheet', book: null });
  assert.deepEqual(parseHash('#/characters/char%20a'), { tab: 'characters', charId: 'char a', charView: 'sheet', book: null });
  assert.deepEqual(parseHash('#/characters/c1/bags'), { tab: 'characters', charId: 'c1', charView: 'bags', book: null });
  assert.deepEqual(parseHash('#/characters/c1/nope'), { tab: 'characters', charId: 'c1', charView: 'sheet', book: null });
  assert.deepEqual(parseHash('#/nope/x'), { tab: 'characters', charId: null, charView: 'sheet', book: null });
  assert.equal(toHash('characters', 'char a'), '#/characters/char%20a');
  assert.equal(toHash('characters', 'c1', 'wardrobe'), '#/characters/c1/wardrobe');
  assert.equal(toHash('inventory', 'ignored', 'bags'), '#/inventory');
  assert.equal(parseHash('#/collections/housing').book, 'housing');
  assert.equal(parseHash('#/collections/nope').book, null);
  assert.equal(toHash('collections', null, 'sheet', 'sets'), '#/collections/sets');
  assert.equal(toHash('collections'), '#/collections');
  assert.equal(parseHash('#/tome/endeavors').book, 'endeavors');
  assert.equal(parseHash('#/achievements/antiquities').book, 'antiquities');
  assert.equal(parseHash('#/tome/antiquities').book, null); // another tab's book
  assert.equal(toHash('tome', null, 'sheet', 'pursuits'), '#/tome/pursuits');
  assert.equal(parseHash('#/characters/c1/crafting').charView, 'crafting');
});
