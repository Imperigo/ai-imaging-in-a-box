// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, renderZeile, setzeModellGlb, type VisGraph } from '@kosmo/kernel';
import { RenderScene } from '@kosmo/contracts';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { sendeGraphRenderAuftrag } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import {
  freigabeZeile,
  registriereSkizzenQuelle,
  SKIZZE_IPAD_TYP,
  SKIZZE_OHNE_BEMERKUNG_SATZ,
} from '../../kosmo-orbit/src/modules/vis/skizze-quelle';
import { bestelltesWerkzeugZusatz } from '../../kosmo-orbit/src/modules/vis/skizze-fuehrt';
import { huellboxAlsNetz, skizzenQuelleDerMappe } from '../src/mappe';

/**
 * VISBOX-EIGEN, Befund F4 (Demolauf 24.10.2026, Mac 0.3.54 / Heim-PC 0.3.55): «Bild aus Skizze»
 * scheiterte dreimal mit «prompt fehlt oder ist leer (None)». Das iPad legt die Skizze mit der
 * Bemerkung «gewünschter Name: Variante A» ab; die Knotenansicht hielt das für eine Bemerkung und
 * schickte den Prompt nicht mit. Geprüft mit dem Wirt dieser Seite und dem glb der Mappe — auch für
 * einen Heim-PC, der die Bemerkung noch ungekürzt meldet (vor dem Kern-Fix). Die Probe aus
 * KosmoOrbit (`kv-skizze-anweisung.test.ts`) baut ihr Gebäude im Architekturkern und kommt darum
 * nicht mit; den Heim-PC-Teil prüft `tests/test_skizze_anweisung_f4.py`.
 */
const SKIZZEN = [
  { name: 'ipad/skizze-20261024-081200.png', titel: null, erzeugt: '2026-10-24T08:12:00', ueber: null, stand: 'offen', bemerkung: 'gewünschter Name: Variante A' },
];

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
let anzahl = 0;

beforeEach(() => {
  gesendet = null;
  anzahl = 0;
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
    if (String(url).startsWith('./mappe')) return { ok: true, json: async () => ({ name: 'Probemappe', glb: true, skizzen: SKIZZEN }) };
    if (String(url).endsWith('/bruecke/jobs')) {
      anzahl += 1;
      gesendet = JSON.parse(String((init!.body as FormData).get('scene')));
      return {
        ok: true,
        json: async () => ({
          job_id: 'vis-1761300000-5e1a00',
          status: 'awaiting_approval',
          approval_token: 'CONFIRMED_RENDER_0123456789abcdef',
          scene: 's.json',
          created_at: '2026-10-24T08:00:00Z',
          idle_window_only: true,
        }),
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

function graph(prompt: string): { graphId: string; renderId: string } {
  const { runCommand, doc } = useProject.getState();
  const graphId = (runCommand('vis.graphErstellen', { name: 'F4' }).patches[0] as { id: string }).id;
  const setze = (typ: string, params?: Record<string, string>) => {
    runCommand('vis.nodeSetzen', { graphId, typ, x: 0, y: 0, ...(params ? { params } : {}) });
    return doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  };
  const modell = setze('modell');
  const renderId = setze('render');
  runCommand('vis.verbinden', { graphId, from: modell, fromPort: 'szene', to: renderId, toPort: 'szene' });
  if (prompt) {
    const p = setze('prompt', { text: prompt });
    runCommand('vis.verbinden', { graphId, from: p, fromPort: 'prompt', to: renderId, toPort: 'prompt' });
  }
  const s = setze(SKIZZE_IPAD_TYP);
  runCommand('vis.verbinden', { graphId, from: s, fromPort: 'bild', to: renderId, toPort: 'skizze' });
  return { graphId, renderId };
}

describe('Visbox · Befund F4: der gewünschte Name ist keine Anweisung', () => {
  it('der Demolauf: Bemerkung nur «gewünschter Name: Variante A» + Prompt → der Prompt geht als Anweisung, mit Qwen angezeigt', async () => {
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    const { graphId, renderId } = graph('Holzfassade im Abendlicht');
    sendeGraphRenderAuftrag(graphId, renderId, undefined, { backbone: 'qwen-image-2.1' });
    await vi.waitFor(() => expect(gesendet).not.toBeNull());
    const skizze = gesendet!['skizze'] as Record<string, unknown>;
    expect(skizze['name']).toBe('ipad/skizze-20261024-081200.png');
    expect(String(skizze['anweisung'])).toContain('Holzfassade im Abendlicht');
    expect(RenderScene.safeParse(gesendet).success).toBe(true);
    await vi.waitFor(() => expect(useVisRuntime.getState().laeufe[renderId]?.status).toBe('wartetFreigabe'));
    const lauf = useVisRuntime.getState().laeufe[renderId]!;
    expect(freigabeZeile(lauf.anweisung)).toContain('Anweisung: Prompt «');
    expect(bestelltesWerkzeugZusatz(undefined, lauf.backbone)).toBe('bestellt: Qwen-Image 2.1');
  });

  it('ohne Prompt: nichts gesendet, der Satz steht am Knoten', async () => {
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    const { graphId, renderId } = graph('');
    sendeGraphRenderAuftrag(graphId, renderId);
    await vi.waitFor(() => expect(useVisRuntime.getState().laeufe[renderId]?.status).toBe('fehler'));
    expect(useVisRuntime.getState().laeufe[renderId]?.fehler).toContain(SKIZZE_OHNE_BEMERKUNG_SATZ);
    expect(anzahl).toBe(0);
  });

  it('K-2: eine über Kosmo mitgegebene Grundlage geht mit Skizze nicht mit (Vertrag gültig)', async () => {
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    const { graphId, renderId } = graph('Abendlicht');
    sendeGraphRenderAuftrag(graphId, renderId, undefined, { grundlage: 'gl-0123456789abcdef', seed: 3 });
    await vi.waitFor(() => expect(gesendet).not.toBeNull());
    expect((gesendet!['vis'] as Record<string, unknown>)['grundlage']).toBeUndefined();
    expect(RenderScene.safeParse(gesendet).success).toBe(true);
  });

  it('die Karte sagt, dass danach am Render-Knoten «Freigeben» kommt', () => {
    expect(renderZeile({ kameraWahl: 'auto' })).toContain('nach «Anwenden» jetzt am Render-Knoten «Freigeben»');
  });
});
