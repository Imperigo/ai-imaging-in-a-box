// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, History, KosmoDoc, setzeModellGlb, type VisGraph } from '@kosmo/kernel';
import { RenderResult } from '@kosmo/contracts';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { grundlageStandFuerKnoten, sendeGraphRenderAuftrag } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import {
  GRUNDLAGE_PARAM,
  grundlageAmKnoten,
  grundlageNachErgebnis,
  grundlageZustand,
} from '../../kosmo-orbit/src/modules/vis/grundlage';
import { huellboxAlsNetz } from '../src/mappe';

/**
 * Visbox-Mac-Prüfliste 0.3.35 (22.10.2026), Befund 3: Ein Auftrag rechnete Grundbild und KI für vier
 * Standpunkte (voll, Entscheid 98c). Danach stand am Render-Knoten weiter «Grundlage veraltet — erst neu
 * rendern». Der Heim-PC rechnet bei einem vollen Lauf eine neue Grundlage und meldet sie
 * (`result.grundlage`, `wiederverwendet: false`); der Knoten merkte sich aber nur die von «Grundlage
 * rendern». Hier in der Mappe der Visbox (Hüllbox als Netz, glb), wie `bild-aus-skizze.test.tsx`; die
 * Probe von KosmoOrbit (`kv-grundlage-auftrag`) baut eine Wand im Architekturkern und läuft hier nicht.
 * Gegen den alten Stand rot.
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

beforeEach(() => {
  gesendet = null;
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
      gesendet = JSON.parse(String((init!.body as FormData).get('scene')));
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
  return { graphId, renderId };
}

function ergebnis(): RenderResult {
  const pfad = resolve(process.cwd(), '../../packages/kosmo-contracts/test/fixtures/kv-grundlage-nur-grundlage.json');
  return RenderResult.parse(JSON.parse(readFileSync(pfad, 'utf8')));
}

describe('Befund 3 (0.3.35) · nach einem vollen Auftrag ist die Grundlage aktuell', () => {
  it('die beim vollen Lauf gerechnete Grundlage wird die des Knotens — «veraltet» verschwindet', async () => {
    const { graphId, renderId } = graph();
    const { doc, runCommand } = useProject.getState();
    const params = () => doc.get<VisGraph>(graphId)!.nodes.find((n) => n.id === renderId)!.params ?? {};
    // Eine alte Grundlage eines anderen Stands am Knoten — so stand es am Mac vor dem Auftrag.
    runCommand('vis.nodeParametrieren', {
      graphId,
      nodeId: renderId,
      params: { [GRUNDLAGE_PARAM.id]: 'gl-0123456789abcdef', [GRUNDLAGE_PARAM.seed]: 1, [GRUNDLAGE_PARAM.stand]: 'alter-stand', [GRUNDLAGE_PARAM.kameras]: 4 },
    });
    const roh = evaluiereGraph(doc, doc.get<VisGraph>(graphId)!).renderAuftraege.get(renderId)!;
    const standJetzt = grundlageStandFuerKnoten(doc, roh, params());
    expect(grundlageZustand(grundlageAmKnoten(params(), standJetzt), standJetzt)).toBe('veraltet');

    sendeGraphRenderAuftrag(graphId, renderId, undefined, { kameraWahl: 'auto' });
    await vi.waitFor(() => expect(gesendet).not.toBeNull());
    expect(((gesendet!['vis'] ?? {}) as Record<string, unknown>)['skip']).toBe(false);
    const lauf = useVisRuntime.getState().laeufe[renderId]!;
    expect(lauf.stufe).toBeUndefined();
    expect(lauf.grundlageStand).toBe(standJetzt);

    const r = ergebnis();
    expect(grundlageNachErgebnis(renderId, lauf, r)).toBe('abgelegt');
    const am = grundlageAmKnoten(params(), standJetzt)!;
    expect(am.id).toBe(r.grundlage!.id);
    expect(grundlageZustand(am, standJetzt)).toBe('aktuell');
  });
});
