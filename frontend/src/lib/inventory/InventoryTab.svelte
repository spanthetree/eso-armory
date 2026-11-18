<script>
  import ItemList from './ItemList.svelte';
  import { app } from '../store.svelte.js';

  /** Every item on the account: characters, bank, craft bag and house chests. */
  const items = $derived(app.data.value?.items ?? []);
  const characters = $derived(
    Object.values(app.data.value?.characters ?? {})
      .sort((a, b) => a.name.localeCompare(b.name))
      .map((c) => ({ v: c.id, l: c.name })),
  );
</script>

<ItemList {items} where="account" {characters} />
