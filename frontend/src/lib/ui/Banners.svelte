<script>
  import { allianceIcon, classIcon } from '../eso.js';

  /**
   * Backdrop: two worn swallowtail banners hanging from wooden rods. Class emblem on the left,
   * faction on the right. Emblems are the game's white-on-black icons used as luminance masks,
   * so they keep their inner detail and take the alliance accent colour.
   * @type {{ cls?: string, alliance?: string }}
   */
  let { cls = '', alliance = '' } = $props();

  const W = 180;
  const H = 370;
  const L = 18; // cloth left edge
  const R = 162; // cloth right edge
  const ROD = 32; // rod centre line
  const TOP = 27; // cloth top (sleeve wraps the rod)
  const TAIL = 355; // swallowtail points
  const NOTCH = 300; // swallowtail centre

  /** Small seeded PRNG so each banner's damage is stable across renders. */
  function rng(seed) {
    return () => {
      seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /**
   * Ragged outline: jittered sides with one or two tears, frayed swallowtail, plus moth holes
   * as extra sub-paths (drawn with evenodd so they cut through).
   * @param {number} seed
   */
  function clothPath(seed) {
    const r = rng(seed);
    const j = (n) => (r() - 0.5) * n;
    /** @type {[number, number][]} */
    const pts = [[L, TOP], [R, TOP]];
    const tearR = 130 + r() * 110;
    for (let y = TOP + 24; y < TAIL - 10; y += 14) {
      if (Math.abs(y - tearR) < 9) pts.push([R - 2, y - 7], [R - 8, y - 3], [R - 6, y - 1], [R - 14 - r() * 8, y + 1], [R - 7, y + 3], [R - 3, y + 7]);
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
      if (Math.abs(y - tearL) < 9) pts.push([L + 3, y + 7], [L + 7, y + 3], [L + 5, y + 1], [L + 13 + r() * 8, y - 1], [L + 8, y - 3], [L + 2, y - 7]);
      else pts.push([L + j(3), y]);
    }
    let d = 'M' + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(' L') + ' Z';
    for (let h = 0; h < 3; h++) {
      const cx = 40 + r() * 100;
      const cy = 200 + r() * 80;
      const rad = 2.5 + r() * 4;
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
      <svg class="banner {b.side}" viewBox="-12 0 {W + 24} {H}">
        <title>{b.label}</title>
        <defs>
          <filter id="wave-{b.side}" x="-10%" y="-5%" width="120%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="0.008 0.03" numOctaves="2" seed={b.side === 'l' ? 3 : 7}>
              <animate attributeName="baseFrequency" values="0.008 0.03;0.011 0.024;0.008 0.03" dur="9s" repeatCount="indefinite" />
            </feTurbulence>
            <feDisplacementMap in="SourceGraphic" scale="7" />
          </filter>
          <filter id="grime-{b.side}" x="0" y="0" width="100%" height="100%">
            <feTurbulence type="fractalNoise" baseFrequency="0.06 0.04" numOctaves="4" seed={b.side === 'l' ? 5 : 13} />
            <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1.6 -0.75" />
          </filter>
          <linearGradient id="folds-{b.side}" x1="0" x2="1" spreadMethod="repeat" gradientTransform="scale(.42 1)">
            <stop offset="0" stop-color="#000" stop-opacity=".5" />
            <stop offset=".35" stop-color="#fff" stop-opacity=".1" />
            <stop offset=".6" stop-color="#000" stop-opacity=".2" />
            <stop offset="1" stop-color="#000" stop-opacity=".5" />
            <animateTransform attributeName="gradientTransform" type="translate" values="0 0;1 0" dur="7s" repeatCount="indefinite" additive="sum" />
          </linearGradient>
          <linearGradient id="fade-{b.side}" x1="0" y1="0" x2="0" y2="1">
            <stop offset=".45" stop-color="#000" stop-opacity="0" />
            <stop offset="1" stop-color="#000" stop-opacity=".55" />
          </linearGradient>
          <linearGradient id="wood-{b.side}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="#1a0f07" />
            <stop offset=".35" stop-color="#6b4a2a" />
            <stop offset=".6" stop-color="#3a2614" />
            <stop offset="1" stop-color="#120a05" />
          </linearGradient>
          <clipPath id="cloth-{b.side}"><path d={b.d} clip-rule="evenodd" /></clipPath>
          <mask id="emblem-{b.side}"><image href={b.icon} x="42" y="78" width="96" height="96" /></mask>
        </defs>

        <g filter="url(#wave-{b.side})">
          <g clip-path="url(#cloth-{b.side})">
            <rect class="cloth" width={W} height={H} />
            <path class="trim" d="M{L + 9} {TOP + 22} H{R - 9} V{TAIL - 22} L{W / 2} {NOTCH - 12} L{L + 9} {TAIL - 22} Z" />
            <rect class="sleeve" x="0" y={TOP} width={W} height="14" />
            <rect class="emblem" width={W} height={H} mask="url(#emblem-{b.side})" />
            <rect width={W} height={H} fill="url(#folds-{b.side})" />
            <rect width={W} height={H} filter="url(#grime-{b.side})" opacity=".55" />
            <rect width={W} height={H} fill="url(#fade-{b.side})" />
          </g>
        </g>

        <!-- Support: hanging cord and hook, wooden rod through the sleeve, metal finials. Not rippled. -->
        <path class="cord" d="M22 {ROD} L{W / 2} 5 L{W - 22} {ROD}" />
        <circle class="hook" cx={W / 2} cy="5" r="3.2" />
        <rect x="8" y={ROD - 5} width={W - 16} height="10" rx="5" fill="url(#wood-{b.side})" />
        <rect x="8" y={ROD - 3} width={W - 16} height="1.2" fill="#ffffff22" />
        {#each [8, W - 8] as x, i (x)}
          <g class="finial" transform="translate({x} {ROD}) scale({i ? 1 : -1} 1)">
            <rect x="-2" y="-6.5" width="4" height="13" rx="1.5" />
            <circle cx="5" r="4" />
            <path d="M8 0 L12 -5 L24 0 L12 5 Z" />
          </g>
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
    opacity: 0.8;
    transform-origin: 50% 1%;
    animation: sway 9s ease-in-out infinite alternate, drop 1.2s var(--ease-out) both;
  }
  .banner.l { left: 2%; }
  .banner.r { right: 2%; animation-delay: -4.5s, 0.15s; }
  .cloth { fill: color-mix(in srgb, var(--accent) 38%, #0a0806); }
  .trim { fill: none; stroke: var(--accent); stroke-width: 2; opacity: 0.8; }
  .emblem { fill: var(--accent-hi); opacity: 0.85; }
  .sleeve { fill: #00000055; }
  .cord { fill: none; stroke: #8a7350; stroke-width: 1.4; stroke-dasharray: 2.2 1; }
  .hook { fill: none; stroke: color-mix(in srgb, var(--accent-hi) 70%, #6b5a3a); stroke-width: 1.6; }
  .finial { fill: color-mix(in srgb, var(--accent-hi) 75%, #6b5a3a); }
  @keyframes sway { from { transform: rotate(-1.2deg); } to { transform: rotate(1.2deg); } }
  @keyframes drop { from { translate: 0 -30%; opacity: 0; } }
  @media (max-width: 560px) { .banner { opacity: 0.4; } }
</style>
