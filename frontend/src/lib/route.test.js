import { test } from 'node:test';
import assert from 'node:assert/strict';

import { parseHash, toHash } from './route.js';

test('hash round-trip', () => {
  assert.deepEqual(parseHash(''), { tab: 'characters', charId: null });
  assert.deepEqual(parseHash('#/inventory'), { tab: 'inventory', charId: null });
  assert.deepEqual(parseHash('#/characters/char%20a'), { tab: 'characters', charId: 'char a' });
  assert.deepEqual(parseHash('#/nope/x'), { tab: 'characters', charId: null });
  assert.equal(toHash('characters', 'char a'), '#/characters/char%20a');
  assert.equal(toHash('inventory', 'ignored'), '#/inventory');
});
