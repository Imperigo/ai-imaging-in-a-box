/**
 * STELLVERTRETER (Visbox) (Kopfteile, Entscheide 115/116, 20.10.2026) fuer `state/project-sync.ts`
 * von KosmoOrbit.
 *
 * Einen gemeinsamen Raum (Sync) gibt es in Visbox nicht — Ausnahme «Sync-Leiste» in
 * `kosmovis/UI_AUSNAHMEN.json`. Die Zweitgruppe (`InselKopf.tsx`, woertlich) liest hier nur den Typ;
 * an der Stelle des Sync-Chips steht in Visbox der Heim-PC-Chip.
 */
export type SyncStatus = 'aus' | 'verbinde' | 'live' | 'getrennt' | 'abgelehnt';
