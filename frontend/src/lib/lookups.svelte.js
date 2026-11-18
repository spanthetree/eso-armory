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

// Destruction Staff skills take the equipped staff's element in their in-game name (Blockade of Fire), but
// eso-skillbook.com has one page per base skill (Elemental Blockade).
const STAFF_BASE = {
  'Wall of Elements': ['Wall of Fire', 'Wall of Frost', 'Wall of Storms'],
  'Unstable Wall of Elements': ['Unstable Wall of Fire', 'Unstable Wall of Frost', 'Unstable Wall of Storms'],
  'Elemental Blockade': ['Blockade of Fire', 'Blockade of Frost', 'Blockade of Storms'],
  'Destructive Touch': ['Fire Touch', 'Frost Touch', 'Shock Touch'],
  'Destructive Clench': ['Flame Clench', 'Frost Clench', 'Shock Clench'],
  'Destructive Reach': ['Flame Reach', 'Frost Reach', 'Shock Reach'],
  Impulse: ['Fire Impulse', 'Frost Impulse', 'Shock Impulse'],
  'Elemental Ring': ['Fire Ring', 'Frost Ring', 'Shock Ring'],
  Pulsar: ['Flame Pulsar', 'Frost Pulsar', 'Storm Pulsar'],
  'Elemental Storm': ['Fire Storm', 'Ice Storm', 'Thunderstorm'],
  'Elemental Rage': ['Fiery Rage', 'Icy Rage', 'Thunderous Rage'],
  'Eye of the Storm': ['Eye of Flame', 'Eye of Frost', 'Eye of Lightning'],
};
const SKILL_PAGE = new Map(Object.entries(STAFF_BASE).flatMap(([base, variants]) => variants.map((v) => [v, base])));
/** The eso-skillbook.com skill a game ability name belongs to. @param {string} name */
export const skillPage = (name) => SKILL_PAGE.get(name.trim()) ?? name;

/** @param {string} name ability name */
export async function loadSkillInfo(name) {
  if (!name || name.startsWith('#')) return;
  const key = slugify(name);
  if (skillInfo[key]) return;
  skillInfo[key] = { loading: true };
  try {
    skillInfo[key] = await api.get('/api/skill_info', { label: 'Skill info', params: { name: skillPage(name) }, share: false });
  } catch (e) {
    skillInfo[key] = { error: /** @type {Error} */ (e).message || 'Skill lookup failed' };
  }
}

/** @param {string} name */
export const skillbookUrl = (name) => `https://eso-skillbook.com/skill/${slugify(skillPage(name))}`;

/** Names for ability ids iasync couldn't resolve, filled from UESP via the server. */
export const extraAbilityNames = $state(/** @type {Record<string, string>} */ ({}));
const askedAbilityIds = new Set();
/** Ability ids whose name is being fetched right now (their skill slots show a spinner). */
export const pendingAbilityIds = $state(/** @type {Record<string, boolean>} */ ({}));

/** Look up names for ability ids not yet known or asked for. @param {(number | string)[]} ids */
export async function loadAbilityNames(ids) {
  const todo = [...new Set(ids.map(String))].filter((id) => id && id !== '0' && !askedAbilityIds.has(id));
  for (let i = 0; i < todo.length; i += 40) {
    const batch = todo.slice(i, i + 40);
    batch.forEach((id) => (askedAbilityIds.add(id), (pendingAbilityIds[id] = true)));
    try {
      const d = await api.get('/api/ability_names', { label: 'Ability names', params: { ids: batch.join(',') }, share: false });
      Object.assign(extraAbilityNames, d.names ?? {});
    } catch {
      batch.forEach((id) => askedAbilityIds.delete(id)); // retry on a later view
    } finally {
      batch.forEach((id) => delete pendingAbilityIds[id]);
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
