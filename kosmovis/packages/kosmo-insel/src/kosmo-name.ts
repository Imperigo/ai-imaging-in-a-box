/**
 * **Der Name des Assistenten neben Claude** — Nahtstelle für einen Wirt (KosmoVis-Kopf S3,
 * 20.10.2026; Visbox-Entscheid 116 (2)). Liegt im Paket, weil die Erzählzeile ihn liest;
 * KosmoOrbit reicht ihn über `state/kosmo-name.ts` weiter.
 *
 * In KosmoOrbit heisst der zweite Urheber «Kosmo», und dabei bleibt es: Ruft niemand
 * `registriereKosmoName`, ist alles wie vorher. Visbox meldet vor dem ersten Bild «Assistent» an.
 *
 * Gelesen wird der Name **beim Zeichnen** (`kosmoName()`), nicht beim Laden des Moduls: der Wirt
 * meldet ihn an, nachdem die Module schon geladen sind.
 */
export const KOSMO_NAME_VORGABE = 'Kosmo';

let name = KOSMO_NAME_VORGABE;

/** Meldet den Namen des Assistenten an; `null` oder leer stellt «Kosmo» wieder her. */
export function registriereKosmoName(neu: string | null): void {
  name = neu !== null && neu.trim() !== '' ? neu.trim() : KOSMO_NAME_VORGABE;
}

/** Der Name des Assistenten — «Kosmo», solange kein Wirt einen anderen angemeldet hat. */
export function kosmoName(): string {
  return name;
}
