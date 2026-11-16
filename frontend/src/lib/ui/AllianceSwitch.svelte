<script>
  /**
   * AD / DC / EP segmented control with a sliding pill.
   * @type {{ value: 'ad' | 'dc' | 'ep', onchange?: (v: 'ad' | 'dc' | 'ep') => void }}
   */
  let { value = $bindable(), onchange } = $props();

  const OPTIONS = /** @type {const} */ ([
    ['ad', 'Aldmeri Dominion'],
    ['dc', 'Daggerfall Covenant'],
    ['ep', 'Ebonheart Pact'],
  ]);

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

<div class="seg" role="group" aria-label="Alliance colour">
  <span class="pill" style="left: {pill.left}px; width: {pill.width}px"></span>
  {#each OPTIONS as [key, name] (key)}
    <button
      type="button"
      title={name}
      aria-pressed={value === key}
      bind:this={buttons[key]}
      onclick={() => { value = key; onchange?.(key); }}>{key.toUpperCase()}</button>
  {/each}
</div>

<style>
  .seg { position: relative; display: inline-flex; gap: 6px; padding: 4px; border: 1px solid var(--line); background: #00000066; }
  button { all: unset; position: relative; z-index: 1; cursor: pointer; padding: 5px 10px; font: 500 12px var(--f-display); letter-spacing: 0.12em; color: var(--muted); transition: color 0.3s; }
  button[aria-pressed='true'] { color: var(--bg); }
  button:focus-visible { outline: 1px solid var(--accent-hi); }
  .pill {
    position: absolute;
    top: 4px;
    bottom: 4px;
    background: linear-gradient(var(--accent-hi), var(--accent));
    box-shadow: 0 0 16px -2px var(--accent);
    transition: left 0.5s var(--ease-spring), width 0.5s var(--ease-spring);
  }
</style>
