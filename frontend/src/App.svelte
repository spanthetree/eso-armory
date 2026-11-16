<script>
  import { setAllianceTint } from './lib/eso.js';
  import Frame from './lib/ui/Frame.svelte';
  import Slot from './lib/ui/Slot.svelte';
  import ResourceBar from './lib/ui/ResourceBar.svelte';
  import Tabs from './lib/ui/Tabs.svelte';
  import AllianceSwitch from './lib/ui/AllianceSwitch.svelte';
  import Banners from './lib/ui/Banners.svelte';
  import TooltipHost from './lib/ui/TooltipHost.svelte';

  // Phase 1 component preview with sample data; replaced by the app shell in Phase 2.
  let al = $state(/** @type {'ad' | 'dc' | 'ep'} */ ('ep'));
  const ALLIANCE = { ad: 'Aldmeri Dominion', dc: 'Daggerfall Covenant', ep: 'Ebonheart Pact' };
  $effect(() => setAllianceTint(al));

  let tab = $state('equipment');
  const TABS = [
    { id: 'equipment', label: 'Equipment' },
    { id: 'inventory', label: 'Inventory' },
    { id: 'achievements', label: 'Achievements' },
    { id: 'collections', label: 'Collections' },
  ];

  const g = '/assets/gear';
  const ARMOR = [
    ['Head', 'armor/light/gear_breton_light_head_d', 'legendary'],
    ['Shoulders', 'armor/light/gear_breton_light_shoulders_d', 'legendary'],
    ['Chest', 'armor/light/gear_breton_light_shirt_d', 'legendary'],
    ['Hands', 'armor/light/gear_breton_light_hands_d', 'epic'],
    ['Waist', 'armor/light/gear_breton_light_waist_d', 'legendary'],
    ['Legs', 'armor/light/gear_breton_light_legs_d', 'legendary'],
    ['Feet', 'armor/light/gear_breton_light_feet_d', 'superior'],
  ];
  const OTHER = [
    ['Neck', 'jewelry/gear_breton_neck_a', 'mythic'],
    ['Ring', 'jewelry/gear_breton_ring_a', 'legendary'],
    ['Ring', 'jewelry/gear_breton_ring_a', 'epic'],
    ['Main hand', 'weapon/gear_breton_staff_d', 'legendary'],
    ['Off hand', '', 'normal'],
  ];
  const RES = /** @type {const} */ ([
    ['magicka', 41210, 45000],
    ['health', 21865, 30000],
    ['stamina', 12400, 30000],
  ]);
  let replay = $state(0);

  const SET = { name: "Mother's Sorrow", have: 4, bonus: ['(2) Adds 657 Critical Chance', '(3) Adds 1096 Max Magicka', '(4) Adds 657 Critical Chance', '(5) Adds 1528 Critical Chance'] };
</script>

{#snippet itemTip(/** @type {{ label: string, q: string }} */ it)}
  <div class="t-name" style="color: var(--q-{it.q})">{it.label} of Mother's Sorrow</div>
  <div class="t-row"><span>Light Armor · {it.label}</span><span>Divines</span></div>
  <hr />
  <div class="t-row"><span>Part of</span><span>{SET.name} ({SET.have}/5)</span></div>
  {#each SET.bonus as b, i (i)}<div class:t-off={i + 2 > SET.have}>{b}</div>{/each}
{/snippet}

<TooltipHost />
<Banners cls="Arcanist" alliance={ALLIANCE[al]} />

<main>
  <div class="top">
    <button class="link" onclick={() => replay++}>↻ Replay intro</button>
    <AllianceSwitch bind:value={al} />
  </div>

  <header>
    <div class="sub">Dark Elf · Arcanist · {ALLIANCE[al]}</div>
    <h1>Seryn Vel-Ashar</h1>
    <div class="sub">Level 50 · CP 2,104</div>
  </header>

  <Tabs items={TABS} bind:active={tab} />

  {#key replay}
    <div class="grid">
      <Frame title="ARMOR" delay={0.15}>
        <div class="slots">
          {#each ARMOR as [label, icon, q], i (i)}<Slot {label} icon="{g}/{icon}.png" quality={q} delay={0.35 + i * 0.05} tip={{ snippet: itemTip, arg: { label, q } }} />{/each}
        </div>
      </Frame>
      <Frame title="ATTRIBUTES" delay={0.3}>
        <div class="bars">
          {#each RES as [kind, v, max], i (kind)}<ResourceBar {kind} value={v} {max} delay={0.55 + i * 0.15} />{/each}
        </div>
      </Frame>
      <Frame title="JEWELRY & WEAPONS" delay={0.25}>
        <div class="slots">
          {#each OTHER as [label, icon, q], i (i)}<Slot {label} icon={icon && `${g}/${icon}.png`} quality={q} delay={0.5 + i * 0.05} />{/each}
        </div>
      </Frame>
    </div>
  {/key}
  <p class="sub">Active tab: {tab}. Tab content switching arrives with the app shell in Phase 2.</p>
</main>

<style>
  :global(#app) { position: relative; isolation: isolate; min-height: 100vh; }
  main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 64px; display: grid; gap: 18px; }
  .top { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
  header { text-align: center; display: grid; gap: 4px; }
  h1 { color: var(--accent-hi); font-size: clamp(24px, 4vw, 34px); letter-spacing: 0.12em; text-shadow: 0 0 18px color-mix(in srgb, var(--accent) 40%, transparent); }
  .sub { color: var(--muted); text-transform: uppercase; letter-spacing: 0.2em; font-size: 13px; margin: 0; }
  p.sub { text-transform: none; letter-spacing: 0.04em; text-align: center; }
  .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; align-items: start; }
  @media (max-width: 760px) { .grid { grid-template-columns: minmax(0, 1fr); } }
  .slots { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
  .bars { display: grid; gap: 12px; }
  .link { all: unset; cursor: pointer; color: var(--muted); font-size: 14px; }
  .link:hover { color: var(--fg); }
</style>
