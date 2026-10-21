// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type VisGraph } from '@kosmo/kernel';
import { RenderResult } from '@kosmo/contracts';
import { koerperBreite, NodeCanvas, NODE_W } from '../src/modules/vis/NodeCanvas';
import { memoKey, useVisRuntime, type NodeLauf } from '../src/modules/vis/vis-runtime';
import {
  ANSICHT_PARAM,
  bildAnsichtAmKnoten,
  BILD_MIN_BREITE,
  grundbildZumBild,
  mitGrundbild,
  nebeneinanderPasst,
  wirksameAnsicht,
} from '../src/modules/vis/nebeneinander';
import { useProject } from '../src/state/project-store';

/**
 * Entscheid 117a (Owner per Klickfrage, 21.10.2026; Blatt 35) — W-4, Grundbild neben dem KI-Bild, der Teil ohne
 * Waende (kommt wortgleich in die Visbox-Kopie; die Bestellung prueft `kv-nebeneinander.test.tsx`, sie braucht
 * `design.*`-Befehle):
 *  - der Render-Knoten bestellt das Grundbild von sich aus mit (`render.passes` enthaelt `schoenbild`), nicht mit
 *    «Grundlage rendern» (dort `alle`), «nur Cycles», Strichzeichnung oder fuer den Varianten-Knoten;
 *  - der Poll legt `<kamera>__schoenbild.png` zur Kamera des Hauptbilds an den Lauf (`NodeLauf.grundbild`);
 *  - Entscheid 119: am 196 px breiten Render-Knoten stehen KI-Bild und Grundbild schon nebeneinander (je 96 px),
 *    beide beschriftet; bei 184 px (alle anderen Knoten) fiele es auf das KI-Bild zurueck. Ein Klick zeigt beide
 *    gross, dort der Umschalter (`KTabs`), Vorgabe nebeneinander;
 *  - ohne Grundbild (aelterer Lauf) bleibt das Bild wie bisher — allein, ohne Luecke, ohne Klickflaeche.
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
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
function mount(graphId: string): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}
const q = (id: string) => container!.querySelector(`[data-testid="${id}"]`);
const qd = (id: string) => document.querySelector(`[data-testid="${id}"]`);

function graphMitRender(params: Record<string, string | number | boolean> = {}): { graphId: string; nodeId: string } {
  const { runCommand, doc } = useProject.getState();
  const g = runCommand('vis.graphErstellen', { name: `KV-NB-${Math.random()}` });
  const graphId = (g.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  const modellId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0, params });
  const nodeId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  runCommand('vis.verbinden', { graphId, from: modellId, fromPort: 'szene', to: nodeId, toPort: 'szene' });
  runCommand('vis.nodeSetzen', { graphId, typ: 'prompt', x: 0, y: 300, params: { text: 'Abendlicht' } });
  const promptId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  runCommand('vis.verbinden', { graphId, from: promptId, fromPort: 'prompt', to: nodeId, toPort: 'prompt' });
  useVisRuntime.setState({ laeufe: {}, verlauf: {} });
  return { graphId, nodeId };
}

const paramAmKnoten = (graphId: string, nodeId: string) =>
  useProject.getState().doc.get<VisGraph>(graphId)!.nodes.find((n) => n.id === nodeId)!.params ?? {};

function memo(graphId: string, nodeId: string): string {
  const { doc } = useProject.getState();
  return memoKey(evaluiereGraph(doc, doc.get<VisGraph>(graphId)!).renderAuftraege.get(nodeId)!);
}

/** Das echte Ergebnis der Gegenseite mit Ebenen (E124, `Suedost.png` / `Suedost__schoenbild.png`). */
function e124(): Record<string, unknown> {
  return JSON.parse(
    readFileSync(
      path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../packages/kosmo-contracts/test/fixtures/e124-render-result.json'),
      'utf8',
    ),
  ) as Record<string, unknown>;
}

describe('kv-nebeneinander — reine Regeln', () => {
  it('mitGrundbild behaelt bestehende Paesse und ergaenzt nur, was fehlt', () => {
    expect(mitGrundbild()).toEqual(['schoenbild']);
    expect(mitGrundbild('alle')).toBe('alle');
    expect(mitGrundbild(['tiefe'])).toEqual(['tiefe', 'schoenbild']);
    expect(mitGrundbild(['schoenbild', 'tiefe'])).toEqual(['schoenbild', 'tiefe']);
  });

  it('grundbildZumBild findet die Ebene zur Kamera des Bildes — aus dem echten Ergebnis der Gegenseite', () => {
    const r = RenderResult.parse(e124());
    expect(grundbildZumBild(r.ebenen, 'Suedost.png', r.images)).toBe('Suedost__schoenbild.png');
    expect(grundbildZumBild(r.ebenen, 'Suedwest.png', r.images)).toBe('Suedwest__schoenbild.png');
    // Ohne Ebenen (aelterer Lauf) kein Grundbild.
    expect(grundbildZumBild(undefined, 'Suedost.png')).toBeUndefined();
    // Bestellt, aber nicht geliefert: kein Grundbild, die KI-Kachel steht allein.
    expect(grundbildZumBild([{ kamera: 'Suedost', art: 'schoenbild', datei: null }], 'Suedost.png')).toBeUndefined();
    // Passt der Bildname nicht, gilt die Kamera an derselben Stelle.
    expect(
      grundbildZumBild([{ kamera: 'K1', art: 'schoenbild', datei: 'K1__schoenbild.png' }], 'bild-0.png', ['bild-0.png'], [{ kamera: 'K1' }]),
    ).toBe('K1__schoenbild.png');
    expect(grundbildZumBild([{ kamera: 'K1', art: 'tiefe', datei: 'K1__tiefe.png' }], 'K1.png')).toBeUndefined();
  });

  it('Vorgabe nebeneinander; am 196 px breiten Render-Knoten passt es, bei 184 px Rueckfall statt Bilder unter 96 px', () => {
    // Entscheid 119: der Render-Knoten ist so breit, dass «nebeneinander» schon am Knoten steht.
    expect(koerperBreite('render')).toBe(196);
    expect(nebeneinanderPasst(koerperBreite('render'))).toBe(true);
    expect(wirksameAnsicht('nebeneinander', true, koerperBreite('render'))).toEqual({ ansicht: 'nebeneinander', rueckfall: false });
    expect(bildAnsichtAmKnoten({})).toBe('nebeneinander');
    expect(bildAnsichtAmKnoten({ [ANSICHT_PARAM]: 'nur-grundbild' })).toBe('nur-grundbild');
    expect(bildAnsichtAmKnoten({ [ANSICHT_PARAM]: 'quer' })).toBe('nebeneinander');
    expect(nebeneinanderPasst(NODE_W - 16)).toBe(false);
    expect(nebeneinanderPasst(2 * BILD_MIN_BREITE + 4)).toBe(true);
    expect(wirksameAnsicht('nebeneinander', true, NODE_W - 16)).toEqual({ ansicht: 'nur-ki', rueckfall: true });
    expect(wirksameAnsicht('nebeneinander', true, 400)).toEqual({ ansicht: 'nebeneinander', rueckfall: false });
    expect(wirksameAnsicht('nur-grundbild', true, NODE_W - 16)).toEqual({ ansicht: 'nur-grundbild', rueckfall: false });
    expect(wirksameAnsicht('nur-grundbild', false, 400)).toEqual({ ansicht: 'nur-ki', rueckfall: false });
  });
});

describe('kv-nebeneinander — das Grundbild aus dem Ergebnis an den Lauf', () => {
  async function pollMit(stufe?: 'grundlage' | 'variante'): Promise<NodeLauf | undefined> {
    const { graphId, nodeId } = graphMitRender();
    const result = e124();
    const jobId = String(result['job_id']);
    vi.stubGlobal('fetch', (async (url: unknown) => {
      const href = String(url);
      if (href.endsWith(`/jobs/${jobId}`)) {
        return { ok: true, status: 200, json: async () => ({ job_id: jobId, status: 'done', scene: 's.json', created_at: '2026-10-21T00:00:00Z', result }) } as Response;
      }
      return { ok: false, status: 404, json: async () => ({}) } as Response;
    }) as unknown as typeof fetch);
    useVisRuntime.getState().setzeLauf(nodeId, {
      status: 'rendert',
      jobId,
      memoKey: memo(graphId, nodeId),
      gestartetUm: Date.now(),
      grundbild: 'alt__schoenbild.png',
      ...(stufe ? { stufe } : {}),
    });
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    vi.useFakeTimers();
    mount(graphId);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });
    return useVisRuntime.getState().laeufe[nodeId];
  }

  it('ein KI-Lauf traegt das Grundbild zur Kamera des Hauptbilds', async () => {
    expect(await pollMit('variante')).toMatchObject({ status: 'fertig', bild: 'Suedost.png', grundbild: 'Suedost__schoenbild.png' });
  });

  it('nach «Grundlage rendern» kein Grundbild daneben — das Bild IST das Grundbild; der alte Wert bleibt nicht stehen', async () => {
    const lauf = await pollMit('grundlage');
    expect(lauf?.status).toBe('fertig');
    expect(lauf?.grundbild).toBeUndefined();
  });
});

describe('kv-nebeneinander — am Knoten und gross', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', (async () => ({ ok: false, status: 404, json: async () => ({}) }) as Response) as unknown as typeof fetch);
  });

  function fertig(graphId: string, nodeId: string, extra: Partial<NodeLauf> = {}): void {
    useVisRuntime.setState({
      laeufe: {
        [nodeId]: { status: 'fertig', jobId: 'vis-1-abcdef', bild: 'K1.png', bilder: ['K1.png'], memoKey: memo(graphId, nodeId), ...extra } as NodeLauf,
      },
      verlauf: {},
    });
  }

  it('ohne Grundbild (aelterer Lauf): ein Bild, keine Beschriftung; ein Klick zeigt es gross (L4-14)', () => {
    const { graphId, nodeId } = graphMitRender();
    fertig(graphId, nodeId);
    mount(graphId);
    const haupt = q('render-hauptbild')!;
    // Bis L4-14 war das Bild ohne Grundbild keine Klickflaeche; seither oeffnet es den Lauf gross.
    expect(haupt.getAttribute('role')).toBe('button');
    expect(haupt.getAttribute('aria-label')).toBe('Bild gross anzeigen');
    expect(haupt.querySelectorAll('[data-testid="render-bild"], [data-testid="render-bild-laedt"]').length).toBe(1);
    expect(q('render-bild-beschriftung')).toBeNull();
    expect(q('render-grundbild')).toBeNull();
  });

  it('mit Grundbild: am Knoten beide nebeneinander (Entscheid 119), Klick zeigt beide gross — Vorgabe nebeneinander', () => {
    const { graphId, nodeId } = graphMitRender();
    fertig(graphId, nodeId, { grundbild: 'K1__schoenbild.png', guete: 'vorschau' });
    mount(graphId);
    const haupt = q('render-hauptbild')!;
    expect(haupt.getAttribute('data-ansicht')).toBe('nebeneinander');
    expect(haupt.getAttribute('data-rueckfall')).toBe('false');
    expect(haupt.querySelectorAll('.vis-bildpaar-zelle').length).toBe(2);
    expect(q('render-bild-beschriftung')!.textContent).toBe('KI-Bild');
    expect(q('render-grundbild-beschriftung')!.textContent).toBe('Grundbild mit Licht');
    // Mit der Marke «Vorschau» rueckt die Beschriftung des KI-Bilds ueber sie (Klasse, CSS unten).
    expect(haupt.classList.contains('vis-hauptbild--vorschau')).toBe(true);
    expect(q('render-guete-marke')).not.toBeNull();
    // Die Hoehe bleibt die der Registerzeile — der Knoten waechst nicht.
    expect((haupt as HTMLElement).style.height).toBe('110px');
    act(() => (haupt as HTMLElement).click());
    expect(qd('render-bildpaar-gross')).not.toBeNull();
    expect(qd('render-bildpaar')!.getAttribute('data-ansicht')).toBe('nebeneinander');
    expect(qd('render-bildpaar-ki')!.textContent).toContain('KI-Bild');
    expect(qd('render-bildpaar-grundbild')!.textContent).toContain('Grundbild mit Licht');
    // Die Vorschau-Marke nur am KI-Bild.
    expect(qd('render-bildpaar-ki')!.querySelector('[data-testid="render-bildpaar-guete-marke"]')).not.toBeNull();
    expect(qd('render-bildpaar-grundbild')!.querySelector('[data-guete]')).toBeNull();
    // Umschalter als KTabs, drei Reiter, mit Kennung je Knopf.
    expect(qd('render-ansicht')!.getAttribute('role')).toBe('tablist');
    expect(qd('render-ansicht-nebeneinander')!.getAttribute('aria-selected')).toBe('true');
  });

  it('«nur Grundbild» setzt den Knoten-Parameter, gilt auch am Knoten; Undo nimmt es zurueck', () => {
    const { graphId, nodeId } = graphMitRender();
    fertig(graphId, nodeId, { grundbild: 'K1__schoenbild.png', guete: 'vorschau' });
    mount(graphId);
    act(() => (q('render-hauptbild') as HTMLElement).click());
    act(() => (qd('render-ansicht-nur-grundbild') as HTMLButtonElement).click());
    expect(paramAmKnoten(graphId, nodeId)[ANSICHT_PARAM]).toBe('nur-grundbild');
    expect(qd('render-bildpaar-ki')).toBeNull();
    expect(qd('render-bildpaar-grundbild')).not.toBeNull();
    expect(q('render-hauptbild')!.getAttribute('data-ansicht')).toBe('nur-grundbild');
    expect(q('render-grundbild-beschriftung')!.textContent).toBe('Grundbild mit Licht');
    expect(q('render-guete-marke'), 'keine Vorschau-Marke am Grundbild').toBeNull();
    act(() => (qd('render-ansicht-nur-ki') as HTMLButtonElement).click());
    expect(qd('render-bildpaar-grundbild')).toBeNull();
    act(() => useProject.getState().undo());
    expect(bildAnsichtAmKnoten(paramAmKnoten(graphId, nodeId))).toBe('nur-grundbild');
    // Escape schliesst die grosse Ansicht.
    act(() => {
      qd('render-bildpaar')!.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(qd('render-bildpaar-gross')).toBeNull();
  });

  it('CSS: am Knoten haelt jede Zelle mindestens 96 px; gross rueckt das Grundbild unter das KI-Bild statt zu stauchen', () => {
    const css = readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/modules/vis/vis-visual.css'), 'utf8');
    expect(/\n\.vis-bildpaar-zelle \{[^}]*min-width: 96px;/.test(css)).toBe(true);
    expect(/\n\.vis-bildpaar-gitter \{[^}]*minmax\(96px, 1fr\)/.test(css)).toBe(true);    // Entscheid 119: mit der Marke «Vorschau» liegt die Beschriftung des KI-Bilds ueber ihr, nicht darunter.
    expect(/\.vis-hauptbild--vorschau \.vis-bildpaar-zelle:first-child > \.vis-bildpaar-beschriftung \{[^}]*bottom: calc\(2 \* var\(--k-s2\) \+ 16px\)/.test(css)).toBe(true);
  });
});
