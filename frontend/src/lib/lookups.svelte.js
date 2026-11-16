// Cached lookups the server scrapes from eso-sets.com / eso-skillbook.com. Each key is fetched once.
import * as api from './api.js';
import { setKey, slugify } from './gear.js';

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
