// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';

// jsdom kennt kein ResizeObserver — NodeCanvas nutzt es nur, um die
// Container-Grösse für die viewBox zu messen (P6-Review #6), für den
// Pan-Absturz irrelevant. Ein No-Op-Stub reicht, damit useLayoutEffect nicht
// mit «ResizeObserver is not defined» abbricht.
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// jsdom implementiert (Pointer Capture-)`setPointerCapture`/`releasePointer-
// Capture` gar nicht (echte Browser tun das) — ein No-Op-Stub, damit dieser
// Test wirklich die panning.current-Race prüft, statt an einer reinen
// Testumgebungslücke vorbeizulaufen.
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
 * v0.6.4 / F6 — Owner-Befund (Live-Test 0.6.3-Desktop): «KosmoVis ist auf
 * einen Fehler gelaufen» beim Pannen des Node-Trees.
 *
 * Ursache (NodeCanvas.tsx, onPointerMove-Handler des Hintergrund-Pans): der
 * Code las `panning.current` (ein Ref, in Echtzeit mutierbar) NICHT beim
 * Event, sondern LAZY innerhalb der `setView(v => ...)`-Updater-Funktion.
 * React ruft Updater-Funktionen erst auf, wenn der Zustand tatsächlich
 * verarbeitet wird — feuert dazwischen ein `pointerup` (setzt
 * `panning.current = null`, z.B. weil der Browser mehrere pointermove/-up
 * in einem Batch verarbeitet, bevor ein älterer pointermove-Updater lief),
 * liest der Updater den Ref als `null`: «Cannot read properties of null
 * (reading 'cx')» — von der KFehlerzone gefangen.
 *
 * Dieser Test stellt die Race MIT nativen PointerEvents nach (synchrones
 * down → viele move → up, ohne Yield an die Event-Loop dazwischen — exakt
 * das Timing, das den Ref vor dem Fix als null erwischen konnte). Er ist
 * VOR dem Fix (Lesen von `panning.current!.cx` direkt im Updater) rot
 * (unhandled TypeError) und NACH dem Fix (lokale Konstante beim Event
 * geschnappt) grün.
 */
describe('NodeCanvas — F6 Pan-Absturz (Owner-Befund v0.6.4)', () => {
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

  function neuerGraphMitKamera(): string {
    const { runCommand, doc } = useProject.getState();
    const res = runCommand('vis.graphErstellen', { name: `F6-Test-${Math.random()}` });
    const graphId = (res.patches[0] as { id: string }).id;
    // A10-Kamera-Node dazu — der Owner-Verdacht («neue Node-Art bricht eine
    // Annahme im Renderer») gehört mit ins Repro.
    runCommand('vis.nodeSetzen', { graphId, typ: 'kamera', x: 40, y: 40 });
    runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 400, y: 40 });
    void doc;
    return graphId;
  }

  function feuereRaceSequence(svg: SVGSVGElement) {
    const rect = svg.getBoundingClientRect();
    const cx = rect.left + 400;
    const cy = rect.top + 300;
    // jsdom kennt (noch) kein PointerEvent/setPointerCapture (nachgewiesen:
    // beide sind `undefined`) — NodeCanvas liest vom Event nur clientX/
    // clientY/target (echte MouseEvent-Felder) und optional-chained
    // pointerId/setPointerCapture. Ein MouseEvent mit angehängtem
    // `pointerId` reicht darum für die Race exakt aus.
    const fire = (type: string, x: number, y: number) => {
      const ev = new MouseEvent(type, {
        bubbles: true,
        cancelable: true,
        clientX: x,
        clientY: y,
        button: 0,
        buttons: type === 'pointerup' ? 0 : 1,
      });
      Object.defineProperty(ev, 'pointerId', { value: 1, configurable: true });
      svg.dispatchEvent(ev);
    };
    // Down → viele Move → Up, synchron in einem Zug (kein await dazwischen)
    // — das ist die Batching-Konstellation, die den panning-Ref vor dem Fix
    // als bereits null lesen liess.
    fire('pointerdown', cx, cy);
    for (let i = 1; i <= 60; i++) fire('pointermove', cx - i * 4, cy - i * 3);
    fire('pointerup', cx - 240, cy - 180);
  }

  it('übersteht ein schnelles down→move…→up (Kamera-Node im Graph) ohne Absturz', () => {
    const graphId = neuerGraphMitKamera();

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });

    const svg = container.querySelector('[data-testid="node-canvas"]') as SVGSVGElement | null;
    expect(svg).not.toBeNull();

    // Die eigentliche Zusicherung: das Dispatchen der Race-Sequenz darf
    // NICHT werfen. Vor dem Fix warf React beim Flush der queued
    // setView-Updater eine TypeError («Cannot read properties of null
    // (reading 'cx')»), die hier unhandled durchschlagen und den Test
    // fehlschlagen liesse (kein Error-Boundary-Wrapper in diesem Unit-Test
    // — genau das macht die Zusicherung scharf).
    expect(() => {
      act(() => {
        feuereRaceSequence(svg!);
      });
    }).not.toThrow();

    // Der Node-Tree lebt danach unverändert weiter (kein Remount nötig).
    expect(container.querySelector('[data-testid="node-canvas"]')).not.toBeNull();
    expect(container.querySelectorAll('[data-testid="vis-node-kamera"]')).toHaveLength(1);
  });

  it('mehrere Runden derselben Race bleiben stabil (kein Einzeltreffer-Zufall)', () => {
    const graphId = neuerGraphMitKamera();

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });

    const svg = container.querySelector('[data-testid="node-canvas"]') as SVGSVGElement;

    expect(() => {
      for (let round = 0; round < 15; round++) {
        act(() => {
          feuereRaceSequence(svg);
        });
      }
    }).not.toThrow();
  });
});
