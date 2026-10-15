// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, setzeModellGlb, type VisGraph } from '@kosmo/kernel';
import { RenderScene } from '@kosmo/contracts';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { sendeGraphRenderAuftrag } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { registriereSkizzenQuelle, SKIZZE_IPAD_TYP } from '../../kosmo-orbit/src/modules/vis/skizze-quelle';
import { huellboxAlsNetz, skizzenQuelleDerMappe } from '../src/mappe';

/**
 * VISBOX-EIGEN (Owner-Entscheid 96, 15.10.2026): die Skizze vom iPad führt das Bild. Mit dem Wirt
 * dieser Seite (Liste aus `GET ./mappe`) und dem glb der Mappe geht die Bestellung an `/bruecke/jobs`
 * mit `skizze: { quelle: 'mappe', name }` — «neueste» beim Klick aus der Mappe aufgelöst. Die Probe
 * aus KosmoOrbit (`kv-skizze-fuehrt.test.ts`) baut ihr Gebäude im Architekturkern und kommt darum
 * nicht mit; den Heim-PC-Teil prüft `tests/test_skizze_fuehrt.py`.
 */
const SKIZZEN = [
  { name: 'skizze-20261015-081200.png', titel: 'Vordach', erzeugt: '2026-10-15T08:12:00', ueber: 'bild-1.png', stand: 'offen' },
  { name: 'skizze-20261014-091200.png', titel: 'Fassade Süd', erzeugt: '2026-10-14T09:12:00', ueber: null, stand: 'offen' },
];

/** Ein glb-Kopf mit leerem JSON-Block — genug für Glasnaht-Prüfung und Versand. */
function glb(): ArrayBuffer {
  const js = new TextEncoder().encode(JSON.stringify({ asset: { version: '2.0' } }).padEnd(28, ' '));
  const buf = new ArrayBuffer(12 + 8 + js.length);
  const dv = new DataView(buf);
  dv.setUint32(0, 0x46546c67, true);
  dv.setUint32(4, 2, true);
  dv.setUint32(8, buf.byteLength, true);
  dv.setUint32(12, js.length, true);
  dv.setUint32(16, 0x4e4f534a, true);
  new Uint8Array(buf, 20).set(js);
  return buf;
}

let gesendet: Record<string, unknown> | null = null;

beforeEach(() => {
  gesendet = null;
  history.replaceState(null, '', '/knoten/?ordner=Probemappe');
  localStorage.setItem('kosmo.bridge', `${location.origin}/bruecke`);
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
  setzeModellGlb(glb());
  // Wie `ladeMappe`: die Hüllbox des Modells als Netz im Dokument — sonst sperrt «0 Bauteile».
  const { doc } = useProject.getState();
  const geschoss = { id: 'st-probe', kind: 'storey', name: 'Mappe', index: 0, elevation: 0, height: 3000, cutHeight: 1100 };
  const huelle = { id: 'fm-probe', kind: 'freemesh', storeyId: geschoss.id, name: 'Hüllbox', ...huellboxAlsNetz([[0, 0, 0], [8, 5, 3]]) };
  doc.apply([
    { id: geschoss.id, before: null, after: geschoss as never },
    { id: huelle.id, before: null, after: huelle as never },
  ]);
  vi.stubGlobal('fetch', async (url: string, init?: RequestInit) => {
    if (String(url).startsWith('./mappe')) return { ok: true, json: async () => ({ name: 'Probemappe', glb: true, skizzen: SKIZZEN }) };
    if (String(url).endsWith('/bruecke/jobs')) {
      gesendet = JSON.parse(String((init!.body as FormData).get('scene')));
      return {
        ok: true,
        json: async () => ({ job_id: 'vis-1790500000-5e1a00', status: 'awaiting_approval', scene: 's.json', created_at: '2026-10-15T08:00:00Z', idle_window_only: true }),
      };
    }
    return { ok: true, blob: async () => new Blob([new Uint8Array([0x89, 0x50, 0x4e, 0x47])], { type: 'image/png' }) };
  });
});

afterEach(() => {
  registriereSkizzenQuelle(null);
  setzeModellGlb(null);
  vi.unstubAllGlobals();
});

function graph(mitSkizze: boolean): { graphId: string; renderId: string } {
  const { runCommand, doc } = useProject.getState();
  const graphId = (runCommand('vis.graphErstellen', { name: 'Skizze führt' }).patches[0] as { id: string }).id;
  const setze = (typ: string, params?: Record<string, string>) => {
    runCommand('vis.nodeSetzen', { graphId, typ, x: 0, y: 0, ...(params ? { params } : {}) });
    return doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  };
  const modell = setze('modell');
  const renderId = setze('render');
  runCommand('vis.verbinden', { graphId, from: modell, fromPort: 'szene', to: renderId, toPort: 'szene' });
  const p = setze('prompt', { text: 'ein Vordach aus Holz' });
  runCommand('vis.verbinden', { graphId, from: p, fromPort: 'prompt', to: renderId, toPort: 'prompt' });
  if (mitSkizze) {
    const s = setze(SKIZZE_IPAD_TYP);
    runCommand('vis.verbinden', { graphId, from: s, fromPort: 'bild', to: renderId, toPort: 'skizze' });
  }
  return { graphId, renderId };
}

describe('Visbox · die Skizze führt das Bild (Entscheid 96)', () => {
  it('mit dem Wirt der Seite: die neueste Skizze der Mappe, ohne Anweisung aus dem Prompt (Entscheid 96a: es gilt die Bemerkung der Skizze), gültig nach dem Vertrag', async () => {
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    const { graphId, renderId } = graph(true);
    sendeGraphRenderAuftrag(graphId, renderId);
    await vi.waitFor(() => expect(gesendet).not.toBeNull());
    expect(gesendet!['skizze']).toEqual({ quelle: 'mappe', name: 'skizze-20261015-081200.png' });
    expect(gesendet!['cameras']).toBe('auto');
    expect(RenderScene.safeParse(gesendet).success).toBe(true);
    await vi.waitFor(() => expect(useVisRuntime.getState().laeufe[renderId]?.status).toBe('wartetFreigabe'));
  });

  it('ohne Skizze am Render-Knoten: kein Feld «skizze»', async () => {
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    const { graphId, renderId } = graph(false);
    sendeGraphRenderAuftrag(graphId, renderId);
    await vi.waitFor(() => expect(gesendet).not.toBeNull());
    expect('skizze' in gesendet!).toBe(false);
  });
});
