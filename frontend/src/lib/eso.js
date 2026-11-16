// ESO game-data helpers shared across the UI. Paths match scripts/assets_manifest.json.

/** @typedef {'ad' | 'dc' | 'ep'} AllianceKey */

const ALLIANCE_KEYS = /** @type {const} */ ({ aldmeri: 'ad', daggerfall: 'dc', ebonheart: 'ep' });

/**
 * "Ebonheart Pact" -> "ep". Unknown or missing -> null.
 * @param {string | null | undefined} alliance
 * @returns {AllianceKey | null}
 */
export function allianceKey(alliance) {
  if (!alliance) return null;
  return ALLIANCE_KEYS[/** @type {keyof typeof ALLIANCE_KEYS} */ (alliance.split(' ')[0].toLowerCase())] ?? null;
}

/** @param {string | null | undefined} alliance */
export function allianceIcon(alliance) {
  return alliance ? `/assets/alliance/${alliance.split(' ')[0].toLowerCase()}.png` : '';
}

/** @param {string | null | undefined} cls */
export function classIcon(cls) {
  return cls ? `/assets/class/${cls.toLowerCase().replace(/\s+/g, '')}.png` : '';
}

/**
 * Icon key normalisation. Must match server.py:
 * re.sub(r'[^a-z0-9]+', '_', icon.stem.lower()).strip('_')
 * @param {string} name
 */
export function iconKey(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '');
}

/**
 * Apply the alliance tint to the whole page.
 * @param {AllianceKey | null} key
 */
export function setAllianceTint(key) {
  if (key) document.documentElement.dataset.al = key;
  else delete document.documentElement.dataset.al;
}
