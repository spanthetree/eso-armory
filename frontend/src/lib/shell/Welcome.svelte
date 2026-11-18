<script>
  import Frame from '../ui/Frame.svelte';
  import { app, login } from '../store.svelte.js';
  import { nav } from '../nav.svelte.js';

  let name = $state('');
  let password = $state('');
  let busy = $state(false);
  let error = $state('');

  async function submit() {
    if (busy) return;
    if (!name.trim() || !password) return (error = 'Account name and password are required.');
    busy = true;
    error = '';
    try {
      await login(name, password);
      password = '';
    } catch (e) {
      error = /** @type {Error} */ (e).message;
    } finally {
      busy = false;
    }
  }
</script>

<div class="welcome">
  <Frame title="LOAD YOUR ESO DATA" delay={0.05}>
    <ol>
      <li>Install the <strong>iasync</strong> addon (required). <strong>Wizards Wardrobe</strong> is optional and adds builds.</li>
      <li>Find your SavedVariables files in <code>Documents\Elder Scrolls Online\live\SavedVariables\</code></li>
      <li>Upload <code>iasync.lua</code>, and <code>WizardsWardrobe.lua</code> if you have it.</li>
    </ol>
    <button class="btn primary" onclick={() => (nav.dialog = 'upload')}>Select files…</button>
    {#if app.data.error}<p class="hint">Server: {app.data.error}</p>{/if}
  </Frame>

  <Frame title="LOG IN TO AN EXISTING ACCOUNT" delay={0.2}>
    <p class="hint">Open your data on another device with your ESO account name and password.</p>
    <form onsubmit={(e) => { e.preventDefault(); submit(); }}>
      <input class="field" bind:value={name} placeholder="accountname (case sensitive)" autocomplete="username" aria-label="Account name" />
      <input class="field" type="password" bind:value={password} placeholder="Password" autocomplete="current-password" aria-label="Password" />
      <button class="btn primary" disabled={busy}>{busy ? 'Logging in…' : 'Log in'}</button>
    </form>
    {#if error}<p class="err" role="alert">{error}</p>{/if}
  </Frame>
</div>

<style>
  .welcome { max-width: 520px; margin: 48px auto 0; display: grid; gap: 20px; }
  ol { margin: 0 0 18px; padding-left: 22px; display: grid; gap: 10px; color: var(--muted); }
  ol li::marker { font-family: var(--f-display); color: var(--accent); }
  strong { color: var(--fg); font-weight: 600; }
  code { word-break: break-all; }
  form { display: grid; gap: 10px; margin-top: 14px; }
  p { margin: 12px 0 0; }
  .hint:first-child { margin-top: 0; }
</style>
