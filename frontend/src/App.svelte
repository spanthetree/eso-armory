<script>
  import Currencies from './lib/shell/Currencies.svelte';
  import { app, start } from './lib/store.svelte.js';
  import { restoreFolder } from './lib/upload.svelte.js';
  import { nav, go, TABS } from './lib/nav.svelte.js';
  import Tabs from './lib/ui/Tabs.svelte';
  import HeroEmblems from './lib/ui/HeroEmblems.svelte';
  import TooltipHost from './lib/ui/TooltipHost.svelte';
  import TopBar from './lib/shell/TopBar.svelte';
  import Toast from './lib/shell/Toast.svelte';
  import Welcome from './lib/shell/Welcome.svelte';
  import Roster from './lib/shell/Roster.svelte';
  import CharacterSheet from './lib/character/CharacterSheet.svelte';
  import Wardrobe from './lib/character/Wardrobe.svelte';
  import Bags from './lib/character/Bags.svelte';
  import Compare from './lib/character/Compare.svelte';
  import Superstar from './lib/character/Superstar.svelte';
  import InventoryTab from './lib/inventory/InventoryTab.svelte';
  import AchievementsTab from './lib/achievements/AchievementsTab.svelte';
  import CollectionsTab from './lib/collections/CollectionsTab.svelte';
  import AchievementsSimple from './lib/achievements/AchievementsSimple.svelte';
  import CollectionsSimple from './lib/collections/CollectionsSimple.svelte';
  import CollectiblesBook from './lib/collections/CollectiblesBook.svelte';
  import { BOOKS } from './lib/collections.js';
  import { ui } from './lib/uimode.svelte.js';
  import { applyUiColors } from './lib/eso/tex.js';
  import Segmented from './lib/ui/Segmented.svelte';
  import ShareDialog from './lib/shell/ShareDialog.svelte';
  import PasswordDialog from './lib/shell/PasswordDialog.svelte';
  import UploadDialog from './lib/shell/UploadDialog.svelte';

  start().then(restoreFolder);

  const data = $derived(app.data.value);
  $effect(() => applyUiColors(data?.uiColors));
  const char = $derived(nav.charId ? data?.characters?.[nav.charId] ?? null : null);

  const CHAR_VIEW_ITEMS = [
    { id: 'sheet', label: 'Sheet', icon: 'inventory/inventory_tabicon_armor' },
    { id: 'wardrobe', label: 'Wardrobe', icon: 'inventory/inventory_tabicon_appearance' },
    { id: 'bags', label: 'Bags', icon: 'inventory/inventory_tabicon_items' },
    { id: 'compare', label: 'Compare', icon: 'inventory/inventory_tabicon_quickslot' },
    { id: 'superstar', label: 'SuperStar', icon: 'mainmenu/menubar_skills' },
  ];

  const TAB_ITEMS = [
    { id: 'characters', label: 'Characters', icon: 'character' },
    { id: 'inventory', label: 'Inventory', icon: 'inventory' },
    { id: 'achievements', label: 'Achievements', icon: 'journal' },
    { id: 'collections', label: 'Collections', icon: 'collections' },
  ];

  // Collections book tab: as linked, else Collectibles once iasync 1.9.0 data is there, else Set Items.
  const book = $derived(nav.book ?? (app.stickerbook.value?.collectibles?.categories?.length ? 'collectibles' : 'sets'));
  const bookInfo = $derived(BOOKS.find((b) => b.id === book) ?? BOOKS[0]);

  // Slide tab content in from the side you moved towards.
  let dir = $state('');
  let prevIndex = TABS.indexOf(nav.tab);
  $effect(() => {
    const i = TABS.indexOf(nav.tab);
    dir = i > prevIndex ? 'from-r' : i < prevIndex ? 'from-l' : '';
    prevIndex = i;
  });
</script>

<TooltipHost />
<Toast />
<ShareDialog />
<PasswordDialog />
<UploadDialog />

<TopBar />

{#if !app.ready}
  <div class="splash" role="status">
    <div class="sigil">◆</div>
    <p>{app.waking ? 'The server is waking up…' : 'Loading the Armory…'}</p>
  </div>
{:else if !data}
  <main><Welcome /></main>
{:else}
  <div class="stage">
    <main>
      <header class="hero">
        {#if char}
          <HeroEmblems cls={char.class} alliance={char.alliance} />
          <div class="herobar">
            <button class="back" onclick={() => go('characters')}>‹ All characters</button>
          </div>
          <div class="sub">{[char.race, char.class, char.alliance].filter(Boolean).join(' · ')}</div>
          <h1>{char.name}</h1>
        {:else}
          <div class="sub">{data.meta.server} · {data.meta.character_count} characters</div>
          <h1 class="acct">{data.meta.account}</h1>
          <Currencies />
          <div class="orn" aria-hidden="true">◆</div>
        {/if}
      </header>

      <div class="tabrow">
        <Tabs items={TAB_ITEMS} active={nav.tab} onchange={(id) => go(/** @type {any} */ (id))} />
        {#if nav.tab === 'characters' && char}
          <div class="subbar"><Segmented label="Character view" options={CHAR_VIEW_ITEMS} value={nav.charView} showLabel={false} onchange={(v) => go('characters', char.id, /** @type {any} */ (v))} /></div>
        {:else if nav.tab === 'collections'}
          <div class="subbar"><Segmented label="Collections book" options={BOOKS} value={book} showLabel={false} onchange={(v) => go('collections', null, 'sheet', /** @type {any} */ (v))} /></div>
        {/if}
      </div>

      {#key `${nav.tab}/${nav.charId ?? ''}/${nav.charView}/${nav.tab === 'collections' ? book : ''}`}
        <section class="pane {dir}">
          {#if nav.tab === 'characters' && !char}
            <Roster />
          {:else if nav.tab === 'characters' && nav.charView === 'wardrobe'}
            <Wardrobe {char} />
          {:else if nav.tab === 'characters' && nav.charView === 'bags'}
            <Bags {char} />
          {:else if nav.tab === 'characters' && nav.charView === 'compare'}
            <Compare {char} />
          {:else if nav.tab === 'characters' && nav.charView === 'superstar'}
            <Superstar {char} />
          {:else if nav.tab === 'characters'}
            <CharacterSheet {char} />
          {:else if nav.tab === 'inventory'}
            <InventoryTab />
          {:else if nav.tab === 'achievements'}
            {#if ui.mode === 'classic'}<AchievementsTab />{:else}<AchievementsSimple />{/if}
          {:else if nav.tab === 'collections'}
            {#if book !== 'sets'}<CollectiblesBook book={bookInfo} />{:else if ui.mode === 'classic'}<CollectionsTab />{:else}<CollectionsSimple />{/if}
          {/if}
        </section>
      {/key}
    </main>
  </div>
{/if}

<footer class="legal">
  Fan-made and not affiliated with or endorsed by ZeniMax Online Studios, Bethesda or Microsoft. The Elder Scrolls Online, its names and its art are trademarks and copyright of ZeniMax Media Inc.
</footer>

<style>
  .stage { position: relative; isolation: isolate; }
  /* Character views and Collections books: their own row under the main tabs. */
  .subbar { display: flex; justify-content: center; margin-top: 0; }
  .legal { max-width: 1240px; margin: 0 auto; padding: 0 16px 8px; text-align: center; font-size: 11px; line-height: 1.3; color: var(--muted); opacity: 0.7; }
  main { max-width: 1240px; margin: 0 auto; padding: 12px max(16px, env(safe-area-inset-right, 0px)) 6px max(16px, env(safe-area-inset-left, 0px)); display: grid; grid-template-columns: minmax(0, 1fr); gap: 10px; }
  .hero { position: relative; isolation: isolate; text-align: center; display: grid; gap: 2px; padding-top: 4px; }
  .hero h1 { color: var(--fg); font-size: clamp(24px, 3.4vw, 34px); letter-spacing: 0.12em; text-shadow: 0 0 18px #ffffff26; text-wrap: balance; }
  .sub { color: var(--muted); text-transform: uppercase; letter-spacing: 0.2em; font-size: 13px; }
  .orn { display: flex; align-items: center; justify-content: center; gap: 10px; color: var(--accent); font-size: 12px; }
  .orn::before, .orn::after { content: ''; width: 90px; height: 1px; background: linear-gradient(90deg, transparent, var(--accent)); }
  .orn::after { transform: scaleX(-1); }
  /* The back link sits in the hero's corner; the view switcher has its own row under the tabs. */
  .herobar { position: absolute; left: 0; top: 4px; z-index: 1; }
  .back { all: unset; cursor: pointer; font-size: 14px; color: var(--muted); }
  .back:hover, .back:focus-visible { color: var(--fg); }
  .pane { animation: pane 0.45s var(--ease-out) both; }
  .pane.from-l { --dx: -40px; }
  .pane.from-r { --dx: 40px; }
  @keyframes pane { from { opacity: 0; transform: translateX(var(--dx, 0)); filter: blur(3px); } }
  .todo { text-align: center; margin: 8px 0; }
  .splash { min-height: 60vh; display: grid; place-content: center; text-align: center; gap: 10px; }
  .sigil { font-size: 30px; color: var(--accent); animation: pulse 1.6s ease-in-out infinite; }
  .splash p { font: 500 17px var(--f-display); letter-spacing: 0.12em; color: var(--fg); margin: 0; }
  @keyframes pulse { 50% { opacity: 0.35; transform: scale(0.85); } }
  /* Classic: ZO_PanelTitle (ZoFontWindowTitle, uppercase) with the dynamic divider; no ornament. */
  :global(:root[data-ui='classic']) .hero h1 { position: relative; font: 700 30px/1.1 var(--eso-font); letter-spacing: 0; text-transform: uppercase; text-shadow: var(--eso-shadow); padding-bottom: 8px; }
  :global(:root[data-ui='classic']) .hero h1::after { content: ''; position: absolute; left: 50%; bottom: 0; width: min(560px, 90%); height: 6px; transform: translateX(-50%);
    background: var(--eso-divider-l) left / 56px 6px no-repeat, var(--eso-divider-r) right / 56px 6px no-repeat, var(--eso-divider-m) center / calc(100% - 112px) 6px no-repeat; }
  :global(:root[data-ui='classic']) .sub { font: 700 16px var(--eso-font); letter-spacing: 0; color: var(--eso-normal); }
  /* Account view: the divider goes under the currencies (on .orn) instead of under the name. */
  :global(:root[data-ui='classic']) .hero h1.acct { padding-bottom: 0; }
  :global(:root[data-ui='classic']) .hero h1.acct::after { display: none; }
  :global(:root[data-ui='classic']) .orn { display: block; justify-self: center; width: min(560px, 90%); height: 6px; margin-top: 4px; font-size: 0;
    background: var(--eso-divider-l) left / 56px 6px no-repeat, var(--eso-divider-r) right / 56px 6px no-repeat, var(--eso-divider-m) center / calc(100% - 112px) 6px no-repeat; }
  :global(:root[data-ui='classic']) .orn::before, :global(:root[data-ui='classic']) .orn::after { display: none; }
  :global(:root[data-ui='classic']) .back { font: 700 18px var(--eso-font); color: var(--eso-normal); text-shadow: var(--eso-shadow); }
  :global(:root[data-ui='classic']) .back:hover, :global(:root[data-ui='classic']) .back:focus-visible { color: var(--eso-highlight); }
  :global(:root[data-ui='classic']) .splash p { font: 700 20px var(--eso-font); letter-spacing: 0; text-transform: uppercase; }
  :global(:root[data-ui='classic']) .sigil { color: var(--eso-normal); }
</style>
