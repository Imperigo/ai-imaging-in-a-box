// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';

/**
 * KV-B5 (Auftrag `docs/auftraege-kosmovis/auf-vis-20261006-01-render-knoten-felder-leer.md`):
 * am Render-Knoten standen in der Desktop-App (WebKitGTK) die Felder leer
 * bzw. oben links im Fenster, und «Ausführen» wirkte nicht. Die Knotenkoerper
 * lagen als HTML in einem SVG-`foreignObject` innerhalb einer verschobenen
 * `<g>`; WebKit zeichnet HTML mit eigener Zeichenebene darin am falschen Ort.
 *
 * Diese Probe haelt den Bau fest, der von keiner Engine-Eigenheit abhaengt:
 *  - kein Feld des Render-Knotens steht in einem `foreignObject`, und die
 *    Leinwand traegt ueberhaupt keines mehr;
 *  - die Knoten liegen in der HTML-Knotenebene neben dem `<svg>`, mit
 *    derselben Verschiebung und Zoomstufe wie die `viewBox`;
 *  - jeder Knoten-Kasten umschliesst weiter Anschluesse UND Koerper (die
 *    E2E-Proben suchen Felder «in diesem Knoten»), und der Koerper liegt
 *    da, wo das `foreignObject` lag (8 px Rand, unter den Anschluessen).
 * Vor dem Umbau rot (die Felder standen im `foreignObject`), danach gruen.
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let container: HTMLDivElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
});

function montiere(): { graphId: string; renderId: string } {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `KV-B5-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 40, y: 40 });
  const r = runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 320, y: 120 });
  const renderId = (r.patches[0] as { id?: string }).id ?? '';
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
  return { graphId, renderId };
}

const FELDER = [
  'vis-preset-select',
  'render-aufloesung',
  'render-qualitaet',
  'render-himmel',
  'render-umgebung-drehen',
  'render-bildwerkzeug',
  'render-ausfuehren',
  'render-status',
  'node-expand',
  // Nr. 85 Paket 2: das Haekchen «nur Cycles» ist der Knopf «Grundlage rendern» geworden.
  'render-grundlage',
  'render-grundlage-zeile',
  'render-final-prompt',
];

describe('KV-B5 · Render-Knoten ohne foreignObject', () => {
  it('kein Feld des Render-Knotens steht in einem foreignObject, und die Leinwand traegt keines', () => {
    montiere();
    const svg = container!.querySelector('[data-testid="node-canvas"]')!;
    expect(svg).not.toBeNull();
    for (const feld of FELDER) {
      const el = container!.querySelector(`[data-testid="${feld}"]`);
      expect(el, `Feld «${feld}» fehlt`).not.toBeNull();
      expect(el!.closest('foreignObject'), `«${feld}» steht in einem foreignObject`).toBeNull();
      // Kein Feld ist Teil des SVG-Baums: HTML im SVG ist genau der Weg, den WebKit falsch zeichnet.
      expect(svg.contains(el), `«${feld}» steht im Leinwand-SVG`).toBe(false);
      expect(el instanceof HTMLElement, `«${feld}» ist kein HTML-Element`).toBe(true);
    }
    expect(container!.querySelectorAll('foreignObject')).toHaveLength(0);
  });

  it('jedes Feld liegt im Knoten-Kasten seines Render-Knotens, in dessen HTML-Koerper', () => {
    montiere();
    const knoten = container!.querySelector('[data-testid="vis-node-render"]')!;
    expect(knoten).not.toBeNull();
    expect(knoten.tagName).toBe('DIV');
    expect(knoten.closest('.vis-knoten-ebene')).not.toBeNull();
    const koerper = knoten.querySelector('.vis-node-koerper')!;
    expect(koerper).not.toBeNull();
    for (const feld of FELDER) {
      const el = container!.querySelector(`[data-testid="${feld}"]`)!;
      expect(knoten.contains(el), `«${feld}» liegt nicht im Render-Knoten`).toBe(true);
      expect(koerper.contains(el), `«${feld}» liegt nicht im Koerper`).toBe(true);
    }
    // Anschluesse bleiben im selben Kasten (eigenes kleines SVG).
    expect(knoten.querySelector('[data-testid="port-in-szene"]')).not.toBeNull();
    expect(knoten.querySelector('[data-testid="port-out-bild"]')).not.toBeNull();
  });

  it('Kasten und Koerper liegen an den Weltkoordinaten des Knotens, wie das foreignObject vorher', () => {
    montiere();
    const knoten = container!.querySelector<HTMLElement>('[data-testid="vis-node-render"]')!;
    expect(knoten.style.left).toBe('320px');
    expect(knoten.style.top).toBe('120px');
    // Entscheid 119: der Render-Knoten ist 212 px breit (Innenbreite 196), die anderen bleiben 200.
    expect(knoten.style.width).toBe('212px');
    const koerper = knoten.querySelector<HTMLElement>('.vis-node-koerper')!;
    expect(koerper.style.left).toBe('8px');
    expect(koerper.style.width).toBe('196px');
    // Unter Kopf (26) + 8 + fuenf Anschluesse des Render-Knotens.
    expect(Number.parseFloat(koerper.style.top)).toBeGreaterThan(26 + 8);
    // Die Gruppe im knoteneigenen SVG traegt dieselbe Verschiebung wie frueher.
    const g = knoten.querySelector('svg.vis-knoten-svg > g[transform]')!;
    expect(g.getAttribute('transform')).toBe('translate(320, 120)');
  });

  it('die Knotenebene folgt der viewBox: dieselbe Verschiebung und Zoomstufe', () => {
    montiere();
    const svg = container!.querySelector('[data-testid="node-canvas"]')!;
    const [vx, vy, vw, vh] = svg.getAttribute('viewBox')!.split(/\s+/).map(Number) as [number, number, number, number];
    const welt = container!.querySelector<HTMLElement>('.vis-knoten-welt')!;
    // Owner-Befund 20.10.2026 (WebKit unscharf): Verschiebung als `translate` an der Welt,
    // Zoomstufe als `zoom` an der inneren Hülle — kein `scale()` mehr.
    const m = /^translate\(([-\d.e]+)px, ([-\d.e]+)px\)$/.exec(welt.style.transform);
    expect(m, welt.style.transform).not.toBeNull();
    const zoomHuelle = welt.querySelector<HTMLElement>('.vis-knoten-zoom')!;
    expect(zoomHuelle.parentElement).toBe(welt);
    // Owner-Fund 22.10.2026: unter 1 traegt die Huelle `transform: scale()` statt `zoom`; die
    // wirksame Stufe ist zoom × scale und steht in `data-knoten-zoom`.
    const tf = /scale\(([-\d.e]+)\)/.exec(zoomHuelle.style.transform);
    const wirksam = Number(zoomHuelle.style.zoom || 1) * (tf ? Number(tf[1]) : 1);
    expect(wirksam).toBeCloseTo(Number(zoomHuelle.dataset.knotenZoom), 9);
    const [tx, ty, s] = [Number(m![1]), Number(m![2]), wirksam];
    expect(s).toBeGreaterThan(0);
    // Flaeche (Platzhalter 1200 × 700 in jsdom) = viewBox-Breite × Zoom.
    expect(vw * s).toBeCloseTo(1200, 6);
    expect(vh * s).toBeCloseTo(700, 6);
    // Die linke obere viewBox-Ecke landet auf (0, 0) der Ebene.
    expect(tx + vx * s).toBeCloseTo(0, 6);
    expect(ty + vy * s).toBeCloseTo(0, 6);
  });
});

/**
 * auf-20261006-239 (lokaler Worker, Desktop-App v0.1.6): «Tab fokussiert
 * ‹Ausführen›, Enter waehlt aber nur den Knoten aus und sendet nicht.» Das
 * liegt nicht an WebKit: der Tastenhandler des Knotens fing Enter und
 * Leertaste aus JEDEM Kind ab (`preventDefault` fuer die Auswahl) — ausser
 * aus Eingabefeldern (B1). Ein Knopf im Knoten bekam seine Taste damit nie,
 * und der Browser loest den Klick eines Knopfs genau ueber diese Taste aus.
 */
describe('KV-B5 · Enter und Leertaste auf einem Knopf im Knoten gehoeren dem Knopf', () => {
  function druecke(el: Element, key: string): KeyboardEvent {
    const ev = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true });
    act(() => {
      el.dispatchEvent(ev);
    });
    return ev;
  }

  it('Enter auf «Ausführen» wird nicht abgefangen und waehlt den Knoten nicht', () => {
    montiere();
    const knopf = container!.querySelector('[data-testid="render-ausfuehren"]')!;
    const knoten = container!.querySelector('[data-testid="vis-node-render"]')!;
    const ev = druecke(knopf, 'Enter');
    expect(ev.defaultPrevented, 'Enter auf «Ausführen» wurde vom Knoten abgefangen').toBe(false);
    expect(knoten.getAttribute('aria-pressed')).toBe('false');
  });

  it('Leertaste auf «Ausführen» und auf dem Klappknopf wird nicht abgefangen', () => {
    montiere();
    for (const id of ['render-ausfuehren', 'node-expand']) {
      const ev = druecke(container!.querySelector(`[data-testid="${id}"]`)!, ' ');
      expect(ev.defaultPrevented, `Leertaste auf «${id}» wurde vom Knoten abgefangen`).toBe(false);
    }
  });

  it('Gegenprobe: Enter auf dem Knoten selbst waehlt ihn weiter aus', () => {
    montiere();
    const knoten = container!.querySelector('[data-testid="vis-node-render"]')!;
    const ev = druecke(knoten, 'Enter');
    expect(ev.defaultPrevented).toBe(true);
    expect(knoten.getAttribute('aria-pressed')).toBe('true');
  });
});
