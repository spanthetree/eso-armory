<script>
  import { allianceKey, setAllianceTint } from './lib/eso.js';
  import { app, start } from './lib/store.svelte.js';
  import { nav, go, TABS } from './lib/nav.svelte.js';
  import Tabs from './lib/ui/Tabs.svelte';
  import Frame from './lib/ui/Frame.svelte';
  import HeroEmblems from './lib/ui/HeroEmblems.svelte';
  import TooltipHost from './lib/ui/TooltipHost.svelte';
  import TopBar from './lib/shell/TopBar.svelte';
  import Toast from './lib/shell/Toast.svelte';
  import Welcome from './lib/shell/Welcome.svelte';
  import Roster from './lib/shell/Roster.svelte';
  import ShareDialog from './lib/shell/ShareDialog.svelte';
  import PasswordDialog from './lib/shell/PasswordDialog.svelte';
  import UploadDialog from './lib/shell/UploadDialog.svelte';

  start();

  const data = $derived(app.data.value);
  const char = $derived(nav.charId ? data?.characters?.[nav.charId] ?? null : null);

  // Alliance tint: the viewer's manual choice wins; AUTO ('') follows the selected character.
  const PREF_KEY = 'eso-alliance';
  let pref = $state(/** @type {'' | 'ad' | 'dc' | 'ep'} */ (readPref()));
  function readPref() {
    try {
      const v = localStorage.getItem(PREF_KEY);
      return v === 'ad' || v === 'dc' || v === 'ep' ? v : '';
    } catch {
      return '';
    }
  }
  $effect(() => {
    try {
      localStorage.setItem(PREF_KEY, pref);
    } catch {
      // storage blocked: preference lasts for this visit only
    }
  });
  $effect(() => setAllianceTint(pref || allianceKey(char?.alliance) || 'ad'));

  const TAB_ITEMS = [
    { id: 'characters', label: 'Characters' },
    { id: 'inventory', label: 'Inventory' },
    { id: 'achievements', label: 'Achievements' },
    { id: 'collections', label: 'Collections' },
  ];

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

<TopBar bind:alliance={pref} />

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
          <button class="back" onclick={() => go('characters')}>‹ All characters</button>
          <div class="sub">{[char.race, char.class, char.alliance].filter(Boolean).join(' · ')}</div>
          <h1>{char.name}</h1>
        {:else}
          <div class="sub">{data.meta.server} · {data.meta.character_count} characters</div>
          <h1>{data.meta.account}</h1>
        {/if}
        <div class="orn" aria-hidden="true">◆</div>
      </header>

      <Tabs items={TAB_ITEMS} active={nav.tab} onchange={(id) => go(/** @type {any} */ (id))} />

      {#key `${nav.tab}/${nav.charId ?? ''}`}
        <section class="pane {dir}">
          {#if nav.tab === 'characters' && !char}
            <Roster />
          {:else if nav.tab === 'characters'}
            <Frame title="CHARACTER SHEET"><p class="hint todo">Equipment, attributes and builds for {char?.name} arrive in Phase 3.</p></Frame>
          {:else}
            <Frame title={TAB_ITEMS.find((t) => t.id === nav.tab)?.label.toUpperCase()}>
              <p class="hint todo">This tab is ported in Phase 3.</p>
            </Frame>
          {/if}
        </section>
      {/key}
    </main>
  </div>
{/if}

<style>
  .stage { position: relative; isolation: isolate; }
  main { max-width: 1240px; margin: 0 auto; padding: 22px max(16px, env(safe-area-inset-right, 0px)) 64px max(16px, env(safe-area-inset-left, 0px)); display: grid; gap: 18px; }
  .hero { position: relative; isolation: isolate; text-align: center; display: grid; gap: 4px; padding-top: 10px; }
  .hero h1 { color: var(--accent-hi); font-size: clamp(26px, 4vw, 38px); letter-spacing: 0.12em; text-shadow: 0 0 18px color-mix(in srgb, var(--accent) 40%, transparent); text-wrap: balance; }
  .sub { color: var(--muted); text-transform: uppercase; letter-spacing: 0.2em; font-size: 13px; }
  .orn { display: flex; align-items: center; justify-content: center; gap: 10px; color: var(--accent); font-size: 12px; }
  .orn::before, .orn::after { content: ''; width: 90px; height: 1px; background: linear-gradient(90deg, transparent, var(--accent)); }
  .orn::after { transform: scaleX(-1); }
  .back { all: unset; justify-self: center; cursor: pointer; font-size: 14px; color: var(--muted); margin-bottom: 4px; }
  .back:hover, .back:focus-visible { color: var(--fg); }
  .pane { animation: pane 0.45s var(--ease-out) both; }
  .pane.from-l { --dx: -40px; }
  .pane.from-r { --dx: 40px; }
  @keyframes pane { from { opacity: 0; transform: translateX(var(--dx, 0)); filter: blur(3px); } }
  .todo { text-align: center; margin: 8px 0; }
  .splash { min-height: 60vh; display: grid; place-content: center; text-align: center; gap: 10px; }
  .sigil { font-size: 30px; color: var(--accent); animation: pulse 1.6s ease-in-out infinite; }
  .splash p { font: 500 17px var(--f-display); letter-spacing: 0.12em; color: var(--accent-hi); margin: 0; }
  @keyframes pulse { 50% { opacity: 0.35; transform: scale(0.85); } }
</style>
