import { melde } from '@kosmo/ui';

/**
 * STELLVERTRETER für `apps/kosmo-orbit/src/shell/homeserver-knopf.ts` (KosmoOrbit, 41 Zeilen).
 *
 * Runde 26 (14.10.2026): Im Original hängt an einem Brückenfehler, der den Token nennt, ein
 * Knopf «Einstellungen öffnen», der zum Abschnitt HomeServer springt. Visbox hat diese
 * Einstellungen nicht — auf der Knotenseite ist der Visbox-Server selbst die Brücke
 * (`apps/visbox-knoten/src/mappe.ts`). Ein Knopf, der nirgends hinführt, wäre ein
 * Bedienelement ohne Wirkung; darum bleibt es hier eine gewöhnliche Fehler-Meldung.
 * `HOMESERVER_KNOPF` ist wörtlich, damit die Kennung beim Zurückführen dieselbe bleibt.
 */
export const HOMESERVER_KNOPF = {
  label: 'Einstellungen öffnen',
  testid: 'bruecke-token-einstellungen',
  ariaLabel: 'Einstellungen öffnen, Abschnitt HomeServer, um den Bridge-Token einzutragen',
} as const;

export function meldeBrueckenFehler(text: string): void {
  melde(text, { ton: 'fehler' });
}
