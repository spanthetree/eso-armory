<script>
  /** A name, an optional heading line and a description (mundus stones, champion stars). @type {{ name: string, head?: string, desc?: string }} */
  let { name, head = '', desc = '' } = $props();
</script>

{#if head}<div class="t-head"><span>{head}</span></div>{/if}
<div class="t-name">{name}</div>
{#if desc}<div class="t-small">{desc}</div>{:else}<div class="t-faint">Description needs a newer iasync: log in to this character, then upload again.</div>{/if}

<style>
  .t-small { white-space: pre-line; max-width: 340px; }
</style>
