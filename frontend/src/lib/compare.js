// Build comparison: an imported build (share code) or a SuperStar screenshot against the account's items.
// Ported from the classic compareGearToItem / compareMissingItems / compareSourceMeta / ssComparison.

const QUALITY_COLORS = ['#8b8b8b', '#cccccc', '#2dc50e', '#5199ff', '#a02ee4', '#c29300', '#e87800'];
const APPAREL_SLOTS = [0, 2, 3, 5, 6, 8, 9, 16, 21];
const JEWELRY_SLOTS = [1, 11, 12];

/** Identity of a specific item roll: base item, trait and enchant. @param {any} g */
export const gearSig = (g) => [g?.item_id || 0, g?.trait_id || 0, g?.enchant_id || 0].join(':');

/**
 * Display item for imported gear: the saved link's own data, borrowing quality/type from a matching owned item.
 * @param {any} g imported gear entry @param {any[]} items account items
 */
export function importedGearItem(g, items) {
  const id = Number(g?.item_id || 0);
  const match =
    items.find((i) => Number(i.item_id || 0) === id && Number(i.trait_id || 0) === Number(g?.trait_id || 0) && Number(i.enchant_id || 0) === Number(g?.enchant_id || 0)) ??
    items.find((i) => Number(i.item_id || 0) === id);
  const slot = g?.slot ?? -1;
  const quality = Number.isInteger(g?.quality) ? g.quality : Number.isInteger(match?.quality) ? match.quality : 4;
  return {
    name: g?.link_name || match?.name || (id ? `Item #${id}` : 'Unknown'),
    quality,
    quality_name: g?.quality_name || match?.quality_name || '',
    quality_color: g?.quality_color || match?.quality_color || QUALITY_COLORS[quality] || QUALITY_COLORS[4],
    filter_type: Number.isInteger(g?.filter_type) ? g.filter_type : match?.filter_type ?? (APPAREL_SLOTS.includes(slot) ? 2 : JEWELRY_SLOTS.includes(slot) ? 25 : 1),
    filter_type_name: g?.filter_type_name || match?.filter_type_name || '',
    weapon_type: g?.weapon_type || match?.weapon_type || null,
    armor_type: g?.armor_type || match?.armor_type || null,
    trait_id: g?.trait_id || 0,
    trait_name: g?.trait_name || null,
    is_transmuted: !!g?.is_transmuted,
    style_name: g?.style_name || null,
    is_crafted: !!g?.is_crafted,
    is_enchanted: !!g?.is_enchanted,
    enchant_name: g?.enchant_name || '',
    set_name: g?.set_name || '',
    set_id: g?.set_id || 0,
    level: Number.isInteger(g?.level) ? g.level : 0,
    locations: [],
  };
}

/**
 * Where a set drops, from the collection data, and whether that's a dungeon/trial/arena (no TTC price then).
 * @param {string} setName @param {any[]} sets stickerbook sets
 */
export function setSource(setName, sets) {
  if (!setName) return { text: 'Source: Unknown', dungeon: false, trial: false, arena: false };
  const set = (sets ?? []).find((s) => (s.name || '').toLowerCase() === setName.toLowerCase());
  if (!set) return { text: `Source: ${setName}`, dungeon: false, trial: false, arena: false };
  const where = set.subcategory && set.subcategory !== set.category ? `${set.category} / ${set.subcategory}` : set.category;
  const cat = `${set.category || ''} ${set.subcategory || ''}`.toLowerCase();
  return { text: `Source: ${where || setName}`, dungeon: /dungeon/.test(cat), trial: /trial/.test(cat), arena: /arena/.test(cat) };
}

/**
 * Imported gear the account doesn't own (same item, trait and enchant), with where to get it and whether
 * a TTC price applies (not for crafted gear or dungeon/trial/arena drops).
 * @param {any[]} gear imported build gear @param {any[]} items account items @param {any[]} sets stickerbook sets
 */
export function missingItems(gear, items, sets) {
  const owned = new Set(items.map(gearSig));
  const craftedIds = new Set(items.filter((i) => i.is_crafted && i.item_id).map((i) => Number(i.item_id)));
  return (gear ?? [])
    .filter((g) => !owned.has(gearSig(g)))
    .map((g) => {
      const src = setSource(g.set_name, sets);
      const crafted = !!g.is_crafted || craftedIds.has(Number(g.item_id || 0));
      const drop = src.dungeon || src.trial || src.arena;
      const dropLabel = [src.dungeon && 'Dungeon', src.trial && 'Trial', src.arena && 'Arena'].filter(Boolean).join('/');
      return {
        ...g,
        name: g.link_name || (g.item_id ? `Item #${g.item_id}` : 'Unknown Item'),
        crafted,
        priced: !crafted && !drop,
        dropLabel,
        sourceText: crafted ? `Crafted • ${src.text}` : src.text,
      };
    });
}

const BAG_LABEL = /** @type {Record<number, string>} */ ({ 1: 'Backpack', 2: 'Bank', 5: 'Craft Bag', 6: 'ESO+ Bank' });
/** @param {any} loc */
function locLabel(loc) {
  if (!loc) return 'Storage';
  if (loc.bag_id === 0) return `Equipped on ${loc.location_label}`;
  if (loc.bag_id === 1) return `${loc.location_label}'s Backpack`;
  return BAG_LABEL[loc.bag_id] || 'Storage';
}

/**
 * Rows comparing a parsed SuperStar build with what this character wears and what the account owns.
 * status: equipped | have | wrong_trait | missing | na
 * @param {any[]} target parsed gear rows ({ slot, slot_id, item_name, trait, enchantment })
 * @param {Record<number, any>} worn this character's equipped items by slot
 * @param {any[]} items account items
 */
export function superstarRows(target, worn, items) {
  /** @type {Map<string, any[]>} */
  const byName = new Map();
  for (const i of items) {
    const k = (i.name || '').toLowerCase().trim();
    if (k) (byName.get(k) ?? byName.set(k, []).get(k)).push(i);
  }
  return (target ?? []).map((slot) => {
    const w = worn[slot.slot_id];
    const cur = w ? { name: w.name || null, trait: w.trait_name || null, enchant: w.enchant_name || null } : null;
    if (!slot.item_name) return { ...slot, status: 'na', statusLabel: 'N/A', cur };
    const key = slot.item_name.toLowerCase().trim();
    const trait = (slot.trait || '').toLowerCase().trim();
    const curItemMatch = !!cur && (cur.name || '').toLowerCase() === key;
    const curTraitMatch = curItemMatch && (!trait || (cur?.trait || '').toLowerCase() === trait);
    const matches = byName.get(key) ?? [];
    if (!matches.length) return { ...slot, status: 'missing', statusLabel: '✗ Missing', cur, curItemMatch, curTraitMatch };
    const traitMatch = matches.find((i) => !trait || (i.trait_name || '').toLowerCase() === trait);
    const candidate = traitMatch ?? matches[0];
    const locs = candidate.locations ?? [];
    const best = locs.find((l) => l.bag_id === 0) ?? locs.find((l) => l.bag_id === 1) ?? locs.find((l) => l.bag_id === 2) ?? locs[0];
    if (!traitMatch) return { ...slot, status: 'wrong_trait', statusLabel: `⚠ ${locLabel(best)} (${candidate.trait_name || 'unknown trait'})`, cur, curItemMatch, curTraitMatch };
    const status = best?.bag_id === 0 ? 'equipped' : 'have';
    return { ...slot, status, statusLabel: `✓ ${locLabel(best)}`, cur, curItemMatch, curTraitMatch };
  });
}
