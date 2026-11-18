<script>
  /**
   * Small segmented control with a sliding gold pill.
   * Classic UI with icons: the game's ZO_LabelButtonBar (selected name, then 32px icons growing to 50px when hovered or
   * selected; drawn at 28/40px here to fit the header row, 16px apart). `icon` is a path under /assets/esoui/ without the _up/_down/_over suffix.
   * `showLabel` false drops the selected name in front of the icons (Classic).
   * @type {{ options: { id: string, label: string, icon?: string }[], value: string, label: string, onchange: (id: string) => void, showLabel?: boolean }}
   */
  let { options, value, label, onchange, showLabel = true } = $props();
  import { ui } from '../uimode.svelte.js';
  const classic = $derived(ui.mode === 'classic' && options.every((o) => o.icon));

  /** @type {Record<string, HTMLElement>} */
  const buttons = {};
  let pill = $state({ left: 0, width: 0 });

  function place() {
    const b = buttons[value];
    if (b) pill = { left: b.offsetLeft, width: b.offsetWidth };
  }
  $effect(() => {
    value; // re-measure on change
    place();
    document.fonts.ready.then(place); // widths change once Cinzel loads
  });
</script>

{#if classic}
  <div class="lbb" role="group" aria-label={label}>
    {#if showLabel}<span class="lbl">{options.find((o) => o.id === value)?.label}</span>{/if}
    {#each options as o (o.id)}
      <button type="button" aria-pressed={value === o.id} aria-label={o.label} title={o.label} onclick={() => value !== o.id && onchange(o.id)}>
        <img src="/assets/esoui/{o.icon}_{value === o.id ? 'down' : 'up'}.png" alt="" />
        <img class="over" src="/assets/esoui/{o.icon}_over.png" alt="" />
      </button>
    {/each}
  </div>
{:else}
<div class="seg" role="group" aria-label={label}>
  <span class="pill" style="left: {pill.left}px; width: {pill.width}px"></span>
  {#each options as o (o.id)}
    <button type="button" aria-pressed={value === o.id} bind:this={buttons[o.id]} onclick={() => value !== o.id && onchange(o.id)}>{o.label.toUpperCase()}</button>
  {/each}
</div>
{/if}

<style>
  .lbb { display: inline-flex; align-items: center; gap: 16px; }
  .lbl { margin-right: 9px; font: 700 18px var(--eso-font); text-transform: uppercase; color: var(--eso-selected); text-shadow: var(--eso-shadow); }
  .lbb button { all: unset; position: relative; width: 40px; height: 40px; display: grid; place-items: center; cursor: pointer; }
  .lbb img { position: absolute; width: 28px; height: 28px; transition: width 0.15s, height 0.15s; }
  .lbb .over { opacity: 0; mix-blend-mode: plus-lighter; }
  .lbb button:hover img, .lbb button[aria-pressed='true'] img { width: 40px; height: 40px; }
  .lbb button:hover .over { opacity: 1; }
  .lbb button:focus-visible { outline: 1px solid var(--eso-normal); }
  .seg { position: relative; display: inline-flex; gap: 4px; padding: 3px; max-width: 100%; overflow-x: auto; scrollbar-width: none; border: 1px solid var(--line); background: #00000066; }
  button { all: unset; flex: none; position: relative; z-index: 1; cursor: pointer; padding: 4px 10px; font: 500 12px var(--f-display); letter-spacing: 0.12em; color: var(--muted); transition: color 0.3s; }
  button:hover { color: var(--fg); }
  button[aria-pressed='true'] { color: var(--bg); }
  button:focus-visible { outline: 1px solid var(--accent-hi); }
  .pill {
    position: absolute;
    top: 3px;
    bottom: 3px;
    background: linear-gradient(var(--accent-hi), var(--accent));
    box-shadow: 0 0 14px -3px var(--accent);
    transition: left 0.45s var(--ease-spring), width 0.45s var(--ease-spring);
  }
</style>
