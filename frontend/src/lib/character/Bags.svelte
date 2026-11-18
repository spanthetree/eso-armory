<script>
  import ItemList from '../inventory/ItemList.svelte';
  import { app } from '../store.svelte.js';
  import { forCharacter } from '../items.js';

  /** One character's equipped and backpack items. @type {{ char: any }} */
  let { char } = $props();

  const items = $derived(forCharacter(app.data.value?.items, char.id));
</script>

<ItemList {items} where="bags" placeholder="Search {char.name}'s items…" />
