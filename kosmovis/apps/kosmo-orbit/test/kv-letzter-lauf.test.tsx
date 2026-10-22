// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type VisGraph } from '@kosmo/kernel';
import { RenderResult } from '@kosmo/contracts';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import {
  ergebnisFelder,
  holeLetzteLaeufe,
  LETZTER_LAUF_PARAM,
  letzterLaufAmKnoten,
  letzterLaufText,
  merkeLetztenLauf,
  wiederzuholen,
  type GeholterAuftrag,
} from '../src/modules/vis/letzter-lauf';
import { memoKey, useVisRuntime } from '../src/modules/vis/vis-runtime';
import { useProject } from '../src/state/project-store';

/**
 * Visbox-Mac-Prüfliste 0.3.41 (22.10.2026), Mappe «Haus am Hang»: nach dem Öffnen der Mappe stand
 * am Render-Knoten «Bild erscheint hier», obwohl das KI-Bild des letzten Laufs in der Mappe lag.
 * Ursache: Die Läufe sind reine Laufzeit, und nichts im Graph nannte den Auftrag des Knotens. Jetzt
 * merkt sich der Knoten seinen letzten fertigen Lauf (ohne Rückgängig-Schritt), und die
 * Knotenansicht legt ihn beim Öffnen wieder an (`letzter-lauf.ts`).
 *
 * Gegen den alten Stand rot: dort gab es weder den Parameter noch das Wiederholen — nach dem
 * Öffnen blieb der Knoten leer (Fall «nach dem Öffnen steht das Bild wieder am Knoten»), und der
 * Poll legte nichts am Knoten ab (Fall «der Poll merkt …»).
 */

class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
if (!('createObjectURL' in URL)) {
  Object.assign(URL, { createObjectURL: () => 'blob:stub', revokeObjectURL: () => undefined });
}

const JOB = 'vis-1792688229-591d59';

function ergebnis(): RenderResult {
  const pfad = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    '../../../packages/kosmo-contracts/test/fixtures/kv-grundlage-variante.json',
  );
  return RenderResult.parse(JSON.parse(readFileSync(pfad, 'utf8')));
}

function auftrag(extra: Partial<GeholterAuftrag> = {}): GeholterAuftrag & Record<string, unknown> {
  return {
    job_id: JOB,
    status: 'done',
    scene: 'scene.json',
    created_at: '2026-10-22T10:00:00Z',
    updated_at: '2026-10-22T10:03:00Z',
    result: ergebnis(),
    ...extra,
  };
}

let root: Root | null = null;
let container: HTMLDivElement | null = null;
let graphId = '';
let nodeId = '';
let schluessel = '';
let abfragen: string[] = [];

/** Die Brücke: der Auftrag `JOB` ist fertig; seine Bilder liegen (wie in der Mappe am Mac). */
function stubBridge(antwort: () => Record<string, unknown> | null = () => auftrag()): void {
  abfragen = [];
  vi.stubGlobal('fetch', (async (url: unknown) => {
    const href = String(url);
    if (href.includes('/artifacts/')) {
      return { ok: true, status: 200, blob: async () => new Blob(['x'], { type: 'image/png' }) } as Response;
    }
    if (href.includes(`/jobs/${JOB}`)) {
      abfragen.push(href);
      const a = antwort();
      if (!a) return { ok: false, status: 404, json: async () => ({}) } as Response;
      return { ok: true, status: 200, json: async () => a } as Response;
    }
    return { ok: false, status: 404, json: async () => ({}) } as Response;
  }) as unknown as typeof fetch);
}

function params(): Record<string, unknown> {
  return useProject.getState().doc.get<VisGraph>(graphId)!.nodes.find((n) => n.id === nodeId)!.params ?? {};
}

function montiere(): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

async function warte(): Promise<void> {
  for (let i = 0; i < 10; i++) {
    await act(async () => {
      await Promise.resolve();
    });
  }
}

const knotenText = (): string => container!.querySelector('[data-testid="vis-node-render"]')?.textContent ?? '';

beforeEach(() => {
  stubBridge();
  useVisRuntime.setState({ laeufe: {}, verlauf: {}, laufZaehler: {} });
  const { runCommand, doc } = useProject.getState();
  graphId = (runCommand('vis.graphErstellen', { name: `Letzter-${Math.random()}` }).patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 40, y: 20 });
  const graph = doc.get<VisGraph>(graphId)!;
  nodeId = graph.nodes.at(-1)!.id;
  schluessel = memoKey(evaluiereGraph(doc, graph).renderAuftraege.get(nodeId)!);
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('letzter Lauf — der Parameter am Knoten', () => {
  it('liest nur eine gültige Kennung mit memoKey; Stufe und Stand gehen mit', () => {
    const text = letzterLaufText({ jobId: JOB, memoKey: 'm', stufe: 'grundlage', grundlageStand: 's1' });
    expect(letzterLaufAmKnoten({ [LETZTER_LAUF_PARAM]: text })).toEqual({
      jobId: JOB,
      memoKey: 'm',
      stufe: 'grundlage',
      grundlageStand: 's1',
    });
    expect(letzterLaufAmKnoten(undefined)).toBeNull();
    expect(letzterLaufAmKnoten({ [LETZTER_LAUF_PARAM]: 'kein json' })).toBeNull();
    expect(letzterLaufAmKnoten({ [LETZTER_LAUF_PARAM]: JSON.stringify({ jobId: '../x', memoKey: 'm' }) })).toBeNull();
    expect(letzterLaufAmKnoten({ [LETZTER_LAUF_PARAM]: JSON.stringify({ jobId: JOB }) })).toBeNull();
  });

  it('merken: am Render-Knoten, ohne Rückgängig-Schritt, einmal je Kennung', () => {
    const vorher = useProject.getState().history.undoStack.length;
    expect(merkeLetztenLauf(nodeId, { graphId, memoKey: schluessel }, JOB)).toBe(true);
    expect(letzterLaufAmKnoten(params())).toEqual({ jobId: JOB, memoKey: schluessel });
    expect(useProject.getState().history.undoStack.length, 'kein Schritt des Architekten').toBe(vorher);
    expect(merkeLetztenLauf(nodeId, { graphId, memoKey: schluessel }, JOB), 'dieselbe Kennung: nichts').toBe(false);
  });

  it('merken: nicht für eine Varianten-Kennung, einen fremden Graph oder eine falsche Kennung', () => {
    expect(merkeLetztenLauf('variante-abend-1', { graphId, memoKey: 'm' }, JOB)).toBe(false);
    expect(merkeLetztenLauf(nodeId, { graphId: 'gibt-es-nicht', memoKey: 'm' }, JOB)).toBe(false);
    expect(merkeLetztenLauf(nodeId, { memoKey: 'm' }, JOB)).toBe(false);
    expect(merkeLetztenLauf(nodeId, { graphId, memoKey: 'm' }, 'job-1')).toBe(false);
    expect(params()[LETZTER_LAUF_PARAM]).toBeUndefined();
  });

  it('wiederzuholen: nur Render-Knoten ohne Lauf mit gemerkter Kennung', () => {
    merkeLetztenLauf(nodeId, { graphId, memoKey: schluessel }, JOB);
    const graph = useProject.getState().doc.get<VisGraph>(graphId)!;
    expect(wiederzuholen(graph, {}).map((w) => w.nodeId)).toEqual([nodeId]);
    expect(wiederzuholen(graph, { [nodeId]: { status: 'rendert' } })).toEqual([]);
  });
});

describe('letzter Lauf — wiederholen', () => {
  it('fertig mit Bild: der Lauf steht wieder am Knoten, mit denselben Feldern wie aus dem Poll', async () => {
    merkeLetztenLauf(nodeId, { graphId, memoKey: schluessel }, JOB);
    const graph = useProject.getState().doc.get<VisGraph>(graphId)!;
    expect(await holeLetzteLaeufe(graph, async () => auftrag())).toBe(1);
    const lauf = useVisRuntime.getState().laeufe[nodeId]!;
    const r = ergebnis();
    expect(lauf).toMatchObject({ status: 'fertig', jobId: JOB, graphId, memoKey: schluessel, bild: r.images[0] });
    expect(lauf.fertigUm).toBe(Date.parse('2026-10-22T10:03:00Z'));
    const { fertigUm: _a, ...ausPoll } = ergebnisFelder(r, {});
    expect(lauf).toMatchObject(ausPoll);
  });

  it('still, wenn der Auftrag fehlt, nicht fertig oder ohne Bild ist — und nie über einen Lauf', async () => {
    merkeLetztenLauf(nodeId, { graphId, memoKey: schluessel }, JOB);
    const graph = useProject.getState().doc.get<VisGraph>(graphId)!;
    expect(await holeLetzteLaeufe(graph, async () => Promise.reject(new Error('404')))).toBe(0);
    expect(await holeLetzteLaeufe(graph, async () => auftrag({ status: 'running', result: undefined }))).toBe(0);
    expect(await holeLetzteLaeufe(graph, async () => auftrag({ result: { ...ergebnis(), images: [] } }))).toBe(0);
    expect(useVisRuntime.getState().laeufe[nodeId]).toBeUndefined();
    useVisRuntime.getState().setzeLauf(nodeId, { status: 'rendert', jobId: 'vis-1-aaaaaa', memoKey: 'neu' });
    expect(await holeLetzteLaeufe(graph, async () => auftrag())).toBe(0);
    expect(useVisRuntime.getState().laeufe[nodeId]!.status).toBe('rendert');
  });
});

describe('letzter Lauf — in der Knotenansicht (Befund Mac 0.3.41)', () => {
  it('der Poll merkt die Kennung eines fertigen Laufs mit Bild am Knoten', async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
    montiere();
    act(() =>
      useVisRuntime
        .getState()
        .setzeLauf(nodeId, { status: 'rendert', jobId: JOB, graphId, memoKey: schluessel, gestartetUm: Date.now() }),
    );
    act(() => {
      vi.advanceTimersByTime(2600);
    });
    await warte();
    expect(useVisRuntime.getState().laeufe[nodeId]!.status).toBe('fertig');
    expect(letzterLaufAmKnoten(params())).toEqual({ jobId: JOB, memoKey: schluessel });
  });

  it('nach dem Öffnen steht das Bild wieder am Knoten statt «Bild erscheint hier»', async () => {
    merkeLetztenLauf(nodeId, { graphId, memoKey: schluessel }, JOB);
    // Das Öffnen: die Laufzeit ist leer (neue Seite), der Graph mit dem Parameter ist da.
    useVisRuntime.setState({ laeufe: {}, verlauf: {}, laufZaehler: {} });
    montiere();
    await warte();
    expect(abfragen.length, 'einmal abgefragt').toBeGreaterThanOrEqual(1);
    const lauf = useVisRuntime.getState().laeufe[nodeId];
    expect(lauf?.status).toBe('fertig');
    expect(lauf?.jobId).toBe(JOB);
    expect(knotenText()).not.toContain('Bild erscheint hier');
    expect(knotenText(), 'nicht veraltet: derselbe Auftrag').not.toContain('veraltet');
  });

  it('ohne gemerkte Kennung bleibt alles wie bisher: keine Abfrage, «Bild erscheint hier»', async () => {
    montiere();
    await warte();
    expect(abfragen).toEqual([]);
    expect(knotenText()).toContain('Bild erscheint hier');
  });
});
