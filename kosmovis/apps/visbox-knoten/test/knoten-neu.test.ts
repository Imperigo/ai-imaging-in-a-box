// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, setzeModellGlb, stimmungParams, type VisGraph } from '@kosmo/kernel';
import { RenderScene } from '@kosmo/contracts';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { grundlageStandFuerKnoten, sendeGraphRenderAuftrag } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { GRUNDLAGE_PARAM } from '../../kosmo-orbit/src/modules/vis/grundlage';
import { evaluiereGraph } from '@kosmo/kernel';
import { registriereStandpunkteAbfrage, standpunkteFuer } from '../../kosmo-orbit/src/modules/vis/heim-standpunkte';
import { huellboxAlsNetz, standpunkteAbfrageDerMappe } from '../src/mappe';

/**
 * VISBOX-EIGEN (Bauplan «Neue Knoten», 21.10.2026): der Wirt reicht die Standpunkte des Knotens
 * «Kamera» mit seinen Einstellungen durch (`GET ./standpunkte?…`, dieselbe Rechnung wie der Auftrag,
 * `knotenweg.standpunkte_abfrage`), und eine Bestellung aus den neuen Knoten geht in der Form des
 * Vertrags an die Brücke — ohne gezeichnetes Bauteil, mit der Hüllbox der Mappe wie `ladeMappe`.
 */

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
let gefragt: string[] = [];

beforeEach(() => {
  gesendet = null;
  gefragt = [];
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
    if (String(url).startsWith('./standpunkte')) {
      gefragt.push(String(url));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          standpunkte: [{ kuerzel: 's', name: 'Süd', art: 'frontal', abstand_m: 30, auge: [0, -30, 1.7], blick_auf: [0, 0, 1.7], vollstaendig: true, begruendung: '' }],
          satz: 'Rechnet der Heim-PC.',
        }),
      };
    }
    if (String(url).endsWith('/bruecke/jobs')) {
      gesendet = JSON.parse(String((init!.body as FormData).get('scene')));
      return {
        ok: true,
        json: async () => ({ job_id: 'vis-1790500000-5e1a00', status: 'awaiting_approval', scene: 's.json', created_at: '2026-10-21T08:00:00Z', idle_window_only: true }),
      };
    }
    return { ok: true, blob: async () => new Blob([new Uint8Array([0x89, 0x50, 0x4e, 0x47])], { type: 'image/png' }) };
  });
});

afterEach(() => {
  registriereStandpunkteAbfrage(null);
  setzeModellGlb(null);
  vi.unstubAllGlobals();
});

describe('Visbox · neue Knoten', () => {
  it('die Standpunkte-Abfrage trägt die Mappe und die Einstellungen des Knotens', async () => {
    registriereStandpunkteAbfrage(standpunkteAbfrageDerMappe());
    standpunkteFuer({ richtungen: ['s', 'nNW'], brennweite_mm: 50, abstand: { art: 'fest', meter: 40 }, perspektive: 'frei' });
    await vi.waitFor(() => expect(gefragt).toHaveLength(1));
    expect(gefragt[0]).toBe('./standpunkte?ordner=Probemappe&richtungen=s%2CnNW&brennweite=50&abstand=40&perspektive=frei');
    const wahl = { richtungen: ['s', 'nNW'], brennweite_mm: 50, abstand: { art: 'fest' as const, meter: 40 }, perspektive: 'frei' as const };
    await vi.waitFor(() => expect(standpunkteFuer(wahl)?.stand).toBe('da'));
    expect(standpunkteFuer(wahl)?.ergebnis?.standpunkte[0]?.name).toBe('Süd');
    expect(gefragt).toHaveLength(1);
  });

  it('Stimmung, Auto-Kamera und Oberfläche gehen in der Form des Vertrags an die Brücke', async () => {
    const { runCommand, doc } = useProject.getState();
    const graphId = (runCommand('vis.graphErstellen', { name: 'Neue Knoten' }).patches[0] as { id: string }).id;
    const setze = (typ: string, params?: Record<string, string | number | boolean>) => {
      runCommand('vis.nodeSetzen', { graphId, typ, x: 0, y: 0, ...(params ? { params } : {}) });
      return doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
    };
    const verbinde = (from: string, fromPort: string, to: string, toPort: string) => runCommand('vis.verbinden', { graphId, from, fromPort, to, toPort });
    const modell = setze('modell');
    const st = setze('stimmung', { ...stimmungParams(['nebel']), drehung: 90 });
    const kam = setze('kamera', { art: 'auto', richtungen: '["sSE"]' });
    const mat = setze('materialTextur', { bibliothek: 'klinker' });
    const ober = setze('material');
    const komb = setze('kombinierer');
    const render = setze('render');
    verbinde(modell, 'szene', render, 'szene');
    verbinde(st, 'prompt', komb, 'stimmung');
    verbinde(mat, 'material', ober, 'fassade');
    verbinde(ober, 'material', komb, 'material');
    verbinde(komb, 'prompt', render, 'prompt');
    verbinde(kam, 'kameras', render, 'kameras');
    sendeGraphRenderAuftrag(graphId, render);
    await vi.waitFor(() => expect(gesendet).not.toBeNull());
    const r = gesendet!['render'] as Record<string, unknown>;
    expect(r['environment']).toEqual({ preset: 'nebel', rotationGrad: 90 });
    expect(gesendet!['cameras']).toBe('auto');
    expect(gesendet!['cameras_auto']).toEqual({ richtungen: ['sSE'] });
    expect(r['materialien']).toEqual({ fassade: { id: 'klinker' } });
    expect(RenderScene.safeParse(gesendet).success).toBe(true);
  });

  it('Befund B1 (306): «Grundlage rendern» für denselben Stand sendet nichts, nach einer anderen Stimmung wieder', async () => {
    const { runCommand, doc } = useProject.getState();
    const graphId = (runCommand('vis.graphErstellen', { name: 'B1' }).patches[0] as { id: string }).id;
    const setze = (typ: string, params?: Record<string, string | number | boolean>) => {
      runCommand('vis.nodeSetzen', { graphId, typ, x: 0, y: 0, ...(params ? { params } : {}) });
      return doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
    };
    const modell = setze('modell');
    const st = setze('stimmung', stimmungParams(['abend']));
    const render = setze('render');
    runCommand('vis.verbinden', { graphId, from: modell, fromPort: 'szene', to: render, toPort: 'szene' });
    runCommand('vis.verbinden', { graphId, from: st, fromPort: 'prompt', to: render, toPort: 'prompt' });
    const roh = evaluiereGraph(doc, doc.get<VisGraph>(graphId)!).renderAuftraege.get(render)!;
    const stand = grundlageStandFuerKnoten(doc, roh, doc.get<VisGraph>(graphId)!.nodes.find((n) => n.id === render)!.params);
    runCommand('vis.nodeParametrieren', { graphId, nodeId: render, params: { [GRUNDLAGE_PARAM.id]: 'gl-00000000000000ab', [GRUNDLAGE_PARAM.stand]: stand } });
    sendeGraphRenderAuftrag(graphId, render, undefined, { stufe: 'grundlage', wiederverwenden: true });
    await new Promise((r) => setTimeout(r, 20));
    expect(gesendet).toBeNull();
    runCommand('vis.nodeParametrieren', { graphId, nodeId: st, params: stimmungParams(['nebel']) });
    sendeGraphRenderAuftrag(graphId, render, undefined, { stufe: 'grundlage', wiederverwenden: true });
    await vi.waitFor(() => expect(gesendet).not.toBeNull());
    expect((gesendet!['render'] as Record<string, unknown>)['environment']).toEqual({ preset: 'nebel' });
  });
});
