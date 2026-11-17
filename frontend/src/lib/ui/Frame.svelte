<script>
  /**
   * Obsidian panel: translucent black with gold rules that draw outward from the centre.
   * @type {{ title?: string, delay?: number, children: import('svelte').Snippet }}
   */
  let { title = '', delay = 0, children } = $props();
</script>

<section class="frame" style="--d: {delay}s">
  {#if title}<h5>{title}</h5>{/if}
  {@render children()}
</section>

<style>
  .frame {
    position: relative;
    background: var(--panel);
    padding: 12px 16px 14px;
    backdrop-filter: blur(3px);
    animation: rise 0.7s var(--ease-out) both;
    animation-delay: var(--d);
  }
  .frame::before {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    --rule: linear-gradient(90deg, transparent, var(--accent) 15%, var(--accent-hi) 50%, var(--accent) 85%, transparent);
    background: var(--rule) top / 100% 1px no-repeat, var(--rule) bottom / 100% 1px no-repeat;
    animation: draw 1s var(--ease-out) both;
    animation-delay: var(--d);
  }
  h5 { color: var(--fg); font-size: 13px; letter-spacing: 0.18em; text-align: center; margin-bottom: 10px; }
  @keyframes draw { from { clip-path: inset(0 50% 0 50%); } }
  @keyframes rise { from { opacity: 0; transform: translateY(14px); filter: blur(4px); } }

  /* Classic: the game's soft-edged translucent window backdrop, a ZoFontWinH2-style title over horizontalDivider. */
  :global(:root[data-ui='classic']) .frame { background: url('/assets/esoui/miscellaneous/centerscreen_left.png') center / 100% 100%; backdrop-filter: none; padding: 10px 16px 14px; }
  :global(:root[data-ui='classic']) .frame::before { display: none; }
  :global(:root[data-ui='classic']) h5 { font: 700 18px var(--eso-font); letter-spacing: 0; text-transform: uppercase; color: var(--eso-selected); margin-bottom: 6px; padding-bottom: 7px;
    background: url('/assets/esoui/miscellaneous/horizontaldivider.png') bottom center / min(512px, 100%) 8px no-repeat; }
</style>
