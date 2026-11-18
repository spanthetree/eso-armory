// Pure URL-hash helpers (no runes), so node --test can cover them.
// Hashes: #/inventory, #/characters, #/characters/<id>, #/characters/<id>/<view>, #/collections/<book>

export const TABS = /** @type {const} */ (['characters', 'inventory', 'achievements', 'collections']);
/** @typedef {typeof TABS[number]} Tab */

/** Sub-views of one character. */
export const CHAR_VIEWS = /** @type {const} */ (['sheet', 'wardrobe', 'bags', 'compare', 'superstar']);
/** @typedef {typeof CHAR_VIEWS[number]} CharView */

/** Collections book tabs (collections.js BOOKS). Plain #/collections leaves the choice to the app (book null). */
export const BOOK_IDS = /** @type {const} */ (['collectibles', 'housing', 'outfits', 'sets', 'tribute']);
/** @typedef {typeof BOOK_IDS[number]} Book */

/** @param {string} hash */
export function parseHash(hash) {
  const [tab, id, view] = hash.replace(/^#\/?/, '').split('/');
  const known = /** @type {readonly string[]} */ (TABS).includes(tab);
  const charId = known && tab === 'characters' && id ? decodeURIComponent(id) : null;
  return {
    tab: /** @type {Tab} */ (known ? tab : 'characters'),
    charId,
    charView: /** @type {CharView} */ (charId && /** @type {readonly string[]} */ (CHAR_VIEWS).includes(view) ? view : 'sheet'),
    book: /** @type {Book | null} */ (tab === 'collections' && /** @type {readonly string[]} */ (BOOK_IDS).includes(id) ? id : null),
  };
}

/** @param {Tab} tab @param {string | null} [charId] @param {CharView} [charView] @param {Book | null} [book] */
export function toHash(tab, charId = null, charView = 'sheet', book = null) {
  if (tab === 'collections') return book ? `#/collections/${book}` : '#/collections';
  if (tab !== 'characters' || !charId) return `#/${tab}`;
  return `#/characters/${encodeURIComponent(charId)}${charView === 'sheet' ? '' : `/${charView}`}`;
}
