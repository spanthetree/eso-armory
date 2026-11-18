<script>
  /**
   * Dropdown of toggleable options. `selected` is an array of option values (bindable).
   * Pass `groups` for sectioned lists (e.g. traits), or `options` for a flat one.
   * @type {{
   *   label: string,
   *   selected: string[],
   *   options?: { v: string, l: string }[],
   *   groups?: { group: string, options: { v: string, l: string }[] }[],
   *   align?: 'left' | 'right',
   * }}
   */
  let { label, selected = $bindable(), options = [], groups = [], align = 'left' } = $props();

  let open = $state(false);
  /** @type {HTMLElement} */
  let root;

  const all = $derived([...options, ...groups.flatMap((g) => g.options)]);
  /** Button text: the label when nothing is picked, "A, B" for two, "A +N" beyond. */
  const summary = $derived.by(() => {
    if (!selected.length) return label;
    const names = selected.map((v) => (v === 'any' ? 'Any' : all.find((o) => o.v === v)?.l ?? v));
    return names.length <= 2 ? names.join(', ') : `${names[0]} +${names.length - 1}`;
  });

  /** @param {string} v */
  function toggle(v) {
    selected = selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v];
  }
</script>

<svelte:window
  onpointerdown={(e) => open && !root.contains(/** @type {Node} */ (e.target)) && (open = false)}
  onkeydown={(e) => open && e.key === 'Escape' && (open = false)} />

<div class="ms" bind:this={root}>
  <button type="button" class="btn" class:active={selected.length} aria-expanded={open} aria-haspopup="listbox" onclick={() => (open = !open)}>
    <span class="text">{summary}</span><span class="caret">{open ? '▴' : '▾'}</span>
  </button>
  {#if open}
    <div class="menu {align}" role="listbox" aria-multiselectable="true" aria-label={label}>
      {#snippet opt(/** @type {{ v: string, l: string }} */ o)}
        <button type="button" role="option" aria-selected={selected.includes(o.v)} onclick={() => toggle(o.v)}>
          <span class="check">{selected.includes(o.v) ? '◆' : ''}</span>{o.l}
        </button>
      {/snippet}
      {#each options as o (o.v)}{@render opt(o)}{/each}
      {#each groups as g (g.group)}
        <div class="group">{g.group}</div>
        {#each g.options as o (g.group + o.v)}{@render opt(o)}{/each}
      {/each}
    </div>
  {/if}
</div>

<style>
  .ms { position: relative; }
  .btn { min-width: 118px; justify-content: space-between; }
  .btn.active { color: var(--accent-hi); border-color: var(--accent); }
  .text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 150px; }
  .caret { font-size: 11px; opacity: 0.7; }
  .menu {
    position: absolute;
    top: calc(100% + 4px);
    z-index: 30;
    min-width: 180px;
    max-height: 340px;
    overflow-y: auto;
    padding: 4px 0;
    background: #0d0c0b;
    border: 1px solid var(--line);
    box-shadow: 0 16px 40px #000c;
    animation: drop 0.18s var(--ease-out);
  }
  .menu.left { left: 0; }
  .menu.right { right: 0; }
  .menu button { all: unset; box-sizing: border-box; display: flex; align-items: center; gap: 6px; width: 100%; padding: 5px 12px; font-size: 14px; color: var(--fg); cursor: pointer; }
  .menu button:hover, .menu button:focus-visible { background: #ffffff0d; }
  .menu button[aria-selected='true'] { color: var(--accent-hi); }
  .check { width: 10px; font-size: 9px; color: var(--accent); }
  .group { margin-top: 4px; padding: 6px 12px 2px; border-top: 1px solid var(--line); font: 600 11px var(--f-display); letter-spacing: 0.14em; color: var(--muted); text-transform: uppercase; }
  .group:first-child { margin-top: 0; border-top: 0; }
  @keyframes drop { from { opacity: 0; transform: translateY(-4px); } }
</style>
