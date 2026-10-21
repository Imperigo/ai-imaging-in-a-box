// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { leereKiZustand } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import { alsText, boteDerApp, haengeKiAn, MAPPE_GEWECHSELT, SEITE_LAEDT_NEU, type VisboxKi } from '../src/ki-wirt';

/**
 * VISBOX-EIGEN (KI-Bedienung Stufe 3, Entscheide 105–106f, 108, 114): Der Wirt haengt den
 * KI-Werkzeugsatz als `window.visboxKi` an, reicht jedes Ereignis an die Mac-App, setzt die Wache
 * fuer Strg+Z und verwirft offene Karten, wenn die Mappe wechselt. Laedt die Seite neu, bleiben die
 * Karten (Strang Karten, 21.10.2026): Die App gibt sie mit `stelleWieder` zurueck.
 */

let graphId = '';
let modellId = '';
let renderId = '';
let gesendet: Record<string, unknown>[] = [];
let ab: () => void = () => undefined;

const bote = { postMessage: (n: unknown) => void gesendet.push(n as Record<string, unknown>) };
const ki = () => (window as unknown as { visboxKi: VisboxKi }).visboxKi;
const graph = () => useProject.getState().doc.get<VisGraph>(graphId)!;
const arten = () => gesendet.map((n) => (n['art'] === 'taetigkeit' ? `${String(n['phase'])}` : String(n['art'])));

function neuesDokument(): KosmoDoc {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0 });
  const g = doc.get<VisGraph>(graphId)!;
  modellId = g.nodes[0]!.id;
  renderId = g.nodes[1]!.id;
  return doc;
}

beforeEach(() => {
  leereKiZustand();
  useProject.setState({ doc: neuesDokument(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
  gesendet = [];
  ab = haengeKiAn(window, bote);
});

afterEach(() => {
  ab();
  leereKiZustand();
});

describe('window.visboxKi', () => {
  it('steht mit allen Wegen der App — und keiner gibt die Grafikkarte frei', () => {
    expect(Object.keys(ki()).sort()).toEqual(['alsText', 'blick', 'blickMausWerkzeuge', 'entscheide', 'kiVerlauf', 'maus', 'offene', 'rueckgaengigKi', 'rufe', 'stelleWieder', 'verwirf', 'werkzeuge']);
    expect(Object.keys(ki()).filter((k) => /freig|approv|gpu/i.test(k))).toEqual([]);
    expect(gesendet[0]).toEqual({ art: 'bereit', werkzeuge: ki().werkzeuge().length });
    expect(ki().werkzeuge().map((w) => w.name)).toContain('graph_lesen');
  });

  it('ohne Mac-App (kein webkit.messageHandlers) gibt es keinen Boten', () => {
    expect(boteDerApp(window)).toBeNull();
    expect(boteDerApp({ webkit: { messageHandlers: { visboxKi: bote } } })).toBe(bote);
  });

  it('jede Antwort ist als JSON-Text lesbar', () => {
    const a = ki().rufe({ kennung: 'K-1', werkzeug: 'graph_lesen' }, 'karte');
    expect(JSON.parse(alsText(a))).toEqual(JSON.parse(JSON.stringify(a)));
    expect(alsText(undefined)).toBe('null');
  });
});

describe('Ereignisse an die App', () => {
  it('Karte: beginn, karte — und nach «Anwenden» entschieden, ende; als reine JSON-Werte', () => {
    gesendet = [];
    const a = ki().rufe({ kennung: 'K-2', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 9, y: 9 } }, 'karte');
    expect('karte' in a).toBe(true);
    expect(arten()).toEqual(['beginn', 'karte']);
    expect(gesendet[1]!['vorschlag']).toMatchObject({ kennung: 'K-2', art: 'aendern', urheber: 'claude' });
    ki().entscheide('K-2', true);
    expect(arten()).toEqual(['beginn', 'karte', 'entschieden', 'ende']);
    expect(gesendet[2]).toMatchObject({ art: 'entschieden', kennung: 'K-2', angewendet: true, ergebnis: { ok: true } });
    expect(graph().nodes.find((n) => n.id === modellId)).toMatchObject({ x: 9, y: 9 });
  });

  it('Coop: der KI-Schritt meldet «kiverlauf», und «Claudes letzten Schritt» nimmt ihn zurück', () => {
    gesendet = [];
    ki().rufe({ kennung: 'K-3', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 5, y: 5 } }, 'coop');
    const verlauf = gesendet.find((n) => n['art'] === 'kiverlauf')!;
    expect(verlauf).toMatchObject({ anzahl: 1, letzter: { claude: { kennung: 'K-3' }, assistent: null } });
    const r = ki().rueckgaengigKi('claude');
    expect(r.ok).toBe(true);
    expect(graph().nodes.find((n) => n.id === modellId)).toMatchObject({ x: 0, y: 0 });
    expect(gesendet.at(-1)).toEqual({ art: 'kiverlauf', anzahl: 0, letzter: { claude: null, assistent: null } });
  });
});

describe('Strg+Z nimmt nur die eigenen Schritte zurück (Entscheid 114)', () => {
  it('die Wache des Werkzeugsatzes ist gesetzt: über Claudes Arbeit hinweg sperrt Strg+Z', () => {
    useProject.getState().runCommand('vis.nodeSchieben', { graphId, nodeId: renderId, x: 400, y: 0 });
    ki().rufe({ kennung: 'K-4', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 7, y: 7 } }, 'voll');
    expect(useProject.getState().undo()).toBe(false);
    expect(graph().nodes.find((n) => n.id === modellId)).toMatchObject({ x: 7, y: 7 });
    ki().rueckgaengigKi('claude');
    // Die Ruecknahme ist selbst ein eigener Schritt: Strg+Z trifft jetzt sie und stellt Claudes Stand her.
    expect(useProject.getState().undo()).toBe(true);
    expect(graph().nodes.find((n) => n.id === modellId)).toMatchObject({ x: 7, y: 7 });
  });

  it('nach dem Abhängen wacht nichts mehr', () => {
    ab();
    ab = () => undefined;
    useProject.getState().runCommand('vis.nodeSchieben', { graphId, nodeId: renderId, x: 1, y: 1 });
    expect(useProject.getState().undo()).toBe(true);
  });
});

describe('Mappenwechsel und Neuladen', () => {
  it('ein neues Dokument verwirft offene Karten — die App bekommt «VERWORFEN»', () => {
    ki().rufe({ kennung: 'K-5', werkzeug: 'vis_nodeLoeschen', argumente: { graphId, nodeId: modellId } }, 'voll');
    expect(ki().offene()).toHaveLength(1);
    gesendet = [];
    useProject.setState({ doc: neuesDokument() } as never);
    expect(ki().offene()).toEqual([]);
    const e = gesendet.find((n) => n['art'] === 'entschieden')!;
    expect(e).toMatchObject({ kennung: 'K-5', angewendet: false });
    expect(String((e['ergebnis'] as { text: string }).text)).toContain(`VERWORFEN: ${MAPPE_GEWECHSELT}`);
  });

  it('beim Verlassen der Seite (pagehide) wird nichts verworfen — die App hört nur «weg»', () => {
    ki().rufe({ kennung: 'K-6', werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId, kameraWahl: 'auto' } }, 'voll');
    gesendet = [];
    window.dispatchEvent(new Event('pagehide'));
    expect(ki().offene().map((v) => v.kennung)).toEqual(['K-6']);
    expect(gesendet.filter((n) => n['art'] === 'entschieden')).toEqual([]);
    expect(gesendet.at(-1)).toEqual({ art: 'weg', grund: SEITE_LAEDT_NEU });
  });
});

/** Die Seite laedt neu: Modulzustand weg, Wirt neu angehaengt — wie in der WKWebView. */
function neuLaden(): void {
  ab();
  leereKiZustand();
  gesendet = [];
  ab = haengeKiAn(window, bote);
}

/** Der Vorschlag, wie die App ihn aus dem Ereignis «karte» haelt. */
function karteAusEreignis(kennung: string): unknown {
  const e = gesendet.find((n) => n['art'] === 'karte' && (n['vorschlag'] as { kennung: string }).kennung === kennung);
  return JSON.parse(JSON.stringify(e!['vorschlag']));
}

describe('Karten überleben das Neuladen (Strang Karten)', () => {
  it('Karte offen → Seite neu geladen → die App gibt sie zurück → sie liegt wieder, und Anwenden wirkt', () => {
    ki().rufe({ kennung: 'K-3', werkzeug: 'vis_nodeParametrieren', argumente: { graphId, nodeId: modellId, params: { stimmung: 'abend' } } }, 'karte');
    const roh = karteAusEreignis('K-3');
    window.dispatchEvent(new Event('pagehide'));
    neuLaden();
    expect(ki().offene()).toEqual([]);
    const antwort = ki().stelleWieder([roh]);
    expect(antwort).toEqual([{ kennung: 'K-3', liegt: true, text: expect.any(String) }]);
    expect(ki().offene().map((v) => v.kennung)).toEqual(['K-3']);
    expect(gesendet.some((n) => n['art'] === 'karte')).toBe(true);
    const ergebnis = ki().entscheide('K-3', true)!;
    expect(ergebnis.ok).toBe(true);
    expect(graph().nodes.find((n) => n.id === modellId)!.params['stimmung']).toBe('abend');
  });

  it('eine zurückgegebene Karte wird nie still angewendet — auch in Voll bleibt sie eine Karte', () => {
    ki().rufe({ kennung: 'K-4', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: renderId, x: 50, y: 60 } }, 'karte');
    const roh = karteAusEreignis('K-4');
    neuLaden();
    expect(ki().stelleWieder([roh])[0]!.liegt).toBe(true);
    expect(graph().nodes.find((n) => n.id === renderId)!.x).toBe(300);
  });

  it('passt die Karte nicht mehr zum Graph, sagt die Antwort den Satz — nichts liegt, nichts ist geändert', () => {
    ki().rufe({ kennung: 'K-7', werkzeug: 'vis_nodeParametrieren', argumente: { graphId, nodeId: modellId, params: { stimmung: 'abend' } } }, 'karte');
    const roh = karteAusEreignis('K-7');
    neuLaden();
    useProject.getState().runCommand('vis.nodeLoeschen', { graphId, nodeId: modellId });
    const [w] = ki().stelleWieder([roh]);
    expect(w).toMatchObject({ kennung: 'K-7', liegt: false });
    expect(w!.text).toMatch(/^FEHLER: /);
    expect(ki().offene()).toEqual([]);
  });

  it('ein Paket kommt als Paket zurück (ein Rückgängig)', () => {
    ki().rufe(
      {
        kennung: 'K-8',
        werkzeug: 'vis_paket',
        argumente: { schritte: [{ befehl: 'vis_nodeSetzen', argumente: { graphId, typ: 'stimmung', x: 10, y: 10 } }, { befehl: 'vis_nodeSchieben', argumente: { graphId, nodeId: '$neu:0', x: 20, y: 20 } }] },
      },
      'karte',
    );
    const roh = karteAusEreignis('K-8');
    neuLaden();
    const [w] = ki().stelleWieder([roh]);
    expect(w!.liegt).toBe(true);
    expect(ki().offene()[0]!.werkzeug).toBe('vis_paket');
    expect(ki().offene()[0]!.schritte).toHaveLength(2);
  });

  it('Unlesbares gibt die Seite nicht als Karte aus', () => {
    expect(ki().stelleWieder(null)).toEqual([]);
    expect(ki().stelleWieder([{ nix: 1 }])).toEqual([]);
  });
});
