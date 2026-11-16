// Run with: npm test (node --test). Covers the pure helpers; browser-only parts are exercised by Playwright.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';

globalThis.crypto ??= webcrypto;
globalThis.location = { search: '' };
globalThis.localStorage = { getItem: () => null, setItem() {}, removeItem() {} };
const { normalizeShareCode, buildUrl, readJson, ApiError } = await import('./api.js');

test('normalizeShareCode', () => {
  assert.equal(normalizeShareCode('abcd1234'), 'ABCD-1234');
  assert.equal(normalizeShareCode(' ab-cd 12-34 '), 'ABCD-1234');
  assert.equal(normalizeShareCode('ABC'), '');
  assert.equal(normalizeShareCode(null), '');
});

test('buildUrl skips empty params and adds share only when set', () => {
  assert.equal(buildUrl('/api/data', { a: '', b: null, c: 0 }, { session: 's1' }), '/api/data?session=s1&c=0');
  assert.equal(buildUrl('/x', {}, { session: 's1', share: 'ABCD-1234' }), '/x?session=s1&share=ABCD-1234');
});

const res = (body, { status = 200, type = 'application/json' } = {}) =>
  new Response(body, { status, statusText: status === 200 ? 'OK' : 'Error', headers: { 'content-type': type } });

test('readJson returns data', async () => {
  assert.deepEqual(await readJson(res('{"ok":true}'), 'T'), { ok: true });
});

test('readJson keeps HTTP status and server error text', async () => {
  await assert.rejects(readJson(res('{"error":"User data not loaded"}', { status: 503 }), 'T'),
    (e) => e instanceof ApiError && e.status === 503 && e.message === 'User data not loaded');
});

test('readJson hides HTML and broken JSON behind readable messages', async () => {
  await assert.rejects(readJson(res('<html><body>Bad Gateway</body></html>', { status: 502, type: 'text/html' }), 'Upload'),
    /Upload returned 502 Error: <html>/);
  await assert.rejects(readJson(res('{"oops"', {}), 'Upload'), /Upload returned invalid JSON response/);
});
