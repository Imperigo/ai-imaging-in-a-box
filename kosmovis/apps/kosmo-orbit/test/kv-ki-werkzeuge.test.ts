// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { allCommands, execute, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { setzeVerlaufWache, useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import {
  abonniere,
  ablehnen,
  anwenden,
  behandle,
  brauchtKarte,
  GRAPH_LESEN,
  kiSchnittstelle,
  kiSchritte,
  kiVerlaufWache,
  letzterKiSchritt,
  rueckgaengigKi,
  verwirfVorschlaege,
  leereKiZustand,
  offeneVorschlaege,
  VIS_BEFEHL_ART,
  PAKET_HINWEIS,
  VIS_PAKET,
  visWerkzeuge,
  type GraphLesenDaten,
  type KiEreignis,
  type KiModus,
  type KiWerkzeugArt,
} from '../src/modules/vis/ki-werkzeuge';

/**
 * Visbox Plan «KI-Bedienung» Stufe 1 (20.10.2026, Entscheide 105–106f, 108): der gemeinsame
 * KI-Werkzeugsatz der Knotenansicht. Geprueft wird die Spielregel, die Claude ueber MCP und der
 * Assistent gleich bekommen: Lesen aendert nichts, ein Vorschlag aendert nichts, Anwenden ist
 * genau EIN Rueckgaengig, die Antwort nennt die neue nodeId, das Paket loest «$neu:N» auf,
 * Loeschen und Rendern sind in jedem Modus eine Karte, und die GPU-Freigabe ist kein Werkzeug.
 */

let graphId = '';
let modellId = '';
let renderId = '';

function graph(): VisGraph {
  return useProject.getState().doc.get<VisGraph>(graphId)!;
}

function stand(): string {
  return JSON.stringify(useProject.getState().doc.toJSON());
}

beforeEach(() => {
  leereKiZustand();
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0, params: { guete: 'voll' } });
  const g = doc.get<VisGraph>(graphId)!;
  modellId = g.nodes[0]!.id;
  renderId = g.nodes[1]!.id;
  execute(doc, 'vis.verbinden', { graphId, from: modellId, fromPort: 'szene', to: renderId, toPort: 'szene' });
  useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
});

afterEach(() => {
  leereKiZustand();
  setzeVerlaufWache(null);
});

describe('Werkzeugliste', () => {
  it('enthaelt graph_lesen, jeden vis.*-Befehl und vis_paket — sonst nichts', () => {
    const namen = visWerkzeuge().map((w) => w.name);
    const vis = allCommands().filter((c) => c.id.startsWith('vis.') && !c.kiVerborgen).map((c) => c.id.replace(/\./g, '_'));
    expect(namen).toEqual([GRAPH_LESEN, ...vis, VIS_PAKET]);
    expect(namen).toContain('vis_nodeLoeschen');
    expect(namen).toContain('vis_graphLoeschen');
    expect(namen.filter((n) => !n.startsWith('vis_') && n !== GRAPH_LESEN)).toEqual([]);
  });

  it('jeder vis.*-Befehl ist ausdruecklich eingeteilt', () => {
    const ohne = allCommands().filter((c) => c.id.startsWith('vis.') && !(c.id in VIS_BEFEHL_ART)).map((c) => c.id);
    expect(ohne).toEqual([]);
  });

  it('Einteilung: lesen | aendern | loeschen | rendern', () => {
    const art = Object.fromEntries(visWerkzeuge().map((w) => [w.name, w.art]));
    expect(art[GRAPH_LESEN]).toBe('lesen');
    expect(art['vis_nodeSetzen']).toBe('aendern');
    expect(art['vis_verbinden']).toBe('aendern');
    expect(art['vis_nodeLoeschen']).toBe('loeschen');
    expect(art['vis_graphLoeschen']).toBe('loeschen');
    expect(art['vis_render']).toBe('rendern');
  });

  it('Namen und Schemas passen zum MCP-Kern und zur Claude-API', () => {
    for (const w of visWerkzeuge()) {
      expect(w.name).toMatch(/^[A-Za-z0-9_-]{1,64}$/);
      expect(w.inputSchema['type']).toBe('object');
      const text = JSON.stringify(w.inputSchema);
      expect(text).not.toContain('$schema');
      expect(text).not.toContain('additionalItems');
      expect(text).not.toContain(String(Number.MAX_SAFE_INTEGER));
    }
    const render = visWerkzeuge().find((w) => w.name === 'vis_render')!;
    const aufl = (render.inputSchema['properties'] as Record<string, Record<string, unknown>>)['aufloesung']!;
    expect(Array.isArray(aufl['items'])).toBe(false);
    expect(aufl['minItems']).toBe(2);
    expect(aufl['maxItems']).toBe(2);
  });

  it('Setzen und Verbinden nennen den Paketweg mit «$neu:0» (Visbox-Messung 319)', () => {
    const w = visWerkzeuge();
    for (const name of ['vis_nodeSetzen', 'vis_verbinden']) {
      const d = w.find((x) => x.name === name)!.description;
      expect(d).toContain('vis_paket');
      expect(d).toContain('$neu:0');
      expect(d.endsWith(PAKET_HINWEIS)).toBe(true);
    }
    expect(w.filter((x) => x.description.includes(PAKET_HINWEIS)).map((x) => x.name).sort())
      .toEqual(['vis_nodeSetzen', 'vis_verbinden']);
  });

  it('kein Werkzeug gibt die Grafikkarte frei', () => {
    const w = visWerkzeuge();
    expect(w.filter((x) => /freig|approv|confirm|gpu|bestaetig/i.test(x.name))).toEqual([]);
    expect(w.find((x) => x.name === 'vis_render')!.description).toMatch(/kein Werkzeug/);
    const schnitt = kiSchnittstelle();
    expect(Object.keys(schnitt).filter((k) => /freig|approv/i.test(k))).toEqual([]);
  });
});

describe('Spielregel wie Mcpfreigabe (Swift)', () => {
  it('Lesen nie, Loeschen und Rendern immer, Aendern nur im Modus Karte', () => {
    const tafel: Record<KiWerkzeugArt, Record<KiModus, boolean>> = {
      lesen: { karte: false, coop: false, voll: false },
      aendern: { karte: true, coop: false, voll: false },
      loeschen: { karte: true, coop: true, voll: true },
      rendern: { karte: true, coop: true, voll: true },
    };
    for (const [art, zeile] of Object.entries(tafel)) {
      for (const [modus, soll] of Object.entries(zeile)) expect(brauchtKarte(art as KiWerkzeugArt, modus as KiModus)).toBe(soll);
    }
  });
});

describe('graph_lesen', () => {
  it('liefert Knoten mit nodeId, Typ, Label, Ports, Parametern, Kanten, Lauf, Grundlage und Guete', () => {
    useVisRuntime.getState().setzeLauf(renderId, { status: 'fertig', jobId: 'job-1', bild: 'data:x', memoKey: 'm', stufe: 'variante', seed: 7, guete: 'voll' });
    const a = behandle({ kennung: 'L-1', werkzeug: GRAPH_LESEN, argumente: { katalog: true } }, 'voll');
    if (!('sofort' in a)) throw new Error('lesen braucht keine Karte');
    expect(a.sofort.ok).toBe(true);
    const d = a.sofort.daten as GraphLesenDaten;
    expect(JSON.parse(a.sofort.text)).toEqual(JSON.parse(JSON.stringify(d)));
    expect(d.graphen).toHaveLength(1);
    const g = d.graphen[0]!;
    expect(g).toMatchObject({ graphId, name: 'Probe', gezeigt: true });
    expect(g.kanten).toHaveLength(1);
    const kante = g.kanten[0]!;
    const r = g.knoten.find((k) => k.nodeId === renderId)!;
    expect(r).toMatchObject({ typ: 'render', label: 'Render', x: 300, y: 0, eingeklappt: false, guete: 'voll', grundlage: null });
    expect(r.parameter).toEqual({ guete: 'voll' });
    expect(r.eingaenge.find((p) => p.name === 'szene')!.kante).toEqual({ edgeId: kante.edgeId, von: modellId, port: 'szene' });
    expect(r.eingaenge.find((p) => p.name === 'skizze')!.nurVon).toEqual(['skizzeIpad']);
    expect(r.lauf).toEqual({ status: 'fertig', jobId: 'job-1', stufe: 'variante', seed: 7, guete: 'voll', laufNummer: 1, mitBild: true });
    const m = g.knoten.find((k) => k.nodeId === modellId)!;
    expect(m.ausgaenge[0]!.kanten).toEqual([{ edgeId: kante.edgeId, nach: renderId, port: 'szene' }]);
    expect(m.lauf).toBeNull();
    expect('guete' in m).toBe(false);
    expect(d.renderAuftrag).toBeNull();
    expect(d.katalog!.some((t) => t.typ === 'render')).toBe(true);
  });

  it('lesen aendert nichts — Dokument, Rueckgaengig, Revision', () => {
    const vorher = stand();
    const tiefe = useProject.getState().history.depth;
    behandle({ kennung: 'L-2', werkzeug: GRAPH_LESEN }, 'karte');
    expect(stand()).toBe(vorher);
    expect(useProject.getState().history.depth).toBe(tiefe);
    expect(useProject.getState().revision).toBe(0);
    expect(offeneVorschlaege()).toEqual([]);
  });
});

describe('Vorschlag, Anwenden, Ablehnen', () => {
  it('ein Vorschlag aendert nichts', () => {
    const vorher = stand();
    const tiefe = useProject.getState().history.depth;
    const a = behandle({ kennung: 'K-1', werkzeug: 'vis_nodeSetzen', argumente: { graphId, typ: 'prompt', x: 0, y: 200 } }, 'karte');
    expect('karte' in a).toBe(true);
    expect(stand()).toBe(vorher);
    expect(useProject.getState().history.depth).toBe(tiefe);
    expect(offeneVorschlaege().map((v) => v.kennung)).toEqual(['K-1']);
    // Dieselbe Kennung noch einmal (Neuverbinden): keine zweite Karte.
    behandle({ kennung: 'K-1', werkzeug: 'vis_nodeSetzen', argumente: { graphId, typ: 'prompt', x: 0, y: 200 } }, 'karte');
    expect(offeneVorschlaege()).toHaveLength(1);
  });

  it('Anwenden ist genau EINE Rueckgaengig-Gruppe und nennt die NEUE nodeId', () => {
    behandle({ kennung: 'K-2', werkzeug: 'vis_nodeSetzen', argumente: { graphId, typ: 'prompt', x: 0, y: 200, params: { text: 'Sichtbeton' } } }, 'karte');
    const tiefe = useProject.getState().history.depth;
    const e = anwenden('K-2')!;
    expect(e.ok).toBe(true);
    expect(useProject.getState().history.depth).toBe(tiefe + 1);
    const neu = graph().nodes.find((n) => n.typ === 'prompt')!;
    expect(e.text).toContain(`NEUE nodeId «${neu.id}» (prompt)`);
    expect((e.daten as { neu: { knoten: unknown[] } }).neu.knoten).toEqual([{ nodeId: neu.id, typ: 'prompt', graphId }]);
    expect(useProject.getState().journal.at(-1)!.actor).toBe('kosmo');
    expect(offeneVorschlaege()).toEqual([]);
    useProject.getState().undo();
    expect(graph().nodes.some((n) => n.typ === 'prompt')).toBe(false);
    expect(anwenden('K-2')).toBeNull();
  });

  it('Ablehnen aendert nichts', () => {
    const vorher = stand();
    behandle({ kennung: 'K-3', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 50, y: 50 } }, 'karte');
    const e = ablehnen('K-3')!;
    expect(e.ok).toBe(false);
    expect(e.text).toMatch(/^ABGELEHNT/);
    expect(stand()).toBe(vorher);
  });

  it('ein ungueltiger Aufruf wird sofort FEHLER, ohne Karte und ohne Aenderung', () => {
    const vorher = stand();
    const a = behandle({ kennung: 'K-4', werkzeug: 'vis_nodeParametrieren', argumente: { graphId, nodeId: 'node_gibtsnicht', params: { x: 1 } } }, 'voll');
    expect('sofort' in a && a.sofort.ok).toBe(false);
    expect('sofort' in a && a.sofort.text).toMatch(/^FEHLER: .*existiert nicht.*nichts wurde vorgeschlagen/);
    const b = behandle({ kennung: 'K-5', werkzeug: 'design_wandZeichnen', argumente: {} }, 'voll');
    expect('sofort' in b && b.sofort.text).toMatch(/Unbekanntes Werkzeug/);
    expect(stand()).toBe(vorher);
    expect(offeneVorschlaege()).toEqual([]);
  });

  it('Coop und Voll: Aendern laeuft sofort, mit Urheber Claude, im KI-Verlauf statt in der Kette des Architekten (114)', () => {
    for (const modus of ['coop', 'voll'] as const) {
      const tiefe = useProject.getState().history.depth;
      const a = behandle({ kennung: `C-${modus}`, werkzeug: 'vis_nodeKollabieren', argumente: { graphId, nodeId: modellId, collapsed: modus === 'coop' } }, modus);
      if (!('sofort' in a)) throw new Error('Aendern im Coop braucht keine Karte');
      expect(a.sofort.ok).toBe(true);
      expect(a.sofort.text).toMatch(/^ANGEWENDET/);
      expect(a.sofort.text).toContain('«Claudes letzten Schritt zurücknehmen»');
      expect(useProject.getState().history.depth).toBe(tiefe);
      expect(useProject.getState().journal.at(-1)!.actor).toBe('claude');
      expect(letzterKiSchritt('claude')!.kennung).toBe(`C-${modus}`);
    }
    expect(kiSchritte()).toHaveLength(2);
  });
});

describe('Zwei Rueckgaengig-Verlaeufe (Entscheid 114)', () => {
  it('Strg+Z nimmt nur die eigenen Schritte zurueck; «Claudes letzten Schritt» nimmt Claudes zurueck', () => {
    setzeVerlaufWache(kiVerlaufWache);
    // Ein eigener Schritt des Architekten (Strg+Z-faehig) …
    useProject.getState().runCommand('vis.nodeSchieben', { graphId, nodeId: renderId, x: 400, y: 50 });
    // … dann Claude im Coop an einem anderen Knoten.
    behandle({ kennung: 'Z-1', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 77, y: 77 } }, 'coop');
    const knoten = (id: string) => graph().nodes.find((n) => n.id === id)!;
    expect(knoten(modellId)).toMatchObject({ x: 77, y: 77 });
    // Strg+Z: Der Graph ist EIN Teil — Claude hat danach daran gearbeitet, also gesperrt, nichts geaendert.
    expect(useProject.getState().undo()).toBe(false);
    expect(knoten(renderId)).toMatchObject({ x: 400, y: 50 });
    expect(knoten(modellId)).toMatchObject({ x: 77, y: 77 });
    // Claudes Schritt in der Leiste zuruecknehmen: nur er, als Schritt des Architekten.
    const tiefe = useProject.getState().history.depth;
    const r = rueckgaengigKi('claude');
    expect(r).toMatchObject({ ok: true, kennung: 'Z-1' });
    expect(r.satz).toMatch(/^Zurückgenommen: /);
    expect(knoten(modellId)).toMatchObject({ x: 0, y: 0 });
    expect(knoten(renderId)).toMatchObject({ x: 400, y: 50 });
    expect(useProject.getState().history.depth).toBe(tiefe + 1);
    expect(kiSchritte()).toEqual([]);
    expect(rueckgaengigKi('claude')).toMatchObject({ ok: false, kennung: null });
    // Die Ruecknahme selbst ist ein Schritt des Architekten: Strg+Z stellt Claudes Stand wieder her.
    useProject.getState().undo();
    expect(knoten(modellId)).toMatchObject({ x: 77, y: 77 });
  });

  it('ohne KI-Schritt laeuft Strg+Z wie immer', () => {
    setzeVerlaufWache(kiVerlaufWache);
    useProject.getState().runCommand('vis.nodeSchieben', { graphId, nodeId: renderId, x: 1, y: 2 });
    expect(useProject.getState().undo()).toBe(true);
    expect(graph().nodes.find((n) => n.id === renderId)).toMatchObject({ x: 300, y: 0 });
  });

  it('hat der Architekt seither daran gearbeitet, aendert die Ruecknahme nichts und sagt es', () => {
    behandle({ kennung: 'Z-2', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 5, y: 5 } }, 'voll');
    useProject.getState().runCommand('vis.nodeSchieben', { graphId, nodeId: modellId, x: 9, y: 9 });
    const vorher = stand();
    const r = rueckgaengigKi('claude');
    expect(r.ok).toBe(false);
    expect(r.satz).toMatch(/lässt sich nicht zurücknehmen: an Render-Graph «Probe» wurde seither weitergearbeitet/);
    expect(stand()).toBe(vorher);
  });

  it('eine angewendete Karte ist ein Schritt des Architekten, kein KI-Schritt', () => {
    behandle({ kennung: 'Z-3', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 3, y: 3 } }, 'karte');
    const tiefe = useProject.getState().history.depth;
    anwenden('Z-3');
    expect(useProject.getState().history.depth).toBe(tiefe + 1);
    expect(kiSchritte()).toEqual([]);
  });

  it('Ereignis «kiverlauf» je Aenderung; ein Mappenwechsel (verwirf) leert den KI-Verlauf', () => {
    const ereignisse: KiEreignis[] = [];
    const ab = abonniere((e) => ereignisse.push(e));
    behandle({ kennung: 'Z-4', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 4, y: 4 } }, 'coop');
    const v = ereignisse.find((e) => e.art === 'kiverlauf');
    expect(v).toEqual({ art: 'kiverlauf', anzahl: 1, letzter: { claude: { kennung: 'Z-4', urheber: 'claude', zusammenfassung: expect.any(String) }, assistent: null } });
    expect(kiSchnittstelle().kiVerlauf().letzter.claude!.kennung).toBe('Z-4');
    verwirfVorschlaege('Mappe gewechselt');
    expect(kiSchritte()).toEqual([]);
    expect(ereignisse.at(-1)).toEqual({ art: 'kiverlauf', anzahl: 0, letzter: { claude: null, assistent: null } });
    ab();
  });
});

describe('Loeschen und Rendern', () => {
  it('Loeschen ist IMMER eine Karte, auch im Modus Voll', () => {
    for (const modus of ['karte', 'coop', 'voll'] as const) {
      const vorher = stand();
      const a = behandle({ kennung: `D-${modus}`, werkzeug: 'vis_nodeLoeschen', argumente: { graphId, nodeId: modellId } }, modus);
      expect('karte' in a).toBe(true);
      const b = behandle({ kennung: `G-${modus}`, werkzeug: 'vis_graphLoeschen', argumente: { graphId } }, modus);
      expect('karte' in b).toBe(true);
      expect(stand()).toBe(vorher);
    }
  });

  it('Rendern ist IMMER eine Karte und stellt nach Anwenden nur den Auftrag ins Dokument', () => {
    const vorher = stand();
    const a = behandle({ kennung: 'R-1', werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'vorschau' } }, 'voll');
    expect('karte' in a).toBe(true);
    expect('karte' in a && a.karte.art).toBe('rendern');
    expect(stand()).toBe(vorher);
    const e = anwenden('R-1')!;
    expect(e.ok).toBe(true);
    expect(useProject.getState().doc.settings.visRenderAuftrag).toMatchObject({ graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'vorschau' });
    // Kein Lauf, keine Freigabe: die Laufzeit startet erst die App, die Grafikkarte erst der Mensch.
    expect(useVisRuntime.getState().laeufe).toEqual({});
  });

  it('ein Paket mit Loeschen oder Rendern ist in jedem Modus eine Karte', () => {
    const a = behandle(
      {
        kennung: 'P-L',
        werkzeug: VIS_PAKET,
        argumente: { schritte: [{ befehl: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 1, y: 1 } }, { befehl: 'vis_nodeLoeschen', argumente: { graphId, nodeId: renderId } }] },
      },
      'voll',
    );
    expect('karte' in a && a.karte.art).toBe('loeschen');
  });
});

describe('vis_paket', () => {
  it('bis 40 Schritte mit «$neu:N» → eine Karte, ein Rueckgaengig', () => {
    const vorher = stand();
    const a = behandle(
      {
        kennung: 'P-1',
        werkzeug: VIS_PAKET,
        argumente: {
          schritte: [
            { befehl: 'vis_graphErstellen', argumente: { name: 'Zweiter' } },
            { befehl: 'vis_nodeSetzen', argumente: { graphId: '$neu:0', typ: 'modell', x: 0, y: 0 } },
            { befehl: 'vis_nodeSetzen', argumente: { graphId: '$neu:0', typ: 'render', x: 300, y: 0 } },
            { befehl: 'vis.verbinden', argumente: { graphId: '$neu:0', from: '$neu:1', fromPort: 'szene', to: '$neu:2', toPort: 'szene' } },
          ],
        },
      },
      'karte',
    );
    if (!('karte' in a)) throw new Error(`Karte erwartet: ${JSON.stringify(a)}`);
    expect(a.karte.schritte).toHaveLength(4);
    expect(stand()).toBe(vorher);
    const tiefe = useProject.getState().history.depth;
    const e = anwenden('P-1')!;
    expect(e.ok).toBe(true);
    expect(useProject.getState().history.depth).toBe(tiefe + 1);
    const zweiter = useProject.getState().doc.byKind<VisGraph>('visgraph').find((g) => g.name === 'Zweiter')!;
    expect(zweiter.nodes).toHaveLength(2);
    expect(zweiter.edges).toEqual([expect.objectContaining({ from: zweiter.nodes[0]!.id, to: zweiter.nodes[1]!.id, toPort: 'szene' })]);
    for (const n of zweiter.nodes) expect(e.text).toContain(`NEUE nodeId «${n.id}»`);
    expect(e.text).toContain(`NEUE graphId «${zweiter.id}»`);
    useProject.getState().undo();
    expect(useProject.getState().doc.get(zweiter.id)).toBeUndefined();
  });

  it('ein ungueltiger Schritt: nichts wird vorgeschlagen, die Antwort nennt ihn', () => {
    const vorher = stand();
    const a = behandle(
      {
        kennung: 'P-2',
        werkzeug: VIS_PAKET,
        argumente: {
          schritte: [
            { befehl: 'vis_nodeSetzen', argumente: { graphId, typ: 'prompt', x: 0, y: 0 } },
            { befehl: 'vis_verbinden', argumente: { graphId, from: '$neu:0', fromPort: 'prompt', to: renderId, toPort: 'szene' } },
            { befehl: 'vis_nodeSetzen', argumente: { graphId: '$neu:5', typ: 'modell', x: 0, y: 0 } },
          ],
        },
      },
      'karte',
    );
    if (!('sofort' in a)) throw new Error('Fehler erwartet');
    expect(a.sofort.ok).toBe(false);
    expect(a.sofort.text).toMatch(/2 von 3 Schritten ungültig/);
    expect(a.sofort.text).toMatch(/Schritt 1 \(vis_verbinden\): Port-Typen passen nicht/);
    expect(a.sofort.text).toMatch(/Schritt 2 .*\$neu:5/);
    expect(stand()).toBe(vorher);
    expect(offeneVorschlaege()).toEqual([]);
  });

  it('mehr als 40 Schritte und Verschachteln werden abgewiesen', () => {
    const viele = Array.from({ length: 41 }, () => ({ befehl: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 0, y: 0 } }));
    const a = behandle({ kennung: 'P-3', werkzeug: VIS_PAKET, argumente: { schritte: viele } }, 'karte');
    expect('sofort' in a && a.sofort.text).toMatch(/höchstens 40/);
    const b = behandle({ kennung: 'P-4', werkzeug: VIS_PAKET, argumente: { schritte: [{ befehl: VIS_PAKET, argumente: {} }] } }, 'karte');
    expect('sofort' in b && b.sofort.text).toMatch(/verschachteln/);
  });
});

describe('Taetigkeit als Ereignis', () => {
  it('beginn und ende; bei einer Karte kommt das Ende erst mit dem Entscheid', () => {
    const ereignisse: KiEreignis[] = [];
    const ab = abonniere((e) => ereignisse.push(e));
    behandle({ kennung: 'T-1', werkzeug: GRAPH_LESEN }, 'karte');
    expect(ereignisse.map((e) => (e.art === 'taetigkeit' ? `${e.phase}:${e.kennung}` : e.art))).toEqual(['beginn:T-1', 'ende:T-1']);
    ereignisse.length = 0;
    behandle({ kennung: 'T-2', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 9, y: 9 }, urheber: 'assistent' }, 'karte');
    expect(ereignisse.map((e) => (e.art === 'taetigkeit' ? `${e.phase}:${e.kennung}` : e.art))).toEqual(['beginn:T-2', 'karte']);
    kiSchnittstelle().entscheide('T-2', true);
    expect(ereignisse.map((e) => (e.art === 'taetigkeit' ? `${e.phase}:${e.kennung}` : e.art))).toEqual(['beginn:T-2', 'karte', 'entschieden', 'ende:T-2']);
    const ende = ereignisse.at(-1)!;
    expect(ende.art === 'taetigkeit' && ende.urheber).toBe('assistent');
    ab();
  });
});
