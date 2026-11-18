import { test } from 'node:test';
import assert from 'node:assert/strict';
import { slotIcon, itemIcon, equipped, mundusIcon, setKey, slugify, resolveWeaponType } from './gear.js';

test('armor slot icons follow weight; light chest is a shirt', () => {
  assert.equal(slotIcon(2, { armor_type: 'Light' }), '/assets/gear/armor/light/gear_breton_light_shirt_d.png');
  assert.equal(slotIcon(2, { armor_type: 'Heavy' }), '/assets/gear/armor/heavy/gear_breton_heavy_chest_d.png');
  assert.equal(slotIcon(16, { armor_type: 'Medium' }), '/assets/gear/armor/medium/gear_breton_medium_hands_d.png');
  assert.equal(slotIcon(0, {}), '/assets/interface/inventory_armor.png');
});

test('stale Staff weapon type is ignored when the name disagrees', () => {
  assert.equal(resolveWeaponType('Inferno Staff', 'sword of x'), null);
  assert.equal(slotIcon(4, { weapon_type: 'Inferno Staff', name: 'Sword of Ruin' }), '/assets/gear/weapon/gear_breton_1hsword_d.png');
  assert.equal(slotIcon(4, { weapon_type: 'Inferno Staff', name: 'Inferno Staff of X' }), '/assets/gear/weapon/gear_breton_staff_d.png');
});

test('shields are filter_type 2 with weaponType Shield', () => {
  assert.equal(itemIcon({ filter_type: 2, weapon_type: 'Shield' }), '/assets/gear/weapon/gear_breton_shield_d.png');
});

test('equipped maps bag 0 slots for one character only', () => {
  const a = { locations: [{ bag_id: 0, location_key: 'c1', bag_slots: { 4: 1 } }] };
  const b = { locations: [{ bag_id: 1, location_key: 'c1', bag_slots: { 7: 1 } }, { bag_id: 0, location_key: 'c2', bag_slots: { 0: 1 } }] };
  assert.deepEqual(equipped([a, b], 'c1'), { 4: a });
});

test('mundus, slugs and mythic set keys', () => {
  assert.equal(mundusIcon('The Thief'), '/assets/constellations/thief.png');
  assert.equal(slugify("Mother's Sorrow"), 'mothers-sorrow');
  assert.equal(setKey({ set_id: 0, set_name: "Velothi Ur-Mage's Amulet" }), 'velothi-ur-mages-amulet');
  assert.equal(setKey({ set_id: 123, set_name: 'X' }), 123);
});
