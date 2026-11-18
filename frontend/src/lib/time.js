// Small time helpers for game timers (unix seconds).

/** "3d 4h", "5h 12m", "8m" until `unix`; '' if it has passed or is unknown. @param {number} unix @param {number} [now] ms */
export function timeLeft(unix, now = Date.now()) {
  const s = Math.floor(unix - now / 1000);
  if (!unix || s <= 0) return '';
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60);
  return d ? `${d}d ${h}h` : h ? `${h}h ${m}m` : `${Math.max(m, 1)}m`;
}
