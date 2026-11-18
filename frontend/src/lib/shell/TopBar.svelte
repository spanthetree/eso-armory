<script>
  import { ui, setUiMode } from '../uimode.svelte.js';
  import { app, refresh, switchSlot, deleteShadow, logout, toast } from '../store.svelte.js';
  import { nav, go } from '../nav.svelte.js';
  import { watch, checkFolder } from '../upload.svelte.js';

  const data = $derived(app.data.value);
  const ws = $derived(app.workspace);

  // Nag until the account has a password: without one it only opens in this browser.
  let nudgeHidden = $state(false);
  const nudge = $derived(!!data && !!app.auth.account_name && !app.auth.has_password && !nudgeHidden && nav.dialog !== 'password');

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
    <span class="word">ESO<img class="logo" src="/assets/favicon.png" alt="" />ARMORY</span>
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
        {ws.shadow.account ? 'Alt' : 'Alt · empty'}
      </button>
      {#if ws.activeSlot === 'shadow' && ws.shadow.account}
        <button class="btn" title="Remove alt account" aria-label="Remove alt account" onclick={deleteShadow}>🗑</button>
      {/if}
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
      {#if app.auth.account_name}
      <span class="pwd">
        <button class="btn" class:ring={nudge} onclick={() => (nav.dialog = 'password')}>{app.auth.has_password ? '🔐 Password' : '🔓 Set password'}</button>
        {#if nudge}
          <span class="nudge ring" role="status">
            <button class="msg" onclick={() => (nav.dialog = 'password')}>
              Set a password for <b>{app.auth.account_name}</b> to open your armory on another device.
            </button>
            <button class="x" aria-label="Hide until reload" title="Hide until reload" onclick={() => (nudgeHidden = true)}>×</button>
          </span>
        {/if}
      </span>
      {/if}
      <button class="btn" onclick={logout} title="Forget this browser">Log out</button>
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
  .word { display: flex; align-items: center; gap: 6px; font: 700 17px var(--f-display); letter-spacing: 0.16em; color: var(--fg); }
  /* The favicon (the in-game Armory icon, 64px source) between the words. */
  .logo { width: 40px; height: 40px; margin: -12px -5px; } /* tall icon with side padding: bigger, without growing the bar */
  .meta { font-size: 13px; color: var(--muted); }
  .badge { margin-left: 4px; padding: 0 5px; font-size: 11px; font-weight: 600; color: var(--fg); text-shadow: 0 0 2px #000, 0 1px 1px #000; background: var(--accent); }
  .slots { display: flex; gap: 4px; }
  .slots .btn { padding: 3px 9px; font-size: 13px; }
  .slots [aria-pressed='true'] { color: var(--bg); background: var(--accent); border-color: var(--accent); }
  .actions { margin-left: auto; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
  @media (max-width: 700px) { .bar { position: static; } }
  .watch { font-size: 12px; color: var(--accent-hi); max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .live { width: 7px; height: 7px; border-radius: 50%; background: var(--line); transition: background 0.4s, box-shadow 0.4s; }
  .live.on { background: var(--q-fine); box-shadow: 0 0 8px var(--q-fine); }
  .spin { display: inline-block; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .pwd { position: relative; }
  .nudge { position: absolute; top: calc(100% + 8px); right: 0; z-index: 30; display: flex; align-items: flex-start; gap: 6px; width: 240px;
    padding: 8px 10px; font-size: 13px; color: var(--fg); background: #0b0b0bf2; border: 1px solid var(--accent); box-shadow: 0 6px 18px #000a; }
  .nudge::before { content: ''; position: absolute; top: -6px; right: 22px; width: 10px; height: 10px; background: inherit;
    border-left: 1px solid var(--accent); border-top: 1px solid var(--accent); transform: rotate(45deg); }
  .nudge button { padding: 0; font: inherit; color: inherit; text-align: left; background: none; border: 0; cursor: pointer; }
  .nudge .x { font-size: 16px; line-height: 1; color: var(--muted); }
  .nudge .x:hover { color: var(--fg); }
  /* Ring: a short bell wiggle at the start of every 30 s cycle. */
  .ring { animation: ring 30s ease-in-out infinite; transform-origin: 50% 0; }
  @keyframes ring {
    0%, 4%, 100% { transform: rotate(0); }
    0.5% { transform: rotate(-6deg); } 1% { transform: rotate(5deg); } 1.5% { transform: rotate(-4deg); }
    2% { transform: rotate(3deg); } 2.5% { transform: rotate(-2deg); } 3% { transform: rotate(1deg); }
  }
  @media (prefers-reduced-motion: reduce) { .ring { animation: none; } }

  /* Classic: a dark band like the game's screen edge, with the title divider under it. */
  :global(:root[data-ui='classic']) .bar { background: linear-gradient(#000, #000c); backdrop-filter: none; border-bottom: 0; }
  :global(:root[data-ui='classic']) .bar::after { content: ''; position: absolute; left: 0; right: 0; bottom: -3px; height: 6px; display: block;
    background: var(--eso-divider-l) left / 56px 6px no-repeat, var(--eso-divider-r) right / 56px 6px no-repeat, var(--eso-divider-m) center / calc(100% - 112px) 6px no-repeat; }
  :global(:root[data-ui='classic']) .word { font: 700 22px var(--eso-font); letter-spacing: 0; text-transform: uppercase; }
  :global(:root[data-ui='classic']) .meta, :global(:root[data-ui='classic']) .uisel { font: 500 16px var(--eso-font-medium); color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .badge { font: 700 13px var(--eso-font); color: var(--eso-selected); background: var(--eso-normal); }
  :global(:root[data-ui='classic']) .slots .btn { font-size: 16px; padding: 0 10px; }
  :global(:root[data-ui='classic']) .slots [aria-pressed='true'] { color: var(--eso-selected); background: none; }
  :global(:root[data-ui='classic']) .nudge { font: 500 16px var(--eso-font-medium); color: var(--eso-normal); background: #000e; }
</style>
