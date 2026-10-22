/**
 * **Zoom am Zeiger fuer den Knotengraph** (P-KNOTEN-ZOOM, 09.09.2026).
 *
 * ## Der Befund
 *
 * Das Mausrad im Knotengraph zoomte **zur Mitte der Flaeche**, nicht dorthin,
 * wo der Zeiger stand: `setView((v) => ({ ...v, scale: … }))` aenderte
 * ausschliesslich den Massstab und liess den Mittelpunkt stehen. Wer einen
 * Knoten am Rand vergroessern wollte, schob ihn damit aus dem Bild und musste
 * hinterherziehen.
 *
 * **Die Plansicht macht es seit Langem richtig** (`navigation-geste.ts`,
 * `zoomKameraAnPunkt`) — der Knotengraph war die Ausnahme, nicht die Regel.
 * Uebernommen wird die Idee, nicht die Funktion: jene rechnet in
 * Plan-Koordinaten mit **umgekehrter y-Achse** (`cy - py/scale + py/scale`),
 * der Knotengraph in Bildschirmrichtung. Ein Import haette das Vorzeichen
 * mitgeschleppt und den Zeiger senkrecht spiegelverkehrt verfolgt.
 *
 * ## Die Rechnung
 *
 * Die Ansicht bildet Welt auf Bildschirm ueber
 * `viewBox = (cx - b/2, cy - h/2, b, h)` mit `b = flaeche.b / scale` ab; ein
 * Bildschirmpunkt `d` Pixel neben der Flaechenmitte liegt also auf dem
 * Weltpunkt `cx + d / scale`.
 *
 * Damit derselbe Weltpunkt nach dem Zoom wieder unter dem Zeiger liegt:
 *
 *     cx + d/alt = cx' + d/neu   →   cx' = cx + d * (1/alt - 1/neu)
 *
 * Beide Achsen gleich, weil beide gleich orientiert sind.
 */

export interface KnotenAnsicht {
  readonly cx: number;
  readonly cy: number;
  readonly scale: number;
}

/**
 * Neuer Ansichtszustand nach einem Zoom um `faktor`, verankert am Punkt
 * `(dx, dy)` — beides Bildschirm-Pixel **relativ zur Mitte der Zeichenflaeche**
 * (rechts/unten positiv).
 *
 * `dx = 0, dy = 0` ist der Knopf-Fall (`+`/`-`): dort ist der Anker die Mitte,
 * und die Rechnung faellt auf den alten, reinen Massstabswechsel zurueck — kein
 * Sonderweg noetig, dieselbe Funktion.
 *
 * Klemmt an `min`/`max`. Ist der Massstab bereits an der Grenze, bleibt die
 * Ansicht **unveraendert** (identische Referenz) — sonst wanderte der Ausschnitt
 * am Anschlag weiter, obwohl sichtbar nichts passiert.
 */
export function zoomAmZeiger(
  v: KnotenAnsicht,
  faktor: number,
  dx: number,
  dy: number,
  grenzen: { min: number; max: number },
): KnotenAnsicht {
  const neu = Math.min(grenzen.max, Math.max(grenzen.min, v.scale * faktor));
  if (neu === v.scale) return v;
  const differenz = 1 / v.scale - 1 / neu;
  return { cx: v.cx + dx * differenz, cy: v.cy + dy * differenz, scale: neu };
}

/**
 * **Verstaerkung je Zoom-Schritt** (Owner 14.10.2026, in der Mac-App von Visbox: «das Scrollen
 * ist sehr traege, man muss viel scrollen, um naeher an die Knoten zu kommen oder
 * rauszuzoomen»). Mausrad, Pinch in Chromium (`wheel` + ctrlKey) und Pinch in WebKit liefern
 * je Ereignis einen Faktor; er wird hier potenziert. Mit 2.5 zoomt ein Mausrad-Notch
 * (deltaY 100) um rund 26 % statt 11 %, und ein Pinch wirkt entsprechend staerker.
 *
 * Gilt nur fuer den Knotengraph — Grundriss, Schnitt und Tafeln behalten ihre Werte
 * (`navigation-geste.ts`, nicht Teil des Vis-Werkzeugs).
 */
export const KNOTEN_ZOOM_VERSTAERKUNG = 2.5;

/** Der Faktor eines Zoom-Schritts, verstaerkt um {@link KNOTEN_ZOOM_VERSTAERKUNG}. */
export function verstaerkterFaktor(faktor: number): number {
  if (!Number.isFinite(faktor) || faktor <= 0) return 1;
  return Math.pow(faktor, KNOTEN_ZOOM_VERSTAERKUNG);
}

/**
 * **Wie die Knotenebene ihre Zoomstufe traegt** (Owner-Funde Mac 22.10.2026, Visbox 0.3.33 und 0.3.35).
 *
 * ## Die Befunde
 *
 * 1. (0.3.33) Seit L69 (20.10.2026) sass die Zoomstufe als CSS `zoom` an der Knotenebene. `zoom`
 *    legt den Inhalt in der gezoomten Groesse NEU aus, und unter 1 hielt die Mindestschrift der
 *    Engine (WebKit 9 px) die Schrift gross, waehrend der Rahmen schrumpfte. Behoben mit
 *    `transform: scale()` unter 1 — aber ab 1 blieb `zoom`.
 * 2. (0.3.35) «Die Schrift ist nicht fixiert an den Knoten, sie jittert und aendert teils die
 *    Groesse.» Drei Ursachen, gemessen in `e2e/kv-zoom-schrift.spec.ts`:
 *    * **Neu-Auslegen je Zoomschritt ab 1.** Mit `zoom` rechnet die Engine Breiten, Raender,
 *      Zeilenhoehen und Glyphen bei jeder Stufe neu und rundet sie neu — Textbreiten, Umbrueche und
 *      Knotenhoehen springen von Schritt zu Schritt.
 *    * **Wegwechsel bei 1.** Unter 1 Skalierung einer festen Auslegung, ab 1 Neu-Auslegen: beim
 *      Pinch ueber 1 wechselte die Auslegung mitten in der Geste.
 *    * **SVG-Schrift in Bildschirmgroesse.** Kopfzeile und Anschlussnamen sind SVG-`<text>`. WebKit
 *      und Chromium legen SVG-Text in der Schriftgroesse AM BILDSCHIRM aus (Schrift × Massstab,
 *      gerundet, mit Mindestschrift) und rechnen dann zurueck — bei jedem Massstab anders, egal ob
 *      `zoom` oder `scale()`. Gemessen (Chromium): die Kopfzeile «Prompt» ist bei 0,5 relativ zum
 *      Knoten 8 % hoeher und 4 % breiter als bei 1. Abhilfe: `text-rendering: geometricPrecision`
 *      an der Knoten-SVG (`vis-visual.css`) — die Engines legen SVG-Text dann in der eigenen
 *      Groesse aus und skalieren die Zeichnung.
 *
 * ## Die Regel (Owner-Leitsatz «Der Knoten ist eine Zeichnung im Massstab», Entscheid 130, R1)
 *
 * **Ein Weg fuer alle Stufen.** Die Ebene wird in einem ganzzahligen Massstab `raster` ausgelegt
 * (CSS `zoom: raster`) und als Ganzes mit `transform: scale(stufe / raster)` auf die Stufe gebracht.
 * Rahmen und Schrift wachsen mit EINEM Faktor wie eine Zeichnung; waehrend der Geste aendert sich
 * an der Auslegung nichts.
 *
 * * `raster` ist **ganzzahlig** (1 … 4): ein ganzzahliger `zoom` verdoppelt/verdreifacht jedes Mass
 *   exakt, die Auslegung ist bei 2 dieselbe Zeichnung wie bei 1, nur feiner gerastert.
 * * **Schaerfe erst in der Ruhe.** Hineinzoomen hebt `raster` erst, wenn der Zoom
 *   {@link ZOOM_RUHE_MS} ms ruht — einmal, nach der Geste (dann rastert WebKit die Ebene in der
 *   passenden Aufloesung neu, statt eine Bitmap aufzuziehen; L69). Herauszoomen senkt `raster`
 *   sofort, damit eine gezoomte Ebene nie in vielfacher Aufloesung im Speicher liegt.
 * * Zeiger, Draehte und Treffer rechnen weiter ueber die Ansicht (`view`), nie ueber Knoten-Masse;
 *   HTML-Treffer folgen der Transformation von selbst. Die wirksame Stufe steht in
 *   `data-knoten-zoom`, das Raster in `data-knoten-raster`.
 */
export interface KnotenEbenenStil {
  readonly zoom: number;
  readonly transform: string;
  readonly transformOrigin: string;
}

/** Ruhezeit nach dem letzten Zoomschritt, bevor die Ebene schaerfer gerastert wird. */
export const ZOOM_RUHE_MS = 150;

/** Feinstes Raster (= hoechste Zoomstufe der Knotenansicht, `ZOOM_MAX` in NodeCanvas). */
export const RASTER_MAX = 4;

function gueltig(s: number): number {
  return Number.isFinite(s) && s > 0 ? s : 1;
}

/** Ganzzahliges Raster fuer eine Stufe: die naechste ganze Zahl darueber, 1 … {@link RASTER_MAX}. */
export function rasterStufe(stufe: number): number {
  const s = gueltig(stufe);
  return Math.min(RASTER_MAX, Math.max(1, Math.ceil(s - 1e-9)));
}

/**
 * Raster waehrend einer Geste: in der Ruhe gewaehlt ({@link rasterStufe} der Ruhestufe), beim
 * Herauszoomen sofort gesenkt, beim Hineinzoomen erst nach der Ruhe gehoben.
 */
export function rasterInGeste(stufe: number, ruheStufe: number): number {
  return Math.min(rasterStufe(ruheStufe), rasterStufe(stufe));
}

export function knotenEbenenStil(scale: number, raster: number = rasterStufe(scale)): KnotenEbenenStil {
  const s = gueltig(scale);
  const r = Math.min(RASTER_MAX, Math.max(1, Math.round(gueltig(raster))));
  return { zoom: r, transform: `scale(${s / r})`, transformOrigin: '0 0' };
}
