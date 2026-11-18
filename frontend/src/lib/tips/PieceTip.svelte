<script>
  import { loadPrice, prices, priceKey } from '../lookups.svelte.js';
  import { pieceSource } from '../collections.js';

  /** One set collection piece: type, collected or not, where it drops and (for tradeable sets) its TTC price. @type {{ s: any, p: any }} */
  let { s, p } = $props();

  const src = $derived(pieceSource(s));
  $effect(() => {
    if (src.priced && p.name) loadPrice(p.name);
  });
  const price = $derived(src.priced && p.name ? prices[priceKey(p.name)] : null);
  const gold = (/** @type {number} */ v) => Math.round(v).toLocaleString('en-US');
</script>

<div class="bar" class:got={p.collected}></div>
<div class="t-head"><span>{p.filterName || 'Piece'}</span><span class:gold={p.collected}>{p.collected ? 'Collected' : 'Not collected'}</span></div>
<div class="t-name" class:gold={p.collected}>{p.name || s.name}</div>
<div class="t-row"><span>Source</span><b>{src.where}</b></div>
{#if src.priced}
  {#if !price || price.loading}
    <div class="t-small t-faint">Loading TTC price…</div>
  {:else if price.error}
    <div class="t-small t-faint">{price.error}</div>
  {:else}
    <div class="t-row"><span>TTC average</span><b class="num">{gold(price.avg)} gold</b></div>
  {/if}
  <div class="t-faint">Click to search Tamriel Trade Centre.</div>
{:else}
  <div class="t-faint">{src.kind} drop; not sold on guild traders.</div>
{/if}

<style>
  .bar { height: 2px; margin: -12px -14px 10px; background: var(--line); }
  .bar.got { background: var(--accent); }
  .gold { color: var(--accent-hi); }
  b { font-weight: 500; }
</style>
