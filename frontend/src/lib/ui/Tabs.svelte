<script>
  /**
   * Tab bar with a spring underline that slides to the active tab. Arrow keys move between tabs.
   * Classic UI: the game's main menu category bar instead (ZO_MainMenu: menuBar_<icon> icons, 51px, 64px when selected,
   * 16px apart). Names show as tooltips, as in the game.
   * @type {{ items: { id: string, label: string, icon?: string }[], active: string, onchange?: (id: string) => void }}
   */
  let { items, active = $bindable(), onchange } = $props();
  import { ui } from '../uimode.svelte.js';
  const classic = $derived(ui.mode === 'classic' && items.every((t) => t.icon));

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

<div class="tabs" class:mm={classic} role="tablist" tabindex="-1" bind:this={bar} {onkeydown}>
  {#each items as t, i (t.id)}
    <button
      type="button"
      role="tab"
      aria-selected={t.id === active}
      aria-label={classic ? t.label : undefined}
      title={classic ? t.label : undefined}
      tabindex={t.id === active ? 0 : -1}
      bind:this={buttons[i]}
      onclick={() => select(t.id)}>
      {#if classic}
        <img class="up" src="/assets/esoui/mainmenu/menubar_{t.icon}_{t.id === active ? 'down' : 'up'}.png" alt="" />
        <img class="over" src="/assets/esoui/mainmenu/menubar_{t.icon}_over.png" alt="" />
      {:else}{t.label.toUpperCase()}{/if}
    </button>
  {/each}
  {#if !classic}<span class="uline" style="left: {line.left}px; width: {line.width}px"></span>{/if}
</div>


<style>
  .tabs { position: relative; display: flex; gap: 26px; justify-content: safe center; border-bottom: 1px solid var(--line); overflow-x: auto; scrollbar-width: none; }
  button { all: unset; flex: 0 0 auto; cursor: pointer; padding: 10px 2px; font: 500 14px var(--f-display); letter-spacing: 0.16em; color: var(--muted); transition: color 0.3s, text-shadow 0.3s; }
  button:hover { color: var(--fg); }
  button[aria-selected='true'] { color: var(--fg); text-shadow: 0 0 12px #ffffff40; }
  button:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: 2px; }
  .uline {
    position: absolute;
    bottom: -1px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-hi), transparent);
    box-shadow: 0 0 10px var(--accent);
    transition: left 0.5s var(--ease-spring), width 0.5s var(--ease-spring);
  }
  /* Classic main menu bar */
  .mm { gap: 16px; align-items: center; height: 62px; border-bottom: 0; overflow: visible; }
  .mm button { position: relative; width: 60px; height: 60px; padding: 0; display: grid; place-items: center; }
  .mm img { position: absolute; width: 51px; height: 51px; transition: width 0.2s var(--ease-out), height 0.2s var(--ease-out); }
  .mm .over { opacity: 0; mix-blend-mode: plus-lighter; }
  .mm button:hover .over { opacity: 1; }
  .mm button[aria-selected='true'] img { width: 60px; height: 60px; }
  .mm button[aria-selected='true'] .over { opacity: 0; }
</style>
