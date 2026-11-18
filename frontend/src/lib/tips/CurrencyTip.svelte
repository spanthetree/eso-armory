<script>
  import { gameIcon } from '../achievements.js';

  /** Every account-wide currency (iasync 1.11.0; icons from 1.12.0). @type {{ list: any[] }} */
  let { list } = $props();
</script>

<div class="t-name">CURRENCIES</div>
<div class="rows">
  {#each list as c (c.key)}
    <span class="cn">{#if gameIcon(c.icon)}<img src={gameIcon(c.icon)} alt="" />{/if}{c.name}</span><span class="num">{(c.account ?? 0).toLocaleString('en-US')}</span>
  {/each}
</div>

<style>
  .rows { display: grid; grid-template-columns: auto auto; gap: 3px 18px; margin-top: 6px; font-size: 14px; }
  .cn { display: inline-flex; align-items: center; gap: 6px; }
  .cn img { width: 18px; height: 18px; }
  .num { text-align: right; }
</style>
