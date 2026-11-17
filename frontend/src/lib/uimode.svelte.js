// UI style: "classic" draws the in-game ESO look (game textures, layouts and colours); "simple" is the Obsidian web look.
// Per-browser preference; also mirrored on <html data-ui> so global styles can follow it.

const KEY = 'eso-armory:ui';
/** @typedef {'classic' | 'simple'} UiMode */

function read() {
  try {
    return localStorage.getItem(KEY) === 'simple' ? 'simple' : 'classic';
  } catch {
    return 'classic'; // blocked storage: default look, not remembered
  }
}

export const ui = $state({ mode: /** @type {UiMode} */ (read()) });

/** @param {UiMode} mode */
export function setUiMode(mode) {
  ui.mode = mode;
  try {
    localStorage.setItem(KEY, mode);
  } catch {
    /* not remembered */
  }
}

$effect.root(() => {
  $effect(() => {
    document.documentElement.dataset.ui = ui.mode;
  });
});
