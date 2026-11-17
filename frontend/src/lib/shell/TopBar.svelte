<script>
  import { ui, setUiMode } from '../uimode.svelte.js';
  import { app, refresh, switchSlot, deleteShadow, toast } from '../store.svelte.js';
  import { nav, go } from '../nav.svelte.js';
  import { watch, checkFolder } from '../upload.svelte.js';

  const data = $derived(app.data.value);
  const ws = $derived(app.workspace);

  /** Character currency plus bank, like the classic header. @param {string} key */
  function total(key) {
    const chars = Object.values(data?.characters ?? {});
    return chars.reduce((s, c) => s + (c[key] || 0), 0) + (data?.bank?.[key] || 0);
  }
  const CURRENCIES = [
    ['gold', 'Gold'],
    ['ap', 'Alliance Points'],
    ['tv', 'Tel Var Stones'],
    ['wv', 'Writs'],
  ];
  /** @param {number} n */
  const short = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : String(n));

  let refreshing = $state(false);
  async function onRefresh() {
    refreshing = true;
    // With a watched folder, refresh means "re-read the folder"; otherwise ask the server.
    if (watch.handle) toast((await checkFolder()) ? 'Data updated' : 'No updates');
    else await refresh();
    refreshing = false;
  }

  /** @param {'primary' | 'shadow'} slot */
  async function slot(slot) {
    if (slot === 'shadow' && !ws.shadow.account) return;
    go('characters');
    await switchSlot(slot);
  }
</script>

<header class="bar">
  <div class="brand">
    <span class="word">ESO ARMORY</span>
    {#if data}
      <span class="meta">
        {data.meta.account} · {data.meta.server} · <span class="num">{data.meta.item_count.toLocaleString('en-US')}</span> items
        {#if app.status.isAdmin}<span class="badge">admin</span>{/if}
      </span>
    {/if}
  </div>

  {#if ws.primary.account || ws.shadow.account}
    <div class="slots" role="group" aria-label="Workspace">
      <button class="btn" aria-pressed={ws.activeSlot === 'primary'} onclick={() => slot('primary')}>
        {ws.primary.account ? 'Primary' : 'Primary · empty'}
      </button>
      <button class="btn" aria-pressed={ws.activeSlot === 'shadow'} disabled={!ws.shadow.account} onclick={() => slot('shadow')}>
        {ws.shadow.account ? 'Shadow' : 'Shadow · empty'}
      </button>
      {#if ws.activeSlot === 'shadow' && ws.shadow.account}
        <button class="btn" title="Delete shadow workspace" aria-label="Delete shadow workspace" onclick={deleteShadow}>🗑</button>
      {/if}
    </div>
  {/if}

  {#if data}
    <div class="money">
      {#each CURRENCIES as [key, label] (key)}
        {@const n = total(key)}
        {#if key === 'gold' || n > 0}
          <span title="{label}: {n.toLocaleString('en-US')}"><img src="/assets/currencies/{key}.png" alt={label} /><span class="num">{short(n)}</span></span>
        {/if}
      {/each}
    </div>
  {/if}

  <div class="actions">
    <label class="uisel" title="Classic: the in-game look. Simple: the plain web look.">
      <span>UI</span>
      <select class="field" value={ui.mode} onchange={(e) => setUiMode(/** @type {any} */ (e.currentTarget).value)} aria-label="UI style">
        <option value="classic">Classic</option>
        <option value="simple">Simple</option>
      </select>
    </label>
    {#if watch.handle}<span class="watch" title="Watching {watch.handle.name} for new SavedVariables">● {watch.handle.name}</span>{/if}
    <span class="live" class:on={app.live} title={app.live ? 'Live updates connected' : 'Live updates reconnecting'}></span>
    <button class="btn" disabled={refreshing} onclick={onRefresh} title="Check for updated SavedVariables data">
      <span class:spin={refreshing}>↻</span>{refreshing ? 'Checking…' : 'Refresh'}
    </button>
    <button class="btn" onclick={() => (nav.dialog = 'upload')}>⬆ Upload</button>
    <button class="btn" onclick={() => (nav.dialog = 'share')} title="Create or join a shared workspace">
      {app.shareCode ? `🔗 ${app.shareCode}` : 'Share'}
    </button>
    {#if data}
      <button class="btn" onclick={() => (nav.dialog = 'password')}>{app.auth.has_password ? '🔐 Password' : '🔓 Set password'}</button>
    {/if}
  </div>
</header>

<style>
  .uisel { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--muted); }
  .uisel select { width: auto; padding: 3px 6px; }
  .bar {
    position: sticky;
    top: 0;
    z-index: 20;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 18px;
    padding: 10px max(16px, env(safe-area-inset-right, 0px)) 10px max(16px, env(safe-area-inset-left, 0px));
    background: #070707cc;
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--line);
  }
  .brand { display: grid; line-height: 1.2; }
  .word { font: 700 17px var(--f-display); letter-spacing: 0.16em; color: var(--fg); }
  .meta { font-size: 13px; color: var(--muted); }
  .badge { margin-left: 4px; padding: 0 5px; font-size: 11px; font-weight: 600; color: var(--bg); background: var(--accent); }
  .slots { display: flex; gap: 4px; }
  .slots .btn { padding: 3px 9px; font-size: 13px; }
  .slots [aria-pressed='true'] { color: var(--bg); background: var(--accent); border-color: var(--accent); }
  .money { display: flex; gap: 14px; font-size: 14px; color: var(--muted); }
  .money span { display: inline-flex; align-items: center; gap: 4px; }
  .money img { width: 18px; height: 18px; }
  .actions { margin-left: auto; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
  @media (max-width: 700px) { .bar { position: static; } }
  .watch { font-size: 12px; color: var(--accent-hi); max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .live { width: 7px; height: 7px; border-radius: 50%; background: var(--line); transition: background 0.4s, box-shadow 0.4s; }
  .live.on { background: var(--q-fine); box-shadow: 0 0 8px var(--q-fine); }
  .spin { display: inline-block; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
