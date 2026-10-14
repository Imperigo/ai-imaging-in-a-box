import { describe, expect, it } from 'vitest';
import { RenderResult, renderResultMaengel, unbekannteFelder } from '../src';

/**
 * kv-lieferstatus-null (KosmoVis L1, Antwortblatt
 * `auftraege/ergebnisse/erg-20261001-216-kosmovis-v017.md` L1, Entscheid 51
 * der Gegenseite): `lieferstatus: null` heisst «nicht festgestellt» und ist
 * ein VORBEHALT, kein Fehler. Vorher verwarf der Vertrag das ganze Ergebnis
 * samt allen Bildern (Pfad `lieferstatus`, nachgemessen im Antwortblatt
 * `kosmo-orbit/docs/auftraege-kosmovis/antwort-20260930-int1-an-kosmovis.md`).
 *
 * Das Beispiel ist woertlich die Form, die der Schreiber der Gegenseite
 * sendet (Auftrag an uns vom 01.10.2026), gekuerzt um Felder, die hier
 * nichts pruefen.
 */

const GRUND = 'Nicht festgestellt: die Bilderzahl der Kameras passt nicht zur Bildliste.';

const BASIS = {
  schema: 'kosmovis.render-result/v2',
  job_id: 'vis-1790000000-l1null',
  images: ['sSE.png', 'sNW.png'],
  qa: { verdict: { passed: true, reason: '', hinweise: [] } },
};

describe('kv-lieferstatus-null: oberste Ebene', () => {
  it('(a) lieferstatus: null mit Grund wird angenommen, bleibt null und behaelt alle Bilder', () => {
    const roh = { ...BASIS, lieferstatus: null, lieferstatus_grund: GRUND };
    const r = RenderResult.safeParse(roh);
    expect(r.success).toBe(true);
    expect(r.data?.lieferstatus).toBeNull();
    expect(r.data?.lieferstatus_grund).toBe(GRUND);
    expect(r.data?.images).toEqual(['sSE.png', 'sNW.png']);
    expect(r.data?.qa.verdict.passed).toBe(true);
    // `null` ist ein bekannter Wert, kein abgestreiftes Fremdfeld.
    expect(unbekannteFelder(roh, r.data)).toEqual([]);
  });

  it('(a) renderResultMaengel nennt den Vorbehalt mit dem Grund der Gegenseite', () => {
    const r = RenderResult.parse({ ...BASIS, lieferstatus: null, lieferstatus_grund: GRUND });
    expect(renderResultMaengel(r)).toContain(`Lieferstatus nicht festgestellt: ${GRUND}`);
  });

  it('Pflicht-Grund gilt auch fuer null: null ohne Grund faellt durch', () => {
    const res = RenderResult.safeParse({ ...BASIS, lieferstatus: null });
    expect(res.success).toBe(false);
    expect(res.error?.issues.map((i) => i.path.join('.'))).toContain('lieferstatus_grund');
  });

  it('Pflicht-Grund: ein leerer Grund zaehlt nicht als Grund', () => {
    expect(RenderResult.safeParse({ ...BASIS, lieferstatus: null, lieferstatus_grund: '' }).success).toBe(false);
  });

  it('(c) fehlt das Feld, bleibt es «geliefert» wie bisher, ohne Mangelzeile', () => {
    const r = RenderResult.parse(BASIS);
    expect(r.lieferstatus).toBe('geliefert');
    expect(renderResultMaengel(r).some((m) => m.startsWith('Lieferstatus'))).toBe(false);
  });

  it('Gegenprobe: «geliefert» bleibt ohne Mangelzeile, ein unbekanntes Wort faellt weiter durch', () => {
    const r = RenderResult.parse({ ...BASIS, lieferstatus: 'geliefert' });
    expect(renderResultMaengel(r)).toEqual([]);
    expect(RenderResult.safeParse({ ...BASIS, lieferstatus: 'teilweise', lieferstatus_grund: 'x' }).success).toBe(false);
  });
});

describe('kv-lieferstatus-null: je Kamera', () => {
  it('(b) eine Kamera mit lieferstatus: null verwirft das Ergebnis nicht', () => {
    const roh = {
      ...BASIS,
      qa_je_kamera: [
        { kamera: 'sSE', lieferstatus: 'geliefert', bilder_soll: 1, bilder_ist: 1 },
        { kamera: 'sNW', lieferstatus: null, lieferstatus_grund: GRUND },
      ],
    };
    const r = RenderResult.safeParse(roh);
    expect(r.success).toBe(true);
    expect(r.data?.qa_je_kamera?.[1]?.lieferstatus).toBeNull();
    expect(r.data?.images).toEqual(['sSE.png', 'sNW.png']);
    expect(renderResultMaengel(r.data!)).toContain(`qa_je_kamera[sNW].lieferstatus: nicht festgestellt (${GRUND})`);
  });

  it('Pflicht-Grund je Kamera gilt auch fuer null', () => {
    const res = RenderResult.safeParse({ ...BASIS, qa_je_kamera: [{ kamera: 'sNW', lieferstatus: null }] });
    expect(res.success).toBe(false);
    expect(res.error?.issues.map((i) => i.path.join('.'))).toContain('qa_je_kamera.0.lieferstatus_grund');
  });

  it('fehlt das Kamera-Feld, bleibt es fehlend (kein Default, keine Mangelzeile)', () => {
    const r = RenderResult.parse({ ...BASIS, qa_je_kamera: [{ kamera: 'sSE' }] });
    expect(r.qa_je_kamera?.[0]).not.toHaveProperty('lieferstatus');
    expect(renderResultMaengel(r)).toEqual([]);
  });
});
