import { mount } from 'svelte';
import './lib/styles/global.css';
import App from './App.svelte';

// Icons fetched on demand (/esoicons, ability icons; the server may go through UESP or a proxy) show a spinner until
// they load (see global.css). load/error don't bubble, so listen in the capture phase. An icon that fails shows the
// game's own question-mark icon instead of the browser's broken-image glyph; category tree icons (subfolders of
// /esoicons) keep their own error handling, which hides them.
const MISSING = '/assets/esoui/icons/icon_missing.png';
const ON_DEMAND = /^\/(esoicons\/[^/]+\.png|assets\/abilities\/)/;
for (const type of ['load', 'error']) {
  document.addEventListener(type, (e) => {
    const t = e.target;
    if (!(t instanceof HTMLImageElement)) return;
    t.dataset.loaded = '';
    if (type === 'error' && !t.dataset.missing && ON_DEMAND.test(new URL(t.src, location.href).pathname)) {
      t.dataset.missing = '';
      t.src = MISSING;
    }
  }, true);
}
// Svelte reuses <img> elements: a new src means a new load, so it spins again.
new MutationObserver((records) => {
  for (const r of records) {
    const t = /** @type {HTMLImageElement} */ (r.target);
    if (t.src !== new URL(MISSING, location.href).href) delete t.dataset.missing;
    if (!t.complete) delete t.dataset.loaded;
  }
}).observe(document, { subtree: true, attributes: true, attributeFilter: ['src'] });

mount(App, { target: document.getElementById('app') });
