// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { execute, KosmoDoc } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/** jsdom kennt `ResizeObserver` nicht; `NodeCanvas` beobachtet damit seine
 *  Flaechengroesse. Attrappe wie in `auf-20260901-70-wartet-grund.test.tsx`. */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;

/**
 * **P-HOOKS-ORDNUNG — der Knotengraph zog sich vor fuenf Hooks zurueck.**
 *
 * `NodeCanvas` trug `if (!graph) return null;` MITTEN in der Komponente, und
 * darunter standen fuenf weitere `useEffect`. `react-hooks/rules-of-hooks`
 * meldete das fuenfmal; im gedeckelten Bestand stand es als «geduldeter
 * Altfall».
 *
 * **Es war keine Formalie.** Verschwindet der Graph, waehrend die Komponente
 * steht — Graph geloescht, Projekt gewechselt, Wurzel neu geladen —, rendert
 * React beim naechsten Durchlauf WENIGER Hooks als beim vorigen und wirft
 * «Rendered fewer hooks than expected». Das ist ein harter Abbruch.
 *
 * **Diese Probe stellt genau diesen Uebergang her**: erst mit Graph rendern
 * (alle Hooks laufen), dann den Graphen aus dem Projekt nehmen und erneut
 * rendern. Vorher stuerzte das ab, nachher nicht.
 *
 * Warum das nicht als Lint-Regel genuegt: der Deckel duldete den Zustand
 * bereits, und eine geduldete Regelverletzung meldet sich nie wieder. Erst
 * ein Fall, der den ABSTURZ herstellt, macht aus einer Zaehlung einen Beweis.
 */

let root: Root | null = null;
let wirt: HTMLDivElement | null = null;

afterEach(() => {
  if (root) act(() => root!.unmount());
  wirt?.remove();
  root = null;
  wirt = null;
  vi.restoreAllMocks();
});

function docMitGraph(): string {
  const doc = new KosmoDoc();
  const graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: graphId });
  return graphId;
}

describe('NodeCanvas ueberlebt den Verlust seines Graphen', () => {
  it('KONTROLLFALL: mit Graph rendert die Flaeche ueberhaupt etwas', () => {
    const graphId = docMitGraph();
    wirt = document.createElement('div');
    document.body.appendChild(wirt);
    root = createRoot(wirt);
    act(() => root!.render(<NodeCanvas graphId={graphId} />));
    expect(wirt.querySelector('svg'), 'ohne Ausgabe belegt der Fall unten nichts').not.toBeNull();
  });

  it('nimmt man der STEHENDEN Komponente den Graphen weg, rendert sie leer statt abzustuerzen', () => {
    const graphId = docMitGraph();
    wirt = document.createElement('div');
    document.body.appendChild(wirt);
    root = createRoot(wirt);

    // 1. Durchlauf: Graph da, ALLE Hooks laufen.
    act(() => root!.render(<NodeCanvas graphId={graphId} />));
    expect(wirt.querySelector('svg')).not.toBeNull();

    // React meldet einen Renderfehler zusaetzlich ueber die Konsole. Wir
    // fangen sie ab, damit ein Absturz nicht als Rauschen durchgeht, sondern
    // als Befund zaehlt.
    const fehler: unknown[] = [];
    vi.spyOn(console, 'error').mockImplementation((...a: unknown[]) => {
      fehler.push(a);
    });

    // 2. Durchlauf: derselbe `graphId`, aber das Projekt kennt ihn nicht mehr
    // — genau der Zustand nach einem Graph-Loeschen oder Projektwechsel.
    act(() => {
      useProject.setState({ doc: new KosmoDoc(), journal: [], revision: 1, activeStoreyId: null, selection: [] });
      root!.render(<NodeCanvas graphId={graphId} />);
    });

    expect(wirt.querySelector('svg'), 'die Flaeche zeichnet ohne Graph weiter').toBeNull();
    const hooksFehler = fehler.filter((f) => JSON.stringify(f).includes('fewer hooks'));
    expect(hooksFehler, `React hat die Hook-Reihenfolge beanstandet: ${JSON.stringify(hooksFehler)}`).toHaveLength(0);
  });

  it('und der Weg zurueck geht auch — Graph wieder da, Flaeche wieder da', () => {
    // Der Gegenfall. Eine Fassung, die nach dem Verlust dauerhaft leer
    // bliebe, waere oben gruen und hier rot.
    const graphId = docMitGraph();
    const gesichert = useProject.getState().doc;
    wirt = document.createElement('div');
    document.body.appendChild(wirt);
    root = createRoot(wirt);
    act(() => root!.render(<NodeCanvas graphId={graphId} />));
    act(() => {
      useProject.setState({ doc: new KosmoDoc(), journal: [], revision: 1, activeStoreyId: null, selection: [] });
      root!.render(<NodeCanvas graphId={graphId} />);
    });
    expect(wirt.querySelector('svg')).toBeNull();
    act(() => {
      useProject.setState({ doc: gesichert, journal: [], revision: 2, activeStoreyId: null, selection: [] });
      root!.render(<NodeCanvas graphId={graphId} />);
    });
    expect(wirt.querySelector('svg'), 'die Flaeche kommt nicht zurueck').not.toBeNull();
  });
});
