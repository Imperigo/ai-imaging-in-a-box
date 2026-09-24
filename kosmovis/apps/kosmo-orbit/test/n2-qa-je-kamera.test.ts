import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import {
  kameraQaZeilen,
  type KuratierKartenDaten,
  type JobQaJeKameraEintrag,
} from '../src/modules/vis/varianten-diff';
import { KuratierFlaeche } from '../src/modules/vis/KuratierFlaeche';
import type { JobQa } from '../src/modules/vis/vis-jobs';
import type { VisGraph, VisNode } from '@kosmo/kernel';

// Diese Probe bleibt bewusst `.test.ts` (kein JSX-Syntax-Zucker, reines
// `createElement`) — nur `.tsx`-Dateien werden hier mit dem JSX-Parser
// uebersetzt (`@vitejs/plugin-react`/esbuild-Default, `vite.config.ts` setzt
// keinen abweichenden Loader fuer `.ts`), und der Dateiname war im Auftrag
// wortwoertlich mit `.ts` vorgegeben.

/**
 * N2 (V0959-N2N3-AUFTRAG, auf-20260826-49 Posten B5) — `qa_je_kamera` steht
 * NEBEN dem bestehenden `qa`-Block im Vertrag (render-result.ts:375, ein
 * Geschwisterfeld, kein Kind) und wird (Stand vor dieser Probe) von KEINEM
 * Konsumenten gelesen. Woertlich der Absender: «Wer drei Ansichten bestellt
 * und eine davon faellt durch, sieht heute 'durchgefallen' und nicht,
 * WELCHE.»
 *
 * Zwei Bloecke:
 * 1. `kameraQaZeilen` — die reine Ableitungsfunktion (kein React), die aus
 *    `qa_je_kamera` je Kamera ein Ja/Nein-Urteil liest (nur Kombination
 *    bereits berechneter `passed`-Flaggen, keine neue Schwelle).
 * 2. Die Oberflaeche (`KuratierFlaeche.tsx`): das Raster zeigt je Karte
 *    sichtbar, WELCHE Kamera durchfiel, waehrend der bestehende `qa`-Block
 *    (QA-Verdikt) UNVERAENDERT weiterhin die Hauptauskunft bleibt. Fehlt
 *    `qa_je_kamera`, bleibt die Oberflaeche wie vor diesem Paket.
 */

function kamera(
  name: string,
  opts: { geometryBestanden?: boolean; styleBestanden?: boolean } = {},
): JobQaJeKameraEintrag {
  return {
    kamera: name,
    ...(opts.geometryBestanden !== undefined
      ? { geometry: { passed: opts.geometryBestanden } }
      : {}),
    ...(opts.styleBestanden !== undefined ? { style: { passed: opts.styleBestanden } } : {}),
  } as JobQaJeKameraEintrag;
}

describe('kameraQaZeilen — reine Ableitung, keine neue Schwelle', () => {
  it('undefined/leer: leere Liste', () => {
    expect(kameraQaZeilen(undefined)).toEqual([]);
    expect(kameraQaZeilen([])).toEqual([]);
  });

  it('eine Kamera, Geometrie UND Stil bestanden: bestanden:true', () => {
    const zeilen = kameraQaZeilen([kamera('front', { geometryBestanden: true, styleBestanden: true })]);
    expect(zeilen).toEqual([
      { kamera: 'front', geometryBestanden: true, styleBestanden: true, bestanden: true },
    ]);
  });

  it('Geometrie bestanden, Stil NICHT: die Kamera gilt insgesamt als durchgefallen (UND-Verknuepfung, keine neue Zahl)', () => {
    const zeilen = kameraQaZeilen([kamera('seite', { geometryBestanden: true, styleBestanden: false })]);
    expect(zeilen[0]!.bestanden).toBe(false);
  });

  it('weder Geometrie- noch Stil-QA fuer diese Kamera: bestanden bleibt undefined (keine erfundene Aussage)', () => {
    const zeilen = kameraQaZeilen([kamera('rueckseite')]);
    expect(zeilen[0]).toEqual({ kamera: 'rueckseite' });
  });

  it('DER Kernfall: drei Kameras, GENAU EINE faellt durch — das Urteil ist je Kamera unterscheidbar', () => {
    const zeilen = kameraQaZeilen([
      kamera('front', { geometryBestanden: true, styleBestanden: true }),
      kamera('seite', { geometryBestanden: false, styleBestanden: true }),
      kamera('oben', { geometryBestanden: true, styleBestanden: true }),
    ]);
    expect(zeilen.map((z) => [z.kamera, z.bestanden])).toEqual([
      ['front', true],
      ['seite', false],
      ['oben', true],
    ]);
  });
});

// ── Oberflaeche ─────────────────────────────────────────────────────────

const node = (id: string, typ = 'render'): VisNode => ({ id, typ, x: 0, y: 0, params: {} });
const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'g', nodes: [node('n1'), node('n2')], edges: [] };

const HAUPT_QA: JobQa = { verdict: { passed: true } };

function karteMit(quelleZusatz: {
  qa?: JobQa;
  qaJeKamera?: JobQaJeKameraEintrag[];
}): KuratierKartenDaten {
  return {
    node: node('n1'),
    quelle: { jobId: 'vis-1-abcdef', bild: 'out_0.png', qa: quelleZusatz.qa, qaJeKamera: quelleZusatz.qaJeKamera },
    kur: { markiert: false, verworfen: false },
  };
}

function renderRaster(karten: KuratierKartenDaten[]): string {
  return renderToStaticMarkup(
    createElement(KuratierFlaeche, {
      graph,
      karten,
      vergleichAuswahl: [],
      onMarkieren: () => {},
      onVerwerfen: () => {},
      onVergleichWahl: () => {},
    }),
  );
}

describe('KuratierFlaeche — qa_je_kamera wird je Kamera sichtbar, der qa-Block bleibt unveraendert Hauptauskunft', () => {
  it('ohne qa_je_kamera: KEIN Kamera-Block im Markup — "bleibt alles wie heute"', () => {
    const html = renderRaster([karteMit({ qa: HAUPT_QA })]);
    expect(html).not.toContain('data-testid="vis-kuratier-kamera-qa"');
  });

  it('mit qa_je_kamera: der Kamera-Block erscheint, UND jede Kamera einzeln mit ihrem eigenen Urteil', () => {
    const html = renderRaster([
      karteMit({
        qa: HAUPT_QA,
        qaJeKamera: [
          kamera('front', { geometryBestanden: true, styleBestanden: true }),
          kamera('seite', { geometryBestanden: false, styleBestanden: true }),
        ],
      }),
    ]);
    expect(html).toContain('data-testid="vis-kuratier-kamera-qa"');
    expect(html).toContain('front');
    expect(html).toContain('seite');
    expect(html).toContain('durchgefallen');
    expect(html).toContain('bestanden');
  });

  it('der bestehende qa-Block bleibt die Hauptauskunft — QA-Verdikt-Text ist unabhaengig von qa_je_kamera identisch', () => {
    const ohneKamera = renderRaster([karteMit({ qa: HAUPT_QA })]);
    const mitKamera = renderRaster([
      karteMit({ qa: HAUPT_QA, qaJeKamera: [kamera('front', { geometryBestanden: false })] }),
    ]);
    // Beide Male traegt die Karte dieselbe Kennung/Meta-Zeile — qa_je_kamera
    // steht NUR daneben (zusaetzlicher Block), veraendert die bestehende
    // Kartenstruktur nicht.
    expect(ohneKamera).toContain('data-testid="vis-kuratier-karte"');
    expect(mitKamera).toContain('data-testid="vis-kuratier-karte"');
  });
});
