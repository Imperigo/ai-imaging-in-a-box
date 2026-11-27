// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { anfangFallsLeer } from '../../kosmo-orbit/src/modules/vis/start-graph';
import {
  ladeGesichertenGraph,
  oeffneGesichertenGraph,
  registriereGraphOeffnen,
  legeGraphen,
  renderGraphen,
  sichereBeiAenderung,
  sicherWeg,
  type GraphLesung,
} from '../src/graph-sichern';

/**
 * A0832 «Lesefehler legt nichts an» (externes Audit 24.11.2026, Befund V2, Wirt). Die Audit-Probe
 * «Lesefehler: der erste Aufbau schickt einen neuen Graph …» war grün, solange der Fehler da war: nach
 * einem 503 legte der Wirt den fertigen Anfang an und sicherte ihn über den gesicherten Graph. Hier der
 * richtige Vertrag: nur eine bestätigt leere Mappe bekommt den Anfang, gesichert wird erst nach einem
 * gelungenen Lesen, und ein Lesefehler zeigt einen Satz mit «Nochmals laden».
 */
const GRAPH: VisGraph = {
  id: 'visgraph_gesichert',
  kind: 'visgraph',
  name: 'Gesichert',
  nodes: [{ id: 'm', typ: 'modell', x: 40, y: 40, params: {} }],
  edges: [],
} as VisGraph;

const ok = (rumpf: string) => new Response(rumpf, { status: 200, headers: { 'Content-Type': 'application/json' } });

/** Wie `main.tsx`: Öffnen, Sichern mit 1 s Verzögerung, der Satz mit «Nochmals laden» wird mitgeschrieben. */
async function oeffne(holen: () => Promise<Response>) {
  const wege: string[] = [];
  const senden = vi.fn(async (_rumpf: string) => {
    wege.push(sicherWeg());
    return ok(JSON.stringify({ gesichert: true, stand: 'neu' }));
  });
  const saetze: { satz: string; nochmals: () => Promise<GraphLesung> }[] = [];
  let ab: (() => void) | null = null;
  const lesung = await oeffneGesichertenGraph({
    holen: vi.fn(holen) as unknown as typeof fetch,
    suche: '?mappe=Probemappe',
    sichern: () => {
      ab = sichereBeiAenderung(senden, 1000);
    },
    zeigeSatz: (satz, nochmals) => saetze.push({ satz, nochmals }),
  });
  // Die Knotenansicht ruft das bei jeder Revision (VisWorkspace), hier einmal von Hand.
  anfangFallsLeer();
  return { lesung, senden, wege, saetze, stopp: () => ab?.() };
}

beforeEach(() => {
  vi.useFakeTimers();
  useProject.setState({ doc: new KosmoDoc(), history: new History(), revision: 0 } as never);
});
afterEach(() => {
  vi.useRealTimers();
});

describe('A0832: ein Lesefehler beim Öffnen legt keinen Startgraph an und sichert nichts', () => {
  const FEHLER: [string, () => Promise<Response>][] = [
    ['HTTP 503', async () => new Response('', { status: 503 })],
    ['abgebrochenes JSON', async () => ok('{"graphen": [{"id": "visgraph_gesi')],
    [
      'leere Liste mit «satz» (Datei nicht lesbar)',
      async () => ok(JSON.stringify({ graphen: [], mappe: 'Probemappe', satz: 'Der gesicherte Graph lässt sich nicht lesen.' })),
    ],
    ['keine Antwort', async () => Promise.reject(new TypeError('Failed to fetch'))],
  ];

  for (const [name, holen] of FEHLER) {
    it(`nach ${name}: in 2 s kein Sicher-Aufruf, kein Startgraph, ein Satz mit «Nochmals laden»`, async () => {
      const { lesung, senden, saetze, stopp } = await oeffne(holen);
      await vi.advanceTimersByTimeAsync(2000);
      expect(senden, 'kein einziger Sicher-Aufruf').toHaveBeenCalledTimes(0);
      expect(renderGraphen(), 'kein Startgraph im Dokument').toEqual([]);
      expect(lesung.art).not.toBe('leer');
      expect(saetze).toHaveLength(1);
      const satz = saetze[0]!.satz;
      expect(satz).toContain('«Nochmals laden»');
      expect(satz).toMatch(/\bdein\b|\bDein\b|Prüfe|klick/);
      expect(satz, 'kein Pfad und kein Programmtext').not.toMatch(/\/|`|\.json|Error|\d{3}/);
      stopp();
    });
  }

  it('der Satz des Heim-PC steht nur, wenn er einer für Menschen ist', async () => {
    const lesbar = await oeffne(async () => ok(JSON.stringify({ graphen: [], satz: 'Die Datei ist beschädigt.' })));
    expect(lesbar.saetze[0]!.satz).toContain('Der Heim-PC sagt: Die Datei ist beschädigt.');
    lesbar.stopp();
    const pfad = await oeffne(async () => ok(JSON.stringify({ graphen: [], satz: 'Kann /srv/mappen/x/graph.json nicht lesen' })));
    expect(pfad.saetze[0]!.satz).not.toContain('/srv');
    pfad.stopp();
  });
});

describe('A0832: nach dem Fehler «Nochmals laden»', () => {
  it('legt den gesicherten Graph ins Dokument, und erst danach sichert die Seite (mit Kennung und Stand)', async () => {
    let heimPc: () => Promise<Response> = async () => new Response('', { status: 503 });
    const { senden, wege, saetze, stopp } = await oeffne(() => heimPc());
    await vi.advanceTimersByTimeAsync(2000);
    expect(senden).toHaveBeenCalledTimes(0);

    heimPc = async () => ok(JSON.stringify({ graphen: [GRAPH], mappe: 'Probemappe', stand: 'stand-1' }));
    const zweite = await saetze[0]!.nochmals();
    expect(zweite).toEqual({ art: 'vorhanden', zahl: 1 });
    anfangFallsLeer();
    expect(renderGraphen().map((g) => g.id), 'der gesicherte Graph, kein Anfang daneben').toEqual(['visgraph_gesichert']);
    expect(saetze, 'kein zweiter Satz').toHaveLength(1);
    // Das Legen selbst ist kein Grund zu sichern.
    await vi.advanceTimersByTimeAsync(2000);
    expect(senden).toHaveBeenCalledTimes(0);

    // Erst eine Änderung wird gesichert — in die gelesene Mappe, auf den gelesenen Stand.
    legeGraphen([{ ...GRAPH, id: 'visgraph_neu' } as VisGraph]);
    await vi.advanceTimersByTimeAsync(1000);
    expect(senden).toHaveBeenCalledTimes(1);
    expect(wege).toEqual(['./graph?mappe=Probemappe&stand=stand-1']);
    expect((JSON.parse(senden.mock.calls[0]![0]) as { graphen: VisGraph[] }).graphen.map((g) => g.id)).toContain('visgraph_gesichert');
    stopp();
  });

  it('schlägt auch das zweite Lesen fehl: wieder ein Satz, weiter nichts gesichert', async () => {
    const { senden, saetze, stopp } = await oeffne(async () => new Response('', { status: 503 }));
    const zweite = await saetze[0]!.nochmals();
    expect(zweite.art).toBe('nicht_erreichbar');
    anfangFallsLeer();
    await vi.advanceTimersByTimeAsync(2000);
    expect(saetze).toHaveLength(2);
    expect(senden).toHaveBeenCalledTimes(0);
    expect(renderGraphen()).toEqual([]);
    stopp();
  });
});

describe('A0832: der Weg von main.tsx (angemeldetes Öffnen, dann ladeGesichertenGraph)', () => {
  afterEach(() => registriereGraphOeffnen(null));

  it('nach HTTP 503: 0 Graphen, kein Sichern, ein Satz; ohne Anmeldung nur lesen wie bisher', async () => {
    const sichern = vi.fn();
    const zeigeSatz = vi.fn();
    registriereGraphOeffnen({ sichern, zeigeSatz });
    const holen = vi.fn(async () => new Response('', { status: 503 })) as unknown as typeof fetch;
    expect(await ladeGesichertenGraph(holen)).toBe(0);
    anfangFallsLeer();
    expect(renderGraphen()).toEqual([]);
    expect(sichern).not.toHaveBeenCalled();
    expect(zeigeSatz).toHaveBeenCalledTimes(1);

    registriereGraphOeffnen(null);
    expect(await ladeGesichertenGraph(holen)).toBe(0);
    expect(zeigeSatz).toHaveBeenCalledTimes(1);
  });

  it('bestätigt leer: Sichern startet einmal, der Anfang entsteht', async () => {
    const sichern = vi.fn();
    registriereGraphOeffnen({ sichern, zeigeSatz: vi.fn() });
    expect(await ladeGesichertenGraph((async () => ok('{"graphen": []}')) as unknown as typeof fetch)).toBe(0);
    anfangFallsLeer();
    expect(sichern).toHaveBeenCalledTimes(1);
    expect(renderGraphen()).toHaveLength(1);
  });
});

describe('A0832: bleibt — die bestätigt leere Mappe (Entscheid 91)', () => {
  it('Antwort ok, graphen: [], kein satz: genau ein fertiger Anfang, und der wird gesichert', async () => {
    const { lesung, senden, saetze, stopp } = await oeffne(async () => ok(JSON.stringify({ graphen: [], mappe: 'Probemappe', stand: 's0' })));
    expect(lesung).toEqual({ art: 'leer' });
    anfangFallsLeer(); // Strict Mode ruft doppelt: weiter genau einer
    const graphen = renderGraphen();
    expect(graphen).toHaveLength(1);
    expect(graphen[0]!.nodes.map((n) => n.typ)).toEqual(
      expect.arrayContaining(['stimmung', 'prompt', 'modell', 'kamera', 'render', 'varianten', 'vergleich']),
    );
    expect(saetze).toHaveLength(0);
    await vi.advanceTimersByTimeAsync(1000);
    expect(senden).toHaveBeenCalledTimes(1);
    expect(sicherWeg()).toBe('./graph?mappe=Probemappe&stand=neu');
    stopp();
  });

  it('ein gesicherter Graph wird gelegt, kein Anfang, kein Satz', async () => {
    const { lesung, saetze, stopp } = await oeffne(async () => ok(JSON.stringify({ graphen: [GRAPH], mappe: 'Probemappe', stand: 's1' })));
    expect(lesung).toEqual({ art: 'vorhanden', zahl: 1 });
    expect(renderGraphen().map((g) => g.id)).toEqual(['visgraph_gesichert']);
    expect(saetze).toHaveLength(0);
    stopp();
  });
});
