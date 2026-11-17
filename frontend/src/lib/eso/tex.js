// In-game UI textures (ESO keyboard UI, from UESP via `make assets`) cut up the way the game's XML templates use them.
// The game crops sub-rectangles (TextureCoords) and builds frames from 8-segment edge strips; CSS can do neither, so we
// do it once on a canvas and expose the pieces as CSS custom properties on :root (see styles/eso.css).

export const ART = '/assets/esoui/';

/** @param {string} path */
function load(path) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`missing texture ${path}; run make assets`));
    img.src = ART + path + '.png';
  });
}

/** @param {number} w @param {number} h */
function canvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return /** @type {[HTMLCanvasElement, CanvasRenderingContext2D]} */ ([c, /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'))]);
}

/** Sub-rectangle of a texture, as a data URL. @param {string} path @param {number} x @param {number} y @param {number} w @param {number} h */
export async function crop(path, x, y, w, h) {
  const img = await load(path);
  const [c, g] = canvas(w, h);
  g.drawImage(img, x, y, w, h, 0, 0, w, h);
  return c.toDataURL();
}

/**
 * A `border-image` source (3x3 segments) from an ESO backdrop edge file: 8 square segments in a row, in the order
 * left, right, top, bottom, top-left, top-right, bottom-left, bottom-right, with top and bottom stored rotated 90°.
 * @param {string} edge @param {string | null} center
 */
export async function edgeFrame(edge, center) {
  const img = await load(edge);
  const s = img.height;
  const [c, g] = canvas(s * 3, s * 3);
  if (center) g.drawImage(await load(center), s, s, s, s);
  /** @param {number} i @param {number} dx @param {number} dy @param {boolean} [rot] */
  const seg = (i, dx, dy, rot = false) => {
    if (!rot) return g.drawImage(img, i * s, 0, s, s, dx, dy, s, s);
    g.save();
    g.translate(dx + s, dy);
    g.rotate(Math.PI / 2);
    g.drawImage(img, i * s, 0, s, s, 0, 0, s, s);
    g.restore();
  };
  seg(0, 0, s);
  seg(1, 2 * s, s);
  seg(2, s, 0, true);
  seg(3, s, 2 * s, true);
  seg(4, 0, 0);
  seg(5, 2 * s, 0);
  seg(6, 0, 2 * s);
  seg(7, 2 * s, 2 * s);
  return c.toDataURL();
}

/** CSS custom property -> how to build it. Coordinates come from the TextureCoords in the game's XML. */
const PIECES = {
  // ZO_ArrowStatusBarBG / ZO_ArrowStatusBarOverlay: 10px caps and a stretched middle, top 20 rows of a 512x32 file.
  '--eso-bar-bg-l': () => crop('miscellaneous/progressbar_frame_bg', 0, 0, 10, 20),
  '--eso-bar-bg-m': () => crop('miscellaneous/progressbar_frame_bg', 10, 0, 292, 20),
  '--eso-bar-bg-r': () => crop('miscellaneous/progressbar_frame_bg', 304, 0, 10, 20),
  '--eso-bar-frame-l': () => crop('miscellaneous/progressbar_frame', 0, 0, 10, 20),
  '--eso-bar-frame-m': () => crop('miscellaneous/progressbar_frame', 10, 0, 292, 20),
  '--eso-bar-frame-r': () => crop('miscellaneous/progressbar_frame', 304, 0, 10, 20),
  '--eso-bar-fill': () => crop('miscellaneous/progressbar_genericfill', 0, 0, 4, 20),
  '--eso-bar-gloss': () => crop('miscellaneous/progressbar_genericfill_gloss', 0, 0, 4, 20),
  '--eso-bar-edge': () => crop('miscellaneous/progressbar_genericfill_leadingedge', 0, 0, 8, 20),
  '--eso-bar-edge-gloss': () => crop('miscellaneous/progressbar_genericfill_leadingedge_gloss', 0, 0, 8, 20),
  // ZO_ListEntryBackdrop: rows 0-40 of the file, drawn with 16/stretch/32 px bands.
  '--eso-list-bg': () => crop('miscellaneous/listitem_backdrop', 0, 0, 512, 40),
  '--eso-list-hl': () => crop('miscellaneous/listitem_selectedhighlight', 0, 0, 512, 80),
  // ZO_ContextualActionsTile highlight cell of the market slot sheet.
  '--eso-slot-hl': () => crop('market/market_slotbgandhighlight', 295, 0, 295, 155),
  // ZO_DynamicHorizontalDivider: two caps and a stretched centre of a 128x8 file.
  '--eso-divider-l': () => crop('miscellaneous/horizontaldivider_dynamic', 2, 0, 54, 8),
  '--eso-divider-m': () => crop('miscellaneous/horizontaldivider_dynamic', 56, 0, 16, 8),
  '--eso-divider-r': () => crop('miscellaneous/horizontaldivider_dynamic', 72, 0, 55, 8),
  // Backdrops built from edge files.
  '--eso-edit': () => edgeFrame('chatwindow/textentry_edge', 'chatwindow/textentry_center'),
  '--eso-backdrop': () => edgeFrame('tooltips/ui-border', 'tooltips/ui-tooltipcenter'),
  '--eso-inset': () => edgeFrame('miscellaneous/inset_edgefile_8', null),
};

/** @type {Promise<void> | null} */
let installing = null;

/** Build every piece once and publish it on :root. Safe to call from every component that needs the art. */
export function installEsoArt() {
  installing ??= Promise.all(
    Object.entries(PIECES).map(async ([name, make]) => {
      try {
        document.documentElement.style.setProperty(name, `url(${await make()})`);
      } catch (e) {
        console.warn(String(e)); // the page still works with the plain fallbacks in eso.css
      }
    }),
  ).then(() => {});
  return installing;
}

/** In-game text and bar colours from iasync 1.7.0 (`uiColors`), published as CSS variables. @param {Record<string, string> | undefined} colors */
export function applyUiColors(colors) {
  if (!colors) return;
  /** @type {Record<string, string>} */
  const map = {
    textNormal: '--eso-normal',
    textSelected: '--eso-selected',
    textHighlight: '--eso-highlight',
    textDisabled: '--eso-disabled',
    textDefault: '--eso-default',
    textContrast: '--eso-contrast',
    textSecondSelected: '--eso-second-selected',
    textSecondNormal: '--eso-second-normal',
    xpStart: '--eso-xp-start',
    xpEnd: '--eso-xp-end',
  };
  for (const [k, v] of Object.entries(colors)) if (map[k] && /^[0-9a-f]{6}$/i.test(v)) document.documentElement.style.setProperty(map[k], `#${v}`);
}
