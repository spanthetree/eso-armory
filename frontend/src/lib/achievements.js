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

/**
 * Game texture path -> URL the server proxies from UESP and caches: "/esoui/art/icons/foo.dds" -> "/esoicons/foo.png",
 * "/esoui/art/treeicons/bar_up.dds" -> "/esoicons/treeicons/bar_up.png"; null for anything else.
 * @param {string} icon
 */
export function gameIcon(icon) {
  const m = /^\/esoui\/art\/(icons\/mapkey|icons|treeicons|collections|achievements|charactercreate|tribute\/patrons|tribute|currency)\/([a-z0-9_-]+)\.dds$/i.exec(icon ?? '');
  if (!m) return null;
  const folder = m[1].toLowerCase();
  return folder === 'icons' ? `/esoicons/${m[2].toLowerCase()}.png` : `/esoicons/${folder}/${m[2].toLowerCase()}.png`;
}
export const achievementIcon = gameIcon;

/** A tree icon's pressed variant ("..._up" -> "..._down"), as the game shows for the open category. @param {string | null} url */
export const pressedIcon = (url) => (url ? url.replace(/_up\.png$/, '_down.png') : url);

/**
 * Search every category for one character: groups of hits by "Category › Subcategory", in category order.
 * @param {ReturnType<typeof buildIndex>} idx @param {any[]} categories @param {string | null} charId @param {string} q
 * @param {number} [limit] stop after this many hits
 */
export function searchAll(idx, categories, charId, q, limit = 300) {
  const needle = q.toLowerCase().trim();
  if (!needle) return { groups: [], total: 0, capped: false };
  const keys = new Set([...idx.account.keys(), ...((charId && idx.byChar.get(charId)?.keys()) || [])]);
  const order = new Map((categories ?? []).map((c, i) => [c.name, i]));
  const sorted = [...keys].sort((a, b) => {
    const [ca, sa] = a.split('||');
    const [cb, sb] = b.split('||');
    return (order.get(ca) ?? 999) - (order.get(cb) ?? 999) || sa.localeCompare(sb);
  });
  const groups = [];
  let total = 0;
  for (const key of sorted) {
    const [cat, sub] = key.split('||');
    const hits = achievementsIn(idx, cat, sub, charId, needle);
    if (!hits.length) continue;
    total += hits.length;
    groups.push({ cat, sub, list: hits });
    if (total >= limit) return { groups, total, capped: true };
  }
  return { groups, total, capped: false };
}

/**
 * Recent completions grouped by day, newest first, one entry per achievement.
 * @param {any[]} recent newest first
 */
export function timeline(recent) {
  const seen = new Set();
  /** @type {{ day: string, list: any[] }[]} */
  const days = [];
  for (const a of recent ?? []) {
    if (seen.has(a.id)) continue;
    seen.add(a.id);
    const day = a.completionDate || 'Unknown date';
    if (days.at(-1)?.day !== day) days.push({ day, list: [] });
    /** @type {any} */ (days.at(-1)).list.push(a);
  }
  return days;
}

/** Character names carry a grammar suffix ("Name^Mx"); drop it. @param {string} name */
export const charName = (name) => (name || '').replace(/\^.*$/, '');

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

/**
 * The in-game list shows one row per achievement line (tiers I, II, III...): the first tier not yet earned, or the last
 * if all are. Each shown row gets `line`, the whole line in order, when it has more than one tier.
 * @param {any[]} list
 */
export function collapseLines(list) {
  const byId = new Map(list.map((a) => [a.id, a]));
  /** @type {Map<number, any[]>} */
  const groups = new Map();
  for (const a of list) {
    const k = a.lineBaseId || a.id;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k)?.push(a);
  }
  return [...groups.values()].map((g) => {
    const ids = new Set(g.map((a) => a.id));
    let cur = g.find((a) => !ids.has(a.linePreviousId)) ?? g[0];
    const line = [];
    const seen = new Set();
    while (cur && ids.has(cur.id) && !seen.has(cur.id)) {
      line.push(cur);
      seen.add(cur.id);
      cur = byId.get(cur.lineNextId);
    }
    for (const a of g) if (!seen.has(a.id)) line.push(a);
    const shown = line.find((a) => !a.complete) ?? line[line.length - 1];
    return line.length > 1 ? { ...shown, line } : shown;
  });
}
