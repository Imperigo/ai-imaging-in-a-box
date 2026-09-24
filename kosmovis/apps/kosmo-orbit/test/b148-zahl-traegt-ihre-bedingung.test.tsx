// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { varianteMerkmale, type KuratierKartenDaten } from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';

/**
 * **B148 — die Zahl trägt die Bedingung, unter der sie gemessen wurde.**
 *
 * ## Woher der Auftrag kommt
 *
 * `auf-20260826-52` des KosmoVis-Workers, Regeln 2 und 3, wörtlich:
 *
 * > **Regel 2** — «Nicht messbar ist weder bestanden noch durchgefallen. Die
 * > Anzeige kennt drei Zustände, nicht zwei.»
 * >
 * > **Regel 3** — «Eine Zahl gehört an die Bedingung, unter der sie gemessen
 * > wurde. […] Sie werden bereits mitgeliefert. Heute liest sie niemand.»
 *
 * ## Der Befund, gemessen am Quelltext
 *
 * Der Kurations-Inspektor zeigte genau **eine** Zeile zum QA-Urteil:
 * `qa.verdict.passed ? 'bestanden' : 'verfehlt'` — ein `boolean`. Ein Lauf,
 * dessen Geometrie **gar nicht gemessen** wurde, las sich damit als
 * «verfehlt».
 *
 * Der dritte Zustand kam im Vertrag an (`qa.geometry.status`,
 * `render-result.ts:209`) und `varianteMerkmale()` berechnete ihn bereits —
 * gezeigt wurde er **nur in der A/B-Tabelle**, also genau dort, wo man zwei
 * Varianten vergleicht, und nicht dort, wo man eine einzelne beurteilt.
 * Dasselbe galt für den Nullproben-Anker.
 *
 * Die Schwelle (`qa.geometry.threshold`, Vertragsvorgabe 0.65) wurde
 * nirgends gelesen.
 *
 * ## Warum der Nullproben-Anker der wichtigste Wert davon ist
 *
 * Er sagt, was ein Bild **ohne jede Geometrie** auf **dieser** Szene
 * erreicht. Gemessen erreichte ein leeres Grundstück **0.9848**, wo das
 * perfekte Bild **0.9703** erreichte (ROADMAP 1062). Eine Zahl wie 0.97 liest
 * sich gut, bis man weiss, dass nichts auf der Szene 0.98 erreicht.
 *
 * ## Was diese Probe prüft
 *
 * Dass die drei Werte **im Inspektor** ankommen, dass sie **fehlen**, wenn der
 * Vertrag sie nicht liefert (keine erfundene Zahl, keine erfundene
 * Verneinung), und dass das Verdikt selbst **unverändert** bleibt — die
 * Fläche zeigt an und urteilt nicht.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/** Ein Lauf, dessen Geometrie NICHT gemessen wurde, dessen Verdikt aber steht. */
function qaNichtGemessen(): JobQa {
  return {
    geometry: { status: 'not_measured', threshold: 0.65, rho_maske: 0.91, nullprobe: { rho_maske: 0.98 } },
    verdict: { passed: false },
  };
}

/** Gegenprobe: der Vertrag sagt zu alldem nichts. */
function qaOhneAngaben(): JobQa {
  return { geometry: {}, verdict: { passed: true } };
}

describe('varianten-diff — die Schwelle wird aus dem Vertrag gelesen', () => {
  const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };

  it('nimmt qa.geometry.threshold auf', () => {
    expect(varianteMerkmale(node, undefined, qaNichtGemessen()).geometrieSchwelle).toBe(0.65);
  });

  it('Gegenprobe: ohne Angabe im Vertrag bleibt das Feld weg — keine erfundene Schwelle', () => {
    expect(varianteMerkmale(node, undefined, qaOhneAngaben()).geometrieSchwelle).toBeUndefined();
  });

  it('Gegenprobe: `null` im Vertrag heisst «keine angewendet», nicht «0»', () => {
    const qa: JobQa = { geometry: { threshold: null }, verdict: { passed: true } };
    expect(varianteMerkmale(node, undefined, qa).geometrieSchwelle).toBeUndefined();
  });
});

describe('KuratierInspektor — drei Zustände statt zwei, und die Zahl mit ihrer Bedingung', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root!.unmount());
      root = null;
    }
    if (container) {
      container.remove();
      container = null;
    }
  });

  function render(qa: JobQa) {
    const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
    const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'Test', nodes: [node], edges: [] };
    const karte: KuratierKartenDaten = {
      node,
      quelle: { jobId: 'vis-1788277501-b799e4', bild: 'a.png', qa },
      kur: { markiert: false, verworfen: false },
    };
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(
        <KuratierInspektor
          graph={graph}
          karte={karte}
          id="V-01"
          onMarkieren={() => {}}
          onVerwerfen={() => {}}
          onInsProjekt={() => {}}
        />,
      );
    });
    return container!.textContent ?? '';
  }

  it('zeigt den dritten Zustand «nicht gemessen» neben dem Verdikt', () => {
    const text = render(qaNichtGemessen());
    expect(text).toContain('Geometrie-Status');
    expect(text).toContain('nicht gemessen');
  });

  it('schreibt das Verdikt NICHT um — die Fläche zeigt an und urteilt nicht', () => {
    const text = render(qaNichtGemessen());
    expect(text).toContain('QA-Verdikt');
    // `verdict.passed` ist false und bleibt «verfehlt»; der Status steht
    // DANEBEN, er ersetzt das Urteil nicht.
    expect(text).toContain('verfehlt');
  });

  it('zeigt die Schwelle, gegen die gemessen wurde', () => {
    const text = render(qaNichtGemessen());
    expect(text).toContain('Schwelle');
    expect(text).toContain('0.65');
  });

  it('zeigt den Nullproben-Anker neben seinem Hauptwert', () => {
    const text = render(qaNichtGemessen());
    expect(text).toContain('Nullprobe');
    expect(text).toContain('0.98');
  });

  it('KONTROLLFALL — ohne Angaben im Vertrag erscheint keine der drei Zeilen', () => {
    const text = render(qaOhneAngaben());
    expect(text).not.toContain('Geometrie-Status');
    expect(text).not.toContain('Schwelle');
    expect(text).not.toContain('Nullprobe');
  });

  it('KONTROLLFALL — der Inspektor rendert überhaupt etwas', () => {
    const text = render(qaOhneAngaben());
    expect(text).toContain('Kurations-Inspektor');
  });
});
