/**
 * Nachbearbeitung — zwei gezielte Griffe ins fertige Bild: Deckenholz dunkler,
 * Gruen kraeftiger.
 *
 * WARUM AM BILD UND NICHT IM MODELL: beides sind Wuensche zur Anmutung, nicht
 * zur Konstruktion, und ein neuer Renderlauf kostet Minuten. Und warum
 * gerechnet statt generativ: beide Griffe bewegen KEINEN Bildpunkt von der
 * Stelle — sie aendern nur Helligkeit und Saettigung innerhalb einer
 * gemessenen Maske. Der generative Durchgang vom 10.09.2026 hat, obwohl nur
 * eine Flaeche bearbeitet werden sollte, nachweislich die Bepflanzung, das
 * Weinglas und Verdeckungen mitveraendert. Ein Bildmodell kann diese Zusage
 * nicht geben; diese Rechnung gibt sie aus ihrer Bauart heraus: jeder
 * Ausgabepunkt haengt nur vom Wert und der ZEILE desselben Eingabepunkts ab.
 *
 * DIE DECKENMASKE ist bewusst zweiteilig: die Lage allein wuerde den
 * Betontraeger und die weissen Waende mitnehmen, die Farbe allein die
 * Holzmoebel im unteren Bildteil. Nur wo BEIDES zutrifft — oben im Bild UND
 * warm getoent — wird abgedunkelt. Der Traeger ist grau (Rot minus Blau nahe
 * null) und faellt damit von selbst heraus.
 *
 * DIE GRUENMASKE greift ueber den Farbton, nicht ueber die Lage: die
 * Bepflanzung steht aussen am Fenster, spiegelt sich aber auch in den
 * Glasflaechen. Eine Ortsmaske wuerde die Spiegelungen verfehlen und das Bild
 * uneinheitlich machen.
 *
 * WAS DIE MASKEN ERFASSEN, STEHT IM BERICHT — beide Flaechenanteile und die
 * Werte vorher/nachher. Ohne diese Zahlen waere nicht nachpruefbar, ob eine
 * Maske das Richtige getroffen hat, und eine unsichtbare Maske ist eine
 * Behauptung.
 *
 * VORLAGE IST `kosmo-render/werkzeug/nachbearbeitung.py` (141 Zeilen). Diese
 * Fassung ist deren Uebersetzung, absichtlich Zahl fuer Zahl gleich; die
 * Proben in `test/bild-farbe.test.ts` messen gegen Bytes, die die
 * PYTHON-Fassung geschrieben hat.
 *
 * HSV IST HIER SELBST GEBAUT (`rgbZuHsv`/`hsvZuRgb`), ohne Bibliothek — die
 * Vorlage begruendet das mit «matplotlib waere eine Abhaengigkeit fuer drei
 * Zeilen», und im Kern gilt dasselbe schaerfer: er haengt an vier Paketen und
 * bekommt fuer eine Farbraumdrehung kein fuenftes.
 *
 * Zur `Math.fround`-Klammerung gilt Wort fuer Wort, was am Kopf von
 * `farbangleich.ts` steht: die Vorlage rechnet in `float32`, und nur wer das
 * nachbaut, kann eine Abweichung von einem Byte als Fehler LESEN statt sie
 * wegzuerklaeren.
 */

import type { Bild } from './farbangleich';
import { alsKanaele, ausKanaelen } from './farbangleich';

const f32 = Math.fround;

/** Vorgaben der Vorlage (`--decke`, `--gruen`, `--deckenhoehe`). */
export const DECKE_VORGABE = 0.88;
export const GRUEN_VORGABE = 1.2;
export const DECKENHOEHE_VORGABE = 0.34;

export interface NachbearbeitungOptionen {
  /** Helligkeitsfaktor im Kern der Deckenmaske; kleiner heisst dunkler. */
  decke?: number;
  /** Saettigungsfaktor im Kern der Gruenmaske; groesser heisst kraeftiger. */
  gruen?: number;
  /** Anteil der Bildhoehe, ueber den die Lagemaske von oben ausblendet. */
  deckenhoehe?: number;
}

export interface NachbearbeitungBericht {
  /** Breite und Hoehe, in dieser Reihenfolge — wie die Vorlage sie meldet. */
  bild: [number, number];
  decke: {
    faktor: number;
    hoeheAnteil: number;
    /** Anteil der Bildflaeche mit Maskenwert ueber 0.5, in Prozent. */
    erfassteFlaecheProzent: number;
    /** Mittelwert R/G/B in Byte-Schritten ueber die obersten 22 Prozent der Zeilen. */
    oberesFuenftelVorher: [number, number, number];
    oberesFuenftelNachher: [number, number, number];
  };
  gruen: {
    faktor: number;
    erfassteFlaecheProzent: number;
    /** Mit der Maske gewichtete mittlere Saettigung. */
    saettigungImGruenVorher: number;
    saettigungImGruenNachher: number;
  };
}

export interface NachbearbeitungErgebnis {
  bild: Bild;
  bericht: NachbearbeitungBericht;
}

/**
 * Sanfter Uebergang statt harter Kante (`smoothstep`) — sonst sieht man die
 * Maske als Linie im Bild.
 */
export function weich(x: number): number {
  const c = f32(Math.min(Math.max(x, 0), 1));
  return f32(f32(c * c) * f32(3 - f32(2 * c)));
}

/**
 * RGB (je 0..1) nach HSV; Farbton in Grad 0..360, Saettigung und Wert 0..1.
 *
 * ZUR REIHENFOLGE DER DREI FAELLE: die Vorlage schreibt nacheinander in drei
 * Masken (`h[rm] = ...; h[gm] = ...; h[bm] = ...`), und die Masken UEBERLAPPEN,
 * wenn zwei Kanaele gleichauf das Maximum halten. numpy laesst dann die
 * spaetere Zuweisung gewinnen — Blau schlaegt Gruen schlaegt Rot. Darum stehen
 * hier drei getrennte `if` und kein `else if`. Nachgerechnet liefern die
 * Zweige im Gleichstand denselben Wert. Das ist nicht bloss argumentiert,
 * sondern ausgezaehlt: ueber alle 97 920 Gleichstands-Faelle eines
 * 256-Stufen-Gitters stimmen die jeweils zustaendigen Zweige exakt ueberein,
 * Unterschied null. Die Reihenfolge aendert also nichts am Ergebnis — ein
 * `else if` hier bleibt von der Probe unbemerkt. Sie steht trotzdem so da,
 * weil sie in der Vorlage so steht und damit niemand sie fuer einen
 * Schreibfehler haelt und «aufraeumt».
 *
 * `aus` kann mitgegeben werden, damit die Schleife ueber ein Millionenbild
 * nicht fuer jeden Punkt ein Tripel anlegt.
 */
export function rgbZuHsv(
  r: number,
  g: number,
  b: number,
  aus: [number, number, number] = [0, 0, 0],
): [number, number, number] {
  const mx = Math.max(r, g, b);
  const mn = Math.min(r, g, b);
  const d = f32(mx - mn);
  let h = 0;
  if (d > 1e-9) {
    if (mx === r) {
      // `% 6` in numpy traegt das Vorzeichen des TEILERS, in JavaScript das des
      // Zaehlers: (g-b)/d kann negativ sein, und dann liegen die zwei Sprachen
      // um volle 6 auseinander (also um 360 Grad Farbton).
      const roh = f32(f32(g - b) / d);
      const rest = roh % 6;
      h = rest !== 0 && rest < 0 ? f32(rest + 6) : rest;
    }
    if (mx === g) h = f32(f32(f32(b - r) / d) + 2);
    if (mx === b) h = f32(f32(f32(r - g) / d) + 4);
  }
  aus[0] = f32(h * 60);
  aus[1] = mx > 1e-9 ? f32(d / Math.max(mx, f32(1e-9))) : 0;
  aus[2] = mx;
  return aus;
}

/** HSV zurueck nach RGB — die genaue Umkehrung von {@link rgbZuHsv}. */
export function hsvZuRgb(
  h: number,
  s: number,
  v: number,
  aus: [number, number, number] = [0, 0, 0],
): [number, number, number] {
  const hh = f32(h / 60);
  const unten = Math.floor(hh);
  let i = unten % 6;
  if (i < 0) i += 6;
  const f = f32(hh - unten);
  const p = f32(v * f32(1 - s));
  const q = f32(v * f32(1 - f32(s * f)));
  const t = f32(v * f32(1 - f32(s * f32(1 - f))));
  switch (i) {
    case 0: aus[0] = v; aus[1] = t; aus[2] = p; break;
    case 1: aus[0] = q; aus[1] = v; aus[2] = p; break;
    case 2: aus[0] = p; aus[1] = v; aus[2] = t; break;
    case 3: aus[0] = p; aus[1] = q; aus[2] = v; break;
    case 4: aus[0] = t; aus[1] = p; aus[2] = v; break;
    default: aus[0] = v; aus[1] = p; aus[2] = q; break;
  }
  return aus;
}

/**
 * Die zwei Griffe, in der Reihenfolge der Vorlage: erst die Decke abdunkeln,
 * dann — auf dem BEREITS abgedunkelten Bild — das Gruen kraeftigen. Die
 * Reihenfolge ist nicht beliebig: die Deckenmaske liest Rot minus Blau, und
 * eine vorher hochgezogene Saettigung wuerde diese Messung verschieben.
 */
export function nachbearbeitung(
  bild: Bild,
  optionen: NachbearbeitungOptionen = {},
): NachbearbeitungErgebnis {
  const decke = optionen.decke ?? DECKE_VORGABE;
  const gruenFaktor = optionen.gruen ?? GRUEN_VORGABE;
  const deckenhoehe = optionen.deckenhoehe ?? DECKENHOEHE_VORGABE;

  const [r, g, b] = alsKanaele(bild);
  const breite = bild.breite;
  const hoehe = bild.hoehe;

  // --- Deckenholz dunkler ---------------------------------------------------
  const dhF = f32(deckenhoehe);
  const nennerF = f32(Math.max(deckenhoehe, 1e-6));
  const abzugF = f32(1 - decke);
  const warmSchwelleF = f32(0.045);
  const warmBreiteF = f32(0.085);

  let erfasstDecke = 0;
  let obenZeilen = 0;
  const obenVorher: [number, number, number] = [0, 0, 0];
  const obenNachher: [number, number, number] = [0, 0, 0];

  for (let zeile = 0; zeile < hoehe; zeile++) {
    const y = f32(f32(zeile) / f32(hoehe));
    const lage = weich(f32(f32(dhF - y) / nennerF));
    // «Oberes Fuenftel» der Vorlage: die Zeilen unter 22 Prozent der Bildhoehe.
    // Das ist der BERICHTSAUSSCHNITT und nicht die Maske — er ist absichtlich
    // schmaler als `deckenhoehe`, damit die Zahl den Kern der Maske zeigt und
    // nicht deren Ausklang.
    const imBericht = y < 0.22;
    if (imBericht) obenZeilen++;
    for (let s = 0; s < breite; s++) {
      const i = zeile * breite + s;
      const ri = r[i]!;
      const gi = g[i]!;
      const bi = b[i]!;
      const waerme = weich(f32(f32(f32(ri - bi) - warmSchwelleF) / warmBreiteF));
      const maskeD = f32(lage * waerme);
      if (maskeD > 0.5) erfasstDecke++;
      const faktor = f32(1 - f32(maskeD * abzugF));
      const rn = f32(ri * faktor);
      const gn = f32(gi * faktor);
      const bn = f32(bi * faktor);
      if (imBericht) {
        obenVorher[0] += ri; obenVorher[1] += gi; obenVorher[2] += bi;
        obenNachher[0] += rn; obenNachher[1] += gn; obenNachher[2] += bn;
      }
      r[i] = rn;
      g[i] = gn;
      b[i] = bn;
    }
  }

  const obenPunkte = obenZeilen * breite || 1;
  const mittelBytes = (summe: [number, number, number]): [number, number, number] => [
    (summe[0] / obenPunkte) * 255,
    (summe[1] / obenPunkte) * 255,
    (summe[2] / obenPunkte) * 255,
  ];

  // --- Gruen kraeftiger -----------------------------------------------------
  // 70 bis 175 Grad ist Blattgruen; die Raender laufen ueber 12 Grad aus, damit
  // an Gelb und Tuerkis keine Kante entsteht. Die Flanken stehen darum bei 58
  // und 187 Grad — 12 Grad vor beziehungsweise hinter dem Kernbereich.
  const tonUnten = f32(58);
  const tonOben = f32(187);
  const tonFlanke = f32(12);
  // Nur was ueberhaupt Farbe hat — sonst wuerde Grau ins Gruene kippen.
  const satSchwelle = f32(0.05);
  const satFlanke = f32(0.1);
  const gruenAnstieg = f32(gruenFaktor - 1);

  const n = breite * hoehe;
  let erfasstGruen = 0;
  let maskeSumme = 0;
  let satVorherSumme = 0;
  let satNachherSumme = 0;
  const hsv: [number, number, number] = [0, 0, 0];
  const rgb: [number, number, number] = [0, 0, 0];

  for (let i = 0; i < n; i++) {
    rgbZuHsv(r[i]!, g[i]!, b[i]!, hsv);
    const ton = hsv[0];
    const sat = hsv[1];
    const tonMaske = f32(
      weich(f32(f32(ton - tonUnten) / tonFlanke)) * weich(f32(f32(tonOben - ton) / tonFlanke)),
    );
    const maskeG = f32(tonMaske * weich(f32(f32(sat - satSchwelle) / satFlanke)));
    if (maskeG > 0.5) erfasstGruen++;
    maskeSumme += maskeG;
    satVorherSumme += f32(sat * maskeG);
    const satNeu = Math.min(Math.max(f32(sat * f32(1 + f32(maskeG * gruenAnstieg))), 0), 1);
    satNachherSumme += f32(satNeu * maskeG);
    hsvZuRgb(ton, satNeu, hsv[2], rgb);
    r[i] = rgb[0];
    g[i] = rgb[1];
    b[i] = rgb[2];
  }

  const maskeNenner = Math.max(maskeSumme, 1e-6);

  return {
    // Die Vorlage rundet hier (`*255 + 0.5`), waehrend `farbangleich.py`
    // abschneidet — siehe `ausKanaelen`.
    bild: ausKanaelen([r, g, b], bild, false),
    bericht: {
      bild: [breite, hoehe],
      decke: {
        faktor: decke,
        hoeheAnteil: deckenhoehe,
        erfassteFlaecheProzent: (erfasstDecke / n) * 100,
        oberesFuenftelVorher: mittelBytes(obenVorher),
        oberesFuenftelNachher: mittelBytes(obenNachher),
      },
      gruen: {
        faktor: gruenFaktor,
        erfassteFlaecheProzent: (erfasstGruen / n) * 100,
        saettigungImGruenVorher: satVorherSumme / maskeNenner,
        saettigungImGruenNachher: satNachherSumme / maskeNenner,
      },
    },
  };
}
