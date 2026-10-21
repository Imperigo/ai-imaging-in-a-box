/**
 * kosmo-maus-4 (LW, 08.10.2026), herausgeloest in Runde 13 (Integrator): eine
 * Quelle fuer die KosmoMaus-Antwort und den Fehlermeldeweg.
 *
 * Hinweise, die der Browser als `error` ans Fenster meldet, ohne dass etwas
 * schiefging. Nur GENAU diese Wortlaute: Chromium/WebKit «ResizeObserver loop
 * completed with undelivered notifications.», Chromium älter «ResizeObserver
 * loop limit exceeded». Sie sagen nur, dass eine Grössenmeldung auf den
 * nächsten Takt verschoben wurde (Spezifikation «ResizeObserver», Schritt
 * «deliver resize loop error notification»).
 */
export const HARMLOSE_FENSTER_HINWEISE: readonly string[] = [
  'ResizeObserver loop completed with undelivered notifications.',
  'ResizeObserver loop limit exceeded',
];

export function istHarmloserFensterHinweis(ev: Pick<ErrorEvent, 'message' | 'error'>): boolean {
  if (ev.error instanceof Error) return false;
  const text = String(ev.message ?? '').replace(/^Uncaught\s+/, '').trim();
  return HARMLOSE_FENSTER_HINWEISE.some((h) => text === h || text === h.replace(/\.$/, ''));
}
