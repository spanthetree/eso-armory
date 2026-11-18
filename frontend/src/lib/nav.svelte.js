// Navigation and dialog state. The tab (and selected character) live in the URL hash,
// e.g. #/characters/char-a or #/inventory, so reloads and links keep your place.

import { parseHash, toHash } from './route.js';

/** @typedef {import('./route.js').Tab} Tab */
/** @typedef {import('./route.js').CharView} CharView */
export { TABS, CHAR_VIEWS } from './route.js';

export const nav = $state({
  ...parseHash(typeof location === 'undefined' ? '' : location.hash),
  /** Which dialog is open: '' for none. */
  dialog: /** @type {'' | 'upload' | 'share' | 'password'} */ (''),
});

/** @param {Tab} tab @param {string | null} [charId] @param {CharView} [charView] */
export function go(tab, charId = null, charView = 'sheet') {
  const hash = toHash(tab, charId, charView);
  if (location.hash !== hash) location.hash = hash;
  Object.assign(nav, parseHash(hash));
}

if (typeof window !== 'undefined') {
  addEventListener('hashchange', () => Object.assign(nav, parseHash(location.hash)));
}
