import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { RenderResult, RenderScene } from '../src';

/**
 * Nr. 85 (Owner-Grundsatz, Demolauf 16.10.2026) mit 81/83/84: ein Render = EINE
 * Blender-Grundlage, mehrere deckungsgleiche KI-Varianten. Vertrag zwischen
 * KosmoVis und Integrator vom 20.10.2026 (Zentrale
 * `erledigt/20261020-095801-integrator-an-kosmovis-grundlage-varianten.json`).
 *
 * Auflage 3: `vis.skip` heisst verbindlich «nur Grundlage» — die Probe haelt
 * beide Seiten an derselben Lesart fest (der 26.08.-Fehler). Die zwei
 * Ergebnisse unter `fixtures/kv-grundlage-*.json` hat der Heim-PC-Code der
 * Visbox geschrieben (Probenlauf mit Attrappen fuer Blender und Bildmodell),
 * sie sind nicht von Hand gebaut.
 */

const SZENE = { geometry: { path: 'model/model.glb', format: 'glb' }, out: 'out' } as const;
const KENNUNG = 'gl-0123456789abcdef';

function fehlerPfade(eingabe: unknown): string[] {
  const r = RenderScene.safeParse(eingabe);
  return r.success ? [] : r.error.issues.map((i) => i.path.join('.'));
}

function fixture(name: string): unknown {
  const pfad = fileURLToPath(new URL(`./fixtures/${name}`, import.meta.url));
  return JSON.parse(readFileSync(pfad, 'utf8'));
}

describe('RenderScene.vis — nur Grundlage, Grundlage wiederverwenden, fester Seed', () => {
  it('skip:true mit passes "alle" und ohne KI-Felder ist ein gueltiger Auftrag', () => {
    const s = RenderScene.parse({ ...SZENE, render: { passes: 'alle' }, vis: { skip: true } });
    expect(s.vis.skip).toBe(true);
    expect('grundlage' in s.vis).toBe(false);
    expect('seed' in s.vis).toBe(false);
  });

  it('grundlage und seed kommen unveraendert an', () => {
    const s = RenderScene.parse({ ...SZENE, vis: { grundlage: KENNUNG, seed: 0 } });
    expect(s.vis.grundlage).toBe(KENNUNG);
    expect(s.vis.seed).toBe(0);
    expect(RenderScene.parse({ ...SZENE, vis: { seed: 2147483647 } }).vis.seed).toBe(2147483647);
  });

  it('ohne die Felder ist alles wie bisher', () => {
    const s = RenderScene.parse(SZENE);
    expect('grundlage' in s.vis).toBe(false);
    expect('seed' in s.vis).toBe(false);
  });

  it('falsche Kennung oder Startwert werden abgewiesen', () => {
    expect(fehlerPfade({ ...SZENE, vis: { grundlage: 'vis-1-abcdef' } })).toEqual(['vis.grundlage']);
    expect(fehlerPfade({ ...SZENE, vis: { seed: -1 } })).toEqual(['vis.seed']);
    expect(fehlerPfade({ ...SZENE, vis: { seed: 2147483648 } })).toEqual(['vis.seed']);
    expect(fehlerPfade({ ...SZENE, vis: { seed: 1.5 } })).toEqual(['vis.seed']);
  });

  it('Grundlage mit skip oder mit Skizze geht nicht', () => {
    expect(fehlerPfade({ ...SZENE, vis: { grundlage: KENNUNG, skip: true } })).toEqual(['vis.grundlage']);
    expect(
      fehlerPfade({
        ...SZENE,
        skizze: { quelle: 'mappe', name: 'skizzen/a.png' },
        vis: { grundlage: KENNUNG },
      }),
    ).toEqual(['vis.grundlage']);
  });
});

describe('RenderResult — grundlage, seed und pose (vom Heim-PC geschrieben)', () => {
  it('nur Grundlage: engine_used "cycles", neue Grundlage, Pose je Kamera', () => {
    const r = RenderResult.parse(fixture('kv-grundlage-nur-grundlage.json'));
    expect(r.engine_used).toBe('cycles');
    expect(r.lieferstatus).toBe('geliefert');
    expect(r.grundlage?.wiederverwendet).toBe(false);
    expect(r.grundlage?.id).toMatch(/^gl-[0-9a-f]{16}$/);
    expect(r.qa_je_kamera?.every((k) => k.pose?.up_axis === 'z')).toBe(true);
    expect(r.qa_je_kamera?.some((k) => 'seed' in k)).toBe(false);
  });

  it('Variante: dieselbe Grundlage, wiederverwendet, fester Seed je Kamera', () => {
    const basis = RenderResult.parse(fixture('kv-grundlage-nur-grundlage.json'));
    const r = RenderResult.parse(fixture('kv-grundlage-variante.json'));
    expect(r.grundlage).toEqual({ id: basis.grundlage?.id, wiederverwendet: true });
    expect(r.qa_je_kamera?.map((k) => k.seed)).toEqual([7, 7, 7]);
  });

  it('eine Pose ohne drei Zahlen wird abgewiesen', () => {
    const r = RenderResult.safeParse({
      job_id: 'vis-1-abcdef',
      images: ['s.png'],
      qa_je_kamera: [{ kamera: 's', pose: { position: [0, 1], target: [0, 0, 0], fov: 50, up_axis: 'z' } }],
    });
    expect(r.success).toBe(false);
  });
});
