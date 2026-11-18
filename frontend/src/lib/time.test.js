import { test } from 'node:test';
import assert from 'node:assert/strict';
import { timeLeft } from './time.js';

test('timeLeft counts down days, hours and minutes', () => {
  const now = 1_000_000 * 1000;
  assert.equal(timeLeft(1_000_000 + 3 * 86400 + 4 * 3600 + 59, now), '3d 4h');
  assert.equal(timeLeft(1_000_000 + 5 * 3600 + 12 * 60, now), '5h 12m');
  assert.equal(timeLeft(1_000_000 + 30, now), '1m');
  assert.equal(timeLeft(1_000_000 - 5, now), '');
  assert.equal(timeLeft(0, now), '');
});
