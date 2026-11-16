<script>
  import { tooltip } from './tooltip.svelte.js';

  /**
   * Gear slot: square with a quality-coloured inner border. When empty it shows `placeholder`
   * (the game's faded gear-slot outline) with no frame, like the in-game equipped panel.
   * `color` is the item's quality colour from the game data (e.g. item.quality_color).
   * @type {{ icon?: string, placeholder?: string, color?: string, label: string, delay?: number, tip?: import('./tooltip.svelte.js').TipContent | null, onclick?: () => void }}
   */
  let { icon = '', placeholder = '', color = 'var(--line)', label, delay = 0, tip = null, onclick } = $props();
</script>

<button type="button" class="slot" class:empty={!icon} style="--qc: {color}; --d: {delay}s" aria-label={label} use:tooltip={tip} {onclick}>
  {#if icon}<img src={icon} alt="" loading="lazy" />{:else if placeholder}<img class="ph" src={placeholder} alt="" />{/if}
</button>

<style>
  .slot {
    all: unset;
    box-sizing: border-box;
    position: relative;
    display: grid;
    place-items: center;
    aspect-ratio: 1;
    width: 100%;
    background: var(--slot-bg);
    border: 1px solid var(--line);
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.25s, border-color 0.25s;
    animation: pop 0.5s var(--ease-spring) both;
    animation-delay: var(--d);
  }
  .slot::after { content: ''; position: absolute; inset: 3px; border: 1px solid var(--qc); opacity: 0.55; pointer-events: none; }
  .slot.empty { background: none; border-color: transparent; cursor: default; }
  .slot.empty::after { display: none; }
  .slot.empty:hover { transform: none; box-shadow: none; border-color: transparent; }
  .ph { opacity: 0.28; }
  .slot:hover, .slot:focus-visible {
    transform: translateY(-2px);
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent), 0 0 22px -2px var(--qc), inset 0 0 18px -6px var(--qc);
    outline: none;
  }
  img { width: 78%; height: 78%; object-fit: contain; }
  @keyframes pop { from { opacity: 0; transform: scale(0.6); } }
</style>
