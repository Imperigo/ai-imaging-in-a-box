// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, VARIANTEN_TYP, VIS_STIMMUNGEN, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime, type NodeLauf } from '../src/modules/vis/vis-runtime';
import {
  gewaehlteZelle,
  useVariantenBestellung,
  VARIANTE_GEWAEHLT_PARAM,
  variantenStandText,
  variantenZellen,
  zellenSchluessel,
  zellenTitel,
  type VariantenBestellung,
} from '../src/modules/vis/varianten';
import { VariantenDaumen } from '../src/modules/vis/VariantenDaumen';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';

/**
 * Blatt 36 «Varianten-Daumen» (Owner-Wunsch «Varianten-Node sollte Bildvorschauen zeigen»): die
 * Bildzeile im Varianten-Knoten. Ein Daumen 96 × 60 px mit Blaettern, Zustaende leer / wartet /
 * rechnet / fehlgeschlagen / fertig in derselben Box, Klick zeigt gross, dort waehlen. Nur das
 * KI-Bild (117a C). Alle Namen sind erfunden; die Bruecke ist eine Attrappe.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;

/** Das Wort der Stimmung kommt aus dem Katalog (dasselbe wie an den Haken und im Raster). */
const ABEND = VIS_STIMMUNGEN['abend']!.label;

let root: Root | null = null;
let container: HTMLDivElement | null = null;
function zeige(el: React.ReactElement): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(el));
}
const q = (id: string): HTMLElement | null => document.body.querySelector(`[data-testid="${id}"]`);
const klick = (id: string) => act(() => q(id)!.dispatchEvent(new MouseEvent('click', { bubbles: true })));

function graphMitVarianten(): { gid: string; vid: string } {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: 'Daumen' });
  const gid = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', {
    graphId: gid,
    typ: VARIANTEN_TYP,
    x: 40,
    y: 40,
  });
  const g = useProject.getState().doc.get<VisGraph>(gid)!;
  return { gid, vid: g.nodes[g.nodes.length - 1]!.id };
}
const graph = (gid: string) => useProject.getState().doc.get<VisGraph>(gid)!;
const knoten = (gid: string, vid: string) => graph(gid).nodes.find((n) => n.id === vid)!;

function bestellungFuer(vid: string, nr = 2): VariantenBestellung {
  return {
    graphId: 'g',
    nodeId: vid,
    nr,
    zeilen: ['Süd', 'Nordwest'],
    stimmungen: ['morgen', 'abend', 'weiss'],
    entwuerfe: [{ id: 'aktuell', name: 'Aktuelles Modell' }],
    gruppen: [
      {
        laufId: `${vid}::morgen::aktuell`,
        stimmung: 'morgen',
        entwurf: 'aktuell',
        standpunkte: ['Süd', 'Nordwest'],
      },
      {
        laufId: `${vid}::abend::aktuell`,
        stimmung: 'abend',
        entwurf: 'aktuell',
        standpunkte: ['Süd', 'Nordwest'],
      },
      {
        laufId: `${vid}::weiss::aktuell`,
        stimmung: 'weiss',
        entwurf: 'aktuell',
        standpunkte: ['Süd', 'Nordwest'],
      },
    ],
    anzahl: 6,
  };
}
function laeufeFuer(vid: string): Record<string, NodeLauf> {
  return {
    [`${vid}::morgen::aktuell`]: { status: 'rendert', jobId: 'job-m' },
    [`${vid}::abend::aktuell`]: {
      status: 'fertig',
      jobId: 'job-a',
      bild: 'a0.png',
      bilder: ['a0.png', 'a1.png'],
      guete: 'vorschau',
      lizenzOffen: true,
      engineUsed: 'testmodell',
      engineLicense: 'erfunden',
    },
    [`${vid}::weiss::aktuell`]: {
      status: 'fehler',
      jobId: 'job-w',
      fehler: 'Kein Render-Worker aktiv.',
    },
  };
}

beforeEach(() => {
  useProject.setState({
    doc: new KosmoDoc(),
    history: new History(),
    journal: [],
    revision: 0,
    activeStoreyId: null,
    selection: [],
  });
  useVisRuntime.setState({ aktiverGraphId: null, laeufe: {} });
  useVariantenBestellung.setState({ bestellungen: {} });
  vi.stubGlobal('fetch', (async () => ({
    ok: true,
    blob: async () => new Blob(['x']),
  })) as unknown as typeof fetch);
  vi.stubGlobal(
    'URL',
    Object.assign(URL, {
      createObjectURL: () => 'blob:x',
      revokeObjectURL: () => undefined,
    }),
  );
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (k === 'kosmo.bridge' ? 'http://localhost:8600' : null),
    setItem: () => undefined,
    removeItem: () => undefined,
  });
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  root = null;
  container?.remove();
  container = null;
  vi.unstubAllGlobals();
});

describe('Zellen tragen, was der Daumen zeigt (Blatt 36)', () => {
  it('fertige Zellen tragen Güte und Lizenz des Ergebnisses; Titel «Stimmung · Standpunkt»', () => {
    const b = bestellungFuer('v1');
    const z = variantenZellen(b, laeufeFuer('v1'));
    const abendSued = z.find((c) => c.stimmung === 'abend' && c.standpunkt === 'Süd')!;
    expect(abendSued).toMatchObject({
      zustand: 'fertig',
      bild: 'a0.png',
      guete: 'vorschau',
      lizenz: { lizenzOffen: true, engineUsed: 'testmodell' },
    });
    expect(zellenTitel(abendSued, b)).toBe(`${ABEND} · Süd`);
    // Mehr als ein Entwurf: der Entwurf steht im Titel.
    const b2 = {
      ...b,
      entwuerfe: [...b.entwuerfe, { id: 'k1', name: 'Riegel' }],
    };
    expect(zellenTitel(abendSued, b2)).toBe(`${ABEND} · Süd · Aktuelles Modell`);
    // Ohne Güte/Lizenz im Ergebnis: keine Felder (gilt als voll, keine offene Lizenz).
    const ohne = variantenZellen(b, {
      ...laeufeFuer('v1'),
      ['v1::abend::aktuell']: {
        status: 'fertig',
        jobId: 'j',
        bild: 'x.png',
        bilder: ['x.png', 'y.png'],
      },
    });
    const c = ohne.find((x) => x.stimmung === 'abend')!;
    expect('guete' in c).toBe(false);
    expect('lizenz' in c).toBe(false);
  });

  it('die Wahl gilt der Bestellung, in der sie getroffen wurde', () => {
    const b = bestellungFuer('v1', 3);
    const z = variantenZellen(b, laeufeFuer('v1'));
    const nw = z.find((c) => c.stimmung === 'abend' && c.standpunkt === 'Nordwest')!;
    expect(zellenSchluessel(3, nw)).toBe('3|Nordwest|abend|aktuell');
    expect(gewaehlteZelle({ [VARIANTE_GEWAEHLT_PARAM]: '3|Nordwest|abend|aktuell' }, b, z)).toBe(nw);
    expect(gewaehlteZelle({ [VARIANTE_GEWAEHLT_PARAM]: '2|Nordwest|abend|aktuell' }, b, z)).toBeUndefined();
    expect(gewaehlteZelle({ [VARIANTE_GEWAEHLT_PARAM]: '' }, b, z)).toBeUndefined();
    expect(gewaehlteZelle({}, undefined, z)).toBeUndefined();
  });
});

describe('Die Bildzeile am Knoten', () => {
  it('ohne Bestellung: ein Platz in Daumengrösse mit Satz, Blättern gesperrt', () => {
    const { gid, vid } = graphMitVarianten();
    zeige(<VariantenDaumen graph={graph(gid)} node={knoten(gid, vid)} />);
    expect(q('varianten-daumen')!.dataset['zustand']).toBe('leer');
    expect(q('varianten-daumen-leer')!.textContent).toBe('Noch keine Bilder');
    expect((q('varianten-daumen-zurueck') as HTMLButtonElement).disabled).toBe(true);
    expect((q('varianten-daumen-weiter') as HTMLButtonElement).disabled).toBe(true);
  });

  it('beginnt beim ersten fertigen Bild, blättert durch alle Zustände; Marken am Daumen', async () => {
    const { gid, vid } = graphMitVarianten();
    useVariantenBestellung.setState({
      bestellungen: { [vid]: bestellungFuer(vid) },
    });
    useVisRuntime.setState({ laeufe: laeufeFuer(vid) });
    zeige(<VariantenDaumen graph={graph(gid)} node={knoten(gid, vid)} />);
    await act(async () => {});
    // Reihenfolge wie im Raster: morgen (Süd, NW), abend (Süd, NW), weiss (Süd, NW) — das erste fertige ist Index 2.
    expect(q('varianten-daumen')!.dataset['zustand']).toBe('fertig');
    expect(q('varianten-daumen-titel')!.textContent).toBe(`${ABEND} · Süd`);
    expect(q('varianten-daumen-zahl')!.textContent).toBe('3 von 6');
    expect(q('varianten-daumen-guete')!.textContent).toBe('Vorschau');
    expect(q('varianten-daumen-lizenz-offen')).not.toBeNull();
    expect(q('varianten-daumen-bild')!.dataset['gewaehlt']).toBe('nein');
    // Kein title= (UI-Regel: Kurzhilfe ueber KTooltip).
    expect(container!.querySelector('[title]')).toBeNull();

    klick('varianten-daumen-zurueck');
    expect(q('varianten-daumen')!.dataset['zustand']).toBe('rechnet');
    expect(q('varianten-daumen-platz')!.dataset['zustand']).toBe('rechnet');
    klick('varianten-daumen-zurueck');
    expect(q('varianten-daumen-zahl')!.textContent).toBe('1 von 6');
    expect((q('varianten-daumen-zurueck') as HTMLButtonElement).disabled).toBe(true);
    for (let n = 0; n < 5; n++) klick('varianten-daumen-weiter');
    expect(q('varianten-daumen-zahl')!.textContent).toBe('6 von 6');
    expect(q('varianten-daumen-platz')!.dataset['zustand']).toBe('fehlgeschlagen');
    expect(q('varianten-daumen-platz')!.textContent).toBe('fehlgeschlagen');
    expect((q('varianten-daumen-weiter') as HTMLButtonElement).disabled).toBe(true);
  });

  it('Klick zeigt gross; dort blättern und wählen — ein Rückgängig-Schritt, im Stand für Kosmo und Claude', async () => {
    const { gid, vid } = graphMitVarianten();
    useVariantenBestellung.setState({
      bestellungen: { [vid]: bestellungFuer(vid) },
    });
    useVisRuntime.setState({ laeufe: laeufeFuer(vid) });
    zeige(<VariantenDaumen graph={graph(gid)} node={knoten(gid, vid)} />);
    await act(async () => {});
    klick('varianten-daumen-bild');
    expect(q('varianten-daumen-gross')).not.toBeNull();
    expect(q('varianten-daumen-gross')!.textContent).toContain('Nur das KI-Bild');
    expect(q('varianten-daumen-gross-guete')).not.toBeNull();
    expect((q('varianten-daumen-gross-zurueck') as HTMLButtonElement).disabled).toBe(true);
    klick('varianten-daumen-gross-weiter');
    expect(q('varianten-daumen-gross')!.textContent).toContain(`${ABEND} · Nordwest`);
    expect((q('varianten-daumen-gross-weiter') as HTMLButtonElement).disabled).toBe(true);

    const journalVorher = useProject.getState().journal.length;
    klick('varianten-daumen-waehlen');
    expect(knoten(gid, vid).params?.[VARIANTE_GEWAEHLT_PARAM]).toBe('2|Nordwest|abend|aktuell');
    expect(useProject.getState().journal.length).toBe(journalVorher + 1);
    act(() => root!.render(<VariantenDaumen graph={graph(gid)} node={knoten(gid, vid)} />));
    expect(q('varianten-daumen-waehlen')!.textContent).toBe('Auswahl aufheben');
    expect(variantenStandText(gid, vid)).toContain(`Gewählt: «Nordwest» · ${ABEND} · Aktuelles Modell, Bild a1.png.`);

    // Nach dem Schliessen zeigt der Knoten die gewaehlte Variante mit Haken.
    act(() => q('varianten-daumen-gross')!.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })));
    act(() => root!.render(<VariantenDaumen graph={graph(gid)} node={knoten(gid, vid)} />));
    expect(q('varianten-daumen-titel')!.textContent).toBe(`${ABEND} · Nordwest`);
    expect(q('varianten-daumen-zahl')!.textContent).toBe('4 von 6 · gewählt');
    expect(q('varianten-daumen-haken')).not.toBeNull();

    // Rueckgaengig hebt die Wahl auf.
    act(() => useProject.getState().undo());
    expect(knoten(gid, vid).params?.[VARIANTE_GEWAEHLT_PARAM]).toBeUndefined();
  });
});

describe('Höhe: die Bildzeile lässt die Karte nicht wachsen (kv-b5)', () => {
  it('der Varianten-Knoten ist in jedem Zustand gleich hoch — leer, rechnend, fertig, gewählt', async () => {
    const { gid, vid } = graphMitVarianten();
    zeige(<NodeCanvas graphId={gid} />);
    const hoehe = () => Number.parseFloat(container!.querySelector<HTMLElement>(`[data-testid="vis-node-${VARIANTEN_TYP}"]`)!.style.height);
    const leer = hoehe();
    act(() => {
      useVariantenBestellung.setState({
        bestellungen: { [vid]: bestellungFuer(vid) },
      });
      useVisRuntime.setState({ laeufe: laeufeFuer(vid) });
    });
    await act(async () => {});
    expect(q('varianten-daumen')!.dataset['zustand']).toBe('fertig');
    expect(hoehe()).toBe(leer);
    act(() =>
      useProject.getState().runCommand('vis.nodeParametrieren', {
        graphId: gid,
        nodeId: vid,
        params: { [VARIANTE_GEWAEHLT_PARAM]: '2|Süd|abend|aktuell' },
      }),
    );
    expect(q('varianten-daumen-haken')).not.toBeNull();
    expect(hoehe()).toBe(leer);
  });
});
