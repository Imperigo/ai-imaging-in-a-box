import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { RenderResult } from '../src';

/**
 * Vorschlag C18 (Visbox, Video-Befund L4-2, 21.10.2026): der Hausanteil an Grundlage
 * (`qa.haus_anteil_grundlage`, gezaehlt) und KI-Bild (`qa.haus_anteil_bild`, geschaetzt),
 * je 0..1, am `qa`-Block und je Kamera. Optional, ohne Default, kein Tor; ein kaputter Wert
 * faellt still weg und lehnt nie das ganze Ergebnis ab.
 */
const echt = JSON.parse(
  readFileSync(fileURLToPath(new URL('./fixtures/kv-hausanteil.json', import.meta.url)), 'utf8'),
) as { result: Record<string, unknown> };

describe('C18 · Hausanteil an Grundlage und KI-Bild', () => {
  it('Ergebnis aus dem Heim-PC-Kern: beide Zahlen am qa-Block und je Kamera', () => {
    const r = RenderResult.parse(echt.result);
    expect(r.qa.haus_anteil_grundlage).toBe(0.029);
    expect(r.qa.haus_anteil_bild).toBe(0.17);
    expect(r.qa_je_kamera?.map((k) => [k.kamera, k.haus_anteil_grundlage, k.haus_anteil_bild])).toEqual([
      ['s', 0.029, 0.17],
      ['nNW', 0.31, 0.33],
    ]);
    expect(r.qa.verdict.reason).toContain('Geometrie 0.0 gegen 0.65 — nur Auskunft');
    expect(r.qa.verdict.hinweise?.some((h) => h.startsWith('KI-BILD RAHMT ANDERS: '))).toBe(true);
  });

  it('rueckwaertsvertraeglich: ohne die Felder bleibt alles, ein kaputter Wert faellt still weg', () => {
    const qa = { ...(echt.result['qa'] as Record<string, unknown>) };
    delete qa['haus_anteil_grundlage'];
    delete qa['haus_anteil_bild'];
    const ohne = RenderResult.parse({ ...echt.result, qa });
    expect(ohne.qa.haus_anteil_grundlage).toBeUndefined();
    expect(ohne.qa.haus_anteil_bild).toBeUndefined();
    const kaputt = RenderResult.parse({ ...echt.result, qa: { ...qa, haus_anteil_bild: 1.7, haus_anteil_grundlage: 'x' } });
    expect(kaputt.qa.haus_anteil_bild).toBeUndefined();
    expect(kaputt.qa.haus_anteil_grundlage).toBeUndefined();
    expect(kaputt.qa.verdict.passed).toBe(false);
  });
});
