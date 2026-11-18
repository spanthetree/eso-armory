<script>
  import { loadSetBonus, setBonuses } from '../lookups.svelte.js';
  import { setKey } from '../gear.js';

  /**
   * Item tooltip: quality, set bonuses (fetched on first view), traits and where the item is.
   * @type {{ item: any, slotLabel?: string, equippedFromSet?: number }}
   */
  let { item, slotLabel = '', equippedFromSet = 0 } = $props();

  $effect(() => {
    if (item?.set_name) loadSetBonus(item);
  });
  const bonus = $derived(item?.set_name ? setBonuses[setKey(item)] : null);
  const q = $derived(item.quality_color);
</script>

<div class="bar" style="background: {q}"></div>
<div class="t-head"><span>{item.filter_type_name}</span><span style="color: {q}">{item.quality_name}</span></div>
<div class="t-name" style="color: {q}">{item.name}</div>

{#if item.set_name}
  <div class="set">{item.set_name}{#if equippedFromSet} <span class="count">({equippedFromSet} equipped)</span>{/if}</div>
  {#if bonus?.loading}
    <div class="t-small t-faint">Loading bonuses…</div>
  {:else if bonus?.bonuses?.length}
    {#each bonus.bonuses as b (b.pieces)}
      <div class="t-small bonus" class:t-off={equippedFromSet > 0 && b.pieces > equippedFromSet}>
        <span class="pcs">({b.pieces})</span> {b.text}
      </div>
    {/each}
    <div class="t-faint">via eso-sets.com</div>
  {:else if bonus}
    <div class="t-small warn">{bonus.error || 'Bonus lookup unavailable'}</div>
  {/if}
{/if}

{#if item.level > 0 || slotLabel}
  <div class="t-head meta">
    {#if item.level > 0}<span>Level <b>{item.level}</b></span>{/if}
    {#if slotLabel}<span>Slot <b>{slotLabel}</b></span>{/if}
  </div>
{/if}

<div class="t-chips">
  {#if item.trait_name}
    <span class="t-chip" style="color: {q}; border-color: color-mix(in srgb, {q} 45%, transparent)">
      {#if item.is_transmuted}<img src="/assets/services/transmutation_station.png" alt="Transmuted" />{/if}{item.trait_name}
    </span>
  {/if}
  {#if item.style_name}<span class="t-chip">{item.style_name}</span>{/if}
  {#if item.weapon_type}<span class="t-chip">{item.weapon_type}</span>{/if}
  {#if item.armor_type}<span class="t-chip">{item.armor_type}</span>{/if}
  {#if item.is_enchanted}<span class="t-chip" style="color: var(--q-superior)">{item.enchant_name || 'Enchanted'}</span>{/if}
  {#if item.is_crafted}<span class="t-chip" style="color: var(--q-fine)">Crafted</span>{/if}
  {#if item.is_stolen}<span class="t-chip" style="color: #ef4444">Stolen</span>{/if}
</div>

{#if item.locations?.length}
  <hr />
  {#each item.locations as loc (loc.location_key + loc.bag_id)}
    <div class="loc t-small">
      <span>
        {loc.location_type === 'character' ? loc.location_label : loc.bag_label}
        {#if loc.location_type === 'character'}<span class="muted"> · {loc.bag_label}</span>{/if}
      </span>
      <span class="muted num">×{loc.quantity}</span>
    </div>
  {/each}
  {#if item.locations.length > 1}
    <div class="loc t-small total"><span class="muted">Total</span><b class="num">×{item.total_quantity}</b></div>
  {/if}
{/if}

<style>
  .bar { height: 2px; margin: -12px -14px 10px; }
  .set { font: 600 13px var(--f-display); letter-spacing: 0.04em; color: var(--accent-hi); margin: 6px 0 3px; }
  .count { font: 400 12px var(--f-ui); color: var(--muted); letter-spacing: 0; }
  .bonus { color: #d6d6d6; }
  .pcs { color: var(--accent); font-variant-numeric: tabular-nums; }
  .warn { color: #e8b04a; }
  .meta { margin-top: 8px; }
  .meta b, .total b { color: var(--fg); font-weight: 600; }
  .t-chip img { width: 13px; height: 13px; vertical-align: -2px; margin-right: 3px; opacity: 0.8; }
  .loc { display: flex; justify-content: space-between; gap: 10px; }
  .muted { color: var(--muted); }
</style>
