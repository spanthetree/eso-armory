<script>
  /**
   * Magicka / Health / Stamina bar. Fills on mount, then a sheen passes over it.
   * @type {{ kind: 'magicka' | 'health' | 'stamina', value: number, max?: number, delay?: number }}
   */
  let { kind, value, max = value, delay = 0 } = $props();
  const pct = $derived(max > 0 ? Math.min(100, (value / max) * 100) : 0);
</script>

<div class="bar" style="--d: {delay}s">
  <div class="row"><span>{kind.toUpperCase()}</span><span class="num">{value.toLocaleString('en-US')}</span></div>
  <div class="track" role="meter" aria-label={kind} aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
    <div class="fill" style="background: var(--res-{kind}); width: {pct}%"></div>
  </div>
</div>

<style>
  .bar { display: grid; gap: 3px; }
  .row { display: flex; justify-content: space-between; font-size: 14px; letter-spacing: 0.06em; }
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
</style>
