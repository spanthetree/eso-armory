<script>
  import { app } from '../store.svelte.js';
  import Frame from '../ui/Frame.svelte';
  import SkillSlot from './SkillSlot.svelte';
  import { extraAbilityNames, loadAbilityNames } from '../lookups.svelte.js';

  /**
   * Front/back/werewolf skill bars. `skills` is { primary: { 3..8: abilityId }, ... }.
   * @type {{ skills: any, names: Record<string, string>, icons?: Record<string, string>, delay?: number }}
   */
  let { skills, names, icons = {}, delay = 0.25 } = $props();

  const BARS = /** @type {const} */ ([
    ['primary', 'Front bar'],
    ['backup', 'Back bar'],
    ['werewolf', 'Werewolf'],
  ]);
  const SLOTS = [3, 4, 5, 6, 7, 8];
  const iconPaths = $derived({ ...(app.builds.value?.abilityIcons ?? {}), ...icons });
  const bars = $derived(BARS.filter(([bar]) => Object.keys(skills?.[bar] ?? {}).length));

  // Older uploads and unresolved abilities can still use the server lookup.
  $effect(() => {
    const missing = bars.flatMap(([bar]) => Object.values(skills[bar])).filter((id) => id && !names[String(id)]);
    if (missing.length) loadAbilityNames(missing);
  });
  /** @param {number} id */
  const nameOf = (id) => names[String(id)] || extraAbilityNames[String(id)] || `#${id}`;
</script>

{#if bars.length}
  <Frame title="SKILLS" {delay}>
    <div class="skills">
      {#each bars as [bar, label] (bar)}
        <div class="skillrow">
          <span class="barname">{label}</span>
          <div class="skillslots">
            {#each SLOTS as s, i (s)}
              {@const id = skills[bar][s]}
              <SkillSlot name={id ? nameOf(id) : ''} iconPath={iconPaths[String(id)]} ultimate={s === 8} delay={delay + 0.25 + i * 0.04} />
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </Frame>
{/if}

<style>
  .skills { display: grid; gap: 10px; }
  .skillrow { display: grid; grid-template-columns: 74px 1fr; align-items: center; gap: 8px; }
  .barname { font-size: 13px; color: var(--muted); }
  .skillslots { display: flex; gap: 5px; flex-wrap: wrap; }
  @media (max-width: 420px) { .skillrow { grid-template-columns: 1fr; } }
</style>
