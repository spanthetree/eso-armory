<script>
  import Frame from '../ui/Frame.svelte';
  import EsoWindow from '../eso/EsoWindow.svelte';
  import EsoBar from '../eso/EsoBar.svelte';
  import AchievTip from '../tips/AchievTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { ART, applyUiColors } from '../eso/tex.js';
  import { app } from '../store.svelte.js';
  import { buildIndex, achievementsIn, extraSubcats, gameIcon, pressedIcon, searchAll, charName, collapseLines, timeline, pct } from '../achievements.js';

  // The in-game keyboard Achievements screen (esoui ingame/achievements/keyboard/achievements.xml), positioned in the
  // game's own pixels on EsoWindow's stage. Comments give the template each block copies.
  const data = $derived(app.achievements.value);
  const idx = $derived(buildIndex(data));
  $effect(() => applyUiColors(data?.uiColors));
  const fmt = (/** @type {number} */ n) => (n ?? 0).toLocaleString('en-US');
  const SUMMARY_ICON = '/esoicons/treeicons/achievements_indexicon_summary_up.png';
  // shortcut: tree icons UESP has under a guessable name, for data scanned before iasync 1.6.0 recorded them; drop once everyone has 1.6.0.
  /** @type {Record<string, string>} */
  const KNOWN_ICONS = { Character: 'general', 'Player VS Player': 'alliancewar', Crafting: 'crafting', Dungeons: 'dungeons', 'DLC Dungeons': 'dungeons', Exploration: 'exploration', Quests: 'quests', 'Holiday Events': 'events' };
  /** @param {any} c */
  const catIcon = (c) => gameIcon(c.icon) ?? (KNOWN_ICONS[c.name] ? `/esoicons/treeicons/achievements_indexicon_${KNOWN_ICONS[c.name]}_up.png` : null);
  /** @param {string | null} src */
  const overIcon = (src) => (src ? src.replace(/_up\.png$/, '_over.png') : src);

  let charId = $state(/** @type {string | null} */ (null));
  $effect(() => {
    // Start on the character with the most records: iasync can miss a category for a character it scanned early.
    if (!charId && data?.chars?.length)
      charId = data.chars.reduce((/** @type {any} */ best, /** @type {any} */ c) => ((data.items_by_char[c.id]?.length ?? 0) > (data.items_by_char[best.id]?.length ?? 0) ? c : best)).id;
  });

  // FILTER BY: like the game, the search narrows the tree to categories with matches.
  let search = $state('');
  const needle = $derived(search.trim().toLowerCase());
  const found = $derived(needle ? searchAll(idx, data?.categories, charId, needle, 100000) : null);
  /** @type {Map<string, Set<string>> | null} */
  const hits = $derived(found ? found.groups.reduce((m, g) => m.set(g.cat, (m.get(g.cat) ?? new Set()).add(g.sub)), new Map()) : null);

  let filter = $state('all'); // SI_ACHIEVEMENT_FILTER_SHOW_*
  /** Extra tree entry (not in the game): every recent completion, by day. */
  let showTimeline = $state(false);
  const TIMELINE_ICON = '/esoicons/treeicons/tutorial_idexicon_timedactivities_up.png';
  const days = $derived(timeline(data?.recent));
  /** null = summary */
  let catName = $state(/** @type {string | null} */ (null));
  let subName = $state(/** @type {string | null} */ (null));
  let openId = $state(/** @type {number | null} */ (null));

  const cats = $derived((data?.categories ?? []).filter((/** @type {any} */ c) => !hits || hits.has(c.name)));
  const cat = $derived(cats.find((/** @type {any} */ c) => c.name === catName) ?? (hits && cats[0]) ?? null);
  const subcats = $derived(cat ? [...cat.subcats, ...extraSubcats(idx, cat, charId)].filter((s) => !hits || hits.get(cat.name)?.has(s.key ?? s.name)) : []);
  const withData = $derived(new Set(subcats.filter((/** @type {any} */ s) => achievementsIn(idx, cat.name, s.key ?? s.name, charId).length).map((/** @type {any} */ s) => s.name)));
  const sub = $derived(subcats.find((/** @type {any} */ s) => s.name === subName) ?? subcats.find((/** @type {any} */ s) => withData.has(s.name)) ?? subcats[0] ?? null);
  const list = $derived(
    cat && sub
      ? collapseLines(achievementsIn(idx, cat.name, sub.key ?? sub.name, charId, needle)).filter((a) => filter === 'all' || (filter === 'earned') === !!a.complete)
      : [],
  );
  const recent = $derived((data?.recent ?? []).slice(0, 6)); // NUM_RECENT_ACHIEVEMENTS_TO_SHOW
  const summaryCats = $derived((data?.categories ?? []).filter((/** @type {any} */ c) => c.totalPts > 0));

  /** @param {string | null} name */
  function pick(name) {
    showTimeline = false;
    if (name === catName && name) return void (catName = null); // clicking the open category folds it back to the summary
    catName = name;
    subName = null;
    openId = null;
  }
  /** @param {string} cname @param {string} sname */
  function pickSub(cname, sname) {
    showTimeline = false;
    catName = cname;
    subName = sname;
    openId = null;
  }
  /** @param {any} a */
  const expandable = (a) => !!(a.criteria?.length || a.rewards?.length || a.line || (a.desc?.length ?? 0) > 90);
  /** @param {any} r */
  const rewardText = (r) => (r.type === 'title' ? `Title: ${r.name}` : r.type === 'dye' ? `Dye: ${r.name ?? ''}` : r.type === 'collectible' || r.type === 'item' ? (r.name ?? '') : '');
</script>

{#snippet icon(/** @type {any} */ a, /** @type {number} */ size)}
  {@const src = gameIcon(a.icon)}
  <span class="eso-icon" class:off={!a.complete} style="width: {size}px; height: {size}px">
    {#if src}<img {src} alt="" loading="lazy" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.visibility = 'hidden')} />{/if}
  </span>
{/snippet}

{#snippet treeHead(/** @type {string | null} */ src, /** @type {string} */ label, /** @type {boolean} */ on, /** @type {boolean | undefined} */ expanded, /** @type {() => void} */ click, /** @type {string | undefined} */ tip = undefined)}
  <button class="eso-th" aria-current={on} aria-expanded={expanded} onclick={click} title={tip}>
    {#if src}
      <img class="ico" src={on || expanded ? pressedIcon(src) : src} alt="" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.visibility = 'hidden')} />
      <img class="ico-hl" src={overIcon(src)} alt="" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.display = 'none')} />
    {/if}
    <span class="txt">{label}</span>
  </button>
{/snippet}

{#snippet row(/** @type {any} */ a)}
  {@const open = openId === a.id}
  {@const canOpen = expandable(a)}
  <!-- ZO_Achievement: 550 wide, 88 collapsed -->
  <div class="ach eso-list-bg" class:done={a.complete} class:open role="listitem">
    <i class="hl eso-list-hl"></i>
    {#if canOpen}<button class="eso-arrow ex" aria-expanded={open} aria-label={open ? 'Collapse' : 'Expand'} onclick={() => (openId = open ? null : a.id)}></button>{/if}
    <span class="ai">{@render icon(a, 52)}</span>
    {#if a.rewards?.length}<img class="thumb" src="{ART}achievements/achievements_reward_{a.complete ? 'earned' : 'unearned'}.png" alt="Has a reward" />{/if}
    <div class="at eso-ellipsis">{a.name}</div>
    <div class="ad" class:clamp={!open}>{a.desc}</div>
    <div class="ap">{a.points}</div>
    {#if a.complete && a.completionDate}<div class="adate">{a.completionDate}</div>{/if}
    {#if open}
      <div class="more">
        {#each a.criteria ?? [] as c, i (i)}
          {#if c.req > 1}
            <div class="crit-bar"><span class="cl eso-h5">{c.desc}</span><EsoBar value={c.cur} max={c.req} style="width: 345px" /></div>
          {:else}
            <div class="crit-chk"><img src="{ART}cadwell/check.png" alt="" style:opacity={c.cur >= c.req ? 1 : 0} /><span>{c.desc}</span></div>
          {/if}
        {/each}
        {#if a.line}
          <div class="line">
            {#each a.line as t (t.id)}
              <div class="lt" title={t.name}>{@render icon(t, 45)}<span class:on={t.complete}>{t.points}</span></div>
            {/each}
          </div>
        {/if}
        {#each a.rewards ?? [] as r, i (i)}
          {#if rewardText(r)}<div class="rw eso-h5">{rewardText(r)}</div>{/if}
        {/each}
      </div>
    {/if}
  </div>
{/snippet}

{#if app.achievements.loading && !data}
  <Frame title="ACHIEVEMENTS"><p class="hint center">Loading achievements…</p></Frame>
{:else if app.achievements.error}
  <Frame title="ACHIEVEMENTS">
    <div class="err-box" role="alert"><b>User data not loaded</b><span>{app.achievements.error}</span></div>
  </Frame>
{:else if data}
  <EsoWindow title="Achievements">
    {#if data.chars?.length}
      <div class="eso-combo eso-abs" style="left: 768px; top: 24px; width: 222px">
        <select bind:value={charId} aria-label="Character">
          {#each data.chars as c (c.id)}<option value={c.id}>{charName(c.name)}</option>{/each}
        </select>
      </div>
    {/if}

    <!-- Search + "Filter By" (ContentsSearch at 9,33 of Contents) -->
    <label class="eso-abs flab" for="ach-search">Filter By</label>
    <input id="ach-search" class="eso-edit eso-abs" type="search" placeholder="Search" aria-label="Search achievements" bind:value={search} style="left: 74px; top: 105px; width: 240px" />

    <!-- Category tree (ContentsCategories: 353 wide at -28,77) -->
    <nav class="eso-abs eso-scroll eso-tree tree" aria-label="Achievement categories">
      {#if !hits}
        {@render treeHead(SUMMARY_ICON, 'Summary', catName === null && !showTimeline, undefined, () => pick(null))}
        {#if days.length}{@render treeHead(TIMELINE_ICON, 'Timeline', showTimeline, undefined, () => ((showTimeline = true), (catName = null)))}{/if}
      {/if}
      {#each cats as c (c.name)}
        {@const isOpen = cat?.name === c.name}
        {@render treeHead(catIcon(c), c.name, false, isOpen, () => pick(c.name), `${fmt(c.earnedPts)} / ${fmt(c.totalPts)} points (${pct(c.earnedPts, c.totalPts)}%)`)}
        {#if isOpen}
          {#each subcats as s (s.key ?? s.name)}
            <button class="eso-ts" class:dim={!withData.has(s.name)} aria-current={sub?.name === s.name} onclick={() => pickSub(c.name, s.name)} title={s.total ? `${s.complete}/${s.total} complete` : undefined}>{s.name}</button>
          {/each}
        {/if}
      {:else}
        <p class="none">No achievements match.</p>
      {/each}
    </nav>

    {#if showTimeline && !hits}
      <div class="eso-abs eso-h2 ctitle">Timeline</div>
      <div class="eso-abs pts">Achievement Points: <span>{fmt(data.earnedPts)}</span></div>
      <div class="eso-abs eso-scroll list tl" role="list">
        {#each days as d (d.day)}
          <div class="day eso-h4">{d.day}</div>
          {#each d.list as a (a.id)}
            {@render row(a)}
            <div class="by">
              <button class="lnk" onclick={() => pickSub(a.cat, a.subcat || 'Other')}>{a.cat}{a.subcat ? ` › ${a.subcat}` : ''}</button>
              {#if a.completedByCharName}<span>· {charName(a.completedByCharName)}</span>{/if}
            </div>
          {/each}
        {/each}
      </div>
    {:else if !cat}
      <!-- ContentsSummaryInset -->
      <div class="eso-abs pts">Achievement Points: <span>{fmt(data.earnedPts)}</span></div>
      <div class="eso-abs eso-scroll bars">
        <div class="bars-in" style="height: {98 + Math.ceil(summaryCats.length / 2) * 66}px">
          <span class="eso-abs eso-h4 blabel" style="left: 4px; top: 4px">Achievement Points Earned</span>
          <EsoBar value={data.earnedPts} max={data.totalPts} style="position: absolute; left: 4px; top: 28px; width: 522px" />
          {#each summaryCats as c, i (c.name)}
            {@const left = i % 2 ? 286 : 4}
            {@const top = 98 + Math.floor(i / 2) * 66}
            <button class="sbar" style="left: {left}px; top: {top - 24}px" onclick={() => pick(c.name)}>
              <span class="eso-h4 blabel eso-ellipsis">{c.name}</span>
              <EsoBar value={c.earnedPts} max={c.totalPts} style="width: 240px" />
            </button>
          {/each}
        </div>
      </div>
      <div class="eso-abs recent">
        <img src="{ART}quest/questjournal_divider.png" alt="" style="display: block; width: 512px; height: 4px" />
        <div class="eso-h2 rtitle">Recent Achievements</div>
        {#each recent as a, i (i)}
          <button class="ri" style="left: {i * 84}px" use:tooltip={{ component: AchievTip, props: { a } }} onclick={() => a.cat && pickSub(a.cat, a.subcat || 'Other')}>{@render icon(a, 64)}</button>
        {/each}
      </div>
    {:else}
      <!-- Category header: title, progress (ZO_AchievementsStatusBar), filter combo (222x32) -->
      <div class="eso-abs eso-h2 eso-ellipsis ctitle">{cat.name}</div>
      {#if sub}<EsoBar value={sub.earnedPts} max={sub.totalPts} style="position: absolute; left: 427px; top: 118px; width: 321px" />{/if}
      <div class="eso-combo eso-abs" style="left: 768px; top: 112px; width: 222px; height: 32px">
        <select bind:value={filter} aria-label="Filter achievements">
          <option value="all">All Achievements</option>
          <option value="earned">Show Earned</option>
          <option value="unearned">Show Unearned</option>
        </select>
      </div>
      <!-- ContentsContentList -->
      <div class="eso-abs eso-scroll list" role="list">
        {#each list as a (`${charId}_${a.id}`)}{@render row(a)}{:else}<p class="none">No achievements to show.</p>{/each}
      </div>
    {/if}
  </EsoWindow>
{/if}

<style>
  .flab { left: 74px; top: 84px; font-size: 18px; color: var(--eso-normal); }
  .tree { left: 37px; top: 149px; width: 353px; height: 608px; }
  .none { margin: 12px 20px; font-size: 18px; color: var(--eso-selected); }

  .pts { right: 17px; top: 84px; font-size: 20px; color: var(--eso-normal); }
  .pts span { color: var(--eso-selected); }
  .bars { left: 427px; top: 149px; width: 551px; height: 451px; }
  .bars-in { position: relative; }
  .blabel { color: var(--eso-selected); }
  .sbar { all: unset; position: absolute; display: grid; gap: 4px; width: 240px; cursor: pointer; }
  .sbar:hover .blabel { color: var(--eso-highlight); }
  .sbar:focus-visible { outline: 1px solid var(--eso-normal); outline-offset: 2px; }
  .recent { left: 427px; top: 605px; width: 551px; height: 140px; }
  .rtitle { margin-top: 7px; }
  .ri { all: unset; position: absolute; bottom: 32px; width: 64px; height: 64px; cursor: pointer; }
  .ri:hover::after { content: ''; position: absolute; inset: 0; background: url('/assets/esoui/actionbar/actionbar_mouseover.png') 0 0 / 100% 100%; mix-blend-mode: plus-lighter; }
  .ri:focus-visible { outline: 1px solid var(--eso-normal); }

  .ctitle { left: 427px; top: 78px; width: 563px; }
  .list { left: 390px; top: 154px; width: 588px; height: 603px; }
  .tl { top: 120px; height: 637px; }
  .day { padding: 10px 0 6px 38px; color: var(--eso-selected); }
  .by { margin: -6px 0 6px 96px; font-size: 16px; color: var(--eso-normal); }
  .lnk { all: unset; cursor: pointer; color: var(--eso-normal); }
  .lnk:hover, .lnk:focus-visible { color: var(--eso-highlight); text-decoration: underline; }

  .ach { position: relative; width: 550px; min-height: 88px; padding: 10px 0 12px 96px; }
  .hl { position: absolute; inset: 0; opacity: 0; transition: opacity 0.15s; pointer-events: none; }
  .ach:hover .hl, .ach.open .hl { opacity: 1; }
  .ach:not(.done) .hl { filter: brightness(0.6) grayscale(1); }
  .ex { position: absolute; left: 1px; top: 20px; }
  .ai { position: absolute; left: 38px; top: 10px; }
  .thumb { position: absolute; left: 42px; top: 58px; width: 32px; height: 32px; }
  .at { width: 274px; font-size: 18px; color: var(--eso-selected); }
  .ad { width: 380px; font-size: 16px; color: var(--eso-normal); }
  .ad.clamp { display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; max-height: 45px; }
  .ach:not(.done) .at, .ach:not(.done) .ad, .ach:not(.done) .ap { color: var(--eso-disabled); }
  .ap { position: absolute; right: 6px; top: 2px; width: 70px; text-align: center; font-size: 54px; line-height: 54px; color: var(--eso-selected); }
  .adate { position: absolute; right: 6px; top: 48px; width: 70px; text-align: center; font-size: 18px; color: var(--eso-normal); white-space: nowrap; }
  .more { display: grid; gap: 10px; margin: 12px 0 0 -6px; }
  .crit-bar { display: grid; gap: 4px; }
  .cl { color: var(--eso-selected); }
  .crit-chk { display: flex; align-items: center; gap: 4px; width: 380px; font-size: 16px; color: var(--eso-selected); }
  .crit-chk img { width: 16px; height: 16px; }
  .line { display: flex; gap: 5px; margin-left: -90px; width: 550px; justify-content: center; }
  .lt { display: grid; justify-items: center; gap: 2px; width: 45px; font-size: 16px; color: var(--eso-disabled); }
  .lt span.on { color: var(--eso-selected); }
  .rw { color: var(--eso-normal); }

  .center { text-align: center; }
  .err-box { display: grid; gap: 4px; padding: 12px 16px; border: 1px solid #e5675a66; background: #e5675a14; color: #f2c4bd; font-size: 14px; }
  .err-box b { font: 600 14px var(--f-display); letter-spacing: 0.06em; color: #ffd9d3; }
</style>
