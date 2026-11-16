<script>
  import Frame from '../ui/Frame.svelte';
  import PaperDoll from './PaperDoll.svelte';
  import SkillBars from './SkillBars.svelte';
  import ChampionPoints from './ChampionPoints.svelte';
  import { app } from '../store.svelte.js';
  import { savedGearItem, setCounts } from '../gear.js';

  /** Wizards Wardrobe saved builds: pick one on the left, see it in the equipped-panel layout. @type {{ char: any }} */
  let { char } = $props();

  const itemsById = $derived(new Map((app.data.value?.items ?? []).filter((i) => i.item_id).map((i) => [i.item_id, i])));
  /** Builds with something worth showing, like the classic charWWBuilds. */
  const builds = $derived(
    (app.wwBuilds.value?.builds?.[String(char.id)] ?? []).filter(
      (/** @type {any} */ b) =>
        b.gear?.length || b.food || Object.values(b.cp ?? {}).some((v) => Number(v) > 0) ||
        ['primary', 'backup', 'werewolf'].some((bar) => Object.keys(b.skills?.[bar] ?? {}).length),
    ),
  );
  let picked = $state(0);
  const build = $derived(builds[Math.min(picked, builds.length - 1)] ?? null);

  const gear = $derived.by(() => {
    /** @type {Record<number, any>} */
    const m = {};
    for (const g of build?.gear ?? []) m[g.slot] = savedGearItem(g, itemsById.get(g.item_id));
    return m;
  });
  const sets = $derived(setCounts(gear));
  const setCount = (/** @type {any} */ item) => sets.find(([s]) => s === item?.set_name)?.[1] ?? 0;
  const food = $derived(build?.food ? build.food.link_name || itemsById.get(build.food.item_id)?.name || `Item #${build.food.item_id}` : '');
</script>

{#if app.wwBuilds.loading}
  <Frame title="WIZARDS WARDROBE"><p class="hint none">Loading saved builds…</p></Frame>
{:else if !builds.length}
  <Frame title="WIZARDS WARDROBE">
    <p class="hint none">No Wizards Wardrobe builds saved for {char.name}. Upload <code>WizardsWardrobe.lua</code> to see them here.</p>
  </Frame>
{:else}
  <div class="sheet">
    <div class="col">
      <Frame title="SAVED BUILDS" delay={0.05}>
        <div class="list" role="listbox" aria-label="Saved builds">
          {#each builds as b, i (`${b.zone}-${b.page}-${b.setup}`)}
            <button role="option" aria-selected={b === build} class="build" onclick={() => (picked = i)}>
              <span class="name">{b.name || `Setup ${b.setup}`}</span>
              <span class="where">{b.zone} · {b.page_name}</span>
            </button>
          {/each}
        </div>
      </Frame>
    </div>

    {#key build}
      <div class="col">
        <PaperDoll {gear} race={char.race} gender={char.gender} {setCount} />
      </div>
      <div class="col">
        <SkillBars skills={build.skills} names={app.builds.value?.abilityNames ?? {}} delay={0.15} />
        <ChampionPoints cp={build.cp} names={app.builds.value?.cpNames ?? {}} delay={0.25} />
        {#if sets.length || food}
          <Frame title="SETS & FOOD" delay={0.3}>
            <div class="sets">
              {#each sets as [name, n] (name)}<div class="set"><span>{name}</span><span class="num">{n}</span></div>{/each}
              {#if food}<div class="set food"><span>{food}</span><span>Food</span></div>{/if}
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
  .list { display: grid; gap: 3px; max-height: 560px; overflow-y: auto; }
  .build {
    all: unset;
    display: grid;
    gap: 1px;
    padding: 6px 10px;
    cursor: pointer;
    border-left: 2px solid transparent;
    background: #ffffff05;
    transition: background 0.2s, border-color 0.2s;
  }
  .build:hover { background: #ffffff0d; }
  .build:focus-visible { outline: 1px solid var(--accent-hi); }
  .build[aria-selected='true'] { border-left-color: var(--accent); background: #ffffff10; }
  .name { font-size: 15px; color: var(--fg); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .where { font-size: 12px; color: var(--muted); }
  .sets { display: grid; gap: 3px; }
  .set { display: flex; justify-content: space-between; gap: 10px; padding: 3px 10px; border-left: 2px solid var(--accent); background: #ffffff06; font-size: 14px; }
  .set .num, .food span:last-child { color: var(--muted); }
  .none { text-align: center; margin: 4px 0; }
</style>
