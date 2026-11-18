import { mount } from 'svelte';
import './lib/styles/global.css';
import App from './App.svelte';

// Icons fetched on demand (/esoicons, possibly via UESP) show a spinner until they load or fail: load/error don't
// bubble, so listen in the capture phase and mark the image (see global.css img[src^="/esoicons/"]).
for (const type of ['load', 'error']) {
  document.addEventListener(type, (e) => {
    const t = /** @type {HTMLElement} */ (e.target);
    if (t instanceof HTMLImageElement) t.dataset.loaded = '';
  }, true);
}

mount(App, { target: document.getElementById('app') });
