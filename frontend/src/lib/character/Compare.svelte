<script>
  import Frame from '../ui/Frame.svelte';
  import PaperDoll from './PaperDoll.svelte';
  import SkillBars from './SkillBars.svelte';
  import ChampionPoints from './ChampionPoints.svelte';
  import ItemTip from '../tips/ItemTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { app, toast, exportBuild, importCompare, deleteCompare } from '../store.svelte.js';
  import { prices, priceKey, loadPrice } from '../lookups.svelte.js';
  import { equipped, setCounts } from '../gear.js';
  import { importedGearItem, missingItems } from '../compare.js';

  /** This character's build next to one imported by share code, plus what's missing and its TTC cost. @type {{ char: any }} */
  let { char } = $props();

  const items = $derived(app.data.value?.items ?? []);
  const current = $derived(equipped(items, char.id));
  const currentSets = $derived(setCounts(current));
  const hasBuild = $derived(!!app.builds.value?.builds?.some((/** @type {any} */ b) => b.char_id === char.id && b.gear?.length));

  const record = $derived(app.compare.value?.imported?.[String(char.id)] ?? null);
  const build = $derived(record?.build ?? null);
  const imported = $derived.by(() => {
    /** @type {Record<number, any>} */
    const m = {};
    for (const g of build?.gear ?? []) m[g.slot] = importedGearItem(g, items);
    return m;
  });
  const importedSets = $derived(setCounts(imported));
  const names = $derived({ ...(app.builds.value?.abilityNames ?? {}), ...(record?.ability_names ?? {}) });
  const cpNames = $derived({ ...(app.builds.value?.cpNames ?? {}), ...(record?.cp_names ?? {}) });

  const missing = $derived(build ? missingItems(build.gear, items, app.stickerbook.value?.sets ?? []) : []);
  $effect(() => {
    for (const m of missing) if (m.priced) loadPrice(m.name);
  });
  /** @param {any} m */
  const avg = (m) => (m.priced && typeof prices[priceKey(m.name)]?.avg === 'number' ? prices[priceKey(m.name)].avg : null);
  const total = $derived(missing.reduce((s, m) => s + (avg(m) ?? 0), 0));
  const gold = (/** @type {number} */ n) => Math.round(n).toLocaleString('en-US');

  let code = $state('');
  let exported = $state('');
  let busy = $state(false);
  let status = $state('');

  /** @param {() => Promise<void>} fn */
  async function run(fn) {
    if (busy) return;
    busy = true;
    status = '';
    try {
      await fn();
    } catch (e) {
      status = /** @type {Error} */ (e).message || 'Something went wrong';
    } finally {
      busy = false;
    }
  }
  const doExport = () =>
    run(async () => {
      exported = await exportBuild(char.id);
      try {
        await navigator.clipboard.writeText(exported);
        toast('Build code copied');
      } catch {
        toast(`Exported ${exported}`);
      }
    });
  const doImport = () => run(async () => { await importCompare(char.id, code); code = ''; toast('Imported compare build'); });
  const doDelete = () => run(async () => { await deleteCompare(char.id); toast('Imported build deleted'); });
</script>

<div class="bar">
  <button class="btn" disabled={busy || !hasBuild} onclick={doExport}>Export build code</button>
  {#if exported}<span class="code">Code <code>{exported}</code></span>{/if}
  <form class="imp" onsubmit={(e) => { e.preventDefault(); if (code.trim()) doImport(); }}>
    <input class="field" bind:value={code} placeholder="ABCD-EFGH" aria-label="Build code to import" autocomplete="off" spellcheck="false" />
    <button class="btn" disabled={busy || !code.trim()}>Import by code</button>
  </form>
  {#if record}<button class="btn" disabled={busy} onclick={doDelete}>Delete imported build</button>{/if}
  {#if status}<span class="err" role="status">{status}</span>{/if}
</div>

<div class="sheet">
  <div class="col">
    <PaperDoll gear={current} race={char.race} gender={char.gender} setCount={(i) => currentSets.find(([s]) => s === i?.set_name)?.[1] ?? 0} title="CURRENT BUILD" />
  </div>

  <div class="col">
    {#if build}
      <PaperDoll gear={imported} race={build.race} setCount={(i) => importedSets.find(([s]) => s === i?.set_name)?.[1] ?? 0} title={`IMPORTED · ${(build.char_name || 'BUILD').toUpperCase()}`} />
    {:else}
      <Frame title="IMPORTED BUILD" delay={0.1}>
        <p class="hint empty">Paste a build code above to compare it with {char.name}'s current gear. Codes come from "Export build code" on any character, yours or a friend's.</p>
      </Frame>
    {/if}
  </div>

  <div class="col">
    <Frame title="MISSING ITEMS" delay={0.15}>
      {#if !build}
        <p class="hint empty">Import a build to see which pieces you don't own and what they cost on the Trade Centre.</p>
      {:else if !missing.length}
        <p class="ok empty">You own every piece of this build.</p>
      {:else}
        <ul class="missing">
          {#each missing as m (`${m.slot}-${m.item_id}-${m.trait_id}-${m.enchant_id}`)}
            <li use:tooltip={{ component: ItemTip, props: { item: imported[m.slot] } }}>
              <span class="row"><span class="nm">{m.slot_name}: {m.name}</span>
                <span class="price">{m.crafted ? 'Crafted' : !m.priced ? m.dropLabel : avg(m) != null ? `~${gold(avg(m))}g` : prices[priceKey(m.name)]?.loading ? '…' : 'No price'}</span></span>
              <span class="src">{m.sourceText}</span>
            </li>
          {/each}
        </ul>
        <div class="total">Purchasable total <b class="num">{gold(total)} gold</b></div>
      {/if}
    </Frame>
    {#if build}
      <SkillBars skills={build.skills} {names} delay={0.25} />
      <ChampionPoints cp={build.cp} names={cpNames} delay={0.3} />
    {/if}
  </div>
</div>

<style>
  .bar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 12px; }
  .code { font-size: 14px; color: var(--muted); }
  .code code { color: var(--accent-hi); letter-spacing: 0.08em; }
  .imp { display: flex; gap: 6px; margin-left: auto; }
  .imp .field { width: 130px; padding: 5px 8px; text-transform: uppercase; letter-spacing: 0.08em; }
  .sheet { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; align-items: start; }
  @media (max-width: 980px) { .sheet { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); } .col:last-child { grid-column: 1 / -1; } }
  @media (max-width: 620px) { .sheet { grid-template-columns: minmax(0, 1fr); } .imp { margin-left: 0; } }
  .col { display: grid; gap: 14px; min-width: 0; }
  .empty { text-align: center; margin: 6px 0; }
  .missing { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; max-height: 300px; overflow-y: auto; }
  .missing li { padding: 5px 8px; background: #ffffff06; border-left: 2px solid var(--accent); outline: none; }
  .missing li:hover { background: #ffffff0d; }
  .row { display: flex; justify-content: space-between; gap: 8px; font-size: 14px; }
  .nm { color: var(--accent-hi); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .price { color: var(--muted); white-space: nowrap; font-size: 13px; }
  .src { display: block; font-size: 12px; color: var(--muted); }
  .total { margin-top: 8px; display: flex; justify-content: space-between; font-size: 14px; color: var(--muted); }
  .total b { color: var(--accent-hi); font-weight: 600; }
</style>
