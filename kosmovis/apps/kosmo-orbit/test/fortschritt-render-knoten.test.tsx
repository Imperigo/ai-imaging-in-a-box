// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type VisGraph } from '@kosmo/kernel';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';
import { memoKey, useVisRuntime, type NodeLauf } from '../src/modules/vis/vis-runtime';
import { renderWarteAnzeige } from '../src/modules/vis/render-warteort';

/**
 * Fortschritt am Render-Knoten (Owner 06.10.2026: «für sämtliche dinge im node ui für prozesse … eine
 * progressbar»). Der Knoten zeigt während des Laufs `KWarteOrt` als Fläche im Bild-Platzhalter, gefüllt NUR
 * aus `NodeLauf.progress.pct` (Regel G6). Ohne Zahl atmet er; liefert der Rechner nur Etappen (Blender und
 * Probe-Rechner: 0,5 und 1,0), sagt der Text «Phase …» und der Balken springt ehrlich.
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

describe('renderWarteAnzeige — eine Quelle für Knoten und Insel', () => {
  const jetzt = 1_000_000_000;

  it('fertige, freigabepflichtige und ruhende Läufe zeigen keinen Warteort', () => {
    expect(renderWarteAnzeige(undefined, jetzt)).toBeNull();
    expect(renderWarteAnzeige({ status: 'fertig', memoKey: 'k' }, jetzt)).toBeNull();
    expect(renderWarteAnzeige({ status: 'wartetFreigabe', memoKey: 'k' }, jetzt)).toBeNull();
    expect(renderWarteAnzeige({ status: 'fehler', memoKey: 'k' }, jetzt)).toBeNull();
  });

  it('Warten auf den Rechner ist unbestimmt und nennt die Wartezeit', () => {
    const a = renderWarteAnzeige({ status: 'wartetGpu', memoKey: 'k', gestartetUm: jetzt - 3 * 60_000 }, jetzt)!;
    expect(a.art).toBe('unbestimmt');
    expect('fortschritt' in a).toBe(false);
    expect(a.text).toContain('seit 3 Min.');
  });

  it('feiner Fortschritt je Kamera füllt mit der echten Zahl und nennt die Kamera', () => {
    const a = renderWarteAnzeige(
      { status: 'rendert', memoKey: 'k', progress: { phase: 'rendert Eingang', pct: 0.42 }, worker: 'bildrechner' },
      jetzt,
    )!;
    expect(a.art).toBe('fein');
    expect(a.fortschritt).toBe(0.42);
    expect(a.text).toContain('Kamera «Eingang»');
    expect(a.text).toContain('42 %');
    expect(a.text).toContain('bildrechner');
  });

  it('nur Etappen (0,5): Text sagt «Phase», keine Prozentzahl wird vorgetäuscht, der Balken steht auf der Etappe', () => {
    const a = renderWarteAnzeige({ status: 'rendert', memoKey: 'k', progress: { phase: 'rendern', pct: 0.5 } }, jetzt)!;
    expect(a.art).toBe('etappe');
    expect(a.fortschritt).toBe(0.5);
    expect(a.text).toContain('Phase «rendern»');
    expect(a.text).not.toMatch(/\d+ ?%/);
  });

  it('läuft ohne Fortschritt: unbestimmt, ohne erfundene Zahl', () => {
    const a = renderWarteAnzeige({ status: 'rendert', memoKey: 'k' }, jetzt)!;
    expect(a.art).toBe('unbestimmt');
    expect(a.fortschritt).toBeUndefined();
  });

  it('ein Hinweis der Brücke steht mit im Text', () => {
    const a = renderWarteAnzeige({ status: 'gesendet', memoKey: 'k', bridgeHinweis: 'Brücke antwortet nicht' }, jetzt)!;
    expect(a.text).toContain('Brücke antwortet nicht');
  });
});

describe('NodeCanvas — der Render-Knoten wartet am Ort', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root!.unmount());
      root = null;
    }
    container?.remove();
    container = null;
    vi.unstubAllGlobals();
  });

  function zeigeKnoten(lauf: Omit<NodeLauf, 'memoKey'>): HTMLDivElement {
    const { runCommand, doc } = useProject.getState();
    const g = runCommand('vis.graphErstellen', { name: `fortschritt-${Math.random()}` });
    const graphId = (g.patches[0] as { id: string }).id;
    runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 200, y: 0 });
    const nodeId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
    const auftrag = evaluiereGraph(doc, doc.get<VisGraph>(graphId)!).renderAuftraege.get(nodeId)!;
    useVisRuntime.getState().setzeLauf(nodeId, { ...lauf, memoKey: memoKey(auftrag) });
    vi.stubGlobal('fetch', (async () => ({ ok: false, status: 404, json: async () => ({}) }) as Response) as unknown as typeof fetch);
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => root!.render(<NodeCanvas graphId={graphId} />));
    return container;
  }

  it('feiner Fortschritt: Fläche im Bildplatz, gefüllt aus progress.pct', () => {
    const c = zeigeKnoten({ status: 'rendert', gestartetUm: Date.now(), progress: { phase: 'rendert Eingang', pct: 0.42 } });
    const ort = c.querySelector('[data-testid="render-warteort"]');
    expect(ort).not.toBeNull();
    const warten = ort!.querySelector('.k-warten')!;
    expect(warten.getAttribute('data-form')).toBe('flaeche');
    expect(warten.getAttribute('data-art')).toBe('bestimmt');
    expect(warten.getAttribute('aria-valuenow')).toBe('42');
    expect(warten.textContent).toContain('Kamera «Eingang»');
  });

  it('Warten auf den Rechner: unbestimmt, und die bisherige Kennung mit «Grund bekannt» bleibt', () => {
    const c = zeigeKnoten({ status: 'wartetGpu', gestartetUm: Date.now() });
    const warten = c.querySelector('[data-testid="render-warteort"] .k-warten')!;
    expect(warten.getAttribute('data-art')).toBe('unbestimmt');
    expect(c.querySelector('[data-testid="render-wartet-text"]')!.getAttribute('data-grund-bekannt')).toBe('false');
  });
});
