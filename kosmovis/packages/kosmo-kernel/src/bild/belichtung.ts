/**
 * Belichtung — das fertige Bild heller stellen, OHNE dass der Aussenraum
 * ausbrennt.
 *
 * DER ZURUF, den dieses Modul bedient (Abnahmeliste Zeile 49, 10.09.2026):
 * «danach bitte bild noch minimal grundsaetzlich heller als aktuell und schau
 * das aussen nicht zu viel ausbrennt». Das ist der schwierige Fall des
 * Innenraums mit Blick nach draussen: innen dunkel, draussen sehr hell. Eine
 * gleichmaessige Aufhellung frisst den Aussenraum — und das ist hier nicht
 * behauptet, sondern am Auftragsbild gemessen (s. «GEMESSEN» weiter unten).
 *
 * DIE FORM IST DIE DER ZWEI NACHBARN in diesem Ordner (`farbangleich.ts`,
 * `nachbearbeitung.ts`), und zwar aus deren Grund: es wird KEIN BILDPUNKT
 * VERSCHOBEN. Jeder Ausgabepunkt haengt nur vom Wert DESSELBEN Eingabepunkts
 * ab. Und weil eine unsichtbare Maske eine Behauptung waere, BERICHTET auch
 * dieses Werkzeug, welche Flaeche es erfasst hat und was sich darin bewegt
 * hat — samt Kennlinie, damit es keine Blackbox ist.
 *
 * ────────────────────────────────────────────────────────────────────────
 * GEMESSEN, NICHT GEGLAUBT — am Auftragsbild `Innenbild_4000x2667.png`
 * (10.7 Mio. Bildpunkte). Der Aussenraum ist dabei NICHT aus der Helligkeit
 * geraten, sondern aus der Tiefenebene desselben Laufs abgegrenzt: die
 * Fernsichtebene hinter dem Glas steht in rund 1600 m und macht 1.63 % der
 * Flaeche aus. Das ist die unabhaengige Wahrheit, gegen die gemessen wurde.
 *
 * 1. DIE GLEICHMAESSIGE AUFHELLUNG FRISST DEN AUSSENRAUM — belegt.
 *    Faktor 1.15 auf jeden Bildpunkt: innen +14.6 %, aussen +11.3 %, und
 *    8.249 % DES GANZEN BILDES brennen aus (vorher: 0.000 %). Das oberste
 *    Promille der Leuchtdichte laeuft von 0.966 auf 1.000 — dort ist keine
 *    Zeichnung mehr.
 *
 * 2. EINE HELLIGKEITSSCHWELLE TRENNT DEN AUSSENRAUM NICHT SAUBER AB.
 *    Das ist der unbequeme Befund, und er gehoert hierher: bei Schwelle 0.85
 *    werden 83.8 % der Fernflaeche erfasst — aber 83.2 % dessen, was die
 *    Schwelle erfasst, ist GAR NICHT draussen. Es ist helle Decke, weisse
 *    Wand, Kuechenfront, Lampe. Die helle Zone ist fuenfmal so gross wie das
 *    Fenster. Aus einem fertigen Bild allein laesst sich das eine vom
 *    anderen NICHT trennen — dieses Werkzeug schont darum die Lichter, nicht
 *    «den Aussenraum», und der Bericht sagt genau das.
 *
 * 3. DER TREIBER IST DER SPITZKANAL, NICHT DIE LEUCHTDICHTE.
 *    Ausbrennen ist eine Eigenschaft je Kanal: ein Bildpunkt brennt, wenn
 *    EIN Kanal 255 erreicht. Mit der Leuchtdichte als Treiber brannten bei
 *    Knie 0.70/0.95 wieder 0.0076 % aus, mit `max(R,G,B)` 0.0000 % — bei
 *    gleichzeitig kleinerer Bewegung draussen (+1.81 % statt +2.75 %). Der
 *    Spitzkanal gewann bei JEDEM geprueften Knie.
 *
 * 4. DAS KNIE IST GEMESSEN, NICHT GEWAEHLT.
 *    Oben (0.92): oberhalb dieser Spitzkanal-Schwelle liegen 57.8 % der
 *    Fernflaeche, aber nur 3.89 % des Innenraums — Anreicherung 14.8-fach,
 *    der hoechste gemessene Wert. Einen Schritt weiter (0.94) faellt sie auf
 *    4.7-fach, weil die Fernflaeche selbst dort endet (nur noch 5.9 % von
 *    ihr liegen darueber). 0.92 ist also die Kante der Fernflaeche, nicht
 *    eine runde Zahl.
 *    Unten (0.66): dort werden 69.9 % des Bildes noch VOLL gehoben, und die
 *    Kurve traegt bis Faktor 1.239. Hoeher angesetzt (0.80) gewinnt man 18
 *    Prozentpunkte Flaeche, verliert aber die Tragfaehigkeit (nur noch
 *    1.097) und bewegt den Aussenraum um 60 % mehr. Tiefer (0.50) schont
 *    kaum besser (+0.44 % statt +0.58 %), hebt aber nur noch 27 % voll.
 *
 * 5. EINE ZWEITE RECHENART BRACHTE NICHTS. Dieselbe Maske mit der Hebung im
 *    LINEAREN Licht statt im Anzeigewert gerechnet (zwei sRGB-Kennlinien
 *    mehr im Code) ergab bei gleicher Wirkung dasselbe Verhaeltnis von
 *    Gewinn zu Schaden (9.2 gegen 8.9) — die Maske traegt den ganzen Effekt,
 *    der Farbraum nichts. Darum ist sie NICHT gebaut.
 *
 * ────────────────────────────────────────────────────────────────────────
 * DIE ZUSAGE, UND WARUM SIE AUS DER BAUART FOLGT.
 *
 * Alle drei Kanaele werden mit DEMSELBEN Faktor multipliziert. Damit bleiben
 * ihre Verhaeltnisse zueinander gleich — Farbton und Saettigung (in HSV
 * `(max-min)/max`) sind Punkt fuer Punkt unveraendert, nur der Wert steigt.
 * Gemessen: mittlere Saettigung 0.1757 vorher, 0.1757 nachher.
 *
 * Und: WENN DIE KURVE MONOTON IST, KANN KEIN BILDPUNKT AUSBRENNEN. Beweis in
 * zwei Zeilen: oberhalb des Knies ist der Faktor genau 1, also y(1) = 1; ist
 * y monoton steigend, gilt y(x) <= y(1) = 1 fuer alle x <= 1. Der Spitzkanal
 * ist der groesste Kanal, also bleiben auch die anderen beiden unter 1. Die
 * Messreihe bestaetigt es: bis zur Monotoniegrenze 1.2394 ausnahmslos
 * 0.0000 % ausgebrannt, und die Saettigung ruehrt sich nicht.
 *
 * Genau deshalb wird die Hebung an der MONOTONIEGRENZE geklemmt und nicht an
 * der Klemmgrenze. Die Monotoniegrenze (1.2394) ist die schaerfere von
 * beiden — die Kurve wuerde rueckwaerts laufen, lange bevor ein Bildpunkt
 * ueberlaeuft (das erst ab 1/0.66 = 1.5152). Eine rueckwaerts laufende
 * Tonkurve dreht Helligkeitsstufen um und macht sichtbare Baender; das ist
 * ein Fehler, keine Einstellung. Gemessen: bei 1.26 laeuft die Kurve
 * rueckwaerts, bei 1.55 brennen 20.6 % aus und die Saettigung faellt.
 *
 * UND DAS IST EINE ECHTE GRENZE, kein Notbehelf: eine Kurve, die die Mitte
 * hebt und die Lichter exakt stehen laesst, MUSS irgendwo flacher als
 * waagrecht werden. Man kann den Innenraum nicht beliebig weit hochziehen,
 * ohne den Aussenraum mitzunehmen. Der Bericht sagt darum, wo die Grenze
 * liegt und ob geklemmt wurde — statt still etwas anderes zu tun als
 * verlangt.
 *
 * ────────────────────────────────────────────────────────────────────────
 * KEINE VORLAGE IN PYTHON, und darum KEIN `Math.fround`. Die zwei Nachbarn
 * klammern jeden Rechenschritt in `f32`, weil sie eine numpy-Vorlage Byte
 * fuer Byte nachbilden und eine Abweichung von einem Byte als Fehler LESEN
 * koennen muessen. Dieses Modul hat keine solche Vorlage; ein `f32` waere
 * hier abgeschriebene Form ohne den Grund dahinter. Gerechnet wird in 64
 * Bit, und die Rundung auf `float32` passiert dort, wo sie ohnehin
 * unvermeidlich ist: beim Schreiben in die `Float32Array`-Kanalfelder.
 *
 * KEINE NEUE ABHAENGIGKEIT, kein Canvas, kein DOM: Eingabe sind rohe
 * Bildpunkte, wie bei beiden Nachbarn. Wer sie laedt, entscheidet draussen.
 */

import { alsKanaele, ausKanaelen, type Bild } from './farbangleich';
import { weich } from './nachbearbeitung';

/**
 * Vorgabe-Hebung: 1.08, also acht Prozent.
 *
 * «minimal grundsaetzlich heller» — am Auftragsbild hebt das die
 * Innenraum-Leuchtdichte von 0.5550 auf 0.5905 (rund neun Byte-Schritte im
 * mittleren Grau), waehrend die Fernflaeche sich um 0.0049 bewegt (gut ein
 * Byte-Schritt) und nichts ausbrennt. Das ist der Betrag, bei dem man den
 * Unterschied sieht und den Aussenraum nicht verliert.
 */
export const HEBUNG_VORGABE = 1.08;

/** Bis zu diesem Spitzkanalwert wirkt die Hebung voll (s. Kopf, Befund 4). */
export const SCHUTZ_UNTEN_VORGABE = 0.66;

/** Ab diesem Spitzkanalwert wirkt sie gar nicht mehr (s. Kopf, Befund 4). */
export const SCHUTZ_OBEN_VORGABE = 0.92;

/**
 * Stuetzstellen der berichteten Kennlinie — 256, eine je moeglichem
 * Byte-Wert, wie in `farbangleich.ts`.
 *
 * DER PRAEFIX IST NICHT ZIERDE: `farbangleich.ts` exportiert bereits ein
 * `KENNLINIE_PUNKTE` und ein `WAS_GEAENDERT_WURDE`, und der Kern reicht
 * seine Module mit `export *` heraus. Ohne eigene Namen waeren beide Namen
 * doppelt belegt und faenden in `@kosmo/kernel` gar nicht mehr statt — still,
 * erst beim naechsten Aufrufer sichtbar. Geprueft wurde das nicht geglaubt,
 * sondern mit einem Sammelexport ueber beide Dateien nachgestellt.
 */
export const BELICHTUNG_KENNLINIE_PUNKTE = 256;

/**
 * Wortlaut der Zusage. Steht als Konstante bei der Rechnung, die sie gibt.
 *
 * MIT UMLAUTEN, anders als jede Zeile Prosa in dieser Datei: das hier ist
 * kein Kommentar, sondern ein Satz, den der Owner im Inspektor LIEST. Die
 * Umschrift dieser Mappe gilt fuer das, was Entwickler lesen — «Saettigung»
 * in der Oberflaeche waere schlicht falsch geschrieben.
 */
export const BELICHTUNG_WAS_GEAENDERT_WURDE =
  'nur die Helligkeit innerhalb einer gemessenen Lichter-Maske; Farbton und Sättigung bleiben ' +
  'Punkt für Punkt gleich, kein Bildpunkt wandert, nichts entsteht, nichts verschwindet';

export interface BelichtungOptionen {
  /**
   * Helligkeitsfaktor im vollen Teil der Maske. 1.0 heisst: nichts tun.
   * Groesser als 1 hellt auf, kleiner als 1 dunkelt ab (auch das ist
   * monoton, s. {@link monotonieGrenze}). Wird an der Monotoniegrenze
   * geklemmt, und der Bericht sagt es.
   */
  hebung?: number;
  /** Spitzkanalwert, bis zu dem voll gehoben wird. Vorgabe 0.66. */
  schutzUnten?: number;
  /** Spitzkanalwert, ab dem gar nicht mehr gehoben wird. Vorgabe 0.92. */
  schutzOben?: number;
}

/** Mittelwerte einer Teilflaeche, in Byte-Schritten wie im Nachbarmodul. */
export interface FlaechenMass {
  /** Anteil an der Bildflaeche in Prozent. */
  anteilProzent: number;
  /** Mittlere Leuchtdichte (Rec.709) vorher, 0 bis 255. */
  vorher: number;
  /** Dieselbe nachher. */
  nachher: number;
}

export interface BelichtungBericht {
  /** Breite und Hoehe, in dieser Reihenfolge — wie die Nachbarn es melden. */
  bild: [number, number];
  /** Was der Aufrufer wollte. */
  hebungAngefragt: number;
  /** Was tatsaechlich gerechnet wurde (geklemmt, falls noetig). */
  hebungAngewendet: number;
  /** Die groesste Hebung, bei der die Kurve fuer dieses Knie nicht rueckwaerts laeuft. */
  hebungGrenze: number;
  /** Wurde geklemmt? Dann steht oben ein anderer Wert als unten. */
  geklemmt: boolean;
  schutzUnten: number;
  schutzOben: number;
  /** Die voll gehobene Flaeche: Spitzkanal unter `schutzUnten`. */
  vollGehoben: FlaechenMass;
  /** Der Uebergang: Spitzkanal zwischen den beiden Schwellen, teils gehoben. */
  teilweise: FlaechenMass;
  /** Die unangetastete Flaeche: Spitzkanal ueber `schutzOben` — Faktor exakt 1. */
  unangetastet: FlaechenMass;
  /**
   * Bildpunkte mit mindestens einem Kanal auf 255, vorher, in Prozent.
   *
   * BEI NULL BILDPUNKTEN: `NaN`, nicht 0 — s. {@link jeBildpunkt}.
   */
  ausgebranntVorherProzent: number;
  /** Dieselbe Zahl nachher. Steigt sie, ist die Zusage verletzt. `NaN` bei null Bildpunkten. */
  ausgebranntNachherProzent: number;
  /** Mittlere HSV-Saettigung vorher — muss sich nicht bewegen. `NaN` bei null Bildpunkten. */
  saettigungVorher: number;
  /** Dieselbe nachher. `NaN` bei null Bildpunkten. */
  saettigungNachher: number;
  /**
   * Die Kennlinie mit {@link BELICHTUNG_KENNLINIE_PUNKTE} Werten: `kennlinie[j]` ist der
   * Ausgabewert fuer den Eingabe-Spitzkanal `j/255`.
   *
   * Sie wird MITGEGEBEN und nicht nur angewandt — aus dem Grund, den
   * `farbangleich.ts` fuer seine Kennlinien nennt: sonst waere das Werkzeug
   * eine Blackbox, die man nur am Bild beurteilen kann.
   */
  kennlinie: Float64Array;
  /**
   * Der groesste Wert der Kennlinie. Liegt er unter oder auf 1, kann kein
   * Bildpunkt ueberlaufen — das ist die Zusage aus dem Kopfkommentar, hier
   * als Zahl statt als Satz.
   */
  hoechsterAusgabewert: number;
  wasGeaendertWurde: string;
}

export interface BelichtungErgebnis {
  bild: Bild;
  bericht: BelichtungBericht;
}

/**
 * Die Schutzmaske: 1 unterhalb von `unten`, 0 oberhalb von `oben`, dazwischen
 * der weiche Uebergang aus `nachbearbeitung.ts` (`smoothstep`).
 *
 * WEICH UND NICHT HART, aus demselben Grund wie beim Nachbarn: eine harte
 * Kante sieht man als Linie im Bild — hier saehe man sie als Saum um jedes
 * Fenster.
 */
export function schutzMaske(spitzkanal: number, unten: number, oben: number): number {
  const breite = oben - unten;
  if (!(breite > 0)) return spitzkanal < unten ? 1 : 0;
  return 1 - weich((spitzkanal - unten) / breite);
}

/**
 * Die groesste Hebung, bei der die Tonkurve nicht rueckwaerts laeuft —
 * GESCHLOSSEN gerechnet, nicht abgetastet.
 *
 * Die Kurve ist `y(x) = x * (1 + m(x) * (h-1))` mit `m` aus
 * {@link schutzMaske}. Mit `c = (x-u)/w`, `w = o-u` und `k = 6u/w` ergibt
 * Ausmultiplizieren von `y'(x) = 1 + (h-1) * phi(c)` ein KUBISCHES `phi`:
 *
 *     phi(c) = 8c^3 + (k-9)c^2 - k*c + 1
 *
 * Also ist `phi'(c) = 24c^2 + 2(k-9)c - k` eine Parabel mit positivem
 * Leitglied: `phi` faellt zwischen den beiden Nullstellen und steigt danach,
 * das Minimum liegt auf der GROESSEREN Nullstelle. Die steht mit der
 * Mitternachtsformel da, und damit ist `min(phi)` exakt.
 *
 * Ist `min(phi) < 0`, folgt die Grenze aus `1 + (h-1)*min(phi) >= 0`, also
 * `h <= 1 - 1/min(phi)`.
 *
 * GEGENPROBE — und sie hat zuerst WIDERSPROCHEN. An Knie 0.66/0.92 gibt die
 * Formel 1.2394074; eine Abtastung der Kurve an 400 001 Stellen gab 1.2367716,
 * also 2.6e-3 weniger. Der Fehler lag bei der PROBE, und er ist daran zu
 * erkennen, dass die Abweichung mit feinerem Schritt GROESSER wurde statt
 * kleiner (1/2000: 1.9e-6 · 1/200 000: 1.1e-3 · 1/2 000 000: 1.4e-2). Eine
 * echte Kurveneigenschaft konvergiert; was mit dem Schritt waechst, ist
 * Rauschen. Die Quelle ist `weich()`, das aus seiner numpy-Herkunft jeden
 * Zwischenschritt auf `float32` rundet — bei einem Schritt von 5e-7 ist diese
 * Rundung so gross wie der gemessene Zuwachs selbst. Dieselbe Abtastung mit
 * einem glatten smoothstep in 64 Bit trifft die Formel auf 1e-13, und die
 * Vormessung in numpy (ebenfalls 64 Bit, 200 001 Stellen) gab 0.2394. Die
 * Formel steht.
 *
 * WAS IN BYTES UEBRIG BLEIBT: die Ausgabe wird auf 8 Bit gerundet, und dort
 * ist an der Grenze nichts davon zu sehen — an 2 000 001 Stuetzstellen
 * betraegt der groesste Rueckschritt bei Hebung 1.2394174 genau 0 Byte, bei
 * 1.30 dagegen 1 Byte. Der `float32`-Saum von `weich()` liegt also rund drei
 * Groessenordnungen unter dem, was ein Bildpunkt ueberhaupt darstellen kann.
 *
 * Abdunkeln (`h < 1`) ist nie eingeschraenkt: `phi(0) = 1` ist zugleich das
 * Maximum, und `1 + (h-1)*1 = h > 0` gilt fuer jedes positive `h`.
 */
export function monotonieGrenze(unten: number, oben: number): number {
  const w = oben - unten;
  // Ohne Uebergangsbreite waere die Maske ein Sprung nach unten: die Kurve
  // faellt dort um `u*(h-1)` und ist fuer jedes `h > 1` rueckwaerts.
  if (!(w > 0)) return 1;
  const k = (6 * unten) / w;
  const b = 2 * (k - 9);
  const wurzel = Math.sqrt(b * b + 4 * 24 * k);
  const c = (-b + wurzel) / (2 * 24);
  // Liegt die Nullstelle ausserhalb des Uebergangs, gibt es dort kein
  // Minimum unter null — `phi` ist auf [0,1] dann nirgends negativ.
  if (!(c > 0) || !(c < 1)) return Number.POSITIVE_INFINITY;
  const phi = 8 * c * c * c + (k - 9) * c * c - k * c + 1;
  if (!(phi < 0)) return Number.POSITIVE_INFINITY;
  return 1 - 1 / phi;
}

/** Rec.709-Leuchtdichte, wie in `farbangleich.ts`. */
function leuchtdichte(r: number, g: number, b: number): number {
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Eine Kennzahl je Bildpunkt — und DER ENTSCHEID, was bei NULL Bildpunkten
 * dort steht (Befund 6, gefaellt am 17.09.2026).
 *
 * ────────────────────────────────────────────────────────────────────────
 * DIE ZAHLEN AENDERN SICH NICHT. Was sich aendert, ist, dass sie nicht mehr
 * durch Zufall entstehen. Bisher lieferten `(0/0)*100` und `0/0` von selbst
 * `NaN`; ab hier steht es da, mit Grund — und wer es «repariert», muss eine
 * Zeile loeschen, die erklaert, warum sie da ist. Genau darum ging es dem
 * Erbauer, als er die Rechnung ausdruecklich NICHT anfasste und den
 * Ist-Zustand verankerte: die Reparatur soll bewusst geschehen.
 *
 * WARUM NICHT NULL. Ein Prozentsatz ausgebrannter Flaeche bei null Flaeche
 * ist nicht null, er ist nicht bestimmbar. Eine Null waere eine Behauptung —
 * «nichts ist ausgebrannt», wo es nichts gibt, das brennen koennte. Dasselbe
 * fuer die mittlere Saettigung von null Bildpunkten. `NaN` ist hier nicht
 * der Rest einer kaputten Rechnung, sondern die richtige Antwort: die Frage
 * hat bei leerer Menge keine.
 *
 * WARUM NICHT ABWEISEN. Ein `throw` waere die andere ehrliche Moeglichkeit,
 * und sie waere nach Muster 9 («eine fehlende Zutat wird rot, nicht leer»)
 * sogar die schaerfere. GEMESSEN, ob der Fall ueberhaupt eintreten kann:
 * `belichtung()` hat im ganzen Arbeitsbaum GENAU EINEN Aufrufer,
 * `apps/kosmo-orbit/src/modules/vis/bild-rechnen.ts` (Stand 17.09.2026), und
 * der laedt seine Bildpunkte ausschliesslich ueber `bildpunkteAus()`, das
 * vorher `if (!(breite > 0) || !(hoehe > 0)) throw new Error('Das Bild hat
 * keine messbare Grösse.')` wirft. Die Oberflaeche kann also kein leeres Bild
 * herunterreichen — der Riegel steht schon, einen Schritt frueher. Ein
 * zweiter Riegel im Kern haette dafuer einen Preis: er wuerde die vorhandene
 * Verankerung des Ist-Zustands in `test/a16-belichtung.test.ts` umwerfen,
 * also eine fremde Probe, ohne dass sich am Produkt etwas aendert.
 *
 * WAS DAMIT NICHT ENTSCHIEDEN IST, und ausdruecklich nicht mitrepariert
 * wurde: die drei Flaechenmasse (`vollGehoben`, `teilweise`, `unangetastet`)
 * fangen die Null in `Teilflaeche.mass()` ab und melden bei null Bildpunkten
 * `anteilProzent: 0`, `vorher: 0`, `nachher: 0`. Nach derselben Logik ist
 * auch das eine Behauptung und keine Messung. Das zu aendern ist ein
 * ZWEITER Entscheid mit eigener Messung — und sein Anker liegt ebenfalls in
 * `test/a16-belichtung.test.ts`. Er ist gemeldet, nicht nebenbei erledigt.
 */
function jeBildpunkt(summe: number, n: number, faktor: number): number {
  // Nicht `n || 1`: das waere genau die Null-Abfangung, die hier falsch ist.
  if (n <= 0) return Number.NaN;
  return (summe / n) * faktor;
}

/** Sammelt Anteil und Mittelwerte einer Teilflaeche und rechnet sie in Bytes. */
class Teilflaeche {
  punkte = 0;
  private vorher = 0;
  private nachher = 0;

  zaehle(vorher: number, nachher: number): void {
    this.punkte++;
    this.vorher += vorher;
    this.nachher += nachher;
  }

  mass(gesamt: number): FlaechenMass {
    const n = this.punkte || 1;
    return {
      anteilProzent: (this.punkte / Math.max(gesamt, 1)) * 100,
      vorher: (this.vorher / n) * 255,
      nachher: (this.nachher / n) * 255,
    };
  }
}

/**
 * Das fertige Bild heller stellen und die Lichter dabei stehen lassen.
 *
 * Der Ablauf, Schritt fuer Schritt:
 *  1. Bildpunkte nach 0..1 (`alsKanaele`, `float32` wie bei beiden Nachbarn);
 *  2. Knie einordnen und die Hebung an der Monotoniegrenze klemmen;
 *  3. je Bildpunkt den SPITZKANAL `max(R,G,B)` messen — er entscheidet ueber
 *     das Ausbrennen, nicht die Leuchtdichte;
 *  4. daraus die Maske, daraus EIN Faktor, und der geht auf alle drei
 *     Kanaele gleich (darum bleibt die Farbe stehen);
 *  5. runden (nicht abschneiden) auf ganze Bytes.
 *
 * ZU SCHRITT 5: `farbangleich.ts` schneidet ab, `nachbearbeitung.ts` rundet —
 * die zwei sind dort wirklich verschieden, weil ihre Python-Vorlagen es sind.
 * Hier gibt es keine Vorlage, und Abschneiden waere sachlich falsch: es zieht
 * im Mittel ein halbes Byte ab, also ausgerechnet gegen die Richtung, in die
 * dieses Werkzeug arbeiten soll. Bei der Vorgabe-Hebung von acht Prozent
 * waere das rund ein Zwanzigstel der ganzen Wirkung, still abgezogen.
 */
export function belichtung(
  bild: Bild,
  optionen: BelichtungOptionen = {},
): BelichtungErgebnis {
  const angefragt = optionen.hebung ?? HEBUNG_VORGABE;
  // `schutzOben` muss unter oder auf 1 bleiben: nur dann ist der Faktor am
  // oberen Ende exakt 1, und nur darauf stuetzt sich der Beweis, dass nichts
  // ueberlaufen kann.
  const unten = Math.min(Math.max(optionen.schutzUnten ?? SCHUTZ_UNTEN_VORGABE, 0), 1);
  const oben = Math.min(Math.max(optionen.schutzOben ?? SCHUTZ_OBEN_VORGABE, unten), 1);

  const grenze = monotonieGrenze(unten, oben);
  const hebung = Math.min(Math.max(angefragt, 0), grenze);
  const anstieg = hebung - 1;

  const [r, g, b] = alsKanaele(bild);
  const n = bild.breite * bild.hoehe;

  const voll = new Teilflaeche();
  const teil = new Teilflaeche();
  const frei = new Teilflaeche();
  let ausgebranntVorher = 0;
  let ausgebranntNachher = 0;
  let satVorher = 0;
  let satNachher = 0;

  for (let i = 0; i < n; i++) {
    const ri = r[i]!;
    const gi = g[i]!;
    const bi = b[i]!;
    const spitze = Math.max(ri, gi, bi);
    const tief = Math.min(ri, gi, bi);
    const maske = schutzMaske(spitze, unten, oben);
    const faktor = 1 + maske * anstieg;

    // Geklemmt wird trotzdem — nicht weil es noetig waere (der Beweis oben
    // sagt, dass es nicht vorkommt), sondern weil `hebung` auch von aussen
    // kommen kann und ein stiller Ueberlauf schlimmer ist als ein
    // begrenzter Wert. Der Bericht misst hinterher nach, ob es passiert ist.
    const rn = Math.min(ri * faktor, 1);
    const gn = Math.min(gi * faktor, 1);
    const bn = Math.min(bi * faktor, 1);

    const lv = leuchtdichte(ri, gi, bi);
    const ln = leuchtdichte(rn, gn, bn);
    if (maske >= 1) voll.zaehle(lv, ln);
    else if (maske <= 0) frei.zaehle(lv, ln);
    else teil.zaehle(lv, ln);

    if (Math.round(spitze * 255) >= 255) ausgebranntVorher++;
    const spitzeNeu = Math.max(rn, gn, bn);
    if (Math.round(spitzeNeu * 255) >= 255) ausgebranntNachher++;

    satVorher += spitze > 0 ? (spitze - tief) / spitze : 0;
    const tiefNeu = Math.min(rn, gn, bn);
    satNachher += spitzeNeu > 0 ? (spitzeNeu - tiefNeu) / spitzeNeu : 0;

    r[i] = rn;
    g[i] = gn;
    b[i] = bn;
  }

  const kennlinie = new Float64Array(BELICHTUNG_KENNLINIE_PUNKTE);
  let hoechster = 0;
  for (let j = 0; j < BELICHTUNG_KENNLINIE_PUNKTE; j++) {
    const x = j / (BELICHTUNG_KENNLINIE_PUNKTE - 1);
    const y = Math.min(x * (1 + schutzMaske(x, unten, oben) * anstieg), 1);
    kennlinie[j] = y;
    if (y > hoechster) hoechster = y;
  }

  return {
    bild: ausKanaelen([r, g, b], bild, false),
    bericht: {
      bild: [bild.breite, bild.hoehe],
      hebungAngefragt: angefragt,
      hebungAngewendet: hebung,
      hebungGrenze: grenze,
      geklemmt: hebung !== angefragt,
      schutzUnten: unten,
      schutzOben: oben,
      vollGehoben: voll.mass(n),
      teilweise: teil.mass(n),
      unangetastet: frei.mass(n),
      // Die vier Zahlen, die DIREKT durch die Bildpunktzahl teilen. Bei null
      // Bildpunkten stehen sie auf `NaN` — Begruendung an `jeBildpunkt`.
      ausgebranntVorherProzent: jeBildpunkt(ausgebranntVorher, n, 100),
      ausgebranntNachherProzent: jeBildpunkt(ausgebranntNachher, n, 100),
      saettigungVorher: jeBildpunkt(satVorher, n, 1),
      saettigungNachher: jeBildpunkt(satNachher, n, 1),
      kennlinie,
      hoechsterAusgabewert: hoechster,
      wasGeaendertWurde: BELICHTUNG_WAS_GEAENDERT_WURDE,
    },
  };
}
