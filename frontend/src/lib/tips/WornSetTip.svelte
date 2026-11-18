<script>
  import { loadSetBonus, setBonuses } from '../lookups.svelte.js';
  import { setKey } from '../gear.js';

  /** A set the character wears: its bonuses (fetched on first view), the active ones highlighted. @type {{ item: any, count: number }} */
  let { item, count } = $props();
  $effect(() => {
    loadSetBonus(item);
  });
  const bonus = $derived(setBonuses[setKey(item)]);
</script>

<div class="t-head"><span>Set</span><span>{count} equipped</span></div>
<div class="t-name">{item.set_name}</div>
{#if !bonus || bonus.loading}
  <div class="t-small t-faint">Loading bonuses…</div>
{:else if bonus.bonuses?.length}
  {#each bonus.bonuses as b (b.pieces)}<div class="t-small" class:off={b.pieces > count}><span class="pcs">({b.pieces})</span> {b.text}</div>{/each}
{:else}
  <div class="t-small">{bonus.error || 'Bonus lookup unavailable'}</div>
{/if}

<style>
  .off { opacity: 0.45; }
  .pcs { color: var(--accent-hi); }
</style>
