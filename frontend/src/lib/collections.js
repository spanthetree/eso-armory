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

// ── in-game set grid ─────────────────────────────────────

/** Piece types (EQUIPMENT_FILTER_TYPE_*) for the "Apparel Types" and "Weapon Types" filters. */
export const APPAREL_TYPES = [
  { v: '1', l: 'Light' }, { v: '2', l: 'Medium' }, { v: '3', l: 'Heavy' }, { v: '7', l: 'Shield' }, { v: '4', l: 'Necklace' }, { v: '5', l: 'Ring' },
];
export const WEAPON_TYPES = [
  { v: '6', l: 'One-Handed' }, { v: '8', l: 'Two-Handed' }, { v: '9', l: 'Destruction Staff' }, { v: '10', l: 'Restoration Staff' }, { v: '11', l: 'Bow' },
];
export const COMPLETION = [
  { v: '', l: 'Any progress' }, { v: 'incomplete', l: 'Not complete' }, { v: 'near', l: 'Missing 1–2' }, { v: 'untouched', l: 'None collected' }, { v: 'complete', l: 'Complete' },
];

const SLOT_WORDS = /** @type {[RegExp, string][]} */ ([
  [/\b(arm cops|epaulets?|pauldrons?|spaulders?|shoulders?|mantle)\b/i, 'shoulders'],
  [/\b(hat|helm|helmet|hood|crown|mask|cap|visage|headdress)\b/i, 'head'],
  [/\b(gloves|bracers|gauntlets)\b/i, 'hands'],
  [/\b(sash|belt|girdle)\b/i, 'belt'],
  [/\b(breeches|guards|greaves|trousers)\b/i, 'legs'],
  [/\b(shoes|boots|sabatons)\b/i, 'feet'],
]);

/**
 * The piece's own icon (iasync 1.6.0), else the paper-doll slot silhouette guessed from its type and name.
 * @param {{ icon?: string, filterType: number, name?: string }} p @param {(path: string) => string | null} gameIcon
 */
export function pieceIcon(p, gameIcon) {
  const own = gameIcon(p.icon ?? '');
  if (own) return own;
  const t = p.filterType;
  const slot =
    t === 4 ? 'neck' : t === 5 ? 'ring' : t === 7 ? 'offhand' : t >= 6 ? 'mainhand' : (SLOT_WORDS.find(([re]) => re.test(p.name ?? ''))?.[1] ?? 'chest');
  return `/assets/interface/gearslot_${slot}.png`;
}

/**
 * Per-subcategory collected/total within one category, A-Z ('' = sets filed directly under the category).
 * @param {any[]} sets @param {string} category
 */
export function subSummary(sets, category) {
  /** @type {Map<string, { name: string, collected: number, total: number }>} */
  const by = new Map();
  for (const s of sets ?? []) {
    if ((s.category || 'Unknown') !== category) continue;
    const name = s.subcategory || '';
    const c = by.get(name) ?? by.set(name, { name, collected: 0, total: 0 }).get(name);
    c.collected += s.numCollected;
    c.total += s.numTotal;
  }
  return [...by.values()].sort((a, b) => a.name.localeCompare(b.name));
}

/** @typedef {{ search: string, apparel: string[], weapons: string[], showLocked: boolean, completion: string }} GridFilters */

/** @returns {GridFilters} */
export const emptyGridFilters = () => ({ search: '', apparel: [], weapons: [], showLocked: true, completion: '' });

/** @param {any} s @param {string} completion */
function completionMatches(s, completion) {
  const missing = s.numTotal - s.numCollected;
  if (completion === 'complete') return missing <= 0;
  if (completion === 'incomplete') return missing > 0;
  if (completion === 'near') return missing > 0 && missing <= 2;
  if (completion === 'untouched') return s.numCollected === 0;
  return true;
}

/**
 * Sets to draw and the pieces to show in each. A search spans every category; otherwise the scope is the
 * category (and subcategory, if given). Type filters narrow the pieces; sets left with none are dropped.
 * @param {any[]} sets @param {string | null} category @param {string | null} sub @param {GridFilters} f
 */
export function gridSets(sets, category, sub, f) {
  const q = f.search.toLowerCase().trim();
  const types = new Set([...f.apparel, ...f.weapons]);
  const out = [];
  for (const s of sets ?? []) {
    if (q) {
      if (!s.name.toLowerCase().includes(q) && !s.pieces.some((/** @type {any} */ p) => (p.name || '').toLowerCase().includes(q))) continue;
    } else {
      if ((s.category || 'Unknown') !== category) continue;
      if (sub != null && (s.subcategory || '') !== sub) continue;
    }
    if (!completionMatches(s, f.completion)) continue;
    const pieces = s.pieces.filter((/** @type {any} */ p) => (!types.size || types.has(String(p.filterType))) && (f.showLocked || p.collected));
    if (!pieces.length) continue;
    out.push({ set: s, pieces });
  }
  return out;
}

/**
 * Where a set's pieces come from, and whether guild traders sell them (dungeon, trial and arena gear binds on pickup).
 * Same rule as Compare's setSource.
 * @param {any} s stickerbook set
 */
export function pieceSource(s) {
  const where = s.subcategory && s.subcategory !== s.category ? `${s.category} › ${s.subcategory}` : s.category || 'Unknown';
  const cat = `${s.category || ''} ${s.subcategory || ''}`.toLowerCase();
  const kind = /trial/.test(cat) ? 'Trial' : /arena/.test(cat) ? 'Arena' : /dungeon/.test(cat) ? 'Dungeon' : '';
  return { where, kind, priced: !kind };
}

// ── Collectibles (iasync 1.9.0) ──────────────────────────────────────────────
// The in-game Collections book's tabs. `spec` is COLLECTIBLE_CATEGORY_SPECIALIZATION_*; `sets` is the set
// collection above. Order and icons follow the game (keyboardingamescenes.lua).
export const BOOKS = [
  { id: 'collectibles', label: 'Collectibles', icon: 'collections/collections_tabicon_collectibles', spec: 0 },
  { id: 'housing', label: 'Housing', icon: 'collections/collections_tabicon_housing', spec: 2 },
  { id: 'outfits', label: 'Outfit Styles', icon: 'collections/collections_tabicon_outfitstyles', spec: 3 },
  { id: 'sets', label: 'Set Items', icon: 'collections/collections_tabicon_itemsets', spec: null },
  { id: 'tribute', label: 'Tales of Tribute', icon: 'collections/collections_tabicon_tributepatrons', spec: 4 },
];

/** SI_COLLECTIONS_BOOK_FILTER_SHOW_* the web can answer (no "new" or "usable" outside the game). */
export const COLLECTIBLE_FILTERS = [
  { v: 'all', l: 'Show All' },
  { v: 'locked', l: 'Show Locked' },
  { v: 'unlocked', l: 'Show Unlocked' },
];

/** One book tab's categories (in game order). @param {any} col @param {number} spec */
export const bookCategories = (col, spec) => (col?.categories ?? []).filter((/** @type {any} */ c) => c.specialization === spec);

/**
 * Collectibles to show: in the picked category/subcategory, or across the whole tab while searching. Categories
 * that hide locked collectibles in game (hidesLocked) hide them here too.
 * @param {any} col @param {any[]} cats this tab's categories @param {{ cat: number | null, sub: number | null }} at
 * @param {{ search: string, show: string }} f
 */
export function bookItems(col, cats, at, f) {
  const q = f.search.trim().toLowerCase();
  const byIdx = new Map(cats.map((c) => [c.idx, c]));
  return (col?.items ?? []).filter((/** @type {any} */ it) => {
    const c = byIdx.get(it.cat);
    if (!c) return false;
    if (q ? !it.name.toLowerCase().includes(q) : it.cat !== at.cat || it.sub !== (at.sub ?? 0)) return false;
    if (!it.unlocked && (c.hidesLocked || f.show === 'unlocked')) return false;
    return !(it.unlocked && f.show === 'locked');
  });
}
