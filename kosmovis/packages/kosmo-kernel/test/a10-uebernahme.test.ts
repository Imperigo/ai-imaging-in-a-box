import { describe, expect, it } from 'vitest';
import {
  BEREICHE,
  EIGENSCHAFTEN,
  FARBTON_MESSGRENZE,
  SAT_TOR_FLANKE,
  SAT_TOR_SCHWELLE,
  UEBERNAHME_BEREICH_LABEL,
  UEBERNAHME_BEREICH_VORBEHALT,
  UEBERNAHME_EIGENSCHAFT_LABEL,
  UEBERNAHME_KENNLINIE_PUNKTE,
  UEBERNAHME_WAS_GEAENDERT_WURDE,
  aufKennlinie,
  bereichsMaske,
  kuerzesteDrehung,
  uebernahme,
} from '../src/bild/uebernahme';
import { farbangleich, type Bild } from '../src/bild/farbangleich';
import { hsvZuRgb, nachbearbeitung, rgbZuHsv } from '../src/bild/nachbearbeitung';
import * as uebernahmeModul from '../src/bild/uebernahme';
import * as belichtungModul from '../src/bild/belichtung';
import * as farbangleichModul from '../src/bild/farbangleich';
import * as nachbearbeitungModul from '../src/bild/nachbearbeitung';

/**
 * A10 · ZEILE 54 — «Aus einem Referenzbild einzelne, benannte Eigenschaften
 * uebernehmen, und nur diese.» Die Proben zu `src/bild/uebernahme.ts`.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * GEGEN WAS HIER GEMESSEN WIRD
 * ────────────────────────────────────────────────────────────────────────────
 * Jede Sollzahl steht AUSGESCHRIEBEN. Keine wird aus dem Geprueften geholt —
 * eine Probe, die ihre Erwartung aus dem Modul zieht, das sie prueft, kann
 * nicht Nein sagen (Muster 3 der Anleitung).
 *
 * Die Zahlen stammen aus einer ZWEITRECHNUNG in Python/numpy (numpy 2.5.1,
 * Python 3.14.4), die den TypeScript-Code nicht aufruft, sondern die Rechnung
 * aus der Beschreibung neu aufbaut: vektorisiert statt als Schleife, in einer
 * anderen Sprache, mit einer anderen Gleitkomma-Bibliothek. Fuer dieses Modul
 * gibt es — wie fuer `belichtung.ts` und anders als fuer die zwei aeltesten
 * Nachbarn — KEINE Python-Vorlage; die Referenz ist darum eine Zweitrechnung
 * und keine Vorlage.
 *
 * ERGEBNIS DES ABGLEICHS: ueber NEUN Faelle an je 378 000 Bildpunkten
 * stimmen beide Seiten BYTE FUER BYTE ueberein (Fingerabdruck und Bytesumme),
 * und die Berichtszahlen auf zwoelf Stellen.
 *
 * EINE ECHTE ABWEICHUNG GAB ES, und sie gehoert hierher: im ersten Lauf
 * unterschied sich eine einzige Kennzahl — «wieviele Bildpunkte hat der
 * Farbton bewegt» — um 22 von 273 208. Kein einziges Byte war betroffen. Die
 * Ursache lag in der Referenz: `nachbearbeitung.ts` rundet die
 * Vorzeichen-Korrektur des Farbton-Restes (`rest + 6`) zusaetzlich auf
 * `float32`, `np.mod` tut das nicht; der Unterschied betraegt bis zu 2e-5
 * Grad und entscheidet nur darueber, ob ein Bildpunkt als «bewegt» zaehlt.
 * Nach dem Angleich der Referenz: kein Unterschied mehr.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * DIE ZWEI PRUEFBILDER, und warum keines im Repo liegt
 * ────────────────────────────────────────────────────────────────────────────
 * Beide entstehen aus einer FORMEL, in Python und in TypeScript derselben —
 * nur Ganzzahlen und Bitoperationen, damit beide Seiten wirklich dasselbe Bild
 * in der Hand haben. Die erste Probe jedes Laufs prueft genau das; ohne sie
 * verglichen zwei Laeufe zwei verschiedene Bilder.
 *
 *  * BILD (700 x 540 = 378 000 Punkte): ein Innenraum mit warmem Deckenholz,
 *    grauer Wand, Begruenung, einem hellen Fensterfeld und einer Lampe. Die
 *    Groesse ist kein Zufall — der Befund im Kopf von `bild-farbe.test.ts`
 *    haelt fest, dass ein `float32`-Summenfehler erst bei rund 376 000
 *    Bildpunkten die erste Nachkommastelle kippt. Eine Probe auf 64 x 64
 *    Punkten saehe davon nichts.
 *  * VORBILD (512 x 384 = 196 608 Punkte): dieselbe Gliederung, aber
 *    ausdruecklich ANDERS gefaerbt — kraeftigeres, roeteres Holz, saftigeres
 *    Gruen, ein warmes helles Feld. Und ABSICHTLICH ANDERS GROSS: ein Vorbild
 *    ist ein anderes Bild, kein Ueberzug.
 *
 * EINE FORMEL IST KEIN FOTO. Was diese Bilder pruefen koennen, ist die
 * RECHNUNG: dass eine benannte Groesse wandert und die anderen zwei
 * stehenbleiben, dass ein Bereich haelt, dass zwei Wege dieselbe Zahl geben.
 * Was sie NICHT pruefen koennen, ist, ob der Owner das Ergebnis am echten
 * Renderbild fuer richtig haelt — ob also die Deckenmaske an SEINEM Bild die
 * Decke trifft. Dafuer braucht es ein Renderbild, und im Repo liegt keines.
 * Der Befund dazu steht im Bericht zu A10, nicht hier.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * WAS DIESE DATEI SONST NICHT MISST
 * ────────────────────────────────────────────────────────────────────────────
 * Sie misst die Rechnung, nicht die Oberflaeche. Ob Zeile 54 im
 * Kurations-Inspektor bedienbar ist, misst `apps/kosmo-orbit/test/
 * a10-uebernahme-oberflaeche.test.tsx`.
 */

// ---------------------------------------------------------------------------
// Werkzeug
// ---------------------------------------------------------------------------

/** FNV-1a, 32 Bit — derselbe Fingerabdruck, den die Zweitrechnung bildet. */
function fnv1a(daten: Uint8ClampedArray | Uint8Array): number {
  let h = 2166136261;
  for (let i = 0; i < daten.length; i++) h = Math.imul(h ^ daten[i]!, 16777619) >>> 0;
  return h >>> 0;
}

function byteSumme(daten: Uint8ClampedArray | Uint8Array): number {
  let s = 0;
  for (let i = 0; i < daten.length; i++) s += daten[i]!;
  return s;
}

/** Wieviele Bildpunkte haben sich in mindestens einem Byte bewegt? */
function veraenderteBildpunkte(a: Bild, b: Bild): number {
  const n = a.breite * a.hoehe;
  let zahl = 0;
  for (let i = 0; i < n; i++) {
    for (let c = 0; c < 3; c++) {
      if (a.daten[i * a.kanaele + c] !== b.daten[i * b.kanaele + c]) {
        zahl++;
        break;
      }
    }
  }
  return zahl;
}

/**
 * Das Bild aus einer Formel. Nur Ganzzahlen und Bitoperationen; der
 * Zahlengenerator ist derselbe lineare Kongruenzgenerator wie in
 * `bild-farbe.test.ts` und `a16-belichtung.test.ts` — ein Zug je Kanal,
 * zeilenweise von links oben, R vor G vor B.
 */
function formelBild(
  breite: number,
  hoehe: number,
  saat: number,
  basis: (x: number, y: number) => readonly [number, number, number],
  verlaufX: number,
  verlaufY: number,
): Bild {
  const daten = new Uint8Array(breite * hoehe * 3);
  let z = saat;
  for (let y = 0; y < hoehe; y++) {
    for (let x = 0; x < breite; x++) {
      const i = y * breite + x;
      const b = basis(x, y);
      const verlauf = Math.floor((x * verlaufX) / breite) + Math.floor((y * verlaufY) / hoehe);
      for (let c = 0; c < 3; c++) {
        z = (Math.imul(1664525, z) + 1013904223) >>> 0;
        const rausch = ((z >>> 24) & 15) - 8;
        const v = b[c]! + verlauf + rausch;
        daten[i * 3 + c] = v < 0 ? 0 : v > 255 ? 255 : v;
      }
    }
  }
  return { daten, breite, hoehe, kanaele: 3 };
}

const Q_BREITE = 700;
const Q_HOEHE = 540;
const V_BREITE = 512;
const V_HOEHE = 384;

function pruefBild(): Bild {
  return formelBild(
    Q_BREITE,
    Q_HOEHE,
    20260917,
    (x, y) => {
      if (x >= 430 && x < 650 && y >= 55 && y < 380) return [238, 243, 249]; // Fensterfeld
      if ((x - 150) * (x - 150) + (y - 95) * (y - 95) < 2500) return [250, 248, 236]; // Lampe
      if (y * 3 < Q_HOEHE) return [150, 126, 96]; // Deckenholz
      if (y * 3 < 2 * Q_HOEHE) return [128, 126, 122]; // Wand
      return [74, 96, 62]; // Begruenung
    },
    20,
    12,
  );
}

function pruefVorbild(): Bild {
  return formelBild(
    V_BREITE,
    V_HOEHE,
    20260954,
    (x, y) => {
      if (x >= 300 && x < 470 && y >= 40 && y < 260) return [246, 240, 228]; // helles Feld
      if (y * 3 < V_HOEHE) return [180, 110, 70]; // kraeftiges, roetliches Holz
      if (y * 3 < 2 * V_HOEHE) return [136, 124, 112]; // Wand
      return [50, 110, 40]; // kraeftiges Gruen
    },
    16,
    10,
  );
}

/** Die drei Groessen je Bildpunkt, unabhaengig vom geprueften Modul gemessen. */
function hsvFelder(b: Bild): { h: Float64Array; s: Float64Array; v: Float64Array } {
  const n = b.breite * b.hoehe;
  const h = new Float64Array(n);
  const s = new Float64Array(n);
  const v = new Float64Array(n);
  const aus: [number, number, number] = [0, 0, 0];
  for (let i = 0; i < n; i++) {
    rgbZuHsv(
      Math.fround(b.daten[i * b.kanaele]! / 255),
      Math.fround(b.daten[i * b.kanaele + 1]! / 255),
      Math.fround(b.daten[i * b.kanaele + 2]! / 255),
      aus,
    );
    h[i] = aus[0];
    s[i] = aus[1];
    v[i] = aus[2];
  }
  return { h, s, v };
}

/**
 * Was sich zwischen zwei Bildern in den drei Groessen bewegt hat — gemessen
 * OHNE das gepruefte Modul, damit der Bericht des Moduls selbst ueberpruefbar
 * ist und nicht die Probe stellt.
 */
function bewegung(a: Bild, b: Bild) {
  const fa = hsvFelder(a);
  const fb = hsvFelder(b);
  const n = a.breite * a.hoehe;
  let hMax = 0;
  let sMax = 0;
  let vMax = 0;
  let hN = 0;
  let sN = 0;
  let vN = 0;
  let gemessen = 0;
  for (let i = 0; i < n; i++) {
    const ds = Math.abs(fb.s[i]! - fa.s[i]!) * 255;
    const dv = Math.abs(fb.v[i]! - fa.v[i]!) * 255;
    if (ds > sMax) sMax = ds;
    if (dv > vMax) vMax = dv;
    if (ds > 0) sN++;
    if (dv > 0) vN++;
    if (fa.s[i]! >= FARBTON_MESSGRENZE && fb.s[i]! >= FARBTON_MESSGRENZE) {
      gemessen++;
      const dh = Math.abs(kuerzesteDrehung(fa.h[i]!, fb.h[i]!));
      if (dh > hMax) hMax = dh;
      if (dh > 0) hN++;
    }
  }
  return {
    farbtonMax: hMax,
    farbtonBewegt: hN,
    farbtonGemessen: gemessen,
    saettigungMax: sMax,
    saettigungBewegt: sN,
    helligkeitMax: vMax,
    helligkeitBewegt: vN,
  };
}

// ===========================================================================
// 1 · Die Anker
// ===========================================================================

describe('A10 · die Kennzahlen des Moduls stehen fest', () => {
  it('die Namenslisten haben genau diese Eintraege', () => {
    // Warum es genau DREI Eigenschaften sind und nicht die sechs des Zurufs,
    // steht im Kopf des Moduls. Wer eine vierte erfindet, ohne dass sie aus
    // einem fertigen Bild ablesbar waere, wird hier rot.
    expect([...EIGENSCHAFTEN]).toEqual(['farbton', 'saettigung', 'helligkeit']);
    expect([...BEREICHE]).toEqual([
      'ganzesBild',
      'deckenholz',
      'bewuchs',
      'helleFlaechen',
      'eigeneMaske',
    ]);
    expect(UEBERNAHME_KENNLINIE_PUNKTE).toBe(256);
    expect(SAT_TOR_SCHWELLE).toBe(0.02);
    expect(SAT_TOR_FLANKE).toBe(0.04);
    expect(FARBTON_MESSGRENZE).toBe(0.05);
  });

  it('jeder Name traegt eine Beschriftung UND einen Vorbehalt', () => {
    // Ein Bereich ohne Vorbehalt ist der Anfang einer Attrappe: «Decke» klaenge
    // nach einem Bauteil. Die Liste muss vollstaendig sein, nicht ungefaehr.
    for (const e of EIGENSCHAFTEN) expect(UEBERNAHME_EIGENSCHAFT_LABEL[e].length).toBeGreaterThan(3);
    for (const b of BEREICHE) {
      expect(UEBERNAHME_BEREICH_LABEL[b].length).toBeGreaterThan(3);
      expect(UEBERNAHME_BEREICH_VORBEHALT[b].length).toBeGreaterThan(40);
    }
    // Die gemessene Zahl aus `belichtung.ts` steht woertlich im Vorbehalt der
    // Lichter-Maske — sie ist der Grund, warum sie NICHT «Kuechenfront» heisst.
    expect(UEBERNAHME_BEREICH_VORBEHALT.helleFlaechen).toContain('83.2 %');
    expect(UEBERNAHME_BEREICH_VORBEHALT.helleFlaechen).toContain('Kein Bauteil');
  });

  it('die Zusage steht woertlich so da — und mit Umlauten', () => {
    expect(UEBERNAHME_WAS_GEAENDERT_WURDE).toBe(
      'nur die benannten Eigenschaften in den benannten Bereichen; jede nicht benannte Eigenschaft ' +
        'und jeder Bildpunkt ausserhalb bleiben Byte für Byte gleich, kein Bildpunkt wandert, ' +
        'nichts entsteht, nichts verschwindet',
    );
    // Wie bei `belichtung.ts`: der Owner LIEST diesen Satz im Inspektor.
    expect(UEBERNAHME_WAS_GEAENDERT_WURDE).toContain('für');
    expect(UEBERNAHME_EIGENSCHAFT_LABEL.saettigung).toBe('Sättigung');
  });

  it('kein Name kollidiert mit den drei Nachbarn', () => {
    // WARUM DAS EINE ECHTE GEFAHR IST: `src/index.ts` reicht die Bild-Module
    // mit `export *` heraus. Bei doppelten Namen faellt das Ergebnis in
    // ECMAScript still auf `undefined` — erst beim naechsten Aufrufer
    // sichtbar. `farbangleich.ts` hat bereits ein `KENNLINIE_PUNKTE` und ein
    // `WAS_GEAENDERT_WURDE`; darum traegt hier alles den Praefix.
    const namen = (m: object): Set<string> => new Set(Object.keys(m));
    const meine = namen(uebernahmeModul);
    expect(meine.size).toBeGreaterThan(8);
    for (const fremd of [farbangleichModul, nachbearbeitungModul, belichtungModul]) {
      for (const n of meine) {
        expect(namen(fremd).has(n), `${n} kollidiert mit einem Nachbarmodul`).toBe(false);
      }
    }
  });
});

// ===========================================================================
// 2 · Haben beide Seiten dasselbe Bild in der Hand?
// ===========================================================================

describe('A10 · die zwei Pruefbilder', () => {
  it('Bild und Vorbild tragen den Fingerabdruck der Zweitrechnung', () => {
    // OHNE DIESE PROBE IST DER GANZE REST WERTLOS: verglichen wuerden dann
    // zwei verschiedene Bilder, und jede Abweichung waere unlesbar.
    const q = pruefBild();
    const v = pruefVorbild();
    expect(q.breite * q.hoehe).toBe(378000);
    expect(v.breite * v.hoehe).toBe(196608);
    expect(fnv1a(q.daten)).toBe(135893599);
    expect(byteSumme(q.daten)).toBe(167143408);
    expect(fnv1a(v.daten)).toBe(255828894);
    expect(byteSumme(v.daten)).toBe(80658791);
  });
});

// ===========================================================================
// 3 · Die neun Faelle gegen die Zweitrechnung
// ===========================================================================

/**
 * Die Zahlen dieser Tabelle sind die der Zweitrechnung. Fingerabdruck und
 * Bytesumme sind das schaerfste Mass, das es gibt: sie fallen bei EINEM Byte
 * Unterschied auf 378 000 Bildpunkten.
 */
const FAELLE = [
  {
    name: 'S1 — nur die Saettigung, nur an der Decke',
    posten: [{ eigenschaft: 'saettigung', bereich: 'deckenholz' }],
    fnv: 1950757129,
    summe: 164176254,
    ausserhalb: 74.78571428571429,
    unveraendert: 76.64232804232805,
    ueberlappung: 0,
  },
  {
    name: 'S2 — nur der Farbton, nur an der Decke',
    posten: [{ eigenschaft: 'farbton', bereich: 'deckenholz' }],
    fnv: 3110374554,
    summe: 166604705,
    ausserhalb: 74.78571428571429,
    unveraendert: 78.40899470899471,
    ueberlappung: 0,
  },
  {
    name: 'S3 — nur die Helligkeit, nur in den hellen Flaechen',
    posten: [{ eigenschaft: 'helligkeit', bereich: 'helleFlaechen' }],
    fnv: 4213165199,
    summe: 166896460,
    ausserhalb: 76.4962962962963,
    unveraendert: 98.68571428571428,
    ueberlappung: 0,
  },
  {
    name: 'S4 — «die saettigung und farbe der decke», also zwei Posten an einem Bereich',
    posten: [
      { eigenschaft: 'saettigung', bereich: 'deckenholz' },
      { eigenschaft: 'farbton', bereich: 'deckenholz' },
    ],
    fnv: 1130143488,
    summe: 163319753,
    ausserhalb: 74.78571428571429,
    unveraendert: 76.62486772486773,
    ueberlappung: 25.214285714285715,
  },
  {
    name: 'S5 — nur die Helligkeit, aber ueber das ganze Bild',
    posten: [{ eigenschaft: 'helligkeit', bereich: 'ganzesBild' }],
    fnv: 278368245,
    summe: 176334598,
    ausserhalb: 0,
    unveraendert: 20.383333333333333,
    ueberlappung: 0,
  },
  {
    name: 'S6 — die Saettigung des Bewuchses, aber nur halb',
    posten: [{ eigenschaft: 'saettigung', bereich: 'bewuchs', staerke: 0.5 }],
    fnv: 924913661,
    summe: 163992070,
    ausserhalb: 61.81428571428571,
    unveraendert: 66.62645502645502,
    ueberlappung: 0,
  },
  {
    name: 'S7 — zwei Eigenschaften in zwei verschiedenen Bereichen',
    posten: [
      { eigenschaft: 'saettigung', bereich: 'deckenholz' },
      { eigenschaft: 'farbton', bereich: 'bewuchs' },
    ],
    fnv: 344566463,
    summe: 163453696,
    ausserhalb: 37.120899470899474,
    unveraendert: 42.144708994709,
    ueberlappung: 0.5208994708994709,
  },
  {
    name: 'S8 — zwei Saettigungs-Posten, deren Bereiche einander UEBERLAPPEN',
    posten: [
      { eigenschaft: 'saettigung', bereich: 'ganzesBild', staerke: 0.5 },
      { eigenschaft: 'saettigung', bereich: 'deckenholz', staerke: 0.5 },
    ],
    fnv: 2114908069,
    summe: 159516362,
    ausserhalb: 0,
    unveraendert: 20.13148148148148,
    ueberlappung: 25.214285714285715,
  },
  {
    name: 'S9 — dasselbe fuer die Helligkeit: zwei Posten, ueberlappende Bereiche',
    posten: [
      { eigenschaft: 'helligkeit', bereich: 'ganzesBild', staerke: 0.5 },
      { eigenschaft: 'helligkeit', bereich: 'helleFlaechen', staerke: 0.5 },
    ],
    fnv: 828939040,
    summe: 171748935,
    ausserhalb: 0,
    unveraendert: 20.383333333333333,
    ueberlappung: 23.503703703703703,
  },
] as const;

describe('A10 · neun Faelle, Byte fuer Byte gegen die Zweitrechnung', () => {
  for (const fall of FAELLE) {
    it(fall.name, () => {
      const e = uebernahme(pruefBild(), pruefVorbild(), { posten: fall.posten as never });
      expect(fnv1a(e.bild.daten)).toBe(fall.fnv);
      expect(byteSumme(e.bild.daten)).toBe(fall.summe);
      expect(e.bericht.ausserhalbProzent).toBeCloseTo(fall.ausserhalb, 10);
      expect(e.bericht.unveraenderteBildpunkteProzent).toBeCloseTo(fall.unveraendert, 10);
      expect(e.bericht.ueberlappungProzent).toBeCloseTo(fall.ueberlappung, 10);
      expect(e.bericht.bild).toEqual([700, 540]);
      expect(e.bericht.vorbild).toEqual([512, 384]);
      expect(e.bericht.posten).toHaveLength(fall.posten.length);
      expect(e.bericht.wasGeaendertWurde).toBe(UEBERNAHME_WAS_GEAENDERT_WURDE);
    });
  }
});

// ===========================================================================
// 4 · «und nur diese» — die Zusage als Zahl
// ===========================================================================

describe('A10 · was NICHT benannt ist, bewegt sich nicht', () => {
  it('Farbton uebernehmen laesst Saettigung und Helligkeit an 378 000 Punkten EXAKT stehen', () => {
    // DIE ZENTRALE PROBE DER GANZEN ZEILE. Gemessen wird ausserhalb des
    // Moduls, aus den ausgegebenen Bytes: nicht ein einziger Bildpunkt
    // aendert seine Saettigung oder seine Helligkeit.
    const q = pruefBild();
    const e = uebernahme(q, pruefVorbild(), {
      posten: [{ eigenschaft: 'farbton', bereich: 'deckenholz' }],
    });
    const b = bewegung(q, e.bild);
    expect(b.saettigungBewegt).toBe(0);
    expect(b.saettigungMax).toBe(0);
    expect(b.helligkeitBewegt).toBe(0);
    expect(b.helligkeitMax).toBe(0);
    // Und der Farbton hat sich sehr wohl bewegt — sonst waere die Null oben
    // kein Befund, sondern ein Werkzeug, das gar nichts tut.
    expect(b.farbtonBewegt).toBe(81614);
    expect(b.farbtonMax).toBeCloseTo(12.307703018188477, 9);
    // Der Bericht des Moduls sagt dasselbe wie die Messung von aussen.
    expect(e.bericht.eigenschaftenGesamt.saettigung.bildpunkteBewegt).toBe(0);
    expect(e.bericht.eigenschaftenGesamt.helligkeit.bildpunkteBewegt).toBe(0);
    expect(e.bericht.eigenschaftenGesamt.farbton.bildpunkteBewegt).toBe(81614);
  });

  it('Saettigung uebernehmen laesst die Helligkeit EXAKT stehen — der Farbton ruehrt sich nur um die Rundung', () => {
    const q = pruefBild();
    const e = uebernahme(q, pruefVorbild(), {
      posten: [{ eigenschaft: 'saettigung', bereich: 'deckenholz' }],
    });
    const b = bewegung(q, e.bild);
    expect(b.helligkeitBewegt).toBe(0);
    expect(b.helligkeitMax).toBe(0);
    expect(b.saettigungMax).toBeCloseTo(67.88960427045822, 9);
    // UNBESCHOENIGT: der Farbton bleibt NICHT bitgleich. Er wandert an
    // 86 739 Punkten um hoechstens 2.5 Grad — das ist die Rundung auf ganze
    // Bytes, nicht die Rechnung. Genau darum steht die Zahl im Bericht,
    // statt dass ein Satz «der Farbton bleibt» behauptet wuerde.
    expect(b.farbtonBewegt).toBe(86739);
    expect(b.farbtonMax).toBeCloseTo(2.5, 9);
  });

  it('Helligkeit uebernehmen bewegt Farbton und Saettigung nur um die Rundung', () => {
    const q = pruefBild();
    const e = uebernahme(q, pruefVorbild(), {
      posten: [{ eigenschaft: 'helligkeit', bereich: 'ganzesBild' }],
    });
    const b = bewegung(q, e.bild);
    expect(b.helligkeitMax).toBeCloseTo(55.99999666213989, 9);
    // Ein Byte Rundung auf dem groessten Kanal schlaegt hier auf die
    // Saettigung durch — hoechstens 1.19 Byte-Schritte, ueber das ganze Bild.
    expect(b.saettigungMax).toBeCloseTo(1.1805586516857147, 9);
    expect(b.farbtonMax).toBeCloseTo(5.333343505859375, 9);
  });

  it('ausserhalb des Bereichs ist KEIN Byte anders — und das haelt auch bei zwei Bereichen', () => {
    // Die raeumliche Haelfte der Zusage. Gemessen wird sie nicht am Bericht,
    // sondern an der Maske selbst: wo alle Masken null sind, muessen die drei
    // Bytes gleich sein.
    const q = pruefBild();
    const e = uebernahme(q, pruefVorbild(), {
      posten: [
        { eigenschaft: 'saettigung', bereich: 'deckenholz' },
        { eigenschaft: 'farbton', bereich: 'bewuchs' },
      ],
    });
    const decke = bereichsMaske('deckenholz', q);
    const gruen = bereichsMaske('bewuchs', q);
    const n = q.breite * q.hoehe;
    let draussen = 0;
    let verletzt = 0;
    for (let i = 0; i < n; i++) {
      if (decke[i]! > 0 || gruen[i]! > 0) continue;
      draussen++;
      for (let c = 0; c < 3; c++) {
        if (e.bild.daten[i * 3 + c] !== q.daten[i * 3 + c]) {
          verletzt++;
          break;
        }
      }
    }
    expect(draussen).toBe(140317); // 37.12 % von 378 000
    expect(verletzt).toBe(0);
    // Und die Gegenprobe zur Gegenprobe: INNERHALB hat sich sehr wohl etwas
    // getan, sonst waere die Null oben die Null eines Werkzeugs, das schlaeft.
    // 218 693 ist die Gegenzahl zu den 42.144708994709 % der Zweitrechnung
    // (378 000 x 0.57855291005291) — sie ist nicht hier nachgemessen, sondern
    // dort gerechnet.
    expect(veraenderteBildpunkte(q, e.bild)).toBe(218693);
  });

  it('Staerke 0 heisst wirklich nichts: kein einziges Byte bewegt sich', () => {
    // Der Bildpunkt wird dann KOPIERT und nicht durch HSV und zurueck
    // geschickt. Ohne diesen Weg kaeme die Rundung des Hin- und Rueckwegs
    // dazwischen, und «nichts tun» waere nicht mehr bytegleich mit nichts tun.
    const q = pruefBild();
    const e = uebernahme(q, pruefVorbild(), {
      posten: [{ eigenschaft: 'saettigung', bereich: 'ganzesBild', staerke: 0 }],
    });
    expect(fnv1a(e.bild.daten)).toBe(fnv1a(q.daten));
    expect(veraenderteBildpunkte(q, e.bild)).toBe(0);
    expect(e.bericht.ausserhalbProzent).toBe(100);
    expect(e.bericht.unveraenderteBildpunkteProzent).toBe(100);
    // Der Posten wird trotzdem BERICHTET — die Kennlinie ist gerechnet, und
    // der Bericht sagt, was passiert waere.
    expect(e.bericht.posten[0]!.staerke).toBe(0);
    expect(e.bericht.posten[0]!.kennlinie).toHaveLength(256);
  });
});

// ===========================================================================
// 5 · Der Unterschied zum Farbangleich — der ganze Punkt der Zeile
// ===========================================================================

describe('A10 · Zeile 54 gegen Zeile 55: Auswahl gegen das Ganze', () => {
  it('der Farbangleich bewegt ALLE DREI Groessen, die Uebernahme genau EINE', () => {
    // «sry nur decke uebernehmen» (08:00) ist die Berichtigung von «nutze sie
    // um einen grund ai imaging layer zu erstellen» (07:16). Dieser Satz ist
    // hier eine Zahl.
    const q = pruefBild();
    const v = pruefVorbild();

    const ganz = bewegung(q, farbangleich(q, v).bild);
    expect(ganz.farbtonBewegt).toBe(271881);
    expect(ganz.saettigungBewegt).toBe(332679);
    expect(ganz.helligkeitBewegt).toBe(286852);

    const nurFarbton = bewegung(
      q,
      uebernahme(q, v, { posten: [{ eigenschaft: 'farbton', bereich: 'deckenholz' }] }).bild,
    );
    expect(nurFarbton.farbtonBewegt).toBe(81614);
    expect(nurFarbton.saettigungBewegt).toBe(0);
    expect(nurFarbton.helligkeitBewegt).toBe(0);

    // Und in der Flaeche: der Farbangleich laesst 12 % des Bildes unberuehrt,
    // die Uebernahme 78 %.
    expect(veraenderteBildpunkte(q, farbangleich(q, v).bild)).toBe(332679);
    expect(veraenderteBildpunkte(q, uebernahme(q, v, {
      posten: [{ eigenschaft: 'farbton', bereich: 'deckenholz' }],
    }).bild)).toBe(81614);
  });
});

// ===========================================================================
// 6 · Die Bereiche — gemessen am laufenden Nachbarn, nicht am Quelltext
// ===========================================================================

describe('A10 · die kopierten Masken stimmen mit denen von nachbearbeitung.ts ueberein', () => {
  it('die Deckenmaske: aus dem Nachbarn zurueckgerechnet, hoechstens 0.005 Unterschied', () => {
    // WIE DIE MESSUNG GEHT: `nachbearbeitung(bild, { decke: 0 })` multipliziert
    // jeden Bildpunkt mit `1 - maske`. Aus Ein- und Ausgabe laesst sich die
    // Maske also zurueckrechnen — das ist eine Messung AM LAUFENDEN NACHBARN
    // und keine zweite Lesung desselben Quelltexts.
    //
    // `gruen: 1.0` laesst den zweiten Griff untaetig; was von ihm bleibt, ist
    // der Hin- und Rueckweg durch HSV, und der kostet hoechstens ein Byte.
    const q = pruefBild();
    const nach = nachbearbeitung(q, { decke: 0, gruen: 1.0 });
    const meine = bereichsMaske('deckenholz', q);
    const n = q.breite * q.hoehe;
    let groesster = 0;
    let gemessen = 0;
    for (let i = 0; i < n; i++) {
      // Nur an hellen Punkten ist die Ruckrechnung genau: bei Eingabewert 20
      // traegt ein Byte Rundung schon 2.5 % Maskenfehler.
      const ein = q.daten[i * 3]!;
      if (ein < 120) continue;
      gemessen++;
      const raus = nach.bild.daten[i * 3]!;
      const zurueck = 1 - raus / ein;
      const d = Math.abs(zurueck - meine[i]!);
      if (d > groesster) groesster = d;
    }
    expect(gemessen).toBeGreaterThan(200000);
    expect(groesster).toBeLessThan(0.005);
    // Gegenprobe: die Maske ist nicht ueberall dasselbe, sonst haette der
    // Vergleich oben nichts zu sagen. Die 52 694 sind die Stichprobengroesse
    // der Zweitrechnung und damit eine Zahl von aussen — nicht eine hier
    // nachgemessene.
    let ueberHalb = 0;
    let leer = 0;
    for (let i = 0; i < n; i++) {
      if (meine[i]! > 0.5) ueberHalb++;
      if (meine[i]! < 0.001) leer++;
    }
    expect(ueberHalb).toBe(52694);
    expect(leer).toBeGreaterThan(200000);
  });

  it('die Gruenmaske: an einem Farbton-Saettigungs-Feld zurueckgerechnet', () => {
    // EIGENES PRUEFFELD, und zwar mit Absicht: an einem Innenraumbild liegt die
    // Flanke der Gruenmaske in wenigen Bildpunkten, und die Ruckrechnung
    // saehe sie kaum. Dieses Feld faehrt den Farbton in 360 Spalten einmal
    // ganz herum und die Saettigung in 100 Zeilen von 0.25 bis 0.95 — die
    // Flanken bei 58 und 187 Grad sind darin voll ausgefahren.
    const breite = 360;
    const hoehe = 100;
    const daten = new Uint8Array(breite * hoehe * 3);
    for (let y = 0; y < hoehe; y++) {
      for (let x = 0; x < breite; x++) {
        const ton = x;
        const sat = 0.25 + (0.7 * y) / (hoehe - 1);
        const v = 0.75;
        const c = v * sat;
        const hh = ton / 60;
        const xx = c * (1 - Math.abs((hh % 2) - 1));
        const m = v - c;
        const teil = Math.floor(hh) % 6;
        const rgb =
          teil === 0 ? [c, xx, 0] : teil === 1 ? [xx, c, 0] : teil === 2 ? [0, c, xx]
          : teil === 3 ? [0, xx, c] : teil === 4 ? [xx, 0, c] : [c, 0, xx];
        const i = y * breite + x;
        for (let k = 0; k < 3; k++) daten[i * 3 + k] = Math.round((rgb[k]! + m) * 255);
      }
    }
    const feld: Bild = { daten, breite, hoehe, kanaele: 3 };
    const meine = bereichsMaske('bewuchs', feld);
    // `decke: 1` laesst den ersten Griff untaetig; `gruen: 1.8` hebt die
    // Saettigung um `0.8 * maske`, woraus sich die Maske zurueckrechnen laesst.
    const nach = nachbearbeitung(feld, { decke: 1.0, gruen: 1.8 });
    const vor = hsvFelder(feld);
    const hinterher = hsvFelder(nach.bild);
    let groesster = 0;
    let gemessen = 0;
    for (let i = 0; i < breite * hoehe; i++) {
      if (vor.s[i]! < 0.4) continue; // unten ist die Ruckrechnung zu grob
      if (hinterher.s[i]! > 0.95) continue; // dort klemmt die Saettigung
      gemessen++;
      const zurueck = (hinterher.s[i]! / vor.s[i]! - 1) / 0.8;
      const d = Math.abs(zurueck - meine[i]!);
      if (d > groesster) groesster = d;
    }
    expect(gemessen).toBeGreaterThan(8000);
    expect(groesster).toBeLessThan(0.05);
    // Und an den zwei Pruefbildern: die Stichprobengroesse des Bereichs
    // «bewuchs» ist die der Zweitrechnung.
    let ueberHalb = 0;
    const amBild = bereichsMaske('bewuchs', pruefBild());
    for (let i = 0; i < amBild.length; i++) if (amBild[i]! > 0.5) ueberHalb++;
    expect(ueberHalb).toBe(125221);
    // Und die Maske trifft wirklich nur das Gruen: bei 0 Grad (Rot) null, bei
    // 120 Grad (Gruen) eins.
    expect(meine[99 * breite + 0]!).toBeCloseTo(0, 6);
    expect(meine[99 * breite + 120]!).toBeCloseTo(1, 6);
    expect(meine[99 * breite + 240]!).toBeCloseTo(0, 6); // Blau
  });

  it('die Lichter-Maske ist die umgedrehte Maske von belichtung.ts', () => {
    // Hier ist NICHTS kopiert — `schutzMaske` wird importiert. Die Probe haelt
    // trotzdem fest, in welche Richtung sie zeigt: unter dem Knie null, ueber
    // dem Knie eins. Wer die Richtung dreht, faerbt beim naechsten Mal die
    // Schatten statt der Lichter.
    const punkte: number[][] = [];
    for (let i = 0; i < 256; i++) punkte.push([i, i, i]);
    const daten = new Uint8Array(256 * 3);
    for (let i = 0; i < 256; i++) for (let c = 0; c < 3; c++) daten[i * 3 + c] = punkte[i]![c]!;
    const grau: Bild = { daten, breite: 256, hoehe: 1, kanaele: 3 };
    const m = bereichsMaske('helleFlaechen', grau);
    expect(m[0]!).toBe(0);
    expect(m[Math.round(0.5 * 255)]!).toBe(0); // deutlich unter dem Knie 0.66
    expect(m[255]!).toBe(1);
    expect(m[Math.round(0.95 * 255)]!).toBe(1); // ueber dem Knie 0.92
    // Und dazwischen laeuft sie WEICH — eine harte Kante saehe man als Linie.
    const mitte = m[Math.round(0.79 * 255)]!;
    expect(mitte).toBeGreaterThan(0.3);
    expect(mitte).toBeLessThan(0.7);
  });
});

// ===========================================================================
// 7 · Reihenfolge, Grau, eigene Maske
// ===========================================================================

describe('A10 · die Rechnung haelt sich an ihre eigenen Zusagen', () => {
  it('bei getrennten Bereichen ist die Reihenfolge der Posten egal', () => {
    // Weil alle Zielwerte VOR dem ersten Schreiben aus den unveraenderten
    // Bildern kommen. Waere das nicht so, verschoebe der erste Posten dem
    // zweiten die Grundlage — und zwei Aufrufe derselben Bestellung gaeben
    // zwei verschiedene Bilder.
    const q = pruefBild();
    const v = pruefVorbild();
    const a = uebernahme(q, v, {
      posten: [
        { eigenschaft: 'saettigung', bereich: 'deckenholz' },
        { eigenschaft: 'farbton', bereich: 'bewuchs' },
      ],
    });
    const b = uebernahme(q, v, {
      posten: [
        { eigenschaft: 'farbton', bereich: 'bewuchs' },
        { eigenschaft: 'saettigung', bereich: 'deckenholz' },
      ],
    });
    expect(fnv1a(b.bild.daten)).toBe(fnv1a(a.bild.daten));
    expect(fnv1a(a.bild.daten)).toBe(344566463);
    // EHRLICH DAZU: die zwei Bereiche ueberschneiden sich auf 0.52 % der
    // Flaeche, und dort wirken zwei Posten auf denselben Punkt — aber auf
    // VERSCHIEDENE Groessen (Saettigung und Farbton), die einander nicht
    // lesen. Der Bericht nennt die Ueberlappung trotzdem.
    expect(a.bericht.ueberlappungProzent).toBeCloseTo(0.5208994708994709, 10);
  });

  it('bei ZWEI Posten auf DERSELBEN Groesse zaehlt die Reihenfolge — und das steht so da', () => {
    // DIE EHRLICHE GRENZE DER ZUSAGE OBEN. Die Zielwerte kommen aus dem
    // unveraenderten Bild, der Mischpartner ist der laufende Wert — greifen
    // zwei Posten DIESELBE Groesse an DERSELBEN Stelle an, kommt es darum auf
    // die Reihenfolge an. Der Bericht meldet die Ueberlappung (25.2 %); die
    // Zusage sagt «solange ihre Bereiche einander nicht ueberlappen», und
    // diese Probe haelt beides fest.
    //
    // SIE IST AUSSERDEM DIE EINZIGE, DIE MERKT, wenn der Zielwert nicht mehr
    // aus dem Original kommt: gemessen mit einer Verfaelschung
    // (`aufKennlinie(q.s[i]!, …)` -> `aufKennlinie(s, …)`) blieben ALLE
    // anderen 35 Proben gruen, weil in ihnen kein Bildpunkt zweimal
    // angefasst wird.
    const q = pruefBild();
    const v = pruefVorbild();
    const a = uebernahme(q, v, {
      posten: [
        { eigenschaft: 'saettigung', bereich: 'ganzesBild', staerke: 0.5 },
        { eigenschaft: 'saettigung', bereich: 'deckenholz', staerke: 0.5 },
      ],
    });
    const b = uebernahme(q, v, {
      posten: [
        { eigenschaft: 'saettigung', bereich: 'deckenholz', staerke: 0.5 },
        { eigenschaft: 'saettigung', bereich: 'ganzesBild', staerke: 0.5 },
      ],
    });
    // Beide Zahlen stammen aus der Zweitrechnung.
    expect(fnv1a(a.bild.daten)).toBe(2114908069);
    expect(byteSumme(a.bild.daten)).toBe(159516362);
    expect(fnv1a(b.bild.daten)).toBe(3812810679);
    expect(byteSumme(b.bild.daten)).toBe(159492872);
    expect(fnv1a(a.bild.daten)).not.toBe(fnv1a(b.bild.daten));
    // Der ZIELWERT beider Posten haengt NICHT an der Reihenfolge — er kommt
    // aus dem unveraenderten Bild. Nur der Mischpartner tut es.
    expect(a.bericht.posten[0]!.wertVorbild).toBeCloseTo(97.60876, 4);
    expect(b.bericht.posten[1]!.wertVorbild).toBeCloseTo(97.60876, 4);
    expect(a.bericht.posten[1]!.wertVorher).toBeCloseTo(86.55775582752736, 9);
    expect(b.bericht.posten[0]!.wertVorher).toBeCloseTo(86.55775582752736, 9);
  });

  it('der Weg RGB → HSV → RGB verliert kein Byte — die Zusage steht darauf', () => {
    // WORAUF DIE ZUSAGE «ausserhalb bleibt Byte fuer Byte gleich» WIRKLICH
    // RUHT: das Modul kopiert unberuehrte Bildpunkte, statt sie zu rechnen.
    // Gemessen wurde aber auch, was passierte, wenn es das NICHT taete —
    // ueber ALLE 16 777 216 Farben des 8-Bit-Raums: **null** Farben aendern
    // sich auf dem Weg durch HSV und zurueck, groesste Abweichung 0 Byte.
    //
    // DARUM IST EINE VERFAELSCHUNG DES KOPIERWEGS STUMPF: nimmt man das
    // `continue` heraus, bleiben alle Proben gruen — nicht weil sie schwach
    // waeren, sondern weil an dieser Schraube nichts haengt (Muster 7 der
    // Anleitung). Der Kopierweg bleibt trotzdem: er macht aus einer
    // gemessenen Eigenschaft der Nachbarmodule eine Eigenschaft DIESES
    // Ablaufs — und er spart die Rechnung.
    //
    // Hier laeuft der volle Wuerfel nicht (vier Minuten); geprueft wird der
    // 16-Stufen-Wuerfel, 4096 Farben, dieselbe Rechnung.
    const hsv: [number, number, number] = [0, 0, 0];
    const rgb: [number, number, number] = [0, 0, 0];
    let anders = 0;
    for (let i = 0; i < 4096; i++) {
      const ein = [((i >> 8) & 15) * 17, ((i >> 4) & 15) * 17, (i & 15) * 17];
      rgbZuHsv(
        Math.fround(ein[0]! / 255),
        Math.fround(ein[1]! / 255),
        Math.fround(ein[2]! / 255),
        hsv,
      );
      hsvZuRgb(hsv[0], hsv[1], hsv[2], rgb);
      for (let c = 0; c < 3; c++) {
        const x = Math.min(Math.max(rgb[c]!, 0), 1);
        const byte = Math.trunc(Math.fround(Math.fround(x * 255) + Math.fround(0.5)));
        if (byte !== ein[c]!) anders++;
      }
    }
    expect(anders).toBe(0);
  });

  it('Grau bleibt Grau: das Farblos-Tor erfindet keine Farbe', () => {
    // OHNE DAS TOR waere das hier Rot. Eine Saettigungs-Kennlinie, die 0 auf
    // 0.4 abbildet, macht aus jedem grauen Punkt einen mit Farbton 0.
    const grau = new Uint8Array(4 * 3);
    for (let i = 0; i < 4; i++) for (let c = 0; c < 3; c++) grau[i * 3 + c] = 100 + i * 20;
    const bild: Bild = { daten: grau, breite: 4, hoehe: 1, kanaele: 3 };
    const buntDaten = new Uint8Array(4 * 3);
    for (let i = 0; i < 4; i++) {
      buntDaten[i * 3] = 200;
      buntDaten[i * 3 + 1] = 60;
      buntDaten[i * 3 + 2] = 40;
    }
    const bunt: Bild = { daten: buntDaten, breite: 4, hoehe: 1, kanaele: 3 };
    const e = uebernahme(bild, bunt, {
      posten: [{ eigenschaft: 'saettigung', bereich: 'ganzesBild' }],
    });
    for (let i = 0; i < 4 * 3; i++) expect(e.bild.daten[i]).toBe(grau[i]);
    expect(e.bericht.posten[0]!.farblosUebergangenProzent).toBe(100);
    // KLEIN, UND DAS IST HIER RICHTIG: das ist eine Eigenschaft je Bildpunkt,
    // sie haeuft sich nicht mit der Menge. Vier Punkte genuegen; die grossen
    // Proben oben messen das, was sich mit der Menge haeuft.
  });

  it('eine von aussen gelieferte Maske wirkt genau dort, wo sie steht', () => {
    // Das ist der Anschluss fuer Zeile 59 (Material-ID-Bild). Ohne ihn waere
    // «die Vorhangfarbe» fuer immer unerreichbar.
    const q = pruefBild();
    const n = q.breite * q.hoehe;
    const maske = new Float32Array(n);
    for (let y = 0; y < q.hoehe; y++) {
      for (let x = 0; x < q.breite; x++) maske[y * q.breite + x] = x < 350 ? 1 : 0;
    }
    const e = uebernahme(q, pruefVorbild(), {
      posten: [{ eigenschaft: 'helligkeit', bereich: 'eigeneMaske', maske }],
    });
    let rechtsVeraendert = 0;
    let linksVeraendert = 0;
    for (let y = 0; y < q.hoehe; y++) {
      for (let x = 0; x < q.breite; x++) {
        const i = y * q.breite + x;
        let anders = false;
        for (let c = 0; c < 3; c++) if (e.bild.daten[i * 3 + c] !== q.daten[i * 3 + c]) anders = true;
        if (!anders) continue;
        if (x < 350) linksVeraendert++;
        else rechtsVeraendert++;
      }
    }
    expect(rechtsVeraendert).toBe(0);
    expect(linksVeraendert).toBeGreaterThan(100000);
    expect(e.bericht.ausserhalbProzent).toBe(50);
    // Ohne Vorbildmaske wird das GANZE Vorbild gemessen — und der Bericht
    // sagt es, statt die Entscheidung still zu treffen.
    expect(e.bericht.posten[0]!.vorbildGanz).toBe(true);
    expect(e.bericht.posten[0]!.stichprobeVorbild).toBe(196608);
  });
});

// ===========================================================================
// 8 · Eine fehlende Zutat wird rot, nicht leer
// ===========================================================================

describe('A10 · Fehler melden sich, statt still durchzulaufen', () => {
  const q = () => pruefBild();
  const v = () => pruefVorbild();

  it('eine leere Postenliste ist ein Fehler', () => {
    expect(() => uebernahme(q(), v(), { posten: [] })).toThrow(/ohne Posten/);
  });

  it('ein unbekannter Name faellt nicht lautlos zu Boden', () => {
    // Muster 9 der Anleitung: ein Auftragsleser, der ein unbekanntes Feld mit
    // `.get()` liest, erzeugt Bestellungen, die niemand ausfuehrt.
    expect(() =>
      uebernahme(q(), v(), { posten: [{ eigenschaft: 'durchlaessigkeit' as never, bereich: 'ganzesBild' }] }),
    ).toThrow(/Unbekannte Eigenschaft/);
    expect(() =>
      uebernahme(q(), v(), { posten: [{ eigenschaft: 'farbton', bereich: 'vorhang' as never }] }),
    ).toThrow(/Unbekannter Bereich/);
  });

  it('«eigeneMaske» ohne Maske ist ein Fehler, keine leere Flaeche', () => {
    expect(() =>
      uebernahme(q(), v(), { posten: [{ eigenschaft: 'farbton', bereich: 'eigeneMaske' }] }),
    ).toThrow(/ohne Maske/);
  });

  it('eine Maske in der falschen Groesse wird nicht gedehnt', () => {
    expect(() =>
      uebernahme(q(), v(), {
        posten: [{ eigenschaft: 'farbton', bereich: 'eigeneMaske', maske: new Float32Array(10) }],
      }),
    ).toThrow(/nicht passt/);
  });

  it('ein Vorbild ohne Flaeche im Bereich wird gemeldet', () => {
    // Ein einfarbig graues Vorbild hat kein Deckenholz. Still das ganze Bild
    // zu nehmen waere genau die Sorte «falsches Ja», gegen die Muster 9 steht.
    const grau = new Uint8Array(64 * 3).fill(120);
    const leer: Bild = { daten: grau, breite: 8, hoehe: 8, kanaele: 3 };
    expect(() =>
      uebernahme(q(), leer, { posten: [{ eigenschaft: 'farbton', bereich: 'deckenholz' }] }),
    ).toThrow(/keine Fläche/);
  });
});

// ===========================================================================
// 9 · Die zwei kleinen Bausteine
// ===========================================================================

describe('A10 · Kennlinie und Winkel', () => {
  it('die geschlossene Auswertung trifft die binaere Suche ueber dasselbe Gitter', () => {
    // `aufKennlinie` rechnet die Stelle aus, statt sie zu suchen — weil das
    // Gitter gleichmaessig ist. Das ist eine Behauptung, und hier steht die
    // Gegenrechnung: dieselbe Kennlinie ueber das AUSGESCHRIEBENE Gitter
    // gesucht, wie `farbangleich.ts` es tut.
    const kl = new Float64Array(256);
    for (let j = 0; j < 256; j++) kl[j] = Math.sin(j / 40) * 0.4 + 0.5;
    const gitter = new Float64Array(256);
    const schritt = 1 / 255;
    for (let i = 0; i < 256; i++) gitter[i] = i * schritt;
    gitter[255] = 1;
    const gesucht = (x: number): number => {
      if (x > gitter[255]!) return kl[255]!;
      if (x < gitter[0]!) return kl[0]!;
      let lo = 0;
      let hi = 256;
      while (lo < hi) {
        const m = (lo + hi) >> 1;
        if (x >= gitter[m]!) lo = m + 1;
        else hi = m;
      }
      const j = lo - 1;
      if (j >= 255) return kl[255]!;
      if (gitter[j]! === x) return kl[j]!;
      return ((kl[j + 1]! - kl[j]!) / (gitter[j + 1]! - gitter[j]!)) * (x - gitter[j]!) + kl[j]!;
    };
    let groesster = 0;
    for (let k = 0; k <= 100000; k++) {
      const x = k / 100000;
      const d = Math.abs(aufKennlinie(x, kl) - gesucht(x));
      if (d > groesster) groesster = d;
    }
    expect(groesster).toBeLessThan(1e-12);
  });

  it('die Drehung nimmt den kuerzeren Weg — auch ueber die Naht bei Rot', () => {
    // 359 und 1 Grad sind ZWEI Grad auseinander, nicht 358. Wer das falsch
    // rechnet, dreht ein warmes Holz einmal durch das ganze Farbrad.
    expect(kuerzesteDrehung(359, 1)).toBeCloseTo(2, 12);
    expect(kuerzesteDrehung(1, 359)).toBeCloseTo(-2, 12);
    expect(kuerzesteDrehung(10, 200)).toBeCloseTo(-170, 12);
    expect(kuerzesteDrehung(200, 10)).toBeCloseTo(170, 12);
    expect(kuerzesteDrehung(0, 180)).toBeCloseTo(180, 12);
    expect(Math.abs(kuerzesteDrehung(0, 181))).toBeCloseTo(179, 12);
    for (let a = 0; a < 360; a += 7) {
      for (let b = 0; b < 360; b += 11) {
        expect(Math.abs(kuerzesteDrehung(a, b))).toBeLessThanOrEqual(180);
      }
    }
  });

  it('die Buendelung sagt, wieviel der gemittelte Farbton wert ist', () => {
    // Ein Bereich aus einem einzigen Farbton buendelt bei 1; ein Bereich aus
    // Gegenfarben nahe 0. Die Zahl steht im Bericht, statt dass ein fester
    // Grenzwert die schwache Aussage still verschluckt.
    const einTon = new Uint8Array(4 * 3);
    for (let i = 0; i < 4; i++) {
      einTon[i * 3] = 200;
      einTon[i * 3 + 1] = 80;
      einTon[i * 3 + 2] = 60;
    }
    const a: Bild = { daten: einTon, breite: 4, hoehe: 1, kanaele: 3 };
    const e = uebernahme(a, a, { posten: [{ eigenschaft: 'farbton', bereich: 'ganzesBild' }] });
    expect(e.bericht.posten[0]!.buendelungBild).toBeCloseTo(1, 9);
    expect(e.bericht.posten[0]!.drehungGrad).toBeCloseTo(0, 9);

    const gemischt = new Uint8Array(4 * 3);
    // Zwei Punkte Rot, zwei Punkte Tuerkis — Gegenfarben, der Zeiger hebt sich auf.
    for (const [i, rgb] of [[0, [220, 40, 40]], [1, [220, 40, 40]], [2, [40, 220, 220]], [3, [40, 220, 220]]] as const) {
      for (let c = 0; c < 3; c++) gemischt[i * 3 + c] = rgb[c]!;
    }
    const b: Bild = { daten: gemischt, breite: 4, hoehe: 1, kanaele: 3 };
    const e2 = uebernahme(b, b, { posten: [{ eigenschaft: 'farbton', bereich: 'ganzesBild' }] });
    expect(e2.bericht.posten[0]!.buendelungBild!).toBeLessThan(0.05);
  });
});
