// ESO game-data helpers shared across the UI. Paths match scripts/assets_manifest.json.

/** @param {string | null | undefined} alliance */
export function allianceIcon(alliance) {
  return alliance ? `/assets/alliance/${alliance.split(' ')[0].toLowerCase()}.png` : '';
}

/** @param {string | null | undefined} cls */
export function classIcon(cls) {
  return cls ? `/assets/class/${cls.toLowerCase().replace(/\s+/g, '')}.png` : '';
}

/**
 * Icon key normalisation. Must match app/server.py:
 * re.sub(r'[^a-z0-9]+', '_', icon.stem.lower()).strip('_')
 * @param {string} name
 */
export function iconKey(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '');
}
