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
  {#if tip.content}{@render tip.content.snippet(tip.content.arg)}{/if}
</div>

<style>
  .tip {
    position: fixed;
    z-index: 100;
    width: 290px;
    max-width: calc(100vw - 16px);
    pointer-events: none;
    padding: 12px 14px;
    text-align: center;
    color: var(--fg);
    background: linear-gradient(#0e0c0a, #050505);
    border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--line));
    box-shadow: 0 10px 40px #000c;
    opacity: 0;
    transform: translateY(6px) scale(0.98);
    transition: opacity 0.16s, transform 0.2s var(--ease-spring);
  }
  .tip.on { opacity: 1; transform: none; }
  /* Shared tooltip content styles, used by snippets rendered inside. */
  .tip :global(.t-name) { font: 600 16px var(--f-display); letter-spacing: 0.05em; }
  .tip :global(.t-row) { display: flex; justify-content: space-between; gap: 12px; font-size: 14px; color: var(--muted); }
  .tip :global(hr) { border: 0; height: 1px; margin: 8px 0; background: linear-gradient(90deg, transparent, var(--accent), transparent); }
  .tip :global(.t-off) { opacity: 0.45; }
</style>
