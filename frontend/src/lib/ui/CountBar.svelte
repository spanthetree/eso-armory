<script>
  /**
   * In-game style progress bar: a teal fill with "value/max" printed over it.
   * @type {{ value: number, max: number, big?: boolean, label?: string }}
   */
  let { value, max, big = false, label } = $props();
  const fmt = (/** @type {number} */ n) => (n ?? 0).toLocaleString('en-US');
</script>

<span class="bar" class:big role="progressbar" aria-label={label} aria-valuenow={value} aria-valuemin="0" aria-valuemax={max}>
  <span class="fill" style="width: {max ? Math.min(100, (value / max) * 100) : 0}%"></span>
  <span class="bt num">{fmt(value)}/{fmt(max)}</span>
</span>

<style>
  .bar { position: relative; display: block; height: 16px; background: #0b1114; border: 1px solid #3a4a52; box-shadow: inset 0 1px 3px #000; overflow: hidden; }
  .bar.big { height: 20px; }
  .fill { position: absolute; inset: 0 auto 0 0; background: linear-gradient(#9fe3f2, #4aa7c4 45%, #2f7f9d); box-shadow: 0 0 8px #5cc3e080; transition: width 0.8s var(--ease-out); }
  .bt { position: relative; display: block; text-align: center; font-size: 12px; line-height: 14px; color: #fff; text-shadow: 0 0 3px #000, 0 0 2px #000; }
  .big .bt { line-height: 18px; font-size: 13px; }
</style>
