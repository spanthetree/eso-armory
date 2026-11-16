// Navigation and dialog state. The tab (and selected character) live in the URL hash,
// e.g. #/characters/char-a or #/inventory, so reloads and links keep your place.

import { parseHash, toHash } from './route.js';

/** @typedef {import('./route.js').Tab} Tab */
export { TABS } from './route.js';

export const nav = $state({
  ...parseHash(typeof location === 'undefined' ? '' : location.hash),
  /** Which dialog is open: '' for none. */
  dialog: /** @type {'' | 'upload' | 'share' | 'password'} */ (''),
});

/** @param {Tab} tab @param {string | null} [charId] */
export function go(tab, charId = null) {
  const hash = toHash(tab, charId);
  if (location.hash !== hash) location.hash = hash;
  nav.tab = tab;
  nav.charId = tab === 'characters' ? charId : null;
}

if (typeof window !== 'undefined') {
  addEventListener('hashchange', () => Object.assign(nav, parseHash(location.hash)));
}
