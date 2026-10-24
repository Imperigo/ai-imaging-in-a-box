import { describe, expect, it } from 'vitest';
import { RenderScene } from '../src';

/**
 * Knoten «Umfeld» (Visbox-Owner-Wunsch 24.10.2026): `vis.umfeld` bestellt Baeume, Bueche, Wiese,
 * Strasse und Autos um das Haus. Nur der Wunsch; die Gegenseite plant, laedt (nur CC0) und stellt.
 */

const SZENE = { geometry: { path: 'model/model.glb', format: 'glb' }, out: 'out' } as const;

describe('vis.umfeld im Auftrag', () => {
  it('ohne Feld: kein umfeld im Auftrag (alte Auftraege bleiben gleich)', () => {
    expect('umfeld' in RenderScene.parse(SZENE).vis).toBe(false);
  });

  it('der Wunsch kommt unveraendert an', () => {
    const umfeld = { kategorien: ['baeume', 'autos', 'strasse'], dichte: 'wenig', seed: 7, anzahl: { autos: 2 } } as const;
    expect(RenderScene.parse({ ...SZENE, vis: { umfeld } }).vis.umfeld).toEqual(umfeld);
  });

  it('leere Kategorien, unbekannte Kategorie, Dichte oder Feld werden abgewiesen', () => {
    for (const umfeld of [
      { kategorien: [] },
      { kategorien: ['palmen'] },
      { kategorien: ['baeume'], dichte: 'dicht' },
      { kategorien: ['baeume'], farbe: 'gruen' },
      { kategorien: ['baeume'], anzahl: { autos: 99 } },
      { kategorien: ['baeume'], anzahl: { haeuser: 1 } },
    ]) {
      expect(RenderScene.safeParse({ ...SZENE, vis: { umfeld } }).success, JSON.stringify(umfeld)).toBe(false);
    }
  });
});
