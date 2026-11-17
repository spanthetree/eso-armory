// Cached lookups the server scrapes from eso-sets.com / eso-skillbook.com. Each key is fetched once.
import * as api from './api.js';
import { setKey, slugify } from './gear.js';
import { app } from './store.svelte.js';

/** @typedef {{ loading?: boolean, bonuses?: { pieces: number, text: string }[], url?: string, error?: string | null }} BonusEntry */
/** @typedef {{ loading?: boolean, error?: string, url?: string, type?: string, location?: string, cost?: string, cast_time?: string, target?: string, range?: string, description?: string }} SkillEntry */

export const setBonuses = $state(/** @type {Record<string, BonusEntry>} */ ({}));
export const skillInfo = $state(/** @type {Record<string, SkillEntry>} */ ({}));

/** @param {any} item has set_id and set_name */
export async function loadSetBonus(item) {
  const key = setKey(item);
  if (key == null || setBonuses[key]) return;
  setBonuses[key] = { loading: true };
  try {
    const d = await api.get('/api/set_bonus', { label: 'Set bonus lookup', params: { set_id: item.set_id || 0, set_name: item.set_name }, share: false });
    const bonuses = Array.isArray(d?.bonuses) ? d.bonuses : [];
    setBonuses[key] = {
      bonuses,
      url: d?.url || `https://eso-sets.com/set/${slugify(item.set_name)}`,
      error: d?.error || (bonuses.length ? null : 'Bonus lookup unavailable'),
    };
  } catch (e) {
    setBonuses[key] = { bonuses: [], error: /** @type {Error} */ (e).message || 'Bonus lookup unavailable' };
  }
}

/** @param {string} name ability name */
export async function loadSkillInfo(name) {
  if (!name || name.startsWith('#')) return;
  const key = slugify(name);
  if (skillInfo[key]) return;
  skillInfo[key] = { loading: true };
  try {
    skillInfo[key] = await api.get('/api/skill_info', { label: 'Skill info', params: { name }, share: false });
  } catch (e) {
    skillInfo[key] = { error: /** @type {Error} */ (e).message || 'Skill lookup failed' };
  }
}

/** @param {string} name */
export const skillbookUrl = (name) => `https://eso-skillbook.com/skill/${slugify(name)}`;

/** Names for ability ids iasync couldn't resolve, filled from UESP via the server. */
export const extraAbilityNames = $state(/** @type {Record<string, string>} */ ({}));
const askedAbilityIds = new Set();

/** Look up names for ability ids not yet known or asked for. @param {(number | string)[]} ids */
export async function loadAbilityNames(ids) {
  const todo = [...new Set(ids.map(String))].filter((id) => id && id !== '0' && !askedAbilityIds.has(id));
  for (let i = 0; i < todo.length; i += 40) {
    const batch = todo.slice(i, i + 40);
    batch.forEach((id) => askedAbilityIds.add(id));
    try {
      const d = await api.get('/api/ability_names', { label: 'Ability names', params: { ids: batch.join(',') }, share: false });
      Object.assign(extraAbilityNames, d.names ?? {});
    } catch {
      batch.forEach((id) => askedAbilityIds.delete(id)); // retry on a later view
    }
  }
}

/** Tamriel Trade Centre prices by normalised item name. */
export const prices = $state(/** @type {Record<string, any>} */ ({}));
/** @param {string} name */
export const priceKey = (name) => (name || '').toLowerCase().replace(/\s+/g, ' ').trim();

/** @param {string} name */
export function ttcSearchUrl(name) {
  const region = String(app.data.value?.meta?.server || 'NA').toUpperCase() === 'EU' ? 'eu' : 'us';
  return `https://${region}.tamrieltradecentre.com/pc/Trade/SearchResult?ItemNamePattern=${encodeURIComponent(name)}`;
}

/** @param {string} name */
export async function loadPrice(name) {
  const key = priceKey(name);
  if (!key || prices[key]) return;
  prices[key] = { loading: true };
  try {
    prices[key] = await api.get('/api/ttc_price', { label: 'TTC price', params: { name } });
  } catch (e) {
    prices[key] = { error: /** @type {Error} */ (e).message || 'Price lookup failed', url: ttcSearchUrl(name) };
  }
}

/** Average TTC prices by lower-cased name for the Inventory value column; filled in bulk. */
export const avgPrices = $state({ /** @type {Record<string, number>} */ map: {}, error: '', loading: false });
const askedPriceNames = new Set();

/** Fetch average prices for any of these names not asked for yet. @param {string[]} names lower-cased */
export async function loadAvgPrices(names) {
  const want = [...new Set(names)].filter((n) => n && !askedPriceNames.has(n));
  if (!want.length) return;
  want.forEach((n) => askedPriceNames.add(n));
  avgPrices.loading = true;
  try {
    const d = await api.post('/api/ttc_prices', { label: 'TTC prices', init: { body: JSON.stringify({ names: want }), headers: { 'Content-Type': 'application/json' } } });
    avgPrices.map = { ...avgPrices.map, ...d.prices };
    avgPrices.error = d.error || '';
  } catch (e) {
    want.forEach((n) => askedPriceNames.delete(n)); // retry on a later view
    avgPrices.error = /** @type {Error} */ (e).message || 'TTC price lookup failed';
  } finally {
    avgPrices.loading = false;
  }
}

/** Forget bulk prices after new TTC tables are uploaded. */
export function resetAvgPrices() {
  askedPriceNames.clear();
  avgPrices.map = {};
  avgPrices.error = '';
}
