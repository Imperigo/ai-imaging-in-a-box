import { describe, expect, it } from 'vitest';
import { RenderScene } from '../src';

/**
 * Owner-Entscheid 96 der Visbox (15.10.2026): die Skizze vom iPad fuehrt das
 * Bild. Das optionale Feld `skizze` nennt eine Skizze, die in der Mappe der
 * Visbox liegt — es reist nur ihr Name, kein Bild.
 */

const SZENE = { geometry: { path: 'model/model.glb', format: 'glb' }, out: 'out' } as const;
const SKIZZE = { quelle: 'mappe', name: 'skizzen/fassade-sued.png', anweisung: 'Balkon aus Holz' } as const;
const KAMERA = { position: [0, 1.6, 10], target: [0, 1.6, 0], fov: 50, up_axis: 'y' } as const;

function fehlerPfade(eingabe: unknown): string[] {
  const r = RenderScene.safeParse(eingabe);
  return r.success ? [] : r.error.issues.map((i) => i.path.join('.'));
}

describe('RenderScene.skizze — die Skizze fuehrt das Bild (Entscheid 96)', () => {
  it('das Feld steht im Vertrag', () => {
    expect('skizze' in RenderScene.shape).toBe(true);
  });

  it('gueltige Szene mit Skizze: alles kommt unveraendert an, mit und ohne Anweisung', () => {
    expect(RenderScene.parse({ ...SZENE, skizze: SKIZZE }).skizze).toEqual(SKIZZE);
    const ohne = RenderScene.parse({ ...SZENE, skizze: { quelle: 'mappe', name: 'skizzen/a.png' } });
    expect(ohne.skizze).toEqual({ quelle: 'mappe', name: 'skizzen/a.png' });
    expect('anweisung' in (ohne.skizze ?? {})).toBe(false);
  });

  it('ohne Skizze ist alles wie bisher: kein Feld, keine Vorgabe, dieselbe Ausgabe', () => {
    const s = RenderScene.parse(SZENE);
    expect('skizze' in s).toBe(false);
    expect(JSON.stringify(RenderScene.parse(SZENE))).toBe(JSON.stringify(s));
  });

  it('Quelle nur «mappe»; Name und Anweisung nicht leer; fremde Felder abgewiesen (strict)', () => {
    expect(fehlerPfade({ ...SZENE, skizze: { ...SKIZZE, quelle: 'upload' } })).toEqual(['skizze.quelle']);
    expect(fehlerPfade({ ...SZENE, skizze: { ...SKIZZE, name: '' } })).toEqual(['skizze.name']);
    expect(fehlerPfade({ ...SZENE, skizze: { ...SKIZZE, anweisung: '' } })).toEqual(['skizze.anweisung']);
    expect(fehlerPfade({ ...SZENE, skizze: { ...SKIZZE, bild: 'data:image/png;base64,AAAA' } })).toEqual(['skizze']);
    expect(fehlerPfade({ ...SZENE, skizze: { anweisung: 'x' } })).toEqual(['skizze.quelle', 'skizze.name']);
    expect(fehlerPfade({ ...SZENE, skizze: null })).toEqual(['skizze']);
  });

  it('eine Skizze ist EIN Bild: Kameraliste und Innenansicht abgewiesen, "auto" geht', () => {
    expect(fehlerPfade({ ...SZENE, skizze: SKIZZE, cameras: [KAMERA] })).toEqual(['cameras']);
    expect(fehlerPfade({ ...SZENE, skizze: SKIZZE, cameras: 'auto' })).toEqual([]);
    expect(
      fehlerPfade({
        ...SZENE,
        geometry: { path: 'm.ifc', format: 'ifc' },
        skizze: SKIZZE,
        interior: { rooms: 'auto' },
      }),
    ).toEqual(['interior']);
    // Ohne Skizze bleibt die Kameraliste, was sie war.
    expect(fehlerPfade({ ...SZENE, cameras: [KAMERA] })).toEqual([]);
  });

  it('eine Skizze braucht das Bildmodell: vis.skip abgewiesen', () => {
    expect(fehlerPfade({ ...SZENE, skizze: SKIZZE, vis: { skip: true } })).toEqual(['vis.skip']);
    expect(fehlerPfade({ ...SZENE, vis: { skip: true } })).toEqual([]);
  });
});
