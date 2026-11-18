<script>
  import Frame from '../ui/Frame.svelte';
  import Progress from '../ui/Progress.svelte';
  import AchievTip from '../tips/AchievTip.svelte';
  import { tooltip } from '../ui/tooltip.svelte.js';
  import { app } from '../store.svelte.js';
  import { buildIndex, achievementsIn, extraSubcats, pct, achievementIcon } from '../achievements.js';

  const data = $derived(app.achievements.value);
  const idx = $derived(buildIndex(data));
  const fmt = (/** @type {number} */ n) => (n ?? 0).toLocaleString('en-US');

  let charId = $state(/** @type {string | null} */ (null));
  $effect(() => {
    if (!charId && data?.chars?.length) charId = data.chars[0].id;
  });
  let search = $state('');
  /** null = summary */
  let catName = $state(/** @type {string | null} */ (null));
  const cat = $derived(data?.categories?.find((/** @type {any} */ c) => c.name === catName) ?? null);
  /** The category's own subcategories, then any extra ones its achievements are filed under. */
  const subcats = $derived(cat ? [...cat.subcats, ...extraSubcats(idx, cat, charId)] : []);
  /** Expanded subcategories in the open category. */
  let open = $state(/** @type {Set<string>} */ (new Set()));

  /** @param {string | null} name */
  function pick(name) {
    catName = name;
    open = new Set();
  }
  /** @param {string} sub */
  function toggle(sub) {
    const next = new Set(open);
    next.has(sub) ? next.delete(sub) : next.add(sub);
    open = next;
  }
  // While searching, every subcategory with a hit opens.
  const searching = $derived(search.trim().length > 0);
</script>

{#snippet icon(/** @type {any} */ a, /** @type {number} */ size)}
  {@const src = achievementIcon(a.icon)}
  <span class="icon" class:done={a.complete} style="width: {size}px; height: {size}px">
    <span class="star">★</span>
    {#if src}<img {src} alt="" loading="lazy" onerror={(e) => (/** @type {HTMLElement} */ (e.currentTarget).style.visibility = 'hidden')} />{/if}
  </span>
{/snippet}

{#if app.achievements.loading && !data}
  <Frame title="ACHIEVEMENTS"><p class="hint center">Loading achievements…</p></Frame>
{:else if app.achievements.error}
  <Frame title="ACHIEVEMENTS">
    <div class="err-box" role="alert"><b>User data not loaded</b><span>{app.achievements.error}</span></div>
  </Frame>
{:else if data}
  <div class="layout">
    <nav class="nav" aria-label="Achievement categories">
      <button class="cat" aria-current={catName === null} onclick={() => pick(null)}><span class="cn">SUMMARY</span></button>
      {#each data.categories as c (c.name)}
        <button class="cat" aria-current={catName === c.name} onclick={() => pick(c.name)}>
          <span class="cn">{c.name}</span><span class="cp num">{pct(c.earnedPts, c.totalPts)}%</span>
          <Progress value={c.earnedPts} max={c.totalPts} height={3} />
        </button>
      {/each}
    </nav>

    <section class="pane">
      <div class="tools">
        {#if data.chars?.length}
          <label class="sel"><span>CHARACTER</span>
            <select class="field" bind:value={charId}>
              {#each data.chars as c (c.id)}<option value={c.id}>{c.name}</option>{/each}
            </select>
          </label>
        {/if}
        <input class="field search" type="search" placeholder="Search achievements…" aria-label="Search achievements" bind:value={search} />
      </div>

      {#if !cat}
        <div class="body">
          <div class="head"><h2>SUMMARY</h2><span class="pts">Achievement points <b class="num">{fmt(data.earnedPts)} / {fmt(data.totalPts)}</b></span></div>
          <Progress value={data.earnedPts} max={data.totalPts} height={10} />

          {#if data.recent?.length}
            <h3>RECENT ACHIEVEMENTS</h3>
            <div class="recent">
              {#each data.recent as a, i (`${a.id}-${i}`)}
                <div class="ra" style="--d: {i * 0.04}s" tabindex="0" role="listitem" use:tooltip={{ component: AchievTip, props: { a } }}>
                  {@render icon(a, 52)}
                  <span class="rn">{a.name}</span>
                  <span class="rd">{a.completionDate}</span>
                </div>
              {/each}
            </div>
          {/if}

          <h3>CATEGORIES</h3>
          <div class="cats">
            {#each data.categories as c (c.name)}
              <button class="cg" onclick={() => pick(c.name)}>
                <span class="row"><span class="cgn">{c.name}</span><span class="num muted">{fmt(c.earnedPts)} / {fmt(c.totalPts)}</span></span>
                <Progress value={c.earnedPts} max={c.totalPts} height={7} />
              </button>
            {/each}
          </div>
        </div>
      {:else}
        <div class="body">
          <div class="crumbs"><button class="link" onclick={() => pick(null)}>Summary</button> › <span>{cat.name}</span></div>
          <div class="head">
            <h2>{cat.name.toUpperCase()}</h2>
            <span class="pts">
              <button class="link" onclick={() => (open = open.size ? new Set() : new Set(subcats.map((/** @type {any} */ s) => s.name)))}>
                {open.size ? '▼ Collapse all' : '▶ Expand all'}
              </button>
              <b class="num">{fmt(cat.earnedPts)} / {fmt(cat.totalPts)} pts</b>
            </span>
          </div>
          <Progress value={cat.earnedPts} max={cat.totalPts} height={8} />

          {#each subcats as sub (cat.name + '|' + (sub.key ?? sub.name))}
            {@const list = achievementsIn(idx, cat.name, sub.key ?? sub.name, charId, search)}
            {@const isOpen = open.has(sub.name) || (searching && list.length > 0)}
            {#if !searching || list.length}
              <div class="sub">
                <button class="subhead" aria-expanded={isOpen} onclick={() => toggle(sub.name)}>
                  <span class="sn">{sub.name}</span>
                  <span class="muted num">{fmt(sub.earnedPts)} / {fmt(sub.totalPts)} pts · {sub.complete}/{sub.total} <span class="chev">{isOpen ? '▼' : '▶'}</span></span>
                </button>
                <Progress value={sub.earnedPts} max={sub.totalPts} height={4} />
                {#if isOpen}
                  <div class="items">
                    {#each list as a (`${charId}_${a.id}`)}
                      <div class="ach" class:done={a.complete} tabindex="0" role="listitem" use:tooltip={{ component: AchievTip, props: { a } }}>
                        {@render icon(a, 38)}
                        <div class="txt">
                          <div class="row"><span class="an">{a.name}</span><span class="ap">{a.points}pt{a.complete ? ` · ${a.completionDate}` : ''}</span></div>
                          {#if a.desc}<p class="ad">{a.desc}</p>{/if}
                          {#if !a.complete && a.criteria?.length}
                            {#each a.criteria.slice(0, 3) as c, i (i)}
                              <div class="crit"><span>{c.desc}</span><span class="num">{c.cur}/{c.req}</span></div>
                              {#if c.req > 1}<Progress value={c.cur} max={c.req} height={3} />{/if}
                            {/each}
                          {/if}
                        </div>
                      </div>
                    {:else}
                      <p class="hint">No individual achievement data for this subcategory.</p>
                    {/each}
                  </div>
                {/if}
              </div>
            {/if}
          {/each}
        </div>
      {/if}
    </section>
  </div>
{/if}

<style>
  /* Both columns scroll inside the page so the tab fits one screen. */
  .layout { display: grid; grid-template-columns: 230px minmax(0, 1fr); gap: 14px; height: max(420px, calc(100dvh - 260px)); }
  @media (max-width: 760px) { .layout { grid-template-columns: minmax(0, 1fr); height: auto; } .nav { max-height: 220px; } }
  .nav, .pane { min-height: 0; background: var(--panel); border: 1px solid var(--line); }
  .nav { overflow-y: auto; }
  .pane { display: flex; flex-direction: column; min-width: 0; }
  .cat { all: unset; box-sizing: border-box; display: grid; grid-template-columns: 1fr auto; gap: 4px 8px; width: 100%; padding: 8px 14px; border-bottom: 1px solid #ffffff0a; cursor: pointer; transition: background 0.2s; }
  .cat :global(.track) { grid-column: 1 / -1; }
  .cat:hover { background: #ffffff08; }
  .cat:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: -1px; }
  .cat[aria-current='true'] { background: #ffffff0f; box-shadow: inset 2px 0 0 var(--accent); }
  .cn { font: 500 12px var(--f-display); letter-spacing: 0.08em; color: var(--fg); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .cp { font-size: 12px; color: var(--muted); }

  .tools { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 10px 16px; border-bottom: 1px solid var(--line); }
  .sel { display: flex; align-items: center; gap: 8px; font: 600 12px var(--f-display); letter-spacing: 0.12em; color: var(--muted); }
  .sel select { width: auto; padding: 4px 8px; }
  .search { margin-left: auto; width: min(280px, 100%); padding: 5px 10px; }
  .body { flex: 1; min-height: 0; overflow-y: auto; padding: 14px 18px 20px; animation: fade 0.35s var(--ease-out); }
  .head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 8px; margin-bottom: 6px; }
  h2 { font-size: 19px; letter-spacing: 0.14em; }
  h3 { font-size: 13px; letter-spacing: 0.16em; margin: 18px 0 10px; }
  .pts { display: flex; align-items: baseline; gap: 14px; font-size: 14px; color: var(--muted); }
  .pts b { color: var(--fg); font-weight: 500; }
  .link { all: unset; cursor: pointer; color: var(--muted); }
  .link:hover, .link:focus-visible { color: var(--fg); }
  .crumbs { font-size: 13px; color: var(--muted); margin-bottom: 8px; }
  .crumbs span { color: var(--accent-hi); }
  .muted { color: var(--muted); font-size: 13px; }

  .recent { display: flex; flex-wrap: wrap; gap: 12px; }
  .ra { width: 76px; display: grid; justify-items: center; gap: 3px; text-align: center; outline: none; animation: pop 0.45s var(--ease-spring) both; animation-delay: var(--d); }
  .ra:focus-visible .icon { outline: 1px solid var(--accent-hi); }
  .rn { font-size: 11px; line-height: 1.15; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .rd { font-size: 10px; color: var(--muted); }

  .cats { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 10px 22px; }
  .cg { all: unset; display: grid; gap: 3px; cursor: pointer; }
  .cg:hover .cgn, .cg:focus-visible .cgn { color: var(--accent-hi); }
  .cg:focus-visible { outline: 1px solid var(--accent-hi); outline-offset: 3px; }
  .row { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
  .cgn { font: 500 12px var(--f-display); letter-spacing: 0.08em; transition: color 0.2s; }

  .sub { margin-top: 14px; }
  .subhead { all: unset; box-sizing: border-box; display: flex; justify-content: space-between; gap: 10px; width: 100%; padding-bottom: 4px; cursor: pointer; }
  .subhead:focus-visible { outline: 1px solid var(--accent-hi); }
  .sn { font: 600 14px var(--f-display); letter-spacing: 0.04em; }
  .subhead:hover .sn { color: var(--accent-hi); }
  .chev { display: inline-block; width: 14px; text-align: center; }
  .items { display: grid; gap: 2px; margin-top: 6px; animation: fade 0.3s var(--ease-out); }
  .ach { display: grid; grid-template-columns: auto 1fr; gap: 10px; padding: 6px 8px; outline: none; transition: background 0.15s; }
  .ach:hover, .ach:focus-visible { background: #ffffff08; }
  .ach.done { background: #ffffff05; }
  .txt { min-width: 0; }
  .an { font-size: 14px; color: var(--muted); }
  .ach.done .an { color: var(--accent-hi); }
  .ap { font-size: 11px; color: var(--muted); white-space: nowrap; }
  .ad { margin: 1px 0 0; font-size: 12px; color: #a9a9a9; line-height: 1.3; }
  .crit { display: flex; justify-content: space-between; gap: 8px; font-size: 11px; color: var(--muted); margin-top: 3px; }
  .crit span:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .icon { position: relative; display: grid; place-items: center; flex: none; overflow: hidden; border: 1px solid var(--line); background: #0b0a09; }
  .icon.done { border-color: color-mix(in srgb, var(--accent) 55%, transparent); box-shadow: 0 0 10px -4px var(--accent); }
  .icon img { position: absolute; inset: 0; width: 100%; height: 100%; }
  .icon:not(.done) img { filter: grayscale(0.7) brightness(0.65); }
  .star { color: #3a3226; font-size: 18px; }
  .center { text-align: center; }
  .err-box { display: grid; gap: 4px; padding: 12px 16px; border: 1px solid #e5675a66; background: #e5675a14; color: #f2c4bd; font-size: 14px; }
  .err-box b { font: 600 14px var(--f-display); letter-spacing: 0.06em; color: #ffd9d3; }
  @keyframes fade { from { opacity: 0; transform: translateY(6px); } }
  @keyframes pop { from { opacity: 0; transform: scale(0.7); } }
</style>
