<script>
  /**
   * Small segmented control with a sliding gold pill.
   * @type {{ options: { id: string, label: string }[], value: string, label: string, onchange: (id: string) => void }}
   */
  let { options, value, label, onchange } = $props();

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

<div class="seg" role="group" aria-label={label}>
  <span class="pill" style="left: {pill.left}px; width: {pill.width}px"></span>
  {#each options as o (o.id)}
    <button type="button" aria-pressed={value === o.id} bind:this={buttons[o.id]} onclick={() => value !== o.id && onchange(o.id)}>{o.label.toUpperCase()}</button>
  {/each}
</div>

<style>
  .seg { position: relative; display: inline-flex; gap: 4px; padding: 3px; border: 1px solid var(--line); background: #00000066; }
  button { all: unset; position: relative; z-index: 1; cursor: pointer; padding: 4px 10px; font: 500 12px var(--f-display); letter-spacing: 0.12em; color: var(--muted); transition: color 0.3s; }
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
