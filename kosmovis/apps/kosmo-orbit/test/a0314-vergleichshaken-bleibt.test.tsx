// @vitest-environment jsdom
import { act, useState } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { KuratierFlaeche } from '../src/modules/vis/KuratierFlaeche';
import type { KuratierKartenDaten, KuratierQuelle } from '../src/modules/vis/varianten-diff';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * A0314 (V-H5, «Vergleichshaken unter Last»): das zweite VGL-Häkchen schaltet die Fläche selbst auf die
 * Vergleichsansicht. Hängte das Raster dabei aus, war das eben gedrückte Häkchen sofort vom Baum — Playwrights
 * Zustandsprüfung nach `check()` fand es nicht mehr und lief ins Zeitlimit (4 von 20 unter Last). Das Häkchen muss
 * den Wechsel überleben.
 */
const q = (id: string, bild: string) => ({ jobId: id, bild }) as KuratierQuelle;
const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'T', nodes: [node, { ...node, id: 'n2' }], edges: [] } as VisGraph;
const karte = (id: string, quelle: KuratierQuelle): KuratierKartenDaten => ({ node: { ...node, id }, quelle, kur: { markiert: false, verworfen: false } });
const karten = [karte('n1', q('vis-1-aaaaaa', 'a.png')), karte('n2', q('vis-2-bbbbbb', 'b.png'))];
const leer = () => {};

function Traeger() {
  const [wahl, setWahl] = useState<readonly string[]>([]);
  return (
    <KuratierFlaeche
      graph={graph}
      karten={karten}
      vergleichAuswahl={wahl}
      onMarkieren={leer}
      onVerwerfen={leer}
      onVergleichWahl={(id) => setWahl((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))}
    />
  );
}

let root: Root | null = null;
let host: HTMLDivElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  host?.remove();
  root = null;
  host = null;
});

describe('A0314 Vergleichshäkchen', () => {
  it('das zweite Häkchen bleibt nach dem Wechsel in die Vergleichsansicht im Baum und angehakt', () => {
    host = document.createElement('div');
    document.body.appendChild(host);
    root = createRoot(host);
    act(() => root!.render(<Traeger />));
    const haken = () => Array.from(host!.querySelectorAll<HTMLInputElement>('[data-testid="vis-kuratier-vergleich-wahl"]'));
    expect(haken()).toHaveLength(2);
    const [erstes, zweites] = haken();
    act(() => erstes!.click());
    act(() => zweites!.click());
    expect(host.querySelector('[data-testid="vis-kuratier-vergleich-flaeche"]')).not.toBeNull();
    expect(zweites!.isConnected).toBe(true);
    expect(zweites!.checked).toBe(true);
    expect(erstes!.isConnected).toBe(true);
  });

  it('die Vergleichsansicht zeigt das Raster nicht (nur eingehängt, unsichtbar)', () => {
    host = document.createElement('div');
    document.body.appendChild(host);
    root = createRoot(host);
    act(() => root!.render(<Traeger />));
    const haken = Array.from(host.querySelectorAll<HTMLInputElement>('[data-testid="vis-kuratier-vergleich-wahl"]'));
    act(() => haken[0]!.click());
    act(() => haken[1]!.click());
    const huelle = host.querySelector<HTMLElement>('.vis-kuratier-raster-huelle')!;
    expect(huelle.style.display).toBe('none');
  });
});
