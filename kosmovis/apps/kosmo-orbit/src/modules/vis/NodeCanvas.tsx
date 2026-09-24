import {
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
  type ReactNode,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  augeImModell,
  evaluiereGraph,
  HIMMEL_ARTEN,
  projektKameras,
  RENDER_PRESETS,
  renderPromptBausteine,
  VIS_KATEGORIE_HUE,
  VIS_NODE_KATALOG,
  VIS_STIMMUNGEN,
  type VisGraph,
  type VisKategorie,
  type VisNode,
  type VisPortTyp,
} from '@kosmo/kernel';
import { ansage, KButton, KField, KIcon, KInput, KSelect, KTooltip, melde, meldeFehler, useRollfokus, type KIconName } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import {
  abbrechenJob,
  aufnahmeAufsBlatt,
  AUFLOESUNGEN,
  bescheideBridgeCatch,
  BILDWERKZEUG_IDS,
  BILDWERKZEUG_TEXTE,
  BridgeHttpError,
  bildAufsBlatt,
  bridgeBase,
  formularZusatz,
  freigebenJob,
  fremdnahtSatz,
  holeJob,
  interiorFaehrt,
  istAuthFehler,
  kombiniertePrompt,
  istUeberDiesenWegBestellbar,
  KEINE_GEOMETRIE_HINWEIS,
  mappeJobStatus,
  QUALITAETSSTUFEN,
  renderBedienungAusParams,
  sendeGraphRenderAuftrag,
  szeneBauteileAnzahl,
  zeitschaetzungSekunden,
  zeitText,
} from './vis-jobs';
import {
  istZeitUeberschritten,
  memoKey,
  type Aufnahme,
  type NodeLauf,
  OFFENE_LAUF_STATUS,
  RENDER_TIMEOUT_MS_DEFAULT,
  useVisRuntime,
  waehleAufnahme,
  wartetAbholerLabel,
  wartetAbholerText,
} from './vis-runtime';
import { BridgeBild } from './BridgeBild';
import { zoomAmZeiger } from './knoten-zoom';
import { KuratierFlaeche } from './KuratierFlaeche';
import { quelleAusLauf, type KuratierKartenDaten, type KuratierQuelle } from './varianten-diff';
import './vis-visual.css';

/**
 * NodeCanvas (V1-Finish P2, W1-Neubau UI-KONZEPT-065 §5) — der Blender-artige
 * Node-Editor von KosmoVis. Eigenbau-SVG statt react-flow: jede Änderung läuft
 * als vis.*-Command (Undo, Yjs, Kosmo spricht Graphen). Drag lebt im lokalen
 * State und wird bei pointerup als EIN vis.nodeSchieben committet; Parameter
 * committen bei blur. Render nur auf «Ausführen» — nie automatisch.
 *
 * V1-Nachtkampagne (v0.6.7 Stream V1, Commit 1+2): Mehrfachauswahl +
 * Gruppen-Drag + Grid-Snap + Ausrichten, orthogonales Kanten-Routing und
 * echter Node-Kollaps kommen alle als lokaler Laufzeit-State/additive
 * vis.*-Commands dazu — kein bestehender E2E-Vertrag (Kantenzahlen, Overlap,
 * Testpunkt (30,30), Status-Texte, Minimap) wird angetastet.
 */

export const NODE_W = 200;
const PORT_ABSTAND = 20;
/** V1-Welle Commit 2 (Node-Kollaps): Port-Abstand im eingeklappten Zustand —
 * kompakter als PORT_ABSTAND; `portY()` wählt je nach `node.collapsed`. */
const PORT_ABSTAND_KOLLABIERT = 14;
const KOPF_H = 26;
/** Portanker sitzen 4px vom Kartenrand abgesetzt (W1 Massnahme 5). */
const PORT_ABSATZ = 4;
/** Zoom-Grenzen der Steuerleiste (W1 Massnahme 4). */
const ZOOM_MIN = 0.25;
const ZOOM_MAX = 2.5;
/** V1-Welle Commit 1: Grid-Snap-Raster in Node-Raum-Einheiten — deckt sich
 * mit dem sichtbaren 24px-Punktraster (`vis-raster`-Pattern unten). */
const RASTER = 24;

function snap24(v: number): number {
  return Math.round(v / RASTER) * RASTER;
}

/** K35 (Owner-Korrekturen 2026-07, S.14 «diese übersicht raus, die bringt
 * nichts»): die Minimap (Welle 3, v0.7.8 P6 Dock-Panel + PC1 Island-Overlay)
 * ist ERSATZLOS entfernt — Konstanten (`MINIMAP_W/H/KNOTEN_MIN`), Geometrie
 * (`berechneMinimapAnsicht`/`minimapZuNodeRaum`), `visMinimap`-Dock-Panel,
 * `vis-minimap-toggle`-Chrome und das Island-Overlay sind weg; der
 * Legende-Begleiter des Island-Overlays bleibt als eigenständige
 * Legende-Fläche unten links erhalten (Owner K36: «legende ist gut»).
 * `LEGENDE_W` trägt die bisherige Breite des gemeinsamen Stapels weiter. */
const LEGENDE_W = 160;

/**
 * W1 P-KURATIERDECKEL (ROADMAP «siebter Deckel»/1151, `tokens.ts` zEbene
 * `INSEL_BUEHNENKOPF` AUSGESCHLOSSEN-Eintrag): der Kuratier-Knopf
 * (`.vis-chrome-topright`) sass in derselben Fensterecke wie der GLOBAL
 * fixierte Insel-Einstellungs-Kreis (`island.css:1109-1120`,
 * `position:fixed; top:14px; right:14px`, `z-index:42`). GEMESSEN
 * (`getBoundingClientRect`/`elementFromPoint`, 1400×900/1180×820/1024×768):
 * der Kreis beansprucht wegen seiner 44×44px-Trefferfläche (`margin:-3px`
 * auf 38×38px sichtbar, `island.css:1046-1050`) an ALLEN DREI Grössen
 * IDENTISCH 55px vom rechten Fensterrand (14px Basiswert + 44px
 * Trefferfläche − 3px Margin-Ausgleich = 55, gegengemessen: 1400−1345=55,
 * 1180−1125=55, 1024−969=55). Der Knopf lag darunter VOLLSTÄNDIG
 * verdeckt (Überlappfläche 1344px² = seine gesamte Fläche); ein echter
 * Klick auf seine Mitte traf das `<path>` des Kreis-Icons, nie den Knopf.
 *
 * Kein z-index-Wert löst das: beide liegen im selben `#root`-Stacking-
 * Context (kein `createPortal`), UND `.vis-chrome-topright` ist zusätzlich
 * durch `.k-einblenden`s eigenen Stacking-Context gedeckelt
 * (`design.css:185-197`) — selbst ein Wert von 1000 änderte nichts, s.
 * `tokens.ts`s `AUSGESCHLOSSEN`-Kommentar. Der Kreis ist global und in
 * jeder Station gleich (`INSEL_BUEHNENKOPF`) — er weicht nicht aus, der
 * stationslokale Knopf tut es: ehrliche geometrische Lösung, Muster
 * `design.css:185-197` (Mehr…-Menü scrollt, BEVOR es die BodenDock-Pille
 * erreicht). Reserve = 55px (Kreis-Trefferfläche) + `--k-s3` (8px Abstand).
 * `right`-Verankerung bleibt robust, auch wenn der Knopf mit dem
 * Kuratier-Zähler breiter wird — er wächst dann nach LINKS, von der
 * Kreis-Zone weg, nie hinein.
 */
export const ISLAND_KREIS_RESERVE_PX = 55;

/**
 * **Der zweite Deckel, und warum die Loesung diesmal senkrecht ist.**
 *
 * Der Ausweich nach links (`ISLAND_KREIS_RESERVE_PX`, oben) hat den
 * Einstellungs-Kreis geloest — und ist am 03.09.2026 an einem NEUEN Nachbarn
 * gescheitert. `w1-p-kuratierdeckel.spec.ts` misst es selbst, an allen drei
 * Bildschirmgroessen, mit `document.elementFromPoint` auf der Knopfmitte:
 * getroffen wird `DIV[data-testid=island-kopf-zweitgruppe]`, nicht der Knopf.
 *
 * **Gemessen (03.09.2026, echte Seite, 1400x900 und 1024x768 — die Zahlen
 * unten sind die von 1400):**
 *
 * | Element | Kasten | rechter Abstand |
 * |---|---|---|
 * | Kuratier-Knopf | x 1295…1337, y 12…44 | 63 px |
 * | `.isl-kopf-zweitgruppe` (`position:fixed`, `z:42`) | x 1083.6…1334, y 14…60 | **66 px**, 250.4 px breit |
 * | `.isl-einstellungen-kreis` (`position:fixed`, `z:42`) | x 1345…1389, y 11…55 | 14 px |
 *
 * Die Zweitgruppe ist seit B82 auf vier Kinder gewachsen (`sync-toggle`,
 * `starter-guide-start`, `island-undo`, `app-version`) und reicht damit
 * 250 px weit nach links — genau ueber die Zone, in die der Knopf 2026-08
 * ausgewichen war. Die Knopfmitte liegt 84 px vom rechten Rand, die
 * Zweitgruppe deckt 66…316 px ab.
 *
 * **Warum nicht einfach weiter nach links.** Weil die Breite der Zweitgruppe
 * vom TEXT abhaengt: die Sync-Plakette zeigt «Sync live · 3» oder «Sync aus»,
 * je nach Zustand verschieden breit. Eine Reserve, die auf 316 px gesetzt
 * wird, ist am naechsten Zustandswechsel wieder falsch — dieselbe Bauform,
 * die schon einmal gehalten hat, bis sie es nicht mehr tat. **Die HOEHE ist
 * die stabile Groesse:** beide Kopf-Elemente sind aus 44-px-Trefferflaechen
 * gebaut (`§4.2`, `min-height: 44px`), und diese Messlatte ist eine Regel des
 * Hauses, keine Zufallszahl. Der Knopf weicht darum nach UNTEN aus, unter die
 * ganze Kopfzeile — dann ist die Breite der Nachbarn gleichgueltig.
 *
 * Die tiefere der beiden Unterkanten ist die der Zweitgruppe: `top:14px` +
 * 44 px Mindesthoehe + 2 x 1 px Rahmen = **60 px** (gemessen: y 14…60, exakt).
 * Der Kreis endet bei 55. Darunter `--k-s3` Abstand, wie beim ersten Ausweich.
 *
 * **Und der Riegel bleibt, wo er ist:** `w1-p-kuratierdeckel.spec.ts` prueft
 * das ERGEBNIS mit `elementFromPoint` und einem echten Klick, an drei
 * Groessen — waechst der naechste Nachbar nach unten statt nach links, faellt
 * das genauso auf wie diesmal. Diese Konstante ist gemessen, nicht geraten,
 * und sie hat eine Wache.
 */
export const INSEL_KOPFZEILE_UNTERKANTE_PX = 60;

/**
 * v0.8.8 / PA4 (`docs/V088-SPEZ.md` §2 D7/§3 E-Zeile, C-10) — Token-Brücke:
 * die sechs Port-Typ-Farben kommen jetzt aus `aura.css` (`--k-port-*`,
 * byte-gleiche Hex-Werte). `NodeCanvas.tsx` ist SVG (kein Canvas) — jede
 * Verwendung unten ist entweder ein SVG-`fill`/`stroke`-Attribut (native
 * `var()`-Unterstützung, Beweis: :1169 nutzte bereits `var(--k-accent)` in
 * genau diesem Ternary) oder eine CSS-Custom-Prop-Durchreichung
 * (`style={{ '--_farbe': PORT_FARBE[t] }}`, konsumiert in `aura.css`/
 * `vis-visual.css` via `var(--_farbe)`) — ein `var()`-String als Wert einer
 * weitergereichten Custom-Property löst CSS ganz normal verschachtelt auf,
 * kein Sonderfall nötig. Seit v0.8.9 E6 (Owner-Entscheid «K2 Ausgewogen»,
 * 19.07.2026) sind die Tokens NICHT mehr theme-invariant: das dunkle Theme
 * überschreibt fünf der sechs Werte auf ein ≥4.6:1-Kontrastband gegen
 * `--k-field` (s. `aura.css` `[data-theme='orbit']`-Block) — genau dafür
 * zahlt sich der `var()`-Kanal aus: ein Theme-Wechsel färbt Ports und
 * Legende ohne Redraw-Sonderweg um (Beweis: `e2e/vis-token.spec.ts`).
 */
const PORT_FARBE: Record<VisPortTyp, string> = {
  szene: 'var(--k-port-szene)',
  bild: 'var(--k-port-bild)',
  prompt: 'var(--k-port-prompt)',
  zahl: 'var(--k-port-zahl)',
  material: 'var(--k-port-material)',
  kameras: 'var(--k-port-kameras)',
};

/** Deutsche Kurznamen je Porttyp — für die Legende (nicht die Port-Labels,
 * die pro Node unterschiedlich heissen, z.B. «Wert» vs. «Geometrie-Treue»). */
const PORT_TYP_NAME: Record<VisPortTyp, string> = {
  szene: 'Szene',
  bild: 'Bild',
  prompt: 'Prompt',
  zahl: 'Zahl',
  material: 'Material',
  kameras: 'Kameras',
};

/** Ein KIcon je Kategorie (W1 Massnahme 1) — die Hue kommt aus dem Kernel-
 * Katalog (`VIS_KATEGORIE_HUE`), die Zeichenwahl ist reine UI-Entscheidung. */
const KATEGORIE_ICON: Record<VisKategorie, KIconName> = {
  quelle: 'ordner',
  wandler: 'stift',
  render: 'auge',
  ausgabe: 'dokument',
};

/**
 * A15 (17.09.2026) — der Abstand zwischen zwei Zeilen eines Node-Körpers.
 * KEINE Schätzung: `.vis-node-render-wrap` in `vis-visual.css` ist
 * `display: grid; gap: 6px`. Wer ihn dort ändert, ändert ihn hier mit —
 * `test/a15-render-knotenhoehe.test.tsx` rechnet mit genau dieser Zahl.
 */
export const ZEILEN_ABSTAND = 6;

/**
 * Eine Zeile des Render-Körpers: die Kennung, die sie im DOM trägt
 * (`data-zeile`), und ihre am laufenden Bild gemessene Höhe.
 *
 * `hLauf` ist die Höhe DERSELBEN Zeile, sobald am Knoten ein Render-Lauf
 * hängt — zwei Zeilen wachsen dann (der Bildplatz vom Streifen auf den vollen
 * Rahmen, die Knopfzeile um «Abbrechen»). Ohne dieses Feld hätte das Register
 * zwei schlechte Möglichkeiten: den Ruhezustand eintragen und beim Rendern
 * still abschneiden, oder den Laufzustand eintragen und einen frischen Knoten
 * um 124 px zu hoch machen — womit er wieder aus dem Ausschnitt fiele.
 */
export type Koerperzeile = {
  readonly id: string;
  readonly h: number;
  readonly hLauf?: number;
  /** Zeilen, die nur in EINEM Zustand erscheinen (heute genau eine: der
   *  Drehungs-Hinweis steht nur da, solange kein Himmel gewählt ist). Ihre
   *  Höhe ist im Register trotzdem reserviert — fehlt die Zeile, bleibt ein
   *  Stück Karte leer, was harmlos ist; wäre sie NICHT reserviert, schnitte
   *  sie ab, was es nicht ist. */
  readonly bedingt?: true;
};

/**
 * A15 · DAS ZEILENREGISTER DES RENDER-KÖRPERS — Nachfolger der einen Zahl
 * `render: 872`.
 *
 * WARUM ein Register und keine Zahl mehr: eine einzelne Zahl sagt nicht,
 * WORAUS sie besteht. Wer eine Zeile hinzufügt, sieht ihr nicht an, dass sie
 * zu klein geworden ist — der Körper schneidet still ab, und ein
 * abgeschnittener Knoten sieht aus wie ein fertiger. Genau das ist zweimal
 * passiert: erst lagen rund 93 px alten Inhalts ausserhalb des Rahmens, dann
 * war der geschätzte Zuschlag für die sechs Bedienelemente (+206) um mehr als
 * das Doppelte zu klein (gemessen: 416).
 *
 * WAS DAS REGISTER ERZWINGT: jede Zeile des Körpers trägt im DOM ein
 * `data-zeile="<id>"`. `test/a15-render-knotenhoehe.test.tsx` vergleicht die
 * gerenderten Kennungen mit diesem Register in BEIDE Richtungen — eine neue
 * Zeile ohne Eintrag ist rot, ein Eintrag ohne Zeile ebenso. Dieselbe Probe
 * hält zwei Budgets: die sechs Bedienelemente müssen in die untere Hälfte des
 * Fensters passen, und der ganze Knoten muss in einen 700 px hohen Ausschnitt
 * passen, sonst meldet B69 bei JEDEM Render-Knoten «liegt ausserhalb».
 *
 * ⚠️ A21 (17.09.2026) — BERICHTIGUNG an der Begründung des ersten Budgets,
 * nicht an seiner Zahl. Hier stand: «der neue Knoten wird mit seiner LINKEN
 * OBEREN Ecke auf die Sichtmitte gesetzt — unter ihm liegt also nur die halbe
 * Fensterhöhe». Das war richtig beschrieben und war genau der Strukturfehler
 * (Posten 1/16 in `docs/RENDERPROJEKT-2026-09-10/73-BEFUNDE-OHNE-BESITZER.md`):
 * am laufenden Bild gemessen ragte die Karte bei allen fünf geprüften
 * Fenstergrössen unten hinaus (130/130/180/196/40 px), und vier bis sieben der
 * 20 Bedien- und Anzeige-Elemente lagen unter dem Fensterrand. Seit A21 setzt
 * `vis-graph-aktionen.ts#nodeHinzufuegen` die MITTE des Knotens auf die
 * Sichtmitte; über und unter ihm liegt je die halbe Fensterhöhe, und die
 * tragende Bedingung heisst jetzt «der ganze Knoten passt ins Fenster» statt
 * «die sechs passen in die untere Hälfte». Das erste Budget ist damit die
 * STRENGERE der beiden Fragen — es bleibt stehen, weil es hält (gemessen 392
 * gegen 450 erlaubte px) und weil ein Budget, das mehr verlangt als nötig,
 * niemanden in die Irre führt. Wer es eines Tages lockern will, misst vorher
 * am Bild nach, ob die Karte noch ganz im Fenster liegt.
 *
 * WAS DAS REGISTER NICHT KANN: jsdom hat kein Layout — keine Probe dieser
 * Suite kann prüfen, ob eine EINZELNE Zahl unten stimmt. Sie muss am Browser
 * gemessen werden (Fenster 1400×900, frischer Render-Knoten, Rahmenbreite
 * 184 px); die Zahlen unten stammen aus genau dieser Messung vom 17.09.2026.
 * Was die Probe erzwingt, ist, dass niemand an dieser Messung VORBEI eine
 * Zeile einbaut.
 */
export const RENDER_ZEILEN: readonly Koerperzeile[] = [
  // Die sechs Bedienelemente der Abnahmeliste (Zeilen 4/50a/51/47/48/56)
  // stehen ZUERST — sie sind das einzige, was von einem frisch gesetzten
  // Knoten überhaupt im Fenster liegt.
  { id: 'bedienung-preset', h: 28 },
  { id: 'bedienung-aufloesung', h: 45 },
  { id: 'bedienung-qualitaet', h: 45 },
  { id: 'bedienung-himmel', h: 45 },
  { id: 'bedienung-drehung', h: 20 },
  { id: 'bedienung-bildwerkzeug', h: 45 },
  // Beim Lauf kommen «Abbrechen»/«Freigeben» dazu und die Zeile bricht um.
  { id: 'aktionen', h: 32, hLauf: 70 },
  // Der Klappknopf steht bewusst HIER und nicht am Fuss des Körpers: an
  // dieser Stelle liegt er beim frischen Knoten (Fenster 1400×900) noch im
  // Bild — am Fuss läge er bei y≈951 und wäre selbst nur durch Schieben zu
  // erreichen. Ein Klappknopf, den man nicht sieht, klappt nichts auf.
  { id: 'klapp', h: 20 },
  // Zwei Schalter nebeneinander brechen im 184 px schmalen Körper auf zwei
  // Zeilen um — gemessen 41, eingetragen 44. Jede Zeile, deren Umbruch am
  // Text hängt, trägt hier eine kleine Reserve: zu viel Reserve ist ein
  // Streifen leere Karte, zu wenig ist ein stiller Schnitt.
  { id: 'schalter', h: 44 },
  { id: 'prompt', h: 26 },
  // Ohne Lauf ein Streifen, mit Lauf der volle Rahmen: 110 px ist die feste
  // Höhe von `.vis-node-leerbild` (vis-visual.css) UND der Deckel, auf den
  // das fertige Bild gesetzt wird (s. `maxHeight` unten). Ohne diesen Deckel
  // hinge die Zeilenhöhe am Seitenverhältnis des gelieferten Bildes, und kein
  // Registereintrag wäre je richtig.
  { id: 'bild', h: 26, hLauf: 110 },
];

/**
 * Die Zeilen, die erst der Klappknopf zeigt — das Prompt-Formular und die
 * vier Erklärtexte. Auswahlregel: was der Architekt bei JEDEM Bild anfasst,
 * bleibt offen; was er einmal liest, klappt zu. Die Erklärtexte sind damit
 * nicht verschwunden (ein weggelassener Hinweis wäre eine Unwahrheit), sie
 * sind einen Klick entfernt.
 */
export const RENDER_ZEILEN_ZUSATZ: readonly Koerperzeile[] = [
  { id: 'zusatz-formular', h: 154 },
  // Die vier Hinweiszeilen tragen je EINE Zeile Reserve über dem gemessenen
  // Wert (58/35/35/35): ihr Text hängt am Zustand — ein anderes Bildwerkzeug
  // bringt einen anderen Hinweis, ein gewählter Himmel eine längere Zeile.
  // Reserve nach OBEN ist ein Stück leere Karte, Reserve nach unten wäre ein
  // stiller Schnitt.
  { id: 'zusatz-zeitschaetzung', h: 70 },
  { id: 'zusatz-himmel-hinweis', h: 47 },
  { id: 'zusatz-drehung-hinweis', h: 59, bedingt: true },
  { id: 'zusatz-bildwerkzeug-hinweis', h: 47 },
  { id: 'zusatz-ehrlichkeit', h: 106 },
];

/** Summe einer Zeilenfolge samt der Abstände ZWISCHEN ihren Zeilen.
 *  `mitLauf` nimmt für jede Zeile die Lauf-Höhe, wo es eine gibt. */
export function zeilenHoehe(zeilen: readonly Koerperzeile[], mitLauf = false): number {
  if (zeilen.length === 0) return 0;
  const h = zeilen.reduce((s, z) => s + (mitLauf && z.hLauf !== undefined ? z.hLauf : z.h), 0);
  return h + (zeilen.length - 1) * ZEILEN_ABSTAND;
}

/** Zuwachs des Render-Körpers, sobald ein Lauf am Knoten hängt. */
const RENDER_H_LAUF_ZUSATZ = zeilenHoehe(RENDER_ZEILEN, true) - zeilenHoehe(RENDER_ZEILEN);

/** Zuwachs, wenn `zeilen` zu einem bereits gefüllten Körper dazukommen: jede
 *  zusätzliche Zeile bringt ihre eigene Höhe UND einen weiteren Abstand mit. */
function zusatzHoehe(zeilen: readonly Koerperzeile[]): number {
  return zeilen.reduce((s, z) => s + z.h + ZEILEN_ABSTAND, 0);
}

/** Höhe des Inhaltsbereichs je Node-Typ (Canvas-Einheiten). `render` kommt
 * seit A15 aus dem Zeilenregister oben, nicht mehr aus einer Einzelzahl. */
const KOERPER_H: Record<string, number> = {
  modell: 22,
  material: 60,
  prompt: 56,
  stimmung: 90,
  kombinierer: 80,
  zahl: 38,
  // A2/16.09. hatte hier 872 stehen — am laufenden Bild gemessen und trotzdem
  // falsch benutzt: 872 px Körper ergeben einen 1016 px hohen Knoten, und das
  // Fenster ist 900 px hoch. Gemessen am 17.09. lagen VIER der sechs
  // Bedienelemente unter dem Fensterrand (Auflösung 904, Qualität 955, Himmel
  // 1058, Umgebung drehen 1123, Bildwerkzeug 1205 — Fenster 900). Nicht die
  // Zahl war das Problem, sondern dass der Inhalt nicht ins Fenster passt.
  // Seit A15 steht hier die Summe des Zeilenregisters; wer sie ändern will,
  // ändert eine Zeile, und die Probe rechnet die Summe selbst nach.
  render: zeilenHoehe(RENDER_ZEILEN),
  vergleich: 132,
  blatt: 38,
  referenz: 92,
  kamera: 54,
  aufnahme: 118,
};

/**
 * SK-V3: Zusatzhöhe, wenn ein geklappter Körper (`node-expand`) offen ist —
 * lokaler UI-State, NICHT im Doc.
 *
 * A15: EINE Zahl je Art statt einer globalen. Bis hierhin stand hier `= 70`
 * für alle, daneben eine zweite Liste `KLAPPBARE_TYPEN` mit denselben drei
 * Namen. Solange nur die drei Textkörper klappten, war das dieselbe Zahl; der
 * Render-Knoten klappt ein ganzes Formular samt Erklärtexten auf und hätte mit
 * 70 px genau den Fehler wiederholt, gegen den das Register oben steht.
 *
 * Die zweite Liste ist mit derselben Änderung ENTFALLEN: die Schlüssel dieses
 * Records SIND die klappbaren Arten. Zwei handgepflegte Listen, die dasselbe
 * meinen, sind in diesem Repo dreimal auseinandergelaufen — eine Art in der
 * einen und nicht in der anderen hätte einen Körper aufgeklappt und die Karte
 * nicht mitwachsen lassen.
 *
 * ⚠️ P16 (17.09.2026) — DER RENDER-KNOTEN STEHT HIER NICHT MEHR, und das ist
 * der ganze Umbau in einer Zeile. Bis P16 stand hier
 * `render: zusatzHoehe(RENDER_ZEILEN_ZUSATZ)` = 519 px. Am laufenden Bild
 * gemessen (eigener Bau, eigener kopfloser Chromium auf CDP 9293, fünf
 * Fenstergrössen) ergab das einen **1099 px hohen Knoten**, und bei JEDER der
 * fünf Grössen lagen **7 von 15 Bedienelementen ausserhalb des Fensters** —
 * das ganze Auftrags-Formular und beide Schalter.
 *
 * Das ist weder eine Frage der Platzierung noch eine der Reihenfolge, sondern
 * Arithmetik: das kleinste gemessene Fenster ist 720 px hoch, der Inhalt
 * braucht 1099. Die geschlossene Karte steht dort bei y 80 … 660, es bleiben
 * **60 px Luft nach unten** (die Karte wächst beim Aufklappen nur nach unten,
 * ihr `y` ändert sich nicht). Ein Klapp-Zusatz von 519 px passt da nicht, und
 * auch der kleinste sinnvolle Abschnitt — das Formular allein, 160 px —
 * passt nicht. Mehrere Klappknöpfe hätten den Befund verkleinert und nicht
 * behoben.
 *
 * Der Zusatz lebt seit P16 darum in einem BEIBLATT neben der Karte
 * (`RenderBeiblatt` unten), das sich am FENSTER bemisst statt an der Karte.
 * `RENDER_ZEILEN_ZUSATZ` bleibt Zeile für Zeile, was es war, und wird Zeile
 * für Zeile weiter geprüft — es bemisst jetzt das Beiblatt.
 *
 * Die Schlüssel dieses Records sind damit NICHT mehr «alle klappbaren Arten»,
 * sondern die Arten, deren Klapp-Zusatz die KARTE wachsen lässt. Wer eine
 * weitere Art klappbar macht, ohne sie hier einzutragen, bekommt ein Beiblatt
 * oder gar nichts — nie einen stillen Schnitt.
 */
const KOERPER_H_ZUSATZ_OFFEN: Record<string, number> = {
  kombinierer: 70,
  stimmung: 70,
  material: 70,
};

/**
 * P16 · DIE MASSE DES BEIBLATTS — alle vier Randreserven sind am laufenden
 * Bild gemessen, keine geraten.
 *
 * Die Vis-Station legt fixe Insel-Chrome ueber die Leinwand. Gemessen am
 * 17.09.2026 bei 1280x720 UND 1920x1080 (beide Male identisch, weil die
 * Inseln an den Raendern verankert sind und nicht mitwachsen):
 *
 *   oben    `island-kopf-zweitgruppe` reicht bis y=60      → 60 px
 *   links   `island-graph-root` x 14…100                   → 100 px
 *   rechts  `kosmo-orb-wurzel` endet 90 px vor dem Rand     → 90 px
 *           (`island-einstellungen-kreis` 55, `island-stimmung-root` 48 —
 *            die 90 decken alle drei)
 *   unten   `island-grundstreifen` beginnt 60 px vor dem Rand → 60 px
 *
 * Die obere Reserve ist dieselbe Zahl, die `INSEL_KOPFZEILE_UNTERKANTE_PX`
 * oben schon traegt — sie wird von dort genommen statt neu eingetippt.
 *
 * Bei 1280x720 bleibt damit ein Feld von 600 px Hoehe. Das Beiblatt misst
 * nominell 539 px (Register 519 + zweimal Polster) — es passt bei allen fuenf
 * gemessenen Groessen OHNE zu rollen; `maxHeight`/`overflowY` sind der Riegel
 * fuer noch kleinere Fenster, nicht der Normalfall.
 */
const BEIBLATT_POLSTER = 10;
const BEIBLATT_ABSTAND = 12;
const BEIBLATT_RESERVE_OBEN = INSEL_KOPFZEILE_UNTERKANTE_PX;
const BEIBLATT_RESERVE_LINKS = 100;
const BEIBLATT_RESERVE_RECHTS = 90;
const BEIBLATT_RESERVE_UNTEN = 60;
/** Inhaltsspalte GENAU so breit wie im Kartenkoerper (`foreignObject`-Breite
 *  `NODE_W - 16`) — die Hoehen in `RENDER_ZEILEN_ZUSATZ` sind bei dieser
 *  Breite gemessen. Ein breiteres Beiblatt haette sie alle ungueltig gemacht. */
const BEIBLATT_INHALT_W = NODE_W - 16;
export const BEIBLATT_W = BEIBLATT_INHALT_W + 2 * BEIBLATT_POLSTER + 2;
/** Nennhoehe fuer die Klemmrechnung — Obergrenze, nicht Zusicherung: faellt
 *  die bedingte Zeile weg, ist das Beiblatt kuerzer (ein Stueck leere Karte,
 *  nie ein Schnitt). `zusatzHoehe` rechnet je Zeile einen Abstand mit und ist
 *  damit die konservative Seite. */
export const BEIBLATT_H_NENN = zusatzHoehe(RENDER_ZEILEN_ZUSATZ) + 2 * BEIBLATT_POLSTER;
/** Ueber der Leinwand und der Legende (z 20), unter der Kuratier-Flaeche
 *  (z 35) und ihrem Knopf (z 36). */
const BEIBLATT_Z = 25;

/**
 * P16 — das Feld, in dem ein Beiblatt liegen darf: die Leinwand abzueglich der
 * vier gemessenen Insel-Reserven. EINE Stelle fuer die Rechnung, damit die
 * Probe die Zahlen nicht nachtippt (sonst prueft sie ihre eigene Kopie).
 */
export function beiblattFeld(flaeche: { w: number; h: number }): { links: number; rechts: number; oben: number; unten: number } {
  return {
    links: BEIBLATT_RESERVE_LINKS,
    rechts: flaeche.w - BEIBLATT_RESERVE_RECHTS,
    oben: BEIBLATT_RESERVE_OBEN,
    unten: flaeche.h - BEIBLATT_RESERVE_UNTEN,
  };
}

/**
 * P16 — wo das Beiblatt eines Knotens landet. Reine Rechnung, damit sie ohne
 * Browser pruefbar ist (`test/p16-beiblatt-im-fenster.test.ts`).
 *
 * Bevorzugt rechts neben der Karte; passt es dort nicht ganz ins Feld,
 * weicht es nach LINKS neben die Karte aus; passt es auch dort nicht, wird es
 * ins Feld geklemmt. Senkrecht: Oberkante an der Karte, dann ins Feld geklemmt.
 */
export function beiblattPlatz(
  knoten: { x: number; y: number },
  sicht: { cx: number; cy: number; scale: number },
  flaeche: { w: number; h: number },
): { links: number; oben: number; maxHoehe: number } {
  const schirmX = (x: number): number => flaeche.w / 2 + (x - sicht.cx) * sicht.scale;
  const schirmY = (y: number): number => flaeche.h / 2 + (y - sicht.cy) * sicht.scale;

  const { links: feldLinks, rechts: feldRechts, oben: feldOben, unten: feldUnten } = beiblattFeld(flaeche);

  const maxHoehe = Math.max(0, Math.min(BEIBLATT_H_NENN, feldUnten - feldOben));

  const rechtsDavon = schirmX(knoten.x + NODE_W) + BEIBLATT_ABSTAND;
  const linksDavon = schirmX(knoten.x) - BEIBLATT_ABSTAND - BEIBLATT_W;
  const links =
    rechtsDavon + BEIBLATT_W <= feldRechts
      ? rechtsDavon
      : linksDavon >= feldLinks
        ? linksDavon
        : klemme(rechtsDavon, feldLinks, Math.max(feldLinks, feldRechts - BEIBLATT_W));

  const oben = klemme(schirmY(knoten.y), feldOben, Math.max(feldOben, feldUnten - maxHoehe));
  return { links: klemme(links, feldLinks, Math.max(feldLinks, feldRechts - BEIBLATT_W)), oben, maxHoehe };
}

/** Basis-Nodehöhe eines Typs (ohne Klapp-Zusatz) — für Layout-Vorausberechnung
 * (Drei-Stimmungen-Zeilenabstand, Spiral-Platzsuche), die noch keine Node-ID hat. */
export function basisNodeHoehe(typ: string): number {
  const kat = VIS_NODE_KATALOG[typ];
  const ports = Math.max(kat?.inputs.length ?? 0, kat?.outputs.length ?? 0);
  return KOPF_H + 8 + ports * PORT_ABSTAND + (KOERPER_H[typ] ?? 30) + 10;
}

/** V1-Welle Commit 2: Höhe eines eingeklappten Nodes — nur Kopf + (komprimiert
 * gestapelte) Ports, kein Körper. Mindestens ein Port-Slot, auch ohne Ports. */
function kollabierteNodeHoehe(typ: string): number {
  const kat = VIS_NODE_KATALOG[typ];
  const ports = Math.max(kat?.inputs.length ?? 0, kat?.outputs.length ?? 0, 1);
  return KOPF_H + 14 + (ports - 1) * PORT_ABSTAND_KOLLABIERT + 12;
}

/** Y-Position des i-ten Ports (Eingang ODER Ausgang, gleiche Zählung) — im
 * eingeklappten Zustand komprimiert (`PORT_ABSTAND_KOLLABIERT`), sonst der
 * gewohnte `PORT_ABSTAND`. EINE Naht für `portPos()` UND das Render selbst
 * (V1-Welle Commit 2: Kanten bleiben beim Kollaps korrekt verbunden, weil
 * beide Stellen dieselbe Funktion rufen). */
function portY(n: VisNode, i: number): number {
  const abstand = n.collapsed ? PORT_ABSTAND_KOLLABIERT : PORT_ABSTAND;
  return KOPF_H + 14 + i * abstand;
}

/** Echte Nodehöhe inkl. eines offenen Klapptexts (W1 Massnahme 3a) ODER
 * (V1-Welle Commit 2) eingeklappt — `collapsed` gewinnt: ein Klapptext bleibt
 * dabei zu (kollabiert zeigt nie einen Körper). */
function nodeHoehe(n: VisNode, offen?: ReadonlySet<string>, hatLauf?: boolean): number {
  if (n.collapsed) return kollabierteNodeHoehe(n.typ);
  const zusatz = offen?.has(n.id) ? (KOERPER_H_ZUSATZ_OFFEN[n.typ] ?? 0) : 0;
  const lauf = hatLauf === true && n.typ === 'render' ? RENDER_H_LAUF_ZUSATZ : 0;
  return basisNodeHoehe(n.typ) + zusatz + lauf;
}

function portPos(n: VisNode, port: string, richtung: 'in' | 'out'): { x: number; y: number } {
  const kat = VIS_NODE_KATALOG[n.typ];
  const liste = richtung === 'in' ? (kat?.inputs ?? []) : (kat?.outputs ?? []);
  const i = Math.max(0, liste.findIndex((p) => p.name === port));
  return {
    x: n.x + (richtung === 'in' ? -PORT_ABSATZ : NODE_W + PORT_ABSATZ),
    y: n.y + portY(n, i),
  };
}

/** Trefferradius eines Ports in Canvas-Koordinaten — exakt der `r={11}` der
 *  transparenten Hit-Kreise, die Ein- und Ausgänge über ihren sichtbaren
 *  5px-Kreis legen (s. Ein-/Ausgänge-Blöcke unten). EINE Zahl für Render und
 *  Rettung: was der Nutzer treffen kann, ist auch das, was `eingangUnterPunkt`
 *  findet — nie ein grösserer, unsichtbarer Fangbereich.
 *  P-ZWEITKANTE Posten 5, s. `eingangUnterPunkt`. */
export const PORT_TREFFER_R = 11;

/**
 * P-ZWEITKANTE Posten 5 (`auftraege/von-homestation/auf-orbit-20260828-16.md`)
 * — welcher EINGANGS-Port liegt unter diesem Canvas-Punkt?
 *
 * Gebraucht wird das, weil eine abgebrochene Kanten-Geste (`pointercancel`)
 * ihr `pointerup` nie am Ziel-Port zustellt: der Ziel-Port-Handler
 * (`onPointerUp` am Hit-Kreis) läuft dann NICHT. Die zuletzt gemeldete
 * Zeigerposition kennt der Canvas aber (`pending.x/y`, fortgeschrieben vom
 * `onPointerMove` des SVG) — daraus lässt sich der Ziel-Port geometrisch
 * bestimmen, mit demselben Radius, den der Hit-Kreis hätte.
 *
 * Bewusst eng gefasst, damit daraus nie eine stille Falschverbindung wird
 * (genau der Fehler, den der `onPointerCancel`-Handler seinerzeit geschlossen
 * hat, s. Kommentar dort):
 * - der Quell-Node selbst ist ausgeschlossen (`ausserNodeId`),
 * - nur typgleiche Eingänge zählen (dieselbe Regel, die `vis.verbinden`
 *   kernelseitig durchsetzt — hier vorgezogen, damit gar nicht erst ein
 *   Command mit sicherem Fehlschlag abgesetzt wird),
 * - der NÄCHSTE Treffer gewinnt, und nur innerhalb `PORT_TREFFER_R`.
 * Liegt der Punkt auf leerer Fläche, kommt `null` zurück — dann bleibt es
 * beim Verwerfen samt Meldung.
 */
export function eingangUnterPunkt(
  nodes: readonly VisNode[],
  punkt: { x: number; y: number },
  quelle: { ausserNodeId: string; typ: VisPortTyp },
): { nodeId: string; port: string } | null {
  let bester: { nodeId: string; port: string; d2: number } | null = null;
  for (const n of nodes) {
    if (n.id === quelle.ausserNodeId) continue;
    const eingaenge = VIS_NODE_KATALOG[n.typ]?.inputs ?? [];
    for (let i = 0; i < eingaenge.length; i++) {
      const p = eingaenge[i]!;
      if (p.typ !== quelle.typ) continue;
      const dx = punkt.x - (n.x - PORT_ABSATZ);
      const dy = punkt.y - (n.y + portY(n, i));
      const d2 = dx * dx + dy * dy;
      if (d2 > PORT_TREFFER_R * PORT_TREFFER_R) continue;
      if (bester === null || d2 < bester.d2) bester = { nodeId: n.id, port: p.name, d2 };
    }
  }
  return bester ? { nodeId: bester.nodeId, port: bester.port } : null;
}

function klemme(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

/** Fit-Berechnung als eigene Funktion (W1 Massnahme 4) — sowohl der Mount-
 * Auto-Fit als auch der «Fit»-Knopf der Zoom-Steuerleiste rufen sie auf. */
function berechneFit(
  nodes: VisNode[],
  flaeche: { w: number; h: number },
): { cx: number; cy: number; scale: number } | null {
  if (nodes.length === 0) return null;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const n of nodes) {
    minX = Math.min(minX, n.x);
    minY = Math.min(minY, n.y);
    maxX = Math.max(maxX, n.x + NODE_W);
    maxY = Math.max(maxY, n.y + nodeHoehe(n));
  }
  const scale = Math.min(1, (flaeche.w - 80) / Math.max(1, maxX - minX), (flaeche.h - 80) / Math.max(1, maxY - minY));
  return { cx: (minX + maxX) / 2, cy: (minY + maxY) / 2, scale: klemme(scale, 0.35, ZOOM_MAX) };
}

export type VisRoutingModus = 'kurve' | 'ortho';

/** Kubische Bézier mit horizontalen Tangenten — kein Routing, ruhige Kurven
 * (Default, byte-identisch zum bisherigen Verhalten). */
function edgePfadKurve(a: { x: number; y: number }, b: { x: number; y: number }): string {
  const dx = Math.max(40, Math.abs(b.x - a.x) / 2);
  return `M ${a.x} ${a.y} C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`;
}

/** V1-Welle Commit 2: orthogonales («Manhattan») Routing — waagrecht/senkrecht
 * mit kleinen Eck-Radien (Q-Segmente statt scharfer Ecken). Nur L/Q, kein C —
 * der Umschalter (`vis-routing-toggle`) prüft das im E2E direkt am d-Attribut. */
function edgePfadOrtho(a: { x: number; y: number }, b: { x: number; y: number }): string {
  const RADIUS = 8;
  const midX = a.x + (b.x - a.x) / 2;
  if (Math.abs(b.y - a.y) < 0.5) {
    return `M ${a.x} ${a.y} L ${b.x} ${b.y}`;
  }
  const signY = b.y > a.y ? 1 : -1;
  const r = Math.max(0, Math.min(RADIUS, Math.abs(midX - a.x), Math.abs(b.x - midX), Math.abs(b.y - a.y) / 2));
  if (r < 0.5) {
    return `M ${a.x} ${a.y} L ${midX} ${a.y} L ${midX} ${b.y} L ${b.x} ${b.y}`;
  }
  return [
    `M ${a.x} ${a.y}`,
    `L ${midX - r} ${a.y}`,
    `Q ${midX} ${a.y} ${midX} ${a.y + signY * r}`,
    `L ${midX} ${b.y - signY * r}`,
    `Q ${midX} ${b.y} ${midX + r} ${b.y}`,
    `L ${b.x} ${b.y}`,
  ].join(' ');
}

/** EIN Weg für beide Routing-Modi (Default 'kurve' — alle Bestandsverträge
 * unverändert). Sowohl bestehende Kanten als auch die Pending-Kante rufen
 * diese Funktion mit demselben `routingModus`-State. */
function edgePfad(a: { x: number; y: number }, b: { x: number; y: number }, modus: VisRoutingModus = 'kurve'): string {
  return modus === 'ortho' ? edgePfadOrtho(a, b) : edgePfadKurve(a, b);
}

/**
 * Bild + QA-Zeile — der gemeinsame Kern des bestehenden Bildvergleichs
 * (`vergleich`-Node, ehemals als Inline-JSX dupliziert). V-H5 (Welle 3): die
 * Kuratier-Fläche nutzt exakt dieselbe Kachel für ihre Zweier-Vergleichsfläche
 * — «bestehenden Bildvergleich wiederverwenden», nicht neu erfinden.
 */
function BildKachel({
  jobId,
  bild,
  qa,
  alt,
}: {
  jobId: string;
  bild: string;
  qa?: { verdict: { passed: boolean; reason?: string | undefined } } | undefined;
  alt: string;
}) {
  // Auftrag auf-20260827-62 (Posten 2, `docs/auftraege-kosmovis/
  // auf-20260827-62.md`) — der Cloud-Worker liefert `qa.verdict.reason` seit
  // 27.08.2026 GENAU dann, wenn der Score besteht UND das Paarurteil
  // widerspricht (bestandener Score, verschwundenes Bauwerk — «geom_iou»
  // belohnt die Abwesenheit). Reine Weitergabe: keine eigene Schwelle, kein
  // Nachbau des Tors, kein gekürzter Text (Auflagen des Auftrags) — der Satz
  // erscheint NUR, wenn der Vertrag ihn mitliefert, und verschwindet mit ihm
  // wieder (kein stehender Fusstext, U10).
  const vorbehalt = qa?.verdict.reason;
  return (
    <div className="vis-bild-kachel">
      <BridgeBild jobId={jobId} imageName={bild} alt={alt} className="vis-img-full" />
      {qa && (
        <span
          className={`vis-bild-kachel-qa ${qa.verdict.passed ? 'vis-bild-kachel-qa--ok' : 'vis-bild-kachel-qa--fehl'}${vorbehalt ? ' vis-bild-kachel-qa--vorbehalt' : ''}`}
        >
          QA {qa.verdict.passed ? 'ok' : '✗'}
          {vorbehalt ? ' ⚠' : ''}
        </span>
      )}
      {/* U11: der Vorbehalt bleibt bei der Zahl, die er einschränkt — direkt
          unter der QA-Zeile, nicht auf einer anderen Seite/hinter einem Klapp-
          Text (U9b: erreicht den Benutzer, ohne dass er etwas aufklappt). */}
      {vorbehalt && (
        <span className="vis-bild-kachel-qa-vorbehalt" data-testid="vis-bild-kachel-qa-vorbehalt">
          {vorbehalt}
        </span>
      )}
    </div>
  );
}

export function NodeCanvas({
  graphId,
}: {
  graphId: string;
  /* v0.9.25 P-M: `onNodeHinzu` (Palette-Klick des Manuell-Modus) und
   * `islandModus` sind mit dem Manuell-Codepfad entfallen — NodeCanvas
   * rendert nur noch die Island-Fassung (Palette/Ausrichten/Zoom leben in
   * den GRAPH-/ANSICHT-Inseln, ferngesteuert über `vis-runtime.ts`s
   * `canvasBefehl`; die Legende ist das Overlay unten links). */
}) {
  const revision = useProject((s) => s.revision);
  void revision;
  const runCommand = useProject((s) => s.runCommand);
  const doc = useProject.getState().doc;
  const graph = doc.get<VisGraph>(graphId);
  // V-H5 (Welle 3): die Kuratier-Fläche startet zu — reines Overlay-UI,
  // kein Layout-Shift am Canvas selbst. (`vis-runtime.ts`s `paletteOffen`
  // hat seit P-M hier KEINEN Konsumenten mehr — sein letzter Leser war das
  // `visPalette`-Dock-Panel des Manuell-Modus; das Feld selbst bleibt im
  // Store, weil `dock-preset-anwendung.ts` es noch schreibt — Teil des
  // benannten Dock-Kern-Postens aus `docs/V0925-SPEZ.md` §3 P-M Schritt 3.)
  const [kuratierOffen, setKuratierOffen] = useState(false);
  const [vergleichAuswahl, setVergleichAuswahl] = useState<readonly string[]>([]);
  // PC1: Snap + Routing lebten hier als lokaler `useState` — für die
  // Insel-Fernsteuerung (ANSICHT-Insel liest/schreibt dieselben Felder,
  // ohne einen Closure-Pfad zu brauchen) nach `vis-runtime.ts` gehoben
  // (s. dortiger Kopfkommentar). Verhalten byte-gleich: gleiche Defaults
  // (`true`/`'kurve'`), gleiche Toggle-Semantik, nur die Quelle wechselt
  // von lokal auf den globalen Store. Die frühere Minimap-Übersteuerung
  // (`canvasMinimapManuell`) ist mit K35 mitsamt der Minimap entfallen.
  const snapAktiv = useVisRuntime((s) => s.canvasSnapAktiv);
  const routingModus = useVisRuntime((s) => s.canvasRoutingModus);
  const setCanvasAuswahlGroesse = useVisRuntime((s) => s.setCanvasAuswahlGroesse);
  const setCanvasSichtMitte = useVisRuntime((s) => s.setCanvasSichtMitte);
  const setCanvasSichtRechteck = useVisRuntime((s) => s.setCanvasSichtRechteck);
  const canvasBefehl = useVisRuntime((s) => s.canvasBefehl);
  const setAktiverGraphId = useVisRuntime((s) => s.setAktiverGraphId);

  const svgRef = useRef<SVGSVGElement>(null);
  const [view, setView] = useState({ cx: 560, cy: 300, scale: 1 });
  // P6-Review #6: Containergrösse als State (ResizeObserver) — die viewBox
  // aus getBoundingClientRect wäre beim Mount und nach Resize stale
  const [flaeche, setFlaeche] = useState({ w: 1200, h: 700 });
  const panning = useRef<{ x: number; y: number; cx: number; cy: number } | null>(null);
  // V1-Welle Commit 1: Mehrfachauswahl (lokaler Laufzeit-State, NICHT im Doc —
  // wie `offenerKlapptext`). Klick am Kopf = Einzelauswahl (ersetzt), Shift-
  // Klick = toggeln, Shift-Marquee auf leerer Fläche = Box-Auswahl, Escape leert.
  const [auswahl, setAuswahl] = useState<ReadonlySet<string>>(new Set());
  // P-g-Rollout (Tastatur-Rückgrat, `docs/UI-UX-2026-09-09-GRAPH-TASTATUR.md`):
  // die Nodes sind eine Gruppe gleichrangiger Elemente (Reihenfolge =
  // `graph.nodes`-Array-Index — KEIN echtes 2D-Zeilen/Spalten-Wandern, dieselbe
  // im `useRollfokus`-Kopfkommentar dokumentierte Vereinfachung wie in
  // `AssetWorkspace.tsx`). `anzahl` bleibt sicher bei `graph === undefined`
  // (Hook VOR dem frühen `return null` unten — ein zweiter Hook dort würde den
  // vom Lint-Deckel geduldeten `rules-of-hooks`-Fund auf sechs erhöhen).
  const rf = useRollfokus(graph?.nodes.length ?? 0, { ausrichtung: 'waagrecht' });
  // Nur EIN `.focus()`-DOM-Aufruf, wenn eine Pfeil-/Home-/End-Taste den
  // `aktiverIndex` bewegt hat — sonst würde der Fokus-Effekt unten auch beim
  // Erstmount (aktiverIndex startet bei 0) einen Node fokussieren, obwohl
  // niemand die Tastatur benutzt hat (Muster `AssetWorkspace.tsx:327`).
  const canvasTastaturBewegt = useRef(false);
  const [marquee, setMarquee] = useState<{ x0: number; y0: number; x1: number; y1: number } | null>(null);
  // Node-Drag (Einzel ODER Gruppe, W1 + V1-Welle Commit 1): lokale
  // Startpositionen ALLER bewegten Nodes + der laufende Pointer-Delta;
  // EIN vis.nodeSchieben je Node bei pointerup, bei Mehrfachauswahl in
  // EINER beginGroup/endGroup-Klammer (Muster VisWorkspace.tsx:126-188).
  const [drag, setDrag] = useState<{
    start: Record<string, { x: number; y: number }>;
    startPX: number;
    startPY: number;
    curPX: number;
    curPY: number;
  } | null>(null);
  const [pending, setPending] = useState<{ from: string; fromPort: string; typ: VisPortTyp; x: number; y: number } | null>(null);
  const [auswahlEdge, setAuswahlEdge] = useState<string | null>(null);
  // W1 Massnahme 5: Hover je Kante (CSS-Opazität steuert Trenn-✕ + Stroke).
  const [hoverEdge, setHoverEdge] = useState<string | null>(null);
  // SK-V3: offene Klapptexte je Node (lokaler UI-State, NICHT im Doc).
  const [offenerKlapptext, setOffenerKlapptext] = useState<ReadonlySet<string>>(new Set());
  const toggleKlapptext = (nodeId: string) =>
    setOffenerKlapptext((s) => {
      const next = new Set(s);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });

  const laeufe = useVisRuntime((s) => s.laeufe);
  // PC1: `setzeLauf` wandert mit der `ausfuehren()`-Extraktion nach
  // `vis-jobs.ts`s `sendeGraphRenderAuftrag` (dort direkt über
  // `useVisRuntime.getState()` genutzt) — hier nicht mehr nötig.
  const patchLauf = useVisRuntime((s) => s.patchLauf);
  // V-H5: Kuration lebt in vis-runtime (Laufzeit ≠ Modell) — Stern/Ablage
  // hängen am AKTUELLEN Bild eines Nodes, nie im Doc/Undo/Yjs.
  const kuration = useVisRuntime((s) => s.kuration);
  const markiereBild = useVisRuntime((s) => s.markiereBild);
  const verwerfeBild = useVisRuntime((s) => s.verwerfeBild);
  // v0.6.7 P0: Viewport-Aufnahmen (aufnahme-Node) — reine Laufzeit, wie `laeufe`.
  const aufnahmen = useVisRuntime((s) => s.aufnahmen);

  const auswertung = useMemo(
    () => (graph ? evaluiereGraph(doc, graph) : null),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- 'revision' erzwingt Neuberechnung bei Doc-Mutation (Bestandsmuster, s. DesignWorkspace.tsx bemassungPreset).
    [doc, graph, revision],
  );

  // Ein Poll für alle offenen Render-Jobs (2.5 s — wie die Einfach-Ansicht).
  // HS3: die Wartezustände (Freigabe/GPU-Leerlauf) zählen als offen; ein
  // lokaler Wächter schlägt bei Zeitüberschreitung ehrlich an, statt ewig
  // «rendert» zu zeigen.
  useEffect(() => {
    const t = setInterval(() => {
      const jetzt = Date.now();
      const limitMs =
        Number(localStorage.getItem('kosmo.render.timeoutMs')) || RENDER_TIMEOUT_MS_DEFAULT;
      const offen = Object.entries(useVisRuntime.getState().laeufe).filter(
        ([, l]) => (OFFENE_LAUF_STATUS as readonly string[]).includes(l.status),
      );
      for (const [nodeId, lauf] of offen) {
        // Timeout-Wächter ZUERST — unabhängig von einer jobId (HS3-Auflage 2):
        // ein hängender POST bleibt sonst ewig «gesendet» ohne jobId und würde
        // nie ablaufen.
        if (istZeitUeberschritten(lauf, jetzt, limitMs)) {
          patchLauf(nodeId, {
            status: 'zeitueberschreitung',
            fehler: 'Zeitüberschreitung — Bridge/GPU meldet sich nicht.',
          });
          continue;
        }
        // Ohne jobId (POST noch nicht bestätigt) gibt es nichts abzufragen.
        if (!lauf.jobId) continue;
        const jobId = lauf.jobId;
        void holeJob(jobId)
          .then((j) => {
            // P6-Review #7: eine verspätete Antwort darf einen NEUEN Lauf
            // (anderer/kein jobId) nie als «fertig» markieren
            if (useVisRuntime.getState().laeufe[nodeId]?.jobId !== jobId) return;
            // Fortschritt/Worker mitführen (HS3-Auflage 5) — der Node zeigt sie.
            // `wartetGrund` immer EXPLIZIT gesetzt (auf-20260901-70, Posten 1):
            // `j.message` trägt den Wartegrund nur, solange `queued`, und ist
            // in jedem anderen Zustand laut Vertragszusage gelöscht — würde
            // hier nur bedingt gespreadet, bliebe ein alter Grund über
            // `patchLauf`s Merge hinweg stehen, sobald der Job zu rendern
            // beginnt (dieselbe Falle wie bei den Feldern oben, nur ohne den
            // rettenden Bedingungs-Spread, weil `wartetGrund` bewusst
            // `| undefined` trägt).
            const marker: Partial<NodeLauf> = {
              ...(j.worker !== undefined ? { worker: j.worker } : {}),
              ...(j.progress !== undefined ? { progress: j.progress } : {}),
              wartetGrund: j.message,
            };
            if (j.result) {
              patchLauf(nodeId, {
                ...marker,
                status: 'fertig',
                bild: j.result.images[0] ?? '',
                qa: j.result.qa,
                // N4 — additiv, nur wenn der Worker es geschickt hat. Kein
                // Default: ein fehlendes Feld heisst «je Kamera nichts gesagt».
                ...(j.result.qa_je_kamera ? { qaJeKamera: j.result.qa_je_kamera } : {}),
              });
            } else if (j.status === 'error') {
              patchLauf(nodeId, { ...marker, status: 'fehler', fehler: 'Render fehlgeschlagen' });
            } else if (j.status === 'kein-render-worker') {
              // Matrix-C-1-Fund (v0.9.0): dieser ehrliche Worker-Status wurde
              // vorher von safeParse abgelehnt und hier still verschluckt —
              // jetzt landet die Worker-Begründung sichtbar am Node.
              patchLauf(nodeId, {
                ...marker,
                status: 'fehler',
                fehler: j.message ?? 'Kein Render-Worker auf der HomeStation aktiv (Checkpoint/ComfyUI prüfen).',
              });
            } else {
              patchLauf(nodeId, { ...marker, status: mappeJobStatus(j) });
            }
          })
          .catch((err) => {
            // KLEIN 8: Ein Auth-Fehler (401/403) heisst falscher/fehlender
            // Token — der wurde früher still verschluckt und tauchte erst mit
            // der Renderfrist als Zeitüberschreitung auf. Jetzt sofort ehrlich
            // am Node. (Die Frist stand hier als «10 min»; v0.9.21 P-E hat sie
            // auf 30 min gehoben — eine Zahl in einem Kommentar veraltet
            // lautlos, darum steht jetzt der Begriff statt des Werts. Gemeldet
            // hat es P-E selbst, ausserhalb seines Dateikreises.)
            // (Wieder gegen den aktuellen jobId prüfen — kein Fremd-Lauf.)
            if (useVisRuntime.getState().laeufe[nodeId]?.jobId !== jobId) return;
            if (istAuthFehler(err)) {
              patchLauf(nodeId, {
                status: 'fehler',
                fehler: 'Bridge lehnt ab — Token fehlt oder ist falsch (KosmoVis-Einstellungen).',
              });
            } else if (!(err instanceof TypeError) && !(err instanceof BridgeHttpError)) {
              // P-DONE (auftraege/von-homestation/auf-orbit-20260821-01.md
              // AUFTRAG 1, HomeStation-Messung 21.08.2026): die Bridge
              // ANTWORTET (200, `status:"done"`, ein `result`-Block) — aber
              // `parseJob`s `RenderJob.safeParse` lehnt den Datensatz ab
              // (fehlendes/umbenanntes Feld, dieselbe Fehlerklasse wie der
              // reale `kantenanteil`-Fund vor ROADMAP 1068). So eine Error
              // ist WEDER `TypeError` (Netzfehler, hier bewusst weiter
              // transient) NOCH `BridgeHttpError` (HTTP-Status, z.B. ein
              // 5xx, kann sich beim nächsten Poll erledigen) — sie war
              // bisher NICHT abgedeckt und fiel durch den Kommentar unten
              // lautlos durch. Der abgelehnte Datensatz ändert sich beim
              // nächsten Poll nicht: derselbe Bruch käme 237 Mal wieder,
              // exakt das gemessene Bild. Sofort ehrlich statt endlos
              // "rendert" — mit der echten Vertragsmeldung aus `parseJob`
              // (inkl. der `safeParse`-Issues, s. dortigen Kommentar).
              patchLauf(nodeId, {
                status: 'fehler',
                fehler: `Bridge-Antwort nicht verstanden — ${err instanceof Error ? err.message : String(err)}`,
              });
            }
            // Echte Netzfehler (TypeError) NICHT hochziehen: der nächste
            // Poll fasst nach — ein einmaliger Aussetzer soll den Lauf
            // nicht töten.
          });
      }
    }, 2500);
    return () => clearInterval(t);
  }, [patchLauf]);

  // Batch 6: useLayoutEffect statt useEffect — die Erstmessung muss VOR dem
  // ersten Browser-Paint sitzen. ResizeObserver feuert seinen ersten Callback
  // erst einen Tick später; bis dahin stand die viewBox auf dem 1200×700-
  // Platzhalter. Ein Klick/Drag, der in genau diesem Fenster startet (z.B.
  // E2E-Port-Drag), traf noch die Platzhalter-Koordinaten — der folgende
  // Resize-Snap auf die echte Grösse verschob Ports unter dem Zeiger weg,
  // der Down landete dadurch auf dem leeren Canvas statt auf dem Port und
  // startete Pan statt Pending-Edge (die eigentliche Ursache der Flakiness).
  useLayoutEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const r = svg.getBoundingClientRect();
    if (r.width > 0) setFlaeche({ w: r.width, h: r.height });
    const ro = new ResizeObserver((eintraege) => {
      const rect = eintraege[0]?.contentRect;
      if (rect && rect.width > 0) setFlaeche({ w: rect.width, h: rect.height });
    });
    ro.observe(svg);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const factor = Math.exp(-e.deltaY * 0.0012);
      // P-KNOTEN-ZOOM (09.09.2026): Zoom AM ZEIGER statt zur Flaechenmitte.
      // Vorher stand hier nur der Massstabswechsel — wer einen Knoten am
      // Rand vergroessern wollte, schob ihn damit aus dem Bild. Die Plansicht
      // macht es seit Langem richtig; der Knotengraph war die Ausnahme.
      // Der Anker wird HIER gemessen (das Rechteck ist nur im Ereignis
      // verfuegbar) und als Abstand zur Flaechenmitte weitergereicht; die
      // Rechnung selbst wohnt rein und geprueft in `knoten-zoom.ts`.
      const r = svg.getBoundingClientRect();
      const dx = e.clientX - r.left - r.width / 2;
      const dy = e.clientY - r.top - r.height / 2;
      setView((v) => zoomAmZeiger(v, factor, dx, dy, { min: ZOOM_MIN, max: ZOOM_MAX }));
    };
    svg.addEventListener('wheel', onWheel, { passive: false });
    return () => svg.removeEventListener('wheel', onWheel);
  }, []);

  // V1-Welle Commit 1: Escape leert die Mehrfachauswahl (global, wie die
  // Kurzbefehle-Registry — greift unabhängig davon, wo der Fokus gerade sitzt).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setAuswahl(new Set());
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // P-g-Rollout: der Hook selbst führt KEIN `.focus()` aus (s. dessen
  // Kopfkommentar «Trennung hält den Hook frei von jeder DOM-Kenntnis») —
  // das DOM-Fokussieren des Ziel-Nodes ist Sache dieses Konsumenten, über
  // `data-rf-index` am äusseren Node-`<g>` (Muster `AssetWorkspace.tsx:328`).
  useEffect(() => {
    if (!canvasTastaturBewegt.current) return;
    canvasTastaturBewegt.current = false;
    const ziel = svgRef.current?.querySelector<SVGGElement>(`[data-rf-index="${rf.aktiverIndex}"]`);
    ziel?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rf.aktiverIndex]);

  const toCanvas = (clientX: number, clientY: number) => {
    const rect = svgRef.current!.getBoundingClientRect();
    return {
      x: view.cx + (clientX - rect.left - rect.width / 2) / view.scale,
      y: view.cy + (clientY - rect.top - rect.height / 2) / view.scale,
    };
  };

  // P-HOOKS-ORDNUNG (09.09.2026): HIER stand `if (!graph) return null;` —
  // und darunter fuenf weitere `useEffect`. Das ist der Fehler, den
  // `react-hooks/rules-of-hooks` fuenfmal in dieser Datei meldet, und er ist
  // KEINE Formalie: verschwindet der Graph waehrend die Komponente steht
  // (Graph geloescht, Projekt gewechselt, Wurzel neu geladen), rendert React
  // beim naechsten Durchlauf WENIGER Hooks als beim vorigen und wirft
  // «Rendered fewer hooks than expected» — ein harter Abbruch, kein
  // Schoenheitsfehler.
  //
  // Der Rueckzug steht jetzt UNTEN, hinter dem letzten Hook (s. dort). Alles
  // dazwischen sind Funktionsdefinitionen, die erst beim Aufruf laufen; die
  // zwei, die `graph` wirklich anfassen (`ausrichtenAn`,
  // `vertikalVerteilen`), tragen ihre eigene Wache — sichtbar statt
  // stillschweigend, damit niemand sie fuer ueberfluessig haelt und entfernt.
  //
  // Der Kommentar bei `setCanvasSichtRechteck` weiter unten beschrieb diese
  // Lage als Bestandsmuster und verzichtete deswegen auf einen eigenen
  // sechsten Effekt. Der Verzicht ist damit gegenstandslos.

  const nodePos = (n: VisNode) => {
    const d = drag;
    const s = d?.start[n.id];
    if (!d || !s) return n;
    return { ...n, x: s.x + (d.curPX - d.startPX), y: s.y + (d.curPY - d.startPY) };
  };

  // SK-V1 (UI-Selbstkritik 0.6.4, Runde 2): beim Öffnen eines Graphen die
  // Ansicht auf die Nodes EINPASSEN — vorher startete der Canvas fix bei
  // (560, 300) und ein «Drei Stimmungen»-Graph lag halb ausserhalb, links
  // oben blieb eine grosse Leerfläche. Nur beim Mount (key={graphId} in
  // VisWorkspace remountet je Graph) — Nutzer-Pan/Zoom danach bleiben heilig.
  useEffect(() => {
    const g = useProject.getState().doc.get<VisGraph>(graphId);
    if (!g) return;
    // flaeche ist beim ersten Mount evtl. noch der Default (1200×700) — fürs
    // Einpassen gut genug, der ResizeObserver korrigiert die viewBox danach.
    const fit = berechneFit(g.nodes, flaeche);
    if (fit) setView(fit);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphId]);

  // PC1 (`docs/V084-SPEZ.md` §5 W2, C-15): spiegelt den aktiven Graphen in
  // `vis-runtime.ts` — die GRAPH-/STIMMUNG-/AUSTAUSCH-Insel-Inhalte
  // (`island/inhalte/*.tsx`) lesen NUR globale Stores (dasselbe Muster wie
  // `design/island/inhalte/*.tsx`), kein Prop-Pfad durch die Registry.
  useEffect(() => {
    setAktiverGraphId(graphId);
  }, [graphId, setAktiverGraphId]);

  // PC1: die ANSICHT-/GRAPH-Insel zeigt «Ausrichten» nur ab 2 ausgewählten
  // Nodes — dieselbe Regel wie die bisherige `visAusrichten`-Dock-Panel-
  // Sichtbarkeit (`auswahl.size >= 2`), hier nur als Zähler gespiegelt (die
  // volle Auswahl-Menge bleibt NodeCanvas-lokal, kein Store-Feld dafür nötig).
  useEffect(() => {
    setCanvasAuswahlGroesse(auswahl.size);
  }, [auswahl, setCanvasAuswahlGroesse]);

  // W3-a (`docs/ENTSCHEID-KNOTENPLATZ-2026-08-26.md` Weg c): spiegelt den
  // Sicht-Mittelpunkt (`view.cx/cy`) in `vis-runtime.ts`, Muster wie der
  // `canvasAuswahlGroesse`-Effekt direkt darüber. `nodeHinzufuegen()`
  // (`vis-graph-aktionen.ts`) liest den Wert als Spiral-Anker statt eines
  // festen Weltpunkts — die viewBox bildet ihn IMMER auf die Bildschirm-
  // mitte ab, unabhängig von Pan/Zoom/Fenstergrösse (Zeile 862ff. unten).
  // B69 (`docs/UI-UX-2026-09-07-B69-ENTSCHEID-HINWEIS.md` §3.2) — MITBEDIENT
  // hier statt in einem eigenen Effekt: ein neuer `useEffect` an dieser
  // Stelle wäre eine ZUSÄTZLICHE Verletzung von `react-hooks/rules-of-hooks`
  // (alle Hooks hier stehen NACH dem frühen `if (!graph) return null;` oben,
  // ein Bestandsmuster, das der Lint-Deckel `tools/lint-deckel-gate.mjs` als
  // 5 GEDULDETE Altfälle zählt — dieser Datei-Bereich zählt gemeinsam
  // hinein), ein Gate, das dieser Auftrag nicht anfassen darf. Statt eines
  // sechsten Verstosses spiegelt derselbe, bereits bestehende Effekt jetzt
  // ZUSÄTZLICH das ganze sichtbare Weltrechteck (nicht nur seine Mitte) —
  // dieselbe Rechnung wie die viewBox unten (Zeile ~1011ff.), hier vorweg
  // gezogen, damit `nodeHinzufuegen()` (`vis-graph-aktionen.ts`) entscheiden
  // kann, ob ein per Spiral-Suche gefundener Platz wirklich im Bild liegt.
  useEffect(() => {
    setCanvasSichtMitte({ x: view.cx, y: view.cy });
    const w = flaeche.w / view.scale;
    const h = flaeche.h / view.scale;
    setCanvasSichtRechteck({ x: view.cx - w / 2, y: view.cy - h / 2, b: w, h });
  }, [view.cx, view.cy, view.scale, flaeche.w, flaeche.h, setCanvasSichtMitte, setCanvasSichtRechteck]);

  /** Zoom-Steuerleiste (W1 Massnahme 4): ×1.25/÷1.25, geklemmt 0.25–2.5. */
  const zoomUm = (faktor: number) => setView((v) => ({ ...v, scale: klemme(v.scale * faktor, ZOOM_MIN, ZOOM_MAX) }));
  const zoomFit = () => {
    const g = useProject.getState().doc.get<VisGraph>(graphId);
    const fit = g ? berechneFit(g.nodes, flaeche) : null;
    if (fit) setView(fit);
  };

  const sicher = (fn: () => void) => {
    try {
      fn();
    } catch (err) {
      meldeFehler(err);
    }
  };

  /**
   * PC1 (`docs/V084-SPEZ.md` §5 W2, C-15/C-17): die eigentliche Sende-Logik
   * lebt jetzt in `vis-jobs.ts`s `sendeGraphRenderAuftrag` (Extraktion, EXAKT
   * dasselbe Verhalten wie bisher hier — s. dortigen Kommentar), damit die
   * neue AUSTAUSCH-Insel («Render senden») sie ohne Duplikat mitnutzen kann.
   * `environment` kommt aus der STIMMUNG-Insel (`renderStimmungPreset`,
   * `null` ausserhalb des Island-Modus → kein Feld im Job, byte-gleich).
   */
  const ausfuehren = (nodeId: string) => {
    const preset = useVisRuntime.getState().renderStimmungPreset;
    sendeGraphRenderAuftrag(graphId, nodeId, preset ? { preset } : undefined);
  };

  /** Wartenden Job freigeben (nur bei aktiver Freigabe-Pflicht). */
  const freigeben = (nodeId: string) => {
    const lauf = useVisRuntime.getState().laeufe[nodeId];
    if (!lauf?.jobId || !lauf.approvalToken) return;
    void freigebenJob(lauf.jobId, lauf.approvalToken)
      .then((j) => patchLauf(nodeId, { status: mappeJobStatus(j), wartetGrund: j.message }))
      .catch(bescheideBridgeCatch);
  };

  /** Kooperativer Abbruch eines wartenden/laufenden Jobs. */
  const abbrechen = (nodeId: string) => {
    const lauf = useVisRuntime.getState().laeufe[nodeId];
    if (!lauf?.jobId) return;
    void abbrechenJob(lauf.jobId)
      .then((j) => patchLauf(nodeId, { status: mappeJobStatus(j), wartetGrund: j.message }))
      .catch(bescheideBridgeCatch);
  };

  // V1-Welle Commit 2: ein laufender Render-Job (Status weder «bereit» noch
  // «fertig») lässt sich nicht kollabieren — ein ehrlicher Hinweis statt eines
  // stillen No-Ops (sonst verliert der Architekt den Job optisch aus den Augen).
  const kollapsBlockiert = (n: VisNode): boolean =>
    n.typ === 'render' && !!laeufe[n.id] && laeufe[n.id]!.status !== 'fertig';

  /**
   * P-g-Rollout: Pfeiltasten/Home/End wandern über `rf.onKeyDown` (bewegt nur
   * `rf.aktiverIndex`, der Fokus-Effekt oben holt sich den DOM-Knoten selbst).
   * Enter/Leertaste ruft DENSELBEN Auswahlweg wie ein Klick auf den Kopf-Griff
   * (dessen Einzelauswahl-Zweig, `:1440` — `setAuswahl(new Set([n.id]))`) —
   * kein zweiter Auswahl-Mechanismus. `ansage()` meldet NUR die Auswahl
   * (nicht jede Pfeilbewegung) — genau das, was der sichtbare Akzent-Rahmen
   * (`vis-node-ausgewaehlt-rahmen`) sehenden Nutzer:innen bereits zeigt.
   * Escape bleibt beim bestehenden globalen `window`-Listener (oben) — der
   * greift unabhängig vom Fokus und leert die Auswahl bereits.
   */
  const behandleNodeTaste = (e: ReactKeyboardEvent<SVGGElement>, index: number, n: VisNode, label: string) => {
    canvasTastaturBewegt.current = true;
    // `rf.onKeyDown` liest nur `.key`/`.preventDefault()` (jedes `KeyboardEvent`
    // trägt beides, unabhängig vom Element-Typ) — die Signatur in
    // `rollfokus.ts` ist auf `HTMLElement` typisiert, weil ihre bisherigen
    // Konsumenten (`AssetWorkspace.tsx` u.a.) alle HTML-Karten sind; der
    // Knotengraph ist SVG. Der Cast ändert kein Verhalten, nur den Typ.
    rf.onKeyDown(e as unknown as ReactKeyboardEvent<HTMLElement>, index);
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setAuswahl(new Set([n.id]));
      ansage(`${label} ausgewählt`);
    }
  };

  // V1-Welle Commit 1: Ausrichten/Verteilen — EIN beginGroup-Batch, wie
  // Gruppen-Drag (Muster VisWorkspace.tsx:126-188).
  const ausrichtenAn = (achse: 'x' | 'y') => {
    // P-HOOKS-ORDNUNG: eigene Wache, seit der Rueckzug unten steht. Sie kann
    // im Betrieb nicht greifen (ohne Graph rendert die Komponente nichts,
    // also gibt es keinen Knopf, der hier hereinfuehrt) — sie macht die
    // Voraussetzung nachpruefbar statt sie zu behaupten.
    if (!graph) return;
    const nodes = [...auswahl].map((id) => graph.nodes.find((n) => n.id === id)).filter((n): n is VisNode => !!n);
    if (nodes.length < 2) return;
    const ziel = Math.min(...nodes.map((n) => n[achse]));
    sicher(() => {
      const { history } = useProject.getState();
      history.beginGroup();
      try {
        for (const n of nodes) {
          if (n[achse] !== ziel) {
            runCommand('vis.nodeSchieben', {
              graphId,
              nodeId: n.id,
              x: achse === 'x' ? ziel : n.x,
              y: achse === 'y' ? ziel : n.y,
            });
          }
        }
      } finally {
        history.endGroup();
      }
    });
  };

  const vertikalVerteilen = () => {
    if (!graph) return; // P-HOOKS-ORDNUNG, s. `ausrichtenAn` oben
    const nodes = [...auswahl].map((id) => graph.nodes.find((n) => n.id === id)).filter((n): n is VisNode => !!n);
    if (nodes.length < 2) return;
    const sortiert = [...nodes].sort((a, b) => a.y - b.y);
    const oben = sortiert[0]!.y;
    const unten = sortiert[sortiert.length - 1]!.y;
    const schritt = sortiert.length > 1 ? (unten - oben) / (sortiert.length - 1) : 0;
    sicher(() => {
      const { history } = useProject.getState();
      history.beginGroup();
      try {
        sortiert.forEach((n, i) => {
          const zielY = Math.round(oben + i * schritt);
          if (n.y !== zielY) runCommand('vis.nodeSchieben', { graphId, nodeId: n.id, x: n.x, y: zielY });
        });
      } finally {
        history.endGroup();
      }
    });
  };

  // PC1 (`docs/V084-SPEZ.md` §5 W2, C-15): Fernauslöser aus der ANSICHT-/
  // GRAPH-Insel (`island/inhalte/ansicht.tsx`/`graph.tsx`) — die eigentliche
  // Zoom-/Ausrichten-Rechnung bleibt HIER (sie braucht `flaeche`/`graph`/
  // `auswahl`, die nicht sinnvoll in `vis-runtime.ts` leben, s. dortiger
  // Kopfkommentar). `nonce` erzwingt IMMER einen neuen Effekt-Lauf, auch bei
  // zweimal demselben Typ hintereinander (sonst würde ein identisches
  // `{typ, nonce}`-Objekt den Effekt beim zweiten Klick auf denselben Knopf
  // gar nicht erst feuern lassen). Ausserhalb des Island-Modus bleibt
  // `canvasBefehl` immer `null` (kein Aufrufer setzt es dort) — der Effekt
  // ist dann ein No-Op, byte-gleiches Bestandsverhalten.
  useEffect(() => {
    if (!canvasBefehl) return;
    switch (canvasBefehl.typ) {
      case 'zoom-in':
        zoomUm(1.25);
        return;
      case 'zoom-out':
        zoomUm(1 / 1.25);
        return;
      case 'zoom-fit':
        zoomFit();
        return;
      case 'ausrichten-x':
        ausrichtenAn('x');
        return;
      case 'ausrichten-y':
        ausrichtenAn('y');
        return;
      case 'vertikal-verteilen':
        vertikalVerteilen();
        return;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canvasBefehl]);

  // P-HOOKS-ORDNUNG (09.09.2026): DER frueher Rueckzug, jetzt an seiner
  // richtigen Stelle — hinter JEDEM Hook dieser Komponente. Ab hier folgen
  // nur noch Funktionsdefinitionen und die Ausgabe; ein `return null` kann
  // die Hook-Reihenfolge nicht mehr veraendern.
  //
  // Die fuenf Effekte darueber sind fuer einen fehlenden Graphen bereits
  // gefahrlos: der Einpass-Effekt holt sich den Graphen selbst und steigt bei
  // `!g` aus, die drei Spiegel-Effekte schreiben nur Werte, die ohne Graphen
  // ebenso stimmen (Auswahl leer, Sicht unveraendert), und der
  // Fernausloeser steigt bei `!canvasBefehl` aus. Geprueft, nicht angenommen —
  // `test/vis-node-canvas-hooks-ordnung.test.tsx` nimmt der stehenden
  // Komponente den Graphen weg und verlangt, dass sie das ueberlebt.
  if (!graph) return null;

  /**
   * Bild-Quelle eines Eingangs-Ports — entweder der Lauf eines verbundenen
   * Render-Nodes (Bridge-Artefakt) ODER (v0.6.7 P0) eine Viewport-Aufnahme:
   * derselbe `bild`-Port, zwei ehrlich unterschiedliche Herkünfte. `vergleich`/
   * `blatt` bleiben Bild-Port-kompatibel zu beiden (kein Sonderfall am Ziel-Node).
   */
  const bildQuelle = (nodeId: string, port: string): KuratierQuelle | null => {
    const e = graph.edges.find((e) => e.to === nodeId && e.toPort === port);
    if (!e) return null;
    const quellNode = graph.nodes.find((n) => n.id === e.from);
    if (quellNode?.typ === 'aufnahme') {
      const params = quellNode.params ?? {};
      const aufnahme = waehleAufnahme(aufnahmen, String(params['kamera'] ?? 'aktuell'));
      return aufnahme ? { dataUrl: aufnahme.dataUrl } : null;
    }
    // N4-Wache (ROADMAP 1340): dieselbe Abbildung wie `renderKarten` unten —
    // beide rufen jetzt `quelleAusLauf` statt das Literal je an ihrer Stelle
    // nachzubauen (`varianten-diff.ts` traegt die Probe dazu).
    return quelleAusLauf(laeufe[e.from]);
  };

  const rect = { w: 100 / view.scale, h: 100 / view.scale };
  void rect;

  // W1 Massnahme 5: Porttyp-Legende — nur die Typen, die im aktuellen Graphen
  // tatsächlich vorkommen (kein toter Ballast bei kleinen Graphen).
  const legendeTypen: VisPortTyp[] = [];
  {
    const gesehen = new Set<VisPortTyp>();
    for (const n of graph.nodes) {
      const k = VIS_NODE_KATALOG[n.typ];
      if (!k) continue;
      for (const p of [...k.inputs, ...k.outputs]) {
        if (!gesehen.has(p.typ)) {
          gesehen.add(p.typ);
          legendeTypen.push(p.typ);
        }
      }
    }
  }

  // V-H5 (Welle 3, Kuratier-Fläche) + H-36 (V1-Welle Commit 1): jeder
  // Render-Node mit einem fertigen Bild UND jeder aufnahme-Node mit einer
  // vorhandenen Viewport-Aufnahme ist eine Karte — dieselbe Kartenform, zwei
  // ehrlich unterschiedliche Bildquellen (wie `bildQuelle` es fürs Verbinden
  // schon kennt). Laufzeit bleibt in vis-runtime (`laeufe`/`aufnahmen`/
  // `kuration`) — der Graph selbst kennt nur den Node, nie das Bild. Der volle
  // `lauf.qa` (nicht nur `verdict.passed`) wandert mit — die Kuratierfläche
  // (Welle 1) leitet daraus Sterne-Bewertung + Parameter-Diff ab
  // (`varianten-diff.ts`), ohne ein neues Datenfeld im Doc/in vis-runtime.
  const renderKarten: KuratierKartenDaten[] = graph.nodes
    .filter((n) => n.typ === 'render')
    .map((n) => {
      // N4-Wache (ROADMAP 1340): dieselbe `quelleAusLauf`-Abbildung wie
      // `bildQuelle` oben — eine Stelle statt zwei gleichlautenden Literalen.
      const quelle = quelleAusLauf(laeufe[n.id]);
      if (!quelle) return null;
      const auftrag = auswertung?.renderAuftraege.get(n.id);
      return {
        node: n,
        quelle,
        kur: kuration[n.id] ?? { markiert: false, verworfen: false },
        ...(auftrag ? { auftrag } : {}),
      };
    })
    .filter((k): k is NonNullable<typeof k> => k !== null);
  const aufnahmeKarten: KuratierKartenDaten[] = graph.nodes
    .filter((n) => n.typ === 'aufnahme')
    .map((n) => {
      const gewaehlt = waehleAufnahme(aufnahmen, String((n.params ?? {})['kamera'] ?? 'aktuell'));
      if (!gewaehlt) return null;
      return {
        node: n,
        quelle: { dataUrl: gewaehlt.dataUrl },
        kur: kuration[n.id] ?? { markiert: false, verworfen: false },
      };
    })
    .filter((k): k is NonNullable<typeof k> => k !== null);
  const kuratierKarten: KuratierKartenDaten[] = [...renderKarten, ...aufnahmeKarten];
  const toggleVergleich = (nodeId: string) =>
    setVergleichAuswahl((sel) => {
      if (sel.includes(nodeId)) return sel.filter((id) => id !== nodeId);
      // Genau zwei zur Zeit — die dritte Wahl verdrängt die älteste (FIFO),
      // bleibt so immer sofort bedienbar statt stumm zu blockieren.
      const next = [...sel, nodeId];
      return next.length > 2 ? next.slice(next.length - 2) : next;
    });

  // v0.9.25 P-M: das frühere `visDockPanels`-Array (Palette/Ausrichten/
  // Legende als `DockFlaeche station="vis"`-Panels, v0.7.8 P6) ist mit dem
  // Manuell-Codepfad entfallen — Palette und Ausrichten leben als
  // GRAPH-Insel-Inhalte (`island/inhalte/graph.tsx`, Fernsteuerung über
  // `canvasBefehl` oben), die Legende als Overlay unten links (s. unten).

  return (
    <div className="vis-canvas-wrap">
    <svg
      ref={svgRef}
      data-testid="node-canvas"
      // PC1 (`docs/V084-SPEZ.md` §5 W2, Punkt 5): `data-cursor-zone="eigen"`
      // ist seit PA1 tot — `CursorEbene.tsx` versteckt sich seither NICHT
      // mehr über Zonen-Heuristiken (die «buggende Maus», D1), sondern folgt
      // ausschliesslich dem berechneten Cursor (`formVonComputedCursor`,
      // `CursorEbene.tsx:76-82`). Entfernt statt als Leiche stehen gelassen
      // (dieselbe Regel wie die tote PD2-Hinweis-Entfernung, v0.8.3 P10).
      className="vis-canvas-svg"
      viewBox={(() => {
        const w = flaeche.w / view.scale;
        const h = flaeche.h / view.scale;
        return `${view.cx - w / 2} ${view.cy - h / 2} ${w} ${h}`;
      })()}
      onPointerDown={(e) => {
        if (e.target === svgRef.current) {
          // V1-Welle Commit 1: Shift auf leerer Fläche startet die Marquee-
          // Auswahl statt zu pannen — OHNE Shift bleibt Pan exakt wie bisher
          // (Testpunkt (30,30) + bestehende Pan-Tests unangetastet).
          if (e.shiftKey) {
            const p = toCanvas(e.clientX, e.clientY);
            setMarquee({ x0: p.x, y0: p.y, x1: p.x, y1: p.y });
            (e.target as Element).setPointerCapture?.(e.pointerId);
            return;
          }
          panning.current = { x: e.clientX, y: e.clientY, cx: view.cx, cy: view.cy };
          // Wie beim Node-Kopf-Griff (unten) mit `?.` statt blankem Aufruf:
          // ein zwischenzeitlich schon abgelaufener/losgelassener Pointer
          // (schnelle Klickfolge, manche Browser/Webviews) darf das Pannen
          // selbst nicht zum Fehler machen — die Position tracken wir ohnehin
          // per pointermove auf dem svg, Capture ist nur die Komfort-Zugabe.
          (e.target as Element).setPointerCapture?.(e.pointerId);
          setAuswahlEdge(null);
        }
      }}
      onPointerMove={(e) => {
        // V1-Welle Commit 1: Marquee zuerst — sie schliesst Pan/Drag/Pending
        // in derselben Geste per Konstruktion aus (Pan startet gar nicht,
        // wenn Shift gedrückt war; s. onPointerDown).
        if (marquee) {
          const p = toCanvas(e.clientX, e.clientY);
          setMarquee({ ...marquee, x1: p.x, y1: p.y });
          return;
        }
        // F6 (v0.6.4): NICHT panning.current im setView-Updater lesen — die
        // Updater-Funktion läuft erst, wenn React den Zustand tatsächlich
        // verarbeitet, was NACH diesem Event liegen kann. Feuert dazwischen
        // ein pointerup (setzt panning.current = null, z.B. bei einem
        // schnellen Los-/Klick-Ende), lesen ältere, noch nicht geflushte
        // pointermove-Updater den Ref dann als null — «Cannot read properties
        // of null (reading 'cx')», von der KFehlerzone gefangen (Owner-Befund
        // F6: Absturz beim Pannen des Node-Trees). Fix: den Anfangszustand
        // JETZT in eine lokale Konstante schnappen — die bleibt stabil, ganz
        // gleich, was mit dem Ref danach passiert.
        const anfang = panning.current;
        if (anfang) {
          const { clientX, clientY } = e;
          setView((v) => ({
            ...v,
            cx: anfang.cx - (clientX - anfang.x) / view.scale,
            cy: anfang.cy - (clientY - anfang.y) / view.scale,
          }));
          return;
        }
        if (drag) {
          const p = toCanvas(e.clientX, e.clientY);
          setDrag({ ...drag, curPX: p.x, curPY: p.y });
        }
        if (pending) {
          const p = toCanvas(e.clientX, e.clientY);
          setPending({ ...pending, x: p.x, y: p.y });
        }
      }}
      onPointerUp={() => {
        panning.current = null;
        // V1-Welle Commit 1: Marquee committet die Box-Auswahl (jeder Node,
        // dessen Bounding-Box die Marquee-Box berührt — Overlap-Test).
        if (marquee) {
          const x0 = Math.min(marquee.x0, marquee.x1);
          const x1 = Math.max(marquee.x0, marquee.x1);
          const y0 = Math.min(marquee.y0, marquee.y1);
          const y1 = Math.max(marquee.y0, marquee.y1);
          const getroffen = graph.nodes
            .filter((n) => {
              const h = nodeHoehe(n, offenerKlapptext, !!laeufe[n.id]);
              return n.x < x1 && n.x + NODE_W > x0 && n.y < y1 && n.y + h > y0;
            })
            .map((n) => n.id);
          setAuswahl(new Set(getroffen));
          setMarquee(null);
        }
        // Gruppen-Drag-Commit: EIN Command je bewegtem Node, bei Mehrfach-
        // auswahl in EINER beginGroup/endGroup-Klammer — EIN Undo-Schritt
        // (Muster VisWorkspace.tsx:126-188). Grid-Snap (24px, Toggle
        // `vis-snap-toggle`) rundet die Zielposition, wenn aktiv. Ein reiner
        // Klick ohne Bewegung committet NICHTS (kein Leer-Patch fürs Undo).
        if (drag) {
          const bewegt = drag.curPX !== drag.startPX || drag.curPY !== drag.startPY;
          if (bewegt) {
            const dx = drag.curPX - drag.startPX;
            const dy = drag.curPY - drag.startPY;
            const eintraege = Object.entries(drag.start);
            sicher(() => {
              const { history } = useProject.getState();
              history.beginGroup();
              try {
                for (const [nodeId, s] of eintraege) {
                  const zielX = Math.round(s.x + dx);
                  const zielY = Math.round(s.y + dy);
                  runCommand('vis.nodeSchieben', {
                    graphId,
                    nodeId,
                    x: snapAktiv ? snap24(zielX) : zielX,
                    y: snapAktiv ? snap24(zielY) : zielY,
                  });
                }
              } finally {
                history.endGroup();
              }
            });
          }
          setDrag(null);
        }
        if (pending) setPending(null);
      }}
      // P-ZWEITKANTE (Messung `docs/MESSUNG-GRAPHSTART-ZWEITKANTE-2026-08-24.md`):
      // ein `pointercancel` (statt `pointerup`) beendet eine Geste, OHNE dass
      // sie je onPointerUp erreicht — bisher blieb `pending`/`drag`/`marquee`
      // dann stehen. Für einen abgebrochenen Kanten-Zug (`pending`) heisst
      // das konkret: der NÄCHSTE simple Klick auf einen beliebigen
      // Eingangs-Port (der eigene `onPointerUp`-Handler dort prüft nur
      // `if (!pending) return`) verbindet dann lautlos die ALTE, längst
      // abgebrochene Quelle mit einem Ziel, das der Nutzer nie angefasst
      // hat — kein Absturz, keine Fehlermeldung, einfach eine falsche Kante.
      // Deshalb hier dieselbe Aufräum-Logik wie `onPointerUp`, aber OHNE
      // Commit (eine abgebrochene Geste bestätigt nichts, s. `drag`/
      // `marquee` unten — nur verwerfen, nicht anwenden).
      //
      // P-KNOTENFELD Posten 7 (`auftraege/von-homestation/auf-orbit-
      // 20260825-07.md` Abschnitt 3, `docs/MESSUNG-GRAPHSTART-ZWEITKANTE-
      // 2026-08-24.md` Fund B): der HomeStation-Bericht rügt ausdrücklich
      // «OHNE jede Meldung an den Nutzer» — GENAU dieser Teil war nach der
      // P-ZWEITKANTE-Reparatur (ROADMAP 1096) noch offen. Die Reparatur von
      // damals räumt `pending` korrekt auf (verhindert die stille Fehl-
      // verbindung beim nächsten Klick, s. Kommentar oben), sagt dem Nutzer
      // aber nichts — ein abgebrochener Kanten-Zug sah exakt so aus wie ein
      // erfolgreicher: nichts passierte sichtbar. Die Kante selbst lässt
      // sich aus App-Code nicht zurückholen (der Browser beendet die Geste,
      // bevor die Zielkoordinaten je ankommen, s. Messung oben) — aber die
      // STILLE lässt sich beheben. Nur für den Kanten-Fall (`pending`), weil
      // nur dafür der Auftrag eine fehlende Meldung rügt — `drag`/`marquee`
      // brechen ohnehin sichtbar ab (der Node bleibt einfach stehen, kein
      // Rätsel für den Nutzer).
      //
      // P-ZWEITKANTE Posten 5 (`auftraege/von-homestation/auf-orbit-
      // 20260828-16.md`, Block A): bis hierhin blieb es beim Verwerfen +
      // Melden — die Kante selbst kam NICHT zurueck, der Nutzer musste die
      // Geste wiederholen (Demolauf 25.08.: 7 Versuche fuer 2 Kanten). Was
      // fehlte, ist keine zweite Aufraeum-Regel, sondern die RETTUNG: die
      // letzte gemeldete Zeigerposition kennt der Canvas (`pending.x/y`,
      // vom `onPointerMove` des SVG fortgeschrieben) — `eingangUnterPunkt()`
      // (oben) loest daraus denselben Ziel-Port auf, den der Hit-Kreis
      // getroffen haette — gleicher Radius, gleiche Typregel, Quell-Node
      // ausgeschlossen.
      //
      // BERICHTIGT 01.09.2026 (Messung `docs/MESSUNG-P5-POINTERCANCEL-2026-
      // 09-01.md`): hier stand bis zu dieser Zeile die Behauptung, «der
      // Zeiger stand beim Abbruch in aller Regel laengst auf dem Ziel-
      // Port» — das ist FALSCH, am echten Chromium gemessen und zweimal
      // reproduziert. Die Ursache des `pointercancel` ist eine stehen-
      // gebliebene Text-Selektion (die SVG-`<text>`-Labels waren nie mit
      // `user-select: none` geschuetzt): der erste Kanten-Zug markiert beim
      // Mousedown+Move eine Selektion, die das `pointerup` ueberlebt; der
      // ZWEITE Zug beginnt darauf, und Chromium deutet Mousedown+Move dann
      // als «Selektion ziehen» — es feuert `dragstart` und unmittelbar
      // danach `pointercancel`, gemessen NACH DER ERSTEN BEWEGUNG, mit dem
      // Zeiger noch mitten auf der Leinwand, NICHT am Ziel-Port. Der
      // eigentliche Fix sitzt darum in `vis-visual.css`
      // (`.vis-canvas-svg { user-select: none }`) — die Selektion, und
      // damit die ganze Kette, entsteht seither gar nicht mehr erst. Diese
      // Rettung hier bleibt trotzdem stehen: sie greift additiv bei jedem
      // ANDEREN `pointercancel` (z.B. wenn der Zeiger zufaellig wirklich
      // schon auf/nahe einem Eingang steht), schliesst aber die urspruenglich
      // gemessene Zweitkanten-Luecke NICHT zuverlaessig — genau deshalb war
      // sie am echten Browser bei diesem Fehlerbild ROT.
      //
      // Gemessen (jsdom, `test/p-zweitkante-zwei-kanten-ein-durchgang.
      // test.tsx`, Fall 3):
      // ZWEI saubere Gesten hintereinander liefern schon am unveraenderten
      // Code zwei Kanten — im Canvas bleibt zwischen zwei Zuegen KEIN
      // Zustand stehen. Der Verlust haengt allein am abgebrochenen `pointer-
      // up`. Darum greift die Rettung genau hier und nirgends sonst.
      //
      // KEIN Pointer-Capture als Gegenmittel (s. den ausdruecklichen Riegel
      // am Quell-Port unten, «KEIN Pointer-Capture: das pointerup muss den
      // Ziel-Port treffen»): der Riegel bleibt unangetastet, der gewoehnliche
      // Weg laeuft weiterhin ueber den Ziel-Port selbst. Diese Rettung ist
      // rein additiv und wird nur betreten, wenn gar kein `pointerup` mehr
      // kommt.
      //
      // Eng gefasst, damit daraus nie die stille Falschverbindung von
      // damals wird: nur ein typgleicher Eingang IM Trefferradius zaehlt,
      // und die Kante wird ANGESAGT (kein stilles Setzen). Findet sich
      // nichts, bleibt es beim bisherigen Verwerfen samt Meldung.
      onPointerCancel={() => {
        panning.current = null;
        if (marquee) setMarquee(null);
        if (drag) setDrag(null);
        if (pending) {
          const ziel = eingangUnterPunkt(
            graph.nodes.map(nodePos),
            { x: pending.x, y: pending.y },
            { ausserNodeId: pending.from, typ: pending.typ },
          );
          setPending(null);
          if (ziel) {
            sicher(() =>
              runCommand('vis.verbinden', {
                graphId,
                from: pending.from,
                fromPort: pending.fromPort,
                to: ziel.nodeId,
                toPort: ziel.port,
              }),
            );
            melde('Die Geste brach ab — die Kante wurde am erreichten Eingang geschlossen.', { ton: 'info' });
          } else {
            melde('Verbindung abgebrochen — bitte die Kante erneut ziehen.', { ton: 'info' });
          }
        }
      }}
    >
      {/* Punktraster — leise Orientierung */}
      <defs>
        <pattern id="vis-raster" width="24" height="24" patternUnits="userSpaceOnUse">
          <circle cx="1" cy="1" r="1" fill="var(--k-line)" />
        </pattern>
      </defs>
      <rect x={view.cx - 4000} y={view.cy - 4000} width={8000} height={8000} fill="url(#vis-raster)" pointerEvents="none" />

      {/* Kanten */}
      {graph.edges.map((e) => {
        const von = graph.nodes.find((n) => n.id === e.from);
        const zu = graph.nodes.find((n) => n.id === e.to);
        if (!von || !zu) return null;
        const a = portPos(nodePos(von), e.fromPort, 'out');
        const b = portPos(nodePos(zu), e.toPort, 'in');
        const typ = VIS_NODE_KATALOG[von.typ]?.outputs.find((p) => p.name === e.fromPort)?.typ ?? 'prompt';
        const gewaehlt = auswahlEdge === e.id;
        const gehovert = hoverEdge === e.id;
        // W1 Massnahme 5: Trenn-✕ bleibt IMMER im DOM (E2E hovert dann klickt);
        // Sichtbarkeit läuft über CSS-Opazität, nicht über Mount/Unmount —
        // sonst könnte ein Klick den Knopf treffen, bevor er real gerendert ist.
        const trennenSichtbar = gehovert || gewaehlt;
        return (
          <g
            key={e.id}
            data-testid="vis-edge"
            onPointerEnter={() => setHoverEdge(e.id)}
            onPointerLeave={() => setHoverEdge((h) => (h === e.id ? null : h))}
          >
            <path
              d={edgePfad(a, b, routingModus)}
              fill="none"
              stroke="transparent"
              strokeWidth={12}
              className="vis-edge-hit"
              onPointerDown={(ev) => {
                ev.stopPropagation();
                setAuswahlEdge(e.id);
              }}
            />
            <path
              d={edgePfad(a, b, routingModus)}
              fill="none"
              stroke={gewaehlt ? 'var(--k-accent)' : PORT_FARBE[typ]}
              strokeWidth={gewaehlt ? 2.5 : gehovert ? 2 : 1.5}
              opacity={0.85}
              pointerEvents="none"
              className="k-uebergang-schnell"
            />
            <g
              transform={`translate(${(a.x + b.x) / 2}, ${(a.y + b.y) / 2})`}
              className={`k-uebergang-schnell vis-edge-trennen${trennenSichtbar ? ' vis-edge-trennen--sichtbar' : ''}`}
              data-testid="edge-trennen"
              onPointerDown={(ev) => {
                ev.stopPropagation();
                sicher(() => runCommand('vis.trennen', { graphId, edgeId: e.id }));
                setAuswahlEdge(null);
                setHoverEdge(null);
              }}
            >
              {/* .k-druck sitzt auf einer INNEREN Gruppe ohne eigenes
                  `transform`-Attribut — die ÄUSSERE Gruppe trägt die
                  Positionierung (translate); CSS-`transform` (das `.k-druck`
                  bei :active setzt) würde ein `transform`-ATTRIBUT sonst
                  ersetzen statt ergänzen und den Knopf beim Drücken an den
                  SVG-Ursprung springen lassen. */}
              <g className="k-druck">
                <title>Verbindung trennen</title>
                <circle r={9} fill="var(--k-raised)" stroke="var(--k-danger)" />
                <KIcon name="schliessen" size={14} x={-7} y={-7} className="vis-edge-trennen-icon" />
              </g>
            </g>
          </g>
        );
      })}

      {/* Pending-Kante folgt dem Zeiger */}
      {pending && (() => {
        const von = graph.nodes.find((n) => n.id === pending.from);
        if (!von) return null;
        const a = portPos(nodePos(von), pending.fromPort, 'out');
        return (
          <path
            d={edgePfad(a, { x: pending.x, y: pending.y }, routingModus)}
            fill="none"
            stroke={PORT_FARBE[pending.typ]}
            strokeWidth={1.5}
            strokeDasharray="5 4"
            pointerEvents="none"
          />
        );
      })()}

      {/* V1-Welle Commit 1: Marquee-Auswahlbox (Shift+Drag auf leerer Fläche) —
          Akzent-Rahmen, kein Fill (dezent), folgt dem Zeiger bis pointerup. */}
      {marquee && (
        <rect
          data-testid="vis-marquee"
          x={Math.min(marquee.x0, marquee.x1)}
          y={Math.min(marquee.y0, marquee.y1)}
          width={Math.abs(marquee.x1 - marquee.x0)}
          height={Math.abs(marquee.y1 - marquee.y0)}
          fill="var(--k-accent)"
          fillOpacity={0.06}
          stroke="var(--k-accent)"
          strokeWidth={1}
          strokeDasharray="4 3"
          pointerEvents="none"
        />
      )}

      {/* Nodes */}
      {graph.nodes.map((n0, rfIndex) => {
        const n = nodePos(n0);
        const kat = VIS_NODE_KATALOG[n.typ];
        if (!kat) return null;
        const h = nodeHoehe(n0, offenerKlapptext, !!laeufe[n0.id]);
        const lauf = laeufe[n.id];
        const auftrag = auswertung?.renderAuftraege.get(n.id);
        // H-32-Fix (V1-Welle Auflage 0, docs/SIM-BEFUNDE.md): der Veraltet-
        // Vergleich MUSS denselben kombinierten Prompt (roh + Formular-Zusatz)
        // nutzen wie `ausfuehren()` beim Absenden — sonst bleibt ein Render mit
        // gesetzten Formularfeldern für immer «veraltet» (memoKey-Schiefe).
        // `auftrag` selbst bleibt RAW (geht als `eingehenderPrompt` an
        // NodeKoerper, das den Formular-Zusatz SELBST anhängt — sonst
        // erschiene er im Text doppelt).
        const veraltetAuftrag = auftrag
          ? { ...auftrag, prompt: kombiniertePrompt(auftrag.prompt, formularZusatz(n0.params ?? {})) }
          : undefined;
        const veraltet = lauf && veraltetAuftrag && lauf.memoKey !== memoKey(veraltetAuftrag);
        const koerperY = KOPF_H + 8 + Math.max(kat.inputs.length, kat.outputs.length) * PORT_ABSTAND;
        // W1 Massnahme 1: Kategorie-Icon + 2px-Tonstreifen (Hue aus dem
        // Kernel-Katalog, Zeichen aus der KIcon-Registry je Kategorie).
        const kategorieFarbe = VIS_KATEGORIE_HUE[kat.kategorie];
        const kategorieIcon = KATEGORIE_ICON[kat.kategorie];
        const istAusgewaehlt = auswahl.has(n.id);
        // v0.8.0B / P5 (Spez §3 B-44, KPipelineNode-Anatomie): running-Puls
        // NUR am laufenden Render-Node (Gesetz 7 — Glow ist Informations-
        // zustand, nie Deko). Dieselbe Statusmenge wie `laeuftNoch` unten in
        // `NodeKoerper` (`gesendet/wartetFreigabe/wartetGpu/rendert`) — EIN
        // Wahrheitsbegriff für «läuft», hier nur auf den Kartenrahmen gespiegelt.
        const nodeLaeuft = n.typ === 'render' && !!lauf && (OFFENE_LAUF_STATUS as readonly string[]).includes(lauf.status);
        return (
          <g
            key={n.id}
            transform={`translate(${n.x}, ${n.y})`}
            data-testid={`vis-node-${n.typ}`}
            data-rf-index={rfIndex}
            tabIndex={rf.tabIndexFuer(rfIndex)}
            role="button"
            aria-label={kat.label}
            aria-pressed={istAusgewaehlt}
            onKeyDown={(e) => behandleNodeTaste(e, rfIndex, n, kat.label)}
          >
            {/* Karte mit geschnittener Ecke (Karteikarten-Verwandter) — Form/
                Layout unangetastet; Rand folgt jetzt der KPipelineNode-
                Anatomie (1.5px Rollenborder 55%, running-Puls nur bei
                laufendem Status, `vis-visual.css`). */}
            <path
              d={`M 0 0 H ${NODE_W - 12} L ${NODE_W} 12 V ${h} H 0 Z`}
              fill="var(--vis-node-flaeche)"
              className={`vis-node-karte${nodeLaeuft ? ' vis-node-karte--laeuft' : ''}`}
              style={{ ['--_rolle' as string]: kategorieFarbe }}
            />
            {/* V1-Welle Commit 1: Akzent-Rahmen (Tusche, kein Fill) für
                ausgewählte Nodes — Marquee/Klick/Shift-Klick setzen `auswahl`. */}
            {istAusgewaehlt && (
              <rect
                data-testid="vis-node-ausgewaehlt"
                x={-3}
                y={-3}
                width={NODE_W + 6}
                height={h + 6}
                fill="none"
                stroke="var(--k-accent)"
                strokeWidth={1.5}
                className="vis-node-ausgewaehlt-rahmen"
              />
            )}
            {/* Kopf = Drag-Griff (V1-Welle Commit 1: + Auswahl-Logik) */}
            <g
              className="vis-node-kopf-griff"
              onPointerDown={(e) => {
                e.stopPropagation();
                if (e.shiftKey) {
                  setAuswahl((s) => {
                    const next = new Set(s);
                    if (next.has(n.id)) next.delete(n.id);
                    else next.add(n.id);
                    return next;
                  });
                  return;
                }
                // Ein Klick auf einen bereits mehrfach ausgewählten Node hält
                // die Gruppe (Gruppen-Drag); sonst ersetzt der Klick die
                // Auswahl durch genau diesen Node (Einzelauswahl). IMMER ein
                // FRISCHES Set (auch wenn inhaltlich gleich) — dieselbe
                // Set-Referenz an setAuswahl zurückzugeben liess Chromium/
                // Playwright das nachfolgende Pointer-Capture-Drag(!) verlieren
                // (kein Bug im Muster selbst, aber ein neues Set kostet nichts
                // und ist die robuste Seite).
                const effektiv = auswahl.has(n.id) && auswahl.size > 1 ? new Set(auswahl) : new Set([n.id]);
                setAuswahl(effektiv);
                const p = toCanvas(e.clientX, e.clientY);
                const start: Record<string, { x: number; y: number }> = {};
                for (const id of effektiv) {
                  const nd = graph.nodes.find((x) => x.id === id);
                  if (nd) start[id] = { x: nd.x, y: nd.y };
                }
                setDrag({ start, startPX: p.x, startPY: p.y, curPX: p.x, curPY: p.y });
                (e.currentTarget.ownerSVGElement as SVGSVGElement).setPointerCapture?.(e.pointerId);
              }}
            >
              <rect width={NODE_W} height={KOPF_H} fill="transparent" />
              <KIcon name={kategorieIcon} size={14} x={8} y={6} className="vis-node-icon-soft" />
              <text x={28} y={17} fontSize={11.5} fontWeight="var(--k-gewicht-stark)" fill="var(--vis-node-tinte)" className="vis-node-kopf-label">
                {kat.label}
              </text>
              {/* V1-Welle Commit 2: Node-Kollaps — nur Kopf+Ports sichtbar
                  (nodeHoehe/portY berücksichtigen `collapsed`). Ein laufender
                  Render-Job (Status weder «bereit» noch «fertig») blockiert
                  den Kollaps mit einem ehrlichen Hinweis statt still zu tun. */}
              <g
                className="k-druck vis-node-knopf"
                data-testid="node-kollaps"
                onPointerDown={(e) => {
                  e.stopPropagation();
                  if (kollapsBlockiert(n0)) {
                    melde('Render läuft noch — erst wenn er fertig ist, lässt sich der Node einklappen.', { ton: 'info' });
                    return;
                  }
                  sicher(() => runCommand('vis.nodeKollabieren', { graphId, nodeId: n.id, collapsed: !n0.collapsed }));
                }}
              >
                <title>{n0.collapsed ? 'Node aufklappen' : 'Node einklappen'}</title>
                {/* D7-Fund (V089-SPEZ §2): das Chevron-Icon allein ist nur an
                    seinen Glyph-Strichen hit-testbar — Klicks daneben (aber
                    noch im Kopf) fielen durch auf die grössere, darunter-
                    liegende Kopf-Drag-Rect (:1343) und lösten einen
                    versehentlichen Node-Drag statt des Kollaps aus (die zwei
                    bisherigen force:true in vis-editor.spec.ts waren die
                    Krücke dafür). Eigene transparente Hit-Fläche als erstes
                    (unterstes) Kind deckt die volle Icon-Bbox (x 160–174,
                    y 6–20) mit Rand ab, bleibt aber vor der Löschen-Zone
                    (ab x=178) stehen — Drag am restlichen Kopf ist
                    unverändert, weil dieser g weiterhin vor der Drag-Rect
                    gemalt wird (Dokumentreihenfolge = Trefferpriorität). */}
                <rect x={NODE_W - 48} y={3} width={24} height={20} fill="transparent" />
                <KIcon
                  name={n0.collapsed ? 'pfeil-unten' : 'pfeil-oben'}
                  size={14}
                  x={NODE_W - 40}
                  y={6}
                  className="vis-node-icon-faint"
                />
              </g>
              <g
                className="k-druck vis-node-knopf"
                data-testid="node-loeschen"
                onPointerDown={(e) => {
                  e.stopPropagation();
                  sicher(() => runCommand('vis.nodeLoeschen', { graphId, nodeId: n.id }));
                }}
              >
                <title>Node löschen</title>
                <KIcon name="schliessen" size={14} x={NODE_W - 22} y={6} className="vis-node-icon-faint" />
              </g>
            </g>
            {/* Tonstreifen (W1): zurückhaltender Kategorie-Hue, 2px, ersetzt die
                bisherige neutrale Hairline unter dem Kopf. */}
            <rect x={0} y={KOPF_H} width={NODE_W} height={2} fill={kategorieFarbe} />

            {/* Eingänge links */}
            {kat.inputs.map((p, i) => {
              const y = portY(n, i);
              return (
                <g key={p.name}>
                  <circle
                    cx={-PORT_ABSATZ}
                    cy={y}
                    r={5}
                    fill={graph.edges.some((e) => e.to === n.id && e.toPort === p.name) ? PORT_FARBE[p.typ] : 'var(--vis-node-flaeche)'}
                    stroke={PORT_FARBE[p.typ]}
                    strokeWidth={1.5}
                    data-testid={`port-in-${p.name}`}
                  />
                  {/* 16-px-Hitkreis */}
                  <circle
                    cx={-PORT_ABSATZ}
                    cy={y}
                    r={11}
                    fill="transparent"
                    className="vis-node-port-hit"
                    onPointerUp={(e) => {
                      if (!pending) return;
                      e.stopPropagation();
                      sicher(() =>
                        runCommand('vis.verbinden', {
                          graphId,
                          from: pending.from,
                          fromPort: pending.fromPort,
                          to: n.id,
                          toPort: p.name,
                        }),
                      );
                      setPending(null);
                    }}
                  />
                  <text x={10} y={y + 3.5} fontSize={10} fill="var(--vis-node-tinte)">{p.label}</text>
                </g>
              );
            })}

            {/* Ausgänge rechts */}
            {kat.outputs.map((p, i) => {
              const y = portY(n, i);
              return (
                <g key={p.name}>
                  <circle cx={NODE_W + PORT_ABSATZ} cy={y} r={5} fill={PORT_FARBE[p.typ]} stroke={PORT_FARBE[p.typ]} data-testid={`port-out-${p.name}`} />
                  <circle
                    cx={NODE_W + PORT_ABSATZ}
                    cy={y}
                    r={11}
                    fill="transparent"
                    className="vis-node-port-hit"
                    onPointerDown={(e) => {
                      // KEIN Pointer-Capture: das pointerup muss den Ziel-Port treffen
                      //
                      // P-ZWEITKANTE Posten 5 (28.08.2026): dieser Riegel ist
                      // AUSDRUECKLICH NICHT aufgehoben. Ein `setPointerCapture`
                      // hier tauscht den Fehler nur gegen einen anderen — das
                      // `pointerup` landete dann am Quell-Port und erreichte
                      // den Ziel-Port nie. Die verlorene zweite Kante ist
                      // stattdessen im `onPointerCancel` des SVG geheilt
                      // (Rettung ueber die letzte Zeigerposition, s. dort);
                      // dass der Ziel-Port dabei weiterhin selbst getroffen
                      // wird, prueft `test/p-zweitkante-zwei-kanten-ein-
                      // durchgang.test.tsx` als eigenen Fall ab.
                      e.stopPropagation();
                      const pos = toCanvas(e.clientX, e.clientY);
                      setPending({ from: n.id, fromPort: p.name, typ: p.typ, x: pos.x, y: pos.y });
                    }}
                  />
                  <text x={NODE_W - 10} y={y + 3.5} fontSize={10} textAnchor="end" fill="var(--vis-node-tinte)">{p.label}</text>
                </g>
              );
            })}

            {/* Körper je Typ — V1-Welle Commit 2: eingeklappte Nodes zeigen NUR
                Kopf + Ports, kein Körper. pointer-events AUS, solange ein
                Drag/eine Marquee läuft (V1-Welle Commit 1) — der Zeiger kann
                sonst während des Ziehens über ein HTML-Formularelement im
                foreignObject (z.B. eine `prompt-text`-Textarea, auch eines
                FREMDEN Nodes) laufen und native Text-Interaktion auslösen.
                Ausserhalb eines Drags unverändert interaktiv. */}
            {!n0.collapsed && (
              <foreignObject
                x={8}
                y={koerperY}
                width={NODE_W - 16}
                height={h - koerperY - 8}
                className={drag || marquee ? 'vis-node-koerper--gesperrt' : undefined}
              >
                <NodeKoerper
                  graphId={graphId}
                  node={n0}
                  prompt={auswertung?.werte.get(n.id)?.['prompt'] as string | undefined}
                  material={auswertung?.werte.get(n.id)?.['material'] as string | undefined}
                  eingehenderPrompt={auftrag?.prompt ?? ''}
                  lauf={lauf}
                  veraltet={!!veraltet}
                  onAusfuehren={() => ausfuehren(n.id)}
                  onFreigeben={() => freigeben(n.id)}
                  onAbbrechen={() => abbrechen(n.id)}
                  cloudLeer={bridgeBase() === ''}
                  bildQuelle={bildQuelle}
                  aufnahmen={aufnahmen}
                  offen={offenerKlapptext.has(n.id)}
                  onToggleOffen={() => toggleKlapptext(n.id)}
                />
              </foreignObject>
            )}
          </g>
        );
      })}
    </svg>

    {/* P16 · DIE BEIBLAETTER — was `node-expand` am Render-Knoten zeigt.
        Sie stehen hier, AUSSERHALB des `<svg>`, und das ist die tragende
        Eigenschaft: der Zoom-Horcher haengt am `<svg>`-Element selbst
        (`svg.addEventListener('wheel', …)` oben, mit `preventDefault`), und
        ein Ereignis auf einem Geschwister-Element laeuft nie durch ihn
        hindurch. Das Rad ueber der Leinwand zoomt, das Rad ueber dem
        Beiblatt rollt das Beiblatt — zwei Flaechen, nicht zwei Bedeutungen
        fuer dieselbe. Gemessen, nicht angenommen (s. Kopfkommentar von
        `RenderBeiblatt`).
        `nodePos` statt `n0`: wird der Knoten gezogen, wandert das Beiblatt
        mit ihm. */}
    {graph.nodes
      .filter((n) => n.typ === 'render' && !n.collapsed && offenerKlapptext.has(n.id))
      .map((n0) => {
        const n = nodePos(n0);
        const platz = beiblattPlatz(n, view, flaeche);
        return (
          <RenderBeiblatt
            key={`beiblatt-${n0.id}`}
            graphId={graphId}
            node={n0}
            links={platz.links}
            oben={platz.oben}
            maxHoehe={platz.maxHoehe}
          />
        );
      })}


    {/* v0.9.25 P-M: der `vis-palette-toggle` (fixe Chrome oben links, nur
        Manuell-Modus) ist mit dem Manuell-Codepfad entfallen — die
        Node-Palette lebt als Werkzeug in der GRAPH-Insel
        (`island/inhalte/graph.tsx`, `island-palette-eintrag-<typ>`). */}

    {/* Kuratier-Fläche (Welle 1 — Soll-Bild `Kosmo Viz Kuratierung.dc.html`
        §6.2): vom schwebenden Overlay zum Vollflächen-Raster ausgebaut
        (`KuratierFlaeche.tsx`) — 3-spaltiges Karten-Raster ODER A/B-Vergleich
        mit Parameter-Diff, Filter (Alle/Favoriten/Verworfen), Kurations-
        Inspektor. Der Umschalt-Knopf bleibt oben rechts über der Fläche
        erreichbar (schliessen). Laufzeitdaten (Bild/Kuration) bleiben in
        vis-runtime — der Doc kennt nur die Nodes.
        zIndex 36 statt 9 (P6): die Kuratier-Fläche selbst liegt jetzt bei
        z-35 (über den Dock-Panels z-14/30, wie sie vorher mit 8 über den
        z-5-Overlays lag) — der Schliessen-Knopf muss weiterhin EINE Stufe
        darüber bleiben. */}
    {/* W1 P-KURATIERDECKEL, zweite Fassung (03.09.2026): der Knopf weicht
        jetzt nach UNTEN aus, unter die ganze global fixierte Insel-Kopfzeile
        (`INSEL_KOPFZEILE_UNTERKANTE_PX`, s. Konstanten-Kommentar oben mit den
        gemessenen Kaesten). Der frühere Ausweich nach links löste den
        Einstellungs-Kreis und scheiterte an `.isl-kopf-zweitgruppe`, die seit
        B82 250px weit nach links reicht — und deren Breite mit dem Sync-Text
        schwankt. Die Höhe schwankt nicht: beide Kopf-Elemente sind aus
        44px-Trefferflächen gebaut. `right` bleibt klein, `.vis-visual.css`
        setzt beides bewusst nicht selbst (dort nur Kommentar + Verweis). */}
    <div
      className="vis-chrome-topright"
      style={{
        top: `calc(${INSEL_KOPFZEILE_UNTERKANTE_PX}px + var(--k-s3))`,
        right: 'var(--k-s3)',
      }}
    >
      <KButton
        size="sm"
        tone="ghost"
        data-testid="vis-kuratier-toggle"
        title="Kuratieren"
        aria-label="Kuratieren"
        aria-expanded={kuratierOffen}
        onClick={() => setKuratierOffen((o) => !o)}
      >
        <KIcon name={kuratierOffen ? 'schliessen' : 'stern'} size={16} title="Kuratieren" />
        {kuratierKarten.length > 0 && (
          <span className="vis-kuratier-zaehler">{kuratierKarten.length}</span>
        )}
      </KButton>
    </div>
    {kuratierOffen && (
      <KuratierFlaeche
        graph={graph}
        karten={kuratierKarten}
        vergleichAuswahl={vergleichAuswahl}
        onMarkieren={markiereBild}
        onVerwerfen={verwerfeBild}
        onVergleichWahl={toggleVergleich}
      />
    )}

    {/* v0.9.25 P-M: die schwebende Zoom-/Snap-/Routing-Leiste
        (`.vis-chrome-bottomright`, nur Manuell-Modus) ist mit dem
        Manuell-Codepfad entfallen — Zoom/Fit/Snap/Routing leben in der
        ANSICHT-Insel (`island/inhalte/ansicht.tsx`), die dieselben
        `vis-runtime.ts`-Felder und den Fernauslöser `canvasBefehl`
        (Effekt oben) nutzt. */}

    {/* K35 (Owner-Korrekturen 2026-07, S.14 «diese übersicht raus, die bringt
        nichts»): der `vis-minimap-toggle` (fixe Chrome unten links, Welle 3)
        und das PC1-Island-Overlay der Minimap sind ERSATZLOS entfernt.
        Der Legende-Begleiter des früheren Overlays bleibt (Owner K36 im
        selben Rundown: «legende ist gut») — jetzt als eigenständige
        Legende-Fläche unten links im Island-Modus, sichtbar sobald der
        Graph Nodes mit bekannten Porttypen trägt (der frühere Anker an die
        Minimap-Schwelle `>= 5 Nodes` war reine Minimap-Semantik und ist mit
        ihr entfallen). Position/Randabstand unverändert
        (`.vis-island-legende-overlay`, vormals `.vis-island-minimap-overlay`,
        `vis-visual.css`). v0.9.25 P-M: die frühere `islandModus`-Bedingung
        ist entfallen — es gibt nur noch die Island-Fassung. */}
    {graph.nodes.length > 0 && legendeTypen.length > 0 && (
      <div className="vis-island-legende-overlay" data-testid="vis-island-legende">
        <div data-testid="vis-legende" className="vis-legende-panel" style={{ width: LEGENDE_W, height: 'auto' }}>
          {legendeTypen.map((t) => (
            <div key={t} className="vis-legende-zeile">
              <span aria-hidden className="vis-legende-punkt" style={{ ['--_farbe' as string]: PORT_FARBE[t] }} />
              <span>{PORT_TYP_NAME[t]}</span>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* v0.9.25 P-M: `<DockFlaeche station="vis">` ist mit dem
        Manuell-Codepfad entfallen — die Vis-Station rendert keine
        Dock-Fläche mehr (Owner-Auftrag «die alte Dock muss weg», K15
        aufgehoben; `docs/V0925-SPEZ.md` §3 P-M). */}
    </div>
  );
}

/**
 * SK-V3 (W1): 3-Zeilen-Klapptext — «… mehr» expandiert den Node über den
 * Eltern-State (`offen`/`onToggleOffen`), NICHT lokal, weil die Kartenhöhe
 * (SVG-Pfad + foreignObject) im ELTERN-Node-Canvas berechnet wird.
 */
function KlappText({
  testid,
  text,
  platzhalter,
  offen,
  onToggleOffen,
}: {
  testid: string;
  text: string;
  platzhalter: string;
  offen: boolean;
  onToggleOffen: () => void;
}) {
  const hatText = text.trim().length > 0;
  return (
    <div className="vis-klapptext">
      <div
        data-testid={testid}
        className={[
          'vis-klapptext-text',
          !hatText ? 'vis-klapptext-text--platzhalter' : '',
          !offen ? 'vis-klapptext-text--clamp' : '',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {hatText ? text : platzhalter}
      </div>
      {hatText && (
        <button
          type="button"
          className="k-druck vis-klapptext-mehr"
          data-testid="node-expand"
          onPointerDown={(e) => e.stopPropagation()}
          onClick={onToggleOffen}
        >
          {offen ? 'weniger' : '… mehr'}
        </button>
      )}
    </div>
  );
}

/**
 * A2 · Vis-Bedienung (16.09.2026) — die sechs Bedienelemente der Abnahmeliste
 * 60-ABNAHMELISTE.md, Zeilen 4 / 47 / 48 / 50a / 51 / 56, am Render-Node.
 *
 * WARUM ALLE SECHS AN EINEN ORT: hier wird der Auftrag aufgegeben. Ein Regler
 * für die Auflösung an anderer Stelle als der Knopf, der rendert, erzeugt
 * genau die zweite Wahrheit, an der dieses Repo schon dreimal gescheitert ist.
 *
 * WIE SIE WIRKEN: jedes Element schreibt einen PERSISTENTEN Node-Parameter
 * über den bestehenden `vis.nodeParametrieren`-Command (undo-fähig, überlebt
 * ein Remount). Gelesen wird er an EINER Stelle, `renderBedienungAusParams`
 * in `vis-jobs.ts` — dieselbe Funktion, aus der auch die Zeitzeile unten ihre
 * Zahlen zieht. Anzeige und Auftrag können darum nicht auseinanderlaufen.
 *
 * WAS DIESE OBERFLÄCHE NICHT BEHAUPTET: dass der ferne Renderer alles davon
 * auch liest. Auflösung und Abtastungen liest er nachweislich (der
 * ComfyUI-Worker nimmt genau diese zwei aus `render`).
 *
 * BERICHTIGT AM 17.09.2026 (A15/W5, Welle 5). Hier stand: «Himmel, Belichtung
 * und Sonnendetails sind neu im Vertrag und werden hier verschickt — ob der
 * Cycles-Schritt auf der HomeStation sie schon auswertet, ist von hier aus
 * nicht zu prüfen.» **Das ist jetzt geprüft, und die Antwort ist Nein.**
 * Gemessen an der Naht: die Nutzlast dieses Knotens durch den echten Leser der
 * Bildseite (`kosmo_szene.lies_szene`) und weiter durch die Funktion, die
 * Blenders Befehlszeile baut (`seams._multipass_argumente`). Vom Sonnenblock
 * kommen dort nur `elevation` und `azimuth` an; `staerke`, `kelvin` und
 * `winkelGrad` nicht, `himmel`, `belichtung` und `rauschschwelle` gar nicht
 * erst. Der Befund steht als Tabelle in `vis-jobs.ts` (`FREMDNAHT`), der
 * Hinweistext unten wird daraus gerechnet, und `a15-fremdnaht-bild.test.ts`
 * zählt nach, dass kein Bedienelement ohne Messung dazukommt. Ein Satz, der
 * einen Weg behauptet, den es nicht gibt, war der Befund der Welle 0 — ein
 * Satz, der eine erledigte Prüfung weiter als offen führt, ist dieselbe Sorte
 * Fehler mit umgekehrtem Vorzeichen.
 */
/**
 * Anzeigenamen der vier Himmelsarten. Die GEMESSENEN Kennungen
 * (`MULTIPLE_SCATTERING` …) bleiben die Wahrheit im Auftrag und stehen in der
 * Hinweiszeile unter dem Feld — hier steht nur, wie sie im 200 px schmalen
 * Knoten heissen, ohne über den Rand zu laufen. Eine Übersetzung, keine
 * zweite Liste: der Record ist über `HimmelArt` vollständig, eine fünfte Art
 * im Kernel bricht hier die Typprüfung.
 */
const HIMMEL_TEXTE: Record<(typeof HIMMEL_ARTEN)[number], string> = {
  SINGLE_SCATTERING: 'Einfachstreuung',
  MULTIPLE_SCATTERING: 'Mehrfachstreuung',
  PREETHAM: 'Preetham',
  HOSEK_WILKIE: 'Hosek-Wilkie',
};

/**
 * A15 — EINE Zeile des Node-Körpers.
 *
 * Sie tut genau zwei Dinge, und beide sind Befunde vom 17.09.2026:
 *
 * 1. `data-zeile` schreibt die Kennung der Zeile ins DOM. Das Zeilenregister
 *    (`RENDER_ZEILEN` oben) und das Gerenderte lassen sich dadurch
 *    gegeneinander halten — ohne diese Kennung bliebe die Höhe eine Bitte im
 *    Kommentar («Wer Zeilen hinzufügt, MISST nach»), und eine Bitte ist kein
 *    Wächter. In diesem Projekt sind 35 Prüfungen einzeln entfernt worden und
 *    elf blieben grün.
 * 2. `minWidth: 0` klemmt die Spalte. Gemessen am ausgelieferten Bündel:
 *    der Körper bot 184 px und der Inhalt lief auf 242 px — NICHT ein
 *    einzelnes Element, sondern JEDE Zeile, weil ein Grid-Kind ohne
 *    `min-width: 0` seine Spur auf seine eigene Mindestbreite aufzieht und
 *    der breiteste Wähler damit den ganzen Körper mitnimmt. Die Höhe war
 *    gemessen worden, die Breite nicht.
 */
function Zeile({ id, children, title }: { id: string; children: ReactNode; title?: string }): ReactNode {
  return (
    <div data-zeile={id} style={{ minWidth: 0 }} {...(title !== undefined ? { title } : {})}>
      {children}
    </div>
  );
}

/** A15 — Breitenklemme eines vollbreiten Bedienelements. `width`/`minWidth`/
 *  `maxWidth`/`display` sind KSelect-Layout-Schlüssel und landen laut
 *  `packages/kosmo-ui/src/select.tsx` (`WRAP_STYLE_KEYS`) auf dem Wrapper —
 *  genau dort, wo die Mindestbreite entsteht. */
const KLEMME_VOLL: CSSProperties = { display: 'block', width: '100%', minWidth: 0, maxWidth: '100%', boxSizing: 'border-box' };

/** A15 — dasselbe für native Felder (Regler, Eingabefeld): die haben eine
 *  eigene UA-Standardbreite, die ohne `minWidth: 0` als Mindestbreite wirkt. */
const KLEMME_FELD: CSSProperties = { minWidth: 0, maxWidth: '100%', boxSizing: 'border-box' };

/** A15 — Fliesstext im 184 px schmalen Körper: ein einziges langes Wort
 *  (`MULTIPLE_SCATTERING`, ein Dateiname im Prompt) schöbe die Zeile sonst
 *  über den Rand, genau wie die Wähler es taten. */
const KLEMME_TEXT: CSSProperties = { minWidth: 0, overflowWrap: 'anywhere' };

/** A15 — der abgehende Prompt bleibt IMMER sichtbar (er ist die Antwort auf
 *  «was schickt ‹Ausführen› ab?»), im zugeklappten Zustand auf eine Zeile
 *  gekürzt. Gekürzt, nicht versteckt: aufgeklappt steht er vollständig da. */
const KLEMME_TEXT_ZWEIZEILIG: CSSProperties = {
  ...KLEMME_TEXT,
  display: '-webkit-box',
  WebkitBoxOrient: 'vertical',
  WebkitLineClamp: 2,
  overflow: 'hidden',
};

function RenderBedienung({
  params,
  param,
  preset,
}: {
  params: Record<string, string | number | boolean>;
  param: (feld: string, wert: string | number | boolean) => void;
  /** Der Preset-Wähler ist Zeile 4 der Abnahmeliste und damit das ERSTE der
   *  sechs Bedienelemente — er stand bis A15 ausserhalb dieser Komponente,
   *  obwohl deren Kopfkommentar «alle sechs an einen Ort» verspricht. */
  preset: (typeof RENDER_PRESETS)[number] | undefined;
}): ReactNode {
  const bedienung = renderBedienungAusParams(params);
  const himmelGewaehlt = bedienung.himmel !== undefined;
  const drehung = typeof params['umgebungDrehungGrad'] === 'number' ? (params['umgebungDrehungGrad'] as number) : 0;

  return (
    <>
      {/* ZEILE 4 — «recherchiere kamera und lichteinstellungen fuer
          architektur innenraumbilder»: Kamera-, Licht- und Bildwerte als
          GANZES aus einer geprüften Tabelle (K20/A10-Preset), nie einzeln
          von Hand. Leer = bisheriger Default (128 Abtastungen). */}
      <Zeile id="bedienung-preset">
        <KSelect
          size="sm"
          value={String(params['preset'] ?? '')}
          data-testid="vis-preset-select"
          onChange={(e) => param('preset', e.target.value)}
          onPointerDown={(e) => e.stopPropagation()}
          className="vis-node-select-voll"
          style={KLEMME_VOLL}
        >
          <option value="">kein Preset (Default 128 Samples)</option>
          {RENDER_PRESETS.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </KSelect>
      </Zeile>

      {/* ZEILE 50a — «rendere volle aufloesung» */}
      <Zeile id="bedienung-aufloesung">
        <label className="vis-node-render-formular">
          <span className="vis-node-fortschritt">Auflösung</span>
          <KSelect
            size="sm"
            value={bedienung.resolution ? `${bedienung.resolution[0]}x${bedienung.resolution[1]}` : ''}
            data-testid="render-aufloesung"
            onChange={(e) => param('aufloesung', e.target.value)}
            className="vis-node-select-voll"
            style={KLEMME_VOLL}
          >
            <option value="">
              {preset ? `aus dem Preset (${preset.render.resolution[0]} × ${preset.render.resolution[1]})` : '1600 × 1000'}
            </option>
            {AUFLOESUNGEN.map((a) => (
              <option key={a.text} value={`${a.wert[0]}x${a.wert[1]}`}>
                {a.text}
              </option>
            ))}
          </KSelect>
        </label>
      </Zeile>

      {/* ZEILE 51 — «mach mir einer der in 10min durch ist, schreib qualitaet runter» */}
      <Zeile id="bedienung-qualitaet">
        <label className="vis-node-render-formular">
          <span className="vis-node-fortschritt">Qualität gegen Zeit</span>
          <KSelect
            size="sm"
            value={bedienung.samples !== undefined ? String(bedienung.samples) : ''}
            data-testid="render-qualitaet"
            onChange={(e) => param('abtastungen', Number(e.target.value) || 0)}
            className="vis-node-select-voll"
            style={KLEMME_VOLL}
          >
            <option value="">{preset ? `aus dem Preset (${preset.render.samples})` : '128 — Vorgabe'}</option>
            {QUALITAETSSTUFEN.map((q) => (
              <option key={q.abtastungen} value={String(q.abtastungen)}>
                {`${q.abtastungen} · ${zeitText(zeitschaetzungSekunden(q.abtastungen, [4000, 2667]))} · ${q.name}`}
              </option>
            ))}
          </KSelect>
        </label>
      </Zeile>

      {/* ZEILE 47 — «hintergrund basically weiss … einbringen … ohne an der Belichtung zu verlieren» */}
      <Zeile id="bedienung-himmel">
        <label className="vis-node-render-formular">
          <span className="vis-node-fortschritt">Himmel</span>
          <KSelect
            size="sm"
            value={String(params['himmel'] ?? '')}
            data-testid="render-himmel"
            onChange={(e) => param('himmel', e.target.value)}
            className="vis-node-select-voll"
            style={KLEMME_VOLL}
          >
            <option value="">{preset?.render.himmel ? 'aus dem Preset' : 'keiner'}</option>
            {HIMMEL_ARTEN.map((h) => (
              <option key={h} value={h}>
                {HIMMEL_TEXTE[h]}
              </option>
            ))}
          </KSelect>
        </label>
      </Zeile>

      {/* ZEILE 48 — «zeig vom hintergrundbild mehr die berge weniger das wasser» */}
      {/* Diese eine Zeile liegt waagrecht (Name · Regler · Wert) — dieselbe
          Anordnung wie am Zahl-Node, darum dieselben drei Klassen von dort.
          A15: ohne Himmel steht der GRUND im Wertfeld, statt eine eigene
          Hinweiszeile zu kosten — ein gesperrter Regler ohne Wort daneben
          wäre die Sorte stiller Zustand, an der dieses Repo schon hing. */}
      <Zeile
        id="bedienung-drehung"
        {...(himmelGewaehlt
          ? {}
          : { title: 'Ohne Himmel gibt es nichts zu drehen — die Drehung reist erst mit, wenn oben einer gewählt ist.' })}
      >
        <label className="vis-node-zahl-wrap">
          <span className="vis-node-fortschritt">Umgebung drehen</span>
          <input
            type="range"
            min={0}
            max={360}
            step={5}
            value={drehung}
            disabled={!himmelGewaehlt}
            data-testid="render-umgebung-drehen"
            className="vis-node-zahl-regler"
            style={KLEMME_FELD}
            onChange={(e) => param('umgebungDrehungGrad', Number(e.target.value))}
          />
          <span className="vis-node-zahl-wert">{himmelGewaehlt ? `${drehung}°` : '—'}</span>
        </label>
      </Zeile>

      {/* ZEILE 56 — «fuettere ai imaging tools … dann vergleichen» (hier: die Wahl) */}
      <Zeile id="bedienung-bildwerkzeug">
        <label className="vis-node-render-formular">
          <span className="vis-node-fortschritt">Bildwerkzeug</span>
          <KSelect
            size="sm"
            value={String(params['backbone'] ?? '')}
            data-testid="render-bildwerkzeug"
            onChange={(e) => param('backbone', e.target.value)}
            className="vis-node-select-voll"
            style={KLEMME_VOLL}
            disabled={params['nurCycles'] === true || params['lineart'] === true}
          >
            <option value="">Z-Image Turbo — Vorgabe</option>
            {BILDWERKZEUG_IDS.map((id) => (
              <option key={id} value={id}>
                {BILDWERKZEUG_TEXTE[id].name}
              </option>
            ))}
          </KSelect>
        </label>
      </Zeile>
    </>
  );
}

/**
 * A15 — die Erklärtexte zu den sechs Bedienelementen, als EIGENER Block hinter
 * dem Klappknopf.
 *
 * WARUM NICHT unter das jeweilige Element: gemessen (1400×900). Standen die
 * Hinweise zwischen den Bedienelementen, schob das Aufklappen den
 * Bildwerkzeug-Wähler von y=812 auf y=959 — aus dem Fenster heraus. Wer den
 * Auftrag liest, verliert dann das, was er einstellen wollte. So bleiben die
 * sechs Elemente in BEIDEN Klappzuständen an derselben Stelle (gemessen:
 * 584/635/685/736/771/812, zu wie auf).
 *
 * Damit die Texte ohne ihren Nachbarn verständlich bleiben, nennt jeder von
 * ihnen sein Bedienelement beim Namen — ein Hinweis, der nicht sagt, wozu er
 * gehört, ist keiner.
 */
function RenderErklaerungen({
  params,
  preset,
}: {
  params: Record<string, string | number | boolean>;
  preset: (typeof RENDER_PRESETS)[number] | undefined;
}): ReactNode {
  const bedienung = renderBedienungAusParams(params);
  // Die WIRKSAME Auflösung/Abtastzahl — genau die Reihenfolge, die
  // `sendeGraphRenderAuftrag` verwendet: Bedienung schlägt Preset, Preset
  // schlägt die alte Vorgabe. Damit zeigt die Zeitzeile die Zahlen des
  // Auftrags, der wirklich abgeht, nicht die eines gedachten.
  const aufloesung = bedienung.resolution ?? preset?.render.resolution ?? ([1600, 1000] as const);
  const abtastungen = bedienung.samples ?? preset?.render.samples ?? 128;
  const sekunden = zeitschaetzungSekunden(abtastungen, [aufloesung[0], aufloesung[1]]);
  const istMesspunkt = (abtastungen === 128 || abtastungen === 2048) && aufloesung[0] === 4000 && aufloesung[1] === 2667;
  const himmelGewaehlt = bedienung.himmel !== undefined;
  const werkzeug = BILDWERKZEUG_TEXTE[bedienung.backbone ?? 'z-image-turbo'];

  return (
    <>
      <Zeile id="zusatz-zeitschaetzung">
        <div className="vis-node-final-prompt" data-testid="render-zeitschaetzung" style={KLEMME_TEXT}>
          {istMesspunkt
            ? `Qualität: ${zeitText(sekunden)} — gemessen am 11.09. auf OPTIX bei ${aufloesung[0]} × ${aufloesung[1]}.`
            : `Qualität: rund ${zeitText(sekunden)} — GESCHÄTZT aus zwei gemessenen Punkten ` +
              `(128 Abtastungen 83 s, 2048 Abtastungen 775 s, beide bei 4000 × 2667). Eine andere Szene rechnet anders.`}
        </div>
      </Zeile>
      <Zeile id="zusatz-himmel-hinweis">
        <div className="vis-node-final-prompt" data-testid="render-himmel-hinweis" style={KLEMME_TEXT}>
          {bedienung.himmel
            ? `Himmel: ${bedienung.himmel.modell} · Stärke ${bedienung.himmel.staerke}, Luft ${bedienung.himmel.luftdichte},` +
              ` Aerosol ${bedienung.himmel.aerosoldichte}` +
              // Die Drehung steht NUR hier, wenn sie wirklich mitreist — der
              // Regler zeigt sonst einen Winkel, den der Auftrag nicht trägt.
              `${bedienung.himmel.drehungGrad !== undefined ? `, gedreht ${bedienung.himmel.drehungGrad}°` : ''}`
            : 'Himmel: vier Arten — genau die, die Blender 5.2 hat (NISHITA gibt es nicht mehr).'}
        </div>
      </Zeile>
      {!himmelGewaehlt && (
        <Zeile id="zusatz-drehung-hinweis">
          <div className="vis-node-final-prompt" data-testid="render-drehung-ohne-himmel" style={KLEMME_TEXT}>
            Umgebung drehen: ohne Himmel gibt es nichts zu drehen — die Drehung reist erst mit, wenn
            oben einer gewählt ist.
          </div>
        </Zeile>
      )}
      <Zeile id="zusatz-bildwerkzeug-hinweis">
        <div className="vis-node-final-prompt" data-testid="render-bildwerkzeug-hinweis" style={KLEMME_TEXT}>
          {params['nurCycles'] === true || params['lineart'] === true
            ? 'Bildwerkzeug: keines im Spiel — «nur Cycles» bzw. Strichzeichnung rechnet ohne KI-Veredelung.'
            : `Bildwerkzeug: ${werkzeug.hinweis}`}
        </div>
      </Zeile>
      {/* A15/W5, 17.09.2026 — DIESER SATZ IST JETZT GEMESSEN.
          Bis heute stand hier «ob der Cycles-Schritt sie schon auswertet, ist
          von hier aus nicht geprüft». Das war am 16.09. ehrlich; seit der
          Messung an der Naht ist es überholt, und ein überholter Satz schlägt
          eine Gegenprobe (Muster 2). Der Text kommt darum aus `fremdnahtSatz()`
          und damit aus derselben Tabelle, die die Probe nachzählt — er kann
          nicht mehr etwas anderes behaupten als die Messung. */}
      <Zeile id="zusatz-ehrlichkeit">
        <div className="vis-node-final-prompt" data-testid="render-bedienung-ehrlichkeit" style={KLEMME_TEXT}>
          {fremdnahtSatz()} «nur Cycles» rechnet ohne KI-Veredelung, «Strichzeichnung» erzwingt
          Line-Art.
        </div>
      </Zeile>
    </>
  );
}

/**
 * P16 — das Auftrags-Formular, aus dem Kartenkoerper herausgeloest.
 *
 * WORTGLEICH uebernommen aus `NodeKoerper`s Render-Zweig: dieselben fuenf
 * testids, dieselben Optionen, dieselben Klemmen. Verschoben ist nur der ORT,
 * an dem es haengt — und das ist der ganze Punkt von P16. Wer hier ein Feld
 * ergaenzt, aendert die Hoehe des Beiblatts und muss `RENDER_ZEILEN_ZUSATZ`
 * (`zusatz-formular`) anfassen; `test/a15-render-knotenhoehe.test.tsx` wird
 * sonst rot.
 */
function RenderAuftragsFormular({
  params,
  param,
  fassadenBausteine,
}: {
  params: Record<string, string | number | boolean>;
  param: (feld: string, wert: string | number | boolean) => void;
  fassadenBausteine: readonly string[];
}): ReactNode {
  const formFassade = String(params['formFassade'] ?? '');
  const formSzene = String(params['formSzene'] ?? '');
  const formJahreszeit = String(params['formJahreszeit'] ?? '');
  const formPersonen = String(params['formPersonen'] ?? '');
  const formFreitext = String(params['formFreitext'] ?? '');
  return (
    <Zeile id="zusatz-formular">
      <div data-testid="render-formular" className="vis-node-render-formular">
        {/* V-H4-Fix (Kritik-065 Runde 1, Befund 1): `1fr 1fr` allein lässt
            Grid-Spalten am Inhalt (Select-Optionstext) wachsen — `minmax(0, 1fr)`
            erzwingt die Spur, `minWidth: 0` an JEDEM Grid-Kind bricht die
            Flex-/Select-Mindestbreite, `width: 100% + boxSizing: border-box` an
            Input/Select klemmt sie auf das Innenmass. Sonst ragen «Szene»/
            «Personen» über den rechten Rand hinaus. */}
        <div className="vis-node-render-grid">
          <div className="vis-node-feld-zelle">
            <KField label="Fassade">
              {fassadenBausteine.length > 0 ? (
                <KSelect
                  size="sm"
                  value={formFassade}
                  data-testid="render-formular-fassade"
                  onChange={(e) => param('formFassade', e.target.value)}
                  className="vis-node-select-zelle"
                  style={KLEMME_VOLL}
                >
                  <option value="">— frei —</option>
                  {fassadenBausteine.map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </KSelect>
              ) : (
                <KInput
                  size="sm"
                  defaultValue={formFassade}
                  key={formFassade}
                  placeholder="frei …"
                  data-testid="render-formular-fassade"
                  onBlur={(e) => e.target.value !== formFassade && param('formFassade', e.target.value)}
                  className="vis-node-select-zelle"
                  style={KLEMME_FELD}
                />
              )}
            </KField>
          </div>
          <div className="vis-node-feld-zelle">
            <KField label="Szene">
              <KSelect
                size="sm"
                value={formSzene}
                data-testid="render-formular-szene"
                onChange={(e) => param('formSzene', e.target.value)}
                className="vis-node-select-zelle"
                style={KLEMME_VOLL}
              >
                <option value="">—</option>
                <option value="strasse">Aussen · Strasse</option>
                <option value="hof">Aussen · Hof</option>
                <option value="vogel">Aussen · Vogel</option>
                <option value="innen">Innen</option>
              </KSelect>
            </KField>
          </div>
          <div className="vis-node-feld-zelle">
            <KField label="Jahreszeit">
              <KSelect
                size="sm"
                value={formJahreszeit}
                data-testid="render-formular-jahreszeit"
                onChange={(e) => param('formJahreszeit', e.target.value)}
                className="vis-node-select-zelle"
                style={KLEMME_VOLL}
              >
                <option value="">—</option>
                <option value="sommer">Sommer</option>
                <option value="winter">Winter</option>
                <option value="herbst">Herbst</option>
              </KSelect>
            </KField>
          </div>
          <div className="vis-node-feld-zelle">
            <KField label="Personen">
              <KSelect
                size="sm"
                value={formPersonen}
                data-testid="render-formular-personen"
                onChange={(e) => param('formPersonen', e.target.value)}
                className="vis-node-select-zelle"
                style={KLEMME_VOLL}
              >
                <option value="">—</option>
                <option value="keine">keine</option>
                <option value="wenige">wenige</option>
                <option value="belebt">belebt</option>
              </KSelect>
            </KField>
          </div>
        </div>
        <KField label="Freitext">
          <KInput
            size="sm"
            defaultValue={formFreitext}
            key={formFreitext}
            placeholder="Freitext-Zusatz …"
            data-testid="render-formular-freitext"
            onBlur={(e) => e.target.value !== formFreitext && param('formFreitext', e.target.value)}
            className="vis-node-select-zelle"
            style={KLEMME_FELD}
          />
        </KField>
      </div>
    </Zeile>
  );
}

/**
 * P16 · DAS BEIBLATT — was der Klappknopf zeigt, steht neben der Karte statt
 * in ihr.
 *
 * ── Warum nicht wachsen, nicht rollen, nicht in Abschnitte teilen ────────
 *
 * GEMESSEN am laufenden Bild (eigener Bau, eigener kopfloser Chromium auf
 * CDP 9293), fuenf Fenstergroessen, frischer Render-Knoten:
 *
 *   Fenster      Karte zu     Karte auf    draussen zu   draussen auf
 *   1280x720     230x580      230x1099     0 von 10      7 von 15
 *   1366x768     230x580      230x1099     0 von 10      7 von 15
 *   1440x900     230x580      230x1099     0 von 10      7 von 15
 *   1680x1050    230x580      230x1099     0 von 10      7 von 15
 *   1920x1080    230x580      230x1099     0 von 10      7 von 15
 *
 * - WACHSEN geht nicht. Die Karte waechst beim Aufklappen nur nach unten
 *   (ihr `y` bleibt stehen); bei 1280x720 steht sie zugeklappt bei y 80…660,
 *   das sind **60 px Luft**. Der Zusatz braucht 519. Selbst der kleinste
 *   sinnvolle Abschnitt — das Formular allein, 160 px — passt nicht. Und
 *   selbst wenn die Karte symmetrisch um ihre Mitte wuechse, waere bei einem
 *   720 px hohen Fenster bei rund 700 px Schluss: 1099 px Inhalt passen in
 *   kein gemessenes Fenster. ABSCHNITTE verkleinern den Befund, sie beheben
 *   ihn nicht.
 * - ROLLEN im Knoten geht nicht. Gemessen mit einer Sonde am ausgelieferten
 *   Verhalten: eine Rollflaeche im Koerper ist zwar rollbar (scrollHeight
 *   892 gegen clientHeight 300), aber ein echtes Radereignis auf ihrer Mitte
 *   bewegt sie um **0 px** und zoomt stattdessen die Leinwand (Knotenbreite
 *   230 → 160.47 px). Ursache ist `svg.addEventListener('wheel', …)` mit
 *   `preventDefault()` weiter oben — das Rad der Leinwand frisst das Rollen.
 *   Man koennte es mit `stopPropagation` abfangen; dann bedeutet dasselbe Rad
 *   je nach Zeigerort zweierlei. Genau davor warnt der Auftrag, und die
 *   Gegenprobe zeigt, dass das Rad heute genau EINE Bedeutung hat (dasselbe
 *   Rad auf leerer Leinwand: 160.47 → 111.95 px, derselbe Faktor).
 *
 * ── Was das Beiblatt ist ─────────────────────────────────────────────────
 *
 * Ein Bedienfeld neben der Karte, das sich am FENSTER bemisst statt an der
 * Karte: es sitzt rechts neben dem Knoten (links, wenn rechts kein Platz
 * ist) und wird in ein Rechteck geklemmt, das die fixe Insel-Chrome
 * ausspart. Es liegt AUSSERHALB des `<svg>` — darum erreicht sein Rad den
 * Zoom-Horcher der Leinwand nicht, und es gibt keine zweite Bedeutung fuer
 * dasselbe Rad, sondern zwei verschiedene Flaechen.
 *
 * Die Inhaltsspalte ist **genau so breit wie im Knoten** (`NODE_W - 16` =
 * 184 px). Das ist kein Zufall und keine Bequemlichkeit: die Hoehen in
 * `RENDER_ZEILEN_ZUSATZ` sind bei 184 px Breite am Bild gemessen worden.
 * Ein breiteres Beiblatt haette sie alle ungueltig gemacht, und das Register
 * waere von einer Messung zu einer Behauptung geworden.
 *
 * NICHT GELOEST und ausdruecklich nicht gemessen: sind ZWEI Render-Knoten
 * zugleich aufgeklappt, koennen sich ihre Beiblaetter ueberlagern. Gemessen
 * ist der Fall, den ein Mensch ausloest — ein Knoten.
 */
function RenderBeiblatt({
  graphId,
  node,
  links,
  oben,
  maxHoehe,
}: {
  graphId: string;
  node: VisNode;
  links: number;
  oben: number;
  maxHoehe: number;
}): ReactNode {
  const runCommand = useProject((s) => s.runCommand);
  const doc = useProject.getState().doc;
  const params = node.params ?? {};
  const param = (feld: string, wert: string | number | boolean) => {
    try {
      runCommand('vis.nodeParametrieren', { graphId, nodeId: node.id, params: { [feld]: wert } });
    } catch (err) {
      meldeFehler(err);
    }
  };
  const preset = RENDER_PRESETS.find((p) => p.id === params['preset']);
  const fassadenBausteine = renderPromptBausteine(doc);

  return (
    <div
      data-testid="render-beiblatt"
      className="vis-node-render-wrap"
      aria-label="Auftrag und Erklärungen"
      style={{
        position: 'absolute',
        left: links,
        top: oben,
        width: BEIBLATT_W,
        maxHeight: maxHoehe,
        overflowY: 'auto',
        boxSizing: 'border-box',
        padding: BEIBLATT_POLSTER,
        zIndex: BEIBLATT_Z,
        /* Dieselben Tokens wie die Legende-Flaeche daneben
           (`.vis-legende-panel`, `vis-visual.css`): `--k-surface` auf
           `--k-line`, Text `--k-ink-soft`. Bewusst NICHT die Kartenfarben
           (`--vis-node-flaeche`/`--vis-node-tinte`) — die sind auf
           `.vis-canvas-svg` definiert, und das Beiblatt ist dessen
           Geschwister, erbt sie also gar nicht. Ein Beiblatt ist ausserdem
           ein Bedienfeld und keine Karte; es traegt die Elevations-Logik der
           uebrigen Flaechen, die in BEIDEN Themes traegt. */
        background: 'var(--k-surface)',
        color: 'var(--k-ink-soft)',
        border: '1px solid var(--k-line)',
        borderRadius: 'var(--k-radius-sm)',
        /* VEREINIGUNG 17.09.2026: stand hier als fester Wert
           `0 6px 18px rgba(0, 0, 0, 0.28)` — schwarz, in beiden Themes gleich,
           und damit genau das, wovor der Kommentar darueber warnt. Der
           elevations-Riegel (aus dem Sammelzweig) hat es als einzigen neuen
           Fund gemeldet. `--k-shadow-overlay` ist die Stufe fuer schwebende
           Bedienfelder und traegt die Theme-Farbe mit. */
        boxShadow: 'var(--k-shadow-overlay)',
      }}
    >
      {/* Reihenfolge wie im Register (`RENDER_ZEILEN_ZUSATZ`): das Formular
          zuerst. Es traegt die fuenf Bedienelemente; muesste das Beiblatt an
          einem sehr kleinen Fenster doch einmal rollen, rollen die Erklaerungen
          weg und nicht das, was man bedient. */}
      <RenderAuftragsFormular params={params} param={param} fassadenBausteine={fassadenBausteine} />
      <RenderErklaerungen params={params} preset={preset} />
    </div>
  );
}

/** HTML-Inhalt eines Nodes — Parameter committen bei blur (nie pro Tastendruck). */
function NodeKoerper({
  graphId,
  node,
  prompt,
  material,
  eingehenderPrompt,
  lauf,
  veraltet,
  onAusfuehren,
  onFreigeben,
  onAbbrechen,
  cloudLeer,
  bildQuelle,
  aufnahmen,
  offen,
  onToggleOffen,
}: {
  graphId: string;
  node: VisNode;
  prompt: string | undefined;
  material: string | undefined;
  /** V-H4: der eingehende Prompt am Render-Node (vor dem Formular-Zusatz). */
  eingehenderPrompt: string;
  lauf: { status: string; jobId?: string; bild?: string; qa?: { verdict: { passed: boolean; reason?: string | undefined } } | undefined; fehler?: string; worker?: string; progress?: { phase: string; pct: number }; gestartetUm?: number; wartetGrund?: string | undefined } | undefined;
  veraltet: boolean;
  onAusfuehren: () => void;
  onFreigeben: () => void;
  onAbbrechen: () => void;
  cloudLeer: boolean;
  bildQuelle: (
    nodeId: string,
    port: string,
  ) => { jobId: string; bild: string; qa?: { verdict: { passed: boolean; reason?: string | undefined } } | undefined } | { dataUrl: string } | null;
  /** v0.6.7 P0: Viewport-Aufnahmen (nur der 'aufnahme'-Node zeigt sich selbst
   * daraus — Quell-Nodes ohne Eingang brauchen die rohe Ablage, nicht `bildQuelle`). */
  aufnahmen: Record<string, Aufnahme>;
  /** SK-V3: ist der Klapptext dieses Nodes offen (lokaler UI-State im Canvas). */
  offen: boolean;
  onToggleOffen: () => void;
}) {
  const runCommand = useProject((s) => s.runCommand);
  const doc = useProject.getState().doc;
  const param = (feld: string, wert: string | number | boolean) => {
    try {
      runCommand('vis.nodeParametrieren', { graphId, nodeId: node.id, params: { [feld]: wert } });
    } catch (err) {
      meldeFehler(err);
    }
  };
  // Bug T4a: ein Node OHNE `params` (Hand-Edit/Fremd-Import/Yjs-Merge von
  // einem anderen Stand) darf die Station nie abstürzen lassen — fehlende
  // Parameter zählen wie leere/Default-Werte (Wurzel-Fix in derive/visgraph.ts
  // spiegelt sich hier, weil der Node-Körper dieselben Felder direkt liest).
  const params = node.params ?? {};

  switch (node.typ) {
    case 'modell': {
      const teile = szeneBauteileAnzahl(doc);
      return <div className="vis-node-info-zeile">Szene: {teile} Bauteile (GLB)</div>;
    }
    case 'material':
      return (
        <KlappText
          testid="material"
          text={material ?? ''}
          platzhalter="keine Material-Phrasen — Wandaufbauten sprechen mit"
          offen={offen}
          onToggleOffen={onToggleOffen}
        />
      );
    case 'prompt':
      return (
        <textarea
          defaultValue={String(params['text'] ?? '')}
          key={String(params['text'] ?? '')}
          placeholder="Stil-Text …"
          rows={3}
          data-testid="prompt-text"
          onBlur={(e) => e.target.value !== params['text'] && param('text', e.target.value)}
          onPointerDown={(e) => e.stopPropagation()}
          className="vis-node-feld vis-node-feld--textarea"
        />
      );
    case 'stimmung': {
      const presetKey = String(params['preset'] ?? 'morgen');
      return (
        <div className="vis-node-stimmung-wrap">
          <KSelect
            size="sm"
            value={presetKey}
            data-testid="stimmung-preset"
            onChange={(e) => param('preset', e.target.value)}
            onPointerDown={(e) => e.stopPropagation()}
            className="vis-node-select-voll"
          >
            {Object.entries(VIS_STIMMUNGEN).map(([key, s]) => (
              <option key={key} value={key}>{s.label}</option>
            ))}
          </KSelect>
          {/* SK-V3: die Stimmungs-Beschreibung (der tatsächliche Prompt-Text
              des Presets) sichtbar — clampt wie kombinierer-prompt/material. */}
          <KlappText
            testid="stimmung-beschrieb"
            text={VIS_STIMMUNGEN[presetKey]?.prompt ?? ''}
            platzhalter="kein Beschrieb"
            offen={offen}
            onToggleOffen={onToggleOffen}
          />
        </div>
      );
    }
    case 'zahl': {
      const min = Number(params['min'] ?? 0);
      const max = Number(params['max'] ?? 1);
      const schritt = Number(params['schritt'] ?? 0.05);
      return (
        <div className="vis-node-zahl-wrap" onPointerDown={(e) => e.stopPropagation()}>
          <input
            type="range"
            key={String(params['wert'] ?? 0)}
            min={min}
            max={max}
            step={schritt}
            defaultValue={Number(params['wert'] ?? 0)}
            data-testid="zahl-regler"
            onPointerUp={(e) => param('wert', Number((e.target as HTMLInputElement).value))}
            className="vis-node-zahl-regler"
          />
          <span className="vis-node-zahl-wert">{Number(params['wert'] ?? 0)}</span>
        </div>
      );
    }
    case 'kombinierer':
      return (
        <KlappText
          testid="kombinierer-prompt"
          text={prompt ?? ''}
          platzhalter="verbinde Stimmung / Stil / Material — der finale Prompt erscheint live"
          offen={offen}
          onToggleOffen={onToggleOffen}
        />
      );
    case 'render': {
      const roh = lauf?.status ?? 'bereit';
      const status = veraltet && roh === 'fertig' ? 'veraltet' : roh;
      // Menschliche Beschriftung — der Poll/Status-Enum bleibt intern, hier
      // steht, was der Architekt lesen soll (E2E prüft genau diese Texte).
      const STATUS_LABEL: Record<string, string> = {
        bereit: 'bereit',
        gesendet: 'gesendet',
        wartetFreigabe: 'wartet auf Freigabe',
        // auf-20260901-70 (Posten 1): mit bekanntem Grund (`lauf.wartetGrund`,
        // aus `RenderJob.message`) zeigt die Badge das — ohne bleibt exakt die
        // bisherige Beschriftung (`wartetAbholerLabel` gibt dann unverändert
        // `WARTET_ABHOLER_LABEL` zurück).
        wartetGpu: wartetAbholerLabel(lauf?.wartetGrund),
        rendert: 'rendert',
        fertig: 'fertig',
        fehler: 'fehler',
        abgebrochen: 'abgebrochen',
        zeitueberschreitung: 'Zeitüberschreitung',
        veraltet: 'veraltet',
      };
      const gruen = status === 'fertig';
      const rot = status === 'fehler' || status === 'zeitueberschreitung';
      const grau = status === 'bereit' || status === 'abgebrochen';
      const statusKlasse = gruen
        ? 'vis-node-status--fertig'
        : rot
          ? 'vis-node-status--fehler'
          : grau
            ? 'vis-node-status--neutral'
            : 'vis-node-status--aktiv';
      const laeuftNoch = ['gesendet', 'wartetFreigabe', 'wartetGpu', 'rendert'].includes(status);
      // V-H4 (UI-KONZEPT-065 §5): semantisches Formular — schreibt in flache
      // Render-Node-`params` über den bestehenden `vis.nodeParametrieren`-Weg;
      // derselbe Zusammenführungs-Helfer (vis-jobs.ts) speist Anzeige UND Job.
      //
      // P16: die sechs Hilfsgroessen des Formulars (`formFassade` … und die
      // `fassadenBausteine`) sind HIER entfallen, weil das Formular hier nicht
      // mehr steht — sie leben in `RenderAuftragsFormular`/`RenderBeiblatt`.
      // Stehen geblieben waeren sie tot, und eine Leiche im Quelltext sieht
      // aus wie eine Verdrahtung. Die Zeile darunter braucht sie nicht: der
      // angezeigte Prompt kommt aus `formularZusatz(params)`, also aus
      // denselben `params`, die auch der Auftrag liest.
      const finalPrompt = kombiniertePrompt(eingehenderPrompt, formularZusatz(params));
      // P-LEERSZENE: dieselbe Zahl wie die «Szene: N Bauteile»-Anzeige am
      // Modell-Node (Kommentar an `szeneBauteileAnzahl`, vis-jobs.ts) — der
      // Knopf sperrt, statt bedienbar auszusehen und folgenlos zu bleiben.
      const keineGeometrie = szeneBauteileAnzahl(doc) === 0;
      const preset = RENDER_PRESETS.find((p) => p.id === params['preset']);
      /**
       * A15 (17.09.2026) — DIE REIHENFOLGE DES RENDER-KÖRPERS IST EIN BEFUND,
       * KEIN GESCHMACK.
       *
       * Gemessen am ausgelieferten Bündel (Fenster 1400×900, frischer
       * Render-Knoten): der Knoten ist 1016 px hoch, seine linke obere Ecke
       * landet auf der SICHTMITTE (`vis-graph-aktionen.ts` setzt sie dorthin)
       * — unter ihm liegen also nur 450 px Fenster, und davon gehen 134 px
       * für Kopf und Ports ab. Vom Körper sind 316 px zu sehen. Vier der
       * sechs Bedienelemente lagen darunter: Auflösung 904, Qualität 955,
       * Himmel 1058, Umgebung drehen 1123, Bildwerkzeug 1205.
       *
       * Daraus folgt die Reihenfolge: die sechs Bedienelemente ZUERST
       * (zusammen 258 px, also innerhalb der sichtbaren 316), danach das,
       * was man auslöst, und erst dann, was man einmal liest. Das
       * Prompt-Formular und die vier Erklärtexte liegen im Klapp-Zusatz
       * (`node-expand`, derselbe Mechanismus wie an Kombinierer/Stimmung/
       * Material) — was der Architekt bei jedem Bild anfasst, bleibt offen;
       * was er einmal liest, klappt zu.
       *
       * WAS DAS KOSTET, offen gesagt: `render-formular-fassade/-szene/
       * -jahreszeit` stehen im zugeklappten Knoten nicht im DOM. Vier
       * E2E-Stellen greifen ohne Umweg darauf zu (`kosmo-journey-efh.spec.ts`
       * :382, `kosmo-journey-mfh.spec.ts`:436/480, `vis-editor.spec.ts`:420)
       * und brauchen künftig einen Klick auf `node-expand` davor. Die
       * Playwright-Suite läuft nicht in `npm test`; das ist gemeldet, nicht
       * stillschweigend in Kauf genommen.
       */
      return (
        <div className="vis-node-render-wrap" onPointerDown={(e) => e.stopPropagation()}>
          <RenderBedienung params={params} param={param} preset={preset} />

          <Zeile id="aktionen">
            <div className="vis-node-aktionen">
              <KButton
                size="sm"
                tone="accent"
                data-testid="render-ausfuehren"
                onClick={onAusfuehren}
                disabled={laeuftNoch || cloudLeer || keineGeometrie}
                title={
                  cloudLeer
                    ? 'Kein HomeStation-Server verbunden — im Cloud-Betrieb rendert die Kette nicht lokal. Ein Cloud-Renderweg (Gemini Omni Flash, Public Preview) ist im Tech-Radar (KosmoDoc) vorgemerkt — braucht deinen Entscheid + API-Schlüssel.'
                    : keineGeometrie
                      ? KEINE_GEOMETRIE_HINWEIS
                      : undefined
                }
              >
                Ausführen
              </KButton>
              {status === 'wartetFreigabe' && (
                <KButton size="sm" tone="quiet" data-testid="render-freigeben" onClick={onFreigeben}>
                  Freigeben
                </KButton>
              )}
              {laeuftNoch && (
                <KButton size="sm" tone="ghost" data-testid="render-abbrechen" onClick={onAbbrechen}>
                  Abbrechen
                </KButton>
              )}
              <span data-testid="render-status" className={`vis-node-status k-label k-label-eng ${statusKlasse}`}>
                {STATUS_LABEL[status] ?? status}
              </span>
            </div>
          </Zeile>

          {/* A15 — derselbe Klappknopf wie an den Textkörpern (`node-expand`,
              s. `KlappText`): EIN Mechanismus, nicht ein zweiter daneben. */}
          <Zeile id="klapp">
            <button
              type="button"
              className="k-druck vis-klapptext-mehr"
              data-testid="node-expand"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={onToggleOffen}
            >
              {offen ? 'weniger' : '… mehr (Auftrag und Erklärungen)'}
            </button>
          </Zeile>

          {/* P16 (17.09.2026) — HIER STAND DER ZUSATZ, UND GENAU DAS WAR DER
              BEFUND. `{offen && <RenderErklaerungen …>}` und das
              Auftrags-Formular haben die Karte von 580 auf 1099 px wachsen
              lassen; gemessen lagen damit bei ALLEN fuenf Fenstergroessen
              (1280x720 … 1920x1080) 7 von 15 Bedienelementen unter dem
              Fensterrand. Beides steht jetzt im `RenderBeiblatt` neben der
              Karte — gleicher Knopf (`node-expand`), gleiche testids,
              gleiche Inhalte, nur nicht mehr in einem Behaelter, der hoeher
              werden kann als das Fenster. Die Karte bleibt in BEIDEN
              Klappzustaenden 580 px. */}


          {/* HS5 «nur Cycles» (reines Cycles statt KI-Veredelung) und v0.8.11 Z4
              «Line-Art» (persistenter Node-Parameter `lineart`, den
              `sendeGraphRenderAuftrag` als `vis.skip:true` HART erzwingt) —
              A15: eine Zeile statt zwei. Die volle Erklärung beider Schalter
              steht im aufgeklappten Ehrlichkeits-Absatz UND hier am `title`;
              weggelassen ist sie nirgends. */}
          <Zeile id="schalter">
            {/* Abstands-Gate (Befund 17.09.2026): 'gap: 3px 12px' lag
                ausserhalb der Skala --k-s1..--k-s10. 12px = --k-s4,
                unveraendert. 3px liegt genau in der Mitte zwischen --k-s1
                (2px) und --k-s2 (4px); Owner-Entscheid: bei genauer Mitte
                den KLEINEREN Wert nehmen -> --k-s1 (2px). Geprueft:
                --k-s1/--k-s4 stehen auf :root in
                packages/kosmo-ui/src/aura.css, dieses style-Objekt liegt in
                einem React-Baum unter document.body, also ist :root immer
                Vorfahre -> var(...) loest auf. */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--k-s1) var(--k-s4)', minWidth: 0 }}>
              <KTooltip text="nur Cycles — keine KI-Veredelung">
                <label className="vis-node-checkbox-label">
                  <input
                    type="checkbox"
                    data-testid="render-nur-cycles"
                    checked={params['nurCycles'] === true}
                    onChange={(e) => param('nurCycles', e.target.checked)}
                  />
                  nur Cycles
                </label>
              </KTooltip>
              <KTooltip text="als Strichzeichnung (Line-Art)">
                <label className="vis-node-checkbox-label">
                  <input
                    type="checkbox"
                    data-testid="render-lineart"
                    checked={params['lineart'] === true}
                    onChange={(e) => param('lineart', e.target.checked)}
                  />
                  Strichzeichnung
                </label>
              </KTooltip>
            </div>
          </Zeile>

          {/* Ehrlichkeit/V8: der TATSÄCHLICHE Prompt, den «Ausführen» sendet.
              A15: bleibt IMMER stehen — ein Knopf, der etwas absendet, und
              kein Ort, an dem steht, WAS, wäre genau die Lücke, gegen die
              diese Zeile gebaut wurde. Auf ZWEI Zeilen geklammert, in beiden
              Klappzuständen gleich: ein Prompt ist beliebig lang, und eine
              Zeile, deren Höhe am Text hängt, macht jede Registerzahl falsch.
              Der volle Wortlaut steht am `title` und im Inspektor. */}
          <Zeile id="prompt">
            <div
              data-testid="render-final-prompt"
              className="vis-node-final-prompt"
              style={KLEMME_TEXT_ZWEIZEILIG}
              title={finalPrompt || undefined}
            >
              {finalPrompt || 'kein Prompt — verbinde Stimmung/Stil oder fülle das Formular'}
            </div>
          </Zeile>

          <Zeile id="bild">
            {status === 'fertig' && lauf?.jobId && lauf.bild ? (
              /* A15 — das Bild wird auf die registrierte Zeilenhöhe GEDECKELT.
                 Ohne Deckel folgt seine Höhe dem Seitenverhältnis (184 px
                 breit: 16:10 ergibt 117 px, ein quadratisches Bild 186) — die
                 Zeile `bild` im Register wäre dann für manche Bilder zu klein
                 und schnitte still ab, genau die Klasse Fehler, gegen die das
                 Register steht. `BridgeBild` reicht `style` an das `<img>`
                 durch (`BridgeBild.tsx`:74). */
              <BridgeBild
                jobId={lauf.jobId}
                imageName={lauf.bild}
                alt="Render"
                testid="render-bild"
                className="vis-img-full"
                style={{ maxHeight: 110, width: 'auto', maxWidth: '100%', display: 'block', marginInline: 'auto' }}
              />
            ) : (
              /* A15 — OHNE Lauf ein Streifen statt eines 110 px hohen leeren
                 Rahmens. Gemessen: der leere Rahmen war der grösste einzelne
                 Block des frischen Knotens und zeigte nichts. Sobald ein Lauf
                 hängt (auch ein fehlgeschlagener), steht der volle Rahmen da —
                 dann gibt es etwas zu zeigen. Die Höhe beider Zustände steht
                 im Register (`bild`: 24 / 110). */
              <div
                className={`vis-node-leerbild${rot ? ' vis-node-leerbild--fehler' : ''}${status === 'wartetGpu' && lauf?.wartetGrund ? ' vis-node-leerbild--grund-bekannt' : ''}`}
                /* Abstands-Gate (Befund 17.09.2026): 'padding: 4px 6px' lag
                   ausserhalb der Skala --k-s1..--k-s10. 4px = --k-s2,
                   unveraendert. 6px liegt genau in der Mitte zwischen
                   --k-s2 (4px) und --k-s3 (8px); Owner-Entscheid: bei
                   genauer Mitte den KLEINEREN Wert nehmen -> --k-s2 (4px).
                   Geprueft: --k-s2 steht auf :root in
                   packages/kosmo-ui/src/aura.css, dieses style-Objekt liegt
                   in einem React-Baum unter document.body, also ist :root
                   immer Vorfahre -> var(...) loest auf. */
                {...(lauf ? {} : { style: { height: 'auto', padding: 'var(--k-s2) var(--k-s2)', textAlign: 'left' as const } })}
                data-testid={status === 'wartetGpu' ? 'render-wartet-text' : undefined}
                data-grund-bekannt={status === 'wartetGpu' ? String(!!lauf?.wartetGrund) : undefined}
              >
                <span style={KLEMME_TEXT}>
                  {rot
                    ? (lauf?.fehler ?? 'Render fehlgeschlagen')
                    : status === 'fertig'
                      ? 'fertig — aber kein Bild geliefert'
                      : status === 'wartetFreigabe'
                        ? 'wartet auf Freigabe — «Freigeben» startet den Render'
                        : status === 'wartetGpu'
                          ? wartetAbholerText(lauf?.gestartetUm, Date.now(), lauf?.wartetGrund)
                          : status === 'abgebrochen'
                            ? 'abgebrochen'
                            : lauf
                              ? 'rendert im GPU-Leerlauf …'
                              : cloudLeer
                                ? 'Cloud-Betrieb: kein lokaler Render. Geprüfter Cloud-Weg (Gemini Omni Flash, Preview) wartet auf Owner-Entscheid + Schlüssel — siehe KosmoDoc → Tech-Radar.'
                                : 'Bild erscheint hier'}
                  {/* Worker + Fortschritt, sobald der Worker den Job hält
                      (HS3-Auflage 5). A15: IM Platzhalter statt als eigene
                      Zeile — eine Zeile, die nur manchmal da ist, macht die
                      Knotenhöhe von einem Zustand abhängig, den die
                      Platzsuche nicht kennt. */}
                  {(lauf?.worker || lauf?.progress) && (status === 'rendert' || status === 'wartetGpu') && (
                    <span data-testid="render-fortschritt" className="vis-node-fortschritt">
                      {` · ${lauf.worker ?? 'worker'}`}
                      {lauf.progress ? ` · ${lauf.progress.phase} ${Math.round(lauf.progress.pct * 100)}%` : ''}
                    </span>
                  )}
                </span>
              </div>
            )}
          </Zeile>
        </div>
      );
    }
    case 'vergleich': {
      const bilder = ['bild1', 'bild2', 'bild3']
        .map((p) => bildQuelle(node.id, p))
        .filter((b): b is NonNullable<typeof b> => b !== null);
      return (
        <div className="vis-vergleich-bilder" data-testid="vergleich-bilder">
          {bilder.length === 0 && (
            <div className="vis-vergleich-leer">
              {/* Kritik-065 Runde 1, Befund 5: Leerzustand-Signet — zwei
                  überlappende Bildrahmen statt reiner Textwüste. */}
              <svg width="28" height="22" viewBox="0 0 28 22" aria-hidden focusable="false">
                <rect x="0.75" y="4.75" width="17.5" height="13.5" rx="1.5" fill="none" stroke="var(--k-ink-faint)" strokeWidth="1.5" />
                <rect x="9.75" y="0.75" width="17.5" height="13.5" rx="1.5" fill="var(--k-raised)" stroke="var(--k-ink-faint)" strokeWidth="1.5" />
                <circle cx="14.75" cy="5.25" r="1.4" fill="none" stroke="var(--k-ink-faint)" strokeWidth="1.2" />
                <path d="M11 11 L15.5 6.5 L19.5 10.5 L22.5 7.5 L26.25 11" fill="none" stroke="var(--k-ink-faint)" strokeWidth="1.2" strokeLinejoin="round" strokeLinecap="round" />
              </svg>
              verbinde Render-Bilder
            </div>
          )}
          {bilder.map((b, i) =>
            'dataUrl' in b ? (
              // v0.6.7 P0: Viewport-Aufnahme — keine Bridge, direktes <img> (wie
              // der 'referenz'-Node bei einer data:-URL, s.u.).
              <div key={i} className="vis-bild-kachel">
                <img src={b.dataUrl} alt={`Bild ${i + 1}`} className="vis-img-full" />
              </div>
            ) : (
              <BildKachel key={i} jobId={b.jobId} bild={b.bild} qa={b.qa} alt={`Bild ${i + 1}`} />
            ),
          )}
        </div>
      );
    }
    case 'blatt': {
      const quelle = bildQuelle(node.id, 'bild');
      return (
        <div onPointerDown={(e) => e.stopPropagation()}>
          <KButton
            size="sm"
            tone="quiet"
            data-testid="blatt-ablegen"
            disabled={!quelle}
            onClick={() => {
              if (!quelle) return;
              const titel = String(params['titel'] ?? 'Visualisierung');
              // v0.6.7 P0: eine Viewport-Aufnahme braucht keinen Bridge-Fetch
              // (die dataURL liegt schon lokal vor) — sonst derselbe Weg.
              const ablage = 'dataUrl' in quelle ? aufnahmeAufsBlatt(quelle.dataUrl, titel) : bildAufsBlatt(quelle.jobId, quelle.bild, titel);
              // P5b (v0.9.56): der `bildAufsBlatt`-Zweig ist ein Bridge-Fetch
              // (Aufnahme-Zweig nicht) — derselbe Uebersetzer fuer beide, weil
              // `bescheidFuerBridgeFehler` einen Nicht-Netzfehler unveraendert
              // als Rohtext zurueckgibt (bridge-bescheid.ts, Fall `roh`).
              void ablage
                .then((name) => melde(`Render liegt auf «${name}» — im KosmoPublish weiterschieben`, { ton: 'erfolg' }))
                .catch(bescheideBridgeCatch);
            }}
          >
            Aufs Blatt
          </KButton>
        </div>
      );
    }
    case 'referenz': {
      const url = String(params['url'] ?? '');
      return (
        <div className="vis-node-referenz-wrap" onPointerDown={(e) => e.stopPropagation()}>
          <input
            defaultValue={url}
            key={url}
            placeholder="Bild-URL / data:-URL"
            onBlur={(e) => e.target.value !== url && param('url', e.target.value)}
            className="vis-node-feld"
          />
          {url ? (
            <img src={url} alt="Referenz" className="vis-img-full" />
          ) : (
            <div className="vis-node-referenz-leer">
              Referenz / Splat-Ansicht
            </div>
          )}
        </div>
      );
    }
    case 'aufnahme': {
      // v0.6.7 P0 — ECHTE lokale Bildquelle: das Bild kommt vom «Für Vis
      // aufnehmen»-Knopf im 3D-Viewport (Viewport3D.tsx, testid
      // viewport-aufnahme), NICHT von hier. KosmoVis kann selbst nicht in den
      // 3D-Viewport blicken (Viewport3D mountet nur in KosmoDesign, App.tsx
      // hält Design/Vis als sich ausschliessende Stationen) — «Aufnehmen»
      // hier wechselt DESHALB bewusst NICHT die Station (Vis bleibt offen,
      // Owner-Vorgabe), sondern sagt ehrlich, wo der Knopf wirklich sitzt.
      // Das Bild selbst lebt NUR in vis-runtime (entities.ts:500-505: Render-
      // Graph-Bilder gehen nie durchs Doc/Undo/Yjs) — dieselbe Regel wie beim
      // 'render'-Node.
      const kameraParam = String(params['kamera'] ?? 'aktuell');
      const gewaehlt = waehleAufnahme(aufnahmen, kameraParam);
      return (
        <div className="vis-node-aufnahme-wrap" onPointerDown={(e) => e.stopPropagation()}>
          <div className="vis-node-aufnahme-info">Viewport-Aufnahme (kein Rendering)</div>
          <KSelect
            size="sm"
            value={kameraParam}
            data-testid="aufnahme-kamera"
            onChange={(e) => param('kamera', e.target.value)}
            onPointerDown={(e) => e.stopPropagation()}
            className="vis-node-select-voll"
          >
            <option value="aktuell">jüngste Aufnahme</option>
            <option value="nordost">Nordost</option>
            <option value="sued">Süd</option>
          </KSelect>
          {gewaehlt ? (
            <img
              src={gewaehlt.dataUrl}
              alt="Viewport-Aufnahme"
              data-testid="aufnahme-bild"
              className="vis-img-full"
            />
          ) : (
            <div className="vis-node-aufnahme-leer">
              Noch keine Aufnahme
            </div>
          )}
          <KButton
            size="sm"
            tone="ghost"
            data-testid="aufnahme-ausfuehren"
            onClick={() =>
              melde(
                // B78 (a) / C-9: der Hinweis nennt jetzt BEIDE Orte, an denen es
                // «Für Vis aufnehmen» wirklich gibt. Bis B78 nannte er nur die
                // klassische Viewport-Ecke — die im Island-Modus (dem
                // ausgelieferten Zustand) gar nicht rendert; der Satz schickte den
                // Nutzer damit auf eine Suche, die nicht enden konnte. Nachgezogen
                // wurde der TEXT, nicht der Knopf.
                'Öffne kurz KosmoDesign und klicke «Für Vis aufnehmen» — im 3D-Viewport unten rechts oder in der AUSTAUSCH-Insel unter «Rendern». Vis bleibt offen, das Bild landet automatisch hier.',
                { ton: 'info' },
              )
            }
          >
            Aufnehmen
          </KButton>
        </div>
      );
    }
    case 'kamera': {
      // Reine Anzeige — live aus den aktuellen Modell-Bounds abgeleitet,
      // nie gespeichert (wie der Material-Node). Ehrlich: «Vorschlag aus dem
      // Modell», keine KI-Wahl.
      // 12.09.2026: `projektKameras` statt `deriveAutoKameras` — dieselbe
      // Ableitung, davor die von Hand gesetzten, aus einer 3DS-Datei
      // uebernommenen Standpunkte (`doc.settings.uebernommeneKameras`). Die
      // Anzeige MUSS dieselbe Quelle lesen wie der Auftrag (`visgraph.ts`),
      // sonst verspricht die Oberflaeche wieder etwas anderes, als die
      // Leitung traegt — der Befund, der `istUeberDiesenWegBestellbar`
      // ueberhaupt erzwungen hat.
      const kameras = projektKameras(doc);
      const uebernommen = new Set((doc.settings.uebernommeneKameras ?? []).map((k) => k.name));
      // B117 SCHRITT 2 (Owner-Entscheid E57): dieselbe Bedingung wie im
      // Auftrag (`vis-jobs.ts` `postRenderJob`) — EINE Funktion, nicht zwei
      // gleichlautende Pruefungen (s. Kommentar an `istUeberDiesenWegBestell
      // bar` in vis-jobs.ts).
      const interiorMoeglich = interiorFaehrt(doc);
      return (
        <div className="vis-node-kamera-liste" data-testid="vis-auto-kamera-liste">
          {kameras.length === 0 ? (
            <span className="vis-node-kamera-leer">
              Keine Geometrie im Modell — nichts abzuleiten.
            </span>
          ) : (
            kameras.map((k) =>
              uebernommen.has(k.name) ? (
                /* Ein uebernommener Standpunkt ist KEIN «Vorschlag aus dem
                   Modell» — das waere schlicht falsch, nichts an ihm ist
                   abgeleitet. Und ob er zu DIESEM Modell gehoert, wird
                   gemessen statt angenommen: die 3DS-Datei bringt ihren
                   eigenen Nullpunkt mit (`augeImModell`, `derive/kamera.ts`).
                   Ein Auge ausserhalb der Huellbox ist genau der Fall, der am
                   26.08.2026 ein Bild 60 m neben dem Bau erzeugt hat — hier
                   steht er, statt still zu passieren. */
                <KTooltip key={k.name} text={k.begruendung}>
                  <div data-testid={`vis-kamera-uebernommen-${k.name}`}>
                    <b>{k.name}</b> — von Hand gesetzt, übernommen
                    {augeImModell(doc, k.position) === false && (
                      <span className="vis-node-kamera-nicht-bestellt">
                        {' '}· Auge ausserhalb dieses Modells
                      </span>
                    )}
                  </div>
                </KTooltip>
              ) : istUeberDiesenWegBestellbar(k.name, interiorMoeglich) ? (
                <KTooltip key={k.name} text={k.begruendung}>
                  <div>
                    <b>{k.name}</b> — Vorschlag aus dem Modell
                  </div>
                </KTooltip>
              ) : (
                /* P-DREISTANDPUNKTE-Nachtrag (v0.9.46, ROADMAP 1074): der
                   Standpunkt wird zu Recht abgeleitet, ueber DIESEN Weg aber
                   nicht bestellt (er sendet immer glb und nie ein
                   `interior`-Feld; Innenansichten haengen seit P-INTERIOR
                   hart an beidem). Bis eben zeigte das Panel ihn wie jeden
                   anderen — der Knoten versprach also weiter mehr, als er
                   bestellt, nur lag die Luecke nach dem Auftrags-Fix in der
                   ANZEIGE statt im Auftrag. NICHT verstecken, sondern die
                   Grenze benennen: der Vorschlag ist echt und ueber den
                   IFC-Weg erreichbar — hier ist er es nicht. Deklarierte
                   Grenze statt Attrappe, dieselbe Linie wie ueberall sonst
                   in diesem Programm. */
                <div key={k.name} className="vis-node-kamera-nicht-bestellt" title={k.begruendung}>
                  <b>{k.name}</b> — abgeleitet, ueber diesen Weg nicht bestellbar (braucht IFC)
                </div>
              ),
            )
          )}
        </div>
      );
    }
    default:
      return null;
  }
}
