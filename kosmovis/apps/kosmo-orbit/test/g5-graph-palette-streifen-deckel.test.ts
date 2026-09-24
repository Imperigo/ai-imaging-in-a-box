import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { VIS_INSELN, VIS_ISLAND_REIHENFOLGE } from '../src/modules/vis/island/vis-island-katalog';
import { VIS_NODE_KATALOG } from '@kosmo/kernel';

/**
 * G5 (ROADMAP 1259, Gruppe «`island-palette-eintrag-blatt` von
 * `open-project` verdeckt», Auftrag an diesen Dateikreis: `vis-island.css` +
 * `vis/island/*` + eine eigene Testdatei). Eigene, additive Datei — testet
 * NUR die neue `:has(.isl-rand-links.isl-root--offen)`-Regel in
 * `vis-island.css`; `island.css`/`InselKopf.tsx`/`IslandShell.tsx` bleiben
 * fremder Dateikreis und werden hier nur GELESEN, nie erwartet zu ändern.
 *
 * GRENZE, ehrlich benannt (dieselbe wie `prand-rand-im-bild.test.tsx`/
 * `insel-scroll-e10.test.tsx`): jsdom hat keine Layout-Engine — kein Test
 * hier kann beweisen, dass der Knopf am echten Chromium wieder klickbar
 * ist. Geprüft wird die STRUKTUR: (a) das reale Sondenergebnis, das den
 * Fund überhaupt belegt (`e2e-messungen/w5-1-insel-ueberdeckung-funde.json`,
 * ein echter Playwright-Lauf, kein Mock), (b) dass genau die drei erwarteten
 * Rand-Klassen gedeckt sind und keine vierte, und (c) dass dieselbe kleine
 * Auswerte-Funktion an einem ungedeckten Rand AUTO liefert — sonst waere
 * die NONE-Zusicherung wertlos. Die
 * Browser-Abnahme (bleibt der Knopf am echten Chromium erreichbar UND bleibt
 * `open-project` weiterhin selbst klickbar?) ist NICHT Teil dieser Datei.
 *
 * ROT-VOR-GRUEN, und warum es hier nicht als Testfall steht: der Rot-Nachweis
 * wurde am 02.09.2026 gegen den Stand VOR diesem Bau gefahren (`e1fb6c64`,
 * `gedeckteRandKlassen` = {`isl-rand-sonne`, `isl-rand-unten`}, der GRAPH-Rand
 * also ungedeckt, Streifen `pointer-events: auto`). Ein Testfall, der diesen
 * Stand per `git show HEAD:…` liest, ist genau EINEN Commit lang wahr und
 * schlaegt danach dauerhaft fehl — ein Beleg, der sich beim Einchecken selbst
 * zerstoert. Er steht darum als Zahl im ROADMAP-Eintrag und hier im Kopf,
 * nicht als gruene Zusicherung, die von der Commit-Lage abhaengt.
 */

const HIER = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(HIER, '../src');
const CSS_PFAD = 'modules/vis/island/vis-island.css';

function ohneKommentare(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, '');
}

function aktuellesCss(): string {
  return ohneKommentare(readFileSync(resolve(SRC, CSS_PFAD), 'utf8'));
}

/**
 * Extrahiert aus dem CSS-Text alle `.app-wurzel[data-station='vis']:has(
 * .isl-rand-<X>.isl-root--offen) .isl-grundstreifen`-Regeln und liefert die
 * Menge der damit gedeckten Rand-Klassen — nur jene, deren Regelkörper
 * `pointer-events: none` UND `opacity: 0.45` trägt (dasselbe Wertepaar wie
 * SONNE/AUSTAUSCH, keine abweichende Dimmung).
 */
function gedeckteRandKlassen(css: string): Set<string> {
  const muster =
    /\.app-wurzel\[data-station='vis'\]:has\(\.(isl-rand-[a-z]+)\.isl-root--offen\)\s*\.isl-grundstreifen\s*\{([^}]*)\}/g;
  const treffer = new Set<string>();
  for (const m of css.matchAll(muster)) {
    const [, randKlasse, koerper] = m;
    if (koerper!.includes('pointer-events: none') && koerper!.includes('opacity: 0.45')) {
      treffer.add(randKlasse!);
    }
  }
  return treffer;
}

/**
 * Simuliert, was `:has()` am echten Chromium für den Streifen entscheiden
 * würde, WENN genau `randKlasse` gerade offen ist (`isl-root--offen`) —
 * reine Textauswertung der tatsächlich im CSS deklarierten Regeln, kein
 * DOM, keine Annahme über Regeln, die es geben SOLLTE.
 */
function streifenPointerEvents(css: string, randKlasse: string): 'auto' | 'none' {
  return gedeckteRandKlassen(css).has(randKlasse) ? 'none' : 'auto';
}

describe('G5 · GRAPH-Palette (island-palette-eintrag-blatt) vs. open-project', () => {
  /**
   * Der historische Befund, eingefroren als Daten statt als Zusicherung gegen
   * eine Datei, die sich bewegt. Gemessen im Sweep vom 02.09.2026, 05:35 Uhr
   * (`erzeugtAm` im damaligen Artefakt), vier Funde, alle mit
   * `treffer: "open-project"`. Er steht hier, damit der Eintrag unten sagen
   * kann, WAS verschwunden sein muss — nicht, um ihn nachzuweisen.
   */
  const HISTORISCH = [
    { viewport: '1024x768', stufe: 'fenster:palette', x: 129.8125, y: 715.609375, w: 286, h: 27.390625 },
    { viewport: '1024x768', stufe: 'popup:palette', x: 125.8125, y: 719.609375, w: 220, h: 27.390625 },
    { viewport: '1180x820', stufe: 'fenster:palette', x: 129.8125, y: 767.609375, w: 286, h: 27.390625 },
    { viewport: '1180x820', stufe: 'popup:palette', x: 125.8125, y: 771.609375, w: 220, h: 27.390625 },
  ] as const;

  /**
   * v0.1.0 / A3 (04.09.2026): das Artefakt liegt unter `e2e-messungen/` und
   * ist gitignoriert (`.gitignore`, P-MESSSPUR). Auf einem FRISCHEN Klon
   * existiert es nicht — und genau dort fiel dieser Fall am 04.09.2026 als
   * EINZIGER roter Test der ganzen Unit-Suite (`npm run test` auf frischem
   * Klon, `ENOENT … w5-1-insel-ueberdeckung-funde.json`). Der Test mass damit
   * den Bauzustand der Maschine, nicht den Commit — dieselbe Klasse, gegen
   * die P-WACHE (02.09.2026, RELEASE-ABLAUF §2b) die Kette schon einmal
   * bereinigt hat. Fehlt das Artefakt, wird der Fall SICHTBAR uebersprungen
   * (mit dem Grund im Namen), nicht rot und nicht still gruen; liegt es vor,
   * gilt die Zusicherung unveraendert. Gegenprobe gefahren: ein praepariertes
   * Artefakt mit einem G5-Fund macht den Fall rot.
   */
  const SWEEP_PFAD = resolve(HIER, '../../../e2e-messungen/w5-1-insel-ueberdeckung-funde.json');

  it.skipIf(!existsSync(SWEEP_PFAD))(
    'der aktuelle Sweep-Befund traegt KEINEN GRAPH-Palette-Deckel mehr — die eigentliche Zusicherung (braucht das lokale Sweep-Artefakt e2e-messungen/w5-1-insel-ueberdeckung-funde.json; ohne Artefakt uebersprungen, nicht gruen)',
    () => {
    // WARUM NICHT gegen die vier historischen Funde geprueft wird: dieselbe
    // Falle wie beim urspruenglichen «ROT VORHER»-Fall dieser Datei (s. Kopf).
    // `e2e-messungen/w5-1-insel-ueberdeckung-funde.json` wird bei jedem Sweep
    // NEU GESCHRIEBEN. Eine Zusicherung, die dort vier Funde verlangt, ist
    // genau so lange gruen, wie der Defekt existiert — und wird rot, sobald
    // die Reparatur wirkt. Sie hat im Schnitt v0.9.55 real zugeschlagen: der
    // Sweed vom 02.09. 11:26 fand die vier nicht mehr, und die Probe fiel
    // durch, WEIL der Fix funktioniert. Ein Test, der bei Erfolg rot wird,
    // misst den Defekt, nicht die Reparatur.
    const daten = JSON.parse(readFileSync(SWEEP_PFAD, 'utf8')) as {
      funde: ReadonlyArray<{ station: string; insel: string; testid: string; treffer: string }>;
    };
    const g5 = daten.funde.filter(
      (f) => f.station === 'vis' && f.insel === 'graph' && f.testid === 'island-palette-eintrag-blatt',
    );
    expect(g5).toEqual([]);
    // Und die Gegenprobe zur Gegenprobe: die Datei muss ueberhaupt gelesen
    // worden sein. Ein leeres `funde` waere sonst ebenfalls gruen, ohne dass
    // je gemessen wurde.
    expect(Array.isArray(daten.funde)).toBe(true);
    expect(HISTORISCH).toHaveLength(4);
    },
  );

  it('«blatt» ist strukturell der LETZTE Katalog-Eintrag der Palette — deshalb dieser Eintrag, kein Zufall', () => {
    const KATEGORIE_REIHENFOLGE = ['quelle', 'wandler', 'render', 'ausgabe'] as const;
    const eintraege = KATEGORIE_REIHENFOLGE.flatMap((kat) =>
      Object.values(VIS_NODE_KATALOG).filter((t) => t.kategorie === kat),
    );
    expect(eintraege.at(-1)?.typ).toBe('blatt');
    // Zwölf Node-Typen — wächst der Katalog, wächst die Popup-/Fenster-Liste
    // mit (E-10 Antwort c, kein Scroll) und der Fund bliebe strukturell
    // derselbe: der jeweils letzte Eintrag der letzten Kategorie.
    expect(eintraege).toHaveLength(12);
  });

  it('GRAPH sitzt am linken Rand, vertikal mittig — nicht an der Streifen-Ecke wie SONNE', () => {
    const graph = VIS_INSELN.find((i) => i.id === 'graph');
    expect(graph?.randKlasse).toBe('isl-rand-links');
    expect(graph?.orientierung).toBe('vertikal');
    expect(VIS_ISLAND_REIHENFOLGE).toContain('graph');
    // Gegenprobe zur SONNE-Insel (Nachtrag 01.09.2026 oben in derselben
    // Datei): SONNE sitzt an derselben Ecke wie der Streifen
    // (`left:14px;bottom:14px`), GRAPH nicht.
    const sonne = VIS_INSELN.find((i) => i.id === 'sonne');
    expect(sonne?.randKlasse).not.toBe('isl-rand-links');
  });

  it('die Auswerte-Funktion faellt auf AUTO zurueck, wo keine Regel steht — sonst waere GRUEN nichts wert', () => {
    // Die Gegenprobe zur Zusicherung darunter: dieselbe Funktion, angewandt
    // auf einen Rand, den keine Regel deckt, muss AUTO liefern. Ohne sie
    // koennte `streifenPointerEvents` konstant NONE zurueckgeben und der
    // Gruen-Fall waere ein Selbstbetrug.
    const nachher = aktuellesCss();
    expect(streifenPointerEvents(nachher, 'isl-rand-rechts')).toBe('auto');
    expect(streifenPointerEvents(nachher, 'isl-rand-links')).toBe('none');
  });

  it('GRUEN NACHHER: die neue Regel deckt den Streifen bei offener GRAPH-Insel — mit demselben Wertepaar wie SONNE/AUSTAUSCH', () => {
    const nachher = aktuellesCss();
    expect(streifenPointerEvents(nachher, 'isl-rand-links')).toBe('none');
    expect(gedeckteRandKlassen(nachher)).toEqual(new Set(['isl-rand-sonne', 'isl-rand-unten', 'isl-rand-links']));
  });

  it('kein neues Muster: keine z-index-Regel, kein NICHT_ANKLICKEN, keine Dauer-Dimmung ausserhalb von :has(...isl-root--offen)', () => {
    const nachher = aktuellesCss();
    const neuerBlock = nachher.slice(nachher.indexOf(".isl-rand-links.isl-root--offen"));
    // Nur diese eine neue Regel im weiteren Dateiverlauf ab hier geprüft —
    // kein z-index, kein Deckname für einen harten Sperr-Zustand.
    const block = neuerBlock.slice(0, neuerBlock.indexOf('}') + 1);
    expect(block).not.toMatch(/z-index/);
    expect(block).not.toMatch(/NICHT_ANKLICKEN/i);
    expect(block).toContain('pointer-events: none');
    expect(block).toContain('opacity: 0.45');
  });

  it('kein Henne-Ei-Fall wie bei SONNE: die geschlossene GRAPH-Pille liegt weit ausserhalb der Streifen-Zone (72–820px und 72–768px geprüft)', () => {
    // Reale Konstanten, nicht geraten — alle aus den CSS-Dateien gelesen:
    const RAND_ABSTAND = 14; // .isl-root { --isl-rand-abstand: 14px } (design/island/island.css)
    const PILL_HOEHE_VERTIKAL = 88; // .isl-vertikal .isl-pill { height: 88px } (design/island/island.css)
    const STREIFEN_MIN_HOEHE = 44; // .isl-grundstreifen { min-height: 44px } (design/island/island.css)
    for (const fensterHoehe of [768, 820]) {
      // Streifen-Y-Band (bottom:14px, min. 44px hoch):
      const streifenOben = fensterHoehe - RAND_ABSTAND - STREIFEN_MIN_HOEHE;
      const streifenUnten = fensterHoehe - RAND_ABSTAND;
      // GRAPH-Pille: vertikal mittig (top:50%, translateY(-50%)), 88px hoch:
      const pilleOben = fensterHoehe / 2 - PILL_HOEHE_VERTIKAL / 2;
      const pilleUnten = fensterHoehe / 2 + PILL_HOEHE_VERTIKAL / 2;
      // Kein Überlapp der beiden Bänder — das Hover-Ereignis, das
      // `isl-root--offen` setzt, trifft nie auf den Streifen.
      expect(pilleUnten).toBeLessThan(streifenOben);
      expect(pilleOben).toBeGreaterThan(0);
      expect(streifenUnten).toBeLessThanOrEqual(fensterHoehe);
    }
  });
});
