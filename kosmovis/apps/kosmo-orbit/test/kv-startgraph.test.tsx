// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { evaluiereGraph, History, KosmoDoc, VIS_NODE_KATALOG, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { VisWorkspace } from '../src/modules/vis/VisWorkspace';
import { BLATT_REFERENZ_GRUND, groessteNodeHoehe, NODE_W, NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { anfangFallsLeer, legeAnfangBeimOeffnen, startGraphAnlegen, startGraphLage } from '../src/modules/vis/start-graph';
import { registriereModellLaden, ladeModellDatei, setzeModellLadeZustand } from '../src/modules/vis/modell-laden';
import { registriereHeimStandpunkte } from '../src/modules/vis/heim-standpunkte';
import { umgebungFehltSatz } from '../src/modules/vis/umgebung-fehlt';

/**
 * KV-STARTGRAPH (Owner-Entscheid 91/91a/91b der Visbox, Blatt 22; Nachtrag 92, Blatt 23) und
 * die kleinen Punkte aus dem Visbox-Plan «Was die Knoten tun» / «Modell laden im Knoten».
 *
 *  - Der fertige Anfang: Modell, Auto-Kamera, Stimmung, Prompt → Kombinierer → Render →
 *    Bildvergleich, verbunden, EINE Rueckgaengig-Klammer, nichts rechnet.
 *  - Von selbst nur, wenn der Wirt es will (Visbox); sonst ein Knopf (KosmoOrbit). Ein
 *    bestehender Graph bleibt unveraendert.
 *  - Bild-Referenz traegt ihr Bild in den Vergleich, nicht aufs Blatt.
 *  - «Samples»-Zahl: der Knoten sagt, wer Vorrang hat.
 *  - Nach «nicht lesbar» nennt der Modell-Knoten das vorige Modell weiter.
 *  - Heim-Standpunkte (Visbox): der Knoten zeigt sie, der Auftrag bleibt `auto`.
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

function graphen(): VisGraph[] {
  return useProject.getState().doc.byKind<VisGraph>('visgraph');
}

beforeEach(() => frischesDokument());
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  legeAnfangBeimOeffnen(false);
  registriereModellLaden(null);
  registriereHeimStandpunkte(null);
});

describe('KV-STARTGRAPH · der fertige Anfang', () => {
  it('sieben Knoten, sechs Linien, an den richtigen Anschluessen', () => {
    const gid = startGraphAnlegen()!;
    const g = useProject.getState().doc.get<VisGraph>(gid)!;
    expect(g.nodes.map((n) => n.typ).sort()).toEqual(
      ['kamera', 'kombinierer', 'modell', 'prompt', 'render', 'stimmung', 'vergleich'].sort(),
    );
    const typ = (id: string) => g.nodes.find((n) => n.id === id)!.typ;
    const linien = g.edges.map((e) => `${typ(e.from)}.${e.fromPort}→${typ(e.to)}.${e.toPort}`).sort();
    expect(linien).toEqual(
      [
        'stimmung.prompt→kombinierer.stimmung',
        'prompt.prompt→kombinierer.stil',
        'kombinierer.prompt→render.prompt',
        'modell.szene→render.szene',
        'kamera.kameras→render.kameras',
        'render.bild→vergleich.bild1',
      ].sort(),
    );
    expect(useVisRuntime.getState().aktiverGraphId).toBe(gid);
  });

  it('nichts rechnet: kein Render-Auftrag, kein Lauf', () => {
    startGraphAnlegen();
    expect(useProject.getState().doc.settings.visRenderAuftrag ?? null).toBeNull();
    expect(useVisRuntime.getState().laeufe).toEqual({});
  });

  it('EIN Strg+Z nimmt den ganzen Anfang zurueck', () => {
    startGraphAnlegen();
    expect(graphen()).toHaveLength(1);
    act(() => {
      useProject.getState().undo();
    });
    expect(graphen()).toHaveLength(0);
  });

  it('die Knoten ueberlappen sich nicht — auch aufgeklappt nicht', () => {
    const lage = Object.entries(startGraphLage());
    for (const [a, pa] of lage) {
      for (const [b, pb] of lage) {
        if (a >= b) continue;
        const ha = groessteNodeHoehe(a);
        const hb = groessteNodeHoehe(b);
        const ueber = pa.x < pb.x + NODE_W && pb.x < pa.x + NODE_W && pa.y < pb.y + hb && pb.y < pa.y + ha;
        expect(ueber, `${a} und ${b}`).toBe(false);
      }
    }
  });

  it('die Auto-Kamera hat keinen Eingang — darum keine Linie vom Modell (Katalog)', () => {
    expect(VIS_NODE_KATALOG.kamera!.inputs).toEqual([]);
  });
});

describe('KV-STARTGRAPH · wann der Anfang entsteht', () => {
  it('KosmoOrbit (kein Wirt-Wunsch): Oeffnen aendert nichts, der Vorschlag hat einen Knopf', () => {
    const revVorher = useProject.getState().revision;
    montiere(<VisWorkspace />);
    expect(graphen()).toHaveLength(0);
    expect(useProject.getState().revision).toBe(revVorher);
    expect(useProject.getState().history.canUndo).toBe(false);
    expect(q('vis-leer-anfang-satz')?.textContent).toContain('Bildvergleich');
    act(() => q('vis-leer-anfang-anlegen')!.dispatchEvent(new MouseEvent('click', { bubbles: true })));
    expect(graphen()).toHaveLength(1);
    expect(graphen()[0]!.nodes).toHaveLength(7);
  });

  it('Visbox (Wirt will ihn): beim Oeffnen da, «Datei laden …» sofort im Modell-Knoten', () => {
    registriereModellLaden({ formate: ['IFC', 'glb/glTF'], annehmen: '.ifc,.glb', laden: async () => ({ stand: 'leer' }) });
    legeAnfangBeimOeffnen(true);
    montiere(<VisWorkspace />);
    expect(graphen()).toHaveLength(1);
    expect(q('modell-datei-laden')?.textContent).toBe('Datei laden …');
  });

  it('ein bestehender Graph bleibt unveraendert', () => {
    const { runCommand } = useProject.getState();
    const gid = (runCommand('vis.graphErstellen', { name: 'Eigener' }).patches[0] as { id: string }).id;
    runCommand('vis.nodeSetzen', { graphId: gid, typ: 'render', x: 300, y: 40 });
    const vorher = JSON.stringify(useProject.getState().doc.get<VisGraph>(gid));
    legeAnfangBeimOeffnen(true);
    montiere(<VisWorkspace />);
    expect(graphen()).toHaveLength(1);
    expect(JSON.stringify(useProject.getState().doc.get<VisGraph>(gid))).toBe(vorher);
  });

  it('zurueckgenommen bleibt zurueckgenommen — kein zweiter Anfang im selben Dokument', () => {
    legeAnfangBeimOeffnen(true);
    montiere(<VisWorkspace />);
    expect(graphen()).toHaveLength(1);
    act(() => {
      useProject.getState().undo();
    });
    expect(graphen()).toHaveLength(0);
    expect(anfangFallsLeer()).toBeUndefined();
    expect(graphen()).toHaveLength(0);
    expect(q('vis-leer-anfang-anlegen')).not.toBeNull();
  });
});

describe('KV-STARTGRAPH · kleine Punkte am Knoten', () => {
  function graphMit(): { gid: string; setze: (typ: string, x: number, y: number, params?: Record<string, string | number>) => string } {
    const { runCommand } = useProject.getState();
    const gid = (runCommand('vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
    const setze = (typ: string, x: number, y: number, params?: Record<string, string | number>) => {
      runCommand('vis.nodeSetzen', { graphId: gid, typ, x, y, ...(params ? { params } : {}) });
      const g = useProject.getState().doc.get<VisGraph>(gid)!;
      return g.nodes[g.nodes.length - 1]!.id;
    };
    return { gid, setze };
  }
  const verbinde = (graphId: string, from: string, fromPort: string, to: string, toPort: string) =>
    useProject.getState().runCommand('vis.verbinden', { graphId, from, fromPort, to, toPort });

  it('Hilfetext der Auto-Kamera nennt den Innenraum bei Raeumen (wie der Code bestellt)', () => {
    const hilfe = VIS_NODE_KATALOG.kamera!.hilfe;
    expect(hilfe).toContain('Innenraum');
    expect(hilfe).toContain('IFC');
    expect(hilfe).not.toContain('Bestellt wird nur Eingang/Übersicht');
  });

  it('Bild-Referenz: das Bild steht im Bildvergleich', () => {
    const { gid, setze } = graphMit();
    const ref = setze('referenz', 40, 40, { url: 'data:image/png;base64,AAAA' });
    const vgl = setze('vergleich', 400, 40);
    verbinde(gid, ref, 'bild', vgl, 'bild1');
    montiere(<NodeCanvas graphId={gid} />);
    const bilder = q('vergleich-bilder')!.querySelectorAll('img');
    expect(bilder).toHaveLength(1);
    expect(bilder[0]!.getAttribute('src')).toBe('data:image/png;base64,AAAA');
  });

  it('Bild-Referenz: aufs Blatt geht sie nicht, und der Knoten sagt warum', () => {
    const { gid, setze } = graphMit();
    const ref = setze('referenz', 40, 40, { url: 'data:image/png;base64,AAAA' });
    const blatt = setze('blatt', 400, 40);
    verbinde(gid, ref, 'bild', blatt, 'bild');
    montiere(<NodeCanvas graphId={gid} />);
    expect((q('blatt-ablegen') as HTMLButtonElement).disabled).toBe(true);
    expect(q('blatt-referenz-hinweis')?.textContent).toBe('nur Vorbild');
    expect(BLATT_REFERENZ_GRUND).toContain('fremdes Vorbild');
  });

  it('«Samples»: mit Zahl am Eingang nennt die Qualitaets-Zeile den Vorrang', () => {
    const { gid, setze } = graphMit();
    const zahl = setze('zahl', 40, 40, { wert: 64, min: 1, max: 512, schritt: 1 });
    const render = setze('render', 400, 40);
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('render-qualitaet-zeile')?.closest('[data-zeile]')?.getAttribute('title') ?? null).toBeNull();
    act(() => {
      verbinde(gid, zahl, 'zahl', render, 'samples');
    });
    const zeile = q('render-qualitaet-zeile')!.closest('[data-zeile]')!;
    expect(zeile.getAttribute('title')).toContain('Vorrang');
    // Leer gewaehlt zeigt der Waehler den leeren Eintrag — er nennt jetzt die Zahl.
    expect(zeile.textContent).toContain('von der Zahl am Eingang «Samples»');
  });

  it('nach «nicht lesbar» nennt der Modell-Knoten das vorige Modell weiter', async () => {
    registriereModellLaden({ formate: ['IFC'], annehmen: '.ifc', laden: async () => ({ stand: 'fehler', satz: 'Nicht lesbar.' }) });
    setzeModellLadeZustand({ stand: 'geladen', bauteile: 12, herkunft: 'IFC', mappe: 'haus', fassung: 1 });
    const { gid, setze } = graphMit();
    setze('modell', 40, 40);
    montiere(<NodeCanvas graphId={gid} />);
    await act(async () => {
      await ladeModellDatei(new File(['x'], 'kaputt.ifc'));
    });
    expect(q('modell-satz')?.textContent).toBe('Nicht lesbar.');
    expect(q('modell-noch')?.textContent).toBe('Noch geladen: Mappe «haus» · Szene: 12 Bauteile (aus IFC)');
  });

  it('ohne vorheriges Modell gibt es keine «Noch geladen»-Zeile', async () => {
    registriereModellLaden({ formate: ['IFC'], annehmen: '.ifc', laden: async () => ({ stand: 'fehler', satz: 'Nicht lesbar.' }) });
    const z = await ladeModellDatei(new File(['x'], 'kaputt.ifc'));
    expect(z).toEqual({ stand: 'fehler', satz: 'Nicht lesbar.' });
  });

  it('Heim-Standpunkte (Visbox): der Knoten zeigt sie, der Auftrag bleibt «auto»', () => {
    registriereHeimStandpunkte({
      standpunkte: [
        { kuerzel: 's', name: 'Süd', art: 'frontal', abstand_m: 24.4, auge: [0, -30, 1.7], blick_auf: [0, 0, 1.7], vollstaendig: true, begruendung: 'frontal' },
        { kuerzel: 'sSE', name: 'Südost', art: 'über Eck', abstand_m: 26, auge: [1, -1, 1.7], blick_auf: [0, 0, 1.7], vollstaendig: true, begruendung: '' },
        { kuerzel: 'nNW', name: 'Nordwest', art: 'über Eck', abstand_m: 26, auge: [-1, 1, 1.7], blick_auf: [0, 0, 1.7], vollstaendig: true, begruendung: '' },
      ],
      satz: 'Rechnet der Heim-PC aus der Hüllbox (dem Bauwerk) — Vorschau.',
    });
    const { gid, setze } = graphMit();
    const kamera = setze('kamera', 40, 40);
    const render = setze('render', 400, 40);
    verbinde(gid, kamera, 'kameras', render, 'kameras');
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('vis-kamera-heim-s')?.textContent).toBe('Süd — frontal, 24 m');
    expect(q('vis-kamera-heim-nNW')?.textContent).toBe('Nordwest — über Eck, 26 m');
    expect(q('vis-kamera-heim-satz')?.textContent).toContain('Vorschau');
    const doc = useProject.getState().doc;
    const auftrag = evaluiereGraph(doc, doc.get<VisGraph>(gid)!).renderAuftraege.get(render)!;
    expect(auftrag.kameras).toBeUndefined();
  });

  it('Runde 29: «Ohne Umgebung: <Grund>» am Render-Knoten, solange der Lauf steht — ohne Feld keine Zeile', () => {
    const { gid, setze } = graphMit();
    const render = setze('render', 400, 40);
    useVisRuntime.setState({ laeufe: { [render]: { status: 'abgebrochen', jobId: 'vis-1-abc' } } });
    montiere(<NodeCanvas graphId={gid} />);
    expect(q('render-umgebung-fehlt')).toBeNull();
    act(() => {
      useVisRuntime.setState({
        laeufe: { [render]: { status: 'abgebrochen', jobId: 'vis-1-abc', umgebungFehlt: 'Der Splat kam ohne Pfad.' } as never },
      });
    });
    expect(q('render-umgebung-fehlt')?.textContent).toBe('Ohne Umgebung: Der Splat kam ohne Pfad.');
  });

  it('Runde 29: das Feld wird duldsam gelesen (Satz, { grund }, true), sonst nichts', () => {
    expect(umgebungFehltSatz({ umgebungFehlt: 'kein Pfad' })).toBe('kein Pfad');
    expect(umgebungFehltSatz({ umgebungFehlt: { grund: 'kein Pfad' } })).toBe('kein Pfad');
    expect(umgebungFehltSatz({ umgebungFehlt: true })).toBe('Grund nicht genannt');
    expect(umgebungFehltSatz({ status: 'fertig' })).toBeNull();
    expect(umgebungFehltSatz(undefined)).toBeNull();
  });
});
