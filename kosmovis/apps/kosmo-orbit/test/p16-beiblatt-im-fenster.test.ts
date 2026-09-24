import { beforeEach, describe, expect, it } from 'vitest';
import { KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { nodeHinzufuegen } from '../src/modules/vis/vis-graph-aktionen';
import {
  BEIBLATT_H_NENN,
  BEIBLATT_W,
  NODE_W,
  basisNodeHoehe,
  beiblattFeld,
  beiblattPlatz,
} from '../src/modules/vis/NodeCanvas';

/**
 * P16 · DAS BEIBLATT LIEGT GANZ IM FENSTER (17.09.2026).
 *
 * ── Woher der Fall kommt ─────────────────────────────────────────────────
 *
 * Posten 16 aus `docs/RENDERPROJEKT-2026-09-10/73-BEFUNDE-OHNE-BESITZER.md`,
 * zurueckgestuft vom unabhaengigen Pruefer: zugeklappt hielt der Render-Knoten
 * seine Zusage, AUFGEKLAPPT nicht. Am laufenden Bild gemessen (eigener Bau,
 * eigener kopfloser Chromium auf CDP 9293, frischer Render-Knoten), VORHER:
 *
 *   Fenster      Karte zu    Karte auf   draussen zu   draussen auf
 *   1280x720     230x580     230x1099    0 von 10      7 von 15
 *   1366x768     230x580     230x1099    0 von 10      7 von 15
 *   1440x900     230x580     230x1099    0 von 10      7 von 15
 *   1680x1050    230x580     230x1099    0 von 10      7 von 15
 *   1920x1080    230x580     230x1099    0 von 10      7 von 15
 *
 * Draussen lagen jedes Mal dieselben sieben: die fuenf Felder des
 * Auftrags-Formulars und die beiden Schalter, die das Formular nach unten
 * schiebt.
 *
 * ── Warum es kein Wachsen sein konnte ────────────────────────────────────
 *
 * Die Karte waechst beim Aufklappen nur nach unten (ihr `y` bleibt stehen).
 * Bei 1280x720 steht sie zugeklappt bei y 80…660 — 60 px Luft. Der Zusatz
 * braucht 519 px. Selbst wenn man ihn in Abschnitte teilte, waere der
 * kleinste sinnvolle Abschnitt (das Formular allein) 160 px gross und passte
 * nicht. Und selbst symmetrisches Wachsen um die Kartenmitte endete bei rund
 * 700 px: 1099 px Inhalt passen in kein gemessenes Fenster.
 *
 * Seit P16 waechst die Karte gar nicht mehr; der Zusatz steht in einem
 * BEIBLATT neben ihr, das sich am FENSTER bemisst.
 *
 * ── Was diese Probe kann, und was nicht ──────────────────────────────────
 *
 * KANN NICHT: die Pixel messen. jsdom hat kein Layout. Die Zahlen oben und
 * die vier Randreserven in `NodeCanvas.tsx` stammen aus Messungen am
 * laufenden Bild.
 *
 * KANN: die RECHNUNG pruefen, die das Beiblatt platziert — an genau den fuenf
 * Fenstergroessen, an denen gemessen wurde, mit einem Knoten, den
 * `nodeHinzufuegen()` selbst gesetzt hat. Keine Zahl unten ist eingetippt:
 * Breite, Hoehe und Feld kommen aus denselben Quellen, die auch die
 * Oberflaeche benutzt.
 *
 * ROT VOR GRUEN, wirklich gefahren am 17.09.2026 — jeder Schnitt einzeln, mit
 * Hash-Vorpruefung, Rueckstellung im `finally` und `sha256sum`-Gleichheit
 * danach (Skript ohne Rohr um den Lauf):
 *   - eine Zusatzzeile um 200 px erhoeht  → Fall 3 rot (und A15 Budget C).
 *   - `BEIBLATT_ABSTAND` auf -220         → Fall 2 UND Fall 4 rot.
 *   - die Links-Ausweiche entfernt        → Fall 4 rot.
 *   - die Schluss-Klemme in `beiblattPlatz` entfernt → Fall 7 rot.
 *
 * EIN SCHNITT BLIEB ZUERST GRUEN, und das steht hier, statt weggelassen zu
 * werden: die Schluss-Klemme zu entfernen liess Fall 1…6 gruen. Nachgesehen
 * statt gemeldet — bei einem frisch gesetzten Knoten greift der erste Zweig
 * («rechts daneben passt»), die Schluss-Klemme kommt im Pruefweg gar nicht
 * vor. Es war an einer Schraube gedreht worden, die der Pruefweg nicht
 * anfasst. Fall 7 ist daraufhin NACHGETRAGEN und dreht an ihr.
 *
 * WAS DIESE PROBE NICHT BEWEIST: dass die vier Randreserven RICHTIG sind.
 * Sie prueft gegen `beiblattFeld()` — dieselbe Rechnung, die das Beiblatt
 * selbst benutzt. Waeren die Reserven falsch, blieben alle Faelle gruen. Die
 * Reserven sind am laufenden Bild gemessen (`NodeCanvas.tsx`, Kopfkommentar
 * der BEIBLATT-Konstanten), und die Gegenprobe dazu ist die Messung an der
 * Oberflaeche: 15 von 15 Bedienelementen treffbar bei allen fuenf Groessen,
 * `elementFromPoint` auf jede Mitte, echter Klick auf zwei davon.
 *
 * NICHT GEPRUEFT, ausdruecklich: sind ZWEI Render-Knoten zugleich
 * aufgeklappt, koennen sich ihre Beiblaetter ueberlagern. Gemessen und
 * bewacht ist der Fall, den ein Mensch ausloest — ein Knoten.
 */

/** Die fuenf Fenstergroessen des unabhaengigen Pruefers — dieselben, an denen
 *  P16 vorher und nachher am Bild gemessen hat. */
const FENSTER = [
  { b: 1280, h: 720 },
  { b: 1366, h: 768 },
  { b: 1440, h: 900 },
  { b: 1680, h: 1050 },
  { b: 1920, h: 1080 },
] as const;

/** Gemessen: `.vis-canvas-wrap` fuellt das Fenster (x 0, y 0, w/h = Fenster,
 *  bei 1280x720 UND 1920x1080). Der Standard-Blick ist `{cx: 560, cy: 300,
 *  scale: 1}` (`NodeCanvas.tsx`s `useState`). */
const SICHT = { cx: 560, cy: 300, scale: 1 };

function rechteckFuer(f: { b: number; h: number }): { x: number; y: number; b: number; h: number } {
  return { x: SICHT.cx - f.b / 2, y: SICHT.cy - f.h / 2, b: f.b, h: f.h };
}

/** Die Bildschirmkiste der Karte — dieselbe Umrechnung, die `beiblattPlatz`
 *  benutzt, hier fuer die Karte statt fuer das Beiblatt. */
function karteAufSchirm(
  n: { x: number; y: number },
  flaeche: { w: number; h: number },
): { links: number; oben: number; rechts: number; unten: number } {
  const links = flaeche.w / 2 + (n.x - SICHT.cx) * SICHT.scale;
  const oben = flaeche.h / 2 + (n.y - SICHT.cy) * SICHT.scale;
  return { links, oben, rechts: links + NODE_W * SICHT.scale, unten: oben + basisNodeHoehe('render') * SICHT.scale };
}

function frischerRenderKnoten(f: { b: number; h: number }): { x: number; y: number } {
  const doc = new KosmoDoc();
  useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ canvasSichtMitte: { x: SICHT.cx, y: SICHT.cy }, canvasSichtRechteck: rechteckFuer(f) });
  const { runCommand } = useProject.getState();
  const gid = (runCommand('vis.graphErstellen', { name: `P16 ${f.b}x${f.h}` }).patches[0] as { id: string }).id;
  nodeHinzufuegen(gid, 'render');
  const n = useProject.getState().doc.get<VisGraph>(gid)!.nodes[0]!;
  return { x: n.x, y: n.y };
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

describe('P16 — das Beiblatt des aufgeklappten Render-Knotens liegt bei allen fuenf gemessenen Fenstergroessen im Bild', () => {
  it('Fall 1: das Beiblatt liegt ganz im Feld — bei allen fuenf Groessen', () => {
    for (const f of FENSTER) {
      const flaeche = { w: f.b, h: f.h };
      const n = frischerRenderKnoten(f);
      const feld = beiblattFeld(flaeche);
      const p = beiblattPlatz(n, SICHT, flaeche);

      expect(p.links, `${f.b}x${f.h}: linke Kante im Chrome-Streifen links`).toBeGreaterThanOrEqual(feld.links);
      expect(p.links + BEIBLATT_W, `${f.b}x${f.h}: rechte Kante im Chrome-Streifen rechts`).toBeLessThanOrEqual(
        feld.rechts,
      );
      expect(p.oben, `${f.b}x${f.h}: Oberkante unter der Insel-Kopfzeile`).toBeGreaterThanOrEqual(feld.oben);
      expect(p.oben + p.maxHoehe, `${f.b}x${f.h}: Unterkante ueber dem Grundstreifen`).toBeLessThanOrEqual(feld.unten);
    }
  });

  it('Fall 2: das Beiblatt deckt die Karte nicht zu — sonst waere der Klappknopf darunter', () => {
    for (const f of FENSTER) {
      const flaeche = { w: f.b, h: f.h };
      const n = frischerRenderKnoten(f);
      const p = beiblattPlatz(n, SICHT, flaeche);
      const karte = karteAufSchirm(n, flaeche);

      const ueberlappt =
        p.links < karte.rechts &&
        p.links + BEIBLATT_W > karte.links &&
        p.oben < karte.unten &&
        p.oben + p.maxHoehe > karte.oben;
      expect(
        ueberlappt,
        `${f.b}x${f.h}: Beiblatt (${p.links}…${p.links + BEIBLATT_W}) liegt auf der Karte (${karte.links}…${karte.rechts})`,
      ).toBe(false);
    }
  });

  it('Fall 3: das Beiblatt muss bei keiner der fuenf Groessen rollen', () => {
    // Rollen waere erlaubt (es liegt ausserhalb des `<svg>`, sein Rad
    // erreicht den Zoom der Leinwand nicht) — aber es ist der Riegel fuer
    // noch kleinere Fenster, nicht der Normalfall. Waechst der Zusatz ueber
    // das kleinste gemessene Fenster hinaus, sagt dieser Fall es an, statt
    // dass ein Rollbalken still erscheint.
    for (const f of FENSTER) {
      const p = beiblattPlatz(frischerRenderKnoten(f), SICHT, { w: f.b, h: f.h });
      expect(p.maxHoehe, `${f.b}x${f.h}: Beiblatt muesste rollen`).toBe(BEIBLATT_H_NENN);
    }
  });

  it('Fall 4: steht die Karte am rechten Feldrand, weicht das Beiblatt nach LINKS aus statt hinauszuragen', () => {
    const flaeche = { w: 1280, h: 720 };
    const feld = beiblattFeld(flaeche);
    // Ein Knoten so weit rechts, dass rechts neben ihm kein Platz mehr ist.
    const n = { x: SICHT.cx + flaeche.w / 2 - NODE_W - 10, y: SICHT.cy };
    const p = beiblattPlatz(n, SICHT, flaeche);
    const karte = karteAufSchirm(n, flaeche);

    expect(p.links + BEIBLATT_W, 'ragt rechts hinaus').toBeLessThanOrEqual(feld.rechts);
    expect(p.links + BEIBLATT_W, 'nicht nach links ausgewichen').toBeLessThanOrEqual(karte.links);
    expect(p.links, 'ragt links hinaus').toBeGreaterThanOrEqual(feld.links);
  });

  it('Fall 5: Gegenprobe — das Feld ist wirklich kleiner als das Fenster, sonst prueft Fall 1 nichts', () => {
    // Eine Probe gegen ein Feld, das zufaellig das ganze Fenster waere,
    // koennte die Chrome-Reserven nie fangen. Diese Zeile haelt fest, dass
    // alle vier Reserven groesser als null sind — sie sind am Bild gemessen
    // (`NodeCanvas.tsx`, Kopfkommentar der BEIBLATT-Konstanten).
    for (const f of FENSTER) {
      const feld = beiblattFeld({ w: f.b, h: f.h });
      expect(feld.links).toBeGreaterThan(0);
      expect(feld.oben).toBeGreaterThan(0);
      expect(feld.rechts).toBeLessThan(f.b);
      expect(feld.unten).toBeLessThan(f.h);
    }
  });

  it('Fall 7: auch eine aus dem Bild gezogene Karte laesst ihr Beiblatt nicht hinauswandern', () => {
    // NACHGETRAGEN, weil ein Schnitt stumpf war (17.09.2026): die
    // Schluss-Klemme in `beiblattPlatz` zu entfernen liess Fall 1…6 GRUEN.
    // Nachgesehen statt «der Test ist blind» gemeldet: bei einem frisch
    // gesetzten Knoten greift der erste Zweig (rechts daneben passt), die
    // Schluss-Klemme kommt im Pruefweg gar nicht vor. Sie traegt erst, wenn
    // die Karte WEIT links oder rechts steht — und dorthin kann ein Mensch
    // sie ziehen. Dieser Fall dreht genau an dieser Schraube; mit ihm ist
    // derselbe Schnitt rot.
    const flaeche = { w: 1280, h: 720 };
    const feld = beiblattFeld(flaeche);
    const weitDraussen = [
      { name: 'weit links', x: SICHT.cx - 4000, y: SICHT.cy },
      { name: 'weit rechts', x: SICHT.cx + 4000, y: SICHT.cy },
      { name: 'weit oben', x: SICHT.cx, y: SICHT.cy - 4000 },
      { name: 'weit unten', x: SICHT.cx, y: SICHT.cy + 4000 },
    ];
    for (const k of weitDraussen) {
      const p = beiblattPlatz(k, SICHT, flaeche);
      expect(p.links, `${k.name}: links raus`).toBeGreaterThanOrEqual(feld.links);
      expect(p.links + BEIBLATT_W, `${k.name}: rechts raus`).toBeLessThanOrEqual(feld.rechts);
      expect(p.oben, `${k.name}: oben raus`).toBeGreaterThanOrEqual(feld.oben);
      expect(p.oben + p.maxHoehe, `${k.name}: unten raus`).toBeLessThanOrEqual(feld.unten);
    }
  });

  it('Fall 6: die Karte bleibt beim Aufklappen gleich hoch — das ist der ganze Umbau', () => {
    // Die frueher entscheidende Zahl: 580 zugeklappt, 1099 aufgeklappt.
    // Heute gibt es nur noch EINE Kartenhoehe, und sie passt in das kleinste
    // gemessene Fenster.
    expect(basisNodeHoehe('render')).toBeLessThanOrEqual(FENSTER[0]!.h);
    // Und der Zusatz ist immer noch da — er ist nur woanders. Waere er
    // gestrichen, waere diese Zeile rot, und genau das war verboten.
    expect(BEIBLATT_H_NENN).toBeGreaterThan(400);
  });
});
