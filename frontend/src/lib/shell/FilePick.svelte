<script>
  /**
   * One .lua file picker: click to choose or drop a file onto it.
   * @type {{ id: string, file: File | null, placeholder: string }}
   */
  let { id, file = $bindable(), placeholder } = $props();
  let over = $state(false);
</script>

<label
  class="pick"
  class:over
  class:has={!!file}
  for={id}
  ondragover={(e) => { e.preventDefault(); over = true; }}
  ondragleave={() => (over = false)}
  ondrop={(e) => { e.preventDefault(); over = false; file = e.dataTransfer?.files?.[0] ?? null; }}>
  <span class="ic">📄</span>
  <span class="nm">{file?.name || placeholder}</span>
  <input {id} type="file" accept=".lua" onchange={(e) => (file = /** @type {HTMLInputElement} */ (e.currentTarget).files?.[0] ?? null)} />
</label>

<style>
  .pick { position: relative; display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1px dashed var(--line); background: #00000066; cursor: pointer; transition: border-color 0.2s; }
  .pick:hover, .pick.over, .pick:focus-within { border-color: var(--accent); }
  .pick.has { border-style: solid; }
  .nm { font-size: 14px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .has .nm { color: var(--fg); }
  input { position: absolute; width: 1px; height: 1px; opacity: 0; }
</style>
