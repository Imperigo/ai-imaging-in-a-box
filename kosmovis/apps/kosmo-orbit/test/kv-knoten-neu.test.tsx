// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, getCommand, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { RenderScene } from '@kosmo/contracts';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { groessteNodeHoehe, NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { STIMMUNG_KOERPER_H } from '../src/modules/vis/StimmungKnoten';
import { einfrieren, gltfZuHeim, heimZuGltf, KAMERA_KOERPER_H } from '../src/modules/vis/KameraKnoten';
import { FARBPALETTE_KOERPER_H, MATERIAL_KOERPER_H, oberflaecheZeile } from '../src/modules/vis/OberflaecheKnoten';
import {
  registriereHeimStandpunkte,
  registriereStandpunkteAbfrage,
  standpunkteSuchteil,
  type HeimStandpunkte,
} from '../src/modules/vis/heim-standpunkte';
import { GRUNDLAGE_PARAM, GRUNDLAGEN_JE_STAND_PARAM, grundlageAmKnoten, grundlageFuerStand, mitGrundlageJeStand } from '../src/modules/vis/grundlage';
import { grundlagenNachfuehren, grundlageStandFuerKnoten } from '../src/modules/vis/vis-jobs';

/**
 * Bauplan «Neue Knoten» Schritte C, D, E (Blätter 31–33, Entscheide 109–113): die Körper der
 * Knoten Stimmung, Kamera, Oberfläche/Material/Farbpalette und was sie bestellen — gegen den
 * Vertrag (Vorschlag V) und in der Form der Fixtures auf `claude/kosmovis-knoten-fixtures`.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
if (!('setPointerCapture' in Element.prototype)) {
  Object.assign(Element.prototype, {
    setPointerCapture(): void {},
    releasePointerCapture(): void {},
    hasPointerCapture(): boolean {
      return false;
    },
  });
}

/**
 * Zwei Fälle brauchen ein gezeichnetes Bauteil (Wand) — das gibt es nur mit dem Entwurf von
 * KosmoOrbit. In der Visbox-Kopie (ohne `design.*`) werden sie SICHTBAR übersprungen, nicht still grün.
 */
const MIT_ENTWURF = getCommand('design.wandZeichnen') !== undefined;

let container: HTMLDivElement | null = null;
let root: Root | null = null;
const q = (id: string): HTMLElement | null => document.body.querySelector(`[data-testid="${id}"]`);

function frischesDokument(): void {
  const doc = new KosmoDoc();
  useProject.setState({ doc, history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
}

function montiere(el: React.ReactElement): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(el));
}

function graphMit(): { gid: string; setze: (typ: string, params?: Record<string, string | number | boolean>) => string } {
  const { runCommand } = useProject.getState();
  const gid = (runCommand('vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  let x = 40;
  const setze = (typ: string, params?: Record<string, string | number | boolean>) => {
    runCommand('vis.nodeSetzen', { graphId: gid, typ, x: (x += 300), y: 40, ...(params ? { params } : {}) });
    const g = useProject.getState().doc.get<VisGraph>(gid)!;
    return g.nodes[g.nodes.length - 1]!.id;
  };
  return { gid, setze };
}
const verbinde = (graphId: string, from: string, fromPort: string, to: string, toPort: string) =>
  useProject.getState().runCommand('vis.verbinden', { graphId, from, fromPort, to, toPort });
const knoten = (gid: string, id: string) => useProject.getState().doc.get<VisGraph>(gid)!.nodes.find((n) => n.id === id)!;
const klick = (el: Element | null) => act(() => (el as HTMLElement).click());

const HEIM: HeimStandpunkte = {
  standpunkte: [
    { kuerzel: 's', name: 'Süd', art: 'frontal', abstand_m: 30, auge: [0, -30, 1.7], blick_auf: [0, 0, 5.5], vollstaendig: true, begruendung: '' },
    { kuerzel: 'nNW', name: 'Nordwest', art: 'über Eck', abstand_m: 30, auge: [-20, 20, 1.7], blick_auf: [0, 0, 5.5], vollstaendig: true, begruendung: '' },
  ],
  satz: 'Rechnet der Heim-PC — Vorschau.',
};

beforeEach(() => frischesDokument());
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  registriereHeimStandpunkte(null);
  registriereStandpunkteAbfrage(null);
  vi.unstubAllGlobals();
});

describe('C · Stimmung', () => {
  it('acht Stimmungen, Mehrfachwahl, Himmelsbild 96 px, feste Höhe', () => {
    const { gid, setze } = graphMit();
    const st = setze('stimmung');
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('stimmung')?.style.height).toBe(`${STIMMUNG_KOERPER_H}px`);
    expect(q('stimmung-bild')?.style.height).toBe('96px');
    expect(document.body.querySelectorAll('[data-testid="stimmung-wahl"] input[type="checkbox"]')).toHaveLength(8);
    act(() => (q('stimmung-mittag') as HTMLInputElement).click());
    expect(knoten(gid, st).params['presets']).toBe('["morgen","mittag"]');
    // die letzte bleibt
    act(() => (q('stimmung-morgen') as HTMLInputElement).click());
    act(() => (q('stimmung-mittag') as HTMLInputElement).click());
    expect(knoten(gid, st).params['presets']).toBe('["mittag"]');
    expect(q('stimmung-render-zeile')?.textContent).toBe('Render: Mittag');
  });

  it('Himmel drehen und Wirkung schreiben Parameter', () => {
    const { gid, setze } = graphMit();
    const st = setze('stimmung');
    montiere(<NodeCanvas graphId={gid} />);
    act(() => (q('stimmung-drehen') as HTMLInputElement).click());
    expect(knoten(gid, st).params['drehung']).toBe(0);
    klick(q('stimmung-wirkung-licht'));
    expect(knoten(gid, st).params['wirkung']).toBe('licht');
  });

  it.skipIf(!MIT_ENTWURF)('Stimmung geht als render.environment hinaus — ohne Drehung ohne rotationGrad (Heim-PC: zur Kamera; braucht den Entwurf von KosmoOrbit)', async () => {
    vi.stubGlobal('localStorage', { getItem: (k: string) => (k === 'kosmo.bridge' ? 'http://localhost:8600' : null), setItem: () => undefined, removeItem: () => undefined });
    let roh: string | null = null;
    vi.stubGlobal('fetch', (async (_u: unknown, init?: RequestInit) => {
      roh = String((init!.body as FormData).get('scene'));
      return { ok: true, json: async () => ({ job_id: 'vis-1751400000-a1b2c3', status: 'queued', scene: 's.json', created_at: '2026-10-21T00:00:00Z', idle_window_only: true }) };
    }) as unknown as typeof fetch);
    const { runCommand } = useProject.getState();
    const eg = runCommand('design.geschossErstellen', { name: 'EG', index: 0, elevation: 0, height: 3000 });
    const aufbau = runCommand('design.aufbauErstellen', { name: 'AW', target: 'wall', layers: [{ material: 'beton', thickness: 250, function: 'tragend' }] });
    runCommand('design.wandZeichnen', { storeyId: (eg.patches[0] as { id: string }).id, a: { x: 0, y: 0 }, b: { x: 5000, y: 0 }, assemblyId: (aufbau.patches[0] as { id: string }).id });
    const { gid, setze } = graphMit();
    const st = setze('stimmung', { presets: '["blaue-stunde","winter"]', preset: 'blaue-stunde' });
    const modell = setze('modell');
    const kam = setze('kamera', { art: 'auto', richtungen: '["s","nNW"]', brennweite: 50, fuellt: 0.6, perspektive: 'senkrecht' });
    const mat = setze('materialTextur', { bibliothek: 'stampflehm', massstab: 2 });
    const pal = setze('farbpalette', { farben: '["#aa8866"]', leitfarbe: 0, staerke: 0.3 });
    const ober = setze('material');
    const komb = setze('kombinierer');
    const render = setze('render');
    verbinde(gid, st, 'prompt', komb, 'stimmung');
    verbinde(gid, pal, 'palette', mat, 'palette');
    verbinde(gid, mat, 'material', ober, 'boden');
    verbinde(gid, ober, 'material', komb, 'material');
    verbinde(gid, komb, 'prompt', render, 'prompt');
    verbinde(gid, modell, 'szene', render, 'szene');
    verbinde(gid, kam, 'kameras', render, 'kameras');
    const { sendeGraphRenderAuftrag } = await import('../src/modules/vis/vis-jobs');
    sendeGraphRenderAuftrag(gid, render, { preset: 'abend' });
    await vi.waitFor(() => expect(roh).not.toBeNull());
    const szene = JSON.parse(roh!) as Record<string, unknown>;
    const r = szene['render'] as Record<string, unknown>;
    // Der Knoten gewinnt vor der Insel (`environment`-Parameter).
    expect(r['environment']).toEqual({ preset: 'blaue-stunde' });
    expect(szene['cameras']).toBe('auto');
    expect(szene['cameras_auto']).toEqual({ richtungen: ['s', 'nNW'], brennweite_mm: 50, abstand: { art: 'auto', fuellt: 0.6 }, perspektive: 'senkrecht' });
    expect(r['materialien']).toEqual({ boden: { id: 'stampflehm', massstab_m: 2, toenung: { farbe: '#aa8866', staerke: 0.3 } } });
    expect(szene).not.toHaveProperty('interior');
    expect(RenderScene.safeParse(szene).success).toBe(true);
  });
});

describe('D · Kamera', () => {
  it('Auto: acht Richtungen, Brennweite, Abstand, Perspektive schreiben Parameter; feste Höhe', () => {
    const { gid, setze } = graphMit();
    const kam = setze('kamera');
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('kamera')?.getAttribute('data-art')).toBe('auto');
    expect(q('kamera')?.style.height).toBe(`${KAMERA_KOERPER_H}px`);
    expect(document.body.querySelectorAll('[data-testid="kamera-richtungen"] input[type="checkbox"]')).toHaveLength(8);
    act(() => (q('kamera-richtung-e') as HTMLInputElement).click());
    expect(knoten(gid, kam).params['art']).toBe('auto');
    expect(knoten(gid, kam).params['richtungen']).toBe('["e","sSE","s","nNW"]');
    klick(q('kamera-brennweite-24'));
    expect(knoten(gid, kam).params['brennweite']).toBe(24);
    klick(q('kamera-perspektive-frei'));
    expect(knoten(gid, kam).params['perspektive']).toBe('frei');
    klick(q('kamera-abstand-fest'));
    expect(knoten(gid, kam).params['abstandArt']).toBe('fest');
    expect(knoten(gid, kam).params['abstandM']).toBe(40);
    expect(q('kamera-blick')?.style.height).toBe('96px');
  });

  it('Live-Vorschau: die Wahl geht als Abfrage an den Wirt, die Antwort steht am Knoten', async () => {
    const gefragt: string[] = [];
    registriereStandpunkteAbfrage(async (w) => {
      gefragt.push(standpunkteSuchteil(w));
      return HEIM;
    });
    const { gid, setze } = graphMit();
    setze('kamera', { art: 'auto', richtungen: '["s","nNW"]', augenhoehe: 1.6 });
    montiere(<NodeCanvas graphId={gid} />);
    await vi.waitFor(() => expect(q('kamera-stand')?.textContent).toBe(HEIM.satz));
    expect(gefragt).toEqual(['richtungen=s%2CnNW&augenhoehe=1.6']);
    expect(q('kamera-blick')?.textContent).toBe('Süd');
    expect(q('kamera-manuell-uebernehmen')?.hasAttribute('disabled')).toBe(false);
  });

  it('Manuell übernehmen friert die Standpunkte ein; Werte tippen verschiebt sie; Bestellung als Liste mit Perspektive', async () => {
    registriereStandpunkteAbfrage(async () => HEIM);
    const { gid, setze } = graphMit();
    const kam = setze('kamera', { art: 'auto', richtungen: '["s","nNW"]' });
    const render = setze('render');
    verbinde(gid, kam, 'kameras', render, 'kameras');
    montiere(<NodeCanvas graphId={gid} />);
    await vi.waitFor(() => expect(q('kamera-manuell-uebernehmen')?.hasAttribute('disabled')).toBe(false));
    klick(q('kamera-manuell-uebernehmen'));
    const p = knoten(gid, kam).params;
    expect(p['art']).toBe('manuell');
    const kameras = JSON.parse(String(p['kameras'])) as { name: string; position: number[] }[];
    expect(kameras.map((k) => k.name)).toEqual(['Süd', 'Nordwest']);
    expect(kameras[0]!.position).toEqual(heimZuGltf([0, -30, 1.7]));
    const doc = useProject.getState().doc;
    const a = evaluiereGraph(doc, doc.get<VisGraph>(gid)!).renderAuftraege.get(render)!;
    expect(a.kameras?.map((k) => k.name)).toEqual(['Süd', 'Nordwest']);
    expect(a.kamerasPerspektive).toBe('senkrecht');
    expect(a.kamerasAuto).toBeUndefined();
  });

  it('Achsen: Heim-PC (Z oben) und glTF (Y oben) hin und zurück', () => {
    expect(gltfZuHeim(heimZuGltf([3, -30, 1.7]))).toEqual([3, -30, 1.7]);
    expect(einfrieren(HEIM.standpunkte, { richtungen: ['s'] })[0]!.fov).toBeCloseTo(54.432, 2);
  });

  it.skipIf(!MIT_ENTWURF)('ohne `art` und mit Standpunkten aus dem Modell (KosmoOrbit): wie bisher, Reiter «Modell» (braucht den Entwurf von KosmoOrbit)', () => {
    const { runCommand } = useProject.getState();
    const eg = runCommand('design.geschossErstellen', { name: 'EG', index: 0, elevation: 0, height: 3000 });
    const aufbau = runCommand('design.aufbauErstellen', { name: 'AW', target: 'wall', layers: [{ material: 'beton', thickness: 250, function: 'tragend' }] });
    runCommand('design.wandZeichnen', { storeyId: (eg.patches[0] as { id: string }).id, a: { x: 0, y: 0 }, b: { x: 5000, y: 0 }, assemblyId: (aufbau.patches[0] as { id: string }).id });
    const { gid, setze } = graphMit();
    // Gespeicherter Knoten ohne `art` (vor dem 21.10.2026): bleibt «Modell», nichts wird still umgestellt.
    const alt = setze('kamera');
    const { runCommand: rc, doc: d } = useProject.getState();
    const g = d.get<VisGraph>(gid)!;
    d.apply([{ id: gid, before: g, after: { ...g, nodes: g.nodes.map((n) => (n.id === alt ? { ...n, params: {} } : n)) } }]);
    void rc;
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('kamera')?.getAttribute('data-art')).toBe('modell');
    expect(q('kamera-art-modell')).not.toBeNull();
    expect(q('vis-auto-kamera-liste')?.textContent).toContain('Eingang');
  });
});

describe('E · Oberfläche, Material, Farbpalette', () => {
  it('Material: Bibliothek, Vorschau 96 px als Kugel/Würfel/Fläche, Massstab, feste Höhe', () => {
    const { gid, setze } = graphMit();
    const mat = setze('materialTextur');
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('material-textur')?.style.height).toBe(`${MATERIAL_KOERPER_H}px`);
    expect(q('material-vorschau')?.style.width).toBe('96px');
    expect(q('material-vorschau')?.getAttribute('data-form')).toBe('kugel');
    klick(q('material-vorschau-wuerfel'));
    expect(knoten(gid, mat).params['vorschau']).toBe('wuerfel');
    klick(q('material-bibliothek'));
    const popup = q('material-bibliothek-popup');
    expect(popup?.querySelectorAll('[role="option"]')).toHaveLength(11);
    klick(popup!.querySelector('[data-value="klinker"]'));
    expect(knoten(gid, mat).params['bibliothek']).toBe('klinker');
  });

  it('Farbpalette: Leitfarbe und Satz', () => {
    const { gid, setze } = graphMit();
    const pal = setze('farbpalette');
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('farbpalette')?.style.height).toBe(`${FARBPALETTE_KOERPER_H}px`);
    klick(q('farbpalette-leit-2'));
    expect(knoten(gid, pal).params['leitfarbe']).toBe(2);
    expect(q('farbpalette-satz')?.textContent).toMatch(/^Farbpalette: /);
  });

  it('Oberfläche: die Zuordnung je Bauteil-Art, ohne Material «aus dem Modell»', () => {
    const { gid, setze } = graphMit();
    const ober = setze('material');
    const mat = setze('materialTextur', { bibliothek: 'sichtbeton-sandgestrahlt' });
    verbinde(gid, mat, 'material', ober, 'fassade');
    const g = useProject.getState().doc.get<VisGraph>(gid)!;
    const z = oberflaecheZeile(g, ober);
    expect(z.kurz).toBe('Fassade: Sichtbeton, sandgestrahlt');
    expect(z.voll).toContain('Dach: aus dem Modell');
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('oberflaeche-zuordnung')?.textContent).toBe('Fassade: Sichtbeton, sandgestrahlt');
  });

  it('kein Knoten ist höher als 600 px (das kleinste gemessene Feld, kv-b5)', () => {
    for (const typ of ['stimmung', 'kamera', 'material', 'materialTextur', 'farbpalette']) {
      expect(groessteNodeHoehe(typ), typ).toBeLessThanOrEqual(600);
    }
  });
});

describe('Grundlage je Stand', () => {
  it('eine gemerkte Grundlage desselben Stands wird wieder die gezeigte', () => {
    const p0 = { [GRUNDLAGE_PARAM.id]: 'gl-0000000000000001', [GRUNDLAGE_PARAM.stand]: 'A' };
    const nurA = mitGrundlageJeStand({}, 'A', { id: 'gl-0000000000000001', seed: 1, kameras: 3, ebenen: [] });
    const map = mitGrundlageJeStand({ [GRUNDLAGEN_JE_STAND_PARAM]: nurA }, 'B', { id: 'gl-0000000000000002', seed: 2, kameras: 3, ebenen: ['tiefe'] });
    const params = { ...p0, [GRUNDLAGEN_JE_STAND_PARAM]: map };
    expect(grundlageFuerStand(params, 'A')).toBeNull();
    expect(grundlageFuerStand(params, 'B')?.[GRUNDLAGE_PARAM.id]).toBe('gl-0000000000000002');
    expect(grundlageAmKnoten(params, 'B')?.id).toBe('gl-0000000000000002');
    expect(grundlageAmKnoten(params, 'C')?.id).toBe('gl-0000000000000001');
  });

  it('die Stimmung zurückwechseln holt die Grundlage dieses Stands an den Render-Knoten zurück', () => {
    const { gid, setze } = graphMit();
    const st = setze('stimmung', { presets: '["abend"]', preset: 'abend' });
    const render = setze('render');
    verbinde(gid, st, 'prompt', render, 'prompt');
    const standJetzt = () => {
      const doc = useProject.getState().doc;
      const roh = evaluiereGraph(doc, doc.get<VisGraph>(gid)!).renderAuftraege.get(render)!;
      return grundlageStandFuerKnoten(doc, roh, knoten(gid, render).params);
    };
    const standAbend = standJetzt();
    const { runCommand } = useProject.getState();
    runCommand('vis.nodeParametrieren', {
      graphId: gid,
      nodeId: render,
      params: {
        [GRUNDLAGE_PARAM.id]: 'gl-00000000000000ab',
        [GRUNDLAGE_PARAM.stand]: standAbend,
        [GRUNDLAGEN_JE_STAND_PARAM]: mitGrundlageJeStand({}, standAbend, { id: 'gl-00000000000000ab', seed: 7, kameras: 3, ebenen: [] }),
      },
    });
    runCommand('vis.nodeParametrieren', { graphId: gid, nodeId: st, params: { presets: '["nebel"]', preset: 'nebel' } });
    expect(standJetzt()).not.toBe(standAbend);
    runCommand('vis.nodeParametrieren', { graphId: gid, nodeId: render, params: { [GRUNDLAGE_PARAM.id]: 'gl-00000000000000cd', [GRUNDLAGE_PARAM.stand]: standJetzt() } });
    runCommand('vis.nodeParametrieren', { graphId: gid, nodeId: st, params: { presets: '["abend"]', preset: 'abend' } });
    expect(grundlagenNachfuehren(gid)).toBe(1);
    expect(knoten(gid, render).params[GRUNDLAGE_PARAM.id]).toBe('gl-00000000000000ab');
    expect(knoten(gid, render).params[GRUNDLAGE_PARAM.stand]).toBe(standAbend);
  });
});
