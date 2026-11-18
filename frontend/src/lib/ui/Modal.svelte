<script>
  /**
   * Dialog on a native <dialog>: focus trapping, Escape and the backdrop come from the browser.
   * Clicking the backdrop closes it.
   * @type {{ open: boolean, title: string, onclose: () => void, wide?: boolean, children: import('svelte').Snippet }}
   */
  let { open, title, onclose, wide = false, children } = $props();

  /** @type {HTMLDialogElement} */
  let dlg;

  $effect(() => {
    if (open && !dlg.open) dlg.showModal();
    if (!open && dlg.open) dlg.close();
  });
</script>

<dialog
  bind:this={dlg}
  class:wide
  aria-label={title}
  onclose={onclose}
  onclick={(e) => e.target === dlg && onclose()}>
  <div class="body">
    <button type="button" class="x" aria-label="Close" onclick={onclose}>×</button>
    <h2>{title}</h2>
    {@render children()}
  </div>
</dialog>

<style>
  dialog {
    width: min(440px, calc(100vw - 32px));
    max-height: calc(100dvh - 48px);
    padding: 0;
    border: 0;
    background: transparent;
    color: var(--fg);
    overflow: visible;
  }
  dialog.wide { width: min(560px, calc(100vw - 32px)); }
  dialog::backdrop { background: #000b; backdrop-filter: blur(3px); }
  dialog[open] { animation: open 0.35s var(--ease-spring); }
  dialog[open]::backdrop { animation: fade 0.25s ease; }
  .body {
    position: relative;
    max-height: inherit;
    overflow-y: auto;
    padding: 26px 26px 24px;
    background: linear-gradient(#11100e, #070707);
    border: 1px solid var(--line);
    box-shadow: 0 24px 80px #000;
  }
  .body::before {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    --rule: linear-gradient(90deg, transparent, var(--accent) 15%, var(--accent-hi) 50%, var(--accent) 85%, transparent);
    background: var(--rule) top / 100% 1px no-repeat, var(--rule) bottom / 100% 1px no-repeat;
  }
  h2 { color: var(--fg); font-size: 18px; margin: 0 28px 14px 0; }
  .x { all: unset; position: absolute; top: 14px; right: 16px; font-size: 22px; line-height: 1; color: var(--muted); cursor: pointer; }
  .x:hover { color: var(--fg); }
  .x:focus-visible { outline: 1px solid var(--accent-hi); }
  @keyframes open { from { opacity: 0; transform: translateY(12px) scale(0.97); } }
  @keyframes fade { from { opacity: 0; } }
</style>
