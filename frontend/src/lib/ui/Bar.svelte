<script>
  /** Progress bar in the current look: the game's arrow bar in Classic, the teal count bar in Simple. */
  import EsoBar from '../eso/EsoBar.svelte';
  import CountBar from './CountBar.svelte';
  import { ui } from '../uimode.svelte.js';
  /** @type {{ value: number, max: number, label?: string }} */
  let { value, max, label } = $props();
</script>

{#if ui.mode === 'classic'}<EsoBar {value} {max} {label} />{:else}<CountBar {value} {max} {label} />{/if}
