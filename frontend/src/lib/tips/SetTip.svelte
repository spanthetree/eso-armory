<script>
  import Progress from '../ui/Progress.svelte';
  import { loadSetBonus, setBonuses } from '../lookups.svelte.js';
  import { setKey } from '../gear.js';

  /** Collection set tooltip: progress plus set bonuses (fetched on first view). @type {{ s: any }} */
  let { s } = $props();

  const item = $derived({ set_id: s.setId, set_name: s.name });
  $effect(() => {
    loadSetBonus(item);
  });
  const bonus = $derived(setBonuses[setKey(item)]);
</script>

<div class="bar"></div>
<div class="t-head"><span>{s.subcategory || s.category}</span><span class:gold={s.complete}>{s.numCollected}/{s.numTotal} pieces</span></div>
<div class="t-name gold">{s.name}</div>
<Progress value={s.numCollected} max={s.numTotal} height={4} />
<div class="bonuses">
  {#if !bonus || bonus.loading}
    <div class="t-small t-faint">Loading bonuses…</div>
  {:else if bonus.bonuses?.length}
    {#each bonus.bonuses as b (b.pieces)}<div class="t-small"><span class="pcs">({b.pieces})</span> {b.text}</div>{/each}
  {:else}
    <div class="t-small warn">{bonus.error || 'Bonus lookup unavailable'}</div>
  {/if}
</div>
<div class="t-faint">Click the name to open it on eso-sets.com</div>

<style>
  .bar { height: 2px; margin: -12px -14px 10px; background: var(--accent); }
  .gold { color: var(--accent-hi); }
  .bonuses { display: grid; gap: 2px; margin-top: 8px; color: #d6d6d6; }
  .pcs { color: var(--accent); }
  .warn { color: #e8b04a; }
</style>
