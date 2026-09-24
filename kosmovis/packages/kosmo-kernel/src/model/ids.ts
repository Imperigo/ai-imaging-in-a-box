/**
 * Entity-IDs: zeitlich sortierbar + kollisionsfrei, ohne externe Abhängigkeit.
 * Format: <prefix>_<zeit base36><zufall base36> — lesbar in Journal und Yjs.
 */

let lastTime = 0;
let seq = 0;

export function newId(prefix: string): string {
  const now = Date.now();
  if (now === lastTime) {
    seq++;
  } else {
    lastTime = now;
    seq = 0;
  }
  const rand = Math.floor(Math.random() * 36 ** 6)
    .toString(36)
    .padStart(6, '0');
  return `${prefix}_${now.toString(36)}${seq.toString(36)}${rand}`;
}
