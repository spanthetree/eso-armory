<script>
  import Modal from '../ui/Modal.svelte';
  import { app, setPassword } from '../store.svelte.js';
  import { nav } from '../nav.svelte.js';

  let pwd = $state('');
  let confirm = $state('');
  let busy = $state(false);
  let status = $state(/** @type {{ ok: boolean, msg: string } | null} */ (null));
  const hasPassword = $derived(!!app.auth.has_password);

  $effect(() => {
    if (nav.dialog === 'password') {
      pwd = confirm = '';
      status = null;
    }
  });

  async function save() {
    if (busy) return;
    if (pwd.length < 8) return (status = { ok: false, msg: 'Password must be at least 8 characters.' });
    if (pwd !== confirm) return (status = { ok: false, msg: 'Passwords do not match.' });
    busy = true;
    try {
      await setPassword(pwd);
      pwd = confirm = '';
      status = { ok: true, msg: 'Password saved.' };
    } catch (e) {
      status = { ok: false, msg: /** @type {Error} */ (e).message };
    } finally {
      busy = false;
    }
  }
</script>

<Modal open={nav.dialog === 'password'} title={hasPassword ? 'Change Password' : 'Set Account Password'} onclose={() => (nav.dialog = '')}>
  <p class="hint">Protect your account so you can log in from any device with your ESO account name and this password.</p>
  <form onsubmit={(e) => { e.preventDefault(); save(); }}>
    <!-- Read-only so password managers save the ESO account name with the password. -->
    <input class="field" type="text" value={app.auth.account_name || ''} readonly autocomplete="username" aria-label="ESO account name" />
    <input class="field" type="password" bind:value={pwd} placeholder="New password (at least 8 characters)" autocomplete="new-password" aria-label="New password" />
    <input class="field" type="password" bind:value={confirm} placeholder="Confirm password" autocomplete="new-password" aria-label="Confirm password" />
    <button class="btn primary" disabled={busy}>{busy ? 'Saving…' : hasPassword ? 'Change password' : 'Save password'}</button>
  </form>
  {#if status}<p class={status.ok ? 'ok' : 'err'} role="status">{status.msg}</p>{/if}
</Modal>

<style>
  form { display: grid; gap: 10px; margin-top: 16px; }
  p { margin: 0; }
  [role='status'] { margin-top: 12px; }
</style>
