<script>
  import Frame from '../ui/Frame.svelte';
  import Bar from '../ui/Bar.svelte';
  import { app } from '../store.svelte.js';
  import { gameIcon } from '../achievements.js';
  import { timeLeft } from '../time.js';

  /** The Tamriel Tomes menu (iasync 1.11.0): Tome rewards track, Endeavors (timed activities) and Golden Pursuits. @type {{ book: string }} */
  let { book } = $props();

  const act = $derived(app.data.value?.activities);
  const tome = $derived(act?.tome);
  const timed = $derived(act?.timed ?? []);
  const campaigns = $derived(act?.campaigns ?? []);
  const fmt = (/** @type {number} */ n) => (n ?? 0).toLocaleString('en-US');
  const QUALITY = ['normal', 'normal', 'fine', 'superior', 'epic', 'legendary', 'mythic'];
  const nextTier = $derived(tome?.tiers?.find((/** @type {any} */ t) => t.tier === tome.tier + 1));
</script>

{#snippet reward(/** @type {any} */ r, /** @type {boolean} */ locked)}
  <div class="rw" class:locked class:claimed={r.claimed} title="{r.name}{r.quantity > 1 ? ` ×${r.quantity}` : ''}{r.claimed ? ' (claimed)' : locked ? ' (premium)' : ''}">
    {#if gameIcon(r.icon)}<img src={gameIcon(r.icon)} alt="" loading="lazy" />{/if}
    <span style="color: var(--q-{QUALITY[r.quality] ?? 'normal'})">{r.name}{#if r.quantity > 1} <span class="num">×{fmt(r.quantity)}</span>{/if}</span>
  </div>
{/snippet}

{#snippet activityRow(/** @type {any} */ a, /** @type {string} */ rewardText)}
  {@const done = a.max && a.progress >= a.max}
  <div class="act" class:done>
    <div class="an">{#if gameIcon(a.icon)}<img src={gameIcon(a.icon)} alt="" />{/if}<span>{a.name}</span></div>
    <Bar value={Math.min(a.progress, a.max)} max={a.max} label={a.name} />
    <span class="ar">{rewardText}</span>
  </div>
{/snippet}

{#if !act}
  <Frame title="TAMRIEL TOME"><p class="hint none">No activity data yet: it needs iasync 1.11.0. Type /reloadui in game, then upload again.</p></Frame>
{:else if book === 'endeavors'}
  <div class="two">
    {#each [['weekly', 'WEEKLY ENDEAVORS'], ['seasonal', 'SEASONAL ENDEAVORS']] as [type, title] (type)}
      {@const list = timed.filter((/** @type {any} */ t) => t.type === type)}
      <Frame {title}>
        <div class="sum"><span>Completed</span><span class="num">{[`${list.filter((/** @type {any} */ t) => t.max && t.progress >= t.max).length} / ${list.length}`, timeLeft(act.resets?.[type]) && `resets in ${timeLeft(act.resets[type])}`].filter(Boolean).join(' · ')}</span></div>
        <div class="list">
          {#each list as t, i (i)}
            {@render activityRow(t, `${fmt(t.reward)} Tome Points${t.claimable > 1 ? ` · ${t.claimed}/${t.claimable}` : ''}`)}
          {:else}
            <p class="hint">None this {type === 'weekly' ? 'week' : 'season'}.</p>
          {/each}
        </div>
      </Frame>
    {/each}
  </div>
{:else if book === 'pursuits'}
  <div class="two">
    {#each campaigns as c, i (i)}
      <Frame title={c.name.toUpperCase()}>
        <p class="desc">{c.description}</p>
        <div class="sum"><span>Completed</span><span class="num">{[`${c.completed} / ${c.capstone}`, timeLeft(c.endTime) && `ends in ${timeLeft(c.endTime)}`].filter(Boolean).join(' · ')}</span></div>
        <Bar value={Math.min(c.completed, c.capstone)} max={c.capstone} label="{c.name} progress" />
        {#if c.milestones.length}
          <div class="miles">{#each c.milestones as m, i (i)}<span class:got={m.claimed || c.completed >= m.threshold}>{m.threshold}</span>{/each}</div>
        {/if}
        <div class="list tall">
          {#each c.activities as a, i (i)}{@render activityRow(a, a.claimed ? 'Claimed' : '')}{/each}
        </div>
      </Frame>
    {:else}
      <Frame title="GOLDEN PURSUITS"><p class="hint none">No Golden Pursuits running.</p></Frame>
    {/each}
  </div>
{:else if !tome}
  <Frame title="TAMRIEL TOME"><p class="hint none">No Tamriel Tome season is running.</p></Frame>
{:else}
  <Frame title={tome.name.toUpperCase()}>
    <div class="head">
      <span class="lvl">Level <b class="num">{tome.tier}</b></span>
      <div class="hb">
        <Bar value={tome.progressToNext} max={nextTier?.total || tome.progressToNext || 1} label="Progress to the next level" />
      </div>
      <span class="dim">{[tome.premium ? 'Premium' : 'Free track', timeLeft(tome.endTime) && `ends in ${timeLeft(tome.endTime)}`].filter(Boolean).join(' · ')}</span>
    </div>
    <div class="tiers">
      {#each tome.tiers as t (t.tier)}
        <section class="tier" class:cur={t.tier === tome.tier} class:past={t.tier < tome.tier}>
          <h6>Level {t.tier}</h6>
          {#each t.free as r, i (i)}{@render reward(r, false)}{/each}
          {#each t.premium as r, i (i)}{@render reward(r, !tome.premium)}{/each}
        </section>
      {/each}
    </div>
  </Frame>
{/if}

<style>
  .two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; align-items: start; }
  @media (max-width: 900px) { .two { grid-template-columns: minmax(0, 1fr); } }
  .sum { display: flex; justify-content: space-between; gap: 10px; font-size: 14px; color: var(--muted); margin-bottom: 6px; }
  .list { display: grid; gap: 4px; margin-top: 8px; max-height: max(280px, calc(100dvh - 470px)); overflow-y: auto; padding-right: 4px; }
  .list.tall { max-height: max(240px, calc(100dvh - 540px)); } /* description and milestones above it */
  .act { display: grid; grid-template-columns: minmax(0, 1fr) 160px auto; align-items: center; gap: 10px; padding: 3px 6px; font-size: 14px; }
  .an { display: flex; align-items: center; gap: 6px; min-width: 0; }
  .an span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .an img { width: 22px; height: 22px; }
  .act.done .an { color: var(--accent-hi); }
  .ar { font-size: 12px; color: var(--muted); white-space: nowrap; }
  .desc { margin: 0 0 8px; font-size: 13px; color: var(--muted); }
  .miles { display: flex; gap: 6px; margin-top: 6px; }
  .miles span { padding: 0 6px; font-size: 12px; border: 1px solid var(--line); color: var(--muted); }
  .miles span.got { color: var(--accent-hi); border-color: var(--accent); }
  .head { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 14px; margin-bottom: 10px; }
  .lvl { font-size: 18px; }
  .dim { color: var(--muted); font-size: 13px; }
  .tiers { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 8px; max-height: max(320px, calc(100dvh - 420px)); overflow-y: auto; }
  .tier { display: grid; align-content: start; gap: 4px; padding: 8px; border: 1px solid #ffffff17; }
  .tier.cur { border-color: var(--accent-hi); }
  .tier.past { opacity: 0.75; }
  h6 { margin: 0 0 2px; font-size: 13px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--fg); }
  .rw { display: grid; grid-template-columns: 32px minmax(0, 1fr); align-items: center; gap: 6px; font-size: 13px; line-height: 1.15; }
  .rw img { width: 32px; height: 32px; }
  .rw.locked { opacity: 0.45; }
  .rw.claimed span::after { content: ' ✓'; color: var(--accent-hi); }
  .none { text-align: center; margin: 4px 0; }
  :global(:root[data-ui='classic']) .act, :global(:root[data-ui='classic']) .rw { font: 500 16px var(--eso-font-medium); color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .act { background: var(--eso-list-bg) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) .act.done .an { color: var(--eso-contrast); }
  :global(:root[data-ui='classic']) .tier { border: 0; background: var(--eso-slot-bg) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) .tier.cur { background: var(--eso-slot-hl) 0 0 / 100% 100%, var(--eso-slot-bg) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) h6, :global(:root[data-ui='classic']) .lvl { font: 700 18px var(--eso-font); color: var(--eso-selected); letter-spacing: 0; }
  :global(:root[data-ui='classic']) .sum, :global(:root[data-ui='classic']) .dim, :global(:root[data-ui='classic']) .ar, :global(:root[data-ui='classic']) .desc { color: var(--eso-normal); }
</style>
