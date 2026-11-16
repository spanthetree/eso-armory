<script>
  /**
   * AD / DC / EP segmented control with a sliding pill. With `auto`, an extra AUTO option ('')
   * lets the page follow the selected character's alliance.
   * @type {{ value: '' | 'ad' | 'dc' | 'ep', auto?: boolean, onchange?: (v: '' | 'ad' | 'dc' | 'ep') => void }}
   */
  let { value = $bindable(), auto = false, onchange } = $props();

  const OPTIONS = $derived(
    /** @type {['' | 'ad' | 'dc' | 'ep', string, string][]} */ ([
      ...(auto ? [['', 'AUTO', "Follow the selected character's alliance"]] : []),
      ['ad', 'AD', 'Aldmeri Dominion'],
      ['dc', 'DC', 'Daggerfall Covenant'],
      ['ep', 'EP', 'Ebonheart Pact'],
    ]),
  );

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
  {#each OPTIONS as [key, label, name] (key)}
    <button
      type="button"
      title={name}
      aria-pressed={value === key}
      bind:this={buttons[key]}
      onclick={() => { value = key; onchange?.(key); }}>{label}</button>
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
