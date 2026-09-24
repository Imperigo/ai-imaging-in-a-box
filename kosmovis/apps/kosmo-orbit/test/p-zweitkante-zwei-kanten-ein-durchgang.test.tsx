// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';
import type { VisGraph } from '@kosmo/kernel';

// Dieselben zwei Stubs wie `node-canvas-pointer-cancel.test.tsx` — jsdom kennt
// weder ResizeObserver noch PointerCapture.
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
 * P-ZWEITKANTE Posten 5 (`auftraege/von-homestation/auf-orbit-20260828-16.md`)
 * — «die verlorene zweite Kante».
 *
 * **Was hier gemessen wird, und was ausdruecklich nicht.** Die Vorgaenger-
 * messung (`docs/MESSUNG-GRAPHSTART-ZWEITKANTE-2026-08-24.md`, Fund B) hat am
 * echten Chromium aufgezeichnet: der zweite Kanten-Zug in derselben
 * Ausfuehrung endet mit `pointercancel` statt `pointerup`. Ein
 * `onPointerCancel`-Handler raeumte danach zwar auf und meldete sich
 * (`NodeCanvas.tsx:1019-1027`), **warf die begonnene Kante aber weg** — der
 * Nutzer musste die Geste wiederholen (Demolauf 25.08.: 7 Versuche fuer 2
 * Kanten).
 *
 * Dass die Ursache NICHT in einem stehengebliebenen React-Zustand des
 * Canvas liegt, ist hier mitgemessen: der dritte Fall unten fuehrt zwei
 * vollstaendige, saubere Gesten hintereinander in EINER Ausfuehrung aus und
 * bekommt zwei Kanten — der Canvas selbst setzt zwischen zwei Zuegen nichts
 * falsch zurueck. Was fehlte, war allein die Rettung der abgebrochenen Geste.
 *
 * **Auflage des Auftrags: die Zahl der Versuche zaehlen, nicht nur den
 * Endzustand.** `versuche` zaehlt darum jede einzelne Geste; die Zusicherung
 * lautet «2 Kanten aus 2 Gesten», nicht «am Ende stehen 2 Kanten da».
 *
 * **BERICHTIGT 01.09.2026 (`docs/MESSUNG-P5-POINTERCANCEL-2026-09-01.md`).**
 * `abgebrocheneGeste()` feuerte bis hierhin: Bewegung BIS AUF DEN ZIEL-PORT
 * — und erst dann `pointercancel`. Das war die falsche Annahme: am echten
 * Chromium kommt der Abbruch schon NACH DER ERSTEN Bewegung, mit dem Zeiger
 * noch MITTEN AUF DER LEINWAND, nie in Naehe des Ziel-Ports (Ursache: eine
 * stehengebliebene Text-Selektion vom ersten Zug wird beim zweiten Zug als
 * «Selektion ziehen» gedeutet, Chromium feuert `dragstart` dann
 * `pointercancel`, s. Messung). Diese Datei war darum GRUEN, waehrend der
 * echte Browser ROT war — sie hatte genau die Bedingung vorausgesetzt, die
 * Chromium nie liefert. `abgebrocheneGeste()` ist auf die real gemessene
 * Sequenz nachgezogen (EINE Bewegung zur Zwischenposition, dann sofort
 * `pointercancel`, ohne die zweite Bewegung zum Ziel).
 *
 * **Der eigentliche Fix liegt NICHT hier** (nicht in `onPointerCancel`,
 * nicht in dieser Wache) — er liegt in `vis-visual.css`
 * (`.vis-canvas-svg { user-select: none }`), die die Selektion und damit
 * die ganze Abbruchkette an der Wurzel verhindert und die im DOM/CSS-losen
 * jsdom nicht nachstellbar ist. Diese Datei bleibt darum bewusst eine
 * GRENZPRUEFUNG des `onPointerCancel`-Rettungsmechanismus fuer den Fall,
 * dass ein `pointercancel` mitten auf der Leinwand eintrifft — und die
 * ehrliche Zusicherung ist, dass die Rettung genau DAS nicht retten kann
 * (der Zeiger ist nicht in Portnaehe): siehe die neue Erwartung im ersten
 * Fall unten, NICHT auf `versuche:2, kanten:2` gesenkt, um gruen zu werden.
 *
 * **Pointer-Capture bleibt verboten.** Der Kommentar `NodeCanvas.tsx:1344`
 * («KEIN Pointer-Capture: das pointerup muss den Ziel-Port treffen») ist
 * NICHT aufgehoben — Fall 4 ist die Probe dafuer: der gewoehnliche Weg
 * (`pointerup` auf dem Hit-Kreis des Ziel-Ports, dessen eigener Handler) legt
 * die Kante weiterhin an.
 */
describe('P-ZWEITKANTE Posten 5 — zwei Kanten in EINEM Durchgang, Versuche gezaehlt', () => {
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

  function neuerGraph(): string {
    const { runCommand } = useProject.getState();
    const res = runCommand('vis.graphErstellen', { name: `P5-${Math.random()}` });
    const graphId = (res.patches[0] as { id: string }).id;
    runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 40, y: 40 });
    runCommand('vis.nodeSetzen', { graphId, typ: 'kamera', x: 40, y: 400 });
    runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 520, y: 200 });
    return graphId;
  }

  function montiere(graphId: string): SVGSVGElement {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });
    return container.querySelector('[data-testid="node-canvas"]') as SVGSVGElement;
  }

  function feuere(el: Element, typ: string, koord?: { clientX: number; clientY: number }): void {
    const ev = new MouseEvent(typ, { bubbles: true, cancelable: true, button: 0, ...(koord ?? {}) });
    Object.defineProperty(ev, 'pointerId', { value: 1, configurable: true });
    el.dispatchEvent(ev);
  }

  /** Hit-Kreis eines Ports = der naechste `<circle>` nach dem sichtbaren. */
  function hitKreisVon(sichtbarerPort: Element): SVGCircleElement {
    return sichtbarerPort.nextElementSibling as SVGCircleElement;
  }

  /** Canvas-Koordinate eines gerenderten Ports: Node-`transform` + Kreis-cx/cy
   *  — genau die Zahlen, die `NodeCanvas` selbst gemalt hat, keine Nachrechnung. */
  function portPunkt(port: Element): { x: number; y: number } {
    const nodeG = port.closest('g[transform]') as SVGGElement;
    const m = /translate\(([-\d.]+),\s*([-\d.]+)\)/.exec(nodeG.getAttribute('transform') ?? '')!;
    return {
      x: Number(m[1]) + Number(port.getAttribute('cx')),
      y: Number(m[2]) + Number(port.getAttribute('cy')),
    };
  }

  /** Umkehrung von `NodeCanvas`s `toCanvas()` — in jsdom liefert
   *  `getBoundingClientRect()` Nullen, also gilt `client = (welt - mitte) * scale`.
   *  Mitte und Skala kommen aus der real gerenderten `viewBox`. */
  function clientFuer(svg: SVGSVGElement, punkt: { x: number; y: number }): { clientX: number; clientY: number } {
    const [vx, vy, vw, vh] = svg.getAttribute('viewBox')!.split(/\s+/).map(Number) as [number, number, number, number];
    const scale = 1200 / vw;
    const cx = vx + vw / 2;
    const cy = vy + vh / 2;
    return { clientX: (punkt.x - cx) * scale, clientY: (punkt.y - cy) * scale };
  }

  function kanten(graphId: string): number {
    return useProject.getState().doc.get<VisGraph>(graphId)!.edges.length;
  }

  interface Zaehler {
    versuche: number;
  }

  /** EINE Geste, so wie Chromium sie am 01.09.2026 tatsaechlich zugestellt
   *  hat (`docs/MESSUNG-P5-POINTERCANCEL-2026-09-01.md`): `pointerdown` auf
   *  dem Quell-Port, EINE Bewegung zu einer Zwischenposition — und DANN,
   *  ohne die zweite Bewegung zum Ziel, sofort `pointercancel` auf dem SVG.
   *  Der Zeiger steht dabei mitten auf der Leinwand, NICHT am Ziel-Port. */
  function abgebrocheneGeste(
    svg: SVGSVGElement,
    z: Zaehler,
    quelle: { node: string; port: string },
    ziel: { node: string; port: string },
  ): void {
    z.versuche += 1;
    const q = container!.querySelector(`[data-testid="vis-node-${quelle.node}"]`)!;
    const r = container!.querySelector(`[data-testid="vis-node-${ziel.node}"]`)!;
    const aus = q.querySelector(`[data-testid="port-out-${quelle.port}"]`)!;
    const ein = r.querySelector(`[data-testid="port-in-${ziel.port}"]`)!;
    const start = clientFuer(svg, portPunkt(aus));
    const ende = clientFuer(svg, portPunkt(ein));
    const zwischenposition = {
      clientX: (start.clientX + ende.clientX) / 2,
      clientY: (start.clientY + ende.clientY) / 2,
    };
    act(() => feuere(hitKreisVon(aus), 'pointerdown', start));
    act(() => feuere(svg, 'pointermove', zwischenposition));
    act(() => feuere(svg, 'pointercancel', zwischenposition));
  }

  it('zwei abgebrochene Gesten in EINEM Durchgang, Abbruch mitten auf der Leinwand — die Rettung kann das NICHT ausgleichen (Grenzpruefung, s. Kopfkommentar)', () => {
    const graphId = neuerGraph();
    const svg = montiere(graphId);
    const z: Zaehler = { versuche: 0 };

    abgebrocheneGeste(svg, z, { node: 'modell', port: 'szene' }, { node: 'render', port: 'szene' });
    abgebrocheneGeste(svg, z, { node: 'kamera', port: 'kameras' }, { node: 'render', port: 'kameras' });

    // NICHT auf {versuche:2, kanten:2} gesenkt: die Zwischenposition liegt
    // ausserhalb von PORT_TREFFER_R jedes Ports, `eingangUnterPunkt()`
    // findet dort nichts — genau das erklaert, warum die Wache am echten
    // Browser bei diesem Fehlerbild ROT blieb, bevor der eigentliche Fix
    // (`vis-visual.css`, `user-select: none`) griff.
    expect({ versuche: z.versuche, kanten: kanten(graphId) }).toEqual({ versuche: 2, kanten: 0 });
  });

  it('Gegenprobe: bricht die Geste ueber leerer Flaeche ab, entsteht KEINE Kante', () => {
    const graphId = neuerGraph();
    const svg = montiere(graphId);

    const q = container!.querySelector('[data-testid="vis-node-modell"]')!;
    const aus = q.querySelector('[data-testid="port-out-szene"]')!;
    act(() => feuere(hitKreisVon(aus), 'pointerdown', clientFuer(svg, portPunkt(aus))));
    act(() => feuere(svg, 'pointermove', clientFuer(svg, { x: 2000, y: 2000 })));
    act(() => feuere(svg, 'pointercancel', clientFuer(svg, { x: 2000, y: 2000 })));

    expect(kanten(graphId)).toBe(0);
  });

  it('Messung: zwei SAUBERE Gesten in EINEM Durchgang liefern schon heute zwei Kanten — kein stehengebliebener Canvas-Zustand', () => {
    const graphId = neuerGraph();
    const svg = montiere(graphId);
    const z: Zaehler = { versuche: 0 };

    const sauber = (quelle: { node: string; port: string }, ziel: { node: string; port: string }) => {
      z.versuche += 1;
      const q = container!.querySelector(`[data-testid="vis-node-${quelle.node}"]`)!;
      const r = container!.querySelector(`[data-testid="vis-node-${ziel.node}"]`)!;
      const aus = q.querySelector(`[data-testid="port-out-${quelle.port}"]`)!;
      const ein = r.querySelector(`[data-testid="port-in-${ziel.port}"]`)!;
      act(() => feuere(hitKreisVon(aus), 'pointerdown', clientFuer(svg, portPunkt(aus))));
      act(() => feuere(svg, 'pointermove', clientFuer(svg, portPunkt(ein))));
      act(() => feuere(hitKreisVon(ein), 'pointerup', clientFuer(svg, portPunkt(ein))));
    };

    sauber({ node: 'modell', port: 'szene' }, { node: 'render', port: 'szene' });
    sauber({ node: 'kamera', port: 'kameras' }, { node: 'render', port: 'kameras' });

    expect({ versuche: z.versuche, kanten: kanten(graphId) }).toEqual({ versuche: 2, kanten: 2 });
  });

  it('Probe zum Pointer-Capture-Riegel: der Ziel-Port wird weiterhin selbst getroffen (sein eigener pointerup-Handler legt die Kante an)', () => {
    const graphId = neuerGraph();
    const svg = montiere(graphId);

    const q = container!.querySelector('[data-testid="vis-node-kamera"]')!;
    const r = container!.querySelector('[data-testid="vis-node-render"]')!;
    const aus = q.querySelector('[data-testid="port-out-kameras"]')!;
    const ein = r.querySelector('[data-testid="port-in-kameras"]')!;

    // Der `pointerup` geht an den Hit-Kreis des ZIEL-Ports, nicht ans SVG:
    // genau das, was ein Pointer-Capture auf dem Quell-Port verhindern wuerde.
    let zielGetroffen: Element | null = null;
    hitKreisVon(ein).addEventListener('pointerup', (e) => {
      zielGetroffen = e.target as Element;
    });

    act(() => feuere(hitKreisVon(aus), 'pointerdown', clientFuer(svg, portPunkt(aus))));
    act(() => feuere(hitKreisVon(ein), 'pointerup', clientFuer(svg, portPunkt(ein))));

    expect(zielGetroffen).toBe(hitKreisVon(ein));
    expect(kanten(graphId)).toBe(1);
  });
});
