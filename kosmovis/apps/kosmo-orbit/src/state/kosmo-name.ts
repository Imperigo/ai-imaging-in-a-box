/**
 * **Der Name des Assistenten neben Claude** — Nahtstelle fuer einen Wirt (KosmoVis-Kopf S3,
 * 20.10.2026; Visbox-Entscheid 116 (2)).
 *
 * In KosmoOrbit heisst der zweite Urheber «Kosmo», und dabei bleibt es: Ruft niemand
 * `registriereKosmoName`, ist alles wie vorher. Visbox uebernimmt Kugel, Fensterkopf und die
 * Coop-Teile wortgleich, rechnet aber mit einem eigenen Assistenten (nicht Kosmo); dort meldet
 * der Wirt vor dem ersten Bild «Assistent» an. Ohne diese Stelle stuende in Visbox «Kosmo
 * oeffnen» an einer Kugel, hinter der kein Kosmo ist — eine Falschauskunft in einer sonst
 * wortgleichen Datei.
 *
 * Gelesen wird der Name **beim Zeichnen** (`kosmoName()`), nicht beim Laden des Moduls: Der Wirt
 * meldet ihn an, nachdem die Module schon geladen sind. Darum sind die Namenstafeln, die ihn
 * tragen (`URHEBER_NAME`, der Name der Erzaehlzeile), Getter.
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

/**
 * **Der Name der App** in Sätzen an einen Agenten («… in KosmoOrbit einschalten») — dieselbe Art
 * Nahtstelle (KosmoVis-Kopf, Visbox Plan KI-Bedienung Stufe 6, 21.10.2026). In KosmoOrbit bleibt
 * «KosmoOrbit»; Visbox meldet «Visbox» an, weil dort KosmoMaus und KosmoBlick wortgleich laufen.
 */
export const APP_NAME_VORGABE = 'KosmoOrbit';

let app = APP_NAME_VORGABE;

/** Meldet den Namen der App an; `null` oder leer stellt «KosmoOrbit» wieder her. */
export function registriereAppName(neu: string | null): void {
  app = neu !== null && neu.trim() !== '' ? neu.trim() : APP_NAME_VORGABE;
}

/** Der Name der App — «KosmoOrbit», solange kein Wirt einen anderen angemeldet hat. */
export function appName(): string {
  return app;
}
