<script>
  import Frame from '../ui/Frame.svelte';
  import EsoWindow from '../eso/EsoWindow.svelte';
  import EsoBar from '../eso/EsoBar.svelte';
  import { applyUiColors } from '../eso/tex.js';
  import CountBar from '../ui/CountBar.svelte';
  import { app } from '../store.svelte.js';
  import { ui } from '../uimode.svelte.js';
  import { gameIcon, pressedIcon, pct } from '../achievements.js';
  import { bookCategories, bookItems, patronBook, COLLECTIBLE_FILTERS } from '../collections.js';

  // Classic: the in-game keyboard Collections book (esoui ingame/collections/keyboard/collectionsbook.xml and the
  // specialized books) on EsoWindow's stage: category tree, Filter By search, show filter, 175x125 collectible tiles.
  // Simple: the same data in the Obsidian two-column layout.
  /** @type {{ book: { id: string, label: string, spec: number } }} */
  let { book } = $props();

  const sb = $derived(app.stickerbook.value);
  // Tales of Tribute: the patrons as the game's tree shows them (iasync 1.10.0), when present.
  const col = $derived(book.spec === 4 ? patronBook(sb?.collectibles) : sb?.collectibles);
  $effect(() => applyUiColors(sb?.uiColors));
  const cats = $derived(bookCategories(col, book.spec));

  /** Tree entries under a category: its subcategories, plus the collectibles filed directly under it (sub 0). */
  function entries(/** @type {any} */ c) {
    const direct = (col?.items ?? []).some((/** @type {any} */ i) => i.cat === c.idx && i.sub === 0);
    return [...(direct && c.subcats.length ? [{ idx: 0, name: c.name }] : []), ...c.subcats];
  }

  let catIdx = $state(/** @type {number | null} */ (null));
  let subIdx = $state(/** @type {number | null} */ (null));
  let f = $state({ search: '', show: 'all' });
  // Like the game, the book opens on its first category and that category's first entry.
  $effect(() => {
    if (catIdx === null && cats.length) pick(cats[0]);
  });
  const searching = $derived(f.search.trim().length > 0);
  const items = $derived(bookItems(col, cats, { cat: catIdx, sub: subIdx }, f));
  /** Unlocked/total of the picked entry, whatever the filters. */
  const scope = $derived.by(() => {
    let unlocked = 0, total = 0;
    for (const i of col?.items ?? []) if (i.cat === catIdx && i.sub === (subIdx ?? 0)) (total++, i.unlocked && unlocked++);
    return { unlocked, total };
  });

  const STEP = 60;
  let limit = $state(STEP);
  $effect(() => {
    items;
    limit = STEP;
  });

  function pick(/** @type {any} */ c) {
    f.search = '';
    catIdx = c.idx;
    subIdx = entries(c)[0]?.idx ?? null;
  }
  const fmt = (/** @type {number} */ n) => (n ?? 0).toLocaleString('en-US');
  /** Category tree icons are _up textures; anything else (e.g. the missing-icon placeholder) is not drawn. */
  const treeIcon = (/** @type {string} */ icon) => (/_up\.dds$/i.test(icon) ? gameIcon(icon) : null);
</script>

{#if app.stickerbook.loading && !sb}
  <Frame title={book.label.toUpperCase()}><p class="hint center">Loading collections…</p></Frame>
{:else if app.stickerbook.error}
  <Frame title={book.label.toUpperCase()}>
    <div class="err-box" role="alert"><b>User data not loaded</b><span>{app.stickerbook.error}</span></div>
  </Frame>
{:else if sb && ui.mode !== 'classic'}
  <div class="layout">
    <nav class="nav" aria-label="{book.label} categories">
      {#each cats as c (c.idx)}
        {@const isOpen = catIdx === c.idx && !searching}
        {@const src = treeIcon(c.icon)}
        <button class="cat" aria-expanded={isOpen} onclick={() => pick(c)}>
          <span class="ti">{#if src}<img src={isOpen ? pressedIcon(src) : src} alt="" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.visibility = 'hidden')} />{:else}<i class="dot"></i>{/if}</span>
          <span class="cn">{c.name}</span><span class="cp num">{pct(c.unlocked, c.total)}%</span>
        </button>
        {#if isOpen && entries(c).length > 1}
          <div class="subs">
            {#each entries(c) as s (s.idx)}
              <button class="subn" aria-current={subIdx === s.idx} onclick={() => (subIdx = s.idx)}>{s.name}</button>
            {/each}
          </div>
        {/if}
      {:else}
        <p class="hint pad">Collectibles need iasync 1.9.0 or newer: update it, /reloadui in game, then upload again.</p>
      {/each}
    </nav>
    <section class="pane">
      <div class="tools">
        <input class="field search" type="search" placeholder="Filter by keyword…" aria-label="Search {book.label}" bind:value={f.search} />
        <select class="field sel" aria-label="Show" bind:value={f.show}>
          {#each COLLECTIBLE_FILTERS as o (o.v)}<option value={o.v}>{o.l}</option>{/each}
        </select>
      </div>
      <div class="body">
        {#if searching}<p class="crumbs">{fmt(items.length)} {items.length === 1 ? 'result' : 'results'}</p>
        {:else if cats.length}<CountBar value={scope.unlocked} max={scope.total} big />{/if}
        <div class="sgrid" role="list">
          {#each items.slice(0, limit) as it (it.id)}
            {@const img = gameIcon(it.icon)}
            <div class="sc" class:locked={!it.unlocked} role="listitem" tabindex="0" title="{it.name}{it.unlocked ? '' : ' (locked)'}">
              {#if img}<img src={img} alt="" loading="lazy" />{/if}<span>{it.name}</span>
            </div>
          {/each}
        </div>
        {#if items.length > limit}<button class="btn more" onclick={() => (limit += STEP)}>Show {Math.min(STEP, items.length - limit)} more of {fmt(items.length - limit)}</button>{/if}
      </div>
    </section>
  </div>
{:else if sb}
  <EsoWindow title={book.label}>
    {#if !col?.categories?.length}
      <p class="eso-abs none-yet">Collectibles need iasync 1.9.0 or newer. Update the addon, type <b>/reloadui</b> in game, then upload again.</p>
    {:else}
      <div class="eso-combo eso-abs" style="left: 768px; top: 24px; width: 222px">
        <select aria-label="Show" bind:value={f.show}>
          {#each COLLECTIBLE_FILTERS as o (o.v)}<option value={o.v}>{o.l}</option>{/each}
        </select>
      </div>
      <label class="eso-abs flab" for="col-search">Filter By</label>
      <input id="col-search" class="eso-edit eso-abs" type="search" placeholder="Enter a keyword" aria-label="Search {book.label}" bind:value={f.search} style="left: 74px; top: 105px; width: 240px" />

      <nav class="eso-abs eso-scroll eso-tree tree" aria-label="{book.label} categories">
        {#each cats as c (c.idx)}
          {@const isOpen = catIdx === c.idx && !searching}
          {@const src = treeIcon(c.icon)}
          {@const subs = isOpen ? entries(c) : []}
          <button class="eso-th" aria-expanded={isOpen} onclick={() => pick(c)} title="{fmt(c.unlocked)} / {fmt(c.total)} ({pct(c.unlocked, c.total)}%)">
            {#if src}
              <img class="ico" src={isOpen ? pressedIcon(src) : src} alt="" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.visibility = 'hidden')} />
              <img class="ico-hl" src={src.replace(/_up\.png$/, '_over.png')} alt="" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.display = 'none')} />
            {/if}
            <span class="txt">{c.name}</span>
            <span class="pc">{pct(c.unlocked, c.total)}%</span>
          </button>
          {#each subs as s (s.idx)}
            <button class="eso-ts" aria-current={subIdx === s.idx} onclick={() => (subIdx = s.idx)} title={s.total ? `${fmt(s.unlocked)} / ${fmt(s.total)}` : undefined}>{s.name}</button>
          {/each}
        {/each}
      </nav>

      {#if searching}
        <div class="eso-abs eso-h4 scope">{fmt(items.length)} {items.length === 1 ? 'result' : 'results'}</div>
      {:else}
        <EsoBar value={scope.unlocked} max={scope.total} label="{book.label} unlocked" style="position: absolute; left: 400px; top: 151px; width: 555px" />
      {/if}
      <div class="eso-abs eso-scroll list">
        <div class="grid" role="list">
          {#each items.slice(0, limit) as it (it.id)}
            {@const img = gameIcon(it.icon)}
            <!-- ZO_CollectibleTile_Keyboard: 175x125, 52px icon centred 41px from the top, name below -->
            <div class="ct" class:locked={!it.unlocked} class:coin={it.icon.includes('/tribute/patrons/')} role="listitem" tabindex="0" title="{it.name}{it.unlocked ? '' : ' (locked)'}">
              {#if img}<img src={img} alt="" loading="lazy" />{/if}
              <span class="nm">{it.name}</span>
            </div>
          {:else}
            <p class="none">{searching ? 'No collectibles match this search.' : 'Nothing to show with this filter.'}</p>
          {/each}
        </div>
        {#if items.length > limit}<button class="more eso-h4" onclick={() => (limit += STEP)}>Show {Math.min(STEP, items.length - limit)} more of {fmt(items.length - limit)}</button>{/if}
      </div>
    {/if}
  </EsoWindow>
{/if}

<style>
  .flab { left: 74px; top: 84px; font-size: 18px; color: var(--eso-normal); }
  .tree { left: 37px; top: 144px; width: 353px; height: 613px; }
  .scope { left: 404px; top: 150px; color: var(--eso-normal); }
  .list { left: 390px; top: 181px; width: 588px; height: 576px; }
  .grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; width: 572px; padding-bottom: 10px; }
  .ct { position: relative; width: 175px; height: 125px; box-sizing: border-box; outline: none; background: var(--eso-slot-bg) 0 0 / 100% 100%; }
  .ct::after { content: ''; position: absolute; inset: 0; background: var(--eso-slot-hl) 0 0 / 100% 100%; opacity: 0; transition: opacity 0.15s; pointer-events: none; }
  .ct:hover::after, .ct:focus-visible::after { opacity: 1; }
  .ct img { position: absolute; left: 61px; top: 15px; width: 52px; height: 52px; transition: transform 0.15s; }
  .ct:hover img, .ct:focus-visible img { transform: scale(1.15); }
  /* Patron coins fill only the middle 57% of their texture. */
  .ct.coin img { transform: scale(1.7); }
  .ct.coin:hover img, .ct.coin:focus-visible img { transform: scale(1.95); }
  .nm {
    position: absolute; left: 7px; right: 7px; top: 73px; text-align: center;
    font: 700 18px/20px var(--eso-font); color: var(--eso-selected); text-shadow: var(--eso-shadow);
    overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  }
  .ct.locked img { filter: grayscale(1) brightness(0.6); }
  .ct.locked .nm { color: var(--eso-disabled); }
  .none { margin: 12px 20px; font-size: 18px; color: var(--eso-selected); }
  .none-yet { left: 430px; top: 150px; width: 500px; font-size: 20px; line-height: 1.4; color: var(--eso-selected); }
  .more { all: unset; display: block; margin: 6px auto 14px; color: var(--eso-normal); cursor: pointer; }
  .more:hover, .more:focus-visible { color: var(--eso-highlight); }
  .center { text-align: center; }

  /* Simple */
  .layout { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 14px; height: max(420px, calc(100dvh - 320px)); } /* tabs + book switcher row above */
  @media (max-width: 760px) { .layout { grid-template-columns: minmax(0, 1fr); height: auto; } .nav { max-height: 260px; } }
  .nav, .pane { min-height: 0; background: var(--panel); border: 1px solid var(--line); }
  .nav { overflow-y: auto; padding: 4px 0; scrollbar-width: thin; }
  .pad { padding: 10px 14px; }
  .cat { all: unset; box-sizing: border-box; display: flex; align-items: center; gap: 8px; width: 100%; padding: 4px 12px; cursor: pointer; transition: background 0.2s; }
  .cat:hover { background: #ffffff08; }
  .cat:hover .cn, .cat[aria-expanded='true'] .cn { color: var(--fg); }
  .cat:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: -1px; }
  .cat[aria-expanded='true'] { background: linear-gradient(90deg, #ffffff14, transparent); }
  .ti { flex: none; width: 30px; height: 30px; display: grid; place-items: center; }
  .ti img { width: 30px; height: 30px; }
  .dot { width: 6px; height: 6px; transform: rotate(45deg); background: color-mix(in srgb, var(--accent) 60%, transparent); }
  .cn { flex: 1; font: 600 13px var(--f-display); letter-spacing: 0.04em; color: #c9c3b8; text-transform: uppercase; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .cp { font-size: 12px; color: var(--muted); }
  .subs { padding: 2px 12px 6px 50px; display: grid; gap: 4px; }
  .subn { all: unset; font-size: 14px; color: var(--muted); cursor: pointer; }
  .subn:hover, .subn[aria-current='true'] { color: var(--fg); }
  .subn[aria-current='true'] { text-decoration: underline; text-decoration-color: var(--accent); text-underline-offset: 3px; }
  .subn:focus-visible { outline: 1px solid var(--accent-hi); }
  .pane { display: flex; flex-direction: column; min-width: 0; }
  .tools { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; padding: 10px 16px; border-bottom: 1px solid var(--line); }
  .search { width: min(240px, 100%); padding: 5px 10px; }
  .sel { width: auto; padding: 5px 8px; }
  .body { flex: 1; min-height: 0; overflow-y: auto; padding: 14px 18px 20px; }
  .crumbs { font-size: 13px; color: var(--muted); margin: 0 0 8px; }
  .sgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 6px; margin-top: 12px; }
  .sc { display: grid; justify-items: center; gap: 4px; padding: 8px 6px; text-align: center; font-size: 12px; line-height: 1.2; color: var(--fg); background: radial-gradient(#ffffff0d, #0000004d); border: 1px solid #ffffff17; outline: none; }
  .sc:not(.locked) { border-color: color-mix(in srgb, var(--accent) 45%, #ffffff17); }
  .sc:hover, .sc:focus-visible { border-color: var(--accent); }
  .sc img { width: 44px; height: 44px; }
  .sc.locked { color: var(--muted); }
  .sc.locked img { filter: grayscale(1) brightness(0.5); }
  .more { margin-top: 16px; }
  .err-box { display: grid; gap: 4px; padding: 12px 16px; border: 1px solid #e5675a66; background: #e5675a14; color: #f2c4bd; font-size: 14px; }
  .err-box b { font: 600 14px var(--f-display); letter-spacing: 0.06em; color: #ffd9d3; }
</style>
