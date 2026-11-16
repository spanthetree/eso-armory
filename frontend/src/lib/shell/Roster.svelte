<script>
  import { app } from '../store.svelte.js';
  import { go } from '../nav.svelte.js';
  import { allianceIcon, classIcon } from '../eso.js';

  // Simple character picker for the shell; Phase 3 adds gear and stats to these cards.
  const chars = $derived(
    Object.values(app.data.value?.characters ?? {}).sort((a, b) => a.name.localeCompare(b.name)),
  );
</script>

<div class="roster">
  {#each chars as c, i (c.id)}
    <button class="card" style="--d: {0.05 + i * 0.05}s" onclick={() => go('characters', c.id)}>
      <span class="icons">
        {#if c.class}<img src={classIcon(c.class)} alt={c.class} title={c.class} />{/if}
        {#if c.alliance}<img src={allianceIcon(c.alliance)} alt={c.alliance} title={c.alliance} />{/if}
      </span>
      <span class="name">{c.name}</span>
      <span class="sub">{[c.race, c.class].filter(Boolean).join(' · ')}</span>
      <span class="sub">{c.alliance ?? ''}</span>
    </button>
  {/each}
</div>

<style>
  .roster { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr)); gap: 14px; }
  .card {
    all: unset;
    position: relative;
    display: grid;
    gap: 2px;
    padding: 16px 18px;
    cursor: pointer;
    background: var(--panel);
    border: 1px solid var(--line);
    transition: border-color 0.25s, transform 0.25s var(--ease-spring), box-shadow 0.25s;
    animation: rise 0.6s var(--ease-out) both;
    animation-delay: var(--d);
  }
  .card:hover, .card:focus-visible { border-color: var(--accent); transform: translateY(-3px); box-shadow: 0 10px 30px -12px var(--accent); outline: none; }
  .icons { position: absolute; top: 14px; right: 14px; display: flex; gap: 6px; opacity: 0.7; }
  .icons img { width: 22px; height: 22px; }
  .name { font: 600 18px var(--f-display); letter-spacing: 0.06em; color: var(--fg); padding-right: 60px; }
  .sub { font-size: 14px; color: var(--muted); }
  @keyframes rise { from { opacity: 0; transform: translateY(12px); } }
</style>
