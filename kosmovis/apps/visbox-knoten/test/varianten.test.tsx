// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, setzeModellGlb, VARIANTEN_TYP, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { startGraphAnlegen } from '../../kosmo-orbit/src/modules/vis/start-graph';
import { registriereHeimStandpunkte } from '../../kosmo-orbit/src/modules/vis/heim-standpunkte';
import {
  alleFreigeben,
  KI_SEKUNDEN_JE_BILD_ANNAHME,
  STARTWERTAUSWAHL_SEKUNDEN_JE_BILD_ANNAHME,
  ungefaehreDauer,
  useVariantenBestellung,
  variantenAuswahl,
  variantenZellen,
} from '../../kosmo-orbit/src/modules/vis/varianten';
import { huellboxAlsNetz } from '../src/mappe';
import { sendeGraphRenderAuftrag, zeitschaetzungSekunden } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { merkeGrundlage } from '../../kosmo-orbit/src/modules/vis/grundlage';

/**
 * VISBOX-EIGEN (L24 Bildweg Varianten, E246; Owner-Entscheide 92/92a/92b): «Varianten mit einem
 * Klick» mit dem glb der Mappe und den drei Richtungen des Heim-PCs. Die Probe aus KosmoOrbit
 * (`kv-varianten.test.tsx`) baut ihr Gebäude im Architekturkern und fragt die Werkzeugliste von
 * `@kosmo/ai` ab — beides gibt es in der Kopie nicht. Hier: Vorgabe 3 × Abend × 1, ein Auftrag je
 * Stimmung mit `cameras: 'auto'`, eine Freigabe für alle.
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

const gesendet: Record<string, unknown>[] = [];
const freigaben: string[] = [];

beforeEach(() => {
  gesendet.length = 0;
  freigaben.length = 0;
  localStorage.setItem('kosmo.bridge', `${location.origin}/bruecke`);
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, laeufe: {} });
  useVariantenBestellung.setState({ bestellungen: {} });
  setzeModellGlb(glb());
  const { doc } = useProject.getState();
  const geschoss = { id: 'st-probe', kind: 'storey', name: 'Mappe', index: 0, elevation: 0, height: 3000, cutHeight: 1100 };
  const huelle = { id: 'fm-probe', kind: 'freemesh', storeyId: geschoss.id, name: 'Hüllbox', ...huellboxAlsNetz([[0, 0, 0], [8, 5, 3]]) };
  doc.apply([
    { id: geschoss.id, before: null, after: geschoss as never },
    { id: huelle.id, before: null, after: huelle as never },
  ]);
  registriereHeimStandpunkte({
    standpunkte: ['Süd', 'Südost', 'Nordwest'].map((name, i) => ({
      kuerzel: ['s', 'sSE', 'nNW'][i]!, name, art: 'frontal', abstand_m: 20, auge: [0, 0, 1.6], blick_auf: [0, 0, 0], vollstaendig: true, begruendung: '',
    })),
    satz: 'Probe',
  });
  let n = 0;
  vi.stubGlobal('fetch', async (url: string, init?: RequestInit) => {
    const pfad = String(url);
    if (pfad.endsWith('/approve')) {
      freigaben.push(pfad.split('/').at(-2)!);
      return { ok: true, json: async () => ({ job_id: pfad.split('/').at(-2), status: 'queued', scene: 's.json', created_at: '2026-10-15T08:00:00Z', idle_window_only: true }) };
    }
    if (pfad.endsWith('/bruecke/jobs')) {
      gesendet.push(JSON.parse(String((init!.body as FormData).get('scene'))));
      const nr = ++n;
      return {
        ok: true,
        json: async () => ({ job_id: `vis-1790500000-a0000${nr}`, status: 'awaiting_approval', approval_token: `CONFIRMED_RENDER_${nr}`, scene: 's.json', created_at: '2026-10-15T08:00:00Z', idle_window_only: true }),
      };
    }
    return { ok: true, json: async () => ({}) };
  });
});

afterEach(() => {
  registriereHeimStandpunkte(null);
  setzeModellGlb(null);
  vi.unstubAllGlobals();
});

describe('Varianten mit einem Klick in Visbox', () => {
  it('Vorgabe: 3 Richtungen des Heim-PCs × Abend × aktuelles Modell = 3 Bilder', () => {
    const gid = startGraphAnlegen()!;
    const g = useProject.getState().doc.get<VisGraph>(gid)!;
    const a = variantenAuswahl(useProject.getState().doc, g, g.nodes.find((x) => x.typ === VARIANTEN_TYP)!);
    expect(a.heim).toEqual(['Süd', 'Südost', 'Nordwest']);
    expect(a.anzahl).toBe(3);
    expect(a.achsen.stimmungen).toEqual(['abend']);
  });

  it('2 Stimmungen: zwei Aufträge mit cameras «auto», eine Freigabe gibt beide frei', async () => {
    const gid = startGraphAnlegen()!;
    const v = useProject.getState().doc.get<VisGraph>(gid)!.nodes.find((x) => x.typ === VARIANTEN_TYP)!;
    useProject.getState().runCommand('vis.varianten', { nodeId: v.id, stimmungen: ['morgen', 'abend'] });
    await vi.waitFor(() => expect(gesendet).toHaveLength(2));
    expect(gesendet.map((s) => s['cameras'])).toEqual(['auto', 'auto']);
    await vi.waitFor(() =>
      expect(Object.values(useVisRuntime.getState().laeufe).filter((l) => l.status === 'wartetFreigabe')).toHaveLength(2),
    );
    expect(await alleFreigeben(v.id)).toBe(2);
    expect(freigaben.sort()).toEqual(['vis-1790500000-a00001', 'vis-1790500000-a00002']);
  });
});

/**
 * Generalprobe 327 (S3, 22.10.2026): Kamera Auto auf SO + NW umgestellt — der Varianten-Knoten nannte
 * weiter «Süd, Südost, Nordwest» (die Vorgabe des Heim-PCs), und im Raster stand für «Süd»
 * «fehlgeschlagen». Und die Frage der HomeStation: Schickt die Knotenansicht dieselbe Szene wie die
 * Brücke, obwohl am Render-Knoten «Himmel: keiner» steht?
 */
describe('Generalprobe 327: Kamera SO + NW und die Szene der Knotenansicht', () => {
  function stelleKameraUndStimmung(gid: string) {
    const { doc, runCommand } = useProject.getState();
    const g = doc.get<VisGraph>(gid)!;
    const kamera = g.nodes.find((x) => x.typ === 'kamera')!;
    const stimmung = g.nodes.find((x) => x.typ === 'stimmung')!;
    runCommand('vis.nodeParametrieren', { graphId: gid, nodeId: kamera.id, params: { art: 'auto', richtungen: JSON.stringify(['sSE', 'nNW']) } });
    runCommand('vis.nodeParametrieren', { graphId: gid, nodeId: stimmung.id, params: { presets: JSON.stringify(['abend']), preset: 'abend' } });
    return useProject.getState().doc.get<VisGraph>(gid)!;
  }

  it('der Varianten-Knoten nennt die Richtungen des Knotens «Kamera», nicht die drei der Vorgabe', () => {
    const gid = startGraphAnlegen()!;
    const g = stelleKameraUndStimmung(gid);
    const a = variantenAuswahl(useProject.getState().doc, g, g.nodes.find((x) => x.typ === VARIANTEN_TYP)!);
    expect(a.heim).toEqual(['Südost', 'Nordwest']);
    expect(a.zeilen).toEqual(['Südost', 'Nordwest']);
    expect(a.anzahl).toBe(2);
  });

  it('ohne Einstellung am Knoten «Kamera» bleibt es bei den drei des Heim-PCs', () => {
    const gid = startGraphAnlegen()!;
    const g = useProject.getState().doc.get<VisGraph>(gid)!;
    const a = variantenAuswahl(useProject.getState().doc, g, g.nodes.find((x) => x.typ === VARIANTEN_TYP)!);
    expect(a.heim).toEqual(['Süd', 'Südost', 'Nordwest']);
  });

  it('die zwei Bilder landen in den zwei Zeilen — keine Zeile «Süd», die fehlschlägt', async () => {
    const gid = startGraphAnlegen()!;
    const g = stelleKameraUndStimmung(gid);
    const v = g.nodes.find((x) => x.typ === VARIANTEN_TYP)!;
    useProject.getState().runCommand('vis.varianten', { nodeId: v.id });
    await vi.waitFor(() => expect(useVariantenBestellung.getState().bestellungen[v.id]).toBeDefined());
    const b = useVariantenBestellung.getState().bestellungen[v.id]!;
    expect(b.zeilen).toEqual(['Südost', 'Nordwest']);
    const laufId = b.gruppen[0]!.laufId;
    const lauf = { ...useVisRuntime.getState().laeufe[laufId]!, status: 'fertig' as const, bilder: ['sSE.png', 'nNW.png'] };
    const zellen = variantenZellen(b, { [laufId]: lauf });
    expect(zellen.map((z) => [z.standpunkt, z.zustand, z.bild])).toEqual([
      ['Südost', 'fertig', 'sSE.png'],
      ['Nordwest', 'fertig', 'nNW.png'],
    ]);
  });

  it('die Szene: Himmelsbild der Stimmung und die Richtungen gehen hinaus, «Himmel» des Render-Knotens und die Schalter nicht', async () => {
    const gid = startGraphAnlegen()!;
    const g = stelleKameraUndStimmung(gid);
    const v = g.nodes.find((x) => x.typ === VARIANTEN_TYP)!;
    useProject.getState().runCommand('vis.varianten', { nodeId: v.id });
    await vi.waitFor(() => expect(gesendet).toHaveLength(1));
    const szene = gesendet[0]! as {
      cameras: unknown;
      cameras_auto?: { richtungen: string[] };
      render: Record<string, unknown>;
      vis: Record<string, unknown>;
    };
    expect(szene.cameras).toBe('auto');
    expect(szene.cameras_auto?.richtungen).toEqual(['sSE', 'nNW']);
    expect(szene.render['environment']).toMatchObject({ preset: 'abend' });
    // «Himmel: keiner» am Render-Knoten ist `render.himmel` (Himmelsmodell in Blender) — seit 29.09.2026 nie gesendet.
    expect(szene.render).not.toHaveProperty('himmel');
    // Die drei Schalter setzt die Knotenansicht nicht: Es gilt die Vorgabe des Heim-PCs (Entscheid 126), wie bei der Brücke.
    for (const schalter of ['himmel_sichtbar', 'material_vorne', 'umriss_halten']) expect(szene.vis).not.toHaveProperty(schalter);
  });
});

describe('Gegenprobe 328 (S6/S7): Varianten auf der Grundlage des Render-Knotens', () => {
  function stelle(gid: string) {
    const { doc, runCommand } = useProject.getState();
    const g = doc.get<VisGraph>(gid)!;
    runCommand('vis.nodeParametrieren', { graphId: gid, nodeId: g.nodes.find((x) => x.typ === 'kamera')!.id, params: { art: 'auto', richtungen: JSON.stringify(['sSE', 'nNW']) } });
    runCommand('vis.nodeParametrieren', { graphId: gid, nodeId: g.nodes.find((x) => x.typ === 'stimmung')!.id, params: { presets: JSON.stringify(['abend']), preset: 'abend' } });
  }

  it('wie in 328: «Grundlage rendern», dann «2 Bilder bestellen» — die Bestellung nennt die Grundlage und EINEN Startwert', async () => {
    const gid = startGraphAnlegen()!;
    stelle(gid);
    const g = () => useProject.getState().doc.get<VisGraph>(gid)!;
    const render = g().nodes.find((x) => x.typ === 'render')!;
    sendeGraphRenderAuftrag(gid, render.id, undefined, { stufe: 'grundlage' });
    await vi.waitFor(() => expect(gesendet).toHaveLength(1));
    const stand = useVisRuntime.getState().laeufe[render.id]!.grundlageStand!;
    merkeGrundlage(gid, render.id, { id: 'gl-95fe4c6f18cc8061', wiederverwendet: false, kameras: 2, ebenen: ['schoenbild', 'tiefe', 'material-id'] }, stand);
    useProject.getState().runCommand('vis.varianten', { nodeId: g().nodes.find((x) => x.typ === VARIANTEN_TYP)!.id });
    await vi.waitFor(() => expect(gesendet).toHaveLength(2));
    const szene = gesendet[1]! as { cameras: unknown; vis: Record<string, unknown> };
    expect(szene.cameras).toBe('auto');
    expect(szene.vis['grundlage']).toBe('gl-95fe4c6f18cc8061');
    expect(szene.vis['seed']).toBe(368987247);
    expect(szene.vis).not.toHaveProperty('guete');
  });

  it('Material am Modell geändert (Variante B): keine passende Grundlage — die Bestellung rechnet ihre eigene wie bisher', async () => {
    const gid = startGraphAnlegen()!;
    stelle(gid);
    const g = () => useProject.getState().doc.get<VisGraph>(gid)!;
    const render = g().nodes.find((x) => x.typ === 'render')!;
    sendeGraphRenderAuftrag(gid, render.id, undefined, { stufe: 'grundlage' });
    await vi.waitFor(() => expect(gesendet).toHaveLength(1));
    merkeGrundlage(gid, render.id, { id: 'gl-95fe4c6f18cc8061', wiederverwendet: false, kameras: 2, ebenen: [] }, useVisRuntime.getState().laeufe[render.id]!.grundlageStand!);
    const { doc } = useProject.getState();
    const alt = doc.get('fm-probe') as unknown as { positions: number[] };
    doc.apply([{ id: 'fm-probe', before: alt as never, after: { ...alt, positions: alt.positions.map((p) => p + 1) } as never }]);
    useProject.getState().runCommand('vis.varianten', { nodeId: g().nodes.find((x) => x.typ === VARIANTEN_TYP)!.id });
    await vi.waitFor(() => expect(gesendet).toHaveLength(2));
    const szene = gesendet[1]! as { vis: Record<string, unknown> };
    expect(szene.vis).not.toHaveProperty('grundlage');
    expect(szene.vis).not.toHaveProperty('seed');
  });
});

describe('Gegenprobe 330 (B2): die Dauer am Varianten-Knoten folgt der Grundlage', () => {
  function stelle(gid: string) {
    const { doc, runCommand } = useProject.getState();
    const g = doc.get<VisGraph>(gid)!;
    runCommand('vis.nodeParametrieren', { graphId: gid, nodeId: g.nodes.find((x) => x.typ === 'kamera')!.id, params: { art: 'auto', richtungen: JSON.stringify(['sSE', 'nNW']) } });
    runCommand('vis.nodeParametrieren', { graphId: gid, nodeId: g.nodes.find((x) => x.typ === 'stimmung')!.id, params: { presets: JSON.stringify(['abend']), preset: 'abend' } });
  }
  const g = (gid: string) => useProject.getState().doc.get<VisGraph>(gid)!;
  const dauer = (gid: string) => {
    const a = variantenAuswahl(useProject.getState().doc, g(gid), g(gid).nodes.find((x) => x.typ === VARIANTEN_TYP)!);
    return ungefaehreDauer(a.anzahl, a.sekundenJeBild);
  };
  const voll = () => zeitschaetzungSekunden(128, [1600, 1000]) + KI_SEKUNDEN_JE_BILD_ANNAHME + STARTWERTAUSWAHL_SEKUNDEN_JE_BILD_ANNAHME;

  async function grundlage(gid: string) {
    const render = g(gid).nodes.find((x) => x.typ === 'render')!;
    sendeGraphRenderAuftrag(gid, render.id, undefined, { stufe: 'grundlage' });
    await vi.waitFor(() => expect(gesendet).toHaveLength(1));
    merkeGrundlage(gid, render.id, { id: 'gl-95fe4c6f18cc8061', wiederverwendet: false, kameras: 2, ebenen: [] }, useVisRuntime.getState().laeufe[render.id]!.grundlageStand!);
  }

  it('wie in 330: vor der Grundlage rund 200 s, nach «Grundlage rendern» nur der KI-Schritt — «ungefähr 1 min 34 s» statt «3 min 2 s» (gemessen 92 s)', async () => {
    const gid = startGraphAnlegen()!;
    stelle(gid);
    expect(voll()).toBe(100);
    expect(dauer(gid)).toBe('ungefähr 3 min 20 s');
    await grundlage(gid);
    expect(dauer(gid)).toBe('ungefähr 1 min 34 s');
    // Und die Bestellung tut, was die Zahl annimmt: sie nennt die Grundlage.
    useProject.getState().runCommand('vis.varianten', { nodeId: g(gid).nodes.find((x) => x.typ === VARIANTEN_TYP)!.id });
    await vi.waitFor(() => expect(gesendet).toHaveLength(2));
    expect((gesendet[1] as { vis: Record<string, unknown> }).vis['grundlage']).toBe('gl-95fe4c6f18cc8061');
  });

  it('Material geändert (Variante B in 330: 205 s): wieder die volle Schätzung — die Bestellung rechnet ihre eigene Grundlage', async () => {
    const gid = startGraphAnlegen()!;
    stelle(gid);
    await grundlage(gid);
    const { doc } = useProject.getState();
    const alt = doc.get('fm-probe') as unknown as { positions: number[] };
    doc.apply([{ id: 'fm-probe', before: alt as never, after: { ...alt, positions: alt.positions.map((p) => p + 1) } as never }]);
    expect(dauer(gid)).toBe('ungefähr 3 min 20 s');
  });
});
