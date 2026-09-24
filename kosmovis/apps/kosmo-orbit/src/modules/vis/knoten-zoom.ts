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
