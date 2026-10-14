import { describe, expect, it } from 'vitest';
import { RenderScene } from '../src';

/**
 * Owner-Entscheid 76 (Splat jetzt): das optionale Feld `context` an der
 * Bestellung — eine Gauss-Splat-Aufnahme der Umgebung, auf der HomeStation
 * abgelegt, mit Lage im glTF-Welt-System des Modells. Festgelegt mit
 * Integrator, prepare und HomeStation; die App-Seite der HomeStation schaltet
 * sich an `'context' in RenderScene.shape` ein.
 */

const SZENE = { geometry: { path: 'model/model.glb', format: 'glb' }, out: 'out' } as const;
const EINHEIT = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
const KONTEXT = {
  kind: 'splat',
  ply: '/home/station/splats/umgebung.ply',
  verortung: '/home/station/splats/umgebung.verortung.json',
  transform: EINHEIT,
  fit: 'behelf',
  crs_note: 'Lage von Hand eingepasst; Ursprung Modell-Nullpunkt, LV95 nicht bestimmt.',
} as const;

function fehlerPfade(eingabe: unknown): string[] {
  const r = RenderScene.safeParse(eingabe);
  return r.success ? [] : r.error.issues.map((i) => i.path.join('.'));
}

describe('RenderScene.context — Splat-Kontext (Entscheid 76)', () => {
  it('das Feld steht im Vertrag (daran schaltet sich die HomeStation ein)', () => {
    expect('context' in RenderScene.shape).toBe(true);
  });

  it('gueltige Szene mit context: alles kommt unveraendert an', () => {
    const s = RenderScene.parse({ ...SZENE, context: KONTEXT });
    expect(s.context).toEqual(KONTEXT);
    const mitPasspunkten = RenderScene.parse({ ...SZENE, context: { ...KONTEXT, fit: 'passpunkte', verortung: null } });
    expect(mitPasspunkten.context?.fit).toBe('passpunkte');
    expect(mitPasspunkten.context?.verortung).toBeNull();
  });

  it('ohne context ist alles wie bisher: kein Feld, keine Vorgabe, dieselbe Ausgabe', () => {
    const s = RenderScene.parse(SZENE);
    expect('context' in s).toBe(false);
    expect(JSON.stringify(RenderScene.parse(SZENE))).toBe(JSON.stringify(s));
  });

  it('falsche Matrixlaenge wird abgewiesen', () => {
    expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, transform: EINHEIT.slice(0, 15) } })).toEqual(['context.transform']);
    expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, transform: [...EINHEIT, 0] } })).toEqual(['context.transform']);
    expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, transform: [] } })).toEqual(['context.transform']);
  });

  it('nicht-endliche Zahlen in der Matrix werden abgewiesen', () => {
    for (const schlecht of [Number.NaN, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY]) {
      const t = [...EINHEIT];
      t[3] = schlecht;
      expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, transform: t } })).toEqual(['context.transform.3']);
    }
    const alsText = [...EINHEIT] as unknown[];
    alsText[0] = '1';
    expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, transform: alsText } })).toEqual(['context.transform.0']);
  });

  it('unbekanntes kind und unbekanntes fit werden abgewiesen', () => {
    expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, kind: 'mesh' } })).toEqual(['context.kind']);
    expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, fit: 'auto' } })).toEqual(['context.fit']);
  });

  it('jedes fehlende Feld wird abgewiesen; leere Pfade auch; ein fremdes Feld auch (strict)', () => {
    for (const feld of ['kind', 'ply', 'verortung', 'transform', 'fit', 'crs_note'] as const) {
      const ohne: Record<string, unknown> = { ...KONTEXT };
      delete ohne[feld];
      expect(fehlerPfade({ ...SZENE, context: ohne }), `ohne ${feld}`).toEqual([`context.${feld}`]);
    }
    expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, ply: '' } })).toEqual(['context.ply']);
    expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, verortung: '' } })).toEqual(['context.verortung']);
    expect(fehlerPfade({ ...SZENE, context: { ...KONTEXT, skala: 2 } })).toEqual(['context']);
    expect(fehlerPfade({ ...SZENE, context: null })).toEqual(['context']);
  });
});
