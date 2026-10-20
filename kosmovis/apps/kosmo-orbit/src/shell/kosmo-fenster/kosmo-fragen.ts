/**
 * STELLVERTRETER (Visbox) (Plan UI-Gleichheit S3, 20.10.2026) fuer `shell/kosmo-fenster/kosmo-fragen.ts`
 * von KosmoOrbit.
 *
 * Dort meldet der Eck-Orb beim Einhaengen bei `@kosmo/ui` an, wie man Kosmo eine Frage stellt; dann
 * traegt jede Fehlermeldung einen Knopf «Kosmo fragen» (U16, Owner B10). **In Visbox stuende dieser
 * Knopf mit dem Namen «Kosmo» an jeder Fehlermeldung** — er steht woertlich in `@kosmo/ui`
 * (`meldungen.tsx`), und den Assistenten hinter der Kugel gibt es nur in der Mac-App. Der
 * Stellvertreter meldet darum nichts an: ohne Anmeldung kein Knopf (so baut es das Paket selbst).
 * Fragen stellt man in Visbox im Gespraechsfeld der Kugel.
 */

/** Wortgleich wie dort; hier ohne Bedeutung (kein Motor, auf den gewartet wird). */
export const MOTOR_WARTEZEIT_MS = 4000;

/** Die Frage geht ins Gespraechsfeld — in Visbox nur ueber das Feld selbst, nicht aus einer Meldung. */
export function fragKosmo(_frage: string): void {
  // Bewusst leer: siehe Kopf. `registriereKosmoFragen` meldet diesen Weg nie an.
}

/** Meldet nichts an — Abmelden ist darum ebenso leer. */
export function registriereKosmoFragen(): () => void {
  return () => undefined;
}
