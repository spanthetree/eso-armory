<script>
  import { setAllianceTint } from './lib/eso.js';

  // Phase 1 preview page; replaced by the app shell in Phase 2.
  let al = $state(/** @type {'ad' | 'dc' | 'ep'} */ ('ep'));
  $effect(() => setAllianceTint(al));

  const qualities = ['trash', 'normal', 'fine', 'superior', 'epic', 'legendary', 'mythic'];
</script>

<main>
  <h1>Seryn Vel-Ashar</h1>
  <p class="muted">Design tokens preview. Alliance: {al.toUpperCase()}</p>
  <div class="row">
    {#each ['ad', 'dc', 'ep'] as k (k)}
      <button aria-pressed={al === k} onclick={() => (al = /** @type {any} */ (k))}>{k.toUpperCase()}</button>
    {/each}
  </div>
  <div class="row">
    {#each qualities as q (q)}<span style="color: var(--q-{q})">{q}</span>{/each}
  </div>
</main>

<style>
  main { max-width: 760px; margin: 0 auto; padding: 48px 16px; display: grid; gap: 16px; }
  h1 { color: var(--accent-hi); font-size: 34px; transition: color var(--tint-time); }
  .muted { color: var(--muted); margin: 0; }
  .row { display: flex; gap: 12px; flex-wrap: wrap; }
  button { font: 600 14px var(--f-display); letter-spacing: 0.12em; color: var(--muted); background: #0006; border: 1px solid var(--line); padding: 6px 14px; cursor: pointer; }
  button[aria-pressed='true'] { color: var(--bg); background: var(--accent); }
</style>
