// Der Name des Assistenten liegt in `@kosmo/insel` (die Erzählzeile dort liest ihn); hier weitergereicht.
export { KOSMO_NAME_VORGABE, kosmoName, registriereKosmoName } from '@kosmo/insel';

/**
 * **Der Name der App** in Sätzen an einen Agenten («… in KosmoOrbit einschalten») — dieselbe Art
 * Nahtstelle (KosmoVis-Kopf, Visbox Plan KI-Bedienung Stufe 6, 21.10.2026). In KosmoOrbit bleibt
 * «KosmoOrbit»; Visbox meldet «Visbox» an, weil dort KosmoMaus und KosmoBlick wortgleich laufen.
 * (R57, Integrator: beim Einspielen von @kosmo/insel neben dem Paket-Namen behalten.)
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
