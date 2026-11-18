// Item list filtering, sorting and set grouping, shared by the character Bags view and the Inventory tab.
// Ported from the classic filteredItems / charFilteredItems / groupedItems getters.

export const TYPE_OPTIONS = [
  { v: '1', l: 'Weapons' }, { v: '2', l: 'Armor' }, { v: '25', l: 'Jewelry' }, { v: '3', l: 'Consumables' },
  { v: '4', l: 'Materials' }, { v: '6', l: 'Glyphs' }, { v: '21', l: 'Furnishings' }, { v: '5', l: 'Miscellaneous' },
];

export const BAG_OPTIONS = [{ v: '0', l: 'Equipped' }, { v: '1', l: 'Backpack' }];

export const LOCATION_OPTIONS = [
  { v: 'character', l: 'Characters' }, { v: 'bank', l: 'Bank' }, { v: 'craftbag', l: 'Craft Bag' }, { v: 'house_chest', l: 'House Chests' },
  { v: 'guild_bank', l: 'Guild Banks' },
];

export const TRAIT_GROUPS = [
  { group: 'Armor', options: [{ v: '18', l: 'Divines' }, { v: '16', l: 'Infused' }, { v: '25', l: 'Nirnhoned' }, { v: '13', l: 'Reinforced' }, { v: '11', l: 'Sturdy' }, { v: '14', l: 'Well-Fitted' }, { v: '12', l: 'Impenetrable' }, { v: '15', l: 'Training' }] },
  { group: 'Weapon', options: [{ v: '4', l: 'Infused' }, { v: '26', l: 'Nirnhoned' }, { v: '5', l: 'Defending' }, { v: '2', l: 'Charged' }, { v: '7', l: 'Sharpened' }, { v: '1', l: 'Powered' }, { v: '3', l: 'Precise' }, { v: '8', l: 'Decisive' }, { v: '6', l: 'Training' }] },
  { group: 'Jewelry', options: [{ v: '32', l: 'Protective' }, { v: '29', l: 'Harmony' }, { v: '31', l: 'Bloodthirsty' }, { v: '30', l: 'Triune' }, { v: '33', l: 'Infused' }, { v: '28', l: 'Swift' }, { v: '22', l: 'Arcane' }, { v: '21', l: 'Healthy' }, { v: '23', l: 'Robust' }] },
];

/** Quality filter values match item.quality; colours are game data. */
export const QUALITY_OPTIONS = [
  { v: '0', l: 'Trash', color: '#8b8b8b' }, { v: '1', l: 'Normal', color: '#cccccc' }, { v: '2', l: 'Fine', color: '#2dc50e' },
  { v: '3', l: 'Superior', color: '#5199ff' }, { v: '4', l: 'Epic', color: '#a02ee4' }, { v: '5', l: 'Legendary', color: '#c29300' },
  { v: '6', l: 'Mythic', color: '#e87800' },
];

/** @typedef {{ search: string, quality: string, types: string[], traits: string[], bags: string[], locTypes: string[], chars: string[], transmuted: boolean, crafted: boolean, unbound: boolean, hasSet: boolean, dupes: boolean }} Filters */

/** @returns {Filters} */
export const emptyFilters = () => ({ search: '', quality: '', types: [], traits: [], bags: [], locTypes: [], chars: [], transmuted: false, crafted: false, unbound: false, hasSet: false, dupes: false });

/** @param {Filters} f */
export const hasFilters = (f) =>
  !!(f.search.trim() || f.quality || f.types.length || f.traits.length || f.bags.length || f.locTypes.length || f.chars.length || f.transmuted || f.crafted || f.unbound || f.hasSet || f.dupes);

/** Built-in filter chips; saved ones are added by the user. @type {{ name: string, f: Partial<Filters> }[]} */
export const PRESETS = [
  { name: 'Duplicate gear', f: { dupes: true } },
  { name: 'Sellable set gear', f: { types: ['1', '2', '25'], unbound: true, hasSet: true } },
  { name: 'Trash', f: { quality: '0' } },
  { name: 'Glyphs', f: { types: ['6'] } },
];

/** A preset's filters on top of empty ones. @param {Partial<Filters>} p @returns {Filters} */
export const applyPreset = (p) => ({ ...emptyFilters(), ...JSON.parse(JSON.stringify(p)) }); // JSON, not structuredClone: saved chips are state proxies

/** Whether the filters are exactly this preset. @param {Filters} f @param {Partial<Filters>} p */
export const isPreset = (f, p) => JSON.stringify(f) === JSON.stringify(applyPreset(p));

const GEAR = new Set([1, 2, 25]);

/**
 * Gear names held more than once across the account (same name, any trait or location): candidates to clear out.
 * @param {any[]} items
 */
export function duplicateNames(items) {
  /** @type {Map<string, number>} */
  const n = new Map();
  for (const i of items ?? []) if (GEAR.has(i.filter_type)) n.set(i.name, (n.get(i.name) ?? 0) + (i.total_quantity || 0));
  return new Set([...n].filter(([, c]) => c > 1).map(([name]) => name));
}

/**
 * Items with `value` (avg TTC price x quantity) set; bound items and unpriced ones get null.
 * @param {any[]} items @param {Record<string, number>} avg prices by lower-cased name
 */
export function withValues(items, avg) {
  return items.map((i) => {
    const p = i.is_bound ? undefined : avg[priceName(i.name)];
    return { ...i, unit: p ?? null, value: p != null ? p * (i.total_quantity || 0) : null };
  });
}

/** @param {string} name */
export const priceName = (name) => (name || '').toLowerCase().replace(/\s+/g, ' ').trim();

/**
 * Count and value per item type and per location type, for the summary strip.
 * A location's value is the unit price times the quantity held there.
 * @param {any[]} items items from withValues
 */
export function summarize(items) {
  /** @type {Record<string, { count: number, value: number }>} */
  const types = {};
  /** @type {Record<string, { count: number, value: number }>} */
  const locs = {};
  let value = 0;
  for (const i of items) {
    const t = (types[String(i.filter_type)] ??= { count: 0, value: 0 });
    t.count++;
    t.value += i.value ?? 0;
    value += i.value ?? 0;
    const seen = new Set();
    for (const l of i.locations ?? []) {
      const s = (locs[l.location_type] ??= { count: 0, value: 0 });
      if (!seen.has(l.location_type)) s.count++;
      seen.add(l.location_type);
      s.value += (i.unit ?? 0) * (l.quantity || 0);
    }
  }
  return { types, locs, value };
}

/**
 * One character's items, with locations and quantity narrowed to that character.
 * @param {any[]} items @param {string} charId
 */
export function forCharacter(items, charId) {
  const out = [];
  for (const item of items ?? []) {
    const locations = (item.locations ?? []).filter((/** @type {any} */ l) => l.location_type === 'character' && l.location_key === charId);
    if (!locations.length) continue;
    out.push({ ...item, key: `${item.key}::${charId}`, locations, total_quantity: locations.reduce((s, l) => s + (l.quantity || 0), 0) });
  }
  return out;
}

/**
 * Items passing the filters. With a location filter (bag, location type, character) each row keeps only the matching
 * locations, and its quantity and value cover just those, so "Bank" doesn't show an item's guild bank stacks.
 * @param {any[]} items @param {Filters} f
 */
export function filterItems(items, f) {
  const q = f.search.toLowerCase().trim();
  const dupes = f.dupes ? duplicateNames(items) : null;
  const byLocation = !!(f.bags.length || f.locTypes.length || f.chars.length);
  /** @param {any} l */
  const at = (l) =>
    (!f.bags.length || f.bags.includes(String(l.bag_id))) &&
    (!f.locTypes.length || f.locTypes.includes(l.location_type)) &&
    (!f.chars.length || f.chars.includes(l.location_key));
  const kept = items.filter((i) => {
    if (dupes && !dupes.has(i.name)) return false;
    if (f.unbound && i.is_bound) return false;
    if (f.hasSet && !i.set_name) return false;
    if (q && !i.name.toLowerCase().includes(q)) return false;
    if (f.quality !== '' && i.quality !== Number(f.quality)) return false;
    if (f.types.length && !f.types.includes(String(i.filter_type))) return false;
    if (f.traits.length && !(f.traits.includes('any') ? i.trait_id > 0 : f.traits.includes(String(i.trait_id)))) return false;
    if (f.transmuted && !i.is_transmuted) return false;
    if (f.crafted && !i.is_crafted) return false;
    return !byLocation || i.locations.some(at);
  });
  if (!byLocation) return kept;
  return kept.map((i) => {
    const locations = i.locations.filter(at);
    if (locations.length === i.locations.length) return i;
    const total_quantity = locations.reduce((/** @type {number} */ s, /** @type {any} */ l) => s + (l.quantity || 0), 0);
    return { ...i, locations, total_quantity, value: i.unit != null ? i.unit * total_quantity : i.value };
  });
}

/** @param {any[]} items @param {string} key @param {'asc' | 'desc'} dir */
export function sortItems(items, key, dir) {
  const d = dir === 'asc' ? 1 : -1;
  // null (e.g. no price) sorts after every number either way
  return [...items].sort((a, b) =>
    typeof a[key] === 'string' ? d * a[key].localeCompare(b[key]) : a[key] == null ? (b[key] == null ? 0 : 1) : b[key] == null ? -1 : d * (a[key] - b[key]));
}

/**
 * Table rows; grouped by 'set' or 'name', a header row per group (alphabetical, "No Set" last) before its items.
 * @param {any[]} items @param {'' | 'set' | 'name'} groupBy
 * @returns {({ t: 'item', item: any } | { t: 'h', set: string, count: number })[]}
 */
export function displayRows(items, groupBy) {
  if (!groupBy) return items.map((item) => ({ t: 'item', item }));
  const field = groupBy === 'set' ? 'set_name' : 'name';
  /** @type {Map<string, any[]>} */
  const groups = new Map();
  const noSet = [];
  for (const item of items) {
    const g = item[field];
    if (!g) noSet.push(item);
    else (groups.get(g) ?? groups.set(g, []).get(g)).push(item);
  }
  /** @type {any[]} */
  const rows = [];
  const add = (/** @type {string} */ set, /** @type {any[]} */ list) => {
    rows.push({ t: 'h', set, count: list.length });
    for (const item of list) rows.push({ t: 'item', item });
  };
  for (const set of [...groups.keys()].sort()) add(set, /** @type {any[]} */ (groups.get(set)));
  if (noSet.length) add('No Set', noSet);
  return rows;
}
