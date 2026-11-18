<script>
  import { app } from '../store.svelte.js';

  const data = $derived(app.data.value);

  /** Character currency plus bank, like the classic header. @param {string} key */
  function total(key) {
    const chars = Object.values(data?.characters ?? {});
    return chars.reduce((s, c) => s + (c[key] || 0), 0) + (data?.bank?.[key] || 0);
  }
  const CURRENCIES = [
    ['gold', 'Gold'],
    ['ap', 'Alliance Points'],
    ['tv', 'Tel Var Stones'],
    ['wv', 'Writs'],
  ];
  /** @param {number} n */
  const short = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : String(n));
</script>

{#if data}
  <div class="money">
    {#each CURRENCIES as [key, label] (key)}
      {@const n = total(key)}
      {#if key === 'gold' || n > 0}
        <span title="{label}: {n.toLocaleString('en-US')}"><img src="/assets/currencies/{key}.png" alt={label} /><span class="num">{short(n)}</span></span>
      {/if}
    {/each}
  </div>
{/if}

<style>
  .money { display: flex; justify-content: center; flex-wrap: wrap; gap: 14px; font-size: 14px; color: var(--muted); }
  .money span { display: inline-flex; align-items: center; gap: 4px; }
  .money img { width: 18px; height: 18px; }
  :global(:root[data-ui='classic']) .money { font: 500 16px var(--eso-font-medium); color: var(--eso-normal); }
</style>
