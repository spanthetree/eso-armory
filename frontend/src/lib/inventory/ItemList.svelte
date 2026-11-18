<script>
  import MultiSelect from '../ui/MultiSelect.svelte';
  import { ui } from '../uimode.svelte.js';
  /** Classic: the in-game inventory filter tab icon for each item type. */
  /** @type {Record<string, string>} */
  const TYPE_ICON = { 1: 'weapons', 2: 'armor', 25: 'craftbag_jewelrycrafting', 3: 'consumables', 4: 'crafting', 6: 'craftbag_enchanting', 21: 'furnishing_seating', 5: 'misc' };
  import ItemTip from '../tips/ItemTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { itemIcon } from '../gear.js';
  import { avgPrices, loadAvgPrices } from '../lookups.svelte.js';
  import {
    TYPE_OPTIONS, BAG_OPTIONS, LOCATION_OPTIONS, TRAIT_GROUPS, QUALITY_OPTIONS, PRESETS,
    emptyFilters, hasFilters, filterItems, sortItems, displayRows, withValues, summarize, priceName, applyPreset, isPreset,
  } from '../items.js';

  /**
   * Searchable, filterable item table. Used by a character's Bags view and the Inventory tab.
   * `where` picks the location filters: 'bags' (equipped/backpack) for one character,
   * 'account' (location type + character) for everything.
   * @type {{ items: any[], where: 'bags' | 'account', characters?: { v: string, l: string }[], placeholder?: string }}
   */
  let { items, where, characters = [], placeholder = 'Search items…' } = $props();

  let f = $state(emptyFilters());
  let groupBySet = $state(false);
  let sort = $state({ key: 'name', dir: /** @type {'asc' | 'desc'} */ ('asc') });
  let extrasOpen = $state(false);

  // TTC values: one bulk request for every tradeable name in the list.
  $effect(() => {
    loadAvgPrices(items.filter((i) => !i.is_bound).map((i) => priceName(i.name)));
  });
  const valued = $derived(withValues(items, avgPrices.map));
  const filtered = $derived(sortItems(filterItems(valued, f), sort.key, sort.dir));
  const rows = $derived(displayRows(filtered, f.dupes ? 'name' : groupBySet ? 'set' : ''));
  const sum = $derived(summarize(filtered));
  const all = $derived(where === 'account' ? summarize(valued) : null);
  const gold = (/** @type {number} */ n) =>
    n >= 1e6 ? `${(n / 1e6).toFixed(n >= 1e7 ? 0 : 1)}M` : n >= 1e4 ? `${Math.round(n / 1e3)}k` : Math.round(n).toLocaleString('en-US');

  // Saved filter chips live in this browser only.
  const SAVED_KEY = 'eso-armory:item-presets';
  /** @type {{ name: string, f: any }[]} */
  let saved = $state(readSaved());
  function readSaved() {
    try {
      const v = JSON.parse(localStorage.getItem(SAVED_KEY) || '[]');
      return Array.isArray(v) ? v : [];
    } catch {
      return [];
    }
  }
  function writeSaved() {
    try {
      localStorage.setItem(SAVED_KEY, JSON.stringify(saved));
    } catch {
      // storage blocked: chips last for this page only
    }
  }
  let naming = $state(false);
  let newName = $state('');
  const matchesChip = $derived([...PRESETS, ...saved].some((p) => isPreset(f, p.f)));
  function saveChip() {
    const name = newName.trim();
    if (!name) return;
    const { search, ...rest } = $state.snapshot(f);
    saved = [...saved.filter((p) => p.name !== name), { name, f: { ...rest, search } }];
    writeSaved();
    naming = false;
    newName = '';
  }
  /** @param {string} name */
  function dropChip(name) {
    saved = saved.filter((p) => p.name !== name);
    writeSaved();
  }
  /** @param {any} p */
  const useChip = (p) => (f = isPreset(f, p.f) ? emptyFilters() : applyPreset(p.f));

  /** Toggle one value in a list filter (strip chips, type cells, location chips). @param {'types' | 'locTypes' | 'chars' | 'bags'} key @param {string} v */
  function toggleIn(key, v) {
    f[key] = f[key].includes(v) ? f[key].filter((x) => x !== v) : [...f[key], v];
  }
  /** @param {any} loc */
  function filterLoc(loc) {
    if (where === 'bags') toggleIn('bags', String(loc.bag_id));
    else if (loc.location_type === 'character') toggleIn('chars', loc.location_key);
    else toggleIn('locTypes', loc.location_type);
  }
  /** @param {any} loc */
  const locOn = (loc) =>
    where === 'bags' ? f.bags.includes(String(loc.bag_id)) : loc.location_type === 'character' ? f.chars.includes(loc.location_key) : f.locTypes.includes(loc.location_type);

  // Render rows in batches as the table scrolls, so thousands of items stay responsive.
  const BATCH = 150;
  let limit = $state(BATCH);
  /** @type {HTMLElement} */
  let scroller;
  $effect(() => {
    rows; // new filter/sort results start from the top
    limit = BATCH;
    if (scroller) scroller.scrollTop = 0;
  });
  const shown = $derived(rows.slice(0, limit));
  /** @param {HTMLElement} node */
  function more(node) {
    const io = new IntersectionObserver((e) => e[0].isIntersecting && (limit += BATCH), { root: node.closest('.scroll'), rootMargin: '400px' });
    io.observe(node);
    return { destroy: () => io.disconnect() };
  }
  /** Locations shown per row before "+N more". */
  const MAX_LOCS = where === 'account' ? 2 : 99;
  const extrasOn = $derived(f.quality !== '' || f.transmuted || f.crafted || f.unbound || f.hasSet);

  /** @param {string} key */
  function sortBy(key) {
    sort = sort.key === key ? { key, dir: sort.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: key === 'name' ? 'asc' : 'desc' };
  }
  /** @param {string} key */
  const arrow = (key) => (sort.key === key ? (sort.dir === 'asc' ? '▲' : '▼') : '');
  /** @param {any} loc */
  // Characters and guild banks name which one; other locations are unique.
  const locLabel = (loc) => (where === 'bags' || !['character', 'guild_bank'].includes(loc.location_type) ? loc.bag_label : `${loc.location_label} · ${loc.bag_label}`);
</script>

<svelte:window onpointerdown={(e) => extrasOpen && !(/** @type {Element} */ (e.target)).closest('.extras') && (extrasOpen = false)} />

{#snippet coin(/** @type {number} */ n)}<span class="g num">{gold(n)}<img src="/assets/currencies/gold.png" alt="gold" /></span>{/snippet}

<div class="list">
  <div class="filters">
    <div class="chips" role="group" aria-label="Saved filters">
      {#each PRESETS as p (p.name)}
        <button type="button" class="fchip" aria-pressed={isPreset(f, p.f)} onclick={() => useChip(p)}>{p.name}</button>
      {/each}
      {#each saved as p (p.name)}
        <span class="fchip own" class:on={isPreset(f, p.f)}>
          <button type="button" aria-pressed={isPreset(f, p.f)} onclick={() => useChip(p)}>{p.name}</button>
          <button type="button" class="x" aria-label="Delete saved filter {p.name}" onclick={() => dropChip(p.name)}>×</button>
        </span>
      {/each}
      {#if naming}
        <form class="name" onsubmit={(e) => { e.preventDefault(); saveChip(); }}>
          <!-- svelte-ignore a11y_autofocus -->
          <input class="field" bind:value={newName} placeholder="Name this filter" aria-label="Saved filter name" maxlength="40" autofocus
            onkeydown={(e) => e.key === 'Escape' && (naming = false)} />
          <button class="btn" disabled={!newName.trim()}>Save</button>
        </form>
      {:else if hasFilters(f) && !matchesChip}
        <button type="button" class="fchip add" onclick={() => (naming = true)}>+ Save filter</button>
      {/if}
    </div>
    <input class="field search" type="search" bind:value={f.search} {placeholder} aria-label="Search items" />
    <div class="row">
      <MultiSelect label="All types" options={TYPE_OPTIONS} bind:selected={f.types} />
      {#if where === 'bags'}
        <MultiSelect label="Equipped & backpack" options={BAG_OPTIONS} bind:selected={f.bags} />
      {:else}
        <MultiSelect label="All locations" options={LOCATION_OPTIONS} bind:selected={f.locTypes} />
        {#if characters.length}<MultiSelect label="All characters" options={characters} bind:selected={f.chars} />{/if}
      {/if}
      <MultiSelect label="All traits" options={[{ v: 'any', l: 'Has a trait' }]} groups={TRAIT_GROUPS} bind:selected={f.traits} />

      <div class="extras">
        <button type="button" class="btn" class:active={extrasOn} aria-expanded={extrasOpen} onclick={() => (extrasOpen = !extrasOpen)}>
          {extrasOn ? 'Quality & more ◆' : 'Quality & more'} <span class="caret">{extrasOpen ? '▴' : '▾'}</span>
        </button>
        {#if extrasOpen}
          <div class="pop">
            <div class="label">QUALITY</div>
            <div class="pills">
              {#each QUALITY_OPTIONS as q (q.v)}
                <button type="button" class="pill" style="--qc: {q.color}" aria-pressed={f.quality === q.v} onclick={() => (f.quality = f.quality === q.v ? '' : q.v)}>{q.l}</button>
              {/each}
            </div>
            <label class="tick"><input type="checkbox" bind:checked={f.transmuted} /><img src="/assets/services/transmutation_station.png" alt="" />Transmuted</label>
            <label class="tick"><input type="checkbox" bind:checked={f.crafted} />Crafted</label>
            <label class="tick"><input type="checkbox" bind:checked={f.unbound} />Not bound</label>
            <label class="tick"><input type="checkbox" bind:checked={f.hasSet} />Part of a set</label>
          </div>
        {/if}
      </div>

      <button type="button" class="btn" class:active={groupBySet} aria-pressed={groupBySet} onclick={() => (groupBySet = !groupBySet)}>Group by set</button>
      {#if hasFilters(f)}<button type="button" class="btn" onclick={() => (f = emptyFilters())}>Clear</button>{/if}
      <span class="count num">
        {filtered.length.toLocaleString('en-US')} of {items.length.toLocaleString('en-US')}
        {#if sum.value}<span class="total" title="Average TTC listing price × quantity, unbound items only"> · ≈ {@render coin(sum.value)}</span>{/if}
      </span>
    </div>
  </div>

  {#if all}
    <div class="strip" aria-label="Item types and locations">
      {#each TYPE_OPTIONS as t (t.v)}
        {@const s = all.types[t.v]}
        {#if s}
          <button type="button" class="stat" aria-pressed={f.types.includes(t.v)} onclick={() => toggleIn('types', t.v)}>
            {#if ui.mode === 'classic' && TYPE_ICON[t.v]}<img class="ti" src="/assets/esoui/inventory/inventory_tabicon_{TYPE_ICON[t.v]}_{f.types.includes(t.v) ? 'down' : 'up'}.png" alt="" />{/if}
            <span class="sl">{t.l}</span><span class="sv"><span class="num">{s.count.toLocaleString('en-US')}</span>{#if s.value}{@render coin(s.value)}{/if}</span>
          </button>
        {/if}
      {/each}
      <span class="sep"></span>
      {#each LOCATION_OPTIONS as l (l.v)}
        {@const s = all.locs[l.v]}
        {#if s}
          <button type="button" class="stat" aria-pressed={f.locTypes.includes(l.v)} onclick={() => toggleIn('locTypes', l.v)}>
            <span class="sl">{l.l}</span><span class="sv"><span class="num">{s.count.toLocaleString('en-US')}</span>{#if s.value}{@render coin(s.value)}{/if}</span>
          </button>
        {/if}
      {/each}
    </div>
  {/if}

  <div class="scroll" bind:this={scroller}>
    <table>
      <thead>
        <tr>
          <th class="name"><button onclick={() => sortBy('name')}>Item {arrow('name')}</button></th>
          <th class="type"><button onclick={() => sortBy('filter_type_name')}>Type {arrow('filter_type_name')}</button></th>
          <th class="qty"><button onclick={() => sortBy('total_quantity')}>Qty {arrow('total_quantity')}</button></th>
          <th class="val"><button onclick={() => sortBy('value')} title={avgPrices.error || 'Average TTC listing price × quantity'}>Value {arrow('value')}</button></th>
          <th class="where">Where</th>
        </tr>
      </thead>
      <tbody>
        {#each shown as r (r.t === 'h' ? `h:${r.set}` : `i:${r.item.key}`)}
          {#if r.t === 'h'}
            <tr class="set"><td colspan="5">{r.set} <span>({r.count})</span></td></tr>
          {:else}
            {@const item = r.item}
            <tr class="item" tabindex="0" use:tooltip={{ component: ItemTip, props: { item } }}>
              <td class="name">
                <img src={itemIcon(item)} alt="" loading="lazy" />
                <span class="nm" style="color: {item.quality_color}">{item.name}</span>
                {#if item.level > 0}<span class="lv">Lv {item.level}</span>{/if}
              </td>
              <td class="type"><button class="cell" aria-pressed={f.types.includes(String(item.filter_type))} title="Filter by {item.filter_type_name}"
                onclick={() => toggleIn('types', String(item.filter_type))}>{item.filter_type_name}</button></td>
              <td class="qty num">{item.total_quantity.toLocaleString('en-US')}</td>
              <td class="val num">{#if item.value != null}<span title="≈ {gold(item.unit)} gold each">{@render coin(item.value)}</span>{:else if item.is_bound}<span class="dim">bound</span>{/if}</td>
              <td class="where">
                {#each item.locations.slice(0, MAX_LOCS) as loc (loc.location_key + loc.bag_id)}
                  <button class="chip" aria-pressed={locOn(loc)} title="Filter by this location" onclick={() => filterLoc(loc)}>{locLabel(loc)}{item.locations.length > 1 ? ` ×${loc.quantity}` : ''}</button>
                {/each}
                {#if item.locations.length > MAX_LOCS}<span class="chip more">+{item.locations.length - MAX_LOCS} more</span>{/if}
              </td>
            </tr>
          {/if}
        {:else}
          <tr><td colspan="5" class="empty">No items match these filters.</td></tr>
        {/each}
        {#if limit < rows.length}<tr use:more><td colspan="5" class="empty">Loading more…</td></tr>{/if}
      </tbody>
    </table>
  </div>
</div>

<style>
  .list { display: grid; gap: 10px; min-width: 0; }
  .filters { display: grid; gap: 8px; padding: 12px 14px; background: var(--panel); border: 1px solid var(--line); }
  .search { font-size: 15px; }
  .row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
  .btn.active { color: var(--accent-hi); border-color: var(--accent); }
  .caret { font-size: 11px; opacity: 0.7; }
  .count { margin-left: auto; font-size: 13px; color: var(--muted); }
  .total { color: var(--accent-hi); }

  .chips { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
  .fchip, .fchip.own button { all: unset; padding: 2px 10px; font-size: 13px; color: var(--muted); border: 1px solid var(--line); border-radius: 999px; cursor: pointer; transition: color 0.2s, border-color 0.2s; }
  .fchip.own { all: unset; display: inline-flex; align-items: center; border: 1px solid var(--line); border-radius: 999px; }
  .fchip.own button { border: 0; padding-right: 4px; }
  .fchip.own .x { padding: 0 8px 0 2px; }
  .fchip:hover, .fchip.own button:hover { color: var(--fg); }
  .fchip[aria-pressed='true'], .fchip.own.on { color: var(--accent-hi); border-color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); }
  .fchip:focus-visible, .fchip.own button:focus-visible { outline: 1px solid var(--accent-hi); }
  .fchip.add { border-style: dashed; }
  .name { display: flex; gap: 4px; }
  .name .field { width: 170px; padding: 2px 8px; font-size: 13px; }
  .name .btn { padding: 2px 10px; }

  .strip { display: flex; flex-wrap: wrap; gap: 6px; }
  .stat { all: unset; flex: 1 0 auto; display: grid; padding: 4px 10px; background: var(--panel); border: 1px solid var(--line); cursor: pointer; transition: border-color 0.2s; }
  .stat:hover { border-color: color-mix(in srgb, var(--accent) 60%, var(--line)); }
  .stat[aria-pressed='true'] { border-color: var(--accent); box-shadow: inset 0 -2px 0 var(--accent); }
  .stat:focus-visible { outline: 1px solid var(--accent-hi); }
  .sl { font: 600 11px var(--f-display); letter-spacing: 0.05em; color: var(--muted); text-transform: uppercase; }
  .sv { display: flex; justify-content: space-between; gap: 10px; font-size: 13px; }
  .g { display: inline-flex; align-items: center; gap: 2px; }
  .g img { width: 14px; height: 14px; }
  .sv .g { color: var(--accent-hi); }
  .sep { flex: none; width: 1px; background: var(--line); margin: 4px 2px; }

  .extras { position: relative; }
  .pop { position: absolute; top: calc(100% + 4px); left: 0; z-index: 30; width: 270px; padding: 12px; background: #0d0c0b; border: 1px solid var(--line); box-shadow: 0 16px 40px #000c; display: grid; gap: 8px; }
  .pills { display: flex; flex-wrap: wrap; gap: 4px; }
  .pill { all: unset; padding: 2px 8px; font-size: 13px; color: var(--qc); border: 1px solid #ffffff1a; cursor: pointer; }
  .pill[aria-pressed='true'] { border-color: var(--qc); background: color-mix(in srgb, var(--qc) 15%, transparent); }
  .pill:focus-visible { outline: 1px solid var(--accent-hi); }
  .tick { display: flex; align-items: center; gap: 6px; font-size: 14px; cursor: pointer; }
  .tick img { width: 15px; height: 15px; opacity: 0.8; }
  .tick input { accent-color: var(--accent); }

  /* The table scrolls inside the page so the view fits one screen. */
  .scroll { max-height: max(300px, calc(100dvh - 470px)); overflow: auto; background: var(--panel); border: 1px solid var(--line); }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  thead th { position: sticky; top: 0; z-index: 1; background: #0e0d0c; border-bottom: 1px solid var(--line); text-align: left; padding: 0; }
  th button { all: unset; display: block; padding: 8px 12px; font: 600 12px var(--f-display); letter-spacing: 0.12em; color: var(--muted); cursor: pointer; white-space: nowrap; }
  th button:hover { color: var(--fg); }
  th.where { padding: 8px 12px; font: 600 12px var(--f-display); letter-spacing: 0.12em; color: var(--muted); }
  td { padding: 5px 12px; border-bottom: 1px solid #ffffff0a; vertical-align: middle; }
  tr.item { cursor: default; transition: background 0.15s; }
  tr.item:hover, tr.item:focus-visible { background: #ffffff0a; outline: none; }
  td.name { display: flex; align-items: center; gap: 8px; min-width: 0; }
  td.name img { width: 30px; height: 30px; flex: none; }
  .nm { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .lv { font-size: 12px; color: var(--muted); white-space: nowrap; }
  td.type { color: var(--muted); white-space: nowrap; }
  td.qty, td.val { text-align: right; color: var(--muted); white-space: nowrap; }
  th.qty button, th.val button { box-sizing: border-box; width: 100%; text-align: right; }
  .dim { font-size: 12px; opacity: 0.6; }
  .cell { all: unset; cursor: pointer; }
  .cell:hover, .cell[aria-pressed='true'] { color: var(--accent-hi); }
  .cell:focus-visible { outline: 1px solid var(--accent-hi); }
  .chip.more { color: var(--accent); }
  .chip { all: unset; display: inline-block; margin: 1px 4px 1px 0; padding: 0 6px; font-size: 12px; color: var(--muted); border: 1px solid var(--line); white-space: nowrap; }
  button.chip { cursor: pointer; }
  button.chip:hover { color: var(--fg); }
  button.chip[aria-pressed='true'] { color: var(--accent-hi); border-color: var(--accent); }
  button.chip:focus-visible { outline: 1px solid var(--accent-hi); }
  tr.set td { padding: 6px 12px; background: #ffffff06; font: 600 13px var(--f-display); letter-spacing: 0.06em; color: var(--accent-hi); }
  tr.set span { font: 400 12px var(--f-ui); color: var(--muted); letter-spacing: 0; }
  .empty { text-align: center; padding: 36px; color: var(--muted); }
  @media (max-width: 760px) { .type, .where, .val { display: none; } }
  .ti { display: none; }
  /* Classic: the in-game inventory window. Panels on the window backdrop, list rows on ZO_ListEntryBackdrop with the
     teal mouse-over highlight, sort headers in the header font, type stats with the inventory tab icons. */
  :global(:root[data-ui='classic']) .filters, :global(:root[data-ui='classic']) .scroll { background: var(--eso-panel) center / 100% 100%; border: 0; }
  :global(:root[data-ui='classic']) .filters { padding: 12px 16px; }
  :global(:root[data-ui='classic']) .count { font: 500 16px var(--eso-font-medium); color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .total, :global(:root[data-ui='classic']) .sv .g { color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .fchip, :global(:root[data-ui='classic']) .fchip.own { border: 0 solid transparent; border-radius: 0; border-image: url('/assets/esoui/buttons/eso_buttonlarge_normal.png') 0 9 fill / 0 9px stretch;
    padding: 2px 12px; font: 700 16px var(--eso-font); color: var(--eso-normal); text-shadow: var(--eso-shadow); }
  :global(:root[data-ui='classic']) .fchip.own button { font: 700 16px var(--eso-font); color: inherit; }
  :global(:root[data-ui='classic']) .fchip:hover, :global(:root[data-ui='classic']) .fchip.own button:hover { color: var(--eso-highlight); }
  :global(:root[data-ui='classic']) .fchip[aria-pressed='true'], :global(:root[data-ui='classic']) .fchip.own.on { color: var(--eso-selected); background: none; border-image-source: url('/assets/esoui/buttons/eso_buttonllarge_mousedown.png'); }
  :global(:root[data-ui='classic']) .fchip.add { border-style: solid; }
  :global(:root[data-ui='classic']) .stat { position: relative; grid-template-columns: auto 1fr; column-gap: 4px; align-items: center; background: none; border: 0; padding: 2px 3px; }
  :global(:root[data-ui='classic']) .strip { gap: 2px; }
  :global(:root[data-ui='classic']) .stat > .sl, :global(:root[data-ui='classic']) .stat > .sv { grid-column: 2; }
  :global(:root[data-ui='classic']) .ti { display: block; grid-row: span 2; width: 28px; height: 28px; }
  :global(:root[data-ui='classic']) .stat:hover { border-color: transparent; background: var(--eso-hover) center / 100% 100%; }
  :global(:root[data-ui='classic']) .stat[aria-pressed='true'] { box-shadow: none; background: var(--eso-list-hl) center / 100% 100%; }
  :global(:root[data-ui='classic']) .sl { font: 700 14px var(--eso-font); letter-spacing: 0; color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .sv { gap: 6px; font: 500 15px var(--eso-font-medium); color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .sep { width: 8px; margin: 0 4px; background: url('/assets/esoui/miscellaneous/verticaldivider_64.png') center / 8px 100% no-repeat; }
  :global(:root[data-ui='classic']) .pop { background: none; border: 0 solid transparent; border-image: var(--eso-backdrop) 16 fill / 16px; padding: 18px; }
  :global(:root[data-ui='classic']) .pill { font: 500 16px var(--eso-font-medium); }
  :global(:root[data-ui='classic']) .tick { font: 500 18px var(--eso-font-medium); color: var(--eso-selected); }
  :global(:root[data-ui='classic']) table { font: 500 18px var(--eso-font-medium); }
  :global(:root[data-ui='classic']) thead th { background: #000c; border-bottom: 0; }
  :global(:root[data-ui='classic']) th button, :global(:root[data-ui='classic']) th.where { font: 700 16px var(--eso-font); letter-spacing: 0; text-transform: uppercase; color: var(--eso-normal); text-shadow: var(--eso-shadow); }
  :global(:root[data-ui='classic']) th button:hover { color: var(--eso-highlight); }
  :global(:root[data-ui='classic']) td { border-bottom: 0; padding: 4px 12px; }
  :global(:root[data-ui='classic']) tr.item { background: var(--eso-list-bg) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) tr.item:hover, :global(:root[data-ui='classic']) tr.item:focus-visible { background: var(--eso-hover) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) td.name img { width: 40px; height: 40px; }
  :global(:root[data-ui='classic']) td.type, :global(:root[data-ui='classic']) td.qty, :global(:root[data-ui='classic']) td.val { color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .lv { font-size: 16px; color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .chip { font: 500 15px var(--eso-font-medium); color: var(--eso-normal); border-color: var(--line); }
  :global(:root[data-ui='classic']) button.chip[aria-pressed='true'], :global(:root[data-ui='classic']) .cell[aria-pressed='true'] { color: var(--eso-highlight); }
  :global(:root[data-ui='classic']) tr.set td { background: #0008; font: 700 18px var(--eso-font); letter-spacing: 0; text-transform: uppercase; color: var(--eso-selected); }
  :global(:root[data-ui='classic']) tr.set span { font: 500 16px var(--eso-font-medium); color: var(--eso-normal); }
</style>
