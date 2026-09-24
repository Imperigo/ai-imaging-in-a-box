import { describe, expect, it } from 'vitest';
import { bewertungsLage, varianteDiff, varianteMerkmale } from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';
import type { VisNode } from '@kosmo/kernel';

/**
 * N3 (V0959-N2N3-AUFTRAG) — die beiden additiven Vertragsfelder
 * `qa.geometry.status` (`GeometryStatus`, render-result.ts:209) und
 * `qa.geometry.nullprobe` (R4, render-result.ts:219) landen im Vertrag,
 * werden aber (Stand vor dieser Probe) von KEINEM Konsumenten gelesen.
 *
 * Zwei Ansprueche, je ein Block:
 * 1. `status` trennt «gemessen»/«nicht gemessen»/«nicht zustaendig» — bisher
 *    fiel «nicht zustaendig» in denselben Topf wie «nicht geschafft»
 *    (`bewertungsLage`/`nurAlteGeometrie`). Diese Probe belegt: die
 *    Unterscheidung ist jetzt SICHTBAR (eigene Diff-Tabellen-Zeile, eigener
 *    `bewertungsLage`-Fall), nicht nur intern typisiert.
 * 2. `nullprobe.rho_maske` ist der Anker, OHNE den «kein Score einzuordnen
 *    ist» (ROADMAP 1062: leeres Grundstueck 0.9848 gegen 0.9703 fuers
 *    perfekte Bild bei `geom_iou`). Diese Probe belegt: der Anker erscheint
 *    NEBEN dem Hauptwert (Tiefenstaffelung-Zeile) in der Vergleichstabelle —
 *    reines Zeigen, keine erfundene Ableitung (kein Score-minus-Nullprobe).
 */

const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };

describe('N3 — varianteMerkmale liest status und nullprobe', () => {
  it('ohne qa: beide Felder fehlen (kein Default, keine Aussage)', () => {
    const m = varianteMerkmale(node, undefined, undefined);
    expect(m.geometryStatus).toBeUndefined();
    expect(m.nullprobeRhoMaske).toBeUndefined();
  });

  it('qa ohne geometry: beide Felder fehlen weiterhin', () => {
    const qa: JobQa = { verdict: { passed: true } };
    const m = varianteMerkmale(node, undefined, qa);
    expect(m.geometryStatus).toBeUndefined();
    expect(m.nullprobeRhoMaske).toBeUndefined();
  });

  it('status "measured" wird wortgleich uebernommen', () => {
    const qa: JobQa = {
      geometry: { status: 'measured', rho_maske: 0.9, passed: true },
      verdict: { passed: true },
    };
    expect(varianteMerkmale(node, undefined, qa).geometryStatus).toBe('measured');
  });

  it('status "not_measured" wird wortgleich uebernommen', () => {
    const qa: JobQa = {
      geometry: { status: 'not_measured', passed: false },
      verdict: { passed: false },
    };
    expect(varianteMerkmale(node, undefined, qa).geometryStatus).toBe('not_measured');
  });

  it('status "not_applicable" wird wortgleich uebernommen — der Fall, der bisher unsichtbar war', () => {
    const qa: JobQa = {
      geometry: { status: 'not_applicable', passed: true },
      verdict: { passed: true },
    };
    expect(varianteMerkmale(node, undefined, qa).geometryStatus).toBe('not_applicable');
  });

  it('nullprobe.rho_maske wird als Zahl uebernommen', () => {
    const qa: JobQa = {
      geometry: { rho_maske: 0.94, nullprobe: { rho_maske: 0.42 }, passed: true },
      verdict: { passed: true },
    };
    expect(varianteMerkmale(node, undefined, qa).nullprobeRhoMaske).toBe(0.42);
  });

  it('nullprobe.rho_maske: null (P-NULLGEOMETRIE, nicht gemessen) zeigt sich wie fehlend, nicht wie 0', () => {
    const qa: JobQa = {
      geometry: { rho_maske: 0.94, nullprobe: { rho_maske: null }, passed: true },
      verdict: { passed: true },
    };
    expect(varianteMerkmale(node, undefined, qa).nullprobeRhoMaske).toBeUndefined();
  });

  it('nullprobe ganz ohne rho_maske (nur andere Masse gemeldet): Anker fehlt, keine erfundene Zahl', () => {
    const qa: JobQa = {
      geometry: { rho_maske: 0.94, nullprobe: { geom_iou: 0.98 }, passed: true },
      verdict: { passed: true },
    };
    expect(varianteMerkmale(node, undefined, qa).nullprobeRhoMaske).toBeUndefined();
  });
});

describe('N3 — varianteDiff zeigt Geometrie-Status und die Nullprobe NEBEN dem Hauptwert', () => {
  it('traegt eine Zeile "Geometrie-Status" mit den deutschen Uebersetzungen', () => {
    const a = varianteMerkmale(node, undefined, {
      geometry: { status: 'not_applicable', passed: true },
      verdict: { passed: true },
    } as JobQa);
    const b = varianteMerkmale(node, undefined, {
      geometry: { status: 'not_measured', passed: false },
      verdict: { passed: false },
    } as JobQa);
    const zeile = varianteDiff(a, b).find((z) => z.label === 'Geometrie-Status');
    expect(zeile).toBeDefined();
    expect(zeile!.a).toBe('nicht zuständig');
    expect(zeile!.b).toBe('nicht gemessen');
    expect(zeile!.abweichend).toBe(true);
  });

  it('ohne status-Feld: die Zeile zeigt "—", keine erfundene Aussage', () => {
    const a = varianteMerkmale(node, undefined, undefined);
    const b = varianteMerkmale(node, undefined, undefined);
    const zeile = varianteDiff(a, b).find((z) => z.label === 'Geometrie-Status');
    expect(zeile!.a).toBe('—');
    expect(zeile!.b).toBe('—');
  });

  it('traegt eine Zeile "Nullprobe (rho_maske)" — direkt neben "Tiefenstaffelung" (dem Hauptwert)', () => {
    const a = varianteMerkmale(node, undefined, {
      geometry: { rho_maske: 0.92, nullprobe: { rho_maske: 0.31 }, passed: true },
      verdict: { passed: true },
    } as JobQa);
    const b = varianteMerkmale(node, undefined, {
      geometry: { rho_maske: 0.71, nullprobe: { rho_maske: 0.68 }, passed: true },
      verdict: { passed: true },
    } as JobQa);
    const zeilen = varianteDiff(a, b);
    const idxTiefe = zeilen.findIndex((z) => z.label === 'Tiefenstaffelung');
    const idxNull = zeilen.findIndex((z) => z.label === 'Nullprobe (rho_maske)');
    expect(idxTiefe).toBeGreaterThanOrEqual(0);
    // Der Anker steht UNMITTELBAR neben dem Hauptwert, nicht irgendwo in der Tabelle.
    expect(idxNull).toBe(idxTiefe + 1);
    expect(zeilen[idxNull]!.a).toBe('0.31');
    expect(zeilen[idxNull]!.b).toBe('0.68');
  });

  it('ohne Nullprobe: "—", kein erfundener Wert und keine Ableitung (kein Score-minus-Nullprobe irgendwo in den Zeilen)', () => {
    const a = varianteMerkmale(node, undefined, {
      geometry: { rho_maske: 0.92, passed: true },
      verdict: { passed: true },
    } as JobQa);
    const b = varianteMerkmale(node, undefined, undefined);
    const zeilen = varianteDiff(a, b);
    const zeile = zeilen.find((z) => z.label === 'Nullprobe (rho_maske)');
    expect(zeile!.a).toBe('—');
    expect(zeile!.b).toBe('—');
    expect(zeilen.some((z) => /guete|güte/i.test(z.label))).toBe(false);
  });
});

describe('N3 — bewertungsLage: "nicht zustaendig" ist ein EIGENER, sichtbarer Fall — nicht "widerrufen"', () => {
  it('status "not_applicable" ergibt "nicht-zustaendig", auch wenn NUR die alten Geometrie-Zahlen vorliegen', () => {
    const qa = {
      geometry: {
        status: 'not_applicable',
        geometry_fidelity: 0.2,
        spearman: 0.3,
        geom_iou: 0.9,
        threshold: 0.65,
        passed: true,
        method: 'alt',
      },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0];
    // Vorher (ohne diese Unterscheidung) waere das "widerrufen" gewesen —
    // dieselbe Eingabe wie im bestehenden "widerrufen"-Test in
    // varianten-diff.test.ts, NUR mit status ergaenzt.
    expect(bewertungsLage(qa)).toBe('nicht-zustaendig');
    expect(bewertungsLage(qa)).not.toBe('widerrufen');
  });

  it('status "not_measured" aendert am bisherigen Verhalten NICHTS — NUR "not_applicable" bekommt eine eigene Lage', () => {
    const geometrieBasis = {
      geometry_fidelity: 0.2,
      spearman: 0.3,
      geom_iou: 0.9,
      threshold: 0.65,
      passed: true,
      method: 'alt',
    };
    const ohneStatus = {
      geometry: geometrieBasis,
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0];
    const mitNotMeasured = {
      geometry: { ...geometrieBasis, status: 'not_measured' },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0];
    // Dieselbe Geometrie-Grundlage, einmal mit "not_measured" ergaenzt — das
    // Urteil bleibt unveraendert "widerrufen" (nur "not_applicable" greift
    // vor der `nurAlteGeometrie`-Pruefung ein).
    expect(bewertungsLage(mitNotMeasured)).toBe(bewertungsLage(ohneStatus));
    expect(bewertungsLage(mitNotMeasured)).toBe('widerrufen');
  });

  it('ohne status-Feld: unveraendertes Verhalten (Regression gegen den bestehenden "widerrufen"-Fall)', () => {
    const qa = {
      geometry: {
        geometry_fidelity: 0.23,
        spearman: 0.4,
        geom_iou: 0.98,
        threshold: 0.65,
        passed: true,
        method: 'alt',
      },
      style: { style_score: 0.9, threshold: 0.3, passed: true, method: 'dinov3' },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0];
    expect(bewertungsLage(qa)).toBe('widerrufen');
  });

  it('alle vier Lagen sind wirklich paarweise unterscheidbar', () => {
    const ohne = bewertungsLage(undefined);
    const widerrufen = bewertungsLage({
      geometry: { geometry_fidelity: 0.2, spearman: 0.3, geom_iou: 0.9, threshold: 0.65, passed: true, method: 'alt' },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0]);
    const nichtZustaendig = bewertungsLage({
      geometry: { status: 'not_applicable', passed: true },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0]);
    const bewertet = bewertungsLage({
      style: { style_score: 0.9, threshold: 0.3, passed: true, method: 'dinov3' },
      verdict: { passed: true },
    } as unknown as Parameters<typeof bewertungsLage>[0]);
    expect(new Set([ohne, widerrufen, nichtZustaendig, bewertet]).size).toBe(4);
  });
});
