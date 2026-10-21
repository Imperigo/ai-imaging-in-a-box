import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { AutoRichtung, BAUTEIL_ARTEN, RenderScene, StimmungPreset } from '../src';

/**
 * Vorschlag V (Bauplan «Neue Knoten», Visbox-Entscheide 109–113): die Bestellseite der neuen
 * Knoten Stimmung, Kamera und Oberflaeche. Geprueft gegen die echten Bestellungen des Heim-PC-Codes
 * (`claude/kosmovis-knoten-fixtures`, je Datei `{scene, result}`), nicht gegen erfundene Beispiele.
 * Die Fixtures tragen kein `out` (die Bruecke setzt es) — es wird hier ergaenzt.
 */
function bestellung(datei: string): Record<string, unknown> {
  const roh = JSON.parse(readFileSync(fileURLToPath(new URL(`./fixtures/${datei}`, import.meta.url)), 'utf8')) as {
    scene: Record<string, unknown>;
  };
  return { out: '', ...roh.scene };
}

const STIMMUNGEN = ['morgen', 'mittag', 'abend', 'blaue-stunde', 'bedeckt', 'nebel', 'winter', 'weiss'] as const;

describe('Vorschlag V · neue Knoten', () => {
  it('acht Stimmungen in der Reihenfolge der Visbox, je die echte Bestellung', () => {
    expect(StimmungPreset.options).toEqual([...STIMMUNGEN]);
    for (const s of STIMMUNGEN) {
      const r = RenderScene.safeParse(bestellung(`kv-stimmung-${s}.json`));
      expect(r.success, s).toBe(true);
    }
  });

  it('Stimmung mit Himmelsbild und gedrehtem Himmel', () => {
    const r = RenderScene.parse(bestellung('kv-stimmung-hdri.json'));
    expect(r.render.environment?.preset).toBe('abend');
    expect(r.render.environment?.rotationGrad).toBe(30);
  });

  it('cameras_auto aus dem Knoten «Kamera» (echte Bestellungen)', () => {
    const a = RenderScene.parse(bestellung('kv-kamera-auto.json'));
    expect(a.cameras).toBe('auto');
    expect(a.cameras_auto).toEqual({
      richtungen: ['s', 'nNW'],
      brennweite_mm: 50,
      abstand: { art: 'auto', fuellt: 0.6 },
      perspektive: 'senkrecht',
    });
    const b = RenderScene.parse(bestellung('kv-drehung-bestellt.json'));
    expect(b.cameras_auto?.richtungen).toEqual(['sSE']);
    expect(AutoRichtung.options).toHaveLength(12);
  });

  it('cameras_auto: fester Abstand, Grenzen, nur mit "auto"', () => {
    const basis = { geometry: { path: 'm.glb', format: 'glb' }, out: '' };
    expect(RenderScene.safeParse({ ...basis, cameras_auto: { richtungen: ['n'], abstand: { art: 'fest', meter: 40 } } }).success).toBe(true);
    expect(RenderScene.safeParse({ ...basis, cameras_auto: { richtungen: [] } }).success).toBe(false);
    expect(RenderScene.safeParse({ ...basis, cameras_auto: { richtungen: ['x'] } }).success).toBe(false);
    expect(RenderScene.safeParse({ ...basis, cameras_auto: { richtungen: ['n'], brennweite_mm: 28 } }).success).toBe(false);
    expect(RenderScene.safeParse({ ...basis, cameras_auto: { richtungen: ['n'], abstand: { art: 'auto', fuellt: 0.99 } } }).success).toBe(false);
    const mitListe = RenderScene.safeParse({
      ...basis,
      cameras: [{ position: [0, 1.7, 30], target: [0, 3, 0], fov: 50, up_axis: 'y' }],
      cameras_auto: { richtungen: ['n'] },
    });
    expect(mitListe.success).toBe(false);
    const mitInnen = RenderScene.safeParse({
      ...basis,
      geometry: { path: 'm.ifc', format: 'ifc' },
      interior: { rooms: 'auto' },
      cameras_auto: { richtungen: ['n'] },
    });
    expect(mitInnen.success).toBe(false);
  });

  it('CameraSpec.perspektive: optional, nur senkrecht oder frei', () => {
    const basis = { geometry: { path: 'm.glb', format: 'glb' }, out: '' };
    const k = { position: [0, 1.7, 30], target: [0, 1.7, 0], fov: 50, up_axis: 'y' };
    expect(RenderScene.safeParse({ ...basis, cameras: [{ ...k, perspektive: 'senkrecht' }] }).success).toBe(true);
    expect(RenderScene.safeParse({ ...basis, cameras: [k] }).success).toBe(true);
    expect(RenderScene.safeParse({ ...basis, cameras: [{ ...k, perspektive: 'schief' }] }).success).toBe(false);
  });

  it('render.materialien aus dem Knoten «Oberfläche» (echte Bestellung), leer abgewiesen', () => {
    const r = RenderScene.parse(bestellung('kv-materialien.json'));
    expect(r.render.materialien?.fassade?.id).toBe('sichtbeton-sandgestrahlt');
    expect(r.render.materialien?.boden?.toenung).toEqual({ farbe: '#aa8866', staerke: 0.3 });
    expect(BAUTEIL_ARTEN).toEqual(['fassade', 'dach', 'fenster', 'boden', 'uebrige']);
    const basis = { geometry: { path: 'm.glb', format: 'glb' }, out: '' };
    expect(RenderScene.safeParse({ ...basis, render: { materialien: {} } }).success).toBe(false);
    expect(RenderScene.safeParse({ ...basis, render: { materialien: { fassade: { id: 'Gross' } } } }).success).toBe(false);
    expect(
      RenderScene.safeParse({ ...basis, render: { materialien: { dach: { id: 'klinker', toenung: { farbe: 'rot', staerke: 1 } } } } }).success,
    ).toBe(false);
  });
});
