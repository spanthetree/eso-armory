<script>
  import Frame from '../ui/Frame.svelte';
  import EsoWindow from '../eso/EsoWindow.svelte';
  import EsoBar from '../eso/EsoBar.svelte';
  import SetTip from '../tips/SetTip.svelte';
  import PieceTip from '../tips/PieceTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { ART, applyUiColors } from '../eso/tex.js';
  import { app } from '../store.svelte.js';
  import { ttcSearchUrl } from '../lookups.svelte.js';
  import { gameIcon, pressedIcon, pct } from '../achievements.js';
  import { slugify } from '../gear.js';
  import { categorySummary, totals, subSummary, gridSets, emptyGridFilters, pieceIcon, pieceSource, APPAREL_TYPES, WEAPON_TYPES, COMPLETION } from '../collections.js';

  // The in-game keyboard Sets screen (esoui ingame/collections/keyboard/itemsetsbook_keyboard.xml), positioned in the
  // game's own pixels on EsoWindow's stage.
  const sb = $derived(app.stickerbook.value);
  const sets = $derived(sb?.sets ?? []);
  const icons = $derived(sb?.categoryIcons ?? {});
  $effect(() => applyUiColors(sb?.uiColors));
  const cats = $derived(categorySummary(sets));
  const all = $derived(totals(sets));

  /** null = summary */
  let catName = $state(/** @type {string | null} */ (null));
  let subName = $state(/** @type {string | null} */ (null));
  let f = $state(emptyGridFilters());
  const searching = $derived(f.search.trim().length > 0);
  const subs = $derived(catName ? subSummary(sets, catName) : []);
  const rows = $derived(searching || catName ? gridSets(sets, searching ? null : catName, searching ? null : subName, f) : []);
  const scope = $derived(searching ? totals(rows.map((r) => r.set)) : (subs.find((s) => s.name === subName) ?? { collected: 0, total: 0 }));

  // Big categories and broad searches draw a few dozen sets at a time.
  const STEP = 40;
  let limit = $state(STEP);
  $effect(() => {
    rows;
    limit = STEP;
  });
  let folded = $state(/** @type {Set<number>} */ (new Set()));
  /** Which multi-select dropdown is open. */
  let menu = $state(/** @type {'apparel' | 'weapons' | null} */ (null));

  /** @param {string | null} name */
  function pick(name) {
    f.search = '';
    if (name && name === catName) return void (catName = null);
    catName = name;
    subName = name ? (subSummary(sets, name)[0]?.name ?? '') : null; // like the game, opening a category selects its first zone
  }
  /** @param {number} id */
  function fold(id) {
    const next = new Set(folded);
    next.has(id) ? next.delete(id) : next.add(id);
    folded = next;
  }
  /** @param {string[]} list @param {string} v */
  const toggle = (list, v) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);
  /** SI_ITEM_SETS_BOOK_*_TYPES_DROPDOWN_TEXT @param {number} n @param {string} what */
  const comboText = (n, what) => (n ? `${n} ${what} Type${n === 1 ? '' : 's'}` : `${what} Types`);
  const fmt = (/** @type {number} */ n) => (n ?? 0).toLocaleString('en-US');
</script>

<svelte:window onclick={(e) => menu && !(/** @type {HTMLElement} */ (e.target).closest('.mc')) && (menu = null)} />

{#snippet multi(/** @type {'apparel' | 'weapons'} */ key, /** @type {string} */ what, /** @type {{ v: string, l: string }[]} */ opts, /** @type {number} */ left)}
  <div class="eso-combo eso-abs mc" style="left: {left}px; top: 103px; width: 175px">
    <button aria-haspopup="true" aria-expanded={menu === key} onclick={() => (menu = menu === key ? null : key)}>{comboText(f[key].length, what)}</button>
    {#if menu === key}
      <div class="menu" role="menu">
        {#each opts as o (o.v)}
          <label class="eso-check" role="menuitemcheckbox" aria-checked={f[key].includes(o.v)}>
            <input type="checkbox" checked={f[key].includes(o.v)} onchange={() => (f[key] = toggle(f[key], o.v))} />{o.l}
          </label>
        {/each}
      </div>
    {/if}
  </div>
{/snippet}

{#snippet treeHead(/** @type {string | null} */ src, /** @type {string} */ label, /** @type {boolean} */ on, /** @type {boolean | undefined} */ expanded, /** @type {() => void} */ click, /** @type {string | undefined} */ tip = undefined, /** @type {number | undefined} */ pc = undefined)}
  <button class="eso-th" aria-current={on} aria-expanded={expanded} onclick={click} title={tip}>
    {#if src}
      <img class="ico" src={on || expanded ? pressedIcon(src) : src} alt="" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.visibility = 'hidden')} />
      <img class="ico-hl" src={src.replace(/_up\.png$/, '_over.png')} alt="" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.display = 'none')} />
    {/if}
    <span class="txt">{label}</span>
    {#if pc !== undefined}<span class="pc">{pc}%</span>{/if}
  </button>
{/snippet}

{#snippet setBlock(/** @type {any} */ s, /** @type {any[]} */ pieces)}
  {@const src = pieceSource(s)}
  {@const open = !folded.has(s.setId)}
  <section class="set">
    <!-- ZO_ItemSetsBook_Entry_Header_Keyboard (60 tall) -->
    <div class="sh">
      <button class="eso-arrow" aria-expanded={open} aria-label="{open ? 'Hide' : 'Show'} {s.name} pieces" onclick={() => fold(s.setId)}></button>
      <a class="sn eso-ellipsis" href="https://eso-sets.com/set/{slugify(s.name)}" target="_blank" rel="noopener noreferrer" use:tooltip={{ component: SetTip, props: { s } }}>{s.name}{#if searching}<span class="where"> · {src.where}</span>{/if}</a>
      <EsoBar value={s.numCollected} max={s.numTotal} label="{s.name} pieces collected" style="position: absolute; left: 32px; top: 32px; width: 314px" />
      {#if s.reconCost != null}
        <span class="cost"><span class="ch">Cost</span> {fmt(s.reconCost)} <img src="{ART}currency/currency_seedcrystal_32.png" alt="Transmute Crystals" /></span>
      {/if}
    </div>
    {#if open}
      <div class="grid" role="list">
        {#each pieces as p, i (i)}
          {@const img = pieceIcon(p, gameIcon)}
          {#if src.priced && p.name}
            <a class="tile" class:locked={!p.collected} role="listitem" href={ttcSearchUrl(p.name)} target="_blank" rel="noopener noreferrer"
              aria-label="{p.name}{p.collected ? '' : ' (not collected)'}" use:tooltip={{ component: PieceTip, props: { s, p } }}><img src={img} alt="" loading="lazy" /></a>
          {:else}
            <span class="tile" class:locked={!p.collected} role="listitem" tabindex="0"
              aria-label="{p.name || s.name}{p.collected ? '' : ' (not collected)'}" use:tooltip={{ component: PieceTip, props: { s, p } }}><img src={img} alt="" loading="lazy" /></span>
          {/if}
        {/each}
      </div>
    {/if}
  </section>
{/snippet}

{#if app.stickerbook.loading && !sb}
  <Frame title="SET ITEMS"><p class="hint center">Loading collections…</p></Frame>
{:else if app.stickerbook.error}
  <Frame title="SET ITEMS">
    <div class="err-box" role="alert"><b>User data not loaded</b><span>{app.stickerbook.error}</span></div>
  </Frame>
{:else if sb}
  <EsoWindow title="Set Items">
    <div class="eso-combo eso-abs" style="left: 768px; top: 24px; width: 222px">
      <select aria-label="Completion" bind:value={f.completion}>
        {#each COMPLETION as c (c.v)}<option value={c.v}>{c.l}</option>{/each}
      </select>
    </div>

    <!-- Filters: search, Apparel Types, Weapon Types, Show Locked -->
    <label class="eso-abs flab" for="sets-search">Filter By</label>
    <input id="sets-search" class="eso-edit eso-abs" type="search" placeholder="Enter a keyword" aria-label="Search sets" bind:value={f.search} style="left: 74px; top: 105px; width: 240px" />
    {#if searching || catName}<!-- SetFiltersHidden(true) on the Summary page -->
      {@render multi('apparel', 'Apparel', APPAREL_TYPES, 334)}
      {@render multi('weapons', 'Weapon', WEAPON_TYPES, 529)}
      <label class="eso-check eso-abs" style="left: 724px; top: 108px"><input type="checkbox" bind:checked={f.showLocked} />Show Locked</label>
    {/if}

    <!-- Categories (353 wide at -28,77) -->
    <nav class="eso-abs eso-scroll eso-tree tree" aria-label="Collection categories">
      {@render treeHead('/esoicons/treeicons/achievements_indexicon_summary_up.png', 'Summary', catName === null && !searching, undefined, () => pick(null))}
      {#each cats as c (c.name)}
        {@const isOpen = catName === c.name && !searching}
        {@render treeHead(gameIcon(icons[c.name]), c.name, false, isOpen, () => pick(c.name), `${fmt(c.collected)} / ${fmt(c.total)} pieces (${pct(c.collected, c.total)}%)`, pct(c.collected, c.total))}
        {#if isOpen && (subs.length > 1 || subs[0]?.name)}
          {#each subs as s (s.name)}
            <button class="eso-ts" aria-current={subName === s.name} onclick={() => (subName = s.name)} title="{fmt(s.collected)} / {fmt(s.total)} pieces">{s.name || c.name}</button>
          {/each}
        {/if}
      {/each}
    </nav>

    {#if !searching && !catName}
      <!-- Summary -->
      <div class="eso-abs eso-h2 shead">Summary</div>
      <div class="eso-abs eso-scroll summary">
        <div class="se total">
          <span class="eso-h4 sl">Set Items Collected</span>
          <EsoBar value={all.collected} max={all.total} text="hover" />
        </div>
        <div class="cols">
          {#each cats as c (c.name)}
            <button class="se" onclick={() => pick(c.name)}>
              <span class="eso-h4 sl eso-ellipsis">{c.name}</span>
              <EsoBar value={c.collected} max={c.total} text="hover" />
            </button>
          {/each}
        </div>
      </div>
    {:else}
      <EsoBar value={scope.collected} max={scope.total} style="position: absolute; left: 400px; top: 151px; width: 555px" />
      <div class="eso-abs eso-scroll list">
        {#each rows.slice(0, limit) as r (r.set.setId)}
          {@render setBlock(r.set, r.pieces)}
        {:else}
          <p class="none">No sets match these filters.</p>
        {/each}
        {#if rows.length > limit}<button class="more eso-h4" onclick={() => (limit += STEP)}>Show {Math.min(STEP, rows.length - limit)} more of {rows.length - limit}</button>{/if}
      </div>
    {/if}
  </EsoWindow>
{/if}

<style>
  .flab { left: 74px; top: 84px; font-size: 18px; color: var(--eso-normal); }
  .tree { left: 37px; top: 144px; width: 353px; height: 613px; }
  .menu {
    position: absolute; z-index: 5; left: -8px; top: calc(100% + 4px); min-width: calc(100% + 16px); display: grid; gap: 6px; padding: 14px 16px;
    border: 0 solid transparent; border-image: var(--eso-backdrop) 16 fill / 16px;
  }
  .menu .eso-check { font: 500 18px var(--eso-font-medium); color: var(--eso-selected); white-space: nowrap; }

  .shead { left: 428px; top: 78px; }
  .summary { left: 430px; top: 145px; width: 548px; height: 612px; }
  .se { all: unset; display: grid; align-content: start; gap: 5px; box-sizing: border-box; height: 67px; padding-right: 5px; cursor: pointer; }
  .se.total { margin-left: 6px; width: 517px; cursor: default; }
  .sl { text-transform: uppercase; color: var(--eso-selected); }
  button.se:hover .sl { color: var(--eso-highlight); }
  button.se:focus-visible { outline: 1px solid var(--eso-normal); }
  .cols { display: grid; grid-template-columns: 1fr 1fr; column-gap: 20px; margin-left: 6px; width: 517px; }

  .list { left: 390px; top: 181px; width: 588px; height: 576px; }
  .set { content-visibility: auto; contain-intrinsic-size: auto 220px; }
  .sh { position: relative; height: 60px; padding: 0 10px 0 32px; }
  .sh .eso-arrow { position: absolute; left: 0; top: 0; }
  .sn { display: block; padding-top: 4px; font-size: 20px; font-weight: 700; color: var(--eso-normal); text-decoration: none; }
  .sn:hover, .sn:focus-visible { color: var(--eso-highlight); }
  .where { font-size: 16px; color: var(--eso-disabled); }
  .cost { position: absolute; right: 10px; top: 32px; display: flex; align-items: center; gap: 4px; height: 20px; font: 700 18px var(--eso-font); color: #fff; }
  .ch { margin-right: 1px; color: var(--eso-normal); }
  .cost img { width: 18px; height: 18px; }
  /* ZO_GridScrollList: 67px tiles, 5px padding, centred */
  .grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; width: 572px; padding: 0 0 10px; }
  .tile { position: relative; display: grid; place-items: center; width: 67px; height: 67px; outline: none; }
  .tile::before { content: ''; position: absolute; inset: 0; background: url('/assets/esoui/restyle/keyboard/outfitslot_hoverbackground.png') 0 0 / 100% 100%; opacity: 0; transition: opacity 0.15s; }
  .tile::after { content: ''; position: absolute; inset: 0; border: 0 solid transparent; border-image: var(--eso-inset) 8 / 16px; pointer-events: none; }
  .tile:hover::before, .tile:focus-visible::before { opacity: 1; }
  .tile.locked::before { filter: grayscale(1); }
  .tile img { position: relative; width: 52px; height: 52px; transition: transform 0.15s; }
  .tile:hover img, .tile:focus-visible img { transform: scale(1.15); }
  .tile.locked img { filter: grayscale(1) brightness(0.25); } /* ZO_SILHOUETTE_ICON_ATTRIBUTES */
  .none { margin: 12px 20px; font-size: 18px; color: var(--eso-selected); }
  .more { all: unset; display: block; margin: 6px auto 14px; color: var(--eso-normal); cursor: pointer; }
  .more:hover, .more:focus-visible { color: var(--eso-highlight); }

  .center { text-align: center; }
  .err-box { display: grid; gap: 4px; padding: 12px 16px; border: 1px solid #e5675a66; background: #e5675a14; color: #f2c4bd; font-size: 14px; }
  .err-box b { font: 600 14px var(--f-display); letter-spacing: 0.06em; color: #ffd9d3; }
</style>
