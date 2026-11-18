<script>
  import Frame from '../ui/Frame.svelte';
  import TextTip from '../tips/TextTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';

  /**
   * Slotted champion stars per tree. `cp` is { "1".."12": starId }: 1-4 Craft, 5-8 Warfare, 9-12 Fitness.
   * `descriptions` (star id -> text) feeds the hover tooltip when iasync recorded it.
   * @type {{ cp: Record<string, number> | null | undefined, names: Record<string, string>, descriptions?: Record<string, string>, delay?: number }}
   */
  let { cp, names, descriptions = {}, delay = 0.35 } = $props();

  const TREES = [
    { label: 'Craft', color: '#A5DB52', icon: '/assets/interface/champion_stamina.png', slots: ['1', '2', '3', '4'] },
    { label: 'Warfare', color: '#5ABAE7', icon: '/assets/interface/champion_magicka.png', slots: ['5', '6', '7', '8'] },
    { label: 'Fitness', color: '#E76931', icon: '/assets/interface/champion_health.png', slots: ['9', '10', '11', '12'] },
  ];
  const any = $derived(Object.values(cp ?? {}).some((v) => Number(v) > 0));
</script>

{#if any}
  <Frame title="CHAMPION POINTS" {delay}>
    <div class="cp">
      {#each TREES as t (t.label)}
        <div>
          <div class="cphead" style="color: {t.color}"><img src={t.icon} alt="" />{t.label}</div>
          <div class="cpnames">
            {#each t.slots as s (s)}
              {#if cp?.[s]}<span tabindex="0" use:tooltip={{ component: TextTip, props: { head: t.label, name: names[String(cp[s])] || `#${cp[s]}`, desc: descriptions?.[String(cp[s])] } }}>{names[String(cp[s])] || `#${cp[s]}`}</span>{/if}
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </Frame>
{/if}

<style>
  .cp { display: grid; gap: 10px; }
  .cphead { display: flex; align-items: center; justify-content: center; gap: 5px; font-weight: 600; font-size: 14px; margin-bottom: 4px; }
  .cphead img { width: 18px; height: 18px; }
  /* Up to 4 slotted stars per tree, on one centred line (wraps only if the panel is too narrow). */
  .cpnames { display: flex; flex-wrap: wrap; justify-content: center; gap: 2px 14px; font-size: 13px; color: #cfcfcf; }
  .cpnames span { white-space: nowrap; }
</style>
