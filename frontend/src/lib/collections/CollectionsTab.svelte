<script>
  import Frame from '../ui/Frame.svelte';
  import Progress from '../ui/Progress.svelte';
  import SetTip from '../tips/SetTip.svelte';
  import PriceTip from '../tips/PriceTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { app } from '../store.svelte.js';
  import { ttcSearchUrl } from '../lookups.svelte.js';
  import { slugify } from '../gear.js';
  import { categorySummary, totals, sections, searchSets } from '../collections.js';
  import { pct } from '../achievements.js';

  const sets = $derived(app.stickerbook.value?.sets ?? []);
  const cats = $derived(categorySummary(sets));
  const all = $derived(totals(sets));
  const fmt = (/** @type {number} */ n) => n.toLocaleString('en-US');

  /** null = summary */
  let catName = $state(/** @type {string | null} */ (null));
  let search = $state('');
  /** Expanded set cards, by setId. */
  let open = $state(/** @type {Set<number>} */ (new Set()));
  const results = $derived(searchSets(sets, search));
  const groups = $derived(catName ? sections(sets, catName) : []);

  /** @param {string | null} name */
  function pick(name) {
    catName = name;
    search = '';
  }
  /** @param {number} id */
  function toggle(id) {
    const next = new Set(open);
    next.has(id) ? next.delete(id) : next.add(id);
    open = next;
  }
</script>

{#snippet card(/** @type {any} */ s, /** @type {boolean} */ showWhere)}
  <div class="set" class:full={s.complete}>
    <button class="head" aria-expanded={open.has(s.setId)} onclick={() => toggle(s.setId)}>
      {#if showWhere}<span class="where">{s.subcategory || s.category}</span>{/if}
      <span class="row">
        <a class="name" href="https://eso-sets.com/set/{slugify(s.name)}" target="_blank" rel="noopener noreferrer"
          onclick={(e) => e.stopPropagation()} use:tooltip={{ component: SetTip, props: { s } }}>{s.name}</a>
        {#if s.complete}<span class="badge">FULL</span>{/if}
      </span>
      <Progress value={s.numCollected} max={s.numTotal} height={4} />
      <span class="row">
        <span class="pips" aria-hidden="true">{#each s.pieces as p, i (i)}<i class:got={p.collected}></i>{/each}</span>
        <span class="count num">{s.numCollected}/{s.numTotal}</span>
      </span>
    </button>
    {#if open.has(s.setId)}
      <ul class="pieces">
        {#each s.pieces as p, i (i)}
          <li class:got={p.collected}>
            <span class="mark">{p.collected ? '✓' : '○'}</span>
            <a href={ttcSearchUrl(p.name || s.name)} target="_blank" rel="noopener noreferrer"
              use:tooltip={{ component: PriceTip, props: { name: p.name || s.name } }}>{p.name || `Piece ${i + 1}`}</a>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
{/snippet}

{#if app.stickerbook.loading && !app.stickerbook.value}
  <Frame title="COLLECTIONS"><p class="hint center">Loading collections…</p></Frame>
{:else if app.stickerbook.error}
  <Frame title="COLLECTIONS">
    <div class="err-box" role="alert"><b>User data not loaded</b><span>{app.stickerbook.error}</span></div>
  </Frame>
{:else if app.stickerbook.value}
  <div class="layout">
    <nav class="nav" aria-label="Collection categories">
      <button class="cat" aria-current={catName === null && !search} onclick={() => pick(null)}><span class="cn">SUMMARY</span></button>
      {#each cats as c (c.name)}
        <button class="cat" aria-current={catName === c.name && !search} onclick={() => pick(c.name)}>
          <span class="cn">{c.name}</span><span class="cp num">{pct(c.collected, c.total)}%</span>
          <Progress value={c.collected} max={c.total} height={3} />
        </button>
      {/each}
    </nav>

    <section class="pane">
      <div class="tools">
        <input class="field search" type="search" placeholder="Search sets…" aria-label="Search sets" bind:value={search} />
      </div>
      <div class="body">
        {#if search.trim()}
          <div class="head2"><h2>SEARCH</h2><span class="muted">{results.length} sets</span></div>
          <div class="grid">{#each results as s (s.setId)}{@render card(s, true)}{:else}<p class="hint">No sets found.</p>{/each}</div>
        {:else if !catName}
          <div class="head2"><h2>SUMMARY</h2><span class="muted">Set items collected <b class="num">{fmt(all.collected)} / {fmt(all.total)}</b></span></div>
          <Progress value={all.collected} max={all.total} height={10} />
          <div class="cats">
            {#each cats as c, i (c.name)}
              <button class="cg" style="--d: {i * 0.02}s" onclick={() => pick(c.name)}>
                <span class="row"><span class="cgn">{c.name}</span><span class="muted num">{fmt(c.collected)} / {fmt(c.total)}</span></span>
                <Progress value={c.collected} max={c.total} height={7} />
              </button>
            {/each}
          </div>
        {:else}
          <div class="crumbs"><button class="link" onclick={() => pick(null)}>Summary</button> › <span>{catName}</span></div>
          {#each groups as g (g.heading)}
            {#if g.heading}<h3>{g.heading}</h3>{/if}
            <div class="grid">{#each g.sets as s (s.setId)}{@render card(s, false)}{/each}</div>
          {:else}
            <p class="hint">No sets found.</p>
          {/each}
        {/if}
      </div>
    </section>
  </div>
{/if}

<style>
  /* Both columns scroll inside the page so the tab fits one screen. */
  .layout { display: grid; grid-template-columns: 230px minmax(0, 1fr); gap: 14px; height: max(420px, calc(100dvh - 260px)); }
  @media (max-width: 760px) { .layout { grid-template-columns: minmax(0, 1fr); height: auto; } .nav { max-height: 220px; } }
  .nav, .pane { min-height: 0; background: var(--panel); border: 1px solid var(--line); }
  .nav { overflow-y: auto; }
  .pane { display: flex; flex-direction: column; min-width: 0; }
  .cat { all: unset; box-sizing: border-box; display: grid; grid-template-columns: 1fr auto; gap: 4px 8px; width: 100%; padding: 8px 14px; border-bottom: 1px solid #ffffff0a; cursor: pointer; transition: background 0.2s; }
  .cat :global(.track) { grid-column: 1 / -1; }
  .cat:hover { background: #ffffff08; }
  .cat:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: -1px; }
  .cat[aria-current='true'] { background: #ffffff0f; box-shadow: inset 2px 0 0 var(--accent); }
  .cn { font: 500 12px var(--f-display); letter-spacing: 0.08em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .cp { font-size: 12px; color: var(--muted); }
  .tools { display: flex; padding: 10px 16px; border-bottom: 1px solid var(--line); }
  .search { margin-left: auto; width: min(280px, 100%); padding: 5px 10px; }
  .body { flex: 1; min-height: 0; overflow-y: auto; padding: 14px 18px 20px; animation: fade 0.35s var(--ease-out); }
  .head2 { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 8px; margin-bottom: 8px; }
  h2 { font-size: 19px; letter-spacing: 0.14em; }
  h3 { font-size: 12px; letter-spacing: 0.16em; color: var(--muted); text-transform: uppercase; margin: 16px 0 8px; padding-bottom: 4px; border-bottom: 1px solid var(--line); }
  .muted { color: var(--muted); font-size: 13px; }
  .muted b { color: var(--fg); font-weight: 500; }
  .crumbs { font-size: 13px; color: var(--muted); margin-bottom: 6px; }
  .crumbs span { color: var(--accent-hi); }
  .link { all: unset; cursor: pointer; }
  .link:hover, .link:focus-visible { color: var(--fg); }
  .row { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }

  .cats { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 10px 22px; margin-top: 18px; }
  .cg { all: unset; display: grid; gap: 3px; cursor: pointer; animation: fade 0.4s var(--ease-out) both; animation-delay: var(--d); }
  .cg:hover .cgn, .cg:focus-visible .cgn { color: var(--accent-hi); }
  .cg:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: 3px; }
  .cgn { font: 500 12px var(--f-display); letter-spacing: 0.08em; transition: color 0.2s; }

  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 250px), 1fr)); gap: 10px; align-items: start; }
  .set { border: 1px solid var(--line); background: #0b0a09; transition: border-color 0.2s; }
  .set.full { border-color: color-mix(in srgb, var(--accent) 50%, var(--line)); }
  .set:hover { border-color: var(--accent); }
  .head { all: unset; box-sizing: border-box; display: grid; gap: 5px; width: 100%; padding: 10px 12px; cursor: pointer; }
  .head:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: -1px; }
  .where { font: 500 10px var(--f-display); letter-spacing: 0.08em; color: var(--muted); }
  .name { font: 600 13px var(--f-display); letter-spacing: 0.04em; color: var(--fg); text-decoration: none; }
  .name:hover { color: var(--accent-hi); }
  .badge { flex: none; padding: 0 5px; font: 600 9px var(--f-display); letter-spacing: 0.14em; color: var(--accent-hi); border: 1px solid color-mix(in srgb, var(--accent) 60%, transparent); }
  .pips { display: flex; flex-wrap: wrap; gap: 3px; }
  .pips i { width: 8px; height: 8px; background: #2a2620; }
  .pips i.got { background: var(--accent); }
  .count { font-size: 12px; color: var(--muted); }
  .pieces { list-style: none; margin: 0; padding: 6px 12px 10px; border-top: 1px solid var(--line); display: grid; gap: 2px; animation: fade 0.25s var(--ease-out); }
  .pieces li { display: flex; gap: 8px; font-size: 13px; }
  .pieces a { color: var(--fg); text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pieces a:hover { color: var(--accent-hi); text-decoration: underline; }
  .pieces li.got a { color: var(--muted); text-decoration: line-through; }
  .mark { color: var(--accent); width: 12px; flex: none; }
  .center { text-align: center; }
  .err-box { display: grid; gap: 4px; padding: 12px 16px; border: 1px solid #e5675a66; background: #e5675a14; color: #f2c4bd; font-size: 14px; }
  .err-box b { font: 600 14px var(--f-display); letter-spacing: 0.06em; color: #ffd9d3; }
  @keyframes fade { from { opacity: 0; transform: translateY(6px); } }
</style>
