<script>
  import { app } from '../store.svelte.js';

  let shown = $state('');
  /** @type {ReturnType<typeof setTimeout> | undefined} */
  let timer;

  $effect(() => {
    if (!app.toast.seq) return;
    shown = app.toast.msg;
    clearTimeout(timer);
    timer = setTimeout(() => (shown = ''), 3000);
  });
</script>

<div class="toast" class:on={!!shown} role="status" aria-live="polite">{shown}</div>

<style>
  .toast {
    position: fixed;
    left: 50%;
    bottom: calc(24px + env(safe-area-inset-bottom, 0px));
    z-index: 200;
    padding: 9px 18px;
    font: 500 15px var(--f-ui);
    letter-spacing: 0.04em;
    color: var(--fg);
    background: #0b0a09f0;
    border: 1px solid var(--accent);
    box-shadow: 0 0 24px -6px var(--accent), 0 12px 30px #000;
    pointer-events: none;
    opacity: 0;
    transform: translate(-50%, 16px);
    transition: opacity 0.25s, transform 0.4s var(--ease-spring);
  }
  .toast.on { opacity: 1; transform: translate(-50%, 0); }
</style>
