// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { execute, History, KosmoDoc, stimmungAusParams, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { leereKiZustand } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import {
  graphDerNeuenMappe,
  graphMappe,
  graphStand,
  ladeGesichertenGraph,
  leseWeg,
  renderGraphen,
  setzeGraphMappe,
  sicherWeg,
  sichereBeiAenderung,
} from '../src/graph-sichern';
import { haengeKiAn, type VisboxKi } from '../src/ki-wirt';

/**
 * Mac-Befund 0.3.33 (22.10.2026, Protokoll 74 §231). Karte K-2 «Stimmung morgen → abend» lag offen;
 * nach Startansicht → «Schon anfangen» stand im Graph `presets=["abend"]` und am Kamera-Knoten
 * `richtungen=["sSE","nNW"]`. **Angewendet war K-2 nicht:** Die Knotenansicht zeigte nach dem
 * Neuladen den Graph einer ANDEREN Mappe («probe330», die Gegenprobe 330 hatte sie am Heim-PC
 * geöffnet und genau so eingestellt). Der Heim-PC hat eine «zuletzt geöffnete» Mappe für alle
 * Geräte. Zwei Folgen werden hier bewacht:
 *
 *  1. Die Seite sichert ihren Graph in die Mappe, die sie GELESEN hat (`?mappe=`), nie in die, die
 *     ein anderes Gerät inzwischen geöffnet hat.
 *  2. Eine Karte gehört zu ihrer Mappe: Die App gibt sie nach dem Neuladen zurück, aber eine
 *     Knotenansicht einer anderen Mappe nimmt sie nicht an.
 *
 * Und die Spielregel «Modus Karte» selbst, als Wache über den ganzen Weg: Eine offene Karte ändert
 * weder das Dokument noch das, was gesichert wird — auch nicht über das Neuladen mit `stelleWieder`.
 */

let graphId = '';
let stimmungId = '';
let gesendet: Record<string, unknown>[] = [];
let ab: () => void = () => undefined;
const bote = { postMessage: (n: unknown) => void gesendet.push(n as Record<string, unknown>) };
const ki = () => (window as unknown as { visboxKi: VisboxKi }).visboxKi;

function dokumentMitStimmung(): KosmoDoc {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Bilder' }).patches[0] as { id: string }).id;
  // So legt der fertige Anfang die Stimmung an: nur `preset` (Entscheid 91).
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'stimmung', x: 0, y: 0, params: { preset: 'morgen' } });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0 });
  stimmungId = doc.get<VisGraph>(graphId)!.nodes[0]!.id;
  return doc;
}

function oeffne(doc: KosmoDoc): void {
  useProject.setState({ doc, history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
}

const stimmung = () => {
  const n = useProject.getState().doc.get<VisGraph>(graphId)!.nodes.find((x) => x.id === stimmungId)!;
  return n.params ?? {};
};

const antwort = (wert: unknown) => new Response(JSON.stringify(wert), { status: 200 });

beforeEach(() => {
  leereKiZustand();
  setzeGraphMappe(null);
  oeffne(dokumentMitStimmung());
  gesendet = [];
});

afterEach(() => {
  ab();
  ab = () => undefined;
  leereKiZustand();
  setzeGraphMappe(null);
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('§231 — gesichert wird in die gelesene Mappe', () => {
  it('der Heim-PC nennt die Mappe beim Lesen; gesichert wird mit ?mappe= genau dorthin', async () => {
    oeffne(new KosmoDoc());
    await ladeGesichertenGraph((async () => antwort({ graphen: [], mappe: 'Demohaus Test' })) as unknown as typeof fetch);
    expect(graphMappe()).toBe('Demohaus Test');
    expect(sicherWeg()).toBe('./graph?mappe=Demohaus+Test'); // «+» heisst am Heim-PC Leerzeichen (parse_qs)

    vi.useFakeTimers();
    const geholt: string[] = [];
    vi.stubGlobal('fetch', vi.fn(async (weg: string) => {
      geholt.push(weg);
      return new Response('{"gesichert":1}', { status: 200 });
    }));
    const stop = sichereBeiAenderung(undefined, 10);
    execute(useProject.getState().doc, 'vis.graphErstellen', { name: 'Neu' });
    useProject.setState((s) => ({ revision: s.revision + 1 }));
    vi.advanceTimersByTime(10);
    stop();
    expect(geholt).toEqual(['./graph?mappe=Demohaus+Test']);
  });

  it('ohne genannte Mappe (Mappe am Mac) wie bisher: ./graph', async () => {
    await ladeGesichertenGraph((async () => antwort({ graphen: [] })) as unknown as typeof fetch);
    expect(graphMappe()).toBeNull();
    expect(sicherWeg()).toBe('./graph');
  });

  it('nach «Datei laden …» gilt die neue Mappe; ohne Antwort keine alte', async () => {
    setzeGraphMappe('Alt');
    await graphDerNeuenMappe((async () => antwort({ graphen: [], mappe: 'Neu' })) as unknown as typeof fetch);
    expect(graphMappe()).toBe('Neu');
    await graphDerNeuenMappe((async () => {
      throw new Error('kein Netz');
    }) as unknown as typeof fetch);
    expect(graphMappe()).toBeNull();
  });
});

describe('§231 — eine Karte gehört zu ihrer Mappe', () => {
  it('die Karte trägt die Mappe ihres Graphen an die App', () => {
    setzeGraphMappe('Demohaus Test');
    ab = haengeKiAn(window, bote);
    ki().rufe({ kennung: 'K-2', werkzeug: 'vis_nodeParametrieren', argumente: { graphId, nodeId: stimmungId, params: { preset: 'abend' } } }, 'karte');
    const karte = gesendet.find((n) => n['art'] === 'karte')!;
    expect((karte['vorschlag'] as Record<string, unknown>)['mappe']).toBe('Demohaus Test');
  });

  it('die Knotenansicht einer anderen Mappe nimmt die Karte nicht an — mit Satz, nichts geändert', () => {
    setzeGraphMappe('probe330');
    ab = haengeKiAn(window, bote);
    const roh = {
      kennung: 'K-2',
      werkzeug: 'vis_nodeParametrieren',
      art: 'aendern',
      urheber: 'claude',
      zusammenfassung: 'Node-Parameter (preset)',
      mappe: 'Demohaus Test',
      schritte: [{ commandId: 'vis.nodeParametrieren', params: { graphId, nodeId: stimmungId, params: { preset: 'abend' } }, zusammenfassung: 'Node-Parameter (preset)' }],
    };
    const [w] = ki().stelleWieder([roh]);
    expect(w).toMatchObject({ kennung: 'K-2', liegt: false });
    expect(w!.text).toContain('«Demohaus Test»');
    expect(w!.text).toContain('«probe330»');
    expect(ki().offene()).toEqual([]);
    expect(stimmung()).toEqual({ preset: 'morgen' });
    // Dieselbe Mappe: die Karte liegt wieder.
    setzeGraphMappe('Demohaus Test');
    expect(ki().stelleWieder([roh])[0]!.liegt).toBe(true);
  });
});

describe('Spielregel «Modus Karte» über das Neuladen', () => {
  it('eine offene Karte ändert weder das Dokument noch das Gesicherte — vor und nach dem Neuladen', async () => {
    vi.useFakeTimers();
    const gesichert: string[] = [];
    let stop = sichereBeiAenderung(async (rumpf) => void gesichert.push(rumpf), 10);
    ab = haengeKiAn(window, bote);
    ki().rufe({ kennung: 'K-2', werkzeug: 'vis_nodeParametrieren', argumente: { graphId, nodeId: stimmungId, params: { preset: 'abend' } } }, 'karte');
    expect(ki().offene().map((v) => v.kennung)).toEqual(['K-2']);
    vi.advanceTimersByTime(50);
    expect(stimmung()).toEqual({ preset: 'morgen' });
    const roh = JSON.parse(JSON.stringify(gesendet.find((n) => n['art'] === 'karte')!['vorschlag']));

    // NEULADEN: die Seite geht, der gesicherte Graph kommt in ein neues Dokument, die App gibt die Karte zurück.
    stop();
    ab();
    leereKiZustand();
    const gespeichert = JSON.parse(JSON.stringify(renderGraphen())) as VisGraph[];
    oeffne(new KosmoDoc());
    await ladeGesichertenGraph((async () => antwort({ graphen: gespeichert })) as unknown as typeof fetch);
    stop = sichereBeiAenderung(async (rumpf) => void gesichert.push(rumpf), 10);
    gesendet = [];
    ab = haengeKiAn(window, bote);
    expect(ki().stelleWieder([roh])[0]!.liegt).toBe(true);
    vi.advanceTimersByTime(50);
    expect(stimmung()).toEqual({ preset: 'morgen' });
    expect(stimmungAusParams(stimmung()).presets).toEqual(['morgen']);
    expect(gesichert.join('')).not.toContain('abend');

    // «Ablehnen»: nichts ändert sich. Erst «Anwenden» ändert den Graph.
    ki().entscheide('K-2', false);
    expect(stimmung()).toEqual({ preset: 'morgen' });
    ki().stelleWieder([roh]);
    ki().entscheide('K-2', true);
    expect(stimmung()).toMatchObject({ preset: 'abend' });
    stop();
  });

  it('der Befund war die andere Mappe: «presets» schreibt nur der Knoten selbst, K-2 hätte nur «preset» geschrieben', () => {
    ab = haengeKiAn(window, bote);
    ki().rufe({ kennung: 'K-2', werkzeug: 'vis_nodeParametrieren', argumente: { graphId, nodeId: stimmungId, params: { preset: 'abend' } } }, 'karte');
    ki().entscheide('K-2', true);
    expect(stimmung()).toEqual({ preset: 'abend' });
    expect('presets' in stimmung()).toBe(false);
  });
});

describe('Entscheid 129 — der Mac öffnet seine Mappe', () => {
  it('mit ?mappe= in der Adresse liest die Seite genau diese Mappe', async () => {
    expect(leseWeg('?mappe=Demohaus%20Test')).toBe('./graph?mappe=Demohaus%20Test');
    expect(leseWeg('')).toBe('./graph');
    const holen = vi.fn(async () => antwort({ graphen: [], mappe: 'Demohaus Test', stand: 'leer' }));
    await ladeGesichertenGraph(holen as unknown as typeof fetch, '?mappe=Demohaus%20Test');
    expect(holen).toHaveBeenCalledWith('./graph?mappe=Demohaus%20Test');
  });

  it('gibt es die verlangte Mappe nicht, sichert die Seite trotzdem nur dorthin (der Heim-PC weist ab)', async () => {
    await ladeGesichertenGraph((async () => new Response('{"fehler":"gibt es nicht"}', { status: 404 })) as unknown as typeof fetch, '?mappe=Weg');
    expect(graphMappe()).toBe('Weg');
    expect(sicherWeg()).toBe('./graph?mappe=Weg');
  });
});

describe('§231 Nachtrag — zwei Geräte in einer Mappe', () => {
  it('gesichert wird mit dem gelesenen Stand; danach gilt der neue', async () => {
    await ladeGesichertenGraph((async () => antwort({ graphen: [], mappe: 'probe330', stand: 'aaaa' })) as unknown as typeof fetch);
    expect(sicherWeg()).toBe('./graph?mappe=probe330&stand=aaaa');
    vi.useFakeTimers();
    const stop = sichereBeiAenderung(async () => new Response(JSON.stringify({ gesichert: 1, stand: 'bbbb' }), { status: 200 }), 10);
    execute(useProject.getState().doc, 'vis.graphErstellen', { name: 'Neu' });
    useProject.setState((s) => ({ revision: s.revision + 1 }));
    await vi.advanceTimersByTimeAsync(10);
    stop();
    expect(graphStand()).toBe('bbbb');
  });

  it('hat ein anderes Gerät inzwischen gesichert, sagt der Speichern-Kreis es — nichts still', async () => {
    vi.useFakeTimers();
    const lagen: { stand: string; grund?: string }[] = [];
    const satz = 'Ein anderes Gerät hat den Graph dieser Mappe inzwischen geändert — nicht überschrieben. Die Knotenansicht neu laden, dann weiterarbeiten.';
    const stop = sichereBeiAenderung(
      async () => new Response(JSON.stringify({ fehler: satz }), { status: 409 }),
      10,
      (l) => void lagen.push(l as { stand: string; grund?: string }),
    );
    execute(useProject.getState().doc, 'vis.graphErstellen', { name: 'Neu' });
    useProject.setState((s) => ({ revision: s.revision + 1 }));
    await vi.advanceTimersByTimeAsync(10);
    stop();
    expect(lagen.at(-1)).toMatchObject({ stand: 'fehler', grund: satz });
  });
});
