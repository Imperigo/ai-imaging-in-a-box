// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { KosmoDoc, type VisGraph } from '@kosmo/kernel';
import {
  BEIBLATT_H_NENN,
  basisNodeHoehe,
  beiblattFeld,
  NodeCanvas,
  RENDER_ZEILEN,
  RENDER_ZEILEN_ZUSATZ,
  zeilenHoehe,
} from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';

/**
 * A15 · DER WAECHTER UEBER DER KNOTENHOEHE (17.09.2026).
 *
 * ── Warum es diese Datei gibt ────────────────────────────────────────────
 *
 * Die Hoehe des Render-Koerpers war eine Zahl im Quelltext, und daneben stand
 * die Bitte: «Wer Zeilen hinzufuegt, MISST nach.» Zweimal wurde sie nicht
 * befolgt, und beide Male fiel es niemandem auf, weil ein abgeschnittener
 * Knoten genauso aussieht wie ein fertiger:
 *
 * - Erst lagen rund 93 px alten Inhalts ausserhalb des gezeichneten Rahmens
 *   (419 px Inhalt, 324 angeboten).
 * - Dann kamen sechs Bedienelemente dazu, geschaetzt mit +206; gemessen
 *   brauchten sie 416. Der Bildwerkzeug-Waehler war unerreichbar.
 * - Und als die Zahl endlich am Browser gemessen war (872), war sie zwar
 *   richtig und der Knoten trotzdem kaputt: 872 px Koerper ergeben einen
 *   1016 px hohen Knoten, und das Fenster ist 900 px hoch. Vier von sechs
 *   Bedienelementen lagen unter dem Fensterrand (gemessen am ausgelieferten
 *   Buendel: 904 / 955 / 1058 / 1123 / 1205).
 *
 * In diesem Projekt sind 35 Pruefungen einzeln entfernt worden und elf
 * blieben gruen. Eine Bitte im Kommentar ist kein Waechter.
 *
 * ── Was diese Probe kann, und was nicht ──────────────────────────────────
 *
 * KANN NICHT: die einzelne Zahl im Register pruefen. jsdom hat kein Layout;
 * `scrollHeight` ist dort immer 0. Jede Probe, die hier eine Pixelhoehe
 * «misst», wuerde ihre eigene Konstante zurueckbekommen — eine Probe, die
 * nicht widersprechen kann. Die Zahlen des Registers stammen darum aus einer
 * Messung am laufenden Bild (eigener kopfloser Chromium, CDP 9229, Fenster
 * 1400x900, frischer Render-Knoten, Rahmenbreite 184 px).
 *
 * KANN: verhindern, dass jemand an dieser Messung VORBEI eine Zeile einbaut,
 * und die beiden Budgets halten, die den Befund vom 17.09. ausmachen:
 *
 *  1. Jede gerenderte Zeile traegt `data-zeile`. Register und DOM werden in
 *     BEIDE Richtungen verglichen — eine neue Zeile ohne Eintrag ist rot, ein
 *     Eintrag ohne Zeile auch. Wer eine Zeile hinzufuegt, MUSS das Register
 *     anfassen; und wer das Register anfasst, steht vor der Frage nach der
 *     Zahl, statt sie zu uebersehen.
 *  2. Die REIHENFOLGE wird mitgeprueft. Ohne sie waere Budget A wertlos: es
 *     rechnet die sechs Bedienelemente von oben zusammen, und eine im JSX
 *     verschobene Zeile wuerde die Rechnung stillschweigend falsch machen.
 *  3. Budget A — die sechs Bedienelemente liegen im Fenster. (Seit A21 sitzt
 *     die MITTE des neuen Knotens auf der Sichtmitte, nicht mehr seine linke
 *     obere Ecke — Budget A ist damit die STRENGERE der beiden Fragen und
 *     bleibt stehen, weil es haelt.)
 *  4. Budget B — der frische Knoten passt in einen 700 px hohen Ausschnitt.
 *     Sonst liegt seine Mitte strukturell ausserhalb, und die B69-Meldung
 *     «liegt ausserhalb des sichtbaren Ausschnitts» kommt bei JEDEM
 *     Render-Knoten (s. `p-b69-knotenplatz-ausserhalb-hinweis.test.tsx`).
 *  5. Die Breitenklemme. Gemessen am ausgelieferten Buendel lief der Koerper
 *     auf 242 px in einem 184 px breiten Rahmen — nicht ein Element, sondern
 *     JEDE Zeile, weil ein Grid-Kind ohne `min-width: 0` seine Spur auf seine
 *     eigene Mindestbreite aufzieht. Die Hoehe war gemessen worden, die
 *     Breite nicht.
 *
 * ── P16 (17.09.2026): das Register bewacht jetzt ZWEI Orte ───────────────
 *
 * Der zugeklappte Knoten hielt seine Zusage, der aufgeklappte nicht: gemessen
 * an fuenf Fenstergroessen (1280x720 … 1920x1080) war die Karte aufgeklappt
 * 1099 px hoch, und bei JEDER Groesse lagen 7 von 15 Bedienelementen
 * ausserhalb des Fensters. Seit P16 waechst die Karte beim Aufklappen gar
 * nicht mehr — der Zusatz steht in einem BEIBLATT neben ihr
 * (`RenderBeiblatt`, `NodeCanvas.tsx`).
 *
 * Fuer diese Probe heisst das: `RENDER_ZEILEN` bewacht die KARTE,
 * `RENDER_ZEILEN_ZUSATZ` bewacht das BEIBLATT, und Fall 2 prueft zusaetzlich,
 * dass keine Zeile an beiden Orten steht (sonst zaehlt das Register sie
 * doppelt). Dazu kommt Budget C: das Beiblatt passt in das kleinste der fuenf
 * gemessenen Fenster, ohne zu rollen.
 *
 * Wie man sich ueberzeugt, dass sie widersprechen kann — sechs Schnitte, alle
 * am 17.09. nachgestellt: eine Zeile aus dem Register streichen (Fall 1 rot),
 * zwei Registerzeilen tauschen (Fall 2 rot), eine Zeilenhoehe um 100 erhoehen
 * (Budget A und B rot), das `minWidth: 0` aus `KLEMME_VOLL` nehmen (Fall 5
 * rot), `render` wieder in `KOERPER_H_ZUSATZ_OFFEN` eintragen (Fall 2 rot —
 * die Karte waechst dann wieder), eine Zusatzzeile um 200 px erhoehen
 * (Budget C rot).
 */

// jsdom kennt kein ResizeObserver — NodeCanvas nutzt ihn nur, um die
// Containergroesse fuer die viewBox zu messen (Muster `node-canvas-pan.test.tsx`).
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * Das Fenster, an dem gemessen wurde: 1400x900 — die Hausgroesse der
 * E2E-Suite (`playwright.config.ts`, `viewport: { width: 1400, height: 900 }`)
 * und zugleich die Groesse, an der der unabhaengige Pruefer den Befund
 * aufgenommen hat (er mass 913 px Fensterhoehe; 900 ist der strengere Wert).
 */
const FENSTER_H = 900;

/**
 * Die Hoehe des Ausschnitts, gegen den die B69-Gegenprobe prueft
 * (`p-b69-knotenplatz-ausserhalb-hinweis.test.tsx`: eine unbewegte
 * NodeCanvas-Standardflaeche 1200x700 bei Skala 1). Ein Knoten, der hoeher
 * ist als der Ausschnitt, faellt strukturell immer heraus — seine linke obere
 * Ecke sitzt auf der Sichtmitte, seine Mitte also eine halbe Knotenhoehe
 * darunter.
 */
const AUSSCHNITT_H = 700;

/**
 * P16 (17.09.2026): die kleinste der fuenf Fenstergroessen, an denen der
 * unabhaengige Pruefer UND P16 gemessen haben (1280x720 · 1366x768 ·
 * 1440x900 · 1680x1050 · 1920x1080). Wer hier eine kleinere Zahl eintraegt,
 * behauptet eine Messung, die es nicht gibt.
 */
const KLEINSTES_FENSTER_H = 720;

/** Die sechs Bedienelemente der Abnahmeliste, in der Reihenfolge, in der sie
 *  im Koerper stehen (Zeilen 4 / 50a / 51 / 47 / 48 / 56). */
const SECHS = [
  ['bedienung-preset', 'vis-preset-select'],
  ['bedienung-aufloesung', 'render-aufloesung'],
  ['bedienung-qualitaet', 'render-qualitaet'],
  ['bedienung-himmel', 'render-himmel'],
  ['bedienung-drehung', 'render-umgebung-drehen'],
  ['bedienung-bildwerkzeug', 'render-bildwerkzeug'],
] as const;

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function knoten(): HTMLElement {
  const g = container!.querySelector('[data-testid="vis-node-render"]');
  expect(g, 'kein Render-Knoten gerendert').not.toBeNull();
  return g as unknown as HTMLElement;
}

/** Die Kennungen der Koerperzeilen IN DER KARTE, in DOM-Reihenfolge. */
function zeilenImDom(): string[] {
  return [...knoten().querySelectorAll('[data-zeile]')].map((e) => e.getAttribute('data-zeile') ?? '');
}

/** P16: das Beiblatt, oder null. Es liegt AUSSERHALB des `<svg>` — darum wird
 *  es am Container gesucht und nicht am Knoten. */
function beiblatt(): HTMLElement | null {
  return container!.querySelector('[data-testid="render-beiblatt"]');
}

/** Die Kennungen der Zeilen IM BEIBLATT, in DOM-Reihenfolge. */
function zeilenImBeiblatt(): string[] {
  const b = beiblatt();
  if (!b) return [];
  return [...b.querySelectorAll('[data-zeile]')].map((e) => e.getAttribute('data-zeile') ?? '');
}

function klappe(): void {
  const knopf = knoten().querySelector('[data-testid="node-expand"]');
  expect(knopf, 'kein Klappknopf im Render-Knoten').not.toBeNull();
  act(() => {
    (knopf as HTMLElement).dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
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
  const { runCommand } = useProject.getState();
  const graphId = (runCommand('vis.graphErstellen', { name: 'A15' }).patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0 });
  expect(useProject.getState().doc.get<VisGraph>(graphId)!.nodes).toHaveLength(1);

  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<NodeCanvas graphId={graphId} />);
  });
});

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
});

describe('A15 — das Zeilenregister des Render-Koerpers haelt, was die Hoehe verspricht', () => {
  it('Fall 1: jede gerenderte Zeile steht im Register, und jede Registerzeile wird gerendert (zugeklappt)', () => {
    expect(zeilenImDom()).toEqual(RENDER_ZEILEN.map((z) => z.id));
  });

  it('Fall 2 (P16): aufgeklappt kommen GENAU die Zusatzzeilen dazu — aber im BEIBLATT, und die Karte ruehrt sich nicht', () => {
    const zu = zeilenImDom();
    expect(beiblatt(), 'zugeklappt darf es kein Beiblatt geben').toBeNull();

    klappe();
    const auf = zeilenImDom();
    const zusatz = zeilenImBeiblatt();

    // Bis P16 stand hier: «aufgeklappt enthaelt die Karte Grund- UND
    // Zusatzzeilen». Genau das war der Befund — die Karte wuchs auf 1099 px
    // und 7 von 15 Bedienelementen lagen ausserhalb des Fensters. Seither
    // gilt die STAERKERE Aussage: die Karte aendert sich beim Aufklappen
    // ueberhaupt nicht.
    expect(auf, 'die Karte darf beim Aufklappen keine Zeile gewinnen oder verlieren').toEqual(zu);
    expect(auf).toEqual(RENDER_ZEILEN.map((z) => z.id));

    // Und das Beiblatt traegt GENAU das Zusatzregister — beide Richtungen,
    // als Menge: nichts Unbekanntes dazu, nichts Bekanntes weg. Damit bleibt
    // die Klammer zu: wer eine Zeile hinzufuegt, MUSS das Register anfassen,
    // egal an welchem der beiden Orte.
    expect([...zusatz].sort()).toEqual([...RENDER_ZEILEN_ZUSATZ].map((z) => z.id).sort());

    // Keine Zeile darf an BEIDEN Orten stehen — sonst zaehlt das Register sie
    // doppelt und eine der beiden Hoehenrechnungen ist still falsch.
    expect(zusatz.filter((id) => auf.includes(id)), 'Zeile steht in Karte UND Beiblatt').toEqual([]);

    // Wieder zuklappen: das Beiblatt verschwindet vollstaendig.
    klappe();
    expect(beiblatt(), 'nach dem Zuklappen darf kein Beiblatt stehenbleiben').toBeNull();
    expect(zeilenImDom()).toEqual(zu);
  });

  it('Fall 3: die sechs Bedienelemente stehen im zugeklappten Knoten — nicht hinter dem Klappknopf', () => {
    const k = knoten();
    for (const [zeile, testid] of SECHS) {
      expect(zeilenImDom(), `${zeile} fehlt im zugeklappten Knoten`).toContain(zeile);
      expect(k.querySelector(`[data-testid="${testid}"]`), `${testid} fehlt im zugeklappten Knoten`).not.toBeNull();
    }
    // Und sie stehen GANZ OBEN, in der Reihenfolge der Abnahmeliste — Budget A
    // unten rechnet genau diese sechs von der Koerperoberkante ab.
    expect(RENDER_ZEILEN.slice(0, 6).map((z) => z.id)).toEqual(SECHS.map(([zeile]) => zeile));
  });

  it('Budget A: alle sechs Bedienelemente liegen in der unteren Fensterhaelfte, in der der neue Knoten sitzt', () => {
    // Der Koerper beginnt unter Kopf und Ports. Die Zahl wird NICHT nochmal
    // eingetippt, sondern aus denselben Groessen gewonnen, die der Knoten
    // selbst benutzt.
    const koerperOben = basisNodeHoehe('render') - zeilenHoehe(RENDER_ZEILEN) - 10;
    const unterkanteSechs = koerperOben + zeilenHoehe(RENDER_ZEILEN.slice(0, 6));

    // Die linke obere Ecke des neuen Knotens sitzt auf der Sichtmitte —
    // darunter liegt die halbe Fensterhoehe.
    expect(unterkanteSechs).toBeLessThanOrEqual(FENSTER_H / 2);
  });

  it('Budget B: der frische Render-Knoten passt in den Ausschnitt, sonst meldet B69 bei jedem Knoten «liegt ausserhalb»', () => {
    expect(basisNodeHoehe('render')).toBeLessThanOrEqual(AUSSCHNITT_H);
  });

  it('Budget C (P16): das Beiblatt passt in das KLEINSTE gemessene Fenster, ohne zu rollen', () => {
    // Das kleinste Fenster der P16-Messung ist 1280x720. Abzueglich der beiden
    // gemessenen senkrechten Insel-Reserven bleibt ein Feld; das Beiblatt muss
    // hineinpassen. Die Zahlen werden NICHT eingetippt, sondern aus derselben
    // Rechnung genommen, die das Beiblatt selbst benutzt (`beiblattFeld`).
    const feld = beiblattFeld({ w: 1280, h: KLEINSTES_FENSTER_H });
    const platz = feld.unten - feld.oben;
    expect(BEIBLATT_H_NENN, `Beiblatt ${BEIBLATT_H_NENN} px in ${platz} px Feld`).toBeLessThanOrEqual(platz);

    // Und die Gegenprobe zur Gegenprobe: das Register IST die Hoehe des
    // Beiblatts. Waere die Nennhoehe eine eigene Zahl, koennte sie von den
    // Zeilen wegdriften, ohne dass jemand es merkt.
    expect(BEIBLATT_H_NENN).toBeGreaterThan(zeilenHoehe(RENDER_ZEILEN_ZUSATZ));

    // Und die Karte daneben bleibt, was sie zugeklappt war — der ganze Punkt
    // von P16: aufklappen aendert die Kartenhoehe um NULL.
    expect(basisNodeHoehe('render')).toBeLessThanOrEqual(KLEINSTES_FENSTER_H);
  });

  it('Fall 4: eine Zeile, die nur in EINEM Zustand erscheint, ist im Register als «bedingt» verzeichnet', () => {
    // Der Drehungs-Hinweis steht nur da, solange kein Himmel gewaehlt ist.
    // Ohne diesen Fall waere `bedingt` ein Feld, das eine Bedeutung behauptet
    // und keinen Leser hat — genau die Attrappe, vor der die Anleitung warnt.
    const bedingte = RENDER_ZEILEN_ZUSATZ.filter((z) => z.bedingt === true).map((z) => z.id);
    const feste = RENDER_ZEILEN_ZUSATZ.filter((z) => z.bedingt !== true).map((z) => z.id);
    expect(bedingte, 'kein bedingter Eintrag mehr — dann gehoert das Feld weg').not.toHaveLength(0);

    klappe();
    for (const id of [...feste, ...bedingte]) expect(zeilenImBeiblatt()).toContain(id);

    // Jetzt einen Himmel waehlen: die bedingte Zeile verschwindet, alle
    // uebrigen bleiben. Ihre Hoehe bleibt im Register reserviert — ein Stueck
    // leere Karte, nie ein Schnitt.
    const { doc, runCommand } = useProject.getState();
    const graph = doc.byKind<VisGraph>('visgraph')[0]!;
    act(() => {
      runCommand('vis.nodeParametrieren', {
        graphId: graph.id,
        nodeId: graph.nodes[0]!.id,
        params: { himmel: 'PREETHAM' },
      });
    });

    const jetzt = zeilenImBeiblatt();
    for (const id of bedingte) expect(jetzt, `${id} haette verschwinden muessen`).not.toContain(id);
    for (const id of feste) expect(jetzt, `${id} ist zu Unrecht verschwunden`).toContain(id);
  });

  it('Fall 5: die Breitenklemme sitzt — an jeder Zeile und an jedem der sechs Bedienelemente', () => {
    // jsdom schreibt `min-width: 0` als «0», echte Browser als «0px» — beide
    // meinen dasselbe. Die Probe prueft die WIRKUNG, nicht die Schreibweise.
    const geklemmt = (el: HTMLElement | null | undefined): boolean =>
      el !== null && el !== undefined && (el.style.minWidth === '0' || el.style.minWidth === '0px');

    const k = knoten();
    for (const zeile of k.querySelectorAll('[data-zeile]')) {
      expect(geklemmt(zeile as HTMLElement), `Zeile ${zeile.getAttribute('data-zeile')} ohne Breitenklemme`).toBe(true);
    }
    // P16: dieselbe Klemme im Beiblatt. Seine Inhaltsspalte ist genauso breit
    // wie die des Koerpers (184 px) — ein Grid-Kind ohne `min-width: 0` zieht
    // dort dieselbe Spur auf.
    klappe();
    const b = beiblatt();
    expect(b, 'kein Beiblatt nach dem Aufklappen').not.toBeNull();
    for (const zeile of b!.querySelectorAll('[data-zeile]')) {
      expect(
        geklemmt(zeile as HTMLElement),
        `Beiblatt-Zeile ${zeile.getAttribute('data-zeile')} ohne Breitenklemme`,
      ).toBe(true);
    }
    for (const [, testid] of SECHS) {
      const el = k.querySelector(`[data-testid="${testid}"]`) as HTMLElement | null;
      expect(el, `${testid} nicht gefunden`).not.toBeNull();
      // KSelect legt Layout-Schluessel (`width`/`minWidth`) auf seinen
      // Wrapper, nicht auf den Ausloeser (`select.tsx`, WRAP_STYLE_KEYS) —
      // darum zaehlt das Element ODER sein Elternteil.
      expect(
        geklemmt(el) || geklemmt(el!.parentElement),
        `${testid} ohne minWidth:0 — der Waehler zieht die ganze Spalte auf`,
      ).toBe(true);
    }
  });
});
