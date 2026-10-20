// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type VisGraph, type VisNode } from '@kosmo/kernel';
import { BildKachel, NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { laufGrund, laufUrteil, treueText } from '../src/modules/vis/render-verlauf';
import { kameraQaText, kameraQaZeilen, type KuratierKartenDaten } from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';
import { memoKey, useVisRuntime, type NodeLauf } from '../src/modules/vis/vis-runtime';
import { useProject } from '../src/state/project-store';

/**
 * WebKitGTK-Pruefung der HomeStation (266/267, echte Laeufe ueber den
 * Abholer): der Abholer liefert in `qa.geometry` NIE `rho_maske`, `kante`
 * oder `paarurteil` — nur die alten Zahlen. Die Attrappen-Bruecke liefert
 * sie, darum fiel es in Chromium nicht auf. Folge: `bewertungsLage` sagte bei
 * jedem echten Ergebnis `widerrufen`, und der Verlauf machte daraus «nicht
 * beurteilbar» — auch bei einem echten Durchfallen (0.598 gegen 0.65), waehrend
 * die Kachel daneben richtig «QA ✗» zeigte. Der Inspektor sagte bei «nicht
 * beurteilbar» zusaetzlich «Bewertung zurueckgezogen».
 *
 * Diese Probe nimmt die REALISTISCHE Form (nur `geometry_fidelity`,
 * `geom_iou`, `threshold`, `passed`) und haelt Kachel und Verlauf gegeneinander:
 * dasselbe Ergebnis, dasselbe Urteil.
 */

class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
if (!('createObjectURL' in URL)) {
  Object.assign(URL, { createObjectURL: () => 'blob:stub', revokeObjectURL: () => undefined });
}

const SATZ_NB =
  "NICHT BEURTEILBAR (Gebaeudeanteil): Das Haus fuellt nur 18% des Bildes, weniger als 20 %; der Gesamtwert ist hier nicht anwendbar. 'passed: false' heisst hier nicht durchgefallen, sondern nicht beurteilbar.";

/** So liefert der echte Abholer: keine Maskenfelder. */
function echt(passed: boolean, reason?: string, gf = 0.81): JobQa {
  return {
    verdict: { passed, ...(reason !== undefined ? { reason } : {}) },
    geometry: { geometry_fidelity: gf, geom_iou: 0.77, threshold: 0.65, passed, method: 'depthanything-v2-redepth' },
    style: { style_score: 0.6, threshold: 0.3, passed: true, method: 'clip' },
  };
}
const ECHT_OK = echt(true, undefined, 0.81);
const ECHT_FEHL = echt(false, 'Geometrie 0.598 gegen 0.65', 0.598);
const ECHT_NB = echt(false, SATZ_NB, 0.71);
const FAELLE = [
  ['bestanden', ECHT_OK, 'bestanden'],
  ['echtes Durchfallen', ECHT_FEHL, 'durchgefallen'],
  ['nicht beurteilbar laut Grund', ECHT_NB, 'nicht-beurteilbar'],
] as const;

let root: Root | null = null;
let container: HTMLDivElement | null = null;
function stubBridge(): void {
  vi.stubGlobal('fetch', (async () =>
    ({ ok: true, status: 200, blob: async () => new Blob(['x'], { type: 'image/png' }) }) as Response) as unknown as typeof fetch);
}
function mount(el: React.ReactElement): HTMLDivElement {
  if (root) act(() => root!.unmount());
  container?.remove();
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(el));
  return container;
}
beforeEach(() => {
  stubBridge();
  useVisRuntime.setState({ laeufe: {}, verlauf: {}, laufZaehler: {} });
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.unstubAllGlobals();
});

/** Das Urteil, das die Kachel ZEIGT — aus ihrer Klasse gelesen, nicht gerechnet. */
function kachelUrteil(qa: JobQa): string {
  const c = mount(<BildKachel jobId="j" bild="b.png" qa={qa} alt="Bild" />);
  const k = c.querySelector<HTMLElement>('.vis-bild-kachel-qa')!;
  if (k.classList.contains('vis-bild-kachel-qa--ok')) return 'bestanden';
  if (k.classList.contains('vis-bild-kachel-qa--fehl')) return 'durchgefallen';
  if (k.classList.contains('vis-bild-kachel-qa--neutral')) return 'nicht-beurteilbar';
  return `unbekannt (${k.className})`;
}

/** Die Punkte am Verlauf eines echten Render-Knotens, neuestes zuerst. */
function verlaufPunkte(qas: readonly JobQa[]): string[] {
  const { runCommand, doc } = useProject.getState();
  const graphId = (runCommand('vis.graphErstellen', { name: `Echt-${Math.random()}` }).patches[0] as { id: string }).id;
  // Owner-Entscheid 101a: der Verlauf ist zugeklappt die Vorgabe — hier werden seine Daumenbilder geprueft.
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 40, y: 20, params: { verlaufOffen: true } });
  const graph = doc.get<VisGraph>(graphId)!;
  const nodeId = graph.nodes.at(-1)!.id;
  const schluessel = memoKey(evaluiereGraph(doc, graph).renderAuftraege.get(nodeId)!);
  qas.forEach((qa, i) => {
    const lauf: NodeLauf = { status: 'fertig', jobId: `echt-${i}`, bild: 'b.png', qa, memoKey: schluessel, fertigUm: Date.now() };
    act(() => useVisRuntime.getState().setzeLauf(nodeId, lauf));
  });
  const c = mount(<NodeCanvas graphId={graphId} />);
  const punkte = [...c.querySelectorAll<HTMLElement>('[data-testid="render-verlauf-bild"]')].map((d) => d.dataset['urteil'] ?? '');
  const haupt = c.querySelector<HTMLElement>('[data-testid="render-hauptbild-urteil"]')?.dataset['urteil'];
  return [haupt ?? 'kein Abzeichen', ...punkte];
}

describe('Echte Abholer-Ergebnisse (ohne Maskenfelder): Kachel und Verlauf sagen dasselbe', () => {
  for (const [name, qa, soll] of FAELLE) {
    it(`${name}: Kachel = Verlauf = ${soll}`, () => {
      expect(kachelUrteil(qa), 'Kachel').toBe(soll);
      expect(laufUrteil(qa), 'Verlauf (Rechnung)').toBe(soll);
    });
  }

  it('am Knoten: Punkte und Abzeichen tragen das Urteil der Kachel', () => {
    // Reihenfolge der Laeufe: OK, FEHL, NB, FEHL → neuestes zuerst: FEHL, NB, FEHL, OK.
    const [haupt, ...punkte] = verlaufPunkte([ECHT_OK, ECHT_FEHL, ECHT_NB, ECHT_FEHL]);
    expect(punkte).toEqual(['durchgefallen', 'nicht-beurteilbar', 'durchgefallen', 'bestanden']);
    expect(haupt).toBe('durchgefallen');
    expect(punkte).toEqual([ECHT_FEHL, ECHT_NB, ECHT_FEHL, ECHT_OK].map((q) => kachelUrteil(q)));
  });

  it('Treue ohne rho_maske: kein «Grundlage widerrufen» mehr', () => {
    expect(treueText(ECHT_OK)).toBe('keine Gebäude-Zahl geliefert');
    expect(treueText(ECHT_FEHL)).toBe('keine Gebäude-Zahl geliefert — Urteil und Zahl im Grund');
    expect(treueText(ECHT_NB)).toBe('nicht anwendbar — siehe Grund');
    // Der Grund bleibt der Satz des Absenders; ohne Satz kein «zurueckgezogen».
    expect(laufGrund(ECHT_FEHL)).toBe('Geometrie 0.598 gegen 0.65');
    expect(laufGrund(ECHT_OK)).toBe('Ohne Begründung geliefert.');
  });

  it('Inspektor bei «nicht beurteilbar»: nur ein Satz, kein «Bewertung zurückgezogen» dazu', () => {
    const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
    const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'T', nodes: [node], edges: [] };
    const karte: KuratierKartenDaten = { node, quelle: { jobId: 'j1', bild: 'b.png', qa: ECHT_NB }, kur: { markiert: false, verworfen: false } };
    const c = mount(<KuratierInspektor graph={graph} karte={karte} id="V-01" onMarkieren={() => {}} onVerwerfen={() => {}} onInsProjekt={() => {}} />);
    expect(c.textContent).toContain('Nicht beurteilbar — der Grund steht unter «QA-Vorbehalt», keine Wertung.');
    expect(c.textContent).not.toContain('Bewertung zurueckgezogen');
    expect(c.textContent).not.toContain('Bewertung zurückgezogen');
  });

  it('Kamera-Eintrag mit status not_measured heisst «nicht gemessen», nicht «ohne QA»', () => {
    const zeilen = kameraQaZeilen([
      { kamera: 'cam-01', geometry: { status: 'not_measured', threshold: 0.65, passed: false, method: 'm' } },
      { kamera: 'cam-02', geometry: { status: 'not_applicable', threshold: 0.65, passed: false, method: 'm' } },
      { kamera: 'cam-03' },
      { kamera: 'cam-04', geometry: { geometry_fidelity: 0.8, threshold: 0.65, passed: true, method: 'm' } },
    ] as never);
    expect(zeilen.map(kameraQaText)).toEqual(['nicht gemessen', 'nicht zuständig', 'ohne QA', 'bestanden']);
  });
});
