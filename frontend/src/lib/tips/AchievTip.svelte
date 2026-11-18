<script>
  /** Achievement tooltip: category, status, description, points and criteria progress. @type {{ a: any }} */
  let { a } = $props();
</script>

<div class="bar" class:done={a.complete}></div>
<div class="t-head"><span>{a.cat}{a.subcat ? ` › ${a.subcat}` : ''}</span><span class:gold={a.complete}>{a.complete ? '✓ Completed' : 'Incomplete'}</span></div>
<div class="t-name" class:gold={a.complete}>{a.name}</div>
{#if a.desc}<p class="t-small desc">{a.desc}</p>{/if}
<hr />
<div class="t-head"><span>{a.points} Achievement Points</span>{#if a.complete}<span>{a.completionDate}</span>{/if}</div>
{#if a.complete && a.completedByCharName}<div class="t-faint">Earned by {a.completedByCharName.replace(/\^.*$/, '')}</div>{/if}
{#if !a.complete && a.criteria?.length}
  <div class="crit">
    {#each a.criteria as c, i (i)}
      <div class="t-small row"><span class="d">{c.desc}</span><span class="num" class:gold={c.cur >= c.req}>{c.cur}/{c.req}</span></div>
      {#if c.req > 1}<div class="track"><i style="width: {Math.min(100, (c.cur / c.req) * 100)}%"></i></div>{/if}
    {/each}
  </div>
{/if}

<style>
  .bar { height: 2px; margin: -12px -14px 10px; background: var(--line); }
  .bar.done { background: var(--accent); }
  .gold { color: var(--accent-hi); }
  .desc { margin: 4px 0 0; color: #d6d6d6; }
  .crit { display: grid; gap: 3px; margin-top: 8px; }
  .row { display: flex; justify-content: space-between; gap: 8px; color: var(--muted); }
  .d { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .track { height: 3px; background: #000; }
  .track i { display: block; height: 100%; background: var(--accent); }
</style>
