<script>
  /**
   * ZO_ArrowStatusBarWithBG: frame background, fill tinted with the XP gradient (ZO_XP_BAR_GRADIENT_COLORS, spanning the
   * whole bar like ZO_StatusBar_SetGradientColor), gloss, leading edge, frame overlay. `text`: 'always', 'hover'
   * (ZO_ResponsiveArrowBarBehavior) or 'none'.
   * @type {{ value: number, max: number, text?: 'always' | 'hover' | 'none', label?: string, style?: string }}
   */
  let { value, max, text = 'always', label, style = '' } = $props();
  const p = $derived(max > 0 ? Math.max(0, Math.min(1, value / max)) : 0);
  const fmt = (/** @type {number} */ n) => (n ?? 0).toLocaleString('en-US');
</script>

<div class="bar" class:hover={text === 'hover'} {style} style:--p={p} role="progressbar" aria-label={label} aria-valuenow={value} aria-valuemin="0" aria-valuemax={max}>
  <i class="l bg"></i><i class="m bg"></i><i class="r bg"></i>
  {#if p > 0}<i class="fill"></i><i class="edge"></i>{/if}
  <i class="l fr"></i><i class="m fr"></i><i class="r fr"></i>
  {#if text !== 'none'}<span class="txt">{fmt(value)}/{fmt(max)}</span>{/if}
</div>

<style>
  .bar { position: relative; height: 20px; container-type: inline-size; }
  i { position: absolute; top: 0; height: 20px; background-size: 100% 100%; }
  .l { left: 0; width: 10px; }
  .r { right: 0; width: 10px; }
  .m { left: 10px; right: 10px; }
  .l.bg { background-image: var(--eso-bar-bg-l); }
  .m.bg { background-image: var(--eso-bar-bg-m); }
  .r.bg { background-image: var(--eso-bar-bg-r); }
  .l.fr { background-image: var(--eso-bar-frame-l); }
  .m.fr { background-image: var(--eso-bar-frame-m); }
  .r.fr { background-image: var(--eso-bar-frame-r); }
  .fill {
    left: 0; width: calc(var(--p) * (100% - 8px));
    background-image: var(--eso-bar-gloss), var(--eso-bar-fill), linear-gradient(90deg, var(--eso-xp-start), var(--eso-xp-end));
    background-size: 100% 100%, 100% 100%, 100cqw 100%;
    background-blend-mode: normal, multiply, normal;
  }
  .edge {
    left: calc(var(--p) * (100% - 8px)); width: 8px;
    background-image: var(--eso-bar-edge-gloss), var(--eso-bar-edge), linear-gradient(color-mix(in srgb, var(--eso-xp-start), var(--eso-xp-end) calc(var(--p) * 100%)) 0 0);
    background-blend-mode: normal, multiply, normal;
    mask: var(--eso-bar-edge) 0 0 / 100% 100%;
  }
  .txt { position: absolute; inset: -1px 0 0; display: grid; place-items: center; font: 700 16px/1 var(--eso-font); color: var(--eso-selected); text-shadow: var(--eso-shadow); }
  .hover .txt { opacity: 0; transition: opacity 0.15s; }
  .hover:hover .txt { opacity: 1; }
</style>
