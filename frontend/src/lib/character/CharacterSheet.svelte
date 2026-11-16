<script>
  import Frame from '../ui/Frame.svelte';
  import Slot from '../ui/Slot.svelte';
  import ResourceBar from '../ui/ResourceBar.svelte';
  import ItemTip from '../tips/ItemTip.svelte';
  import SkillSlot from './SkillSlot.svelte';
  import { app } from '../store.svelte.js';
  import { SLOT_LABELS, APPAREL, JEWELRY, FRONT_BAR, BACK_BAR, slotIcon, equipped, mundusIcon } from '../gear.js';

  /** @type {{ char: any }} */
  let { char } = $props();

  const gear = $derived(equipped(app.data.value?.items, char.id));
  // Latest scanned build with gear, like the classic UI.
  const build = $derived(app.builds.value?.builds?.find((/** @type {any} */ b) => b.char_id === char.id && b.gear?.length) ?? null);
  const names = $derived(app.builds.value?.abilityNames ?? {});
  const cpNames = $derived(app.builds.value?.cpNames ?? {});

  /** Equipped pieces per set, most first. */
  const sets = $derived.by(() => {
    /** @type {Record<string, number>} */
    const n = {};
    for (const item of Object.values(gear)) if (item.set_name) n[item.set_name] = (n[item.set_name] ?? 0) + 1;
    return Object.entries(n).sort((a, b) => b[1] - a[1]);
  });

  const BARS = /** @type {const} */ ([
    ['primary', 'Front bar'],
    ['backup', 'Back bar'],
    ['werewolf', 'Werewolf'],
  ]);
  const SKILL_SLOTS = [3, 4, 5, 6, 7, 8];
  const CP = [
    { label: 'Craft', color: '#A5DB52', icon: '/assets/interface/champion_stamina.png', slots: ['1', '2', '3', '4'] },
    { label: 'Warfare', color: '#5ABAE7', icon: '/assets/interface/champion_magicka.png', slots: ['5', '6', '7', '8'] },
    { label: 'Fitness', color: '#E76931', icon: '/assets/interface/champion_health.png', slots: ['9', '10', '11', '12'] },
  ];

  // Bars scale to the 64 attribute points a max-level character has.
  const attrTotal = $derived(Object.values(build?.attributes ?? {}).reduce((s, v) => s + (Number(v) || 0), 0));
  const hasSkills = $derived(BARS.some(([bar]) => Object.keys(build?.skills?.[bar] ?? {}).length));
  const hasCP = $derived(Object.values(build?.cp ?? {}).some((v) => Number(v) > 0));
  const space = $derived(char.space_max ? char.space_used / char.space_max : 0);

  /** @param {any} item */
  const setCount = (item) => (item?.set_name ? sets.find(([s]) => s === item.set_name)?.[1] ?? 0 : 0);
</script>

{#snippet slots(/** @type {number[]} */ list, /** @type {number} */ start)}
  {#each list as s, i (s)}
    {@const item = gear[s]}
    <Slot
      label={item ? `${SLOT_LABELS[s]}: ${item.name}` : `${SLOT_LABELS[s]}: empty`}
      icon={item ? slotIcon(s, item) : ''}
      color={item?.quality_color}
      delay={start + i * 0.04}
      tip={item ? { component: ItemTip, props: { item, slotLabel: SLOT_LABELS[s], equippedFromSet: setCount(item) } } : null} />
  {/each}
{/snippet}

<div class="sheet">
  <div class="col">
    <Frame title="APPAREL" delay={0.05}>
      <div class="grid g2">{@render slots(APPAREL, 0.25)}</div>
    </Frame>
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
            <ResourceBar kind={/** @type {any} */ (kind)} value={Number(build.attributes[kind]) || 0} max={Math.max(64, attrTotal)} delay={0.45 + i * 0.12} />
          {/each}
        </div>
      </Frame>
    {/if}

    {#if hasSkills}
      <Frame title="SKILLS" delay={0.35}>
        <div class="skills">
          {#each BARS as [bar, label] (bar)}
            {#if Object.keys(build.skills?.[bar] ?? {}).length}
              <div class="skillrow">
                <span class="barname">{label}</span>
                <div class="skillslots">
                  {#each SKILL_SLOTS as s, i (s)}
                    {@const id = build.skills[bar][s]}
                    <SkillSlot name={id ? names[String(id)] || `#${id}` : ''} ultimate={s === 8} delay={0.6 + i * 0.04} />
                  {/each}
                </div>
              </div>
            {/if}
          {/each}
        </div>
      </Frame>
    {/if}

    {#if hasCP}
      <Frame title="CHAMPION POINTS" delay={0.45}>
        <div class="cp">
          {#each CP as g (g.label)}
            <div>
              <div class="cphead" style="color: {g.color}"><img src={g.icon} alt="" />{g.label}</div>
              {#each g.slots as s (s)}
                {#if build.cp?.[s]}<div class="cpname">{cpNames[String(build.cp[s])] || `#${build.cp[s]}`}</div>{/if}
              {/each}
            </div>
          {/each}
        </div>
      </Frame>
    {/if}

    {#if !build}
      <Frame title="BUILD" delay={0.25}>
        <p class="hint none">No build scanned for this character yet. Log in to it with iasync enabled, then upload again.</p>
      </Frame>
    {/if}
  </div>

  <div class="col">
    <Frame title="JEWELRY" delay={0.1}>
      <div class="grid g3">{@render slots(JEWELRY, 0.3)}</div>
    </Frame>
    <Frame title="WEAPONS" delay={0.2}>
      <div class="weapons">
        <div><div class="sublabel">Front</div><div class="grid g2">{@render slots(FRONT_BAR, 0.4)}</div></div>
        <div><div class="sublabel">Back</div><div class="grid g2">{@render slots(BACK_BAR, 0.48)}</div></div>
      </div>
    </Frame>
    {#if sets.length}
      <Frame title="SETS" delay={0.3}>
        <div class="sets">
          {#each sets as [name, n] (name)}
            <div class="set"><span>{name}</span><span class="num">{n}</span></div>
          {/each}
        </div>
      </Frame>
    {/if}
  </div>
</div>

<style>
  .sheet { display: grid; grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.25fr) minmax(0, 0.8fr); gap: 16px; align-items: start; }
  @media (max-width: 980px) { .sheet { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); } .col:nth-child(2) { grid-column: 1 / -1; grid-row: 2; } }
  @media (max-width: 620px) { .sheet { grid-template-columns: minmax(0, 1fr); } .col:nth-child(2) { grid-row: auto; } }
  .col { display: grid; gap: 16px; min-width: 0; }

  /* Slots stay at or below the 64px source icons so they render sharp. */
  .grid { display: grid; gap: 8px; justify-content: center; }
  .g2 { grid-template-columns: repeat(2, 58px); }
  .g3 { grid-template-columns: repeat(3, 58px); }
  .grid :global(.slot img) { width: 46px; height: 46px; }
  .weapons { display: flex; justify-content: center; gap: 18px; flex-wrap: wrap; }
  .sublabel { font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); text-align: center; margin-bottom: 6px; }

  .money { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 16px; font-size: 15px; }
  .money span, .fact { display: inline-flex; align-items: center; gap: 5px; }
  .money img { width: 20px; height: 20px; }
  b { font-weight: 500; }
  .space { margin-top: 12px; }
  .row { display: flex; justify-content: space-between; font-size: 14px; color: var(--muted); }
  .track { height: 6px; margin-top: 4px; background: #000; border: 1px solid var(--line); overflow: hidden; }
  .track i { display: block; height: 100%; transition: width 0.6s var(--ease-out); }
  .facts { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 18px; margin-top: 12px; font-size: 15px; }
  .fact img { width: 24px; height: 24px; }

  .bars { display: grid; gap: 12px; }
  .skills { display: grid; gap: 10px; }
  .skillrow { display: grid; grid-template-columns: 74px 1fr; align-items: center; gap: 8px; }
  .barname { font-size: 13px; color: var(--muted); }
  .skillslots { display: flex; gap: 5px; flex-wrap: wrap; }
  @media (max-width: 420px) { .skillrow { grid-template-columns: 1fr; } }

  .cp { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
  .cphead { display: flex; align-items: center; gap: 5px; font-weight: 600; font-size: 14px; margin-bottom: 4px; }
  .cphead img { width: 18px; height: 18px; }
  .cpname { font-size: 13px; color: #cfcfcf; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  @media (max-width: 420px) { .cp { grid-template-columns: 1fr; } }

  .sets { display: grid; gap: 6px; }
  .set { display: flex; justify-content: space-between; gap: 10px; padding: 6px 10px; border-left: 2px solid var(--accent); background: #ffffff06; font-size: 14px; }
  .set .num { color: var(--muted); }
  .none { text-align: center; margin: 4px 0; }
</style>
