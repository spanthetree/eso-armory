<script>
  import Frame from '../ui/Frame.svelte';
  import { gameIcon } from '../achievements.js';

  /** Scribing (iasync 1.11.0): grimoires and the scripts each can take, per character. @type {{ char: any }} */
  let { char } = $props();

  const grimoires = $derived(char.scribing?.grimoires ?? []);
  const scripts = $derived(char.scribing?.scripts ?? {});
  const unlockedScripts = $derived(Object.values(scripts).filter((/** @type {any} */ s) => s.unlocked).length);
  let picked = $state(0);
  const g = $derived(grimoires[Math.min(picked, grimoires.length - 1)]);
  // The game's slot names for primary/secondary/tertiary scripts.
  const SLOTS = [['primary', 'Focus Scripts'], ['secondary', 'Signature Scripts'], ['tertiary', 'Affix Scripts']];
</script>

{#if !grimoires.length}
  <Frame title="SCRIBING"><p class="hint none">No scribing data for {char.name} yet: it needs iasync 1.11.0 and a login on this character.</p></Frame>
{:else}
  <div class="scribe">
    <Frame title="GRIMOIRES">
      <div class="sum"><span>Unlocked</span><span class="num">{grimoires.filter((/** @type {any} */ x) => x.unlocked).length} / {grimoires.length} · scripts {unlockedScripts} / {Object.keys(scripts).length}</span></div>
      <div class="grid" role="listbox" aria-label="Grimoires">
        {#each grimoires as x, i (x.id)}
          <button class="gr" class:locked={!x.unlocked} role="option" aria-selected={i === picked} onclick={() => (picked = i)} title="{x.name}{x.unlocked ? '' : ' (locked)'}">
            {#if gameIcon(x.icon)}<img src={gameIcon(x.icon)} alt="" />{/if}
            <span>{x.name}</span>
            {#if x.scribed}<small>Scribed</small>{/if}
          </button>
        {/each}
      </div>
    </Frame>

    {#if g}
      <Frame title={g.name.toUpperCase()}>
        <div class="slots">
          {#each SLOTS as [slot, label] (slot)}
            {@const ids = g.scripts?.[slot] ?? []}
            <section>
              <h6>{label} <span class="num dim">{ids.filter((/** @type {number} */ id) => scripts[id]?.unlocked).length}/{ids.length}</span></h6>
              <ul>
                {#each ids as id (id)}<li class:off={!scripts[id]?.unlocked}>{scripts[id]?.name || `Script ${id}`}</li>{/each}
              </ul>
            </section>
          {/each}
        </div>
      </Frame>
    {/if}
  </div>
{/if}

<style>
  .scribe { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr); gap: 14px; align-items: start; }
  @media (max-width: 900px) { .scribe { grid-template-columns: minmax(0, 1fr); } }
  .sum { display: flex; justify-content: space-between; font-size: 14px; color: var(--muted); margin-bottom: 8px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 6px; }
  .gr { all: unset; box-sizing: border-box; display: grid; justify-items: center; gap: 3px; padding: 8px 4px; text-align: center; font-size: 13px; cursor: pointer; border: 1px solid #ffffff17; }
  .gr img { width: 44px; height: 44px; }
  .gr small { font-size: 11px; color: var(--accent-hi); }
  .gr[aria-selected='true'] { border-color: var(--accent); background: #ffffff0d; }
  .gr:hover, .gr:focus-visible { border-color: var(--accent-hi); }
  .gr.locked { color: var(--muted); }
  .gr.locked img { filter: grayscale(1) brightness(0.5); }
  .slots { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
  @media (max-width: 700px) { .slots { grid-template-columns: minmax(0, 1fr); } }
  h6 { display: flex; justify-content: space-between; margin: 0 0 6px; font-size: 14px; letter-spacing: 0.06em; color: var(--fg); text-transform: uppercase; }
  ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 2px; font-size: 14px; }
  li.off { color: var(--muted); opacity: 0.6; }
  .dim { color: var(--muted); }
  .none { text-align: center; margin: 4px 0; }
  :global(:root[data-ui='classic']) .gr { border: 0; background: var(--eso-slot-bg) 0 0 / 100% 100%; font: 700 16px var(--eso-font); color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .gr[aria-selected='true'], :global(:root[data-ui='classic']) .gr:hover { background: var(--eso-slot-hl) 0 0 / 100% 100%, var(--eso-slot-bg) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) .gr.locked { color: var(--eso-disabled); }
  :global(:root[data-ui='classic']) h6 { font: 700 18px var(--eso-font); color: var(--eso-selected); letter-spacing: 0; }
  :global(:root[data-ui='classic']) ul { font: 500 16px var(--eso-font-medium); color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .dim, :global(:root[data-ui='classic']) .sum { color: var(--eso-normal); }
</style>
