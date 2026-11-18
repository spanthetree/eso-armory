<script>
  import { app } from '../store.svelte.js';
  import { iconKey } from '../eso.js';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { skillbookUrl } from '../lookups.svelte.js';
  import SkillTip from '../tips/SkillTip.svelte';

  /**
   * One ability on a skill bar: game icon when known, else the name. Links to eso-skillbook.com.
   * @type {{ name: string, ultimate?: boolean, delay?: number }}
   */
  let { name, ultimate = false, delay = 0 } = $props();

  const known = $derived(!!name && !name.startsWith('#'));
  const icon = $derived(known ? app.abilityIcons[iconKey(name)] : null);
</script>

{#if known}
  <a
    class="skill"
    class:ult={ultimate}
    style="--d: {delay}s"
    href={skillbookUrl(name)}
    target="_blank"
    rel="noopener noreferrer"
    aria-label={name}
    use:tooltip={{ component: SkillTip, props: { name, ultimate } }}>
    {#if icon}<img src={icon} alt="" loading="lazy" />{:else}<span>{name}</span>{/if}
  </a>
{:else}
  <span class="skill empty" class:ult={ultimate} style="--d: {delay}s" title={name ? `Unknown ability ${name}: no name from iasync or UESP` : 'Empty slot'}>{name ? '?' : ''}</span>
{/if}

<style>
  .skill {
    display: grid;
    place-items: center;
    width: 40px;
    height: 40px;
    overflow: hidden;
    border: 1px solid var(--line);
    background: linear-gradient(160deg, #1c1813, #0b0a09);
    color: var(--fg);
    text-decoration: none;
    font-size: 9px;
    line-height: 1.05;
    text-align: center;
    transition: transform 0.2s var(--ease-spring), border-color 0.2s, box-shadow 0.2s;
    animation: pop 0.45s var(--ease-spring) both;
    animation-delay: var(--d);
  }
  .skill.ult { margin-left: 6px; border-color: var(--accent); box-shadow: 0 0 12px -3px var(--accent); }
  a.skill:hover, a.skill:focus-visible { transform: translateY(-2px); border-color: var(--accent-hi); box-shadow: 0 0 14px -2px var(--accent); outline: none; }
  img { width: 38px; height: 38px; }
  span { padding: 2px; overflow: hidden; }
  .empty { color: var(--muted); opacity: 0.5; }
  @keyframes pop { from { opacity: 0; transform: scale(0.6); } }
</style>
