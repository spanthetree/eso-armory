// HTTP layer. Every request carries the browser's session id and, when joined, the share code.
// Storage keys match the Alpine UI so both UIs see the same uploaded workspace.

const SESSION_KEY = 'eso-session-id';
const SHARE_KEY = 'eso-share-code';

/**
 * "abcd1234" / "ABCD-1234" -> "ABCD-1234"; anything else -> "".
 * @param {string | null | undefined} code
 */
export function normalizeShareCode(code) {
  const raw = (code || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
  return raw.length === 8 ? `${raw.slice(0, 4)}-${raw.slice(4)}` : '';
}

/**
 * @param {string} path
 * @param {Record<string, string | number | null | undefined>} params
 * @param {{ session: string, share?: string }} ctx
 */
export function buildUrl(path, params, { session, share }) {
  const qp = new URLSearchParams({ session });
  if (share) qp.set('share', share);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') qp.set(k, String(v));
  }
  return `${path}?${qp}`;
}

/** Error carrying the HTTP status, so callers can treat 503 ("no data yet") specially. */
export class ApiError extends Error {
  /** @param {string} message @param {number} status */
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

/**
 * Parse a JSON response. Turns HTML error pages and parser failures into readable messages
 * instead of leaking raw markup (the UI suite checks for this).
 * @param {Response} r
 * @param {string} label
 */
export async function readJson(r, label) {
  const text = await r.text();
  const trimmed = text.trim();
  const preview = trimmed.replace(/\s+/g, ' ').slice(0, 160);
  const looksJson = (r.headers.get('content-type') || '').includes('application/json') || /^[[{]/.test(trimmed);
  if (!looksJson) throw new ApiError(`${label} returned ${r.status} ${r.statusText}: ${preview || 'non-JSON response'}`.replace(/ +:/, ':'), r.status);
  let data;
  try {
    data = trimmed ? JSON.parse(trimmed) : {};
  } catch {
    throw new ApiError(`${label} returned invalid JSON response: ${preview || 'empty response'}`, r.status);
  }
  if (!r.ok || data?.error) throw new ApiError(data?.error || `${label} failed with HTTP ${r.status}`, r.status);
  return data;
}

// ── browser session ─────────────────────────────────────

function storage(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    return null; // private mode / blocked storage: run without persistence
  }
}

export const session = {
  id: storage(SESSION_KEY) || '',
  share: '',
};
if (!session.id) {
  // randomUUID needs a secure context; plain-http LAN access (e.g. Docker on another host) lacks it.
  session.id = crypto.randomUUID?.() ??
    '10000000-1000-4000-8000-100000000000'.replace(/[018]/g, (c) =>
      (+c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (+c / 4)))).toString(16));
  storage(SESSION_KEY, session.id);
}
session.share = normalizeShareCode(new URLSearchParams(location.search).get('share') || storage(SHARE_KEY));

/** @param {string} code normalized code, or '' to leave the shared workspace */
export function setShareCode(code) {
  session.share = code;
  storage(SHARE_KEY, code || null);
}

/**
 * @param {string} path
 * @param {Record<string, any>} [params]
 * @param {{ share?: boolean }} [opts] share=false omits the share code (session-scoped calls)
 */
export function url(path, params = {}, { share = true } = {}) {
  return buildUrl(path, params, { session: session.id, share: share ? session.share : '' });
}

/**
 * @param {string} path
 * @param {{ label?: string, params?: Record<string, any>, share?: boolean, init?: RequestInit }} [o]
 */
export async function request(path, { label = path, params, share, init } = {}) {
  const r = await fetch(url(path, params, { share }), init);
  return readJson(r, label);
}

export const get = (path, o = {}) => request(path, o);
export const post = (path, o = {}) => request(path, { ...o, init: { method: 'POST', ...o.init } });
export const del = (path, o = {}) => request(path, { ...o, init: { method: 'DELETE', ...o.init } });
