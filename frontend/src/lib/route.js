// Pure URL-hash helpers (no runes), so node --test can cover them.

export const TABS = /** @type {const} */ (['characters', 'inventory', 'achievements', 'collections']);
/** @typedef {typeof TABS[number]} Tab */

/** @param {string} hash */
export function parseHash(hash) {
  const [tab, ...rest] = hash.replace(/^#\/?/, '').split('/');
  const known = /** @type {readonly string[]} */ (TABS).includes(tab);
  return {
    tab: /** @type {Tab} */ (known ? tab : 'characters'),
    charId: known && tab === 'characters' && rest[0] ? decodeURIComponent(rest[0]) : null,
  };
}

/** @param {Tab} tab @param {string | null} [charId] */
export function toHash(tab, charId = null) {
  return `#/${tab}${tab === 'characters' && charId ? `/${encodeURIComponent(charId)}` : ''}`;
}
