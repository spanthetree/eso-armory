<script>
  import Frame from '../ui/Frame.svelte';
  import Bar from '../ui/Bar.svelte';
  import { TRAIT_GROUPS } from '../items.js';
  import { gameIcon } from '../achievements.js';
  import { timeLeft } from '../time.js';

  /** Crafting knowledge iasync 1.11.0 records per character: trait research, motifs, recipes. @type {{ char: any }} */
  let { char } = $props();

  const TRAITS = new Map(TRAIT_GROUPS.flatMap((g) => g.options.map((o) => [Number(o.v), o.l])));
  const CRAFTS = [['blacksmithing', 'Blacksmithing'], ['clothier', 'Clothing'], ['woodworking', 'Woodworking'], ['jewelrycrafting', 'Jewelry Crafting']];
  // The Lore Library's misc "Crafting Books" collection isn't a motif; it goes last, apart.
  const motifs = $derived((char.motifs ?? []).filter((/** @type {any} */ m) => m.name !== 'Crafting Books'));
  const books = $derived((char.motifs ?? []).find((/** @type {any} */ m) => m.name === 'Crafting Books'));
  const motifTotals = $derived(motifs.reduce((t, m) => ({ known: t.known + m.known, total: t.total + m.total }), { known: 0, total: 0 }));
  const recipeTotals = $derived((char.recipes ?? []).reduce((t, r) => ({ known: t.known + r.known.length, total: t.total + r.total }), { known: 0, total: 0 }));
  let open = $state(/** @type {string | null} */ (null));
  const toggle = (/** @type {string} */ k) => (open = open === k ? null : k);
  const fmt = (/** @type {number} */ n) => n.toLocaleString('en-US');
</script>

{#if !char.level}
  <Frame title="CRAFTING"><p class="hint none">No crafting data for {char.name} yet: it needs iasync 1.11.0 and a login on this character.</p></Frame>
{:else}
  <div class="craft">
    <Frame title="RESEARCH">
      <div class="scroll">
        {#each CRAFTS as [key, label] (key)}
          {@const lines = char.research?.[key] ?? []}
          {#if lines.length}
            {@const known = lines.reduce((/** @type {number} */ s, /** @type {any} */ l) => s + l.known.length, 0)}
            {@const total = lines.reduce((/** @type {number} */ s, /** @type {any} */ l) => s + l.numTraits, 0)}
            <h6>{label} <span class="num dim">{known}/{total}</span></h6>
            {#each lines as l (l.name)}
              <div class="line" class:done={l.known.length >= l.numTraits}>
                {#if gameIcon(l.icon)}<img src={gameIcon(l.icon)} alt="" />{/if}
                <span class="ln">{l.name}</span>
                <span class="dots" title={l.known.map((/** @type {number} */ t) => TRAITS.get(t) ?? `Trait ${t}`).join(', ') || 'No traits known'}>
                  {#each { length: l.numTraits } as _, i (i)}<i class:on={i < l.known.length}></i>{/each}
                </span>
                <span class="num dim">{l.known.length}/{l.numTraits}</span>
              </div>
              {#each l.researching as r (r.trait)}
                <div class="busy">{`Researching ${TRAITS.get(r.trait) ?? `trait ${r.trait}`} · ${timeLeft(r.endTime) ? `${timeLeft(r.endTime)} left` : 'done'}`}</div>
              {/each}
            {/each}
          {/if}
        {/each}
      </div>
    </Frame>

    <Frame title="MOTIFS">
      <div class="sum"><span>Chapters known</span><span class="num">{fmt(motifTotals.known)} / {fmt(motifTotals.total)}</span></div>
      <div class="scroll">
        {#each [...motifs, ...(books ? [books] : [])] as m (m.id)}
          <button class="item" class:misc={m === books} aria-expanded={open === `m${m.id}`} onclick={() => toggle(`m${m.id}`)}>
            <span class="in">{m.name}</span><span class="num dim">{m.known}/{m.total}</span>
          </button>
          {#if open === `m${m.id}`}
            <ul class="sub">{#each m.books as b, i (i)}<li class:off={!b.known}>{b.title}</li>{/each}</ul>
          {/if}
        {/each}
      </div>
    </Frame>

    <Frame title="RECIPES">
      <div class="sum"><span>Recipes known</span><span class="num">{fmt(recipeTotals.known)} / {fmt(recipeTotals.total)}</span></div>
      <Bar value={recipeTotals.known} max={recipeTotals.total} label="Recipes known" />
      <div class="scroll short">
        {#each char.recipes ?? [] as r, i (i)}
          <button class="item" aria-expanded={open === `r${i}`} onclick={() => toggle(`r${i}`)}>
            <span class="in">{r.name}</span><span class="num dim">{r.known.length}/{r.total}</span>
          </button>
          {#if open === `r${i}`}
            <ul class="sub">{#each r.known as n (n)}<li>{n}</li>{:else}<li class="off">None known</li>{/each}</ul>
          {/if}
        {/each}
      </div>
    </Frame>
  </div>
{/if}

<style>
  .craft { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; align-items: start; }
  @media (max-width: 980px) { .craft { grid-template-columns: minmax(0, 1fr); } }
  .scroll { max-height: max(300px, calc(100dvh - 400px)); overflow-y: auto; margin-top: 6px; padding-right: 4px; }
  .scroll.short { max-height: max(260px, calc(100dvh - 430px)); }
  h6 { display: flex; justify-content: space-between; margin: 10px 0 4px; font-size: 14px; letter-spacing: 0.08em; color: var(--fg); text-transform: uppercase; }
  h6:first-child { margin-top: 0; }
  .line { display: grid; grid-template-columns: 26px minmax(0, 1fr) auto auto; align-items: center; gap: 8px; padding: 2px 4px; font-size: 14px; }
  .line img { width: 26px; height: 26px; }
  .line.done .ln { color: var(--accent-hi); }
  .ln { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .dots { display: flex; gap: 2px; }
  .dots i { width: 6px; height: 6px; transform: rotate(45deg); border: 1px solid var(--muted); }
  .dots i.on { background: var(--accent-hi); border-color: var(--accent-hi); }
  .busy { margin: 0 0 3px 38px; font-size: 13px; color: var(--accent-hi); }
  .dim { color: var(--muted); }
  .sum { display: flex; justify-content: space-between; font-size: 14px; color: var(--muted); margin-bottom: 4px; }
  .item { all: unset; box-sizing: border-box; display: flex; justify-content: space-between; gap: 8px; width: 100%; padding: 3px 6px; font-size: 14px; cursor: pointer; }
  .item:hover, .item:focus-visible { background: #ffffff0a; }
  .item[aria-expanded='true'] .in { color: var(--accent-hi); }
  .item.misc { margin-top: 8px; border-top: 1px solid var(--line); }
  .sub { margin: 0 0 6px; padding: 0 0 0 18px; display: grid; gap: 1px; font-size: 13px; list-style: none; }
  .sub li.off { color: var(--muted); opacity: 0.6; }
  .none { text-align: center; margin: 4px 0; }
  /* Classic: list rows and the game's text colours. */
  :global(:root[data-ui='classic']) .item, :global(:root[data-ui='classic']) .line { font: 500 16px var(--eso-font-medium); color: var(--eso-selected); }
  :global(:root[data-ui='classic']) .item:hover, :global(:root[data-ui='classic']) .item:focus-visible { background: var(--eso-hover) 0 0 / 100% 100%; }
  :global(:root[data-ui='classic']) h6 { font: 700 18px var(--eso-font); color: var(--eso-selected); letter-spacing: 0; }
  :global(:root[data-ui='classic']) .dim, :global(:root[data-ui='classic']) .sum { color: var(--eso-normal); }
  :global(:root[data-ui='classic']) .sub { font: 500 15px var(--eso-font-medium); color: var(--eso-selected); }
</style>
