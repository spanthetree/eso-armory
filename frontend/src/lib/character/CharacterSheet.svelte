<script>
  import Frame from '../ui/Frame.svelte';
  import PaperDoll from './PaperDoll.svelte';
  import ResourceBar from '../ui/ResourceBar.svelte';
  import SkillBars from './SkillBars.svelte';
  import ChampionPoints from './ChampionPoints.svelte';
  import { app } from '../store.svelte.js';
  import { equipped, mundusIcon, setCounts } from '../gear.js';

  /** @type {{ char: any }} */
  let { char } = $props();

  const gear = $derived(equipped(app.data.value?.items, char.id));
  // Latest scanned build with gear, like the classic UI.
  const build = $derived(app.builds.value?.builds?.find((/** @type {any} */ b) => b.char_id === char.id && b.gear?.length) ?? null);
  const names = $derived(app.builds.value?.abilityNames ?? {});
  const cpNames = $derived(app.builds.value?.cpNames ?? {});

  const sets = $derived(setCounts(gear));

  // Bars scale to the 64 attribute points a max-level character has.
  const attrTotal = $derived(Object.values(build?.attributes ?? {}).reduce((s, v) => s + (Number(v) || 0), 0));
  const space = $derived(char.space_max ? char.space_used / char.space_max : 0);

  /** @param {any} item */
  const setCount = (item) => (item?.set_name ? sets.find(([s]) => s === item.set_name)?.[1] ?? 0 : 0);
</script>


<div class="sheet">
  <div class="col">
    <PaperDoll {gear} race={char.race} gender={char.gender} {setCount} />
  </div>

  <div class="col">
    <Frame title="CHARACTER" delay={0.15}>
      <div class="money">
        {#each [['gold', 'Gold'], ['ap', 'Alliance Points'], ['tv', 'Tel Var'], ['wv', 'Writs']] as [k, label] (k)}
          {#if k === 'gold' || char[k] > 0}
            <span title={label}><img src="/assets/currencies/{k}.png" alt={label} /><b class="num">{(char[k] ?? 0).toLocaleString('en-US')}</b></span>
          {/if}
        {/each}
      </div>
      <div class="space">
        <div class="row"><span>Bag space</span><span class="num">{char.space_used} / {char.space_max}</span></div>
        <div class="track"><i style="width: {space * 100}%; background: {space > 0.9 ? '#ef4444' : space > 0.75 ? '#f59e0b' : 'var(--q-fine)'}"></i></div>
      </div>
      {#if build?.mundus?.length || build?.cp_earned}
        <div class="facts">
          {#if build?.mundus?.length}
            <span class="fact"><img src={mundusIcon(build.mundus[0])} alt="" />{build.mundus.join(', ')}</span>
          {/if}
          {#if build?.cp_earned}
            <span class="fact"><img src="/assets/interface/champion_system.png" alt="" /><b class="num">{build.cp_earned.toLocaleString('en-US')}</b> CP</span>
          {/if}
        </div>
      {/if}
    </Frame>

    {#if attrTotal}
      <Frame title="ATTRIBUTES" delay={0.25}>
        <div class="bars">
          {#each ['magicka', 'health', 'stamina'] as kind, i (kind)}
            {@const pts = Number(build.attributes[kind]) || 0}
            {@const pool = Number(build.pools?.[kind]) || 0}
            <ResourceBar kind={/** @type {any} */ (kind)} value={pts} max={Math.max(64, attrTotal)} shown={pool || null} note={pool ? `${pts} pts` : ''} delay={0.45 + i * 0.12} />
          {/each}
        </div>
      </Frame>
    {/if}

    {#if sets.length}
      <Frame title="SETS" delay={0.35}>
        <div class="sets">
          {#each sets as [name, n] (name)}
            <div class="set"><span>{name}</span><span class="num">{n}</span></div>
          {/each}
        </div>
      </Frame>
    {/if}
  </div>

  <div class="col">
    <SkillBars skills={build?.skills} {names} />
    <ChampionPoints cp={build?.cp} names={cpNames} />

    {#if !build}
      <Frame title="BUILD" delay={0.25}>
        <p class="hint none">No build scanned for this character yet. Log in to it with iasync enabled, then upload again.</p>
      </Frame>
    {/if}
  </div>
</div>

<style>
  .sheet { display: grid; grid-template-columns: minmax(0, 0.95fr) minmax(0, 1fr) minmax(0, 1.05fr); gap: 14px; align-items: start; }
  @media (max-width: 980px) { .sheet { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); } .col:nth-child(2) { grid-column: 1 / -1; grid-row: 2; } }
  @media (max-width: 620px) { .sheet { grid-template-columns: minmax(0, 1fr); } .col:nth-child(2) { grid-row: auto; } }
  .col { display: grid; gap: 14px; min-width: 0; }

  .money { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 16px; font-size: 15px; }
  .money span, .fact { display: inline-flex; align-items: center; gap: 5px; }
  .money img { width: 20px; height: 20px; }
  b { font-weight: 500; }
  .space { margin-top: 8px; }
  .row { display: flex; justify-content: space-between; font-size: 14px; color: var(--muted); }
  .track { height: 6px; margin-top: 4px; background: #000; border: 1px solid var(--line); overflow: hidden; }
  .track i { display: block; height: 100%; transition: width 0.6s var(--ease-out); }
  .facts { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 18px; margin-top: 8px; font-size: 15px; }
  .fact img { width: 24px; height: 24px; }

  .bars { display: grid; gap: 8px; }

  .sets { display: grid; gap: 3px; }
  .set { display: flex; justify-content: space-between; gap: 10px; padding: 3px 10px; border-left: 2px solid var(--accent); background: #ffffff06; font-size: 14px; }
  .set .num { color: var(--muted); }
  .none { text-align: center; margin: 4px 0; }
</style>
