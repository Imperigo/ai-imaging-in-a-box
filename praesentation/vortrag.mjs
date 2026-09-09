// Schlusspraesentation "Beweisgang KosmoVis" — Bilder gross, ein Satz je Folie.
//
// Die Regeln dieser Fassung, mit dem Owner am 09.09.2026 festgelegt:
//   1  Ein Bild fuellt die Folie. Es ist das Argument, nicht die Beigabe.
//   2  Ein Satz je Folie. Alles Erklaerende steht in den Sprechernotizen.
//   3  Keine Kaertchen, keine Messwertkaestchen, keine Aufzaehlungen.
//   4  Zahlen nur da, wo sie den Satz tragen.
import pptxgen from "pptxgenjs";
import { readFileSync } from "node:fs";

const GRUND = "101318";
const TINTE = "EDEBE6";
const MATT = "9096A0";
const LEISE = "5E646E";
const ORANGE = "E08A3C";
const ROT = "D4574B";

const SERIF = "Cambria";
const SANS = "Calibri";
const MONO = "Courier New";

const B = "bilder/";
const W = 13.333;
const H = 7.5;
const RAND = 0.75;
const SPALTE = W - 2 * RAND;

// Der Bildkasten: alles zwischen Satz und Fussmarke.
const BILD_OBEN = 1.95;
const BILD_UNTEN = 6.55;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Andrin Bau";
pres.title = "Beweisgang KosmoVis";
pres.subject = "Schlusspraesentation Vertiefungsarbeit HS26, ITA, ETH Zuerich";

// Seitenverhaeltnisse, aus den Dateien gelesen — ein gestrecktes Beweisbild waere
// eine Falschaussage ueber die Messung.
function seiten(datei) {
  const d = readFileSync(B + datei);
  return d.readUInt32BE(16) / d.readUInt32BE(20);
}

let nr = 0;

function neu() {
  nr += 1;
  const s = pres.addSlide();
  s.background = { color: GRUND };
  return s;
}

function marke(s, quelle) {
  s.addText(String(nr).padStart(2, "0"), {
    x: RAND, y: 6.7, w: 0.6, h: 0.3, isTextBox: true, margin: 0,
    fontFace: MONO, fontSize: 9, color: LEISE,
  });
  if (quelle) {
    s.addText(quelle, {
      x: W - RAND - 6.0, y: 6.7, w: 6.0, h: 0.3, isTextBox: true, margin: 0,
      align: "right", fontFace: SANS, fontSize: 9, color: LEISE,
    });
  }
}

function satz(s, text, farbe = TINTE) {
  // Zwei Zeilen sind das Maximum. Wer drei braucht, hat keinen Satz, sondern einen
  // Absatz — und der gehoert in die Notizen.
  if (text.length > 150) {
    throw new Error(`Satz zu lang (${text.length} Zeichen): «${text}»`);
  }
  s.addText(text, {
    x: RAND, y: 0.62, w: SPALTE, h: 1.15, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 25, color: farbe, lineSpacing: 34,
  });
}

/** Ein Bild, so gross wie der Kasten es zulaesst, mittig. */
function einBild(s, datei, { unten = null } = {}) {
  const kh = (unten ? BILD_UNTEN - 0.45 : BILD_UNTEN) - BILD_OBEN;
  const kb = SPALTE;
  const v = seiten(datei);
  let b = kb, h = kb / v;
  if (h > kh) { h = kh; b = kh * v; }
  const x = RAND + (kb - b) / 2;
  s.addImage({ path: B + datei, x, y: BILD_OBEN, w: b, h });
  if (unten) {
    s.addText(unten, {
      x: RAND, y: BILD_OBEN + h + 0.12, w: SPALTE, h: 0.34, isTextBox: true, margin: 0,
      align: "center", fontFace: SANS, fontSize: 11, color: MATT, italic: true,
    });
  }
  return { x, y: BILD_OBEN, b, h };
}

/** Zwei Bilder nebeneinander, gleiche Hoehe, mit je einer kleinen Zeile darunter. */
function zweiBilder(s, a, b, ua, ub) {
  const luft = 0.5;
  const kh = BILD_UNTEN - 0.45 - BILD_OBEN;
  const kb = (SPALTE - luft) / 2;
  const bilder = [[a, ua], [b, ub]].map(([d]) => {
    const v = seiten(d);
    let bb = kb, hh = kb / v;
    if (hh > kh) { hh = kh; bb = kh * v; }
    return { d, bb, hh };
  });
  const hoehe = Math.min(...bilder.map((x) => x.hh));
  bilder.forEach((x, i) => {
    const bb = hoehe * seiten(x.d);
    const feld = RAND + i * (kb + luft);
    s.addImage({ path: B + x.d, x: feld + (kb - bb) / 2, y: BILD_OBEN, w: bb, h: hoehe });
    s.addText(i === 0 ? ua : ub, {
      x: feld, y: BILD_OBEN + hoehe + 0.12, w: kb, h: 0.34, isTextBox: true, margin: 0,
      align: "center", fontFace: SANS, fontSize: 11, color: MATT, italic: true,
    });
  });
}

/** Eine Folie, die nur einen Satz zeigt. Zweimal im ganzen Vortrag — als Atempause. */
function aussage(s, gross, klein) {
  s.addText(gross, {
    x: RAND, y: 2.6, w: SPALTE - 1.2, h: 1.6, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 40, color: TINTE, lineSpacing: 52,
  });
  if (klein) {
    s.addText(klein, {
      x: RAND, y: 4.35, w: SPALTE - 2.0, h: 1.9, isTextBox: true, margin: 0,
      fontFace: SANS, fontSize: 16, color: MATT, lineSpacing: 24,
    });
  }
}

/** Wo ein Bild von der HomeStation hingehoert, das noch nicht da ist. */
function platzhalter(s, was) {
  const kh = BILD_UNTEN - BILD_OBEN;
  s.addShape(pres.ShapeType.rect, {
    x: RAND + 1.5, y: BILD_OBEN, w: SPALTE - 3.0, h: kh,
    fill: { color: "171B22" }, line: { color: ORANGE, width: 1.25, dashType: "dash" },
  });
  s.addText("Bild folgt", {
    x: RAND + 1.5, y: BILD_OBEN + kh / 2 - 0.6, w: SPALTE - 3.0, h: 0.45,
    isTextBox: true, margin: 0, align: "center",
    fontFace: SANS, fontSize: 15, bold: true, color: ORANGE,
  });
  s.addText(was, {
    x: RAND + 2.5, y: BILD_OBEN + kh / 2 - 0.1, w: SPALTE - 5.0, h: 1.0,
    isTextBox: true, margin: 0, align: "center",
    fontFace: SANS, fontSize: 13, color: MATT, lineSpacing: 19,
  });
}

// =============================================================================
// I · Aufschlag
// =============================================================================
{
  const s = neu();
  s.addText("Beweisgang KosmoVis", {
    x: RAND, y: 2.55, w: 11.0, h: 1.2, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 56, bold: true, color: TINTE,
  });
  s.addText("Aus einem IFC-Modell ein Bild — und der Nachweis, dass es dasselbe Bauwerk zeigt", {
    x: RAND, y: 3.8, w: 11.0, h: 0.5, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 19, color: MATT,
  });
  s.addText("Andrin Bau · Vertiefungsarbeit HS26 · ITA · ETH Zürich · Betreuung Gonzalo Casas", {
    x: RAND, y: 6.5, w: 11.0, h: 0.3, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 12, color: LEISE,
  });
  s.addNotes("30 Minuten. Der Bogen: erst das Ergebnis, dann der Weg dorthin, dann die Methode, "
    + "dann die Grenzen der eigenen Prüfung.");
}

{
  const s = neu();
  satz(s, "Das hier ist das Ergebnis: links das Modell, rechts das Bild, das die Kette daraus gemacht hat.");
  platzhalter(s, "C0.png neben der Tiefenkarte der Gebäudeszene — bestellt bei der HomeStation, auf-20260909-96");
  marke(s, "erzeugt am 08.09.2026, RTX 5090");
  s.addNotes("Score 0,9682, Übereinstimmung über dem Bauwerk 0,9029. Fünf Geschosse, "
    + "Stützenraster, Fassadentafeln — synthetische Geometrie aus dem eigenen Repo.");
}

{
  const s = neu();
  satz(s, "Dazwischen liegen fünf Stufen, und keine davon braucht eine Eingabe von Hand.");
  einBild(s, "kette.png", { unten: "IFC → glb → Multipass → Bild → Prüfung, ein Lauf, mit den gemessenen Zeiten" });
  marke(s, "Beweis 20");
  s.addNotes("Der Renderschritt braucht GPU und Gewichte; alles andere läuft auf jedem Rechner. "
    + "Die Zeiten stammen aus diesem einen Lauf, nicht aus einem Mittelwert.");
}

// =============================================================================
// II · Was hineingeht
// =============================================================================
{
  const s = neu();
  satz(s, "Hinein geht ein IFC-Modell. Sonst nichts — kein Standpunkt, kein Ausschnitt, keine Einstellung.");
  einBild(s, "ifc_grundriss.png", { unten: "sechs Bauteile, 72 Dreiecke — die Testgeometrie ist im Repo erzeugbar" });
  marke(s, "Beweis 20, Stufe 1");
  s.addNotes("Regel 3 des Projekts: keine echten Projektdaten im Repo. Die Testgeometrie wird "
    + "erzeugt, nicht abgelegt — darum kann jeder diesen Lauf nachfahren.");
}

{
  const s = neu();
  satz(s, "Zwei Normversionen, zwei Einheiten, viermal umgewandelt — und das Differenzbild zwischen zwei Renders ist vollständig schwarz.");
  einBild(s, "vier_ifc_diff.png", { unten: "IFC4 in Metern gegen IFC2X3 in Millimetern, grösster Unterschied 0,00000" });
  marke(s, "Beweis 26");
  s.addNotes("An 40 echten Dateien gemessen: 10 waren IFC2X3, und alle zehn ArchiCAD-Exporte "
    + "darunter. 25 von 40 standen in Millimetern. Wer nur gegen IFC4 in Metern prüft, prüft "
    + "nicht gegen das, was das verbreitetste Autorenprogramm liefert.");
}

{
  const s = neu();
  satz(s, "Zuerst wird das Gelände vom Bauwerk getrennt — hier schrumpft die Szene dabei um zwei Drittel.");
  einBild(s, "trennung.png", { unten: "Szenenbox gegen Bauwerksbox, Schrumpfung 0,6665" });
  marke(s, "Beweis 13");
  s.addNotes("Ohne diesen Schritt rahmt die Kamera das Gelände. Entschieden wird nach dem "
    + "Bauteilnamen; greift der nicht, urteilt eine Formregel über Grundrissanteil, Flachheit "
    + "und Tieflage.");
}

// =============================================================================
// III · Die Kamera setzt sich selbst
// =============================================================================
{
  const s = neu();
  satz(s, "Die Kamera sucht sich zwölf Standpunkte selbst — aus der gemessenen Bauwerksbox, nicht aus einer Voreinstellung.");
  einBild(s, "kameras.png", { unten: "vier Hauptrichtungen, acht mit 35° Versatz" });
  marke(s, "Beweis 09");
  s.addNotes("Der Versatz von 35° ist die Antwort auf einen Befund: Die vier frontalen "
    + "Richtungen zeigen je nur eine Fassade.");
}

{
  const s = neu();
  satz(s, "Bei jedem einzelnen Standpunkt liegen acht von acht Gebäudeecken im Bild, mit demselben Füllgrad 0,70.");
  einBild(s, "ecken.png", { unten: "Kamera Nord, Abstand 56,6 m, Überstehen 0,818" });
  marke(s, "Beweis 09");
  s.addNotes("Der Eckentest ist der Riegel dahinter: Er prüft alle acht Ecken der Hüllbox "
    + "gegen den Bildrand, statt sich auf den gerechneten Abstand zu verlassen.");
}

{
  const s = neu();
  satz(s, "Links kippt die Kamera und die Linien stürzen. Rechts steht sie senkrecht und verschiebt stattdessen das Objektiv.");
  einBild(s, "shift.png", { unten: "Lot gekippt 0,362° gegen Lot mit Shift 0,000° — nötiger Shift 1,89 mm" });
  marke(s, "Beweis 11");
  s.addNotes("Über Gebäudehöhen von 3 bis 100 m bleibt der nötige Shift unter 2 mm; kein "
    + "einziger von 96 Fällen überschreitet die Objektivgrenze. Die Kamera stand fünf Tage "
    + "lang gekippt, bis das jemand gemessen hat.");
}

{
  const s = neu();
  satz(s, "Gerahmt wird das Bauwerk, nicht die Szene — sonst füllt das Gelände das Bild und das Haus wird zum Fleck.");
  einBild(s, "rahmung.png", { unten: "nach der Szene gerahmt 0,2795 — nach dem Bauwerk 0,6985" });
  marke(s, "Beweis 13");
  s.addNotes("Beide Bilder halten den bestellten Deckungsgrad 0,70 ein. Links gilt er für das "
    + "Gelände, rechts für das Bauwerk — dieselbe Bestellung, zwei völlig verschiedene Bilder.");
}

{
  const s = neu();
  satz(s, "Aus den zwölf wählt sie drei, die alle vier Fassaden zeigen: drei Renderläufe statt zwölf.");
  einBild(s, "auswahl.png", { unten: "gewählt nNE + eES + wWS, Fassadenabdeckung 4 von 4" });
  marke(s, "Beweis 12");
  s.addNotes("Alle 56 Dreierkombinationen werden bewertet, acht liegen im Gleichstand. "
    + "Gewählt wird nach Abdeckung und Streuung, nicht nach dem besten Einzelbild.");
}

// =============================================================================
// IV · Innen
// =============================================================================
{
  const s = neu();
  satz(s, "Auch innen setzt sie den Standpunkt selbst: zwei Räume, vier Blickrichtungen, Auge auf halber Raumhöhe.");
  einBild(s, "raum_plan.png", { unten: "Raum Nord 26,6 m², Raum Süd 5,9 m² — je frontal und über Eck" });
  marke(s, "Beweis 14");
  s.addNotes("Der Innenstandpunkt kommt aus den IfcSpace-Räumen der Datei. Die Kamera steht "
    + "waagrecht, das Auge auf halber Raumhöhe, die Brennweite bei 24 mm.");
}

{
  const s = neu();
  satz(s, "Frontal und über Eck, aus demselben Raum — beides gerechnet, nicht gewählt.");
  zweiBilder(s, "innen_frontal.png", "innen_eck.png",
    "frontal, Blick auf die Zielwand", "über Eck, längste Sichtweite");
  marke(s, "Beweis 21 — über den Produktivweg gefahren");
  s.addNotes("Diese beiden Bilder sind über den echten Auftragsweg entstanden, nicht über einen "
    + "Testaufruf: Auftrag aus dem fremden Vertrag, Abholer, Blender. Im Bericht steht die "
    + "Brennweite 24,0 mm.");
}

{
  const s = neu();
  satz(s, "Die Augenhöhe entscheidet, was im Bild ist: auf 2,02 m verschwindet der Boden ganz.");
  einBild(s, "augenhoehe.png", { unten: "Wandanteil bei 0,68 m · 1,35 m · 2,02 m — Bodenanteil 0,323 / 0,146 / 0,000" });
  marke(s, "Beweis 22");
  s.addNotes("Gemessen gegen den gerenderten Bildinhalt, nicht gerechnet: Der Bodenanteil aus "
    + "der Formel und der im Material-Pass gezählte weichen um 0,001 voneinander ab.");
}

// =============================================================================
// V · Was Blender liefert
// =============================================================================
{
  const s = neu();
  satz(s, "Ein einziger Blender-Lauf liefert vier Bilder — und alle vier zeigen dieselbe Silhouette.");
  einBild(s, "multipass.png", { unten: "Ansicht · Tiefe · Material-ID · Tiefe in Falschfarben" });
  marke(s, "Beweis 02");
  s.addNotes("Die gemeinsame Silhouette ist der Beleg, dass alle vier aus derselben Kamera "
    + "stammen. Blender läuft als eigenständiges Programm, nicht als Bibliothek — das ist eine "
    + "Lizenzgrenze, keine Bequemlichkeit.");
}

{
  const s = neu();
  satz(s, "Die Tiefe kommt in Metern zurück, nicht in Graustufen: hier von 30,0 bis 68,2 Meter.");
  einBild(s, "tiefe.png", { unten: "aus der EXR-Datei, nah hell — die Karte, gegen die später gemessen wird" });
  marke(s, "Beweis 02");
  s.addNotes("Diese Karte ist das Soll der ganzen Prüfung. Sie kommt aus dem Renderer und "
    + "nicht aus einer Schätzung — der Schätzer arbeitet später auf dem erzeugten Bild.");
}

{
  const s = neu();
  satz(s, "Und die bestellte Sonne kommt wirklich an: hell ist genau die Fassade, die zwischen Morgen und Abend ins Licht kommt.");
  einBild(s, "sonne_diff.png", { unten: "Differenz Morgen gegen Abend, gleiche Kamera, nur der Sonnenstand verschoben" });
  marke(s, "Beweis 25");
  s.addNotes("Bis Ende August lief diese Bestellung ins Leere und ergab ein sauberes, gut "
    + "belichtetes, falsches Bild. Der Beweis hat sich beim Bauen selbst angehalten: Das erste "
    + "Mass zählte Punkte unter 0,25 als Schatten — der dunkelste Wert dieser Renders liegt bei "
    + "0,34, es gab null solche Punkte.");
}

// =============================================================================
// VI · Das Bild
// =============================================================================
{
  const s = neu();
  satz(s, "Aus der Tiefenkarte wird ein Bild — sie führt das Bildmodell, statt es nur anzustossen.");
  platzhalter(s, "Tiefenkarte und erzeugtes Bild nebeneinander — bestellt bei der HomeStation");
  marke(s, "auf-20260909-92, Stärke 1,00");
  s.addNotes("Der Weg heisst ControlNet: ein eigener Steuereingang des Bildmodells. Vier Wochen "
    + "lang lief die Kette ohne ihn — die Tiefenkarte ging als Bild hinein und ersetzte dabei "
    + "die Vorlage. Der Unterschied im Ergebnis: 0,359 gegen 0,98.");
}

{
  const s = neu();
  satz(s, "Zwölf Bilder, drei Startwerte je Fall — denn zwischen zwei Läufen liegt mehr Zufall als zwischen zwei Einstellungen.");
  platzhalter(s, "A0, B0, C0, C2 als Reihe — bestellt bei der HomeStation");
  marke(s, "auf-20260909-92");
  s.addNotes("Ein Render dauert 1,6 Sekunden. Drei Startwerte je Fall kosten also fast nichts "
    + "und sind der Unterschied zwischen einer Messung und einem Eindruck.");
}

{
  const s = neu();
  satz(s, "Das bestbewertete Bild der Reihe.");
  platzhalter(s, "B0.png — Score 0,9884, Übereinstimmung über dem Bauwerk 0,9748");
  marke(s, "auf-20260909-92, Fall B, Startwert 0");
  s.addNotes("Und jetzt der unangenehme Teil: Die HomeStation beschreibt dieses Bild als «eine "
    + "graue geriffelte Masse, die kein Mensch als Gebäude bezeichnen würde». Es hat den besten "
    + "Wert der ganzen Reihe.");
}

{
  const s = neu();
  satz(s, "Und das schönste Bild der Reihe hat die schlechteste Bauwerkstreue.", ROT);
  platzhalter(s, "C2.png — Score 0,8965, Übereinstimmung über dem Bauwerk 0,1437");
  marke(s, "auf-20260909-92, Fall C, Startwert 2");
  s.addNotes("Fenster, Gesimse, Satteldach — das einzige Bild, das wie ein Haus aussieht. Über "
    + "dem Bauwerk selbst ordnet die Karte fast nichts richtig. Von hier an geht es darum, "
    + "warum geprüft werden muss.");
}

// =============================================================================
// VII · Wie ich gemessen habe
// =============================================================================
{
  const s = neu();
  aussage(s, "«Nicht messbar» ist weder bestanden noch durchgefallen.",
    "Die erste von fünf Regeln, und keine davon ist vorab gesetzt — jede stammt aus einem Lauf, "
    + "der schiefgegangen ist. Ein Riegel, der bei fehlenden Daten «bestanden» sagt, ist keiner.");
  marke(s, "docs/METHODE_2026-09-10.md");
  s.addNotes("Die anderen vier: Ein Wächter, der nicht fällt, bewacht nichts. Eine Vorprüfung "
    + "darf widerlegen, nie zusagen. Eine Zahl gehört an die Bedingung, unter der sie gemessen "
    + "wurde. Und: Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden — er wird "
    + "geglaubt.");
}

{
  const s = neu();
  satz(s, "Jeder Wächter wird mit eingebautem Fehler gegengeprüft: Einer, der nicht fällt, bewacht nichts.");
  einBild(s, "mutation.png", { unten: "Regel 3 als ausgeführter Wächter: 542 Dateien geprüft, 0 Treffer" });
  marke(s, "Beweis 19");
  s.addNotes("Ein Nullbefund ist nur dann eine Aussage, wenn der Wächter beweisbar anschlagen "
    + "kann. Darum wird jeder mit einem absichtlich eingebauten Fehler gegengefahren.");
}

{
  const s = neu();
  satz(s, "Und jede Zahl gehört an ihre Bedingung: Der Zufall zwischen zwei Läufen ist grösser als jede Einstellung.");
  einBild(s, "zufall.png", { unten: "Startwertstreuung 0,2269 gegen den stärksten Parametereffekt 0,14" });
  marke(s, "Beweis 28");
  s.addNotes("Zwei Folgen: Ein Vergleich zweier Einstellungen mit je einem Bild misst den "
    + "Zufall. Und die Auswahl über mehrere Startwerte ist der billigste Qualitätssprung der "
    + "Kette. Die 0,2269 gelten für den Lauf ohne Tiefenführung; mit Führung sind es 0,0820.");
}

// =============================================================================
// VIII · Warum geprüft werden muss
// =============================================================================
{
  const s = neu();
  satz(s, "Gemessen wird über dem Bauwerk allein — sonst trägt der Boden die Zahl.");
  zweiBilder(s, "maske_soll.png", "maske_nur.png",
    "die ganze Szene: 6348 Punkte Geometrie, davon 4836 Boden",
    "nur das Bauwerk: 1512 Punkte");
  marke(s, "Beweis 15");
  s.addNotes("Der Beleg: Ein Bild, in dem das Bauwerk in der Tiefe gespiegelt ist und der Boden "
    + "stimmt, erreicht über das ganze Bild 0,962 — über der Bauwerksmaske −1,000.");
}

{
  const s = neu();
  satz(s, "Eine erfundene Kubatur besteht die Tiefenprüfung mit 0,966 — und fällt an der Silhouette durch.");
  einBild(s, "qa_luege.png", { unten: "Soll, Ist und Überdeckung: Überlappung 0,101, Gesamturteil 0,312 — durchgefallen" });
  marke(s, "Beweis 04");
  s.addNotes("Deshalb steht im Urteil ein Produkt aus zwei Massen und nicht eines allein: "
    + "Tiefenordnung fängt die eine Art zu lügen, Silhouettenüberlappung die andere.");
}

{
  const s = neu();
  satz(s, "Aber dieselben zwölf Bilder bestehen die Schwelle auch gegen die Karte eines völlig anderen Gebäudes.", ROT);
  einBild(s, "vertausch.png", { unten: "blau gegen die eigene Vorlage, orange gegen die falsche — alle 24 über der Schwelle" });
  marke(s, "auf-20260909-92, Vertauschprobe");
  s.addNotes("Ein fünfgeschossiger Bau gegen die Tiefenkarte einer 8 × 5 × 3 m grossen "
    + "Schachtel und umgekehrt. Diese Probe war nicht bestellt — die HomeStation hat sie "
    + "gefahren, weil eine Probe, die nur bestätigen kann, keine ist.");
}

{
  const s = neu();
  satz(s, "Und wenn die Führung fast weg ist, bestehen elf von zwölf immer noch. Die Prüfung ist damit zu grob.", ROT);
  einBild(s, "staerke.png", { unten: "Übereinstimmung über dem Bauwerk bei Führungsstärke 1,00 · 0,75 · 0,30" });
  marke(s, "auf-20260909-92, Stärkeprobe");
  s.addNotes("Ganz rechts liegt die Übereinstimmung bei null: Das Bild zeigt eine "
    + "mehrgeschossige Lochfassade, wo das Modell einen freistehenden Quader hat. Das Tor ist "
    + "nicht blind — es fällt viermal durch und bei jeder geometriefreien Kontrolle. Es ist zu "
    + "grob, um zwei plausible Architekturbilder zu unterscheiden.");
}

// =============================================================================
// IX · Schluss
// =============================================================================
{
  const s = neu();
  satz(s, "Was heute ohne Zutun läuft — vom IFC-Modell bis zum geprüften Bild.");
  // VIER FELDER GLEICHER GROESSE, jedes Bild darin eingepasst. Sechs Bilder mit sechs
  // Seitenverhaeltnissen nebeneinander ergeben sonst eine ausgefranste Reihe.
  const reihe = ["kameras.png", "shift.png", "raum_plan.png", "multipass.png"];
  const unter = ["Standpunkte und Rahmung", "Shift statt Kippen", "Innenraum", "Vier Pässe je Lauf"];
  const luft = 0.35;
  const feldB = (SPALTE - 3 * luft) / 4;
  const feldH = 2.3;
  const oben = 2.4;
  reihe.forEach((d, i) => {
    const v = seiten(d);
    let bb = feldB, hh = feldB / v;
    if (hh > feldH) { hh = feldH; bb = feldH * v; }
    const feld = RAND + i * (feldB + luft);
    s.addImage({ path: B + d, x: feld + (feldB - bb) / 2, y: oben + (feldH - hh) / 2, w: bb, h: hh });
    s.addText(unter[i], {
      x: feld, y: oben + feldH + 0.16, w: feldB, h: 0.5, isTextBox: true, margin: 0,
      align: "center", fontFace: SANS, fontSize: 11, color: MATT, lineSpacing: 14,
    });
  });
  s.addText("30 Beweisläufe, 212 Bilder — jeder Dateiname trägt die Zahl, unter der er entstanden ist.", {
    x: RAND, y: 5.75, w: SPALTE, h: 0.5, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 15, color: TINTE,
  });
  marke(s, "");
  s.addNotes("Die Reihe ist seriell gefahren, jedes Bild aus einem einzigen sauberen Lauf. "
    + "Kein Bild ist gemalt: Jedes Rechteck ist die Hüllbox eines echten Knotens, jede Farbe "
    + "ein echtes Urteil derselben Funktion.");
}

{
  const s = neu();
  aussage(s, "Was als Nächstes kommt.",
    "Erstens: eine kalibrierte Schwelle für die Übereinstimmung über dem Bauwerk — sie aus "
    + "diesen zwölf Läufen abzulesen wäre Kalibrierung am eigenen Ergebnis.\n"
    + "Zweitens: zwei Riegel mit entgegengesetztem Fehler zu einem Urteil zusammenführen.\n"
    + "Drittens: der Paartest trennt unter dem echten Schätzer frontal nicht mehr.");
  marke(s, "");
  s.addNotes("Der Satz, mit dem ich schliessen will: Jede Erfolgsmeldung muss an etwas hängen, "
    + "das vom Erzähler unabhängig ist. Das ist der Grund, warum es diesen Beweisgang gibt.");
}

await pres.writeFile({ fileName: "beweisgang-kosmovis.pptx" });
console.log(`geschrieben: beweisgang-kosmovis.pptx (${nr} Folien)`);
