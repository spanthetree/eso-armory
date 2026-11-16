<script>
  import Modal from '../ui/Modal.svelte';
  import { nav } from '../nav.svelte.js';
  // shortcut: placeholder until Phase 2c ports file upload and folder watching; uploads go through the classic UI.
</script>

<Modal open={nav.dialog === 'upload'} title="Upload ESO Data" onclose={() => (nav.dialog = '')}>
  <p class="hint">Uploading isn't in the new interface yet. Use the classic interface for now: it shares the same workspace, so this page picks up the data.</p>
  <a class="btn primary" href="/">Open classic interface</a>
</Modal>

<style>
  p { margin: 0 0 16px; }
  a { text-decoration: none; }
</style>
