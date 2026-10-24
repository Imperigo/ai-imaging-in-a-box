// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  evaluiereGraph,
  getCommand,
  History,
  KosmoDoc,
  UMFELD_SATZ_LIZENZ,
  umfeldAusParams,
  umfeldLadeMb,
  umfeldParams,
  VIS_NODE_KATALOG,
  VIS_UMFELD_KATALOG,
  type VisGraph,
} from '@kosmo/kernel';
import { RenderScene } from '@kosmo/contracts';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { UMFELD_KOERPER_H, UMFELD_ZEILE_H, umfeldListe } from '../src/modules/vis/UmfeldKnoten';
import { artVonBefehl, visWerkzeuge } from '../src/modules/vis/ki-werkzeuge';
import { grundlageStandFuerKnoten } from '../src/modules/vis/vis-jobs';

/**
 * Knoten «Umfeld» (Visbox-Owner-Wunsch 24.10.2026, Blatt 57): Bäume, Büsche, Wiese, Strasse und Autos
 * um das Haus — freie 3D-Modelle (nur CC0), geladen und gestellt am Heim-PC. Der Knoten bestellt nur den
 * Wunsch (`vis.umfeld`); er sitzt zwischen «Modell» und Render.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;

/** Senden braucht ein gezeichnetes Bauteil — nur mit dem Entwurf von KosmoOrbit (in Visbox sichtbar übersprungen). */
const MIT_ENTWURF = getCommand('design.wandZeichnen') !== undefined;

let container: HTMLDivElement | null = null;
let root: Root | null = null;
const q = (id: string): HTMLElement | null => document.body.querySelector(`[data-testid="${id}"]`);

beforeEach(() => {
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.unstubAllGlobals();
});

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
const graph = (gid: string) => useProject.getState().doc.get<VisGraph>(gid)!;
const knoten = (gid: string, id: string) => graph(gid).nodes.find((n) => n.id === id)!;
const klick = (el: Element | null) => act(() => (el as HTMLElement).click());

describe('Katalog und Wunsch', () => {
  it('der Knoten: Szene hinein, Szene mit Umfeld hinaus, ein Wandler', () => {
    const k = VIS_NODE_KATALOG['umfeld']!;
    expect(k.label).toBe('Umfeld');
    expect(k.kategorie).toBe('wandler');
    expect(k.inputs.map((p) => [p.name, p.typ])).toEqual([['szene', 'szene']]);
    expect(k.outputs.map((p) => [p.name, p.typ])).toEqual([['szene', 'szene']]);
  });

  it('jedes Stück im Katalog ist CC0 und hat eine Quelle', () => {
    for (const a of VIS_UMFELD_KATALOG) {
      expect(a.lizenz).toBe('CC0-1.0');
      expect(a.seite).toMatch(/^https:\/\//);
    }
  });

  it('Parameter → Wunsch: Reihenfolge fest, ohne Kategorie nichts, Anzahl nur für gewählte', () => {
    expect(umfeldAusParams({ kategorien: '["autos","baeume"]', dichte: 'viel', seed: 3 })).toEqual({ kategorien: ['baeume', 'autos'], dichte: 'viel', seed: 3 });
    expect(umfeldAusParams({ kategorien: '[]' })).toBeNull();
    expect(umfeldAusParams({ kategorien: 'kaputt' })).toBeNull();
    expect(umfeldAusParams({ kategorien: '["autos"]', anzahl: '{"autos":2,"baeume":4}' })).toEqual({
      kategorien: ['autos'],
      dichte: 'mittel',
      seed: 0,
      anzahl: { autos: 2 },
    });
    // Zwei Autos aus einem Paket zählen einmal.
    expect(umfeldLadeMb(umfeldAusParams({ kategorien: '["autos"]' }))).toBe(5);
  });
});

describe('Bestellung', () => {
  it('nur der Knoten direkt am Eingang «Szene» bestellt — ohne ihn bleibt der Auftrag wie bisher', () => {
    const { gid, setze } = graphMit();
    const modell = setze('modell');
    const render = setze('render');
    verbinde(gid, modell, 'szene', render, 'szene');
    expect(evaluiereGraph(useProject.getState().doc, graph(gid)).renderAuftraege.get(render)).not.toHaveProperty('umfeld');
    useProject.getState().runCommand('vis.umfeldSetzen', { graphId: gid, kategorien: ['baeume', 'autos'], anzahl: { autos: 2 } });
    const g = graph(gid);
    const umfeld = g.nodes.find((n) => n.typ === 'umfeld')!;
    expect(g.edges.some((e) => e.from === modell && e.to === umfeld.id && e.toPort === 'szene')).toBe(true);
    expect(g.edges.some((e) => e.from === umfeld.id && e.to === render && e.toPort === 'szene')).toBe(true);
    expect(g.edges.some((e) => e.from === modell && e.to === render)).toBe(false);
    const a = evaluiereGraph(useProject.getState().doc, g).renderAuftraege.get(render)!;
    expect(a.hatSzene).toBe(true);
    expect(a.umfeld).toEqual({ kategorien: ['baeume', 'autos'], dichte: 'mittel', seed: 0, anzahl: { autos: 2 } });
    // Ein zweiter Aufruf ändert den vorhandenen Knoten, er setzt keinen zweiten.
    useProject.getState().runCommand('vis.umfeldSetzen', { graphId: gid, kategorien: ['wiese'], dichte: 'viel' });
    expect(graph(gid).nodes.filter((n) => n.typ === 'umfeld')).toHaveLength(1);
    expect(evaluiereGraph(useProject.getState().doc, graph(gid)).renderAuftraege.get(render)!.umfeld).toEqual({ kategorien: ['wiese'], dichte: 'viel', seed: 0 });
  });

  it('ohne Szene am Render-Knoten sagt der Befehl, was fehlt', () => {
    const { gid, setze } = graphMit();
    setze('render');
    expect(() => useProject.getState().runCommand('vis.umfeldSetzen', { graphId: gid, kategorien: ['baeume'] })).toThrow(/keine Szene/);
  });

  it('eine ausgestattete und eine leere Grundlage sind zwei Stände', () => {
    const doc = useProject.getState().doc;
    const roh = { samples: 64, resolution: [1600, 1000] as const, sun: undefined, kameras: [] };
    const leer = grundlageStandFuerKnoten(doc, roh, {});
    const mit = grundlageStandFuerKnoten(doc, { ...roh, umfeld: { kategorien: ['baeume'], dichte: 'mittel', seed: 0 } }, {});
    expect(mit).not.toBe(leer);
    // Ohne Umfeld bleibt der Stand Zeichen für Zeichen der alte.
    expect(grundlageStandFuerKnoten(doc, { ...roh }, {})).toBe(leer);
  });

  it('Claude: «vis_umfeldSetzen» ist eine Änderung (Karte nur im Modus Karte), kein Rendern', () => {
    expect(artVonBefehl('vis.umfeldSetzen')).toBe('aendern');
    const w = visWerkzeuge().find((x) => x.name === 'vis_umfeldSetzen');
    expect(w).toBeDefined();
    expect(w!.description).toContain('CC0');
  });

  it.skipIf(!MIT_ENTWURF)('geht als vis.umfeld hinaus und besteht den Vertrag (braucht den Entwurf von KosmoOrbit)', async () => {
    vi.stubGlobal('localStorage', { getItem: (k: string) => (k === 'kosmo.bridge' ? 'http://localhost:8600' : null), setItem: () => undefined, removeItem: () => undefined });
    let roh: string | null = null;
    vi.stubGlobal('fetch', (async (_u: unknown, init?: RequestInit) => {
      roh = String((init!.body as FormData).get('scene'));
      return { ok: true, json: async () => ({ job_id: 'vis-1751400000-a1b2c3', status: 'queued', scene: 's.json', created_at: '2026-10-24T00:00:00Z', idle_window_only: true }) };
    }) as unknown as typeof fetch);
    const { runCommand } = useProject.getState();
    const eg = runCommand('design.geschossErstellen', { name: 'EG', index: 0, elevation: 0, height: 3000 });
    const aufbau = runCommand('design.aufbauErstellen', { name: 'AW', target: 'wall', layers: [{ material: 'beton', thickness: 250, function: 'tragend' }] });
    runCommand('design.wandZeichnen', { storeyId: (eg.patches[0] as { id: string }).id, a: { x: 0, y: 0 }, b: { x: 5000, y: 0 }, assemblyId: (aufbau.patches[0] as { id: string }).id });
    const { gid, setze } = graphMit();
    const modell = setze('modell');
    const prompt = setze('prompt', { text: 'Wohnhaus am Mittag' });
    const render = setze('render');
    verbinde(gid, modell, 'szene', render, 'szene');
    verbinde(gid, prompt, 'prompt', render, 'prompt');
    runCommand('vis.umfeldSetzen', { graphId: gid, kategorien: ['baeume', 'strasse', 'autos'], dichte: 'wenig', seed: 4 });
    const { sendeGraphRenderAuftrag } = await import('../src/modules/vis/vis-jobs');
    sendeGraphRenderAuftrag(gid, render, { preset: 'abend' });
    await vi.waitFor(() => expect(roh).not.toBeNull());
    const szene = JSON.parse(roh!) as { vis: Record<string, unknown> };
    expect(szene.vis['umfeld']).toEqual({ kategorien: ['baeume', 'strasse', 'autos'], dichte: 'wenig', seed: 4 });
    expect(RenderScene.safeParse(szene).success).toBe(true);
  });
});

describe('Der Körper (Blatt 57)', () => {
  it('fünf Kategorien, Dichte, Neu würfeln, Liste mit Quelle und CC0, der Satz zur Lizenz; feste Höhe', () => {
    const { gid, setze } = graphMit();
    const u = setze('umfeld');
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('umfeld')?.style.height).toBe(`${UMFELD_KOERPER_H}px`);
    expect(document.body.querySelectorAll('[data-testid="umfeld-wahl"] input[type="checkbox"]')).toHaveLength(5);
    // Vorgabe: Bäume, Büsche, Wiese.
    expect(umfeldAusParams(knoten(gid, u).params)?.kategorien).toEqual(['baeume', 'buesche', 'wiese']);
    act(() => (q('umfeld-autos') as HTMLInputElement).click());
    expect(knoten(gid, u).params['kategorien']).toBe('["baeume","buesche","wiese","autos"]');
    act(() => (q('umfeld-wiese') as HTMLInputElement).click());
    expect(knoten(gid, u).params['kategorien']).toBe('["baeume","buesche","autos"]');
    klick(q('umfeld-dichte-viel'));
    expect(knoten(gid, u).params['dichte']).toBe('viel');
    klick(q('umfeld-wuerfeln'));
    expect(knoten(gid, u).params['seed']).toBe(1);
    expect(q('umfeld-seed')?.textContent).toBe('Nr. 1');
    expect(q('umfeld-liste-autos')?.textContent).toContain('Kenney · CC0');
    expect(q('umfeld-liste-baeume')?.textContent).toContain('Poly Haven · CC0');
    expect(q('umfeld-laden')?.textContent).toMatch(/gemeinfrei \(CC0\)/);
    expect(q('umfeld-lizenz')?.textContent).toBe(UMFELD_SATZ_LIZENZ);
  });

  /**
   * Befund von Int 1 (24.10.2026): Zeilen abgeschnitten (bei Bäumen und Autos fehlte «CC0»), der Lizenzsatz
   * über dem Ladesatz. Hier der Aufbau, der es verhindert; gemessen im Browser in
   * `e2e/kv-umfeld-zeilen-ganz.spec.ts` (Zoom 1 und 0,5, grosse Schrift, lange Namen).
   */
  it('Aufbau: Modelle und «Quelle · CC0» als eigene Stücke, nichts gekappt, die Höhen passen in den Körper', () => {
    const { gid, setze } = graphMit();
    setze('umfeld', umfeldParams({ kategorien: ['baeume', 'buesche', 'wiese', 'strasse', 'autos'] }));
    montiere(<NodeCanvas graphId={gid} />);
    for (const k of ['baeume', 'buesche', 'wiese', 'strasse', 'autos']) {
      const zeile = q(`umfeld-liste-${k}`)!;
      expect(zeile.className).toBe('vis-kn-umfeld-zeile');
      // Die Hülle der Kurzhilfe ist ein Block (sonst inline-block: sie wächst mit dem Text über den Körper).
      expect(zeile.parentElement!.classList.contains('vis-kn-umfeld-huelle')).toBe(true);
      const herkunft = zeile.querySelector('[data-umfeld="herkunft"]')!;
      expect(herkunft.className).toBe('vis-kn-umfeld-herkunft');
      expect(herkunft.textContent).toMatch(/^(Poly Haven|Kenney|ambientCG|Quaternius)(, [A-Za-z ]+)* · CC0$/);
      expect(zeile.querySelector('[data-umfeld="modelle"]')!.textContent!.length).toBeGreaterThan(0);
    }
    // Die zwei Sätze: ohne Zeilenkappung (`vis-kn-zwei`) und in eigener Hülle untereinander.
    for (const id of ['umfeld-laden', 'umfeld-lizenz']) {
      expect(q(id)!.classList.contains('vis-kn-umfeld-satz')).toBe(true);
      expect(q(id)!.classList.contains('vis-kn-zwei')).toBe(false);
    }
    expect(q('umfeld-laden')!.parentElement!.classList.contains('vis-kn-umfeld-huelle')).toBe(true);
    // Feste Höhen in ganzen Textzeilen: Liste 5 × 2 Zeilen, Ladesatz 2, Lizenzsatz 4 — zusammen im Körper.
    const h = (id: string) => Number.parseFloat(q(id)!.style.height);
    expect(h('umfeld-liste')).toBeGreaterThanOrEqual(5 * 2 * UMFELD_ZEILE_H);
    expect(h('umfeld-laden')).toBe(2 * UMFELD_ZEILE_H);
    expect(h('umfeld-lizenz')).toBe(4 * UMFELD_ZEILE_H);
    expect(3 * 18 + 24 + 24 + h('umfeld-liste') + h('umfeld-laden') + h('umfeld-lizenz')).toBeLessThanOrEqual(UMFELD_KOERPER_H);
  });

  it('Regeln: Herkunft und Lizenz werden nie gekürzt, lange Modellnamen schon (voll in der Kurzhilfe)', () => {
    const css = readFileSync(resolve(__dirname, '../src/modules/vis/knoten-neu.css'), 'utf8');
    const regel = (sel: string) => {
      const i = css.indexOf(`${sel} {`);
      expect(i, sel).toBeGreaterThanOrEqual(0);
      return css.slice(i, css.indexOf('}', i));
    };
    expect(regel('.vis-kn-umfeld-huelle')).toMatch(/display: block/);
    const herkunft = regel('.vis-kn-umfeld-herkunft');
    expect(herkunft).toMatch(/flex: none/);
    expect(herkunft).toMatch(/white-space: nowrap/);
    expect(herkunft).not.toMatch(/text-overflow|overflow: hidden/);
    expect(regel('.vis-kn-umfeld-zeile')).toMatch(/flex-wrap: wrap/);
    expect(regel('.vis-kn-umfeld-zeile')).toMatch(new RegExp(`line-height: ${UMFELD_ZEILE_H}px`));
    expect(regel('.vis-kn-umfeld-modelle')).toMatch(/text-overflow: ellipsis/);
    const satz = regel('.vis-kn-umfeld-satz');
    expect(satz).toMatch(/white-space: normal/);
    expect(satz).not.toMatch(/line-clamp/);
    // Ein langer Name ändert die Herkunft nicht.
    const z = umfeldListe(umfeldParams({ kategorien: ['autos'] }))[0]!;
    expect(z.herkunft).toBe('Kenney · CC0');
    expect(z.text).toBe(`${z.modelle} — Kenney · CC0`);
  });

  it('ohne Kategorie bestellt der Knoten nichts und sagt es', () => {
    const { gid, setze } = graphMit();
    setze('umfeld', umfeldParams({ kategorien: [] }));
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('umfeld-liste')?.textContent).toContain('Nichts gewählt');
  });
});
