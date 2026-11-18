<script>
  import { app } from '../store.svelte.js';
  import CurrencyTip from '../tips/CurrencyTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';

  const data = $derived(app.data.value);
  /** Account-held currencies (Seals, Transmute, Tome Points…) for the hover list; character-held ones are shown inline. */
  const accountWide = $derived((data?.currencies ?? []).filter((/** @type {any} */ c) => c.account != null));

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
  <div class="money" use:tooltip={accountWide.length ? { component: CurrencyTip, props: { list: accountWide } } : null}>
    {#each CURRENCIES as [key, label] (key)}
      {@const n = total(key)}
      {#if key === 'gold' || n > 0}
        <span title="{label}: {n.toLocaleString('en-US')}"><img src="/assets/currencies/{key}.png" alt={label} /><span class="num">{short(n)}</span></span>
      {/if}
    {/each}
  </div>
{/if}

<style>
  .money { display: flex; justify-content: center; flex-wrap: wrap; gap: 14px; width: fit-content; margin: 0 auto; font-size: 14px; color: var(--muted); } /* fit: the hover tooltip anchors to it */
  .money span { display: inline-flex; align-items: center; gap: 4px; }
  .money img { width: 18px; height: 18px; }
  :global(:root[data-ui='classic']) .money { font: 500 16px var(--eso-font-medium); color: var(--eso-normal); }
</style>
