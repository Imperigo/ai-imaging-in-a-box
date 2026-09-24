import type { Mm, Pt } from './units';
// NUR EIN TYP, absichtlich: `import type` wird beim Uebersetzen restlos
// entfernt und erzeugt darum KEINEN Ringschluss, obwohl `derive/begruenung`
// seinerseits aus dieser Datei liest.
//
// Warum die Liste nicht hierher wandert, wo sie fachlich hingehoerte: sie
// steht unter einer Wache, die `derive/` von zitierten CSS-Farbnamen
// freihaelt — «orangerot» heisst so, weil «orange» dort anschlug. Die Liste
// nach `model/` zu verschieben, haette diese Wache lautlos umgangen. Eine
// Wache, der man beim Anschlagen ausweicht, misst beim naechsten Mal nichts.
import type { BluetenArt } from '../derive/begruenung';

/**
 * BIM-Entities — flache, JSON-serialisierbare Records. Referenzen sind nur IDs
 * (kein Objektgraph), damit der Store 1:1 auf Yjs-Maps und SQLite-Zeilen passt.
 * Z-Logik ist geschossrelativ (ArchiCAD-Semantik): Elemente wohnen in ihrem
 * Geschoss; verschiebt sich das Geschoss, wandern sie mit.
 */

export interface EntityMeta {
  name?: string;
  layer?: string;
  /** Renovationsstatus für Umbau-Projekte (ArchiCAD-Essenz #9). */
  renovation?: 'bestand' | 'abbruch' | 'neu';
  locked?: boolean;
  /**
   * V4 «Anhang-Kanal für dichte Geometrie» — dieses EINZELNE Bauteil ist
   * dichte, schmückende Geometrie: es gehört ins BILD (3D-Viewport, glTF-
   * Ausfuhr), aber NICHT in `deriveAll` und damit nicht in Schnitt
   * (`derive/section.ts`), Axonometrie (`derive/axo.ts`) und Auto-Kamera
   * (`derive/kamera.ts` `sceneBoundsMm`). Voller Mechanismus samt Begründung:
   * `derive/scene.ts` bei `istNurBild` / `deriveAllMitBilddetails`.
   *
   * DER ANLASS, an dem es gemessen ist: eine Brettstapeldecke aus 1642
   * einzelnen Lattenkörpern. Die Decke selbst steht bereits als `slab` im
   * Modell — sie wird geschnitten, bemasst und ausgemessen. Die 1642 Latten
   * sind die OBERFLÄCHE derselben Decke: im Bild unverzichtbar, im Schnitt
   * 1642 zusätzliche Schnittkörper und in der Auto-Kamera 1642 × 8 Vertices,
   * die die Hüllbox und damit still den Kamerastandpunkt verschieben.
   *
   * WARUM EIN MERKMAL AM ENTITY und nicht eine eigene Bauteilart oder ein
   * Sammelbauteil:
   *
   * (a) NICHT «Art `mass` pauschal ausschliessen». Ein Massenkörper ist
   *     legitime Architektur (ein Gebäudevolumen aus der Volumenstudie,
   *     `design.volumenErstellen`) und gehört in Schnitt und Kamera —
   *     `test/fixtures.ts` `testhausMitQuertrakt` baut den Quertrakt genau
   *     so. Eine ganze Art zu verbannen erschlüge diesen Fall mit. Gebraucht
   *     wird die Unterscheidung ZWISCHEN zwei Volumen, nicht zwischen zwei
   *     Arten.
   *
   * (b) NICHT eine eigene Bauteilart. Die Latten sind geometrisch genau das,
   *     was `deriveMass`/`deriveBeam`/`deriveFreeMesh` schon können. Eine
   *     neue Art bräuchte eine eigene Ableitung (Verdopplung), einen eigenen
   *     Zweig in `deriveEntity`, im Plan, in den Mengen, im IFC-Ausgang — und
   *     sie könnte immer nur EINE Bauform tragen. Das Merkmal trägt jede:
   *     Latte (`beam`), Lamelle (`mass`), Zierteil (`freemesh`).
   *
   * (c) NICHT ein Sammelbauteil. Das gäbe es schon — `FreeMesh` —, aber sein
   *     hartes Budget (`FREEMESH_MAX_VERTICES` 4096) trägt die 1642 Latten
   *     nicht: als Quader sind das 13'136 Vertices. Das Budget ist bewusst
   *     gesetzt (Entwurfsgeometrie, kein Scan-Container) und wird hier nicht
   *     aufgeweicht.
   *
   * `meta` ist im Haus der eingeführte Ort für genau solche Marken am
   * einzelnen Bauteil: `meta.layer` steuert NUR den DXF-Ausgang
   * (`dxf/export.ts`), `meta.locked` NUR den Interaktionspfad — beide ohne
   * Geometriewirkung, beide je Bauteil, beide über einen kleinen Command
   * gesetzt (`design.ebeneSetzen`, `design.sperren`). `nurBild` reiht sich
   * dort ein; gesetzt wird es mit `design.merkmalSetzen` (Merkmal `nurBild`)
 * — bis V9 hatte es einen eigenen Befehl, `design.nurBildSetzen`; der ist in
 * jenem aufgegangen und hat dabei die Werkzeug-Token freigemacht, aus denen
 * die sieben Merkmale unten bezahlt sind (Rechnung dort).
   *
   * EHRLICHE GRENZE, damit sie niemand für erledigt hält: die Marke wirkt
   * heute NUR im Derive-3D-Kanal (`derive/scene.ts`). Grundriss
   * (`derive/plan.ts` zeichnet `mass`-Umrisse), Mengen (`derive/mengen.ts`)
   * und der IFC-Ausgang lesen die Entities direkt und sehen ein markiertes
   * Bauteil weiterhin. Für die Brettstapeldecke heisst das: Schnitt, Axo und
   * Kamera sind sauber, der Grundriss zeigt die Latten noch.
   */
  nurBild?: boolean;
  /**
   * V5 «eigenes Aussehen je Bauteil» — die PBR-Werte DIESES einen Bauteils,
   * die den Materialschlüssel überschreiben. Fehlt das Feld, gilt wie bisher
   * der Schlüssel (`derive/gltf.ts` `MATERIAL_AUSSEHEN`) — ein Dokument ohne
   * dieses Feld ergibt eine byte-gleiche Ausfuhr wie vorher.
   *
   * DER GEMESSENE ANLASS (Renderprojekt 10.09.2026,
   * `docs/RENDERPROJEKT-2026-09-10/30-PLAN-NACHBAU.md` §4): Dort trägt JEDE
   * Oberfläche eigene Werte — die Dreischichtplatte einen Grundton
   * (0.304, 0.478, 0.745) bei Rauheit 0.54, der weisse Küchenlack
   * (0.780, 0.778, 0.762) bei Rauheit 0.16. `derive/gltf.ts` kannte dafür
   * 19 feste Schlüssel und sonst nichts, und `entities.ts` trug kein Feld
   * für Farbe, Rauheit oder Metallgrad. Folge, dort wörtlich gemessen: eine
   * fehlerfrei portierte Lattung käme als EINFARBIGES Holz im Bild an, weil
   * alle Holzbauteile denselben Schlüssel und damit denselben Farbwert
   * tragen.
   *
   * WARUM DIESELBE BAUFORM WIE `nurBild` (Marke an `meta`, je einzelnes
   * Bauteil, an GENAU EINER Stelle gelesen): Es ist dieselbe Art Angabe —
   * ohne Geometriewirkung, ohne Mengenwirkung, je Bauteil, und die
   * bestehende Nachbarschaft (`layer` steuert nur den DXF-Ausgang, `locked`
   * nur den Interaktionspfad) ist genau dafür da. Eine eigene Bauteilart
   * oder ein Feld an jeder einzelnen Entity-Art wäre Verdopplung ohne
   * Gegenwert: das Aussehen ist für Wand, Decke, Stütze, FreeMesh dasselbe.
   *
   * SEIT V9 GIBT ES EINEN SETZWEG — `design.merkmalSetzen`, Merkmale `farbe`,
   * `rauheit`, `metallgrad`. Was hier vorher stand, war richtig gerechnet und
   * ist eingelöst worden, nicht umgangen: der Engpass war die Werkzeugliste
   * der KI-Lane (`packages/kosmo-ai/test/werkzeug-fenster-luft-wache.test.ts`,
   * am 11.09.2026 bei 31 Token Luft), und die Antwort darauf ist EIN Befehl
   * für acht Merkmale, der einen bestehenden ERSETZT statt hinzuzukommen.
   * Eine Zahl von damals war dabei zu günstig geschätzt: ein eigener Command
   * kostet nicht «rund 175» Token, sondern am echten Schätzer nachgezählt
   * 221 (`design.nurBildSetzen`) bei 315 im Durchschnitt. Die volle Rechnung
   * steht bei `design.merkmalSetzen` (`commands/design.ts`).
   *
   * WAS WEITERHIN GILT: Die Werkzeugluft bleibt knapp (nach dem Bau 7011
   * gegen die Schwelle 7000). Das nächste Feld, das einen Setzweg braucht,
   * bekommt ihn als weiteres MERKMAL dieses einen Befehls — ein neunter
   * Enum-Wert kostet einstellige Token —, nicht als eigener Command.
   *
   * ALLE DREI WERTE SIND EINZELN OPTIONAL: was fehlt, kommt weiter vom
   * Schlüssel. Ein Bauteil kann also nur die Rauheit ändern und die Farbe
   * seines Materials behalten.
   */
  aussehen?: BauteilAussehen;
  /**
   * V8 «Begruenung» — DIESES Bauteil traegt Bepflanzung: Triebe, Blaetter,
   * Gras und Blueten wachsen aus seiner Oberkante. Voller Mechanismus samt
   * Begruendung: `derive/begruenung.ts`.
   *
   * DER ANLASS, und er ist nicht ausgedacht: das Renderprojekt vom 10.09.2026
   * hat ein bepflanztes Hochbeet vor einer Loggia gebaut, und der Owner hat
   * am fertigen Bild SIEBEN Mal nachkorrigiert. Fuenf dieser sieben Zurufe
   * betrafen dieselbe Groesse — die HOEHE («etwas weniger hoch», «die blauen
   * blumen sind zu hoch», «wieder etwas hoeher», «begruenung hoeher!»). Eine
   * Groesse, an der fuenfmal nachgestellt wird, darf keine Zahl im Quelltext
   * sein; sie gehoert ans Bauteil.
   *
   * WARUM `meta` UND NICHT EIN FELD AM ENTITY — die Frage ist bei
   * `Slab.spannrichtungGrad` schon einmal gestellt und dort GEGEN `meta`
   * entschieden worden. Hier faellt sie umgekehrt aus, und zwar aus genau
   * denselben drei Gruenden, nur mit anderem Vorzeichen:
   *
   * (a) Die Spannrichtung verschiebt PLANGEOMETRIE (welcher Balken im
   *     Schnitt quer getroffen wird). Diese Angabe verschiebt keine: die
   *     Begruenung erreicht nur den Anhang-Kanal, nie `deriveAll` — also
   *     weder Schnitt noch Axonometrie noch Kamera-Huellbox, und weder
   *     Bemassung noch Mengen. Das ist wortgleich die Selbstbegruendung von
   *     `nurBild` und `aussehen`: «ohne Geometriewirkung, ohne
   *     Mengenwirkung».
   * (b) Die Spannrichtung tragen die Nachbarbauteile laengst am Entity
   *     (Wandachse, Firstrichtung). Eine Wuchshoehe tragen sie nirgends.
   * (c) `meta` ist der Ort fuer Marken mit GENAU EINER Lesestelle. Die hier
   *     hat genau eine: `derive/begruenung.ts`. Die Spannrichtung hat zwei
   *     (Schnitt und Bild) und war darum dort fehl am Platz.
   *
   * GESETZT WIRD ES SEIT V9 mit `design.merkmalSetzen` — drei Merkmale,
   * `bewuchsHoehe`, `bewuchsDichte`, `bluetenAnteil`, je einzeln stellbar.
   * Das ist wichtig fuer die eine Zahl der fuenf Zurufe: «hoeher» bleibt EIN
   * Zug und zieht Dichte und Bluetenanteil nicht mit.
   *
   * DER BEFEHL WEIST ZWEI FAELLE SICHTBAR AB, die diese Ableitung sonst STILL
   * verschluckt: `hoeheMm <= 0` (dann waechst nichts, ohne dass es jemand
   * sagt) und `dichte <= 0` (dann faellt `begruenungsFlaechen` auf 1 zurueck
   * — der Nutzer bekommt etwas anderes als bestellt). Und: Dichte oder
   * Bluetenanteil OHNE gesetzte Hoehe werden abgelehnt, weil die Hoehe hier
   * Pflicht und zugleich der Ausloeser ist.
   */
  begruenung?: BegruenungVorgabe;
}

/**
 * Was auf diesem Bauteil waechst (`EntityMeta.begruenung`).
 *
 * ALLE ZAHLEN SIND VORGABEN, KEINE ERGEBNISSE: die Ableitung streut um sie
 * herum (deterministisch, s. `derive/begruenung.ts`). `hoeheMm` ist darum
 * die Hoehe der HOECHSTEN Triebe, nicht die jedes einzelnen.
 */
export interface BegruenungVorgabe {
  /**
   * Wuchshoehe ueber Oberkante Bauteil, in mm — **die eine Zahl der fuenf
   * Zurufe.** Gras und Blueten leiten ihre Hoehe daraus ab (Verhaeltnisse in
   * `derive/begruenung.ts`), es bleibt also bei EINEM Regler fuer «hoeher»
   * und «niedriger».
   *
   * Fehlt der Wert nicht — er ist Pflicht. Das Feld ist zugleich der
   * AUSLOESER: wer `begruenung` setzt, will Bepflanzung, und dann muss
   * dastehen, wie hoch. Eine stille Vorgabe waere genau die Zahl im
   * Quelltext, gegen die dieses Feld gebaut ist.
   */
  hoeheMm: Mm;
  /**
   * Dichtefaktor, 1 = Regelfall. Kleiner = luftiger, groesser = dichter.
   * Die Regelwerte je Quadratmeter stehen in `derive/begruenung.ts` und sind
   * an der Vorlage gemessen; dieser Faktor skaliert sie gemeinsam.
   *
   * Fehlt = 1. **Ein Deckel bleibt darueber**: die Ableitung begrenzt die
   * Gesamtzahl der Ecken je Bauteil und senkt die Dichte, wenn ein sehr
   * grosses Bauteil sie sprengen wuerde (s. dort, mit der gemessenen Zahl).
   */
  dichte?: number;
  /**
   * Anteil bluehender Stauden an der Unterpflanzung, 0..1. Fehlt = Regelwert.
   *
   * Eigener Regler, weil der Owner ihn getrennt bedient hat: «bring noch
   * etwas farbe mit blumen hinein», «noch diverser mit mehr farbigen blumen»
   * und, am unbearbeiteten Bild, «und im bild sehe ich nach wie vor die
   * farbigen blumen nicht».
   */
  bluetenAnteil?: number;
  /**
   * WELCHE Farben bluehen — eine Art oder mehrere. Fehlt = alle sechs
   * gemischt, wie bisher.
   *
   * WARUM DAS EIN EIGENES FELD IST und nicht mit `bluetenAnteil` zusammen
   * faellt: der Anteil stellt die MENGE der Bluehenden, dieses Feld ihre
   * FARBE. Der Owner hat beides getrennt gerufen — «bring noch etwas farbe
   * mit blumen hinein» meinte die Menge, «farbige blumen sehe ich nach wie
   * vor nicht» (VIERMAL, einer der am haeufigsten wiederholten Zurufe des
   * ganzen Bildtags) meinte die Farbe. Ein unabhaengiger Pruefer hat
   * Abnahmezeile 29 ausdruecklich NICHT als bedienbar gezaehlt, solange es
   * nur den Mengenregler gab.
   *
   * 17.09.2026 nachgetragen: das Feld wurde vom Befehl bereits geschrieben,
   * stand aber nicht im Typ — der Typ verschwieg also, was das Objekt
   * wirklich tragen kann.
   */
  bluetenFarbe?: BluetenArt | readonly BluetenArt[];
}

/**
 * Eigenes PBR-Aussehen eines einzelnen Bauteils (`EntityMeta.aussehen`).
 *
 * EINHEITEN — hier steht die Falle, nicht in der Bequemlichkeit: `rgba` ist
 * der glTF-`baseColorFactor`, also LINEARE Werte 0..1, KEIN sRGB-Hexwert.
 * Die Zahlen aus dem Renderprojekt (0.304, 0.478, 0.745) sind genau solche
 * linearen Faktoren und wandern damit unverändert hier hinein. Ein
 * Hex-Feld hätte sie auf 8 Bit gestaucht UND die Farbräume vermischt — das
 * ist der Grund, warum dieses Feld keine Zeichenkette ist.
 *
 * `rgba[3]` (Alpha) wirkt wie beim Schlüssel: < 1 erzwingt in der Ausfuhr
 * `alphaMode: 'BLEND'` (`derive/gltf.ts`). Ein deckendes Bauteil kann so
 * durchsichtig gemacht werden, ohne dass es «glas» heissen muss.
 */
export interface BauteilAussehen {
  /** baseColorFactor — linear, 0..1, vier Werte (r, g, b, a). */
  rgba?: [number, number, number, number];
  /** roughnessFactor — 0 spiegelglatt, 1 völlig matt. */
  rauheit?: number;
  /** metallicFactor — 0 Nichtleiter, 1 Metall. */
  metallgrad?: number;
  /**
   * A9 / Welle 3, Abnahmezeile 33 — DAS NEUNTE BILDMERKMAL: wie viel Licht
   * dieses eine Bauteil DURCHLAESST, 0..1.
   *
   * DIE ZWEI ZURUFE, woertlich: «vorhang mehr transparent, gib ihm ein
   * weinrote farbe, ist ein textil, mach das sichtbar taktiler bitte» und
   * «dann die begruenung ist besser, mach sie aber etwas transluszenter».
   * Beide Male ist dieselbe Groesse gemeint, und beide Male gab es sie nur
   * als Zahl im Quelltext: `MATERIAL_AUSSEHEN[...].durchlass` (`derive/
   * gltf.ts`) steht je SCHLUESSEL, nicht je Bauteil — jedes Blatt jeder
   * Pflanze im ganzen Projekt trug denselben Wert, und kein Befehl konnte
   * ihn stellen.
   *
   * WAS ES IN DER AUSFUHR WIRD: der `transmissionFactor` von
   * `KHR_materials_transmission`. Es UEBERSCHREIBT den Wert des Schluessels
   * (fehlt es, gilt wie bisher der Schluessel) und ist damit die erste
   * Angabe dieser Art, die aus `meta.aussehen` kommt — bis hierher hielt
   * `materialFor` woertlich fest: «Der Durchlass kommt AUSSCHLIESSLICH vom
   * Schluessel». Dieser Satz ist mit diesem Feld berichtigt; woran man es
   * merken wuerde, steht dort.
   *
   * ALPHA UND DURCHLASS SIND NICHT DASSELBE (lange Begruendung an
   * `MaterialAussehen.durchlass`): Alpha mischt die Flaeche mit dem, was
   * dahinter liegt, Durchlass sagt «dieser Koerper LEITET Licht». Ein
   * Lampenschirm, ein Blatt und ein Vorhang leiten; eine Absperrfolie
   * mischt. Wer Alpha will, setzt den vierten Wert von `farbe`.
   *
   * DIE GRENZE, DIE ES MIT `farbe`/`rauheit`/`metallgrad` TEILT und die
   * ausgesprochen gehoert: es gilt fuer das GANZE Bauteil. An einem Fenster
   * toent es Scheibe UND Rahmen, an einer begruenten Decke den Deckenkoerper
   * mit. Die Leuchte umgeht das nicht durch eine Ausnahme, sondern durch die
   * Bauform: ihr Schirm hat einen EIGENEN Materialschluessel, der seinen
   * Durchlass schon mitbringt (`Leuchte.schirmMaterial`).
   */
  transluzenz?: number;

  /**
   * ═══════════════════════════════════════════════════════════════════════
   *  DER ANSTRICH — Abnahmezeile 35
   * ═══════════════════════════════════════════════════════════════════════
   *
   * Der Zuruf, woertlich: «die wand die aktuell fichte holz ist, ist gut aber
   * da bitte einen layer drauflegen fuer ‹weiss gestrichen› also das holz
   * wird weiss gestrichen».
   *
   * WARUM `farbe` DAS NICHT SCHON KANN — und das ist der ganze Punkt dieser
   * Zeile: `farbe` ERSETZT die Farbe des Materials. Damit ist die Wand weiss,
   * und niemand weiss mehr, dass darunter Fichte liegt. Der Owner hat aber
   * ausdruecklich «einen LAYER DRAUFLEGEN» gesagt und im selben Satz «die wand
   * ist gut» — das Material soll bleiben, nur gestrichen sein.
   *
   * DER UNTERSCHIED IST NICHT KOSMETIK, er hat drei messbare Folgen:
   *   1. Der Materialschluessel bleibt Fichte — Aufbau, U-Wert, Schraffur im
   *      Plan und die Mengen rechnen unveraendert weiter.
   *   2. Der Bildkanal erfaehrt BEIDES. `derive/renderprompt.ts` macht aus
   *      einer Holz-Aussenschicht «Holzfassade (vertikale Lattung)» — das ist
   *      die STRUKTUR, von der die Abnahmezeile spricht. Ein Anstrich haengt
   *      «, weiss gestrichen» daran, statt die Phrase zu ersetzen. Genau so
   *      geht die Maserung nicht verloren.
   *   3. `deckung` unter 1 laesst den Untergrund durchscheinen — eine Lasur.
   *      Mit `farbe` gibt es diesen Zwischenzustand gar nicht.
   *
   * GEMISCHT WIRD LINEAR, und das ist kein Zufall: dieses Feld traegt wie
   * `rgba` einen LINEAREN Wert (glTF `baseColorFactor`). Eine Mischung im
   * Bildschirmraum waere bei halber Deckung sichtbar zu hell — derselbe
   * Fehler, den A20 an 27 Katalogeintraegen behoben hat.
   *
   * WAS ER NICHT IST: eine zweite Materialschicht mit eigener Dicke. Der
   * Aufbau (`Assembly.layers`) bleibt unberuehrt; ein Anstrich hat in diesem
   * Modell keine Staerke und geht in keine Mengenrechnung ein. Wer eine
   * Beschichtung MIT Dicke braucht, braucht eine Aufbauschicht.
   */
  anstrich?: Anstrich;

  /**
   * ═══════════════════════════════════════════════════════════════════════
   *  DIE KOERNUNG — Abnahmezeile 36, viermal zugerufen
   * ═══════════════════════════════════════════════════════════════════════
   *
   * Woertlich, in dieser Reihenfolge: «der boden soll ein geschliffener
   * unterlagsbodenbelag sein» · «dann bodenbelag mit ganz leichter
   * Unterlagsboden textur ergaenzen damit man minimale kiessteine geschnitten
   * sieht» · «der boden hat die leichte steinkoernung nicht. diese koernung
   * in beigetoenen, ein terrazzobelag aber in guenstig weil es ein
   * geschliffener unterlagsboden ist also nicht zu fancy» · «und noch etwas
   * mehr groessere koernung zeigen im bodenbelag».
   *
   * VIER ZURUFE, DREI GROESSEN. Liest man sie der Reihe nach, stellt der Owner
   * nacheinander genau drei Dinge: wie GROSS das Korn ist («minimale
   * kiessteine» → «etwas groessere koernung»), wie VIEL davon da ist («ganz
   * leichte … textur», «nicht zu fancy») und welchen TON es hat («in
   * beigetoenen»). Darum drei Felder und nicht eines.
   *
   * KORNGROESSE IN MILLIMETERN, nicht in Bildpunkten — und das ist der
   * eigentliche Grund, warum dieses Feld im Kern steht und nicht in der
   * Oberflaeche: ein Architekt sagt «etwas groesser» und meint 2 mm statt
   * 1 mm, nicht «14 Bildpunkte statt 7». Die Umrechnung in Bildpunkte gehoert
   * dorthin, wo die Kachel gezeichnet wird, und sie hat ein festes Mass
   * (1 Kachel = 1 m).
   *
   * WAS DIE AUSFUHR DAVON TRAEGT, ehrlich benannt: KEINE Textur. Der Kopf von
   * `derive/gltf.ts` haelt gemessen fest, warum dort keine Texturen stehen.
   * Was die Ausfuhr SEHR WOHL traegt, ist die gemittelte Farbe: bei 30 %
   * Korndichte in Beige wird die Flaeche messbar beiger. Das ist keine
   * Notloesung, sondern genau das, was ein Auge aus zwei Metern Abstand
   * sieht — und es ist der Weg, auf dem die Koernung im gerechneten Bild
   * ankommt. Die KOERNIGKEIT selbst geht ueber den Bildkanal
   * (`derive/renderprompt.ts`), mit ihren echten Zahlen.
   */
  koernung?: Koernung;

  /**
   * ═══════════════════════════════════════════════════════════════════════
   *  MASERUNGSKONTRAST UND FUGENHELLIGKEIT — Abnahmezeile 37, 2x zugerufen
   * ═══════════════════════════════════════════════════════════════════════
   *
   * «zudem die decke etwas kontrast raus bei den aesten im holz selbst» und
   * «die stossfugen in der deckentextur farblich sehr aufhellen dass man sie
   * fast nicht mehr wahrnimmt».
   *
   * ZWEI ZURUFE, ZWEI ZAHLEN — und sie sind ausdruecklich NICHT dasselbe.
   * Der erste betrifft, was IM Brett zu sehen ist (Adern, Astbilder, der
   * Helligkeitsunterschied von Brett zu Brett). Der zweite betrifft, was
   * ZWISCHEN den Brettern zu sehen ist (die Stossfuge). Ein einziger Regler
   * «Maserung» haette den zweiten Zuruf verschluckt — und der Owner hat ihn
   * eigens nachgeschoben, nachdem der erste schon umgesetzt war.
   *
   * KEIN ANLEGE-SCHRITT, anders als bei Anstrich und Koernung: beide Groessen
   * haben einen natuerlichen Vorgabewert (voller Kontrast, dunkle Fuge) und
   * daempfen ihn nur. Wer nichts setzt, bekommt genau das Holz von heute —
   * und darum bleibt jedes bestehende Dokument Byte fuer Byte gleich.
   *
   * WAS «FARBLICH AUFHELLEN» GENAU HEISST, und die Unterscheidung ist die
   * ganze Pointe des zweiten Zurufs: Die Fuge verschwindet aus der FARBE, aber
   * nicht aus dem RELIEF. Die Bretter stossen weiterhin aneinander, man sieht
   * es im Streiflicht — nur die dunkle Linie ist weg. Dieselbe Trennung wie
   * beim deckenden Anstrich, der die Maserung verbirgt und die Oberflaeche
   * fuehlbar laesst.
   *
   * GILT NUR FUER HOLZ. Ein Betonbauteil hat keine Maserung; die Werte lassen
   * sich dort setzen und bewirken nichts. Die Oberflaeche zeigt die beiden
   * Regler darum nur an Holzbauteilen — und sagt es, statt sie stumm
   * anzubieten.
   */
  /** 0..1 — wie stark sich Adern und Brettunterschiede zeigen. 1 = wie bisher. */
  maserungKontrast?: number;
  /** 0..1 — wie hell die Stossfuge wird. 0 = wie bisher (dunkel), 1 = unsichtbar. */
  fugenHelligkeit?: number;
}

/** Die Koernung eines mineralischen Belags (Abnahmezeile 36, lange Begruendung
 *  an `BauteilAussehen.koernung`). */
export interface Koernung {
  /** Korndurchmesser in MILLIMETERN — so, wie ein Architekt es sagt. */
  groesse_mm: number;
  /** Flaechenanteil der Koerner, 0..1 — «ganz leicht» bis «dicht». */
  dichte: number;
  /** Farbton der Koerner — LINEAR 0..1, vier Werte, wie `BauteilAussehen.rgba`. */
  ton: [number, number, number, number];
}

/** Ein Anstrich liegt AUF dem Material, er ersetzt es nicht (Abnahmezeile 35,
 *  lange Begruendung an `BauteilAussehen.anstrich`). */
export interface Anstrich {
  /** Farbton des Anstrichs — LINEAR 0..1, vier Werte, wie `BauteilAussehen.rgba`. */
  rgba: [number, number, number, number];
  /** Deckung 0..1 — 1 deckend, darunter scheint der Untergrund durch (Lasur). */
  deckung: number;
}

interface Base {
  readonly id: string;
  meta?: EntityMeta;
}

/** Geschoss — die fundamentale Z-Ordnung. */
export interface Storey extends Base {
  kind: 'storey';
  /** OK fertig Boden über Projektnull. */
  elevation: Mm;
  /** Geschosshöhe OK–OK. */
  height: Mm;
  /**
   * Schnitthöhe für Wandöffnungen über OK Boden: bestimmt ausschliesslich,
   * welche Fenster/Türen im Grundriss als aufgeschnitten gelten
   * (`derive/plan.ts`, Filter `z0 < cutHeight && z1 > cutHeight`).
   * **NICHT** dieselbe Grösse wie `FREEMESH_SCHNITTHOEHE` in
   * `derive/plan.ts` — jene schneidet ausschliesslich FreeMesh-Körper, nie
   * eine Wandöffnung, und steht in keiner gemeinsamen Formel mit diesem
   * Feld (AUFTRAG-B38 §1, Owner-Entscheid E66,
   * `docs/V009-RUECKSPRUNG-ENTSCHEIDE.md`).
   *
   * **Kein Normwert — eine Hausfestlegung.** SIA 400 C.3.1.1 nennt keine
   * Zahl, sondern eine REGEL: die Schnitthöhe des Grundrisses ist so zu
   * wählen, dass alle Tür- und Fensteröffnungen geschnitten werden. 1100 mm
   * (Default in `commands/design.ts`, Command `design.geschossErstellen`)
   * ist der hier gewählte Hausstandard, kein ArchiCAD-Normwert.
   *
   * **Nicht gebaut (bewusster Verzicht, Owner-Entscheid E66):**
   * VORHABEN-SCHNITTHOEHE-AUS-OEFFNUNGEN — die normnächste Lösung wäre,
   * diese Höhe je Geschoss aus den tatsächlichen Wandöffnungen abzuleiten
   * (so, dass wirklich alle geschnitten werden), statt eines festen
   * Defaults. Der Verzicht ist ausdrücklich, nicht vergessen.
   */
  cutHeight: Mm;
  /** Sortierindex: 0 = EG, negativ = UG. */
  index: number;
  name: string;
}

/** Rasterachse (Stützenraster, z.B. A/B/C × 1/2/3). */
export interface GridAxis extends Base {
  kind: 'grid';
  storeyId: string;
  label: string;
  a: Pt;
  b: Pt;
  /** haupt = Tragachse mit Achskopf; wohn = feine Wohnraster-Zwischenachse. */
  typ?: 'haupt' | 'wohn';
}

/**
 * Stütze (RE-ARCHICAD A3): Rechteck- oder Rundprofil, geschosshoch —
 * Skelettbau wird modellierbar. b = Breite bzw. Durchmesser, t = Tiefe
 * (nur rechteck, fehlt = quadratisch), rotationGrad dreht ums Zentrum.
 */
export interface Column extends Base {
  kind: 'column';
  storeyId: string;
  at: Pt;
  profil: 'rechteck' | 'rund';
  b: Mm;
  t?: Mm;
  material: string;
  rotationGrad?: number;
  /**
   * Profil-Referenz (v0.9.2 P-P1, `docs/V092-SPEZ.md` §P-P1) — additiv,
   * verweist auf ein `Profil` aus dem Typenkatalog (`profilOutline()` unten).
   * GOLDEN-GUARD: fehlt das Feld, bleibt die Ableitung (`columnOutline`,
   * `derive/scene.ts` `deriveColumn`) byte-identisch zum heutigen `profil`/
   * `b`/`t`-Eigenbau — `profilId` überschreibt diesen NUR, wenn gesetzt.
   */
  profilId?: string;
}

/** Unterzug (RE-ARCHICAD A3): Balken unter der Decke, OK = OK Geschoss. */
export interface Beam extends Base {
  kind: 'beam';
  storeyId: string;
  a: Pt;
  b: Pt;
  breite: Mm;
  hoehe: Mm;
  material: string;
  /** Profil-Referenz (v0.9.2 P-P1) — s. `Column.profilId`-Kommentar; bei
   * gesetzter Id liest `derive/scene.ts` `deriveBeam` den echten
   * Profil-Querschnitt (auch Stahl-I/-U) statt des Rechteck-Eigenbaus aus
   * `breite`/`hoehe`. Golden-Guard identisch: fehlt `profilId`, byte-gleiches
   * Bestandsverhalten. */
  profilId?: string;
  /**
   * **A4/15 (Abnahmezeile 15, Renderprojekt) — an WELCHE Decke dieser
   * Unterzug bündig anschliesst.**
   *
   * DER ANLASS, wörtlich: «und der traeger ist buendig mit holzuntersicht,
   * man sieht nicht an den rand des deckenholzes ran». Bis hierher setzte
   * `deriveBeam` (`derive/scene.ts`) die Oberkante HART auf OK Geschoss —
   * also auf die OBERkante der Decke. Ein 400er Balken unter einer 280er
   * Decke steckte damit 280 mm in ihr drin: sichtbar blieben 120 mm, und
   * die Deckenstirn stand daneben frei. Genau das hat der Owner am Bild
   * gesehen.
   *
   * FEHLT DAS FELD, ÄNDERT SICH NICHTS. Jeder bestehende Unterzug und jeder
   * aus `design.unterzugZeichnen` behält OK = OK Geschoss, Zahl für Zahl
   * (Golden-Guard, dasselbe Muster wie `profilId` darüber).
   *
   * WARUM EINE REFERENZ UND KEIN AUFZÄHLWERT wie `'deckenuntersicht'`: die
   * Ableitung müsste dann selbst herausfinden, WELCHE Decke gemeint ist.
   * Über einem Geschoss können mehrere liegen (Podest, Absatz, zwei
   * Bauteile über zwei Räumen), und eine Regel, die sich für eine
   * entscheidet, rät — bei falscher Wahl hinge der Balken auf der falschen
   * Höhe und sähe trotzdem plausibel aus. Dieselbe Begründung, mit der
   * `deckenachseVon` (`derive/deckenachse.ts`) einen unbrauchbaren Wert
   * lieber offen mit `null` beantwortet, statt still auf die Hausregel
   * zurückzufallen: «ein erratener Wert waere schlimmer als ein offen
   * fehlender».
   *
   * DIE UNTERSICHT IST EINE ZAHL AUS EINER QUELLE. `derive/scene.ts`
   * rechnet sie NICHT zweimal: `deriveSlab` und `deriveBeam` fragen beide
   * `deckenUnterkante()` in derselben Datei. Zwei Rechnungen wären genau
   * die Zwillingsbildung, an der dieses Repo mehrfach verbrannt ist
   * (s. `extrudePrismen` in `derive/mesh.ts`).
   *
   * HÄNGENDE REFERENZ = EHRLICHER RÜCKFALL auf OK Geschoss, kein Wurf
   * mitten in der Ableitung — wortgleich das Verhalten von `profilId`
   * darüber. Geprüft wird beim SETZEN (`design.eigenschaftSetzen`): das
   * Ziel muss eine Decke sein, und ihre Untersicht muss ÜBER dem Boden des
   * Geschosses liegen, in dem der Balken steht.
   */
  deckeId?: string;
}

/**
 * Assoziative Etikette (RE-ARCHICAD A6): liest ihr Bauteil LIVE aus der
 * Parametrik — Aufbau umbenennen ändert alle Etiketten mit. inhalt 'aufbau'
 * beschriftet Aufbau/Querschnitt, 'keynote' verweist auf settings.keynotes
 * (die Legende aufs Blatt macht sheetToSvg).
 */
export interface Etikett extends Base {
  kind: 'etikett';
  storeyId: string;
  targetId: string;
  /** Text-Anker in Welt-mm; der Leader zeigt zum Bauteil. */
  at: Pt;
  inhalt: 'aufbau' | 'keynote';
  /** Keynote-Nummer (nur inhalt 'keynote'), z.B. «K3». */
  keynote?: string;
}

/** Grundriss-Polygon einer Stütze (rund als 16-Eck), CCW = positive Fläche. */
export function columnOutline(c: Column): Pt[] {
  if (c.profil === 'rund') {
    const r = c.b / 2;
    const pts: Pt[] = [];
    for (let i = 0; i < 16; i++) {
      const w = (i / 16) * 2 * Math.PI;
      pts.push({ x: Math.round(c.at.x + r * Math.cos(w)), y: Math.round(c.at.y + r * Math.sin(w)) });
    }
    return pts;
  }
  const hb = c.b / 2;
  const ht = (c.t ?? c.b) / 2;
  const w = ((c.rotationGrad ?? 0) * Math.PI) / 180;
  const cos = Math.cos(w);
  const sin = Math.sin(w);
  return [
    { x: -hb, y: -ht }, { x: hb, y: -ht }, { x: hb, y: ht }, { x: -hb, y: ht },
  ].map((p) => ({
    x: Math.round(c.at.x + p.x * cos - p.y * sin),
    y: Math.round(c.at.y + p.x * sin + p.y * cos),
  }));
}

/**
 * Profil (v0.9.2 P-P1, `docs/V092-SPEZ.md` §P-P1) — wiederverwendbares
 * Stützen-/Unterzugsprofil für den Typenkatalog, PROJEKTGLOBAL wie
 * `Assembly` (kein `storeyId`, ein Katalogeintrag). `form` bestimmt, welche
 * Masse zählen (Rest bleibt `undefined`, s. `profilOutline`):
 * rechteck → b (Breite) × h (Höhe); rund → d (Durchmesser); stahl-i/stahl-u
 * → h (Gesamthöhe), b (Flanschbreite), steg (Stegdicke), flansch
 * (Flanschdicke) — dieselben Feldnamen für beide Stahlformen, weil beide
 * dieselbe Bemassung brauchen (nur die Kontur unterscheidet sich, s.
 * `profilOutline`). Alle Masse in mm, > 0 (Command-Gate in `commands/design.ts`).
 */
export interface Profil extends Base {
  kind: 'profil';
  name: string;
  form: 'rechteck' | 'rund' | 'stahl-i' | 'stahl-u';
  /** rechteck: Breite · stahl-i/-u: Flanschbreite. */
  b?: Mm;
  /** rechteck: Höhe · stahl-i/-u: Gesamthöhe. */
  h?: Mm;
  /** rund: Durchmesser. */
  d?: Mm;
  /** stahl-i/-u: Stegdicke. */
  steg?: Mm;
  /** stahl-i/-u: Flanschdicke. */
  flansch?: Mm;
}

/**
 * Profil-Querschnitt, LOKAL um 0/0 (Muster `columnOutline` oben — rund als
 * 16-Eck, dieselbe Segmentzahl). rechteck/rund sind reine Eigenformen wie
 * bei `columnOutline`; stahl-i liefert ein echtes I-Profil-Polygon (12
 * Punkte), stahl-u ein C-förmiges Kanalprofil (8 Punkte, Steg links, Öffnung
 * nach rechts) — jeweils die einfachste ehrliche Näherung OHNE Walzradien
 * (Ausrundungen sind ein späterer Detailgrad, kein Normreihen-Katalog ist
 * Teil dieses Postens, s. V092-SPEZ Nicht-Ziele). Fehlende Masse zählen als 0
 * (die Commands lehnen das vorher ab, `profilOutline` selbst wirft nie —
 * pure Ableitung, wie `columnOutline`). CCW = positive Fläche.
 */
export function profilOutline(p: Profil): Pt[] {
  const rund = (n: number) => Math.round(n);
  if (p.form === 'rund') {
    const r = (p.d ?? 0) / 2;
    const pts: Pt[] = [];
    for (let i = 0; i < 16; i++) {
      const w = (i / 16) * 2 * Math.PI;
      pts.push({ x: rund(r * Math.cos(w)), y: rund(r * Math.sin(w)) });
    }
    return pts;
  }
  if (p.form === 'stahl-i') {
    const hb = (p.b ?? 0) / 2;
    const hh = (p.h ?? 0) / 2;
    const hw = (p.steg ?? 0) / 2;
    const ft = p.flansch ?? 0;
    return [
      { x: -hb, y: -hh }, { x: hb, y: -hh }, { x: hb, y: -hh + ft }, { x: hw, y: -hh + ft },
      { x: hw, y: hh - ft }, { x: hb, y: hh - ft }, { x: hb, y: hh }, { x: -hb, y: hh },
      { x: -hb, y: hh - ft }, { x: -hw, y: hh - ft }, { x: -hw, y: -hh + ft }, { x: -hb, y: -hh + ft },
    ].map((q) => ({ x: rund(q.x), y: rund(q.y) }));
  }
  if (p.form === 'stahl-u') {
    const hb = (p.b ?? 0) / 2;
    const hh = (p.h ?? 0) / 2;
    const steg = p.steg ?? 0;
    const ft = p.flansch ?? 0;
    return [
      { x: -hb, y: -hh }, { x: hb, y: -hh }, { x: hb, y: -hh + ft }, { x: -hb + steg, y: -hh + ft },
      { x: -hb + steg, y: hh - ft }, { x: hb, y: hh - ft }, { x: hb, y: hh }, { x: -hb, y: hh },
    ].map((q) => ({ x: rund(q.x), y: rund(q.y) }));
  }
  // rechteck (Default)
  const hb = (p.b ?? 0) / 2;
  const hh = (p.h ?? 0) / 2;
  return [
    { x: -hb, y: -hh }, { x: hb, y: -hh }, { x: hb, y: hh }, { x: -hb, y: hh },
  ].map((q) => ({ x: rund(q.x), y: rund(q.y) }));
}

/**
 * V0953 P-LAGENART-SCHEMA (`docs/V0953-SPEZ-NEUEOBERFLAECHE.md`, ROADMAP
 * 1198 «B10 ist nach 17 Tagen halb gebaut», SIA 400 Anhang B §16, Figur 35/
 * B.8.11) — `'aufgesetzt'` ist die sechste Lagenart: eine «neue Oberfläche
 * auf bestehender Konstruktion» (Vorsatzschale, Aufdoppelung, neuer Belag).
 *
 * **Owner-Entscheid 27.08.2026, Weg A (§1.1 der Spezifikation), im
 * Owner-Wortlaut:** «Eine 'aufgesetzt'-Lage vergrössert die gezeichnete
 * Wandkörperbreite.» Begründung: `assemblyThickness()` (`geometry/wall.ts`)
 * summiert schon heute jede Lage ausnahmslos, Bemassung und Mengen ziehen
 * automatisch mit — und die drei Alltagsfälle (Vorsatzschale, Aufdoppelung,
 * neuer Belag) sind real raumbildend, keine reine Zeichenkonvention. Weg B
 * (Lage bleibt reines 2D-Sinnbild ohne Dicken-Wirkung) wäre für eine reine
 * Beschichtung ohne relevante Dicke die treffendere Lesart gewesen, hätte
 * aber praktisch jede geometrische Kernel-Funktion um eine Struktur-/
 * Gesamtdicken-Unterscheidung erweitert (§1.2) — dagegen entschieden.
 *
 * **Owner-Entscheid 27.08.2026, Weg 3 (§1.3 der Spezifikation) — der Preis
 * ist mitentschieden, keine Halbmassnahme:** 3D (`derive/scene.ts`,
 * `deriveWall()`) und IFC (`ifc/export.ts`) texturieren die Wand weiterhin
 * AUSSCHLIESSLICH mit dem Material der `'tragend'`-Schicht, ohne
 * zusätzlichen Export-Umbau. Der Wandkörper wird dadurch korrekt breiter
 * (Konsequenz von Weg A oben), bleibt aber an der neuen Aussenfläche mit
 * dem falschen Material texturiert — **eine deklarierte Grenze, keine
 * Lücke**, exakt nach dem Muster von `Opening.geschlossen` (2D-only,
 * ROADMAP.md:5277): IFC kennt heute ohnehin für KEINE der sechs Lagenarten
 * eine Mehrschicht-Darstellung (`grep -c IFCMATERIALLAYERSET ifc/export.ts`
 * → 0) — eine Halbmassnahme nur für die sechste wäre eine Inkonsistenz
 * zwischen den Lagenarten selbst, kein Fortschritt.
 */
export type LayerFunction = 'tragend' | 'daemmung' | 'bekleidung' | 'dichtung' | 'hohlraum' | 'aufgesetzt';

/**
 * v0.9.17 P-B — die Richtung einer **Stablage** (Owner-Beanstandung 07.08.:
 * «bei einer lattung muss stehen ob diese vertikal oder horizontal ist»).
 *
 * Bezug ist die **Bauteilachse**, nicht die Welt: `laengs` läuft mit der
 * Achse, `quer` steht senkrecht dazu. Eine Konterlattung und die Traglattung
 * darüber tragen deshalb verschiedene Werte — genau das unterscheidet sie.
 *
 * **Korrektur v0.9.20 (P-C) — der Klammersatz hier war falsch und hätte ein
 * falsches Bild erzeugt.** Bis hierher stand da «in einer stehenden Wand also
 * senkrecht», die Achse einer Wand wäre demnach ihre Höhe. Die **Erfassung**
 * benutzt seit v0.9.17 die andere Lesart, und zwar durchgängig über alle
 * neun belegten Einträge: sie führt den Ständer als **`quer`** mit der
 * Herleitung «Ständer sind die senkrecht stehenden Hölzer der Wand»
 * (`wissen/regelwissen/lineare-schichten.json`, Lehrheft Wandkonstruktionen
 * S. 43/52). Die Achse einer Wand ist dort ihre **Länge im Grundriss** — und
 * das deckt sich mit `axisDirection(wall)` im Modell.
 *
 * **Massgeblich ist die Erfassung**, aus zwei Gründen: sie ist die grössere
 * und belegte Menge (neun Einträge, jeder mit Heftstelle), und sie stimmt
 * mit dem Achsbegriff des Modells überein. Am Dach sind ohnehin beide
 * Lesarten gleich — «senkrecht zur Traufe» ist `quer`, egal welcher
 * Klammersatz gilt.
 *
 * Die Regel lautet damit unmissverständlich:
 *
 * - **`laengs`** = mit der waagrechten Ausdehnung des Bauteils: die
 *   Traglattung auf dem Sparren, ein waagrechter Riegel in der Wand, eine
 *   Latte parallel zum First.
 * - **`quer`** = senkrecht dazu: der stehende Ständer, der Sparren vom First
 *   zur Traufe, die Konterlattung.
 *
 * **Warum das keine Wortklauberei ist:** v0.9.20 P-A leitet aus der Richtung
 * ab, ob der Rhythmus im Bild sichtbar ist. Mit dem alten Klammersatz hätte
 * jede Holzständerwand ihre Ständer als **waagrechte Sprossen** bekommen.
 * Gefunden hat es der Versuch, die Referenzpläne aus dem echten Katalog zu
 * bauen — nicht ein Test.
 *
 * **v0.9.24 (P-B) — die DECKE trägt hier bewusst keinen Wert.** Bis dahin
 * nannte dieser Kommentar nur Wand und Dach, und das war kein Zufall: beide
 * Werte setzen eine Bauteilachse voraus, und die trägt nur die Wand
 * (`a`/`b`) bzw. das Dach (`firstrichtung`) — die Decke ist ein Umriss ohne
 * Achsenfeld. Ihr Korpus (`wissen/regelwissen/lineare-schichten.json`)
 * lässt die Richtung der tragenden Balkenlagen darum ausdrücklich leer,
 * «weil sie der Raumgeometrie folgt» (`docs/V0924-SPEZ.md` §1 M6). Bei der
 * Wand ist eine fehlende `richtung` also **Unwissen**, bei der tragenden
 * Deckenlage eine **Verweisung**: die Spannrichtung wird aus dem Umriss
 * abgeleitet (`derive/deckenachse.ts`, Owner-Entscheid 09.08.2026 «Balken
 * über die kurze Seite») und im Schnitt über einen eigenen Guard gezeichnet
 * (`deckenStabRaster` in `derive/stabraster.ts`, Zeichnung in
 * `derive/section.ts` `deckenStabFlaechen`). Der Gegenwächter
 * `kosmo-data/test/deckenbalken-richtung.test.ts` hält fest, dass der
 * Katalog diese Leere behält.
 *
 * **V6 — ein Satz oben stimmt seit dem 11.09.2026 nicht mehr, und er wird
 * hier berichtigt statt stillschweigend stehen gelassen:** die Decke ist
 * nicht länger «ein Umriss ohne Achsenfeld». Sie hat eines bekommen
 * (`Slab.spannrichtungGrad`, Owner-Entscheid «Hausregel, aber
 * uebersteuerbar»). An der Aussage dieses Absatzes ändert das nichts: das
 * Achsenfeld sitzt am BAUTEIL, nicht an der Schicht, und der Katalog lässt
 * `richtung` bei tragenden Deckenlagen weiterhin leer. Eine Schicht kann
 * nach wie vor nicht sagen, wohin die Decke spannt, die sie irgendwann
 * tragen wird — das ist der Grund, aus dem hier nichts steht, und er bleibt
 * gültig. Neu ist nur: die Verweisung führt jetzt zu einer Regel, die man
 * am Bauteil überstimmen kann.
 */
export type StabRichtung = 'laengs' | 'quer';

/**
 * v0.9.17 P-B — eine Schicht, die in Wirklichkeit **keine durchgehende
 * Fläche** ist, sondern eine Reihe von Stäben: Lattung, Konterlattung,
 * Sparren, Ständer, Riegel, Balken.
 *
 * **Das Vorhandensein dieses Feldes IST die Unterscheidung.** `stab`
 * gesetzt heisst linear, `stab` fehlt heisst flächig — es braucht kein
 * zweites Feld und keinen Aufzählungstyp, der beides nennt. **15** der 29
 * Katalog-Aufbauten tragen mindestens eine solche Lage, 27 von 138
 * Schichten. Der Befund (`docs/BEFUND-FLAECHIG-LINEAR.md`) nennt **14** —
 * der fünfzehnte (`decke-massivholzplatte-zellulose-40`, Hohlkasten) ist
 * nur über den Beschrieb belegbar und wurde aufgenommen; er steckte
 * ohnehin in den 27 Schichten. Am Modell nachgezählt und als Zeile
 * festgehalten in `kosmo-data/test/stablage.test.ts` — die Differenz ist
 * eine benannte Entscheidung, kein Zählfehler.
 *
 * **Alle drei Felder sind optional, und das ist kein Versehen.** Das
 * Vorhandensein von `stab` trägt die Aussage «diese Lage ist linear» —
 * sie ist für alle 27 Schichten belegt (`docs/BEFUND-FLAECHIG-LINEAR.md`).
 * Was die Stäbe im Einzelnen messen, füllt sich nach und nach auf.
 *
 * **v0.9.19: der Achsabstand ist entschieden worden.** Die Erfassung aus
 * den Lehrheften (`wissen/regelwissen/lineare-schichten.json`,
 * Owner-Auftrag 08.08.) hatte **keinen einzigen Einzelwert** gefunden — die
 * Hefte geben nur Spannen. Die Schweiz-Recherche
 * (`docs/RECHERCHE-ACHSMASSE-CH.md`) hat danach das **625-mm-Raster**
 * belegt, und der Owner hat es am 08.08.2026 als Bürostandard übernommen.
 * Die Werte stehen in `wissen/regelwissen/achsmasse-buerostandard.json`
 * und tragen im Modell die Herkunft `owner-entscheid` — sie sind eine
 * **Entscheidung**, keine Ablesung, und das muss ihnen anzusehen sein.
 *
 * **Kein `derive/` liest dieses Feld** (Wächter-Test in
 * `test/stablage.test.ts`). Es ist eine Angabe; das Zeichnen ist eine
 * Folge, und die kommt in einer eigenen Version — sonst liesse sich
 * hinterher nicht sagen, welcher Teil die Referenzpläne bewegt hat.
 */
/**
 * v0.9.19 P-B — **woher eine Zahl kommt, gehört zur Zahl.**
 *
 * Ein Achsabstand von 625 mm aus einem Bürostandard und einer aus einem
 * Lehrheft sehen im Modell gleich aus und wiegen völlig verschieden: der
 * eine ist eine Entscheidung, die jemand verantwortet, der andere eine
 * Ablesung. Ohne dieses Feld liesse sich beides nach einer Version nicht
 * mehr auseinanderhalten — und eine erfundene Herkunft wäre dann von einer
 * echten nicht mehr zu unterscheiden.
 */
export interface Herkunft {
  art: 'owner-entscheid' | 'lehrheft' | 'hersteller' | 'branchenkatalog';
  /** Der Beleg im Klartext: «Baubüro Andrin, 08.08.2026», «Deckenkonstruktionen S. 11». */
  beleg: string;
}

/** Ein Wert, der seine Herkunft mitträgt. Zusammen, nie getrennt. */
export interface Belegt<T> {
  wert: T;
  herkunft: Herkunft;
}

/**
 * v0.9.19 P-B — **Achsabstand ist keine einzige Grösse.** Die
 * Schweiz-Recherche (`docs/RECHERCHE-ACHSMASSE-CH.md`, Owner-Auftrag
 * 08.08.2026) hat drei Arten herausgearbeitet, die sich verschieden
 * verhalten:
 *
 * - **`raster`** — Sparren, Balkenlage, Ständer, Fassadenlattung. Teiler
 *   von 1250 mm, im Regelfall 625. Trägt EINEN Wert.
 * - **`abhaengig`** — die Konterlattung. Sie hat gar keinen eigenen Wert,
 *   sie übernimmt den der tragenden Lage darunter. Darum ist hier kein
 *   Zahlenfeld vorgesehen: eine Zahl, die es nicht geben darf, kann so
 *   auch nicht versehentlich hineingeschrieben werden.
 * - **`fremdgesteuert`** — die Ziegel-Traglattung folgt der Decklänge, die
 *   Faserzement-Unterkonstruktion der Windlast nach SIA 261. Diese Lagen
 *   dürfen **nicht** gerastert werden; sie tragen höchstens eine Spanne,
 *   nie einen zeichenbaren Einzelwert.
 *
 * **Der Typ ist absichtlich eine Union und kein Objekt mit optionalen
 * Feldern.** Wer die drei Arten in ein gemeinsames `achsabstand?: Mm`
 * presst, rastert früher oder später die Ziegellattung oder fixiert die
 * Fassaden-UK — beides fachlich falsch, und beides fiele niemandem auf.
 */
export type Achsabstand =
  | { art: 'raster'; mm: Belegt<Mm> }
  | { art: 'abhaengig'; von: 'lage-darunter' }
  | {
      art: 'fremdgesteuert';
      /** Wovon der Wert im Projekt abhängt — Klartext, damit es lesbar bleibt. */
      grund: string;
      /** Die Bandbreite, in der er sich bewegt. KEIN zeichenbarer Wert. */
      spanne?: Belegt<readonly [Mm, Mm]>;
    };

export interface StabLage {
  /** Bezogen auf die Bauteilachse. Fehlt, solange die Quelle sie nicht nennt. */
  richtung?: StabRichtung;
  /**
   * Fehlt, solange niemand etwas über den Rhythmus dieser Lage weiss.
   * Vorhanden heisst NICHT «es gibt eine Zahl» — s. `Achsabstand`.
   */
  achsabstand?: Achsabstand;
  /** Stabbreite quer zur Spannrichtung; die Höhe ist `thickness`. */
  breite?: Belegt<Mm>;
  /**
   * v0.9.23 P-A (`docs/V0923-SPEZ.md` §3): woraus der STAB selbst ist — nicht
   * zu verwechseln mit `AssemblyLayer.material`, dem SCHICHTmaterial (das
   * beschreibt die Füllung, s. `derive/section.ts` `istHolzTragschicht`).
   * **Optional, bewusst kein Pflichtfeld** (Sanktion 2 der Spezifikation):
   * Altdokumente kennen es nicht, und es gibt keinen Migrationsweg im Repo
   * (Yjs spiegelt Entities 1:1 ohne Schemaprüfung). **Fehlt es, gilt Holz** —
   * das war schon vor diesem Feld das einzige Verhalten, das die Ableitungen
   * kannten (`derive/plan.ts`, `derive/section.ts`).
   */
  material?: string;
}

export interface AssemblyLayer {
  material: string;
  thickness: Mm;
  function: LayerFunction;
  /** Gesetzt = lineare Lage (s. `StabLage`); fehlend = flächige Schicht. */
  stab?: StabLage;
}

/**
 * Mehrschichtiger Aufbau (ArchiCAD-Composite) — Typenkatalog-Eintrag.
 * Schichten von der Referenzseite (aussen bzw. oben) nach innen/unten.
 */
export interface Assembly extends Base {
  kind: 'assembly';
  name: string;
  target: 'wall' | 'slab' | 'roof';
  layers: AssemblyLayer[];
}

export type WallAlignment = 'zentrum' | 'kern-aussen' | 'kern-innen';

/** Wand — Achse als Segment, Dicke/Schichten aus dem Aufbau. */
export interface Wall extends Base {
  kind: 'wall';
  storeyId: string;
  a: Pt;
  b: Pt;
  assemblyId: string;
  /** Lage der Achse relativ zum Aufbau. */
  alignment: WallAlignment;
  /** Höhenmodus: bis OK nächstes Geschoss (Standard) oder fix. */
  heightMode: 'geschoss' | 'fix';
  height?: Mm;
  /** Fusspunkt-Versatz gegenüber OK Boden des Geschosses. */
  baseOffset: Mm;
  /** P-DP (GOLDEN-WECHSEL-096): expliziter Override, welche Seite die
   * Referenzseite (aussen) des Schichtaufbaus ist — additiv, `undefined` =
   * automatisch über die Umlaufrichtung der geschlossenen Wandschleife
   * bestimmt (`geometry/wall.ts` `wandReferenzseite`). Selten nötig: nur für
   * Wände, die zu keiner sauberen geschlossenen Schleife gehören und bei
   * denen der ehrliche Rückfall `'links'` die falsche Seite trifft. */
  referenzseite?: 'links' | 'rechts';
}

/** Decke/Bodenplatte — Umriss auf Geschossebene, Dicke nach unten. */
export interface Slab extends Base {
  kind: 'slab';
  storeyId: string;
  outline: Pt[];
  holes?: Pt[][];
  assemblyId?: string;
  thickness: Mm;
  /** Versatz der Oberkante gegenüber OK Boden des Geschosses. */
  topOffset: Mm;
  /**
   * **V6 «Hausregel, aber übersteuerbar»** — die Spannrichtung DIESER
   * Decke, ausdrücklich gesetzt, als Winkel in Grad gegen die x-Achse.
   * Fehlt das Feld (jedes bisherige Dokument, jede Decke aus
   * `design.deckeZeichnen`), gilt unverändert die Hausregel: die Achse wird
   * aus dem Umriss abgeleitet (`derive/deckenachse.ts` `deckenachse`,
   * Owner-Entscheid 09.08.2026 «der Balken nimmt den kuerzeren Weg»).
   *
   * DER ANLASS, und er ist gemessen und nicht ausgedacht: am 10.09.2026 hat
   * der Owner die Laufrichtung einer Brettstapeldecke am fertigen Bild
   * korrigiert — «die laufrichtung der brettstapeldecke ist noch um 90 Grad
   * gedreht und laeuft in die andere richtung». Eine Regel, die immer den
   * kürzeren Weg wählt, lässt genau diese Korrektur nicht zu. Der
   * Owner-Entscheid dazu lautet wörtlich «Hausregel, aber uebersteuerbar»:
   * der kürzere Weg bleibt Standard, damit Schnitt und Bild nie
   * widersprechen — wer es anders will, sagt es am Bauteil.
   *
   * EINE ACHSE IST EINE GERADE, KEIN PFEIL. `v` und `-v` bezeichnen
   * dieselbe Spannrichtung; 90 und 270 liefern darum denselben Wert, der
   * Winkel wird modulo 180 gelesen. Das ist dieselbe Regel, nach der
   * `achsWinkel` in `derive/deckenachse.ts` den Quadrat-Fall entscheidet —
   * hier steht sie, damit niemand «die andere Richtung» als 180 Grad
   * einträgt und sich über die ausbleibende Wirkung wundert. Gedreht wird
   * um 90.
   *
   * GRAD UND NICHT `'x' | 'y'` — gemessen am Nachbarn: `Roof.firstrichtung`
   * kennt nur zwei Werte, weil ein Satteldach dort über einem
   * achsparallelen Rechteck sitzt. Die Hausregel hier liefert für ein um 30
   * Grad gedrehtes Haus eine um 30 Grad gedrehte Achse (`deckenachse` nimmt
   * das MINIMALrechteck, ausdrücklich nicht die Bounding-Box). Ein
   * Zwei-Werte-Feld könnte eine solche Decke nicht übersteuern, ohne sie
   * zugleich ins Weltkoordinatensystem zu zwingen. «Grad» ist im Haus die
   * eingeführte Schreibweise für Winkel am Entity (`rotationGrad`,
   * `wendelWinkel`, `winkelGrad`).
   *
   * WARUM AM ENTITY UND NICHT AN `meta` — die Frage ist gestellt worden,
   * `meta.nurBild` und `meta.aussehen` sind gelesen, und die Antwort fällt
   * GEGEN dieses jüngere Muster aus. Drei Gründe:
   *
   * (a) Beide Marken begründen sich selbst mit «ohne Geometriewirkung, ohne
   *     Mengenwirkung» (s. `EntityMeta.aussehen`). Dieses Feld verschiebt
   *     Geometrie: es entscheidet, welcher Balken im SCHNITT quer und
   *     welcher längs getroffen wird (`derive/section.ts`
   *     `deckenStabFlaechen`) und wo jede einzelne Latte liegt. Daran hängt
   *     ein gezeichneter Plan, nicht nur ein Bild.
   *
   * (b) Dieselbe Angabe trägt jedes Nachbarbauteil bereits AM ENTITY: die
   *     Wand ihre Achse als `a`/`b`, das Dach seine als `firstrichtung`.
   *     Der Kommentar bei `StabRichtung` oben nennt beide und hält fest,
   *     die Decke sei «ein Umriss ohne Achsenfeld». Genau dieses Achsenfeld
   *     ist es. In `meta` gelegt, stünde derselbe Gedanke bei drei
   *     Bauteilen an zwei verschiedenen Orten.
   *
   * (c) `meta` ist im Haus der Ort für Marken mit GENAU EINER Lesestelle
   *     (`layer` → DXF, `locked` → Interaktionspfad, `nurBild` →
   *     `derive/scene.ts`, `aussehen` → `derive/gltf.ts`). Diese Angabe
   *     brauchen ZWEI Ableitungswege, Schnitt und Bild — sie ist
   *     Modelldatum, keine Marke.
   *
   * **ES GIBT WEITERHIN KEINEN SETZWEG AUS DER OBERFLÄCHE UND KEINEN FÜR
   * KOSMO**, und das gehört offen hingeschrieben, weil die Nachbarfelder ihn
   * mit V9 bekommen haben. `design.merkmalSetzen` nimmt dieses Feld
   * ABSICHTLICH NICHT auf: jener Befehl setzt ausschliesslich Merkmale, die
   * nur den Bildkanal erreichen, und sagt das in seinem Werkzeugtext. Dieses
   * Feld verschiebt Plangeometrie (Absatz (a) oben) — es dort einzureihen
   * hiesse, dem Modell im Werkzeugtext etwas Falsches zu sagen, und der Text
   * ist das, was das Modell liest. Es gehört in die Familie von
   * `design.eigenschaftSetzen` (Entity-Felder mit Planwirkung); dort fehlt es
   * heute aus dem alten Token-Grund. Bis dahin wird es programmatisch
   * geschrieben, als Patch auf die Decke — derselbe Weg, den ein Einleser
   * ohnehin nimmt.
   *
   * GELESEN WIRD ES AN GENAU EINER STELLE: `deckenachseVon` in
   * `derive/deckenachse.ts`. Schnitt und Bild fragen beide dort, und der
   * Wächter `test/deckenachse-uebersteuerung.test.ts` hält fest, dass kein
   * Ableitungsweg die Hausregel direkt aufruft und sich so an der
   * Übersteuerung vorbeimogelt. Ohne diesen Riegel wäre dieses Feld die
   * gefährlichste Art von Einstellung: eine, die das Bild dreht und den
   * Schnitt stehen lässt.
   *
   * EIN UNBRAUCHBARER WERT (NaN, Infinity) ERGIBT KEINE ACHSE — NICHT DIE
   * HAUSREGEL. `deckenachseVon` gibt dann `null`, und beide Ableitungswege
   * lassen den Balkenrhythmus weg. Der stille Rückfall auf die Hausregel
   * wäre bequemer und wäre falsch: wer eine Richtung setzt und die andere
   * bekommt, sucht den Fehler nie bei seinem Wert.
   */
  spannrichtungGrad?: number;
}

/** Öffnung — in einer Wand verankert (Host-Beziehung). */
export interface Opening extends Base {
  kind: 'opening';
  wallId: string;
  openingType: 'fenster' | 'tuer' | 'leibung';
  /** Abstand Wandanfang (Punkt a) → Öffnungsmitte, entlang der Achse. */
  center: Mm;
  width: Mm;
  height: Mm;
  /** Brüstungshöhe ab OK Boden (bei Türen 0). */
  sill: Mm;
  /** Anschlagrichtung für das Tür- ODER Fensterflügel-Symbol im Grundriss
   * (v0.6.9 Stream A: bei fensterTyp 'einfluegel' bestimmt swing die
   * Angelseite des Öffnungsbogens; 'fensterband'/'fest' tragen kein swing). */
  swing?: 'links' | 'rechts';
  /** Fensteranschlag-Tiefe in der Leibung (B4, Werkplan-Detail; Default 40). */
  anschlag?: Mm;
  typeId?: string;
  /** Fenstertyp (v0.6.9 Stream A, docs/FENSTER-KONZEPT.md): fehlt =
   * Alt-Fenster (heutiges Zweilinien-Symbol, keine Teilung, kein
   * Flügelbogen, keine 3D-Rahmen). Nur bei openingType 'fenster' sinnvoll. */
  fensterTyp?: 'einfluegel' | 'zweifluegel' | 'fest' | 'fensterband';
  /** Feldteilung n (horizontal) × m (vertikal) — Flügel-/Pfosten-Riegel-
   * Raster. Nur wirksam, wenn fensterTyp gesetzt ist. */
  teilung?: { n: number; m: number };
  /** Rahmen-/Pfostenbreite in mm (Blendrahmen bzw. Fensterband-Profil);
   * fehlt = Default 60 in der Ableitung (FENSTER_RAHMEN_DEFAULT_MM). */
  rahmenbreite?: Mm;
  /** Flügeltyp (v0.7.1 E5/4B, docs/V071-KONZEPT.md): steuert die SIA-
   * Öffnungssymbolik in Ansicht (Dreieck/Pfeil) und Grundriss (Doppelstrich/
   * versetzte Doppellinie). Fehlt = keine Symbolik — heutiges Bild bleibt
   * byte-identisch (Goldens-Guard, wie `fensterTyp` in v0.6.9). Nur bei
   * openingType 'fenster' sinnvoll; unabhängig von `fensterTyp` (additiv). */
  fluegelTyp?: 'dreh' | 'kipp' | 'drehkipp' | 'schiebe' | 'fest';
  /**
   * Öffnungsrichtung (v0.7.3 D2, `docs/V073-GESTALTUNG-SPEZ.md` §D2):
   * bestimmt die Strichelung der SIA-Flügelsymbolik in Ansicht/
   * Live-Schnittvorschau — **durchgezogen = öffnet zum Betrachter (innen,
   * Default)**, **gestrichelt (Kadenz 2–1 mm) = öffnet weg (aussen)**.
   * Additiv und rein darstellerisch (keine Geometrieänderung): fehlt/false
   * = heutiges durchgezogenes Bild bleibt byte-identisch (Goldens-Guard,
   * wie `fluegelTyp` selbst). Es gab bisher KEIN Feld, das die
   * Öffnungsrichtung trägt (`swing` ist die ANSCHLAGSEITE/Bandseite, nicht
   * innen/aussen) — dieses Feld schliesst die Lücke, statt `swing`
   * zweckzuentfremden. Nur bei `openingType 'fenster'` sinnvoll,
   * unabhängig von `fluegelTyp` (eine Öffnung ohne `fluegelTyp` zeigt
   * ohnehin keine Symbolik, das Feld bleibt dann wirkungslos). */
  oeffnetNachAussen?: boolean;
  /**
   * Beschlag-Katalog S0 (v0.7.3 D6, `docs/V073-GESTALTUNG-SPEZ.md` §D6):
   * additive Beschlag-Attribute, NUR im Werkplan sichtbar (Daten-Guard —
   * ohne diese Felder bleibt der Grundriss byte-identisch). Sechs Symbole
   * der Katalogstufe S0: Band, Griffseite, Brüstungshöhe (BRH — bewusst
   * KEIN eigenes Feld, die Ableitung etikettiert das bestehende `sill`),
   * Schiebe-Lauf (bewusst kein eigenes Feld — abgeleitet aus
   * `fluegelTyp === 'schiebe'`, s. `derive/plan.ts`), Motorantrieb
   * (`antrieb`) und Absturzsicherung (`absturzsicherung`). Anschläge/RWA/
   * Dichtebene und die 12er-Ausbaustufe S1 bleiben bewusst vertagt (Canvas
   * 7a) — NICHT gebaut.
   */
  /** Bandseite (Scharnierlage) am Blendrahmen — welche Kante des
   * Öffnungsrahmens die Bänder trägt. */
  band?: 'links' | 'rechts' | 'oben' | 'unten';
  /** Seite des Griffs/Drückers (Bedienseite), unabhängig von `swing`
   * (Anschlagseite) und `band`. */
  griffseite?: 'links' | 'rechts';
  /** Motorantrieb vorhanden (Katalogsymbol «M» im Werkplan). */
  antrieb?: boolean;
  /** Absturzsicherung (Geländer/Sicherheitsglas-Hinweis) vorhanden. */
  absturzsicherung?: boolean;
  /**
   * Beschlag-Katalog S2 (v0.7.5 Welle 1 A1): Liste zugewiesener Katalog-Keys
   * aus `BESCHLAG_KATALOG` (`derive/beschlag.ts`, 12 Typen: Türdrücker,
   * Scharnier, Schloss, …). Bewusst OPENING-GEHOSTET (additives Array-Feld)
   * statt einer eigenen Entity wie `Furniture` — Beschläge sind
   * bauteilgebunden (Tür/Fenster), das additive Feld bleibt golden-/undo-/
   * vault-/.kosmo-sicher ohne neue Entity-Klasse. Eine freie, unabhängig
   * platzierbare Beschlag-Instanz (die im S1-Header angedeutete «eigene
   * Entity»-Variante) bleibt bewusst ein optionaler späterer S3-Weg. Additiv
   * und nur im Werkplan sichtbar (Daten-Guard, wie die S0-Felder oben) —
   * fehlt = heutiges Bild bleibt byte-identisch.
   */
  beschlaege?: string[];
  /**
   * B10 (`docs/AUFTRAG-B9-B10-KOTEN-UMBAU.md`, SIA 400 Figur 35/B.8.11,
   * Quelle SN EN ISO 7518): die Öffnung wird zugemauert («Schliessen einer
   * Öffnung»). Norm-Darstellung im **neu gezeichneten** Plan (KosmoOrbit
   * zeichnet immer neu, nie einen bestehenden Plan nach — es gilt
   * durchgehend die rechte Spalte der Figur): schmales schraffiertes Feld
   * zwischen zwei Linien an der Stelle der alten Öffnung, statt eines
   * offenen Lochs. Bewusst ein eigenes Feld statt der Wiederverwendung von
   * `meta.renovation` (`bestand|abbruch|neu`, ArchiCAD-Essenz #9) — jener
   * Status trägt die Bauphasen-Sicht über mehrere Blattplatzierungen
   * (`derive/umbau.ts`, `docFuerUmbau`), während «geschlossen» eine
   * dauerhafte Eigenschaft DIESER Öffnung ist und unabhängig von der
   * Umbau-Blattauswahl gilt. Fehlt/false = offene Öffnung, heutiges
   * Verhalten (Goldens-Guard). Setter: `design.oeffnungSchliessen`. */
  geschlossen?: boolean;
  /**
   * V8 «Der Vorhang» — vor DIESER Öffnung hängt eine Stoffbahn
   * (`derive/vorhang.ts` `deriveVorhaenge`, volle Begründung dort).
   *
   * NUR FÜRS BILD, und zwar in beide Richtungen: Die Geometrie entsteht
   * ausschliesslich im Anhang-Kanal `deriveAllMitBilddetails`
   * (`derive/scene.ts`) und damit nur in 3D-Ansicht und glTF-Ausfuhr.
   * Grundriss, Schnitt, Axonometrie, Bemassung, Mengen und IFC sehen den
   * Vorhang NICHT — er wird nicht bemasst und nicht ausgeschrieben. Fehlt
   * das Feld (also in jedem heute bestehenden Dokument), ändert sich
   * nichts: `deriveVorhaenge` liefert dann ein leeres Array.
   *
   * WARUM EIN FELD AN DER ÖFFNUNG und nicht eine eigene Bauteilart oder ein
   * Möbel: Ein Vorhang ist ohne seine Öffnung sinnlos — Breite, Höhe und
   * Lage kommen ALLE aus ihr (genau wie beim Fensterglas,
   * `deriveFensterGlas`). Eine eigene Entity müsste diese Masse doppelt
   * führen und bei jeder Fensteränderung nachgezogen werden. Dasselbe
   * Muster tragen `geschlossen`, `antrieb` und `absturzsicherung` schon:
   * additive optionale Felder an der Öffnung.
   *
   * WARUM NICHT `meta.nurBild`: Jene Marke nimmt ein Bauteil aus `deriveAll`
   * HERAUS. Die Öffnung soll dort bleiben (sie schneidet die Wand), und
   * «diese Öffnung ist nur fürs Bild» hiesse etwas ganz anderes als «vor
   * dieser Öffnung hängt Stoff».
   *
   * GESETZT WIRD ES SEIT V9 mit `design.merkmalSetzen`, Merkmal `vorhang`.
   * Der frühere Einwand — die Werkzeugliste der KI-Lane hatte 31 Token Luft
   * — galt, und er ist eingelöst worden, indem EIN Befehl acht Merkmale trägt
   * und einen bestehenden ersetzt (Rechnung bei `design.merkmalSetzen`).
   * NICHT aufgenommen wurde `vorhang` dagegen in `design.eigenschaftSetzen`:
   * jener Befehl setzt Entity-Felder mit PLANWIRKUNG, dieser hier nur
   * Merkmale, die ausschliesslich den Bildkanal erreichen — die Trennung
   * bleibt lesbar, und sein Werkzeugtext bleibt wahr.
   *
   * EINE GRENZE, die der Befehl NICHT abfängt: an einer zugemauerten Öffnung
   * (`geschlossen`) wird der Vorhang gesetzt und dann von `derive/vorhang.ts`
   * übersprungen. Kein toter Wert (wird die Öffnung wieder geöffnet, hängt er
   * da), aber eine Wirkung, die ausbleibt, ohne dass es jemand sagt.
   *
   * Gilt für `openingType` 'fenster' UND 'tuer' (die Balkontür ist der
   * häufigste Vorhangfall überhaupt); eine 'leibung' trägt keinen.
   */
  vorhang?: boolean;
}

/**
 * Zone/Raum — Polygon mit SIA-416-Klassierung.
 *
 * B15 §4.3/§4.2 (`docs/AUFTRAG-B15-SIA416-NGF-IST-GF.md`): additive
 * Erweiterung der fuenf urspruenglichen Innen-Klassen um zwei Aeste, beide
 * rein aus der Legenden-NUMMERIERUNG abgeleitet (Gliederungscodes, kein
 * Normwortlaut):
 *
 * - **KFT/KFN** — die Konstruktionsflaeche (`KF`) zerfaellt in tragend
 *   (KFT) und nichttragend (KFN). `KF` selbst bleibt gueltig und
 *   unveraendert (Bestandskonvention `derive/schwarzplan.ts`
 *   `PARZELLEN_SIA_MARKE`, jede bestehende Zone) — KFT/KFN sind eine
 *   zusaetzliche, feinere Wahlmoeglichkeit, keine Ablösung.
 * - **ANF/AVF** — der Aussen-Ast: eine Zone ausserhalb der Gebaeudehuelle
 *   (z. B. ein Balkon) traegt eine Nutz- oder eine Verkehrsflaeche, die
 *   NICHT in die innere NGF gehoert (`derive/sia416.ts` zaehlt sie separat
 *   als `angf`). Die aussenseitige Konstruktionsflaeche (AKF/AKFT/AKFN) ist
 *   NICHT Teil dieser Erweiterung — sie bleibt ein offener Folgeschritt
 *   (B15 §4.2, Reichweite bewusst kleiner als die volle Aussen-Hierarchie).
 *
 * Bestehende Dokumente/Tests/Goldens sind unberuehrt: keine Zone traegt
 * heute einen der vier neuen Werte, jede Summe bleibt bei ausschliesslich
 * alten Werten unveraendert (siehe `derive/sia416.ts`).
 */
export type Sia416Class = 'HNF' | 'NNF' | 'VF' | 'FF' | 'KF' | 'KFT' | 'KFN' | 'ANF' | 'AVF';

export interface Zone extends Base {
  kind: 'zone';
  storeyId: string;
  outline: Pt[];
  name: string;
  number?: string;
  sia: Sia416Class;
  /** Nutzungstyp fürs Raumprogramm (z.B. 'marktgerecht', 'gewerbe'). */
  program?: string;
  /** Raumtyp für Raumgraph/Checks (V2-F1), z.B. 'korridor', 'treppenhaus'. */
  raumTyp?: string;
  /**
   * Site-/Parzellen-Marker (v0.7.0 D8/H-1): additiv, KEINE Migration nötig —
   * Zonen ohne dieses Feld verhalten sich unverändert. Kennzeichnet eine
   * Zone, die eine importierte Kataster-Parzelle repräsentiert (statt eines
   * Raums). Solche Zonen werden von Raumtyp-Checks (`derive/checks.ts`) und
   * von der SIA-416-Flächensumme (`derive/sia416.ts` `areaReport`/`totalNgf`)
   * ausgenommen — die `sia`-Klasse bleibt (meist `'KF'`, Bestandskonvention
   * für `derive/schwarzplan.ts`). Die Parzellenfläche für AZ läuft
   * unverändert separat über `doc.settings.parzellenFlaeche`. Die frühere
   * EHRLICHE GRENZE zu `derive/berechnungsliste.ts` ist seit v0.9.26
   * geschlossen (B19 §1.1): auch dort werden `parzelle`/`nachbar` jetzt
   * mit demselben Filter übersprungen wie hier beschrieben.
   *
   * `'nachbar'` (v0.7.1 E2/1B): additiv nach demselben Muster wie
   * `'parzelle'` — kennzeichnet eine Zone als importierten Nachbargebäude-
   * Footprint (reine Kontext-Geometrie fürs Situationsplan-Bild, kein
   * eigener Raum). Genau wie `'parzelle'` von Raumtyp-Checks und der
   * SIA-416-Flächensumme ausgenommen (`derive/checks.ts`, `derive/
   * sia416.ts`); `derive/schwarzplan.ts` zeichnet Nachbar-Zonen separat als
   * graue Footprints. Entsteht über `design.nachbarnUebernehmen`
   * (`commands/design.ts`) und seit v0.8.6 (E2) auch über das freie
   * `zoneErstellen` — nötig, damit der Eck-Griff-Zug (Erstellen+Löschen
   * in einer Gruppe) den Marker nicht verliert.
   */
  zonenArt?: 'parzelle' | 'nachbar';
}

/** Treppe — Achse a→b, Breite; Steigung aus Geschosshöhe. Formen: V2-A2. */
export interface Stair extends Base {
  kind: 'stair';
  storeyId: string;
  /** Antritt (unten). */
  a: Pt;
  /** Austritt (oben) — bei «u» Ende des ersten Laufs (Wendepodest dahinter). */
  b: Pt;
  width: Mm;
  /** gerade (Default) · podest (Zwischenpodest) · u (Wendepodest) · l (Eckpodest) · gewendelt (Kreisbogen-Lauf, V093-SPEZ §P-T). */
  form?: 'gerade' | 'podest' | 'u' | 'l' | 'gewendelt';
  /** Eckpunkt des L-Laufs (nur form 'l'). */
  ecke?: Pt;
  /**
   * Wendelwinkel in Grad, NUR bei form 'gewendelt' gelesen (additiv — bei
   * jeder anderen Form bleibt das Feld folgenlos, Daten-Guard V093-SPEZ §P-T
   * Sanktion 3). Vorzeichen = Drehsinn von a nach b gesehen (+ links/CCW,
   * − rechts/CW); Betrag typischerweise 90 (Viertelwendel) oder 180 (Halb-
   * wendel). Bewusst KEIN eigener Radius-Parameter: a/b bleiben Antritt/
   * Austritt wie bei jeder anderen Form, der Radius folgt aus Sehne (a→b)
   * + Winkel (Kreis-Sehnen-Formel, `derive/treppe.ts`) — dieselbe Sparsam-
   * keit wie bei der Steigung selbst, die auch nicht gespeichert wird.
   */
  wendelWinkel?: number;
}

/**
 * Rampe (v0.9.1 P-A2, `docs/V091-SPEZ.md` §P-A2) — geneigte Fläche von a
 * (Fuss, unten) nach b (Kopf, oben), Breite. Die Steigung (hoehenDelta/
 * Lauflänge) wird IMMER aus den Rohwerten abgeleitet (`derive/rampe.ts`),
 * NIE gespeichert — dieselbe Regel wie bei `Stair` (Steigung dort aus der
 * Geschosshöhe, hier direkt aus `hoehenDelta`). Das ehrliche Steigungs-Gate
 * mit den drei SIA-500-Bändern (B17: ≤6 % hindernisfrei; >6 % bis 12 %
 * Hinweis «bedingt zulässig nach SIA 500 — erfordert Handläufe»; >12 %
 * Hinweis «über der SIA-500-Grenze von 12 % — nicht hindernisfrei»; >15 %
 * harte Ablehnung, Tiefgaragen-Grenze aus dem Parkierungsnormenwerk VSS/SN,
 * nicht SIA 500) sitzt im Command (`design.rampeZeichnen`), nicht hier
 * im Modell — die Entity selbst nimmt jede geometrisch gültige Steigung an.
 */
export interface Rampe extends Base {
  kind: 'ramp';
  storeyId: string;
  /** Fusspunkt (unten, Geschossniveau). */
  a: Pt;
  /** Kopfpunkt (oben) — Länge a→b bestimmt zusammen mit hoehenDelta die Steigung. */
  b: Pt;
  width: Mm;
  /** Zu überwindender Höhenunterschied a→b in mm, > 0. */
  hoehenDelta: Mm;
  /** Optionales ebenes Zwischenstück (Podest) am oberen Ende, mm — zählt
   * nicht zur Steigungsstrecke (strengere, ehrliche Annahme statt einer
   * geschönten Durchschnittssteigung über die Gesamtlänge). */
  podestLaenge?: Mm;
}

/**
 * Geländer (v0.9.1 P-A1, `docs/V091-SPEZ.md` K24) — Absturzsicherung als
 * echtes Werkzeug: bisher gab es nur den 2D-Beschlagshinweis
 * `Opening.absturzsicherung` an Öffnungen, kein eigenständiges Bauteil für
 * freistehende Geländer (Balkon-/Terrassen-/Treppenhaus-Brüstungen). Muster
 * `MassKette`: eine offene Polylinie (mind. zwei Punkte, Welt-mm), kein
 * geschlossenes Polygon. Die Pfosten-/Handlauf-Zerlegung ist EINE geteilte
 * Wahrheit für 3D und den späteren Plan-Zweig, s. `derive/gelaender.ts`.
 */
export interface Gelaender extends Base {
  kind: 'gelaender';
  storeyId: string;
  /** Mindestens zwei Punkte (Muster `MassKette.punkte`), Welt-mm. Bleibt bei
   * gesetztem `bauteilId` als ROHDATEN erhalten (kein Löschen/Überschreiben)
   * — sie dienen dann als Seiten-Hinweis (welche Wirt-Kante gemeint ist,
   * s. `bauteilId`) und als Rückfallwert, falls der Wirt später verschwindet
   * (s. dort). */
  punkte: Pt[];
  /** Geländerhöhe ab OK Boden des Geschosses, mm — Command-Grenze 700–1500
   * (SIA-Absturzsicherungsbereich), ausserhalb wird ehrlich abgelehnt statt
   * geklemmt (`design.gelaenderZeichnen`). */
  hoehe: Mm;
  /** staketen (Default, senkrechte Stäbe zwischen den Pfosten) · handlauf
   * (nur das Handlauf-Band, keine Füllung) · voll (geschlossene Brüstung). */
  art: 'staketen' | 'handlauf' | 'voll';
  /**
   * Optionale Bindung an eine Treppe oder Rampe IM SELBEN Geschoss (v0.9.3
   * P-GB, `docs/V093-SPEZ.md` §P-GB) — additiv, Daten-Guard: fehlt das Feld,
   * bleibt jedes Verhalten (2D-Zerlegung `derive/gelaender.ts` `gelaenderTeile`,
   * 3D `derive/scene.ts`) BYTE-IDENTISCH zum Stand vor P-GB (Sanktion 3).
   *
   * Gesetzt: `gelaenderTeile` liest die Polylinie NICHT mehr aus `punkte`,
   * sondern leitet sie aus der Lauf-/Rampenkante des Wirts ab (`derive/
   * treppe.ts` `treppenTeile` bzw. `derive/rampe.ts` `rampenTeile` — dieselbe
   * Zerlegung, die auch 3D/Plan der Treppe/Rampe selbst speist, KEIN zweiter
   * Rechenweg, s. Kopfkommentar `derive/gelaender.ts`). Die Geländerhöhe wird
   * dabei ab der GENEIGTEN Oberkante des Wirtlaufs gemessen (ein Geländer auf
   * einer Treppe steht nicht waagrecht) — Details/Herleitung ebenfalls dort.
   *
   * `punkte` bleibt dabei bewusst UNVERÄNDERT im Dokument stehen (kein
   * Command schreibt sie beim Binden um): sie sind der Seiten-Hinweis, mit
   * dem `gelaenderTeile` entscheidet, welche der zwei Lauf-/Rampenkanten
   * gemeint ist (Begründung dieser Seitenwahl: `derive/gelaender.ts`-
   * Kopfkommentar), UND der ehrliche Rückfallwert, falls der Wirt gelöscht
   * wird: `design.loeschen` friert dann die zuletzt abgeleiteten Punkte in
   * `punkte` ein und entfernt `bauteilId` wieder (s. dort) — das Geländer
   * verschwindet NICHT mit seinem Wirt und kollabiert nicht auf 0 Punkte.
   * Zeigt `bauteilId` auf eine unbekannte oder falsch-typisierte Id, lehnt
   * das setzende Command das ehrlich ab (keine stille Nulloperation) —
   * `derive/gelaender.ts` selbst bleibt dennoch total (fällt in diesem Fall,
   * der im laufenden Betrieb durch das Command-Gate nie entstehen sollte,
   * auf `punkte` zurück, statt zu werfen — Muster `deriveGelaender`: pure
   * Ableitungen liefern `null`/einen Rückfallwert, nie eine Exception).
   */
  bauteilId?: string;
}

/** Walm- oder Satteldach — Grundriss-Polygon + Neigung; Geometrie via Straight Skeleton (Walm)
 * bzw. First-Ebenen-Teilung (Sattel). */
export interface Roof extends Base {
  kind: 'roof';
  storeyId: string;
  outline: Pt[];
  /** Dachneigung in Grad. */
  pitch: number;
  /** Dachüberstand über den Umriss hinaus. */
  overhang: Mm;
  /** Fusspunkt (Traufe) über OK Boden des Geschosses. */
  baseOffset: Mm;
  /** Dachform: «walm» (Default, alle Seiten geneigt) oder «sattel» (First + 2 Flächen,
   * Giebel an den Schmalseiten quer zur Firstrichtung). Fehlt das Feld (ältere Dokumente),
   * gilt «walm». */
  form?: 'walm' | 'sattel';
  /** Nur bei form «sattel»: Achse, entlang der der First verläuft. */
  firstrichtung?: 'x' | 'y';
  /**
   * Dach-Aufbau (v0.9.13 P-DACHAUFBAU, `docs/V0913-SPEZ.md` §1) — additiv,
   * nach demselben Muster wie `Slab.assemblyId`: fehlt das Feld (ältere
   * Dokumente, jedes bisherige Dach), bleibt das Dach eine leere Fläche mit
   * blosser Umrandung (`muster: 'keine'`, byte-identisch zu v0.9.12 —
   * Goldens-Guard). Gesetzt, schneidet `derive/section.ts` das Dach
   * schichtweise wie eine Wand mit Aufbau, jede Schicht mit ihrem eigenen
   * Sinnbild aus `derive/schraffur.ts` (`derive/dach.ts` trägt die dazu
   * nötige Tiefe/Schicht-Interpolation, s. `Pt3.sv` dort).
   */
  assemblyId?: string;
}

/** Baugrenze (Phase 0): Polygon aus dem Baugesetz + optionale Höhenbeschränkung. */
export interface Boundary extends Base {
  kind: 'boundary';
  storeyId: string;
  outline: Pt[];
  /** Maximale Gebäudehöhe über Projektnull (mm); null = keine. */
  maxHoehe: Mm | null;
  name: string;
  /** Grenzabstand (V2-Vorform): Bauteile müssen so weit INNERHALB der Linie bleiben (mm). */
  grenzabstand?: Mm | null;
  /** Mehrhöhenzuschlag: Anteil der Fassadenhöhe über der Freigrenze (z.B. 0.5 ab 12 m). */
  mehrHoehen?: { abHoehe: Mm; anteil: number } | null;
}

/** Volumenkörper für Vorform-artige Volumenstudien. */
export interface MassBody extends Base {
  kind: 'mass';
  storeyId: string;
  outline: Pt[];
  height: Mm;
  baseOffset: Mm;
  program?: string;
  /** Fassadenmodul je Kante (1-basiert), Name aus settings.fassadenModule. */
  module?: { kante: number; modul: string }[];
}

/**
 * FreeMesh (V2-Technik Block 3, Owner-Q9 Stufe 3) — frei editierbare
 * ENTWURFSGEOMETRIE (Schalen, skulpturale Dächer, Sonderformen). Bewusst im
 * Doc (selektier-/editier-/undo-/sync-fähig), aber mit HARTEM Budget: das
 * löst den Konflikt mit «Laufzeit ≠ Modell» — Scans/Bibliotheks-GLBs bleiben
 * Laufzeit-Referenz (asset-bibliothek), nie Doc-Last (Buildplan Block 3, E1).
 * Topologie (Verschweissung, planare Regionen) wird NIE gespeichert, sondern
 * zur Laufzeit abgeleitet (derive/mesh-topo.ts, E2).
 */
export interface FreeMesh extends Base {
  kind: 'freemesh';
  storeyId: string;
  /** Vertex-Positionen, flach [x0,y0,z0, x1,…] in mm (ganzzahlig);
   * z relativ zur Geschoss-OK (die Ableitung addiert storey.elevation). */
  positions: number[];
  /** Dreiecks-Indizes, flach [a0,b0,c0, a1,…] — Winding auswärts (CCW). */
  faces: number[];
  name?: string;
  /**
   * P-GLASNAHT (Messung 02.09.2026): Materialschlüssel des Kern-Katalogs
   * (`@kosmo/data` `materialkatalog`, z. B. 'glas', 'backstein', 'beton') —
   * fehlend = wie bisher 'masse' in der Ableitung.
   *
   * WARUM DAS FELD ÜBERHAUPT: Ohne es hatte ein übernommenes Fremdbauteil
   * im Dokument KEINEN Platz für sein Material. Gemessen an einer echten
   * Bestandsdatei (700 `IfcWindow`, alle mit `IfcRelAssociatesMaterial` auf
   * ein `IfcMaterial` namens «Glas»): die Fenster kamen als FreeMesh an,
   * die Ableitung gab ihnen 'masse', und im gerenderten Bild gab es kein
   * Glasmaterial und keinen durchsichtigen Kanal. Das Material war schon in
   * der Datei — es hatte hier nur nichts, worin es hätte ankommen können.
   *
   * Der Wert ist ein KATALOGSCHLÜSSEL, nicht der rohe IFC-Name: die
   * Übersetzung geschieht einmal beim Einlesen
   * (`modules/design/ifc-material.ts`), damit im Dokument genau EIN
   * Vokabular liegt — dasselbe, aus dem Schraffur, Priorität und Textur
   * schon lesen.
   */
  material?: string;
  /**
   * **A12 / Abnahmezeile 9 (17.09.2026) — woher diese Geometrie kommt und was
   * daraus folgt.**
   *
   * DER ANLASS, wörtlich: «zu den moebelgeometrien, bitte diese einsetzen die
   * wir offiziell duerfen im 3d modell». Und der Entscheid des Owners vom
   * 11.09.2026: CC0 darf ausgeliefert werden, Herstellermodelle dürfen im
   * BILD vorkommen, ihre Dateien verlassen den Rechner nicht.
   *
   * WARUM DAS FELD AM BAUTEIL HÄNGT UND NICHT AN DER BIBLIOTHEK: die
   * Objekt-Bibliothek (`apps/…/state/asset-bibliothek.ts`) führt bereits ein
   * `rights_status` — aber sie ist Laufzeit, nicht Dokument. Ein FreeMesh,
   * das aus einem Bibliotheks-Objekt entstanden ist, hat mit dem Anlegen jede
   * Verbindung dorthin verloren: es liegt im Doc, geht durch Yjs, durch Undo,
   * durch die IFC-Ausfuhr — und niemand kann ihm danach ansehen, ob es ein
   * CC0-Stück war oder ein Herstellermodell. Genau diese Trennung war im
   * Renderprojekt der Fehler: der Bericht behauptete «nur CC0-Ersatz»,
   * während vier Aufrufe am Tor vorbei Herstellerdateien einsetzten
   * (`~/kosmo-render/werkzeug/moeblieren_echt.py`, Kommentar bei `setze()`).
   * Die Reparatur dort war, je Stück eine Herkunft mitzuführen. Das ist
   * dieses Feld.
   *
   * **ES GIBT KEINEN DRITTEN WERT «ungeklaert», und das ist Absicht.** Der
   * dritte Zustand existiert (`import/glb-lesen.ts` `LizenzLage`), aber er
   * kommt nie ins Dokument: ein ungeklärtes Stück wird beim Einsetzen
   * abgewiesen. Ein `herkunft: 'ungeklaert'` im Modell wäre die Erlaubnis mit
   * einem Umweg — man hätte es eingebaut und sich dabei zugeflüstert, dass man
   * es nicht darf.
   *
   * **FEHLT DAS FELD, IST DAS KEINE ERLAUBNIS, SONDERN ALTBESTAND.** Es ist
   * optional, weil Dokumente von vor diesem Paket es nicht kennen und es im
   * Repo keinen Migrationsweg gibt (Yjs spiegelt Entities 1:1 ohne
   * Schemaprüfung) — dieselbe benannte Grenze wie bei `StabLage.material`.
   * Ein FreeMesh ohne dieses Feld ist entweder Eigenarbeit (gezeichneter
   * Quader, umgewandeltes Volumen — die tragen nie eine Fremdherkunft) oder
   * Altbestand. Wer zählt, zählt `art === 'hersteller'` und meldet fehlende
   * Angaben GETRENNT, statt sie stillschweigend als frei zu lesen.
   *
   * **BERICHTIGT AM 17.09.2026 — HIER STAND EIN SATZ, DER NICHT MEHR STIMMT.**
   * Er lautete: «Die AUSFUHR selbst liest es noch nicht … die Wirkung ist eine
   * gezeigte Warnung und kein Riegel.» Das war richtig, als es geschrieben
   * wurde, und ist seit dem Einbau von P25 falsch. Ein Grenz-Satz, der stehen
   * bleibt, nachdem die Grenze verschoben wurde, ist schlimmer als keiner — er
   * beruhigt über einen Zustand, den es nicht mehr gibt (Muster 2, «der Satz,
   * der lügt»). Nachgelesen im Code, nicht aus einer Meldung abgeschrieben.
   *
   * **WAS HEUTE WIRKLICH GILT:**
   *
   * - `derive/gltf.ts` (`beurteileHerkuenfte`, `AusfuhrLizenz`) liest dieses
   *   Feld JE BAUTEIL. Vorher las die Ausfuhr `doc.settings.herkunft` — die
   *   Herkunft des DOKUMENTS, und genau das war der Befund des Prüfers. Die
   *   glb trägt daraus einen Vermerk `weitergabe: 'frei' | 'nur-bild'` samt
   *   den gezählten Zahlen.
   * - Die **IFC-Ausfuhr SPERRT** wirklich (`modules/design/export-plan.ts`
   *   `exportIfcFile`), sobald ein Stück `art === 'hersteller'` trägt — laut,
   *   mit dem Namen jedes Stücks und mit einem benannten Ausweg («IFC ohne
   *   Herstellerteile»). Es wird dann KEINE Datei erzeugt.
   * - **Grundriss, Schnitt und DXF sperren NICHT**, und das ist kein
   *   Versehen: eine IFC trägt jedes Dreieck — das ist das Modell; eine
   *   Zeichnung trägt eine 2D-Figur, und «im Bild vorkommen» ist genau das.
   *   Vier Ausfuhrknöpfe sehen aus wie eine Gruppe und sind keine (Muster 17).
   * - Die Anzeige an der Oberfläche bleibt, wie sie war: Insel «Austausch»
   *   vor der Ausfuhr, Insel «Mesh» am gewählten Stück.
   *
   * **WAS WEITERHIN OFFEN IST:** `modules/vis/vis-jobs.ts` — der Weg zur
   * HomeStation — gehört einem anderen Dateikreis und ist hier nicht
   * nachgeprüft. Das steht da, damit es niemand für erledigt hält, und weil
   * genau diese Zeile schon einmal veraltet ist.
   *
   * ──────────────────────────────────────────────────────────────────────────
   * **P26 (17.09.2026) — DAS FELD HAT EINEN ZWEITEN LESER BEKOMMEN, und er
   * liest es zu einem ganz anderen Zweck.**
   *
   * `derive/scene.ts` `istEinrichtung` fragt `art`, um zu entscheiden, ob
   * dieses Stück den KAMERASTANDPUNKT bestimmen darf: `cc0` und `hersteller`
   * sind heruntergeladene Objekte und damit Einrichtung, `eigen` ist das
   * Bestandsmodell des Kunden und damit Bauwerk, ein fehlendes Feld ist
   * Eigenarbeit oder Altbestand und damit ebenfalls Bauwerk.
   *
   * **WAS DAS FÜR JEDE KÜNFTIGE ÄNDERUNG HEISST:** `art` ist ab jetzt nicht
   * mehr nur eine Lizenzaussage. Wer hier einen vierten Wert hinzufügt oder
   * eine Zuordnung verschiebt, verschiebt damit auch, wo die Auto-Kamera
   * steht — und das fällt niemandem auf, weil es keine Lizenzfrage ist.
   * Die Zuordnung ist darum in `derive/scene.ts` begründet und in
   * `test/p26-kamera-huelle.test.ts` je Wert einzeln festgehalten.
   *
   * **WARUM ÜBERHAUPT DIESES FELD und nicht `meta.nurBild`:** weil die Marke
   * `nurBild` das Stück aus `deriveAll` und damit aus SCHNITT und
   * AXONOMETRIE nähme. Der Weg, auf dem dieses Feld gesetzt wird
   * (`design.meshErstellen` form «daten»), ist zugleich der Weg der
   * IFC-Bestandsübernahme — an der echten `demohaus.ifc` 310 von 511
   * Bauteilen. Volle Begründung mit allen vier gemessenen Gründen in
   * `derive/scene.ts` bei `istEinrichtung`.
   */
  herkunft?: FremdHerkunft;
}

/**
 * Woher ein übernommenes Fremdstück stammt — und was daraus folgt. Siehe
 * `FreeMesh.herkunft` für die Begründung und `import/glb-lesen.ts`
 * `beurteileLizenz` für das Tor, das diese Werte vergibt.
 *
 * NICHT zu verwechseln mit `Herkunft` weiter oben: die belegt, woher eine
 * ZAHL kommt (Bürostandard oder Lehrheft, `Belegt<T>`). Beide in einen Typ zu
 * pressen wäre bequem und falsch — «owner-entscheid» ist keine Lizenzlage und
 * «cc0» keine Quelle für einen Achsabstand.
 */
export interface FremdHerkunft {
  /**
   * `eigen` — eigene oder beauftragte Daten (die IFC-Bestandsübernahme des
   *   Kunden, eine selbst vermessene Datei). Keine Fremdlizenz, keine
   *   Einschränkung.
   * `cc0` — frei, darf eingebaut UND ausgeliefert werden.
   * `hersteller` — darf im Bild vorkommen; die Datei verlässt den Rechner nicht.
   *
   * **WARUM `eigen` EXISTIERT — und zwar seit einem gemessenen Fehlgriff.**
   * Die erste Fassung dieses Tors kannte nur die zwei Lizenzlagen und wies
   * alles ohne Angabe ab. Gemessen am 17.09.2026 brach das VIER Proben in
   * drei fremden Dateien: die IFC-Bestandsübernahme
   * (`DesignWorkspace.tsx`, der `sonstige`-Zweig) legt Stützen, Türen und
   * Fenster ebenfalls als FreeMesh an — aus der Datei des KUNDEN, über
   * sein eigenes Gebäude. Das ist keine heruntergeladene Möbeldatei und
   * hat mit dem Owner-Entscheid vom 11.09. nichts zu tun.
   *
   * Das ist Muster 17: eine Gruppe gleichartiger Aufrufer ist fast nie
   * gleich entstanden. Drei Aufrufer von form «daten», drei Herkünfte —
   * IFC-Bestand (eigen), Objekt-Bibliothek (Lizenzfrage), Fremdeingang
   * (Lizenzfrage). Sie alle in «cc0 oder hersteller» zu pressen hiesse,
   * dem Kunden seine eigene Vermessung als Fremdlizenz zu etikettieren.
   */
  art: 'eigen' | 'cc0' | 'hersteller';
  /** Der Beleg im Klartext: «Poly Haven, CC0 1.0», «Muuto Digital Showroom, 17.09.2026». */
  beleg: string;
}

/** Hartes FreeMesh-Budget (E1) — Commands weisen Überschreitung ehrlich ab. */
export const FREEMESH_MAX_VERTICES = 4096;
export const FREEMESH_MAX_FACES = 8192;

/** Papierformate (ISO 216) für Plansätze + `Rolle` (v0.8.1/P13, Plotter-
 * Rollenformat 1600×594mm, `docs/V081-SPEZ.md` §7(d), `derive/blattlayout.ts`
 * `BLATT_FORMATE.Rolle`). */
export type SheetFormat = 'A0' | 'A1' | 'A2' | 'A3' | 'A4' | 'Rolle';

/** Eine platzierte Ansicht auf einem Blatt — Position in Papier-mm. */
export interface SheetPlacement {
  id: string;
  /** 'situationsplan' additiv (v0.7.0 E4/K10, Stream 3A): Parzellengrenze +
   *  Gebäude-Footprints, s. `derive/sheet.ts` `situationsplanInnerSvg` — kein
   *  `storeyId`/`section` nötig, nur `scale`/`x`/`y` wie bei `axo`.
   *
   *  'ansicht' additiv (B40, `docs/AUFTRAG-B40-ANSICHTEN-UND-MASSZAHLEN.md`
   *  §2): SIA 400 führt Fassadenansichten («Südansicht», «Ostansicht») in
   *  beiden Plansätzen als reguläre Blätter — bis hierher gab es dafür
   *  STRUKTURELL keinen Platz im Modell, nur einen wörtlichen Hinweistext
   *  in `derive/blattfuellung.ts`/`derive/baugesuch.ts`. Der Wert schliesst
   *  NUR diese Modell-Lücke: es gibt weder eine Zeichenableitung noch einen
   *  Weg, eine 'ansicht' zu PLATZIEREN (`publish.ansichtPlatzieren` weist
   *  sie bewusst mit `CommandError` ab, s. dort) — «Kanten, Blickrichtung,
   *  Massstabsregel» sind Owner-Entscheide, keine Modellfrage, und bleiben
   *  offen. `derive/sheet.ts` `placementInner()` liefert dafür bewusst eine
   *  leere Fläche statt geratener Geometrie.
   *
   *  'aufsicht' (Dachaufsicht/Sparrenlage, dieselbe SIA-400-Lücke) ist
   *  ABSICHTLICH NICHT ergänzt: offen ist, ob sie ein eigener Blatt-Typ
   *  ist oder eine Ansicht von oben (`view: 'ansicht'` mit einer noch
   *  fehlenden Blickrichtung) — eine Owner-Frage, nicht hier entschieden. */
  view: 'grundriss' | 'schnitt' | 'axo' | 'situationsplan' | 'ansicht';
  /** Grundriss: Quell-Geschoss. */
  storeyId?: string;
  /** Schnitt: Schnittlinie + Sichttiefe (Weltkoordinaten mm). */
  section?: { a: Pt; b: Pt; depth: Mm; lookLeft: boolean };
  /** Massstab, z.B. 100 für 1:100. */
  scale: number;
  /** Mittelpunkt der Zeichnung auf dem Blatt (Papier-mm, Ursprung links oben). */
  x: number;
  y: number;
  title?: string;
  /**
   * Umbau-Filter je Platzierung (ArchiCAD-Renofilter, RE-ARCHICAD A2):
   * fehlend = kombinierter Plan (heutiges Verhalten). 'abbruch' =
   * Abbruchplan (Bestand + Abbruch, Neubau ausgeblendet), 'neu' =
   * Neubauplan (Bestand + Neu, Abbruch ausgeblendet), 'bestand' = nur
   * Bestand. So entstehen die getrennten SIA-Umbau-Planläufe aus EINEM Modell.
   */
  umbau?: 'bestand' | 'abbruch' | 'neu';
  /** Themenplan-Name (RE-ARCHICAD A5): tönt die Platzierung nach den Regeln
   * aus settings.themen + zeichnet eine Legende. Fehlend = normaler Plan. */
  thema?: string;
}

/** Freier Textblock auf einem Blatt (Plakat-Titel, Konzepttexte). */
export interface SheetText {
  id: string;
  /** Ankerpunkt (Papier-mm, Ursprung links oben; y = Basislinie erste Zeile). */
  x: number;
  y: number;
  /** Inhalt; \n bricht Zeilen. */
  text: string;
  /** Schrifthöhe in Papier-mm. */
  size: number;
  /** Plakat-Titel-Stil (fett, gesperrt). */
  titel?: boolean;
}

/**
 * Bild-Slot auf einem Blatt (Render aufs Plakat). assetId=null ist ein
 * LEERER Slot — er hält den Platz, bis die HomeStation echte Renders liefert.
 */
export interface SheetImage {
  id: string;
  /** Linke obere Ecke (Papier-mm). */
  x: number;
  y: number;
  /** Breite in Papier-mm; Höhe folgt dem Bild-Seitenverhältnis (leer: 3:2). */
  w: number;
  assetId: string | null;
  title?: string;
}

/** Revisions-Eintrag eines Blatts (RE-ARCHICAD A7): Index A, B, C … */
export interface SheetRevision {
  index: string;
  text: string;
  /** Datum als Text (de-CH), z.B. «04.07.2026». */
  datum: string;
}

/** Änderungswolke (A7): markiert den geänderten Bereich in Papier-mm,
 * gebunden an einen Revisions-Index. */
export interface SheetWolke {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  revision: string;
}

/**
 * Plankopf-Textfelder (v0.8.0 P2) — additive Angaben für den Kopfstempel
 * eines Blatts (Inhalt, Plannummer, Disziplin, Geschoss-Code, gezeichnet/
 * geprüft von, Datum). Reine Datenhaltung dieser Runde: das eigentliche
 * Zeichnen des Kopfstempels folgt in einem separaten `derive/`-Paket, hier
 * nur die Guard-Phase — fehlend (kein `plankopf` am Blatt) bleibt das Bild
 * byte-identisch (Goldens-Guard, wie z.B. `fluegelTyp` bei `Opening`). Nur
 * über `publish.plankopfSetzen` gesetzt (Merge, s. dortigen Kommentar).
 */
export interface SheetPlankopf {
  inhalt?: string;
  planNummer?: string;
  disziplin?: string;
  geschossCode?: string;
  gezeichnet?: string;
  geprueft?: string;
  datum?: string;
}

/**
 * Blatt-Layout-Schalter (v0.8.0 P2) — additive boolesche Optionen
 * (Heftrand, Faltmarken, Wasserzeichen, Massstabsbalken, Nordpfeil). Wie bei
 * `SheetPlankopf`: reine Datenhaltung, das Zeichnen folgt separat in
 * `derive/` — fehlend = heutiges Bild bleibt byte-identisch (Goldens-Guard).
 * Nur über `publish.blattLayoutSetzen` gesetzt (Merge, s. dortigen
 * Kommentar).
 */
export interface SheetLayout {
  heftrand?: boolean;
  faltmarken?: boolean;
  wasserzeichen?: boolean;
  massstabsbalken?: boolean;
  nordpfeil?: boolean;
}

/** Planblatt (KosmoPublish) — Layout aus platzierten Ansichten. */
export interface Sheet extends Base {
  kind: 'sheet';
  name: string;
  format: SheetFormat;
  orientation: 'quer' | 'hoch';
  /** Sortierung im Plansatz. */
  index: number;
  placements: SheetPlacement[];
  texte?: SheetText[];
  bilder?: SheetImage[];
  /** Plan-Revisionen (A7): Einträge fürs Revisionsverzeichnis im Plankopf. */
  revisionen?: SheetRevision[];
  /** Änderungswolken (A7), je an einen Revisions-Index gebunden. */
  wolken?: SheetWolke[];
  /** Plankopf-Textfelder (v0.8.0 P2) — s. `SheetPlankopf`-Kommentar. */
  plankopf?: SheetPlankopf;
  /** Layout-Schalter (v0.8.0 P2) — s. `SheetLayout`-Kommentar. */
  layout?: SheetLayout;
}

/**
 * Eingebettetes Rasterbild (KosmoVis-Render, Foto). Base64 im Modell ist ein
 * bewusster Trade-off: so erben Undo, Yjs-Sync und .kosmo das Bild gratis —
 * gedacht für einige Plakat-Renders, nicht als Foto-Archiv.
 */
export interface ImageAsset extends Base {
  kind: 'imageasset';
  name: string;
  mime: string;
  /** Base64-Rohdaten (ohne data:-Präfix). */
  data: string;
  width?: number;
  height?: number;
}

/** Möbel (V2-F8): parametrisches Symbol + SIA-500-Bewegungsfläche. */
export interface Furniture extends Base {
  kind: 'furniture';
  storeyId: string;
  /** Katalogschlüssel, z.B. 'bett-doppel', 'wc', 'kuechenzeile'. */
  typ: string;
  /** Referenzpunkt (Mitte der Rückkante). */
  at: Pt;
  /** Rotation in Grad (0 = Bewegungsfläche zeigt +y). */
  rotationGrad: number;
  /**
   * **A4/23b (Abnahmezeile 23) — Körperhöhe dieses einen Stücks in mm,
   * ausdrücklich gesetzt.**
   *
   * DER ANLASS, wörtlich: «dann nur eine lampe, die hoehe davon stimmt
   * nicht». Der Katalog (`derive/moebel.ts` `MoebelTyp.h`) trägt EINE Höhe
   * je Typ, und die ist mit Beleg gewählt. Sie gilt aber für den Regelfall,
   * nicht für das Stück im Bild: eine Tischplatte kann 40 mm haben und die
   * daneben 60, eine Leuchte hängt mal so und mal so.
   *
   * FEHLT DAS FELD, GILT DER KATALOG — unverändert, Zahl für Zahl
   * (Golden-Guard). Gesetzt, ersetzt es `MoebelTyp.h`; `MoebelTyp.zUnten`
   * (die Unterkante) bleibt in JEDEM Fall die des Katalogs. Das ist eine
   * Entscheidung und keine Auslassung: `zUnten` sagt, WORAN das Stück
   * hängt — der Waschtisch an der Wand, die Tischplatte auf ihren Beinen —,
   * und das ändert eine Höhenangabe nicht mit.
   *
   * DIE HÖHE WIRD NICHT AUFS GESCHOSS GEKAPPT, aus demselben Grund wie beim
   * Schrank im Katalog (dort ausführlich): eine stille Kappung verschwiege
   * genau den Konflikt, den ein Bild zeigen soll.
   *
   * ES GIBT HEUTE KEINEN WEG ZURÜCK ZUM KATALOGWERT ausser dem, ihn wieder
   * einzutippen — `design.eigenschaftSetzen` kennt für Zahlenfelder keinen
   * «leer = entfernen»-Pfad, und ihn nur für dieses eine Feld zu erfinden
   * hiesse, zwei Bedeutungen desselben leeren Werts im selben Command zu
   * haben. Offene, benannte Grenze.
   */
  hoehe?: Mm;
  /**
   * **A14 / Abnahmezeile 14 — Unterkante DIESES Stuecks in mm ueber der
   * Geschoss-Oberkante.** Fehlt das Feld, gilt `MoebelTyp.zUnten` aus dem
   * Katalog — unveraendert, Zahl fuer Zahl.
   *
   * DER ANLASS steht im Katalog selbst, woertlich (`derive/moebel.ts`,
   * Oberflaechen-Ablage): «drei der zehn Typen (Fruechtekorb, Weinglas,
   * Schneidbrett) haben ein FESTES `zUnten` auf Tischplattenhoehe, weil
   * `Furniture` keine Instanz-Ueberschreibung fuer die Unterkante kennt».
   * Genau diese fehlende Ueberschreibung ist der Grund, warum die zweite
   * Haelfte von Abnahmezeile 14 — «was aufliegt, setzt sich auf die Flaeche
   * ab» — bis heute nicht gebaut werden KONNTE: Die Erkennung (A13) sagt
   * seit dem 17.09.2026, dass ein Stueck falsch steht; es gab nur keinen
   * Ort, an den man die Berichtigung haette schreiben koennen.
   *
   * WARUM DAS `MoebelTyp.zUnten`-Feld trotzdem bleibt und weiter zaehlt:
   * Der Katalog sagt, WORAN ein Stueck normalerweise haengt — der Waschtisch
   * an der Wand auf 700, der Fruechtekorb auf Tischhoehe. Das ist eine
   * Aussage ueber den TYP und bleibt richtig. Dieses Feld sagt, wo DIESES
   * eine Stueck wirklich liegt, nachdem jemand es abgesetzt hat. Beide
   * Aussagen sind wahr, und die zweite gewinnt nur, wenn es sie gibt.
   *
   * Zurueckgenommen wird es wie `hoehe`: `design.eigenschaftSetzen` mit
   * `null` entfernt das Feld und der Katalog gilt wieder.
   */
  zUnten?: Mm;
  /**
   * **A4/41b (Abnahmezeile 41) — Materialschlüssel dieses einen Stücks.**
   *
   * DER ANLASS, wörtlich: «tischtextur und stuhltextur der esstischmoebel
   * in diesem eichenholzfarbe nicht bitte...mach weiss kunstharz danke».
   * Gemessen am 12.09.: `design.eigenschaftSetzen` wies genau das ab —
   * «material ist bei furniture nicht aenderbar». Der Katalog trug das
   * Material, das Stück nicht.
   *
   * FEHLT DAS FELD, GILT DER KATALOG (`MoebelTyp.material`) — unverändert.
   * Derselbe Namensraum und derselbe Rückfall-Bauplan wie
   * `FreeMesh.material` weiter unten: ein Katalogschlüssel, den Schraffur,
   * Priorität und Textur schon kennen, kein roher Fremdname.
   *
   * Zurücknehmen: s. `hoehe` darüber, dieselbe benannte Grenze.
   */
  material?: string;
}

/**
 * A9 / Welle 3 (17.09.2026) — DIE LEUCHTE, und warum sie ein eigenes Bauteil
 * ist statt ein neunzehnter Moebeltyp.
 *
 * DER ANLASS SIND ACHT ZURUFE DES OWNERS an einem einzigen Bildtag
 * (`docs/RENDERPROJEKT-2026-09-10/60-ABNAHMELISTE.md`, Zeilen 17, 31, 42, 43,
 * 44, 45) — woertlich:
 *
 *   43  «die lampe ist gut, die darf ganz minimal an sein und laeuchten»
 *   43  «das licht ist nun nicht aktiv bei der lampe»
 *   17  «kannst du noch den lampenschirm etwas verlaengern und nach unten
 *        ziehen (die kappe bleibt natuerlich an der decke)»
 *   31  «und die kappe bei der lampe haengt noch runter, die sollte oben an
 *        der decke sein»
 *   31  «die kappe von der esstischlampe haengt immernoch unten»
 *   42  «und mach die schnur der leuchte aus dunklem textil»
 *   44  «dann ist aktuell die ganze lampe am laeuchten, scha das nur
 *        leuchtkoerper leuchtet»
 *   45  «und die lampenlicht beim tisch ist sichtbar, dieser noch in die
 *        lampe hinenverschieben»
 *
 * WARUM DER MOEBELKATALOG DAS NICHT TRAEGT — gemessen, nicht gemutmasst:
 * `derive/moebel.ts` fuehrt je Typ GENAU EINEN Quader (`MoebelTyp.b/t/h/
 * zUnten`), und sein eigener Eintrag `haengelampen-korpus` sagt das selbst:
 * «er wird von A9 sehr wahrscheinlich STRUKTURELL ersetzt (fixe Kappe +
 * beweglicher Schirm sind zwei Koerper, dieser Katalog kennt nur EINEN
 * Quader je Typ)». Die Zurufe 17 und 31 sind genau diese Trennung: EIN Teil
 * bleibt an der Decke, ein anderes wandert nach unten. Mit einem Quader ist
 * das nicht darstellbar — nicht schwierig, sondern unmoeglich.
 *
 * VIER KOERPER, und jeder traegt eine eigene Zeile der Abnahmeliste:
 *
 *   Kappe          fest an der Decke                Zeile 31
 *   Schnur         Kappe → Schirm, eigenes Material Zeile 42
 *   Schirm         beweglich, lichtdurchlaessig     Zeilen 17, 33
 *   Leuchtkoerper  das EINZIGE, was leuchtet        Zeilen 43, 44, 45
 *
 * DIE GEOMETRIE ERGIBT SICH AUS DEN FELDERN, sie steht nicht im Dokument:
 * die Kappe haengt an der Decke (oder an `deckeId`s Untersicht), die Schnur
 * ueberbrueckt `abhaengung`, der Schirm haengt darunter. Wer `abhaengung`
 * vergroessert, zieht Schirm UND Licht nach unten und laesst die Kappe
 * stehen — das ist Zeile 17 und Zeile 31 in EINER Zahl, und genau deshalb
 * sind es nicht zwei Zahlen.
 *
 * WO SIE IM BILD ANKOMMT: im ANHANG-KANAL (`deriveAllMitBilddetails`,
 * `derive/scene.ts`), NICHT in `deriveAll`. Der Grund ist nicht die Menge
 * (eine Leuchte kostet 192 Ecken, ein Beet 115'747), sondern die Wirkung:
 * `deriveAll` speist Schnitt, Axonometrie UND die automatische Kamera
 * (`derive/kamera.ts` laeuft ungefiltert ueber jeden Vertex). Eine Leuchte
 * dort verschoebe still den Kamerastandpunkt jedes Bildes — dieselbe
 * Begruendung, die `meta.nurBild` und die Begruenung tragen.
 */
export interface Leuchte extends Base {
  kind: 'leuchte';
  storeyId: string;
  /** Aufhaengepunkt im Grundriss (Mitte der Leuchte), Welt-mm. */
  at: Pt;
  /**
   * Zeile 43, erste Haelfte: brennt sie?
   *
   * EIN EIGENES FELD UND NICHT «staerke === 0», weil der Owner zweimal
   * verschiedene Dinge gerufen hat: «das licht ist nun nicht aktiv» ist das
   * Schalten, «die darf ganz minimal an sein» das Dosieren. Mit nur einer
   * Zahl verloere das Ausschalten den eingestellten Wert, und das naechste
   * Einschalten faenge wieder bei null an.
   */
  an: boolean;
  /**
   * Zeile 43, zweite Haelfte: Staerke 0..1 als ANTEIL der Regelleistung
   * (`derive/leuchte.ts` `LEUCHTE_REGEL_CANDELA`), nicht in Watt oder Lumen.
   *
   * WARUM EIN ANTEIL UND KEINE PHYSIKALISCHE EINHEIT: Der Zuruf lautet «ganz
   * minimal an», nicht «400 Lumen». Ein Anteil ist die Groesse, die der
   * Architekt am Bild nachzieht; die Umrechnung in die Einheit des jeweiligen
   * Betrachters (Candela in glTF `KHR_lights_punctual`, Intensitaet in
   * three.js) gehoert an die EINE Stelle, die sie kennt, und nicht ins
   * Dokument. 0 ist erlaubt und heisst «an, aber ohne Licht» — sichtbar
   * anders als `an: false`, weil der Leuchtkoerper dann immer noch nicht
   * glueht, die Lampe aber als eingeschaltet gilt.
   */
  staerke: number;
  /**
   * Zeilen 17 + 31 — DIE EINE ZAHL, DIE BEIDE ZURUFE TRAEGT: Laenge der
   * Schnur von der Kappe bis zur Oberkante des Schirms, in mm.
   *
   * «die kappe bleibt natuerlich an der decke» ist hier keine Regel, die
   * jemand einhalten muss, sondern eine Eigenschaft der Bauform: die Kappe
   * haengt an der Decke, weil die Ableitung sie dort ansetzt; `abhaengung`
   * kann sie gar nicht bewegen. Der Zuruf ist damit nicht «erfuellt», er ist
   * nicht mehr stellbar — und genau das wollte der Owner, der ihn zweimal
   * rufen musste.
   */
  abhaengung: Mm;
  /** Zeile 17 «den lampenschirm etwas verlaengern»: Hoehe des Schirms, mm. */
  schirmHoehe: Mm;
  /** Durchmesser des Schirms an seiner Unterkante, mm. */
  schirmDurchmesser: Mm;
  /**
   * Zeile 45 «die lampenlicht beim tisch ist sichtbar, dieser noch in die
   * lampe hinenverschieben».
   *
   * `true` = der Leuchtkoerper sitzt GANZ im Schirm, seine Unterkante liegt
   * ueber dessen Unterkante; man sieht ihn von der Seite und von oben nicht,
   * nur seinen Lichtkegel auf dem Tisch. `false` = er haengt unter dem
   * Schirmrand heraus und ist als heller Koerper im Bild.
   *
   * DAS IST EINE GEOMETRISCHE AUSSAGE, KEINE STILISTISCHE — sie laesst sich
   * am Bild zaehlen (wie viele Bildpunkte sind heller als der Schirm?), und
   * genau so ist sie gemessen.
   */
  quelleVersteckt: boolean;
  /**
   * Zeile 31, die genaue Hoehe: An DIESER Decke haengt sie — die Kappe sitzt
   * an deren Untersicht. Fehlt das Feld, sitzt sie an der Oberkante des
   * Geschosses.
   *
   * DASSELBE MUSTER WIE `Beam.deckeId` («schliesst buendig an diese
   * Deckenuntersicht an; leer = OK Geschoss»), und aus demselben Grund: eine
   * Leuchte weiss nicht von selbst, welche der Decken ueber ihr die ist, an
   * der sie haengt. Der Weg aus der Oberflaeche setzt es mit — dort ist die
   * Decke gerade ausgewaehlt.
   *
   * EHRLICHE GRENZE: zeigt die Id auf ein geloeschtes oder fremdes Bauteil,
   * faellt die Ableitung auf die Geschoss-Oberkante zurueck, statt zu werfen.
   * Eine Leuchte, die wegen einer verwaisten Referenz aus dem Bild
   * verschwaende, waere der schlechtere Fehler.
   */
  deckeId?: string;
  /**
   * Zeile 42 «und mach die schnur der leuchte aus dunklem textil» —
   * Materialschluessel der SCHNUR allein.
   *
   * WARUM DREI EIGENE MATERIALFELDER UND NICHT `meta.aussehen`: `meta` gilt
   * fuer das ganze Bauteil (`derive/gltf.ts` liest es an der BASIS-Entitaet),
   * und eine Leuchte hat vier Teile mit vier verschiedenen Oberflaechen. Der
   * Zuruf betrifft AUSDRUECKLICH nur die Schnur. Ein gemeinsames Feld waere
   * genau die Ungenauigkeit, gegen die die Zeile gerufen wurde.
   *
   * Fehlt das Feld, gilt der Regelwert aus `derive/leuchte.ts`. Der
   * Leuchtkoerper hat bewusst KEIN Feld: er ist das, was leuchtet (Zeile 44),
   * und ein waehlbares Material daran waere die Einladung, das Leuchten
   * wegzustellen.
   */
  schnurMaterial?: string;
  /** Materialschluessel des Schirms; fehlt = `lampenschirm` (durchscheinend). */
  schirmMaterial?: string;
  /** Materialschluessel der Kappe; fehlt = `metall-weiss-lackiert`. */
  kappeMaterial?: string;
}

/** Tür zwischen Zonen (ohne Wand): Punkt auf der gemeinsamen Kante. */
export interface ZonenTuer extends Base {
  kind: 'zonentuer';
  storeyId: string;
  at: Pt;
  breite: Mm;
}

/**
 * Terrainprofil (Vision A2): 3D-Polylinie übers Grundstück, projektglobal
 * (kein Geschoss). Der Schnitt projiziert die Stützpunkte auf seine Ebene —
 * gewachsen gestrichelt, neu ausgezogen (SIA 400 C.2.1). Kein DGM: ein
 * handgesetztes Profil je Zustand; swisstopo-Höhen sind HomeStation-Ausbau.
 */
export interface Terrain extends Base {
  kind: 'terrain';
  typ: 'gewachsen' | 'neu';
  /** Stützpunkte in Welt-mm, z über Projektnull; linear interpoliert. */
  punkte: { x: Mm; y: Mm; z: Mm }[];
}

/**
 * Aussparung/Durchbruch (Vision A3): Symbol + Menge am Wirt (Wand oder Decke)
 * — bewusst OHNE Geometrieschnitt. Der Werkplan zeigt Kreuz + Kote
 * (Hochbauzeichner-Konvention, Lehrheft Deckenkonstruktionen); Statik und
 * Haustechnik führen die Öffnung nach.
 *
 * `lage` und `tiefe` sind additive Felder (AUFTRAG-B39-AUSSPARUNGEN.md §4,
 * nachgemessene Lücke aus dem Lehrheft-Abgleich): beide OPTIONAL, ohne sie
 * bleibt eine Aussparung unverändert gültig und zeichnet byte-gleich weiter
 * (Golden-SVG-Vertrag). `'futterrohr'` erweitert `typ` um die dritte, im
 * Lehrheft benannte Art — reine Typ-Erweiterung ohne eigenen Kommando-Weg:
 * `design.aussparungSetzen` nimmt sie (Stand dieser Erweiterung) noch NICHT
 * entgegen, weil ein Futterrohr eigene Pflichtangaben braucht (Ø innen/aussen,
 * Werkstoff, Kote Achse), die keine der bestehenden Aussparungs-Felder
 * abdecken — offene Owner-Frage, s. Schlussbericht B39.
 */
export interface Aussparung extends Base {
  kind: 'aussparung';
  storeyId: string;
  /** Wirt-Element: Wand oder Decke. */
  hostId: string;
  typ: 'durchbruch' | 'schlitz' | 'futterrohr';
  /**
   * Bezug der Aussparung zum gezeichneten Geschoss (Lehrheft
   * Deckenkonstruktionen/Sanitäranlagen, AUFTRAG-B39-AUSSPARUNGEN.md §4;
   * Norm-Bestätigung AUS-DAR-01/02, `wissen/regelwissen/aussparungen.json`):
   * `decke` = in der Decke ÜBER dem Geschoss — `design.aussparungSetzen`
   * trägt sie seit B23 §2/B39 §3.1 deshalb ins darunterliegende Geschoss
   * ein (Blick nach oben); `boden` = in der Bodenkonstruktion — bleibt im
   * eigenen Geschoss. Fehlt das Feld, ändert sich nichts an der
   * bisherigen Ableitung (weiterhin `host.storeyId`) — additiv,
   * bestandssicher. Die STRICHART (gestrichelt für `decke`, ausgezogen für
   * `boden`) liest `derive/plan.ts` weiterhin nicht — das bleibt offen
   * (B39 §3.4, ausserhalb dieses Zugs gemessen).
   */
  lage?: 'decke' | 'boden';
  /** Wand-Wirt: Mitte in mm entlang der Achse ab Punkt a. */
  center?: Mm;
  /** Decken-Wirt: Mittelpunkt in Welt-mm. */
  at?: Pt;
  /** Öffnungsmass b × h (Wand: h vertikal; Decke: h = zweite Grundriss-Richtung). */
  breite: Mm;
  hoehe: Mm;
  /**
   * Schlitz-Tiefe in mm (Lehrheft-Pflichtangabe für `typ: 'schlitz'`, in
   * beiden Lagen — horizontal wie vertikal). Additiv; ein Schlitz ohne
   * `tiefe` bleibt gültig, nur unvollständig angegeben (unverändert zum
   * Stand vor B39).
   */
  tiefe?: Mm;
  /**
   * Wand: Unterkante über OK Boden — Eingabefeld. Die Kote im Werkplan
   * zeigt seit B23 §2 (`docs/AUFTRAG-B23-SIA400-SCHLUSSBATCH.md`) die
   * daraus abgeleitete OBERKANTE (`sill + hoehe`, SIA 400 Anhang B Fig.
   * 48/49 + Tabelle 6) — `sill` selbst bleibt die Unterkante, nur die
   * Beschriftung rechnet um.
   */
  sill?: Mm;
}

/**
 * Mangel (v0.6.3, `docs/V063-VOLLPROJEKT-KONZEPT.md` Abschnitt 4,
 * Lücken-Batch 5, Owner-Hauptaufgabe K22) — Mängel-Erfassung für die
 * Abschlussphase «Gebäudeabnahme». `ort` ist ein freier Lagetext (z.B. «Bad
 * 2.OG»), optional ergänzt um `storeyId` (Geschossbezug) und/oder `at`
 * (Welt-mm) — bewusst KEIN Bauteil-Host wie bei `Etikett`/`Aussparung`:
 * Mängel treffen oft mehrere Bauteile oder gar keins (z.B. «Handlauf fehlt
 * ganz»), ein starrer Bauteilbezug wäre zu eng. `gewerk` ist ein FREIES Feld
 * ohne Enum-Bindung — die App bietet die Bauablauf-Gewerke
 * (`MANGEL_GEWERK_VORSCHLAEGE`, `derive/bauablauf.ts`) nur als Vorschlagsliste
 * an, jeder Text bleibt gültig. `erfasstAm`/`behobenAm` sind vorformatierte
 * Datumsstrings (de-CH) — wie überall im Kernel NIE `Date.now()` im
 * Command-/Derive-Pfad, das Datum kommt als Parameter von der App.
 */
export interface Mangel extends Base {
  kind: 'mangel';
  ort: string;
  storeyId?: string;
  /** Optionaler Lagepunkt in Welt-mm (Plan-Marker sind bewusst NICHT gebaut,
   * s. `derive/abnahmeprotokoll.ts` Kommentar). Konsument: `ortText()` in
   * `derive/abnahmeprotokoll.ts` zeigt ihn in der Ort-Spalte des
   * Abnahmeprotokolls an, wenn gesetzt (MANGEL-AT-VORRAT, 08.09.2026 —
   * vorher NIRGENDS gelesen). */
  at?: Pt;
  beschreibung: string;
  gewerk: string;
  status: 'offen' | 'behoben';
  /** Vorformatiertes Erfassungsdatum (de-CH), Parameter des Commands. */
  erfasstAm: string;
  /** Vorformatiertes Behebungsdatum (de-CH); nur gesetzt, wenn status 'behoben'. */
  behobenAm?: string;
  /** Optionale Frist (freier Text/Datum) zur Behebung. */
  frist?: string;
}

/**
 * Kommentar (v0.8.3 E1, `docs/V083-SPEZ.md` §1, Island-§8-Freigabe §8-6) —
 * freie Notiz/Anmerkung am Projekt, unabhängig von Mängel-/Abnahme-Workflow
 * (`Mangel`). **Kein Bauteil-Host** (analog `Mangel`-Kommentar oben): ein
 * Kommentar kann sich auf kein, ein oder mehrere Bauteile beziehen — `at`
 * (Welt-mm-Punkt) plus optionale `storeyId` reichen für die Verortung, kein
 * starrer `entityId`-Bezug. `erstelltAm`/`erledigtAm` sind vorformatierte
 * Datumsstrings (de-CH) — wie überall im Kernel NIE `Date.now()` im
 * Command-/Derive-Pfad, das Datum kommt als Parameter von der App.
 */
export interface Kommentar extends Base {
  kind: 'kommentar';
  text: string;
  autor: string;
  at: Pt;
  storeyId?: string;
  status: 'offen' | 'erledigt';
  /** Vorformatiertes Erstelldatum (de-CH) — Parameter des Commands, NIE
   * `Date.now()` im Command-/Derive-Pfad (dieselbe Regel wie `Mangel.erfasstAm`). */
  erstelltAm: string;
  /** Vorformatiertes Erledigungsdatum (de-CH); nur gesetzt, wenn status 'erledigt'. */
  erledigtAm?: string;
}

/**
 * MassKette (v0.8.3 E2, `docs/V083-SPEZ.md` §2, Island-§8-Freigabe §8-7) —
 * ein echtes, vom Benutzer gesetztes Punkt-zu-Punkt-Mess-Ergebnis (mindestens
 * zwei Punkte, eine offene Kette). Unabhängig vom automatischen
 * `design.bemassungSetzen`-Anzeigepfad (`derive/dimensions.ts`), der nur die
 * Darstellung der assoziativen Aussenbemassung steuert — eine MassKette ist
 * eine eigenständige, im Doc gespeicherte Messung, kein Anzeige-Toggle.
 */
export interface MassKette extends Base {
  kind: 'masskette';
  storeyId: string;
  /** Mindestens zwei Punkte (Kettenanfang…-ende), Welt-mm. */
  punkte: Pt[];
}

/**
 * Höhenkote im GRUNDRISS (v0.9.4 P-KW, `docs/V094-SPEZ.md` §P-KW) — ein
 * PLATZIERBARES Mass-Element nach dem Muster `MassKette` (Orchestrator-
 * Entscheid V094-SPEZ «Der Entscheid, der die Version prägt»): der Werkplan
 * setzt Koten an bestimmte Punkte (OK Fertigboden, Podest, Absatz), nicht
 * flächendeckend — und nur so bleiben die ~17 Grundriss-Bestands-Goldens
 * byte-still (Daten-Guard). Die AUTOMATISCHEN Geschoss-Koten im Schnitt
 * (`DocSettings.bemassung.hoehenKoten`, `sectionInnerSvg`) bleiben davon
 * unberührt — dieselbe Trennung wie `MassKette` vs. `design.bemassungSetzen`.
 */
export interface Hoehenkote extends Base {
  kind: 'hoehenkote';
  storeyId: string;
  /** Lagepunkt in Welt-mm (wo das Koten-Dreieck sitzt). */
  at: Pt;
  /** Bezug nach SIA 400 Figur 18 (B9, v0.9.25) — zwei Norm-Achsen in EINEM
   * Wert: OK/UK (Spitze nach unten/oben, Label über/unter der Linie) ×
   * fertig/roh (LEERES/GEFÜLLTES Dreieck). Die Darstellung wird daraus
   * ABGELEITET, nie einzeln geführt: `gefuellt = bezug.endsWith('roh')`,
   * `spitzeHoch = bezug.startsWith('uk')` (`koteDreieckSvg`,
   * derive/plansvg.ts). Bis v0.9.24 stand hier die Füllungsregel verkehrt
   * («ok-fertig = gefüllt») und UK fehlte ganz — die Korrektur ist der
   * Golden-Zug B9 (`docs/AUFTRAG-B9-B10-KOTEN-UMBAU.md`). */
  bezug: 'ok-fertig' | 'ok-roh' | 'uk-fertig' | 'uk-roh';
  /** Expliziter Z-Wert in mm über Projektnull. Fehlt er, wird er aus dem
   * Geschoss aufgelöst: `Storey.elevation` (fertig) bzw. abzüglich des
   * Bodenaufbaus über der tragenden Schicht (roh) — exakt die Regel der
   * Schnitt-Koten (`bodenAufbauVon`, derive/plan.ts). UK-Koten (UK Sturz,
   * UK rohe Decke) haben keinen Geschoss-Default und tragen den Wert
   * praktisch immer explizit; ohne `wertMm` greift ehrlich dieselbe
   * Geschoss-Regel (kein erfundener Sturz-Wert). */
  wertMm?: number;
  /** Zusatz «= X m ü.M.» ans Label anhängen (aus `standort.hoeheM` + Kote,
   * kein Byte ohne gesetzten Standort — Guard-Prinzip, kein erfundener Wert). */
  zeigeUeberMeer?: boolean;
}

/**
 * SIA 400 Figur 18 (B9, v0.9.25) — DIE EINE Stelle, an der die zwei
 * Darstellungs-Merkmale aus `bezug` abgeleitet werden, zum Importieren
 * gedacht statt zum Nachschreiben (Nachzug P-L, `docs/V0925-SPEZ.md` §3 P-L,
 * Zusicherung C-17). Bis v0.9.24 führte die App in `PlanView.tsx` eine
 * EIGENE, verkehrte Kopie der Füllungsregel — genau die Art zweiter Quelle,
 * an der P-K bei den zwei Textstellen schon einmal ansetzen musste.
 *
 * Diese Funktion ist die EINE Quelle für Füllung/Spitzenrichtung. Der
 * Druckweg (`derive/plansvg.ts`, `koteDreieckSvg`) importiert sie seit dem
 * P-L-Nachzug ebenfalls — keine zweite Kopie mehr (s.
 * `hoehenkote-darstellung-waechter.test.ts`). Von den drei Bildschirm-Stellen
 * dieses Pakets importiert nur `PlanView.tsx` sie tatsächlich (das einzige
 * Overlay, das ein Dreieck zeichnet); `Inspector.tsx` und
 * `island/inhalte/zeichnen.tsx` zeigen nur Text bzw. bieten `bezug` als
 * Auswahl an, ohne selbst zu rendern. Wer eine weitere Kopie schreiben will,
 * importiert stattdessen von hier.
 */
export function hoehenkoteDarstellung(bezug: Hoehenkote['bezug']): { gefuellt: boolean; spitzeHoch: boolean } {
  return { gefuellt: bezug.endsWith('roh'), spitzeHoch: bezug.startsWith('uk') };
}

/**
 * Winkelmass (v0.9.4 P-KW) — misst VORHANDENE Geometrie über drei freie
 * Punkte: Scheitel + zwei Schenkelpunkte. MODELLIERUNGS-ENTSCHEID (Fable,
 * V094-SPEZ §P-KW Punkt 2): drei Punkte statt zweier Bauteil-Referenzen,
 * weil (a) das die verbreitete CAD-Form ist (ArchiCAD/AutoCAD: Scheitel +
 * zwei Strahlen), (b) das Mass wie die `MassKette` frei bleibt — es misst
 * auch Geometrie ohne Entity (DXF-Import, Skizzen) und stirbt nicht mit
 * einer gelöschten Wand (kein Referenz-Lebenszyklus), (c) die Schenkellänge
 * zugleich die ZEICHENLÄNGE der Schenkellinien im Plan bestimmt — der
 * Nutzer steuert die Symbolausdehnung mit denselben drei Punkten, ohne
 * Zusatzfelder. Der Winkel selbst ist deriviert (nie gespeichert): der
 * ungerichtete Winkel zwischen den Strahlen Scheitel→A und Scheitel→B,
 * 0–180° (`winkelGrad`, derive/plan.ts).
 */
export interface Winkelmass extends Base {
  kind: 'winkelmass';
  storeyId: string;
  /** Scheitelpunkt in Welt-mm. */
  scheitel: Pt;
  /** Punkt auf dem ersten Schenkel (Abstand zum Scheitel ≥ 10 mm). */
  schenkelA: Pt;
  /** Punkt auf dem zweiten Schenkel (Abstand zum Scheitel ≥ 10 mm). */
  schenkelB: Pt;
}

/**
 * Radialmass (v0.9.4 P-KW) — misst einen Radius über Mittelpunkt + Punkt
 * auf dem Bogen. MODELLIERUNGS-ENTSCHEID (Fable, wie `Winkelmass` oben):
 * zwei freie Punkte statt einer Bogen-Referenz — der Kern kennt keine
 * gebogenen Wände (Nicht-Ziel V094-SPEZ: «Radialmass misst vorhandene
 * Geometrie, erzeugt keine»), die einzigen Bögen (`PlanArc`, Türflügel)
 * sind derivierte Symbole ohne Entity-Identität; eine Referenz-Modellierung
 * hätte also NICHTS zu referenzieren. Der Radius ist deriviert
 * (dist(zentrum, amBogen)), `amBogen` bestimmt zugleich die Pfeilrichtung.
 */
export interface Radialmass extends Base {
  kind: 'radialmass';
  storeyId: string;
  /** Mittelpunkt des gemessenen Bogens/Kreises, Welt-mm. */
  zentrum: Pt;
  /** Punkt AUF dem Bogen (Radius = Abstand zum Zentrum, ≥ 10 mm) —
   * bestimmt zugleich, wohin der Radialpfeil zeigt. */
  amBogen: Pt;
}

/**
 * Annotation (v0.9.7 P-2D, `docs/V097-SPEZ.md` §2 P-2D) — freies Plan-
 * Zeichenwerkzeug: Text, Linienzug/Kreis, freie (nicht materialgebundene)
 * Schraffurfläche. Bis hierher gab es Text NUR auf Blättern
 * (`SheetText`/`publish.textSetzen`) und Schraffur NUR materialgebunden
 * (`derive/schraffur.ts`, Wand-/Deckenschichten) — kein Weg, eine Notiz oder
 * eine Bestandsergänzung direkt IM Grundriss zu setzen.
 *
 * FABLE-SCHNITT (V097-SPEZ «Der Schnitt — hier liegt die eigentliche
 * Anforderung»): EIN Entity-Kind für alle vier Formen, NICHT vier
 * Entity-Familien — genau die Klasse Fehler («ein Weg kann weniger als der
 * andere, obwohl beide dasselbe sein sollen»), die dieses Repo 2026 zehnmal
 * getroffen hat (ROADMAP 699 ×7, 702, 714, 717). `form.art` unterscheidet
 * die vier Gestalten; Ort (`storeyId`), Lebenszyklus (Undo/Yjs/`.kosmo`) und
 * die Plan-Zeichenstelle (`derive/plan.ts` EIN Guard-Block, `derive/
 * plansvg.ts` EIN `annotationSvg()`) sind für alle vier identisch — s. dort.
 *
 * Die vier Commands bleiben trotzdem GETRENNTE Einstiege
 * (`design.annotationTextSetzen`/`-LinienzugSetzen`/`-KreisSetzen`/
 * `-FlaecheSetzen`, `commands/design.ts`): der Kopfkommentar dieser Datei
 * verlangt «flach, ohne verschachtelte Unions (lokale Modelle!)» für jedes
 * Command-Schema, ein `form`-Parameter mit vier Formen wäre genau das. Die
 * EINHEIT liegt also im Modell/in der Ableitung/im Löschen/im Verschieben
 * (`design.annotationVerschieben` bewegt alle vier Formen über EINE
 * `switch(form.art)`-Funktion, `design.annotationLoeschen` kennt gar keinen
 * `art`-Unterschied mehr) — nicht im Erstellungs-Formular, wo die vier
 * Formen ohnehin unterschiedliche Pflichtfelder brauchen.
 */
export type AnnotationText = {
  art: 'text';
  /** Ankerpunkt, Welt-mm (Basislinie erste Zeile, wie `SheetText`). */
  at: Pt;
  /** Inhalt; `\n` bricht Zeilen (Muster `SheetText.text`). */
  text: string;
  /** Schrifthöhe in PAPIER-mm (K27-Grammatik, mit `scale` multipliziert im
   * Renderer) — fehlt = Default `ANNOTATION_TEXT_GROESSE_MM` (`derive/
   * plansvg.ts`). */
  groesseMm?: Mm;
};

/** Linienzug — offen (Standard) oder geschlossen (letzter Punkt schliesst
 * zum ersten); deckt sowohl «Linie» (2 Punkte) als auch «Polylinie»
 * (≥3 Punkte) ab, EIN Feld statt zweier Entity-Arten (Fable-Schnitt oben). */
export type AnnotationLinienzug = {
  art: 'linienzug';
  /** Mindestens zwei Punkte (Muster `MassKette.punkte`), Welt-mm. */
  punkte: Pt[];
  /** Letzter Punkt schliesst zum ersten (gestrichelte Skizzen brauchen das
   * nicht); fehlt/false = offener Zug wie eine Masskette. */
  geschlossen?: boolean;
};

export type AnnotationKreis = {
  art: 'kreis';
  /** Mittelpunkt, Welt-mm. */
  zentrum: Pt;
  /** Radius, mm, > 0. */
  radius: Mm;
};

/**
 * Freie Schraffurfläche — NICHT materialgebunden (der Unterschied zu
 * `derive/schraffur.ts`, das über einen Material-/Funktionsschlüssel
 * nachschlägt): Muster, Winkel und Abstand sind hier reine Nutzerangaben,
 * kein Katalog-Lookup. Bewusst nur die drei echten LINIEN-Muster
 * (`diagonal`/`kreuz`/`wellen`) — `voll`/`keine` aus `SchraffurMuster`
 * (`derive/schraffur.ts`) brauchen eine Flächen-`tint`-Farbe, die diese
 * Annotation nicht führt (freie Schraffur zeichnet Linien, keine Fläche
 * einfärben — sonst wäre `voll` von `keine` nicht zu unterscheiden).
 */
export type AnnotationSchraffurMuster = 'diagonal' | 'kreuz' | 'wellen';

export type AnnotationFlaeche = {
  art: 'flaeche';
  /** Geschlossenes Polygon, Welt-mm, mindestens drei Punkte. */
  outline: Pt[];
  schraffur: {
    muster: AnnotationSchraffurMuster;
    /** Winkel in Grad, frei wählbar (kein «folgt Bauteilachse» — eine freie
     * Fläche hat kein Bauteil, dessen Achse sie folgen könnte). */
    winkelGrad: number;
    /** Linienabstand in Papier-mm (K27-Grammatik, wie jedes Schraffurmass). */
    abstandMm: Mm;
  };
};

export type AnnotationForm = AnnotationText | AnnotationLinienzug | AnnotationKreis | AnnotationFlaeche;

export interface Annotation extends Base {
  kind: 'annotation';
  storeyId: string;
  form: AnnotationForm;
}

/**
 * Skizze (S2, `docs/KONZEPT-SKIZZE.md` §3 «Die Architektur: vier Schichten
 * statt einer» + §6 S2 «Die Skizze bleibt erhalten») — hält den rohen
 * Freihand-Zug fest, AUCH NACHDEM daraus Wände/Zonen entstanden sind. Heute
 * (vor S2) wird ein Strich sofort zu Wänden und ist danach weg (`apps/
 * kosmo-orbit/src/modules/design/sketch.ts` `fitStroke`/`fitStrokes` bleiben
 * reine, zustandslose Ableitungen — kein zweiter Speicherort für Geometrie).
 * Ohne diese Entity kann Kosmo nie sagen «der Schnitt daneben zeigt denselben
 * Bau» (die Information wäre verbraucht) und eine Deutung liesse sich nie
 * revidieren, ohne dass der Architekt neu zeichnet.
 *
 * `striche` sind die ROHEN Züge in Welt-mm, wie die Hand sie gezeichnet hat —
 * VOR jedem RDP-Fitting/Winkel-/Raster-Snap. `druck` ist bewusst optional
 * (anders als bei `Stroke.points` in `sketch.ts`, wo Druck immer vorliegt):
 * eine Skizze kann auch aus Maus/Trackpad, einem digitalisierten Foto oder
 * einem importierten Plan entstehen, die keinen Stiftdruck kennen (Owner-
 * Entscheid §1 «Eingabe»).
 *
 * `zeichnungsart: null` heisst «noch nicht gedeutet», NICHT «unbekannt für
 * immer» (Owner-Reihenfolge-Entscheid §1 «Grundriss zuerst, vollständig»,
 * §4 «Ohne Zeichnungsart ist keine Deutung möglich») — S3 füllt das Feld
 * regelbasiert, mit Rückfrage bei Unsicherheit. `sicherheit` ist bewusst
 * KEIN optionales Feld: «eine Deutung ohne ihren Sicherheitsgrad ist
 * gefährlich» (§3) — auch der Ausgangszustand vor jeder Deutung trägt
 * ehrlich `'unklar'`, nie eine Lücke. `deutungGrund` ist der Owner-Entscheid
 * «bei Unsicherheit sagen, dass er unsicher ist — und warum» (§1): jede
 * gesetzte Deutung, auch die Rückstufung auf `zeichnungsart: null`, nennt
 * ihren Grund im Klartext (`design.skizzeDeutungSetzen`).
 *
 * `erzeugte` ist die Rückverfolgung Skizze→Modell (§3 «Sie ist ausserdem die
 * einzige Möglichkeit, eine Deutung später zu revidieren, ohne dass der
 * Architekt neu zeichnet») — IDs von Entities, die aus dieser Skizze
 * entstanden sind. S2 baut nur das Feld und den Schreibpfad
 * (`design.skizzeDeutungSetzen`, optionaler `erzeugte`-Parameter); WER hier
 * hineinschreibt (die Vorschlag→Modell-Übernahme aus S1/S6), bleibt bewusst
 * ausserhalb dieses Postens — S2 liefert nur Serialisierung/Undo/Migration
 * (§6 S2).
 */
export type SkizzeZeichnungsart = 'grundriss' | 'schnitt' | 'ansicht' | 'axo' | 'perspektive';

export type SkizzeSicherheit = 'sicher' | 'vermutet' | 'unklar';

/** Ein Punkt im rohen Zug — Welt-mm, mit optionalem Stiftdruck. */
export interface SkizzePunkt {
  readonly x: Mm;
  readonly y: Mm;
  /** 0..1 — fehlt bei Eingabequellen ohne Drucksensor (Maus/Trackpad, Foto,
   * importierter Plan). */
  readonly druck?: number;
}

/** Ein roher Zug — die Punktfolge, wie die Hand sie gezeichnet hat. */
export interface SkizzeStrich {
  punkte: SkizzePunkt[];
}

export interface Skizze extends Base {
  kind: 'skizze';
  storeyId: string;
  striche: SkizzeStrich[];
  /** null = noch nicht gedeutet (s. Kopfkommentar). */
  zeichnungsart: SkizzeZeichnungsart | null;
  sicherheit: SkizzeSicherheit;
  deutungGrund: string;
  erzeugte: string[];
}

/**
 * Ein gezeichneter Strich IM Detail-Ausschnitt (v0.9.3 P-D2, `docs/
 * V093-SPEZ.md` §P-D2) — eigenes 2D-Primitiv, das AM `DetailMarker` hängt
 * (`DetailMarker.zeichnung`) statt am Grundriss.
 *
 * KOORDINATEN-WARNUNG (unmissverständlich, weil der häufigste Rechenfehler):
 * `von`/`bis` sind DETAIL-Koordinaten — also bereits im selben skalierten,
 * auf den Bereichs-Ursprung verschobenen System, das `deriveDetail` für
 * seine gefilterten Grundriss-Linien ausgibt (Faktor `1/massstab`, Ursprung
 * (0,0) = linke obere Ecke von `DetailMarker.a`/`.b`, s. `derive/detail.ts`
 * Kopfkommentar «Skalierung»). KEINE Welt-mm wie `DetailMarker.a`/`.b` oben —
 * wer hier Welt-mm einträgt, zeichnet ausserhalb des sichtbaren Ausschnitts
 * oder in falscher Grösse. Vorteil dieser Wahl: der Strich braucht keine
 * eigene Skalierungslogik und wandert automatisch korrekt mit, wenn
 * `deriveDetail` ihn unverändert (nur noch geklassifiziert) durchreicht —
 * anders als bei Welt-mm-Koordinaten, die bei jeder Ableitung neu durch
 * `massstab` geteilt werden müssten.
 */
export interface DetailStrich {
  id: string;
  /** Startpunkt, DETAIL-Koordinaten (s. Kopfkommentar oben). */
  von: Pt;
  /** Endpunkt, DETAIL-Koordinaten (s. Kopfkommentar oben). */
  bis: Pt;
  /** Freier Stift-Bezeichner (z.B. Linienart/Gewicht-Kürzel) — reine
   * Nutzdaten; die heutige read-only-Karte (`PublishWorkspace.tsx`,
   * TABU-Datei dieses Postens) zeichnet alle Striche fix mit
   * `stroke="currentColor"` und liest `stift` NICHT — steht für einen
   * späteren Interpreten (z.B. eine künftige Stift-Legende) bereit, ohne
   * dass dieser Posten die UI anfassen müsste. */
  stift?: string;
  /**
   * Optionale Text-Anmerkung, EINGEBETTET statt eigenem `DetailText[]`-Feld
   * (bewusste Entscheidung, hier begründet statt an einer separaten Stelle,
   * weil sie direkt an diesem Feld hängt): Der Dateikreis dieses Postens
   * kennt nur `design.detailStrichSetzen`/`-Loeschen` — KEIN eigenes
   * Text-Command. Ein zweites, unabhängiges Array (`DetailMarker.text?:
   * DetailText[]`) bräuchte eigene CRUD-Commands, sonst wäre ein Text-Eintrag
   * ein verwaistes Datum ohne Löschpfad (Widerspruch zu Sanktion 3 «ehrliche
   * Ablehnung statt stille Nulloperation» — hier: stiller Datenmüll). Als
   * Teil des Strichs teilt die Anmerkung dessen Lebenszyklus: löscht man den
   * Strich, verschwindet die Anmerkung ehrlich mit (kein stiller Rest), und
   * `detailStrichSetzen` kann Text mitsamt Linie in einem Aufruf pflegen.
   * Position ebenfalls DETAIL-Koordinaten (s. Kopfkommentar oben).
   */
  text?: { pos: Pt; inhalt: string };
}

/**
 * Detail-Marker (v0.9.2 P-D, `docs/V092-SPEZ.md` §P-D — Scope v1 BEWUSST
 * schmal; v0.9.3 P-D2, `docs/V093-SPEZ.md` §P-D2 — additiv um `zeichnung`
 * erweitert, s. dort) — markiert einen Ausschnitt-Bereich im Grundriss eines
 * Geschosses, der als eigener, feiner skalierter Detailplan gedacht ist
 * (Muster `Zone`/`Rampe`: `bereich` ist ein Rechteck über zwei Punkte
 * `a`/`b`, wie `Rampe.a`/`Rampe.b`, KEIN beliebiges Polygon). `massstab` ist
 * — wie `SheetPlacement.scale` (s. dort, «Massstab, z.B. 100 für 1:100») —
 * der Massstab-NENNER, z.B. 5 für 1:5; je kleiner die Zahl, desto stärker
 * vergrössert das Detail gegenüber dem 1:1-Weltmodell.
 *
 * V1-SCOPE-EHRLICHKEIT: Diese Entity ist reine GEOMETRIE + METADATEN, kein
 * Druck-Baustein. Der Marker erscheint NICHT im Plan-Grundriss (`derive/
 * plan.ts`/`derive/plansvg.ts` bleiben unangetastet — ein Marker-Symbol im
 * Druck wäre ein ZWEITER, eigenständiger Golden-Zug und ausdrücklich
 * Nicht-Ziel dieses Postens); die Ausschnitt-ABLEITUNG als reine Daten liefert
 * `derive/detail.ts` (`deriveDetail`), gelesen von der Publish-Station
 * (read-only-Voransicht) — das Aufziehen des Rechtecks direkt im PlanView
 * ist ausdrücklich NICHT Teil dieses Postens (baut der Hauptagent separat).
 */
export interface DetailMarker extends Base {
  kind: 'detail';
  storeyId: string;
  /** Erste Ecke des Ausschnitt-Rechtecks, Welt-mm (Muster `Rampe.a`). */
  a: Pt;
  /** Gegenüberliegende Ecke des Ausschnitt-Rechtecks, Welt-mm (Muster `Rampe.b`) —
   * a/b spannen ein zu den Achsen paralleles Rechteck auf (KEINE Rotation v1). */
  b: Pt;
  /** Massstab-Nenner, z.B. 5 für 1:5 (Muster `SheetPlacement.scale`), > 0. */
  massstab: number;
  name: string;
  /**
   * v0.9.3 P-D2 additiv: eigene 2D-Zeichnung IM Ausschnitt, in
   * DETAIL-Koordinaten (s. `DetailStrich`-Kopfkommentar — NICHT Welt-mm).
   * Fehlend/`undefined` = heutiges Verhalten unverändert (DATEN-GUARD,
   * Sanktion 3 V093-SPEZ) — `deriveDetail` liest dieses Feld additiv NACH
   * der bestehenden Grundriss-Filterung, ohne sie zu berühren.
   */
  zeichnung?: DetailStrich[];
}

/** Port-Typen im Render-Graphen (V1-P2): nur gleiche Typen verbinden sich.
 * `kameras` (Owner-Befund K20/A10): Auto-Kamera-Standpunkte, s. derive/kamera.ts. */
export type VisPortTyp = 'szene' | 'bild' | 'prompt' | 'zahl' | 'material' | 'kameras';

/** Ein Node im Render-Graphen. Typ-Katalog: derive/visgraph.ts. */
export interface VisNode {
  id: string;
  typ: string;
  /** Canvas-Position (freie Einheiten, kein Weltmass). */
  x: number;
  y: number;
  params: Record<string, string | number | boolean>;
  collapsed?: boolean;
}

/** Gerichtete Kante: fromPort (Ausgang) → toPort (Eingang). */
export interface VisEdge {
  id: string;
  from: string;
  fromPort: string;
  to: string;
  toPort: string;
}

/**
 * Render-Graph (V1-Finish P2) — der Blender-artige Node-Tree von KosmoVis.
 * NUR die Graph-Beschreibung lebt im Modell (Undo, Yjs, .kosmo); Job-Status
 * und Render-Bilder bleiben im Laufzeit-Store der App — nie Base64 durch
 * den Sync. Zyklen werden beim Verbinden abgelehnt (vis.verbinden).
 */
export interface VisGraph extends Base {
  kind: 'visgraph';
  name: string;
  nodes: VisNode[];
  edges: VisEdge[];
}

export type Entity =
  | Storey | GridAxis | Assembly | Wall | Slab | Opening | Zone | MassBody | Roof | Stair | Rampe | Sheet | Boundary | ImageAsset | Furniture | ZonenTuer | Terrain | Aussparung | Column | Beam | Etikett | VisGraph | FreeMesh | Mangel | Kommentar | MassKette | Gelaender
  // v0.9.2 P-P1 (V092-SPEZ §P-P1): additiv ans Ende, wie jede spätere Entity hier.
  | Profil
  // v0.9.2 P-D (V092-SPEZ §P-D): additiv ans Ende, wie jede spätere Entity hier.
  | DetailMarker
  // v0.9.4 P-KW (V094-SPEZ §P-KW): additiv ans Ende, wie jede spätere Entity hier.
  | Hoehenkote | Winkelmass | Radialmass
  // v0.9.7 P-2D (V097-SPEZ §2 P-2D): additiv ans Ende, wie jede spätere Entity hier.
  | Annotation
  // S2 (KONZEPT-SKIZZE.md §6): additiv ans Ende, wie jede spätere Entity hier.
  | Skizze
  // A9/Welle 3 (17.09.2026): additiv ans Ende, wie jede spaetere Entity hier.
  | Leuchte;

/**
 * Register ALLER vom Kernel geführten Entity-Arten (v0.9.6 P-MOL,
 * `docs/V096-SPEZ.md` §8 Zelle C-9 — Lücke, die eine gegnerische Prüfung
 * fand: `modell_lesen`/`@kosmo/ai` deckte nur 5 von 32 Arten ab, weil es
 * dafür bis hierher KEINE Laufzeit-Quelle gab — nur den reinen
 * Compile-Zeit-Union `Entity['kind']`, an dem sich weder ein Test noch ein
 * Werkzeug vollständig abarbeiten kann, ohne die Liste selbst noch einmal
 * abzutippen (die zweite Quelle, die genau diese Lücke unentdeckt liess).
 * `EntityKind` unten wird jetzt AUS diesem Array abgeleitet
 * (`(typeof ENTITY_KINDS)[number]`), NICHT umgekehrt — eine neue Entity-Art
 * gehört additiv HIER ans Ende (wie bei `Entity` selbst) UND in die
 * Union oben; verpasst man eines von beiden, bricht der Kompilierungs-Beweis
 * `_entityKindsMatchEntityUnion` weiter unten sofort, keine stille Drift.
 * Reihenfolge = Deklarationsreihenfolge der Interfaces oben, rein kosmetisch.
 */
export const ENTITY_KINDS = [
  'storey', 'grid', 'column', 'beam', 'etikett', 'profil', 'assembly', 'wall',
  'slab', 'opening', 'zone', 'stair', 'ramp', 'gelaender', 'roof', 'boundary',
  'mass', 'freemesh', 'sheet', 'imageasset', 'furniture', 'zonentuer',
  'terrain', 'aussparung', 'mangel', 'kommentar', 'masskette', 'hoehenkote',
  'winkelmass', 'radialmass', 'detail', 'visgraph',
  // v0.9.7 P-2D (V097-SPEZ §2 P-2D): additiv ans Ende.
  'annotation',
  // S2 (KONZEPT-SKIZZE.md §6): additiv ans Ende.
  'skizze',
  // A9/Welle 3 (17.09.2026): additiv ans Ende.
  'leuchte',
] as const;

export type EntityKind = (typeof ENTITY_KINDS)[number];

/**
 * Kompilierungs-Beweis (kein Laufzeit-Test nötig): `ENTITY_KINDS` und der
 * `Entity`-Union-Kind tragen EXAKT dieselbe Menge an Kinds, in BEIDEN
 * Richtungen geprüft. `_KindsExact<A, B>` wird `false`, sobald eine Seite
 * ein Kind trägt, das der anderen fehlt — die Zuweisung `true` an ein Feld
 * vom Typ `false` bricht dann den Typecheck GENAU HIER, statt dass die
 * Lücke erst später (oder nie) auffällt. Eine Entity ohne Eintrag in
 * `ENTITY_KINDS`, oder ein verwaister Eintrag in `ENTITY_KINDS` ohne
 * zugehörige Entity, macht `npm run typecheck` sofort rot.
 */
type _KindsExact<A extends string, B extends string> = [A] extends [B]
  ? [B] extends [A]
    ? true
    : false
  : false;
const _entityKindsMatchEntityUnion: _KindsExact<EntityKind, Entity['kind']> = true;
void _entityKindsMatchEntityUnion;
