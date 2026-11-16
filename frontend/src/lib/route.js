// Pure URL-hash helpers (no runes), so node --test can cover them.
// Hashes: #/inventory, #/characters, #/characters/<id>, #/characters/<id>/<view>

export const TABS = /** @type {const} */ (['characters', 'inventory', 'achievements', 'collections']);
/** @typedef {typeof TABS[number]} Tab */

/** Sub-views of one character. */
export const CHAR_VIEWS = /** @type {const} */ (['sheet', 'wardrobe', 'bags']);
/** @typedef {typeof CHAR_VIEWS[number]} CharView */

/** @param {string} hash */
export function parseHash(hash) {
  const [tab, id, view] = hash.replace(/^#\/?/, '').split('/');
  const known = /** @type {readonly string[]} */ (TABS).includes(tab);
  const charId = known && tab === 'characters' && id ? decodeURIComponent(id) : null;
  return {
    tab: /** @type {Tab} */ (known ? tab : 'characters'),
    charId,
    charView: /** @type {CharView} */ (charId && /** @type {readonly string[]} */ (CHAR_VIEWS).includes(view) ? view : 'sheet'),
  };
}

/** @param {Tab} tab @param {string | null} [charId] @param {CharView} [charView] */
export function toHash(tab, charId = null, charView = 'sheet') {
  if (tab !== 'characters' || !charId) return `#/${tab}`;
  return `#/characters/${encodeURIComponent(charId)}${charView === 'sheet' ? '' : `/${charView}`}`;
}
