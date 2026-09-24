import { beforeEach, describe, expect, it } from 'vitest';
import { KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { nodeHinzufuegen } from '../src/modules/vis/vis-graph-aktionen';
import { NODE_W, basisNodeHoehe } from '../src/modules/vis/NodeCanvas';

/**
 * A21 · EIN NEU GESETZTER KNOTEN STEHT GANZ IM BILD (17.09.2026).
 *
 * ── Woher der Fall kommt ─────────────────────────────────────────────────
 *
 * Posten 1 und 16 aus `docs/RENDERPROJEKT-2026-09-10/73-BEFUNDE-OHNE-
 * BESITZER.md`. Bis A21 setzte `nodeHinzufuegen()` die LINKE OBERE ECKE des
 * neuen Knotens auf die Sichtmitte. Die viewBox bildet die Sichtmitte auf die
 * Bildschirmmitte ab — dem Knoten stand also nur die untere Fensterhälfte zur
 * Verfügung, und ein Knoten, der höher ist als die halbe Leinwand, konnte
 * strukturell nie ganz sichtbar sein.
 *
 * Am laufenden Bild gemessen (eigener Bau, eigener kopfloser Chromium auf
 * CDP 9251, frischer Render-Knoten, Kartenhöhe 580 px), VORHER:
 *
 *   Fenster      Karte y            ragte unten hinaus   Elemente draussen
 *   1400×900     450 … 1030         130 px               4 von 20
 *   1600×900     450 … 1030         130 px               4 von 20
 *   1280×800     400 …  980         180 px               6 von 20
 *   1366×768     384 …  964         196 px               7 von 20
 *   1920×1080    540 … 1120          40 px               0 von 20
 *
 * Bei keiner der fünf Grössen lag die Karte ganz im Fenster.
 *
 * ── Was diese Probe prüft, und warum sie widersprechen kann ──────────────
 *
 * Die drei bestehenden Wächter decken den Fall NICHT ab:
 *
 * - `p-b69-knotenplatz-ausserhalb-hinweis.test.tsx` prüft nur die MITTE des
 *   Knotens gegen den Ausschnitt. Genau darum war der Befund unsichtbar: bei
 *   Ecken-Verankerung lag die Mitte noch im Bild, während die untere Hälfte
 *   des Knotens längst unter dem Fensterrand hing.
 * - `a15-render-knotenhoehe.test.tsx` hält die HÖHE des Körpers klein; wo der
 *   Knoten landet, sieht es nicht.
 * - `p-knotenfeld-knotenplatz.test.ts` hält die Knoten auseinander; ob sie im
 *   Bild liegen, sieht es nicht.
 *
 * Diese Probe prüft die ganze Kiste (x…x+NODE_W, y…y+Höhe) gegen das
 * sichtbare Weltrechteck.
 *
 * ROT VOR GRÜN, nachgestellt am 17.09.2026 (Schnitt: `START_X = anker.x`,
 * `START_Y = anker.y` — der alte Anker; Skript mit Hash-Vorprüfung und
 * `trap`-Rückstellung, danach `sha256sum` gleich):
 *
 *   Fall 1  ROT — «1400×900: Unterkante unter dem Fensterrand: expected 880
 *                  to be less than or equal to 750»
 *   Fall 2  ROT — «expected 2100 to be 2000»
 *   Fall 3  grün (er beschreibt den ALTEN Zustand — er MUSS grün bleiben)
 *   Fall 4  grün — und das ist kein Versehen: die anderen Knotenarten sind so
 *           niedrig, dass sie auch mit dem alten Anker ins Bild passten. Fall 4
 *           kann diese Änderung nicht widerlegen; er bewacht, dass eine
 *           künftig wachsende Knotenart nicht still hinausfällt.
 *   Fall 5  grün — ebenfalls kein Falsifikator, und genau das ist der Befund
 *           von Posten 16: die B69-Prüfung sieht nur die MITTE des Knotens,
 *           und die lag auch mit dem alten Anker noch im Bild, während die
 *           untere Hälfte längst draussen hing. Fall 5 hält fest, dass die
 *           Meldung durch A21 nicht lauter wird — mehr behauptet er nicht.
 *
 * Zwei von fünf Fällen werden rot. Die drei anderen sagen ausdrücklich, dass
 * sie es nicht werden können — eine Probe, die nicht widersprechen kann, ist
 * keine Probe, und eine, die es verschweigt, ist schlimmer.
 *
 * Keine Zahl unten ist eingetippt: Breite und Höhe kommen aus denselben
 * Quellen, die auch `nodeHinzufuegen()` benutzt (`NODE_W`, `basisNodeHoehe`).
 */

/**
 * Die fünf Fenstergrössen, an denen A21 am laufenden Bild gemessen hat. Der
 * NodeCanvas füllt die Fensterhöhe (gemessen: `canvas y 0 … 900` bei einem
 * 900 px hohen Fenster), und der Standard-Blick ist `{cx: 560, cy: 300,
 * scale: 1}` (`NodeCanvas.tsx`s `useState`) — das sichtbare Weltrechteck ist
 * bei Skala 1 also genau das Fenster, um (560/300) zentriert.
 */
const FENSTER = [
  { b: 1400, h: 900 },
  { b: 1600, h: 900 },
  { b: 1280, h: 800 },
  { b: 1920, h: 1080 },
  { b: 1366, h: 768 },
] as const;

const SICHT = { x: 560, y: 300 };

function rechteckFuer(f: { b: number; h: number }): { x: number; y: number; b: number; h: number } {
  return { x: SICHT.x - f.b / 2, y: SICHT.y - f.h / 2, b: f.b, h: f.h };
}

function neuerGraph(name: string): string {
  const { runCommand } = useProject.getState();
  return (runCommand('vis.graphErstellen', { name }).patches[0] as { id: string }).id;
}

function setzeSicht(f: { b: number; h: number }): void {
  const r = rechteckFuer(f);
  useVisRuntime.setState({ canvasSichtMitte: { ...SICHT }, canvasSichtRechteck: r });
}

beforeEach(() => {
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

describe('A21 — der erste Knoten liegt GANZ im sichtbaren Ausschnitt, nicht nur mit seiner Mitte', () => {
  it('Fall 1: Render-Knoten bei allen fünf gemessenen Fenstergrössen vollständig im Bild', () => {
    const hoehe = basisNodeHoehe('render');
    for (const f of FENSTER) {
      const doc = new KosmoDoc();
      useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
      setzeSicht(f);
      const gid = neuerGraph(`A21 ${f.b}x${f.h}`);
      nodeHinzufuegen(gid, 'render');

      const n = useProject.getState().doc.get<VisGraph>(gid)!.nodes[0]!;
      const r = rechteckFuer(f);
      // Voraussetzung des Falls, mitgeprüft statt geglaubt: der Knoten passt
      // überhaupt in den Ausschnitt. Wäre er höher, könnte KEINE Platzierung
      // ihn ganz zeigen — dann wäre ein grünes «liegt ganz drin» eine
      // Unwahrheit über die Platzierung.
      expect(hoehe, `Knoten höher als das Fenster ${f.b}×${f.h}`).toBeLessThanOrEqual(f.h);
      expect(NODE_W, `Knoten breiter als das Fenster ${f.b}×${f.h}`).toBeLessThanOrEqual(f.b);

      expect(n.x, `${f.b}×${f.h}: linke Kante links aus dem Bild`).toBeGreaterThanOrEqual(r.x);
      expect(n.y, `${f.b}×${f.h}: Oberkante über dem Bild`).toBeGreaterThanOrEqual(r.y);
      expect(n.x + NODE_W, `${f.b}×${f.h}: rechte Kante rechts aus dem Bild`).toBeLessThanOrEqual(r.x + r.b);
      expect(n.y + hoehe, `${f.b}×${f.h}: Unterkante unter dem Fensterrand`).toBeLessThanOrEqual(r.y + r.h);
    }
  });

  it('Fall 2: die MITTE des Knotens sitzt auf der Sichtmitte — nicht seine Ecke', () => {
    // Weit weg vom Weltursprung, damit die Randklemme (`Math.max(20, …)` in
    // `nodeHinzufuegen`) nicht mitredet: dort gilt die Zusicherung exakt.
    const mitte = { x: 2000, y: 1500 };
    useVisRuntime.setState({ canvasSichtMitte: mitte, canvasSichtRechteck: { x: 1000, y: 800, b: 2000, h: 1400 } });
    const gid = neuerGraph('A21 Mitte');
    nodeHinzufuegen(gid, 'render');
    const n = useProject.getState().doc.get<VisGraph>(gid)!.nodes[0]!;
    expect(n.x + NODE_W / 2).toBe(mitte.x);
    expect(n.y + basisNodeHoehe('render') / 2).toBe(mitte.y);
  });

  it('Fall 3: Gegenprobe — die alte Ecken-Verankerung wäre bei genau diesen Grössen rot', () => {
    // Keine zweite Wahrheit, sondern dieselbe Rechnung mit dem ALTEN Anker:
    // damit steht im Test, WAS sich geändert hat, und Fall 1 ist kein
    // Zufallstreffer einer Fenstergrösse. Rechnet jemand die Knotenhöhe
    // wieder klein genug, fällt dieser Fall von selbst weg — dann ist er
    // rot und muss neu begründet werden, statt still zu bestehen.
    const hoehe = basisNodeHoehe('render');
    const rot = FENSTER.filter((f) => {
      const r = rechteckFuer(f);
      const alteUnterkante = Math.max(20, SICHT.y) + hoehe; // alter Anker: y = Sichtmitte
      return alteUnterkante > r.y + r.h;
    });
    expect(rot.map((f) => `${f.b}x${f.h}`)).toEqual(['1400x900', '1600x900', '1280x800', '1920x1080', '1366x768']);
  });

  it('Fall 4: auch die anderen Knotenarten landen ganz im Bild (nicht nur der grosse Render-Knoten)', () => {
    for (const typ of ['modell', 'material', 'prompt', 'stimmung', 'kombinierer', 'kamera', 'vergleich', 'aufnahme']) {
      const doc = new KosmoDoc();
      useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
      setzeSicht(FENSTER[4]!); // die kleinste gemessene Grösse, 1366×768
      const gid = neuerGraph(`A21 ${typ}`);
      nodeHinzufuegen(gid, typ);
      const n = useProject.getState().doc.get<VisGraph>(gid)!.nodes[0]!;
      const r = rechteckFuer(FENSTER[4]!);
      const h = basisNodeHoehe(typ);
      expect(n.x, `${typ}: links raus`).toBeGreaterThanOrEqual(r.x);
      expect(n.y, `${typ}: oben raus`).toBeGreaterThanOrEqual(r.y);
      expect(n.x + NODE_W, `${typ}: rechts raus`).toBeLessThanOrEqual(r.x + r.b);
      expect(n.y + h, `${typ}: unten raus`).toBeLessThanOrEqual(r.y + r.h);
    }
  });

  it('Fall 5: die B69-Meldung bleibt der Ausnahmefall — der erste Knoten löst sie bei keiner der fünf Grössen aus', () => {
    // Dieselbe Rechnung, die `nodeHinzufuegen` für die Meldung anstellt
    // (Mitte gegen Rechteck) — hier nur nachgezählt, damit die Aussage
    // «seltener, nicht öfter» eine Zahl hat statt einer Behauptung.
    const hoehe = basisNodeHoehe('render');
    let melden = 0;
    for (const f of FENSTER) {
      const doc = new KosmoDoc();
      useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
      setzeSicht(f);
      const gid = neuerGraph(`A21 B69 ${f.b}`);
      nodeHinzufuegen(gid, 'render');
      const n = useProject.getState().doc.get<VisGraph>(gid)!.nodes[0]!;
      const r = rechteckFuer(f);
      const mx = n.x + NODE_W / 2;
      const my = n.y + hoehe / 2;
      if (mx < r.x || mx > r.x + r.b || my < r.y || my > r.y + r.h) melden++;
    }
    expect(melden).toBe(0);
  });
});
