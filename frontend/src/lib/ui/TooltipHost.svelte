<script>
  import { tip } from './tooltip.svelte.js';

  const GAP = 12;
  const EDGE = 8;

  /** @type {HTMLElement} */
  let el;
  let pos = $state({ x: 0, y: 0 });

  // Right of the anchor, flipped left when it would leave the screen; clamped vertically.
  $effect(() => {
    if (!tip.open || !tip.anchor || !el) return;
    tip.content; // re-measure when content changes
    const a = tip.anchor;
    const w = el.offsetWidth;
    const h = el.offsetHeight;
    let x = a.right + GAP;
    if (x + w > innerWidth - EDGE) x = Math.max(EDGE, a.left - w - GAP);
    const y = Math.max(EDGE, Math.min(a.top, innerHeight - h - EDGE));
    pos = { x, y };
  });

  const close = () => (tip.open = false);
</script>

<svelte:window onscroll={close} onkeydown={(e) => e.key === 'Escape' && close()} />

<div class="tip" class:on={tip.open} role="tooltip" bind:this={el} style="left: {pos.x}px; top: {pos.y}px">
  {#if tip.content}<tip.content.component {...tip.content.props} />{/if}
</div>

<style>
  .tip {
    position: fixed;
    z-index: 100;
    width: 290px;
    max-width: calc(100vw - 16px);
    pointer-events: none;
    padding: 12px 14px;
    color: var(--fg);
    background: linear-gradient(#0e0c0a, #050505);
    border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--line));
    box-shadow: 0 10px 40px #000c;
    opacity: 0;
    transform: translateY(6px) scale(0.98);
    transition: opacity 0.16s, transform 0.2s var(--ease-spring);
  }
  .tip.on { opacity: 1; transform: none; }
  /* Shared tooltip content styles, used by the tooltip components rendered inside. */
  .tip :global(.t-name) { font: 600 16px var(--f-display); letter-spacing: 0.05em; line-height: 1.25; margin-bottom: 4px; }
  .tip :global(.t-head) { display: flex; justify-content: space-between; gap: 12px; font-size: 13px; color: var(--muted); margin-bottom: 2px; }
  .tip :global(.t-chips) { display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0; }
  .tip :global(.t-chip) { font-size: 12px; padding: 1px 6px; color: var(--muted); border: 1px solid var(--line); background: #ffffff08; }
  .tip :global(.t-small) { font-size: 13px; line-height: 1.35; }
  .tip :global(.t-faint) { font-size: 11px; color: var(--muted); opacity: 0.6; margin-top: 6px; }
  .tip :global(.t-row) { display: flex; justify-content: space-between; gap: 12px; font-size: 14px; color: var(--muted); }
  .tip :global(hr) { border: 0; height: 1px; margin: 8px 0; background: linear-gradient(90deg, transparent, var(--accent), transparent); }
  .tip :global(.t-off) { opacity: 0.45; }

  /* Classic: the game's tooltip (ZO_BaseTooltip: ui-border + tooltip centre + munge overlay). */
  :global(:root[data-ui='classic']) .tip { background: url('/assets/esoui/tooltips/munge_overlay.png') repeat, #000a; border: 0 solid transparent; border-image: var(--eso-backdrop) 16 fill / 16px;
    padding: 16px 18px; font-family: var(--eso-font-medium); text-shadow: var(--eso-shadow-thin); }
  :global(:root[data-ui='classic']) .tip :global(.t-name) { font: 700 20px var(--eso-font); letter-spacing: 0; text-transform: uppercase; text-align: center; }
  :global(:root[data-ui='classic']) .tip :global(.t-head) { font: 700 16px var(--eso-font); color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .tip :global(.t-row) { font: 500 16px var(--eso-font-medium); color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .tip :global(.t-small) { font: 500 16px var(--eso-font-medium); }
  :global(:root[data-ui='classic']) .tip :global(.t-faint) { font: 500 14px var(--eso-font-medium); color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .tip :global(.t-chip) { font: 500 14px var(--eso-font-medium); border-color: var(--line); background: #0006; }
  :global(:root[data-ui='classic']) .tip :global(hr) { height: 8px; margin: 8px 0; background: url('/assets/esoui/miscellaneous/horizontaldivider.png') center / 100% 8px no-repeat; }
</style>
