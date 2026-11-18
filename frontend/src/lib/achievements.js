// Achievement indexing. Account-wide achievements live in account_items; character-specific ones in
// items_by_char. A subcategory shows both, deduped by id with the character's copy winning
// (ported from the classic achievItemsByCatSubcat).

/** @param {any[]} list */
function index(list) {
  /** @type {Map<string, any[]>} */
  const m = new Map();
  for (const a of list ?? []) {
    const key = `${a.cat ?? ''}||${a.subcat ?? ''}`;
    (m.get(key) ?? m.set(key, []).get(key)).push(a);
  }
  return m;
}

/** @param {any} data /api/achievements payload */
export function buildIndex(data) {
  return {
    account: index(data?.account_items),
    byChar: new Map(Object.entries(data?.items_by_char ?? {}).map(([id, list]) => [id, index(/** @type {any[]} */ (list))])),
  };
}

/**
 * Achievements in one subcategory for one character, filtered by a search over name and description.
 * @param {ReturnType<typeof buildIndex>} idx
 * @param {string} cat @param {string} subcat @param {string | null} charId @param {string} [search]
 */
export function achievementsIn(idx, cat, subcat, charId, search = '') {
  const key = `${cat ?? ''}||${subcat ?? ''}`;
  const merged = new Map();
  for (const a of idx.account.get(key) ?? []) merged.set(a.id, a);
  for (const a of (charId && idx.byChar.get(charId)?.get(key)) || []) merged.set(a.id, a);
  const q = search.toLowerCase().trim();
  const list = [...merged.values()];
  return q ? list.filter((a) => `${a.name ?? ''}\n${a.desc ?? ''}`.toLowerCase().includes(q)) : list;
}

/** Earned share as a whole percent. @param {number} earned @param {number} total */
export const pct = (earned, total) => (total ? Math.round((earned / total) * 100) : 0);

/** "/esoui/art/icons/foo.dds" -> "/esoicons/foo.png" (served and cached by the server); null otherwise. @param {string} icon */
export function achievementIcon(icon) {
  const m = /^\/esoui\/art\/icons\/([a-z0-9_]+)\.dds$/i.exec(icon ?? '');
  return m ? `/esoicons/${m[1].toLowerCase()}.png` : null;
}

/**
 * Subcategories that have achievements but aren't in the category's own subcategory list (iasync files
 * e.g. dungeon achievements under "Group Dungeons" while the list names each dungeon). Totals are
 * computed from the achievements, so nothing is silently hidden.
 * @param {ReturnType<typeof buildIndex>} idx @param {any} cat @param {string | null} charId
 */
export function extraSubcats(idx, cat, charId) {
  const known = new Set((cat.subcats ?? []).map((/** @type {any} */ s) => s.name));
  const names = new Set();
  for (const m of [idx.account, charId ? idx.byChar.get(charId) : undefined]) {
    for (const key of m?.keys() ?? []) {
      const [c, sub] = key.split('||');
      if (c === cat.name && !known.has(sub)) names.add(sub);
    }
  }
  return [...names].sort().map((name) => {
    const list = achievementsIn(idx, cat.name, name, charId);
    const done = list.filter((a) => a.complete);
    return {
      name: name || 'Other',
      key: name,
      total: list.length,
      complete: done.length,
      totalPts: list.reduce((s, a) => s + (a.points || 0), 0),
      earnedPts: done.reduce((s, a) => s + (a.points || 0), 0),
    };
  });
}
