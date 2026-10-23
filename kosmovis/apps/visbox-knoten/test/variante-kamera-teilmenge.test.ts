// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, History, KosmoDoc, setzeModellGlb, type AutoKameraStandpunkt, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { sendeGraphRenderAuftrag } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { merkeGrundlage } from '../../kosmo-orbit/src/modules/vis/grundlage';
import { huellboxAlsNetz } from '../src/mappe';

/**
 * Geraeteprobe R56 der HomeStation (23.10.2026): eine Variante mit nur Eingang und Übersicht auf einer
 * Grundlage mit drei Kameras rechnete die Grundlage neu (148 s statt rund 60 s). Hier in der Mappe der
 * Visbox (Hüllbox als Netz, glb) wie `grundlage-voller-auftrag.test.ts`; die Probe des Originals
 * (`kv-r56-kamera-teilmenge`) baut den Startgraphen im Architekturkern und läuft hier nicht. Gegen den
 * alten Stand rot. Namen und Zahlen erfunden.
 */
const DREI = [
  { name: 'Eingang', position: [4, 1.6, 14], target: [4, 1.5, 2.5], fov: 50 },
  { name: 'Übersicht', position: [-12, 9, 16], target: [4, 1.5, 2.5], fov: 45 },
  { name: 'Garten', position: [18, 1.6, -9], target: [4, 1.5, 2.5], fov: 55 },
];
const GL = 'gl-5a6b7c8d9e0f1a2b';

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

let gesendet: Record<string, unknown>[] = [];

beforeEach(() => {
  gesendet = [];
  history.replaceState(null, '', '/knoten/?ordner=Probemappe');
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
    if (String(url).endsWith('/bruecke/jobs')) {
      gesendet.push(JSON.parse(String((init!.body as FormData).get('scene'))));
      return {
        ok: true,
        json: async () => ({ job_id: 'vis-1792688229-591d59', status: 'awaiting_approval', scene: 's.json', created_at: '2026-10-22T08:00:00Z', idle_window_only: true }),
      };
    }
    return { ok: true, json: async () => ({}) };
  });
});

afterEach(() => {
  setzeModellGlb(null);
  vi.unstubAllGlobals();
});

function graph(): { graphId: string; renderId: string } {
  const { runCommand, doc } = useProject.getState();
  const graphId = (runCommand('vis.graphErstellen', { name: 'Demo Haus am Hang' }).patches[0] as { id: string }).id;
  const setze = (typ: string, params?: Record<string, string>) => {
    runCommand('vis.nodeSetzen', { graphId, typ, x: 0, y: 0, ...(params ? { params } : {}) });
    return doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  };
  const modell = setze('modell');
  const renderId = setze('render');
  runCommand('vis.verbinden', { graphId, from: modell, fromPort: 'szene', to: renderId, toPort: 'szene' });
  const p = setze('prompt', { text: 'Haus am Hang, Sichtbeton' });
  runCommand('vis.verbinden', { graphId, from: p, fromPort: 'prompt', to: renderId, toPort: 'prompt' });
  const k = setze('kamera', { art: 'manuell', kameras: JSON.stringify(DREI) });
  runCommand('vis.verbinden', { graphId, from: k, fromPort: 'kameras', to: renderId, toPort: 'kameras' });
  return { graphId, renderId };
}

async function mitGrundlage(): Promise<{ graphId: string; renderId: string; alle: AutoKameraStandpunkt[] }> {
  const { graphId, renderId } = graph();
  const { doc } = useProject.getState();
  sendeGraphRenderAuftrag(graphId, renderId, undefined, { stufe: 'grundlage' });
  await vi.waitFor(() => expect(gesendet).toHaveLength(1));
  const lauf = useVisRuntime.getState().laeufe[renderId]!;
  merkeGrundlage(graphId, renderId, { id: GL, wiederverwendet: false, kameras: 3, ebenen: ['schoenbild', 'tiefe'] }, lauf.grundlageStand!);
  const alle = evaluiereGraph(doc, doc.get<VisGraph>(graphId)!).renderAuftraege.get(renderId)!.kameras!;
  return { graphId, renderId, alle };
}

function variante(graphId: string, renderId: string, kameras: AutoKameraStandpunkt[]): void {
  const g = useProject.getState().doc.get<VisGraph>(graphId)!;
  sendeGraphRenderAuftrag(graphId, renderId, undefined, { variante: { graph: g, laufId: `v::${kameras.length}::${Math.random()}`, kameras } });
}

describe('R56 · eine Teilmenge der Kameras rechnet auf der Grundlage', () => {
  it('Eingang und Übersicht von dreien: vis.grundlage geht mit, bestellt werden nur die zwei', async () => {
    const { graphId, renderId, alle } = await mitGrundlage();
    expect(alle.map((k) => k.name)).toEqual(['Eingang', 'Übersicht', 'Garten']);
    variante(graphId, renderId, [alle[0]!, alle[1]!]);
    await vi.waitFor(() => expect(gesendet).toHaveLength(2));
    const s = gesendet[1]!;
    expect((s['vis'] as Record<string, unknown>)['grundlage']).toBe(GL);
    expect((s['cameras'] as { name: string }[]).map((k) => k.name)).toEqual(['Eingang', 'Übersicht']);
  });

  it('eine verschobene Kamera: keine Grundlage, wie bisher', async () => {
    const { graphId, renderId, alle } = await mitGrundlage();
    variante(graphId, renderId, [{ ...alle[0]!, position: [5, 1.6, 14] }, alle[1]!]);
    await vi.waitFor(() => expect(gesendet).toHaveLength(2));
    expect(gesendet[1]!['vis']).not.toHaveProperty('grundlage');
  });
});
