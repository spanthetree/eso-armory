<script>
  import { loadPrice, prices, priceKey } from '../lookups.svelte.js';

  /** Tamriel Trade Centre price for one item name (fetched on first view). @type {{ name: string }} */
  let { name } = $props();

  $effect(() => {
    loadPrice(name);
  });
  const p = $derived(prices[priceKey(name)]);
  /** @param {any} v */
  const gold = (v) => (v == null || Number.isNaN(Number(v)) ? '–' : Math.round(Number(v)).toLocaleString('en-US'));
</script>

<div class="bar"></div>
<div class="t-head"><span>TTC price</span><span>{p?.entryCount ? `${p.entryCount} listings` : ''}</span></div>
<div class="t-name gold">{name}</div>
{#if !p || p.loading}
  <div class="t-small t-faint">Loading TTC price…</div>
{:else if p.error}
  <div class="t-small muted">{p.error}</div>
{:else}
  <div class="grid">
    <div><small>LOWEST</small><b class="num">{gold(p.min)}</b></div>
    <div><small>AVERAGE</small><b class="num">{gold(p.avg)}</b></div>
    <div><small>HIGHEST</small><b class="num">{gold(p.max)}</b></div>
  </div>
  {#if p.suggestedPrice}<div class="t-row"><span>Suggested</span><b class="num">{gold(p.suggestedPrice)}</b></div>{/if}
  {#if p.saleAvg}<div class="t-row"><span>Sale average</span><b class="num">{gold(p.saleAvg)}</b></div>{/if}
{/if}
<hr />
<div class="t-faint">{p?.attribution || 'Data from Tamriel Trade Centre'}{p?.fetchedAtText ? ` · ${p.fetchedAtText}` : ''}. Click to search TTC.</div>

<style>
  .bar { height: 2px; margin: -12px -14px 10px; background: var(--accent); }
  .gold { color: var(--accent-hi); }
  .muted { color: var(--muted); }
  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin: 6px 0; }
  .grid div { display: grid; }
  small { font-size: 10px; letter-spacing: 0.1em; color: var(--muted); }
  b { font-weight: 500; font-size: 14px; }
</style>
