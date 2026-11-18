// App-wide state and loaders. Ported from the Alpine armory() init/fetch*/connectSSE.
// Holds raw API payloads; tab-specific indexing lives with each tab.
import * as api from './api.js';

/**
 * One API payload. `value` is raw state: payloads are replaced, never edited, so they skip Svelte's
 * deep proxies (wrapping ~30k achievement objects froze the page).
 */
class Resource {
  value = $state.raw(/** @type {any} */ (null));
  loading = $state(false);
  error = $state(/** @type {string | null} */ (null));
}

const resource = () => new Resource();

export const app = $state({
  ready: false,
  /** Server unreachable or answering 503 during startup (e.g. a cold start). */
  waking: false,
  status: { isAdmin: false, hasServerKey: false, hasSessionKey: false },
  shareCode: api.session.share,
  workspace: { primary: { account: null }, shadow: { account: null }, activeSlot: 'primary', activeAccount: null },
  /** Last data mtime seen (ETag of /api/data); used by manual refresh. */
  mtime: /** @type {number | null} */ (null),
  live: false,

  data: resource(),
  builds: resource(),
  wwBuilds: resource(),
  compare: resource(),
  achievements: resource(),
  stickerbook: resource(),
  abilityIcons: /** @type {Record<string, string>} */ ({}),
  auth: /** @type {{ has_password?: boolean, account_name?: string | null }} */ ({}),

  toast: { msg: '', seq: 0 },
});

/** @param {string} msg */
export function toast(msg) {
  app.toast = { msg, seq: app.toast.seq + 1 };
}

/**
 * Fill a resource from a GET. With `quiet503`, a 503 means "nothing uploaded yet":
 * value becomes null and no error is shown.
 * @param {Resource<any>} res
 * @param {string} path
 * @param {string} label
 * @param {{ quiet503?: boolean, silent?: boolean }} [o] silent keeps the old value visible while reloading
 */
async function load(res, path, label, { quiet503 = false, silent = false } = {}) {
  if (!silent) res.loading = true;
  try {
    res.value = await api.get(path, { label });
    res.error = null;
  } catch (e) {
    const err = /** @type {api.ApiError} */ (e);
    res.value = null;
    res.error = quiet503 && err.status === 503 ? null : err.message || `${label} request failed`;
  } finally {
    res.loading = false;
  }
}

export async function loadData(silent = false) {
  if (!silent) app.data.loading = true;
  try {
    const r = await fetch(api.url('/api/data'));
    const etag = r.headers.get('ETag');
    app.data.value = await api.readJson(r, 'Data');
    app.data.error = null;
    if (etag) app.mtime = parseFloat(etag);
    const account = app.data.value?.meta?.account;
    if (account) app.workspace.activeAccount = account;
  } catch (e) {
    const err = /** @type {api.ApiError} */ (e);
    app.data.value = null;
    app.data.error = err.status === 503 ? null : err.message;
  } finally {
    app.data.loading = false;
  }
}

export const loadBuilds = () => load(app.builds, '/api/builds', 'Builds', { quiet503: true });
export const loadWWBuilds = () => load(app.wwBuilds, '/api/ww_builds', "Wizard's Wardrobe", { quiet503: true });
export const loadCompare = () => load(app.compare, '/api/compare_builds', 'Compare builds', { quiet503: true });
export const loadAchievements = (silent = false) => load(app.achievements, '/api/achievements', 'Achievements', { silent });
export const loadStickerbook = (silent = false) => load(app.stickerbook, '/api/stickerbook', 'Collections', { silent });

export async function loadWorkspace() {
  try {
    setWorkspace(await api.get('/api/workspace', { label: 'Workspace' }));
  } catch {
    // no workspace yet
  }
}

async function loadAbilityIcons() {
  try {
    app.abilityIcons = await api.get('/api/ability_icons', { label: 'Ability icons' });
  } catch {
    // icons are optional
  }
}

/** Reload everything that changes when new SavedVariables arrive. */
export async function reloadUserData() {
  await Promise.all([loadData(true), loadAchievements(true), loadStickerbook(true)]);
}

export async function loadAuth() {
  try {
    app.auth = await api.get('/api/auth/status', { label: 'Account' });
  } catch {
    // not logged in / no account yet
  }
}

export async function loadAll() {
  await Promise.all([
    loadWorkspace(), loadData(), loadBuilds(), loadWWBuilds(), loadCompare(),
    loadAbilityIcons(), loadAchievements(), loadStickerbook(), loadAuth(),
  ]);
}

/** Everything that belongs to the active workspace slot. */
async function reloadWorkspaceData() {
  await Promise.all([loadData(true), loadBuilds(), loadWWBuilds(), loadCompare(), loadAchievements(), loadStickerbook(), loadAuth()]);
}

/** @param {any} d */
function setWorkspace(d) {
  app.workspace = {
    primary: d.primary || { account: null },
    shadow: d.shadow || { account: null },
    activeSlot: d.activeSlot || 'primary',
    activeAccount: d.activeAccount || null,
  };
}

/** @param {'primary' | 'shadow'} slot */
export async function switchSlot(slot) {
  if (slot === app.workspace.activeSlot) return;
  try {
    setWorkspace(await api.post('/api/workspace/slot', { label: 'Workspace switch', params: { slot }, share: false }));
    await reloadWorkspaceData();
    toast(`Viewing ${slot} workspace`);
  } catch (e) {
    toast(/** @type {Error} */ (e).message || 'Workspace switch failed');
  }
}

export async function deleteShadow() {
  try {
    setWorkspace(await api.del('/api/workspace/shadow', { label: 'Remove alt', share: false }));
    await reloadWorkspaceData();
    toast('Alt account removed');
  } catch (e) {
    toast(/** @type {Error} */ (e).message || 'Delete failed');
  }
}

// ── account ─────────────────────────────────────────────

const jsonInit = (/** @type {any} */ body) => ({ headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

/** Log in to an existing account from another device. Throws with the server's message. */
export async function login(/** @type {string} */ name, /** @type {string} */ password) {
  await api.post('/api/auth/login', { label: 'Login', share: false, init: jsonInit({ account_name: name.trim(), password }) });
  await loadAll();
  toast('Logged in');
}

/** Forget this browser and reload to the Welcome screen. */
export async function logout() {
  const warn = app.auth.account_name && !app.auth.has_password
    ? `${app.auth.account_name} has no password. After logging out you can't open it again until you upload it again. Log out?`
    : 'Log out of this browser?';
  if (!confirm(warn)) return;
  try {
    await api.post('/api/auth/logout', { label: 'Logout', share: false });
  } catch (e) {
    return toast(/** @type {Error} */ (e).message);
  }
  api.forgetSession();
  location.replace(location.pathname);
}

/** Set or change the account password. Throws with the server's message. */
export async function setPassword(/** @type {string} */ password) {
  await api.post('/api/auth/set_password', { label: 'Password', init: jsonInit({ password }) });
  await loadAuth();
  toast('Password saved');
}

// ── startup ─────────────────────────────────────────────

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Poll /api/status until the server answers with something other than 503 (cold starts). */
async function waitForServer() {
  for (;;) {
    try {
      const r = await fetch(api.url('/api/status', {}, { share: false }), { signal: AbortSignal.timeout(6000) });
      if (r.status !== 503) {
        const st = await r.json().catch(() => ({}));
        app.status = {
          isAdmin: !!st.is_admin,
          hasServerKey: !!st.has_server_api_key,
          hasSessionKey: !!st.has_session_api_key,
        };
        app.waking = false;
        return;
      }
    } catch {
      // not up yet
    }
    app.waking = true;
    await sleep(3000);
  }
}

export async function start() {
  const fromUrl = new URLSearchParams(location.search).has('share');
  await waitForServer();
  if (app.shareCode) {
    try {
      if (!(await joinShare(app.shareCode, { quiet: true }))) leaveShare({ quiet: true, removeUrl: fromUrl });
    } catch {
      leaveShare({ quiet: true, removeUrl: fromUrl });
    }
  }
  await loadAll();
  app.ready = true;
  connectLive();
}

// ── sharing ─────────────────────────────────────────────

/** @param {string} code */
function setShare(code) {
  app.shareCode = code;
  api.setShareCode(code);
}

/**
 * Join a shared workspace. Returns the normalized code, or '' for an invalid code.
 * @param {string} code
 * @param {{ quiet?: boolean }} [o] quiet: validation only (startup), no reload or toast
 */
export async function joinShare(code, { quiet = false } = {}) {
  const normalized = api.normalizeShareCode(code);
  if (!normalized) return '';
  const d = await api.post('/api/share/join', { label: 'Join', params: { code: normalized }, share: false });
  const joined = api.normalizeShareCode(d.code || normalized);
  if (joined) setShare(joined);
  if (joined && !quiet) {
    connectLive();
    await loadAll();
    toast('Joined shared workspace');
  }
  return joined;
}

/** Create (or fetch) the share code for the current workspace. */
export async function createShare() {
  const d = await api.post('/api/share', { label: 'Share' });
  const code = api.normalizeShareCode(d.code);
  if (!code) throw new Error('Share code unavailable');
  setShare(code);
  connectLive();
  toast('Workspace shared');
  return code;
}

/** @param {{ quiet?: boolean, removeUrl?: boolean }} [o] */
export function leaveShare({ quiet = false, removeUrl = false } = {}) {
  setShare('');
  if (removeUrl) {
    const u = new URL(location.href);
    u.searchParams.delete('share');
    history.replaceState({}, '', u);
  }
  if (app.ready) {
    connectLive();
    loadAll();
  }
  if (!quiet) toast('Workspace sharing cleared');
}

/** @param {string} [code] */
export function shareLink(code = app.shareCode) {
  if (!code) return '';
  const u = new URL(location.href);
  u.searchParams.set('share', code);
  return u.toString();
}

// ── live updates (SSE) ──────────────────────────────────

/** @type {EventSource | null} */
let es = null;
/** @type {ReturnType<typeof setTimeout> | undefined} */
let retry;
let generation = 0;

/** (Re)connect to /events. The server sends "reload" when this workspace's data changes. */
export function connectLive() {
  es?.close();
  clearTimeout(retry);
  const gen = ++generation;
  const source = new EventSource(api.url('/events'));
  es = source;
  source.onopen = () => (app.live = true);
  source.onmessage = (e) => {
    if (e.data === 'reload') reloadUserData().then(() => toast('Data updated'));
  };
  source.onerror = () => {
    source.close();
    if (es === source) es = null;
    app.live = false;
    retry = setTimeout(() => gen === generation && connectLive(), 5000);
  };
}

/** Manual refresh: reload only if the server's data is newer than what we have. */
export async function refresh() {
  try {
    const st = await api.get('/api/status', { label: 'Status' });
    if (st.ok && st.last_modified && st.last_modified !== app.mtime) {
      await reloadUserData();
      toast('Data updated');
    } else {
      toast('No updates');
    }
  } catch {
    toast('Refresh failed');
  }
}

// ── build compare / SuperStar ───────────────────────────

/** Export a character's current build; returns its share code (ABCD-EFGH). @param {string} charId */
export async function exportBuild(charId) {
  const d = await api.post('/api/build_export', { label: 'Build export', params: { character_id: charId } });
  return /** @type {string} */ (d.code);
}

/** Import a build by code as this character's comparison target. @param {string} charId @param {string} code */
export async function importCompare(charId, code) {
  await api.post('/api/compare_builds/import', { label: 'Compare import', params: { character_id: charId, code: code.trim().toUpperCase() } });
  await loadCompare();
}

/** @param {string} charId */
export async function deleteCompare(charId) {
  await api.del('/api/compare_builds', { label: 'Compare delete', params: { character_id: charId } });
  await loadCompare();
}

/** Save an Anthropic API key for this browser session (used to read SuperStar screenshots). @param {string} key */
export async function saveApiKey(key) {
  await api.post('/api/session/apikey', { label: 'API key', init: { body: new URLSearchParams({ api_key: key }) } });
  app.status.hasSessionKey = true;
}

export async function deleteApiKey() {
  try {
    await api.del('/api/session/apikey', { label: 'API key' });
  } finally {
    app.status.hasSessionKey = false;
  }
}

/** Read a SuperStar build screenshot into { character, mundus, gear: [...] }. @param {File} file */
export async function parseSuperstar(file) {
  const body = new FormData();
  body.append('image', file, file.name || 'screenshot.png');
  return api.post('/api/parse_superstar', { label: 'Screenshot parsing', init: { body } });
}
