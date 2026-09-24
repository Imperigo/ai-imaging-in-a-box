// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KMeldungen } from '@kosmo/ui';
import { KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { nodeHinzufuegen } from '../src/modules/vis/vis-graph-aktionen';
import { basisNodeHoehe, NODE_W } from '../src/modules/vis/NodeCanvas';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * B69 (`docs/UI-UX-2026-09-07-B69-ENTSCHEID-HINWEIS.md`) — Owner-Entscheid
 * woertlich «b69 hinweis anzeigen»: ein per Spiral-Platzsuche eingefuegter
 * Knoten kann ausserhalb des sichtbaren Ausschnitts landen (`klemme` haelt nur
 * eine UNTERE Schranke, keine obere — `vis-graph-aktionen.ts`). Ausdruecklich
 * NICHT gebaut: eine obere Klemme oder ein automatisches Mitfuehren der
 * Leinwand (Blatt §2). Stattdessen meldet `nodeHinzufuegen()` es ueber den
 * bestehenden Meldeweg (`@kosmo/ui`s `melde()`), sobald der gefundene Platz
 * ausserhalb des gespiegelten Weltrechtecks (`canvasSichtRechteck`,
 * `vis-runtime.ts`) liegt.
 *
 * Testmuster identisch zu `p-kamera-vorschlagen-sagt-es.test.tsx` (Modul-
 * Singleton `@kosmo/ui`s Meldungs-Speicher ohne Reset — Fake-Timer +
 * `advanceTimersByTime` im `afterEach`).
 *
 * Die acht-Knoten-Positionen unten (`render`, Start immer am View-Mittelpunkt
 * 560/300 — Fallback, wenn kein `NodeCanvas` gemountet hat) sind gegen die
 * echte Spiral-Logik gemessen, nicht angenommen.
 *
 * A15 (17.09.2026) — ZWEI Berichtigungen an dieser Datei, beide durch eine
 * echte Aenderung ausgeloest, keine Anpassung an ein unbequemes Ergebnis:
 *
 * 1. Die Knotenhoehe stand hier als Zahl (`468`). Sie wurde still falsch, als
 *    der Render-Koerper wuchs: die Pruefung rechnete mit 468, die Anwendung
 *    mit 1016. Die Gegenprobe «genau einer liegt ausserhalb» meldete weiter
 *    gruen, waehrend die Meldung in Wahrheit bei ZWEI Knoten kam. Steht statt
 *    der Zahl `basisNodeHoehe('render')`, kann das nicht wiederkehren — die
 *    Probe rechnet dann mit derselben Hoehe wie der geprueste Code.
 * 2. Die Spirale legt die Knoten bei kleinerer Knotenhoehe anders ab: statt
 *    (560,804) als siebten liegt jetzt (1520,300) dort und (560,912) als
 *    achter. Das alte Rechteck (h: 1200) liess damit ZWEI Mitten heraus. Das
 *    Rechteck ist auf h: 1400 gezogen, damit wieder GENAU der eine Knoten bei
 *    x=1520 herausfaellt — die Aussage des Falls («die Meldung kommt einmal,
 *    nicht je Knoten») bleibt unveraendert, und ihre Voraussetzung wird
 *    unmittelbar darunter nachgezaehlt statt geglaubt.
 *
 * A21 (17.09.2026) — DIE VORAUSSETZUNG DIESER DATEI HAT SICH GEAENDERT, ihre
 * Zusicherungen NICHT. `nodeHinzufuegen()` setzt seit Posten 1/16
 * (`docs/RENDERPROJEKT-2026-09-10/73-BEFUNDE-OHNE-BESITZER.md`) die MITTE des
 * Knotens auf die Sichtmitte statt seiner linken oberen Ecke. Was das hier
 * aendert:
 *
 * - Die acht Spiral-Positionen wandern um (-100, -290) und werden von der
 *   Randklemme (`Math.max(20, …)`) auf y=20 gehoben: (460,20) (700,20)
 *   (220,20) (940,20) (1180,20) (1420,20) (460,658) (1660,20). Ausserhalb von
 *   `b:1650/h:1400` liegt weiterhin GENAU EINER — jetzt der bei x=1660
 *   (Mitte 1760) statt der bei x=1520. Die Zahl im Fall ist nicht angepasst
 *   worden; sie stimmt unveraendert, und der Fall zaehlt sie selbst nach.
 * - Die Gegenprobe (zweiter Fall) ist nicht nur weiter gruen, sie ist
 *   STRENGER wahr geworden: beide Knoten liegen jetzt GANZ im 1200x700-
 *   Ausschnitt — vorher lag keiner der beiden ganz darin, nur ihre Mitten.
 *   Bewacht wird diese staerkere Aussage in
 *   `test/a21-knotenplatz-ganz-im-bild.test.ts`; hier bleibt es bei «keine
 *   Meldung», damit diese Datei genau eine Sache prueft.
 *
 * Unveraendert und ausdruecklich NICHT gebaut, auch von A21 nicht: eine obere
 * Klemme und ein automatisches Mitfuehren der Leinwand. Der Anker wandert,
 * der Ausschnitt gehoert weiter dem Menschen.
 */

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function montiere(): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<KMeldungen />);
  });
}

function meldungsTexte(): string[] {
  return [...document.body.querySelectorAll('.k-meldung-text')].map((e) => e.textContent ?? '');
}

function neuerGraph(): string {
  const { runCommand } = useProject.getState();
  return (runCommand('vis.graphErstellen', { name: 'B69' }).patches[0] as { id: string }).id;
}

beforeEach(() => {
  vi.useFakeTimers();
  const doc = new KosmoDoc();
  useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({
    aktiverGraphId: null,
    aufnahmen: {},
    gespeicherteAnsichten: {},
    reviewPins: {},
    laeufe: {},
    canvasSichtMitte: null,
    canvasSichtRechteck: null,
  });
});

afterEach(() => {
  act(() => {
    vi.advanceTimersByTime(9000);
  });
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
  vi.useRealTimers();
});

describe('B69 — «Hinweis anzeigen», wenn ein neuer Knoten ausserhalb des sichtbaren Ausschnitts landet', () => {
  it('acht Knoten hintereinander, einer davon ausserhalb — Hinweis erscheint genau einmal (nicht je Knoten)', () => {
    montiere();
    // Gemessenes Weltrechteck, das GENAU 7 der 8 Spiral-Positionen einschliesst
    // (seit A21 liegt der eine bei x=1660 — seine Mitte 1760 fällt allein aus
    // `b:1650` heraus). Kein geratener Bildschirm — die Prüfung selbst liest
    // in der App IMMER `canvasSichtRechteck` aus `vis-runtime.ts`, hier nur
    // von Hand gesetzt, weil kein `NodeCanvas` gemountet ist.
    useVisRuntime.setState({ canvasSichtRechteck: { x: -40, y: -50, b: 1650, h: 1400 } });
    const gid = neuerGraph();

    act(() => {
      for (let i = 0; i < 8; i++) nodeHinzufuegen(gid, 'render');
    });

    const graph = useProject.getState().doc.get<VisGraph>(gid)!;
    expect(graph.nodes).toHaveLength(8);
    // Gegenprobe zur Rechteck-Annahme: wirklich genau EIN Knoten liegt
    // ausserhalb (sonst wäre "genau einmal" unten kein Beleg für die
    // Melde-Logik, sondern ein Zufallstreffer des gewählten Rechtecks).
    const rechteck = { x: -40, y: -50, b: 1650, h: 1400 };
    // Breite und Hoehe kommen aus DEMSELBEN Ort wie in `nodeHinzufuegen`
    // (`NODE_W`, `basisNodeHoehe`) — eine zweite, handgepflegte Zahl hier war
    // genau der Fehler, den A15 gefunden hat.
    const ausserhalb = graph.nodes.filter((n) => {
      const mx = n.x + NODE_W / 2;
      const my = n.y + basisNodeHoehe(n.typ) / 2;
      return mx < rechteck.x || mx > rechteck.x + rechteck.b || my < rechteck.y || my > rechteck.y + rechteck.h;
    });
    expect(ausserhalb).toHaveLength(1);

    const texte = meldungsTexte();
    expect(texte).toHaveLength(1);
    expect(texte[0]).toMatch(/angelegt/);
    expect(texte[0]).toMatch(/ausserhalb des sichtbaren Ausschnitts/);
    expect(texte[0]).toMatch(/Einpassen/);
  });

  it('Gegenprobe: zwei Knoten, beide im sichtbaren Ausschnitt — keine Meldung', () => {
    montiere();
    // Dieselbe Rechteckgrösse, die eine unbewegte NodeCanvas-Standardfläche
    // (1200×700, Skala 1) um den View-Mittelpunkt (560/300) ergäbe.
    //
    // A15: DIESER Fall ist der Massstab fuer die Knotenhoehe. Ein Knoten, der
    // hoeher ist als der Ausschnitt, faellt strukturell IMMER heraus und
    // meldet «liegt ausserhalb». Solange dieser Fall gruen ist, ist die
    // Meldung wieder das, was sie sein soll: der Ausnahmefall.
    //
    // A21: Bis hierhin stand an dieser Stelle die Begruendung «der neue
    // Knoten wird mit seiner LINKEN OBEREN Ecke auf die Sichtmitte gesetzt,
    // seine Mitte liegt also eine halbe Knotenhoehe darunter». Genau diese
    // Verankerung war der Befund (Posten 1/16) und ist ersetzt: die MITTE des
    // Knotens sitzt jetzt auf der Sichtmitte. Der Massstab wird dadurch nicht
    // milder, sondern schaerfer — gemessen liegen beide Knoten dieses Falls
    // seither GANZ im 1200x700-Ausschnitt (vorher keiner der beiden).
    useVisRuntime.setState({ canvasSichtRechteck: { x: -40, y: -50, b: 1200, h: 700 } });
    const gid = neuerGraph();

    act(() => {
      nodeHinzufuegen(gid, 'render');
      nodeHinzufuegen(gid, 'render');
    });

    const graph = useProject.getState().doc.get<VisGraph>(gid)!;
    expect(graph.nodes).toHaveLength(2);
    expect(meldungsTexte()).toEqual([]);
  });

  it('Zoom-Fall: stark verkleinerter Ausschnitt — schon der ERSTE Knoten landet ausserhalb, die Meldung kommt trotzdem (kein geratenes Fenstermass)', () => {
    montiere();
    // Ein winziges Weltrechteck, wie es starkes Hineinzoomen ergäbe
    // (`w = flaeche.w / view.scale` — bei hohem `scale` sehr klein). Es
    // enthält den View-Mittelpunkt (560/300) NICHT — der allererste Knoten
    // (immer exakt am View-Mittelpunkt, keine Kollision möglich) landet damit
    // schon beim ersten Aufruf ausserhalb.
    useVisRuntime.setState({ canvasSichtRechteck: { x: 0, y: 0, b: 50, h: 50 } });
    const gid = neuerGraph();

    act(() => nodeHinzufuegen(gid, 'render'));

    const graph = useProject.getState().doc.get<VisGraph>(gid)!;
    expect(graph.nodes).toHaveLength(1);
    const texte = meldungsTexte();
    expect(texte).toHaveLength(1);
    expect(texte[0]).toMatch(/ausserhalb des sichtbaren Ausschnitts/);
  });

  it('Ohne bekanntes Sichtrechteck (kein NodeCanvas gemountet, `canvasSichtRechteck` bleibt `null`) — keine Meldung statt eines geratenen Hinweises', () => {
    montiere();
    // canvasSichtRechteck bleibt der beforeEach-Default: null.
    const gid = neuerGraph();

    act(() => {
      for (let i = 0; i < 8; i++) nodeHinzufuegen(gid, 'render');
    });

    const graph = useProject.getState().doc.get<VisGraph>(gid)!;
    expect(graph.nodes).toHaveLength(8);
    expect(meldungsTexte()).toEqual([]);
  });
});
