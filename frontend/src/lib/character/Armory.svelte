<script>
  import Frame from '../ui/Frame.svelte';
  import PaperDoll from './PaperDoll.svelte';
  import SkillBars from './SkillBars.svelte';
  import ChampionPoints from './ChampionPoints.svelte';
  import ResourceBar from '../ui/ResourceBar.svelte';
  import TextTip from '../tips/TextTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { app } from '../store.svelte.js';
  import { mundusIcon, setCounts } from '../gear.js';
  import { gameIcon } from '../achievements.js';

  /**
   * The in-game Armory (ZO_Armory_Keyboard): saved builds as rows with their build icon; the picked one
   * shows its gear, bars, champion stars, attributes, mundus, curse and outfit. iasync >= 1.16.0.
   * @type {{ char: any }}
   */
  let { char } = $props();

  const builds = $derived(app.builds.value?.armory?.[String(char.id)] ?? []);
  // Open the build the character is wearing, like the game keeps the last one selected.
  let picked = $state(/** @type {number | null} */ (null));
  const build = $derived(builds.find((/** @type {any} */ b) => b.index === picked) ?? builds.find((/** @type {any} */ b) => b.active) ?? builds[0] ?? null);

  // Sets are left out like in game; each item's tooltip still counts its set pieces.
  // Same item as the inventory's (its locations and price), else the copy iasync saved with the build.
  const itemsByKey = $derived(new Map((app.data.value?.items ?? []).map((/** @type {any} */ i) => [i.key, i])));
  const gear = $derived.by(() => {
    /** @type {Record<number, any>} */
    const m = {};
    for (const g of build?.gear ?? []) if (g.item) m[g.slot] = itemsByKey.get(g.item.key) ?? g.item;
    return m;
  });
  /** @type {Record<string, string>} */
  const WARN = { missing: 'missing', inaccessible: 'in a house chest' };
  const warn = $derived(Object.fromEntries((build?.gear ?? []).filter((/** @type {any} */ g) => WARN[g.state]).map((/** @type {any} */ g) => [g.slot, WARN[g.state]])));
  const sets = $derived(setCounts(gear));
  const setCount = (/** @type {any} */ item) => sets.find(([s]) => s === item?.set_name)?.[1] ?? 0;
  const attrTotal = $derived(Object.values(build?.attributes ?? {}).reduce((s, v) => s + (Number(v) || 0), 0));
  const cpTotal = $derived((build?.cp_spent ?? []).reduce((/** @type {number} */ s, /** @type {any} */ d) => s + d.spent, 0));
  const cpDescriptions = $derived(app.builds.value?.cpDescriptions ?? {});
  const mundusDescriptions = $derived(app.builds.value?.builds?.find((/** @type {any} */ b) => b.char_id === char.id)?.mundusDescriptions ?? {});
</script>

{#if app.builds.loading}
  <Frame title="ARMORY"><p class="hint none">Loading the Armory…</p></Frame>
{:else if !builds.length}
  <Frame title="ARMORY">
    <p class="hint none">No Armory builds recorded for {char.name}. Log in to it with iasync 1.16.0 or later, then upload again.</p>
  </Frame>
{:else}
  <div class="sheet">
    <div class="col">
      <Frame title="ARMORY" delay={0.05}>
        <div class="count">Current Builds: {builds.length}</div>
        <div class="list" role="listbox" aria-label="Armory builds">
          {#each builds as b (b.index)}
            <button role="option" aria-selected={b === build} class="build" onclick={() => (picked = b.index)}>
              <img src={gameIcon(b.icon) ?? '/assets/esoui/icons/icon_missing.png'} alt="" />
              <span class="name">{b.name}</span>
              {#if b.active}<span class="on" title="All of this build's gear is equipped and its attributes and mundus match">Equipped</span>{/if}
            </button>
          {/each}
        </div>
      </Frame>

      {#key build}
        <Frame title="BUILD" delay={0.1}>
          <div class="facts">
            <span class="fact" tabindex="0" use:tooltip={{ component: TextTip, props: { head: 'Mundus Stone', name: build.mundus.join(', ') || 'None', desc: build.mundus.map((/** @type {string} */ m) => mundusDescriptions[m]).filter(Boolean).join('\n\n') } }}>
              {#if build.mundus.length}<img src={mundusIcon(build.mundus[0])} alt="" />{/if}Mundus: <b>{build.mundus.join(', ') || 'None'}</b>
            </span>
            <span class="fact">Curse: <b>{build.curse_name}</b></span>
            <span class="fact">Outfit: <b>{build.outfit_name || (build.outfit_index ? `Outfit ${build.outfit_index}` : 'No Outfit')}</b></span>
            {#if build.skill_points}<span class="fact">Skill Points: <b class="num">{build.skill_points}</b></span>{/if}
            {#if cpTotal}
              <span class="fact"><img src="/assets/interface/champion_system.png" alt="" />Champion Points: <b class="num">{cpTotal.toLocaleString('en-US')}</b>
                <span class="dim">({build.cp_spent.map((/** @type {any} */ d) => `${d.name} ${d.spent}`).join(' · ')})</span></span>
            {/if}
          </div>
        </Frame>
      {/key}
    </div>

    {#key build}
      <div class="col">
        <PaperDoll {gear} {warn} race={char.race} gender={char.gender} {setCount} title="EQUIPMENT" />
      </div>
      <div class="col">
        {#if build.bars_update}
          <SkillBars skills={build.skills} names={app.builds.value?.abilityNames ?? {}} delay={0.15} />
          <ChampionPoints cp={build.cp} names={app.builds.value?.cpNames ?? {}} descriptions={cpDescriptions} delay={0.2} />
        {:else}
          <Frame title="SKILLS" delay={0.15}>
            <p class="hint none">The game only hands out Armory skill bars and champion stars at an Armory station. Visit one with iasync enabled, reload, then upload again.</p>
          </Frame>
        {/if}
        {#if attrTotal}
          <Frame title="ATTRIBUTES" delay={0.25}>
            <div class="bars">
              {#each ['magicka', 'health', 'stamina'] as kind, i (kind)}
                <ResourceBar kind={/** @type {any} */ (kind)} value={Number(build.attributes[kind]) || 0} max={Math.max(64, attrTotal)} delay={0.4 + i * 0.12} />
              {/each}
            </div>
          </Frame>
        {/if}
      </div>
    {/key}
  </div>
{/if}

<style>
  .sheet { display: grid; grid-template-columns: minmax(0, 0.8fr) minmax(0, 0.95fr) minmax(0, 1.05fr); gap: 14px; align-items: start; }
  @media (max-width: 980px) { .sheet { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); } .col:first-child { grid-column: 1 / -1; } }
  @media (max-width: 620px) { .sheet { grid-template-columns: minmax(0, 1fr); } }
  .col { display: grid; gap: 14px; min-width: 0; }
  .count { margin: -2px 0 8px; font-size: 13px; color: var(--muted); text-align: right; }
  .list { display: grid; gap: 4px; max-height: 300px; overflow-y: auto; }
  /* ZO_Armory_CollapsedBuildEntry: 48px build icon, then the name. */
  .build {
    all: unset;
    display: grid;
    grid-template-columns: 40px minmax(0, 1fr) auto;
    align-items: center;
    gap: 10px;
    padding: 5px 10px;
    cursor: pointer;
    border-left: 2px solid transparent;
    background: #ffffff05;
    transition: background 0.2s, border-color 0.2s;
  }
  .build:hover { background: #ffffff0d; }
  .build:focus-visible { outline: 1px solid var(--accent-hi); }
  .build[aria-selected='true'] { border-left-color: var(--accent); background: #ffffff10; }
  .build img { width: 40px; height: 40px; }
  .name { font-size: 15px; color: var(--fg); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .on { font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent-hi); }
  .facts { display: grid; gap: 5px; font-size: 14px; color: var(--muted); }
  .fact { display: flex; flex-wrap: wrap; align-items: center; gap: 0 5px; }
  .fact img { width: 22px; height: 22px; }
  .fact b { font-weight: 500; color: var(--fg); }
  .dim { font-size: 12px; }
  .bars { display: grid; gap: 8px; }
  .none { text-align: center; margin: 4px 0; }
  /* Classic: rows on ZO_DefaultBackdrop (ZoFontHeader2, selected text colour); labels as ZoFontHeader in normal colour with the value in selected. */
  :global(:root[data-ui='classic']) .list { max-height: 300px; gap: 0; }
  :global(:root[data-ui='classic']) .build { margin: 3px 4px; padding: 2px 10px; border: 0 solid transparent; border-image: var(--eso-backdrop) 16 fill / 16px; background: none; }
  :global(:root[data-ui='classic']) .build:hover { background: var(--eso-hover) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) .build[aria-selected='true'] { background: var(--eso-list-hl) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) .name { font: 700 19px var(--eso-font); color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .on { font: 700 15px var(--eso-font); letter-spacing: 0; color: var(--eso-highlight); }
  :global(:root[data-ui='classic']) .count { font: 700 17px var(--eso-font); color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .facts { font: 700 17px var(--eso-font); color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .fact b { font-weight: 700; color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .dim { font: 500 15px var(--eso-font-medium); }
</style>
