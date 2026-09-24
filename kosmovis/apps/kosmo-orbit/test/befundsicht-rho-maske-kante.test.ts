import { describe, expect, it } from 'vitest';
import { varianteDiff, varianteMerkmale } from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';
import type { VisNode } from '@kosmo/kernel';

/**
 * P-BEFUNDSICHT (27.08.2026, `docs/STAND-WORKERAUFTRAEGE-2026-08-27.md`
 * Posten 1+2, Auftrag `auftraege/von-homestation/auf-orbit-20260823-03.md`).
 *
 * Zwei Messwerte, die der Vertrag seit 23.08.2026 fuehrt (`render-result.ts`,
 * `GeometryQA.rho_maske`/`kante_an_maskengrenze`) und die bis zu diesem
 * Paket KEIN Konsument las: die Schwelle 0.80 fuer `rho_maske` stand nur als
 * Kommentar, `kante_an_maskengrenze` erschien in keiner Oberflaeche. Diese
 * Suite belegt beide Ketten ROT (vor dem Paket) → GRUEN (danach) —
 * `varianteMerkmale()` ist die einzige Stelle, die `JobQa.geometry` in
 * Anzeige-Merkmale uebersetzt (`KuratierInspektor.tsx`, `varianteDiff`
 * lesen nur von dort).
 */

const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };

function qaMitGeometrie(geometry: JobQa['geometry']): JobQa {
  return { geometry, verdict: { passed: true } };
}

describe('P-BEFUNDSICHT — rho_maske gegen Schwelle 0.80 (Posten 1)', () => {
  it('rho_maske >= 0.80: Tiefenstaffelung bestanden', () => {
    const qa = qaMitGeometrie({ rho_maske: 0.8437, passed: true });
    const m = varianteMerkmale(node, undefined, qa);
    expect(m.tiefenstaffelungBestanden).toBe(true);
  });

  it('rho_maske knapp unter 0.80 (Versatz-2m-Fall aus der Eichung, 0.7843): verfehlt', () => {
    const qa = qaMitGeometrie({ rho_maske: 0.7843, passed: true });
    const m = varianteMerkmale(node, undefined, qa);
    expect(m.tiefenstaffelungBestanden).toBe(false);
  });

  it('rho_maske genau auf der Schwelle: bestanden (>=)', () => {
    const qa = qaMitGeometrie({ rho_maske: 0.8, passed: true });
    expect(varianteMerkmale(node, undefined, qa).tiefenstaffelungBestanden).toBe(true);
  });

  it('rho_maske: null (P-NULLGEOMETRIE, NICHT GEMESSEN) — kein Urteil, keine erfundene Schwelle', () => {
    const qa = qaMitGeometrie({ rho_maske: null, passed: true });
    expect(varianteMerkmale(node, undefined, qa).tiefenstaffelungBestanden).toBeUndefined();
  });

  it('rho_maske fehlt ganz: ebenfalls kein Urteil', () => {
    const qa = qaMitGeometrie({ passed: true });
    expect(varianteMerkmale(node, undefined, qa).tiefenstaffelungBestanden).toBeUndefined();
  });

  it('ohne QA ueberhaupt: kein Urteil', () => {
    expect(varianteMerkmale(node, undefined, undefined).tiefenstaffelungBestanden).toBeUndefined();
  });
});

describe('P-BEFUNDSICHT — kante_an_maskengrenze als Ja/Nein (Posten 2)', () => {
  it('kante_an_maskengrenze: true kommt als bauwerkVorhanden: true an', () => {
    const qa = qaMitGeometrie({ kante_an_maskengrenze: true, passed: true });
    expect(varianteMerkmale(node, undefined, qa).bauwerkVorhanden).toBe(true);
  });

  it('kante_an_maskengrenze: false kommt als bauwerkVorhanden: false an (nicht als "fehlt")', () => {
    const qa = qaMitGeometrie({ kante_an_maskengrenze: false, passed: true });
    expect(varianteMerkmale(node, undefined, qa).bauwerkVorhanden).toBe(false);
  });

  it('kante_an_maskengrenze fehlt: bauwerkVorhanden bleibt undefined, nicht false', () => {
    const qa = qaMitGeometrie({ passed: true });
    expect(varianteMerkmale(node, undefined, qa).bauwerkVorhanden).toBeUndefined();
  });
});

describe('P-BEFUNDSICHT — A/B-Vergleich (varianteDiff) traegt beide Zeilen', () => {
  it('unterschiedliche Tiefenstaffelung/Bauwerk-Urteile werden als abweichend markiert', () => {
    const a = varianteMerkmale(node, undefined, qaMitGeometrie({ rho_maske: 0.9, kante_an_maskengrenze: true, passed: true }));
    const b = varianteMerkmale(node, undefined, qaMitGeometrie({ rho_maske: 0.5, kante_an_maskengrenze: false, passed: true }));
    const zeilen = varianteDiff(a, b);
    const tiefe = zeilen.find((z) => z.label === 'Tiefenstaffelung');
    const bauwerk = zeilen.find((z) => z.label === 'Bauwerk vorhanden');
    expect(tiefe).toEqual({ label: 'Tiefenstaffelung', a: 'bestanden', b: 'verfehlt', abweichend: true });
    expect(bauwerk).toEqual({ label: 'Bauwerk vorhanden', a: 'ja', b: 'nein', abweichend: true });
  });

  it('beide Karten ohne Messung: beide Zeilen zeigen "—", nicht "verfehlt"/"nein"', () => {
    const a = varianteMerkmale(node, undefined, undefined);
    const b = varianteMerkmale(node, undefined, undefined);
    const zeilen = varianteDiff(a, b);
    expect(zeilen.find((z) => z.label === 'Tiefenstaffelung')).toEqual({
      label: 'Tiefenstaffelung',
      a: '—',
      b: '—',
      abweichend: false,
    });
    expect(zeilen.find((z) => z.label === 'Bauwerk vorhanden')).toEqual({
      label: 'Bauwerk vorhanden',
      a: '—',
      b: '—',
      abweichend: false,
    });
  });
});
