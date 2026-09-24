// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';
import type { VisGraph } from '@kosmo/kernel';

// Gleiche zwei Stubs wie `node-canvas-pan.test.tsx` (F6) — jsdom kennt weder
// ResizeObserver noch PointerCapture; ohne die Stubs würde NodeCanvas an
// einer reinen Testumgebungslücke scheitern, nicht an der geprüften Logik.
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
if (!('setPointerCapture' in Element.prototype)) {
  Object.assign(Element.prototype, {
    setPointerCapture(): void {},
    releasePointerCapture(): void {},
    hasPointerCapture(): boolean {
      return false;
    },
  });
}

/**
 * P-ZWEITKANTE (`docs/MESSUNG-GRAPHSTART-ZWEITKANTE-2026-08-24.md`) — Fund B
 * ("die zweite Kante in Folge geht verloren").
 *
 * Die LIVE-Messung (Playwright, echtes Chromium, roh im Bericht) zeigt: ein
 * zweiter unmittelbar folgender Kanten-Zug bricht mit `pointercancel` ab,
 * NICHT mit `pointerup` — ein bekanntes, in `e2e/vis-editor.spec.ts`
 * (`dragReset`-Helfer) bereits dokumentiertes Chromium/Playwright-Verhalten
 * bei zwei echten Mehrschritt-Drags im selben Testlauf, kein App-Fehler
 * (Beleg im Bericht). Der eigentliche App-Fehler, den diese Messung
 * TROTZDEM aufgedeckt hat: `NodeCanvas.tsx`s `onPointerUp` räumt `pending`
 * auf, ein `onPointerCancel` fehlte dafür komplett. Bricht die Geste mit
 * `pointercancel` ab, blieb `pending` (die begonnene, nie fertig gezogene
 * Kante) stehen — und der NÄCHSTE, völlig unabhängige Klick auf irgendeinen
 * typkompatiblen Eingangs-Port (dessen `onPointerUp`-Handler nur
 * `if (!pending) return` prüft) verband dann lautlos die ALTE Quelle mit
 * einem Ziel, das der Nutzer nie gezogen hat — ohne Fehlermeldung, ohne
 * Drag, einfach eine falsche Kante.
 *
 * Dieser Test simuliert genau die Browser-Events, die die Live-Messung
 * aufgezeichnet hat (`pointerdown` auf dem Quell-Port, dann `pointercancel`
 * auf dem SVG statt `pointerup`) und danach einen GANZ GEWÖHNLICHEN
 * `pointerup` auf einem fremden, unbeteiligten Eingangs-Port — ohne
 * vorangehenden Drag an dieser Stelle. Vor der Reparatur (kein
 * `onPointerCancel`) entsteht daraus eine Kante; danach nicht.
 */
describe('NodeCanvas — P-ZWEITKANTE: pointercancel muss `pending` aufräumen', () => {
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

  function neuerGraphMitZweiRenderZielen(): string {
    const { runCommand } = useProject.getState();
    const res = runCommand('vis.graphErstellen', { name: `P-ZWEITKANTE-Test-${Math.random()}` });
    const graphId = (res.patches[0] as { id: string }).id;
    runCommand('vis.nodeSetzen', { graphId, typ: 'kamera', x: 40, y: 40 });
    runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 400, y: 40 });
    runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 400, y: 300 });
    return graphId;
  }

  /** Hit-Kreis eines Ports = der ZWEITE `<circle>` in dessen `<g>` (der
   *  sichtbare Port-Kreis trägt `data-testid`, der Hit-Kreis darüber nicht —
   *  identisch zur Struktur, die `NodeCanvas.tsx` (Ein-/Ausgänge-Blöcke) rendert). */
  function hitKreisVon(sichtbarerPort: Element): SVGCircleElement {
    const hit = sichtbarerPort.nextElementSibling;
    expect(hit).not.toBeNull();
    expect(hit!.getAttribute('class')).toContain('vis-node-port-hit');
    return hit as SVGCircleElement;
  }

  function feuere(el: Element, typ: string): void {
    const ev = new MouseEvent(typ, { bubbles: true, cancelable: true, button: 0 });
    Object.defineProperty(ev, 'pointerId', { value: 1, configurable: true });
    el.dispatchEvent(ev);
  }

  it('lässt nach pointercancel KEINE Kante mehr aus einem fremden, späteren Klick entstehen', () => {
    const graphId = neuerGraphMitZweiRenderZielen();

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });

    const svg = container.querySelector('[data-testid="node-canvas"]') as SVGSVGElement;
    expect(svg).not.toBeNull();

    const kameraNode = container.querySelector('[data-testid="vis-node-kamera"]')!;
    const renderNodes = container.querySelectorAll('[data-testid="vis-node-render"]');
    expect(renderNodes).toHaveLength(2);
    const [, zweitesRender] = renderNodes; // das Ziel, das der Nutzer NIE angefasst hat

    const kameraAusgang = kameraNode.querySelector('[data-testid="port-out-kameras"]')!;
    const zweitesRenderEingang = zweitesRender.querySelector('[data-testid="port-in-kameras"]')!;

    // 1) Zug beginnt: pointerdown auf dem Quell-Port — setzt `pending`.
    act(() => {
      feuere(hitKreisVon(kameraAusgang), 'pointerdown');
    });

    // 2) Die Geste bricht ab — GENAU das Event, das die Live-Messung für den
    //    zweiten Zug in Folge aufgezeichnet hat: `pointercancel`, kein
    //    `pointerup`.
    act(() => {
      feuere(svg, 'pointercancel');
    });

    // 3) Später, unabhängig: ein GEWÖHNLICHER Klick auf einen fremden
    //    Eingangs-Port (kein Drag, kein pointerdown davor an dieser Stelle —
    //    z.B. ein Hover-Klick zum Anschauen des zweiten Render-Nodes).
    act(() => {
      feuere(hitKreisVon(zweitesRenderEingang), 'pointerup');
    });

    const graph = useProject.getState().doc.get<VisGraph>(graphId)!;
    expect(graph.edges).toHaveLength(0);
  });

  it('Gegenprobe: ohne pointercancel dazwischen verbindet derselbe Klick wie erwartet (der Handler selbst ist intakt)', () => {
    const graphId = neuerGraphMitZweiRenderZielen();

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });

    const kameraNode = container.querySelector('[data-testid="vis-node-kamera"]')!;
    const renderNodes = container.querySelectorAll('[data-testid="vis-node-render"]');
    const [erstesRender] = renderNodes;

    const kameraAusgang = kameraNode.querySelector('[data-testid="port-out-kameras"]')!;
    const erstesRenderEingang = erstesRender.querySelector('[data-testid="port-in-kameras"]')!;

    act(() => {
      feuere(hitKreisVon(kameraAusgang), 'pointerdown');
    });
    act(() => {
      feuere(hitKreisVon(erstesRenderEingang), 'pointerup');
    });

    const graph = useProject.getState().doc.get<VisGraph>(graphId)!;
    expect(graph.edges).toHaveLength(1);
  });
});
