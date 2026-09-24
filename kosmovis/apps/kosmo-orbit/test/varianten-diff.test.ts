import { describe, expect, it } from 'vitest';
import { bewertungsLage, sterneAusQa } from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';

/**
 * v0.9.42 P-QA-ZAHLEN/P-NULL-EHRLICH (`docs/V0942-SPEZ.md` §2/§3,
 * `docs/ANTWORT-CLOUDWORKER-2026-08-22.md` §1/§2): `sterneAusQa` mittelte
 * bis hierhin `geometry_fidelity` UND `style_score` zu einer Sternebewertung
 * — genau das «Abzeichen auf widerlegter Grundlage», das der Cloud-Worker
 * an unserer eigenen Oberflaeche gemessen hat (`geom_iou` belohnt ein leeres
 * Grundstueck mit 0.9848, `geometry_fidelity` ist nicht monoton). Diese
 * Suite belegt: `geometry_fidelity` fliesst nicht mehr ein, ganz gleich ob
 * alt, neu oder gemischt — und liegen NUR die alten, widerlegten
 * Geometrie-Zahlen vor, zeigt die Oberflaeche gar KEIN Urteil mehr (Sterne
 * 0), auch nicht mit gueltigem `style_score` daneben (kein stilles
 * Weiterrechnen mit der halben Grundlage).
 */
describe('sterneAusQa', () => {
  it('ohne QA: 0 Sterne (unveraendert)', () => {
    expect(sterneAusQa(undefined)).toBe(0);
  });

  it('nur die alten, widerlegten Geometrie-Zahlen: kein Urteil (0), auch mit gueltigem Stil-Score', () => {
    const qa: JobQa = {
      geometry: { geometry_fidelity: 0.81, spearman: 0.9, geom_iou: 0.73, threshold: 0.65, passed: true, method: 'depthanything-v2-redepth' },
      style: { style_score: 0.9, threshold: 0.3, passed: true, method: 'dinov3' },
      verdict: { passed: true },
    };
    expect(sterneAusQa(qa)).toBe(0);
  });

  it('nur die alten Geometrie-Zahlen, ohne Stil-Score: ebenfalls 0 (nicht der verdict-Fallback)', () => {
    const qa: JobQa = {
      geometry: { geometry_fidelity: 0.81, spearman: 0.9, geom_iou: 0.73, threshold: 0.65, passed: true, method: 'depthanything-v2-redepth' },
      verdict: { passed: true },
    };
    expect(sterneAusQa(qa)).toBe(0);
  });

  it('neue Geometrie-Felder vorhanden: Geometrie traegt weiterhin NICHTS zur Sterne-Mittelung bei, Stil-Score allein zaehlt', () => {
    const qa: JobQa = {
      geometry: {
        rho_maske: 0.93,
        kante: 0.4,
        paarurteil: { rho_maske: 0.93, kante: 0.4 },
        threshold: 0.65,
        passed: true,
        method: 'depthanything-v2-redepth',
      },
      style: { style_score: 0.8, threshold: 0.3, passed: true, method: 'dinov3' },
      verdict: { passed: true },
    };
    // Math.round(0.8 * 5) = 4 — exakt der Stil-Score allein, geometry_fidelity
    // existiert in diesem Objekt gar nicht mehr und kann daher nicht einfliessen.
    expect(sterneAusQa(qa)).toBe(4);
  });

  it('alte UND neue Geometrie-Felder gleichzeitig (Uebergangszeit): gilt als NICHT "nur alt" — Stil-Score allein zaehlt', () => {
    const qa: JobQa = {
      geometry: {
        geometry_fidelity: 0.1, // absichtlich niedrig — darf keinen Einfluss mehr haben
        rho_maske: 0.93,
        kante: 0.4,
        paarurteil: { rho_maske: 0.93, kante: 0.4 },
        threshold: 0.65,
        passed: true,
        method: 'depthanything-v2-redepth',
      },
      style: { style_score: 1, threshold: 0.3, passed: true, method: 'dinov3' },
      verdict: { passed: true },
    };
    expect(sterneAusQa(qa)).toBe(5);
  });

  it('kein Geometrie-QA ueberhaupt, nur Stil-Score: unveraendertes Verhalten', () => {
    const qa: JobQa = {
      style: { style_score: 0.6, threshold: 0.3, passed: true, method: 'dinov3' },
      verdict: { passed: true },
    };
    expect(sterneAusQa(qa)).toBe(3);
  });

  it('P-NULL-EHRLICH: style_score:null (Belichtungsrahmen-Verfahren) faellt auf den verdict-Fallback zurueck, keine Geometrie-Kontamination', () => {
    const qa: JobQa = {
      style: { style_score: null, threshold: null, passed: true, method: 'belichtungsrahmen/hausstil' },
      verdict: { passed: true },
    };
    expect(sterneAusQa(qa)).toBe(4);
  });

  it('weder Geometrie- noch Stil-Zahl vorhanden: verdict-Fallback (4 bestanden / 2 nicht bestanden), unveraendert', () => {
    const bestanden: JobQa = { verdict: { passed: true } };
    const nicht: JobQa = { verdict: { passed: false } };
    expect(sterneAusQa(bestanden)).toBe(4);
    expect(sterneAusQa(nicht)).toBe(2);
  });
});

/**
 * v0.9.42-Nachtrag: «nichts zurueckbekommen» und «Grundlage widerrufen»
 * sahen in der Oberflaeche gleich aus — beides null Sterne, derselbe Satz.
 * Der zweite Fall ist der gefaehrlichere, weil er wie der erste aussieht:
 * er heisst «geprueft, und das Ergebnis taugt nichts», nicht «noch nicht
 * geprueft».
 */
describe('bewertungsLage — drei Faelle, nicht zwei', () => {
  it('ohne QA: ohne-qa', () => {
    expect(bewertungsLage(undefined)).toBe('ohne-qa');
  });

  it('NUR die widerlegten Geometrie-Zahlen: widerrufen — auch mit gueltigem Stilwert daneben', () => {
    const qa = {
      geometry: { geometry_fidelity: 0.23, spearman: 0.4, geom_iou: 0.98, threshold: 0.65, passed: true, method: 'alt' },
      style: { style_score: 0.9, threshold: 0.3, passed: true, method: 'dinov3' },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0];
    expect(bewertungsLage(qa)).toBe('widerrufen');
    // Kein stilles Weiterrechnen mit der Haelfte der Grundlage.
    expect(sterneAusQa(qa)).toBe(0);
  });

  it('mit den neuen Zahlen: bewertet oder ohne-qa, aber NIE widerrufen', () => {
    const qa = {
      geometry: { rho_maske: -0.94, kante: 0.71, paarurteil: { rho_maske: -0.94, kante: 0.71 }, passed: true },
      style: { style_score: 0.8, threshold: 0.3, passed: true, method: 'dinov3' },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0];
    expect(bewertungsLage(qa)).not.toBe('widerrufen');
  });

  // Gegenprobe: die Funktion sagt nicht zu allem dasselbe.
  it('die drei Faelle sind wirklich unterscheidbar', () => {
    const ohne = bewertungsLage(undefined);
    const alt = bewertungsLage({
      geometry: { geometry_fidelity: 0.2, spearman: 0.3, geom_iou: 0.9, threshold: 0.65, passed: true, method: 'alt' },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0]);
    expect(new Set([ohne, alt]).size).toBe(2);
  });
});

describe('P-KANTENANTEIL (22.08.) — SEIN Feldname darf nicht als «alte Zahlen» gelten', () => {
  /**
   * `nurAlteGeometrie()` fragte bis zum 22.08. nur nach `kante` — dem Namen,
   * zu dem ich das Feld in v0.9.42 abgekuerzt hatte. Der Cloud-Worker
   * schickt `kantenanteil`. Ein Ergebnis mit SEINEM Namen waere hier
   * faelschlich als «nur alte Zahlen» eingestuft worden und haette den Satz
   * «Bewertung zurueckgezogen — die Grundlage dieser Zahlen ist widerlegt»
   * bekommen, OBWOHL die tragfaehigen Zahlen vorlagen.
   *
   * Das ist die zweite Haelfte desselben Fehlers wie im Vertrag: dort waere
   * der Befund abgewiesen worden, hier waere er als widerlegt dargestellt
   * worden. Beide Male haette die Demo eine falsche Aussage gezeigt.
   */
  it('ein Ergebnis mit `kantenanteil` (sein Name) ist NICHT widerrufen', () => {
    const qa = {
      geometry: { kantenanteil: 0.874, passed: true },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0];
    expect(bewertungsLage(qa)).not.toBe('widerrufen');
  });

  it('ein Ergebnis mit `kante` (Zweitname aus v0.9.42) ebenfalls nicht — nichts Gebautes bricht', () => {
    const qa = {
      geometry: { kante: 0.4, passed: true },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0];
    expect(bewertungsLage(qa)).not.toBe('widerrufen');
  });

  it('NUR die alten vier bleiben widerrufen — die Unterscheidung ueberlebt den Nachtrag', () => {
    const qa = {
      geometry: { geometry_fidelity: 0.8, geom_iou: 0.97, threshold: 0.65, passed: true },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0];
    expect(bewertungsLage(qa)).toBe('widerrufen');
  });
});
