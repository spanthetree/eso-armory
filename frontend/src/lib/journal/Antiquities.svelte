<script>
  import Frame from '../ui/Frame.svelte';
  import Bar from '../ui/Bar.svelte';
  import { app } from '../store.svelte.js';
  import { gameIcon } from '../achievements.js';
  import { timeLeft } from '../time.js';

  // The Journal's Antiquities (iasync 1.11.0): leads first, then by zone; search and a recovered filter.
  const all = $derived(app.data.value?.antiquities ?? []);
  const leads = $derived(all.filter((/** @type {any} */ a) => a.lead));
  const zones = $derived.by(() => {
    /** @type {Map<string, { name: string, n: number, found: number }>} */
    const m = new Map();
    for (const a of all) {
      const z = m.get(a.zone || 'Other') ?? m.set(a.zone || 'Other', { name: a.zone || 'Other', n: 0, found: 0 }).get(a.zone || 'Other');
      z.n++;
      if (a.recovered) z.found++;
    }
    return [...m.values()].sort((a, b) => a.name.localeCompare(b.name));
  });
  const found = $derived(all.filter((/** @type {any} */ a) => a.recovered).length);

  /** 'leads' or a zone name */
  let at = $state('leads');
  let q = $state('');
  let show = $state('all');
  const rows = $derived.by(() => {
    const s = q.trim().toLowerCase();
    return all.filter((/** @type {any} */ a) =>
      (s ? a.name.toLowerCase().includes(s) || a.set.toLowerCase().includes(s) : at === 'leads' ? a.lead : (a.zone || 'Other') === at) &&
      (show === 'all' || (show === 'found') === a.recovered > 0));
  });
  const QUALITY = ['normal', 'normal', 'fine', 'superior', 'epic', 'legendary', 'mythic'];
</script>

{#if !all.length}
  <Frame title="ANTIQUITIES"><p class="hint none">No antiquities yet: they need iasync 1.11.0. Type /reloadui in game, then upload again.</p></Frame>
{:else}
  <div class="layout">
    <Frame title="ANTIQUITIES">
      <div class="sum"><span>Recovered</span><span class="num">{found} / {all.length}</span></div>
      <Bar value={found} max={all.length} label="Antiquities recovered" />
      <nav class="nav" aria-label="Antiquity zones">
        <button aria-current={at === 'leads' && !q} onclick={() => ((at = 'leads'), (q = ''))}><span>Leads</span><span class="num">{leads.length}</span></button>
        {#each zones as z (z.name)}
          <button aria-current={at === z.name && !q} onclick={() => ((at = z.name), (q = ''))}><span>{z.name}</span><span class="num">{z.found}/{z.n}</span></button>
        {/each}
      </nav>
    </Frame>
    <Frame title={q ? 'SEARCH' : at === 'leads' ? 'LEADS' : at.toUpperCase()}>
      <div class="tools">
        <input class="field" type="search" placeholder="Filter by name or set…" aria-label="Search antiquities" bind:value={q} />
        <select class="field" aria-label="Show" bind:value={show}>
          <option value="all">Show All</option><option value="found">Recovered</option><option value="new">Not recovered</option>
        </select>
      </div>
      <div class="rows" role="list">
        {#each rows as a (a.id)}
          <div class="row" role="listitem">
            {#if gameIcon(a.icon)}<img src={gameIcon(a.icon)} alt="" loading="lazy" />{/if}
            <div class="txt">
              <span class="nm" style="color: var(--q-{QUALITY[a.quality] ?? 'normal'})">{a.name}</span>
              <span class="meta">{[a.set, q || at === 'leads' ? a.zone : ''].filter(Boolean).join(' · ')}</span>
            </div>
            <div class="right">
              {#if a.lead}<span class="lead">{['Lead', timeLeft(a.leadExpires)].filter(Boolean).join(' · ')}</span>{/if}
              <span class="meta">{[a.recovered ? `Recovered ${a.recovered}×` : 'Not recovered', a.loreTotal && `Codex ${a.lore}/${a.loreTotal}`].filter(Boolean).join(' · ')}</span>
            </div>
          </div>
        {:else}
          <p class="hint">Nothing here with these filters.</p>
        {/each}
      </div>
    </Frame>
  </div>
{/if}

<style>
  .layout { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 14px; align-items: start; }
  @media (max-width: 800px) { .layout { grid-template-columns: minmax(0, 1fr); } }
  .sum { display: flex; justify-content: space-between; font-size: 14px; color: var(--muted); margin-bottom: 4px; }
  .nav { display: grid; gap: 1px; margin-top: 10px; max-height: max(260px, calc(100dvh - 485px)); overflow-y: auto; }
  .nav button { all: unset; display: flex; justify-content: space-between; gap: 8px; padding: 3px 8px; font-size: 14px; cursor: pointer; }
  .nav button:hover, .nav button:focus-visible { background: #ffffff0a; }
  .nav button[aria-current='true'] { color: var(--accent-hi); background: #ffffff0d; }
  .nav .num { color: var(--muted); }
  .tools { display: flex; gap: 8px; margin-bottom: 8px; }
  .tools input { flex: 1; min-width: 0; }
  .tools select { width: auto; }
  .rows { display: grid; gap: 2px; max-height: max(300px, calc(100dvh - 415px)); overflow-y: auto; }
  .row { display: grid; grid-template-columns: 40px minmax(0, 1fr) auto; align-items: center; gap: 10px; padding: 4px 8px; background: #ffffff05; }
  .row img { width: 40px; height: 40px; }
  .txt, .right { display: grid; gap: 1px; min-width: 0; }
  .right { justify-items: end; text-align: right; }
  .nm { font-size: 15px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .meta { font-size: 12px; color: var(--muted); }
  .lead { font-size: 13px; color: var(--accent-hi); }
  .none { text-align: center; margin: 4px 0; }
  :global(:root[data-ui='classic']) .nav button { font: 500 16px var(--eso-font-medium); color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .nav button[aria-current='true'] { color: var(--eso-selected); background: var(--eso-list-hl) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) .nav button:hover { background: var(--eso-hover) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) .row { background: var(--eso-list-bg) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) .nm { font: 700 17px var(--eso-font); }
  :global(:root[data-ui='classic']) .meta, :global(:root[data-ui='classic']) .sum { font-size: 14px; color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .lead { font: 700 15px var(--eso-font); color: var(--eso-contrast); }
</style>
