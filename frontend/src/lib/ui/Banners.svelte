<script>
  import { allianceIcon, classIcon } from '../eso.js';

  /**
   * Backdrop: two worn obsidian swallowtail banners hanging by loops from gilt rods.
   * Class emblem on the left, faction on the right. Emblems are the game's white-on-black icons
   * used as luminance masks, so they keep their inner detail and render in gilt.
   * @type {{ cls?: string, alliance?: string }}
   */
  let { cls = '', alliance = '' } = $props();

  const W = 180;
  const H = 380;
  const L = 18; // cloth left edge
  const R = 162; // cloth right edge
  const ROD = 26; // rod centre line
  const TOP = ROD + 4; // cloth body top, just under the rod
  const TAIL = 362; // swallowtail points
  const NOTCH = 305; // swallowtail centre
  const LOOPS = [30, 60, 90, 120, 150];

  /** Small seeded PRNG so each banner's damage is stable across renders. @param {number} seed */
  function rng(seed) {
    return () => {
      seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /**
   * Ragged outline: jittered sides with one jagged tear each, frayed swallowtail, and moth holes
   * as extra sub-paths (cut out with evenodd).
   * @param {number} seed
   */
  function clothPath(seed) {
    const r = rng(seed);
    const j = (/** @type {number} */ n) => (r() - 0.5) * n;
    /** @type {[number, number][]} */
    const pts = [[L, TOP], [R, TOP]];
    const tearR = 130 + r() * 110;
    for (let y = TOP + 24; y < TAIL - 10; y += 14) {
      if (Math.abs(y - tearR) < 8) pts.push([R - 2, y - 7], [R - 8, y - 3], [R - 6, y - 1], [R - 15 - r() * 8, y + 1], [R - 7, y + 3], [R - 3, y + 7]);
      else pts.push([R + j(3), y]);
    }
    pts.push([R + j(4), TAIL + j(10)]);
    for (let i = 1; i < 8; i++) {
      const t = i / 8;
      pts.push([R + (W / 2 - R) * t + j(6), TAIL + (NOTCH - TAIL) * t + (i % 2 ? 6 + r() * 12 : 0)]);
    }
    pts.push([W / 2, NOTCH + j(8)]);
    for (let i = 1; i < 8; i++) {
      const t = i / 8;
      pts.push([W / 2 + (L - W / 2) * t + j(6), NOTCH + (TAIL - NOTCH) * t + (i % 2 ? 6 + r() * 12 : 0)]);
    }
    pts.push([L + j(4), TAIL + j(10)]);
    const tearL = 150 + r() * 110;
    for (let y = TAIL - 24; y > TOP + 18; y -= 14) {
      if (Math.abs(y - tearL) < 8) pts.push([L + 3, y + 7], [L + 7, y + 3], [L + 5, y + 1], [L + 14 + r() * 8, y - 1], [L + 8, y - 3], [L + 2, y - 7]);
      else pts.push([L + j(3), y]);
    }
    let d = 'M' + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(' L') + ' Z';
    for (let h = 0; h < 3; h++) {
      const cx = 40 + r() * 100;
      const cy = 215 + r() * 70;
      const rad = 2.5 + r() * 3.5;
      const hole = Array.from({ length: 6 }, (_, k) => {
        const a = (k / 6) * Math.PI * 2;
        const rr = rad * (0.6 + r() * 0.8);
        return `${(cx + Math.cos(a) * rr).toFixed(1)} ${(cy + Math.sin(a) * rr).toFixed(1)}`;
      });
      d += ` M${hole.join(' L')} Z`;
    }
    return d;
  }

  const banners = $derived([
    { side: 'l', icon: classIcon(cls), label: cls, d: clothPath(11) },
    { side: 'r', icon: allianceIcon(alliance), label: alliance, d: clothPath(29) },
  ]);
</script>

<div class="banners" aria-hidden="true">
  {#each banners as b (b.side)}
    {#if b.icon}
      <svg class="banner {b.side}" viewBox="-14 0 {W + 28} {H}">
        <defs>
          <filter id="wave-{b.side}" x="-10%" y="-5%" width="120%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="0.008 0.03" numOctaves="2" seed={b.side === 'l' ? 3 : 7}>
              <animate attributeName="baseFrequency" values="0.008 0.03;0.011 0.024;0.008 0.03" dur="9s" repeatCount="indefinite" />
            </feTurbulence>
            <feDisplacementMap in="SourceGraphic" scale="6" />
          </filter>
          <filter id="grime-{b.side}" x="0" y="0" width="100%" height="100%">
            <feTurbulence type="fractalNoise" baseFrequency="0.06 0.04" numOctaves="4" seed={b.side === 'l' ? 5 : 13} />
            <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1.6 -0.75" />
          </filter>
          <filter id="glow-{b.side}" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="2.5" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <linearGradient id="folds-{b.side}" x1="0" x2="1" spreadMethod="repeat" gradientTransform="scale(.42 1)">
            <stop offset="0" stop-color="#000" stop-opacity=".45" />
            <stop offset=".35" stop-color="#fff" stop-opacity=".07" />
            <stop offset=".6" stop-color="#000" stop-opacity=".15" />
            <stop offset="1" stop-color="#000" stop-opacity=".45" />
            <animateTransform attributeName="gradientTransform" type="translate" values="0 0;1 0" dur="7s" repeatCount="indefinite" additive="sum" />
          </linearGradient>
          <!-- Metal: lit from above, like a polished rod. -->
          <linearGradient id="metal-{b.side}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" class="m-hi" />
            <stop offset=".45" class="m-mid" />
            <stop offset="1" class="m-lo" />
          </linearGradient>
          <clipPath id="cloth-{b.side}"><path d={b.d} clip-rule="evenodd" /></clipPath>
          <mask id="emblem-{b.side}"><image href={b.icon} x="44" y="84" width="92" height="92" /></mask>
        </defs>

        <!-- Hanging cord from the rod ends to a ring. -->
        <path class="cord" d="M10 {ROD} L{W / 2} 7 L{W - 10} {ROD}" />
        <circle class="ring" cx={W / 2} cy="5" r="3.5" />

        <!-- Cloth (rippled). -->
        <g filter="url(#wave-{b.side})">
          <g clip-path="url(#cloth-{b.side})">
            <rect class="cloth" width={W} height={H} />
            <rect width={W} height={H} fill="url(#folds-{b.side})" />
            <rect width={W} height={H} filter="url(#grime-{b.side})" opacity=".25" />
            <path class="trim" d="M{L + 9} {TOP + 14} H{R - 9} V{TAIL - 24} L{W / 2} {NOTCH - 14} L{L + 9} {TAIL - 24} Z" />
            <path class="trim" d="M{L + 13} {TOP + 18} H{R - 13} V{TAIL - 30} L{W / 2} {NOTCH - 21} L{L + 13} {TAIL - 30} Z" opacity=".5" />
            <g filter="url(#glow-{b.side})"><rect class="emblem" width={W} height={H} mask="url(#emblem-{b.side})" /></g>
            <!-- Inner stroke along the torn outline so tears and holes read against the page. -->
            <path class="edge" d={b.d} />
          </g>
        </g>

        <!-- Rod with finials, then cloth loops in front of it. Not rippled. -->
        <rect x="2" y={ROD - 3.5} width={W - 4} height="7" rx="3.5" fill="url(#metal-{b.side})" />
        {#each [2, W - 2] as x, i (x)}
          <g transform="translate({x} {ROD}) scale({i ? 1 : -1} 1)" fill="url(#metal-{b.side})">
            <rect x="-1" y="-6" width="4" height="12" rx="1.2" />
            <circle cx="6.5" r="3.6" />
            <path d="M9.5 0 L13 -5 L23 0 L13 5 Z" />
          </g>
        {/each}
        {#each LOOPS as x (x)}
          <rect class="loop" x={x - 7} y={ROD - 6} width="14" height={TOP - ROD + 9} rx="2" />
        {/each}
      </svg>
    {/if}
  {/each}
</div>

<style>
  .banners { position: absolute; inset: 0 0 auto; height: 600px; pointer-events: none; overflow: hidden; z-index: -1; }
  .banner {
    position: absolute;
    top: 0;
    width: clamp(100px, 13vw, 160px);
    transform-origin: 50% 1%;
    animation: sway 9s ease-in-out infinite alternate, drop 1.2s var(--ease-out) both;
    -webkit-mask-image: linear-gradient(to bottom, #000 80%, transparent 100%);
    mask-image: linear-gradient(to bottom, #000 80%, transparent 100%);
  }
  .banner.l { left: 2%; }
  .banner.r { right: 2%; animation-delay: -4.5s, 0.15s; }
  /* Obsidian cloth and fixed gilt; banners do not follow the alliance tint. */
  .cloth { fill: #0d0c0b; }
  .trim { fill: none; stroke: var(--gilt); stroke-width: 1.2; opacity: 0.75; }
  .edge { fill: none; stroke: var(--gilt); stroke-width: 2.4; opacity: 0.35; }
  .emblem { fill: var(--gilt-hi); opacity: 0.9; }
  .loop { fill: #100e0c; stroke: color-mix(in srgb, var(--gilt) 55%, transparent); stroke-width: 0.8; }
  .cord { fill: none; stroke: var(--gilt); stroke-width: 1.2; opacity: 0.8; }
  .ring { fill: none; stroke: var(--gilt-hi); stroke-width: 1.6; }
  .m-hi { stop-color: var(--gilt-hi); }
  .m-mid { stop-color: var(--gilt); }
  .m-lo { stop-color: color-mix(in srgb, var(--gilt) 40%, #000); }
  @keyframes sway { from { transform: rotate(-1.2deg); } to { transform: rotate(1.2deg); } }
  @keyframes drop { from { translate: 0 -30%; opacity: 0; } }
  @media (max-width: 560px) { .banner { opacity: 0.45; } }
</style>
