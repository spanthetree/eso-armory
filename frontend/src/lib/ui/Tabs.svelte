<script>
  /**
   * Tab bar with a spring underline that slides to the active tab. Arrow keys move between tabs.
   * @type {{ items: { id: string, label: string }[], active: string, onchange?: (id: string) => void }}
   */
  let { items, active = $bindable(), onchange } = $props();

  /** @type {HTMLElement[]} */
  const buttons = [];
  /** @type {HTMLElement} */
  let bar;
  let line = $state({ left: 0, width: 0 });

  function place() {
    const b = buttons[items.findIndex((t) => t.id === active)];
    if (b) line = { left: Math.max(0, b.offsetLeft - 12), width: b.offsetWidth + 24 };
  }
  $effect(() => {
    active; // re-measure when the active tab changes
    place();
    document.fonts.ready.then(place); // widths change once Cinzel loads
    const ro = new ResizeObserver(place);
    ro.observe(bar);
    return () => ro.disconnect();
  });

  /** @param {string} id */
  function select(id) {
    if (id === active) return;
    active = id;
    onchange?.(id);
  }

  /** @param {KeyboardEvent} e */
  function onkeydown(e) {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    const i = items.findIndex((t) => t.id === active);
    const n = (i + (e.key === 'ArrowRight' ? 1 : -1) + items.length) % items.length;
    select(items[n].id);
    buttons[n].focus();
  }
</script>

<div class="tabs" role="tablist" tabindex="-1" bind:this={bar} {onkeydown}>
  {#each items as t, i (t.id)}
    <button
      type="button"
      role="tab"
      aria-selected={t.id === active}
      tabindex={t.id === active ? 0 : -1}
      bind:this={buttons[i]}
      onclick={() => select(t.id)}>{t.label.toUpperCase()}</button>
  {/each}
  <span class="uline" style="left: {line.left}px; width: {line.width}px"></span>
</div>

<style>
  .tabs { position: relative; display: flex; gap: 26px; justify-content: safe center; border-bottom: 1px solid var(--line); overflow-x: auto; scrollbar-width: none; }
  button { all: unset; flex: 0 0 auto; cursor: pointer; padding: 10px 2px; font: 500 14px var(--f-display); letter-spacing: 0.16em; color: var(--muted); transition: color 0.3s, text-shadow 0.3s; }
  button:hover { color: var(--fg); }
  button[aria-selected='true'] { color: var(--accent-hi); text-shadow: 0 0 12px color-mix(in srgb, var(--accent) 60%, transparent); }
  button:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: 2px; }
  .uline {
    position: absolute;
    bottom: -1px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-hi), transparent);
    box-shadow: 0 0 10px var(--accent);
    transition: left 0.5s var(--ease-spring), width 0.5s var(--ease-spring);
  }
</style>
