// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { History, KAMERA_AUS_3D_TYP, KosmoDoc, VIS_NODE_KATALOG, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { aktuelleKamera } from '../../kosmo-orbit/src/state/viewport-kamera';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { NodeCanvas } from '../../kosmo-orbit/src/modules/vis/NodeCanvas';
import { KEINE_3D_ANSICHT_SATZ, kameraAus3dAnlegen } from '../../kosmo-orbit/src/modules/vis/kamera-aus-3d';

/**
 * VISBOX-EIGEN (Runde 29, 14.10.2026): der Knoten «Kamera aus 3D-Ansicht» in Visbox.
 *
 * Das Vis-Werkzeug bringt aus KosmoOrbit den Knoten mit, der die Kamera der 3D-Ansicht
 * übernimmt. Visbox hat keine 3D-Ansicht — niemand meldet einen Lieferanten an
 * (`state/viewport-kamera.ts`). Der Knoten muss das sagen («Keine 3D-Ansicht offen»), statt
 * abzustürzen oder still eine Kamera vorzutäuschen. Die Probe des Originals
 * (`kv-kamera-aus-3d.test.tsx`) braucht eine Splat-Ebene und den Architekturkern und kommt
 * darum nicht herüber; diese prüft den Visbox-Fall.
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

beforeEach(() => {
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
});

describe('Visbox: «Kamera aus 3D-Ansicht» ohne 3D-Ansicht', () => {
  it('der Knoten steht im Katalog, aber keine 3D-Ansicht liefert eine Kamera', () => {
    expect(VIS_NODE_KATALOG[KAMERA_AUS_3D_TYP]).toBeDefined();
    expect(aktuelleKamera()).toBeNull();
  });

  it('Anlegen geht ohne Fehler; der Knoten traegt keine Kamera, und die Knotenansicht sagt es', () => {
    let ergebnis: ReturnType<typeof kameraAus3dAnlegen> = null;
    expect(() => {
      ergebnis = kameraAus3dAnlegen();
    }).not.toThrow();
    expect(ergebnis).not.toBeNull();
    const e = ergebnis!;
    expect(e.neu).toBe(true);
    expect(e.kamera).toBeNull();
    const g = useProject.getState().doc.get<VisGraph>(e.graphId)!;
    expect(g.nodes.filter((n) => n.typ === KAMERA_AUS_3D_TYP)).toHaveLength(1);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => root!.render(<NodeCanvas graphId={e.graphId} />));
    expect(q('kamera-aus-3d-leer')?.textContent).toBe(KEINE_3D_ANSICHT_SATZ);
    expect(KEINE_3D_ANSICHT_SATZ).toMatch(/^Keine 3D-Ansicht offen/);

    // «Kamera übernehmen» ohne Ansicht: keine Ausnahme, der Knoten bleibt ohne Kamera.
    const knopf = q('kamera-aus-3d-uebernehmen') as HTMLButtonElement | null;
    expect(knopf).not.toBeNull();
    expect(() => act(() => knopf!.click())).not.toThrow();
    expect(q('kamera-aus-3d-leer')?.textContent).toBe(KEINE_3D_ANSICHT_SATZ);
  });
});
