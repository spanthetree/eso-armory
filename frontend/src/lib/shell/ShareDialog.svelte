<script>
  import Modal from '../ui/Modal.svelte';
  import { app, createShare, joinShare, leaveShare, shareLink, toast } from '../store.svelte.js';
  import { nav } from '../nav.svelte.js';

  let joinCode = $state('');
  let busy = $state(false);
  let status = $state(/** @type {{ ok: boolean, msg: string } | null} */ (null));

  $effect(() => {
    if (nav.dialog === 'share') {
      joinCode = app.shareCode;
      status = null;
    }
  });

  /** @param {() => Promise<string>} fn @param {string} okMsg */
  async function run(fn, okMsg) {
    if (busy) return;
    busy = true;
    status = null;
    try {
      const code = await fn();
      status = code ? { ok: true, msg: okMsg } : { ok: false, msg: 'Enter an 8-character code, like ABCD-EFGH.' };
    } catch (e) {
      status = { ok: false, msg: /** @type {Error} */ (e).message };
    } finally {
      busy = false;
    }
  }

  /** @param {string} text @param {string} what */
  async function copy(text, what) {
    try {
      await navigator.clipboard.writeText(text);
      toast(`${what} copied`);
    } catch {
      toast('Copy failed');
    }
  }
</script>

<Modal open={nav.dialog === 'share'} title="Share Workspace" onclose={() => (nav.dialog = '')}>
  <p class="hint">Pair another browser or device with this uploaded data. Anyone with the code can see the same workspace.</p>

  {#if app.shareCode}
    <section class="box">
      <div class="label">CURRENT CODE</div>
      <div class="row">
        <code class="code">{app.shareCode}</code>
        <button class="btn" onclick={() => copy(app.shareCode, 'Share code')}>Copy code</button>
      </div>
      <p class="hint link">{shareLink()}</p>
      <div class="row">
        <button class="btn" onclick={() => copy(shareLink(), 'Share link')}>Copy share link</button>
        <button class="btn" onclick={() => { leaveShare(); status = null; }}>Unlink this browser</button>
      </div>
    </section>
  {/if}

  <section>
    <label class="label" for="share-join">PAIR A CODE</label>
    <form class="row" onsubmit={(e) => { e.preventDefault(); run(() => joinShare(joinCode), 'Joined shared workspace.'); }}>
      <input id="share-join" class="field" bind:value={joinCode} placeholder="ABCD-EFGH" autocomplete="off" spellcheck="false" />
      <button class="btn" disabled={busy}>Join</button>
    </form>
  </section>

  <button class="btn primary" disabled={busy} onclick={() => run(createShare, 'Share code created.')}>
    {busy ? 'Working…' : 'Create share code'}
  </button>

  {#if status}<p class={status.ok ? 'ok' : 'err'} role="status">{status.msg}</p>{/if}
</Modal>

<style>
  section { margin: 16px 0; }
  .box { padding: 14px; border: 1px solid var(--line); background: #00000066; }
  .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .row .field { flex: 1; min-width: 0; }
  .code { flex: 1; font-size: 16px; letter-spacing: 0.1em; padding: 5px 8px; }
  .link { word-break: break-all; margin: 8px 0; font-size: 12px; }
  p { margin: 0; }
  [role='status'] { margin-top: 12px; }
</style>
