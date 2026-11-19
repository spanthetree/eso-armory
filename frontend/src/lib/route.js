// Pure URL-hash helpers (no runes), so node --test can cover them.
// Hashes: #/inventory, #/characters, #/characters/<id>, #/characters/<id>/<view>, #/<tab>/<book> (BOOKS_BY_TAB)

export const TABS = /** @type {const} */ (['characters', 'inventory', 'achievements', 'collections', 'tome']);
/** @typedef {typeof TABS[number]} Tab */

/** Sub-views of one character. */
export const CHAR_VIEWS = /** @type {const} */ (['sheet', 'crafting', 'scribing', 'armory', 'wardrobe', 'bags', 'compare', 'superstar']);
/** @typedef {typeof CHAR_VIEWS[number]} CharView */

/** Each tab's books (its scene group in game). A plain #/<tab> leaves the choice to the app (book null). */
export const BOOKS_BY_TAB = /** @type {Record<string, readonly string[]>} */ ({
  achievements: ['achievements', 'antiquities'],
  collections: ['collectibles', 'housing', 'outfits', 'sets', 'tribute'],
  tome: ['tome', 'endeavors', 'pursuits'],
});
/** @typedef {string} Book */

/** @param {string} hash */
export function parseHash(hash) {
  const [tab, id, view] = hash.replace(/^#\/?/, '').split('/');
  const known = /** @type {readonly string[]} */ (TABS).includes(tab);
  const charId = known && tab === 'characters' && id ? decodeURIComponent(id) : null;
  return {
    tab: /** @type {Tab} */ (known ? tab : 'characters'),
    charId,
    charView: /** @type {CharView} */ (charId && /** @type {readonly string[]} */ (CHAR_VIEWS).includes(view) ? view : 'sheet'),
    book: /** @type {Book | null} */ (known && BOOKS_BY_TAB[tab]?.includes(id) ? id : null),
  };
}

/** @param {Tab} tab @param {string | null} [charId] @param {CharView} [charView] @param {Book | null} [book] */
export function toHash(tab, charId = null, charView = 'sheet', book = null) {
  if (BOOKS_BY_TAB[tab]) return book ? `#/${tab}/${book}` : `#/${tab}`;
  if (tab !== 'characters' || !charId) return `#/${tab}`;
  return `#/characters/${encodeURIComponent(charId)}${charView === 'sheet' ? '' : `/${charView}`}`;
}
