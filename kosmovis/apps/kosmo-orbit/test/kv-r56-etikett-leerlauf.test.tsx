// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { qaUrteil } from '../src/modules/vis/varianten-diff';
import { laufUrteil, URTEIL_LABEL } from '../src/modules/vis/render-verlauf';
import { NodeCanvas, RENDER_VERALTET_SATZ } from '../src/modules/vis/NodeCanvas';

/**
 * Geraeteprobe R56 der HomeStation (23.10.2026, echter Render), Punkte 4 und 5 (Punkt 1:
 * `kv-r56-kamera-teilmenge.test.tsx`). Gegen den alten Stand rot:
 *
 *  4. Ein reiner Grundlage-Lauf trug in der grossen Ansicht «durchgefallen», obwohl sein Befund sagt
 *     «weder durchgefallen noch ungeprueft».
 *  5. Der Render-Knoten zeigte «rendert im GPU-Leerlauf …», obwohl kein eigener Auftrag lief.
 */
const graph = (id: string) => useProject.getState().doc.get<VisGraph>(id)!;

beforeEach(() => {
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, laeufe: {} });
});

describe('R56 Punkt 4: das Etikett folgt dem Befund', () => {
  const nurGrundlage = {
    verdict: {
      passed: false,
      reason:
        "NUR GRUNDLAGE: Geliefert ist das Cycles-Bild, ohne KI-Schritt. 'passed: false' heisst hier weder durchgefallen noch ungeprueft — die Geometrie ist das Modell selbst; gemessen wird erst eine KI-Variante.",
    },
  };
  it('reiner Grundlage-Lauf: nicht «durchgefallen», sondern «ohne QA»', () => {
    expect(qaUrteil(nurGrundlage)).toBe('ohne-qa');
    expect(URTEIL_LABEL[laufUrteil(nurGrundlage as never)]).toBe('ohne QA');
  });
  it('abbestellt und ungeprueft: ebenso', () => {
    expect(qaUrteil({ verdict: { passed: false, reason: "ABBESTELLT: … 'passed: false' heisst hier weder durchgefallen noch ungeprueft — es war nichts bestellt." } })).toBe('ohne-qa');
    expect(qaUrteil({ verdict: { passed: false, reason: "Keine QA gelaufen — weder Geometrie noch Stil wurden gemessen. 'passed: false' heisst hier NICHT durchgefallen, sondern ungeprüft." } })).toBe('ohne-qa');
  });
  it('echtes Durchfallen und «nicht beurteilbar» bleiben, wie sie waren', () => {
    expect(qaUrteil({ verdict: { passed: false, reason: 'Umriss weicht ab.' } })).toBe('durchgefallen');
    expect(qaUrteil({ verdict: { passed: false } })).toBe('durchgefallen');
    expect(
      qaUrteil({ verdict: { passed: false, reason: "NICHT BEURTEILBAR (Gebaeudeanteil): 'passed: false' heisst hier nicht durchgefallen, sondern nicht beurteilbar" } }),
    ).toBe('nicht-beurteilbar');
    expect(qaUrteil({ verdict: { passed: true } })).toBe('bestanden');
  });
});

describe('R56 Punkt 5: «rendert im GPU-Leerlauf» nur mit eigenem Lauf', () => {
  class StubResizeObserver {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  let root: Root | null = null;
  let box: HTMLDivElement | null = null;
  beforeEach(() => {
    (globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
    (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  });
  afterEach(() => {
    if (root) act(() => root!.unmount());
    box?.remove();
    root = null;
    box = null;
  });

  function montiere(): { gid: string; renderId: string } {
    const res = useProject.getState().runCommand('vis.graphErstellen', { name: 'R56' });
    const gid = (res.patches[0] as { id: string }).id;
    useProject.getState().runCommand('vis.nodeSetzen', { graphId: gid, typ: 'render', x: 320, y: 120 });
    const renderId = graph(gid).nodes.at(-1)!.id;
    box = document.createElement('div');
    document.body.appendChild(box);
    root = createRoot(box);
    act(() => root!.render(<NodeCanvas graphId={gid} />));
    return { gid, renderId };
  }
  const leerbild = () => box!.querySelector<HTMLElement>('[data-testid="vis-node-render"] .vis-node-leerbild');

  it('ein fertiger, inzwischen veralteter Lauf sagt «veraltet», nicht «rendert»', () => {
    const { renderId } = montiere();
    act(() => useVisRuntime.getState().setzeLauf(renderId, { status: 'fertig', memoKey: 'ein-alter-stand', jobId: 'vis-1792700000-c00001', bild: 'a.png' }));
    expect(box!.querySelector('[data-testid="render-status"]')!.textContent).toBe('veraltet');
    expect(leerbild()!.textContent).not.toContain('rendert im GPU-Leerlauf');
    expect(leerbild()!.textContent).toContain(RENDER_VERALTET_SATZ);
  });

  it('ohne Lauf: kein «rendert»', () => {
    montiere();
    expect(box!.textContent).not.toContain('rendert im GPU-Leerlauf');
  });
});
