// Item list filtering, sorting and set grouping, shared by the character Bags view and the Inventory tab.
// Ported from the classic filteredItems / charFilteredItems / groupedItems getters.

export const TYPE_OPTIONS = [
  { v: '1', l: 'Weapons' }, { v: '2', l: 'Armor' }, { v: '25', l: 'Jewelry' }, { v: '3', l: 'Consumables' },
  { v: '4', l: 'Materials' }, { v: '6', l: 'Glyphs' }, { v: '21', l: 'Furnishings' }, { v: '5', l: 'Miscellaneous' },
];

export const BAG_OPTIONS = [{ v: '0', l: 'Equipped' }, { v: '1', l: 'Backpack' }];

export const LOCATION_OPTIONS = [
  { v: 'character', l: 'Characters' }, { v: 'bank', l: 'Bank' }, { v: 'craftbag', l: 'Craft Bag' }, { v: 'house_chest', l: 'House Chests' },
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

/** @typedef {{ search: string, quality: string, types: string[], traits: string[], bags: string[], locTypes: string[], chars: string[], transmuted: boolean, crafted: boolean }} Filters */

/** @returns {Filters} */
export const emptyFilters = () => ({ search: '', quality: '', types: [], traits: [], bags: [], locTypes: [], chars: [], transmuted: false, crafted: false });

/** @param {Filters} f */
export const hasFilters = (f) =>
  !!(f.search.trim() || f.quality || f.types.length || f.traits.length || f.bags.length || f.locTypes.length || f.chars.length || f.transmuted || f.crafted);

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

/** @param {any[]} items @param {Filters} f */
export function filterItems(items, f) {
  const q = f.search.toLowerCase().trim();
  return items.filter((i) => {
    if (q && !i.name.toLowerCase().includes(q)) return false;
    if (f.quality !== '' && i.quality !== Number(f.quality)) return false;
    if (f.types.length && !f.types.includes(String(i.filter_type))) return false;
    if (f.traits.length && !(f.traits.includes('any') ? i.trait_id > 0 : f.traits.includes(String(i.trait_id)))) return false;
    if (f.transmuted && !i.is_transmuted) return false;
    if (f.crafted && !i.is_crafted) return false;
    if (f.bags.length || f.locTypes.length || f.chars.length) {
      const hit = i.locations.some(
        (/** @type {any} */ l) =>
          (!f.bags.length || f.bags.includes(String(l.bag_id))) &&
          (!f.locTypes.length || f.locTypes.includes(l.location_type)) &&
          (!f.chars.length || f.chars.includes(l.location_key)),
      );
      if (!hit) return false;
    }
    return true;
  });
}

/** @param {any[]} items @param {string} key @param {'asc' | 'desc'} dir */
export function sortItems(items, key, dir) {
  const d = dir === 'asc' ? 1 : -1;
  return [...items].sort((a, b) => (typeof a[key] === 'string' ? d * a[key].localeCompare(b[key]) : d * (a[key] - b[key])));
}

/**
 * Table rows; with groupBySet, a header row per set (alphabetical, "No Set" last) before its items.
 * @param {any[]} items @param {boolean} groupBySet
 * @returns {({ t: 'item', item: any } | { t: 'h', set: string, count: number })[]}
 */
export function displayRows(items, groupBySet) {
  if (!groupBySet) return items.map((item) => ({ t: 'item', item }));
  /** @type {Map<string, any[]>} */
  const groups = new Map();
  const noSet = [];
  for (const item of items) {
    if (!item.set_name) noSet.push(item);
    else (groups.get(item.set_name) ?? groups.set(item.set_name, []).get(item.set_name)).push(item);
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
