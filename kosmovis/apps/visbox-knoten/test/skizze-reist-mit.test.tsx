// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, setzeModellGlb, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { registriereSkizzenAnlage, sendeGraphRenderAuftrag, SKIZZEN_ANLAGE_FELDER } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { registriereSkizzenQuelle, SKIZZE_IPAD_TYP } from '../../kosmo-orbit/src/modules/vis/skizze-quelle';
import { huellboxAlsNetz, skizzenAnlageDerMappe, skizzenQuelleDerMappe } from '../src/mappe';

/**
 * VISBOX-EIGEN — die Skizze reist mit (Demobefund 25.10.2026, Mac 0.3.66, Mappe am Mac «haus-am-hang»):
 * «Bild aus Skizze» kam mit «liegt nur am Mac … reist beim Bestellen noch nicht mit» zurück. Seither
 * legt die Knotenansicht bei einer Mappe AM MAC (`am_mac: true`) die Skizze, ihre Unterlage (ein Bild
 * eines Auftrags, `bilder/<auftrag>/sSW__schoenbild.png`) und ihre Bemerkung der Bestellung bei. Ohne
 * Mappe am Mac geht die Bestellung wie bisher. Den Heim-PC-Teil prüft `tests/test_skizze_reist_mit.py`.
 * Namen erfunden.
 */
const UEBER = 'bilder/vis-1792842106-6e0b77/sSW__schoenbild.png';
const SKIZZEN = [
  { name: 'ipad/skizze-20261025-122953-50b5.png', titel: 'Vordach', erzeugt: '2026-10-25T12:29:53', ueber: UEBER, stand: 'offen', bemerkung: 'ein Vordach', standpunkt: 'mappe' },
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

let formular: FormData | null = null;
let amMac = true;
const geholt: string[] = [];

beforeEach(() => {
  formular = null;
  amMac = true;
  geholt.length = 0;
  history.replaceState(null, '', '/knoten/');
  localStorage.setItem('kosmo.bridge', `${location.origin}/bruecke`);
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
  setzeModellGlb(glb());
  const { doc } = useProject.getState();
  const geschoss = { id: 'st-probe', kind: 'storey', name: 'Mappe', index: 0, elevation: 0, height: 3000, cutHeight: 1100 };
  const huelle = { id: 'fm-probe', kind: 'freemesh', storeyId: geschoss.id, name: 'Hüllbox', ...huellboxAlsNetz([[0, 0, 0], [8, 5, 3]]) };
  doc.apply([
    { id: geschoss.id, before: null, after: geschoss as never },
    { id: huelle.id, before: null, after: huelle as never },
  ]);
  vi.stubGlobal('fetch', async (url: string, init?: RequestInit) => {
    const u = String(url);
    geholt.push(u);
    if (u.startsWith('./mappe')) return { ok: true, json: async () => ({ name: 'haus-am-hang', glb: true, skizzen: SKIZZEN, ...(amMac ? { am_mac: true } : {}) }) };
    if (u.endsWith('/bruecke/jobs')) {
      formular = init!.body as FormData;
      return {
        ok: true,
        json: async () => ({ job_id: 'vis-1792900000-abc123', status: 'awaiting_approval', scene: 's.json', created_at: '2026-10-25T12:30:00Z', idle_window_only: true }),
      };
    }
    return { ok: true, blob: async () => new Blob([new Uint8Array([0x89, 0x50, 0x4e, 0x47])], { type: 'image/png' }) };
  });
  registriereSkizzenQuelle(skizzenQuelleDerMappe());
  registriereSkizzenAnlage(skizzenAnlageDerMappe());
});

afterEach(() => {
  registriereSkizzenQuelle(null);
  registriereSkizzenAnlage(null);
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

describe('Visbox · die Skizze reist mit (Mappe am Mac)', () => {
  it('Mappe am Mac: Skizze, Unterlage und Angaben gehen im Formular mit', async () => {
    const { graphId, renderId } = graph(true);
    sendeGraphRenderAuftrag(graphId, renderId);
    await vi.waitFor(() => expect(formular).not.toBeNull());
    expect(JSON.parse(String(formular!.get('scene')))['skizze']).toEqual({ quelle: 'mappe', name: SKIZZEN[0]!.name });
    expect(formular!.get(SKIZZEN_ANLAGE_FELDER.skizze)).toBeInstanceOf(Blob);
    expect(formular!.get(SKIZZEN_ANLAGE_FELDER.unterlage)).toBeInstanceOf(Blob);
    expect(JSON.parse(String(formular!.get(SKIZZEN_ANLAGE_FELDER.info)))).toEqual({ ueber: UEBER, bemerkung: 'ein Vordach' });
    expect(geholt.some((u) => u.endsWith('/bruecke/jobs/vis-1792842106-6e0b77/artifacts/sSW__schoenbild.png'))).toBe(true);
    expect(SKIZZEN_ANLAGE_FELDER).toEqual({ skizze: 'skizze_png', unterlage: 'unterlage_png', info: 'skizze_info' });
  });

  it('Mappe am Heim-PC: nichts reist mit, die Bestellung wie bisher', async () => {
    amMac = false;
    const { graphId, renderId } = graph(true);
    sendeGraphRenderAuftrag(graphId, renderId);
    await vi.waitFor(() => expect(formular).not.toBeNull());
    expect(formular!.get(SKIZZEN_ANLAGE_FELDER.skizze)).toBeNull();
    expect(formular!.get(SKIZZEN_ANLAGE_FELDER.info)).toBeNull();
  });

  it('ohne Skizze am Render-Knoten: nichts reist mit', async () => {
    const { graphId, renderId } = graph(false);
    sendeGraphRenderAuftrag(graphId, renderId);
    await vi.waitFor(() => expect(formular).not.toBeNull());
    expect(formular!.get(SKIZZEN_ANLAGE_FELDER.skizze)).toBeNull();
  });
});
