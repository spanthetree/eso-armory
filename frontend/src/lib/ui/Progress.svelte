<script>
  /** Thin gold progress bar that fills on mount. @type {{ value: number, max: number, height?: number, delay?: number }} */
  let { value, max, height = 6, delay = 0 } = $props();
  const p = $derived(max > 0 ? Math.min(100, (value / max) * 100) : 0);
</script>

<div class="track" style="height: {height}px; --d: {delay}s" role="meter" aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
  <i style="width: {p}%"></i>
</div>

<style>
  .track { position: relative; background: #000; border: 1px solid var(--line); overflow: hidden; }
  i { position: absolute; inset: 0 auto 0 0; background: linear-gradient(90deg, var(--accent), var(--accent-hi)); transform-origin: left; transition: width 0.6s var(--ease-out); animation: fill 1.1s var(--ease-out) both; animation-delay: var(--d); }
  @keyframes fill { from { transform: scaleX(0); } }
</style>
