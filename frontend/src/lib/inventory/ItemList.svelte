<script>
  import MultiSelect from '../ui/MultiSelect.svelte';
  import ItemTip from '../tips/ItemTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { itemIcon } from '../gear.js';
  import {
    TYPE_OPTIONS, BAG_OPTIONS, LOCATION_OPTIONS, TRAIT_GROUPS, QUALITY_OPTIONS,
    emptyFilters, hasFilters, filterItems, sortItems, displayRows,
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

  const filtered = $derived(sortItems(filterItems(items, f), sort.key, sort.dir));
  const rows = $derived(displayRows(filtered, groupBySet));
  const extrasOn = $derived(f.quality !== '' || f.transmuted || f.crafted);

  /** @param {string} key */
  function sortBy(key) {
    sort = sort.key === key ? { key, dir: sort.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: key === 'name' ? 'asc' : 'desc' };
  }
  /** @param {string} key */
  const arrow = (key) => (sort.key === key ? (sort.dir === 'asc' ? '▲' : '▼') : '');
  /** @param {any} loc */
  const locLabel = (loc) => (where === 'bags' || loc.location_type !== 'character' ? loc.bag_label : `${loc.location_label} · ${loc.bag_label}`);
</script>

<svelte:window onpointerdown={(e) => extrasOpen && !(/** @type {Element} */ (e.target)).closest('.extras') && (extrasOpen = false)} />

<div class="list">
  <div class="filters">
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
          </div>
        {/if}
      </div>

      <button type="button" class="btn" class:active={groupBySet} aria-pressed={groupBySet} onclick={() => (groupBySet = !groupBySet)}>Group by set</button>
      {#if hasFilters(f)}<button type="button" class="btn" onclick={() => (f = emptyFilters())}>Clear</button>{/if}
      <span class="count num">{filtered.length.toLocaleString('en-US')} of {items.length.toLocaleString('en-US')}</span>
    </div>
  </div>

  <div class="scroll">
    <table>
      <thead>
        <tr>
          <th class="name"><button onclick={() => sortBy('name')}>Item {arrow('name')}</button></th>
          <th class="type"><button onclick={() => sortBy('filter_type_name')}>Type {arrow('filter_type_name')}</button></th>
          <th class="qty"><button onclick={() => sortBy('total_quantity')}>Qty {arrow('total_quantity')}</button></th>
          <th class="where">Where</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as r (r.t === 'h' ? `h:${r.set}` : `i:${r.item.key}`)}
          {#if r.t === 'h'}
            <tr class="set"><td colspan="4">{r.set} <span>({r.count})</span></td></tr>
          {:else}
            {@const item = r.item}
            <tr class="item" tabindex="0" use:tooltip={{ component: ItemTip, props: { item } }}>
              <td class="name">
                <img src={itemIcon(item)} alt="" loading="lazy" />
                <span class="nm" style="color: {item.quality_color}">{item.name}</span>
                {#if item.level > 0}<span class="lv">Lv {item.level}</span>{/if}
              </td>
              <td class="type">{item.filter_type_name}</td>
              <td class="qty num">{item.total_quantity.toLocaleString('en-US')}</td>
              <td class="where">
                {#each item.locations as loc (loc.location_key + loc.bag_id)}
                  <span class="chip">{locLabel(loc)}{item.locations.length > 1 ? ` ×${loc.quantity}` : ''}</span>
                {/each}
              </td>
            </tr>
          {/if}
        {:else}
          <tr><td colspan="4" class="empty">No items match these filters.</td></tr>
        {/each}
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
  .scroll { max-height: max(300px, calc(100dvh - 400px)); overflow: auto; background: var(--panel); border: 1px solid var(--line); }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  thead th { position: sticky; top: 0; z-index: 1; background: #0e0d0c; border-bottom: 1px solid var(--line); text-align: left; padding: 0; }
  th button { all: unset; display: block; padding: 8px 12px; font: 600 12px var(--f-display); letter-spacing: 0.12em; color: var(--muted); cursor: pointer; white-space: nowrap; }
  th button:hover { color: var(--fg); }
  th.where { padding: 8px 12px; font: 600 12px var(--f-display); letter-spacing: 0.12em; color: var(--muted); }
  th.qty button { text-align: right; }
  td { padding: 5px 12px; border-bottom: 1px solid #ffffff0a; vertical-align: middle; }
  tr.item { cursor: default; transition: background 0.15s; }
  tr.item:hover, tr.item:focus-visible { background: #ffffff0a; outline: none; }
  td.name { display: flex; align-items: center; gap: 8px; min-width: 0; }
  td.name img { width: 30px; height: 30px; flex: none; }
  .nm { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .lv { font-size: 12px; color: var(--muted); white-space: nowrap; }
  td.type { color: var(--muted); white-space: nowrap; }
  td.qty { text-align: right; color: var(--muted); }
  .chip { display: inline-block; margin: 1px 4px 1px 0; padding: 0 6px; font-size: 12px; color: var(--muted); border: 1px solid var(--line); white-space: nowrap; }
  tr.set td { padding: 6px 12px; background: #ffffff06; font: 600 13px var(--f-display); letter-spacing: 0.06em; color: var(--accent-hi); }
  tr.set span { font: 400 12px var(--f-ui); color: var(--muted); letter-spacing: 0; }
  .empty { text-align: center; padding: 36px; color: var(--muted); }
  @media (max-width: 760px) { .type, .where { display: none; } }
</style>
