<script>
  import Frame from '../ui/Frame.svelte';
  import Progress from '../ui/Progress.svelte';
  import AchievTip from '../tips/AchievTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { app } from '../store.svelte.js';
  import { buildIndex, achievementsIn, extraSubcats, pct, gameIcon, pressedIcon, searchAll, timeline, charName } from '../achievements.js';

  // Laid out like the in-game Achievements journal: category tree on the left, summary bars or a subcategory's list on the right.
  const data = $derived(app.achievements.value);
  const idx = $derived(buildIndex(data));
  const fmt = (/** @type {number} */ n) => (n ?? 0).toLocaleString('en-US');
  const SUMMARY_ICON = '/esoicons/treeicons/achievements_indexicon_summary_up.png';
  // shortcut: tree icons UESP has under a guessable name, for data scanned before iasync 1.6.0 recorded them; drop once everyone has 1.6.0.
  /** @type {Record<string, string>} */
  const KNOWN_ICONS = { Character: 'general', 'Player VS Player': 'alliancewar', Crafting: 'crafting', Dungeons: 'dungeons', 'DLC Dungeons': 'dungeons', Exploration: 'exploration', Quests: 'quests', 'Holiday Events': 'events' };
  /** @param {any} c */
  const catIcon = (c) => gameIcon(c.icon) ?? (KNOWN_ICONS[c.name] ? `/esoicons/treeicons/achievements_indexicon_${KNOWN_ICONS[c.name]}_up.png` : null);

  let charId = $state(/** @type {string | null} */ (null));
  $effect(() => {
    // Start on the character with the most records: iasync can miss a category for a character it scanned early.
    if (!charId && data?.chars?.length)
      charId = data.chars.reduce((/** @type {any} */ best, /** @type {any} */ c) => ((data.items_by_char[c.id]?.length ?? 0) > (data.items_by_char[best.id]?.length ?? 0) ? c : best)).id;
  });
  let search = $state('');
  const searching = $derived(search.trim().length > 0);
  const found = $derived(searching ? searchAll(idx, data?.categories, charId, search) : null);

  /** null = summary */
  let catName = $state(/** @type {string | null} */ (null));
  let subName = $state(/** @type {string | null} */ (null));
  const cat = $derived(data?.categories?.find((/** @type {any} */ c) => c.name === catName) ?? null);
  /** The category's own subcategories, then any extra ones its achievements are filed under. */
  const subcats = $derived(cat ? [...cat.subcats, ...extraSubcats(idx, cat, charId)] : []);
  /** Subcategories this character has achievement records for; iasync doesn't record every one. */
  const withData = $derived(new Set(subcats.filter((/** @type {any} */ s) => achievementsIn(idx, cat.name, s.key ?? s.name, charId).length).map((/** @type {any} */ s) => s.name)));
  const sub = $derived(subcats.find((/** @type {any} */ s) => s.name === subName) ?? subcats.find((/** @type {any} */ s) => withData.has(s.name)) ?? subcats[0] ?? null);
  const list = $derived(cat && sub ? achievementsIn(idx, cat.name, sub.key ?? sub.name, charId) : []);
  const days = $derived(timeline(data?.recent));

  /** @param {string | null} name */
  function pick(name) {
    search = '';
    if (name === catName && name) return void (catName = null); // clicking the open category folds it back to the summary
    catName = name;
    subName = null;
  }
  /** @param {string} cname @param {string} sname */
  function pickSub(cname, sname) {
    search = '';
    catName = cname;
    subName = sname;
  }
</script>

{#snippet bar(/** @type {number} */ v, /** @type {number} */ max, /** @type {boolean} */ big)}
  <span class="bar" class:big role="progressbar" aria-valuenow={v} aria-valuemin="0" aria-valuemax={max}>
    <span class="fill" style="width: {max ? Math.min(100, (v / max) * 100) : 0}%"></span>
    <span class="bt num">{fmt(v)}/{fmt(max)}</span>
  </span>
{/snippet}

{#snippet icon(/** @type {any} */ a, /** @type {number} */ size)}
  {@const src = gameIcon(a.icon)}
  <span class="icon" class:done={a.complete} style="width: {size}px; height: {size}px">
    <span class="star">★</span>
    {#if src}<img {src} alt="" loading="lazy" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.visibility = 'hidden')} />{/if}
  </span>
{/snippet}

{#snippet treeIcon(/** @type {string | null} */ src, /** @type {boolean} */ on)}
  <span class="ti">{#if src}<img src={on ? pressedIcon(src) : src} alt="" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.visibility = 'hidden')} />{:else}<i class="dot"></i>{/if}</span>
{/snippet}

{#snippet row(/** @type {any} */ a)}
  <div class="ach" class:done={a.complete} tabindex="0" role="listitem" use:tooltip={{ component: AchievTip, props: { a } }}>
    {@render icon(a, 46)}
    <div class="txt">
      <div class="an">{a.name}</div>
      {#if a.desc}<p class="ad">{a.desc}</p>{/if}
      {#if !a.complete && a.criteria?.length}
        {#each a.criteria.slice(0, 3) as c, i (i)}
          <div class="crit"><span>{c.desc}</span><span class="num">{c.cur}/{c.req}</span></div>
          {#if c.req > 1}<Progress value={c.cur} max={c.req} height={3} />{/if}
        {/each}
      {/if}
    </div>
    <div class="side">
      <span class="ap num">{a.points}</span>
      {#if a.complete && a.completionDate}<span class="date">{a.completionDate}</span>{/if}
    </div>
  </div>
{/snippet}

{#if app.achievements.loading && !data}
  <Frame title="ACHIEVEMENTS"><p class="hint center">Loading achievements…</p></Frame>
{:else if app.achievements.error}
  <Frame title="ACHIEVEMENTS">
    <div class="err-box" role="alert"><b>User data not loaded</b><span>{app.achievements.error}</span></div>
  </Frame>
{:else if data}
  <div class="layout">
    <aside class="side-nav">
      <label class="filter"><span>FILTER BY</span>
        <input class="field" type="search" placeholder="Search all achievements…" aria-label="Search achievements" bind:value={search} />
      </label>
      <nav class="nav" aria-label="Achievement categories">
        <button class="cat" aria-current={catName === null && !searching} onclick={() => pick(null)}>
          {@render treeIcon(SUMMARY_ICON, catName === null && !searching)}<span class="cn">SUMMARY</span>
        </button>
        {#each data.categories as c (c.name)}
          {@const on = catName === c.name && !searching}
          <button class="cat" aria-current={on} aria-expanded={catName === c.name} onclick={() => pick(c.name)}>
            {@render treeIcon(catIcon(c), on)}<span class="cn">{c.name}</span>
            <span class="cp num" title="{fmt(c.earnedPts)} / {fmt(c.totalPts)} points">{pct(c.earnedPts, c.totalPts)}%</span>
          </button>
          {#if catName === c.name}
            <div class="subs">
              {#each subcats as s (s.key ?? s.name)}
                <button class="subn" class:empty={!withData.has(s.name)} aria-current={sub?.name === s.name && !searching} onclick={() => pickSub(c.name, s.name)}>
                  <span>{s.name}</span>{#if s.totalPts && s.earnedPts >= s.totalPts}<span class="tick" title="Complete">✓</span>{/if}
                </button>
              {/each}
            </div>
          {/if}
        {/each}
      </nav>
    </aside>

    <section class="pane">
      <div class="tools">
        <h2>{searching ? 'SEARCH' : cat ? cat.name.toUpperCase() : 'SUMMARY'}</h2>
        {#if data.chars?.length}
          <label class="sel"><span>CHARACTER</span>
            <select class="field" bind:value={charId}>
              {#each data.chars as c (c.id)}<option value={c.id}>{charName(c.name)}</option>{/each}
            </select>
          </label>
        {/if}
        <span class="pts">Achievement Points: <b class="num">{fmt(data.earnedPts)}</b></span>
      </div>

      {#if searching && found}
        <div class="body">
          <p class="muted">{found.capped ? `First ${found.total}` : found.total} matches for “{search.trim()}”</p>
          {#each found.groups as g (g.cat + '|' + g.sub)}
            <h3><button class="link" onclick={() => pickSub(g.cat, g.sub || 'Other')}>{g.cat}{g.sub ? ` › ${g.sub}` : ''}</button></h3>
            <div class="items" role="list">{#each g.list as a (`${charId}_${a.id}`)}{@render row(a)}{/each}</div>
          {:else}
            <p class="hint">No achievements match.</p>
          {/each}
        </div>
      {:else if !cat}
        <div class="body">
          <h3 class="first">ACHIEVEMENT POINTS EARNED</h3>
          {@render bar(data.earnedPts, data.totalPts, true)}
          <div class="cats">
            {#each data.categories as c (c.name)}
              <button class="cg" onclick={() => pick(c.name)}>
                <span class="cgn">{c.name.toUpperCase()}</span>
                {@render bar(c.earnedPts, c.totalPts, false)}
              </button>
            {/each}
          </div>

          {#if days.length}
            <h3>RECENT ACHIEVEMENTS</h3>
            <div class="recent" role="list">
              {#each days.flatMap((d) => d.list).slice(0, 12) as a, i (a.id)}
                <div class="ra" style="--d: {i * 0.04}s" tabindex="0" role="listitem" use:tooltip={{ component: AchievTip, props: { a } }}>{@render icon(a, 48)}</div>
              {/each}
            </div>

            <h3>TIMELINE</h3>
            <ol class="timeline">
              {#each days as d (d.day)}
                <li>
                  <span class="day">{d.day}</span>
                  <ul>
                    {#each d.list as a (a.id)}
                      <li tabindex="0" use:tooltip={{ component: AchievTip, props: { a } }}>
                        {@render icon(a, 26)}
                        <span class="tn">{a.name}</span>
                        <button class="link where" onclick={() => pickSub(a.cat, a.subcat || 'Other')}>{a.cat}{a.subcat ? ` › ${a.subcat}` : ''}</button>
                        {#if a.completedByCharName}<span class="by">{charName(a.completedByCharName)}</span>{/if}
                        <span class="ap num">{a.points}</span>
                      </li>
                    {/each}
                  </ul>
                </li>
              {/each}
            </ol>
          {/if}
        </div>
      {:else}
        <div class="body">
          <div class="crumbs"><button class="link" onclick={() => pick(null)}>Summary</button> › <span>{cat.name}</span>{#if sub}{' '}› <span>{sub.name}</span>{/if}</div>
          {#if sub}
            <div class="subhead"><span class="sn">{sub.name}</span><span class="muted num">{sub.complete}/{sub.total} complete</span></div>
            {@render bar(sub.earnedPts, sub.totalPts, false)}
            <div class="items" role="list">
              {#each list as a (`${charId}_${a.id}`)}{@render row(a)}{:else}<p class="hint">No individual achievement data for this subcategory.</p>{/each}
            </div>
          {:else}
            <p class="hint">No achievements in this category.</p>
          {/if}
        </div>
      {/if}
    </section>
  </div>
{/if}

<style>
  /* Both columns scroll inside the page so the tab fits one screen. */
  .layout { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 14px; height: max(420px, calc(100dvh - 260px)); }
  @media (max-width: 760px) { .layout { grid-template-columns: minmax(0, 1fr); height: auto; } .side-nav { max-height: 260px; } }
  .side-nav, .pane { min-height: 0; background: var(--panel); border: 1px solid var(--line); }
  .side-nav { display: flex; flex-direction: column; }
  .filter { display: grid; gap: 4px; padding: 10px 12px; border-bottom: 1px solid var(--line); font: 600 11px var(--f-display); letter-spacing: 0.12em; color: var(--muted); }
  .filter input { padding: 4px 8px; font: 400 14px var(--f-ui); letter-spacing: 0; }
  .nav { flex: 1; min-height: 0; overflow-y: auto; padding: 4px 0; scrollbar-width: thin; }
  .cat { all: unset; box-sizing: border-box; display: flex; align-items: center; gap: 8px; width: 100%; padding: 4px 12px; cursor: pointer; transition: background 0.2s; }
  .cat:hover { background: #ffffff08; }
  .cat:hover .cn { color: var(--fg); }
  .cat:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: -1px; }
  .cat[aria-current='true'] .cn { color: var(--fg); }
  .cat[aria-current='true'] { background: linear-gradient(90deg, #ffffff14, transparent); }
  .ti { flex: none; width: 30px; height: 30px; display: grid; place-items: center; }
  .ti img { width: 30px; height: 30px; }
  .dot { width: 6px; height: 6px; transform: rotate(45deg); background: color-mix(in srgb, var(--accent) 60%, transparent); }
  .cn { flex: 1; font: 600 13px var(--f-display); letter-spacing: 0.04em; color: #c9c3b8; text-transform: uppercase; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; transition: color 0.2s; }
  .cp { font-size: 12px; color: var(--muted); }
  .subs { padding: 2px 0 6px 50px; display: grid; animation: fade 0.25s var(--ease-out); }
  .subn { all: unset; display: flex; justify-content: space-between; gap: 6px; padding: 2px 12px 2px 0; font-size: 14px; color: var(--muted); cursor: pointer; }
  .subn:hover, .subn[aria-current='true'] { color: var(--fg); }
  .subn.empty { opacity: 0.5; }
  .subn[aria-current='true'] span:first-child { text-decoration: underline; text-decoration-color: var(--accent); text-underline-offset: 3px; }
  .subn:focus-visible { outline: 1px solid var(--accent-hi); }
  .tick { color: var(--accent); }

  .pane { display: flex; flex-direction: column; min-width: 0; }
  .tools { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 18px; padding: 10px 18px; border-bottom: 1px solid var(--line); }
  h2 { font-size: 19px; letter-spacing: 0.14em; margin-right: auto; }
  .sel { display: flex; align-items: center; gap: 8px; font: 600 12px var(--f-display); letter-spacing: 0.12em; color: var(--muted); }
  .sel select { width: auto; padding: 4px 8px; }
  .pts { font-size: 15px; color: var(--muted); }
  .pts b { color: var(--fg); font-weight: 500; }
  .body { flex: 1; min-height: 0; overflow-y: auto; padding: 14px 18px 20px; animation: fade 0.35s var(--ease-out); }
  h3 { font-size: 13px; letter-spacing: 0.16em; margin: 20px 0 8px; }
  h3.first { margin-top: 0; }
  h3 .link { color: var(--accent-hi); }
  .link { all: unset; cursor: pointer; color: var(--muted); }
  .link:hover, .link:focus-visible { color: var(--fg); text-decoration: underline; }
  .crumbs { font-size: 13px; color: var(--muted); margin-bottom: 10px; }
  .crumbs span { color: var(--accent-hi); }
  .muted { color: var(--muted); font-size: 13px; }

  /* In-game bars: a teal fill with the count printed over it. */
  .bar { position: relative; display: block; height: 16px; background: #0b1114; border: 1px solid #3a4a52; box-shadow: inset 0 1px 3px #000; overflow: hidden; }
  .bar.big { height: 20px; }
  .fill { position: absolute; inset: 0 auto 0 0; background: linear-gradient(#9fe3f2, #4aa7c4 45%, #2f7f9d); box-shadow: 0 0 8px #5cc3e080; transition: width 0.8s var(--ease-out); }
  .bt { position: relative; display: block; text-align: center; font-size: 12px; line-height: 14px; color: #fff; text-shadow: 0 0 3px #000, 0 0 2px #000; }
  .big .bt { line-height: 18px; font-size: 13px; }
  .cats { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr)); gap: 10px 26px; margin-top: 16px; }
  .cg { all: unset; display: grid; gap: 3px; cursor: pointer; }
  .cg:hover .cgn, .cg:focus-visible .cgn { color: var(--accent-hi); }
  .cg:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: 3px; }
  .cgn { font: 600 12px var(--f-display); letter-spacing: 0.06em; transition: color 0.2s; }

  .recent { display: flex; flex-wrap: wrap; gap: 8px; }
  .ra { outline: none; animation: pop 0.45s var(--ease-spring) both; animation-delay: var(--d); }
  .ra:focus-visible .icon { outline: 1px solid var(--accent-hi); }
  .timeline { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
  .day { display: block; font: 600 12px var(--f-display); letter-spacing: 0.1em; color: var(--accent-hi); margin-bottom: 4px; }
  .timeline ul { list-style: none; margin: 0; padding: 0 0 0 10px; border-left: 1px solid var(--line); display: grid; gap: 2px; }
  .timeline ul li { display: flex; align-items: center; gap: 8px; padding: 2px 6px; font-size: 14px; outline: none; }
  .timeline ul li:hover, .timeline ul li:focus-visible { background: #ffffff08; }
  .tn { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .where { font-size: 12px; white-space: nowrap; }
  .by { font-size: 12px; color: var(--muted); white-space: nowrap; }
  .timeline .ap { margin-left: auto; }

  .subhead { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; margin-bottom: 4px; }
  .sn { font: 600 15px var(--f-display); letter-spacing: 0.04em; }
  .items { display: grid; gap: 4px; margin-top: 10px; }
  .ach { display: grid; grid-template-columns: auto 1fr auto; gap: 12px; padding: 8px 10px; outline: none; background: #00000040; border: 1px solid #ffffff0d; transition: background 0.15s, border-color 0.15s; }
  .ach:hover, .ach:focus-visible { background: #ffffff08; border-color: #ffffff1f; }
  .txt { min-width: 0; }
  .an { font: 600 14px var(--f-display); letter-spacing: 0.03em; color: var(--muted); }
  .ach.done .an { color: var(--fg); }
  .ad { margin: 2px 0 0; font-size: 13px; color: #a9a9a9; line-height: 1.3; }
  .side { display: grid; justify-items: end; align-content: start; gap: 2px; }
  .ap { font: 600 16px var(--f-display); color: var(--muted); }
  .ach.done .ap { color: var(--fg); }
  .date { font-size: 11px; color: var(--muted); white-space: nowrap; }
  .crit { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--muted); margin-top: 3px; }
  .crit span:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .icon { position: relative; display: grid; place-items: center; flex: none; overflow: hidden; border: 1px solid var(--line); background: #0b0a09; }
  .icon.done { border-color: color-mix(in srgb, var(--accent) 55%, transparent); }
  .icon img { position: absolute; inset: 0; width: 100%; height: 100%; }
  .icon:not(.done) img { filter: grayscale(0.8) brightness(0.6); }
  .star { color: #3a3226; font-size: 16px; }
  .center { text-align: center; }
  .err-box { display: grid; gap: 4px; padding: 12px 16px; border: 1px solid #e5675a66; background: #e5675a14; color: #f2c4bd; font-size: 14px; }
  .err-box b { font: 600 14px var(--f-display); letter-spacing: 0.06em; color: #ffd9d3; }
  @keyframes fade { from { opacity: 0; transform: translateY(6px); } }
  @keyframes pop { from { opacity: 0; transform: scale(0.7); } }
</style>
