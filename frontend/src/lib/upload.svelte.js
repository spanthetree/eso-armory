// Uploading SavedVariables: picked files, or a watched ESO "live" folder (Chrome/Edge File System Access API).
// Ported from the classic uploadFiles / folder watcher.
import * as api from './api.js';
import { app, toast, loadWorkspace, loadData, loadBuilds, loadWWBuilds, loadCompare, loadAchievements, loadStickerbook, loadAuth, connectLive } from './store.svelte.js';
import { prices, resetAvgPrices } from './lookups.svelte.js';

/** @typedef {{ iasync?: File | null, ww?: File | null, ttc_lookup?: File | null, ttc_price?: File | null }} UploadFiles */

/**
 * POST files to /api/upload and reload whatever they changed. Returns the server's per-file results.
 * @param {UploadFiles} files
 */
export async function uploadFiles(files) {
  const body = new FormData();
  for (const [field, file] of Object.entries(files)) if (file) body.append(field, file);
  if (![...body.keys()].length) return null;
  const d = await api.post('/api/upload', { label: 'Upload', init: { body } });
  await loadWorkspace();
  const tasks = [];
  if (d.iasync?.ok) tasks.push(loadData(true), loadBuilds(), loadAchievements(), loadStickerbook(), loadAuth());
  if (d.ww?.ok) tasks.push(loadWWBuilds());
  if (d.ttc_lookup?.ok || d.ttc_price?.ok) {
    for (const k of Object.keys(prices)) delete prices[k];
    resetAvgPrices();
  }
  if (tasks.length) {
    await Promise.all(tasks);
    await loadCompare();
  }
  // The live-update stream only reaches sessions that had data when it connected; reconnect now that we do.
  if (d.iasync?.ok) connectLive();
  return d;
}

// ── folder watching ─────────────────────────────────────

export const canWatchFolder = typeof window !== 'undefined' && typeof (/** @type {any} */ (window)).showDirectoryPicker === 'function';

const KEYS = /** @type {const} */ (['iasync', 'ww', 'ttcLookup', 'ttcPrice']);
/** @typedef {typeof KEYS[number]} WatchKey */

export const watch = $state({
  /** @type {any} FileSystemDirectoryHandle */
  handle: null,
  /** lastModified of each file we last uploaded */
  lastMod: /** @type {Record<WatchKey, number>} */ ({ iasync: 0, ww: 0, ttcLookup: 0, ttcPrice: 0 }),
  /** when each file was last synced (ms) */
  synced: /** @type {Record<WatchKey, number>} */ ({ iasync: 0, ww: 0, ttcLookup: 0, ttcPrice: 0 }),
  checked: 0,
});

/** Where each file lives under the live folder, and the upload field it goes to. */
function sources() {
  const region = String(app.data.value?.meta?.server || 'NA').toUpperCase() === 'EU' ? 'EU' : 'NA';
  return /** @type {{ key: WatchKey, field: string, parts: string[], name: string, adminOnly?: boolean }[]} */ ([
    { key: 'iasync', field: 'iasync', parts: ['SavedVariables'], name: 'iasync.lua' },
    { key: 'ww', field: 'ww', parts: ['SavedVariables'], name: 'WizardsWardrobe.lua' },
    { key: 'ttcLookup', field: 'ttc_lookup', parts: ['AddOns', 'TamrielTradeCentre'], name: 'ItemLookUpTable_EN.lua', adminOnly: true },
    { key: 'ttcPrice', field: 'ttc_price', parts: ['AddOns', 'TamrielTradeCentre'], name: `PriceTable${region}.lua`, adminOnly: true },
  ]);
}

/** @param {string[]} parts @param {string} name */
async function getFile(parts, name) {
  try {
    let dir = watch.handle;
    for (const p of parts) dir = await dir.getDirectoryHandle(p);
    return await (await dir.getFileHandle(name)).getFile();
  } catch {
    return null;
  }
}

let busy = false;
/** Upload any watched file that changed since the last sync. Returns true if something was uploaded. */
export async function checkFolder() {
  if (!watch.handle || busy) return false;
  busy = true;
  try {
    watch.checked = Date.now();
    const changed = [];
    for (const src of sources()) {
      if (src.adminOnly && !app.status.isAdmin) continue;
      const file = await getFile(src.parts, src.name);
      if (file && file.lastModified > watch.lastMod[src.key]) changed.push({ src, file });
    }
    if (!changed.length) return false;
    const d = await uploadFiles(Object.fromEntries(changed.map(({ src, file }) => [src.field, file])));
    const now = Date.now();
    for (const { src, file } of changed) {
      if (d?.[src.field]?.ok) {
        watch.lastMod[src.key] = file.lastModified;
        watch.synced[src.key] = now;
      }
    }
    return changed.some(({ src }) => d?.[src.field]?.ok);
  } catch {
    return false;
  } finally {
    busy = false;
  }
}

/** @type {ReturnType<typeof setInterval> | undefined} */
let timer;
function startTimer() {
  clearInterval(timer);
  // A cheap metadata check every minute; files are only uploaded when they changed.
  timer = setInterval(async () => (await checkFolder()) && toast('Data updated'), 60_000);
}

// The directory handle survives reloads in IndexedDB (handles can't go in localStorage).
/** @param {'readonly' | 'readwrite'} mode @param {(s: IDBObjectStore) => IDBRequest} op */
function idb(mode, op) {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('eso-armory', 1);
    req.onupgradeneeded = () => req.result.createObjectStore('kv');
    req.onerror = () => reject(req.error);
    req.onsuccess = () => {
      try {
        const r = op(req.result.transaction('kv', mode).objectStore('kv'));
        r.onsuccess = () => resolve(r.result);
        r.onerror = () => reject(r.error);
      } catch (e) {
        reject(e);
      }
    };
  });
}

/** Ask for the ESO "live" folder, upload what's there, then keep watching it. */
export async function pickFolder() {
  if (!canWatchFolder) return false;
  try {
    watch.handle = await (/** @type {any} */ (window)).showDirectoryPicker({ mode: 'read' });
  } catch (e) {
    if (/** @type {Error} */ (e).name !== 'AbortError') toast('Folder access denied');
    return false;
  }
  await idb('readwrite', (s) => s.put(watch.handle, 'dirHandle')).catch(() => {});
  await checkFolder();
  startTimer();
  toast('Watching live folder');
  return true;
}

/** Resume watching after a reload if the browser still grants access. */
export async function restoreFolder() {
  if (!canWatchFolder) return;
  try {
    const handle = await idb('readonly', (s) => s.get('dirHandle'));
    if (!handle || (await handle.queryPermission({ mode: 'read' })) !== 'granted') return;
    watch.handle = handle;
    await checkFolder();
    startTimer();
  } catch {
    // IndexedDB or the permission API is unavailable
  }
}

export async function stopWatching() {
  clearInterval(timer);
  watch.handle = null;
  watch.checked = 0;
  for (const k of KEYS) watch.lastMod[k] = watch.synced[k] = 0;
  await idb('readwrite', (s) => s.delete('dirHandle')).catch(() => {});
}
