import type { AnyPatch } from './doc';
import type { Entity, Opening, Slab, Wall } from './entities';
import type { Pt } from './units';

/**
 * L15: Teile eines Lifts (Schachtwand, Schachttür, Deckenloch) und der Lift
 * selbst lassen sich nicht einzeln löschen oder verschieben. Die Prüfung sitzt
 * in `execute()` für jeden Befehl ausser `design.lift`; Rückgängig läuft
 * daran vorbei und stellt den Lift als Ganzes her.
 */
const gleich = (p: Pt, q: Pt) => p.x === q.x && p.y === q.y;
const gleichPoly = (a: readonly Pt[], b: readonly Pt[]) => a.length === b.length && a.every((p, i) => gleich(p, b[i]!));

export function pruefeLiftSchutz(patches: readonly AnyPatch[], commandId: string, fehler: (m: string) => Error): void {
  if (commandId === 'design.lift') return;
  for (const p of patches) {
    if ('settings' in p || !p.before) continue;
    const b = p.before as Entity;
    const a = p.after as Entity | null;
    const hinweis = 'gehört zum Lift — mit design.lift ändern oder löschen';
    if (b.kind === 'lift') {
      if (a !== null && a.kind === 'lift' && JSON.stringify(a) === JSON.stringify(b)) continue;
      throw fehler(`Der Lift ${hinweis}`);
    }
    if (b.kind === 'slab') {
      const sl = (b as Slab).liftLoecher ?? [];
      if (sl.length === 0 || a === null || a.kind !== 'slab') continue;
      const rest = (a as Slab).holes ?? [];
      if (sl.some((l) => !rest.some((h) => gleichPoly(h, l.loch)))) throw fehler(`Das Deckenloch ${hinweis}`);
      continue;
    }
    if (!b.meta?.liftId) continue;
    if (b.kind === 'wall') {
      const w = a as Wall | null;
      if (w === null || !gleich(w.a, (b as Wall).a) || !gleich(w.b, (b as Wall).b)) throw fehler(`Die Schachtwand ${hinweis}`);
    } else if (b.kind === 'opening') {
      const o = a as Opening | null;
      const ob = b as Opening;
      if (o === null || o.wallId !== ob.wallId || o.center !== ob.center || o.width !== ob.width) throw fehler(`Die Schachttür ${hinweis}`);
    }
  }
}
