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
/** Zählt jede Meldung — der Schnappschuss für `useSyncExternalStore` (Knoten «Kamera»). */
let fassung = 0;
function meldeAlle(): void {
  fassung++;
  for (const h of hoerer) h();
}
export function heimStandpunkteFassung(): number {
  return fassung;
}

/** Der Wirt setzt die Standpunkte der offenen Mappe — `null`: es gibt keine (KosmoOrbit). */
export function registriereHeimStandpunkte(neu: HeimStandpunkte | null): void {
  stand = neu;
  meldeAlle();
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

// ─────────────────────────────────────────────────────────────────────────────
// Bauplan «Neue Knoten» F2 (Entscheide 109/113 (3), 21.10.2026): die Standpunkte MIT den
// Einstellungen des Knotens «Kamera» (Richtungen, Augenhöhe, Brennweite, Abstand, Perspektive).
// Rechnen tut der Heim-PC — eine Rechnung für beide Programme. Der Wirt meldet eine Abfrage an
// (Visbox: `GET ./standpunkte?…`, `knotenweg.standpunkte_abfrage`); ohne Abfrage (KosmoOrbit)
// zeigt der Knoten die Standpunkte erst, wenn der Heim-PC gerechnet hat.
// ─────────────────────────────────────────────────────────────────────────────

/** Die Einstellungen, wie der Vertrag sie trägt (`RenderScene.cameras_auto`). */
export interface StandpunkteWahl {
  richtungen: readonly string[];
  augenhoehe_m?: number;
  brennweite_mm?: number;
  abstand?: { art: 'auto'; fuellt?: number } | { art: 'fest'; meter: number };
  perspektive?: 'senkrecht' | 'frei';
}

export type StandpunkteAbfrage = (wahl: StandpunkteWahl) => Promise<HeimStandpunkte | null>;

let abfrage: StandpunkteAbfrage | null = null;

interface AbfrageEintrag {
  stand: 'laedt' | 'da' | 'fehler';
  ergebnis: HeimStandpunkte | null;
  satz?: string;
}
const zwischenspeicher = new Map<string, AbfrageEintrag>();
const ZWISCHENSPEICHER_HOECHSTENS = 24;

/** Der Wirt meldet seine Abfrage an (`null`: keine, wie in KosmoOrbit). Leert den Speicher. */
export function registriereStandpunkteAbfrage(neu: StandpunkteAbfrage | null): void {
  abfrage = neu;
  zwischenspeicher.clear();
  meldeAlle();
}

export function hatStandpunkteAbfrage(): boolean {
  return abfrage !== null;
}

/** Der Schlüssel einer Wahl — dieselbe Wahl fragt nur einmal. */
export function wahlSchluessel(wahl: StandpunkteWahl): string {
  return JSON.stringify([
    [...wahl.richtungen],
    wahl.augenhoehe_m ?? null,
    wahl.brennweite_mm ?? null,
    wahl.abstand ?? null,
    wahl.perspektive ?? null,
  ]);
}

/** Die Frage an den Wirt als Suchteil einer Adresse (`richtungen=s,sSE&augenhoehe=1.7&…`). */
export function standpunkteSuchteil(wahl: StandpunkteWahl): string {
  const q = new URLSearchParams();
  q.set('richtungen', wahl.richtungen.join(','));
  if (wahl.augenhoehe_m !== undefined) q.set('augenhoehe', String(wahl.augenhoehe_m));
  if (wahl.brennweite_mm !== undefined) q.set('brennweite', String(wahl.brennweite_mm));
  if (wahl.abstand?.art === 'fest') q.set('abstand', String(wahl.abstand.meter));
  else if (wahl.abstand?.art === 'auto' && wahl.abstand.fuellt !== undefined) q.set('fuellt', String(wahl.abstand.fuellt));
  if (wahl.perspektive) q.set('perspektive', wahl.perspektive);
  return q.toString();
}

/**
 * Die Standpunkte für eine Wahl: aus dem Speicher, sonst wird gefragt und die Hörer hören, wenn
 * die Antwort da ist. `null` ohne Abfrage (KosmoOrbit).
 */
export function standpunkteFuer(wahl: StandpunkteWahl): AbfrageEintrag | null {
  if (!abfrage) return null;
  const schluessel = wahlSchluessel(wahl);
  const da = zwischenspeicher.get(schluessel);
  if (da) return da;
  const eintrag: AbfrageEintrag = { stand: 'laedt', ergebnis: null };
  zwischenspeicher.set(schluessel, eintrag);
  if (zwischenspeicher.size > ZWISCHENSPEICHER_HOECHSTENS) {
    const aeltester = zwischenspeicher.keys().next().value;
    if (aeltester !== undefined) zwischenspeicher.delete(aeltester);
  }
  const frage = abfrage;
  void frage(wahl).then(
    (ergebnis) => {
      zwischenspeicher.set(schluessel, { stand: 'da', ergebnis });
      meldeAlle();
    },
    (e: unknown) => {
      zwischenspeicher.set(schluessel, { stand: 'fehler', ergebnis: null, satz: e instanceof Error ? e.message : String(e) });
      meldeAlle();
    },
  );
  return eintrag;
}
