// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { evaluiereGraph, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { NodeCanvas } from '../../kosmo-orbit/src/modules/vis/NodeCanvas';
import { registriereBlickQuelle, waehlbareBlicke } from '../../kosmo-orbit/src/modules/vis/blick-quelle';
import { blickeAusMappe, KEIN_MAPPEN_BLICK_SATZ, type MappenBlick } from '../src/mappe';

/**
 * VISBOX-EIGEN (Video-Befund L4-4, 21.10.2026, Blatt «Blick zur Kamera»): in Visbox speisen die von
 * Hand gesetzten Standpunkte der Bilder der Mappe die Auswahl «Blick» am Knoten «Kamera»
 * (`knotenweg.blicke_der_mappe` → `blickeAusMappe` → `registriereBlickQuelle`). Erfundene Zahlen.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;

let container: HTMLDivElement | null = null;
let root: Root | null = null;
const q = (id: string): HTMLElement | null => document.body.querySelector(`[data-testid="${id}"]`);
const klick = (el: Element | null) => act(() => (el as HTMLElement).click());

const GARTEN: MappenBlick = { name: 'Gartenblick', bild: 'bilder/a.png', auge: [10, -20, 1.6], blick_auf: [0, 0, 4], brennweite_mm: 36 };

beforeEach(() => {
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  registriereBlickQuelle(null);
});

describe('Blicke der Mappe im Knoten «Kamera»', () => {
  it('Heim-PC (Z oben) wird glTF (Y oben), der Bildwinkel kommt aus der Brennweite', () => {
    const [b] = blickeAusMappe([GARTEN, { ...GARTEN, name: 'kaputt', brennweite_mm: 0 }]);
    expect(b).toEqual({ id: 'bild:bilder/a.png', name: 'Gartenblick', herkunft: 'Mappe', position: [10, 1.6, 20], target: [0, 4, -0], fov: 53.13 });
    expect(blickeAusMappe(undefined)).toEqual([]);
  });

  it('gewählt im Reiter «Blick», bestellt als ein Standpunkt', () => {
    registriereBlickQuelle({ blicke: blickeAusMappe([GARTEN]), leerSatz: KEIN_MAPPEN_BLICK_SATZ });
    expect(waehlbareBlicke(useProject.getState().doc).map((b) => b.name)).toEqual(['Gartenblick']);
    const { runCommand } = useProject.getState();
    const gid = (runCommand('vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
    const neu = (typ: string, x: number) => {
      runCommand('vis.nodeSetzen', { graphId: gid, typ, x, y: 40 });
      const g = useProject.getState().doc.get<VisGraph>(gid)!;
      return g.nodes[g.nodes.length - 1]!.id;
    };
    const kamera = neu('kamera', 40);
    const render = neu('render', 340);
    runCommand('vis.verbinden', { graphId: gid, from: kamera, fromPort: 'kameras', to: render, toPort: 'kameras' });
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => root!.render(<NodeCanvas graphId={gid} />));
    klick(q('kamera-art-blick'));
    const g = useProject.getState().doc.get<VisGraph>(gid)!;
    const a = evaluiereGraph(useProject.getState().doc, g).renderAuftraege.get(render)!;
    expect(a.kameras?.map((k) => k.name)).toEqual(['Gartenblick']);
    expect(a.kameras?.[0]?.position).toEqual([10, 1.6, 20]);
  });

  it('ohne gesetzten Standpunkt: der Satz der Mappe', () => {
    registriereBlickQuelle({ blicke: [], leerSatz: KEIN_MAPPEN_BLICK_SATZ });
    const { runCommand } = useProject.getState();
    const gid = (runCommand('vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
    runCommand('vis.nodeSetzen', { graphId: gid, typ: 'kamera', x: 40, y: 40 });
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => root!.render(<NodeCanvas graphId={gid} />));
    klick(q('kamera-art-blick'));
    expect(q('kamera-blick-leer')?.textContent).toBe(KEIN_MAPPEN_BLICK_SATZ);
  });
});
