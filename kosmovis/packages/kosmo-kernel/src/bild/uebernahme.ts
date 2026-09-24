/**
 * Uebernahme — aus einem Vorbild EINZELNE, BENANNTE Eigenschaften holen, und
 * nur diese.
 *
 * DER ZURUF, den dieses Modul bedient (Abnahmeliste Zeile 54, 10.09.2026,
 * zweimal zugerufen):
 *
 *   08:00  «sry nur decke uebernehmen»
 *   13:15  «wir uebernehmen von diesem referenzbild die saettigung und farbe
 *          der decke, die vorhangfarbe und durchlaessigkeit, die tisch und
 *          stuhltextur fuer esstisch, die weisse kuechenfront ansicht und
 *          ablage»
 *
 * DER ERSTE ZURUF IST DIE GANZE AUFGABE. Er faellt um 08:00 und ist die
 * BERICHTIGUNG des Zurufs von 07:16 — «nutze sie um einen grund ai imaging
 * layer zu erstellen mit dem bolognese stil» (Zeile 53). Der Owner hat ein
 * Vorbild danebengelegt, das ganze Bild danach angeglichen bekommen und
 * vierundvierzig Minuten spaeter gesagt: nein, nur die Decke. Genau dieser
 * Unterschied ist der Inhalt dieser Datei.
 *
 * ────────────────────────────────────────────────────────────────────────
 * WAS ES VOM FARBANGLEICH UNTERSCHEIDET — und warum das kein Beiwerk ist
 *
 * `farbangleich.ts` legt die Summenverteilung des Vorbilds auf die des Bildes,
 * je Kanal, ueber das ganze Bild. Das ist genau richtig fuer «das ganze bild
 * wieder an dieses angleichen» (Zeile 55) und genau falsch fuer Zeile 54: es
 * nimmt das Vorbild ALS GANZES. Farbe, Kontrast, Helligkeit, Saettigung — alle
 * zugleich, ueberall.
 *
 * Zeile 54 verlangt eine AUSWAHL, und zwar in zwei Richtungen zugleich:
 *
 *   WAS  — «die saettigung UND farbe» sind zwei Dinge, nicht eines. Wer die
 *          Saettigung uebernimmt, soll die Helligkeit NICHT mitnehmen.
 *   WO   — «der decke», «die vorhangfarbe», «fuer esstisch». Das Uebrige
 *          bleibt stehen.
 *
 * Darum rechnet dieses Modul nicht in R/G/B, sondern in H/S/V: dort sind
 * Farbton, Saettigung und Helligkeit DREI GETRENNTE ZAHLEN, und eine davon
 * laesst sich anfassen, ohne die anderen zu beruehren. In R/G/B geht das
 * nicht — jeder Kanal traegt alle drei Groessen zugleich.
 *
 * ────────────────────────────────────────────────────────────────────────
 * WAS AUS EINEM FERTIGEN BILD UEBERHAUPT UEBERNEHMBAR IST — gezaehlt, nicht
 * behauptet. Der lange Zuruf von 13:15 nennt SECHS Wuensche:
 *
 *   1. «die saettigung … der decke»        → Saettigung, Bereich Deckenholz  JA
 *   2. «und farbe der decke»               → Farbton, Bereich Deckenholz     JA
 *   3. «die vorhangfarbe»                  → Farbton, Bereich Vorhang        halb
 *   4. «und durchlaessigkeit»              → Materialeigenschaft             NEIN
 *   5. «die tisch und stuhltextur»         → Bildkarte                       NEIN
 *   6. «die weisse kuechenfront … ablage»  → Helligkeit, Bereich helle Fl.   halb
 *
 * DREI davon rechnet dieses Modul, ZWEI kann es grundsaetzlich nicht, und bei
 * ZWEI haengt es am Bereich. Im Einzelnen:
 *
 *  - DURCHLAESSIGKEIT ist keine Eigenschaft eines fertigen Bildes. Ein Bild
 *    zeigt, was durch den Vorhang kam, nicht wieviel durchkommt. Das ist ein
 *    Material-Zuruf und gehoert ins Modell (`design.merkmalSetzen`), nicht an
 *    diese Stelle. Hier wird er NICHT angeboten — ein Regler mit diesem Wort
 *    waere eine Attrappe.
 *  - TEXTUR verlangt eine Bildkarte. `derive/gltf.ts` traegt im Kopf einen
 *    eigenen Abschnitt «TEXTUREN: WARUM HIER KEINE STEHEN»; der Bauplan
 *    fuehrt die Zeilen 5b/36/37 aus demselben Grund als «nicht schaetzbar».
 *    Auch das wird hier NICHT angeboten.
 *  - VORHANG und KUECHENFRONT sind Bauteile. Ein fertiges Bild weiss nicht,
 *    welche Flaeche welchem Bauteil gehoert — das ist Zeile 59 («suche dafuer
 *    zuerst eine oberflaeche die stimmt») und liegt in Welle 5 bei der
 *    Fremdnaht, die ein Material-ID-Bild vom Worker braucht. Bis dahin gibt
 *    es die Bereiche, die sich aus dem Bild selbst MESSEN lassen (unten), und
 *    den Bereich {@link BEREICHE}`.eigeneMaske` — der nimmt eine fertige
 *    Maske von aussen entgegen. Kommt das Material-ID-Bild, ist «die Decke»
 *    darueber exakt, ohne dass an dieser Datei etwas zu aendern waere.
 *
 * Diese Aufstellung ist der Grund, warum die Eigenschaftsliste genau drei
 * Namen hat und nicht sechs.
 *
 * ────────────────────────────────────────────────────────────────────────
 * DIE BEREICHE SIND GEMESSEN, NICHT ERFUNDEN. Drei der vier stammen Zahl fuer
 * Zahl aus den Nachbarmodulen, die sie bereits gegen ihre Vorlage gemessen
 * haben:
 *
 *  - `deckenholz` — die Deckenmaske aus `nachbearbeitung.ts`: Lage oben im
 *    Bild MAL warm getoent (Rot minus Blau). Zweiteilig aus dem dort
 *    genannten Grund: die Lage allein nimmt den Betontraeger und die weissen
 *    Waende mit, die Farbe allein die Holzmoebel unten im Bild.
 *  - `bewuchs` — die Gruenmaske aus `nachbearbeitung.ts`: Farbton 70–175 Grad
 *    mit 12 Grad Ausklang, dazu ein Saettigungstor, damit Grau nicht ins
 *    Gruene kippt.
 *  - `helleFlaechen` — die Lichter-Maske aus `belichtung.ts`, hier UMGEDREHT
 *    (dort wird geschont, was hier gemeint ist). Die Funktion wird importiert,
 *    nicht abgeschrieben.
 *
 * WAS `helleFlaechen` WIRKLICH ERFASST, steht im Kopf von `belichtung.ts` als
 * Messung und wird hier nicht schoengeredet: bei Schwelle 0.85 sind **83.2 %
 * dessen, was die Schwelle erfasst, gar nicht der Aussenraum** — es ist helle
 * Decke, weisse Wand, Kuechenfront, Lampe. Fuer Zeile 49 war das der
 * unbequeme Befund; fuer Zeile 54 ist es brauchbar, weil die «weisse
 * kuechenfront» genau in dieser Gruppe liegt. Brauchbar heisst aber nicht
 * genau: die Maske heisst darum «helle Flaechen» und nicht «Kuechenfront».
 * {@link UEBERNAHME_BEREICH_VORBEHALT} traegt diesen Satz bis in die
 * Oberflaeche.
 *
 * ZWEI KONSTANTENSAETZE SIND KOPIERT, weil `nachbearbeitung.ts` seine Masken
 * inmitten der Rechnung bildet und nicht als Funktion herausreicht
 * (0.045/0.085 fuer warm, 58/187/12 und 0.05/0.1 fuer gruen). Eine Kopie
 * kann auseinanderlaufen; darum misst `test/a10-uebernahme.test.ts` die Maske
 * des Nachbarn zurueck — `nachbearbeitung(bild, { decke: 0 })` setzt jeden
 * Bildpunkt auf `wert * (1 - maske)`, womit sich die Maske aus Ein- und
 * Ausgabe ausrechnen laesst — und haelt sie gegen die hiesige. Das ist keine
 * zweite Lesung desselben Quelltexts, sondern eine Messung am laufenden
 * Nachbarn.
 *
 * ────────────────────────────────────────────────────────────────────────
 * DIE ZUSAGE, UND WARUM SIE AUS DER BAUART FOLGT
 *
 * 1. KEIN BILDPUNKT WANDERT. Jeder Ausgabepunkt haengt nur vom Wert
 *    DESSELBEN Eingabepunkts ab (und, bei `deckenholz`, von seiner Zeile —
 *    wie beim Nachbarn). Die Verteilungen, aus denen die Kennlinien kommen,
 *    sind von der Lage der Bildpunkte unabhaengig.
 * 2. EIN PUNKT, DEN KEIN BEREICH BERUEHRT, WIRD BYTEWEISE KOPIERT. Nicht
 *    gerechnet, nicht gerundet, nicht durch HSV geschickt — kopiert. Damit
 *    ist «und nur diese» im Raum keine Behauptung, sondern eine Eigenschaft
 *    des Ablaufs, und der Bericht zaehlt nach, wieviele Punkte das sind.
 *
 *    EHRLICH DAZU, weil es sonst staerker klingt, als es ist: der Weg durch
 *    HSV und zurueck verliert an KEINER Farbe ein Byte. Das ist nicht
 *    behauptet, sondern ueber alle **16 777 216** Farben des 8-Bit-Raums
 *    gemessen — null Abweichungen, groesste Abweichung 0 Byte. Nimmt man das
 *    Kopieren also heraus, aendert sich am Ergebnis nichts, und alle Proben
 *    bleiben gruen (nachgestellt am 17.09.2026). Der Kopierweg bleibt
 *    trotzdem: er macht aus einer gemessenen Eigenschaft der NACHBARMODULE
 *    eine Eigenschaft DIESES Ablaufs, und er spart die Rechnung an drei
 *    Vierteln des Bildes.
 * 3. EINE NICHT BENANNTE EIGENSCHAFT WIRD NICHT ANGEFASST. Wer nur die
 *    Saettigung uebernimmt, laesst H und V des Punktes stehen; `hsvZuRgb`
 *    gibt zu unveraendertem V wieder genau `max(R,G,B) = V` zurueck. Was
 *    davon nach der Rundung auf ganze Bytes uebrig bleibt, wird NICHT
 *    behauptet, sondern gemessen und im Bericht genannt
 *    ({@link UebernahmeBericht.eigenschaftenGesamt}).
 * 4. ALLE ZIELWERTE WERDEN VOR DEM ERSTEN SCHREIBEN AUS DEN URSPRUNGSBILDERN
 *    GERECHNET. Zwei Posten koennen sich darum nicht gegenseitig die
 *    Grundlage verschieben, und die Reihenfolge der Posten aendert das
 *    Ergebnis nicht, solange ihre Bereiche einander nicht ueberlappen.
 *    Ueberlappen sie doch, sagt es der Bericht
 *    ({@link UebernahmeBericht.ueberlappungProzent}).
 *
 * ────────────────────────────────────────────────────────────────────────
 * ZWEI FALLEN, DIE HIER ABSICHTLICH ZUGEMACHT SIND
 *
 * GRAU HAT KEINEN FARBTON. Eine Saettigungs-Kennlinie, die 0 auf 0.3
 * abbildet, macht aus jedem grauen Bildpunkt einen ROTEN (Farbton 0 ist die
 * Vorgabe von `rgbZuHsv` fuer farblose Punkte). `nachbearbeitung.ts` kennt
 * diese Falle und stellt seiner Gruenmaske ein Saettigungstor voran («sonst
 * wuerde Grau ins Gruene kippen»). Hier steht dasselbe Tor vor der
 * Saettigungs-Uebernahme, und der Bericht zaehlt, wieviele Punkte es
 * uebergangen hat. Die Farbton-Uebernahme braucht kein Tor: eine Drehung des
 * Farbtons an einem Punkt mit Saettigung null aendert am RGB-Wert exakt
 * nichts.
 *
 * DER FARBTON IST EIN WINKEL. Eine Summenverteilung ueber 0…360 Grad zerreisst
 * ihn an der Naht bei Rot: 359 und 1 sind zwei Grad auseinander und stuenden
 * an den entgegengesetzten Enden der Verteilung. Darum wird der Farbton NICHT
 * ueber eine Kennlinie uebernommen, sondern als DREHUNG — das zirkulaere
 * Mittel des Vorbilds minus das des Bildes, auf dem kuerzeren Weg. Wie
 * verlaesslich dieses Mittel ist, sagt die Buendelung (die Laenge des
 * gemittelten Zeigers, 0 bis 1): ein Bereich mit vielen verschiedenen
 * Farbtoenen hat eine kleine Buendelung, und dann ist die Drehung eine
 * schwache Aussage. Die Zahl steht im Bericht, statt dass ein fester
 * Grenzwert sie still verschluckt.
 *
 * ────────────────────────────────────────────────────────────────────────
 * ZUR RECHENGENAUIGKEIT. Die Rechnung JE BILDPUNKT laeuft ueber `rgbZuHsv`/
 * `hsvZuRgb` und `weich()` aus `nachbearbeitung.ts` — die runden wie numpy
 * nach jedem Schritt auf `float32`, weil sie eine numpy-Vorlage Byte fuer
 * Byte nachbilden. Das wird hier NICHT nachgeahmt und nicht bekaempft: es
 * ist derselbe Farbraum, den die Nachbarn benutzen, und ein zweiter waere
 * eine zweite Wahrheit.
 *
 * JEDE SUMME UEBER DAS BILD dagegen laeuft in `float64`, so wie in
 * `belichtung.ts`. Der Grund ist gemessen und steht im Kopf von
 * `bild-farbe.test.ts`: ueber 376 000 Bildpunkte haeuft sich der
 * `float32`-Rundungsfehler einer Mittelung so weit auf, dass die erste
 * Nachkommastelle kippt (122.648 gegen 122.671) — und eine Probe auf 64x64
 * Punkten sieht das nicht.
 *
 * KEIN CANVAS, KEIN DOM, KEIN DATEISYSTEM, KEINE NEUE ABHAENGIGKEIT — wie bei
 * allen drei Nachbarn. Eingabe sind rohe Bildpunkte; wer sie laedt,
 * entscheidet draussen.
 */

import { SCHUTZ_OBEN_VORGABE, SCHUTZ_UNTEN_VORGABE, schutzMaske } from './belichtung';
// `ausKanaelen` wird hier ABSICHTLICH nicht benutzt, obwohl die drei Nachbarn
// es tun: es schreibt JEDEN Bildpunkt neu. Dieses Modul kopiert unberuehrte
// Punkte Byte fuer Byte und schreibt nur die beruehrten — das ist die
// Zusage 2 im Kopf, und mit `ausKanaelen` waere sie nicht zu haben.
import { alsKanaele, kennlinie, type Bild } from './farbangleich';
import { DECKENHOEHE_VORGABE, hsvZuRgb, rgbZuHsv, weich } from './nachbearbeitung';

// ---------------------------------------------------------------------------
// Namen
// ---------------------------------------------------------------------------

/**
 * Die drei Eigenschaften, die sich aus einem fertigen Bild einzeln uebernehmen
 * lassen. Warum es genau diese drei sind und nicht die sechs des Zurufs, steht
 * im Kopf dieser Datei.
 */
export const EIGENSCHAFTEN = ['farbton', 'saettigung', 'helligkeit'] as const;
export type EigenschaftName = (typeof EIGENSCHAFTEN)[number];

/**
 * Die Bereiche, in denen eine Eigenschaft uebernommen werden kann.
 *
 * `eigeneMaske` ist der Anschluss fuer eine von aussen gemessene Flaeche — das
 * Material-ID-Bild aus Zeile 59, sobald es der Worker liefert. Bis dahin
 * tragen die drei gemessenen Bereiche die Last, und keiner von ihnen
 * behauptet, ein Bauteil zu kennen.
 */
export const BEREICHE = ['ganzesBild', 'deckenholz', 'bewuchs', 'helleFlaechen', 'eigeneMaske'] as const;
export type BereichName = (typeof BEREICHE)[number];

/**
 * Anzeigenamen. MIT UMLAUTEN, wie die Zusage in `belichtung.ts` und aus
 * demselben Grund: das hier liest der Owner in der Oberflaeche, und
 * «Saettigung» waere dort schlicht falsch geschrieben.
 */
export const UEBERNAHME_EIGENSCHAFT_LABEL: Record<EigenschaftName, string> = {
  farbton: 'Farbton',
  saettigung: 'Sättigung',
  helligkeit: 'Helligkeit',
};

export const UEBERNAHME_BEREICH_LABEL: Record<BereichName, string> = {
  ganzesBild: 'ganzes Bild',
  deckenholz: 'Deckenholz (oben und warm)',
  bewuchs: 'Bewuchs (grün)',
  helleFlaechen: 'helle Flächen',
  eigeneMaske: 'gelieferte Maske',
};

/**
 * Was der jeweilige Bereich wirklich erfasst — der Vorbehalt, nicht die
 * Werbung. Er steht neben der Auswahl in der Oberflaeche, damit niemand einen
 * Bereich fuer ein Bauteil haelt.
 *
 * Die Zahl bei `helleFlaechen` ist gemessen (Kopf von `belichtung.ts`,
 * Befund 2), nicht geschaetzt.
 */
export const UEBERNAHME_BEREICH_VORBEHALT: Record<BereichName, string> = {
  ganzesBild: 'Jeder Bildpunkt. Die Auswahl liegt dann allein in der Eigenschaft.',
  deckenholz:
    'Oben im Bild und warm getönt. Erfasst warmes Holz im oberen Drittel — ' +
    'ein grauer Betonträger fällt heraus, ein Holzmöbel weiter unten ebenso.',
  bewuchs:
    'Farbton 70–175 Grad mit genug Farbe. Trifft Bepflanzung auch dort, wo sie sich ' +
    'im Glas spiegelt; trifft aber auch jede andere grüne Fläche.',
  helleFlaechen:
    'Alles über dem gemessenen Knie von max(R,G,B). Das ist Küchenfront, weisse Wand, ' +
    'helle Decke, Lampe und Fensterfeld zugleich — am Auftragsbild gemessen sind ' +
    '83.2 % davon nicht der Aussenraum. Kein Bauteil, eine Helligkeitszone.',
  eigeneMaske:
    'Die von aussen gelieferte Fläche, Bildpunkt für Bildpunkt. Genau so genau wie ' +
    'ihre Quelle — erst ein Material-ID-Bild macht daraus «die Decke».',
};

/** Stuetzstellen der berichteten Kennlinie — 256, eine je moeglichem Byte-Wert. */
export const UEBERNAHME_KENNLINIE_PUNKTE = 256;

/**
 * Bis zu dieser Saettigung gilt ein Bildpunkt als farblos; darueber laeuft das
 * Tor ueber {@link SAT_TOR_FLANKE} weich auf. 0.02 sind rund fuenf
 * Byte-Schritte Buntheit bei voller Helligkeit — darunter ist der Farbton
 * dessen, was man sieht, nicht mehr zu unterscheiden.
 *
 * Warum es das Tor gibt, steht im Kopf: ohne ihn macht eine
 * Saettigungs-Kennlinie aus Grau Rot.
 */
export const SAT_TOR_SCHWELLE = 0.02;
export const SAT_TOR_FLANKE = 0.04;

/**
 * Ab dieser Saettigung wird der Farbton eines Bildpunkts ueberhaupt GEMESSEN
 * (fuer den Bericht) — darunter schwankt er bei einer Aenderung von einem Byte
 * um viele Grad und wuerde die Kennzahl «groesste Abweichung» allein
 * bestimmen. Das ist dieselbe Ueberlegung wie beim Tischplatten-Befund der
 * Anleitung: die Farbe nicht im Lichtkegel messen.
 */
export const FARBTON_MESSGRENZE = 0.05;

/**
 * Wortlaut der Zusage. Steht als Konstante bei der Rechnung, die sie gibt —
 * dieselbe Regel wie bei den drei Nachbarn.
 */
export const UEBERNAHME_WAS_GEAENDERT_WURDE =
  'nur die benannten Eigenschaften in den benannten Bereichen; jede nicht benannte Eigenschaft ' +
  'und jeder Bildpunkt ausserhalb bleiben Byte für Byte gleich, kein Bildpunkt wandert, ' +
  'nichts entsteht, nichts verschwindet';

// ---------------------------------------------------------------------------
// Auftrag und Bericht
// ---------------------------------------------------------------------------

export interface UebernahmePosten {
  /** WAS uebernommen wird. */
  eigenschaft: EigenschaftName;
  /** WO es uebernommen wird. */
  bereich: BereichName;
  /**
   * Mischung zwischen «bleibt wie es ist» (0) und «ganz wie das Vorbild» (1).
   * Vorgabe 1. Der Regler sitzt NACH der Kennlinie, nicht in ihr — die
   * Kennlinie bleibt darum bei jeder Staerke dieselbe und vergleichbar
   * (dieselbe Linie wie in `farbangleich.ts`).
   */
  staerke?: number;
  /**
   * Nur bei `bereich: 'eigeneMaske'`: ein Gewicht je Bildpunkt (0 bis 1),
   * zeilenweise, `breite * hoehe` Werte. Fehlt es, ist das ein Fehler und
   * kein leerer Bereich — s. Muster 9 der Anleitung.
   */
  maske?: Float32Array | Float64Array | readonly number[];
  /**
   * Nur bei `bereich: 'eigeneMaske'`: dasselbe fuer das VORBILD. Fehlt es,
   * wird das ganze Vorbild gemessen, und der Bericht sagt es
   * ({@link UebernahmePostenBericht.vorbildGanz}).
   */
  maskeVorbild?: Float32Array | Float64Array | readonly number[];
}

export interface UebernahmeOptionen {
  /** Die Posten. Eine leere Liste ist ein Fehler, kein Nichtstun. */
  posten: readonly UebernahmePosten[];
  /** Anteil der Bildhoehe fuer den Bereich `deckenholz`. Vorgabe 0.34 (Nachbar). */
  deckenhoehe?: number;
  /** Untere Knieschwelle fuer `helleFlaechen`. Vorgabe 0.66 (Nachbar). */
  lichterUnten?: number;
  /** Obere Knieschwelle fuer `helleFlaechen`. Vorgabe 0.92 (Nachbar). */
  lichterOben?: number;
}

/** Was eine Groesse ueber das GANZE Bild getan hat — vorher gegen nachher. */
export interface EigenschaftsMass {
  /**
   * Mittel vorher. Farbton in Grad (zirkulaeres Mittel, mit der Saettigung
   * gewichtet), Saettigung und Helligkeit in Byte-Schritten 0…255.
   */
  mittelVorher: number;
  /** Dasselbe nachher, aus den AUSGEGEBENEN Bytes gemessen. */
  mittelNachher: number;
  /**
   * Die groesste Abweichung an einem einzelnen Bildpunkt — Farbton in Grad,
   * die anderen beiden in Byte-Schritten. Bei einer nicht uebernommenen
   * Eigenschaft ist das die Zahl, die die Zusage traegt.
   */
  groessteAbweichung: number;
  /** Bildpunkte, an denen sich diese Groesse ueberhaupt bewegt hat. */
  bildpunkteBewegt: number;
  /**
   * Wieviele Bildpunkte in die Messung eingingen. Beim Farbton sind das nur
   * die mit Saettigung ueber {@link FARBTON_MESSGRENZE} in BEIDEN Fassungen —
   * an einem grauen Punkt ist der Farbton keine messbare Groesse.
   */
  bildpunkteGemessen: number;
}

export interface UebernahmePostenBericht {
  eigenschaft: EigenschaftName;
  bereich: BereichName;
  staerke: number;
  /** Bildpunkte mit Maskenwert ueber 0.5, in Prozent — die Zaehlweise des Nachbarn. */
  erfassteFlaecheProzent: number;
  /** Bildpunkte mit Maskenwert ueber 0, in Prozent — inklusive Ausklang. */
  beruehrteFlaecheProzent: number;
  /** Punkte der Stichprobe im BILD (Maske ueber 0.5). */
  stichprobeBild: number;
  /** Punkte der Stichprobe im VORBILD. */
  stichprobeVorbild: number;
  /** Wurde das ganze Vorbild gemessen, weil keine Vorbildmaske vorlag? */
  vorbildGanz: boolean;
  /**
   * Der Wert der uebernommenen Groesse IM ERFASSTEN BEREICH: im Bild vorher,
   * im Vorbild, im Bild nachher. Farbton in Grad, sonst in Byte-Schritten.
   */
  wertVorher: number;
  wertVorbild: number;
  wertNachher: number;
  /**
   * Nur beim Farbton: um wieviel Grad gedreht wurde (kuerzester Weg,
   * -180 bis +180), und wie gebuendelt die zwei gemittelten Farbtoene waren
   * (0 bis 1). Eine kleine Buendelung heisst: der Bereich hat viele
   * verschiedene Farbtoene, die Drehung ist eine schwache Aussage.
   */
  drehungGrad: number | undefined;
  buendelungBild: number | undefined;
  buendelungVorbild: number | undefined;
  /**
   * Nur bei Saettigung und Helligkeit: die Kennlinie mit
   * {@link UEBERNAHME_KENNLINIE_PUNKTE} Werten, `kennlinie[j]` ist der
   * Zielwert zum Eingabewert `j/255`. Sie wird MITGEGEBEN und nicht nur
   * angewandt — sonst waere das Werkzeug eine Blackbox, die man nur am Bild
   * beurteilen kann (Begruendung woertlich aus `farbangleich.ts`).
   */
  kennlinie: Float64Array | undefined;
  /**
   * Nur bei der Saettigung: Bildpunkte im Bereich, die das Farblos-Tor
   * uebergangen hat, in Prozent der erfassten Flaeche. Ohne dieses Tor waeren
   * sie rot geworden.
   */
  farblosUebergangenProzent: number | undefined;
}

export interface UebernahmeBericht {
  /** Breite und Hoehe, in dieser Reihenfolge — wie die Nachbarn es melden. */
  bild: [number, number];
  vorbild: [number, number];
  posten: UebernahmePostenBericht[];
  /** Bildpunkte, auf die MEHR ALS EIN Posten wirkt, in Prozent. */
  ueberlappungProzent: number;
  /**
   * Bildpunkte, auf die KEIN Posten wirkt, in Prozent. Sie werden Byte fuer
   * Byte kopiert — nicht durch HSV geschickt, nicht gerundet.
   */
  ausserhalbProzent: number;
  /**
   * Bildpunkte, deren drei Bytes unveraendert sind, in Prozent. Zusammen mit
   * {@link ausserhalbProzent} ist das die Probe auf «und nur diese»: die Zahl
   * muss mindestens so gross sein wie der Anteil ausserhalb.
   */
  unveraenderteBildpunkteProzent: number;
  /** Die drei Groessen ueber das ganze Bild, vorher gegen nachher. */
  eigenschaftenGesamt: Record<EigenschaftName, EigenschaftsMass>;
  wasGeaendertWurde: string;
}

export interface UebernahmeErgebnis {
  bild: Bild;
  bericht: UebernahmeBericht;
}

// ---------------------------------------------------------------------------
// Bausteine
// ---------------------------------------------------------------------------

/** Ein Wert auf 0..1 begrenzt. */
function klemme01(x: number): number {
  return x < 0 ? 0 : x > 1 ? 1 : x;
}

/**
 * Eine Kennlinie aus {@link UEBERNAHME_KENNLINIE_PUNKTE} Stuetzstellen an der
 * Stelle `x` auswerten.
 *
 * Das Gitter ist `j/255` und damit GLEICHMAESSIG; die Stelle laesst sich
 * darum geschlossen ausrechnen, statt sie zu suchen. `farbangleich.ts` sucht,
 * weil seine Stuetzstellen dort Quantile sind und eben nicht gleichmaessig
 * liegen. Dass beide Wege dasselbe liefern, misst
 * `test/a10-uebernahme.test.ts` gegen eine binaere Suche ueber das
 * ausgeschriebene Gitter.
 */
export function aufKennlinie(x: number, kl: Float64Array): number {
  const n = kl.length;
  const t = klemme01(x) * (n - 1);
  const j = Math.floor(t);
  if (j >= n - 1) return kl[n - 1]!;
  const rest = t - j;
  const a = kl[j]!;
  return a + (kl[j + 1]! - a) * rest;
}

/**
 * Der Farbton in HSV ist ein Winkel — sein Mittel ist der Winkel des
 * aufsummierten Einheitszeigers, nicht der Durchschnitt der Zahlen. Ein
 * Mittel aus 359 und 1 Grad ist 0 und nicht 180.
 *
 * Gewichtet wird mit der SAETTIGUNG (mal dem Maskengewicht): ein farbloser
 * Bildpunkt traegt keinen Farbton bei, und ein blasser weniger als ein
 * kraeftiger. Ohne diese Gewichtung bestimmte eine graue Wand, in welche
 * Richtung ein Bild farblich zeigt.
 */
class ZirkulaeresMittel {
  private x = 0;
  private y = 0;
  private gewicht = 0;

  zaehle(gradH: number, gewicht: number): void {
    if (!(gewicht > 0)) return;
    const bogen = (gradH * Math.PI) / 180;
    this.x += gewicht * Math.cos(bogen);
    this.y += gewicht * Math.sin(bogen);
    this.gewicht += gewicht;
  }

  /** Das Mittel in Grad, 0 bis 360. Ohne Gewicht: 0. */
  grad(): number {
    if (!(this.gewicht > 0)) return 0;
    const g = (Math.atan2(this.y, this.x) * 180) / Math.PI;
    return g < 0 ? g + 360 : g;
  }

  /**
   * Die Laenge des gemittelten Zeigers, 0 bis 1 — wie gebuendelt die Farbtoene
   * sind. 1 heisst: alle zeigen in dieselbe Richtung. Nahe 0 heisst: das
   * Mittel ist rechnerisch da und sagt nichts.
   */
  buendelung(): number {
    if (!(this.gewicht > 0)) return 0;
    return Math.hypot(this.x, this.y) / this.gewicht;
  }

  summe(): number {
    return this.gewicht;
  }
}

/** Der kuerzere der zwei Wege von `von` nach `nach`, in Grad, -180 bis +180. */
export function kuerzesteDrehung(von: number, nach: number): number {
  let d = (nach - von) % 360;
  if (d > 180) d -= 360;
  if (d <= -180) d += 360;
  return d;
}

/**
 * HSV-Felder eines Bildes, je Bildpunkt: Farbton in Grad, Saettigung und Wert
 * in 0..1. Genau die drei Groessen, um die es in Zeile 54 geht.
 */
interface HsvFelder {
  h: Float32Array;
  s: Float32Array;
  v: Float32Array;
  breite: number;
  hoehe: number;
  /** Rot minus Blau je Bildpunkt — die Deckenmaske braucht es (Nachbar). */
  rMinusB: Float32Array;
}

function alsHsv(bild: Bild): HsvFelder {
  const [r, g, b] = alsKanaele(bild);
  const n = bild.breite * bild.hoehe;
  const h = new Float32Array(n);
  const s = new Float32Array(n);
  const v = new Float32Array(n);
  const rMinusB = new Float32Array(n);
  const aus: [number, number, number] = [0, 0, 0];
  for (let i = 0; i < n; i++) {
    rgbZuHsv(r[i]!, g[i]!, b[i]!, aus);
    h[i] = aus[0];
    s[i] = aus[1];
    v[i] = aus[2];
    rMinusB[i] = Math.fround(r[i]! - b[i]!);
  }
  return { h, s, v, breite: bild.breite, hoehe: bild.hoehe, rMinusB };
}

// --- die Bereiche ----------------------------------------------------------

/** Warm-Schwelle und -Breite der Deckenmaske, Zahl fuer Zahl aus `nachbearbeitung.ts`. */
const WARM_SCHWELLE = 0.045;
const WARM_BREITE = 0.085;
/** Farbton-Fenster und Saettigungstor der Gruenmaske, ebenfalls aus `nachbearbeitung.ts`. */
const GRUEN_UNTEN = 58;
const GRUEN_OBEN = 187;
const GRUEN_FLANKE = 12;
const GRUEN_SAT_SCHWELLE = 0.05;
const GRUEN_SAT_FLANKE = 0.1;

interface BereichsVorgaben {
  deckenhoehe: number;
  lichterUnten: number;
  lichterOben: number;
}

/**
 * Das Maskengewicht eines Bildpunkts, 0 bis 1.
 *
 * `eigeneMaske` kommt hier NICHT vor — sie wird gereicht und nicht gerechnet;
 * {@link maskeFuer} setzt sie ein.
 */
function bereichsGewicht(
  bereich: Exclude<BereichName, 'eigeneMaske'>,
  felder: HsvFelder,
  i: number,
  vorgaben: BereichsVorgaben,
): number {
  switch (bereich) {
    case 'ganzesBild':
      return 1;
    case 'deckenholz': {
      const zeile = Math.floor(i / felder.breite);
      const y = Math.fround(Math.fround(zeile) / Math.fround(felder.hoehe));
      const dh = Math.fround(vorgaben.deckenhoehe);
      const nenner = Math.fround(Math.max(vorgaben.deckenhoehe, 1e-6));
      const lage = weich(Math.fround(Math.fround(dh - y) / nenner));
      const waerme = weich(
        Math.fround(Math.fround(felder.rMinusB[i]! - Math.fround(WARM_SCHWELLE)) / Math.fround(WARM_BREITE)),
      );
      return Math.fround(lage * waerme);
    }
    case 'bewuchs': {
      const ton = felder.h[i]!;
      const sat = felder.s[i]!;
      const tonMaske = Math.fround(
        weich(Math.fround(Math.fround(ton - Math.fround(GRUEN_UNTEN)) / Math.fround(GRUEN_FLANKE))) *
          weich(Math.fround(Math.fround(Math.fround(GRUEN_OBEN) - ton) / Math.fround(GRUEN_FLANKE))),
      );
      return Math.fround(
        tonMaske * weich(Math.fround(Math.fround(sat - Math.fround(GRUEN_SAT_SCHWELLE)) / Math.fround(GRUEN_SAT_FLANKE))),
      );
    }
    case 'helleFlaechen':
      // UMGEDREHT gegenueber `belichtung.ts`: dort ist 1 die Flaeche, die
      // GEHOBEN werden darf, hier ist 1 die Flaeche, die gemeint ist.
      return 1 - schutzMaske(felder.v[i]!, vorgaben.lichterUnten, vorgaben.lichterOben);
  }
}

/**
 * Das Maskenfeld eines gemessenen Bereichs zu einem Bild — ein Gewicht je
 * Bildpunkt, zeilenweise, 0 bis 1.
 *
 * WARUM DAS HERAUSGEREICHT WIRD und nicht im Modul bleibt: eine unsichtbare
 * Maske ist eine Behauptung. Mit dieser Funktion laesst sich nachmessen, was
 * ein Bereich wirklich erfasst — und die Probe haelt sie gegen die Maske, die
 * `nachbearbeitung.ts` beim Rechnen tatsaechlich benutzt.
 */
export function bereichsMaske(
  bereich: Exclude<BereichName, 'eigeneMaske'>,
  bild: Bild,
  optionen: { deckenhoehe?: number; lichterUnten?: number; lichterOben?: number } = {},
): Float32Array {
  const felder = alsHsv(bild);
  const vorgaben: BereichsVorgaben = {
    deckenhoehe: optionen.deckenhoehe ?? DECKENHOEHE_VORGABE,
    lichterUnten: optionen.lichterUnten ?? SCHUTZ_UNTEN_VORGABE,
    lichterOben: optionen.lichterOben ?? SCHUTZ_OBEN_VORGABE,
  };
  const n = bild.breite * bild.hoehe;
  const aus = new Float32Array(n);
  for (let i = 0; i < n; i++) aus[i] = klemme01(bereichsGewicht(bereich, felder, i, vorgaben));
  return aus;
}

/** Ein geliefertes Maskenfeld pruefen und in ein `Float32Array` giessen. */
function gelieferteMaske(
  roh: Float32Array | Float64Array | readonly number[] | undefined,
  n: number,
  was: string,
): Float32Array {
  if (roh === undefined) {
    throw new Error(
      `Bereich «eigeneMaske» ohne ${was}: eine Maske muss mitgegeben werden. ` +
        'Ein fehlender Bereich ist ein Fehler, kein leerer Bereich.',
    );
  }
  if (roh.length !== n) {
    throw new Error(
      `Die ${was} hat ${roh.length} Werte, das Bild hat ${n} Bildpunkte. ` +
        'Eine Maske, die nicht passt, wird nicht gedehnt.',
    );
  }
  const aus = new Float32Array(n);
  for (let i = 0; i < n; i++) aus[i] = klemme01(roh[i]!);
  return aus;
}

/** Das Maskenfeld eines Postens fuer ein Bild. */
function maskeFuer(
  posten: UebernahmePosten,
  felder: HsvFelder,
  vorgaben: BereichsVorgaben,
  fuerVorbild: boolean,
): Float32Array {
  const n = felder.breite * felder.hoehe;
  if (posten.bereich === 'eigeneMaske') {
    if (fuerVorbild) {
      // Fehlt die Vorbildmaske, wird das ganze Vorbild gemessen — das ist
      // eine Entscheidung und wird im Bericht als solche ausgewiesen
      // (`vorbildGanz`), nicht stillschweigend getroffen.
      if (posten.maskeVorbild === undefined) return new Float32Array(n).fill(1);
      return gelieferteMaske(posten.maskeVorbild, n, 'Maske für das Vorbild');
    }
    return gelieferteMaske(posten.maske, n, 'Maske');
  }
  const aus = new Float32Array(n);
  for (let i = 0; i < n; i++) aus[i] = klemme01(bereichsGewicht(posten.bereich, felder, i, vorgaben));
  return aus;
}

/**
 * Die Stichprobe eines Bereichs: die Werte an den Bildpunkten mit
 * Maskengewicht ueber 0.5.
 *
 * WARUM UEBER 0.5 UND NICHT GEWICHTET: das ist die Zaehlweise, mit der
 * `nachbearbeitung.ts` seine «erfasste Flaeche» meldet, und damit dieselbe
 * Zahl, die im Bericht steht. Eine gewichtete Quantilrechnung waere feiner
 * und haette eine zweite, nicht vergleichbare Flaechendefinition eingefuehrt.
 */
function stichprobe(werte: Float32Array, maske: Float32Array): Float32Array {
  let m = 0;
  for (let i = 0; i < maske.length; i++) if (maske[i]! > 0.5) m++;
  const aus = new Float32Array(m);
  let k = 0;
  for (let i = 0; i < maske.length; i++) if (maske[i]! > 0.5) aus[k++] = werte[i]!;
  return aus;
}

// ---------------------------------------------------------------------------
// Das Werkzeug
// ---------------------------------------------------------------------------

/** Was ein Posten vor dem Schreiben ausgerechnet hat. */
interface PostenPlan {
  posten: UebernahmePosten;
  staerke: number;
  maske: Float32Array;
  kennlinie: Float64Array | undefined;
  drehung: number | undefined;
  bericht: UebernahmePostenBericht;
}

/**
 * Aus dem Vorbild die benannten Eigenschaften in den benannten Bereichen
 * uebernehmen — und nur diese.
 *
 * Der Ablauf, Schritt fuer Schritt:
 *  1. beide Bilder nach H/S/V (`float32` wie bei den Nachbarn);
 *  2. je Posten die Maske in BEIDEN Bildern und daraus der ZIELWERT —
 *     Kennlinie bei Saettigung und Helligkeit, Drehung beim Farbton. Alles
 *     aus den UNVERAENDERTEN Bildern, damit kein Posten dem naechsten die
 *     Grundlage verschiebt;
 *  3. je Bildpunkt die Gewichte aller Posten sammeln. Ist die Summe null,
 *     wird der Punkt BYTEWEISE kopiert und nicht gerechnet;
 *  4. sonst H, S, V getrennt nachfuehren, zurueck nach RGB, runden;
 *  5. nachmessen, was sich bewegt hat — auch das, was sich NICHT bewegen
 *     sollte.
 */
export function uebernahme(
  bild: Bild,
  vorbild: Bild,
  optionen: UebernahmeOptionen,
): UebernahmeErgebnis {
  if (optionen.posten.length === 0) {
    throw new Error(
      'Uebernahme ohne Posten: es muss gesagt werden, WAS aus dem Vorbild kommen soll. ' +
        'Eine leere Liste ist ein Fehler und kein Nichtstun.',
    );
  }
  for (const p of optionen.posten) {
    if (!EIGENSCHAFTEN.includes(p.eigenschaft)) {
      throw new Error(`Unbekannte Eigenschaft «${String(p.eigenschaft)}».`);
    }
    if (!BEREICHE.includes(p.bereich)) {
      throw new Error(`Unbekannter Bereich «${String(p.bereich)}».`);
    }
  }

  const vorgaben: BereichsVorgaben = {
    deckenhoehe: optionen.deckenhoehe ?? DECKENHOEHE_VORGABE,
    lichterUnten: optionen.lichterUnten ?? SCHUTZ_UNTEN_VORGABE,
    lichterOben: optionen.lichterOben ?? SCHUTZ_OBEN_VORGABE,
  };

  const q = alsHsv(bild);
  const v = alsHsv(vorbild);
  const n = bild.breite * bild.hoehe;

  // --- Schritt 2: alle Zielwerte aus den UNVERAENDERTEN Bildern -------------
  const plaene: PostenPlan[] = [];
  for (const posten of optionen.posten) {
    const staerke = klemme01(posten.staerke ?? 1);
    const maske = maskeFuer(posten, q, vorgaben, false);
    const maskeV = maskeFuer(posten, v, vorgaben, true);

    let erfasst = 0;
    let beruehrt = 0;
    for (let i = 0; i < n; i++) {
      if (maske[i]! > 0.5) erfasst++;
      if (maske[i]! > 0) beruehrt++;
    }

    const feldQ = posten.eigenschaft === 'saettigung' ? q.s : posten.eigenschaft === 'helligkeit' ? q.v : q.h;
    const feldV = posten.eigenschaft === 'saettigung' ? v.s : posten.eigenschaft === 'helligkeit' ? v.v : v.h;
    const probeQ = stichprobe(feldQ, maske);
    const probeV = stichprobe(feldV, maskeV);

    if (probeV.length === 0) {
      throw new Error(
        `Das Vorbild hat im Bereich «${UEBERNAHME_BEREICH_LABEL[posten.bereich]}» keine Fläche. ` +
          'Ohne Vorbildfläche gibt es nichts zu übernehmen — das wird gemeldet und nicht still übersprungen.',
      );
    }
    if (probeQ.length === 0) {
      throw new Error(
        `Das Bild hat im Bereich «${UEBERNAHME_BEREICH_LABEL[posten.bereich]}» keine Fläche. ` +
          'Es gibt nichts, worauf die Übernahme wirken könnte.',
      );
    }

    const gemeinsam = {
      eigenschaft: posten.eigenschaft,
      bereich: posten.bereich,
      staerke,
      erfassteFlaecheProzent: (erfasst / n) * 100,
      beruehrteFlaecheProzent: (beruehrt / n) * 100,
      stichprobeBild: probeQ.length,
      stichprobeVorbild: probeV.length,
      vorbildGanz: posten.bereich === 'eigeneMaske' && posten.maskeVorbild === undefined,
    };

    if (posten.eigenschaft === 'farbton') {
      const mQ = new ZirkulaeresMittel();
      const mV = new ZirkulaeresMittel();
      for (let i = 0; i < n; i++) if (maske[i]! > 0.5) mQ.zaehle(q.h[i]!, q.s[i]!);
      for (let i = 0; i < maskeV.length; i++) if (maskeV[i]! > 0.5) mV.zaehle(v.h[i]!, v.s[i]!);
      if (!(mQ.summe() > 0) || !(mV.summe() > 0)) {
        throw new Error(
          `Farbton aus «${UEBERNAHME_BEREICH_LABEL[posten.bereich]}»: die Fläche ist farblos, ` +
            'ein Farbton lässt sich dort nicht messen.',
        );
      }
      const drehung = kuerzesteDrehung(mQ.grad(), mV.grad());
      plaene.push({
        posten,
        staerke,
        maske,
        kennlinie: undefined,
        drehung,
        bericht: {
          ...gemeinsam,
          wertVorher: mQ.grad(),
          wertVorbild: mV.grad(),
          wertNachher: 0, // wird in Schritt 5 gemessen
          drehungGrad: drehung,
          buendelungBild: mQ.buendelung(),
          buendelungVorbild: mV.buendelung(),
          kennlinie: undefined,
          farblosUebergangenProzent: undefined,
        },
      });
    } else {
      const kl = kennlinie(probeQ, probeV);
      let summeQ = 0;
      for (let i = 0; i < probeQ.length; i++) summeQ += probeQ[i]!;
      let summeV = 0;
      for (let i = 0; i < probeV.length; i++) summeV += probeV[i]!;
      let farblos = 0;
      if (posten.eigenschaft === 'saettigung') {
        for (let i = 0; i < n; i++) {
          if (maske[i]! > 0.5 && q.s[i]! < SAT_TOR_SCHWELLE) farblos++;
        }
      }
      plaene.push({
        posten,
        staerke,
        maske,
        kennlinie: kl,
        drehung: undefined,
        bericht: {
          ...gemeinsam,
          wertVorher: (summeQ / probeQ.length) * 255,
          wertVorbild: (summeV / probeV.length) * 255,
          wertNachher: 0, // wird in Schritt 5 gemessen
          drehungGrad: undefined,
          buendelungBild: undefined,
          buendelungVorbild: undefined,
          kennlinie: kl,
          farblosUebergangenProzent:
            posten.eigenschaft === 'saettigung' ? (farblos / Math.max(erfasst, 1)) * 100 : undefined,
        },
      });
    }
  }

  // --- Schritt 3+4: schreiben ----------------------------------------------
  const kanaele = bild.kanaele;
  const aus = new Uint8ClampedArray(n * kanaele);
  // Zuerst alles kopieren. Was kein Bereich beruehrt, bleibt damit BYTEWEISE
  // stehen — auch der Alphakanal, wie bei allen drei Nachbarn.
  for (let i = 0; i < n * kanaele; i++) aus[i] = bild.daten[i]!;

  let ueberlappt = 0;
  let ausserhalb = 0;
  const rgb: [number, number, number] = [0, 0, 0];

  for (let i = 0; i < n; i++) {
    let beruehrende = 0;
    let h = q.h[i]!;
    let s = q.s[i]!;
    let val = q.v[i]!;
    for (const plan of plaene) {
      const m = plan.maske[i]!;
      // GEZAEHLT WIRD DIE WIRKUNG, NICHT DIE ABSICHT: ein Posten mit Staerke 0
      // beruehrt nichts, und dieser Bildpunkt wird darum kopiert statt durch
      // HSV und zurueck geschickt. Sonst waere «Staerke 0» nicht mehr
      // bytegleich mit «nichts tun» — ein stiller Unterschied, den niemand
      // erwartet.
      const gewicht = m * plan.staerke;
      if (!(gewicht > 0)) continue;
      beruehrende++;
      if (plan.posten.eigenschaft === 'farbton') {
        h = (h + gewicht * plan.drehung!) % 360;
        if (h < 0) h += 360;
      } else if (plan.posten.eigenschaft === 'saettigung') {
        // Das Farblos-Tor: an einem Punkt ohne Buntheit wuerde eine angehobene
        // Saettigung eine Farbe ERFINDEN (Farbton 0, also Rot).
        const tor = weich((q.s[i]! - SAT_TOR_SCHWELLE) / SAT_TOR_FLANKE);
        const ziel = klemme01(aufKennlinie(q.s[i]!, plan.kennlinie!));
        s = klemme01(s + gewicht * tor * (ziel - s));
      } else {
        const ziel = klemme01(aufKennlinie(q.v[i]!, plan.kennlinie!));
        val = klemme01(val + gewicht * (ziel - val));
      }
    }
    if (beruehrende === 0) {
      ausserhalb++;
      continue;
    }
    if (beruehrende > 1) ueberlappt++;
    hsvZuRgb(h, s, val, rgb);
    for (let c = 0; c < 3; c++) {
      const x = klemme01(rgb[c]!);
      // Runden, nicht abschneiden — dieselbe Wahl wie in `nachbearbeitung.ts`
      // und `belichtung.ts`: Abschneiden zieht im Mittel ein halbes Byte ab.
      aus[i * kanaele + c] = Math.trunc(Math.fround(Math.fround(x * 255) + Math.fround(0.5)));
    }
  }

  const ergebnis: Bild = { daten: aus, breite: bild.breite, hoehe: bild.hoehe, kanaele: bild.kanaele };

  // --- Schritt 5: nachmessen, an den AUSGEGEBENEN Bytes --------------------
  const nach = alsHsv(ergebnis);

  let unveraendert = 0;
  for (let i = 0; i < n; i++) {
    let gleich = true;
    for (let c = 0; c < 3; c++) {
      if (aus[i * kanaele + c] !== bild.daten[i * kanaele + c]) {
        gleich = false;
        break;
      }
    }
    if (gleich) unveraendert++;
  }

  const masse: Record<EigenschaftName, EigenschaftsMass> = {
    farbton: messeFarbton(q, nach, n),
    saettigung: messeLinear(q.s, nach.s, n),
    helligkeit: messeLinear(q.v, nach.v, n),
  };

  for (const plan of plaene) {
    if (plan.posten.eigenschaft === 'farbton') {
      const m = new ZirkulaeresMittel();
      for (let i = 0; i < n; i++) if (plan.maske[i]! > 0.5) m.zaehle(nach.h[i]!, nach.s[i]!);
      plan.bericht.wertNachher = m.grad();
    } else {
      const feldNach = plan.posten.eigenschaft === 'saettigung' ? nach.s : nach.v;
      let summe = 0;
      let zahl = 0;
      for (let i = 0; i < n; i++) {
        if (plan.maske[i]! > 0.5) {
          summe += feldNach[i]!;
          zahl++;
        }
      }
      plan.bericht.wertNachher = zahl > 0 ? (summe / zahl) * 255 : 0;
    }
  }

  return {
    bild: ergebnis,
    bericht: {
      bild: [bild.breite, bild.hoehe],
      vorbild: [vorbild.breite, vorbild.hoehe],
      posten: plaene.map((p) => p.bericht),
      ueberlappungProzent: (ueberlappt / n) * 100,
      ausserhalbProzent: (ausserhalb / n) * 100,
      unveraenderteBildpunkteProzent: (unveraendert / n) * 100,
      eigenschaftenGesamt: masse,
      wasGeaendertWurde: UEBERNAHME_WAS_GEAENDERT_WURDE,
    },
  };
}

/**
 * Saettigung oder Helligkeit ueber das ganze Bild messen — Mittel in
 * Byte-Schritten, groesste Abweichung je Bildpunkt in Byte-Schritten.
 *
 * Alle Summen in `float64`; die Einzelwerte kommen aus `float32`-Feldern.
 */
function messeLinear(vorher: Float32Array, nachher: Float32Array, n: number): EigenschaftsMass {
  let sv = 0;
  let sn = 0;
  let groesste = 0;
  let bewegt = 0;
  for (let i = 0; i < n; i++) {
    const a = vorher[i]!;
    const b = nachher[i]!;
    sv += a;
    sn += b;
    const d = Math.abs(b - a) * 255;
    if (d > groesste) groesste = d;
    if (d > 0) bewegt++;
  }
  return {
    mittelVorher: (sv / n) * 255,
    mittelNachher: (sn / n) * 255,
    groessteAbweichung: groesste,
    bildpunkteBewegt: bewegt,
    bildpunkteGemessen: n,
  };
}

/**
 * Den Farbton ueber das ganze Bild messen.
 *
 * NUR AN PUNKTEN MIT GENUG SAETTIGUNG (in beiden Fassungen, s.
 * {@link FARBTON_MESSGRENZE}). An einem fast grauen Punkt schwenkt der Farbton
 * bei einer Aenderung von einem Byte um viele Grad — er wuerde die Kennzahl
 * «groesste Abweichung» allein bestimmen und ueber den Farbton der Flaechen,
 * die man ueberhaupt sieht, nichts aussagen. Das ist die Lehre aus dem
 * Tischplatten-Befund: am entscheidenden Instrument messen.
 */
function messeFarbton(vorher: HsvFelder, nachher: HsvFelder, n: number): EigenschaftsMass {
  const mV = new ZirkulaeresMittel();
  const mN = new ZirkulaeresMittel();
  let groesste = 0;
  let bewegt = 0;
  let gemessen = 0;
  for (let i = 0; i < n; i++) {
    mV.zaehle(vorher.h[i]!, vorher.s[i]!);
    mN.zaehle(nachher.h[i]!, nachher.s[i]!);
    if (vorher.s[i]! < FARBTON_MESSGRENZE || nachher.s[i]! < FARBTON_MESSGRENZE) continue;
    gemessen++;
    const d = Math.abs(kuerzesteDrehung(vorher.h[i]!, nachher.h[i]!));
    if (d > groesste) groesste = d;
    if (d > 0) bewegt++;
  }
  return {
    mittelVorher: mV.grad(),
    mittelNachher: mN.grad(),
    groessteAbweichung: groesste,
    bildpunkteBewegt: bewegt,
    bildpunkteGemessen: gemessen,
  };
}
