<script>
  import { allianceIcon, classIcon } from '../eso.js';

  /**
   * Large faint class (left) and faction (right) emblems behind the character name.
   * The game icons are white with black detail, so they are luminance masks filled with gold.
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

<div class="emblems" aria-hidden="true">
  {#each emblems as e (e.side + e.icon)}
    <div class="emblem {e.side}" style="--icon: url('{e.icon}')" title={e.label}></div>
  {/each}
</div>

<style>
  .emblems { position: absolute; inset: -10px 0 auto; height: 100%; pointer-events: none; z-index: -1; display: flex; justify-content: center; gap: clamp(120px, 26vw, 360px); }
  .emblem {
    width: clamp(110px, 16vw, 190px);
    aspect-ratio: 1;
    background: radial-gradient(circle, var(--accent-hi), var(--accent) 70%);
    -webkit-mask: var(--icon) center / contain no-repeat;
    mask: var(--icon) center / contain no-repeat luminance;
    opacity: 0.16;
    filter: drop-shadow(0 0 18px var(--accent));
    animation: emerge 1.4s var(--ease-out) both, breathe 6s ease-in-out 1.4s infinite alternate;
  }
  .emblem.r { animation-delay: 0.15s, 1.55s; }
  @keyframes emerge { from { opacity: 0; transform: scale(0.85); filter: blur(6px); } }
  @keyframes breathe { to { opacity: 0.22; } }
  @media (max-width: 560px) { .emblems { gap: 40px; } .emblem { opacity: 0.1; } }
</style>
