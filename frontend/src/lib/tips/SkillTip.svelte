<script>
  import { loadSkillInfo, skillInfo } from '../lookups.svelte.js';
  import { slugify } from '../gear.js';

  /** Skill tooltip: details scraped from eso-skillbook.com on first view. @type {{ name: string, ultimate?: boolean }} */
  let { name, ultimate = false } = $props();

  $effect(() => {
    loadSkillInfo(name);
  });
  const info = $derived(skillInfo[slugify(name)]);
  const STATS = /** @type {const} */ ([
    ['cost', 'Cost'],
    ['cast_time', 'Cast'],
    ['target', 'Target'],
    ['range', 'Range'],
  ]);
</script>

<div class="bar" class:ult={ultimate}></div>
<div class="t-name skill">{name}</div>
{#if !info || info.loading}
  <div class="t-small t-faint">Loading skill info…</div>
{:else if info.error && !info.description}
  <div class="t-small t-faint">{info.error}</div>
{:else}
  {#if info.type || info.location}
    <div class="t-chips">
      {#if info.type}<span class="t-chip">{info.type}</span>{/if}
      {#if info.location}<span class="t-chip">{info.location}</span>{/if}
    </div>
  {/if}
  <div class="stats t-small">
    {#each STATS as [key, label] (key)}
      {#if info[key]}<span>{label} <b>{info[key]}</b></span>{/if}
    {/each}
  </div>
  {#if info.description}<hr /><p class="t-small desc">{info.description}</p>{/if}
  <div class="t-faint">Click to open on eso-skillbook.com</div>
{/if}

<style>
  .bar { height: 2px; margin: -12px -14px 10px; background: var(--q-superior); }
  .bar.ult { background: var(--accent); }
  .skill { color: #b9d0ff; }
  .stats { display: flex; flex-wrap: wrap; gap: 4px 12px; color: var(--muted); }
  .stats b { color: var(--fg); font-weight: 500; }
  .desc { margin: 0; color: #d6d6d6; }
</style>
