import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseHash, toHash } from './route.js';

test('hash round-trip', () => {
  assert.deepEqual(parseHash(''), { tab: 'characters', charId: null, charView: 'sheet' });
  assert.deepEqual(parseHash('#/inventory'), { tab: 'inventory', charId: null, charView: 'sheet' });
  assert.deepEqual(parseHash('#/characters/char%20a'), { tab: 'characters', charId: 'char a', charView: 'sheet' });
  assert.deepEqual(parseHash('#/characters/c1/bags'), { tab: 'characters', charId: 'c1', charView: 'bags' });
  assert.deepEqual(parseHash('#/characters/c1/nope'), { tab: 'characters', charId: 'c1', charView: 'sheet' });
  assert.deepEqual(parseHash('#/nope/x'), { tab: 'characters', charId: null, charView: 'sheet' });
  assert.equal(toHash('characters', 'char a'), '#/characters/char%20a');
  assert.equal(toHash('characters', 'c1', 'wardrobe'), '#/characters/c1/wardrobe');
  assert.equal(toHash('inventory', 'ignored', 'bags'), '#/inventory');
});
