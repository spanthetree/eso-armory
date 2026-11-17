<script>
  import Frame from '../ui/Frame.svelte';
  import { app, saveApiKey, deleteApiKey, parseSuperstar } from '../store.svelte.js';
  import { equipped } from '../gear.js';
  import { superstarRows } from '../compare.js';

  /**
   * Compare a SuperStar build screenshot (read by Claude vision on the server) with this character's
   * gear and everything the account owns.
   * @type {{ char: any }}
   */
  let { char } = $props();

  let file = $state(/** @type {File | null} */ (null));
  let result = $state(/** @type {any} */ (null));
  let needKey = $state(false);
  let key = $state('');
  let busy = $state(false);
  let status = $state('');
  let dragging = $state(false);
  /** @type {HTMLInputElement} */
  let picker;

  const rows = $derived(result ? superstarRows(result.gear, equipped(app.data.value?.items, char.id), app.data.value?.items ?? []) : []);

  /** @param {File | null | undefined} f */
  function receive(f) {
    if (!f || !f.type.startsWith('image/') || busy) return;
    file = f;
    status = '';
    if (app.status.hasServerKey || app.status.hasSessionKey) parse();
    else needKey = true;
  }
  async function parse() {
    if (!file) return;
    busy = true;
    needKey = false;
    status = '';
    try {
      result = await parseSuperstar(file);
      key = '';
    } catch (e) {
      status = /** @type {Error} */ (e).message;
    } finally {
      busy = false;
    }
  }
  async function saveAndParse() {
    if (!key.trim() || busy) return;
    busy = true;
    try {
      await saveApiKey(key.trim());
    } catch (e) {
      status = /** @type {Error} */ (e).message;
      busy = false;
      return;
    }
    busy = false;
    parse();
  }
  /** @param {ClipboardEvent} e */
  function onpaste(e) {
    if (result) return;
    const it = [...(e.clipboardData?.items ?? [])].find((i) => i.type.startsWith('image/'));
    if (it) receive(it.getAsFile());
  }
  const STATUS_CLASS = /** @type {Record<string, string>} */ ({ equipped: 'ok', have: 'have', wrong_trait: 'warn', missing: 'bad', na: 'na' });
</script>

<svelte:window {onpaste} />

<Frame title="SUPERSTAR COMPARE" delay={0.05}>
  <div class="top">
    <p class="hint">Compare a build screenshot from SuperStar with {char.name}'s gear and everything on the account.</p>
    {#if app.status.hasSessionKey}
      <span class="hint">API key saved · <button class="link" onclick={deleteApiKey}>Remove</button></span>
    {/if}
  </div>

  {#if !result}
    {#if needKey}
      <form class="key" onsubmit={(e) => { e.preventDefault(); saveAndParse(); }}>
        <p class="hint">Reading the screenshot needs an <b>Anthropic API key</b> (Claude vision). It's stored encrypted for this browser session only.</p>
        <input class="field" type="password" bind:value={key} placeholder="sk-ant-..." autocomplete="off" disabled={busy} aria-label="Anthropic API key" />
        <div class="row">
          <button class="btn primary" disabled={!key.trim() || busy}>{busy ? 'Working…' : 'Read screenshot'}</button>
          <button type="button" class="btn" onclick={() => { needKey = false; file = null; status = ''; }}>Back</button>
        </div>
      </form>
    {:else}
      <button
        class="drop"
        class:dragging
        disabled={busy}
        onclick={() => picker.click()}
        ondragover={(e) => { e.preventDefault(); dragging = true; }}
        ondragleave={() => (dragging = false)}
        ondrop={(e) => { e.preventDefault(); dragging = false; receive(e.dataTransfer?.files?.[0]); }}>
        {#if busy}
          <span class="big">Reading the screenshot…</span>
        {:else}
          <span class="big">Press <kbd>Ctrl</kbd>+<kbd>V</kbd> to paste a screenshot</span>
          <span class="hint">or click to choose a file · drag and drop also works</span>
        {/if}
      </button>
      <input bind:this={picker} type="file" accept="image/*" hidden onchange={(e) => receive(/** @type {HTMLInputElement} */ (e.currentTarget).files?.[0])} />
    {/if}
    {#if status}<p class="err" role="alert">{status}</p>{/if}
  {:else}
    <div class="row head">
      <span><b>{result.character?.name || 'Unknown build'}</b>{#if result.character?.cp} · {result.character.cp} CP{/if}{#if result.mundus} · {result.mundus}{/if}</span>
      <button class="btn" onclick={() => { result = null; file = null; status = ''; }}>New screenshot</button>
    </div>
    <div class="scroll">
      <table>
        <thead>
          <tr><th rowspan="2">Slot</th><th colspan="3">Target build</th><th colspan="3">{char.name} wears</th><th rowspan="2">Have it?</th></tr>
          <tr><th>Item</th><th>Trait</th><th>Enchant</th><th>Item</th><th>Trait</th><th>Enchant</th></tr>
        </thead>
        <tbody>
          {#each rows as r, i (`${r.slot}-${i}`)}
            <tr>
              <td class="muted">{r.slot}</td>
              <td class:muted={!r.item_name}>{r.item_name || 'N/A'}</td>
              <td class="muted">{r.trait || '–'}</td>
              <td class="muted">{r.enchantment || '–'}</td>
              <td class={r.status === 'na' ? 'muted' : r.curItemMatch ? 'ok' : 'warn'}>{r.cur?.name || (r.status === 'na' ? 'N/A' : '(empty)')}</td>
              <td class={!r.cur?.trait ? 'muted' : r.curTraitMatch ? 'ok' : 'warn'}>{r.cur?.trait || '–'}</td>
              <td class="muted">{r.cur?.enchant || '–'}</td>
              <td class="status {STATUS_CLASS[r.status]}">{r.statusLabel}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</Frame>

<style>
  .top { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; margin-bottom: 12px; }
  .top p { margin: 0; }
  .link { all: unset; cursor: pointer; color: var(--accent); }
  .link:hover { color: var(--accent-hi); }
  .drop {
    all: unset;
    box-sizing: border-box;
    display: grid;
    gap: 6px;
    justify-items: center;
    width: 100%;
    padding: 44px 16px;
    border: 1px dashed var(--line);
    cursor: pointer;
    text-align: center;
    transition: border-color 0.2s, background 0.2s;
  }
  .drop:hover, .drop.dragging, .drop:focus-visible { border-color: var(--accent); background: #ffffff05; }
  .big { font-size: 16px; }
  kbd { padding: 0 5px; border: 1px solid var(--line); font: 12px ui-monospace, monospace; color: var(--muted); }
  .key { display: grid; gap: 10px; max-width: 460px; margin: 0 auto; }
  .key .btn.primary { width: auto; }
  .row { display: flex; gap: 8px; align-items: center; }
  .head { justify-content: space-between; margin-bottom: 10px; font-size: 15px; }
  .scroll { overflow: auto; max-height: max(300px, calc(100dvh - 420px)); }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; font: 600 11px var(--f-display); letter-spacing: 0.1em; color: var(--muted); padding: 4px 10px 4px 0; border-bottom: 1px solid var(--line); white-space: nowrap; }
  td { padding: 4px 10px 4px 0; border-bottom: 1px solid #ffffff0a; }
  .muted { color: var(--muted); }
  .ok { color: var(--q-fine); }
  .have { color: var(--q-superior); }
  .warn { color: #e8b04a; }
  .bad { color: #e5675a; }
  .na { color: var(--muted); }
  .status { font-weight: 600; white-space: nowrap; }
</style>
