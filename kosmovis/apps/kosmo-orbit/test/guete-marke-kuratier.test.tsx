// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { KuratierFlaeche } from '../src/modules/vis/KuratierFlaeche';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { BildKachel } from '../src/modules/vis/NodeCanvas';
import type { KuratierKartenDaten, KuratierQuelle } from '../src/modules/vis/varianten-diff';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * Entscheid 104a: ein Vorschaubild darf nirgends wie ein volles aussehen — neben Knoten und Verlauf auch in der
 * Kuratier-Karte, im Vergleich, im Inspektor und in der Bildkachel (Kuratier-Quelle trägt `guete`, KosmoVis 97c5ca058).
 */
const VORSCHAU: KuratierQuelle = { jobId: 'vis-1-aaaaaa', bild: 'a.png', guete: 'vorschau' } as KuratierQuelle;
const VOLL: KuratierQuelle = { jobId: 'vis-2-bbbbbb', bild: 'b.png' } as KuratierQuelle;
const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'T', nodes: [node, { ...node, id: 'n2' }], edges: [] } as VisGraph;
const karte = (id: string, quelle: KuratierQuelle): KuratierKartenDaten => ({ node: { ...node, id }, quelle, kur: { markiert: false, verworfen: false } });

let root: Root | null = null;
let host: HTMLDivElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  host?.remove();
  root = null;
  host = null;
});
function mount(el: React.ReactElement): HTMLDivElement {
  host = document.createElement('div');
  document.body.appendChild(host);
  root = createRoot(host);
  act(() => root!.render(el));
  return host;
}
const leer = () => {};

describe('GueteMarke in der Kuratierung', () => {
  it('Kuratier-Karte: Abzeichen nur an der Vorschau', () => {
    const h = mount(<KuratierFlaeche graph={graph} karten={[karte('n1', VORSCHAU), karte('n2', VOLL)]} vergleichAuswahl={[]} onMarkieren={leer} onVerwerfen={leer} onVergleichWahl={leer} />);
    const karten = h.querySelectorAll('[data-testid="vis-kuratier-karte"]');
    expect(karten[0]!.querySelector('[data-testid="vis-kuratier-karte-guete-marke"]')!.getAttribute('data-form')).toBe('abzeichen');
    expect(karten[1]!.querySelector('[data-testid="vis-kuratier-karte-guete-marke"]')).toBeNull();
  });
  it('Vergleich: Marke an B (Vorschau), nicht an A (voll)', () => {
    const h = mount(<KuratierFlaeche graph={graph} karten={[karte('n1', VOLL), karte('n2', VORSCHAU)]} vergleichAuswahl={['n1', 'n2']} onMarkieren={leer} onVerwerfen={leer} onVergleichWahl={leer} />);
    expect(h.querySelector('[data-testid="vis-kuratier-vergleich-guete-marke-a"]')).toBeNull();
    expect(h.querySelector('[data-testid="vis-kuratier-vergleich-guete-marke-b"]')!.textContent).toBe('Vorschau');
  });
  it('Inspektor: Zeile unter dem Bild; volles Bild ohne', () => {
    const h = mount(<KuratierInspektor graph={graph} karte={karte('n1', VORSCHAU)} id="V-01" onMarkieren={leer} onVerwerfen={leer} onInsProjekt={leer} />);
    expect(h.querySelector('[data-testid="vis-kuratier-inspektor-guete-marke"]')!.getAttribute('data-form')).toBe('zeile');
    act(() => root!.unmount());
    root = null;
    host!.remove();
    const v = mount(<KuratierInspektor graph={graph} karte={karte('n1', VOLL)} id="V-01" onMarkieren={leer} onVerwerfen={leer} onInsProjekt={leer} />);
    expect(v.querySelector('[data-testid="vis-kuratier-inspektor-guete-marke"]')).toBeNull();
  });
  it('Bildkachel: mit guete «vorschau» die Zeile, sonst nichts', () => {
    const h = mount(<BildKachel jobId="vis-1-aaaaaa" bild="a.png" guete="vorschau" alt="Bild 1" />);
    expect(h.querySelector('[data-testid="vis-bild-kachel-guete-marke"]')).not.toBeNull();
    act(() => root!.unmount());
    root = null;
    host!.remove();
    expect(mount(<BildKachel jobId="vis-1-aaaaaa" bild="a.png" alt="Bild 1" />).querySelector('[data-testid="vis-bild-kachel-guete-marke"]')).toBeNull();
  });
});
