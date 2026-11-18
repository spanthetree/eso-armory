<script>
  import { allianceIcon, classIcon } from '../eso.js';

  /**
   * Large faint class (left) and faction (right) emblems behind the character name.
   * The game icons are 64px white-on-black silhouettes. An SVG filter turns luminance into alpha
   * and steepens it, so the soft edges from upscaling become a crisp gold edge.
   * @type {{ cls?: string, alliance?: string }}
   */
  let { cls = '', alliance = '' } = $props();

  const emblems = $derived(
    [
      { side: 'l', icon: classIcon(cls), label: cls },
      { side: 'r', icon: allianceIcon(alliance), label: alliance },
    ].filter((e) => e.icon),
  );
</script>

<svg width="0" height="0" aria-hidden="true" style="position: absolute">
  <filter id="emblem-crisp" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">
    <feColorMatrix type="luminanceToAlpha" result="lum" />
    <!-- Moderate alpha ramp: firms up the blurred edge without exaggerating stair-steps baked into the 64px sources. -->
    <feComponentTransfer in="lum" result="shape"><feFuncA type="linear" slope="3" intercept="-1.1" /></feComponentTransfer>
    <feFlood class="emblem-fill" result="gold" />
    <feComposite in="gold" in2="shape" operator="in" />
  </filter>
</svg>

<div class="emblems" aria-hidden="true">
  {#each emblems as e (e.side + e.icon)}
    <!-- Large viewBox so the filter runs at high resolution on a smoothly upscaled image, not at 64px. -->
    <svg class="emblem {e.side}" viewBox="0 0 512 512"><title>{e.label}</title>
      <image href={e.icon} width="512" height="512" preserveAspectRatio="xMidYMid meet" style="image-rendering: auto" filter="url(#emblem-crisp)" />
    </svg>
  {/each}
</div>

<style>
  .emblems { position: absolute; inset: 0 0 auto; height: 100%; pointer-events: none; z-index: -1; display: flex; justify-content: center; align-items: center; gap: clamp(140px, 28vw, 380px); }
  /* As tall as the hero (sub line + name), so they never spill under the top bar. */
  .emblem {
    height: min(100%, 130px);
    width: auto;
    aspect-ratio: 1;
    opacity: 0.16;
    filter: drop-shadow(0 0 14px var(--accent));
    animation: emerge 1.4s var(--ease-out) both, breathe 6s ease-in-out 1.4s infinite alternate;
  }
  .emblem.r { animation-delay: 0.15s, 1.55s; }
  :global(.emblem-fill) { flood-color: var(--accent-hi); }
  @keyframes emerge { from { opacity: 0; transform: scale(0.85); } }
  @keyframes breathe { to { opacity: 0.22; } }
  @media (max-width: 560px) { .emblems { gap: 40px; } .emblem { opacity: 0.1; } }
</style>
