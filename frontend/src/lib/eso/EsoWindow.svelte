<script>
  import './eso.css';
  import { onMount } from 'svelte';
  import { installEsoArt, ART } from './tex.js';

  /**
   * The game's keyboard "right panel" window (ZO_RightFootPrintBackground + ZO_TreeUnderlay + ZO_PanelTitle) drawn on a
   * 995x800 stage in the game's own pixels, scaled down to fit the tab. Children are positioned in stage pixels.
   * @type {{ title: string, children: import('svelte').Snippet }}
   */
  let { title, children } = $props();

  let box = $state(/** @type {HTMLElement | undefined} */ (undefined));
  let scale = $state(1);
  onMount(() => {
    installEsoArt();
    const fit = () => box && (scale = Math.min(1, box.clientWidth / 995, box.clientHeight / 800));
    const ro = new ResizeObserver(fit);
    if (box) ro.observe(box);
    fit();
    return () => ro.disconnect();
  });
</script>

<div class="eso-win" bind:this={box}>
  <div class="eso-stage" style="transform: translateX(-50%) scale({scale}); transform-origin: top center">
    <!-- y = -50 is the texture top: the game anchors these 75px above the panel, which itself sits 380px above screen centre -->
    <img class="eso-bg" src="{ART}miscellaneous/centerscreen_left.png" alt="" style="left: 0; top: -50px; width: 1024px; height: 1024px" />
    <img class="eso-bg" src="{ART}miscellaneous/centerscreen_indexarea_left.png" alt="" style="left: 0; top: -50px; width: 256px; height: 1024px" />
    <img class="eso-bg" src="{ART}miscellaneous/centerscreen_indexarea_right.png" alt="" style="left: 256px; top: -50px; width: 128px; height: 1024px" />
    <h2 class="title eso-abs">{title}</h2>
    <div class="eso-divider eso-abs" style="left: 61px; top: 64px; width: 904px"><i></i><i></i><i></i></div>
    {@render children()}
  </div>
</div>

<style>
  .eso-win { mask-image: linear-gradient(transparent, #000 24px, #000 calc(100% - 24px), transparent); }
  .title { left: 51px; top: 28px; margin: 0; font: 700 30px/34px var(--eso-font); letter-spacing: 0; text-transform: uppercase; color: var(--eso-selected); }
</style>
