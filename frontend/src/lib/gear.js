// Equipment slots and gear icons. Ported from the Alpine UI's static lookups.

import { gameIcon } from './achievements.js';

const GEAR = '/assets/gear';
const WEAPON = `${GEAR}/weapon`;
const STAFF = `${WEAPON}/gear_breton_staff_d.png`;
const NECK = `${GEAR}/jewelry/gear_breton_neck_a.png`;
const RING = `${GEAR}/jewelry/gear_breton_ring_a.png`;

const WEAPON_ICONS = /** @type {Record<string, string>} */ ({
  Dagger: `${WEAPON}/gear_breton_dagger_d.png`,
  Sword: `${WEAPON}/gear_breton_1hsword_d.png`,
  Axe: `${WEAPON}/gear_breton_1haxe_d.png`,
  Hammer: `${WEAPON}/gear_breton_1hhammer_d.png`,
  'Two-Handed Sword': `${WEAPON}/gear_breton_2hsword_d.png`,
  'Two-Handed Axe': `${WEAPON}/gear_breton_2haxe_d.png`,
  'Two-Handed Hammer': `${WEAPON}/gear_breton_2hhammer_d.png`,
  Bow: `${WEAPON}/gear_breton_bow_d.png`,
  Shield: `${WEAPON}/gear_breton_shield_d.png`,
});

/** Equip slot -> armor piece (light chest is "shirt"). */
const ARMOR_SLOT = /** @type {Record<number, string>} */ ({ 0: 'head', 2: 'chest', 3: 'shoulders', 6: 'waist', 8: 'legs', 9: 'feet', 16: 'hands' });

const ARMOR_ICONS = /** @type {Record<string, string>} */ ({
  Heavy: `${GEAR}/armor/heavy/gear_breton_heavy_chest_d.png`,
  Medium: `${GEAR}/armor/medium/gear_breton_medium_chest_d.png`,
  Light: `${GEAR}/armor/light/gear_breton_light_shirt_d.png`,
});

const FALLBACK_ICONS = /** @type {Record<number, string>} */ ({
  1: '/assets/interface/inventory_weapons.png',
  2: '/assets/interface/inventory_armor.png',
  3: '/assets/interface/inventory_consumables.png',
  4: '/assets/interface/inventory_materials.png',
  5: '/assets/interface/inventory_miscellaneous.png',
  6: '/assets/interface/enchanting_potency.png',
});

export const SLOT_LABELS = /** @type {Record<number, string>} */ ({
  0: 'Head', 1: 'Neck', 2: 'Chest', 3: 'Shoulders', 4: 'Main Hand', 5: 'Off Hand', 6: 'Waist',
  8: 'Legs', 9: 'Feet', 10: 'Costume', 11: 'Ring 1', 12: 'Ring 2', 13: 'Poison', 14: 'Backup Poison',
  16: 'Gloves', 20: 'Backup Main', 21: 'Backup Off',
});

/** Paper-doll groups, in display order. */
export const APPAREL = [0, 3, 2, 16, 6, 8, 9];
export const JEWELRY = [1, 11, 12];
export const FRONT_BAR = [4, 5];
export const BACK_BAR = [20, 21];

/** Name-based weapon icon; longer/more specific matches first. @param {string} n lowercased name */
export function weaponNameToSrc(n) {
  if (n.includes('greatsword') || n.includes('great sword')) return WEAPON_ICONS['Two-Handed Sword'];
  if (n.includes('battle axe') || n.includes('battleaxe') || n.includes('great axe')) return WEAPON_ICONS['Two-Handed Axe'];
  if (n.includes('maul')) return WEAPON_ICONS['Two-Handed Hammer'];
  if (n.includes('staff')) return STAFF;
  if (n.includes('dagger')) return WEAPON_ICONS.Dagger;
  if (['sword', 'blade', 'saber', 'sabre', 'machete'].some((w) => n.includes(w))) return WEAPON_ICONS.Sword;
  if (n.includes('axe')) return WEAPON_ICONS.Axe;
  if (n.includes('hammer') || n.includes('mace')) return WEAPON_ICONS.Hammer;
  if (n.includes('bow')) return WEAPON_ICONS.Bow;
  if (n.includes('shield')) return WEAPON_ICONS.Shield;
  return null;
}

/** iasync records weapon type per slot at scan time; drop it when it claims Staff but the name disagrees. */
export function resolveWeaponType(/** @type {string | undefined} */ wt, /** @type {string} */ nameLower) {
  return wt && wt.includes('Staff') && !nameLower.includes('staff') ? null : wt;
}

/** @param {string | undefined} wt @param {string | undefined} name */
function weaponSrc(wt, name) {
  const n = (name || '').toLowerCase();
  const t = resolveWeaponType(wt, n);
  if (!t) return weaponNameToSrc(n) ?? FALLBACK_ICONS[1];
  return WEAPON_ICONS[t] ?? (t.includes('Staff') ? STAFF : FALLBACK_ICONS[1]);
}

/** @param {number} slot @param {string | undefined} armorType */
function armorSrc(slot, armorType) {
  const piece = ARMOR_SLOT[slot];
  if (!piece || !armorType) return FALLBACK_ICONS[2];
  const w = armorType.toLowerCase();
  return `${GEAR}/armor/${w}/gear_breton_${w}_${w === 'light' && piece === 'chest' ? 'shirt' : piece}_d.png`;
}

/**
 * Icon for an item equipped in a specific slot. Off-hand slots (5, 21) can hold a weapon or shield.
 * @param {number} slot
 * @param {any} item
 */
export function slotIcon(slot, item) {
  if (ownIcon(item)) return ownIcon(item);
  if (slot in ARMOR_SLOT) return armorSrc(slot, item.armor_type);
  if (slot === 1) return NECK;
  if (slot === 11 || slot === 12) return RING;
  if ([4, 5, 20, 21].includes(slot)) return weaponSrc(item.weapon_type, item.name);
  if (slot === 10) return '/assets/interface/character_creation_body.png';
  if (slot === 13 || slot === 14) return FALLBACK_ICONS[3];
  return itemIcon(item);
}

/** The item's own texture when iasync recorded it (monster helms, mythics, unique jewelry); else null. @param {any} item */
const ownIcon = (item) => gameIcon(item?.icon);

/** Icon for an item anywhere (inventory, lists). @param {any} item */
export function itemIcon(item) {
  if (ownIcon(item)) return ownIcon(item);
  if (item.filter_type === 1) return weaponSrc(item.weapon_type, item.name);
  if (item.filter_type === 2) return item.weapon_type === 'Shield' ? WEAPON_ICONS.Shield : ARMOR_ICONS[item.armor_type] ?? FALLBACK_ICONS[2];
  if (item.filter_type === 25) return NECK;
  return FALLBACK_ICONS[item.filter_type] ?? FALLBACK_ICONS[5];
}

/**
 * Map of equip slot -> item for one character, from /api/data items (bag 0 = equipped).
 * @param {any[]} items
 * @param {string} charId
 */
export function equipped(items, charId) {
  /** @type {Record<number, any>} */
  const out = {};
  for (const item of items ?? []) {
    for (const loc of item.locations) {
      if (loc.bag_id !== 0 || loc.location_key !== charId) continue;
      for (const slot of Object.keys(loc.bag_slots || {})) out[+slot] = item;
    }
  }
  return out;
}

/** Mundus constellation icon; strips a leading "The ". @param {string} name */
export function mundusIcon(name) {
  return name ? `/assets/constellations/${name.toLowerCase().replace(/^the\s+/, '')}.png` : '';
}

/** "Mother's Sorrow" -> "mothers-sorrow" (eso-sets / skillbook URLs, mythic set_id=0 cache key). @param {string} name */
export function slugify(name) {
  return name.replace(/['‘’]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

/** Set-bonus cache key: set_id, or the slug for mythics (set_id 0). @param {any} item */
export function setKey(item) {
  return item?.set_id || (item?.set_name ? slugify(item.set_name) : null);
}

/** Equipped pieces per set, most first: [[setName, count], ...]. @param {Record<number, any>} gear */
export function setCounts(gear) {
  /** @type {Record<string, number>} */
  const n = {};
  for (const item of Object.values(gear)) if (item?.set_name) n[item.set_name] = (n[item.set_name] ?? 0) + 1;
  return Object.entries(n).sort((a, b) => b[1] - a[1]);
}

/**
 * Item for a saved (Wizards Wardrobe) gear entry: name/quality/type from the matching inventory item when
 * we have one, but trait/style/enchant/set from the saved link itself. Ported from the classic buildTipShow.
 * @param {any} g saved gear entry
 * @param {any} base inventory item with the same item_id, or undefined
 */
export function savedGearItem(g, base) {
  return {
    name: base?.name ?? (g.link_name || `Item #${g.item_id}`),
    icon: base?.icon ?? "",
    quality: base?.quality ?? 4,
    quality_name: base?.quality_name ?? 'Epic',
    quality_color: base?.quality_color ?? '#a02ee4',
    filter_type: base?.filter_type ?? 1,
    filter_type_name: base?.filter_type_name ?? 'Weapons',
    level: base?.level ?? 50,
    locations: base?.locations ?? [],
    total_quantity: base?.total_quantity ?? 0,
    weapon_type: base?.weapon_type ?? null,
    armor_type: base?.armor_type ?? null,
    is_stolen: false,
    trait_id: g.trait_id,
    trait_name: g.trait_name,
    is_transmuted: g.is_transmuted,
    style_name: g.style_name,
    is_crafted: g.is_crafted,
    is_enchanted: g.is_enchanted,
    enchant_name: g.enchant_name || base?.enchant_name || '',
    set_name: g.set_name || base?.set_name || '',
    set_id: g.set_id ?? base?.set_id ?? 0,
  };
}
