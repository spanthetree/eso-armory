<script>
  import Modal from '../ui/Modal.svelte';
  import FilePick from './FilePick.svelte';
  import { app, toast } from '../store.svelte.js';
  import { nav } from '../nav.svelte.js';
  import { uploadFiles, canWatchFolder, watch, pickFolder, stopWatching } from '../upload.svelte.js';

  /** @type {Record<string, File | null>} */
  let files = $state({ iasync: null, ww: null, ttc_lookup: null, ttc_price: null });
  let busy = $state(false);
  /** @type {any} */
  let result = $state(null);
  let error = $state('');
  let help = $state('');

  $effect(() => {
    if (nav.dialog === 'upload') {
      result = null;
      error = '';
      help = '';
    }
  });
  const any = $derived(!!(files.iasync || files.ww || (app.status.isAdmin && (files.ttc_lookup || files.ttc_price))));

  async function load() {
    if (!any || busy) return;
    busy = true;
    error = '';
    result = null;
    try {
      result = await uploadFiles(app.status.isAdmin ? files : { iasync: files.iasync, ww: files.ww });
      if (result?.iasync?.ok) {
        nav.dialog = '';
        toast(`Armory loaded into ${result.iasync.slot_updated || app.workspace.activeSlot}`);
      }
    } catch (e) {
      error = /** @type {Error} */ (e).message;
    } finally {
      busy = false;
    }
  }

  async function folder() {
    if (await pickFolder()) nav.dialog = '';
  }
  const time = (/** @type {number} */ t) => new Date(t).toLocaleTimeString();
  const LINES = [
    ['iasync', 'iasync'],
    ['ww', 'WizardsWardrobe'],
    ['ttc_lookup', 'TTC lookup table'],
    ['ttc_price', 'TTC price table'],
  ];
</script>

{#snippet helpBtn(/** @type {string} */ key, /** @type {string} */ text)}
  <span class="help">
    <button type="button" class="q" aria-expanded={help === key} aria-label="Help" onclick={() => (help = help === key ? '' : key)}>?</button>
    {#if help === key}<span class="pop" role="note">{text}</span>{/if}
  </span>
{/snippet}

<Modal open={nav.dialog === 'upload'} title="Upload ESO Data" onclose={() => (nav.dialog = '')} wide>
  <p class="hint">Find your SavedVariables files in <code>Documents/Elder Scrolls Online/live/SavedVariables/</code></p>

  {#if canWatchFolder}
    <section>
      <div class="label">AUTO-WATCH FOLDER {@render helpBtn('folder', "Watches your ESO live folder and reloads automatically when the game saves new data. You'll need to pick it again after restarting your browser.")}<span class="note">Chrome / Edge only</span></div>
      {#if watch.handle}
        <div class="watching">
          <span>📁 {watch.handle.name}</span><span class="tag">Watching</span>
          <button type="button" class="x" aria-label="Stop watching" onclick={stopWatching}>×</button>
        </div>
        <ul class="synced">
          {#each [['iasync', 'iasync.lua'], ['ww', 'WizardsWardrobe.lua'], ...(app.status.isAdmin ? [['ttcLookup', 'ItemLookUpTable_EN.lua'], ['ttcPrice', 'PriceTable*.lua']] : [])] as [k, label] (k)}
            <li><span>{label}</span><span>{watch.synced[k] ? `synced ${time(watch.synced[k])}` : 'not yet synced'}</span></li>
          {/each}
          {#if watch.checked}<li><span>Last checked</span><span>{time(watch.checked)}</span></li>{/if}
        </ul>
      {:else}
        <button type="button" class="pickdir" onclick={folder}>📁 Select your ESO <b>live</b> folder…</button>
      {/if}
    </section>
    <div class="or"><span>or upload files</span></div>
  {/if}

  <form onsubmit={(e) => { e.preventDefault(); load(); }}>
    <div class="label">IASYNC.LUA <span class="note">inventory & characters</span> {@render helpBtn('iasync', 'Your characters, inventory, gear and currencies: the main data file. SavedVariables\\iasync.lua')}</div>
    <FilePick id="up-iasync" bind:file={files.iasync} placeholder="Click or drop iasync.lua here" />

    <div class="label">WIZARDSWARDROBE.LUA <span class="note">optional, builds</span> {@render helpBtn('ww', 'Saved build loadouts; only needed if you use the Wizards Wardrobe addon. SavedVariables\\WizardsWardrobe.lua')}</div>
    <FilePick id="up-ww" bind:file={files.ww} placeholder="Click or drop WizardsWardrobe.lua here" />

    {#if app.status.isAdmin}
      <div class="label">TAMRIEL TRADE CENTRE <span class="note">pricing, admin only</span></div>
      <FilePick id="up-ttc-lookup" bind:file={files.ttc_lookup} placeholder="Click or drop ItemLookUpTable_EN.lua here" />
      <FilePick id="up-ttc-price" bind:file={files.ttc_price} placeholder="Click or drop PriceTableNA.lua / PriceTableEU.lua here" />
    {/if}

    <button class="btn primary" disabled={!any || busy}>{busy ? 'Parsing…' : 'Load Files'}</button>
  </form>

  {#if error}<p class="err" role="alert">{error}</p>{/if}
  {#if result}
    <ul class="results" role="status">
      {#each LINES as [field, label] (field)}
        {@const r = result[field]}
        {#if r}
          <li class={r.ok ? 'ok' : 'err'}>
            {#if !r.ok}✗ {label}: {r.error}
            {:else if field === 'iasync'}✓ iasync: {r.chars} characters, {r.items.toLocaleString('en-US')} items into {r.slot_updated || 'primary'}
            {:else if field === 'ww'}✓ WizardsWardrobe: {r.builds} builds into {r.slot_updated || app.workspace.activeSlot}
            {:else}✓ {label}{/if}
          </li>
        {/if}
      {/each}
    </ul>
  {/if}
</Modal>

<style>
  p { margin: 0 0 12px; }
  section { margin-bottom: 12px; }
  .label { display: flex; align-items: center; gap: 6px; margin: 12px 0 6px; }
  .note { font: 400 12px var(--f-ui); letter-spacing: 0; color: var(--muted); }
  .label .note:last-child { margin-left: auto; }
  .help { position: relative; display: inline-flex; }
  .q { all: unset; display: grid; place-items: center; width: 15px; height: 15px; border: 1px solid var(--muted); border-radius: 50%; font: 600 10px var(--f-ui); color: var(--muted); cursor: pointer; }
  .q[aria-expanded='true'], .q:hover { border-color: var(--accent); color: var(--accent-hi); }
  .q:focus-visible { outline: 1px solid var(--accent-hi); }
  .pop { position: absolute; top: 20px; left: 0; z-index: 5; width: 260px; padding: 8px 10px; font: 400 13px/1.35 var(--f-ui); letter-spacing: 0; color: var(--fg); background: #0d0c0b; border: 1px solid var(--line); box-shadow: 0 10px 30px #000c; white-space: normal; }
  .pickdir { all: unset; box-sizing: border-box; display: block; width: 100%; padding: 12px 14px; border: 1px dashed var(--line); color: var(--muted); cursor: pointer; }
  .pickdir:hover, .pickdir:focus-visible { border-color: var(--accent); color: var(--fg); }
  .watching { display: flex; align-items: center; gap: 10px; padding: 9px 12px; border: 1px solid var(--accent); font-size: 14px; }
  .tag { font-size: 11px; padding: 0 6px; color: var(--bg); background: var(--accent); }
  .x { all: unset; margin-left: auto; cursor: pointer; font-size: 18px; color: var(--muted); }
  .x:hover { color: var(--fg); }
  .synced { list-style: none; margin: 6px 0 0; padding: 0; font-size: 12px; color: var(--muted); }
  .synced li { display: flex; justify-content: space-between; }
  .or { display: flex; align-items: center; gap: 10px; margin: 14px 0 4px; font-size: 12px; color: var(--muted); }
  .or::before, .or::after { content: ''; flex: 1; height: 1px; background: var(--line); }
  form { display: grid; gap: 6px; }
  form .btn.primary { margin-top: 12px; }
  .results { list-style: none; padding: 0; margin: 12px 0 0; display: grid; gap: 4px; font-size: 14px; }
  .err { margin-top: 12px; }
</style>
