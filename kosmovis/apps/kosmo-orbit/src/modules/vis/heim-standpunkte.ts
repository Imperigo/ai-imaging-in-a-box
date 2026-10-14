/**
 * HEIM-STANDPUNKTE — was die Auto-Kamera zeigt, wenn der WIRT die Standpunkte des
 * Heim-PCs kennt (Owner-Entscheid 92 der Visbox, 14.10.2026, Blatt 23).
 *
 * - **In KosmoOrbit** leitet die Auto-Kamera ihre Standpunkte aus dem Entwurf ab
 *   (`projektKameras`, Eingang/Übersicht/Innenraum), und sie reisen im Auftrag mit.
 *   Niemand registriert hier etwas; der Knoten bleibt, wie er war.
 * - **In Visbox** gibt es keinen Entwurf: `projektKameras` ist leer, der Auftrag traegt
 *   `cameras: 'auto'`, und der Heim-PC rechnet drei feste Richtungen (Süd, Südost,
 *   Nordwest, `abholer.AUTO_RICHTUNGEN`). Visbox holt diese drei vom eigenen Server — aus
 *   derselben Rechnung, die der Heim-PC fährt (`knotenweg.heim_standpunkte`) — und
 *   registriert sie hier. Der Knoten zeigt sie dann als **Vorschau**.
 *
 * **Warum Vorschau und nicht Bestellung:** Mitgeschickt wuerden sie als feste Standpunkte
 * gerechnet — ohne den Objektiv-Shift, mit dem der Heim-PC senkrechte Kanten senkrecht
 * haelt (der Vertrag `CameraSpec` kennt keinen Shift). Das Bild waere ein anderes. Der
 * Auftrag bleibt darum `auto`; angezeigt wird, was `auto` am Heim-PC heisst.
 *
 * Kein React im Kern: ein kleiner Speicher mit Hoerern wie `modell-laden.ts`.
 */

export interface HeimStandpunkt {
  /** Richtungskuerzel des Heim-PCs (`s`, `sSE`, `nNW`). */
  kuerzel: string;
  /** Für einen Menschen: «Süd», «Südost», «Nordwest». */
  name: string;
  /** «frontal» oder «über Eck». */
  art: string;
  /** Abstand vom Bauwerk, Meter — vor dem Zurueckziehen einer verdeckten Kamera. */
  abstand_m: number;
  /** Weltkoordinaten des Heim-PCs: Meter, Z OBEN (nicht glTF). */
  auge: [number, number, number];
  blick_auf: [number, number, number];
  vollstaendig: boolean;
  begruendung: string;
}

export interface HeimStandpunkte {
  standpunkte: HeimStandpunkt[];
  /** Woher sie kommen bzw. warum keine — steht unter der Liste. */
  satz: string;
}

let stand: HeimStandpunkte | null = null;
const hoerer = new Set<() => void>();

/** Der Wirt setzt die Standpunkte der offenen Mappe — `null`: es gibt keine (KosmoOrbit). */
export function registriereHeimStandpunkte(neu: HeimStandpunkte | null): void {
  stand = neu;
  for (const h of hoerer) h();
}

export function heimStandpunkte(): HeimStandpunkte | null {
  return stand;
}

export function abonniereHeimStandpunkte(h: () => void): () => void {
  hoerer.add(h);
  return () => {
    hoerer.delete(h);
  };
}
