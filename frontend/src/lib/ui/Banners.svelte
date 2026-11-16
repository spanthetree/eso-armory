<script>
  import { allianceIcon, classIcon } from '../eso.js';

  /**
   * Backdrop: two hanging swallowtail banners. Class emblem on the left, faction on the right.
   * Icons are white game silhouettes used as masks, so they take the alliance accent colour.
   * @type {{ cls?: string, alliance?: string }}
   */
  let { cls = '', alliance = '' } = $props();

  const banners = $derived([
    { side: 'l', icon: classIcon(cls), label: cls },
    { side: 'r', icon: allianceIcon(alliance), label: alliance },
  ]);
</script>

<!-- Ripple filter for the cloth; shared by both banners. -->
<svg width="0" height="0" aria-hidden="true" style="position: absolute">
  <filter id="banner-wave" x="-10%" y="-5%" width="120%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.03" numOctaves="2" seed="3">
      <animate attributeName="baseFrequency" values="0.008 0.03;0.011 0.024;0.008 0.03" dur="9s" repeatCount="indefinite" />
    </feTurbulence>
    <feDisplacementMap in="SourceGraphic" scale="7" />
  </filter>
</svg>

<div class="banners" aria-hidden="true">
  {#each banners as b (b.side)}
    {#if b.icon}
      <div class="banner {b.side}" title={b.label}>
        <div class="pole"></div>
        <div class="cloth">
          <div class="trim"></div>
          <div class="emblem" style="--icon: url('{b.icon}')"></div>
          <div class="folds"></div>
        </div>
      </div>
    {/if}
  {/each}
</div>

<style>
  .banners { position: absolute; inset: 0 0 auto; height: 560px; pointer-events: none; overflow: hidden; z-index: -1; }
  .banner {
    position: absolute;
    top: 0;
    width: clamp(90px, 13vw, 160px);
    opacity: 0.6;
    transform-origin: 50% 0;
    animation: sway 9s ease-in-out infinite alternate, drop 1.2s var(--ease-out) both;
    -webkit-mask-image: linear-gradient(to bottom, #000 55%, transparent 100%);
    mask-image: linear-gradient(to bottom, #000 55%, transparent 100%);
  }
  .banner.l { left: 3%; }
  .banner.r { right: 3%; animation-delay: -4.5s, 0.15s; }
  .pole { height: 9px; margin: 0 -8px; border-radius: 4px; background: var(--accent-hi); }
  .cloth {
    position: relative;
    aspect-ratio: 152 / 474;
    margin: 0 4px;
    background: color-mix(in srgb, var(--accent) 38%, #0a0806);
    clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 90%, 0 100%);
    filter: url(#banner-wave);
  }
  .trim {
    position: absolute;
    inset: 10px 10px 0;
    border: 2px solid var(--accent);
    border-bottom: 0;
    clip-path: polygon(0 0, 100% 0, 100% 95%, 50% 86%, 0 95%);
  }
  .emblem {
    position: absolute;
    left: 50%;
    top: 20%;
    width: 64%;
    aspect-ratio: 1;
    translate: -50% 0;
    background: var(--accent-hi);
    /* Icons are white with black inner detail, so mask by luminance, not alpha. */
    -webkit-mask: var(--icon) center / contain no-repeat;
    mask: var(--icon) center / contain no-repeat luminance;
  }
  .folds {
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(90deg, #0000007f 0, #ffffff1a 22%, #00000033 34%, #0000007f 50%);
    background-size: 200% 100%;
    animation: folds 7s linear infinite;
  }
  @keyframes sway { from { transform: rotate(-1.2deg) skewX(0.8deg); } to { transform: rotate(1.2deg) skewX(-0.8deg); } }
  @keyframes drop { from { translate: 0 -40%; opacity: 0; } }
  @keyframes folds { to { background-position: -200% 0; } }
  @media (max-width: 560px) { .banner { opacity: 0.35; } }
</style>
