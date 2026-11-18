// Set collection (stickerbook) grouping. Ported from the classic sbCategorySummary / sbSetsInSubcat.

/** Per-category collected/total, alphabetical. @param {any[]} sets */
export function categorySummary(sets) {
  /** @type {Map<string, { name: string, collected: number, total: number }>} */
  const by = new Map();
  for (const s of sets ?? []) {
    const name = s.category || 'Unknown';
    const c = by.get(name) ?? by.set(name, { name, collected: 0, total: 0 }).get(name);
    c.collected += s.numCollected;
    c.total += s.numTotal;
  }
  return [...by.values()].sort((a, b) => a.name.localeCompare(b.name));
}

/** Account-wide totals. @param {any[]} sets */
export function totals(sets) {
  return (sets ?? []).reduce((t, s) => ({ collected: t.collected + s.numCollected, total: t.total + s.numTotal }), { collected: 0, total: 0 });
}

/**
 * A category's sets in sections: sets without a subcategory first (heading ''), then each subcategory A-Z.
 * @param {any[]} sets @param {string} category
 */
export function sections(sets, category) {
  const inCat = (sets ?? []).filter((s) => (s.category || 'Unknown') === category);
  const subs = [...new Set(inCat.map((s) => s.subcategory).filter(Boolean))].sort();
  return [
    { heading: '', sets: inCat.filter((s) => !s.subcategory) },
    ...subs.map((sub) => ({ heading: sub, sets: inCat.filter((s) => s.subcategory === sub) })),
  ].filter((g) => g.sets.length);
}

/** Sets whose name contains the query. @param {any[]} sets @param {string} q */
export function searchSets(sets, q) {
  const needle = q.toLowerCase().trim();
  return needle ? (sets ?? []).filter((s) => s.name.toLowerCase().includes(needle)) : [];
}
