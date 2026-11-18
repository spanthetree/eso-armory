<script>
  import Frame from '../ui/Frame.svelte';
  import Progress from '../ui/Progress.svelte';
  import CountBar from '../ui/CountBar.svelte';
  import MultiSelect from '../ui/MultiSelect.svelte';
  import SetTip from '../tips/SetTip.svelte';
  import PieceTip from '../tips/PieceTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { app } from '../store.svelte.js';
  import { ttcSearchUrl } from '../lookups.svelte.js';
  import { slugify } from '../gear.js';
  import { gameIcon, pressedIcon, pct } from '../achievements.js';
  import {
    categorySummary, totals, subSummary, gridSets, emptyGridFilters, pieceIcon, pieceSource,
    APPAREL_TYPES, WEAPON_TYPES, COMPLETION,
  } from '../collections.js';

  // Laid out like the in-game Sets collection: category tree on the left, each set as a grid of its pieces.
  const sets = $derived(app.stickerbook.value?.sets ?? []);
  const icons = $derived(app.stickerbook.value?.categoryIcons ?? {});
  const cats = $derived(categorySummary(sets));
  const all = $derived(totals(sets));

  /** null = summary */
  let catName = $state(/** @type {string | null} */ (null));
  /** null = the whole category; '' = sets filed directly under it */
  let subName = $state(/** @type {string | null} */ (null));
  let f = $state(emptyGridFilters());
  const searching = $derived(f.search.trim().length > 0);
  const subs = $derived(catName ? subSummary(sets, catName) : []);
  const rows = $derived(searching || catName ? gridSets(sets, catName, subName, f) : []);
  const scope = $derived(totals(rows.map((r) => r.set)));

  // Big categories and broad searches draw a few dozen sets at a time.
  const STEP = 30;
  let limit = $state(STEP);
  $effect(() => {
    rows;
    limit = STEP;
  });
  /** Folded sets, by setId. */
  let folded = $state(/** @type {Set<number>} */ (new Set()));

  /** @param {string | null} name */
  function pick(name) {
    f.search = '';
    if (name && name === catName && subName == null) return void (catName = null);
    catName = name;
    subName = null;
  }
  /** @param {string} name */
  function pickSub(name) {
    f.search = '';
    subName = subName === name ? null : name;
  }
  /** @param {number} id */
  function fold(id) {
    const next = new Set(folded);
    next.has(id) ? next.delete(id) : next.add(id);
    folded = next;
  }
  const filtersOn = $derived(f.apparel.length > 0 || f.weapons.length > 0 || !f.showLocked || f.completion !== '');
</script>

{#snippet treeIcon(/** @type {string | null} */ src, /** @type {boolean} */ on)}
  <span class="ti">{#if src}<img src={on ? pressedIcon(src) : src} alt="" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.visibility = 'hidden')} />{:else}<i class="dot"></i>{/if}</span>
{/snippet}

{#snippet setBlock(/** @type {any} */ s, /** @type {any[]} */ pieces)}
  {@const src = pieceSource(s)}
  <section class="set" class:full={s.complete}>
    <div class="sethead">
      <button class="fold" aria-expanded={!folded.has(s.setId)} aria-label="{folded.has(s.setId) ? 'Show' : 'Hide'} {s.name} pieces" onclick={() => fold(s.setId)}>{folded.has(s.setId) ? '▸' : '▾'}</button>
      <a class="name" href="https://eso-sets.com/set/{slugify(s.name)}" target="_blank" rel="noopener noreferrer" use:tooltip={{ component: SetTip, props: { s } }}>{s.name}</a>
      {#if searching}<span class="where">{src.where}</span>{/if}
      {#if s.complete}<span class="badge">COMPLETE</span>{/if}
    </div>
    <div class="setbar"><CountBar value={s.numCollected} max={s.numTotal} label="{s.name} pieces collected" /></div>
    {#if !folded.has(s.setId)}
      <div class="pieces" role="list">
        {#each pieces as p, i (i)}
          {#if src.priced && p.name}
            <a class="piece" class:locked={!p.collected} role="listitem" href={ttcSearchUrl(p.name)} target="_blank" rel="noopener noreferrer"
              aria-label="{p.name}{p.collected ? '' : ' (not collected)'}" use:tooltip={{ component: PieceTip, props: { s, p } }}>
              <img src={pieceIcon(p, gameIcon)} alt="" loading="lazy" />
            </a>
          {:else}
            <span class="piece" class:locked={!p.collected} role="listitem" tabindex="0"
              aria-label="{p.name || s.name}{p.collected ? '' : ' (not collected)'}" use:tooltip={{ component: PieceTip, props: { s, p } }}>
              <img src={pieceIcon(p, gameIcon)} alt="" loading="lazy" />
            </span>
          {/if}
        {/each}
      </div>
    {/if}
  </section>
{/snippet}

{#if app.stickerbook.loading && !app.stickerbook.value}
  <Frame title="SET ITEMS"><p class="hint center">Loading collections…</p></Frame>
{:else if app.stickerbook.error}
  <Frame title="SET ITEMS">
    <div class="err-box" role="alert"><b>User data not loaded</b><span>{app.stickerbook.error}</span></div>
  </Frame>
{:else if app.stickerbook.value}
  <div class="layout">
    <nav class="nav" aria-label="Collection categories">
      <button class="cat" aria-current={catName === null && !searching} onclick={() => pick(null)}>
        {@render treeIcon('/assets/esoui/collections/collections_tabicon_itemsets_up.png', catName === null && !searching)}<span class="cn">SUMMARY</span>
      </button>
      {#each cats as c (c.name)}
        {@const on = catName === c.name && !searching}
        <button class="cat" aria-current={on && subName == null} aria-expanded={catName === c.name} onclick={() => pick(c.name)}>
          {@render treeIcon(gameIcon(icons[c.name]), on)}<span class="cn">{c.name}</span><span class="cp num">{pct(c.collected, c.total)}%</span>
        </button>
        {#if catName === c.name && subs.length > 1}
          <div class="subs">
            {#each subs as s (s.name)}
              <button class="subn" aria-current={subName === s.name && !searching} onclick={() => pickSub(s.name)}>
                <span class="sl"><span>{s.name || 'General'}</span><span class="num">{s.collected}/{s.total}</span></span>
                <Progress value={s.collected} max={s.total} height={2} />
              </button>
            {/each}
          </div>
        {/if}
      {/each}
    </nav>

    <section class="pane">
      <div class="tools">
        <input class="field search" type="search" placeholder="Filter by keyword…" aria-label="Search sets" bind:value={f.search} />
        <MultiSelect label="Apparel Types" options={APPAREL_TYPES} bind:selected={f.apparel} />
        <MultiSelect label="Weapon Types" options={WEAPON_TYPES} bind:selected={f.weapons} />
        <select class="field sel" aria-label="Completion" bind:value={f.completion}>
          {#each COMPLETION as c (c.v)}<option value={c.v}>{c.l}</option>{/each}
        </select>
        <label class="tick"><input type="checkbox" bind:checked={f.showLocked} />Show Locked</label>
        {#if filtersOn}<button class="btn" onclick={() => (f = { ...emptyGridFilters(), search: f.search })}>Clear</button>{/if}
      </div>

      <div class="body">
        {#if !searching && !catName}
          <h3 class="first">SET ITEMS COLLECTED</h3>
          <CountBar value={all.collected} max={all.total} big />
          <div class="cats">
            {#each cats as c (c.name)}
              <button class="cg" onclick={() => pick(c.name)}>
                <span class="cgn">{c.name.toUpperCase()}</span>
                <CountBar value={c.collected} max={c.total} />
              </button>
            {/each}
          </div>
        {:else}
          <div class="crumbs">
            {#if searching}<span>Search</span> · {rows.length} sets
            {:else}<button class="link" onclick={() => pick(null)}>Summary</button> › <span>{catName}</span>{#if subName != null}{' '}› <span>{subName || 'General'}</span>{/if}{/if}
          </div>
          <CountBar value={scope.collected} max={scope.total} big />
          {#each rows.slice(0, limit) as r (r.set.setId)}
            {@render setBlock(r.set, r.pieces)}
          {:else}
            <p class="hint">No sets match these filters.</p>
          {/each}
          {#if rows.length > limit}<button class="btn more" onclick={() => (limit += STEP)}>Show {Math.min(STEP, rows.length - limit)} more of {rows.length - limit}</button>{/if}
        {/if}
      </div>
    </section>
  </div>
{/if}

<style>
  /* Both columns scroll inside the page so the tab fits one screen. */
  .layout { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 14px; height: max(420px, calc(100dvh - 320px)); } /* tabs + book switcher row above */
  @media (max-width: 760px) { .layout { grid-template-columns: minmax(0, 1fr); height: auto; } .nav { max-height: 260px; } }
  .nav, .pane { min-height: 0; background: var(--panel); border: 1px solid var(--line); }
  .nav { overflow-y: auto; padding: 4px 0; scrollbar-width: thin; }
  .cat { all: unset; box-sizing: border-box; display: flex; align-items: center; gap: 8px; width: 100%; padding: 4px 12px; cursor: pointer; transition: background 0.2s; }
  .cat:hover { background: #ffffff08; }
  .cat:hover .cn, .cat[aria-expanded='true'] .cn { color: var(--fg); }
  .cat:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: -1px; }
  .cat[aria-current='true'] { background: linear-gradient(90deg, #ffffff14, transparent); }
  .cat[aria-current='true'] .cn { color: var(--fg); }
  .ti { flex: none; width: 30px; height: 30px; display: grid; place-items: center; }
  .ti img { width: 30px; height: 30px; }
  .dot { width: 6px; height: 6px; transform: rotate(45deg); background: color-mix(in srgb, var(--accent) 60%, transparent); }
  .cn { flex: 1; font: 600 13px var(--f-display); letter-spacing: 0.04em; color: #c9c3b8; text-transform: uppercase; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; transition: color 0.2s; }
  .cp { font-size: 12px; color: var(--muted); }
  .subs { padding: 2px 12px 6px 50px; display: grid; gap: 4px; animation: fade 0.25s var(--ease-out); }
  .subn { all: unset; display: grid; gap: 2px; cursor: pointer; }
  .sl { display: flex; justify-content: space-between; gap: 6px; font-size: 14px; color: var(--muted); }
  .sl .num { font-size: 12px; }
  .subn:hover .sl, .subn[aria-current='true'] .sl { color: var(--fg); }
  .subn[aria-current='true'] .sl span:first-child { text-decoration: underline; text-decoration-color: var(--accent); text-underline-offset: 3px; }
  .subn:focus-visible { outline: 1px solid var(--accent-hi); }

  .pane { display: flex; flex-direction: column; min-width: 0; }
  .tools { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; padding: 10px 16px; border-bottom: 1px solid var(--line); }
  .search { width: min(240px, 100%); padding: 5px 10px; }
  .sel { width: auto; padding: 5px 8px; }
  .tick { display: flex; align-items: center; gap: 6px; font-size: 14px; cursor: pointer; }
  .tick input { accent-color: var(--accent); }
  .body { flex: 1; min-height: 0; overflow-y: auto; padding: 14px 18px 20px; animation: fade 0.35s var(--ease-out); }
  h3 { font-size: 13px; letter-spacing: 0.16em; margin: 0 0 8px; }
  .crumbs { font-size: 13px; color: var(--muted); margin-bottom: 8px; }
  .crumbs span { color: var(--accent-hi); }
  .link { all: unset; cursor: pointer; }
  .link:hover, .link:focus-visible { color: var(--fg); text-decoration: underline; }
  .cats { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr)); gap: 10px 26px; margin-top: 16px; }
  .cg { all: unset; display: grid; gap: 3px; cursor: pointer; }
  .cg:hover .cgn, .cg:focus-visible .cgn { color: var(--accent-hi); }
  .cg:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: 3px; }
  .cgn { font: 600 12px var(--f-display); letter-spacing: 0.06em; transition: color 0.2s; }

  .set { margin-top: 18px; }
  .sethead { display: flex; align-items: baseline; gap: 8px; }
  .fold { all: unset; width: 14px; color: var(--muted); cursor: pointer; font-size: 13px; }
  .fold:hover, .fold:focus-visible { color: var(--fg); }
  .name { font: 600 15px var(--f-display); letter-spacing: 0.03em; color: var(--fg); text-decoration: none; }
  .name:hover { color: var(--accent-hi); }
  .where { font-size: 12px; color: var(--muted); }
  .badge { padding: 0 5px; font: 600 9px var(--f-display); letter-spacing: 0.14em; color: var(--accent-hi); border: 1px solid color-mix(in srgb, var(--accent) 60%, transparent); }
  .setbar { width: min(320px, 100%); margin: 4px 0 8px 22px; }
  .pieces { display: grid; grid-template-columns: repeat(auto-fill, 54px); gap: 4px; padding-left: 22px; }
  .piece { display: grid; place-items: center; width: 54px; height: 54px; background: radial-gradient(#ffffff0d, #0000004d); border: 1px solid #ffffff17; outline: none; transition: border-color 0.15s, transform 0.15s; }
  .piece img { width: 48px; height: 48px; }
  .piece.locked img { filter: grayscale(1) brightness(0.45); }
  .piece:hover, .piece:focus-visible { border-color: var(--accent); transform: translateY(-1px); }
  .piece:not(.locked) { border-color: color-mix(in srgb, var(--accent) 45%, #ffffff17); box-shadow: inset 0 0 12px -6px var(--accent); }
  .more { margin-top: 16px; }
  .center { text-align: center; }
  .err-box { display: grid; gap: 4px; padding: 12px 16px; border: 1px solid #e5675a66; background: #e5675a14; color: #f2c4bd; font-size: 14px; }
  .err-box b { font: 600 14px var(--f-display); letter-spacing: 0.06em; color: #ffd9d3; }
  @keyframes fade { from { opacity: 0; transform: translateY(6px); } }
</style>
