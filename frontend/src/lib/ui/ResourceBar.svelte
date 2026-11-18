<script>
  /**
   * Magicka / Health / Stamina bar. Fills on mount, then a sheen passes over it.
   * `shown` replaces the number on the right (e.g. the max pool while the bar shows points); `note` sits beside it.
   * @type {{ kind: 'magicka' | 'health' | 'stamina', value: number, max?: number, shown?: number | null, note?: string, delay?: number }}
   */
  let { kind, value, max = value, shown = null, note = '', delay = 0 } = $props();
  const pct = $derived(max > 0 ? Math.min(100, (value / max) * 100) : 0);
</script>

<div class="bar" style="--d: {delay}s">
  <div class="row">
    <span>{kind.toUpperCase()}</span>
    <span>{#if note}<small>{note}</small>{/if}<span class="num">{(shown ?? value).toLocaleString('en-US')}</span></span>
  </div>
  <div class="track" role="meter" aria-label={kind} aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
    <div class="fill" style="background: var(--res-{kind}); width: {pct}%"></div>
  </div>
</div>

<style>
  .bar { display: grid; gap: 3px; }
  .row { display: flex; justify-content: space-between; align-items: baseline; font-size: 14px; letter-spacing: 0.06em; }
  small { margin-right: 8px; font-size: 12px; color: var(--muted); letter-spacing: 0; }
  .track { position: relative; height: 9px; background: #000; border: 1px solid var(--line); overflow: hidden; }
  .fill { position: absolute; inset: 0 auto 0 0; transform-origin: left; transition: width 0.6s var(--ease-out); animation: fill 1.4s var(--ease-out) both; animation-delay: var(--d); }
  .fill::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, #ffffff55 50%, transparent);
    transform: translateX(-100%);
    animation: sheen 3.5s ease-in-out infinite;
    animation-delay: calc(var(--d) + 1.4s);
  }
  @keyframes fill { from { transform: scaleX(0); } }
  @keyframes sheen { 0%, 60% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
  /* Classic: the game's arrow status bar frame, resource-coloured fill shaded by the generic fill texture. */
  :global(:root[data-ui='classic']) .row { font: 700 18px var(--eso-font); letter-spacing: 0; color: var(--eso-selected); text-shadow: var(--eso-shadow); }
  :global(:root[data-ui='classic']) small { font: 500 16px var(--eso-font-medium); color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .track { height: 16px; background: none; border: 0 solid transparent; border-image: var(--eso-bar-bg) 0 10 fill / 0 10px; overflow: visible; }
  :global(:root[data-ui='classic']) .track::after { content: ''; position: absolute; inset: 0; pointer-events: none; border: 0 solid transparent; border-image: var(--eso-bar-frame) 0 10 fill / 0 10px; }
  :global(:root[data-ui='classic']) .fill { inset: 2px auto 2px 2px; max-width: calc(100% - 10px); background-image: var(--eso-bar-gloss), var(--eso-bar-fill) !important; background-size: 100% 100%; background-blend-mode: normal, multiply; }
  :global(:root[data-ui='classic']) .fill::after { display: none; }
</style>
