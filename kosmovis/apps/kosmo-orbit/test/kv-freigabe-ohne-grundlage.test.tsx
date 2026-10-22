// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { type FreeMesh, type Storey, type VisGraph } from '@kosmo/kernel';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import {
  FREIGABE_OHNE_KENNUNG_SATZ,
  FREIGABE_OHNE_WIRKUNG_SATZ,
  freigabeGescheitertSatz,
  BridgeHttpError,
} from '../src/modules/vis/vis-jobs';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { KEINE_GRUNDLAGE_KURZ } from '../src/modules/vis/grundlage';
import { useProject } from '../src/state/project-store';

/**
 * Mac-Demolauf 0.3.33 (22.10.2026, Mappe ohne Grundlage): ein ueber Claude bestellter Auftrag
 * (`vis_render`, Vorschau) stand auf «wartet auf Freigabe»; am Knoten «Noch keine Grundlage —
 * zuerst «Grundlage rendern»», der Knopf aber grau. «Freigeben» tat nichts, ohne ein Wort; erst
 * Abbrechen machte «Grundlage rendern» wieder frei. Diese Probe haelt beides fest:
 *  (b) scheitert «Freigeben», steht der Grund am Knoten;
 *  (c) ein Auftrag, der nur auf Freigabe wartet, sperrt «Grundlage rendern» nicht.
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
});
function mount(graphId: string): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}
const q = (id: string) => container!.querySelector(`[data-testid="${id}"]`);
const warte = () => new Promise((r) => setTimeout(r, 0));

let zaehler = 0;
/**
 * Ein Bauteil im Dokument, ohne die Entwurfsbefehle: ein Wuerfel als Freiform, wie ihn Visbox aus
 * der Huellbox der Mappe legt (`apps/visbox-knoten/src/mappe.ts`). So laeuft die Probe in KosmoOrbit
 * und in der Visbox-Kopie (deren duenner Kern kennt `design.*` nicht).
 */
function legeEinBauteil(): void {
  const n = ++zaehler;
  const geschoss: Storey = { id: `st-kvfg-${n}`, kind: 'storey', name: 'EG', index: 9100 + n, elevation: 0, height: 3000, cutHeight: 1100 };
  const wuerfel: FreeMesh = {
    id: `fm-kvfg-${n}`,
    kind: 'freemesh',
    storeyId: geschoss.id,
    name: 'Würfel',
    positions: [0, 0, 0, 5000, 0, 0, 5000, 5000, 0, 0, 5000, 0, 0, 0, 3000, 5000, 0, 3000, 5000, 5000, 3000, 0, 5000, 3000],
    faces: [0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7],
  };
  useProject.getState().doc.apply([
    { id: geschoss.id, before: null, after: geschoss },
    { id: wuerfel.id, before: null, after: wuerfel },
  ]);
}

function graphMitRender(): { graphId: string; nodeId: string } {
  legeEinBauteil();
  const { runCommand } = useProject.getState();
  const { doc } = useProject.getState();
  const g = runCommand('vis.graphErstellen', { name: `KV-FREIGABE-${Math.random()}` });
  const graphId = (g.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  const modellId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0 });
  const nodeId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  runCommand('vis.verbinden', { graphId, from: modellId, fromPort: 'szene', to: nodeId, toPort: 'szene' });
  useVisRuntime.setState({ laeufe: {}, verlauf: {} });
  return { graphId, nodeId };
}

const JOB = 'vis-1761120000-abcdef';
/** Ein ueber `vis_render` bestellter Auftrag (ohne Stufe), der auf Freigabe wartet. */
function wartenderAuftrag(nodeId: string, mitFreigabe: boolean): void {
  act(() =>
    useVisRuntime.getState().setzeLauf(nodeId, {
      status: 'wartetFreigabe',
      memoKey: 'kv-freigabe',
      jobId: JOB,
      gestartetUm: Date.now(),
      guete: 'vorschau',
      ...(mitFreigabe ? { approvalToken: 'CONFIRMED_RENDER_1234abcd' } : {}),
    }),
  );
}

type Ruf = { url: string; methode: string };
function stubBruecke(antwort: (url: string, methode: string) => Response | Promise<Response>): Ruf[] {
  const rufe: Ruf[] = [];
  vi.stubGlobal('fetch', (async (url: unknown, init?: RequestInit) => {
    const href = String(url);
    const methode = (init?.method ?? 'GET').toUpperCase();
    rufe.push({ url: href, methode });
    return antwort(href, methode);
  }) as unknown as typeof fetch);
  return rufe;
}
const json = (status: number, body: unknown) =>
  ({ ok: status >= 200 && status < 300, status, json: async () => body, text: async () => JSON.stringify(body) }) as Response;
const zettel = (status: string) => ({ job_id: JOB, status, scene: 's', created_at: '2026-10-22T10:00:00Z' });

async function klick(id: string): Promise<void> {
  await act(async () => {
    (q(id) as HTMLButtonElement).click();
    await warte();
    await warte();
  });
}

describe('kv-freigabe-ohne-grundlage — Mac-Demolauf 0.3.33', () => {
  it('(c) wartet ein Auftrag auf Freigabe und fehlt die Grundlage: «Grundlage rendern» ist frei', () => {
    const { graphId, nodeId } = graphMitRender();
    mount(graphId);
    wartenderAuftrag(nodeId, true);
    expect(q('render-grundlage-keine')!.textContent).toBe(KEINE_GRUNDLAGE_KURZ);
    expect(q('render-freigeben')).not.toBeNull();
    expect((q('render-grundlage') as HTMLButtonElement).disabled).toBe(false);
    // «Variante erzeugen» bleibt gesperrt — es gibt keine Grundlage.
    expect((q('render-ausfuehren') as HTMLButtonElement).disabled).toBe(true);
  });

  it('Gegenprobe (c): rechnet der Auftrag schon (in der Reihe), bleibt «Grundlage rendern» gesperrt', () => {
    const { graphId, nodeId } = graphMitRender();
    mount(graphId);
    act(() => useVisRuntime.getState().setzeLauf(nodeId, { status: 'wartetGpu', memoKey: 'kv-freigabe', jobId: JOB }));
    expect((q('render-grundlage') as HTMLButtonElement).disabled).toBe(true);
  });

  it('(b) Lauf ohne Freigabe: «Freigeben» sagt am Knoten, warum und was zu tun ist — kein stilles Nichts', async () => {
    const { graphId, nodeId } = graphMitRender();
    const rufe = stubBruecke(() => json(500, {}));
    mount(graphId);
    wartenderAuftrag(nodeId, false);
    expect(q('render-freigabe-hinweis')).toBeNull();
    await klick('render-freigeben');
    expect(q('render-freigabe-hinweis')!.textContent).toBe(FREIGABE_OHNE_KENNUNG_SATZ);
    expect(rufe.filter((r) => r.url.includes('/approve'))).toHaveLength(0);
    expect(useVisRuntime.getState().laeufe[nodeId]!.status).toBe('wartetFreigabe');
    expect((q('render-grundlage') as HTMLButtonElement).disabled).toBe(false);
  });

  it('(b) die Gegenseite weist ab (403): der Grund steht am Knoten', async () => {
    const { graphId, nodeId } = graphMitRender();
    stubBruecke((url) => (url.includes('/approve') ? json(403, { fehler: 'Freigabe abgewiesen' }) : json(200, zettel('awaiting_approval'))));
    mount(graphId);
    wartenderAuftrag(nodeId, true);
    await klick('render-freigeben');
    const satz = q('render-freigabe-hinweis')!.textContent!;
    expect(satz).toBe(freigabeGescheitertSatz(new BridgeHttpError(403, 'x'), ''));
    expect(satz).toContain('passt nicht zu diesem Auftrag');
  });

  it('(b) die Antwort sagt weiter «wartet»: auch das steht am Knoten', async () => {
    const { graphId, nodeId } = graphMitRender();
    stubBruecke(() => json(200, zettel('awaiting_approval')));
    mount(graphId);
    wartenderAuftrag(nodeId, true);
    await klick('render-freigeben');
    expect(q('render-freigabe-hinweis')!.textContent).toBe(FREIGABE_OHNE_WIRKUNG_SATZ);
  });

  it('Gegenprobe (b): wirkt die Freigabe, steht kein Satz da und der Auftrag ist in der Reihe', async () => {
    const { graphId, nodeId } = graphMitRender();
    const rufe = stubBruecke(() => json(200, zettel('queued')));
    mount(graphId);
    wartenderAuftrag(nodeId, true);
    await klick('render-freigeben');
    expect(rufe.some((r) => r.url.includes(`/jobs/${JOB}/approve`) && r.methode === 'POST')).toBe(true);
    expect(useVisRuntime.getState().laeufe[nodeId]!.status).toBe('wartetGpu');
    expect(useVisRuntime.getState().laeufe[nodeId]!.freigabeHinweis).toBeUndefined();
    expect(q('render-freigabe-hinweis')).toBeNull();
  });

  it('(c) «Grundlage rendern» bei wartendem Auftrag bestellt die Grundlage und bricht den wartenden ab', async () => {
    const { graphId, nodeId } = graphMitRender();
    const rufe = stubBruecke((url) => (url.includes('/cancel') ? json(200, zettel('cancelled')) : json(500, {})));
    mount(graphId);
    wartenderAuftrag(nodeId, true);
    await klick('render-grundlage');
    const lauf = useVisRuntime.getState().laeufe[nodeId]!;
    expect(lauf.stufe).toBe('grundlage');
    expect(lauf.jobId).not.toBe(JOB);
    expect(rufe.some((r) => r.url.includes(`/jobs/${JOB}/cancel`) && r.methode === 'POST')).toBe(true);
  });
});
