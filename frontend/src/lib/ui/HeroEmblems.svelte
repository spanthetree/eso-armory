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
    <!-- Steep alpha ramp: threshold the blurred edge around 40% luminance, keeping a 1px-ish soft edge. -->
    <feComponentTransfer in="lum" result="shape"><feFuncA type="linear" slope="5" intercept="-2" /></feComponentTransfer>
    <feFlood class="emblem-fill" result="gold" />
    <feComposite in="gold" in2="shape" operator="in" />
  </filter>
</svg>

<div class="emblems" aria-hidden="true">
  {#each emblems as e (e.side + e.icon)}
    <svg class="emblem {e.side}" viewBox="0 0 64 64"><title>{e.label}</title>
      <image href={e.icon} width="64" height="64" filter="url(#emblem-crisp)" />
    </svg>
  {/each}
</div>

<style>
  .emblems { position: absolute; inset: 0 0 auto; height: 100%; pointer-events: none; z-index: -1; display: flex; justify-content: center; align-items: center; gap: clamp(140px, 28vw, 380px); }
  .emblem {
    width: clamp(96px, 12vw, 150px);
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
