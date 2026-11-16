<script>
  import Frame from '../ui/Frame.svelte';
  import Slot from '../ui/Slot.svelte';
  import ItemTip from '../tips/ItemTip.svelte';
  import { SLOT_LABELS, slotIcon } from '../gear.js';

  /**
   * The in-game "Equipped" panel: race silhouette ringed by apparel, then accessories and both weapon bars.
   * Empty slots show the game's faded gear-slot outline.
   * @type {{ gear: Record<number, any>, race?: string, gender?: string, setCount: (item: any) => number }}
   */
  let { gear, race = '', gender = '', setCount } = $props();

  // The game has three body silhouettes; every other race uses the human one.
  const body = $derived(race === 'Argonian' ? 'argonian' : race === 'Khajiit' ? 'khajiit' : 'human');
  // gender comes from iasync >= 1.4.0; older data has none and uses the male figure.
  const sex = $derived(gender === 'female' ? 'female' : 'male');

  const PH = /** @type {Record<number, string>} */ ({
    0: 'head', 3: 'shoulders', 2: 'chest', 16: 'hands', 6: 'belt', 8: 'legs', 9: 'feet',
    10: 'costume', 1: 'neck', 11: 'ring', 12: 'ring',
    4: 'mainhand', 5: 'offhand', 13: 'poison', 20: 'mainhand', 21: 'offhand', 14: 'poison',
  });
  // Apparel around the figure, as in game: head above; shoulders/hands/legs left; chest/waist/feet right.
  const APPAREL = [
    { s: 0, c: 2, r: 1 },
    { s: 3, c: 1, r: 2 }, { s: 16, c: 1, r: 3 }, { s: 8, c: 1, r: 4 },
    { s: 2, c: 3, r: 2 }, { s: 6, c: 3, r: 3 }, { s: 9, c: 3, r: 4 },
  ];
  const ACCESSORIES = [10, 1, 11, 12];
  const WEAPON_ROWS = [[4, 5, 13], [20, 21, 14]];
</script>

{#snippet slot(/** @type {number} */ s, /** @type {number} */ delay)}
  {@const item = gear[s]}
  <Slot
    label={item ? `${SLOT_LABELS[s]}: ${item.name}` : `${SLOT_LABELS[s]}: empty`}
    icon={item ? slotIcon(s, item) : ''}
    placeholder="/assets/interface/gearslot_{PH[s]}.png"
    color={item?.quality_color}
    {delay}
    tip={item ? { component: ItemTip, props: { item, slotLabel: SLOT_LABELS[s], equippedFromSet: setCount(item) } } : null} />
{/snippet}

<Frame title="EQUIPPED" delay={0.05}>
  <div class="label">Apparel</div>
  <div class="apparel">
    <div class="figure" style="background-image: url('/assets/silhouettes/{body}_{sex}.png')" title={race}></div>
    {#each APPAREL as a, i (a.s)}
      <div style="grid-column: {a.c}; grid-row: {a.r}">{@render slot(a.s, 0.2 + i * 0.04)}</div>
    {/each}
  </div>

  <div class="label">Accessories</div>
  <div class="row">{#each ACCESSORIES as s, i (s)}{@render slot(s, 0.5 + i * 0.04)}{/each}</div>

  <div class="label">Weapons</div>
  {#each WEAPON_ROWS as row, r (r)}
    <div class="row">{#each row as s, i (s)}{@render slot(s, 0.65 + r * 0.1 + i * 0.04)}{/each}</div>
  {/each}
</Frame>

<style>
  .label {
    font: 600 13px var(--f-display);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--fg);
    margin: 10px 0 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--line);
  }
  .label:first-child { margin-top: 0; }
  /* Slots stay at or below the 64px source icons so they render sharp. */
  .apparel { display: grid; grid-template-columns: 50px 76px 50px; grid-template-rows: repeat(4, 50px); gap: 8px 14px; justify-content: center; }
  .figure {
    grid-column: 2;
    grid-row: 2 / span 3;
    /* The silhouette texture is 64x256 with the figure in its top 160px. */
    background: top center / 100% auto no-repeat;
    width: 66px;
    height: 165px;
    justify-self: center;
    opacity: 0.9;
    animation: fig 0.9s var(--ease-out) both 0.1s;
  }
  .row { display: flex; justify-content: center; gap: 8px; }
  .row + .row { margin-top: 8px; }
  .row :global(.slot), .apparel :global(.slot) { width: 50px; }
  .row :global(.slot img), .apparel :global(.slot img) { width: 42px; height: 42px; }
  @keyframes fig { from { opacity: 0; transform: translateY(8px); filter: blur(3px); } }
</style>
